"""
Routes API — Prédictions et hypothèses.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pronostic import Pronostic
from app.models.course import Course
from app.services.prediction import predire_course

router_predictions = APIRouter(prefix="/predictions", tags=["Prédictions"])
router_hypotheses = APIRouter(prefix="/hypotheses", tags=["Hypothèses"])


# ────────── Prédictions ──────────

@router_predictions.post("/{course_id}", summary="Lancer une prédiction")
def lancer_prediction(
    course_id: int,
    n_simulations: int = Query(100_000, ge=1000, le=500_000, description="Nombre de simulations Monte Carlo"),
    db: Session = Depends(get_db),
):
    """
    Lance le moteur de prédiction complet pour une course.
    Calcule les notes de chaque partant et simule N arrivées.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course introuvable")

    try:
        resultat = predire_course(course_id=course_id, db=db, n_runs=n_simulations)

        # Sauvegarder le pronostic en base
        pronostic = Pronostic(
            course_id=course_id,
            top5_predit=resultat["top5_predit"],
            ordre_predit=[ev["cheval_id"] for ev in resultat["classement"]],
            probabilites={
                str(ev["cheval_id"]): ev.get("probabilite_victoire", 0)
                for ev in resultat["classement"]
            },
            top_hypotheses=resultat["top_hypotheses"][:50],
            methode_utilisee=resultat["methode"],
            version_modele="1.0.0",
        )
        db.add(pronostic)
        db.commit()

        return {
            "message": "Prédiction générée avec succès",
            "course_id": course_id,
            "pronostic_id": pronostic.id,
            "simulations": n_simulations,
            "top5_predit": resultat["top5_predit"],
            "classement": resultat["classement"],
            "methode": resultat["methode"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {e}")


@router_predictions.get("/{course_id}", summary="Dernière prédiction d'une course")
def obtenir_prediction(course_id: int, db: Session = Depends(get_db)):
    pronostic = (
        db.query(Pronostic)
        .filter(Pronostic.course_id == course_id)
        .order_by(Pronostic.date_generation.desc())
        .first()
    )
    if not pronostic:
        raise HTTPException(
            status_code=404,
            detail="Aucune prédiction disponible pour cette course. Lancez d'abord POST /predictions/{id}"
        )
    return {
        "course_id": course_id,
        "pronostic_id": pronostic.id,
        "date_generation": pronostic.date_generation.isoformat(),
        "top5_predit": pronostic.top5_predit,
        "probabilites": pronostic.probabilites,
        "verrouille": pronostic.verrouille,
        "methode": pronostic.methode_utilisee,
    }


# ────────── Hypothèses ──────────

@router_hypotheses.get("/{course_id}", summary="Hypothèses d'une course")
def obtenir_hypotheses(
    course_id: int,
    top: int = Query(50, ge=1, le=524160, description="Nombre d'hypothèses à retourner"),
    db: Session = Depends(get_db),
):
    """
    Retourne les hypothèses de classement des 5 premiers,
    triées par probabilité décroissante.
    """
    pronostic = (
        db.query(Pronostic)
        .filter(Pronostic.course_id == course_id)
        .order_by(Pronostic.date_generation.desc())
        .first()
    )
    if not pronostic or not pronostic.top_hypotheses:
        raise HTTPException(
            status_code=404,
            detail="Aucune hypothèse disponible. Lancez d'abord POST /predictions/{id}"
        )

    hypotheses = pronostic.top_hypotheses
    return {
        "course_id": course_id,
        "total_hypotheses_calculees": len(hypotheses),
        "affichees": min(top, len(hypotheses)),
        "hypotheses": hypotheses[:top],
    }


@router_hypotheses.get("/{course_id}/top", summary="Top 50 hypothèses")
def top_hypotheses(course_id: int, db: Session = Depends(get_db)):
    """Retourne les 50 hypothèses les plus probables."""
    return obtenir_hypotheses(course_id=course_id, top=50, db=db)
