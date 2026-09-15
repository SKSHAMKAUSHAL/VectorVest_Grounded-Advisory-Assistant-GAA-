# Low-Level Design (LLD) — Grounded Advisory Assistant (GAA)
**Document ID:** GAA-LLD-001  
**Project:** Grounded Advisory Assistant (Wealth Management Division)  
**Authors:** Team02 (Bhawana Kumari · Sksham Kaushal · Manvi Dadhwal)  
**Version:** 1.0 (Approved)  

---

## 1. Relational Database Schema & Data Models

PostgreSQL / SQLite implementation models for authentication, multi-tenancy, document lifecycle, and compliance audit logs.

```sql
-- 1. Tenant Accounts (Branches or Business Units)
CREATE TABLE accounts (
    id VARCHAR(64) PRIMARY KEY,
    branch_name VARCHAR(128) NOT NULL,
    branch_code VARCHAR(32) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. System Users (Relationship Managers & Compliance Officers)
CREATE TABLE users (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (role IN ('RM', 'ComplianceAdmin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Document Registry
CREATE TABLE documents (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    uploaded_by VARCHAR(64) NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    doc_type VARCHAR(64) NOT NULL CHECK (doc_type IN ('policy_manual', 'tax_circular', 'product_brochure')),
    effective_date DATE NOT NULL,
    superseded_by VARCHAR(64) NULL REFERENCES documents(id),
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,
    total_pages INTEGER NOT NULL DEFAULT 0,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'INDEXED' CHECK (status IN ('PENDING', 'PROCESSING', 'INDEXED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Compliance Audit Logs
CREATE TABLE compliance_audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    rewritten_query TEXT,
    retrieved_chunk_ids JSONB NOT NULL,
    similarity_score FLOAT NOT NULL,
    response TEXT NOT NULL,
    is_refusal BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Scoped Lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_documents_account ON documents(account_id, is_discontinued);
CREATE INDEX idx_audit_logs_account ON compliance_audit_logs(account_id, created_at DESC);
```

---

## 2. Vector Database Payload Schema

Payload configuration for **Qdrant** / **ChromaDB**:

```json
{
  "id": "chunk_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "vector": [0.0124, -0.0431, 0.0821, "... 1536 dimensions (text-embedding-3-small) ..."],
  "payload": {
    "account_id": "branch_12_central",
    "document_id": "doc_tax_circ_2024_02",
    "document_name": "Tax_Rule_Circular_02_2024.pdf",
    "document_version": "v2.1",
    "doc_type": "tax_circular",
    "clause_id": "Section 4.2.1",
    "page_number": 6,
    "chunk_index": 14,
    "chunk_text": "Capital Gains Exemption: Under amended schedule 4, long-term capital gains on High-Yield Debt Funds shall be taxed at 10% without indexation for domestic resident individual accounts.",
    "is_discontinued": false,
    "effective_date": "2024-01-01"
  }
}
```

---

## 3. Ingestion & Document Processing Engine

### 3.1 Clause-Boundary Parsing & Chunking
Standard splitters break clauses mid-sentence, cutting off exceptions or penalties. The clause-aware parser splits text along identifiable legal headers:

```python
import re
from typing import List, Dict, Any

CLAUSE_PATTERN = r"(?=(\n(?:Section|Clause|Article|\b[0-9]{1,2}\.[0-9]{1,2})\b))"

def chunk_document_by_clause(
    text: str, 
    page_number: int,
    max_tokens: int = 500, 
    overlap_tokens: int = 50
) -> List[Dict[str, Any]]:
    sections = re.split(CLAUSE_PATTERN, text)
    chunks = []
    current_clause_id = f"Page {page_number}"
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        header_match = re.match(r"^((?:Section|Clause|Article|\b[0-9]{1,2}\.[0-9]{1,2})\b[^\n]*)", section)
        if header_match:
            current_clause_id = header_match.group(1).strip()
            
        words = section.split()
        if len(words) <= max_tokens:
            chunks.append({
                "clause_id": current_clause_id,
                "text": section,
                "page_number": page_number
            })
        else:
            for i in range(0, len(words), max_tokens - overlap_tokens):
                sub_text = " ".join(words[i:i + max_tokens])
                chunks.append({
                    "clause_id": current_clause_id,
                    "text": sub_text,
                    "page_number": page_number
                })
                
    return chunks
```

---

## 4. Query Rewriting & RAG Guardrail Pipeline

