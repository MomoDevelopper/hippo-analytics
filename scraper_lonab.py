"""
Scraper historique LONAB / PMU Burkina Faso.

Collecte les programmes et résultats officiels disponibles
sur le site lonab.bf pour alimenter la base de données d'entraînement.

Usage :
    python scraper_lonab.py --output data/historique.json
    python scraper_lonab.py --test   (tente une connexion et affiche ce qu'on trouve)
"""
import sys
import json
import time
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scraper_lonab")

# ── Configuration ─────────────────────────────────────────
BASE_URL = "https://www.lonab.bf"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
DELAI_REQUETES = 2.0   # Secondes entre chaque requête (respectueux du serveur)
TIMEOUT = 20

# Chemins à tester sur le site LONAB
CHEMINS_PMU = [
    "/pmu",
    "/pmub",
    "/pmu-b",
    "/programmes",
    "/programmes-pmub",
    "/hippique",
    "/courses",
    "/resultats",
    "/arrivees",
    "/gains",
    "/",
]


# ── Utilitaires ───────────────────────────────────────────

def requete_safe(url: str, session: requests.Session) -> Optional[requests.Response]:
    """Effectue une requête HTTP avec gestion d'erreur et délai."""
    try:
        time.sleep(DELAI_REQUETES)
        resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        logger.info(f"  GET {url} → HTTP {resp.status_code}")
        return resp if resp.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        logger.warning(f"  ✗ Connexion impossible : {url}")
        return None
    except requests.exceptions.Timeout:
        logger.warning(f"  ✗ Timeout : {url}")
        return None
    except Exception as e:
        logger.error(f"  ✗ Erreur : {e}")
        return None


def extraire_liens_pdf(html: str, base_url: str) -> list[dict]:
    """Extrait tous les liens vers des fichiers PDF depuis une page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    liens = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        texte = tag.get_text(strip=True)

        if not href.lower().endswith(".pdf"):
            continue

        # Construire l'URL absolue
        if href.startswith("http"):
            url_absolue = href
        elif href.startswith("/"):
            url_absolue = f"{base_url.rstrip('/')}{href}"
        else:
            url_absolue = f"{base_url.rstrip('/')}/{href}"

        liens.append({
            "url": url_absolue,
            "texte": texte,
            "type": _classifier_pdf(texte + " " + href),
        })

    return liens


def _classifier_pdf(texte: str) -> str:
    """Classifie un PDF comme programme ou résultat."""
    texte_lower = texte.lower()
    if any(m in texte_lower for m in ["programme", "journal", "partant", "pmub", "pmu"]):
        return "programme"
    if any(m in texte_lower for m in ["arrivée", "arrivee", "résultat", "resultat", "gain"]):
        return "resultat"
    return "inconnu"


def analyser_page_lonab(html: str) -> dict:
    """Analyse le contenu d'une page LONAB pour extraire les informations disponibles."""
    soup = BeautifulSoup(html, "html.parser")

    # Navigation / menu
    menus = []
    for nav in soup.find_all(["nav", "ul", "menu"]):
        for lien in nav.find_all("a", href=True):
            texte = lien.get_text(strip=True)
            if texte and len(texte) > 2:
                menus.append({"texte": texte, "href": lien["href"]})

    # Contenu principal
    contenu = soup.get_text(separator=" ", strip=True)[:3000]

    # Sections hippiques
    mots_hippo = ["pmu", "hippique", "course", "partant", "arrivée", "tiercé",
                  "quarté", "jockey", "programme", "résultat"]
    sections_hippo = {m: m.lower() in contenu.lower() for m in mots_hippo}

    return {
        "titre": soup.title.string if soup.title else "Sans titre",
        "nb_liens": len(soup.find_all("a")),
        "nb_pdfs": len([a for a in soup.find_all("a", href=True)
                        if a["href"].lower().endswith(".pdf")]),
        "menus": menus[:20],
        "mots_hippiques_detectes": {m: v for m, v in sections_hippo.items() if v},
        "extrait_contenu": contenu[:500],
    }


# ── Scraping principal ────────────────────────────────────

