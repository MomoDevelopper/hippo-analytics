"""
HIPPO ANALYTICS — Chargement des données et entraînement du modèle IA.

Ce script :
1. Génère (ou charge depuis fichier) les données historiques
2. Les insère en base de données SQLite (ou PostgreSQL)
3. Lance l'entraînement XGBoost
4. Affiche les métriques de performance

Usage :
    python charger_et_entrainer.py --demo          (données de démonstration)
    python charger_et_entrainer.py --json data/historique.json  (fichier scraped)
    python charger_et_entrainer.py --demo --runs 50000          (simulation réduite)
"""
import sys
import os
import json
import logging
import argparse
import io
from pathlib import Path
from datetime import datetime

# ── Fix encodage Windows ─────────────────────────────────
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Configuration base de données ────────────────────────
# Utilise SQLite par défaut pour les tests locaux
# En production : remplacer par l'URL PostgreSQL dans .env
DB_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./hippo_data.db"
)
os.environ["DATABASE_URL"] = DB_URL
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "hippo_training_key")
os.environ.setdefault("SYNC_INTERVAL_HOURS", "999")  # Pas de sync en mode script

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("charger_entrainer")

# ── Ajouter le backend au path Python ────────────────────
sys.path.insert(0, str(Path(__file__).parent / "backend"))


def ok(msg):  print(f"  OK  {msg}")
def info(msg): print(f"  >>  {msg}")
def warn(msg): print(f"  !!  {msg}")
def err(msg):  print(f"  XX  {msg}")
def titre(msg): print(f"\n{'='*55}\n  {msg}\n{'='*55}")


# ── Étape 1 : Initialiser la base de données ─────────────

def initialiser_db():
    titre("1. Initialisation de la base de données")
    info(f"URL : {DB_URL}")

    from app.database import create_tables, reset_engine
    reset_engine()
    create_tables()
    ok("Tables créées avec succès !")

    from app.database import _get_session_local
    return _get_session_local()


# ── Étape 2 : Charger les données ─────────────────────────

def charger_donnees_demo():
    """Génère des données de démonstration PMU Burkina Faso."""
    titre("2. Génération des données de démonstration")
    info("Génération de 60 jours d'historique PMU'B...")

    # Importer le générateur depuis le scraper
    sys.path.insert(0, str(Path(__file__).parent))
    from scraper_lonab import generer_donnees_demo
    donnees = generer_donnees_demo()

    nb_courses = len(donnees["courses"])
    nb_partants = sum(len(c["partants"]) for c in donnees["courses"])
    ok(f"{nb_courses} courses générées, {nb_partants} partants au total")
    return donnees


def charger_donnees_json(chemin: str):
    """Charge les données depuis un fichier JSON (scraper LONAB)."""
    titre("2. Chargement des données JSON")
    info(f"Fichier : {chemin}")

    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    # Normaliser si c'est le format du rapport de connexion
    if "courses" not in donnees and "pdfs_trouves" in donnees:
        err("Ce fichier est un rapport de connexion, pas des données de courses.")
        err("Utilisez --demo ou fournissez un fichier avec 'courses'.")
        sys.exit(1)

    nb_courses = len(donnees.get("courses", []))
    ok(f"{nb_courses} courses chargées depuis {chemin}")
    return donnees


# ── Étape 3 : Insérer en base de données ─────────────────

