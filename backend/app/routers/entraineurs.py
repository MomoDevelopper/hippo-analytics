"""
Routes API — Entraîneurs.
"""
from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entraineur import Entraineur
from app.models.cheval import Cheval
from app.models.performance import Performance

router = APIRouter(prefix="/entraineurs", tags=["Entraîneurs"])


@router.get("/", summary="Classement des entraîneurs")
def classement_entraineurs(
    periode_jours: int = Query(90, ge=7, le=365),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    date_limite = date.today() - timedelta(days=periode_jours)
    entraineurs = db.query(Entraineur).filter(Entraineur.actif == True).all()
    classement = []

    for entraineur in entraineurs:
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
            continue

        total = len(performances)
        victoires = sum(1 for p in performances if p.place_officielle == 1)
        top5 = sum(1 for p in performances if p.place_officielle and p.place_officielle <= 5)
        chevaux_engages = db.query(Cheval).filter(Cheval.entraineur_id == entraineur.id).count()

        classement.append({
            "id": entraineur.id,
            "nom": f"{entraineur.prenom or ''} {entraineur.nom}".strip(),
            "ecurie": entraineur.ecurie,
            "chevaux_engages": chevaux_engages,
            "sorties": total,
            "victoires": victoires,
            "top5": top5,
            "taux_victoire": round(victoires / total * 100, 1),
            "taux_classes": round(top5 / total * 100, 1),
        })

    classement.sort(key=lambda x: x["taux_victoire"], reverse=True)
    for rang, e in enumerate(classement, start=1):
        e["rang"] = rang

    return {"periode_jours": periode_jours, "classement": classement[:limit]}


@router.get("/{entraineur_id}", summary="Fiche d'un entraîneur")
def fiche_entraineur(entraineur_id: int, db: Session = Depends(get_db)):
    entraineur = db.query(Entraineur).filter(Entraineur.id == entraineur_id).first()
    if not entraineur:
        raise HTTPException(status_code=404, detail="Entraîneur introuvable")

    chevaux = db.query(Cheval).filter(Cheval.entraineur_id == entraineur_id).all()
    return {
        "id": entraineur.id,
        "nom": f"{entraineur.prenom or ''} {entraineur.nom}".strip(),
        "ecurie": entraineur.ecurie,
        "nationalite": entraineur.nationalite,
        "actif": entraineur.actif,
        "chevaux": [{"id": c.id, "nom": c.nom, "age": c.age} for c in chevaux],
    }
