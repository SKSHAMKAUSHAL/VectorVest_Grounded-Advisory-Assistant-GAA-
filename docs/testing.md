# Comprehensive Testing Strategy & Verification Guide: WealthGuard AI

## 1. Testing Philosophy & Scope

WealthGuard AI operates in a high-consequence wealth advisory environment. The test suite is designed to ensure zero tolerance for:
1. Cross-tenant data leakage.
2. Ungrounded generative hallucinations.
3. Use of superseded policies or discontinued financial products.
4. Security perimeter bypasses (authentication, RBAC, file uploads).

---

## 2. Test Execution Quick Reference

### 2.1 Full Backend Test Suite
```bash
# From workspace root
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```
**Results**: 140 passed across 16 test modules in ~136s.

### 2.2 Security & Tenant Isolation Tests
```bash
# 10-Vector Tenant Isolation Attack Suite
backend\venv\Scripts\python.exe -m pytest backend/tests/test_tenant_isolation_attacks.py -v

# 15-Vector Security Attack Simulation Suite
backend\venv\Scripts\python.exe -m pytest backend/tests/test_security_attack_simulation.py -v
```

### 2.3 RAG Grounding & Latency Evaluation
```bash
backend\venv\Scripts\python.exe -m pytest backend/tests/test_latency_and_grounding.py -v
backend\venv\Scripts\python.exe -m pytest backend/tests/test_confidence_gate.py -v
```

### 2.4 Frontend Unit Tests & Build
```bash
# Vitest Component & Store Tests (8 passed)
npm --prefix frontend run test

# Next.js 14 Production Standalone Build (0 errors across 11 routes)
npm --prefix frontend run build
```

---

## 3. Test Suites Breakdown

| Test Suite | File | Focus Area |
| :--- | :--- | :--- |
| **Tenant Isolation Attacks** | `test_tenant_isolation_attacks.py` | 10 vectors: document access by ID, chunk theft, vector search cross-contamination, citation manipulation, user listing, branch spoofing |
| **Security Attack Simulation** | `test_security_attack_simulation.py` | 15 vectors: login brute force, account enumeration, forged JWT, alg 'none', expired tokens, RM role escalation, path traversal, fake PDF magic bytes, 25MB file rejection, 4000-char query limit, prompt injection boundary test |
| **RAG Grounding & Latency** | `test_latency_and_grounding.py` | Clause citations, discontinued product filtering, superseded document suppression, latency bounds (<2000ms), 4-thread concurrency |
| **Confidence Guardrail Gate** | `test_confidence_gate.py` | Cosine similarity threshold (0.68), zero-hallucination refusals, ambiguous query rewriting |
| **Adversarial & Edge Cases** | `test_adversarial_suite.py`, `test_prompt_edge_cases.py` | Jailbreak strings, prompt leakage attempts, malformed SSE requests |
| **Authentication & RBAC** | `test_auth.py` | Signup, login, password reset flow, hash storage, active user enforcement |
| **Document Ingestion** | `test_ingestion.py` | PDF parsing, clause chunking, metadata association, idempotent uploads |
| **Frontend Unit Suite** | `frontend/src/__tests__/auth.test.ts` | Auth state store, token persistence, logout cleanup, role management |

---

## 4. Tenant Isolation: 10 Attack Vectors Verified

1. **Direct Document Fetch by ID**: User from Branch Central queries Branch North document -> Returns `404 Not Found`.
2. **Direct Chunk Fetch by ID**: User from Branch Central queries Branch North document chunks -> Returns `404 Not Found`.
3. **Cross-Tenant Vector Similarity**: User queries confidential keywords existing only in North Branch -> Central Branch vector search returns zero chunks from North Branch.
4. **Citation Preview Spoofing**: User submits chunk ID belonging to another tenant -> Returns `404 Not Found`.
5. **Cross-Tenant Document Listing**: User requests document catalog -> Returned list contains strictly `account_id == current_user.account_id`.
6. **Cross-Tenant Audit Trail Access**: RM or Admin from Branch Central attempts to read North Branch audit logs -> Scoped strictly to current user's branch.
7. **Document Update / Supersede Spoofing**: Central branch user attempts to supersede North branch document -> Rejected with `404 Not Found`.
8. **Chunk Content Bleed in Generation**: RAG query executed by Central Branch user never receives North Branch text in `<untrusted_evidence>`.
9. **Target Account Injection at Signup**: Attacker passes arbitrary `account_id` during signup -> Rejected if invalid.
10. **Branch Isolation Verification**: Multiple tenants uploaded documents concurrently operate completely isolated across ChromaDB and PostgreSQL.

---

## 5. Performance & Concurrency Verification

- **Latency Target**: Time-to-First-Token (TTFT) < 1,500ms; Total Query Latency < 2,500ms.
- **Concurrency**: Verified with `concurrent.futures.ThreadPoolExecutor(max_workers=4)` executing concurrent queries against the SQLite test database with `threading.RLock()` synchronization.
