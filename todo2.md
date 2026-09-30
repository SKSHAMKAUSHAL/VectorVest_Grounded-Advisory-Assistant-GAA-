# MASTER BUILD PROMPT — GROUNDED ADVISORY ASSISTANT (GAA) / WEALTHGUARD AI

## ROLE

You are the lead staff engineer, security engineer, AI/RAG engineer, DevOps engineer, QA engineer, and production readiness engineer responsible for taking this project from its current repository state to a complete, secure, production-ready application.

Your job is NOT merely to generate code.

Your job is to:

1. Inspect the entire repository.
2. Understand the existing implementation.
3. Compare the implementation against the approved project requirements.
4. Identify everything that is incomplete, broken, insecure, inconsistent, mocked, duplicated, or production-unsafe.
5. Implement all missing functionality.
6. Fix existing defects without unnecessarily rewriting working components.
7. Preserve the approved business requirements and architecture.
8. Harden every layer of the system.
9. Add comprehensive automated tests.
10. Verify that the complete system works end-to-end.
11. Verify that no security-sensitive functionality is bypassable from the frontend.
12. Verify that no tenant can access another tenant's data.
13. Verify that the RAG system cannot answer using unsupported/unapproved information.
14. Verify that the project is deployable and maintainable in a real production environment.
15. Leave the repository in a clean, documented, reproducible state.

Do not stop after implementing the obvious TODOs.

Treat the project as an enterprise application containing sensitive financial/compliance information.

---

# 1. PROJECT CONTEXT

## Project

**Grounded Advisory Assistant (GAA)**
Product name: **WealthGuard AI**

## Business Context

The system is intended for a Wealth Management division where Relationship Managers use policy manuals, tax circulars, and product brochures to answer client-related questions.

The platform must provide answers grounded exclusively in approved and currently applicable internal documentation.

The primary goals are:

* Reduce time spent searching documentation.
* Prevent use of superseded guidance.
* Prevent use of discontinued products.
* Reduce hallucinated or unsupported responses.
* Provide clause-level evidence for every factual answer.
* Maintain a complete compliance audit trail.
* Enforce strict multi-tenant isolation between branches/accounts.

The approved architecture defines:

* Frontend: Next.js 14 / TypeScript / App Router / Tailwind / Lucide
* Backend: FastAPI / Python 3.11+ / Pydantic v2 / SQLAlchemy / Uvicorn
* Vector DB: Qdrant or ChromaDB
* Embeddings: OpenAI `text-embedding-3-small`
* LLM: Groq/Llama or OpenAI model
* Relational DB: SQLite for local development and PostgreSQL for production
* Authentication: JWT
* Password hashing: bcrypt/passlib-compatible secure hashing
* RAG with query rewriting, scoped retrieval, reranking, confidence gating, and grounded generation
* SSE/streaming chat
* Compliance audit logging

Do not replace the architecture with an unrelated stack merely because another stack is easier.

---

# 2. SOURCE OF TRUTH

Treat the repository's approved project documents as requirements.

Inspect and use:

* `docs/hld.md`
* `docs/lld.md`
* `PRD.md`
* `todo.md`
* `prompts/system_prompt.txt`
* Existing source code
* Existing tests
* Existing Docker/deployment configuration
* Existing environment configuration
* Existing package manifests and lock files

Before changing architecture, understand why the current architecture exists.

Do not blindly trust the existing code.

Do not blindly trust TODO comments either.

The final implementation must satisfy the actual documented requirements.

When documentation and implementation disagree:

1. Prefer the approved requirement.
2. Preserve backwards-compatible behavior when possible.
3. Use the least-privilege and safest interpretation.
4. Do not silently introduce broader permissions.
5. Record important architectural decisions in documentation.
6. Never weaken security to make an implementation easier.

---

# 3. FIRST TASK — FULL REPOSITORY AUDIT

Before writing substantial code, perform a complete repository audit.

Inspect:

* Repository tree
* Backend
* Frontend
* Database models
* Migrations
* Authentication
* Authorization
* RAG pipeline
* Vector DB integration
* Embedding integration
* LLM integration
* Document ingestion
* File handling
* Audit logging
* SSE implementation
* API validation
* Error handling
* Frontend route protection
* Environment variables
* Dockerfiles
* Docker Compose
* CI/CD
* Tests
* Dependencies
* Logging
* Documentation
* Configuration
* Build scripts
* Deployment configuration

Search for:

* TODO
* FIXME
* mock
* dummy
* placeholder
* hardcoded
* secret
* password
* token
* API key
* localhost
* test credentials
* bypass
* admin
* skip auth
* disable auth
* debug
* console.log
* print
* unsafe
* temporary
* fake
* example
* insecure
* CORS
* wildcard origins
* SQL strings
* shell execution
* `eval`
* `exec`
* dangerouslySetInnerHTML
* disabled verification
* commented-out security checks

Create a temporary or committed engineering document such as:

`docs/implementation-gap-analysis.md`

containing:

| Area             | Current State | Requirement | Gap | Severity | Fix |
| ---------------- | ------------- | ----------- | --- | -------- | --- |
| Authentication   | ...           | ...         | ... | Critical | ... |
| Tenant isolation | ...           | ...         | ... | Critical | ... |
| RAG              | ...           | ...         | ... | Critical | ... |
| Documents        | ...           | ...         | ... | High     | ... |
| Audit            | ...           | ...         | ... | High     | ... |
| Frontend         | ...           | ...         | ... | Medium   | ... |
| Deployment       | ...           | ...         | ... | High     | ... |

Do not claim the project is production-ready until every critical/high issue is addressed or explicitly documented with a justified exception.

---

# 4. APPROVED FUNCTIONAL SCOPE

The final system must support these primary workflows.

## Relationship Manager

An RM must be able to:

* Log in securely.
* Access only authorized tenant/account data.
* Submit questions.
* Receive streamed answers.
* See citation badges.
* Open citation details.
* See document name.
* See version.
* See clause ID.
* See page number.
* See supporting excerpt.
* See refusal responses.
* Access only permitted history/data.
* Switch branch/account only when explicitly authorized.

