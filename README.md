<img width="1536" height="1024" alt="HealthFlow-MS" src="https://github.com/user-attachments/assets/95683969-c99b-4f11-9453-3f6ed3ec3507" />

# 🧠 HealthFlow-MS

**HealthFlow-MS** is an intelligent MLOps platform for clinical risk prediction and machine learning audit, built on an **event-driven microservices architecture**.

It processes standardized medical data (FHIR), predicts patient clinical risk, and continuously monitors model quality, drift, and fairness.

---

## 🚀 Technologies

- **Docker & Docker Compose**
- **Spring Boot (Java)**
- **Python**
- **PostgreSQL**
- **Apache Kafka**
- **FastAPI**
- **Evidently AI**
- **Dash**

---

## 🔍 Overview

HealthFlow-MS is designed to address critical challenges in healthcare AI systems:

- End-to-end **data traceability**
- Early **patient pseudonymization**
- Robust **machine learning pipelines**
- **Data drift detection**
- **Fairness and bias auditing**
- Transparent and auditable predictions

The platform follows **privacy-by-design** principles and is conceptually aligned with **GDPR / HIPAA** requirements.

---

## 🎯 Main Objectives

- **FHIR Ingestion** – Standardized retrieval of medical data using FHIR R4  
- **Privacy Protection** – Early pseudonymization of patient identifiers  
- **Feature Engineering** – Extraction of clinically meaningful features  
- **ML Risk Prediction** – Patient-level risk scoring and classification  
- **ML Monitoring** – Data quality, drift detection, fairness audit  
- **Visualization** – Interactive dashboards for governance  

---

## 🏗️ System Architecture

### Event-Driven Microservices Architecture

<img width="1266" height="431" alt="architecture_readmission" src="https://github.com/user-attachments/assets/3a4c4962-b1ba-4483-8865-e6c635429746" />

Each service is independent, containerized, and communicates asynchronously via Kafka, ensuring scalability, fault tolerance, and full traceability.

---

## 📊 Data Flow Description

### 🔹 ProxyFHIR
- Retrieves FHIR bundles
- Validates resources
- Stores raw data
- Publishes Kafka events

### 🔹 DeID
- Removes sensitive identifiers
- Generates consistent pseudonyms
- Preserves FHIR structure

### 🔹 Featurizer
- Extracts patient-level features
- Stores features in PostgreSQL (JSONB)

### 🔹 ModelRisque
- Computes risk score and level
- Stores predictions in database

### 🔹 ScoreAPI
- Exposes predictions via secure REST API
- JWT-based authentication

### 🔹 AuditFairness
- Data quality analysis
- Drift detection
- Fairness audit across groups
- Generates Evidently HTML reports

---

## 🧪 Observed Results (AuditFairness)

✔️ No data drift detected  
✔️ Stable feature distributions  
✔️ Consistent predictions  
✔️ Robust model behavior over time  

---

## 🚀 Getting Started

### Prerequisites

- Docker Engine ≥ 20.10  
- Docker Compose v2  
- **Minimum 8 GB RAM**  
- **20 GB free disk space**

---

## 📦 Installation



### 1. Clone the repository

```bash
git clone https://github.com/your-org/HealthFlow-MS.git
cd HealthFlow-MS
```
2. Build and start the services
bash
Copy code
docker compose up -d --build
3. Verify running services
bash
Copy code
docker compose ps
🔗 Service Access URLs
Service	URL
ProxyFHIR Health	http://localhost:8081/api/v1/fhir/health
ScoreAPI Docs	http://localhost:8082/docs
AuditFairness Dashboard	http://localhost:8050
PostgreSQL	localhost:5432

📡 Ingest Real FHIR Data
Steps
Choose a valid Patient ID from
https://hapi.fhir.org/baseR4

Trigger ingestion:

bash
Copy code
curl -X POST http://localhost:8081/api/v1/fhir/sync/patient/<PATIENT_ID>
The pipeline executes automatically:

nginx
Copy code
DeID → Featurizer → ModelRisque
View results:

ScoreAPI

AuditFairness dashboard

🔐 Authentication & API Usage
Generate JWT token
bash
Copy code
curl -X POST http://localhost:8082/auth/token
Retrieve patient risk score
bash
Copy code
curl -X GET http://localhost:8082/api/v1/score/PATIENT_XXXX \
  -H "Authorization: Bearer <TOKEN>"
📋 Services Overview
1️⃣ ProxyFHIR (Spring Boot)
FHIR ingestion

Resource validation

Kafka publishing

2️⃣ DeID (Python)
Medical data anonymization

Pseudonym generation

3️⃣ Featurizer (Python)
Feature extraction

JSONB storage in PostgreSQL

4️⃣ ModelRisque (Python / ML)
Clinical risk prediction

Outputs:

risk_level (LOW / MODERATE / HIGH)

confidence

5️⃣ ScoreAPI (FastAPI)
Secure REST API

JWT authentication

6️⃣ AuditFairness (Dash + Evidently)
Post-deployment ML monitoring

Data quality analysis

Drift detection

Fairness analysis

HTML reports generation

🗄️ PostgreSQL Schema
patient_features
patient_pseudo_id

features_json (JSONB)

created_at

risk_scores
patient_pseudo_id

risk_level

confidence

created_at

fairness_reports
id

ref_start

ref_end

cur_start

cur_end

summary (JSONB)

report_path

🔐 Security & Compliance
Early patient pseudonymization

No direct patient identifiers stored

Full pipeline traceability

GDPR / HIPAA-ready (conceptual design)

📈 Future Improvements
Integration of a trained XGBoost model

Advanced explainability using SHAP

Automated drift alerts

Scheduled audits (cron)

PDF export of audit reports

Kubernetes deployment (Helm, HPA, monitoring)

👩‍💻 Authors
Jouhayna Koubichate

Salma El Gouffi

Khaoula Aguabdre

📄 License
This project is released under the MIT License.

markdown
Copy code

---

### ✅ Résultat après correction
- ✔️ plus de texte “coincé” dans un bloc gris  
- ✔️ affichage GitHub propre (bouton **Copy**, syntaxe bash)  
- ✔️ niveau **PFE / projet pro / recruteur**

Si tu veux, je peux maintenant :
- 🔥 ajouter des **badges GitHub**
- 📊 créer une **section BPMN**
- ☁️ ajouter une **version Kubernetes**
- 🎓 adapter pour **article scientifique**

Dis-moi la suite 💜





