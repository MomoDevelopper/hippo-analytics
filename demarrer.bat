@echo off
:: ============================================================
::  HIPPO ANALYTICS — Script de démarrage Windows
::  PMU Burkina Faso (LONAB)
:: ============================================================
title HIPPO ANALYTICS

echo.
echo  ============================================================
echo   🐎  HIPPO ANALYTICS — PMU Burkina Faso
echo  ============================================================
echo.

:: Vérifier Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Docker n'est pas installé ou n'est pas démarré.
    echo     Installez Docker Desktop : https://www.docker.com
    pause
    exit /b 1
)
echo  ✅ Docker détecté

:: Copier .env si absent
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo  ✅ Fichier .env créé
) else (
    echo  ✅ Fichier .env existant
)

echo.
echo  🚀 Lancement de HIPPO ANALYTICS avec Docker...
echo.

docker-compose up -d

echo.
echo  ============================================================
echo   Services disponibles :
echo.
echo   🌐 Application    : http://localhost:3000
echo   🔌 API Backend    : http://localhost:8000
echo   📚 Documentation  : http://localhost:8000/api/docs
echo   💾 PostgreSQL     : localhost:5432
echo.
echo   Pour arrêter : docker-compose down
echo  ============================================================
echo.

pause