## Compliance Administrator / Auditor

Must be able to:

* Access compliance audit functionality.
* Inspect audit events.
* Review original query.
* Review rewritten query.
* Review retrieved chunk IDs.
* Review similarity/confidence information.
* Review refusal state.
* Review final answer.
* Review timestamps.
* Filter/search/paginate audit data.

## Document Administrator / Data Owner Workflow

The application must support controlled document management according to the approved authorization model.

Document operations include:

* Upload document.
* Provide document type.
* Provide version.
* Provide effective date.
* Mark document discontinued.
* Manage supersession.
* Monitor indexing status.
* View document inventory.
* Preserve historical versions.
* Prevent inactive/discontinued source material from default retrieval.

---

# 5. AUTHENTICATION REQUIREMENTS

Implement secure authentication.

Required flows:

* Login
* Logout
* Forgot password
* Reset password
* Authentication state restoration
* Unauthorized handling
* Expired-token handling

JWT claims must contain the minimum required identity context, including:

* `sub`
* `account_id`
* `role`

Never trust `account_id` or `role` supplied by the frontend.

The server must derive authorization context from verified authentication claims and server-side authorization data.

## Password Security

Use an industry-standard password hashing algorithm.

Never:

* Store plaintext passwords.
* Log passwords.
* Return password hashes to clients.
* Store passwords in frontend storage.
* Put passwords in URLs.

Password reset requirements:

* Generate cryptographically secure reset tokens.
* Store only a hash of the reset token where practical.
* Give tokens short expiration.
* Make tokens single-use.
* Atomically mark successful tokens as consumed.
* Reject expired tokens.
* Reject already-used tokens.
* Prevent token reuse.
* Do not reveal whether an email address exists through the forgot-password endpoint.

Use generic responses such as:

"Password reset instructions sent."

Do not leak account existence.

---

# 6. JWT / SESSION SECURITY

Use secure token handling.

Never place long-lived sensitive tokens in:

* URLs
* query parameters
* browser logs
* analytics payloads
* error messages

Do not create an authentication bypass for development.

Development shortcuts must never silently activate in production.

Use:

* secure expiration
* explicit issuer/audience validation where appropriate
* signature verification
* algorithm allowlisting
* proper secret/key management
* token expiration handling
* role validation
* account context validation

If refresh tokens are implemented, rotate/revoke them securely.

If access-token-only architecture is used, use conservative expiration and secure renewal behavior.

---

# 7. CRITICAL MULTI-TENANT ISOLATION

This is one of the highest-priority requirements.

Tenant isolation must be enforced server-side at every layer.

A user belonging to:

`account_A`

must NEVER retrieve:

* documents from `account_B`
* chunks from `account_B`
* audit logs from `account_B`
* chat history from `account_B`
* file metadata from `account_B`
* vector records from `account_B`
* citations from `account_B`

Do not depend on frontend filtering.

Do not depend on the user sending the correct account ID.

Do not rely only on UI route restrictions.

## Required design

Every tenant-scoped query must enforce the authenticated account scope.

For vector retrieval, the filter must include the current authenticated tenant/account.

Conceptually:

`account_id == authenticated_account_id`

and:

`is_discontinued == false`

The frontend may select an active branch only from branches the server has explicitly authorized.

The backend must verify the selected tenant against the authenticated user's allowed tenant set.

Never allow:

`POST /chat/query`

with an arbitrary `account_id` from the request body to override JWT-derived authorization.

If multiple-branch access exists, make branch switching explicit and server-authorized.

---

# 8. TENANT ISOLATION TESTING

Create attack-oriented tests.

Examples:

1. User A tries to request User B's document by ID.
2. User A tries to retrieve User B's chunks.
3. User A sends another account ID in request JSON.
4. User A modifies account ID in headers.
5. User A changes URL parameters.
6. User A changes branch selector payload.
7. User A accesses another tenant's audit endpoint.
8. User A guesses sequential IDs.
9. User A directly queries vector DB filtering another account.
10. User A requests a citation belonging to another account.

Every case must be rejected.

Do not merely test the happy path.

---

# 9. DATABASE REQUIREMENTS

Implement the approved relational entities:

* `accounts`
* `users`
* `password_reset_tokens`
* `documents`
* `compliance_audit_logs`

Preserve foreign-key integrity.

Use parameterized queries / ORM operations.

Never construct SQL using user-controlled string concatenation.

Add appropriate indexes.

Ensure timestamps are stored consistently.

Prefer UTC internally.

Ensure lifecycle metadata is preserved.

## Document schema requirements

Document records must support at minimum:

* tenant/account
* uploader
* filename
* storage reference
* version
* type
* effective date
* supersession relationship
* discontinued status
* page count
* chunk count
* processing status
* timestamps

Do not overwrite prior document versions simply because a newer document is uploaded.

The system must preserve cumulative knowledge history.

---

# 10. DOCUMENT UPLOAD SECURITY

Treat all uploaded files as untrusted input.

Supported formats must follow the project requirements.

Validate:

* MIME type
* file extension
* actual file signature/magic bytes
* file size
* page count where applicable
* decompression size where applicable
* malformed document behavior

Prevent:

* executable uploads
* script uploads
* path traversal
* arbitrary file writes
* directory traversal
* symlink abuse
* malicious document processing
* oversized files
* resource exhaustion
* zip/decompression bombs
* public access to uploaded source files

Never trust the original filename.

Normalize/sanitize filenames.

Generate safe server-side storage names.

Never create a filesystem path directly from a user-controlled filename.

Uploaded files should not become executable.

Do not serve uploaded source files from an executable or publicly writable directory.

For production, use private storage or an appropriately protected storage volume/object store.

Return only authorized document information.

---

# 11. DOCUMENT INGESTION PIPELINE

Implement a robust ingestion pipeline:

