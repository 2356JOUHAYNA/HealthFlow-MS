🏥 HealthFlow-MS
Plateforme intelligente de prédiction de risque clinique et d’audit ML basée sur une architecture microservices

Docker · Spring Boot · Python · PostgreSQL · Apache Kafka · Evidently · Dash

🗺️ Vue d’ensemble

HealthFlow-MS est une plateforme MLOps orientée microservices conçue pour le traitement de données médicales FHIR, la prédiction de risque clinique et le monitoring post-déploiement des modèles de Machine Learning.

Le système met l’accent sur :

la traçabilité complète des données,

la pseudonymisation des patients,

la robustesse du pipeline ML,

la détection de dérive des données,

l’audit d’équité (fairness) des prédictions.

🎯 Objectifs principaux

Ingestion FHIR : récupération standardisée de données médicales (FHIR R4)

Pseudonymisation : protection de la vie privée (approche GDPR / HIPAA-ready)

Extraction de features : agrégation de données cliniques exploitables

Prédiction ML : calcul d’un niveau de risque patient

Monitoring ML : détection de dérive et audit d’équité

Visualisation : dashboards interactifs pour l’analyse décisionnelle

🏗️ Architecture du système
Architecture microservices orientée événements (Event-Driven)
FHIR Server
   ↓
ProxyFHIR
   ↓ (Kafka : fhir.data.raw)
DeID
   ↓ (Kafka : fhir.data.anonymized)
Featurizer
   ↓ PostgreSQL (patient_features)
ModelRisque
   ↓ PostgreSQL (risk_scores)
ScoreAPI
   ↓
AuditFairness (Dash + Evidently)

📊 Flux de données détaillé

ProxyFHIR

Récupère les bundles FHIR

Stocke les données brutes

Publie un événement Kafka

DeID

Anonymise les données patients

Remplace les identifiants par des pseudonymes

Préserve la structure FHIR

Featurizer

Extrait les caractéristiques patient

Stocke les features dans PostgreSQL via JSONB

ModelRisque

Calcule un score / niveau de risque

Enregistre les résultats en base

ScoreAPI

Expose les résultats via une API REST sécurisée

AuditFairness

Analyse la qualité des données

Détecte la dérive

Audite l’équité inter-groupes

Génère des rapports HTML Evidently

🚀 Démarrage rapide
Prérequis

Docker Engine ≥ 20.10

Docker Compose v2

8 Go RAM minimum

20 Go d’espace disque

Installation
git clone https://github.com/your-org/HealthFlow-MS.git
cd HealthFlow-MS
docker compose up -d --build

Vérifier les services
docker compose ps

🔗 Accès aux interfaces
Service	URL
ProxyFHIR Health	http://localhost:8081/api/v1/fhir/health

ScoreAPI Docs	http://localhost:8082/docs

AuditFairness Dashboard	http://localhost:8050

PostgreSQL	localhost:5432
📡 Ingestion de données FHIR réelles
Étapes

Choisir un Patient ID valide depuis
https://hapi.fhir.org/baseR4

Lancer l’ingestion :

curl -X POST http://localhost:8081/api/v1/fhir/sync/patient/<PATIENT_ID>


Le pipeline traite automatiquement :

DeID → Featurizer → ModelRisque

Consulter les résultats :

ScoreAPI

Dashboard AuditFairness

🧪 Test du pipeline complet
# Générer un token
curl -X POST http://localhost:8082/auth/token

# Vérifier un score
curl -X GET http://localhost:8082/api/v1/score/PATIENT_XXXX \
  -H "Authorization: Bearer <TOKEN>"

📋 Services détaillés
1️⃣ ProxyFHIR (Spring Boot)

Rôle :

Ingestion FHIR

Validation des ressources

Publication Kafka

Endpoints clés :

POST /api/v1/fhir/sync/patient/{id}

GET /api/v1/fhir/health

2️⃣ DeID (Python)

Rôle :

Anonymisation des données médicales

Génération de pseudonymes cohérents

Variables clés :

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
POSTGRES_HOST=postgres

3️⃣ Featurizer (Python)

Rôle :

Extraction de caractéristiques patient

Stockage flexible via JSONB

Exemples de features :

âge

genre

nombre de comorbidités

nombre de médicaments

4️⃣ ModelRisque (Python / ML)

Rôle :

Prédiction du risque clinique

Génération d’un niveau de risque

Sorties :

risk_level (LOW / MODERATE / HIGH)

confidence

5️⃣ ScoreAPI (FastAPI)

Rôle :

Exposition REST sécurisée

Accès aux scores et métadonnées

Sécurité :

JWT Bearer Token

6️⃣ AuditFairness (Dash + Evidently)

Rôle :

Surveillance post-déploiement du modèle

Fonctionnalités :

Data Quality

Data Drift

Analyse par groupes :

âge

comorbidité

niveau de risque

Rapports HTML Evidently

Historisation en base

Accès :

http://localhost:8050

🗄️ Base de données PostgreSQL
patient_features
patient_pseudo_id
features_json JSONB
created_at

risk_scores
patient_pseudo_id
risk_level
confidence
created_at

fairness_reports
id
created_at
ref_start
ref_end
cur_start
cur_end
report_path
summary JSONB

📊 Résultats observés (AuditFairness)

✔️ Aucune dérive détectée

✔️ Distributions stables

✔️ Données cohérentes

✔️ Modèle robuste dans le temps

🔐 Sécurité & conformité

Données pseudonymisées dès l’ingestion

Aucun identifiant patient direct

Traçabilité complète

Approche compatible GDPR / HIPAA (conceptuellement)

📈 Perspectives d’évolution

Intégration d’un vrai modèle XGBoost entraîné

SHAP pour explicabilité avancée

Alertes automatiques en cas de drift

Audit planifié (cron)

Export PDF des rapports

Déploiement Kubernetes
