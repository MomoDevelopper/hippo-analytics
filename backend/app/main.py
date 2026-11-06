"""
HIPPO ANALYTICS — Application FastAPI principale.
Plateforme d'analyse et de prédiction hippique pour PMU Burkina Faso (LONAB).
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import create_tables
from app.scheduler import demarrer_scheduler, arreter_scheduler
from app.routers import (
    programmes,
    courses,
    chevaux,
    jockeys,
    entraineurs,
    statistiques,
    resultats,
    sync,
    admin,
)
from app.routers.predictions import router_predictions, router_hypotheses

# ──────────────────────────────────────────────
# Configuration du logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger = logging.getLogger("hippo_analytics")
settings = get_settings()


# ──────────────────────────────────────────────
# Cycle de vie de l'application
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le démarrage et l'arrêt de l'application.
    - Démarrage : création des tables + lancement du scheduler
    - Arrêt     : arrêt propre du scheduler
    """
    logger.info("=" * 60)
    logger.info("  HIPPO ANALYTICS — Démarrage")
    logger.info(f"  Mode debug : {settings.DEBUG}")
    logger.info("=" * 60)

    # Créer les dossiers nécessaires
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR, "programmes").mkdir(parents=True, exist_ok=True)

    # Créer les tables de base de données
    try:
        create_tables()
        logger.info("Base de données initialisée")
    except Exception as e:
        logger.error(f"Erreur d'initialisation de la base de données : {e}")

    # Démarrer la synchronisation autonome
    try:
        demarrer_scheduler()
    except Exception as e:
        logger.error(f"Erreur au démarrage du scheduler : {e}")

    yield  # L'application tourne ici

    # Arrêt propre
    arreter_scheduler()
    logger.info("HIPPO ANALYTICS — Arrêt")


# ──────────────────────────────────────────────
# Création de l'application FastAPI
# ──────────────────────────────────────────────
app = FastAPI(
    title="HIPPO ANALYTICS API",
    description=(
        "Plateforme intelligente d'analyse et de prédiction hippique "
        "pour PMU Burkina Faso (LONAB). "
        "Analyse les chevaux, jockeys et entraîneurs pour produire "
        "des hypothèses de classement avec simulation Monte Carlo."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ──────────────────────────────────────────────
# CORS (autorise le frontend Next.js)
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(programmes.router, prefix=API_PREFIX)
app.include_router(courses.router, prefix=API_PREFIX)
app.include_router(chevaux.router, prefix=API_PREFIX)
app.include_router(jockeys.router, prefix=API_PREFIX)
app.include_router(entraineurs.router, prefix=API_PREFIX)
app.include_router(router_predictions, prefix=API_PREFIX)
app.include_router(router_hypotheses, prefix=API_PREFIX)
app.include_router(statistiques.router, prefix=API_PREFIX)
app.include_router(resultats.router, prefix=API_PREFIX)
app.include_router(sync.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


# ──────────────────────────────────────────────
# Routes de base
# ──────────────────────────────────────────────
@app.get("/health", tags=["Santé"], summary="Vérification de santé")
def health_check():
    """Endpoint de vérification — confirme que l'API est opérationnelle."""
    return {
        "status": "ok",
        "service": "HIPPO ANALYTICS",
        "version": "1.0.0",
        "source": "PMU Burkina Faso (LONAB)",
    }


@app.get("/", tags=["Accueil"])
def racine():
    """Redirection vers la documentation de l'API."""
    return JSONResponse(
        content={
            "bienvenue": "HIPPO ANALYTICS API",
            "documentation": "/api/docs",
            "version": "1.0.0",
        }
    )
