import pytest
from fastapi.testclient import TestClient
from app.services.rag import rag_pipeline, REFUSAL_MESSAGE, conversation_history_manager


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# ConversationHistoryManager unit tests
# ---------------------------------------------------------------------------

class TestConversationHistoryManager:
    """Unit tests for the ConversationHistoryManager helper."""

    def test_trim_honours_max_turns(self):
        """History is capped to max_turns most recent messages."""
        mgr = conversation_history_manager
        history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        trimmed = mgr.trim(history)
        assert len(trimmed) <= mgr.max_turns
        # The retained messages are the most recent ones
        assert trimmed[-1]["content"] == "msg 19"

    def test_is_referential_detects_pronouns(self):
        """Queries with referential pronouns are flagged."""
        mgr = conversation_history_manager
        assert mgr.is_referential("What about for NRIs?") is True
        assert mgr.is_referential("Does it apply to them too?") is True
        assert mgr.is_referential("And for joint accounts?") is True

    def test_is_referential_passes_self_contained_queries(self):
        """Standalone queries that need no context are not flagged."""
        mgr = conversation_history_manager
        assert mgr.is_referential(
            "What is the capital gains tax rate on High-Yield Debt Funds for resident individual accounts?"
        ) is False

    def test_is_referential_flags_short_queries(self):
        """Very short queries (<=5 words) are always considered referential."""
        mgr = conversation_history_manager
        assert mgr.is_referential("How does this work?") is True
        assert mgr.is_referential("What is the rate?") is True

    def test_build_history_string_truncates_long_messages(self):
        """Messages longer than max_chars_per_message are truncated."""
        mgr = conversation_history_manager
        long_content = "x" * 1000
        history = [{"role": "user", "content": long_content}]
        result = mgr.build_history_string(history)
        # Should be truncated + ellipsis
        assert len(result) < 1000
        assert result.endswith("...")

    def test_extract_last_topic_returns_latest_user_message(self):
        """extract_last_topic returns the most recent user turn."""
        mgr = conversation_history_manager
        history = [
            {"role": "user", "content": "First question about bonds"},
            {"role": "assistant", "content": "Bonds are..."},
            {"role": "user", "content": "What about mutual funds?"},
            {"role": "assistant", "content": "Mutual funds are..."},
        ]
        topic = mgr.extract_last_topic(history)
        assert topic == "What about mutual funds?"

    def test_extract_last_topic_empty_history(self):
        """Returns empty string when there is no history."""
        mgr = conversation_history_manager
        assert mgr.extract_last_topic([]) == ""


# ---------------------------------------------------------------------------
# RAGPipeline.rewrite_query tests
# ---------------------------------------------------------------------------

class TestQueryRewriting:
    """Tests for the multi-turn query rewriting logic inside RAGPipeline."""

    def test_empty_history_returns_original_query(self):
        """With no chat history the query is returned unchanged."""
        query = "What is the penalty for early withdrawal from Liquid Fund A?"
        result = rag_pipeline.rewrite_query(query, [])
        assert result == query.strip()

    def test_non_referential_query_skips_llm(self):
        """
        A long, self-contained query with history present must NOT be reformulated
        (fast-path bypass to avoid unnecessary LLM calls).
        """
        query = "What are the lock-in period requirements for ELSS mutual funds under Section 80C?"
        history = [
            {"role": "user", "content": "Tell me about debt funds."},
            {"role": "assistant", "content": "Debt funds are fixed-income instruments."},
        ]
        result = rag_pipeline.rewrite_query(query, history)
        # The non-referential query must be returned as-is (possibly stripped)
        assert result == query.strip()

    def test_conversational_query_rewriting_nri_follow_up(self):
        """Verifies that follow-up queries containing 'NRI' are reformulated with context."""
        history = [
            {"role": "user", "content": "What is the capital gains tax on municipal bonds?"},
            {"role": "assistant", "content": "The tax rate is 10% for domestic resident accounts."},
        ]
        follow_up = "What about for NRIs?"
        rewritten = rag_pipeline.rewrite_query(follow_up, history)
        assert rewritten != follow_up
        assert "nri" in rewritten.lower() or "non-resident" in rewritten.lower()

    def test_pronoun_follow_up_expands_to_include_topic(self):
        """Follow-ups with 'it'/'them' are enriched with the prior conversation topic."""
        history = [
            {"role": "user", "content": "Explain the LTCG rules for equity funds."},
            {"role": "assistant", "content": "LTCG on equity funds is taxed at 10% above 1 lakh."},
        ]
        follow_up = "Does it apply to NRIs too?"
        rewritten = rag_pipeline.rewrite_query(follow_up, history)
        # Must contain some form of context from history
        assert "nri" in rewritten.lower() or "equity" in rewritten.lower() or "ltcg" in rewritten.lower()

    def test_multi_turn_accumulates_context_over_three_turns(self):
        """
        A three-turn conversation followed by a referential query must produce
        a standalone query referencing the earlier topic.
        """
        history = [
            {"role": "user", "content": "What is the KYC requirement for opening a demat account?"},
            {"role": "assistant", "content": "PAN, Aadhaar, and proof of address are required."},
            {"role": "user", "content": "What about for corporate entities?"},
            {"role": "assistant", "content": "Corporate entities need MCA registration and MOA."},
            {"role": "user", "content": "And for NRI accounts?"},
            {"role": "assistant", "content": "NRI accounts require FEMA compliance and NRE/NRO proof."},
        ]
        follow_up = "What about for PIOs?"
        rewritten = rag_pipeline.rewrite_query(follow_up, history)
        # The rewritten query must be standalone and related to KYC/account context
        assert len(rewritten) > len(follow_up)

    def test_history_trimming_prevents_old_context_leakage(self):
        """
        Queries far back in history (beyond max_turns) must not influence reformulation.
        Only the recent window should be used.
        """
        mgr = conversation_history_manager
        # Build a history longer than max_turns
        history = [
            {"role": "user", "content": f"Old topic {i}"},
            {"role": "assistant", "content": f"Old answer {i}"},
        ] * 10  # 20 messages total
        trimmed = mgr.trim(history)
        assert len(trimmed) == mgr.max_turns

    def test_rewrite_fallback_on_empty_llm_response(self):
        """
        When the LLM returns an empty string for a referential query, the fallback
        topic-injection logic must produce a non-empty result.
        """
        history = [
            {"role": "user", "content": "Capital gains tax on ELSS"},
            {"role": "assistant", "content": "ELSS has 3-year lock-in."},
        ]
        # Monkeypatch llm_service.generate to return empty string
        original_generate = rag_pipeline.history_manager.__class__  # just a reference
        import app.services.rag as rag_module
        original = rag_module.llm_service.generate

        try:
            rag_module.llm_service.generate = lambda **kwargs: ""
            result = rag_pipeline.rewrite_query("What about it for NRIs?", history)
            # Should fallback to topic + original query
            assert result  # non-empty
            assert len(result) > 0
        finally:
            rag_module.llm_service.generate = original


# ---------------------------------------------------------------------------
# End-to-end RAG integration tests (require FastAPI client fixture)
# ---------------------------------------------------------------------------

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
