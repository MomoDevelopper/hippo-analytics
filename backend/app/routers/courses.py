"""
Routes API — Courses hippiques.
"""
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.course import Course
from app.models.partant import Partant

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", summary="Liste des courses")
def lister_courses(
    date_course: Optional[date] = Query(None),
    statut: Optional[str] = Query(None, description="programmée | en_cours | terminée | annulée"),
    hippodrome: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retourne la liste des courses avec filtres optionnels."""
    query = db.query(Course)
    if date_course:
        query = query.filter(Course.date_course == date_course)
    if statut:
        query = query.filter(Course.statut == statut)
    if hippodrome:
        query = query.filter(Course.hippodrome.ilike(f"%{hippodrome}%"))

    courses = query.order_by(Course.date_course.desc(), Course.numero_course).limit(limit).all()

    return {
        "courses": [
            {
                "id": c.id,
                "date": str(c.date_course),
                "reunion": c.reunion,
                "numero": c.numero_course,
                "hippodrome": c.hippodrome,
                "distance": c.distance,
                "statut": c.statut,
                "partants": c.nombre_partants,
            }
            for c in courses
        ],
        "total": len(courses),
    }


@router.get("/{course_id}", summary="Détail d'une course")
def detail_course(course_id: int, db: Session = Depends(get_db)):
    """Retourne les détails d'une course avec ses partants."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course introuvable")

    partants = (
        db.query(Partant)
        .filter(Partant.course_id == course_id)
        .order_by(Partant.numero_partant)
        .all()
    )

    return {
        "id": course.id,
        "date": str(course.date_course),
        "reunion": course.reunion,
        "numero": course.numero_course,
        "hippodrome": course.hippodrome,
        "distance": course.distance,
        "type_piste": course.type_piste,
        "conditions": course.conditions,
        "statut": course.statut,
        "partants": [
            {
                "id": p.id,
                "numero": p.numero_partant,
                "cheval": p.cheval.nom if p.cheval else None,
                "jockey": f"{p.jockey.prenom} {p.jockey.nom}" if p.jockey else None,
                "entraineur": (
                    f"{p.cheval.entraineur.prenom} {p.cheval.entraineur.nom}"
                    if p.cheval and p.cheval.entraineur else None
                ),
                "musique": p.musique,
                "cote": p.cote_depart,
                "non_partant": p.non_partant,
            }
            for p in partants
        ],
    }


@router.get("/{course_id}/partants", summary="Partants d'une course")
def partants_course(course_id: int, db: Session = Depends(get_db)):
    """Retourne uniquement la liste des partants d'une course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course introuvable")

    partants = (
        db.query(Partant)
        .filter(Partant.course_id == course_id, Partant.non_partant == False)
        .order_by(Partant.numero_partant)
        .all()
    )

    return {
        "course_id": course_id,
        "date": str(course.date_course),
        "partants_actifs": len(partants),
        "partants": [
            {
                "id": p.id,
                "numero": p.numero_partant,
                "cheval_id": p.cheval_id,
                "cheval": p.cheval.nom if p.cheval else None,
                "jockey_id": p.jockey_id,
                "jockey": f"{p.jockey.nom}" if p.jockey else None,
                "cote": p.cote_depart,
            }
            for p in partants
        ],
    }
