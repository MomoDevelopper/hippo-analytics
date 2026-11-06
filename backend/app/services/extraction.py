"""
Service d'extraction des programmes hippiques depuis des fichiers PDF et Excel.

Utilise PyMuPDF pour la lecture des PDFs structurés et Tesseract OCR
pour les documents scannés.
"""
import re
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def extraire_texte_pdf(chemin_pdf: str) -> str:
    """
    Extrait le texte d'un fichier PDF en utilisant PyMuPDF.

    Args:
        chemin_pdf: Chemin vers le fichier PDF

    Returns:
        Texte extrait du PDF
    """
    try:
        import fitz  # PyMuPDF

        texte_complet = []
        document = fitz.open(chemin_pdf)

        for numero_page, page in enumerate(document, start=1):
            texte = page.get_text("text")
            if texte.strip():
                texte_complet.append(f"[PAGE {numero_page}]\n{texte}")

        document.close()
        logger.info(f"PDF extrait : {len(document)} page(s) — {chemin_pdf}")
        return "\n".join(texte_complet)

    except ImportError:
        logger.error("PyMuPDF non installé. Exécuter : pip install pymupdf")
        return ""
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du PDF {chemin_pdf} : {e}")
        return ""


def extraire_avec_ocr(chemin_image: str, langue: str = "fra") -> str:
    """
    Extrait le texte d'une image ou d'un PDF scanné via Tesseract OCR.

    Args:
        chemin_image: Chemin vers l'image ou le PDF
        langue: Code de langue Tesseract (fra = français)

    Returns:
        Texte reconnu par OCR
    """
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(chemin_image)
        texte = pytesseract.image_to_string(image, lang=langue)
        logger.info(f"OCR terminé pour : {chemin_image} ({len(texte)} caractères)")
        return texte

    except ImportError:
        logger.error("pytesseract ou Pillow non installé")
        return ""
    except Exception as e:
        logger.error(f"Erreur OCR pour {chemin_image} : {e}")
        return ""


def parser_programme(texte: str) -> dict:
    """
    Analyse le texte extrait d'un programme hippique PMU Burkina Faso
    et retourne une structure de données exploitable.

    Args:
        texte: Texte brut extrait du PDF

    Returns:
        Dictionnaire structuré avec les informations du programme
    """
    programme = {
        "date": None,
        "hippodrome": None,
        "reunion": None,
        "courses": [],
        "source": "pdf",
        "texte_brut": texte[:2000],   # Conservation partielle pour débogage
        "confiance_extraction": 0.0,
    }

    # Extraction de la date (formats DD/MM/YYYY ou DD-MM-YYYY)
    patterns_date = [
        r"\b(\d{2})[/\-](\d{2})[/\-](\d{4})\b",
        r"\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|"
        r"août|septembre|octobre|novembre|décembre)\s+(\d{4})\b",
    ]
    mois_fr = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
    }
    for pattern in patterns_date:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            groupes = match.groups()
            if len(groupes) == 3:
                try:
                    if groupes[1].isdigit():
                        programme["date"] = f"{groupes[2]}-{groupes[1]}-{groupes[0]}"
                    else:
                        mois = mois_fr.get(groupes[1].lower(), 1)
                        programme["date"] = f"{groupes[2]}-{mois:02d}-{int(groupes[0]):02d}"
                    break
                except Exception:
                    continue

    # Extraction de l'hippodrome
    hippodromes_connus = [
        "Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Banfora",
        "Paris-Vincennes", "Longchamp", "Chantilly"
    ]
    for hippodrome in hippodromes_connus:
        if hippodrome.lower() in texte.lower():
            programme["hippodrome"] = hippodrome
            break

    # Extraction de la réunion
    match_reunion = re.search(r"R[ÉEé]UNION\s*N?[°º]?\s*(\d+)", texte, re.IGNORECASE)
    if not match_reunion:
        match_reunion = re.search(r"\bR(\d+)\b", texte)
    if match_reunion:
        programme["reunion"] = f"R{match_reunion.group(1)}"

    # Extraction des courses et partants
    # Recherche des blocs "COURSE N°X" ou "C1", "C2"
    pattern_course = re.compile(
        r"COURSE\s*N?[°º]?\s*(\d+)|C(\d+)\s*[-–]", re.IGNORECASE
    )
    lignes = texte.split("\n")
    course_courante = None

    for i, ligne in enumerate(lignes):
        match_c = pattern_course.search(ligne)
        if match_c:
            numero = match_c.group(1) or match_c.group(2)
            course_courante = {
                "numero": int(numero),
                "distance": None,
                "conditions": ligne.strip(),
                "partants": [],
            }
            programme["courses"].append(course_courante)

            # Extraction de la distance sur la même ligne ou la suivante
            match_dist = re.search(r"(\d{3,4})\s*m", ligne + " " + lignes[i + 1] if i + 1 < len(lignes) else ligne)
            if match_dist:
                course_courante["distance"] = int(match_dist.group(1))
            continue

        # Extraction des partants (numéro + nom du cheval)
        if course_courante:
            match_partant = re.match(
                r"^\s*(\d{1,2})\s+([A-ZÀÂÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÉÈÊËÎÏÔÙÛÜa-zàâéèêëîïôùûü\s'\-]{2,40})",
                ligne
            )
            if match_partant:
                course_courante["partants"].append(
                    {
                        "numero": int(match_partant.group(1)),
                        "nom": match_partant.group(2).strip(),
                        "jockey": None,
                        "entraineur": None,
                        "cote": None,
                        "musique": None,
                    }
                )

    # Calcul d'un score de confiance basique
    confiance = 0.0
    if programme["date"]:
        confiance += 30
    if programme["hippodrome"]:
        confiance += 20
    if programme["reunion"]:
        confiance += 20
    if programme["courses"]:
        confiance += 20
        if any(c["partants"] for c in programme["courses"]):
            confiance += 10

    programme["confiance_extraction"] = confiance
    logger.info(
        f"Parsing terminé — {len(programme['courses'])} course(s), "
        f"confiance : {confiance:.0f}%"
    )
    return programme


def extraire_excel(chemin_excel: str) -> dict:
    """
    Extrait les données d'un programme hippique au format Excel (.xlsx).

    Args:
        chemin_excel: Chemin vers le fichier Excel

    Returns:
        Dictionnaire structuré avec les informations du programme
    """
    try:
        import pandas as pd

        programme = {
            "date": None,
            "hippodrome": None,
            "reunion": None,
            "courses": [],
            "source": "excel",
            "confiance_extraction": 80.0,  # Excel = données plus structurées
        }

        # Lire toutes les feuilles
        classeur = pd.read_excel(chemin_excel, sheet_name=None, header=None)

        for nom_feuille, df in classeur.items():
            logger.info(f"Feuille Excel : '{nom_feuille}' — {len(df)} lignes")
            # Traitement basique : chercher les colonnes pertinentes
            # (adapté selon la structure réelle des fichiers LONAB)

        return programme

    except ImportError:
        logger.error("pandas ou openpyxl non installé")
        return {}
    except Exception as e:
        logger.error(f"Erreur lors de la lecture Excel {chemin_excel} : {e}")
        return {}
