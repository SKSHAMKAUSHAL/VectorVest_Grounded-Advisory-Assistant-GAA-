"""
Unit and Integration Tests for Retrieval and LLM Latency Profiling.

Verifies:
1. Retrieval latency P95 is strictly under 30ms.
2. Cross-encoder re-ranking latency P95 is strictly under 20ms.
3. End-to-end lookup latency fulfills the PRD SLA (< 2 minutes, local target < 50ms).
4. Profiler percentiles are computed deterministically.
"""

import pytest
from scripts.profile_latency import run_latency_profiling_benchmarks, compute_percentiles


class TestLatencyProfilingAndSLAs:
    """Verifies that system latency adheres to strict production budgets."""

    def test_compute_percentiles_accuracy(self):
        """Validates statistical correctness of the percentile computation."""
        data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        p = compute_percentiles(data)

        assert p["count"] == 10
        assert p["mean_ms"] == 55.0
        assert p["min_ms"] == 10.0
        assert p["max_ms"] == 100.0
        assert p["p50_ms"] >= 50.0
        assert p["p95_ms"] >= 90.0

    def test_retrieval_and_reranking_latency_budgets(self):
        """Runs the profiling benchmark and asserts retrieval and reranking satisfy SLA targets."""
        report = run_latency_profiling_benchmarks(iterations=8)

        # Retrieval SLA check (local budget < 30ms)
        assert report["retrieval"]["p95_ms"] < 30.0, f"Retrieval P95 {report['retrieval']['p95_ms']}ms exceeded 30ms"

        # Re-ranker SLA check (local budget < 20ms)
        assert report["reranker"]["p95_ms"] < 20.0, f"Reranker P95 {report['reranker']['p95_ms']}ms exceeded 20ms"

        # End-to-end lookup SLA check (local budget < 50ms, production SLA < 120,000ms)
        assert report["e2e_lookup"]["p95_ms"] < 50.0, f"E2E P95 {report['e2e_lookup']['p95_ms']}ms exceeded 50ms"
        assert report["e2e_lookup"]["p95_ms"] < report["sla_target_ms"]
