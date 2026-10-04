#!/usr/bin/env bash
# ==============================================================================
# WealthGuard AI — Production Backup Script
# Performs PostgreSQL database dump and archives persistent Docker volumes.
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%F_%H%M%S)"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-gaa_postgres}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-gaa_db}"

mkdir -p "${BACKUP_DIR}"

echo "=========================================================="
echo " Starting WealthGuard AI Disaster Recovery Backup: ${TIMESTAMP}"
echo "=========================================================="

# 1. PostgreSQL Database Dump
echo "[1/3] Dumping PostgreSQL database '${POSTGRES_DB}' from '${POSTGRES_CONTAINER}'..."
docker exec -t "${POSTGRES_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.sql"
echo "      Saved to: ${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.sql"

# 2. Archive Uploaded Documents Volume
echo "[2/3] Archiving uploads volume (gaa_backend_uploads)..."
docker run --rm \
    -v gaa_backend_uploads:/data:ro \
    -v "$(pwd)/${BACKUP_DIR}":/backup \
    alpine tar czf "/backup/uploads_${TIMESTAMP}.tar.gz" -C /data .
echo "      Saved to: ${BACKUP_DIR}/uploads_${TIMESTAMP}.tar.gz"

# 3. Archive ChromaDB Persistent Vector Storage
echo "[3/3] Archiving ChromaDB vector storage volume (gaa_backend_chroma)..."
docker run --rm \
    -v gaa_backend_chroma:/data:ro \
    -v "$(pwd)/${BACKUP_DIR}":/backup \
    alpine tar czf "/backup/chroma_${TIMESTAMP}.tar.gz" -C /data .
echo "      Saved to: ${BACKUP_DIR}/chroma_${TIMESTAMP}.tar.gz"

echo "=========================================================="
echo " Backup completed successfully at $(date)!"
echo " Backups stored in: ${BACKUP_DIR}"
echo "=========================================================="
