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
POSTGRES_PASSWORD=your_super_strong_postgres_password_min_24_chars
POSTGRES_DB=gaa_db
DATABASE_URL=postgresql://postgres:your_super_strong_postgres_password_min_24_chars@postgres:5432/gaa_db

# Cryptographic Secrets (Minimum 32 random characters)
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

# Vector Database
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=/app/data/chroma
SIMILARITY_THRESHOLD=0.68

# Network & CORS Origins
ALLOWED_ORIGINS=https://wealthguard.yourbank.com,http://localhost:3000
NEXT_PUBLIC_API_URL=https://api.wealthguard.yourbank.com
```

> [!CRITICAL]
> In production mode (`ENVIRONMENT=production`), the application automatically validates `JWT_SECRET_KEY` and rejects default development secrets on startup.

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
- `gaa_postgres` operates on the private internal network (`gaa_internal`) and is not bound to host ports.
- `gaa_backend` exposes port `8000` to the host/reverse proxy.
- `gaa_frontend` exposes port `3000` to the host/reverse proxy.

---

## 5. Database Migrations (Alembic)

The backend container automatically applies migrations at container start via `docker-entrypoint.sh`.

To apply migrations manually:
```bash
# Inside the backend virtual environment
cd backend
alembic upgrade head
```

To verify migration revision history:
```bash
alembic history --verbose
```

---

## 6. Health Checks & Observability

### 6.1 Liveness Probe
Used by Kubernetes or load balancers to determine container liveness:
```bash
curl -f http://localhost:8000/health/liveness
# Response: {"status": "alive", "timestamp": "..."}
```

### 6.2 Readiness Probe
Checks relational database connectivity and vector storage health:
```bash
curl -f http://localhost:8000/health/readiness
# Response: {"status": "ready", "database": "connected", "vector_store": "ready"}
```

---

## 7. Backup & Disaster Recovery

### 7.1 PostgreSQL Database Backup
```bash
docker exec -t gaa_postgres pg_dump -U postgres gaa_db > backup_$(date +%F).sql
```

### 7.2 Vector Store & Document Volume Backup
Archive persistent volumes:
```bash
docker run --rm -v gaa_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_$(date +%F).tar.gz -C /data .
docker run --rm -v gaa_backend_chroma:/data -v $(pwd):/backup alpine tar czf /backup/chroma_$(date +%F).tar.gz -C /data .
```
