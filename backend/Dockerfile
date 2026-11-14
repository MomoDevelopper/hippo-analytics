FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système (Tesseract OCR + PostgreSQL client)
RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-fra \
        libpq-dev \
        gcc \
        curl \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* || true

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p /app/uploads/programmes /app/models

# Port d'écoute (Railway injecte $PORT dynamiquement)
EXPOSE $PORT

# Démarrage — Railway override avec railway.toml startCommand
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
