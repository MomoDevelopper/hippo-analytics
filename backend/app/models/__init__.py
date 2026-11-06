"""
Point d'entrée des modèles ORM.
Importer ce module force l'enregistrement de tous les modèles dans SQLAlchemy Base.
"""
from app.models.entraineur import Entraineur
from app.models.jockey import Jockey
from app.models.cheval import Cheval
from app.models.course import Course
from app.models.partant import Partant
from app.models.performance import Performance
from app.models.evaluation import Evaluation
from app.models.pronostic import Pronostic
from app.models.arrivee import Arrivee

# Liste de tous les modèles pour les migrations Alembic
__all_models__ = [
    Entraineur,
    Jockey,
    Cheval,
    Course,
    Partant,
    Performance,
    Evaluation,
    Pronostic,
    Arrivee,
]

__all__ = [
    "Entraineur",
    "Jockey",
    "Cheval",
    "Course",
    "Partant",
    "Performance",
    "Evaluation",
    "Pronostic",
    "Arrivee",
]
