"""
Service d'entraînement et d'optimisation du modèle XGBoost.

Phase 4 — Apprentissage supervisé sur les données historiques.
Le modèle apprend à prédire la place d'un cheval à partir de ses features,
puis améliore les probabilités de la simulation Monte Carlo.
"""
import logging
import pickle
from pathlib import Path
from typing import Optional
from datetime import date, timedelta

import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Chemin de sauvegarde du modèle entraîné
MODEL_PATH = Path("./models/xgboost_hippo.pkl")
FEATURES_PATH = Path("./models/feature_names.pkl")


def construire_features(partant_id: int, db: Session) -> Optional[np.ndarray]:
    """
    Construit le vecteur de features pour un partant donné.

    Features utilisées :
    - Performances récentes (5 dernières sorties)
    - Stats jockey 90 jours
    - Stats entraîneur 90 jours
    - Distance de la course vs distances habituelles
    - Cote de départ (si disponible)

    Args:
        partant_id: ID du partant
        db: Session de base de données

    Returns:
        Vecteur numpy de features, ou None si données insuffisantes
    """
    from app.models.partant import Partant
    from app.models.performance import Performance
    from app.models.cheval import Cheval
    from app.models.jockey import Jockey

    partant = db.query(Partant).filter(Partant.id == partant_id).first()
    if not partant:
        return None

    cheval = partant.cheval
    course = partant.course

    # ── Performances récentes du cheval
    perfs = (
        db.query(Performance)
        .filter(Performance.cheval_id == cheval.id)
        .order_by(Performance.date_course.desc())
        .limit(10)
        .all()
    )

    # Feature : place moyenne sur les 5 dernières
    places_5 = [p.place_officielle for p in perfs[:5] if p.place_officielle]
    place_moy_5 = np.mean(places_5) if places_5 else 8.0
    place_min_5 = min(places_5) if places_5 else 10
    victoires_5 = sum(1 for p in places_5 if p == 1)
    top3_5 = sum(1 for p in places_5 if p <= 3)

    # Feature : performances à la distance
    dist = course.distance or 2000
    perfs_dist = [
        p for p in perfs
        if p.distance and abs(p.distance - dist) <= 300
    ]
    places_dist = [p.place_officielle for p in perfs_dist if p.place_officielle]
    place_moy_dist = np.mean(places_dist) if places_dist else place_moy_5
    nb_courses_dist = len(perfs_dist)

    # Feature : cote de départ
    cote = partant.cote_depart or 10.0

    # Feature : stats jockey (90 jours)
    jockey_victoires, jockey_courses = 0, 0
    if partant.jockey:
        date_limite = date.today() - timedelta(days=90)
        jockey_perfs = (
            db.query(Performance)
            .filter(
                Performance.jockey_id == partant.jockey_id,
                Performance.date_course >= date_limite,
            )
            .all()
        )
        jockey_courses = len(jockey_perfs)
        jockey_victoires = sum(1 for p in jockey_perfs if p.place_officielle == 1)

    jockey_taux = jockey_victoires / jockey_courses if jockey_courses > 0 else 0.0

    # Feature : stats entraîneur (90 jours)
    entraineur_taux = 0.0
    if cheval.entraineur_id:
        from app.models.cheval import Cheval as ChevalModel
        date_limite = date.today() - timedelta(days=90)
        entraineur_perfs = (
            db.query(Performance)
            .join(ChevalModel, Performance.cheval_id == ChevalModel.id)
            .filter(
                ChevalModel.entraineur_id == cheval.entraineur_id,
                Performance.date_course >= date_limite,
            )
            .all()
        )
        if entraineur_perfs:
            victoires_e = sum(1 for p in entraineur_perfs if p.place_officielle == 1)
            entraineur_taux = victoires_e / len(entraineur_perfs)

    # Feature : régularité (écart-type des places)
    if len(places_5) >= 3:
        regularite = 1.0 / (1.0 + np.std(places_5))
    else:
        regularite = 0.5

    # Vecteur de features final
    features = np.array([
        place_moy_5,           # Place moyenne 5 dernières sorties
        place_min_5,           # Meilleure place récente
        float(victoires_5),    # Nombre de victoires récentes
        float(top3_5),         # Nombre de top 3 récents
        place_moy_dist,        # Place moyenne à la distance
        float(nb_courses_dist),# Nombre de courses à la distance
        cote,                  # Cote de départ
        jockey_taux,           # Taux victoire jockey
        float(jockey_courses), # Expérience jockey
        entraineur_taux,       # Taux victoire entraîneur
        regularite,            # Régularité
        float(len(perfs)),     # Nombre total de sorties historiques
    ], dtype=float)

    return features


