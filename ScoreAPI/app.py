import json
import os
import logging
import threading
from datetime import datetime, timedelta
from typing import List

import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer

from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
from pydantic import BaseModel

# ==================================================
# PATHS (IMPORTANT POUR DOCKER)
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# ==================================================
# CONFIG
# ==================================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres-healthflow")
POSTGRES_DB = os.getenv("POSTGRES_DB", "healthflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "risk.score.calculated"

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGO = "HS256"

# ==================================================
# LOGGING
# ==================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScoreAPI")

# ==================================================
# FASTAPI
# ==================================================
app = FastAPI(
    title="HealthFlow – Score API",
    description="API & Interface pour les scores de risque cliniques",
    version="1.0"
)

# ✅ STATIC FILES (CORRIGÉ)
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# ✅ TEMPLATES (CORRIGÉ)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

security = HTTPBearer()

# ==================================================
# DATABASE
# ==================================================
def get_db():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

# ==================================================
# JWT
# ==================================================
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/token")
def get_token():
    token = jwt.encode(
        {"sub": "clinician", "exp": datetime.utcnow() + timedelta(hours=4)},
        JWT_SECRET,
        algorithm=JWT_ALGO
    )
    return {"access_token": token}

# ==================================================
# MODELS
# ==================================================
class RiskScore(BaseModel):
    patient_pseudo_id: str
    risk_class: int
    risk_level: str
    confidence: float
    natural_explanation: str
    created_at: datetime

# ==================================================
# KAFKA → DB CONSUMER
# ==================================================
def consume_scores():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
        group_id="score-api"
    )

    conn = get_db()
    cur = conn.cursor()

    logger.info("📥 Kafka consumer started (ScoreAPI)")

    for msg in consumer:
        data = msg.value
        try:
            cur.execute("""
                INSERT INTO risk_scores (
                    patient_pseudo_id,
                    risk_class,
                    risk_level,
                    confidence,
                    explanation,
                    natural_explanation
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data["patientPseudoId"],
                data["riskClass"],
                data["riskLevel"],
                data["confidence"],
                json.dumps(data["explanation"]),
                data.get("naturalExplanation", "")
            ))

            conn.commit()
            logger.info(f"💾 Score stocké pour {data['patientPseudoId']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ ERREUR DB : {e}")

# ==================================================
# STARTUP
# ==================================================
@app.on_event("startup")
def startup():
    logger.info("🚀 ScoreAPI démarré")
    threading.Thread(target=consume_scores, daemon=True).start()

# ==================================================
# API
# ==================================================
@app.get("/api/v1/scores/{patient_id}", response_model=RiskScore)
def get_latest_score(patient_id: str, user=Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT patient_pseudo_id,
               risk_class,
               risk_level,
               confidence,
               natural_explanation,
               created_at
        FROM risk_scores
        WHERE patient_pseudo_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (patient_id,))

    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Patient not found")

    return row

# ==================================================
# DASHBOARD WEB
# ==================================================
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT patient_pseudo_id,
               risk_level,
               confidence,
               natural_explanation,
               created_at
        FROM risk_scores
        ORDER BY created_at DESC
        LIMIT 20
    """)

    scores = cur.fetchall()

    # ✅ FIX : convertir datetime → string ISO
    for s in scores:
        if s["created_at"]:
            s["created_at"] = s["created_at"].isoformat()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "scores": scores}
    )

# ==================================================
# HEALTH
# ==================================================
@app.get("/health")
def health():
    return {"status": "UP", "service": "ScoreAPI"}
