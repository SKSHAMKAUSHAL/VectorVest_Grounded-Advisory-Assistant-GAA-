# Grounded Advisory Assistant (GAA) — Developer Guide

## 1. Overview

The Grounded Advisory Assistant (GAA) is an application designed to provide responses grounded in a collection of uploaded documents.

The project is divided into two main parts:

* **Frontend** — Next.js application responsible for the user interface.
* **Backend** — Python application responsible for APIs, authentication, document processing, RAG, and data management.

The repository also contains project documentation, prompts, tests, and configuration files.

---

## 2. Repository Structure

```text
GAA/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── audit.py
│   │   │       ├── auth.py
│   │   │       ├── chat.py
│   │   │       └── documents.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── document.py
│   │   │
│   │   ├── services/
│   │   │   ├── chunking.py
│   │   │   ├── embedding.py
│   │   │   ├── ingestion.py
│   │   │   ├── llm.py
│   │   │   ├── rag.py
│   │   │   └── vector_store.py
│   │   │
│   │   ├── main.py
│   │   └── seed.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── start.ps1
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── audit/
│   │   │   ├── documents/
│   │   │   ├── forgot-password/
│   │   │   ├── login/
│   │   │   ├── reset-password/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   │
│   │   └── components/
│   │       ├── CitationBadge.tsx
│   │       ├── CitationDrawer.tsx
│   │       ├── DocumentUploadModal.tsx
│   │       └── Navbar.tsx
│   │
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── .env.local.example
│
├── docs/
│   ├── hld.md
│   ├── lld.md
│   └── developer-guide.md
│
├── prompts/
│   └── system_prompt.txt
│
├── PRD.md
├── README.md
└── todo.md
```

---

## 3. Frontend

The frontend is implemented using **Next.js**.

The main application code is located inside:

```text
frontend/src/
```

### App Routes

The `app` directory follows the Next.js App Router structure.

Important routes include:

| Route              | Purpose                     |
| ------------------ | --------------------------- |
| `/`                | Main application page       |
| `/login`           | User authentication         |
| `/forgot-password` | Password recovery           |
| `/reset-password`  | Password reset              |
| `/documents`       | Document management         |
| `/audit`           | Audit-related functionality |

### Components

Reusable UI components are located in:

```text
frontend/src/components/
```

Examples include:

* `Navbar.tsx` — application navigation
* `DocumentUploadModal.tsx` — document upload interface
* `CitationBadge.tsx` — displays citation information
* `CitationDrawer.tsx` — displays detailed citation information

Keeping reusable components separate from route-specific pages makes the frontend easier to maintain.

---

## 4. Backend

The backend contains the API and core application logic.

The main backend package is:

```text
backend/app/
```

The backend is organized into several layers.

### API Layer

```text
backend/app/api/
```

The versioned API endpoints are located under:

```text
backend/app/api/v1/
```

Important modules include:

* `auth.py` — authentication-related endpoints
* `chat.py` — chat-related endpoints
* `documents.py` — document-related endpoints
* `audit.py` — audit functionality

`deps.py` contains shared API dependencies used by the application.

---

## 5. Core Layer

The core configuration is located in:

```text
backend/app/core/
```

### `config.py`

Responsible for application configuration and environment-based settings.

### `database.py`

Contains database-related configuration and connections.

### `security.py`

Contains security and authentication-related functionality.

Keeping configuration, database setup, and security logic in a dedicated core layer prevents these concerns from being mixed with API and business logic.

---

## 6. Models and Schemas

### Models

Database models are located in:

```text
backend/app/models/
```

The primary model definitions are contained in:

```text
backend/app/models/models.py
```

Models describe how application data is represented for persistence.

### Schemas

Request and response schemas are located in:

```text
backend/app/schemas/
```

Current schema modules include:

* `auth.py`
* `chat.py`
* `document.py`

Schemas provide a structured way to validate and represent API data.

---

## 7. RAG Pipeline

One of the main parts of the project is the Retrieval-Augmented Generation (RAG) workflow.

The relevant services are located in:

```text
backend/app/services/
```

The general flow is:

```text
Document
   ↓
Ingestion
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Store
   ↓
Relevant Context Retrieval
   ↓
LLM
   ↓
Grounded Response
   ↓
Citations
```

### Document Ingestion

`ingestion.py` handles the document processing workflow.

A document is processed before it can be used as a knowledge source.

### Chunking

`chunking.py` is responsible for breaking larger document content into smaller pieces.

Chunking makes it possible to retrieve relevant portions of a document instead of processing the entire document for every query.

### Embeddings

`embedding.py` handles the creation of vector representations of document content.

These representations allow semantically similar content to be identified during retrieval.

### Vector Store

`vector_store.py` handles storage and retrieval of vectorized document information.

### RAG Service

`rag.py` coordinates the retrieval process.

The service retrieves relevant document context that can be supplied to the language model.

### LLM Service

`llm.py` handles interaction with the language model.

The retrieved context can be used to produce responses grounded in the available documents.

---

## 8. Chat Request Flow

A typical chat request can be understood as the following sequence:

```text
User
  ↓
Frontend
  ↓
Chat API
  ↓
RAG Service
  ↓
Vector Store
  ↓
Relevant Document Chunks
  ↓
LLM Service
  ↓
Grounded Response
  ↓
Frontend
```

The purpose of the RAG layer is to provide relevant document context to the generation step rather than relying only on the language model's general knowledge.

---

## 9. Document Flow

The document workflow can be summarized as:

```text
User uploads document
        ↓
Document API
        ↓
Ingestion Service
        ↓
Document Processing
        ↓
Chunking
        ↓
Embedding Generation
        ↓
Vector Store
        ↓
Document available for retrieval
```

