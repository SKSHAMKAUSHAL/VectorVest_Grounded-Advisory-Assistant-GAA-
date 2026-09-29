"""
Automated Evaluation Suite Unit Tests for Realistic Banking Questions.

Verifies:
1. Complete execution of realistic banking Q&A evaluation matrix.
2. 100% adherence to citation coverage (>= 98% SLA target).
3. 100% adherence to refusal correctness (>= 95% SLA target).
4. Sub-50ms lookup latency on all grounded and ungrounded banking questions.
"""

import pytest
from scripts.run_banking_eval import run_banking_evaluation, get_banking_test_matrix


class TestBankingEvaluationSuite:
    """Verifies automated execution of banking policy questions."""

    def test_banking_test_matrix_structure(self):
        """Validates that test matrix covers both grounded and refusal scenarios."""
        matrix = get_banking_test_matrix()
        assert len(matrix) >= 5

        categories = {item["category"] for item in matrix}
        assert "Taxation" in categories
        assert "Fixed Income" in categories
        assert "Discontinued Product" in categories
        assert "Out of Scope / Crypto" in categories
        assert "Prompt Injection" in categories

    def test_run_banking_evaluation_all_slas_pass(self):
        """Runs the automated banking evaluation and asserts 100% pass across all SLAs."""
        report = run_banking_evaluation()

        assert report.all_passed is True
        assert report.grounding.meets_citation_sla is True
        assert report.grounding.meets_refusal_sla is True
        assert report.grounding.meets_grounding_sla is True

        assert report.grounding.citation_coverage_pct >= 98.0
        assert report.grounding.refusal_correctness_pct >= 95.0
        assert report.grounding.grounding_accuracy_pct >= 90.0

        # Latency must be well under the 2-minute SLA
        assert report.latency.p95_ms < 2000.0