FEATURE_NAMES = [
    "place_moy_5",
    "place_min_5",
    "victoires_5",
    "top3_5",
    "place_moy_dist",
    "nb_courses_dist",
    "cote",
    "jockey_taux_victoire",
    "jockey_nb_courses",
    "entraineur_taux_victoire",
    "regularite",
    "nb_sorties_total",
]


def entrainer_modele(db: Session, nb_jours_historique: int = 365) -> dict:
    """
    Entraîne le modèle XGBoost sur les données historiques.

    Principe :
    - Pour chaque course terminée avec arrivée officielle,
      construire les features de chaque partant + sa place réelle
    - Entraîner XGBoost à prédire la place (régression ordonnée)

    Args:
        db: Session de base de données
        nb_jours_historique: Période d'apprentissage en jours

    Returns:
        Métriques d'entraînement
    """
    try:
        from xgboost import XGBRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error
    except ImportError:
        return {"erreur": "XGBoost ou scikit-learn non installé"}

    from app.models.arrivee import Arrivee
    from app.models.course import Course
    from app.models.partant import Partant
    from app.models.performance import Performance

    logger.info("Démarrage de l'entraînement XGBoost...")

    date_limite = date.today() - timedelta(days=nb_jours_historique)

    # Récupérer les courses terminées avec arrivée officielle
    # Note: "terminée" avec accent peut poser problème en SQLite → utiliser LIKE ou les deux formes
    courses_avec_arrivee = (
        db.query(Course)
        .join(Arrivee, Course.id == Arrivee.course_id)
        .filter(
            Course.date_course >= date_limite,
        )
        .all()
    )

    if len(courses_avec_arrivee) < 10:
        return {
            "message": f"Données insuffisantes : {len(courses_avec_arrivee)} course(s) avec résultat. "
                       "Minimum recommandé : 50 courses."
        }

    X_liste, y_liste = [], []
    courses_utilisees = 0

    for course in courses_avec_arrivee:
        arrivee = db.query(Arrivee).filter(Arrivee.course_id == course.id).first()
        if not arrivee or not arrivee.classement_officiel:
            continue

        # Créer un mapping cheval_id → place réelle
        classement = arrivee.classement_officiel
        place_par_cheval = {cheval_id: rang + 1 for rang, cheval_id in enumerate(classement)}

        partants = (
            db.query(Partant)
            .filter(Partant.course_id == course.id, Partant.non_partant == False)
            .all()
        )

        for partant in partants:
            place_reelle = place_par_cheval.get(partant.cheval_id)
            if not place_reelle:
                continue

            features = construire_features(partant.id, db)
            if features is not None:
                X_liste.append(features)
                y_liste.append(float(place_reelle))

        courses_utilisees += 1

    if len(X_liste) < 50:
        return {
            "message": f"Trop peu de données d'entraînement ({len(X_liste)} exemples). "
                       "Enrichissez d'abord la base de données historiques."
        }

    X = np.array(X_liste)
    y = np.array(y_liste)

    # Division train / test (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraînement XGBoost
    modele = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    modele.fit(X_train, y_train)

    # Évaluation
    y_pred = modele.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    # Sauvegarde du modèle
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(modele, f)
    with open(FEATURES_PATH, "wb") as f:
        pickle.dump(FEATURE_NAMES, f)

    logger.info(f"Modèle XGBoost entraîné — MAE: {mae:.2f} places")

    return {
        "succes": True,
        "statut": "entraîné",
        "nb_courses": courses_utilisees,
        "nb_partants": len(X_liste),
        "precision_top1": float(sum(1 for a, b in zip(y_test, y_pred) if round(b) == round(a)) / max(1, len(y_test))),
        "precision_top3": float(sum(1 for a, b in zip(y_test, y_pred) if b <= 3) / max(1, len(y_test))),
        "precision_top5": float(sum(1 for a, b in zip(y_test, y_pred) if b <= 5) / max(1, len(y_test))),
        "mae_places": round(mae, 3),
        "chemin_modele": str(MODEL_PATH),
    }


def predire_avec_xgboost(partant_ids: list[int], db: Session) -> dict[int, float]:
    """
    Utilise le modèle XGBoost entraîné pour prédire la place de chaque partant.

    Args:
        partant_ids: Liste des IDs de partants de la course
        db: Session de base de données

    Returns:
        {partant_id: place_predite_xgboost}
    """
    if not MODEL_PATH.exists():
        logger.warning("Modèle XGBoost non disponible — utilisation du scoring statistique seul")
        return {}

    try:
        with open(MODEL_PATH, "rb") as f:
            modele = pickle.load(f)
    except Exception as e:
        logger.error(f"Impossible de charger le modèle XGBoost : {e}")
        return {}

    resultats = {}
    for partant_id in partant_ids:
        features = construire_features(partant_id, db)
        if features is not None:
            place_predite = float(modele.predict(features.reshape(1, -1))[0])
            resultats[partant_id] = max(1.0, round(place_predite, 2))

    return resultats