```python
import os
from typing import List, Dict, Any, Optional

REWRITE_SYSTEM_PROMPT = """
You are a search query reformulator.
Given the conversation history and a follow-up question, rewrite the follow-up question into an independent, fully qualified search query.
Do NOT answer the question. Only output the rewritten search string.

Conversation History:
{chat_history}

Follow-up Question: {query}

Rewritten Query:"""

class RAGPipeline:
    def __init__(self, vector_db_client, embedding_client, llm_client, threshold: float = 0.68):
        self.vdb = vector_db_client
        self.embed = embedding_client
        self.llm = llm_client
        self.threshold = threshold

    async def rewrite_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        if not chat_history:
            return query
        prompt = REWRITE_SYSTEM_PROMPT.format(
            chat_history="\n".join([f"{m['role']}: {m['content']}" for m in chat_history]),
            query=query
        )
        return await self.llm.generate(prompt)

    async def retrieve_and_generate(self, query: str, account_id: str, chat_history: List[Dict[str, str]]):
        search_query = await self.rewrite_query(query, chat_history)
        query_vec = await self.embed.get_embedding(search_query)
        
        search_filter = {
            "must": [
                {"key": "account_id", "match": {"value": account_id}},
                {"key": "is_discontinued", "match": {"value": False}}
            ]
        }
        
        candidates = await self.vdb.search(vector=query_vec, filter=search_filter, limit=10)
        
        # Guardrail Confidence Check
        if not candidates or candidates[0].score < self.threshold:
            return {
                "decision": "REFUSAL",
                "message": (
                    "I cannot find approved bank guidance on this topic within your "
                    "account's uploaded documentation. Please escalate this request "
                    "to the Compliance and Legal Department."
                ),
                "citations": [],
                "top_score": candidates[0].score if candidates else 0.0,
                "rewritten_query": search_query
            }
            
        return {
            "decision": "GENERATE",
            "chunks": candidates[:5],
            "top_score": candidates[0].score,
            "rewritten_query": search_query
        }
```

---

## 5. REST & Streaming API Specifications

### 5.1 Authentication Endpoints
- **POST `/api/v1/auth/login`**
  - **Body:** `{"email": "rm@wealth.bank.com", "password": "SecurePassword123!"}`
  - **Response (200 OK):** `{"access_token": "jwt_token...", "token_type": "bearer", "user": {"id": "usr_123", "role": "RM", "account_id": "acc_01"}}`
- **POST `/api/v1/auth/forgot-password`**
  - **Body:** `{"email": "rm@wealth.bank.com"}`
  - **Response (200 OK):** `{"message": "Password reset instructions sent."}`
- **POST `/api/v1/auth/reset-password`**
  - **Body:** `{"token": "reset_token_xyz", "new_password": "NewSecurePassword456!"}`
  - **Response (200 OK):** `{"message": "Password reset successfully."}`

### 5.2 Document Endpoints
- **POST `/api/v1/documents/upload`** (Multipart Form)
  - `file`: PDF / DOCX binary
  - `doc_type`: `policy_manual` | `tax_circular` | `product_brochure`
  - `version`: string (e.g. `v4.2`)
  - `effective_date`: date string (`YYYY-MM-DD`)
  - `is_discontinued`: boolean (default `false`)
  - **Response (201 Created):**
    ```json
    {
      "document_id": "doc_90b24bf4-74c1",
      "filename": "Tax_Rule_Circular_02_2024.pdf",
      "status": "INDEXED",
      "chunks_created": 42,
      "account_id": "branch_ny_01"
    }
    ```
- **GET `/api/v1/documents`**
  - Query params: `doc_type`, `is_discontinued`
  - Returns list of indexed files, chunk counts, versions, and upload timestamps for the current account.

### 5.3 Chat & Streaming RAG Endpoint
- **POST `/api/v1/chat/query`**
  - **Headers:** `Authorization: Bearer <JWT>`
  - **Body:**
    ```json
    {
      "query": "What is the capital gains tax offset for municipal bonds under 2024 rules?",
      "chat_history": [
        {"role": "user", "content": "Hello, I need tax rules guidance."},
        {"role": "assistant", "content": "I am ready to assist with approved policies."}
      ]
    }
    ```
  - **Streaming SSE Format (`text/event-stream`):**
    ```text
    event: token
    data: {"token": "The"}

    event: token
    data: {"token": " capital"}

    event: citations
    data: [{"document_name": "Tax_Rule_Circular_02_2024.pdf", "version": "v2.1", "clause_id": "Section 4.2.1", "page_number": 6, "excerpt": "Under amended schedule 4..."}]

    event: done
    data: [DONE]
    ```

### 5.4 Compliance Audit Endpoint
- **GET `/api/v1/audit/logs?limit=50&offset=0`**
  - **Headers:** `Authorization: Bearer <JWT>` (Restricted to `ComplianceAdmin`)
  - Returns paginated list of audit events: timestamp, user email, query, rewritten query, chunk IDs, similarity score, refusal status, and generated answer.

---

## 6. Frontend Component Architecture

```
frontend/src/
├── app/
│   ├── layout.tsx                # App shell, Navbar, AuthProvider
│   ├── page.tsx                  # RM Chat Interface
│   ├── login/page.tsx            # Login form
│   ├── forgot-password/page.tsx  # Request password reset form
│   ├── reset-password/page.tsx   # Set new password form
│   ├── documents/page.tsx        # Document Library & Uploader
│   └── audit/page.tsx            # Compliance Officer Audit Dashboard
├── components/
│   ├── ChatInterface.tsx         # Token streaming conversation view
│   ├── CitationDrawer.tsx        # Slide-out modal showing exact clause context
│   ├── CitationBadge.tsx         # Interactive pill tag linking to drawer
│   ├── DocumentUploadModal.tsx   # Drag-and-drop PDF uploader with metadata
│   └── AuditTable.tsx            # Searchable and filterable audit logs
└── lib/
    ├── api.ts                    # Backend API client with fetch & SSE handling
    └── auth.ts                   # Token storage & auth state helper
```
