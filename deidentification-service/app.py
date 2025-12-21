import json
import logging
import os
import hashlib
import signal
import sys
from typing import Dict, Any, List

import psycopg2
from kafka import KafkaConsumer, KafkaProducer

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeIdentificationService")

# --------------------------------------------------
# Config
# --------------------------------------------------
KAFKA_BOOTSTRAP = "kafka:9092"
INPUT_TOPIC = "fhir.data.raw"
OUTPUT_TOPIC = "fhir.data.anonymized"

POSTGRES_CONFIG = {
    "host": "postgres-healthflow",
    "database": "healthflow",
    "user": "postgres",
    "password": "postgres",
}

SALT = os.getenv("DEID_SALT", "healthflow-salt")

# --------------------------------------------------
# Utils
# --------------------------------------------------
def pseudonymize(value: str) -> str:
    return hashlib.sha256((value + SALT).encode()).hexdigest()[:12]

# --------------------------------------------------
# Service
# --------------------------------------------------
class DeIdentificationService:

    def __init__(self):
        logger.info("🚀 Initializing DeIdentification Service")

        self.db = psycopg2.connect(**POSTGRES_CONFIG)
        self.db.autocommit = True

        self.consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id="deidentification-service",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        logger.info("✅ DeIdentification Service ready")

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------
    def shutdown(self, *_):
        logger.info("🛑 Stopping DeIdentification Service")
        self.consumer.close()
        self.producer.close()
        self.db.close()
        sys.exit(0)

    # --------------------------------------------------
    # Load bundle from DB
    # --------------------------------------------------
    def load_bundle(self, bundle_id: int) -> Dict[str, Any]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT bundle_data FROM fhir_bundles WHERE id = %s",
                (bundle_id,),
            )
            row = cur.fetchone()

        if not row:
            raise ValueError(f"Bundle {bundle_id} not found")

        return json.loads(row[0])

    # --------------------------------------------------
    # De-identify bundle
    # --------------------------------------------------
    def deidentify_bundle(self, bundle: Dict[str, Any], pseudo_id: str) -> List[Dict[str, Any]]:
        cleaned_resources = []

        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType")

            # ---------- Patient ----------
            if rtype == "Patient":
                resource.pop("name", None)
                resource.pop("telecom", None)
                resource.pop("address", None)
                resource["id"] = pseudo_id
                cleaned_resources.append(resource)

            # ---------- Other resources ----------
            else:
                resource.pop("performer", None)
                resource.pop("recorder", None)
                cleaned_resources.append(resource)

        return cleaned_resources

    # --------------------------------------------------
    # Process Kafka message
    # --------------------------------------------------
    def process(self, msg: Dict[str, Any]):
        bundle_id = msg.get("bundleId")
        real_patient_id = msg.get("patientId")

        if not bundle_id or not real_patient_id:
            logger.warning("⚠️ Invalid message skipped: %s", msg)
            return

        pseudo_id = f"PATIENT_{pseudonymize(real_patient_id)}"

        bundle = self.load_bundle(bundle_id)
        anonymized_bundle = self.deidentify_bundle(bundle, pseudo_id)

        payload = {
            "patient_id": pseudo_id,
            "bundle": anonymized_bundle,
        }

        self.producer.send(OUTPUT_TOPIC, payload)
        self.producer.flush()

        logger.info(
            "✅ Bundle %s anonymized for %s (%d resources)",
            bundle_id, pseudo_id, len(anonymized_bundle)
        )

    # --------------------------------------------------
    # Run
    # --------------------------------------------------
    def run(self):
        logger.info("📥 Listening on fhir.data.raw ...")
        for msg in self.consumer:
            self.process(msg.value)

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    DeIdentificationService().run()
