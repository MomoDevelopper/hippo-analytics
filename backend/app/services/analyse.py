"""
Moteur de scoring statistique des chevaux.

Ce service calcule les notes (0 à 100) de chaque partant
en analysant ses performances passées, son jockey, son entraîneur
et l'adéquation avec les conditions de la course.
"""
import logging
from typing import Optional
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.cheval import Cheval
from app.models.partant import Partant
from app.models.performance import Performance
from app.models.jockey import Jockey
from app.models.entraineur import Entraineur
from app.models.evaluation import Evaluation

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Coefficients de pondération des sous-notes
# (modifiables par l'administrateur dans les paramètres)
# ──────────────────────────────────────────────
COEFFICIENTS = {
    "forme": 0.30,          # Performances récentes (5 dernières sorties)
    "distance": 0.20,       # Adéquation à la distance de la course
    "jockey": 0.20,         # Statistiques du jockey
    "entraineur": 0.15,     # Statistiques de l'entraîneur
    "regularite": 0.15,     # Régularité des résultats
}


def _note_forme(performances: list[Performance], nb_sorties: int = 5) -> float:
    """
    Calcule la note de forme à partir des dernières sorties.
    Donne plus de poids aux sorties les plus récentes.

    Args:
        performances: Liste des performances triées par date (plus récente en premier)
        nb_sorties: Nombre de sorties à analyser

    Returns:
        Note de forme entre 0 et 100
    """
    if not performances:
        return 50.0  # Note neutre par défaut

    recentes = performances[:nb_sorties]
    total_partants_moyen = max(1, sum(p.partants_total or 10 for p in recentes) / len(recentes))

    note = 0.0
    poids_total = 0.0

    for i, perf in enumerate(recentes):
        # Poids décroissant : plus récent = plus important
        poids = 1.0 / (i + 1)
        poids_total += poids

        place = perf.place_officielle
        if place is None:
            note += 50.0 * poids
            continue

        # Conversion place → note (1er = 100, dernier = 0)
        n_partants = perf.partants_total or 10
        score_place = max(0.0, 100.0 * (1 - (place - 1) / n_partants))

        # Bonus victoire
        if place == 1:
            score_place = min(100.0, score_place * 1.1)
        # Bonus place (top 3)
        elif place <= 3:
            score_place = min(100.0, score_place * 1.05)

        note += score_place * poids

    return round(note / poids_total if poids_total > 0 else 50.0, 2)


def _note_distance(performances: list[Performance], distance_course: Optional[int]) -> float:
    """
    Calcule l'adéquation du cheval à la distance de la course.

    Args:
        performances: Historique des performances
        distance_course: Distance de la course en mètres

    Returns:
        Note de distance entre 0 et 100
    """
    if not performances or not distance_course:
        return 50.0

    perf_meme_distance = [
        p for p in performances
        if p.distance and abs(p.distance - distance_course) <= 200
    ]

    if not perf_meme_distance:
        return 50.0

    places = [p.place_officielle for p in perf_meme_distance if p.place_officielle]
    if not places:
        return 50.0

    victoires = sum(1 for p in places if p == 1)
    places_top3 = sum(1 for p in places if p <= 3)

    taux_victoire = victoires / len(places) * 100
    taux_top3 = places_top3 / len(places) * 100

    return round((taux_victoire * 0.6) + (taux_top3 * 0.4), 2)


def _note_jockey(jockey: Optional[Jockey], db: Session, nb_jours: int = 90) -> float:
    """
    Calcule la note du jockey basée sur ses statistiques récentes.

    Args:
        jockey: Instance du jockey
        db: Session de base de données
        nb_jours: Période d'analyse en jours

    Returns:
        Note du jockey entre 0 et 100
    """
    if not jockey:
        return 50.0

    date_limite = date.today() - timedelta(days=nb_jours)
    performances = (
        db.query(Performance)
        .filter(
            Performance.jockey_id == jockey.id,
            Performance.date_course >= date_limite,
        )
        .all()
    )

    if not performances:
        return 50.0

    total = len(performances)
    victoires = sum(1 for p in performances if p.place_officielle == 1)
    top3 = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 3)

    taux_victoire = victoires / total * 100
    taux_top3 = top3 / total * 100

    note = (taux_victoire * 0.7) + (taux_top3 * 0.3)
    # Normalisation : un taux de victoire de 30% = note de 100
    return round(min(100.0, note * (100 / 30)), 2)


