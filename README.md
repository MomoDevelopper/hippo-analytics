# HIPPO ANALYTICS 🐎

> Plateforme intelligente d'analyse et de prédiction hippique  
> **PMU Burkina Faso — LONAB**

## Présentation

HIPPO ANALYTICS analyse automatiquement les programmes hippiques du PMU Burkina Faso (LONAB) et produit des hypothèses de classement pour les 5 premiers chevaux, avec des probabilités calculées par simulation Monte Carlo (100 000 arrivées simulées).

## Fonctionnalités

- 📥 **Import automatique** des programmes LONAB (PDF scraping)
- 📁 **Import manuel** de fichiers PDF et Excel avec OCR
- 🐴 **Analyse des chevaux** : notes basées sur forme, distance, jockey, entraîneur, régularité
- 👤 **Classement jockeys et entraîneurs** avec statistiques détaillées
- 🎯 **Moteur de prédiction** : Plackett-Luce + Monte Carlo (100 000 simulations)
- 📊 **524 160 hypothèses** de classement générées et triées par probabilité
- 🔄 **Synchronisation autonome** : collecte continue même sans administrateur connecté
- 📈 **Historique des prédictions** vs résultats réels

## Architecture technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11 + FastAPI |
| Base de données | PostgreSQL 15 |
| IA / Simulation | NumPy + Scikit-learn + XGBoost |
| Extraction PDF | PyMuPDF + Tesseract OCR |
| Frontend | Next.js 14 + React + Tailwind CSS |
| Déploiement | Docker + Docker Compose |

## Prérequis

- Docker Desktop installé
- Docker Compose v3.9+

## Démarrage rapide

### 1. Cloner et configurer

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer .env si besoin (clé secrète, URL LONAB, etc.)
```

### 2. Lancer avec Docker

```bash
docker-compose up -d
```

### 3. Accéder à l'application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Backend | http://localhost:8000 |
| Documentation API | http://localhost:8000/api/docs |
| Vérification santé | http://localhost:8000/health |

## Structure du projet

```
hyppo_analytics/
├── backend/
│   ├── app/
│   │   ├── main.py           # Application FastAPI
│   │   ├── config.py         # Configuration (variables d'env)
│   │   ├── database.py       # Connexion PostgreSQL
│   │   ├── scheduler.py      # Synchronisation autonome (APScheduler)
│   │   ├── models/           # Modèles de base de données (ORM)
│   │   ├── routers/          # Routes API
│   │   └── services/         # Logique métier
│   └── requirements.txt
├── frontend/                 # Interface Next.js (Phase 5)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Routes API principales

```
GET  /api/programmes           Programmes disponibles
POST /api/programmes/import/pdf    Importer un PDF
POST /api/programmes/import/excel  Importer un Excel
GET  /api/courses              Liste des courses
GET  /api/courses/{id}         Détail d'une course
GET  /api/chevaux              Liste des chevaux
GET  /api/jockeys              Classement des jockeys
GET  /api/entraineurs          Classement des entraîneurs
POST /api/predictions/{id}     Lancer une prédiction
GET  /api/hypotheses/{id}      Top hypothèses
POST /api/resultats            Enregistrer une arrivée
GET  /api/sync/status          État de la synchronisation
POST /api/sync/run             Synchronisation manuelle
GET  /api/statistiques         Statistiques globales
```

## Synchronisation autonome

Le système collecte automatiquement les programmes LONAB toutes les 6 heures.  
Même si vous n'êtes pas connecté pendant 3 jours, au retour vous retrouvez :
- Les programmes téléchargés en attente de validation
- Les historiques mis à jour
- Les statistiques recalculées

```bash
# Vérifier l'état de la synchronisation
curl http://localhost:8000/api/sync/status

# Lancer une synchronisation manuelle
curl -X POST http://localhost:8000/api/sync/run
```

## Phases de développement

| Phase | Statut | Description |
|-------|--------|-------------|
| 1 | ✅ **Terminée** | Architecture, BDD, API backend |
| 2 | 🔄 En cours | Importation PDF/OCR, parsing LONAB |
| 3 | ⏳ Prévue | Analyse avancée, scoring affiné |
| 4 | ⏳ Prévue | XGBoost, apprentissage sur historiques |
| 5 | ⏳ Prévue | Frontend Next.js complet |
| 6 | ⏳ Prévue | Tests, calibration, optimisation |

## Licence

Projet privé — Réservé à l'usage interne HIPPO ANALYTICS.
