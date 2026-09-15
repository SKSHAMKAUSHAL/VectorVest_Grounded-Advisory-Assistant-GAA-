# High-Level Design (HLD) — Grounded Advisory Assistant (GAA)
**Document ID:** GAA-HLD-001  
**Project:** Grounded Advisory Assistant (Wealth Management Division)  
**Authors:** Team02 (Bhawana Kumari · Sksham Kaushal · Manvi Dadhwal)  
**Version:** 1.0 (Approved)  

---

## 1. Executive Summary & Business Context

In the Wealth Management division, 60+ Relationship Managers (RMs) across 12 branches advise high-net-worth clients by referencing investment policies, tax circulars, and product brochures across three disconnected repositories (Policy Wiki, Compliance SharePoint, Product Portal). 

In internal audits:
- **22% of sampled client conversations** contained advice citing superseded tax rules or discontinued products.
- RMs spend an average of **14 minutes per query** searching through unstructured documentation.

**GAA (WealthGuard AI)** is a multi-tenant, enterprise Retrieval-Augmented Generation (RAG) platform that eliminates misstatements by strictly grounding RM responses in approved bank documentation with clause-level citations, automatic exclusion of discontinued products, and hard guardrails against hallucinations.

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

## 3. System Stakeholders & User Roles

```
┌─────────────────────────┐          ┌─────────────────────────┐
│  Relationship Manager   │          │   Compliance Officer    │
│          (RM)           │          │       (Auditor)         │
└────────────┬────────────┘          └────────────┬────────────┘
             │                                    │
    Queries & Live Chat                  Audits Logs & Traces
             │                                    │
             ▼                                    ▼
┌───────────────────────────────────────────────────────────────┐
│          Grounded Advisory Assistant (GAA) Platform           │
└──────────────────────────────┬────────────────────────────────┘
                               ▲
                               │ Uploads & Flags Discontinued Docs
                               │
                    ┌──────────┴──────────┐
                    │  Data Owner / Admin │
                    │ (Compliance/Mktg)   │
                    └─────────────────────┘
```

1. **Relationship Manager (RM):** Queries the assistant before or during client conversations; views stream-generated, clause-grounded guidance with inline citation badges and source preview drawer.
2. **Compliance Officer / Auditor:** Reviews detailed audit trail logs, inspects retrieved source chunks, similarity scores, refusal flags, and validates grounding.
3. **Data Owner / Administrator:** Manages document inventory across branches/accounts, uploads new PDFs/circulars, defines effective dates, and triggers supersession/discontinuation flags.

---

## 4. End-to-End System Architecture

```
                                 USER INTERFACE LAYER
        ┌──────────────────────────────────────────────────────────────────┐
        │            Next.js 14 / TypeScript (Tailwind CSS, Lucide)         │
        │  • Auth Views (Login, Forgot Password, Reset Password)           │
        │  • Token-Streaming Chat Interface with Citation Drawer           │
        │  • Document Upload Modal & Management View                       │
        │  • Compliance Audit Log & Trace Inspection Dashboard             │
        └─────────────────────────────────┬────────────────────────────────┘
                                          │
                                          │ HTTPS / REST / SSE / JWT
                                          ▼
                                 API GATEWAY / BACKEND
        ┌──────────────────────────────────────────────────────────────────┐
        │                 FastAPI (Python 3.11, Pydantic v2)               │
        │  • Authentication & RBAC (RM vs ComplianceAdmin via JWT)         │
        │  • Tenant Isolation Middleware (account_id extraction)           │
        │  • Rate Limiting & Input Validation                              │
        └──────────────┬───────────────────────────────────┬───────────────┘
                       │                                   │
      INGESTION PATH   │                                   │   RUNTIME QUERY PATH
                       ▼                                   ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────────────┐
│ Ingestion & Processing Pipeline       │ │ RAG Orchestration Engine              │
│ • PDF/DOCX Parsing (pypdf/pdfplumber) │ │ • Conversational Query Rewriter       │
│ • Cleaning (Headers/Footers stripped) │ │ • Scoped Hybrid Vector Retrieval      │
│ • Clause-Boundary Chunking (Regex)    │ │ • Re-ranking (Cross-Encoder/Cohere)   │
│ • Metadata Tagging (Tenant, Ver, Date)│ │ • Confidence Gate (Threshold >= 0.68) │
│ • Vector Generation & Indexing        │ │ • LLM Streaming (Groq / OpenAI)      │
└──────────────────┬────────────────────┘ └──────────────────┬────────────────────┘
                   │                                         │
                   ▼                                         ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────────────┐
│ Vector Database Tier                  │ │ LLM Inference Provider Tier           │
│ • Qdrant / ChromaDB                   │ │ • Groq Cloud (Llama 3.1 70B Versatile)│
│ • Partitioned by account_id           │ │ • OpenAI API (GPT-4o-mini / GPT-4o)   │
│ • Payload: doc_name, ver, clause, date│ │ • Zero-Hallucination System Prompt    │
└──────────────────┬────────────────────┘ └──────────────────┬────────────────────┘
                   │                                         │
                   └───────────────────┬─────────────────────┘
                                       ▼
                          RELATIONAL & AUDIT STORAGE
        ┌──────────────────────────────────────────────────────────────────┐
        │                    PostgreSQL / SQLite Database                  │
        │  • Accounts (Branches/Tenants)       • Document Inventory        │
        │  • Users & Passwords (bcrypt)        • Compliance Audit Logs     │
        │  • Password Reset Tokens             • Supersession Mapping      │
        └──────────────────────────────────────────────────────────────────┘
```

