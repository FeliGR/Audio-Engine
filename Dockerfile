FROM python:3.10-slim

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV LOG_LEVEL=INFO
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/tts-key.json


EXPOSE 5003


HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1


CMD ["python", "-m", "app"]
