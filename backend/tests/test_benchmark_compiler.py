"""
Unit and Integration Tests for Benchmark Evaluation Report Compiler and Visual Charts.

Verifies:
1. Generation of valid, well-formed SVG latency distribution charts.
2. Generation of valid, well-formed SVG grounding KPI charts.
3. Successful compilation and markdown output in docs/benchmark-report.md.
"""

from pathlib import Path
import pytest
from scripts.compile_benchmark_report import (
    generate_latency_svg,
    generate_grounding_kpi_svg,
    compile_report,
)


class TestBenchmarkReportCompiler:
    """Verifies generation of production benchmark reports and visual performance charts."""

    def test_generate_latency_svg_markup(self):
        """Asserts latency SVG contains valid XML tags, rects, and percentile labels."""
        latency_data = {
            "p50_ms": 12.5,
            "p90_ms": 15.2,
            "p95_ms": 18.0,
            "p99_ms": 22.1,
            "max_ms": 25.0,
        }
        svg = generate_latency_svg(latency_data)

        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "Response Lookup Latency Percentiles" in svg
        assert "P50 (Median)" in svg
        assert "12.50 ms" in svg
        assert "SLA PASS" in svg

    def test_generate_grounding_kpi_svg_markup(self):
        """Asserts grounding KPI SVG contains valid XML tags and KPI metrics."""
        grounding_data = {
            "citation_coverage_pct": 100.0,
            "refusal_correctness_pct": 98.5,
            "grounding_accuracy_pct": 94.0,
        }
        svg = generate_grounding_kpi_svg(grounding_data)

        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "Compliance &amp; Grounding Guardrail KPIs" in svg
        assert "Citation Coverage" in svg
        assert "100.0%" in svg
        assert "Target: &gt;=98% (MET)" in svg


    def test_compile_report_generates_markdown_file(self):
        """Executes compile_report and verifies output exists with all essential report sections."""
        out_path = Path(__file__).resolve().parent.parent.parent / "docs" / "benchmark-report.md"
        report_text = compile_report()

        assert out_path.exists()
        assert "Production Benchmark Evaluation Report" in report_text
        assert "Core KPI Compliance Matrix" in report_text
        assert "Visual Performance Charts" in report_text
        assert "<svg" in report_text
