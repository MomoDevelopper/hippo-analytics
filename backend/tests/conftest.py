"""
Configuration pytest pour HIPPO ANALYTICS.
"""
import sys
import os

# Ajouter le dossier backend au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Variables d'environnement de test
os.environ.setdefault("DATABASE_URL", "postgresql://hippo_user:hippo_pass@localhost:5432/hippo_analytics_test")
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SIMULATION_RUNS", "1000")  # Moins de simulations en test
