"""
Routes API — Chevaux.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cheval import Cheval
from app.models.performance import Performance

router = APIRouter(prefix="/chevaux", tags=["Chevaux"])


@router.get("/", summary="Liste des chevaux")
def lister_chevaux(
    nom: Optional[str] = Query(None, description="Filtrer par nom"),
    actif: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Cheval)
    if nom:
        query = query.filter(Cheval.nom.ilike(f"%{nom}%"))
    if actif is not None:
        query = query.filter(Cheval.actif == actif)

    total = query.count()
    chevaux = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "chevaux": [
            {
                "id": c.id,
                "nom": c.nom,
                "age": c.age,
                "sexe": c.sexe,
                "robe": c.robe,
                "proprietaire": c.proprietaire,
                "entraineur": (
                    f"{c.entraineur.nom}" if c.entraineur else None
                ),
            }
            for c in chevaux
        ],
    }


@router.get("/{cheval_id}", summary="Fiche détaillée d'un cheval")
def fiche_cheval(cheval_id: int, db: Session = Depends(get_db)):
    cheval = db.query(Cheval).filter(Cheval.id == cheval_id).first()
    if not cheval:
        raise HTTPException(status_code=404, detail="Cheval introuvable")

    # Dernières performances
    performances = (
        db.query(Performance)
        .filter(Performance.cheval_id == cheval_id)
        .order_by(Performance.date_course.desc())
        .limit(10)
        .all()
    )

    victoires = sum(1 for p in performances if p.place_officielle == 1)
    places = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 3)

    return {
        "id": cheval.id,
        "nom": cheval.nom,
        "age": cheval.age,
        "sexe": cheval.sexe,
        "robe": cheval.robe,
        "origine": cheval.origine,
        "proprietaire": cheval.proprietaire,
        "naisseur": cheval.naisseur,
        "entraineur": (
            {"id": cheval.entraineur.id, "nom": cheval.entraineur.nom}
            if cheval.entraineur else None
        ),
        "statistiques": {
            "sorties_analysees": len(performances),
            "victoires": victoires,
            "places_top3": places,
            "taux_victoire": round(victoires / len(performances) * 100, 1) if performances else 0,
        },
        "dernieres_performances": [
            {
                "date": str(p.date_course),
                "hippodrome": p.hippodrome,
                "distance": p.distance,
                "place": p.place_officielle,
                "partants": p.partants_total,
                "jockey": p.jockey.nom if p.jockey else None,
                "cote": p.cote_depart,
            }
            for p in performances
        ],
    }
