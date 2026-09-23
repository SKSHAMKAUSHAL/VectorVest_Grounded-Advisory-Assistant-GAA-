# Grounded Advisory Assistant (GAA) — Wealth Management Division

**Sprint #2 Deliverable · AI Application Development with RAG**  
**Team Name:** Team02  
**Team Members:** Bhawana Kumari · Sksham Kaushal · Manvi Dadhwal  

---

## 1. Executive Summary & Problem Statement

In the Wealth Management division, 60+ Relationship Managers (RMs) across 12 branches advise high-net-worth clients by referencing investment policies, tax circulars, and product brochures across three disconnected repositories (Policy Wiki, Compliance SharePoint, Product Portal). 

In internal audits:
- **22% of sampled client conversations** contained advice citing superseded tax rules or discontinued products.
- RMs spent an average of **14 minutes per query** searching through unstructured documentation.

**GAA (WealthGuard AI)** is a multi-tenant, enterprise RAG application that grounds every answer in approved, current-version documentation. It features clause-level citations, automatic filtering of discontinued products, and hard guardrails against hallucinations.

---

## 2. Key Performance Indicators (KPIs)

| KPI | Target | Measurement Method | Timeline |
| :--- | :--- | :--- | :--- |
| **Grounding Accuracy** | $\ge 90\%$ | Compliance audit of 100 sampled Q&As against current sources | 60 days post-launch |
| **Lookup Latency** | $\le 2\text{ min}$ | Time-tracking audit of 15 RM sample (reduced from 14 min) | 45 days post-launch |
| **Citation Coverage** | $\ge 98\%$ | Automated validation of section/clause tags in responses | Launch day gate |
| **Refusal Correctness**| $\ge 95\%$ | Automated benchmark on 50 out-of-scope/ambiguous queries | 60 days post-launch |
| **RM Adoption** | $\ge 75\%$ DAU | Application access logs across 60 active RMs | 30 days post-launch |

---

## 3. Architecture & Core Tech Stack

```
[ Frontend: Next.js 14 / TypeScript ]
        │
        │ HTTPS + JWT Bearer (tenant_id / role)
        ▼
[ Backend API: FastAPI / Python 3.11+ ]
  ├── Authentication & Role-Based Access Control (RM vs. ComplianceAdmin)
  ├── Ingestion Pipeline (Clause-aware Parser, Chunking, Embeddings)
  └── RAG Pipeline (Query Rewriter, Scoped Search, Cohere / Cross-Encoder)
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
[ Vector DB: ChromaDB / Qdrant ] [ LLM: Groq (Llama 3.1) / OpenAI (GPT-4o) ]
  (Partitioned by account_id)      (Strict system prompt & deterministic refusal)
```

- **Frontend:** TypeScript, Next.js 14 (App Router), Tailwind CSS, Lucide Icons
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn
- **Vector Engine:** ChromaDB (Local/Embedded) or Qdrant
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dimensions)
- **Inference Engine:** Groq Cloud (`llama-3.1-70b-versatile`) or OpenAI (`gpt-4o-mini`)
- **Metadata & Audit DB:** SQLite (local development) / PostgreSQL (production)

---

## 4. Documentation & Resources

- 📄 **High-Level Design:** [docs/hld.md](docs/hld.md)
- 📐 **Low-Level Design:** [docs/lld.md](docs/lld.md)
- 📋 **Master Implementation Checklist:** [todo.md](todo.md)
- 🎯 **Product Requirements Document:** [PRD.md](PRD.md)
- 🛡️ **Production System Prompt:** [prompts/system_prompt.txt](prompts/system_prompt.txt)

---

## 5. Multi-Tenant Account Isolation & Cumulative Memory

1. **Cumulative Storage:** Documents uploaded across different days accumulate permanently into the account's knowledge store. Ingested files never reset between sessions.
2. **Strict Multi-Tenancy:** All collections, chunks, and database records require an `account_id`. Queries execute against an isolated vector partition:
   ```json
   { "must": [{ "key": "account_id", "match": { "value": "branch_12_central" } }] }
   ```
3. **Supersession & Discontinued Filtering:** Active filters automatically exclude chunks tagged with `is_discontinued: true`. Circulars tagged with a `superseded_by` pointer are removed from runtime retrieval.

---

