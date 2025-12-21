FROM python:3.10-slim

# --------------------------------------------------
# System dependencies (NLP + ML)
# --------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Workdir
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# Environment variables (AVANT pip install)
# --------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/cache \
    TORCH_HOME=/app/cache

# ⚠️ SUPPRIMÉ : TRANSFORMERS_CACHE (déprécié)

# --------------------------------------------------
# Create cache directory
# --------------------------------------------------
RUN mkdir -p /app/cache

# --------------------------------------------------
# Python dependencies
# --------------------------------------------------
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
       https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz

# --------------------------------------------------
# (OPTIONNEL MAIS RECOMMANDÉ) Télécharger BioBERT au build
# → évite le blocage au runtime
# --------------------------------------------------
RUN python -c "from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('dmis-lab/biobert-base-cased-v1.1'); \
AutoModel.from_pretrained('dmis-lab/biobert-base-cased-v1.1')"

# --------------------------------------------------
# Copy application
# --------------------------------------------------
COPY app.py .

# --------------------------------------------------
# Run service
# --------------------------------------------------
CMD ["python", "app.py"]
