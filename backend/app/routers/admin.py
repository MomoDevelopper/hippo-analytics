"""
Routes API — Administration (entraînement IA, exports, gestion des données).
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.modele_ia import entrainer_modele
from app.services.rapports import exporter_pronostic_pdf, exporter_historique_excel

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/ia/entrainer", summary="Entraîner le modèle XGBoost")
def lancer_entrainement(
    background_tasks: BackgroundTasks,
    nb_jours: int = Query(365, ge=30, le=1825, description="Historique à utiliser (jours)"),
    db: Session = Depends(get_db),
):
    """
    Lance l'entraînement du modèle XGBoost sur les données historiques.
    La tâche s'exécute en arrière-plan.
    """
    def tache():
        result = entrainer_modele(db, nb_jours)
        return result

    background_tasks.add_task(tache)
    return {
        "message": "Entraînement lancé en arrière-plan",
        "periode_jours": nb_jours,
        "info": "Le modèle sera disponible à la fin de l'entraînement",
    }


@router.post("/exports/pdf/{course_id}", summary="Exporter un pronostic en PDF")
def exporter_pdf(course_id: int, db: Session = Depends(get_db)):
    """Génère un rapport PDF du pronostic d'une course."""
    try:
        chemin = exporter_pronostic_pdf(course_id, db)
        return {"message": "PDF généré", "fichier": chemin}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération PDF : {e}")


@router.post("/exports/excel", summary="Exporter l'historique en Excel")
def exporter_excel(db: Session = Depends(get_db)):
    """Exporte l'historique complet des prédictions vs résultats en Excel."""
    try:
        chemin = exporter_historique_excel(db)
        return {"message": "Export Excel généré", "fichier": chemin}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération Excel : {e}")
