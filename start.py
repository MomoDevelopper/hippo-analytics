#!/usr/bin/env python3
"""
Script de démarrage rapide HIPPO ANALYTICS (sans Docker).
Lance le backend directement sur la machine locale avec SQLite (mode dev).
"""
import os
import sys
import subprocess


def verifier_python():
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ requis")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")


def installer_dependances():
    print("\n📦 Installation des dépendances Python...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
        check=True,
    )
    print("✅ Dépendances installées")


def creer_env():
    if not os.path.exists(".env"):
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅ Fichier .env créé depuis .env.example")
        print("⚠️  Éditez .env pour configurer votre base de données PostgreSQL")
    else:
        print("✅ Fichier .env existant")


def lancer_backend():
    print("\n🚀 Lancement du backend HIPPO ANALYTICS...")
    print("   API disponible sur : http://localhost:8000")
    print("   Documentation    : http://localhost:8000/api/docs")
    print("   Arrêt            : Ctrl+C\n")
    os.chdir("backend")
    subprocess.run(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        check=True,
    )


if __name__ == "__main__":
    print("=" * 55)
    print("  🐎 HIPPO ANALYTICS — Démarrage")
    print("  PMU Burkina Faso (LONAB)")
    print("=" * 55)

    verifier_python()
    creer_env()

    if "--install" in sys.argv:
        installer_dependances()

    lancer_backend()