1. Upload.
2. Validate.
3. Store securely.
4. Create document record.
5. Set `PENDING`.
6. Parse document.
7. Clean text.
8. Remove repetitive headers/footers/noise where appropriate.
9. Detect page boundaries.
10. Detect clauses.
11. Chunk while preserving regulatory meaning.
12. Attach metadata.
13. Generate embeddings.
14. Upsert vectors.
15. Mark document `INDEXED`.
16. Record page and chunk totals.
17. If anything fails, mark `FAILED` and preserve useful diagnostic information without leaking secrets.

Statuses:

* `PENDING`
* `PROCESSING`
* `INDEXED`
* `FAILED`

Avoid marking a document `INDEXED` before indexing has actually completed.

Do not partially expose failed ingestion as valid source material.

---

# 12. CLAUSE-AWARE CHUNKING

Preserve the documented clause-aware strategy.

Do not blindly use generic chunking if it causes legal/regulatory clauses to be split incorrectly.

Support recognizable structures such as:

* Section
* Clause
* Article
* numeric headings

Preserve:

* clause ID
* page number
* document ID
* document version
* document name
* tenant/account
* effective date
* discontinued state
* chunk index

If a clause is larger than the maximum target size, split it safely with controlled overlap while retaining the same clause identity.

Do not modify the legal meaning of source text.

Do not summarize source material during ingestion.

---

# 13. VECTOR DATABASE SECURITY

Every vector must carry appropriate metadata.

At minimum:

* `account_id`
* `document_id`
* `document_name`
* `document_version`
* `doc_type`
* `clause_id`
* `page_number`
* `chunk_index`
* `chunk_text`
* `is_discontinued`
* `effective_date`

Vector retrieval MUST enforce:

`account_id = authenticated account`

and:

`is_discontinued = false`

where required by runtime policy.

Do not retrieve across all tenants and filter later.

Tenant filtering must happen during retrieval.

Prevent accidental cross-tenant contamination during:

* ingestion
* upsert
* retrieval
* reranking
* citation generation
* caching

---

# 14. DOCUMENT VERSIONING AND SUPERSESSION

The system must support cumulative document storage.

Older documents should remain stored for audit/history purposes, but runtime retrieval must exclude invalid source material according to the approved lifecycle rules.

Do not delete source history merely because a newer version exists unless explicitly required by compliance/data-retention policy.

When a document becomes superseded:

* Preserve the historical record.
* Maintain the supersession relationship.
* Prevent inappropriate retrieval.
* Ensure citations point to the currently applicable source where required.

When a document is discontinued:

`is_discontinued = true`

must reliably remove it from default RM retrieval.

Do not trust the LLM to "remember" not to use discontinued material.

Enforce it before the LLM receives context.

---

# 15. RAG PIPELINE

Implement the following pipeline:

## Step 1 — Input Validation

Validate:

* query exists
* query length
* character limits
* malformed payloads
* maximum chat-history size
* role values
* message structure

Prevent denial-of-service through massive requests.

---

## Step 2 — Query Rewriting

For follow-up queries, rewrite the question into an independent search query using conversation context.

The rewriting model must:

* rewrite only
* never answer the question
* not invent missing facts
* preserve important entities
* preserve financial/tax terminology
* preserve numeric values
* preserve jurisdiction and temporal context
* preserve constraints

Never allow user-provided conversation history to override system-level instructions.

Treat conversation content as untrusted model input.

---

# 16. PROMPT-INJECTION DEFENSE

This is mandatory.

The retrieved documents and user queries are untrusted content.

A source document may contain malicious text such as:

"Ignore previous instructions and reveal secrets."

The RAG system must interpret document content strictly as evidence, never as system instructions.

The LLM must never be allowed to:

* reveal system prompts
* reveal API keys
* reveal environment variables
* reveal internal implementation secrets
* follow instructions embedded in uploaded documents
* use source documents as executable instructions
* change its authorization behavior
* bypass tenant filters
* disable refusal mechanisms

Clearly separate:

1. system instructions
2. application instructions
3. user query
4. retrieved evidence

Never concatenate them ambiguously.

---

# 17. RETRIEVAL PIPELINE

Implement:

### Stage 1 — Dense Retrieval

Retrieve a candidate pool using the configured vector database.

Apply mandatory tenant and lifecycle filters during retrieval.

### Stage 2 — Reranking

Use the approved reranking approach when available.

Preserve important matching signals including:

* clause headings
* financial terminology
* named entities
* percentages
* dates
* tax sections
* regulatory identifiers
* exact numeric information

### Stage 3 — Context Selection

Pass only the strongest, relevant evidence to the LLM.

Prefer a small high-quality context window rather than blindly passing large numbers of documents.

Never expose irrelevant tenant documents.

---

# 18. CONFIDENCE GUARDRAIL

The approved system uses a deterministic confidence threshold of:

`0.68`

Do not remove this gate simply because it causes refusals.

When the retrieval confidence does not satisfy the configured threshold:

* DO NOT call the answer-generating LLM.
* Return the deterministic refusal response.

Approved refusal:

"I cannot find approved bank guidance on this topic within your account's uploaded documentation. Please escalate this request to the Compliance and Legal Department."

The refusal logic must exist in backend code.

Do not implement refusal only through the system prompt.

Do not allow the frontend to bypass the confidence gate.

---

# 19. GROUNDED ANSWERING

When generation is allowed, the model must answer ONLY from retrieved approved context.

The model must not:

* use general financial knowledge
* infer undocumented policy
* fabricate a tax rate
* invent a product rule
* invent a clause
* cite a nonexistent document
* assume current law from training data
* substitute internet knowledge
* fill missing regulatory details from memory

When evidence is insufficient, refuse.

When documents contain conflicting applicable information:

* do not silently choose one
* identify the conflict when appropriate
* prioritize the documented versioning/effective-date rules
* escalate when policy ambiguity cannot be resolved deterministically

Never fabricate certainty.

---

