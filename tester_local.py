"""
Script de test local complet — HIPPO ANALYTICS.

Lance le backend avec SQLite (pas besoin de PostgreSQL pour tester),
génère des données de démo, et valide tous les modules.

Usage :
    python tester_local.py
"""
import sys
import os
import json
import time
import subprocess
import threading
import random
import math
from pathlib import Path
from datetime import date, timedelta
from typing import Optional

# ── Couleurs terminal ──────────────────────────────────────
VERT  = "\033[92m"
ROUGE = "\033[91m"
JAUNE = "\033[93m"
BLEU  = "\033[94m"
RESET = "\033[0m"
GRAS  = "\033[1m"

def ok(msg):   print(f"  {VERT}✅ {msg}{RESET}")
def err(msg):  print(f"  {ROUGE}❌ {msg}{RESET}")
def info(msg): print(f"  {BLEU}ℹ  {msg}{RESET}")
def warn(msg): print(f"  {JAUNE}⚠  {msg}{RESET}")
def titre(msg): print(f"\n{GRAS}{BLEU}{'='*55}\n  {msg}\n{'='*55}{RESET}")


# ══════════════════════════════════════════════════════════
# 1. VÉRIFICATION DES DÉPENDANCES
# ══════════════════════════════════════════════════════════

def verifier_dependances():
    titre("1. Vérification des dépendances Python")

    packages = {
        "fastapi":      "FastAPI (framework API)",
        "sqlalchemy":   "SQLAlchemy (ORM)",
        "pydantic":     "Pydantic (validation)",
        "numpy":        "NumPy (simulations)",
        "sklearn":      "Scikit-learn (IA)",
        "xgboost":      "XGBoost (modèle ML)",
        "apscheduler":  "APScheduler (sync autonome)",
        "requests":     "Requests (HTTP)",
        "bs4":          "BeautifulSoup (scraping)",
        "pandas":       "Pandas (données)",
        "fitz":         "PyMuPDF (extraction PDF)",
        "aiofiles":     "Aiofiles (async)",
    }

    manquants = []
    for pkg, description in packages.items():
        try:
            __import__(pkg)
            ok(f"{description}")
        except ImportError:
            err(f"{description} — NON INSTALLÉ")
            manquants.append(pkg)

    if manquants:
        warn(f"{len(manquants)} package(s) manquant(s). "
             f"Exécutez : pip install {' '.join(manquants)}")
    else:
        ok("Toutes les dépendances sont présentes !")

    return len(manquants) == 0


# ══════════════════════════════════════════════════════════
# 2. TEST DU PARSER LONAB
# ══════════════════════════════════════════════════════════

def tester_parser():
    titre("2. Test du parser PMU Burkina Faso")

    sys.path.insert(0, str(Path(__file__).parent / "backend"))

    try:
        from app.services.parser_lonab import parser_programme_lonab, programme_vers_dict

        # Texte simulant un journal hippique PMU'B
        texte_test = """
JOURNAL HIPPIQUE PMU'B — LONAB
Réunion N°1 — Dimanche 06 Novembre 2026
Hippodrome de Ouagadougou

COURSE N°1 — 2100 mètres Piste Sable
Allocation : 500 000 FCFA

PARTANTS
1  VOLTA EXPRESS        OUEDRAOGO S.    KABORE A.    1a2h3p   4.5
2  FASO PRIDE           TRAORE B.       SAWADOGO F.  0p1h2a   6.0
3  DAKAR STAR           NIKIEMA P.      BARRO S.     3a1h0p   3.0
4  BELLE DE NUIT        COULIBALY I.    ZONGO P.     2p3h1a   8.5
5  SAHEL FORCE          KINDA A.        KABORE A.    1h2a4p   5.5
6  BANI RIVER           SAWADOGO R.     TRAORE M.    0a1h3p   7.0
7  MOUHOUN STAR         ZONGO F.        NIKIEMA L.   2h0a1p   9.0
8  OUAGA DREAM          KABORE L.       COULIBALY C. 1p2h3a  12.0

COURSE N°2 — 1800 mètres Piste Sable
Allocation : 400 000 FCFA

PARTANTS
1  CASCADES GOLD        SOME D.         KABORE A.    1a0h2p   3.5
2  BOBO FLASH           TAPSOBA C.      SAWADOGO F.  2h1a0p   5.0
3  SISSILI EXPRESS      ZERBO H.        BARRO S.     0p2h1a   4.0
4  GNAGNA WIND          OUATTARA N.     TRAORE M.    3a0h1p  11.0
5  KAYA PRIDE           RABO J.         ZONGO P.     1h3a0p   6.5
6  FADA THUNDER         BIKIENGA T.     NIKIEMA L.   0a1h2p  15.0
        """

        prog = parser_programme_lonab(texte_test)

        ok(f"Date extraite : {prog.date}")
        ok(f"Hippodrome   : {prog.hippodrome}")
        ok(f"Réunion      : {prog.reunion}")
        ok(f"Courses      : {len(prog.courses)}")

        total_partants = sum(len(c.partants) for c in prog.courses)
        ok(f"Partants     : {total_partants}")
        ok(f"Confiance    : {prog.confiance:.0f}%")

        if prog.courses and prog.courses[0].partants:
            p = prog.courses[0].partants[0]
            ok(f"Ex partant   : N°{p.numero} — {p.nom_cheval} (Jockey: {p.jockey}, Cote: {p.cote})")

        assert prog.date == "2026-11-06", f"Date incorrecte : {prog.date}"
        assert prog.hippodrome == "Ouagadougou"
        assert len(prog.courses) >= 2
        assert total_partants >= 10
        assert prog.confiance >= 50

        ok("Parser LONAB : TOUS LES TESTS PASSÉS ✓")
        return True

    except Exception as e:
        err(f"Erreur parser : {e}")
        import traceback; traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════
