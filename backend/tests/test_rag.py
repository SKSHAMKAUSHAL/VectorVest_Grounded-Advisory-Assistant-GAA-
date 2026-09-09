import pytest
from fastapi.testclient import TestClient
from app.services.rag import rag_pipeline, REFUSAL_MESSAGE

def get_auth_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def test_conversational_query_rewriting():
    """Verifies that follow-up queries are reformulated with conversation context."""
    history = [
        {"role": "user", "content": "What is the capital gains tax on municipal bonds?"},
        {"role": "assistant", "content": "The tax rate is 10% for domestic resident accounts."},
    ]
    follow_up = "What about for NRIs?"
    rewritten = rag_pipeline.rewrite_query(follow_up, history)
    assert rewritten != follow_up
    assert "nri" in rewritten.lower() or "non-resident" in rewritten.lower()

def test_guardrail_hard_refusal_when_unindexed(client: TestClient):
    """Verifies that low confidence queries trigger deterministic compliance refusal."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

    # Vector store is empty for this account
    response = client.post(
        "/api/v1/chat/query/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "What is the penalty for early withdrawal from Fund 900?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is True
    assert data["answer"] == REFUSAL_MESSAGE
    assert len(data["citations"]) == 0
    assert data["similarity_score"] < 0.68

def test_grounded_answer_with_citations(client: TestClient):
    """Verifies that high-confidence queries return grounded answers with citations."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

    # 1. Upload approved policy document
    doc_text = b"""
    Section 4.2.1 High Yield Debt Funds Tax Exemption
    Under amended schedule 4, long-term capital gains on High-Yield Debt Funds
    shall be taxed at 10% without indexation for domestic resident individual accounts.
    """
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Tax_Circular_2024.txt", doc_text, "text/plain")},
        data={
            "doc_type": "tax_circular",
            "version": "v2.1",
            "effective_date": "2024-01-01",
            "is_discontinued": "false",
        },
    )
    assert upload_res.status_code == 201

    # 2. Query grounded guidance
    query_res = client.post(
        "/api/v1/chat/query/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "High Yield Debt Funds tax exemption schedule 4"},
    )
    assert query_res.status_code == 200
    data = query_res.json()

    assert data["is_refusal"] is False
    assert len(data["citations"]) >= 1
    citation = data["citations"][0]
    assert citation["document_name"] == "Tax_Circular_2024.txt"
    assert citation["version"] == "v2.1"
    assert "Section 4.2.1" in citation["clause_id"]
    assert "[Doc: Tax_Circular_2024.txt" in data["answer"]

def test_sse_streaming_response(client: TestClient):
    """Verifies that the /query endpoint streams tokens and emits citations and done events."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

    response = client.post(
        "/api/v1/chat/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Is there any general policy available?"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body_text = response.text
    assert "event: token" in body_text
    assert "event: citations" in body_text
    assert "event: done" in body_text
    assert "[DONE]" in body_text

def test_tenant_isolation_in_rag_retrieval(client: TestClient):
    """Verifies that Tenant A cannot retrieve Tenant B documents during RAG."""
    token_central = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
    token_north = get_auth_token(client, "north_rm@wealth.bank.com", "NorthPassword123!")

    # North uploads proprietary circular
    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_north}"},
        files={"file": ("North_Secret_Rule.txt", b"Section 9.9 Secret North Regional Directive", "text/plain")},
        data={"doc_type": "policy_manual", "version": "v1.0", "effective_date": "2024-01-01"},
    )

    # Central RM queries for North Secret Rule -> Must Refuse!
    central_query = client.post(
        "/api/v1/chat/query/sync",
        headers={"Authorization": f"Bearer {token_central}"},
        json={"query": "Secret North Regional Directive Section 9.9"},
    )
    assert central_query.status_code == 200
    assert central_query.json()["is_refusal"] is True
    assert central_query.json()["answer"] == REFUSAL_MESSAGE

def test_compliance_audit_logging_and_rbac(client: TestClient):
    """Verifies that queries generate audit logs and only ComplianceAdmin can access /audit/logs."""
    rm_token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
    admin_token = get_auth_token(client, "comp_test@wealth.bank.com", "AdminPassword123!")

    # Execute a query
    client.post(
        "/api/v1/chat/query/sync",
        headers={"Authorization": f"Bearer {rm_token}"},
        json={"query": "Auditable test inquiry for compliance log verification"},
    )

    # RM attempts to view audit logs -> 403 Forbidden
    rm_audit = client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {rm_token}"})
    assert rm_audit.status_code == 403

    # ComplianceAdmin views audit logs -> 200 OK
    admin_audit = client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_audit.status_code == 200
    data = admin_audit.json()
    assert data["total"] >= 1
    first_log = data["logs"][0]
    assert first_log["query"] == "Auditable test inquiry for compliance log verification"
    assert first_log["account_id"] == "branch_12_central"
    assert first_log["latency_ms"] >= 0