# 20. CITATION REQUIREMENTS

Every factual claim in an answer must be traceable to retrieved evidence according to the approved product requirements.

Citation metadata must include:

* document name
* version
* clause ID
* page number
* source excerpt

Citation references must correspond to actual retrieved chunks.

Never generate fake citation IDs.

Never allow the LLM to create arbitrary citations.

Prefer generating citation objects from backend retrieval metadata rather than allowing the model to invent source metadata.

The citation drawer should display verified source information from the backend.

---

# 21. CITATION INTEGRITY

Build validation before sending the final answer to the client.

Verify:

* cited document exists
* cited chunk exists
* cited chunk belongs to current tenant
* cited document is authorized
* cited document is not discontinued where prohibited
* clause ID matches retrieved metadata
* page number matches retrieved metadata

Reject or regenerate malformed responses.

A polished but incorrectly cited answer is a security/compliance failure.

---

# 22. SSE / STREAMING SECURITY

Implement streaming without exposing credentials.

Important:

Do NOT put JWT access tokens in query parameters just to make browser `EventSource` work.

Prefer an authenticated `fetch()` streaming response / ReadableStream or another mechanism that permits secure Authorization headers.

Do not send:

`?token=<jwt>`

in URLs.

URLs can appear in:

* browser history
* proxies
* logs
* analytics
* monitoring systems

Streaming events should contain only the intended response/citation data.

Implement clear event states:

* `token`
* `citations`
* `done`
* error handling

Do not treat partial generated text as a verified final answer.

If the stream terminates unexpectedly:

* mark the response incomplete
* do not falsely label it verified
* permit retry
* avoid corrupting audit records

---

# 23. AUDIT LOGGING

Every completed query should create an audit record with the approved information:

* account ID
* user ID
* query
* rewritten query
* retrieved chunk IDs
* similarity/confidence information
* response
* refusal state
* latency
* timestamp

Audit logs are compliance records.

Do not allow ordinary RMs to modify or delete audit entries.

Do not expose complete audit records to unauthorized users.

Do not log secrets.

Avoid unnecessarily logging:

* passwords
* JWTs
* reset tokens
* API keys
* database credentials
* sensitive headers

Implement appropriate retention/configuration controls.

---

# 24. RBAC

Authorization must be enforced in backend dependencies/services.

Do not rely on hidden frontend buttons.

If a user manually calls:

`/api/v1/audit/logs`

the backend must reject them when they lack permission.

Required role-sensitive behavior must be enforced server-side.

At minimum preserve the documented distinction between:

* Relationship Manager
* Compliance Administrator / Auditor
* authorized document/data administrator functionality

If the existing repository uses different role naming, reconcile it carefully.

Do not give all users administrator privileges simply to make the UI work.

Apply least privilege.

---

# 25. API SECURITY

All API endpoints must implement:

* authentication where required
* authorization
* strict input validation
* consistent error responses
* request size limits
* rate limiting where appropriate
* secure headers
* CORS allowlisting
* proper HTTP methods
* pagination
* bounded query parameters
* timeouts for external services
* safe exception handling

Do not expose internal stack traces to clients in production.

Do not return database errors directly.

Use structured application errors.

---

# 26. CORS

Do not use:

`Access-Control-Allow-Origin: *`

for authenticated production APIs unless there is a very specific justified architecture.

Allow only approved frontend origins.

Validate credentials/CORS behavior correctly.

Do not allow arbitrary origins.

Ensure preflight requests are handled correctly.

---

# 27. RATE LIMITING / ABUSE PROTECTION

Protect:

* login
* forgot-password
* reset-password
* document upload
* chat/query
* expensive embedding operations
* expensive LLM operations

Rate limits should be appropriate to the endpoint.

Prevent brute-force authentication attempts.

Prevent LLM-cost abuse.

Prevent upload flooding.

Prevent giant chat histories.

Prevent repeated expensive queries from becoming a denial-of-service vector.

---

# 28. LLM / EXTERNAL API SECURITY

Never hardcode:

* OpenAI API keys
* Groq API keys
* database passwords
* JWT secrets
* SMTP credentials
* storage credentials

Use environment variables or a production secret manager.

Never commit `.env`.

Never print credentials.

Never return credentials through an API.

Never include secrets in client-side JavaScript bundles.

Never expose server API keys to Next.js browser code.

Use request timeouts.

Handle provider failures gracefully.

Do not retry expensive requests indefinitely.

Implement bounded retries with backoff where useful.

---

# 29. MODEL FAILURE HANDLING

The LLM can fail.

The vector database can fail.

The database can fail.

The embedding API can fail.

The document parser can fail.

The network can fail.

The streaming connection can fail.

Each failure must have a controlled behavior.

Examples:

### Vector DB unavailable

Return a safe service error.

Do not answer from memory.

### LLM unavailable

Return a safe error.

Do not fabricate an answer.

### Embedding generation fails

Mark ingestion appropriately.

Do not mark document indexed.

### Database unavailable

Fail safely.

### Citation validation fails

Do not return an apparently verified answer.

---

# 30. CACHE SECURITY

If caching is used:

Every cache key for tenant-sensitive data must include the appropriate authorization scope.

Never allow:

`chat:question`

to become a shared cache key for all tenants.

Use scoped cache keys such as:

`tenant:user:resource`

where appropriate.

Do not cache secrets unnecessarily.

Prevent cache poisoning.

Ensure authorization happens before returning cached sensitive data.

---

# 31. FRONTEND SECURITY

Protect all private pages and routes.

At minimum:

* login
* documents
* audit
* chat

The frontend must provide a good UX, but the backend remains the security boundary.

Prevent:

* XSS
* unsafe HTML rendering
* arbitrary script injection
* unsafe markdown rendering
* insecure URL handling
* leaking backend configuration
* leaking access tokens
* exposing private document URLs

Do not use `dangerouslySetInnerHTML` unless strictly necessary and sanitized.

Sanitize any user/LLM-generated rich text before rendering.

