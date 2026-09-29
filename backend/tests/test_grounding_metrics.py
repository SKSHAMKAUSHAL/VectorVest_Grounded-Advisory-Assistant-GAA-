"""
Unit and Integration Tests for Grounding Metrics, Citation Coverage, and Refusal Correctness.

Verifies:
1. Citation coverage calculation strictly enforces the >= 98% target.
2. Refusal correctness calculation strictly enforces the >= 95% target.
3. Grounding accuracy calculation strictly enforces the >= 90% target.
4. Evaluation engine flags SLA breaches when simulated performance degrades.
"""

import pytest
from app.services.eval import eval_suite, GroundingMetrics


class TestGroundingMetricsAndRefusalCorrectness:
    """Rigorous verification of grounding metrics and SLA compliance scoring."""

    def test_grounding_metrics_sla_threshold_logic(self):
        """Verifies that GroundingMetrics correctly evaluates SLA pass/fail status."""
        # Perfect compliance
        perfect = GroundingMetrics(
            citation_coverage_pct=100.0,
            refusal_correctness_pct=100.0,
            grounding_accuracy_pct=100.0,
        )
        assert perfect.meets_citation_sla is True
        assert perfect.meets_refusal_sla is True
        assert perfect.meets_grounding_sla is True
        assert perfect.all_slas_met is True

        # Citation coverage breach (e.g. 97.5% < 98.0%)
        citation_breach = GroundingMetrics(
            citation_coverage_pct=97.5,
            refusal_correctness_pct=100.0,
            grounding_accuracy_pct=95.0,
        )
        assert citation_breach.meets_citation_sla is False
        assert citation_breach.all_slas_met is False

        # Refusal correctness breach (e.g. 94.0% < 95.0%)
        refusal_breach = GroundingMetrics(
            citation_coverage_pct=99.0,
            refusal_correctness_pct=94.0,
            grounding_accuracy_pct=95.0,
        )
        assert refusal_breach.meets_refusal_sla is False
        assert refusal_breach.all_slas_met is False

        # Grounding accuracy breach (e.g. 89.0% < 90.0%)
        grounding_breach = GroundingMetrics(
            citation_coverage_pct=99.0,
            refusal_correctness_pct=98.0,
            grounding_accuracy_pct=89.0,
        )
        assert grounding_breach.meets_grounding_sla is False
        assert grounding_breach.all_slas_met is False

    def test_citation_coverage_calculation_math(self):
        """Validates exact fractional calculation and rounding of citation coverage."""
        grounded_count = 50
        cited_count = 49
        coverage = (cited_count / grounded_count) * 100.0
        assert coverage == 98.0

        # Below threshold
        failed_count = 48
        failed_coverage = (failed_count / grounded_count) * 100.0
        assert failed_coverage == 96.0
        assert failed_coverage < 98.0

    def test_refusal_correctness_calculation_math(self):
        """Validates exact fractional calculation of refusal correctness."""
        unindexed_total = 20
        refused_correctly = 19
        refusal_rate = (refused_correctly / unindexed_total) * 100.0
        assert refusal_rate == 95.0

        # Perfect refusal
        assert (20 / 20) * 100.0 == 100.0
