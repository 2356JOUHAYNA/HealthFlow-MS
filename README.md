<img width="1536" height="1024" alt="ChatGPT Image Dec 26, 2025, 11_39_07 PM" src="https://github.com/user-attachments/assets/95683969-c99b-4f11-9453-3f6ed3ec3507" />


🧠 HealthFlow-MS
Plateforme intelligente de prédiction de risque clinique et d’audit ML

Basée sur une architecture microservices orientée événements

Technologies :
Docker · Spring Boot · Python · PostgreSQL · Apache Kafka · Evidently · Dash

🔍 Vue d’ensemble

HealthFlow-MS est une plateforme MLOps orientée microservices dédiée au traitement de données médicales standardisées (FHIR R4), à la prédiction de risque clinique, et au monitoring post-déploiement des modèles de Machine Learning.

La plateforme a été conçue pour répondre aux enjeux critiques de l’IA en santé, en mettant l’accent sur :

la traçabilité complète des données,

la pseudonymisation précoce des patients,

la robustesse du pipeline ML,

la détection de dérive des données,

l’audit d’équité (fairness) des prédictions.

🎯 Objectifs principaux

Ingestion FHIR
Récupération standardisée de données médicales via FHIR R4.

Protection de la vie privée
Pseudonymisation des patients selon une approche privacy-by-design (GDPR / HIPAA-ready).

Feature Engineering
Extraction et agrégation de caractéristiques cliniques exploitables.

Prédiction ML
Calcul d’un niveau de risque patient interprétable.

Monitoring & Audit ML

Détection de dérive des données et audit d’équité inter-groupes.

Visualisation
Dashboards interactifs pour l’analyse décisionnelle et la gouvernance IA.

🏗️ Architecture du système
<img width="1266" height="431" alt="architecture_readmission" src="https://github.com/user-attachments/assets/3a4c4962-b1ba-4483-8865-e6c635429746" />
📊 Flux de données détaillé
🔹 ProxyFHIR

Récupération des bundles FHIR

Validation des ressources

Stockage des données brutes

Publication d’événements Kafka

🔹 DeID

Suppression des identifiants sensibles

Génération de pseudonymes cohérents

Préservation de la structure FHIR

🔹 Featurizer

Extraction de caractéristiques patient

Stockage flexible via PostgreSQL (JSONB)

🔹 ModelRisque

Calcul du score et du niveau de risque

Enregistrement des résultats

🔹 ScoreAPI

Exposition sécurisée des scores via API REST

Authentification JWT

🔹 AuditFairness

Analyse de la qualité des données

Détection de dérive

Audit d’équité inter-groupes

Génération de rapports Evidently (HTML)

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
