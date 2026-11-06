"""
Service de synchronisation autonome avec LONAB / PMU Burkina Faso.

Ce service tourne en arrière-plan (via APScheduler) et continue à collecter
les programmes et les résultats même lorsque l'administrateur est absent.
"""
import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Historique de synchronisation en mémoire (complété par la base de données)
_sync_history = {
    "derniere_execution": None,
    "statut": "jamais_executé",
    "fichiers_recuperes": 0,
    "erreur": None,
    "executions_totales": 0,
}


def get_sync_status() -> dict:
    """
    Retourne l'état courant de la synchronisation autonome.
    """
    return {
        **_sync_history,
        "intervalle_heures": settings.SYNC_INTERVAL_HOURS,
        "source": settings.LONAB_BASE_URL,
    }


def _telecharger_pdf(url: str, repertoire: Path) -> Optional[Path]:
    """
    Télécharge un fichier PDF depuis une URL et le sauvegarde localement.
    Utilise le hash MD5 pour éviter les doublons.

    Args:
        url: URL du fichier PDF à télécharger
        repertoire: Dossier de destination

    Returns:
        Chemin du fichier téléchargé, ou None si déjà existant ou erreur
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; HippoAnalytics/1.0; "
                "+https://lonab.bf) [collecte automatique programmes PMU]"
            )
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Calculer le hash pour éviter les doublons
        contenu = response.content
        hash_md5 = hashlib.md5(contenu).hexdigest()[:12]
        nom_fichier = f"programme_{hash_md5}.pdf"
        chemin = repertoire / nom_fichier

        if chemin.exists():
            logger.debug(f"Fichier déjà présent : {nom_fichier}")
            return None

        chemin.write_bytes(contenu)
        logger.info(f"Nouveau programme téléchargé : {nom_fichier} ({len(contenu)} octets)")
        return chemin

    except requests.exceptions.ConnectionError:
        logger.warning(f"Impossible de joindre : {url} — connexion refusée")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"Délai dépassé pour : {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Erreur HTTP {e.response.status_code} pour : {url}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du téléchargement de {url} : {e}")
        return None


def _rechercher_liens_pdf(html: str, base_url: str) -> list[str]:
    """
    Extrait les liens vers des fichiers PDF depuis le HTML de la page LONAB.

    Args:
        html: Contenu HTML de la page
        base_url: URL de base pour compléter les liens relatifs

    Returns:
        Liste d'URLs de fichiers PDF
    """
    soup = BeautifulSoup(html, "html.parser")
    liens = []

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        # Conserver uniquement les liens PDF
        if href.lower().endswith(".pdf"):
            if href.startswith("http"):
                liens.append(href)
            elif href.startswith("/"):
                liens.append(f"{base_url.rstrip('/')}{href}")
            else:
                liens.append(f"{base_url.rstrip('/')}/{href}")

    return list(set(liens))  # Dédoublonnage


def sync_programmes() -> dict:
    """
    Fonction principale de synchronisation autonome.

    Tâche planifiée (APScheduler) exécutée toutes les SYNC_INTERVAL_HOURS heures.
    Collecte automatiquement les nouveaux programmes PMU Burkina Faso depuis LONAB.

    Returns:
        Résumé de la synchronisation : statut, fichiers récupérés, erreurs
    """
    global _sync_history

    logger.info("=" * 60)
    logger.info("HIPPO ANALYTICS — Synchronisation autonome démarrée")
    logger.info(f"Source : {settings.LONAB_BASE_URL}")
    logger.info(f"Heure  : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 60)

    # Préparer le dossier de destination
    repertoire = Path(settings.UPLOAD_DIR) / "programmes"
    repertoire.mkdir(parents=True, exist_ok=True)

    fichiers_recuperes = 0
    erreur = None

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; HippoAnalytics/1.0; "
                "+https://lonab.bf) [collecte automatique programmes PMU]"
            )
        }

        # Tentative de connexion à la page des programmes LONAB
        url_programmes = f"{settings.LONAB_BASE_URL}{settings.LONAB_PMU_PATH}"
        logger.info(f"Connexion à : {url_programmes}")

        response = requests.get(url_programmes, headers=headers, timeout=20)
        response.raise_for_status()

        # Recherche des liens PDF dans la page
        liens_pdf = _rechercher_liens_pdf(response.text, settings.LONAB_BASE_URL)
        logger.info(f"{len(liens_pdf)} lien(s) PDF détecté(s)")

        # Téléchargement des PDFs non encore archivés
        for url_pdf in liens_pdf:
            chemin = _telecharger_pdf(url_pdf, repertoire)
            if chemin:
                fichiers_recuperes += 1

        statut = "succès"
        logger.info(f"Synchronisation terminée : {fichiers_recuperes} nouveau(x) fichier(s)")

    except requests.exceptions.ConnectionError:
        statut = "source_indisponible"
        erreur = f"Impossible de joindre {settings.LONAB_BASE_URL}"
        logger.warning(
            f"Source indisponible — nouvelle tentative dans {settings.SYNC_INTERVAL_HOURS}h"
        )

    except requests.exceptions.Timeout:
        statut = "timeout"
        erreur = "Délai de connexion dépassé"
        logger.warning("Timeout — la source a mis trop de temps à répondre")

    except requests.exceptions.HTTPError as e:
        statut = "erreur_http"
        erreur = f"HTTP {e.response.status_code}"
        logger.error(f"Erreur HTTP lors de la synchronisation : {e}")

    except Exception as e:
        statut = "erreur"
        erreur = str(e)
        logger.error(f"Erreur inattendue lors de la synchronisation : {e}", exc_info=True)

    # Mise à jour de l'historique
    _sync_history.update(
        {
            "derniere_execution": datetime.now().isoformat(),
            "statut": statut,
            "fichiers_recuperes": _sync_history["fichiers_recuperes"] + fichiers_recuperes,
            "erreur": erreur,
            "executions_totales": _sync_history["executions_totales"] + 1,
        }
    )

    return {
        "statut": statut,
        "fichiers_recuperes": fichiers_recuperes,
        "erreur": erreur,
    }
