"""
Routes API — Résultats officiels des courses.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.arrivee import Arrivee
from app.models.course import Course
from app.models.pronostic import Pronostic

router = APIRouter(prefix="/resultats", tags=["Résultats"])


class EnregistrementArrivee(BaseModel):
    course_id: int
    classement_officiel: List[int]   # Liste ordonnée des cheval_ids (1er, 2ème, ...)
    classement_detaille: Optional[List[dict]] = None
    source: str = "officielle"
    saisi_par: Optional[str] = None


@router.post("/", summary="Enregistrer l'arrivée officielle d'une course")
def enregistrer_arrivee(data: EnregistrementArrivee, db: Session = Depends(get_db)):
    """
    Enregistre le résultat officiel d'une course.
    Verrouille automatiquement les pronostics existants (non modifiables rétroactivement).
    """
    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course introuvable")

    # Vérifier si une arrivée existe déjà
    arrivee_existante = db.query(Arrivee).filter(Arrivee.course_id == data.course_id).first()
    if arrivee_existante:
        raise HTTPException(
            status_code=409,
            detail="Une arrivée est déjà enregistrée pour cette course. Supprimez-la d'abord."
        )

    # Créer l'arrivée officielle
    arrivee = Arrivee(
        course_id=data.course_id,
        classement_officiel=data.classement_officiel,
        classement_detaille=data.classement_detaille,
        source=data.source,
        saisi_par=data.saisi_par,
    )
    db.add(arrivee)

    # Mettre à jour le statut de la course
    course.statut = "terminée"

    # Verrouiller tous les pronostics de cette course (intégrité des données)
    pronostics = db.query(Pronostic).filter(Pronostic.course_id == data.course_id).all()
    for pronostic in pronostics:
        pronostic.verrouille = True

    db.commit()

    return {
        "message": "Arrivée enregistrée avec succès",
        "course_id": data.course_id,
        "classement": data.classement_officiel,
        "pronostics_verrouilles": len(pronostics),
    }


@router.get("/{course_id}", summary="Résultat officiel d'une course")
def obtenir_resultat(course_id: int, db: Session = Depends(get_db)):
    arrivee = db.query(Arrivee).filter(Arrivee.course_id == course_id).first()
    if not arrivee:
        raise HTTPException(status_code=404, detail="Aucun résultat enregistré pour cette course")

    return {
        "course_id": course_id,
        "classement_officiel": arrivee.classement_officiel,
        "classement_detaille": arrivee.classement_detaille,
        "source": arrivee.source,
        "date_enregistrement": arrivee.date_enregistrement.isoformat(),
    }
