# ── Tether Public Server ─────────────────────────────────────────────────────
# Deploy anywhere: Railway, Render, Fly.io, Koyeb, or a VPS
#
# Build:  docker build -t tether .
# Run:    docker run -p 8080:8080 -v ~/.tether:/root/.tether tether
#
# The auth config (~/.tether) must be mounted or pre-configured.
# The Groq API key must be set in the credential store.

FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy source
COPY src/ src/
COPY pyproject.toml .

# Expose the port
ENV PORT=8080
EXPOSE 8080

# Run
CMD PYTHONPATH=src uvicorn tether.web.server:app --host 0.0.0.0 --port $PORT
