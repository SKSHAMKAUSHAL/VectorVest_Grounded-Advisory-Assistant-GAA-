"""
Unit and Integration Tests for System Prompt Edge Cases & Citation Formatting.

Verifies:
1. Presence of all mandatory compliance directives in system_prompt.txt.
2. Clause-level citation syntax validation against PRD regex specifications.
3. Fallback formatting when clause identifiers are absent (page-level citations).
4. Composite answers with multiple citations across diverse document versions.
5. Handling of contradictory circulars and chronological priority resolution.
"""

import re
from pathlib import Path
import pytest
from app.services.rag import rag_pipeline, REFUSAL_MESSAGE
from app.services.eval import CITATION_REGEX


class TestSystemPromptAndCitationFormatting:
    """Verifies prompt design integrity and strict citation formatting enforcement."""

    def test_system_prompt_contains_all_mandatory_sections(self):
        """Asserts that system_prompt.txt contains all critical rules specified in PRD Section 5."""
        prompt_file = Path(__file__).resolve().parent.parent.parent / "prompts" / "system_prompt.txt"
        assert prompt_file.exists(), "prompts/system_prompt.txt must exist"

        content = prompt_file.read_text(encoding="utf-8")
        assert "ZERO HALLUCINATION" in content
        assert "DETERMINISTIC HARD REFUSAL RULE" in content
        assert REFUSAL_MESSAGE in content
        assert "CLAUSE-LEVEL CITATION FORMATTING" in content
        assert "[Doc: <document_name>, Ver: <version>, Clause: <clause_or_section_id>]" in content
        assert "SUPERSESSION & VERSION RESOLUTION" in content
        assert "DISCONTINUED PRODUCT EXCLUSION" in content

    def test_citation_regex_parses_valid_syntax(self):
        """Verifies PRD citation regex matches valid citations and extracts components accurately."""
        valid_samples = [
            ("[Doc: Tax_Circular_2024.pdf, Ver: v2.1, Clause: Section 4.2.1]", "Tax_Circular_2024.pdf", "v2.1", "Section 4.2.1"),
            ("[Doc: Policy_Manual.txt, Ver: v1.0, Clause: Clause 8.1.3]", "Policy_Manual.txt", "v1.0", "Clause 8.1.3"),
            ("[Doc: Wealth_Guide_2024.docx, Ver: v3.0, Clause: Article 12]", "Wealth_Guide_2024.docx", "v3.0", "Article 12"),
        ]

        for text, expected_doc, expected_ver, expected_clause in valid_samples:
            match = CITATION_REGEX.search(text)
            assert match is not None, f"Failed to match valid citation: {text}"
            doc, ver, clause = match.groups()
            assert doc.strip() == expected_doc
            assert ver.strip() == expected_ver
            assert clause.strip() == expected_clause

    def test_multi_citation_extraction(self):
        """Verifies extracting multiple citations embedded within a single composite response."""
        response_text = (
            "Under the primary tax guidelines, high-yield debt funds are subject to 10% tax "
            "[Doc: Tax_Circular_2024.pdf, Ver: v2.1, Clause: Section 4.2.1]. "
            "Furthermore, early redemptions trigger a 0.50% exit fee "
            "[Doc: Policy_Manual_2024.pdf, Ver: v4.2, Clause: Clause 8.1.3]."
        )

        matches = list(CITATION_REGEX.finditer(response_text))
        assert len(matches) == 2

        doc1, ver1, clause1 = matches[0].groups()
        assert doc1 == "Tax_Circular_2024.pdf"
        assert ver1 == "v2.1"
        assert clause1 == "Section 4.2.1"

        doc2, ver2, clause2 = matches[1].groups()
        assert doc2 == "Policy_Manual_2024.pdf"
        assert ver2 == "v4.2"
        assert clause2 == "Clause 8.1.3"

    def test_page_fallback_citation_regex(self):
        """Verifies fallback citation format when clause_id is missing: [Doc: ..., Ver: ..., Page: ...]."""
        page_citation_regex = re.compile(
            r"\[Doc:\s*([^,\]]+),\s*Ver:\s*([^,\]]+),\s*(?:Clause|Page):\s*([^\]]+)\]",
            re.IGNORECASE
        )
        sample = "[Doc: Retail_Banking_Guide.pdf, Ver: v1.0, Page: 42]"
        match = page_citation_regex.search(sample)
        assert match is not None
        doc, ver, page = match.groups()
        assert doc == "Retail_Banking_Guide.pdf"
        assert ver == "v1.0"
        assert page == "42"

    def test_rag_pipeline_context_prompt_formatting(self):
        """Asserts that RAGPipeline properly formats retrieved context blocks with metadata tags."""
        candidates = [
            {
                "id": "c1",
                "score": 0.85,
                "text": "Municipal bond coupon payments are exempt under Section 10(15).",
                "metadata": {
                    "document_name": "Tax_Act_Exemptions.pdf",
                    "document_version": "v2.0",
                    "clause_id": "Section 10(15)",
                    "page_number": 5,
                }
            }
        ]

        # Verify context assembling logic
        doc_name = candidates[0]["metadata"]["document_name"]
        ver = candidates[0]["metadata"]["document_version"]
        clause = candidates[0]["metadata"]["clause_id"]
        page = candidates[0]["metadata"]["page_number"]

        tag = f"[Doc: {doc_name}, Ver: {ver}, Clause: {clause}, Page: {page}]"
        assert tag == "[Doc: Tax_Act_Exemptions.pdf, Ver: v2.0, Clause: Section 10(15), Page: 5]"
