#!/usr/bin/env bash
# ==============================================================================
# WealthGuard AI — Production Restore Script
# Restores PostgreSQL database and persistent Docker volumes from archives.
# Usage: ./scripts/restore.sh <SQL_FILE> <UPLOADS_TAR_GZ> <CHROMA_TAR_GZ>
# ==============================================================================
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <SQL_BACKUP_FILE> <UPLOADS_TAR_GZ> <CHROMA_TAR_GZ>"
    exit 1
fi

SQL_FILE="$1"
UPLOADS_TAR="$2"
CHROMA_TAR="$3"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-gaa_postgres}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-gaa_db}"

echo "=========================================================="
echo " Starting WealthGuard AI Disaster Recovery Restore"
echo "=========================================================="

# 1. Restore PostgreSQL Database
echo "[1/3] Restoring PostgreSQL database from ${SQL_FILE}..."
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "${SQL_FILE}"
echo "      Database restored."

# 2. Restore Uploads Volume
echo "[2/3] Restoring uploads volume from ${UPLOADS_TAR}..."
docker run --rm \
    -v gaa_backend_uploads:/data \
    -v "$(cd "$(dirname "${UPLOADS_TAR}")" && pwd)":/backup \
    alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "${UPLOADS_TAR}") -C /data"
echo "      Uploads restored."

# 3. Restore ChromaDB Vector Store
echo "[3/3] Restoring ChromaDB storage from ${CHROMA_TAR}..."
docker run --rm \
    -v gaa_backend_chroma:/data \
    -v "$(cd "$(dirname "${CHROMA_TAR}")" && pwd)":/backup \
    alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "${CHROMA_TAR}") -C /data"
echo "      ChromaDB restored."

echo "=========================================================="
echo " Restore completed successfully!"
echo "=========================================================="