This separation allows document processing and retrieval logic to remain independent from the frontend.

---

## 10. Authentication Flow

Authentication-related API functionality is located in:

```text
backend/app/api/v1/auth.py
```

Security-related implementation is located in:

```text
backend/app/core/security.py
```

The frontend contains authentication-related pages:

```text
frontend/src/app/login/
frontend/src/app/forgot-password/
frontend/src/app/reset-password/
```

At a high level:

```text
User
 ↓
Login Page
 ↓
Authentication API
 ↓
Security Validation
 ↓
Authenticated Session
 ↓
Protected Application Features
```

Authentication-related dependencies are centralized where possible so that API endpoints can consistently apply access-control requirements.

---

## 11. Audit Functionality

Audit-related backend functionality is located at:

```text
backend/app/api/v1/audit.py
```

The corresponding frontend route is:

```text
frontend/src/app/audit/
```

The audit functionality provides a dedicated area for reviewing application activity rather than mixing audit-related concerns into other application pages.

---

## 12. Prompts

System-level prompting is maintained separately from application logic:

```text
prompts/system_prompt.txt
```

Keeping prompts in a dedicated directory makes them easier to inspect and update without searching through backend service implementations.

When modifying prompts, changes should be reviewed carefully because prompt changes can affect generated responses even when application code remains unchanged.

---

## 13. Testing

Backend tests are located in:

```text
backend/tests/
```

Current test files include:

```text
test_auth.py
test_ingestion.py
test_rag.py
test_semantic_search.py
test_latency_and_grounding.py
test_reranker.py
```

### Test Responsibilities

| Test                            | Main Area                                         |
| ------------------------------- | ------------------------------------------------- |
| `test_auth.py`                  | Authentication behavior                           |
| `test_ingestion.py`             | Document ingestion                                |
| `test_rag.py`                   | RAG functionality & SSE token streaming           |
| `test_semantic_search.py`       | Top-k semantic search & filtering                 |
| `test_latency_and_grounding.py` | Response lookup latency & prompt grounding audits |
| `test_reranker.py`              | Cross-encoder re-ranking & supersession filtering |
| `conftest.py`                   | Shared test configuration                         |

When modifying backend functionality, the relevant existing tests should be run before opening a pull request.

---

## 14. Environment Configuration

The backend provides:

```text
backend/.env.example
```

The frontend provides:

```text
frontend/.env.local.example
```

These files act as references for required environment configuration.

Actual secrets and credentials should not be committed to the repository.

Developers should create their local environment files based on the example files and provide their own local credentials/configuration.

---

## 15. Local Development

### Backend

Move into the backend directory:

```bash
cd backend
```

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Create the required environment configuration using:

```text
.env.example
```

The repository also provides:

```text
start.ps1
```

which can be used as the project's PowerShell startup script.

### Frontend

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The exact environment variables required by the frontend should be configured using:

```text
.env.local.example
```

---

## 16. Important Development Principles

When working on the repository:

### Keep responsibilities separated

Frontend code should primarily handle presentation and user interaction.

Backend code should handle API operations, application logic, data access, document processing, and RAG functionality.

### Reuse existing services

Before adding new functionality, check whether an existing service already provides the required behavior.

For example, RAG-related functionality should remain centralized in the existing service layer instead of being duplicated inside API routes.

### Avoid unnecessary changes

A small change should remain a small change.

Avoid modifying unrelated files when working on a specific feature or bug fix.

### Protect configuration and secrets

Never commit:

* API keys
* passwords
* access tokens
* private credentials
* local environment files containing secrets

Use the provided example environment files as templates.

---

## 17. Pull Request Guidelines

Before creating a pull request:

1. Understand the existing implementation.
2. Keep the change focused.
3. Avoid unrelated formatting changes.
4. Run relevant tests.
5. Check that no secrets were accidentally added.
6. Review the final diff.
7. Clearly explain what changed and why.

A good pull request should make it easy for another developer to answer:

* What changed?
* Why was it changed?
* Which files were affected?
* Does it change existing behavior?
* How was it tested?

---

## 18. Recommended Repository Reading Order

For a new developer joining the project, the following order provides a useful introduction:

```text
README.md
   ↓
PRD.md
   ↓
docs/hld.md
   ↓
docs/lld.md
   ↓
backend/app/main.py
   ↓
backend/app/api/
   ↓
backend/app/services/
   ↓
frontend/src/app/
   ↓
frontend/src/components/
   ↓
backend/tests/
```

This order starts with the project's purpose and architecture before moving into implementation details.

---

## 19. Quick Reference

| Area                 | Location                       |
| -------------------- | ------------------------------ |
| Frontend             | `frontend/`                    |
| Backend              | `backend/`                     |
| API routes           | `backend/app/api/v1/`          |
| Configuration        | `backend/app/core/config.py`   |
| Database             | `backend/app/core/database.py` |
| Security             | `backend/app/core/security.py` |
| Models               | `backend/app/models/`          |
| API schemas          | `backend/app/schemas/`         |
| RAG services         | `backend/app/services/`        |
| Prompts              | `prompts/`                     |
| Backend tests        | `backend/tests/`               |
| High-level design    | `docs/hld.md`                  |
| Low-level design     | `docs/lld.md`                  |
| Product requirements | `PRD.md`                       |

---

## 20. Final Note

This guide is intended to serve as a practical starting point for developers working with the GAA repository.

It complements the existing README, PRD, HLD, and LLD documentation by focusing specifically on repository navigation, development workflow, and understanding how the major application components fit together.
