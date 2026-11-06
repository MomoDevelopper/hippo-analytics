"""
Routes API — Jockeys.
"""
from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.jockey import Jockey
from app.models.performance import Performance

router = APIRouter(prefix="/jockeys", tags=["Jockeys"])


@router.get("/", summary="Classement des jockeys")
def classement_jockeys(
    periode_jours: int = Query(90, ge=7, le=365, description="Période d'analyse en jours"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retourne le classement des jockeys avec leurs statistiques."""
    date_limite = date.today() - timedelta(days=periode_jours)

    jockeys = db.query(Jockey).filter(Jockey.actif == True).all()
    classement = []

    for jockey in jockeys:
        performances = (
            db.query(Performance)
            .filter(
                Performance.jockey_id == jockey.id,
                Performance.date_course >= date_limite,
            )
            .all()
        )
        if not performances:
            continue

        total = len(performances)
        victoires = sum(1 for p in performances if p.place_officielle == 1)
        top3 = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 3)
        top5 = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 5)

        classement.append({
            "id": jockey.id,
            "nom": f"{jockey.prenom or ''} {jockey.nom}".strip(),
            "courses": total,
            "victoires": victoires,
            "places_top3": top3,
            "places_top5": top5,
            "taux_victoire": round(victoires / total * 100, 1),
            "taux_top3": round(top3 / total * 100, 1),
        })

    # Trier par taux de victoire décroissant
    classement.sort(key=lambda x: x["taux_victoire"], reverse=True)
    for rang, j in enumerate(classement, start=1):
        j["rang"] = rang

    return {"periode_jours": periode_jours, "classement": classement[:limit]}


@router.get("/{jockey_id}", summary="Fiche d'un jockey")
def fiche_jockey(jockey_id: int, db: Session = Depends(get_db)):
    jockey = db.query(Jockey).filter(Jockey.id == jockey_id).first()
    if not jockey:
        raise HTTPException(status_code=404, detail="Jockey introuvable")

    performances = (
        db.query(Performance)
        .filter(Performance.jockey_id == jockey_id)
        .order_by(Performance.date_course.desc())
        .limit(20)
        .all()
    )

    return {
        "id": jockey.id,
        "nom": f"{jockey.prenom or ''} {jockey.nom}".strip(),
        "nationalite": jockey.nationalite,
        "actif": jockey.actif,
        "performances_recentes": [
            {
                "date": str(p.date_course),
                "hippodrome": p.hippodrome,
                "distance": p.distance,
                "place": p.place_officielle,
                "partants": p.partants_total,
            }
            for p in performances
        ],
    }
