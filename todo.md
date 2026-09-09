# Grounded Advisory Assistant (GAA) — Master Implementation Plan

This checklist outlines the complete roadmap to build, test, and deploy the Grounded Advisory Assistant (WealthGuard AI) platform as specified in [PRD.md](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/PRD.md), [README.md](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/README.md), [docs/hld.md](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/docs/hld.md), and [docs/lld.md](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/docs/lld.md).

---

## Phase 1: Project Setup, Environment & Architecture Foundations
- [ ] **1.1 Directory Structure & Workspace Scaffolding**
  - Set up `backend/`, `frontend/`, and `prompts/` directories matching the architecture specification.
  - Initialize root `.gitignore` to protect virtual environments, node modules, `.env` secrets, and database files.
- [ ] **1.2 Backend Environment & Core Dependencies**
  - Create `backend/requirements.txt` with FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, ChromaDB/Qdrant-client, PyPDF, PDFPlumber, OpenAI, Groq, Passlib, python-jose, and python-multipart.
  - Set up `.env.example` with configuration variables: `DATABASE_URL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `SIMILARITY_THRESHOLD`, `JWT_SECRET`, `LLM_PROVIDER`.
- [ ] **1.3 Production System Prompt Setup**
  - Create `prompts/system_prompt.txt` with zero-hallucination directives, clause-citation requirements, and deterministic refusal rules.

---

## Phase 2: Database Models, Multi-Tenancy & Authentication Engine
- [ ] **2.1 Relational Database Engine & Migration Setup**
  - Implement SQLite/PostgreSQL connection in `backend/app/core/database.py`.
  - Create SQLAlchemy models in `backend/app/models/`:
    - `Account` (Multi-tenant branch entity: `id`, `branch_name`, `branch_code`).
    - `User` (`id`, `account_id`, `email`, `password_hash`, `role` [RM, ComplianceAdmin]).
    - `PasswordResetToken` (`id`, `user_id`, `token_hash`, `expires_at`, `used`).
    - `Document` (`id`, `account_id`, `filename`, `doc_type`, `version`, `effective_date`, `is_discontinued`, `status`).
    - `ComplianceAuditLog` (`id`, `account_id`, `user_id`, `query`, `rewritten_query`, `similarity_score`, `response`, `is_refusal`, `latency_ms`).
- [ ] **2.2 Authentication & Password Management Services**
  - Implement password hashing and verification using `passlib[bcrypt]` in `backend/app/core/security.py`.
  - Implement JWT issuance and token validation (with claims: `sub`, `account_id`, `role`).
  - Implement forgot password token generation and password reset verification logic.
- [ ] **2.3 Auth REST API Endpoints**
  - Implement `POST /api/v1/auth/login` (email/password validation, token issuance).
  - Implement `POST /api/v1/auth/forgot-password` (token generation).
  - Implement `POST /api/v1/auth/reset-password` (token verification and password update).
  - Implement `GET /api/v1/auth/me` (current authenticated profile).
- [ ] **2.4 FastAPI Dependencies & Tenant Isolation Middleware**
  - Implement `get_current_user` and `require_role(role)` in `backend/app/api/deps.py`.
  - Enforce mandatory tenant filtering using extracted `account_id`.

---

## Phase 3: Document Ingestion, PDF Processing & Vector Indexing Pipeline
- [ ] **3.1 Document Text Extraction & Cleaning Engine**
  - Implement parser in `backend/app/services/ingestion.py` using `pypdf` and `pdfplumber`.
  - Strip redundant running headers, footers, page numbering, and whitespace artifacts.
- [ ] **3.2 Clause-Boundary Chunking Algorithm**
  - Implement `chunk_document_by_clause` in `backend/app/services/chunking.py`.
  - Split documents on regulatory section headers (`Section`, `Clause`, `Article`, decimal numbering `X.Y`).
  - Implement recursive token splitting fallback (500 tokens max, 50 token overlap) for long clauses.
- [ ] **3.3 Embedding Service & Vector Database Client**
  - Implement vector embedding generator in `backend/app/services/embedding.py` using OpenAI `text-embedding-3-small` (1536 dimensions).
  - Configure vector database client (`ChromaDB` / `Qdrant`) with HNSW index and metadata filtering.
- [ ] **3.4 Cumulative Upload API Endpoint**
  - Implement `POST /api/v1/documents/upload` accepting multipart file, `doc_type`, `version`, `effective_date`, and `is_discontinued`.
  - Persist document record, chunk text, embed vectors, and store payloads with `account_id` partitioning.
  - Implement `GET /api/v1/documents` to list indexed files, versions, and chunk counts per account.

---

## Phase 4: Conversational RAG, Query Rewriting & Grounding Guardrails
- [ ] **4.1 Multi-Turn Conversational Query Reformulator**
  - Implement query rewriter in `backend/app/services/rag.py` using `REWRITE_SYSTEM_PROMPT`.
  - Transform contextual follow-up questions (e.g., "What about for NRIs?") into standalone search queries.
- [ ] **4.2 Scoped Vector Retrieval & Re-ranking**
  - Implement dense vector search with hard filters: `account_id == current_account AND is_discontinued == false`.
  - Implement supersession check: filter out documents superseded by newer versions.
  - Apply top-candidate re-ranking to isolate the most relevant 3–5 context clauses.
- [ ] **4.3 Zero-Hallucination Confidence Guardrail Gate**
  - Check maximum similarity score against the threshold ($0.68$).
  - If score $< 0.68$, halt generation and immediately return deterministic compliance refusal:
    > *"I cannot find approved bank guidance on this topic within your account's uploaded documentation. Please escalate this request to the Compliance and Legal Department."*
- [ ] **4.4 Grounded Generation & SSE Token Streaming Endpoint**
  - Implement `POST /api/v1/chat/query` returning `text/event-stream` (Server-Sent Events).
  - Stream tokens generated by Groq (`llama-3.1-70b-versatile`) or OpenAI (`gpt-4o-mini`).
  - Emit parsed `citations` event containing `document_name`, `version`, `clause_id`, `page_number`, and `excerpt`.
- [ ] **4.5 Compliance Audit Logging**
  - Write every interaction to `compliance_audit_logs` (query, rewritten query, chunk IDs, score, response, refusal flag, latency).
  - Implement `GET /api/v1/audit/logs` restricted to `ComplianceAdmin` role.

---

## Phase 5: Next.js Frontend Application
- [ ] **5.1 Project Initialization & Design System**
  - Initialize Next.js 14 App Router project with TypeScript and Tailwind CSS.
  - Configure modern dark/light banking theme, typography, and Lucide icons.
- [ ] **5.2 Authentication & Route Guards**
  - Implement Login screen (`/login`) with email/password validation.
  - Implement Forgot Password (`/forgot-password`) and Reset Password (`/reset-password`) screens.
  - Implement JWT storage, session hydration, and route protection for `RM` vs `ComplianceAdmin`.
- [ ] **5.3 Relationship Manager Streaming Chat Interface**
  - Build responsive chat view (`/`) with auto-scrolling message list.
  - Implement SSE stream consumer displaying real-time word-by-word generation.
  - Implement interactive clickable `CitationBadge` tags inside assistant responses.
  - Build slide-out `CitationDrawer` displaying the underlying document name, version, clause, and exact text excerpt.
- [ ] **5.4 Document Management & Upload Drawer**
  - Build `/documents` interface allowing users/admins to view cumulative document stores.
  - Implement drag-and-drop PDF/DOCX upload modal with inputs for `doc_type`, `version`, `effective_date`, and `is_discontinued`.
  - Provide real-time upload and indexing status feedback.
- [ ] **5.5 Compliance Officer Audit Dashboard**
  - Build `/audit` interface restricted to `ComplianceAdmin`.
  - Implement searchable, filterable table displaying queries, timestamps, RM names, similarity scores, refusal indicators, and retrieved chunks.

---

## Phase 6: Automated Verification, Quality Benchmarks & Documentation
- [ ] **6.1 Unit & Integration Test Suite**
  - Implement `tests/test_auth.py` (login, password reset, unauthorized access checks).
  - Implement `tests/test_account_isolation.py` (verify Tenant A cannot retrieve Tenant B vectors).
  - Implement `tests/test_hard_refusal.py` (verify confidence $< 0.68$ triggers exact refusal).
  - Implement `tests/test_discontinued_product.py` (verify discontinued products are excluded from responses).
  - Implement `tests/test_cumulative_retrieval.py` (verify documents uploaded on different days accumulate in retrieval).
- [ ] **6.2 End-to-End Validation & Audit Readiness**
  - Validate citation coverage ($\ge 98\%$).
  - Measure response lookup latency ($\le 2\text{ min}$).
  - Verify complete consistency across PRD, HLD, LLD, and codebase.