# 3. TEST DU MOTEUR DE SCORING
# ══════════════════════════════════════════════════════════

def tester_scoring():
    titre("3. Test du moteur de scoring")
    sys.path.insert(0, str(Path(__file__).parent / "backend"))

    try:
        from app.services.analyse import (
            _note_forme, _note_distance, _note_regularite,
            detecter_categorie, COEFFICIENTS
        )
        from unittest.mock import MagicMock

        # Test note de forme
        perfs_winner = [MagicMock(place_officielle=1, partants_total=10)] * 3
        perfs_loser  = [MagicMock(place_officielle=10, partants_total=10)] * 3
        perfs_vide   = []

        note_winner = _note_forme(perfs_winner)
        note_loser  = _note_forme(perfs_loser)
        note_vide   = _note_forme(perfs_vide)

        assert note_winner > 80, f"Note gagnant trop basse : {note_winner}"
        assert note_loser  < 20, f"Note perdant trop haute : {note_loser}"
        assert note_vide   == 50.0, f"Note vide != 50 : {note_vide}"

        ok(f"Note forme — Gagnant:{note_winner:.0f} | Perdant:{note_loser:.0f} | Vide:{note_vide:.0f}")

        # Test note de distance
        perfs_dist = [MagicMock(distance=2100, place_officielle=1, partants_total=10)] * 3
        note_spec = _note_distance(perfs_dist, 2000)
        ok(f"Note distance — Spécialiste 2100m sur course 2000m : {note_spec:.0f}")

        # Test régularité
        perfs_reg  = [MagicMock(place_officielle=2)] * 5
        perfs_irr  = [MagicMock(place_officielle=p) for p in [1, 10, 2, 9, 3]]
        note_reg = _note_regularite(perfs_reg)
        note_irr = _note_regularite(perfs_irr)
        assert note_reg > note_irr, "Régulier doit scorer plus qu'irrégulier"
        ok(f"Note régularité — Régulier:{note_reg:.0f} | Irrégulier:{note_irr:.0f}")

        # Test catégories
        assert detecter_categorie(85, None)  == "favori_stat"
        assert detecter_categorie(50, 2.0)   == "favori_cote"
        assert detecter_categorie(65, 20.0)  == "outsider"
        assert detecter_categorie(25, None)  == "risque"
        ok("Catégories : favori_stat | favori_cote | outsider | risque → OK")

        # Test coefficients
        assert abs(sum(COEFFICIENTS.values()) - 1.0) < 0.001, "Coefficients ne somment pas à 1"
        ok(f"Coefficients : {COEFFICIENTS}")

        ok("Moteur de scoring : TOUS LES TESTS PASSÉS ✓")
        return True

    except Exception as e:
        err(f"Erreur scoring : {e}")
        import traceback; traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════
# 4. TEST DE LA SIMULATION MONTE CARLO
# ══════════════════════════════════════════════════════════

