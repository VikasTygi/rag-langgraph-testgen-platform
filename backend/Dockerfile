FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV APP_MODE=api

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock ./requirements.lock

RUN pip install --upgrade pip \
    && pip install -r requirements.lock

COPY app ./app
COPY entrypoint.sh ./entrypoint.sh

RUN mkdir -p /app/chroma_db /app/logs \
    && useradd -m appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]