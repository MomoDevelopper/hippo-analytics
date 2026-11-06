
# 🚀 HIPPO ANALYTICS — Instructions de déploiement Railway

## Étapes pour mettre en ligne (15 minutes)

### ÉTAPE 1 — Créer un dépôt GitHub

1. Allez sur https://github.com/new
2. Nom du repo : `hippo-analytics`
3. Visibilité : **Privé** (données sportives sensibles)
4. Cliquer **Create repository**

### ÉTAPE 2 — Pousser le code sur GitHub

Ouvrez PowerShell dans le dossier `hyppo_analytics` :

```powershell
# Remplacez VOTRE_NOM par votre nom d'utilisateur GitHub
git remote add origin https://github.com/VOTRE_NOM/hippo-analytics.git
git branch -M main
git push -u origin main
```

### ÉTAPE 3 — Déployer sur Railway

1. Allez sur https://railway.app
2. Connectez-vous avec GitHub
3. Cliquez **New Project**
4. Choisissez **Deploy from GitHub repo**
5. Sélectionnez `hippo-analytics`
6. Railway détecte automatiquement le `Dockerfile`

### ÉTAPE 4 — Ajouter PostgreSQL

Dans le projet Railway :
1. Cliquez **+ New** → **Database** → **PostgreSQL**
2. Railway crée automatiquement la DB et la variable `DATABASE_URL`

### ÉTAPE 5 — Variables d'environnement

Dans **Settings** → **Variables** du service backend :

```
DATABASE_URL          → ${{ Postgres.DATABASE_URL }}  (auto)
SECRET_KEY            → [Générer ici: python -c "import secrets; print(secrets.token_hex(32))"]
LONAB_BASE_URL        → https://www.lonab.bf
SYNC_INTERVAL_HOURS   → 6
SIMULATION_RUNS       → 100000
UPLOAD_DIR            → /app/uploads
DEBUG                 → false
PORT                  → 8000
```

### ÉTAPE 6 — Déployer le Frontend

Option A — Vercel (recommandé pour Next.js) :
1. https://vercel.com/new
2. Importer `hippo-analytics`
3. Répertoire racine : `frontend`
4. Variable : `NEXT_PUBLIC_API_URL` = URL Railway du backend

Option B — Railway (même projet) :
1. **+ New** → **GitHub repo** → `hippo-analytics`
2. Répertoire source : `frontend`
3. Variable : `NEXT_PUBLIC_API_URL` = URL backend Railway

### ÉTAPE 7 — Vérifier le déploiement

```bash
# Test de santé de l'API
curl https://[votre-url].railway.app/health

# Doit retourner :
# {"status": "ok", "service": "HIPPO ANALYTICS", "version": "1.0.0"}
```

---

## Après le déploiement

### Charger les données initiales

Via l'interface API Swagger (https://[url]/api/docs) :

1. **POST /api/sync/run** — Lance la première sync LONAB
2. **POST /api/admin/ia/entrainer** — Entraîne le modèle XGBoost
3. Accéder au dashboard : https://[url-frontend]

### Workflow quotidien automatique

```
06h00 → Sync LONAB (auto)        → Télécharge nouveaux PDFs
        ↓
        Parser PDF                → Extrait courses + partants
        ↓
        Prédictions disponibles   → Dashboard mis à jour
        
Après la course → Admin saisit l'arrivée officielle
                → Modèle XGBoost se réentraîne
```

---

## Clé secrète à générer

```powershell
# Dans PowerShell :
python -c "import secrets; print(secrets.token_hex(32))"
```

Exemple de sortie : `a3f8b2c4d7e1f9...` (64 caractères hex)

---

## Support et maintenance

- Logs Railway : Dashboard → Service → Logs
- Sync manuelle : POST /api/sync/run via Swagger
- Réentraînement : POST /api/admin/ia/entrainer
- Exports : GET /api/admin/export/excel