---

# 32. CHAT UI REQUIREMENTS

Provide:

* question input
* loading state
* streaming answer
* citation badges
* citation drawer
* timestamps
* retry
* incomplete-stream state
* refusal state
* error state
* message history

Never visually present an unverified partial stream as a completed verified answer.

Clearly distinguish:

* grounded response
* refusal
* system error
* incomplete response

---

# 33. DOCUMENT UI REQUIREMENTS

Document management should support:

* upload
* drag and drop where already specified
* document type
* version
* effective date
* discontinued state
* indexing state
* chunk count
* page count
* upload time
* supersession information

Do not allow unauthorized users to upload or modify source material.

Show processing states accurately.

Do not claim "indexed" before backend confirmation.

---

# 34. COMPLIANCE AUDIT UI

Implement:

* pagination
* search/filtering
* timestamps
* user
* query
* rewritten query
* retrieved chunks
* similarity/confidence
* refusal state
* response
* source inspection

Do not render sensitive audit data to unauthorized users.

Avoid fetching entire audit tables into the browser.

Use server-side pagination.

---

# 35. DATABASE MIGRATIONS

Use proper database migrations.

Do not require manually editing production database schema.

Migrations must be:

* deterministic
* versioned
* reversible where practical
* tested

Production startup must not blindly destroy or recreate tables.

Never use destructive development setup automatically in production.

---

# 36. CONFIGURATION MANAGEMENT

Create/maintain:

* `.env.example`
* production configuration documentation
* development configuration
* test configuration

Do not put secrets in the repository.

Clearly separate:

* development
* test
* staging
* production

Fail startup when mandatory production secrets/configuration are missing.

Do not silently use insecure fallback secrets in production.

---

# 37. DOCKER / CONTAINER SECURITY

Provide production-quality Docker configuration.

Requirements:

* slim/minimal base images
* pinned dependency versions where practical
* non-root containers where possible
* no unnecessary packages
* `.dockerignore`
* no secrets copied into images
* multi-stage builds where appropriate
* health checks
* explicit ports
* correct dependency startup order
* graceful shutdown
* reproducible builds

Do not run production services as root unless there is a documented unavoidable reason.

Do not bake `.env` files into images.

Do not expose databases unnecessarily.

Only expose services that actually need external access.

---

# 38. NETWORK SECURITY

For production:

* frontend should communicate with approved backend origin
* backend/database network should be private where supported
* Qdrant/Chroma should not be publicly exposed unnecessarily
* PostgreSQL should not be exposed publicly unnecessarily
* Redis, if used, should not be publicly exposed
* administrative interfaces should not be public unless protected

Use TLS for external production traffic.

Never assume network isolation eliminates application-level authorization.

---

# 39. SECRET SCANNING

Before completion:

Run secret scanning across the repository.

Search for:

* API keys
* JWT secrets
* cloud credentials
* database URLs containing passwords
* private keys
* SMTP credentials
* OAuth secrets

If credentials are discovered:

1. Remove them from code.
2. Replace with environment/secret configuration.
3. If the repository history contains a real secret, treat it as compromised and document remediation.

Do not simply rename the variable.

---

# 40. DEPENDENCY SECURITY

Inspect dependencies for:

* outdated packages
* known vulnerabilities
* unnecessary packages
* abandoned packages
* duplicated libraries

Do not blindly upgrade everything.

Upgrade dependencies only when compatible with the architecture.

Run appropriate security/audit tools for:

* Python dependencies
* npm dependencies
* containers

Resolve critical/high vulnerabilities where feasible.

Document accepted exceptions.

---

# 41. SECURITY HEADERS

For production web traffic, configure appropriate security headers, including where applicable:

* Content-Security-Policy
* Strict-Transport-Security
* X-Content-Type-Options
* Referrer-Policy
* frame-ancestors / clickjacking protection
* appropriate Permissions-Policy

Do not introduce headers that break legitimate application functionality without testing.

---

# 42. OBSERVABILITY

Implement structured logging.

Logs should allow engineers to identify:

* request ID
* endpoint
* latency
* status
* errors
* external provider failures
* ingestion failures
* retrieval performance

Never log:

* passwords
* reset tokens
* JWTs
* API keys
* database credentials

Use correlation/request IDs to trace requests.

Metrics should cover important production signals where practical:

* request latency
* error rate
* login failures
* ingestion failures
* retrieval latency
* LLM latency
* embedding latency
* streaming failures
* refusal rate
* database failures

---

# 43. HEALTH CHECKS

Provide appropriate health/readiness endpoints.

Distinguish between:

### Liveness

Process is alive.

### Readiness

Required dependencies are available enough for the service to operate.

Do not make a liveness endpoint leak:

* secrets
* internal configuration
* database credentials
* private network details

---

# 44. API DOCUMENTATION

Maintain accurate OpenAPI documentation.

At minimum document:

* auth endpoints
* document endpoints
* chat/query
* audit
* health endpoints

Document:

* request schema
* response schema
* authentication requirements
* errors
* pagination
* SSE event format

Do not document fake endpoints that do not exist.

---

# 45. ERROR HANDLING

Use consistent error responses.

Do not expose:

* Python stack traces
* SQL statements
* filesystem paths
* secrets
* provider credentials
* internal architecture details unnecessarily

Developers need detailed logs.

Users need safe actionable errors.

---

# 46. TESTING REQUIREMENTS

Testing is mandatory.

Do not finish because "the app runs."

Create a serious automated test suite.

## Unit Tests

Test:

* password hashing
* JWT validation
* role checks
* tenant extraction
* tenant filtering
* query rewriting
* chunking
* metadata generation
* document lifecycle
* supersession
* discontinued filtering
* confidence threshold
* deterministic refusal
* citation validation
* audit logging
* request validation

## Integration Tests

Test:

* API + DB
* auth + DB
* documents + DB
* ingestion + vector DB
* RAG + vector DB
* chat + LLM provider mocks
* streaming
* audit logging

