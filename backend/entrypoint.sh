#!/bin/sh
set -e

if [ "$APP_MODE" = "worker" ]; then
  echo "Starting worker mode..."
  exec python -m app.worker.main
fi

echo "Starting API mode..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000