import json
import logging
import os
import time
from datetime import datetime, date
from typing import Dict, Any, Optional
from collections import defaultdict

import psycopg2
import numpy as np
import torch
import spacy

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from transformers import AutoTokenizer, AutoModel

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FeaturizerService")

# --------------------------------------------------
# Config
# --------------------------------------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "fhir.data.anonymized")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "features.patient.ready")

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres-healthflow"),
    "database": os.getenv("POSTGRES_DB", "healthflow"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

BIOBERT_MODEL = os.getenv("BIOBERT_MODEL", "dmis-lab/biobert-base-cased-v1.1")

# --------------------------------------------------
# Clinical mappings (PFE-friendly)
# --------------------------------------------------
ICD_CATEGORY_MAP = {
    "I": "cardio",
    "E": "diabetes",
    "J": "respiratory",
    "C": "cancer",
    "F": "mental",
}

ATC_CATEGORY_MAP = {
    "A10": "antidiabetic",
    "C09": "antihypertensive",
    "N02": "analgesic",
    "J01": "antibiotic",
}

OBS_CODE_MAP = {
    "8867-4": "heart_rate",
    "8480-6": "bp_systolic",
    "8462-4": "bp_diastolic",
    "8310-5": "temperature",
    "59408-5": "spo2",
    "9279-1": "resp_rate",
}

# --------------------------------------------------
# Featurizer Service
# --------------------------------------------------
class FeaturizerService:

    def __init__(self):
        logger.info("🚀 Initializing Featurizer Service")

        # Wait for PostgreSQL (Docker startup safety)
        logger.info("⏳ Waiting for PostgreSQL...")
        time.sleep(10)

        # PostgreSQL
        self.db = psycopg2.connect(**DB_CONFIG)
        self.db.autocommit = True

        # Kafka Consumer (stable for heavy NLP)
        self.consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id="featurizer-service",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_interval_ms=900000,
            max_poll_records=1,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            request_timeout_ms=60000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        # Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            acks="all",
            retries=5,
            linger_ms=10,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        # NLP
        logger.info("🧠 Loading spaCy medical model")
        self.nlp = spacy.load("en_core_sci_sm")

        # BioBERT
        logger.info("🧠 Loading BioBERT")
        self.tokenizer = AutoTokenizer.from_pretrained(BIOBERT_MODEL)
        self.model = AutoModel.from_pretrained(BIOBERT_MODEL)
        self.model.eval()

    # --------------------------------------------------
    # Utils
    # --------------------------------------------------
    def calculate_age(self, birth_date: str) -> Optional[int]:
        try:
            if len(birth_date) == 10:
                born = date.fromisoformat(birth_date)
            elif len(birth_date) == 7:
                born = date.fromisoformat(birth_date + "-01")
            elif len(birth_date) == 4:
                born = date.fromisoformat(birth_date + "-01-01")
            else:
                return None

            today = date.today()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except Exception:
            return None

    def _safe_text(self, x: Any) -> str:
        return str(x).strip() if x is not None else ""

    # --------------------------------------------------
    # BioBERT
    # --------------------------------------------------
    def biobert_embedding(self, text: str) -> Optional[np.ndarray]:
        text = self._safe_text(text)
        if not text:
            return None

        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=256,
            )
            with torch.no_grad():
                output = self.model(**inputs)
            return output.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
        except Exception as e:
            logger.warning(f"⚠️ BioBERT failed: {e}")
            return None

    # --------------------------------------------------
    # NLP
    # --------------------------------------------------
    def extract_entities(self, text: str) -> Dict[str, float]:
        text = self._safe_text(text)
        if not text:
            return {}

        doc = self.nlp(text)
        counts = defaultdict(float)
        for ent in doc.ents:
            counts[f"nlp_{ent.label_.lower()}"] += 1.0
        return dict(counts)
    # --------------------------------------------------
    # Helpers (FIX OBLIGATOIRE)
    # --------------------------------------------------
    def _extract_codings(self, code_block: Dict[str, Any]) -> list:
        return (code_block or {}).get("coding", []) or []

    def _extract_obs_kind(self, obs: Dict[str, Any]) -> Optional[str]:
        for c in self._extract_codings(obs.get("code")):
            code = self._safe_text(c.get("code"))
            if code in OBS_CODE_MAP:
                return OBS_CODE_MAP[code]
        return None

    # --------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------
    def save_features(self, patient_id: str, features: Dict[str, float]):
        try:
            with self.db.cursor() as cur:
              cur.execute(
                """
                INSERT INTO public.patient_features
                (patient_pseudo_id, features_json, feature_count, source)
                VALUES (%s, %s::jsonb, %s, %s)
                """,
                (
                    patient_id,
                    json.dumps(features),
                    len(features),
                    "featurizer"
                )
            )
        except psycopg2.Error as e:
             logger.error(f"❌ PostgreSQL error: {e}")
        return   # ⬅️ IMPORTANT : pas de raise ici



    # --------------------------------------------------
    # Helpers (FIX MANQUANT)
    # --------------------------------------------------
    def _extract_codings(self, code_block: Dict[str, Any]) -> list:
        return (code_block or {}).get("coding", []) or []

    def _extract_obs_kind(self, obs: Dict[str, Any]) -> Optional[str]:
        for c in self._extract_codings(obs.get("code")):
            code = self._safe_text(c.get("code"))
            if code in OBS_CODE_MAP:
                return OBS_CODE_MAP[code]
        return None

    # --------------------------------------------------
    # Processing
    # --------------------------------------------------
    def process(self, message: Dict[str, Any]) -> bool:
        patient_id = message.get("patient_id")
        bundle = message.get("bundle", [])

        if not patient_id or not bundle:
            return False

        features = defaultdict(float)
        clinical_text = []
        vitals = defaultdict(list)

        for r in bundle:
            rt = r.get("resourceType")

            if rt == "Patient":
                age = self.calculate_age(self._safe_text(r.get("birthDate")))
                if age is not None:
                    features["age"] = age
                gender = self._safe_text(r.get("gender")).lower()
                if gender:
                    features[f"gender_{gender}"] = 1.0

            elif rt == "Condition":
                features["conditions_total"] += 1
                for c in self._extract_codings(r.get("code")):
                    code = self._safe_text(c.get("code"))
                    for p, cat in ICD_CATEGORY_MAP.items():
                        if code.startswith(p):
                            features[f"condition_{cat}"] += 1
                clinical_text.append(self._safe_text(r.get("code", {}).get("text")))

            elif rt == "MedicationRequest":
                features["medications_total"] += 1
                for c in self._extract_codings(r.get("medicationCodeableConcept")):
                    code = self._safe_text(c.get("code"))
                    for p, cat in ATC_CATEGORY_MAP.items():
                        if code.startswith(p):
                            features[f"medication_{cat}"] += 1
                clinical_text.append(self._safe_text(r.get("medicationCodeableConcept", {}).get("text")))

            elif rt == "Observation":
                vq = r.get("valueQuantity")
                if vq and "value" in vq:
                    kind = self._extract_obs_kind(r) or "vital_generic"
                    vitals[kind].append(float(vq["value"]))

            elif rt == "DiagnosticReport":
                clinical_text.append(self._safe_text(r.get("conclusion")))

        for k, vals in vitals.items():
            if vals:
                features[f"{k}_mean"] = np.mean(vals)
                features[f"{k}_latest"] = vals[-1]
                if len(vals) > 1:
                    features[f"{k}_trend"] = vals[-1] - vals[0]

        text = " ".join(clinical_text).strip()
        if text:
            features.update(self.extract_entities(text))
            emb = self.biobert_embedding(text)
            if emb is not None:
                for i in range(10):
                    features[f"biobert_{i}"] = float(emb[i])

        self.save_features(patient_id, features)

        self.producer.send(OUTPUT_TOPIC, {
            "patient_id": patient_id,
            "feature_count": len(features),
            "features": dict(features),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "source": "featurizer",
        }).get(timeout=30)

        logger.info(f"✅ Features extracted for {patient_id} ({len(features)})")
        return True

    # --------------------------------------------------
    # Run
    # --------------------------------------------------
    def run(self):
        logger.info("📥 Listening for anonymized data...")
        for msg in self.consumer:
            if self.process(msg.value):
                self.consumer.commit()


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    FeaturizerService().run()
