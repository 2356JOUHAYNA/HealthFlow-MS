FROM python:3.10-slim

# Dossier de travail
WORKDIR /app

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code application
COPY app.py .

# Templates Jinja2
COPY templates ./templates

# ✅ FICHIERS STATIQUES (CSS)
COPY static ./static

# Lancement
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