def tester_connexion_lonab() -> dict:
    """
    Test de connexion à lonab.bf — cartographie ce qui est disponible.
    Retourne un rapport complet sans télécharger de PDFs.
    """
    logger.info("=" * 55)
    logger.info("HIPPO ANALYTICS — Test connexion LONAB")
    logger.info(f"Cible : {BASE_URL}")
    logger.info("=" * 55)

    session = requests.Session()
    rapport = {
        "timestamp": datetime.now().isoformat(),
        "site": BASE_URL,
        "accessible": False,
        "pages_trouvees": [],
        "pdfs_trouves": [],
        "erreur": None,
    }

    # Test de la page d'accueil
    logger.info(f"\n[1] Test de la page d'accueil...")
    resp = requete_safe(BASE_URL, session)

    if not resp:
        rapport["erreur"] = f"Site {BASE_URL} inaccessible depuis ce réseau"
        logger.error(rapport["erreur"])
        logger.info("\n💡 Solutions possibles :")
        logger.info("   • Vérifiez votre connexion Internet")
        logger.info("   • Le site lonab.bf est peut-être temporairement hors-ligne")
        logger.info("   • Vous pouvez importer les programmes PDF manuellement")
        return rapport

    rapport["accessible"] = True
    analyse = analyser_page_lonab(resp.text)
    logger.info(f"   Titre : {analyse['titre']}")
    logger.info(f"   Liens trouvés : {analyse['nb_liens']}")
    logger.info(f"   PDFs directs : {analyse['nb_pdfs']}")
    logger.info(f"   Mots hippiques : {list(analyse['mots_hippiques_detectes'].keys())}")

    rapport["pages_trouvees"].append({
        "url": BASE_URL,
        "analyse": analyse,
    })

    # Exploration des sous-pages PMU
    logger.info(f"\n[2] Exploration des sous-pages PMU...")
    pdfs_total = []

    for chemin in CHEMINS_PMU:
        url = f"{BASE_URL}{chemin}"
        if url == BASE_URL:
            continue

        resp_page = requete_safe(url, session)
        if not resp_page:
            continue

        analyse_page = analyser_page_lonab(resp_page.text)
        pdfs_page = extraire_liens_pdf(resp_page.text, BASE_URL)

        logger.info(f"   {chemin} → {analyse_page['nb_pdfs']} PDF(s), "
                    f"mots hippiques: {list(analyse_page['mots_hippiques_detectes'].keys())}")

        if pdfs_page:
            logger.info(f"      PDFs trouvés :")
            for pdf in pdfs_page[:5]:
                logger.info(f"        [{pdf['type']}] {pdf['texte']} → {pdf['url']}")
            pdfs_total.extend(pdfs_page)

        if analyse_page["nb_pdfs"] > 0 or analyse_page["mots_hippiques_detectes"]:
            rapport["pages_trouvees"].append({
                "url": url,
                "analyse": analyse_page,
            })

    # Dédoublonnage PDFs
    urls_vus = set()
    for pdf in pdfs_total:
        if pdf["url"] not in urls_vus:
            rapport["pdfs_trouves"].append(pdf)
            urls_vus.add(pdf["url"])

    logger.info(f"\n[3] Résumé :")
    logger.info(f"   Pages analysées : {len(rapport['pages_trouvees'])}")
    logger.info(f"   PDFs uniques trouvés : {len(rapport['pdfs_trouves'])}")

    if rapport["pdfs_trouves"]:
        logger.info(f"\n   ✅ PDFs disponibles :")
        for pdf in rapport["pdfs_trouves"]:
            logger.info(f"      [{pdf['type']}] {pdf['url']}")
    else:
        logger.info("\n   ⚠️  Aucun PDF trouvé directement.")
        logger.info("       Le site utilise peut-être JavaScript dynamique")
        logger.info("       ou les programmes ne sont pas publics en PDF.")

    return rapport


