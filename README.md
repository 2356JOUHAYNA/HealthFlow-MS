<img width="1536" height="1024" alt="ChatGPT Image Dec 26, 2025, 11_39_07 PM" src="https://github.com/user-attachments/assets/95683969-c99b-4f11-9453-3f6ed3ec3507" />


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

- **FHIR Ingestion**  
  Standardized retrieval of medical data using FHIR R4

- **Privacy Protection**  
  Early pseudonymization of patient identifiers

- **Feature Engineering**  
  Extraction of clinically meaningful features

- **ML Risk Prediction**  
  Patient-level risk scoring and classification

- **ML Monitoring**  
  Data quality checks, drift detection, and fairness audit

- **Visualization**  
  Interactive dashboards for decision support and governance

---

## 🏗️ System Architecture

### Event-Driven Microservices Architecture


<img width="1266" height="431" alt="architecture_readmission" src="https://github.com/user-attachments/assets/3a4c4962-b1ba-4483-8865-e6c635429746" />

Each service is:
- Independent
- Containerized
- Communicating asynchronously via Kafka

This ensures scalability, fault tolerance, and full traceability.

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

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/your-org/HealthFlow-MS.git
cd HealthFlow-MS
