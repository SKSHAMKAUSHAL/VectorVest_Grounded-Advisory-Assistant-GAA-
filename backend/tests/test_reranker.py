"""
Unit and Integration Tests for Cross-Encoder Re-Ranking Engine & Supersession Filtering.

Verifies:
1. Cross-encoder scoring precision and clause-specific rank promotion.
2. Candidate pool re-ranking and top-n pruning.
3. Active exclusion of superseded circulars/policies in vector search.
4. End-to-end integration into the RAG generation pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from app.services.reranker import reranker, _compute_cross_encoder_score
from app.services.vector_store import vector_store
from app.services.embedding import embedding_service
from app.services.rag import rag_pipeline, REFUSAL_MESSAGE


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# Cross-Encoder Re-ranker Unit Tests
# ---------------------------------------------------------------------------

class TestCrossEncoderReranker:
    """Unit tests for the CrossEncoderReranker service."""

    def test_reranker_promotes_exact_clause_and_entities(self):
        """
        Asserts that a candidate with exact clause and numeric match ranks higher
        than a generic candidate that had a similar initial dense score.
        """
        query = "Section 4.2.1 High Yield Debt Funds 10% tax exemption"

        candidates = [
            {
                "id": "chunk_generic",
                "score": 0.72,
                "text": "General principles of wealth advisory regarding fixed income portfolios.",
                "metadata": {"document_name": "General_Wealth.pdf", "clause_id": "Section 1.0"},
            },
            {
                "id": "chunk_exact",
                "score": 0.70,  # Lower dense score initially
                "text": "Section 4.2.1 High Yield Debt Funds: Taxed at 10% for domestic accounts.",
                "metadata": {"document_name": "Tax_Circular_02.pdf", "clause_id": "Section 4.2.1"},
            },
        ]

        reranked = reranker.rerank(query=query, candidates=candidates, top_n=2)

        assert len(reranked) == 2
        # Exact clause match chunk must be promoted to 1st position
        assert reranked[0]["id"] == "chunk_exact"
        assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
        assert "dense_score" in reranked[0]
        assert "rerank_score" in reranked[0]

    def test_reranker_handles_empty_candidates_or_query(self):
        """Edge case resilience: empty candidates list or whitespace query."""
        assert reranker.rerank("some query", [], top_n=5) == []

        cand = [{"id": "c1", "score": 0.8, "text": "Some text"}]
        res = reranker.rerank("", cand, top_n=5)
        assert len(res) == 1
        assert res[0]["id"] == "c1"

    def test_reranker_caps_output_to_top_n(self):
        """Verifies top_n parameter truncates candidate output correctly."""
        query = "early withdrawal penalties"
        candidates = [
            {"id": f"chunk_{i}", "score": 0.60 + (i * 0.02), "text": f"Policy text on withdrawal penalties rule {i}"}
            for i in range(10)
        ]

        reranked = reranker.rerank(query=query, candidates=candidates, top_n=3)
        assert len(reranked) == 3
        # Ensure descending order
        scores = [c["rerank_score"] for c in reranked]
        assert scores == sorted(scores, reverse=True)

    def test_reranker_with_min_score_cutoff(self):
        """Verifies that candidates below min_score threshold are pruned."""
        query = "wealth management taxation"
        candidates = [
            {"id": "c1", "score": 0.85, "text": "wealth management taxation rules"},
            {"id": "c2", "score": 0.40, "text": "unrelated retail gardening policy"},
        ]
        reranked = reranker.rerank(query=query, candidates=candidates, top_n=5, min_score=0.70)
        assert len(reranked) == 1
        assert reranked[0]["id"] == "c1"

    def test_reranker_handles_special_regex_and_punctuation(self):
        """Ensures query with unescaped regex characters does not throw exceptions."""
        query = "Tax rate (10%) & capital gains [Schedule 4] + Section 4.2.1?"
        candidates = [
            {"id": "c1", "score": 0.70, "text": "Section 4.2.1 specifies capital gains tax rate 10% under Schedule 4."}
        ]
        reranked = reranker.rerank(query=query, candidates=candidates, top_n=1)
        assert len(reranked) == 1
        assert reranked[0]["rerank_score"] >= 0.70

    def test_reranker_profile_latency(self):
        """Verifies profile_rerank returns timing statistics within performance budget."""
        query = "High Yield Debt Fund Section 4.2.1"
        candidates = [
            {"id": f"c_{i}", "score": 0.65 + (i * 0.01), "text": f"Clause {i} policy text for bonds"}
            for i in range(15)
        ]
        res = reranker.profile_rerank(query=query, candidates=candidates, top_n=5)
        assert "latency_ms" in res
        assert res["latency_ms"] < 20.0  # Must be strictly under 20ms
        assert res["input_candidates"] == 15
        assert res["output_candidates"] == 5



# ---------------------------------------------------------------------------
# Supersession Filtering Tests
# ---------------------------------------------------------------------------

class TestSupersessionFiltering:
    """Verifies that superseded documents/circulars are barred from retrieval."""

    def test_mark_document_as_superseded_in_vector_store(self):
        """
        Ingests two documents, marks one as superseded, and verifies that
        default search excludes the superseded document chunks.
        """
        account_id = "test_supersession_acc"
        query_text = "Municipal Bond Tax Exemptions"
        query_vec = embedding_service.get_embedding(query_text)

        # Ingest active circular (v2.0)
        vector_store.add_chunks(
            account_id=account_id,
            document_id="doc_v2_active",
            document_name="Tax_Circular_v2.pdf",
            version="v2.0",
            doc_type="tax_circular",
            effective_date="2024-06-01",
            is_discontinued=False,
            chunks=[{"text": "Section 1 Municipal Bond Tax Exemptions under 2024 active circular", "clause_id": "Section 1", "page_number": 1, "chunk_index": 0}],
            embeddings=[embedding_service.get_embedding("Section 1 Municipal Bond Tax Exemptions under 2024 active circular")],
            is_superseded=False,
        )

        # Ingest older circular (v1.0)
        vector_store.add_chunks(
            account_id=account_id,
            document_id="doc_v1_old",
            document_name="Tax_Circular_v1.pdf",
            version="v1.0",
            doc_type="tax_circular",
            effective_date="2023-01-01",
            is_discontinued=False,
            chunks=[{"text": "Section 1 Municipal Bond Tax Exemptions under 2023 superseded circular", "clause_id": "Section 1", "page_number": 1, "chunk_index": 0}],
            embeddings=[embedding_service.get_embedding("Section 1 Municipal Bond Tax Exemptions under 2023 superseded circular")],
            is_superseded=False,
        )

        # Mark doc_v1_old as superseded
        updated_count = vector_store.mark_document_as_superseded("doc_v1_old")
        assert updated_count >= 1

        # Default search: include_superseded=False
        results_default = vector_store.search(
            query_vector=query_vec,
            account_id=account_id,
            include_superseded=False,
        )
        doc_names = [r["document_name"] for r in results_default]
        assert "Tax_Circular_v2.pdf" in doc_names
        assert "Tax_Circular_v1.pdf" not in doc_names

        # Archival search: include_superseded=True
        results_all = vector_store.search(
            query_vector=query_vec,
            account_id=account_id,
            include_superseded=True,
        )
        all_doc_names = [r["document_name"] for r in results_all]
        assert "Tax_Circular_v1.pdf" in all_doc_names

    def test_ingestion_api_supersedes_prior_document(self, client: TestClient):
        """
        Verifies end-to-end via REST API: uploading a newer tax circular with superseded_by
        removes the older circular from subsequent synchronous chat answers.
        """
        token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

        # 1. Upload initial circular v1.0
        doc1_res = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("Circular_A_v1.txt", b"Section 9.1 Old tax rate 15% on capital gains.", "text/plain")},
            data={"doc_type": "tax_circular", "version": "v1.0", "effective_date": "2023-01-01"},
        )
        assert doc1_res.status_code == 201
        doc1_id = doc1_res.json()["document_id"]

        # Verify query retrieves v1.0
        q1 = client.post(
            "/api/v1/chat/query/sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Section 9.1 Old tax rate 15% on capital gains"},
        )
        assert q1.status_code == 200
        assert not q1.json()["is_refusal"]
        assert any(c["document_name"] == "Circular_A_v1.txt" for c in q1.json()["citations"])

        # 2. Upload circular v2.0 that supersedes doc1_id
        doc2_res = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("Circular_A_v2.txt", b"Section 9.1 Amended tax rate 10% on capital gains.", "text/plain")},
            data={
                "doc_type": "tax_circular",
                "version": "v2.0",
                "effective_date": "2024-01-01",
                "superseded_by": doc1_id,
            },
        )
        assert doc2_res.status_code == 201

        # Verify query now only cites v2.0 and never v1.0
        q2 = client.post(
            "/api/v1/chat/query/sync",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Section 9.1 Amended tax rate 10% on capital gains"},
        )
        assert q2.status_code == 200
        data2 = q2.json()
        assert not data2["is_refusal"]
        for cit in data2["citations"]:
            assert cit["document_name"] != "Circular_A_v1.txt"
        assert any(cit["document_name"] == "Circular_A_v2.txt" for cit in data2["citations"])


# ---------------------------------------------------------------------------
# End-to-End RAG Pipeline with Re-ranker Tests
# ---------------------------------------------------------------------------

class TestRAGPipelineReRankingIntegration:
    """Verifies that RAG pipeline properly applies re-ranking and confidence thresholding."""

    def test_rag_pipeline_retrieve_and_evaluate_with_reranking(self):
        """
        Asserts that retrieve_and_evaluate executes two-stage retrieval,
        returning top candidates ordered by cross-encoder score.
        """
        acc = "branch_rerank_test"

        # Ingest test policy chunks
        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_policy_rr",
            document_name="Wealth_Mandate_v3.pdf",
            version="v3.0",
            doc_type="policy_manual",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=[
                {
                    "text": "Clause 3.2.1 NRI Repatriation Limits: Non-Resident Indian clients may repatriate up to USD 1,000,000 per financial year under RBI LRS guidelines.",
                    "clause_id": "Clause 3.2.1",
                    "page_number": 12,
                    "chunk_index": 0,
                },
                {
                    "text": "Clause 1.0 General Definitions: Terms used in Wealth Advisory services.",
                    "clause_id": "Clause 1.0",
                    "page_number": 1,
                    "chunk_index": 1,
                },
            ],
            embeddings=[
                embedding_service.get_embedding("Clause 3.2.1 NRI Repatriation Limits USD 1,000,000"),
                embedding_service.get_embedding("Clause 1.0 General Definitions"),
            ],
        )

        res = rag_pipeline.retrieve_and_evaluate(
            query="Clause 3.2.1 NRI Repatriation Limits USD 1,000,000",
            account_id=acc,
            top_k=2,
        )

        assert res["decision"] == "GENERATE"
        assert not res["is_refusal"]
        assert len(res["citations"]) >= 1
        # The top citation must be Clause 3.2.1
        assert "Clause 3.2.1" in res["citations"][0]["clause_id"]
        assert res["citations"][0]["score"] >= 0.68