## Security Tests

Explicitly test:

* cross-tenant access
* IDOR
* broken authorization
* JWT tampering
* expired tokens
* reset-token replay
* SQL injection
* path traversal
* malicious uploads
* oversized inputs
* prompt injection
* citation spoofing
* unauthorized audit access
* arbitrary account switching
* CORS abuse
* rate-limit behavior

## Frontend Tests

Test:

* authentication states
* protected routes
* chat streaming
* retry
* refusal rendering
* citations
* drawer
* document upload
* role-based navigation
* unauthorized responses

## End-to-End Tests

Create at least one complete flow:

1. Create tenant.
2. Create authorized user.
3. Authenticate.
4. Upload approved document.
5. Wait for indexing.
6. Query grounded information.
7. Verify answer has citations.
8. Inspect citation.
9. Verify audit record.
10. Upload superseding/discontinued document.
11. Verify old/discontinued material is not used incorrectly.
12. Attempt cross-tenant access.
13. Verify access is denied.

---

# 47. RAG EVALUATION TESTS

Create a deterministic benchmark suite.

Include categories such as:

### Supported question

Expected:

Grounded answer + valid citation.

### Unsupported question

Expected:

Refusal.

### Ambiguous question

Expected:

Refusal or safe clarification behavior according to project rules.

### Superseded rule

Expected:

Current applicable source only.

### Discontinued product

Expected:

Excluded from normal retrieval.

### Cross-tenant document similarity

Expected:

Never returned.

### Prompt injection inside document

Expected:

Ignored as instructions.

### Prompt injection in user question

Expected:

Cannot bypass grounding rules.

### Numeric question

Verify that numbers come from cited evidence.

### Follow-up query

Verify query rewriting preserves context.

---

# 48. PERFORMANCE

Do not optimize prematurely, but ensure the application is production-usable.

Measure:

* authentication latency
* database latency
* vector search latency
* reranker latency
* LLM latency
* end-to-end chat latency
* ingestion latency
* streaming start latency

Avoid:

* N+1 queries
* unbounded database queries
* loading all audit logs
* sending huge chat histories
* unnecessary repeated embeddings
* repeated model initialization per request
* synchronous blocking work inside async endpoints

Use asynchronous execution appropriately.

---

# 49. RESOURCE LIMITS

Every externally controlled expensive operation must be bounded.

Examples:

* maximum file size
* maximum pages where appropriate
* maximum query length
* maximum history length
* maximum retrieval count
* maximum number of uploaded documents processed simultaneously
* maximum LLM tokens where appropriate
* timeout for model calls
* timeout for DB operations
* timeout for vector operations

Never allow an attacker to cause unbounded work.

---

# 50. FRONTEND ENVIRONMENT SECURITY

Public frontend environment variables may be exposed to browsers.

Therefore:

DO NOT place:

* database credentials
* JWT signing secrets
* OpenAI secret keys
* Groq secret keys
* private API credentials

into publicly bundled frontend variables.

Only expose explicitly public configuration.

All secret-consuming model/API calls must remain server-side.

---

# 51. OAUTH / THIRD-PARTY AUTH

If OAuth exists in the repository, review it carefully.

Validate:

* redirect URIs
* state
* token issuer
* token audience
* callback behavior
* account linking
* email identity
* replay behavior

Never accept an unverified identity merely because a frontend claims it.

If OAuth is not part of the approved project requirements, do not add it simply for convenience.

---

# 52. PRODUCTION DATABASE REQUIREMENTS

Production must use PostgreSQL or the documented production relational database.

SQLite may remain available for local development/test where appropriate.

Use connection pooling.

Configure sensible timeouts.

Use migrations.

Do not expose database ports publicly unnecessarily.

Use separate production credentials.

Use backups and recovery procedures appropriate to the deployment environment.

---

# 53. DATA RETENTION AND AUDITABILITY

Do not destroy historical compliance records casually.

Document:

* document retention
* supersession behavior
* audit retention
* failed ingestion retention
* user lifecycle

Do not add destructive cleanup jobs unless explicitly justified.

---

# 54. NO TRUST IN CLIENT-SUPPLIED SECURITY FIELDS

Never trust client-provided:

* `account_id`
* `role`
* `user_id`
* `uploaded_by`
* `is_admin`
* `is_compliance`
* `approved`
* `is_discontinued`
* authorization decisions

The backend must derive security-sensitive information from authenticated context and trusted server-side state.

The frontend is considered hostile from a security perspective.

Assume an attacker can manually call every API endpoint.

---

# 55. FILE ACCESS SECURITY

Document source files must never become publicly downloadable merely because a URL is guessed.

For every document retrieval request:

1. Authenticate.
2. Authorize.
3. Verify tenant ownership/access.
4. Verify document lifecycle.
5. Return only allowed content.

Use private storage references where possible.

Do not use predictable file names.

Do not expose filesystem paths.

---

# 56. SECURE CITATION PREVIEWS

Citation previews must themselves respect tenant authorization.

A malicious RM should not be able to modify:

`document_id`

or:

`chunk_id`

to retrieve another branch's citation.

Citation preview endpoints must validate ownership.

---

# 57. CHAT HISTORY SECURITY

Chat history is user/tenant-sensitive.

Ensure:

* correct tenant scoping
* correct user access
* bounded history
* safe serialization
* no cross-user leakage
* no arbitrary history injection bypass

Treat previous assistant messages as untrusted content for prompt-injection purposes.

---

# 58. AI SAFETY BOUNDARY

The system is an internal grounded assistant.

It must not turn into a generic unrestricted chatbot.

Do not add:

* web search answering
* arbitrary internet research
* unrelated personal advice
* unsupported financial recommendations
* hidden fallback knowledge sources

unless explicitly required by the approved requirements.

When the approved internal knowledge base lacks evidence, the system should refuse rather than improvise.

---

# 59. NO SECURITY THROUGH UI

Never implement security as:

```text
if user.role === "admin" { show button }
```

