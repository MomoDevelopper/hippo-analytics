"""
Connexion à la base de données via SQLAlchemy 2.0.
Supporte PostgreSQL (production) et SQLite (tests locaux).
Fournit la session de base de données et la classe de base ORM.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase


def _build_engine():
    """
    Construit le moteur SQLAlchemy selon la DATABASE_URL courante.
    Appelé à la demande pour respecter les variables d'env configurées dynamiquement.
    """
    # Lire la DATABASE_URL directement depuis os.environ (priorité sur .env)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        try:
            from app.config import get_settings
            database_url = get_settings().DATABASE_URL
        except Exception:
            database_url = "sqlite:///./hippo_analytics.db"

    is_sqlite = database_url.startswith("sqlite")

    if is_sqlite:
        # SQLite : pas de pool_size/max_overflow, connect_args pour le thread
        eng = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=os.environ.get("DEBUG", "false").lower() == "true",
        )
        # Activer les clés étrangères sur SQLite
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        eng = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=os.environ.get("DEBUG", "false").lower() == "true",
        )
    return eng


# Moteur et session initialisés au premier usage
_engine = None
_SessionLocal = None


def _get_engine():
    """Retourne l'engine, en le créant si nécessaire."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def _get_session_local():
    """Retourne le SessionLocal, en le créant si nécessaire."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


# Proxy pour maintenir la compatibilité avec le code existant
class _EngineProxy:
    def __getattr__(self, name):
        return getattr(_get_engine(), name)


engine = _EngineProxy()


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles ORM."""
    pass


def get_db():
    """
    Générateur de session de base de données.
    Utilisé comme dépendance FastAPI (Depends).
    Ferme automatiquement la session après chaque requête.
    """
    SessionLocal = _get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_engine():
    """Réinitialise l'engine (utile pour les tests)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None


def create_tables():
    """Crée toutes les tables en base de données si elles n'existent pas."""
    # Réinitialiser l'engine pour prendre en compte les nouvelles variables d'env
    reset_engine()
    # Importer tous les modèles pour qu'ils soient enregistrés dans Base
    from app.models import __all_models__  # noqa: F401
    Base.metadata.create_all(bind=_get_engine())