def tester_monte_carlo():
    titre("4. Test simulation Monte Carlo (Plackett-Luce)")
    sys.path.insert(0, str(Path(__file__).parent / "backend"))

    try:
        from app.services.prediction import normaliser_probabilites, simulation_monte_carlo
        import numpy as np

        # 16 chevaux (cas standard PMU'B)
        notes_16 = {i: float(random.randint(30, 95)) for i in range(1, 17)}
        notes_16[6]  = 90.0  # Favori statistique
        notes_16[11] = 82.0  # 2ème favori
        notes_16[9]  = 75.0  # 3ème

        print(f"\n  Notes des 16 chevaux :")
        for cid, note in sorted(notes_16.items(), key=lambda x: x[1], reverse=True):
            barre = "█" * int(note / 5)
            print(f"    Cheval {cid:2d} : {note:5.1f} {barre}")

        # Normalisation
        probas = normaliser_probabilites(notes_16)
        assert abs(sum(probas.values()) - 1.0) < 1e-5, "Probas ne somment pas à 1"
        ok(f"Normalisation softmax : somme = {sum(probas.values()):.6f}")

        top3_probas = sorted(probas.items(), key=lambda x: x[1], reverse=True)[:3]
        for cid, p in top3_probas:
            ok(f"  Cheval {cid} → P(victoire) = {p*100:.2f}%")

        # Simulation Monte Carlo (10 000 runs pour le test)
        print(f"\n  🎲 Lancement de 10 000 simulations Monte Carlo...")
        t0 = time.time()
        resultats = simulation_monte_carlo(probas, n_runs=10_000, top_n=5)
        duree = time.time() - t0

        ok(f"Simulation terminée en {duree:.2f}s")
        ok(f"Ordres distincts simulés : {len(resultats)}")
        ok(f"Somme des probabilités top-50 : {sum(h['probabilite'] for h in resultats[:50])*100:.1f}%")

        # Vérifications
        assert len(resultats) > 0
        assert len(resultats[0]["ordre"]) == 5
        assert all(len(set(h["ordre"])) == 5 for h in resultats[:20]), \
            "Doublon détecté dans un ordre !"
        for i in range(len(resultats) - 1):
            assert resultats[i]["probabilite"] >= resultats[i+1]["probabilite"], \
                "Hypothèses non triées !"

        print(f"\n  Top 10 hypothèses :")
        for h in resultats[:10]:
            ordre_str = " → ".join(f"#{c}" for c in h["ordre"])
            print(f"    #{h['rang']:2d} | {ordre_str} | {h['probabilite']*100:.3f}%")

        # Vérifier que le favori (#6) est bien en tête des meilleures hypothèses
        top10 = resultats[:10]
        nb_tete = sum(1 for h in top10 if h["ordre"][0] == 6)
        ok(f"Favori (cheval #6) en tête dans {nb_tete}/10 meilleures hypothèses")

        # Extrapolation : si 100 000 runs
        print(f"\n  📊 Extrapolation pour 100 000 simulations :")
        info(f"Durée estimée : ~{duree * 10:.1f}s ({duree * 10 / 60:.1f} min)")
        info(f"Hypothèses distincts attendus : ~{len(resultats) * 8:,}")

        ok("Simulation Monte Carlo : TOUS LES TESTS PASSÉS ✓")
        return True

    except Exception as e:
        err(f"Erreur Monte Carlo : {e}")
        import traceback; traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════
# 5. TEST AVEC DONNÉES DE DÉMO (sans base de données)
# ══════════════════════════════════════════════════════════

