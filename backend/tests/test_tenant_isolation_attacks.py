import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from app.models.models import Document, ComplianceAuditLog


def get_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


class TestTenantIsolationAttacks:
    """
    Mandatory Section 8 Tenant Isolation Attack Suite.
    Verifies that User A (branch_12_central) can NEVER access or observe User B's (branch_01_north) data.
    """

    @pytest.fixture(autouse=True)
    def seed_tenant_documents(self, client: TestClient):
        """Uploads a confidential document to North Branch (branch_01_north)."""
        north_token = get_token(client, "north_rm@wealth.bank.com", "NorthPassword123!")
        doc_content = (
            b"Section 99.1 North Branch Confidential High-Net-Worth Strategy: "
            b"Exclusive north branch allocation rate is 18.5% for ultra-HNW clients only."
        )
        res = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {north_token}"},
            files={"file": ("North_Confidential_Strategy.txt", doc_content, "text/plain")},
            data={"doc_type": "policy_manual", "version": "v1.0", "effective_date": "2024-01-01"},
        )
        assert res.status_code == 201
        self.north_doc_id = res.json()["document_id"]

        # Also get a chunk ID from North Branch
        chunks_res = client.get(
            f"/api/v1/documents/{self.north_doc_id}/chunks",
            headers={"Authorization": f"Bearer {north_token}"},
        )
        assert chunks_res.status_code == 200
        assert len(chunks_res.json()) > 0
        self.north_chunk_id = chunks_res.json()[0]["id"]

    def test_attack_1_request_other_tenant_document_by_id(self, client: TestClient):
        """Vector 1: User A requests User B's document by ID -> MUST return 404."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.get(
            f"/api/v1/documents/{self.north_doc_id}",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert res.status_code == 404
        assert "not found or does not belong to your tenant account" in res.json()["detail"].lower()

    def test_attack_2_request_other_tenant_chunks(self, client: TestClient):
        """Vector 2: User A tries to retrieve User B's chunks -> MUST return 404."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.get(
            f"/api/v1/documents/{self.north_doc_id}/chunks",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert res.status_code == 404
        assert "not found or does not belong to your tenant account" in res.json()["detail"].lower()

    def test_attack_3_send_other_account_id_in_query_body(self, client: TestClient):
        """Vector 3: User A injects another account_id in query payload -> MUST NOT leak North data."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.post(
            "/api/v1/chat/query/sync",
            headers={"Authorization": f"Bearer {central_token}"},
            json={
                "query": "North branch confidential allocation rate Section 99.1",
                "account_id": "branch_01_north",  # Malicious spoof attempt
            },
        )
        assert res.status_code == 200
        # Must refuse because Central branch does not have this document
        assert res.json()["is_refusal"] is True
        assert "18.5%" not in res.json()["answer"]

    def test_attack_4_modify_account_id_in_headers(self, client: TestClient):
        """Vector 4: User A injects custom tenant headers -> backend strictly derives tenant from verified JWT."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.post(
            "/api/v1/chat/query/sync",
            headers={
                "Authorization": f"Bearer {central_token}",
                "X-Account-ID": "branch_01_north",
                "X-Tenant-Scope": "branch_01_north",
            },
            json={"query": "North branch allocation rate Section 99.1"},
        )
        assert res.status_code == 200
        assert res.json()["is_refusal"] is True

    def test_attack_5_change_url_parameters_to_filter_other_tenant(self, client: TestClient):
        """Vector 5: User A attempts query parameters with another account -> strictly returns only own documents."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.get(
            "/api/v1/documents?account_id=branch_01_north",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert res.status_code == 200
        docs = res.json()["documents"]
        # Ensure none of the returned docs belong to branch_01_north
        for d in docs:
            assert d["account_id"] == "branch_12_central"
            assert d["id"] != self.north_doc_id

    def test_attack_6_delete_other_tenant_document(self, client: TestClient):
        """Vector 6: Compliance Admin in Branch 12 attempts to delete North Branch document -> 404."""
        comp_token = get_token(client, "comp_test@wealth.bank.com", "AdminPassword123!")
        res = client.delete(
            f"/api/v1/documents/{self.north_doc_id}",
            headers={"Authorization": f"Bearer {comp_token}"},
        )
        assert res.status_code == 404
        assert "not found or does not belong to your tenant account" in res.json()["detail"].lower()

    def test_attack_7_access_other_tenant_audit_logs(self, client: TestClient):
        """Vector 7: Compliance Admin in Branch 12 queries audit logs -> only sees Branch 12 logs."""
        comp_token = get_token(client, "comp_test@wealth.bank.com", "AdminPassword123!")
        
        # Plant a north audit log in DB
        db = TestingSessionLocal()
        north_log = ComplianceAuditLog(
            account_id="branch_01_north",
            user_id="usr_north_rm_test",
            query="Confidential North query",
            similarity_score=0.99,
            response="Confidential North response",
            is_refusal=False,
            latency_ms=120,
            retrieved_chunk_ids=["chunk_north_1"],
        )
        db.add(north_log)
        db.commit()
        db.close()

        res = client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {comp_token}"})
        assert res.status_code == 200
        for log in res.json()["logs"]:
            assert log["account_id"] == "branch_12_central"
            assert "Confidential North query" not in log["query"]

    def test_attack_8_guess_sequential_document_ids(self, client: TestClient):
        """Vector 8: Guessing sequential or forged document IDs -> rejected with 404."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        for guessed_id in ["doc_1", "doc_00000001", "doc_north_test", "doc_9999"]:
            res = client.get(
                f"/api/v1/documents/{guessed_id}",
                headers={"Authorization": f"Bearer {central_token}"},
            )
            assert res.status_code == 404

    def test_attack_9_direct_semantic_search_cross_tenant_isolation(self, client: TestClient):
        """Vector 9: Semantic search endpoint strictly filters to caller's account_id."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.post(
            "/api/v1/chat/search",
            headers={"Authorization": f"Bearer {central_token}"},
            json={"query": "North branch confidential allocation rate Section 99.1"},
        )
        assert res.status_code == 200
        # Results must be empty or strictly belong to branch_12_central
        for item in res.json()["results"]:
            assert item["metadata"]["account_id"] == "branch_12_central"

    def test_attack_10_request_citation_preview_belonging_to_other_account(self, client: TestClient):
        """Vector 10: Citation preview endpoint validates tenant ownership of chunk_id -> 404."""
        central_token = get_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
        res = client.get(
            f"/api/v1/chat/citation-preview?chunk_id={self.north_chunk_id}",
            headers={"Authorization": f"Bearer {central_token}"},
        )
        assert res.status_code == 404
        assert "access denied" in res.json()["detail"].lower()