def telecharger_historique(
    dossier_sortie: str = "data/programmes",
    max_pdfs: int = 50,
) -> dict:
    """
    Télécharge les programmes et résultats PMU'B disponibles sur LONAB.

    Args:
        dossier_sortie: Dossier local pour les PDFs téléchargés
        max_pdfs: Nombre maximum de PDFs à télécharger

    Returns:
        Rapport de téléchargement
    """
    Path(dossier_sortie).mkdir(parents=True, exist_ok=True)

    logger.info(f"\n[4] Téléchargement vers : {dossier_sortie}")

    # D'abord tester la connexion
    rapport_connexion = tester_connexion_lonab()

    rapport = {
        "timestamp": datetime.now().isoformat(),
        "accessible": rapport_connexion["accessible"],
        "pdfs_telecharges": [],
        "erreurs": [],
    }

    if not rapport_connexion["accessible"]:
        rapport["erreur"] = rapport_connexion["erreur"]
        return rapport

    session = requests.Session()
    nb_telecharges = 0

    for pdf_info in rapport_connexion["pdfs_trouves"][:max_pdfs]:
        url = pdf_info["url"]
        try:
            time.sleep(DELAI_REQUETES)
            resp = session.get(url, headers=HEADERS, timeout=30, stream=True)
            resp.raise_for_status()

            # Nom de fichier propre
            nom = url.split("/")[-1] or f"lonab_{nb_telecharges:03d}.pdf"
            nom = re.sub(r"[^\w\-.]", "_", nom)
            chemin = Path(dossier_sortie) / nom

            if not chemin.exists():
                chemin.write_bytes(resp.content)
                taille = len(resp.content)
                logger.info(f"   ✅ Téléchargé : {nom} ({taille // 1024} Ko)")
                rapport["pdfs_telecharges"].append({
                    "fichier": str(chemin),
                    "url": url,
                    "type": pdf_info["type"],
                    "taille_ko": taille // 1024,
                })
                nb_telecharges += 1
            else:
                logger.info(f"   ⏭  Déjà présent : {nom}")

        except Exception as e:
            erreur = f"Erreur téléchargement {url}: {e}"
            rapport["erreurs"].append(erreur)
            logger.warning(f"   ✗ {erreur}")

    logger.info(f"\n   {nb_telecharges} PDF(s) téléchargé(s)")
    return rapport


# ── Données de démo pour tests locaux ────────────────────

def generer_donnees_demo() -> dict:
    """
    Génère des données de démonstration réalistes pour tester
    le moteur de prédiction sans connexion à LONAB.

    Basé sur la structure réelle des programmes PMU'B.
    """
    import random
    random.seed(42)

    # Noms de chevaux inspirés du style PMU Burkina Faso
    NOMS_CHEVAUX = [
        "VOLTA EXPRESS", "FASO PRIDE", "DAKAR STAR", "BELLE DE NUIT",
        "CHAMPION DU LAC", "SAHEL FORCE", "BANI RIVER", "MOUHOUN STAR",
        "OUAGA DREAM", "ZINGO POWER", "CASCADES GOLD", "BOBO FLASH",
        "SISSILI EXPRESS", "GNAGNA WIND", "KAYA PRIDE", "FADA THUNDER",
        "KOMBISSIRI STAR", "MANGA DREAM", "TENKODOGO ACE", "KOUDOUGOU WIND",
        "DORI EXPRESS", "OUAHIGOUYA GOLD", "BANFORA STAR", "GAOUA PRIDE",
        "DIEBOUGOU WIND", "BATIÉ EXPRESS", "TOUGAN STAR", "NOUNA GOLD",
        "DEDOUGOU DREAM", "LEO POWER", "SAPOUY WIND", "PO EXPRESS",
    ]

    JOCKEYS = [
        "OUEDRAOGO S.", "TRAORE B.", "SAWADOGO R.", "KINDA A.",
        "NIKIEMA P.", "BARRO M.", "COULIBALY I.", "ZONGO F.",
        "KABORE L.", "SOME D.", "TAPSOBA C.", "ZERBO H.",
        "OUATTARA N.", "RABO J.", "BIKIENGA T.", "COMPAORE Y.",
    ]

    ENTRAINEURS = [
        "KABORE A.", "SAWADOGO F.", "TRAORE M.", "OUEDRAOGO R.",
        "BARRO S.", "NIKIEMA L.", "ZONGO P.", "COULIBALY C.",
    ]

    HIPPODROMES = ["Ouagadougou", "Bobo-Dioulasso", "Koudougou"]
    DISTANCES = [1600, 1800, 2000, 2100, 2200, 2400]

    donnees = {
        "source": "demo_genere",
        "description": "Données de démonstration — structure PMU Burkina Faso",
        "courses": [],
    }

    chevaux_pool = random.sample(NOMS_CHEVAUX, min(len(NOMS_CHEVAUX), 32))

    # Générer 60 jours d'historique (3-4 courses par semaine)
    date_debut = date.today() - timedelta(days=60)
    course_id = 1

    for nb_jours in range(60):
        date_course = date_debut + timedelta(days=nb_jours)

        # Environ 3 courses par semaine (lundi, mercredi, samedi)
        if date_course.weekday() not in [0, 2, 5]:
            continue

        hippodrome = random.choice(HIPPODROMES)
        nb_partants = random.randint(8, 14)
        distance = random.choice(DISTANCES)

        # Sélectionner les partants
        partants_indices = random.sample(range(len(chevaux_pool)), nb_partants)

        # Générer les cotes (distribution réaliste)
        cotes_base = sorted(
            [round(random.uniform(1.5, 25.0), 1) for _ in range(nb_partants)]
        )

        # Simuler un ordre d'arrivée basé sur les cotes (favoris gagnent plus souvent)
        # Les chevaux avec les plus petites cotes ont plus de chances
        poids_arrivee = [1 / c for c in cotes_base]
        total = sum(poids_arrivee)
        probas = [p / total for p in poids_arrivee]

        # Tirage avec bruit aléatoire (surprises possibles)
        bruit = [p + random.uniform(-0.03, 0.03) for p in probas]
        bruit = [max(0.001, b) for b in bruit]
        total_bruit = sum(bruit)
        probas_finales = [b / total_bruit for b in bruit]

        # Ordre d'arrivée
        import numpy as np
        indices_arrives = list(np.random.choice(
            nb_partants, nb_partants, replace=False, p=probas_finales
        ))

        partants = []
        for rang, idx in enumerate(partants_indices):
            nom = chevaux_pool[idx]
            partants.append({
                "numero": rang + 1,
                "nom_cheval": nom,
                "jockey": random.choice(JOCKEYS),
                "entraineur": random.choice(ENTRAINEURS),
                "cote": cotes_base[rang],
                "musique": _generer_musique(),
                "age": random.randint(3, 8),
                "sexe": random.choice(["M", "F", "H"]),
            })

        arrivee_officielle = [partants[i]["numero"] for i in indices_arrives]

        donnees["courses"].append({
            "id": course_id,
            "date": str(date_course),
            "reunion": "R1",
            "numero_course": 1,
            "hippodrome": hippodrome,
            "distance": distance,
            "type_piste": "sable",
            "nb_partants": nb_partants,
            "partants": partants,
            "arrivee_officielle": arrivee_officielle[:5],  # Top 5 officiel
        })
        course_id += 1

    logger.info(f"Données de démo générées : {len(donnees['courses'])} courses")
    return donnees