---

## 5. Subsystem Workflows

### 5.1 Authentication & Multi-Tenant Access Workflow
1. User logs in with `email` and `password` via `/api/v1/auth/login`.
2. Password verification executed using `passlib[bcrypt]`.
3. Backend issues a signed JWT containing `sub` (user_id), `account_id`, and `role` (`RM` or `ComplianceAdmin`).
4. Forgot password flow generates secure, time-expiring reset tokens sent to the user email or reset endpoint (`/api/v1/auth/reset-password`).
5. Every incoming API request validates token claims and injects `account_id` into repository queries to guarantee complete cross-tenant data isolation.

### 5.2 Document Ingestion & Cumulative Memory Workflow
1. **Upload:** User/Admin uploads PDF documents specifying `doc_type` (policy manual, tax circular, product brochure), `version`, `effective_date`, and `is_discontinued`.
2. **Text Parsing:** Extract raw text and layout using `pypdf` or `pdfplumber`. Remove noise (page headers, footers, repetitive confidentiality notices).
3. **Clause-Aware Segmentation:** Apply regex rules matching clause markers (`Section`, `Clause`, `Article`, `X.Y`) to preserve regulatory coherence.
4. **Metadata Attachment:** Every chunk is stamped with `account_id`, `document_id`, `document_name`, `version`, `clause_id`, `page_number`, `is_discontinued`, and `effective_date`.
5. **Cumulative Upsert:** Generate vector embeddings via OpenAI `text-embedding-3-small` (1536-dim) and upsert into the vector store. Prior documents are never overwritten; storage accumulates cumulatively over days and weeks.

### 5.3 Grounded Query & Retrieval Guardrail Workflow
1. **Multi-Turn Context Rewriting:** Follow-up questions (e.g., "What about for NRIs?") are rewritten into standalone search queries using conversation history.
2. **Filtered Dense Search:** Query vector index with mandatory filter:
   `account_id == current_account AND is_discontinued == false`.
3. **Re-ranking:** Top 15–20 candidates are re-scored using a cross-encoder to rank the most relevant clauses.
4. **Confidence Guardrail Gate:**
   - If highest similarity score $< 0.68$, **bypass LLM** and return deterministic refusal:
     > *"I cannot find approved bank guidance on this topic within your account's uploaded documentation. Please escalate this request to the Compliance and Legal Department."*
5. **Grounded Generation:** If confidence passes, format context chunks with strict clause markers and execute token-streamed response via SSE.
6. **Audit Trail Logging:** Store query, rewritten query, retrieved chunk IDs, similarity score, refusal status, latency, and full answer in the database.

---

## 6. Security, Compliance & Governance

1. **Logical Multi-Tenancy:** Hard partition by `account_id`. No query or vector search can ever span across accounts.
2. **Role-Based Access Control (RBAC):**
   - `RM`: Query assistant, view citation excerpts, view personal query history.
   - `ComplianceAdmin`: Upload/manage documents, manage supersessions, inspect complete audit logs across all RMs.
3. **Zero-Hallucination System Prompt:** Directives explicitly forbid external assumptions, training-data extrapolation, and ungrounded statements.
4. **Data Protection:** Data encrypted in transit (TLS 1.3) and at rest (AES-256 for vector/relational databases).
