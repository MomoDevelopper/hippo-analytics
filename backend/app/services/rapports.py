"""
Service de génération de rapports (exports PDF et Excel).
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.pronostic import Pronostic
from app.models.arrivee import Arrivee

logger = logging.getLogger(__name__)


def exporter_pronostic_pdf(course_id: int, db: Session, dossier: str = "./exports") -> str:
    """
    Génère un rapport PDF du pronostic d'une course.

    Args:
        course_id: ID de la course
        db: Session de base de données
        dossier: Dossier de destination

    Returns:
        Chemin du fichier PDF généré
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

    except ImportError:
        logger.error("ReportLab non installé. Exécuter : pip install reportlab")
        raise

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError(f"Course introuvable : {course_id}")

    pronostic = (
        db.query(Pronostic)
        .filter(Pronostic.course_id == course_id)
        .order_by(Pronostic.date_generation.desc())
        .first()
    )

    # Créer le dossier d'export
    Path(dossier).mkdir(parents=True, exist_ok=True)
    nom_fichier = f"pronostic_C{course.numero_course}_{course.date_course}.pdf"
    chemin = Path(dossier) / nom_fichier

    # Créer le document PDF
    doc = SimpleDocTemplate(str(chemin), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    contenu = []

    # En-tête
    titre_style = ParagraphStyle("Titre", parent=styles["Title"], fontSize=18, textColor=colors.darkblue)
    contenu.append(Paragraph("🐎 HIPPO ANALYTICS", titre_style))
    contenu.append(Paragraph("Pronostic de course — PMU Burkina Faso (LONAB)", styles["Heading2"]))
    contenu.append(Spacer(1, 0.5 * cm))

    # Informations de la course
    info_course = [
        ["Date", str(course.date_course)],
        ["Hippodrome", course.hippodrome],
        ["Réunion / Course", f"{course.reunion} — Course n°{course.numero_course}"],
        ["Distance", f"{course.distance} m" if course.distance else "N/D"],
        ["Partants", str(course.nombre_partants or "N/D")],
    ]
    table_info = Table(info_course, colWidths=[5 * cm, 12 * cm])
    table_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    contenu.append(table_info)
    contenu.append(Spacer(1, 0.5 * cm))

    # Pronostic
    if pronostic and pronostic.top_hypotheses:
        contenu.append(Paragraph("Top 10 Hypothèses de classement", styles["Heading3"]))

        entetes = ["Rang", "Ordre d'arrivée estimé", "Probabilité"]
        donnees = [entetes]

        for hyp in pronostic.top_hypotheses[:10]:
            ordre = " - ".join(str(cid) for cid in hyp.get("ordre", []))
            prob = f"{hyp.get('probabilite', 0) * 100:.3f}%"
            donnees.append([str(hyp.get("rang", "")), ordre, prob])

        table_hyp = Table(donnees, colWidths=[2 * cm, 12 * cm, 3 * cm])
        table_hyp.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightyellow]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        contenu.append(table_hyp)

    # Pied de page
    contenu.append(Spacer(1, 1 * cm))
    contenu.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — HIPPO ANALYTICS v1.0",
        styles["Normal"],
    ))

    doc.build(contenu)
    logger.info(f"Rapport PDF généré : {chemin}")
    return str(chemin)


def exporter_historique_excel(db: Session, dossier: str = "./exports") -> str:
    """
    Exporte l'historique des prédictions vs résultats en Excel.

    Returns:
        Chemin du fichier Excel généré
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas non installé")

    Path(dossier).mkdir(parents=True, exist_ok=True)
    nom_fichier = f"historique_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    chemin = Path(dossier) / nom_fichier

    pronostics = db.query(Pronostic).order_by(Pronostic.date_generation.desc()).limit(200).all()

    donnees = []
    for p in pronostics:
        course = p.course
        arrivee = db.query(Arrivee).filter(Arrivee.course_id == p.course_id).first()

        top5_predit = p.top5_predit or []
        top5_reel = arrivee.classement_officiel[:5] if arrivee and arrivee.classement_officiel else []

        nb_communs = len(set(top5_predit) & set(top5_reel)) if top5_predit and top5_reel else None
        ordre_exact = top5_predit == top5_reel if top5_predit and top5_reel else None

        donnees.append({
            "Date": str(course.date_course) if course else None,
            "Course": f"R{course.reunion}C{course.numero_course}" if course else None,
            "Hippodrome": course.hippodrome if course else None,
            "Top5 Prédit": " - ".join(str(x) for x in top5_predit),
            "Top5 Réel": " - ".join(str(x) for x in top5_reel),
            "Chevaux Communs": nb_communs,
            "Ordre Exact": ordre_exact,
            "Méthode": p.methode_utilisee,
            "Date Prédiction": p.date_generation.strftime("%d/%m/%Y %H:%M") if p.date_generation else None,
        })

    df = pd.DataFrame(donnees)
    df.to_excel(chemin, index=False, sheet_name="Historique Prédictions")
    logger.info(f"Export Excel généré : {chemin}")
    return str(chemin)
