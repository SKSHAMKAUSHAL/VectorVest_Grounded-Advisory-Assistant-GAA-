#!/bin/sh
set -e

# Run database migrations if alembic is present
if [ -f "alembic.ini" ]; then
    echo "[Entrypoint] Running Alembic database migrations..."
    alembic upgrade head || echo "[Entrypoint] Warning: Alembic migration encountered an error or already up to date."
fi

echo "[Entrypoint] Starting application process..."
exec "$@"