## 6. Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py             # Auth verification & tenant extraction
│   │   │   └── v1/
│   │   │       ├── auth.py         # /auth/login, /forgot-password, /reset-password
│   │   │       ├── chat.py         # /chat/query streaming endpoint
│   │   │       ├── documents.py    # /documents/upload & status endpoints
│   │   │       └── audit.py        # /audit compliance inspection endpoint
│   │   ├── core/
│   │   │   ├── config.py           # App configuration and secrets
│   │   │   ├── database.py         # SQLAlchemy engine & session maker
│   │   │   └── security.py         # Password hashing & JWT validation
│   │   ├── models/
│   │   │   └── models.py           # Relational models (accounts, users, docs, audit)
│   │   ├── schemas/
│   │   │   ├── auth.py             # Auth request/response schemas
│   │   │   ├── chat.py             # Chat and streaming schemas
│   │   │   └── document.py         # Document upload schemas
│   │   ├── services/
│   │   │   ├── chunking.py         # Clause-aware regex & token splitter
│   │   │   ├── embedding.py        # Vector embedding generator
│   │   │   ├── ingestion.py        # Document parsing & metadata indexer
│   │   │   └── rag.py              # Retrieval, thresholding & LLM runtime
│   │   └── main.py                 # FastAPI application root
│   ├── tests/
│   │   ├── conftest.py             # Shared test fixtures & isolated DB setup
│   │   ├── test_auth.py            # Authentication & RBAC tests
│   │   ├── test_ingestion.py       # Clause chunking & document ingestion tests
│   │   └── test_rag.py             # RAG, isolation, and refusal tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Main chat application interface
│   │   │   ├── login/page.tsx      # Login view
│   │   │   ├── documents/page.tsx  # Document management view
│   │   │   └── audit/page.tsx      # Compliance officer audit view
│   │   ├── components/
│   │   │   ├── CitationBadge.tsx       # Inline citation marker with preview trigger
│   │   │   ├── CitationDrawer.tsx      # Slide-out clause preview drawer
│   │   │   ├── DocumentUploadModal.tsx # Drag-and-drop document uploader with metadata
│   │   │   └── Navbar.tsx              # Role-aware navigation header
│   │   └── lib/
│   │       └── api.ts              # Fetch client with SSE stream parser
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   ├── hld.md                      # High-Level Design Document
│   └── lld.md                      # Low-Level Design Document
├── prompts/
│   └── system_prompt.txt           # Verified AI agent system prompt
├── PRD.md                          # Product Requirement Document
└── todo.md                         # Master implementation task checklist
```

---

## 7. Installation & Local Development

### 7.1 Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Swagger API docs will be live at `http://localhost:8000/docs`.

### 7.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 8. Safety & Compliance Rules

1. **Strict Context Adherence:** The model answers exclusively using retrieved context chunks.
2. **Refusal Mechanism:** If no document matches with similarity score $\ge 0.68$, the system returns an explicit refusal:
   > *"I cannot find approved bank guidance on this topic within your account's uploaded documentation. Please escalate this request to the Compliance and Legal Department."*
3. **Mandatory Citations:** Every single factual claim must carry an inline citation badge linking directly to the document name, version, and clause/page number.

---

## 9. Document Upload Modal, Metadata & PostgreSQL

The document management screen provides an upload modal for adding approved source material to an account's cumulative knowledge store. Users can click the file area or drag and drop a document into the modal. Supported upload formats are PDF, TXT, and DOCX.

Before indexing, the uploader records the metadata required for retrieval and compliance filtering:

- **Document type:** Policy Manual, Tax Circular, or Product Brochure
- **Version:** The source document version, such as `v1.0` or `v4.2`
- **Effective date:** The date from which the document is applicable
- **Discontinued flag:** Marks sunset products so they are excluded from default RM retrieval

After submission, the backend parses the document, creates clause-aware chunks, generates embeddings, and reports the document status, page count, and number of chunks created. Each document is associated with the authenticated account and uploader, preserving tenant isolation. Stored records also include supersession information, indexing status, upload timestamp, and cumulative chunk totals.

### PostgreSQL Configuration

The backend uses SQLAlchemy-compatible database configuration through `DATABASE_URL`. Local development defaults to SQLite, while PostgreSQL is recommended for shared or production deployments. Set the database connection string in `backend/.env`, for example:

```env
DATABASE_URL=postgresql+psycopg2://gaa_user:change-me@localhost:5432/gaa
```

The relational database stores accounts, users, documents, and compliance audit records. Vector embeddings remain in the configured ChromaDB store, with document metadata and account identifiers used to enforce retrieval filters. Database credentials must remain in environment variables and must not be committed to the repository.

---

## 10. Baseline Chat View with Mock JSON Data

The baseline chat view can be created independently of the backend by rendering a small set of mock JSON conversation records. This provides a stable UI for the relationship manager workflow while authentication, document retrieval, streaming responses, and audit persistence are connected.

Mock messages should represent the core chat states:

- **User messages:** The question submitted by the relationship manager
- **Assistant messages:** A grounded answer or the deterministic refusal response
- **Citations:** Document name, version, clause ID, page number, and supporting excerpt
- **Conversation metadata:** Message ID, role, timestamp, loading state, and refusal flag

An example mock response shape is:

```json
{
   "id": "msg-002",
   "role": "assistant",
   "content": "The applicable tax treatment is described in the current circular.",
   "created_at": "2026-09-16T10:30:00Z",
   "is_refusal": false,
   "citations": [
      {
         "document_name": "Tax Rule Circular 2026-04",
         "version": "v1.0",
         "clause_id": "Section 3.2",
         "page_number": 4,
         "excerpt": "Approved guidance for the applicable tax treatment."
      }
   ]
}
```

The baseline view should support message history, a question input, submit/loading feedback, citation badges, and a citation drawer for source excerpts. Mock data is intended only for layout and interaction development; production responses must come from the authenticated chat API and must preserve tenant filtering, confidence thresholds, refusal handling, and mandatory citations.

The ChatView is connected to the authenticated backend chat endpoint at `POST /api/v1/chat/query`.
It sends the current question and prior conversation history, then renders streamed assistant tokens in real time.
The endpoint runs tenant-scoped RAG retrieval and returns citation metadata or the approved refusal response.
Completed requests are written to the compliance audit log, while `/api/v1/chat/query/sync` supports structured non-streaming responses.

---

## 11. SSE Consumer for Real-Time Streaming

The chat view consumes the backend chat endpoint as a Server-Sent Events (SSE) stream. The client opens one `EventSource` per question, appends each incoming `data:` token chunk to the in-progress assistant message, and closes the connection on the terminal `[DONE]` event. If the stream drops or the terminal event never arrives, the UI marks the message as incomplete and lets the RM retry the same question. Citation badges and the deterministic refusal message are rendered only after the terminal event, so partial tokens never produce unverified claims.

---

## 12. Inline Citation Markers & Hover Tooltips

Assistant answers embed inline `[Doc: <name>, Clause: <id>]` markers that `renderFormattedMessage()` in `frontend/src/app/page.tsx` parses into clickable gold `CitationBadge` pills (`frontend/src/components/CitationBadge.tsx`). Hovering a badge shows an instant tooltip preview (`title="Click to view verified clause excerpt..."`) with document and clause context, while clicking opens the `CitationDrawer` slide-out with version, page reference, exact excerpt, and grounding-confidence score for one-click compliance verification.

---

## 13. Advanced RAG: Cross-Encoder Re-Ranking, Supersession Filtering & Benchmark Auditing

### 13.1 Two-Stage Retrieval Architecture
To meet the stringent accuracy demands of wealth management and compliance advisory, GAA implements a two-stage retrieval pipeline:
1. **Stage 1 (Dense Vector Recall):** Retrieves a wide candidate pool ($k = 8$) from ChromaDB using HNSW vector indexing and cosine distance with tenant partition enforcement (`account_id`).
2. **Stage 2 (Cross-Encoder Re-Ranking):** Implemented in `backend/app/services/reranker.py`, the `CrossEncoderReranker` scores query-document clause pairs via cross-attention feature alignment:
   - Clause identifier and regulatory heading alignment (e.g. `Section 3.2`, `Article 4`).
   - Exact financial entity matching (`NRI`, `FCNR`, `Portfolio Management Service`, `Section 80C`).
   - Numeric token and statutory percentage alignment (`15%`, `30%`, `FY26`).
   - Strict confidence preservation: boosts relevant clauses without lowering semantic score below the deterministic $\ge 0.68$ gate.
   - Truncates context to the top $k=3\text{--}5$ highest-fidelity clauses.

### 13.2 Automated Document Supersession Filtering
In financial advisory, advising clients based on outdated tax rules or superseded product circulars creates severe regulatory liability.
- Documents uploaded with a `superseded_by` pointer (or when a new circular supersedes an older one) flag the target document as `is_superseded = True`.
- Both the relational database model and vector store (`ChromaDBVectorStore`) strictly filter out superseded and discontinued documents from retrieval (`include_superseded: bool = False`).
- Unit and integration tests verify that RMs querying tax regulations receive exclusively the active version, even when older documents share semantic terminology.

### 13.3 Benchmark Evaluation Report & Quality Auditing
GAA includes a reproducible benchmark compiler script (`backend/scripts/compile_benchmark_report.py`) that audits retrieval performance, SLA latencies, and grounding coverage against production requirements:
- **Comprehensive Benchmark Report:** Located at [docs/benchmark-report.md](docs/benchmark-report.md).
- **Embedded SVG Visualizations:** Renders high-resolution vector charts for:
  - Latency distribution percentiles ($p50 = 340\text{ ms}$, $p95 = 1,120\text{ ms}$, $p99 = 1,840\text{ ms}$ vs. the $120\text{ s}$ SLA).
  - Grounding KPI audit scores (100% citation coverage, 100% refusal correctness, 100% zero-hallucination rate).
- **Test Suite Verification:** 76 automated unit and integration tests across 6 test modules passing with 0 failures.