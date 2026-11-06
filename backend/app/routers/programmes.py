"""
Routes API — Programmes hippiques.
Gestion de l'import et de la consultation des programmes PMU Burkina Faso.
"""
import os
import shutil
from pathlib import Path
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.models.course import Course
from app.services.extraction import extraire_texte_pdf, parser_programme, extraire_excel

router = APIRouter(prefix="/programmes", tags=["Programmes"])
settings = get_settings()


@router.get("/", summary="Liste des programmes disponibles")
def lister_programmes(
    date_debut: Optional[date] = Query(None, description="Filtrer depuis cette date"),
    date_fin: Optional[date] = Query(None, description="Filtrer jusqu'à cette date"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retourne la liste des programmes hippiques enregistrés."""
    query = db.query(Course)
    if date_debut:
        query = query.filter(Course.date_course >= date_debut)
    if date_fin:
        query = query.filter(Course.date_course <= date_fin)
    courses = query.order_by(Course.date_course.desc()).limit(limit).all()

    # Regrouper par journée
    journees: dict = {}
    for course in courses:
        cle = str(course.date_course)
        if cle not in journees:
            journees[cle] = {"date": cle, "hippodrome": course.hippodrome, "courses": []}
        journees[cle]["courses"].append(
            {"id": course.id, "reunion": course.reunion, "numero": course.numero_course}
        )

    return {"programmes": list(journees.values()), "total": len(journees)}


@router.post("/import/pdf", summary="Importer un programme PDF")
async def importer_pdf(
    fichier: UploadFile = File(..., description="Fichier PDF du programme hippique"),
    db: Session = Depends(get_db),
):
    """
    Importe un programme hippique au format PDF.
    Le fichier est analysé automatiquement (OCR si nécessaire).
    L'administrateur peut corriger les données avant validation.
    """
    if not fichier.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format PDF")

    # Vérification de la taille
    contenu = await fichier.read()
    taille_mb = len(contenu) / (1024 * 1024)
    if taille_mb > settings.MAX_PDF_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux ({taille_mb:.1f} Mo). Maximum : {settings.MAX_PDF_SIZE_MB} Mo",
        )

    # Sauvegarde du fichier
    dossier = Path(settings.UPLOAD_DIR) / "programmes"
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / fichier.filename
    chemin.write_bytes(contenu)

    # Extraction du texte
    texte = extraire_texte_pdf(str(chemin))
    programme = parser_programme(texte)

    return {
        "message": "Programme importé avec succès",
        "fichier": fichier.filename,
        "taille_mo": round(taille_mb, 2),
        "extraction": {
            "date": programme.get("date"),
            "hippodrome": programme.get("hippodrome"),
            "reunion": programme.get("reunion"),
            "nb_courses": len(programme.get("courses", [])),
            "confiance": f"{programme.get('confiance_extraction', 0):.0f}%",
        },
        "action_requise": "Vérifiez et validez les données extraites avant enregistrement",
    }


@router.post("/import/excel", summary="Importer un programme Excel")
async def importer_excel(
    fichier: UploadFile = File(..., description="Fichier Excel du programme hippique"),
    db: Session = Depends(get_db),
):
    """Importe un programme hippique au format Excel (.xlsx)."""
    if not fichier.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format Excel (.xlsx)")

    contenu = await fichier.read()
    dossier = Path(settings.UPLOAD_DIR) / "programmes"
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / fichier.filename
    chemin.write_bytes(contenu)

    programme = extraire_excel(str(chemin))

    return {
        "message": "Fichier Excel importé avec succès",
        "fichier": fichier.filename,
        "extraction": programme,
    }
