"""
Service d'importation et de validation des programmes hippiques.

Orchestre le flux complet :
PDF/Excel → extraction → parsing LONAB → validation → sauvegarde en base
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import date as DateType
from sqlalchemy.orm import Session

from app.services.extraction import extraire_texte_pdf, extraire_avec_ocr, extraire_excel
from app.services.parser_lonab import parser_programme_lonab, programme_vers_dict, ProgrammePMU
from app.models.course import Course
from app.models.cheval import Cheval
from app.models.jockey import Jockey
from app.models.entraineur import Entraineur
from app.models.partant import Partant

logger = logging.getLogger(__name__)


class ImportationError(Exception):
    """Exception levée lors d'une erreur d'importation."""
    pass


def _obtenir_ou_creer_jockey(nom: str, db: Session) -> Optional[Jockey]:
    """Récupère un jockey par son nom ou le crée s'il n'existe pas."""
    if not nom:
        return None
    # Chercher par nom complet
    parties = nom.strip().split()
    nom_famille = parties[-1] if parties else nom
    jockey = db.query(Jockey).filter(Jockey.nom.ilike(f"%{nom_famille}%")).first()
    if not jockey:
        jockey = Jockey(nom=nom_famille, prenom=" ".join(parties[:-1]) if len(parties) > 1 else None)
        db.add(jockey)
        db.flush()
        logger.info(f"Nouveau jockey créé : {nom}")
    return jockey


def _obtenir_ou_creer_entraineur(nom: str, db: Session) -> Optional[Entraineur]:
    """Récupère un entraîneur par son nom ou le crée s'il n'existe pas."""
    if not nom:
        return None
    parties = nom.strip().split()
    nom_famille = parties[-1] if parties else nom
    entraineur = db.query(Entraineur).filter(Entraineur.nom.ilike(f"%{nom_famille}%")).first()
    if not entraineur:
        entraineur = Entraineur(
            nom=nom_famille,
            prenom=" ".join(parties[:-1]) if len(parties) > 1 else None,
        )
        db.add(entraineur)
        db.flush()
        logger.info(f"Nouvel entraîneur créé : {nom}")
    return entraineur


def _obtenir_ou_creer_cheval(nom: str, entraineur_id: Optional[int], db: Session) -> Cheval:
    """Récupère un cheval par son nom ou le crée s'il n'existe pas."""
    cheval = db.query(Cheval).filter(Cheval.nom == nom.upper()).first()
    if not cheval:
        cheval = Cheval(nom=nom.upper(), entraineur_id=entraineur_id)
        db.add(cheval)
        db.flush()
        logger.info(f"Nouveau cheval créé : {nom}")
    elif entraineur_id and not cheval.entraineur_id:
        cheval.entraineur_id = entraineur_id
    return cheval


def sauvegarder_programme(programme: ProgrammePMU, db: Session) -> dict:
    """
    Sauvegarde un programme PMU parsé en base de données.

    Crée ou met à jour toutes les entités :
    - Courses de la journée
    - Chevaux, jockeys, entraîneurs
    - Partants engagés

    Args:
        programme: Programme PMU parsé
        db: Session de base de données

    Returns:
        Résumé de l'importation (courses créées, partants, etc.)
    """
    if not programme.date:
        raise ImportationError("Date du programme manquante — impossible d'importer")

    try:
        date_course = DateType.fromisoformat(programme.date)
    except ValueError:
        raise ImportationError(f"Format de date invalide : {programme.date}")

    hippodrome = programme.hippodrome or "Hippodrome de Ouagadougou"
    reunion = programme.reunion or "R1"

    courses_creees = 0
    partants_crees = 0
    erreurs = []

    for course_data in programme.courses:
        try:
            # Vérifier si la course existe déjà
            course = (
                db.query(Course)
                .filter(
                    Course.date_course == date_course,
                    Course.reunion == reunion,
                    Course.numero_course == course_data.numero,
                )
                .first()
            )

            if not course:
                course = Course(
                    date_course=date_course,
                    reunion=reunion,
                    numero_course=course_data.numero,
                    hippodrome=hippodrome,
                    distance=course_data.distance,
                    type_piste=course_data.type_piste or "sable",
                    conditions=course_data.conditions,
                    allocation=course_data.allocation,
                    nombre_partants=len(course_data.partants),
                    programme_source=programme.source_fichier,
                )
                db.add(course)
                db.flush()
                courses_creees += 1
                logger.info(f"Course créée : {date_course} R{reunion} C{course_data.numero}")

            # Créer les partants
            for partant_data in course_data.partants:
                try:
                    # Entraîneur
                    entraineur = _obtenir_ou_creer_entraineur(partant_data.entraineur or "", db)
                    # Cheval
                    cheval = _obtenir_ou_creer_cheval(
                        partant_data.nom_cheval,
                        entraineur.id if entraineur else None,
                        db,
                    )
                    # Jockey
                    jockey = _obtenir_ou_creer_jockey(partant_data.jockey or "", db)

                    # Vérifier si le partant existe déjà
                    partant_existant = (
                        db.query(Partant)
                        .filter(
                            Partant.course_id == course.id,
                            Partant.cheval_id == cheval.id,
                        )
                        .first()
                    )

                    if not partant_existant:
                        partant = Partant(
                            course_id=course.id,
                            cheval_id=cheval.id,
                            jockey_id=jockey.id if jockey else None,
                            numero_partant=partant_data.numero,
                            musique=partant_data.musique,
                            cote_depart=partant_data.cote,
                            poids=partant_data.poids,
                        )
                        db.add(partant)
                        partants_crees += 1

                except Exception as e:
                    erreurs.append(f"Partant {partant_data.numero} ({partant_data.nom_cheval}): {e}")
                    logger.warning(f"Erreur partant : {e}")

        except Exception as e:
            erreurs.append(f"Course {course_data.numero}: {e}")
            logger.error(f"Erreur course {course_data.numero} : {e}", exc_info=True)

    db.commit()

    return {
        "date": str(date_course),
        "hippodrome": hippodrome,
        "reunion": reunion,
        "courses_creees": courses_creees,
        "partants_crees": partants_crees,
        "erreurs": erreurs,
        "statut": "succès" if not erreurs else "partiel",
    }


def importer_pdf_complet(chemin_pdf: str, db: Session) -> dict:
    """
    Flux complet d'import d'un PDF :
    1. Extraction texte (PyMuPDF)
    2. Fallback OCR si texte insuffisant
    3. Parsing LONAB
    4. Sauvegarde en base

    Args:
        chemin_pdf: Chemin du fichier PDF
        db: Session de base de données

    Returns:
        Résumé de l'importation
    """
    logger.info(f"Import PDF : {chemin_pdf}")

    # Tentative extraction directe
    texte = extraire_texte_pdf(chemin_pdf)

    # Si trop peu de texte → PDF scanné → OCR
    if len(texte.strip()) < 200:
        logger.info("Texte insuffisant — tentative OCR")
        texte = extraire_avec_ocr(chemin_pdf)

    if not texte.strip():
        raise ImportationError("Impossible d'extraire le texte du PDF (ni texte ni OCR)")

    # Parsing spécialisé LONAB
    programme = parser_programme_lonab(texte, source_fichier=Path(chemin_pdf).name)

    if programme.confiance < 30:
        logger.warning(
            f"Confiance d'extraction faible ({programme.confiance:.0f}%) — "
            "vérification manuelle recommandée"
        )

    # Convertir en dict pour la réponse
    programme_dict = programme_vers_dict(programme)

    # Sauvegarder en base si la confiance est suffisante
    resultat_import = None
    if programme.confiance >= 30 and programme.courses:
        try:
            resultat_import = sauvegarder_programme(programme, db)
        except ImportationError as e:
            logger.warning(f"Import automatique impossible : {e}")

    return {
        "confiance": programme.confiance,
        "programme": programme_dict,
        "import_base": resultat_import,
        "action_requise": (
            "Validez les données extraites avant confirmation"
            if programme.confiance < 70
            else "Import automatique effectué"
        ),
    }
