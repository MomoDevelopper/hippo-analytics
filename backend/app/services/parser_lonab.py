"""
Parseur spécialisé pour les programmes PMU Burkina Faso (LONAB).

Le journal hippique PMU'B contient typiquement :
- L'en-tête (date, hippodrome, réunion)
- Les fiches de courses (distance, conditions, allocation)
- Les fiches partants (numéro, nom, jockey, entraîneur, musique, cote)

Ce module gère le parsing de ces structures spécifiques.
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Structures de données
# ──────────────────────────────────────────────

@dataclass
class PartantPMU:
    numero: int
    nom_cheval: str
    jockey: Optional[str] = None
    entraineur: Optional[str] = None
    musique: Optional[str] = None
    cote: Optional[float] = None
    poids: Optional[float] = None
    age: Optional[int] = None
    sexe: Optional[str] = None
    proprietaire: Optional[str] = None


@dataclass
class CoursePMU:
    numero: int
    distance: Optional[int] = None
    conditions: Optional[str] = None
    allocation: Optional[float] = None
    type_piste: Optional[str] = "sable"
    partants: list[PartantPMU] = field(default_factory=list)


@dataclass
class ProgrammePMU:
    date: Optional[str] = None
    hippodrome: Optional[str] = None
    reunion: Optional[str] = None
    courses: list[CoursePMU] = field(default_factory=list)
    source_fichier: Optional[str] = None
    confiance: float = 0.0


# ──────────────────────────────────────────────
# Patterns de reconnaissance PMU Burkina Faso
# ──────────────────────────────────────────────

# Patterns de date
PATTERNS_DATE = [
    r"(\d{2})[/\-](\d{2})[/\-](\d{4})",
    r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
    r"(\d{4})[/\-](\d{2})[/\-](\d{2})",
]

MOIS_FR = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
}

# Hippodromes connus au Burkina Faso et en Afrique de l'Ouest
HIPPODROMES_BF = [
    "Ouagadougou", "Bobo-Dioulasso", "Bobo Dioulasso",
    "Koudougou", "Banfora", "Ouahigouya", "Dédougou",
    "Hippodrome de Ouagadougou", "Hippodrome Municipal",
]

# Patterns numéro de course
PATTERN_COURSE = re.compile(
    r"(?:COURSE|Prix|PRIX|C\.?)\s*(?:N[°º]?\s*)?(\d+)\b",
    re.IGNORECASE,
)

# Pattern partant : "1 NOM DU CHEVAL"
PATTERN_PARTANT = re.compile(
    r"^\s*(\d{1,2})\s+([A-ZÀÂÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÉÈÊËÎÏÔÙÛÜa-zàâéèêëîïôùûü\s'\-\.]{2,50}?)(?:\s{2,}|$)",
    re.MULTILINE,
)

# Pattern distance : "2100m", "2 100 m", "2.100 mètres"
PATTERN_DISTANCE = re.compile(r"(\d[\d\s\.]{0,4})\s*m(?:ètres?)?", re.IGNORECASE)

# Pattern cote : "4.5", "4/1", "4,5"
PATTERN_COTE = re.compile(r"(?:côte|cote|sp)?\s*(\d+)[.,/](\d+)", re.IGNORECASE)

# Pattern musique (ex: "1a3h5D0p" ou "3 1 2 0 4")
PATTERN_MUSIQUE = re.compile(r"[0-9][a-zA-Z0-9\s]{3,20}[a-zA-Z0-9]")

# Pattern allocation (dotation en FCFA ou €)
PATTERN_ALLOCATION = re.compile(
    r"(?:Alloc(?:ation)?|Dotation|Prix|Bourse)[:\s]*(\d[\d\s\.]{2,10})\s*(?:F\.?CFA|€|FCFA|francs?)?",
    re.IGNORECASE,
)


# ──────────────────────────────────────────────
# Fonctions d'extraction
# ──────────────────────────────────────────────

def _extraire_date(texte: str) -> Optional[str]:
    """Extrait et normalise la date au format YYYY-MM-DD."""
    for pattern in PATTERNS_DATE:
        match = re.search(pattern, texte, re.IGNORECASE)
        if not match:
            continue
        g = match.groups()
        try:
            if len(g) == 3:
                # Format JJ/MM/AAAA
                if g[0].isdigit() and g[1].isdigit() and g[2].isdigit():
                    if len(g[0]) == 4:  # AAAA-MM-JJ
                        return f"{g[0]}-{g[1]}-{g[2]}"
                    else:  # JJ/MM/AAAA
                        return f"{g[2]}-{g[1].zfill(2)}-{g[0].zfill(2)}"
                # Format JJ mois AAAA
                elif g[1].lower() in MOIS_FR:
                    mois = MOIS_FR[g[1].lower()]
                    return f"{g[2]}-{mois}-{int(g[0]):02d}"
        except Exception:
            continue
    return None


def _extraire_hippodrome(texte: str) -> Optional[str]:
    """Identifie l'hippodrome dans le texte."""
    for hippodrome in HIPPODROMES_BF:
        if hippodrome.lower() in texte.lower():
            return hippodrome
    # Chercher le mot "hippodrome" suivi d'un nom
    match = re.search(r"hippodrome\s+(?:de\s+)?([A-ZÀÂ][a-zàâéèêëîïôùûü\-]+)", texte, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extraire_distance(texte: str) -> Optional[int]:
    """Extrait la distance en mètres."""
    match = PATTERN_DISTANCE.search(texte)
    if match:
        valeur = match.group(1).replace(" ", "").replace(".", "")
        try:
            dist = int(valeur)
            if 400 <= dist <= 8000:  # Distances hippiques réalistes
                return dist
        except ValueError:
            pass
    return None


def _extraire_cote(texte: str) -> Optional[float]:
    """Extrait la cote d'un cheval."""
    match = PATTERN_COTE.search(texte)
    if match:
        try:
            entier = int(match.group(1))
            decimal = match.group(2)
            if "/" in match.group(0):
                # Format fraction 4/1 → 5.0
                return round(entier + 1, 2)
            return round(entier + int(decimal) / (10 ** len(decimal)), 2)
        except Exception:
            pass
    return None


def _parser_ligne_partant(ligne: str, numero: int) -> Optional[dict]:
    """
    Tente d'extraire les informations d'un partant depuis une ligne de texte.

    Structure typique d'une ligne PMU'B :
    N° NOM_CHEVAL  Jockey  Entraîneur  Musique  Cote
    1  DAKAR STAR  OUEDRAOGO  KABORE  2a1h3  4.5
    """
    parties = re.split(r"\s{2,}", ligne.strip())
    if len(parties) < 2:
        return None

    partant = {"numero": numero, "nom_cheval": None, "jockey": None,
               "entraineur": None, "musique": None, "cote": None}

    # Nom du cheval = 2ème champ (après le numéro) ou 1er si pas de numéro
    partant["nom_cheval"] = parties[0].strip().upper()

    if len(parties) >= 2:
        partant["jockey"] = parties[1].strip().title()
    if len(parties) >= 3:
        partant["entraineur"] = parties[2].strip().title()
    if len(parties) >= 4:
        # Musique ou cote
        val = parties[3].strip()
        cote = _extraire_cote(val)
        if cote:
            partant["cote"] = cote
        elif re.match(r"[0-9][a-zA-Z0-9]{2,}", val):
            partant["musique"] = val
    if len(parties) >= 5:
        cote = _extraire_cote(parties[4].strip())
        if cote:
            partant["cote"] = cote

    return partant


# ──────────────────────────────────────────────
# Parser principal
# ──────────────────────────────────────────────

def parser_programme_lonab(texte: str, source_fichier: Optional[str] = None) -> ProgrammePMU:
    """
    Parse le texte complet d'un programme PMU Burkina Faso (LONAB).

    Args:
        texte: Texte brut extrait du PDF ou du journal hippique
        source_fichier: Nom du fichier source (pour traçabilité)

    Returns:
        Instance ProgrammePMU avec toutes les données extraites
    """
    programme = ProgrammePMU(source_fichier=source_fichier)

    # ── En-tête du programme
    programme.date = _extraire_date(texte)
    programme.hippodrome = _extraire_hippodrome(texte)

    match_reunion = re.search(r"R[ÉEé]UNION\s*N?[°º]?\s*(\d+)|(?<!\w)R(\d)\b", texte, re.IGNORECASE)
    if match_reunion:
        num = match_reunion.group(1) or match_reunion.group(2)
        programme.reunion = f"R{num}"

    # ── Découpage en blocs de courses
    lignes = texte.split("\n")
    course_courante: Optional[CoursePMU] = None
    mode_partants = False
    compteur_partant = 0

    for i, ligne in enumerate(lignes):
        ligne_nettoyee = ligne.strip()
        if not ligne_nettoyee:
            continue

        # ── Détection d'un nouveau bloc de course
        match_course = PATTERN_COURSE.search(ligne_nettoyee)
        if match_course:
            numero_course = int(match_course.group(1))
            course_courante = CoursePMU(numero=numero_course)
            programme.courses.append(course_courante)
            mode_partants = False
            compteur_partant = 0

            # Distance dans la même ligne
            dist = _extraire_distance(ligne_nettoyee)
            if dist:
                course_courante.distance = dist

            # Allocation dans la même ligne
            match_alloc = PATTERN_ALLOCATION.search(ligne_nettoyee)
            if match_alloc:
                try:
                    val = match_alloc.group(1).replace(" ", "").replace(".", "")
                    course_courante.allocation = float(val)
                except ValueError:
                    pass
            continue

        if course_courante is None:
            continue

        # ── Distance si trouvée après la déclaration de course
        if not course_courante.distance:
            dist = _extraire_distance(ligne_nettoyee)
            if dist:
                course_courante.distance = dist

        # ── Détection du début de la liste des partants
        if re.match(r"^\s*(?:PARTANTS?|ENGAGÉS?|N[°º]\s+NOM)", ligne_nettoyee, re.IGNORECASE):
            mode_partants = True
            continue

        # ── Parsing des partants
        match_num = re.match(r"^\s*(\d{1,2})\s+(.+)", ligne_nettoyee)
        if match_num or mode_partants:
            if match_num:
                numero = int(match_num.group(1))
                if 1 <= numero <= 20:
                    mode_partants = True
                    reste = match_num.group(2)
                    info = _parser_ligne_partant(reste, numero)
                    if info and info["nom_cheval"]:
                        partant = PartantPMU(
                            numero=numero,
                            nom_cheval=info["nom_cheval"],
                            jockey=info.get("jockey"),
                            entraineur=info.get("entraineur"),
                            musique=info.get("musique"),
                            cote=info.get("cote"),
                        )
                        course_courante.partants.append(partant)
                        compteur_partant += 1

    # ── Calcul de la confiance d'extraction
    confiance = 0.0
    if programme.date:
        confiance += 25
    if programme.hippodrome:
        confiance += 15
    if programme.reunion:
        confiance += 15
    if programme.courses:
        confiance += 20
        nb_partants = sum(len(c.partants) for c in programme.courses)
        if nb_partants >= 8:
            confiance += 15
        if nb_partants >= 16:
            confiance += 10

    programme.confiance = confiance

    logger.info(
        f"Programme PMU'B parsé — Date: {programme.date}, "
        f"Hippodrome: {programme.hippodrome}, "
        f"{len(programme.courses)} course(s), "
        f"Confiance: {confiance:.0f}%"
    )
    return programme


def programme_vers_dict(programme: ProgrammePMU) -> dict:
    """Convertit un ProgrammePMU en dictionnaire JSON sérialisable."""
    return {
        "date": programme.date,
        "hippodrome": programme.hippodrome,
        "reunion": programme.reunion,
        "confiance": programme.confiance,
        "source": programme.source_fichier,
        "courses": [
            {
                "numero": c.numero,
                "distance": c.distance,
                "type_piste": c.type_piste,
                "allocation": c.allocation,
                "conditions": c.conditions,
                "partants": [
                    {
                        "numero": p.numero,
                        "nom_cheval": p.nom_cheval,
                        "jockey": p.jockey,
                        "entraineur": p.entraineur,
                        "musique": p.musique,
                        "cote": p.cote,
                        "poids": p.poids,
                        "age": p.age,
                        "sexe": p.sexe,
                    }
                    for p in c.partants
                ],
            }
            for c in programme.courses
        ],
    }
