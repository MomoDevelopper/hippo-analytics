#!/usr/bin/env python3
"""
HIPPO ANALYTICS — Script de déploiement Docker local ou production.

Usage:
    python deployer.py --local          Démarre avec Docker Compose (local)
    python deployer.py --check          Vérifie les prérequis
    python deployer.py --stop           Arrête les services Docker
    python deployer.py --logs           Affiche les logs en temps réel
    python deployer.py --reset          Supprime tout et recrée (ATTENTION: perd les données)
"""
import sys
import os
import subprocess
import argparse
import time
import io
import json
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent


def run(cmd, check=True, capture=False):
    """Exécute une commande shell."""
    print(f"  $ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=ROOT,
        capture_output=capture, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode != 0:
        if capture:
            print(result.stderr or result.stdout)
        raise RuntimeError(f"Commande échouée: {cmd}")
    return result


def titre(msg):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}")


def ok(msg):  print(f"  OK  {msg}")
def info(msg): print(f"  >>  {msg}")
def warn(msg): print(f"  !!  {msg}")
def err(msg):  print(f"  XX  {msg}")


def verifier_prerequis():
    """Vérifie que Docker et Docker Compose sont disponibles."""
    titre("Vérification des prérequis")

    # Docker
    r = run("docker --version", check=False, capture=True)
    if r.returncode == 0:
        ok(f"Docker: {r.stdout.strip()}")
    else:
        err("Docker non trouvé — installer depuis https://www.docker.com")
        return False

    # Docker Compose
    r = run("docker compose version", check=False, capture=True)
    if r.returncode != 0:
        r = run("docker-compose --version", check=False, capture=True)
    if r.returncode == 0:
        ok(f"Docker Compose: {r.stdout.strip()}")
    else:
        err("Docker Compose non trouvé")
        return False

    # Fichier .env
    env_path = ROOT / ".env"
    env_example = ROOT / ".env.example"
    if not env_path.exists() and env_example.exists():
        warn(".env manquant — copie depuis .env.example...")
        import shutil
        shutil.copy(env_example, env_path)
        ok(".env créé (modifiez les valeurs avant la production !)")
    elif env_path.exists():
        ok(".env présent")

    # docker-compose.yml
    if (ROOT / "docker-compose.yml").exists():
        ok("docker-compose.yml présent")
    else:
        err("docker-compose.yml manquant !")
        return False

    return True


def demarrer_local():
    """Démarre les services avec Docker Compose."""
    titre("Démarrage local avec Docker Compose")

    if not verifier_prerequis():
        return False

    info("Construction des images Docker...")
    run("docker compose build --no-cache")
    ok("Images construites !")

    info("Démarrage des services...")
    run("docker compose up -d")

    info("Attente de la disponibilité des services (60s)...")
    for i in range(12):
        time.sleep(5)
        r = run("docker compose ps", capture=True, check=False)
        if "healthy" in r.stdout or "running" in r.stdout:
            print(f"  {i*5+5}s... services actifs")
            break
        print(f"  {i*5+5}s...")

    # Test de santé
    import urllib.request
    info("Test de santé de l'API...")
    for tentative in range(10):
        try:
            resp = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
            data = json.loads(resp.read())
            ok(f"API opérationnelle : {data}")
            break
        except Exception:
            time.sleep(5)
            if tentative == 9:
                warn("API non disponible après 50s — vérifiez les logs")

    print()
    ok("HIPPO ANALYTICS est démarré !")
    print()
    print("  Accès :")
    print("    Frontend :  http://localhost:3000")
    print("    API Docs :  http://localhost:8000/api/docs")
    print("    API Santé : http://localhost:8000/health")
    print()
    info("Pour voir les logs : python deployer.py --logs")
    info("Pour arrêter     : python deployer.py --stop")
    return True


def arreter():
    """Arrête les services Docker."""
    titre("Arrêt des services")
    run("docker compose down")
    ok("Services arrêtés !")


def voir_logs():
    """Affiche les logs en temps réel."""
    titre("Logs Docker Compose (Ctrl+C pour quitter)")
    try:
        subprocess.run("docker compose logs -f --tail=100", shell=True, cwd=ROOT)
    except KeyboardInterrupt:
        pass


def reinitialiser():
    """Supprime tout et recrée (perd les données !)."""
    titre("REINITIALISATION COMPLETE")
    warn("ATTENTION : Toutes les données PostgreSQL seront supprimées !")
    confirm = input("  Confirmer ? (tapez OUI) : ").strip()
    if confirm != "OUI":
        info("Annulé.")
        return

    run("docker compose down -v --remove-orphans")
    run("docker compose build --no-cache")
    run("docker compose up -d")
    ok("Réinitialisation terminée !")


def main():
    parser = argparse.ArgumentParser(description="HIPPO ANALYTICS — Déploiement")
    parser.add_argument("--local", action="store_true", help="Démarrer en local avec Docker")
    parser.add_argument("--check", action="store_true", help="Vérifier les prérequis")
    parser.add_argument("--stop", action="store_true", help="Arrêter les services")
    parser.add_argument("--logs", action="store_true", help="Afficher les logs")
    parser.add_argument("--reset", action="store_true", help="Réinitialiser (perd les données)")
    args = parser.parse_args()

    print()
    print("=" * 55)
    print("  HIPPO ANALYTICS — Gestionnaire de déploiement")
    print("  PMU Burkina Faso (LONAB)")
    print("=" * 55)

    if args.check:
        verifier_prerequis()
    elif args.local:
        demarrer_local()
    elif args.stop:
        arreter()
    elif args.logs:
        voir_logs()
    elif args.reset:
        reinitialiser()
    else:
        parser.print_help()
        print()
        info("Pour démarrer : python deployer.py --local")


if __name__ == "__main__":
    main()