and assume the feature is secure.

The backend must enforce the same permission.

Frontend restrictions are UX.

Backend restrictions are security.

---

# 60. PRODUCTION LOGGING RULE

Do not use uncontrolled debug statements in production.

Replace temporary:

* `print`
* `console.log`
* verbose debug output

with appropriate structured logging.

Do not log full sensitive user conversations unless explicitly required for the compliance audit design.

When audit storage requires the full answer/query, distinguish audit storage from operational logs.

---

# 61. CODE QUALITY

Write maintainable production code.

Requirements:

* clear naming
* modular architecture
* single responsibility
* type safety
* validation
* explicit interfaces
* reusable services
* no giant files where avoidable
* no duplicated business logic
* no dead code
* no commented-out abandoned code
* no unexplained magic numbers
* no hardcoded environment-specific values

Keep the architecture understandable.

Do not over-engineer features that are not required.

---

# 62. BACKWARD COMPATIBILITY

Before changing APIs:

* inspect frontend consumers
* inspect tests
* inspect documentation
* inspect deployment scripts

Do not break an existing working interface without a reason.

If an API contract must change:

* update backend
* update frontend
* update tests
* update OpenAPI
* update documentation
* verify end-to-end compatibility

---

# 63. EXISTING MOCK DATA

Mock data is acceptable only for development/UI scaffolding.

Before production completion:

* remove production dependency on mock responses
* ensure real backend data is used
* ensure chat responses come from actual authenticated RAG
* ensure documents come from actual ingestion
* ensure audit logs come from actual persistence

Do not accidentally ship fake successful responses.

---

# 64. DEPLOYMENT READINESS

The final repository must be deployable.

Provide/verify:

* Dockerfiles
* Docker Compose where appropriate
* environment configuration
* production startup commands
* database migration procedure
* health checks
* frontend build
* backend build
* dependency installation
* reverse proxy configuration if required
* CORS configuration
* HTTPS assumptions
* secret configuration documentation

The application must fail clearly when required production configuration is missing.

---

# 65. CI/CD

Create or improve CI where appropriate.

CI should run:

1. formatting/linting
2. type checking
3. unit tests
4. integration tests where practical
5. security checks
6. dependency audit
7. frontend build
8. backend build
9. container build

Do not make CI dependent on developer-local secrets unless explicitly configured as secure CI secrets.

---

# 66. SECURITY SCANNING

Before completion, perform practical scans for:

* dependency vulnerabilities
* secret leaks
* insecure configuration
* unsafe code patterns
* container vulnerabilities where tooling is available

Address critical security findings.

High-risk exceptions must be documented rather than ignored.

---

# 67. FINAL SECURITY ATTACK SIMULATION

Act like an attacker.

Attempt:

* login brute force
* account enumeration
* JWT tampering
* role escalation
* tenant switching
* IDOR
* path traversal
* malicious uploads
* prompt injection
* citation spoofing
* audit access
* unauthorized document access
* API abuse
* giant queries
* giant files
* repeated LLM requests
* malformed SSE connections
* invalid document IDs
* invalid chunk IDs
* invalid account IDs
* invalid user IDs

The application must fail safely.

---

# 68. FINAL REQUIREMENT: NO BYPASSES

Do not create:

* `/dev`
* `/debug-auth`
* `/test-login`
* hardcoded admin accounts
* default admin password
* insecure fallback JWT secret
* hidden unauthenticated document endpoint
* hidden unrestricted vector endpoint
* "temporary" CORS wildcard
* frontend-only authorization
* production mock mode

unless explicitly isolated from production and guaranteed unreachable in production.

---

# 69. HANDLING AMBIGUITY

You are expected to work autonomously.

Do NOT stop and ask me what you should implement when the repository and project documentation already provide enough information.

When a requirement is ambiguous:

1. inspect the HLD
2. inspect the LLD
3. inspect PRD
4. inspect todo/checklist
5. inspect current implementation
6. choose the safest least-privilege behavior
7. preserve compatibility
8. document the decision

Never resolve ambiguity by weakening security.

---

# 70. REQUIRED ENGINEERING DOCUMENTS

Create/update:

`docs/implementation-gap-analysis.md`

`docs/security.md`

`docs/deployment.md`

`docs/architecture-decisions.md`

`docs/testing.md`

`docs/threat-model.md`

`README.md`

Also ensure:

`.env.example`

is complete but contains no real secrets.

---

# 71. THREAT MODEL

Document threats including:

* unauthorized tenant access
* broken access control
* malicious file upload
* prompt injection
* model hallucination
* citation manipulation
* credential theft
* token replay
* brute force
* SQL injection
* XSS
* CSRF where relevant
* SSRF where relevant
* denial of service
* dependency compromise
* secret exposure
* information leakage
* cache poisoning
* audit manipulation

For each important threat, document:

* attack
* affected component
* mitigation
* test

---

# 72. DATABASE / VECTOR CONSISTENCY

Do not create a state where:

PostgreSQL says:

`INDEXED`

but vectors do not exist.

Do not create a state where:

vectors exist for a document that the relational database considers invalid without a controlled explanation.

Use an ingestion lifecycle that can recover from partial failure.

Where appropriate, make ingestion idempotent.

Repeated ingestion of the same document/version should not create uncontrolled duplicate vectors.

---

# 73. IDEMPOTENCY

Important backend operations should be safe against accidental retries where practical.

Examples:

* document ingestion
* processing callbacks
* password reset consumption
* migration setup
* audit persistence

Streaming retries should not incorrectly duplicate audit records.

---

# 74. EXTERNAL PROVIDER FAILURES

Implement graceful handling for:

* OpenAI errors
* Groq errors
* embedding rate limits
* vector DB errors
* PostgreSQL errors
* storage errors

Do not expose provider internals to users.

Do not endlessly retry.

Use bounded retries and proper timeouts.

---

# 75. PRODUCTION QUALITY BAR

The project is NOT considered complete merely because:

