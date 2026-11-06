"""
Moteur de prédiction et simulation Monte Carlo.

Ce module combine trois méthodes complémentaires :
  1. Modèle statistique   — scoring pondéré de chaque partant
  2. Modèle Plackett-Luce — probabilités de classement ordonnés
  3. Simulation Monte Carlo — 100 000 arrivées simulées → top hypothèses
"""
import logging
import random
from collections import Counter, defaultdict
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.partant import Partant
from app.models.evaluation import Evaluation
from app.services.analyse import calculer_note_cheval, detecter_categorie
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ──────────────────────────────────────────────────────────
# 1. Normalisation des notes → probabilités de victoire
# ──────────────────────────────────────────────────────────

def normaliser_probabilites(notes: dict[int, float]) -> dict[int, float]:
    """
    Convertit les notes brutes (0-100) en probabilités de victoire
    qui somment à 1.0 (100%).

    Utilise une transformation softmax pour amplifier les écarts
    entre les chevaux.

    Args:
        notes: {cheval_id: note_globale}

    Returns:
        {cheval_id: probabilite_victoire}
    """
    if not notes:
        return {}

    ids = list(notes.keys())
    valeurs = np.array([notes[i] for i in ids], dtype=float)

    # Softmax avec température (τ=15 → différencie bien les chevaux)
    temperature = 15.0
    exp_vals = np.exp((valeurs - valeurs.max()) / temperature)
    probas = exp_vals / exp_vals.sum()

    return {ids[i]: round(float(probas[i]), 6) for i in range(len(ids))}


# ──────────────────────────────────────────────────────────
# 2. Simulation Monte Carlo (Plackett-Luce)
# ──────────────────────────────────────────────────────────

def simulation_monte_carlo(
    probabilites: dict[int, float],
    n_runs: int = 100_000,
    top_n: int = 5,
) -> list[dict]:
    """
    Simule N arrivées de course selon le modèle Plackett-Luce.

    Principe Plackett-Luce :
      - Pour choisir le 1er → tirage pondéré par les probabilités
      - Pour choisir le 2ème → tirage sur les restants (re-normalisation)
      - Et ainsi de suite jusqu'au 5ème rang

    Args:
        probabilites: {cheval_id: probabilite_victoire}
        n_runs: Nombre de simulations (défaut : 100 000)
        top_n: Nombre de positions à simuler (défaut : 5)

    Returns:
        Liste des top hypothèses triées par probabilité décroissante,
        chacune sous la forme :
        {"ordre": [id1, id2, id3, id4, id5], "probabilite": 0.0085, "rang": 1}
    """
    if len(probabilites) < top_n:
        logger.warning(
            f"Seulement {len(probabilites)} partants pour simuler {top_n} positions"
        )
        top_n = len(probabilites)

    ids = list(probabilites.keys())
    poids = np.array([probabilites[i] for i in ids], dtype=float)

    # Compteur des ordres observés
    compteur: Counter = Counter()

    logger.info(f"Démarrage simulation Monte Carlo : {n_runs:,} runs, {len(ids)} partants")

    for _ in range(n_runs):
        poids_courants = poids.copy()
        ordre = []

        for position in range(top_n):
            total = poids_courants.sum()
            if total <= 0:
                break

            # Tirage pondéré
            probas_norm = poids_courants / total
            index_choisi = np.random.choice(len(ids), p=probas_norm)

            ordre.append(ids[index_choisi])
            poids_courants[index_choisi] = 0.0  # Retirer le cheval choisi

        if len(ordre) == top_n:
            compteur[tuple(ordre)] += 1

    # Conversion en liste triée par fréquence décroissante
    total_valide = sum(compteur.values())
    resultats = []

    for rang, (ordre, count) in enumerate(compteur.most_common(settings.TOP_HYPOTHESES), start=1):
        resultats.append(
            {
                "rang": rang,
                "ordre": list(ordre),
                "probabilite": round(count / total_valide, 6),
                "occurrences": count,
            }
        )

    logger.info(
        f"Simulation terminée : {len(compteur):,} ordres distincts sur {n_runs:,} runs"
    )
    return resultats


# ──────────────────────────────────────────────────────────
# 3. Fonction principale de prédiction
# ──────────────────────────────────────────────────────────

