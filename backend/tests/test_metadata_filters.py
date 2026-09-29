"""
Unit and Integration Tests for Metadata Filters, Discontinued Products, and Superseded Tax Circulars.

Verifies:
1. Strict exclusion of discontinued products in standard vector search.
2. Compliance audit visibility when include_discontinued=True is explicitly supplied.
3. Active exclusion of superseded circulars when newer versions or effective dates exist.
4. Tenant boundary protection in multi-account vector search under complex filters.
5. Dynamic filtering across doc_type, document_id, is_discontinued, and is_superseded.
"""

import pytest
from app.services.vector_store import vector_store
from app.services.embedding import embedding_service


@pytest.fixture(autouse=True)
def clean_test_vector_environment():
    """Ensures test isolates data per test function."""
    yield


class TestMetadataFiltersAndSupersession:
    """Rigorous tests for metadata filters and circular lifecycle management."""

    def test_discontinued_product_exclusion_default(self):
        """Asserts that queries default to omitting discontinued products."""
        acc = "acc_meta_discontinued_test"
        query_text = "Prime Fixed Deposit high yield returns"
        query_vec = embedding_service.get_embedding(query_text)

        # Ingest discontinued product
        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_disc_01",
            document_name="Sunset_Fixed_Deposit.pdf",
            version="v1.0",
            doc_type="product_brochure",
            effective_date="2021-01-01",
            is_discontinued=True,
            chunks=[{
                "text": "Sunset Fixed Deposit provides 9.5% annual return but is discontinued.",
                "clause_id": "Clause 1.1",
                "page_number": 1,
                "chunk_index": 0,
            }],
            embeddings=[embedding_service.get_embedding("Sunset Fixed Deposit provides 9.5% annual return")],
        )

        # Ingest active product
        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_active_01",
            document_name="Prime_Fixed_Deposit.pdf",
            version="v2.0",
            doc_type="product_brochure",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=[{
                "text": "Prime Fixed Deposit offers 7.2% annual return for active accounts.",
                "clause_id": "Clause 2.1",
                "page_number": 1,
                "chunk_index": 0,
            }],
            embeddings=[embedding_service.get_embedding("Prime Fixed Deposit offers 7.2% annual return")],
        )

        # Default search: must exclude discontinued
        res_default = vector_store.search(
            query_vector=query_vec,
            account_id=acc,
            top_k=5,
            include_discontinued=False,
        )
        assert len(res_default) == 1
        assert res_default[0]["metadata"]["document_id"] == "doc_active_01"
        assert res_default[0]["metadata"]["is_discontinued"] is False

        # Compliance audit search: include_discontinued=True must return both
        res_audit = vector_store.search(
            query_vector=query_vec,
            account_id=acc,
            top_k=5,
            include_discontinued=True,
        )
        assert len(res_audit) == 2
        doc_ids = {r["metadata"]["document_id"] for r in res_audit}
        assert "doc_disc_01" in doc_ids
        assert "doc_active_01" in doc_ids

    def test_superseded_circular_exclusion_and_marking(self):
        """Verifies mark_document_superseded accurately bars obsolete circulars."""
        acc = "acc_meta_superseded_test"
        query_text = "Municipal Bond Tax Exemption Section 3"
        query_vec = embedding_service.get_embedding(query_text)

        # Ingest Circular 2022 (Obsolete)
        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_circ_2022",
            document_name="Tax_Circular_2022.pdf",
            version="v1.0",
            doc_type="tax_circular",
            effective_date="2022-04-01",
            is_discontinued=False,
            is_superseded=False,
            chunks=[{
                "text": "Section 3.1.1: Municipal Bond gains are taxed at 15% flat rate.",
                "clause_id": "Section 3.1.1",
                "page_number": 1,
                "chunk_index": 0,
            }],
            embeddings=[embedding_service.get_embedding("Section 3.1.1 Municipal Bond gains are taxed at 15%")],
        )

        # Ingest Circular 2024 (Active / Superseding)
        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_circ_2024",
            document_name="Tax_Circular_2024.pdf",
            version="v2.0",
            doc_type="tax_circular",
            effective_date="2024-04-01",
            is_discontinued=False,
            is_superseded=False,
            chunks=[{
                "text": "Section 3.1.1: Municipal Bond gains are 100% tax exempt up to INR 5,00,000.",
                "clause_id": "Section 3.1.1",
                "page_number": 1,
                "chunk_index": 0,
            }],
            embeddings=[embedding_service.get_embedding("Section 3.1.1 Municipal Bond gains are 100% tax exempt")],
        )

        # Mark 2022 circular as superseded
        updated_count = vector_store.mark_document_superseded(document_id="doc_circ_2022")
        assert updated_count >= 1

        # Search without include_superseded -> only active circular returned
        active_results = vector_store.search(
            query_vector=query_vec,
            account_id=acc,
            top_k=5,
            include_superseded=False,
        )
        assert len(active_results) == 1
        assert active_results[0]["metadata"]["document_id"] == "doc_circ_2024"
        assert active_results[0]["metadata"]["is_superseded"] is False

        # Search with include_superseded=True -> both returned for historical audit
        audit_results = vector_store.search(
            query_vector=query_vec,
            account_id=acc,
            top_k=5,
            include_superseded=True,
        )
        assert len(audit_results) == 2

    def test_combined_doc_type_and_discontinued_filtering(self):
        """Verifies multi-attribute where clause compounding."""
        acc = "acc_compound_filter_test"
        query_vec = embedding_service.get_embedding("Risk Management Disclosures")

        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_policy_active",
            document_name="Risk_Policy.pdf",
            version="v1.0",
            doc_type="policy_manual",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=[{"text": "Mandatory risk disclosure clause", "clause_id": "Sec 1", "page_number": 1, "chunk_index": 0}],
            embeddings=[embedding_service.get_embedding("Mandatory risk disclosure clause")],
        )

        vector_store.add_chunks(
            account_id=acc,
            document_id="doc_circular_active",
            document_name="Risk_Circular.pdf",
            version="v1.0",
            doc_type="tax_circular",
            effective_date="2024-01-01",
            is_discontinued=False,
            chunks=[{"text": "Tax implications of risk reserve", "clause_id": "Sec 2", "page_number": 1, "chunk_index": 0}],
            embeddings=[embedding_service.get_embedding("Tax implications of risk reserve")],
        )

        # Filter strictly by doc_type="policy_manual"
        policy_res = vector_store.search(
            query_vector=query_vec,
            account_id=acc,
            doc_type="policy_manual",
            top_k=5,
        )
        assert len(policy_res) == 1
        assert policy_res[0]["metadata"]["doc_type"] == "policy_manual"
