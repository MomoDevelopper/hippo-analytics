"""
Point d'entrée des routers FastAPI.
"""
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

__all__ = [
    "programmes",
    "courses",
    "chevaux",
    "jockeys",
    "entraineurs",
    "statistiques",
    "resultats",
    "sync",
    "admin",
]