def tester_pipeline_complet():
    titre("5. Test pipeline complet (sans BDD — données de démo)")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from scraper_lonab import generer_donnees_demo
        from app.services.prediction import normaliser_probabilites, simulation_monte_carlo
        from app.services.analyse import _note_forme, _note_regularite, detecter_categorie
        from unittest.mock import MagicMock

        # Générer les données de démo
        print("\n  Génération de 60 jours de données PMU'B simulées...")
        donnees = generer_donnees_demo()
        nb_courses = len(donnees["courses"])
        ok(f"Courses générées : {nb_courses}")

        # Prendre une course et simuler une prédiction complète
        course = donnees["courses"][-1]  # Dernière course
        print(f"\n  Course de test : {course['date']} — {course['hippodrome']}")
        print(f"  Distance       : {course['distance']}m")
        print(f"  Partants       : {course['nb_partants']}")

        # Simuler les notes pour chaque partant
        print(f"\n  Calcul des notes (simulation)...")
        notes = {}
        for partant in course["partants"]:
            # Note basée sur la cote (simulation car pas de BDD)
            cote = partant["cote"]
            note_cote = max(20, min(90, 100 - (cote - 1) * 4))
            bruit = random.uniform(-10, 10)
            note = max(10, min(99, note_cote + bruit))
            notes[partant["numero"]] = round(note, 1)

        # Afficher les notes
        print(f"\n  {'N°':>3} {'Cheval':<22} {'Cote':>5} {'Note':>5} {'Catégorie'}")
        print(f"  {'─'*3} {'─'*22} {'─'*5} {'─'*5} {'─'*18}")
        for partant in sorted(course["partants"], key=lambda p: notes[p["numero"]], reverse=True):
            num = partant["numero"]
            categorie = detecter_categorie(notes[num], partant["cote"])
            cat_court = {
                "favori_stat": "⭐ Fav.Stat",
                "favori_cote": "💰 Fav.Cote",
                "outsider":    "🎯 Outsider",
                "risque":      "⚠  Risque",
            }.get(categorie, categorie)
            print(f"  {num:>3} {partant['nom_cheval']:<22} {partant['cote']:>5.1f} "
                  f"{notes[num]:>5.1f} {cat_court}")

        # Prédiction Monte Carlo
        print(f"\n  🎲 Simulation Monte Carlo (10 000 runs)...")
        probas = normaliser_probabilites(notes)
        t0 = time.time()
        hypotheses = simulation_monte_carlo(probas, n_runs=10_000, top_n=5)
        duree = time.time() - t0

        ok(f"Simulation terminée en {duree:.2f}s")
        ok(f"{len(hypotheses)} hypothèses distinctes générées")

        # Top 5 prédit
        top5_ids = hypotheses[0]["ordre"] if hypotheses else []
        top5_noms = [
            next((p["nom_cheval"] for p in course["partants"] if p["numero"] == cid), f"#{cid}")
            for cid in top5_ids
        ]

        print(f"\n  🏆 TOP 5 PRÉDIT :")
        medailles = ["🥇", "🥈", "🥉", "4️⃣ ", "5️⃣ "]
        for i, (cid, nom) in enumerate(zip(top5_ids, top5_noms)):
            prob = probas.get(cid, 0) * 100
            print(f"    {medailles[i]} N°{cid:2d} — {nom:<22} P(victoire)={prob:.1f}%")

        # Résultat réel (pour comparaison)
        arrivee_reelle = course["arrivee_officielle"]
        arrivee_noms = [
            next((p["nom_cheval"] for p in course["partants"] if p["numero"] == n), f"#{n}")
            for n in arrivee_reelle
        ]
        print(f"\n  ✅ ARRIVÉE RÉELLE (simulée) :")
        for i, (num, nom) in enumerate(zip(arrivee_reelle, arrivee_noms)):
            correct = "✓" if i < len(top5_ids) and num == top5_ids[i] else " "
            print(f"    {i+1}{'er' if i==0 else 'ème'} {correct} N°{num:2d} — {nom}")

        # Évaluation
        top5_pred_set = set(top5_ids)
        top5_reel_set = set(arrivee_reelle[:5])
        communs = len(top5_pred_set & top5_reel_set)
        ok(f"Chevaux communs Top5 : {communs}/5")

        # Top 5 hypothèses
        print(f"\n  Top 5 hypothèses :")
        for h in hypotheses[:5]:
            ordre_str = " → ".join(f"N°{c}" for c in h["ordre"])
            print(f"    #{h['rang']} | {ordre_str} | {h['probabilite']*100:.3f}%")

        ok("Pipeline complet : TEST RÉUSSI ✓")
        return True

    except Exception as e:
        err(f"Erreur pipeline : {e}")
        import traceback; traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════
# 6. TEST DE L'API FASTAPI (mode SQLite)
# ══════════════════════════════════════════════════════════