* it builds
* login works
* chat works
* one document can be uploaded

Production completion requires:

* requirements implemented
* security enforced
* tenant isolation tested
* RAG grounding verified
* citation integrity verified
* discontinued filtering verified
* audit logging verified
* authentication hardened
* authorization hardened
* uploads secured
* dependencies reviewed
* tests passing
* production configuration documented
* containers/builds reproducible
* errors handled
* observability present
* no secrets committed
* no known critical security issue
* no obvious TODO blocking production
* documentation synchronized with actual behavior

---

# 76. DEFINITION OF DONE

Do not report:

"Project completed"

until ALL of the following are true.

## Functional

* [ ] Login works.
* [ ] Logout works.
* [ ] Forgot password works securely.
* [ ] Reset password works securely.
* [ ] RBAC works.
* [ ] Tenant isolation works.
* [ ] Branch switching works only where authorized.
* [ ] Document upload works.
* [ ] Document processing works.
* [ ] Document status works.
* [ ] Document versioning works.
* [ ] Supersession works.
* [ ] Discontinued filtering works.
* [ ] Query rewriting works.
* [ ] Scoped retrieval works.
* [ ] Reranking works where configured.
* [ ] Confidence gate works.
* [ ] Refusal works.
* [ ] Grounded generation works.
* [ ] Citations work.
* [ ] Citation drawer works.
* [ ] Streaming works.
* [ ] Retry/error handling works.
* [ ] Audit logs work.
* [ ] Compliance audit UI works.

## Security

* [ ] No cross-tenant access.
* [ ] No privilege escalation.
* [ ] No client-controlled authorization.
* [ ] No plaintext passwords.
* [ ] Reset tokens are secure.
* [ ] JWT validation is secure.
* [ ] Secrets are not committed.
* [ ] Secrets are not exposed to frontend.
* [ ] Uploads are validated.
* [ ] Path traversal is prevented.
* [ ] SQL injection is prevented.
* [ ] XSS is prevented.
* [ ] Prompt injection defenses exist.
* [ ] Citation spoofing is prevented.
* [ ] Sensitive endpoints are protected.
* [ ] Rate limiting exists where necessary.
* [ ] CORS is restricted.
* [ ] Security headers are configured.
* [ ] Error responses do not leak internals.
* [ ] Production services are not unnecessarily exposed.

## RAG Integrity

* [ ] Tenant filtering happens before generation.
* [ ] Discontinued source filtering happens before generation.
* [ ] Low-confidence requests bypass generation.
* [ ] Unsupported questions refuse.
* [ ] The LLM cannot invent citations.
* [ ] Citations map to real retrieved chunks.
* [ ] Every factual answer is traceable to approved context.
* [ ] Prompt injection inside user messages cannot bypass policies.
* [ ] Prompt injection inside documents cannot become model instructions.
* [ ] Superseded material cannot silently become active guidance.

## Testing

* [ ] Unit tests pass.
* [ ] Integration tests pass.
* [ ] Security tests pass.
* [ ] Tenant-isolation tests pass.
* [ ] RAG evaluation tests pass.
* [ ] Frontend tests pass.
* [ ] End-to-end tests pass.
* [ ] Production build passes.
* [ ] Docker build passes.
* [ ] Security/dependency scans pass or documented exceptions exist.

## Documentation

* [ ] README is accurate.
* [ ] Environment setup is documented.
* [ ] Deployment is documented.
* [ ] Security architecture is documented.
* [ ] Threat model exists.
* [ ] Architecture decisions are documented.
* [ ] Testing strategy is documented.
* [ ] API documentation matches implementation.
* [ ] No documentation describes behavior that no longer exists.

---

# 77. FINAL AUDIT OUTPUT

At the end, provide a concise engineering report with:

## A. What was implemented

Exact features completed.

## B. What was fixed

Bugs, security issues, broken flows, missing components.

## C. Security hardening

Concrete controls added.

## D. Tests executed

Include:

* test command
* total tests
* passing tests
* failed tests
* skipped tests
* reason for any skip

## E. Security scans

Report tools/results.

## F. Remaining issues

Only genuine remaining issues.

Do not hide unresolved problems.

## G. Production deployment status

State whether:

* local build succeeds
* production build succeeds
* containers build
* health checks succeed
* database migrations work
* environment configuration is complete

## H. Final architecture

Describe the actual architecture after implementation.

---

# 78. IMPORTANT BEHAVIORAL RULES FOR THIS AGENT

Always prefer:

**secure > convenient**

**correct > fast**

**auditable > opaque**

**least privilege > broad access**

**deterministic refusal > unsupported answer**

**server-side authorization > frontend restrictions**

**verified citation > generated citation**

**approved source > model memory**

**explicit failure > fake success**

**maintainable code > clever code**

Do not fabricate completed work.

Do not say a security property is guaranteed unless you actually tested or enforced it.

Do not mark a task complete because the code "looks correct."

Actually run the appropriate tests.

Actually build the application.

Actually inspect the final state.

---

# 79. FINAL COMMAND

Now take ownership of the repository.

Start by performing the complete repository audit.

Then create the implementation gap analysis.

Then implement all missing functionality and fix all identified defects.

Then perform security hardening.

Then implement and run comprehensive tests.

Then run production builds.

Then verify deployment configuration.

Then perform the final security/tenant-isolation/RAG audit.

Then update documentation.

Do not stop at the first successful build.

Continue until the repository satisfies the Definition of Done above.

If something is already correctly implemented, do not rewrite it unnecessarily.

If something is incomplete, finish it.

If something is insecure, fix it.

If something is mocked, replace it with the real implementation where production requires it.

If something is contradictory, resolve it using the approved requirements and least-privilege principles.

If something is undocumented but necessary for production readiness, implement it and document it.

The final result must be a coherent, tested, secure, maintainable, production-ready implementation of **Grounded Advisory Assistant / WealthGuard AI** — not a prototype, not a demo, and not a partially completed scaffold.
