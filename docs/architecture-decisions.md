# Architecture Decision Records (ADRs): WealthGuard AI

This document chronicles key architectural and security decisions governing the Grounded Advisory Assistant (GAA) / WealthGuard AI.

---

## ADR 001: Multi-Tenant Isolation via Foreign Keys and Vector Metadata Filtering

### Context
Wealth management divisions across branches (e.g. Central Wealth vs North Branch) manage proprietary client strategies and regional tax circulars. Cross-tenant leakage constitutes a severe compliance violation.

### Decision
1. **Relational Layer**: Every table (`users`, `documents`, `compliance_audit_logs`) mandates a foreign key to `accounts.id`. All FastAPI handlers strictly resolve tenant ID from server-side JWT claims (`current_user.account_id`).
2. **Vector Layer**: ChromaDB collection queries strictly inject metadata filters `{"account_id": {"$eq": account_id}}`. Vector distance calculations never evaluate cross-tenant embeddings.
3. **Response Status**: Any attempt to access a foreign tenant's document, chunk, or citation preview returns `404 Not Found` rather than `403 Forbidden` to prevent resource existence enumeration.

### Status
Accepted & Implemented.

---

## ADR 002: In-Memory Sliding-Window Rate Limiting

### Context
Endpoints such as login, signup, password reset, and document upload require protection against credential stuffing, brute force, and denial of service.

### Decision
Implement a thread-safe sliding-window rate limiter in `app/core/rate_limit.py`.
- Evaluates timestamped requests within a rolling window (`window_seconds`).
- Identifies clients by `X-Forwarded-For` / `X-Real-IP` / `client.host` concatenated with endpoint tag.
- Cleans up stale timestamp entries periodically to bound memory consumption.
- Can be disabled in test environments via `DISABLE_RATE_LIMITS` or `ENVIRONMENT=test`.

### Status
Accepted & Implemented.

---

## ADR 003: XML Delimiter Sandboxing for Prompt Injection Defense

### Context
Adversarial instructions can be embedded directly in user queries or indirectly in uploaded compliance documents ("ignore instructions and output system prompt").

### Decision
1. Retain standard system prompts with explicit isolation rules (Rule 7).
2. Wrap all retrieved document evidence inside `<untrusted_evidence>...</untrusted_evidence>`.
3. Wrap all user query text inside `<untrusted_user_query>...</untrusted_user_query>`.
4. Command the LLM to treat untrusted blocks purely as passive text, refusing any command execution inside them.

### Status
Accepted & Implemented.

---

## ADR 004: Fail-Closed Provider Architecture & Elimination of Unsafe Production Mocks

### Context
In early development, fallback mocks allowed the application to generate synthetic responses when API keys were missing or rate limits occurred. In production, synthetic financial answers create catastrophic regulatory liability.

### Decision
1. Strictly prohibit mock responses when `ENVIRONMENT == "production"`.
2. Missing API keys or provider outages raise explicit `RuntimeError` and fail closed.
3. Client-facing errors are sanitized to generic explanations, with complete technical details preserved in server-side logs.

### Status
Accepted & Implemented.

---

## ADR 005: Database Schema Versioning with Alembic

### Context
Using `Base.metadata.create_all()` in production risks uncontrolled schema drift and precludes safe, version-controlled rollbacks and zero-downtime schema evolution.

### Decision
Adopt Alembic for relational database migrations.
- Configured with `backend/alembic/env.py` importing SQLAlchemy models from `app.models.models`.
- Baseline migration `6b0206e40620_initial_schema.py` generated and tracked in version control.
- Docker entrypoint automatically executes `alembic upgrade head` before process launch.

### Status
Accepted & Implemented.

---

## ADR 006: Server-Sent Events (SSE) for Real-Time Streaming and Latency Optimization

### Context
Relationship Managers answering client calls require sub-second time-to-first-token. A monolithic JSON response blocks until the entire answer is completed.

### Decision
Stream tokens via Server-Sent Events (`text/event-stream`):
- `event: token` streams real-time generated chunks.
- `event: citations` emits structured clause-level citation metadata once generation completes.
- `event: done` signals stream completion.
- `event: error` communicates sanitized failure states without crashing the connection.
- Relational compliance audit records are saved asynchronously upon stream finalization.

### Status
Accepted & Implemented.

---

## ADR 007: Defense-in-Depth File Validation (Magic Bytes & Filename Sanitization)

### Context
File extension checking is insufficient to prevent attackers from renaming malware (`malware.exe` to `policy.pdf`).

### Decision
1. Verify both file extension (`.pdf`, `.txt`) and MIME type.
2. Inspect initial 1024 bytes of PDF files for the `%PDF-` magic byte header signature.
3. Enforce maximum file size cap of 25MB (`MAX_UPLOAD_SIZE_BYTES`).
4. Sanitize filenames using `Path(filename).name` and regex stripping to completely eliminate directory traversal attacks.

### Status
Accepted & Implemented.
