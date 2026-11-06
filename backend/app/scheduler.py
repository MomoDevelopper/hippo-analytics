"""
Scheduler APScheduler — Synchronisation autonome de HIPPO ANALYTICS.

Lance automatiquement la collecte des programmes PMU Burkina Faso
toutes les SYNC_INTERVAL_HOURS heures, même si l'administrateur
n'est pas connecté.
"""
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Instance globale du scheduler
scheduler = BackgroundScheduler(timezone="Africa/Ouagadougou")


def demarrer_scheduler():
    """
    Démarre le scheduler de synchronisation autonome.
    Appelé au démarrage de l'application FastAPI.
    """
    from app.services.synchronisation import sync_programmes

    # Lire l'intervalle depuis os.environ (priorité sur config cachée)
    try:
        hours = int(os.environ.get("SYNC_INTERVAL_HOURS", "6"))
    except ValueError:
        hours = 6

    # Si heures très élevées (mode test), ne pas démarrer la sync
    if hours >= 999:
        logger.info("Scheduler en mode test — synchronisation automatique désactivée")
        return

    # Ajout de la tâche de synchronisation périodique
    scheduler.add_job(
        func=sync_programmes,
        trigger=IntervalTrigger(hours=hours),
        id="sync_programmes_lonab",
        name="Synchronisation programmes LONAB / PMU Burkina Faso",
        replace_existing=True,
        misfire_grace_time=3600,   # Tolérance d'une heure si le serveur est redémarré
    )

    scheduler.start()
    logger.info(
        f"Scheduler démarré — Synchronisation toutes les "
        f"{hours}h (fuseau : Africa/Ouagadougou)"
    )


def arreter_scheduler():
    """Arrête proprement le scheduler (appelé à l'arrêt de l'application)."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")


def lancer_sync_manuelle():
    """
    Déclenche immédiatement une synchronisation manuelle.
    Utilisé par la route POST /api/sync/run.

    Returns:
        Résultat de la synchronisation
    """
    from app.services.synchronisation import sync_programmes
    logger.info("Synchronisation manuelle déclenchée par l'administrateur")
    return sync_programmes()
