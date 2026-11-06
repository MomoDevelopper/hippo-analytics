"""
Routes API — Statistiques globales et classements.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.course import Course
from app.models.cheval import Cheval
from app.models.jockey import Jockey
from app.models.entraineur import Entraineur
from app.models.pronostic import Pronostic
from app.models.arrivee import Arrivee

router = APIRouter(prefix="/statistiques", tags=["Statistiques"])


@router.get("/", summary="Statistiques globales du système")
def statistiques_globales(db: Session = Depends(get_db)):
    """Retourne les statistiques générales de la plateforme."""
    total_courses = db.query(Course).count()
    total_terminees = db.query(Course).filter(Course.statut == "terminée").count()
    total_chevaux = db.query(Cheval).count()
    total_jockeys = db.query(Jockey).count()
    total_entraineurs = db.query(Entraineur).count()
    total_pronostics = db.query(Pronostic).count()

    # Précision du modèle : courses avec pronostic ET arrivée officielle
    courses_evaluables = (
        db.query(Pronostic)
        .join(Arrivee, Pronostic.course_id == Arrivee.course_id, isouter=True)
        .filter(Arrivee.id.isnot(None))
        .count()
    )

    return {
        "base_de_donnees": {
            "total_courses": total_courses,
            "courses_terminees": total_terminees,
            "total_chevaux": total_chevaux,
            "total_jockeys": total_jockeys,
            "total_entraineurs": total_entraineurs,
        },
        "moteur_prediction": {
            "pronostics_generes": total_pronostics,
            "courses_evaluables": courses_evaluables,
            "precision": "Données insuffisantes pour l'instant" if courses_evaluables < 10 else "Calculée",
        },
    }


@router.get("/modele", summary="Performance du modèle de prédiction")
def performance_modele(
    periode_jours: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Analyse la précision des prédictions sur une période donnée."""
    date_limite = date.today() - timedelta(days=periode_jours)

    pronostics = (
        db.query(Pronostic)
        .filter(Pronostic.date_generation >= date_limite)
        .all()
    )

    evaluations = []
    for p in pronostics:
        arrivee = (
            db.query(Arrivee)
            .filter(Arrivee.course_id == p.course_id)
            .first()
        )
        if not arrivee or not arrivee.classement_officiel:
            continue

        top5_reel = arrivee.classement_officiel[:5]
        top5_predit = p.top5_predit or []

        gagnant_ok = len(top5_reel) > 0 and len(top5_predit) > 0 and top5_reel[0] == top5_predit[0]
        top5_identiques = set(top5_reel) == set(top5_predit)
        ordre_exact = top5_reel == top5_predit
        nb_communs = len(set(top5_reel) & set(top5_predit))

        evaluations.append({
            "course_id": p.course_id,
            "gagnant_predit": gagnant_ok,
            "top5_complet_trouve": top5_identiques,
            "ordre_exact": ordre_exact,
            "chevaux_communs": nb_communs,
        })

    if not evaluations:
        return {"message": "Pas encore assez de données pour évaluer le modèle"}

    n = len(evaluations)
    return {
        "periode_jours": periode_jours,
        "courses_evaluees": n,
        "taux_gagnant_predit": round(sum(e["gagnant_predit"] for e in evaluations) / n * 100, 1),
        "taux_top5_complet": round(sum(e["top5_complet_trouve"] for e in evaluations) / n * 100, 1),
        "taux_ordre_exact": round(sum(e["ordre_exact"] for e in evaluations) / n * 100, 1),
        "moyenne_chevaux_communs": round(sum(e["chevaux_communs"] for e in evaluations) / n, 2),
    }