def inserer_en_db(donnees: dict, SessionLocal):
    """Insère les données historiques en base de données."""
    titre("3. Insertion en base de données")

    from app.models.entraineur import Entraineur
    from app.models.jockey import Jockey
    from app.models.cheval import Cheval
    from app.models.course import Course
    from app.models.partant import Partant
    from app.models.performance import Performance
    from app.models.arrivee import Arrivee

    db = SessionLocal()

    try:
        # Compteurs
        nb_entraineurs = nb_jockeys = nb_chevaux = nb_courses = nb_partants = 0

        # Registres pour éviter les doublons
        entraineurs_map = {}  # nom -> Entraineur
        jockeys_map = {}      # nom -> Jockey
        chevaux_map = {}      # nom -> Cheval

        courses_data = donnees.get("courses", [])
        total = len(courses_data)

        for i, course_data in enumerate(courses_data, 1):
            if i % 5 == 0 or i == total:
                info(f"  Progression : {i}/{total} courses...")

            # ── Créer la course ──────────────────────────────
            # Parsing de la date
            date_str = course_data.get("date", "")
            try:
                from datetime import date
                date_obj = date.fromisoformat(date_str) if date_str else date.today()
            except ValueError:
                date_obj = datetime.today().date()

            course = Course(
                date_course=date_obj,
                reunion=course_data.get("reunion", "R1"),
                numero_course=course_data.get("numero_course", i),
                hippodrome=course_data.get("hippodrome", "Ouagadougou"),
                distance=course_data.get("distance", 2000),
                type_piste="sable",
                conditions=course_data.get("conditions", ""),
                nombre_partants=len(course_data.get("partants", [])),
                statut="terminée",
                programme_source=course_data.get("source", "demo"),
            )
            db.add(course)
            db.flush()  # Pour obtenir l'ID
            nb_courses += 1

            # ── Partants ─────────────────────────────────────
            # Note : l'arrivée sera créée APRÈS les partants (besoin des cheval_ids)
            arrivee_data_brut = course_data.get("arrivee_officielle", course_data.get("arrivee", []))
            partants_data = course_data.get("partants", [])
            partants_en_course = []  # (Partant, Cheval, Jockey) dans l'ordre de partants_data

            for p_data in partants_data:
                nom_cheval = p_data.get("nom_cheval", "INCONNU")
                nom_jockey = p_data.get("jockey", "INCONNU")
                nom_entraineur = p_data.get("entraineur", "INCONNU")

                # Entraineur
                if nom_entraineur not in entraineurs_map:
                    # Chercher en DB
                    ent = db.query(Entraineur).filter(
                        Entraineur.nom == nom_entraineur
                    ).first()
                    if not ent:
                        ent = Entraineur(nom=nom_entraineur, prenom="", nationalite="BF")
                        db.add(ent)
                        db.flush()
                        nb_entraineurs += 1
                    entraineurs_map[nom_entraineur] = ent
                entraineur = entraineurs_map[nom_entraineur]

                # Jockey
                if nom_jockey not in jockeys_map:
                    jky = db.query(Jockey).filter(Jockey.nom == nom_jockey).first()
                    if not jky:
                        jky = Jockey(nom=nom_jockey, prenom="", nationalite="BF")
                        db.add(jky)
                        db.flush()
                        nb_jockeys += 1
                    jockeys_map[nom_jockey] = jky
                jockey = jockeys_map[nom_jockey]

                # Cheval
                if nom_cheval not in chevaux_map:
                    chv = db.query(Cheval).filter(Cheval.nom == nom_cheval).first()
                    if not chv:
                        chv = Cheval(
                            nom=nom_cheval,
                            age=p_data.get("age", 4),
                            sexe=p_data.get("sexe", "M"),
                            robe="bai",
                            origine="",
                            entraineur_id=entraineur.id,
                        )
                        db.add(chv)
                        db.flush()
                        nb_chevaux += 1
                    chevaux_map[nom_cheval] = chv
                cheval = chevaux_map[nom_cheval]

                # Partant dans la course
                partant = Partant(
                    course_id=course.id,
                    cheval_id=cheval.id,
                    jockey_id=jockey.id,
                    numero_partant=p_data.get("numero", 1),
                    poids=p_data.get("poids", 60),
                    handicap=0,
                    musique=p_data.get("musique", ""),
                    cote_depart=p_data.get("cote", 5.0),
                    non_partant=False,
                )
                db.add(partant)
                db.flush()
                nb_partants += 1
                partants_en_course.append((partant, cheval, jockey))

            # ── Arrivée officielle avec cheval_ids réels ──────
            # Le modèle XGBoost cherche des cheval_ids dans classement_officiel
            # arrivee_data_brut : liste d'indices 1-based ou 0-based des partants dans l'ordre
            if arrivee_data_brut:
                classement_cheval_ids = []
                for idx_partant_raw in arrivee_data_brut:
                    # Convertir en 0-based si nécessaire
                    idx_partant = idx_partant_raw - 1 if idx_partant_raw >= 1 else idx_partant_raw
                    if 0 <= idx_partant < len(partants_en_course):
                        _, cheval_arr, _ = partants_en_course[idx_partant]
                        classement_cheval_ids.append(cheval_arr.id)

                if classement_cheval_ids:
                    arrivee = Arrivee(
                        course_id=course.id,
                        # classement_officiel = liste ordonnée de cheval_ids (1er → dernier)
                        classement_officiel=classement_cheval_ids,
                        classement_detaille=[],
                        source="demo",
                    )
                    db.add(arrivee)

            # ── Performances (résultats historiques) ─────────
            if arrivee_data_brut:
                for rang_0base, idx_partant_raw in enumerate(arrivee_data_brut):
                    # Convertir en 0-based si nécessaire
                    idx_partant = idx_partant_raw - 1 if idx_partant_raw >= 1 else idx_partant_raw
                    if 0 <= idx_partant < len(partants_en_course):
                        partant, cheval, jockey = partants_en_course[idx_partant]
                        perf = Performance(
                            cheval_id=cheval.id,
                            course_id=course.id,
                            jockey_id=jockey.id,
                            date_course=course.date_course,  # champ obligatoire
                            place_officielle=rang_0base + 1,
                            partants_total=len(partants_en_course),
                            distance=course.distance,
                            hippodrome=course.hippodrome,
                            type_piste=course.type_piste,
                            temps=None,
                            ecart=None,
                            cote_depart=partant.cote_depart,
                            gains=0,
                        )
                        db.add(perf)

        # Commit final
        db.commit()

        print()
        ok(f"Entraineurs insertés : {nb_entraineurs}")
        ok(f"Jockeys insérés      : {nb_jockeys}")
        ok(f"Chevaux insérés      : {nb_chevaux}")
        ok(f"Courses insérées     : {nb_courses}")
        ok(f"Partants insérés     : {nb_partants}")

        return db

    except Exception as e:
        db.rollback()
        err(f"Erreur lors de l'insertion : {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        pass  # On garde la session ouverte pour l'entraînement


# ── Étape 4 : Entraîner le modèle XGBoost ────────────────

def entrainer_modele(SessionLocal, nb_jours: int = 365):
    """Lance l'entraînement du modèle XGBoost sur les données chargées."""
    titre("4. Entraînement du modèle XGBoost")
    info(f"Période d'entraînement : {nb_jours} derniers jours")

    db = SessionLocal()

    try:
        from app.services.modele_ia import entrainer_modele as ia_entrainer

        info("Entraînement en cours (peut prendre quelques secondes)...")
        resultat = ia_entrainer(db, nb_jours_historique=nb_jours)

        if resultat.get("succes"):
            ok(f"Modèle entraîné avec succès !")
            ok(f"Courses utilisées     : {resultat.get('nb_courses', 'N/A')}")
            ok(f"Partants analysés     : {resultat.get('nb_partants', 'N/A')}")
            ok(f"Précision top-1       : {resultat.get('precision_top1', 0):.1%}")
            ok(f"Précision top-3       : {resultat.get('precision_top3', 0):.1%}")
            ok(f"Précision top-5       : {resultat.get('precision_top5', 0):.1%}")
            if "chemin_modele" in resultat:
                ok(f"Modèle sauvegardé    : {resultat['chemin_modele']}")
        else:
            msg = resultat.get("message", "Erreur inconnue")
            warn(f"Entraînement incomplet : {msg}")
            if "minimum" in msg.lower() or "données" in msg.lower():
                warn("Pas assez de données avec résultats officiels.")
                warn("Conseil : ajoutez des arrivées officielles ou utilisez --demo avec plus de jours.")

        return resultat

    except Exception as e:
        err(f"Erreur d'entraînement : {e}")
        import traceback; traceback.print_exc()
        return {"succes": False, "erreur": str(e)}
    finally:
        db.close()


# ── Étape 5 : Test de prédiction ─────────────────────────

def tester_prediction(SessionLocal):
    """Lance une prédiction de démonstration sur la première course disponible."""
    titre("5. Test de prédiction sur la première course")

    db = SessionLocal()
    try:
        from app.models.course import Course
        from app.models.partant import Partant
        from app.services.prediction import predire_course

        # Trouver une course avec des partants
        course = db.query(Course).join(Partant).filter(
            Partant.non_partant == False
        ).first()

        if not course:
            warn("Aucune course avec partants en base — saut du test de prédiction.")
            return

        info(f"Course sélectionnée : {course.hippodrome} — {course.date_course} — {course.distance}m")
        nb_p = db.query(Partant).filter(Partant.course_id == course.id).count()
        info(f"Nombre de partants : {nb_p}")

        info("Lancement de la prédiction Monte Carlo (100 000 simulations)...")
        import time
        t0 = time.time()
        resultat = predire_course(course.id, db, n_runs=100_000)
        duree = time.time() - t0

        ok(f"Prédiction terminée en {duree:.1f}s")

        if resultat and resultat.get("top5"):
            print("\n  Top 5 prédit :")
            for rang, item in enumerate(resultat["top5"][:5], 1):
                nom = item.get("nom_cheval", f"Cheval #{item.get('cheval_id', '?')}")
                prob = item.get("probabilite_victoire", 0)
                note = item.get("note_globale", 0)
                print(f"    {rang}. {nom:<25} | Note: {note:5.1f} | P(victoire): {prob:.1%}")

        if resultat and resultat.get("top_hypotheses"):
            print("\n  Top 5 hypothèses :")
            for rang, hyp in enumerate(resultat["top_hypotheses"][:5], 1):
                ordre = " → ".join([f"#{n}" for n in hyp.get("ordre", [])])
                prob = hyp.get("probabilite", 0)
                print(f"    #{rang} | {ordre} | {prob:.3%}")

    except Exception as e:
        err(f"Erreur de prédiction : {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


# ── Point d'entrée principal ──────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="HIPPO ANALYTICS — Chargement données + Entraînement modèle"
    )
    parser.add_argument("--demo", action="store_true",
                        help="Utiliser les données de démonstration générées")
    parser.add_argument("--json", metavar="FICHIER",
                        help="Chemin vers un fichier JSON de données scrapées")
    parser.add_argument("--db", metavar="URL",
                        help="URL de base de données (défaut: SQLite local)")
    parser.add_argument("--jours", type=int, default=365,
                        help="Nombre de jours d'historique pour l'entraînement")
    parser.add_argument("--sans-entrainement", action="store_true",
                        help="Insérer les données sans entraîner le modèle")
    parser.add_argument("--sans-prediction", action="store_true",
                        help="Ne pas lancer le test de prédiction")
    args = parser.parse_args()

    print()
    print("=" * 55)
    print("  HIPPO ANALYTICS — Chargement & Entraînement")
    print("  PMU Burkina Faso (LONAB)")
    print("=" * 55)

    # Priorité DB depuis argument
    if args.db:
        os.environ["DATABASE_URL"] = args.db
        global DB_URL
        DB_URL = args.db

    if not args.demo and not args.json:
        warn("Aucune source de données spécifiée.")
        warn("Utilisez --demo pour des données de démo, ou --json FICHIER.")
        print()
        parser.print_help()
        sys.exit(1)

    try:
        # Étape 1 : DB
        SessionLocal = initialiser_db()

        # Étape 2 : Données
        if args.demo:
            donnees = charger_donnees_demo()
        else:
            donnees = charger_donnees_json(args.json)

        # Étape 3 : Insertion
        inserer_en_db(donnees, SessionLocal)

        # Étape 4 : Entraînement
        if not args.sans_entrainement:
            entrainer_modele(SessionLocal, nb_jours=args.jours)

        # Étape 5 : Test
        if not args.sans_prediction:
            tester_prediction(SessionLocal)

        # Résumé final
        titre("TERMINÉ")
        ok("Base de données chargée avec succès !")
        ok("Modèle IA entraîné !")
        print()
        info("Pour lancer l'API complète :")
        print("    cd backend")
        print("    uvicorn app.main:app --reload --port 8000")
        print()
        info("Ou avec Docker :")
        print("    docker-compose up -d")
        print()

    except KeyboardInterrupt:
        warn("\nInterrompu par l'utilisateur.")
    except Exception as e:
        err(f"Erreur fatale : {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
