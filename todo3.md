Production Environment Configuration
.env Settings: Use ENVIRONMENT=production and DEBUG=false. Configure strong secrets (no defaults). For example, set POSTGRES_PASSWORD to a high-entropy value (at least 24–32 characters with mixed case, digits, symbols), and run openssl rand -hex 32 to generate a 256-bit random string for JWT_SECRET_KEY (minimum 32 characters). Do not use short or guessable values. Ensure JWT_ALGORITHM=HS256 (or preferably RS256 for asymmetric signing) and reasonable token lifetimes (e.g. 8 hr for access, 15 min for reset). Populate GROQ_API_KEY and OPENAI_API_KEY with your production LLM credentials from the respective consoles.

URLs & CORS: Set ALLOWED_ORIGINS to your real frontend domains (e.g. https://wealthguard.yourbank.com and any dev domains) – do not use wildcards in production. Similarly set NEXT_PUBLIC_API_URL to your backend API endpoint (e.g. https://api.wealthguard.yourbank.com). In FastAPI’s CORSMiddleware, allow only these origins (e.g. allow_origins=["https://wealthguard.yourbank.com"]) to tighten security.

Tenant Isolation & Databases: Use a dedicated PostgreSQL instance for production (avoid SQLite). In Docker Compose, run postgres:16, set POSTGRES_USER (e.g. “postgres”), POSTGRES_DB=gaa_db, and POSTGRES_PASSWORD as above. Mount a Docker volume for /var/lib/postgresql/data so that the database persists between container restarts. Similarly, set VECTOR_DB_TYPE=chromadb and VECTOR_DB_PATH to a persistent directory (e.g. /app/data/chroma), and mount a volume there. This ensures uploaded documents and Chroma vectors survive container downtime.

Docker Compose: Define services for gaa_postgres (no external port, using Docker internal network), gaa_backend (FastAPI on port 8000), and gaa_frontend (Next.js on port 3000). Expose only necessary ports on the host (e.g. map backend to 8000 behind a reverse proxy, frontend to 3000). After docker compose up --build -d, run docker compose ps to verify all containers show healthy. All stateful services (Postgres, Chroma, upload storage) must use named volumes or bind mounts.

Security Hardening
Secrets & Credentials: In production, enforce minimum secret lengths. For example, fail startup if JWT_SECRET_KEY is a default or under 32 chars. Never commit real secrets to source. Use environment variables or a secret manager. Consider rotating keys periodically.

CORS: Use FastAPI’s CORSMiddleware with allow_origins set to an explicit whitelist of your domains. Do not use ["*"] in production, especially if allow_credentials=True. For example: allow_origins=["https://wealthguard.yourbank.com"], allow_methods=["GET","POST"], allow_headers=["*"] as needed.

HTTP Security Headers: Configure headers on all responses. Key headers include:

Content-Security-Policy (CSP): Strictly limit resource origins (e.g. default-src 'self'; img-src 'self'; script-src 'self' ...) to mitigate XSS.
Strict-Transport-Security: Add Strict-Transport-Security: max-age=31536000; includeSubDomains; preload to enforce HTTPS and prevent protocol downgrade.
X-Frame-Options: Set DENY to prevent the site from being framed and block clickjacking.
X-Content-Type-Options: Set nosniff to disable MIME-type sniffing, preventing browsers from misinterpreting content types.
Referrer-Policy: Use strict-origin-when-cross-origin to limit referrer leakage.
Permissions-Policy: Disable camera, microphone, geolocation etc. (e.g. camera=(), microphone=(), geolocation=()).
CSP frame-ancestors: Alternatively or additionally, include frame-ancestors 'none' to further secure framing. These headers can be configured in FastAPI (via middleware) and in next.config.js for Next.js. Security guidelines (e.g. OWASP) recommend all of the above to protect against XSS, clickjacking, and MITM attacks.
Deployment Operations
Database Migrations: Use Alembic for schema management. The backend entrypoint should run alembic upgrade head on startup (as configured). You can also manually apply migrations inside the backend container:

bash
Copy
docker compose exec gaa_backend alembic upgrade head
alembic history --verbose  # verify applied migrations
Ensure the first run uses a baseline migration (e.g. Initial_schema) and future changes use versioned upgrades.

Health Checks: Implement liveness and readiness probes. For example:

Liveness: GET /health/liveness returns 200 with {"status":"alive","timestamp":...}.
Readiness: GET /health/readiness checks PostgreSQL connection and Chroma path; return 200 only if both are healthy.
Automate docker compose ps or your orchestrator to expect these. A healthy system should show no crashes or 502/503 errors.
Backups & Disaster Recovery: Regularly back up critical data. For PostgreSQL, one can use pg_dump:

pgsql
Copy
docker exec -t gaa_postgres pg_dump -U postgres gaa_db > backup_$(date +%F).sql
(For large DBs, consider physical backups or replication for minimal downtime.)
Also archive persistent volumes. For example, back up uploaded documents and Chroma store:

bash
Copy
docker run --rm -v gaa_backend_uploads:/data -v $(pwd):/backup \
    alpine tar czf /backup/uploads_$(date +%F).tar.gz -C /data .
docker run --rm -v gaa_backend_chroma:/data -v $(pwd):/backup \
    alpine tar czf /backup/chroma_$(date +%F).tar.gz -C /data .
Store backups securely offsite. Periodically test restores by spinning up a fresh environment from these backups.

Testing & Validation
Health & Connectivity: After deployment, verify all services:

Use docker compose ps (or kubectl get pods) to ensure containers are healthy.
Test frontend (http://your-domain/) and backend (curl -f https://api.your-domain/health/liveness).
Confirm the database is accessible: try a simple query via psql.
Check CORS by loading the UI in a browser and performing an API call; no CORS errors should occur.
Authentication Flow: Test signup, login, password-reset. Check JWTs are issued (with correct TTL), and invalid/expired tokens are rejected. Ensure error messages do not leak whether an email is registered (prevent account enumeration).

Security Review: Run an HTTP security header scan (e.g. securityheaders.com) against your domain to verify CSP, HSTS, X-Frame-Options, etc. are present.

Rate Limits: Simulate excessive requests on login/signup/upload/chat endpoints. Confirm you get 429 Too Many Requests with a Retry-After header (e.g. login limited to 15/min).

Functional Tests: Execute existing test suites in production mode (if possible) and ensure all pass. Test edge cases: oversized uploads (>25MB should be rejected), overly long queries (>4000 chars refused), missing API keys scenario (should fail closed), and prompt-injection attempts (should be neutralized by the <untrusted_*> delimiters).

By following these steps – setting all production secrets, configuring volumes and services in Docker Compose, enforcing strict CORS and security headers, and performing health checks and backups – you create a hardened WealthGuard AI deployment. All configuration changes should be documented, and continuous monitoring (logs, alerts) should be in place for any anomalies.

Sources: Security best practices for secrets and JWTs; container data persistence; CORS configuration in FastAPI; CSP and other HTTP headers (MDN docs).