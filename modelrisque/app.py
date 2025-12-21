import json
import logging
import os
import time
import pickle
from typing import Dict, Any

import numpy as np
import pandas as pd
import psycopg2
import xgboost as xgb
import shap

from kafka import KafkaConsumer, KafkaProducer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# ==================================================
# CONFIG
# ==================================================
TRAIN_MODE = os.getenv("TRAIN_MODE", "false").lower() == "true"

MODEL_DIR = "/app/model"
MODEL_PATH = f"{MODEL_DIR}/model.xgb"
SCALER_PATH = f"{MODEL_DIR}/scaler.pkl"
FEATURES_PATH = f"{MODEL_DIR}/feature_names.pkl"
CLASS_MAP_PATH = f"{MODEL_DIR}/class_mapping.pkl"

RISK_LABELS = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "CRITICAL"
}

# ==================================================
# FEATURE → MEDICAL MEANING
# ==================================================
FEATURE_MEANING = {
    "age": "âge avancé",
    "medications_total": "polymédication",
    "conditions_total": "comorbidités multiples",
    "hospital_visits_12m": "hospitalisations récentes",
    "gender_male": "sexe masculin",

    "biobert_0": "signal clinique faible",
    "biobert_1": "signal clinique sévère",
    "biobert_2": "symptômes légers",
    "biobert_3": "stabilité clinique",
    "biobert_6": "facteurs aggravants"
}

# ==================================================
# LOGGING
# ==================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ModelRiskService")

# ==================================================
# RULE-BASED LABEL (TRAINING)
# ==================================================
def compute_risk_class(features: Dict[str, Any]) -> int:
    score = 0
    if features.get("age", 0) > 65:
        score += 1
    if features.get("conditions_total", 0) >= 2:
        score += 1
    if features.get("medications_total", 0) >= 3:
        score += 1
    if features.get("hospital_visits_12m", 0) >= 2:
        score += 1
    return min(score, 3)

# ==================================================
# TRAINING
# ==================================================
def train_and_save_model():
    logger.info("🧠 TRAIN MODE ENABLED")

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "healthflow"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

    df = pd.read_sql("SELECT features_json FROM patient_features", conn)
    conn.close()

    rows = []
    for _, r in df.iterrows():
        f = r["features_json"]
        f["risk_class"] = compute_risk_class(f)
        rows.append(f)

    data = pd.DataFrame(rows).fillna(0)

    feature_names = [c for c in data.columns if c != "risk_class"]
    X = data[feature_names]
    y = data["risk_class"].astype(int)

    classes = sorted(y.unique())
    class_mapping = {old: new for new, old in enumerate(classes)}
    inverse_mapping = {v: k for k, v in class_mapping.items()}
    y = y.map(class_mapping)

    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(classes),
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        eval_metric="mlogloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(MODEL_PATH)
    pickle.dump(scaler, open(SCALER_PATH, "wb"))
    pickle.dump(feature_names, open(FEATURES_PATH, "wb"))
    pickle.dump(inverse_mapping, open(CLASS_MAP_PATH, "wb"))

    logger.info("💾 Model trained & saved")

# ==================================================
# MEDICAL NLP EXPLANATION
# ==================================================
def generate_natural_explanation(risk_label, ranked_features):
    reasons = []

    positives = [(f, v) for f, v in ranked_features if v > 0]

    for f, _ in positives[:3]:
        reasons.append(FEATURE_MEANING.get(f, f))

    if not reasons:
        reasons.append("profil clinique global")

    reasons = [f"({i+1}) {r}" for i, r in enumerate(reasons)]

    return f"{risk_label} car : " + ", ".join(reasons)

# ==================================================
# ONLINE SERVICE
# ==================================================
class ModelRiskService:

    def __init__(self):
        self.model = xgb.XGBClassifier()
        self.model.load_model(MODEL_PATH)

        self.scaler = pickle.load(open(SCALER_PATH, "rb"))
        self.feature_names = pickle.load(open(FEATURES_PATH, "rb"))
        self.class_mapping = pickle.load(open(CLASS_MAP_PATH, "rb"))

        background = np.zeros((1, len(self.feature_names)))
        masker = shap.maskers.Independent(background)

        self.explainer = shap.Explainer(
            self.model.predict_proba,
            masker=masker,
            feature_names=self.feature_names
        )

        self.consumer = KafkaConsumer(
            "features.patient.ready",
            bootstrap_servers="kafka:9092",
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="earliest",
            group_id="model-risk-service",
            enable_auto_commit=True
        )

        self.producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            value_serializer=lambda v: json.dumps(v).encode()
        )

        logger.info("🚀 ModelRiskService running (SHAP + MEDICAL NLP OK)")

    def _prepare(self, features):
        ordered = [features.get(f, 0) for f in self.feature_names]
        return self.scaler.transform(np.array(ordered).reshape(1, -1))

    def run(self):
        for msg in self.consumer:
            patient_id = msg.value.get("patient_id")
            features = msg.value.get("features")

            if not patient_id or not features:
                continue

            X = self._prepare(features)
            probs = self.model.predict_proba(X)[0]

            idx = int(np.argmax(probs))
            risk_class = int(self.class_mapping[idx])
            risk_label = RISK_LABELS[risk_class]

            shap_values = self.explainer(X)
            impacts = shap_values.values[0, :, idx]

            ranked = sorted(
                zip(self.feature_names, impacts),
                key=lambda x: abs(x[1]),
                reverse=True
            )

            explanation = [
                {
                    "feature": f,
                    "impact": float(abs(v)),
                    "direction": "increase" if v > 0 else "decrease"
                }
                for f, v in ranked[:5]
            ]

            natural_text = generate_natural_explanation(risk_label, ranked)

            payload = {
                "patientPseudoId": patient_id,
                "riskClass": risk_class,
                "riskLevel": risk_label,
                "confidence": float(np.max(probs)),
                "explanation": explanation,
                "naturalExplanation": natural_text,
                "timestamp": int(time.time() * 1000)
            }

            self.producer.send("risk.score.calculated", payload)
            self.producer.flush()

            logger.info(f"✅ {patient_id} → {risk_label}")

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    if TRAIN_MODE:
        train_and_save_model()
    else:
        ModelRiskService().run()
