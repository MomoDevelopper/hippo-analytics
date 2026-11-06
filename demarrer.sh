#!/bin/bash
# ============================================================
#  HIPPO ANALYTICS — Script de démarrage Linux/macOS
#  PMU Burkina Faso (LONAB)
# ============================================================

set -e

echo ""
echo "  ============================================================"
echo "   🐎  HIPPO ANALYTICS — PMU Burkina Faso"
echo "  ============================================================"
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "  ❌ Docker non installé. Voir : https://www.docker.com"
    exit 1
fi
echo "  ✅ Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"

# Créer .env si absent
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✅ Fichier .env créé depuis .env.example"
else
    echo "  ✅ Fichier .env existant"
fi

echo ""
echo "  🚀 Lancement avec Docker Compose..."
docker-compose up -d

echo ""
echo "  ============================================================"
echo "   Services disponibles :"
echo ""
echo "   🌐 Application    : http://localhost:3000"
echo "   🔌 API Backend    : http://localhost:8000"
echo "   📚 Documentation  : http://localhost:8000/api/docs"
echo "   💾 PostgreSQL     : localhost:5432"
echo ""
echo "   Logs    : docker-compose logs -f"
echo "   Arrêt   : docker-compose down"
echo "  ============================================================"
echo ""
