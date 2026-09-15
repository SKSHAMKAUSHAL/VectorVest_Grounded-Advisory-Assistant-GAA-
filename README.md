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
│   │   ├── test_auth.py            # Authentication & RBAC tests
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
│   │   │   ├── ChatInterface.tsx   # Real-time token streaming chat
│   │   │   ├── CitationDrawer.tsx  # Slide-out clause preview drawer
│   │   │   └── DocumentUpload.tsx  # Multi-file batch uploader
│   │   └── lib/
│   │       └── api.ts              # Fetch client with SSE parser
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