def predire_course(course_id: int, db: Session, n_runs: Optional[int] = None) -> dict:
    """
    Lance une prédiction complète pour une course donnée.

    Étapes :
      1. Récupérer les partants de la course
      2. Calculer la note de chaque partant
      3. Normaliser en probabilités de victoire
      4. Simulation Monte Carlo → top 50 hypothèses
      5. Sauvegarder les évaluations en base de données

    Args:
        course_id: Identifiant de la course
        db: Session de base de données
        n_runs: Nombre de simulations (défaut depuis config)

    Returns:
        Résultat complet de la prédiction
    """
    n_simulations = n_runs or settings.SIMULATION_RUNS

    # Récupérer la course et ses partants actifs
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError(f"Course introuvable : id={course_id}")

    partants = (
        db.query(Partant)
        .filter(
            Partant.course_id == course_id,
            Partant.non_partant == False,
        )
        .all()
    )

    if not partants:
        raise ValueError(f"Aucun partant trouvé pour la course {course_id}")

    logger.info(
        f"Prédiction course {course_id} : {len(partants)} partants, "
        f"{n_simulations:,} simulations"
    )

    # Calcul des notes et évaluations
    evaluations_par_partant = {}
    notes_brutes = {}

    for partant in partants:
        notes = calculer_note_cheval(
            partant=partant,
            distance_course=course.distance,
            db=db,
        )
        evaluations_par_partant[partant.id] = {
            "partant_id": partant.id,
            "cheval_id": partant.cheval_id,
            "numero": partant.numero_partant,
            "nom_cheval": partant.cheval.nom if partant.cheval else f"Cheval #{partant.cheval_id}",
            **notes,
            "categorie": detecter_categorie(notes["note_globale"], partant.cote_depart),
        }
        notes_brutes[partant.cheval_id] = notes["note_globale"]

        # Sauvegarder / mettre à jour l'évaluation en base
        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.partant_id == partant.id)
            .first()
        )
        if not evaluation:
            evaluation = Evaluation(
                partant_id=partant.id,
                course_id=course_id,
                cheval_id=partant.cheval_id,
            )
            db.add(evaluation)

        evaluation.note_globale = notes["note_globale"]
        evaluation.note_forme = notes["note_forme"]
        evaluation.note_distance = notes["note_distance"]
        evaluation.note_jockey = notes["note_jockey"]
        evaluation.note_entraineur = notes["note_entraineur"]
        evaluation.note_regularite = notes["note_regularite"]
        evaluation.categorie = evaluations_par_partant[partant.id]["categorie"]

    db.commit()

    # Normalisation → probabilités de victoire
    probabilites = normaliser_probabilites(notes_brutes)

    # Mise à jour des probabilités de victoire dans les évaluations
    for partant in partants:
        prob_victoire = probabilites.get(partant.cheval_id, 0.0)
        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.partant_id == partant.id)
            .first()
        )
        if evaluation:
            evaluation.probabilite_victoire = round(prob_victoire * 100, 4)

        if partant.id in evaluations_par_partant:
            evaluations_par_partant[partant.id]["probabilite_victoire"] = round(
                prob_victoire * 100, 4
            )

    db.commit()

    # Simulation Monte Carlo
    top_hypotheses = simulation_monte_carlo(
        probabilites=probabilites,
        n_runs=n_simulations,
    )

    # Top 5 prédit = ordre de la meilleure hypothèse
    top5_cheval_ids = top_hypotheses[0]["ordre"] if top_hypotheses else []

    # Construire le classement trié par probabilité de victoire décroissante
    classement = sorted(
        evaluations_par_partant.values(),
        key=lambda e: e.get("probabilite_victoire", 0),
        reverse=True,
    )
    for rang, ev in enumerate(classement, start=1):
        ev["rang_predit"] = rang

    logger.info(
        f"Prédiction terminée — Top 5 prédit : "
        f"{[evaluations_par_partant.get(pid, {}).get('nom_cheval', str(pid)) for pid in top5_cheval_ids]}"
    )

    return {
        "course_id": course_id,
        "nombre_partants": len(partants),
        "nombre_simulations": n_simulations,
        "top5_predit": top5_cheval_ids,
        "classement": classement,
        "top_hypotheses": top_hypotheses[:50],
        "methode": "statistique + Monte Carlo (Plackett-Luce)",
    }
