# Production Deployment & Operations Guide: WealthGuard AI

## 1. Overview

This guide outlines the production deployment lifecycle for the Grounded Advisory Assistant (GAA) / WealthGuard AI. The system comprises:
1. **Frontend**: Next.js 14 Standalone Web Application.
2. **Backend**: FastAPI Application with ChromaDB vector engine and RAG pipeline.
3. **Database**: PostgreSQL 16 relational database with Alembic schema versioning.

---

## 2. Prerequisites & System Requirements

- **Linux / Windows / macOS** host environment with Docker Engine 24.0+ and Docker Compose v2.20+.
- **Host Resources**:
  - Minimum: 2 vCPUs, 4 GB RAM, 20 GB SSD storage.
  - Recommended: 4 vCPUs, 8 GB RAM, 50 GB SSD storage.
- **Outbound Network Access**:
  - Access to Groq Cloud API (`api.groq.com`) or OpenAI API (`api.openai.com`).

---

## 3. Production Environment Configuration

Create a secure `.env` file in the project root:

```env
# Runtime Environment
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="WealthGuard AI"

# Relational Database (PostgreSQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_high_entropy_24_to_32_char_password_with_symbols
POSTGRES_DB=gaa_db
DATABASE_URL=postgresql://postgres:your_high_entropy_24_to_32_char_password_with_symbols@gaa_postgres:5432/gaa_db

# Cryptographic Secrets (Minimum 32 random characters: openssl rand -hex 32)
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32_characters_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
RESET_TOKEN_EXPIRE_MINUTES=15

# LLM Inference Providers
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_production_groq_api_key
GROQ_MODEL=llama-3.1-70b-versatile

# OpenAI Fallback / Embeddings (if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-your_production_openai_api_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database & Persistence
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=/app/data/chroma
SIMILARITY_THRESHOLD=0.68

# Network & CORS Origins (Strict whitelist, NO wildcards in production)
ALLOWED_ORIGINS=https://wealthguard.yourbank.com,http://localhost:3000
NEXT_PUBLIC_API_URL=https://api.wealthguard.yourbank.com
```

> [!CRITICAL]
> In production mode (`ENVIRONMENT=production`), the application automatically validates `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_ORIGINS`, and LLM API keys on startup, refusing to run if insecure defaults or placeholders are detected.

---

## 4. Containerized Deployment (Docker Compose)

### 4.1 Launch Services
Execute from repository root:
```bash
docker compose up -d --build
```

### 4.2 Verify Container Health
```bash
docker compose ps
```
All services (`gaa_postgres`, `gaa_backend`, `gaa_frontend`) should report `healthy`.

### 4.3 Container Network Isolation
- `gaa_postgres` operates on the private internal network (`gaa_internal`) with no external ports exposed.
- `gaa_backend` exposes port `8000` to the host/reverse proxy.
- `gaa_frontend` exposes port `3000` to the host/reverse proxy.

### 4.4 Persistent Data and Safe Teardown

Docker Compose stores relational data, uploaded documents, and ChromaDB files in the named volumes `gaa_postgres_data`, `gaa_backend_uploads`, and `gaa_backend_chroma`. Rebuilding or recreating containers does not remove these volumes.

Use `docker compose down` to stop and remove the stack while retaining its named volumes. Avoid `docker compose down --volumes` for routine maintenance: it deletes the Compose-managed volumes and permanently removes the database, uploaded files, and local vector index unless they have been backed up.

Before a planned data reset or migration, run the repository backup script (`scripts/backup.ps1` on Windows or `scripts/backup.sh` on Linux/macOS). Keep the resulting database dump and volume archives outside the Docker volumes being changed, and verify a restore in a separate environment before relying on the backup for recovery.

---

## 5. Database Migrations (Alembic)

The backend entrypoint automatically applies migrations on container startup (`alembic upgrade head`).

### 5.1 Manual Migration Execution
You can manually apply migrations inside the running backend container:
```bash
docker compose exec gaa_backend alembic upgrade head
```

### 5.2 Verify Applied Migrations
```bash
docker compose exec gaa_backend alembic history --verbose
```

---

## 6. Health Checks & Observability

### 6.1 Liveness Probe
Verifies that the application process is running:
```bash
curl -f http://localhost:8000/health/liveness
# Response: {"status": "alive", "service": "WealthGuard AI", "timestamp": "..."}
```

### 6.2 Readiness Probe
Checks relational database connectivity and Chroma persistent vector storage path:
```bash
curl -f http://localhost:8000/health/readiness
# Response 200 OK:
# {"status": "ready", "checks": {"database": "connected", "vector_store": "connected", "chroma_path": "/app/data/chroma"}, "timestamp": "..."}
```

---

## 7. Backup & Disaster Recovery

### 7.1 Automated Script
Run the automated backup script:
- Linux / macOS:
  ```bash
  chmod +x scripts/backup.sh
  ./scripts/backup.sh
  ```
- Windows PowerShell:
  ```powershell
  .\scripts\backup.ps1
  ```

### 7.2 Manual Backup Commands

#### PostgreSQL Dump:
```bash
docker exec -t gaa_postgres pg_dump -U postgres gaa_db > backup_$(date +%F).sql
```

#### Upload Storage & Chroma Vector Archive:
```bash
docker run --rm -v gaa_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_$(date +%F).tar.gz -C /data .
docker run --rm -v gaa_backend_chroma:/data -v $(pwd):/backup alpine tar czf /backup/chroma_$(date +%F).tar.gz -C /data .
```

### 7.3 Disaster Recovery Restore

To restore into a fresh environment:
- Linux / macOS:
  ```bash
  ./scripts/restore.sh <SQL_FILE> <UPLOADS_TAR_GZ> <CHROMA_TAR_GZ>
  ```
- Windows PowerShell:
  ```powershell
  .\scripts\restore.ps1 -SqlFile backup.sql -UploadsTar uploads.tar.gz -ChromaTar chroma.tar.gz
  ```

---

## 8. Testing & Validation Checklist

Verify the deployment against these criteria:

1. **Health & Connectivity**:
   - `docker compose ps` shows all containers in `healthy` status.
   - Frontend is accessible at `http://localhost:3000` / `https://wealthguard.yourbank.com`.
   - Backend liveness returns 200: `curl -f http://localhost:8000/health/liveness`.
   - PostgreSQL is queryable via `docker exec -it gaa_postgres psql -U postgres -d gaa_db -c "SELECT 1;"`.

2. **CORS Security**:
   - Web browser requests from configured `ALLOWED_ORIGINS` succeed without CORS errors.
   - Requests from untrusted origins are blocked with CORS policy errors.
   - Wildcard `*` is strictly forbidden in production.

3. **HTTP Security Headers**:
   - `Content-Security-Policy`: `default-src 'self'; frame-ancestors 'none';`
   - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`
   - `X-Frame-Options`: `DENY`
   - `X-Content-Type-Options`: `nosniff`
   - `Referrer-Policy`: `strict-origin-when-cross-origin`
   - `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`

4. **Authentication Flow & Zero Account Enumeration**:
   - Signup, login, and password reset flows work with valid JWT issuance and expiry.
   - `/auth/forgot-password` returns identical generic messages for registered vs unregistered emails.

5. **Rate Limiting**:
   - High-frequency burst attempts trigger `429 Too Many Requests` with `Retry-After` header.

6. **Edge Cases**:
   - Uploads >25MB are refused with `413 Payload Too Large`.
   - Queries >4000 characters are refused with `422 Unprocessable Entity`.
   - Missing or template API keys fail closed.
   - Prompt injection attempts are neutralized by `<untrusted_*>` boundary delimiters.