def _generer_musique() -> str:
    """Génère une musique hippique réaliste (ex: '1a2h3p0D')."""
    import random
    types = ["a", "h", "p", "D", "0", "s"]
    longueur = random.randint(4, 8)
    musique = ""
    for _ in range(longueur):
        chiffre = random.randint(0, 9)
        lettre = random.choice(types)
        musique += f"{chiffre}{lettre}"
    return musique


# ── Point d'entrée ────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper LONAB — HIPPO ANALYTICS")
    parser.add_argument("--test", action="store_true",
                        help="Tester la connexion LONAB sans télécharger")
    parser.add_argument("--demo", action="store_true",
                        help="Générer des données de démonstration locales")
    parser.add_argument("--download", action="store_true",
                        help="Télécharger les programmes disponibles")
    parser.add_argument("--output", default="data",
                        help="Dossier de sortie (défaut: data/)")
    parser.add_argument("--max", type=int, default=50,
                        help="Nombre maximum de PDFs à télécharger")
    args = parser.parse_args()

    Path(args.output).mkdir(parents=True, exist_ok=True)

    if args.demo:
        logger.info("Génération des données de démonstration...")
        donnees = generer_donnees_demo()
        sortie = Path(args.output) / "demo_historique.json"
        with open(sortie, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Données sauvegardées : {sortie}")
        logger.info(f"   {len(donnees['courses'])} courses générées")
        sys.exit(0)

    if args.test:
        rapport = tester_connexion_lonab()
        sortie = Path(args.output) / "rapport_connexion.json"
        with open(sortie, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ Rapport sauvegardé : {sortie}")
        sys.exit(0 if rapport["accessible"] else 1)

    if args.download:
        rapport = telecharger_historique(
            dossier_sortie=str(Path(args.output) / "programmes"),
            max_pdfs=args.max,
        )
        sortie = Path(args.output) / "rapport_telechargement.json"
        with open(sortie, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ Rapport sauvegardé : {sortie}")
        sys.exit(0)

    # Par défaut : afficher l'aide
    parser.print_help()