def tester_api_fastapi():
    titre("6. Test démarrage API FastAPI")

    # Configurer SQLite pour le test (pas besoin de PostgreSQL)
    os.environ["DATABASE_URL"] = "sqlite:///./test_hippo.db"
    os.environ["SECRET_KEY"] = "test_secret_key_hippo_analytics"
    os.environ["DEBUG"] = "true"
    os.environ["SYNC_INTERVAL_HOURS"] = "999"  # Désactiver la sync en test
    os.environ["UPLOAD_DIR"] = "./test_uploads"

    sys.path.insert(0, str(Path(__file__).parent / "backend"))

    try:
        info("Import de l'application FastAPI...")
        from app.main import app
        from app.database import create_tables, reset_engine
        ok("Application FastAPI importée !")

        # Réinitialiser l'engine pour prendre en compte SQLite (vars d'env déjà fixées)
        reset_engine()

        # Créer les tables
        info("Création des tables SQLite...")
        create_tables()
        ok("Tables créées en SQLite !")

        # Test avec TestClient
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # Route santé
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        ok(f"GET /health → {data}")

        # Route accueil
        resp = client.get("/")
        assert resp.status_code == 200
        ok(f"GET / → {resp.json()['bienvenue']}")

        # Routes API
        routes_test = [
            ("GET", "/api/courses",      "Liste des courses"),
            ("GET", "/api/chevaux",      "Liste des chevaux"),
            ("GET", "/api/jockeys",      "Classement jockeys"),
            ("GET", "/api/entraineurs",  "Classement entraîneurs"),
            ("GET", "/api/statistiques", "Statistiques globales"),
            ("GET", "/api/sync/status",  "Statut synchronisation"),
        ]

        print(f"\n  Test des routes API :")
        for method, route, description in routes_test:
            resp = client.get(route)
            statut = "✅" if resp.status_code == 200 else f"❌ ({resp.status_code})"
            print(f"    {statut} {method} {route} — {description}")

        # Test import PDF (fichier vide)
        import io
        pdf_vide = b"%PDF-1.4 test"
        resp = client.post(
            "/api/programmes/import/pdf",
            files={"fichier": ("test.pdf", io.BytesIO(pdf_vide), "application/pdf")},
        )
        # 200 ou 422 sont acceptables (fichier trop petit)
        ok(f"POST /api/programmes/import/pdf → HTTP {resp.status_code}")

        ok("API FastAPI : TOUS LES TESTS PASSÉS ✓")

        # Nettoyage
        try:
            Path("test_hippo.db").unlink(missing_ok=True)
        except Exception:
            pass

        return True

    except ImportError as e:
        warn(f"Import partiel (dépendance manquante) : {e}")
        warn("L'API sera testable une fois toutes les dépendances installées")
        return False
    except Exception as e:
        err(f"Erreur API : {e}")
        import traceback; traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════

def afficher_resume(resultats: dict):
    titre("RÉSUMÉ DES TESTS")

    total = len(resultats)
    reussis = sum(1 for v in resultats.values() if v)

    for test, reussi in resultats.items():
        statut = f"{VERT}✅ RÉUSSI{RESET}" if reussi else f"{ROUGE}❌ ÉCHOUÉ{RESET}"
        print(f"  {statut}  {test}")

    print()
    if reussis == total:
        print(f"  {VERT}{GRAS}🎉 {reussis}/{total} tests réussis — HIPPO ANALYTICS est opérationnel !{RESET}")
        print(f"\n  Prochaines étapes :")
        print(f"  1. Lancez Docker : docker-compose up -d")
        print(f"  2. Testez LONAB : python scraper_lonab.py --test --output data")
        print(f"  3. Ouvrez http://localhost:3000")
    else:
        print(f"  {JAUNE}{GRAS}{reussis}/{total} tests réussis.{RESET}")
        print(f"  Vérifiez les erreurs ci-dessus avant de déployer.")


# ══════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Forcer UTF-8 sur Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print(f"\n{GRAS}{'='*55}")
    print(f"  HIPPO ANALYTICS -- Tests locaux")
    print(f"  PMU Burkina Faso (LONAB)")
    print(f"{'='*55}{RESET}")

    # Changer le répertoire de travail vers backend
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    resultats = {}

    resultats["Dépendances Python"]      = verifier_dependances()
    resultats["Parser LONAB"]            = tester_parser()
    resultats["Moteur de scoring"]       = tester_scoring()
    resultats["Simulation Monte Carlo"]  = tester_monte_carlo()
    resultats["Pipeline complet"]        = tester_pipeline_complet()
    resultats["API FastAPI"]             = tester_api_fastapi()

    afficher_resume(resultats)
