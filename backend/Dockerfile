# ==========================================
# AquaWise AI - Production Dockerfile (Backend)
# ==========================================
# Use Python 3.11 slim as requested for lightweight, stable deployment
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install minimal system tools for health checking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code, dataset, and models
COPY . .

# Ensure trained model artifact and metadata exist at build time
# so the application does NOT retrain on every startup
RUN if [ ! -f models/water_potability_model.joblib ]; then python ml/train.py; fi

# Expose HTTP port (Render uses dynamic $PORT at runtime)
EXPOSE 8000

# Healthcheck testing the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start existing FastAPI application via Uvicorn listening on 0.0.0.0 and $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
