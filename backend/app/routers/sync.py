"""
Routes API — Synchronisation autonome.
"""
from fastapi import APIRouter, BackgroundTasks
from app.services.synchronisation import get_sync_status
from app.scheduler import lancer_sync_manuelle

router = APIRouter(prefix="/sync", tags=["Synchronisation"])


@router.get("/status", summary="État de la synchronisation autonome")
def statut_synchronisation():
    """
    Retourne l'état de la dernière synchronisation avec LONAB.
    Permet de savoir si le système collecte bien les programmes automatiquement.
    """
    return get_sync_status()


@router.post("/run", summary="Lancer une synchronisation manuelle")
def synchronisation_manuelle(background_tasks: BackgroundTasks):
    """
    Déclenche immédiatement une synchronisation avec LONAB.
    La tâche tourne en arrière-plan pour ne pas bloquer l'interface.
    """
    background_tasks.add_task(lancer_sync_manuelle)
    return {
        "message": "Synchronisation démarrée en arrière-plan",
        "info": "Consultez GET /sync/status pour suivre l'avancement",
    }
