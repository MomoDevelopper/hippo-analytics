"""
Tests unitaires — Services d'analyse et de prédiction HIPPO ANALYTICS.
Phase 6 — Tests et validation du moteur de prédiction.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────
# Tests du module d'analyse (scoring)
# ──────────────────────────────────────────────────────────

class TestNotesForme:
    """Tests du calcul de la note de forme."""

    def test_note_forme_vide(self):
        """Sans performances, la note doit être neutre (50)."""
        from app.services.analyse import _note_forme
        assert _note_forme([]) == 50.0

    def test_note_forme_avec_victoires(self):
        """Un cheval avec plusieurs victoires doit avoir une note élevée."""
        from app.services.analyse import _note_forme
        perfs = [
            MagicMock(place_officielle=1, partants_total=12),
            MagicMock(place_officielle=1, partants_total=10),
            MagicMock(place_officielle=2, partants_total=14),
        ]
        note = _note_forme(perfs)
        assert note > 75, f"Note attendue > 75, obtenu : {note}"

    def test_note_forme_mauvaises_performances(self):
        """Un cheval en queue de peloton doit avoir une note faible."""
        from app.services.analyse import _note_forme
        perfs = [
            MagicMock(place_officielle=10, partants_total=12),
            MagicMock(place_officielle=12, partants_total=12),
            MagicMock(place_officielle=11, partants_total=12),
        ]
        note = _note_forme(perfs)
        assert note < 30, f"Note attendue < 30, obtenu : {note}"

    def test_note_forme_ponderation_recente(self):
        """La sortie la plus récente doit peser davantage."""
        from app.services.analyse import _note_forme
        # Cheval récemment en forme (1er en dernier) vs en forme dans le passé
        perfs_recentes = [
            MagicMock(place_officielle=1, partants_total=10),  # récente
            MagicMock(place_officielle=10, partants_total=10),
            MagicMock(place_officielle=10, partants_total=10),
        ]
        perfs_passees = [
            MagicMock(place_officielle=10, partants_total=10),  # récente mauvaise
            MagicMock(place_officielle=1, partants_total=10),
            MagicMock(place_officielle=1, partants_total=10),
        ]
        note_recentes = _note_forme(perfs_recentes)
        note_passees = _note_forme(perfs_passees)
        assert note_recentes > note_passees, "La victoire récente doit avoir plus de poids"


class TestNoteDistance:
    """Tests du calcul de la note de distance."""

    def test_distance_sans_historique(self):
        """Sans historique de distance, note neutre."""
        from app.services.analyse import _note_distance
        assert _note_distance([], 2000) == 50.0

    def test_distance_sans_course(self):
        """Sans distance de course, note neutre."""
        from app.services.analyse import _note_distance
        perfs = [MagicMock(distance=2000, place_officielle=1, partants_total=10)]
        assert _note_distance(perfs, None) == 50.0

    def test_distance_cheval_specialiste(self):
        """Un spécialiste de la distance doit avoir une bonne note."""
        from app.services.analyse import _note_distance
        perfs = [
            MagicMock(distance=2100, place_officielle=1, partants_total=10),
            MagicMock(distance=2000, place_officielle=1, partants_total=10),
            MagicMock(distance=2050, place_officielle=2, partants_total=12),
        ]
        note = _note_distance(perfs, 2000)
        assert note > 50, "Un spécialiste de la distance doit dépasser 50"


class TestDetectionCategorie:
    """Tests de la détection de catégorie."""

    def test_favori_cote(self):
        from app.services.analyse import detecter_categorie
        assert detecter_categorie(60.0, 2.5) == "favori_cote"

    def test_favori_statistique(self):
        from app.services.analyse import detecter_categorie
        assert detecter_categorie(80.0, 8.0) == "favori_stat"

    def test_outsider_interessant(self):
        from app.services.analyse import detecter_categorie
        assert detecter_categorie(65.0, 15.0) == "outsider"

    def test_cheval_risque(self):
        from app.services.analyse import detecter_categorie
        assert detecter_categorie(30.0, None) == "risque"


# ──────────────────────────────────────────────────────────
# Tests du moteur de prédiction Monte Carlo
# ──────────────────────────────────────────────────────────

class TestNormalisationProbabilites:
    """Tests de la normalisation softmax."""

    def test_somme_a_1(self):
        from app.services.prediction import normaliser_probabilites
        notes = {1: 90, 2: 70, 3: 50, 4: 40, 5: 30}
        probas = normaliser_probabilites(notes)
        assert abs(sum(probas.values()) - 1.0) < 1e-6, "Les probabilités doivent sommer à 1"

    def test_meilleure_note_plus_grande_proba(self):
        from app.services.prediction import normaliser_probabilites
        notes = {1: 90, 2: 50, 3: 30}
        probas = normaliser_probabilites(notes)
        assert probas[1] > probas[2] > probas[3], "Ordre des probabilités incorrect"

    def test_probabilites_positives(self):
        from app.services.prediction import normaliser_probabilites
        notes = {i: float(i * 10) for i in range(1, 17)}
        probas = normaliser_probabilites(notes)
        assert all(p > 0 for p in probas.values()), "Toutes les probabilités doivent être positives"

    def test_cas_vide(self):
        from app.services.prediction import normaliser_probabilites
        assert normaliser_probabilites({}) == {}


class TestSimulationMonteCarlo:
    """Tests de la simulation Monte Carlo."""

    def test_simulation_basique(self):
        from app.services.prediction import simulation_monte_carlo
        probas = {i: 1/8 for i in range(1, 9)}
        resultats = simulation_monte_carlo(probas, n_runs=1000, top_n=5)
        assert len(resultats) > 0, "La simulation doit produire des résultats"
        assert len(resultats[0]["ordre"]) == 5, "Chaque hypothèse doit avoir 5 chevaux"

    def test_ordre_unique_par_cheval(self):
        from app.services.prediction import simulation_monte_carlo
        probas = {i: 1/10 for i in range(1, 11)}
        resultats = simulation_monte_carlo(probas, n_runs=5000, top_n=5)
        for hyp in resultats[:10]:
            assert len(set(hyp["ordre"])) == 5, "Chaque cheval ne peut apparaître qu'une fois"

    def test_probabilites_decroissantes(self):
        from app.services.prediction import simulation_monte_carlo
        probas = {1: 0.5, 2: 0.3, 3: 0.1, 4: 0.05, 5: 0.05}
        resultats = simulation_monte_carlo(probas, n_runs=10000, top_n=5)
        # Les premières hypothèses doivent avoir des probabilités décroissantes
        for i in range(len(resultats) - 1):
            assert resultats[i]["probabilite"] >= resultats[i+1]["probabilite"], \
                "Les hypothèses doivent être triées par probabilité décroissante"

    def test_gagnant_favori_en_tete(self):
        """Le favori absolu doit dominer les premières hypothèses."""
        from app.services.prediction import simulation_monte_carlo
        probas = {1: 0.7, 2: 0.1, 3: 0.05, 4: 0.05, 5: 0.05, 6: 0.05}
        resultats = simulation_monte_carlo(probas, n_runs=10000, top_n=5)
        # Le cheval #1 doit apparaître en tête dans la majorité des top hypothèses
        top10 = resultats[:10]
        nb_tete = sum(1 for h in top10 if h["ordre"][0] == 1)
        assert nb_tete >= 7, f"Le favori (#1) doit être 1er dans ≥70% des top hypothèses, obtenu : {nb_tete}/10"


# ──────────────────────────────────────────────────────────
# Tests du parser LONAB
# ──────────────────────────────────────────────────────────

class TestParserLonab:
    """Tests du parser de programmes PMU Burkina Faso."""

    TEXTE_EXEMPLE = """
    JOURNAL HIPPIQUE PMU'B
    Réunion N°1 — Dimanche 30 Octobre 2026
    Hippodrome de Ouagadougou

    COURSE N°1 — 2100 mètres — Sable

    PARTANTS
    1  DAKAR STAR         OUEDRAOGO          KABORE           1a2h3  4.5
    2  BELLE DE NUIT      TRAORE             SAWADOGO         0p1h2  6.0
    3  CHAMPION DU LAC    NIKIEMA            BARRO            3a1h0  3.0
    4  VOLTA EXPRESS      COULIBALY          ZONGO            2p3h1  8.0
    5  FASO PRIDE         KINDA              OUATTARA         1h2a4  5.5

    COURSE N°2 — 1800 mètres — Sable
    """

    def test_extraction_date(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        assert prog.date == "2026-10-30", f"Date incorrecte : {prog.date}"

    def test_extraction_hippodrome(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        assert prog.hippodrome == "Ouagadougou"

    def test_extraction_reunion(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        assert prog.reunion == "R1"

    def test_extraction_courses(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        assert len(prog.courses) >= 1, "Au moins une course doit être détectée"

    def test_extraction_distance(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        if prog.courses:
            assert prog.courses[0].distance == 2100, f"Distance incorrecte : {prog.courses[0].distance}"

    def test_confiance_elevee(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab(self.TEXTE_EXEMPLE)
        assert prog.confiance >= 50, f"Confiance trop faible : {prog.confiance}"

    def test_texte_vide(self):
        from app.services.parser_lonab import parser_programme_lonab
        prog = parser_programme_lonab("")
        assert prog.date is None
        assert prog.confiance == 0.0


# ──────────────────────────────────────────────────────────
# Tests de configuration
# ──────────────────────────────────────────────────────────

class TestConfiguration:
    """Tests de la configuration de l'application."""

    def test_parametres_par_defaut(self):
        from app.config import Settings
        settings = Settings()
        assert settings.SIMULATION_RUNS == 100_000
        assert settings.SYNC_INTERVAL_HOURS == 6
        assert settings.MAX_HORSES_PER_RACE == 20
        assert settings.TOP_HYPOTHESES == 50

    def test_url_lonab(self):
        from app.config import Settings
        settings = Settings()
        assert "lonab.bf" in settings.LONAB_BASE_URL


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
