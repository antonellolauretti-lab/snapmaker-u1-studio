# ==============================================================================
# Snapmaker U1 Parametric Studio - Backend Container
# Ottimizzato per Render.com, Railway.app e Docker locale
# ==============================================================================

FROM python:3.11-slim

# Impostazioni di ambiente per Python e porta dinamica Cloud
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Dipendenze di sistema minime per compilazione e motori geometrici/font
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libfreetype6-dev \
    fontconfig \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installazione dipendenze Python con cache pip disabilitata
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia dell'engine geometrico e web backend
COPY generator_u1 /app/generator_u1
COPY run_web.py /app/run_web.py

# Crea directory per uploads temporanei
RUN mkdir -p /app/generator_u1/web/uploads/fonts

# Esponi porta documentata
EXPOSE 8000

# Healthcheck nativo Docker
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Avvio con interpretazione della variabile $PORT fornita da Render o Railway
CMD ["sh", "-c", "uvicorn generator_u1.web.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
