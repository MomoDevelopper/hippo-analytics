"""
Configuration globale de HIPPO ANALYTICS.
Charge les paramètres depuis les variables d'environnement ou le fichier .env
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str = "postgresql://hippo_user:hippo_pass@localhost:5432/hippo_analytics"

    # Sécurité
    SECRET_KEY: str = "changeme_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Source LONAB / PMU Burkina Faso
    LONAB_BASE_URL: str = "https://lonab.bf"
    LONAB_PMU_PATH: str = "/programmes-pmub"

    # Synchronisation autonome
    SYNC_INTERVAL_HOURS: int = 6

    # Paramètres du moteur de prédiction
    MAX_HORSES_PER_RACE: int = 20
    SIMULATION_RUNS: int = 100_000
    TOP_HYPOTHESES: int = 50

    # Fichiers
    UPLOAD_DIR: str = "./uploads"
    MAX_PDF_SIZE_MB: int = 20

    # Mode debug
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance unique des paramètres (mise en cache)."""
    return Settings()