def _note_entraineur(entraineur: Optional[Entraineur], db: Session, nb_jours: int = 90) -> float:
    """
    Calcule la note de l'entraîneur basée sur ses statistiques récentes.

    Args:
        entraineur: Instance de l'entraîneur
        db: Session de base de données
        nb_jours: Période d'analyse en jours

    Returns:
        Note de l'entraîneur entre 0 et 100
    """
    if not entraineur:
        return 50.0

    # Récupérer les performances de tous les chevaux de l'entraîneur
    date_limite = date.today() - timedelta(days=nb_jours)
    performances = (
        db.query(Performance)
        .join(Cheval, Performance.cheval_id == Cheval.id)
        .filter(
            Cheval.entraineur_id == entraineur.id,
            Performance.date_course >= date_limite,
        )
        .all()
    )

    if not performances:
        return 50.0

    total = len(performances)
    victoires = sum(1 for p in performances if p.place_officielle == 1)
    classes = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 5)

    taux_victoire = victoires / total * 100
    taux_classes = classes / total * 100

    note = (taux_victoire * 0.6) + (taux_classes * 0.4)
    return round(min(100.0, note * (100 / 25)), 2)


def _note_regularite(performances: list[Performance]) -> float:
    """
    Calcule la régularité du cheval (variance des résultats).
    Un cheval régulier a des performances stables.

    Args:
        performances: Historique des performances

    Returns:
        Note de régularité entre 0 et 100
    """
    if len(performances) < 3:
        return 50.0

    import math

    places = [p.place_officielle for p in performances[:10] if p.place_officielle]
    if len(places) < 3:
        return 50.0

    moyenne = sum(places) / len(places)
    variance = sum((p - moyenne) ** 2 for p in places) / len(places)
    ecart_type = math.sqrt(variance)

    # Faible écart-type = grande régularité = note élevée
    # Calibration : écart-type de 0 → note 100, de 5+ → note 20
    note = max(20.0, 100.0 - (ecart_type * 16))
    return round(note, 2)


def calculer_note_cheval(
    partant: Partant,
    distance_course: Optional[int],
    db: Session,
    coefficients: Optional[dict] = None,
) -> dict:
    """
    Calcule la note globale d'un partant pour une course donnée.

    Args:
        partant: Instance du partant
        distance_course: Distance de la course en mètres
        db: Session de base de données
        coefficients: Coefficients personnalisés (optionnel)

    Returns:
        Dictionnaire avec toutes les notes et la note globale
    """
    coefs = coefficients or COEFFICIENTS
    cheval = partant.cheval

    # Récupérer l'historique des performances (triées par date décroissante)
    performances = (
        db.query(Performance)
        .filter(Performance.cheval_id == cheval.id)
        .order_by(Performance.date_course.desc())
        .limit(20)
        .all()
    )

    # Calcul des sous-scores
    forme = _note_forme(performances)
    distance = _note_distance(performances, distance_course)
    jockey = _note_jockey(partant.jockey, db)
    entraineur = _note_entraineur(cheval.entraineur, db)
    regularite = _note_regularite(performances)

    # Note globale pondérée
    note_globale = (
        forme * coefs["forme"]
        + distance * coefs["distance"]
        + jockey * coefs["jockey"]
        + entraineur * coefs["entraineur"]
        + regularite * coefs["regularite"]
    )
    note_globale = round(min(100.0, max(0.0, note_globale)), 2)

    return {
        "note_globale": note_globale,
        "note_forme": forme,
        "note_distance": distance,
        "note_jockey": jockey,
        "note_entraineur": entraineur,
        "note_regularite": regularite,
        "note_cote": 50.0,  # Calculé séparément avec les cotes
        "nb_performances": len(performances),
    }


def detecter_categorie(note_globale: float, cote: Optional[float]) -> str:
    """
    Classe le cheval dans l'une des quatre catégories analytiques.

    Catégories :
    - favori_stat    : Meilleure note statistique calculée
    - favori_cote    : Cheval fortement soutenu par le marché (petite cote)
    - outsider       : Note statistique supérieure à ce que suggère sa cote
    - risque         : Indicateurs défavorables ou données insuffisantes

    Args:
        note_globale: Note statistique du cheval (0-100)
        cote: Cote de départ du cheval (plus petite = plus favori)

    Returns:
        Catégorie sous forme de chaîne
    """
    if cote is not None and cote <= 3.0:
        # Favori des cotes = cote ≤ 3
        return "favori_cote"
    elif note_globale >= 75:
        return "favori_stat"
    elif cote is not None and cote >= 10 and note_globale >= 60:
        # Outsider intéressant : grosse cote mais bonne note statistique
        return "outsider"
    elif note_globale < 40:
        return "risque"
    else:
        return "outsider"
