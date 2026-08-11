# Portable container build — works on Fly.io, Railway, Google Cloud Run,
# Azure Container Apps, or any other Docker-based host, in addition to the
# Procfile/render.yaml paths above for buildpack-based platforms.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8420
EXPOSE 8420

CMD ["sh", "-c", "uvicorn webapp.backend.main:app --host 0.0.0.0 --port ${PORT}"]
