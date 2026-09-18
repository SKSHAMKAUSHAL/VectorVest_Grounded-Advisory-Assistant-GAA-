import pytest
from fastapi.testclient import TestClient
from app.services.vector_store import vector_store
from app.services.embedding import embedding_service
from app.services.rag import rag_pipeline


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


class TestTopKSemanticSearch:
    """Tests verifying top-k semantic search capabilities, ranking, filters, and safety."""

    @pytest.fixture(autouse=True)
    def setup_sample_chunks(self):
        """Seeds vector store with structured test chunks across topics and accounts."""
        self.account_a = "tenant_branch_alpha"
        self.account_b = "tenant_branch_beta"

        # Chunks for Account A
        chunks_a = [
            {
                "chunk_index": 0,
                "clause_id": "Clause 1.1",
                "page_number": 1,
                "text": "Section 80C Tax Exemption on Equity-Linked Savings Schemes (ELSS) investments up to Rs 1.5 lakh annually.",
            },
            {
                "chunk_index": 1,
                "clause_id": "Clause 1.2",
                "page_number": 2,
                "text": "Capital Gains Tax on High Yield Debt Funds shall be taxed at 10% without indexation for resident accounts.",
            },
            {
                "chunk_index": 2,
                "clause_id": "Clause 2.1",
                "page_number": 3,
                "text": "Standard Savings Account daily debit card ATM cash withdrawal limit is Rs 50,000.",
            },
            {
                "chunk_index": 3,
                "clause_id": "Clause 3.1",
                "page_number": 4,
                "text": "Corporate Demat account onboarding requirements include MCA registration, PAN, and Board Resolution.",
            },
            {
                "chunk_index": 4,
                "clause_id": "Clause 4.1",
                "page_number": 5,
                "text": "NRI Portfolio Investment Scheme guidelines governed under RBI regulations and FEMA Schedule 3.",
            },
        ]
        embeddings_a = embedding_service.get_embeddings([c["text"] for c in chunks_a])
        vector_store.add_chunks(
            account_id=self.account_a,
            document_id="doc_alpha_policy",
            document_name="Alpha_Investment_Policy.pdf",
            version="v1.0",
            doc_type="policy_manual",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=chunks_a,
            embeddings=embeddings_a,
        )

        # Discontinued product chunk for Account A
        discontinued_chunks = [
            {
                "chunk_index": 0,
                "clause_id": "Clause Sunset 1",
                "page_number": 1,
                "text": "Legacy Gold Plus Advantage Fund discontinued product variant, closed to new investors since 2021.",
            }
        ]
        discontinued_embeddings = embedding_service.get_embeddings([c["text"] for c in discontinued_chunks])
        vector_store.add_chunks(
            account_id=self.account_a,
            document_id="doc_alpha_sunset",
            document_name="Sunset_Gold_Plus.pdf",
            version="v0.9",
            doc_type="product_brochure",
            effective_date="2020-01-01",
            is_discontinued=True,
            chunks=discontinued_chunks,
            embeddings=discontinued_embeddings,
        )

        # Chunks for Account B (Tenant Isolation verification)
        chunks_b = [
            {
                "chunk_index": 0,
                "clause_id": "Clause Beta 9.9",
                "page_number": 1,
                "text": "Confidential Northern Branch Proprietary Algorithm for High Net Worth client risk scoring.",
            }
        ]
        embeddings_b = embedding_service.get_embeddings([c["text"] for c in chunks_b])
        vector_store.add_chunks(
            account_id=self.account_b,
            document_id="doc_beta_secret",
            document_name="Beta_Proprietary.pdf",
            version="v1.0",
            doc_type="policy_manual",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=chunks_b,
            embeddings=embeddings_b,
        )

    def test_top_k_exact_limit(self):
        """Verifies that retrieval strictly respects the requested top_k boundary."""
        for k in (1, 2, 3, 5):
            results = vector_store.semantic_search(
                query_text="tax and investment regulations",
                account_id=self.account_a,
                top_k=k,
            )
            assert len(results) == k, f"Expected exactly {k} candidates, got {len(results)}"

    def test_top_k_descending_score_ordering(self):
        """Verifies that results are monotonically non-increasing in similarity score."""
        results = vector_store.semantic_search(
            query_text="capital gains tax and tax exemptions",
            account_id=self.account_a,
            top_k=5,
        )
        assert len(results) > 1
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results are not sorted descending by score"

    def test_top_k_boundary_zero_and_negative(self):
        """Zero or negative top_k values must return an empty list without error."""
        assert vector_store.semantic_search("tax", self.account_a, top_k=0) == []
        assert vector_store.semantic_search("tax", self.account_a, top_k=-1) == []
        assert vector_store.search([0.1] * 1536, self.account_a, top_k=0) == []
        assert vector_store.search([0.1] * 1536, self.account_a, top_k=-10) == []

    def test_top_k_exceeding_total_chunks(self):
        """Requesting top_k larger than available account chunks safely returns all available matches."""
        results = vector_store.semantic_search(
            query_text="Northern Branch Secret",
            account_id=self.account_b,
            top_k=20,
        )
        assert len(results) == 1
        assert results[0]["clause_id"] == "Clause Beta 9.9"

    def test_semantic_relevance_ranking(self):
        """Topically matching chunks must rank highest with superior similarity scores."""
        # Query specifically matching Section 80C Tax Exemption
        results = vector_store.semantic_search(
            query_text="Section 80C Tax Exemption on ELSS investments",
            account_id=self.account_a,
            top_k=3,
        )
        assert len(results) >= 1
        top_result = results[0]
        assert "80c" in top_result["text"].lower() or "elss" in top_result["text"].lower()
        assert top_result["score"] >= 0.60
        if len(results) > 1:
            assert top_result["score"] > results[1]["score"]


    def test_tenant_isolation_in_semantic_search(self):
        """Tenant A can never retrieve Tenant B data, and vice versa."""
        # Search for Beta's content using Account A
        results_a = vector_store.semantic_search(
            query_text="Confidential Northern Branch Proprietary Algorithm",
            account_id=self.account_a,
            top_k=5,
        )
        retrieved_ids_a = [r["id"] for r in results_a]
        assert not any("doc_beta_secret" in chunk_id for chunk_id in retrieved_ids_a)

        # Search for Alpha's content using Account B
        results_b = vector_store.semantic_search(
            query_text="Section 80C Tax Exemption on ELSS",
            account_id=self.account_b,
            top_k=5,
        )
        retrieved_ids_b = [r["id"] for r in results_b]
        assert not any("doc_alpha_policy" in chunk_id for chunk_id in retrieved_ids_b)

    def test_discontinued_product_filtering(self):
        """Discontinued items are excluded by default and included when include_discontinued=True."""
        # Default: excluded
        results_default = vector_store.semantic_search(
            query_text="Legacy Gold Plus Advantage Fund",
            account_id=self.account_a,
            top_k=5,
            include_discontinued=False,
        )
        assert not any("Sunset" in r["document_name"] for r in results_default)

        # Explicitly included
        results_included = vector_store.semantic_search(
            query_text="Legacy Gold Plus Advantage Fund",
            account_id=self.account_a,
            top_k=5,
            include_discontinued=True,
        )
        assert any("Sunset" in r["document_name"] for r in results_included)

    def test_doc_type_filtering(self):
        """Filtering by doc_type restricts retrieved candidates strictly to that document type."""
        results = vector_store.semantic_search(
            query_text="investment policy",
            account_id=self.account_a,
            top_k=5,
            doc_type="policy_manual",
        )
        assert len(results) > 0
        for r in results:
            assert r["doc_type"] == "policy_manual"

    def test_min_score_filtering(self):
        """Candidates below min_score threshold are pruned."""
        high_threshold = 0.85
        results = vector_store.semantic_search(
            query_text="Random unrelated query with low similarity xyz123",
            account_id=self.account_a,
            top_k=5,
            min_score=high_threshold,
        )
        for r in results:
            assert r["score"] >= high_threshold

    def test_invalid_and_empty_inputs_safety(self):
        """Invalid or malformed inputs return empty lists gracefully without crashing."""
        assert vector_store.semantic_search("", self.account_a) == []
        assert vector_store.semantic_search("   ", self.account_a) == []
        assert vector_store.semantic_search(None, self.account_a) == []
        assert vector_store.search([], self.account_a) == []
        assert vector_store.search([float("nan")] * 1536, self.account_a) == []
        assert vector_store.search([0.1] * 1536, "") == []

    def test_batch_semantic_search(self):
        """Batch semantic search executes retrieval across multiple queries efficiently."""
        queries = [
            "Section 80C Tax Exemption",
            "Debit card ATM withdrawal limit",
            "Non-resident Indian FEMA guidelines",
        ]
        batch_results = vector_store.batch_semantic_search(
            queries=queries,
            account_id=self.account_a,
            top_k=2,
        )
        assert len(batch_results) == 3
        assert len(batch_results[0]) == 2
        assert "80c" in batch_results[0][0]["text"].lower() or "elss" in batch_results[0][0]["text"].lower()
        assert "atm" in batch_results[1][0]["text"].lower() or "savings" in batch_results[1][0]["text"].lower()
        assert "nri" in batch_results[2][0]["text"].lower() or "fema" in batch_results[2][0]["text"].lower()

    def test_rag_pipeline_top_k_integration(self):
        """Verifies that RAGPipeline retrieve_and_evaluate respects top_k limits."""
        eval_result = rag_pipeline.retrieve_and_evaluate(
            query="Capital Gains Tax on High Yield Debt Funds taxed at 10% without indexation for resident accounts",
            account_id=self.account_a,
            top_k=2,
        )
        assert eval_result["decision"] == "GENERATE"
        assert len(eval_result["citations"]) <= 2
        assert len(eval_result["retrieved_chunk_ids"]) <= 2


    def test_api_semantic_search_endpoint(self, client: TestClient):
        """Verifies POST /api/v1/chat/search endpoint returns structured semantic search results."""
        token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

        # Unauthenticated request should be rejected
        unauth_res = client.post("/api/v1/chat/search", json={"query": "tax exemption", "top_k": 3})
        assert unauth_res.status_code == 401

        # Authenticated search
        res = client.post(
            "/api/v1/chat/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "tax exemption rules", "top_k": 3},
        )
        assert res.status_code == 200
        data = res.json()
        assert "query" in data
        assert "account_id" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        assert data["account_id"] == "branch_12_central"
