import pytest
from fastapi.testclient import TestClient

from app.services.chunking import chunk_page_text_by_clause, chunk_document_pages
from app.services.vector_store import vector_store
from app.services.embedding import embedding_service

def get_auth_token(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def test_clause_boundary_chunking():
    """Verifies that regex correctly detects Section, Clause, and Article headings."""
    sample_text = """
    Preamble: General bank advisory principles for high-net-worth clients.

    Section 3.1.2 Capital Gains Tax on Municipal Debt
    Long-term capital gains on Tier-1 Municipal Bonds shall be assessed at 10% without indexation.
    All redemption requests must be submitted within 3 business days.

    Clause 4.1 Exemption Thresholds
    Individual accounts holding less than $50,000 equivalent are exempt from early liquidation fees.

    Article 5 Compliance Escalation
    Any dispute regarding classification must be escalated to the Regional Compliance Desk.
    """
    chunks = chunk_page_text_by_clause(sample_text, page_number=3)
    assert len(chunks) >= 3

    clause_ids = [c["clause_id"] for c in chunks]
    assert any("Section 3.1.2" in cid for cid in clause_ids)
    assert any("Clause 4.1" in cid for cid in clause_ids)
    assert any("Article 5" in cid for cid in clause_ids)

def test_long_clause_fallback_overlap():
    """Verifies that clauses exceeding max_tokens are split with overlapping windows."""
    long_clause_body = "word " * 600
    long_text = f"Section 8.0 Extended Statutory Directive\n{long_clause_body}"
    chunks = chunk_page_text_by_clause(long_text, page_number=1, max_tokens=200, overlap_tokens=20)

    assert len(chunks) > 1
    assert "Section 8.0" in chunks[0]["clause_id"]
    assert "Part 2" in chunks[1]["clause_id"]

def test_document_upload_and_indexing(client: TestClient):
    """Tests POST /api/v1/documents/upload indexing text and generating vector chunks."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
    sample_content = b"""
    Section 1.0 Scope of Wealth Advisory
    This policy governs all active discretionary portfolio mandates for domestic private accounts.

    Section 2.1 Fee Structure
    Management fees for Level-A portfolios are capped at 0.75% per annum.
    """
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Wealth_Policy_v4.txt", sample_content, "text/plain")},
        data={
            "doc_type": "policy_manual",
            "version": "v4.2",
            "effective_date": "2024-01-15",
            "is_discontinued": "false",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "INDEXED"
    assert data["chunks_created"] >= 2
    assert data["account_id"] == "branch_12_central"
    assert data["version"] == "v4.2"

def test_list_documents_tenant_isolation(client: TestClient):
    """Tests that documents listed belong strictly to the authenticated user's account_id."""
    token_central = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
    token_north = get_auth_token(client, "north_rm@wealth.bank.com", "NorthPassword123!")

    # Central upload
    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_central}"},
        files={"file": ("Central_Circular.txt", b"Section 1 Central branch guidance", "text/plain")},
        data={"doc_type": "tax_circular", "version": "v1.0", "effective_date": "2024-02-01"},
    )

    # North upload
    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_north}"},
        files={"file": ("North_Circular.txt", b"Section 1 North branch guidance", "text/plain")},
        data={"doc_type": "tax_circular", "version": "v1.0", "effective_date": "2024-02-01"},
    )

    # Central lists documents
    res_central = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_central}"})
    assert res_central.status_code == 200
    docs_central = res_central.json()["documents"]
    assert len(docs_central) == 1
    assert docs_central[0]["filename"] == "Central_Circular.txt"
    assert docs_central[0]["account_id"] == "branch_12_central"

    # North lists documents
    res_north = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_north}"})
    assert res_north.status_code == 200
    docs_north = res_north.json()["documents"]
    assert len(docs_north) == 1
    assert docs_north[0]["filename"] == "North_Circular.txt"
    assert docs_north[0]["account_id"] == "branch_01_north"

def test_cumulative_vector_storage(client: TestClient):
    """Verifies that uploads across different days/batches accumulate permanently."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

    # Upload Day 1 Doc
    res1 = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Day1_Policy.txt", b"Section 1.0 Day 1 Rule on Equities.", "text/plain")},
        data={"doc_type": "policy_manual", "version": "v1.0", "effective_date": "2024-01-01"},
    )
    chunks_doc1 = res1.json()["chunks_created"]

    # Upload Day 2 Doc
    res2 = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Day2_Circular.txt", b"Section 2.0 Day 2 Rule on Fixed Income.", "text/plain")},
        data={"doc_type": "tax_circular", "version": "v2.0", "effective_date": "2024-01-02"},
    )
    chunks_doc2 = res2.json()["chunks_created"]

    # Assert cumulative count in vector database
    total_stored = vector_store.count_chunks_for_account("branch_12_central")
    assert total_stored == chunks_doc1 + chunks_doc2

    # Query vector store and verify both documents are retrievable
    query_vec = embedding_service.get_embedding("Day 1 Rule on Equities")
    results = vector_store.search(query_vec, account_id="branch_12_central", top_k=10)
    retrieved_doc_names = [r["metadata"]["document_name"] for r in results]
    assert "Day1_Policy.txt" in retrieved_doc_names

def test_discontinued_product_filtering(client: TestClient):
    """Verifies that chunks tagged with is_discontinued=True are excluded from default search."""
    token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")

    # Upload Active Product
    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Active_Product.txt", b"Section 1 High Growth Fund details.", "text/plain")},
        data={"doc_type": "product_brochure", "version": "v1.0", "effective_date": "2024-01-01", "is_discontinued": "false"},
    )

    # Upload Discontinued Product
    client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("Sunset_Product.txt", b"Section 1 Legacy Sunset Fund details.", "text/plain")},
        data={"doc_type": "product_brochure", "version": "v0.9", "effective_date": "2020-01-01", "is_discontinued": "true"},
    )

    query_vec = embedding_service.get_embedding("Sunset Fund details")

    # Default search (include_discontinued = False)
    default_results = vector_store.search(query_vec, account_id="branch_12_central", include_discontinued=False)
    default_doc_names = [r["metadata"]["document_name"] for r in default_results]
    assert "Sunset_Product.txt" not in default_doc_names

    # Archival search (include_discontinued = True)
    archival_results = vector_store.search(query_vec, account_id="branch_12_central", include_discontinued=True)
    archival_doc_names = [r["metadata"]["document_name"] for r in archival_results]
    assert "Sunset_Product.txt" in archival_doc_names

def test_delete_document_rbac(client: TestClient):
    """Verifies that only ComplianceAdmin can delete a document and purge vector chunks."""
    rm_token = get_auth_token(client, "rm_test@wealth.bank.com", "TestPassword123!")
    admin_token = get_auth_token(client, "comp_test@wealth.bank.com", "AdminPassword123!")

    # Upload document
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {rm_token}"},
        files={"file": ("Temp_Circular.txt", b"Section 1 Temporary Circular", "text/plain")},
        data={"doc_type": "tax_circular", "version": "v1.0", "effective_date": "2024-01-01"},
    )
    doc_id = upload_res.json()["document_id"]

    # RM tries to delete -> 403 Forbidden
    rm_delete = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {rm_token}"})
    assert rm_delete.status_code == 403

    # Admin deletes -> 200 OK
    admin_delete = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_delete.status_code == 200
    assert admin_delete.json()["status"] == "deleted"

    # Verify document is gone from list
    list_res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {rm_token}"})
    assert len(list_res.json()["documents"]) == 0
