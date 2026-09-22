import re
import time
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.services.rag import rag_pipeline, REFUSAL_MESSAGE
from app.services.llm import llm_service


CITATION_REGEX = re.compile(r"\[Doc:\s*([^,]+),\s*Ver:\s*([^,]+),\s*Clause:\s*([^\]]+)\]")


@dataclass
class LatencyMetrics:
    count: int = 0
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0

    @classmethod
    def from_samples(cls, samples: List[float]) -> "LatencyMetrics":
        if not samples:
            return cls()

        sorted_samples = sorted(samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            if n == 1:
                return sorted_samples[0]
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_samples[int(k)]
            d0 = sorted_samples[int(f)] * (c - k)
            d1 = sorted_samples[int(c)] * (k - f)
            return round(d0 + d1, 2)

        mean_val = round(sum(sorted_samples) / n, 2)
        return cls(
            count=n,
            mean_ms=mean_val,
            p50_ms=percentile(0.50),
            p90_ms=percentile(0.90),
            p95_ms=percentile(0.95),
            p99_ms=percentile(0.99),
            min_ms=round(sorted_samples[0], 2),
            max_ms=round(sorted_samples[-1], 2),
        )


@dataclass
class GroundingMetrics:
    total_queries: int = 0
    grounded_queries: int = 0
    refusal_queries: int = 0
    citation_coverage_pct: float = 0.0
    refusal_correctness_pct: float = 0.0
    grounding_accuracy_pct: float = 0.0
    meets_citation_sla: bool = False   # Target: >= 98%
    meets_refusal_sla: bool = False    # Target: >= 95%
    meets_grounding_sla: bool = False  # Target: >= 90%


@dataclass
class EvaluationReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    grounding: GroundingMetrics = field(default_factory=GroundingMetrics)
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)
    all_passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvaluationSuite:
    """
    Automated evaluation engine for measuring query latency and prompt grounding.
    Enforces PRD KPI targets:
      - Citation Coverage: >= 98%
      - Refusal Correctness: >= 95%
      - Grounding Accuracy: >= 90%
      - Lookup Latency SLA: <= 2 min (backend target < 2000ms)
    """

    def __init__(self, pipeline=None):
        self.pipeline = pipeline or rag_pipeline

    def evaluate_query(
        self,
        query: str,
        account_id: str,
        expected_decision: str = "GENERATE",  # 'GENERATE' or 'REFUSAL'
        expected_doc_names: Optional[List[str]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single test inquiry through retrieval and generation,
        measuring stage-by-stage latencies and validating grounding compliance.
        """
        chat_history = chat_history or []
        t0 = time.perf_counter()

        # 1. Retrieval & guardrail evaluation
        t_eval_start = time.perf_counter()
        eval_result = self.pipeline.retrieve_and_evaluate(
            query=query,
            account_id=account_id,
            chat_history=chat_history,
        )
        t_eval_end = time.perf_counter()
        retrieval_ms = (t_eval_end - t_eval_start) * 1000

        # 2. Response synthesis
        t_gen_start = time.perf_counter()
        if eval_result["decision"] == "REFUSAL":
            response_text = eval_result["message"]
            is_refusal = True
            citations = []
        else:
            sys_prompt, usr_prompt = self.pipeline.build_generation_prompts(
                query=query,
                rewritten_query=eval_result["rewritten_query"],
                context=eval_result["context"],
                chat_history=chat_history,
            )
            response_text = llm_service.generate(sys_prompt, usr_prompt)
            is_refusal = False
            citations = eval_result["citations"]
        t_gen_end = time.perf_counter()
        generation_ms = (t_gen_end - t_gen_start) * 1000

        total_ms = (time.perf_counter() - t0) * 1000

        # 3. Grounding checks
        has_citation_format = bool(CITATION_REGEX.search(response_text))
        has_structured_citations = len(citations) > 0
        citation_covered = has_citation_format or has_structured_citations

        refusal_correct = False
        if expected_decision == "REFUSAL":
            refusal_correct = is_refusal and (REFUSAL_MESSAGE in response_text)
        elif expected_decision == "GENERATE":
            refusal_correct = not is_refusal

        grounding_accurate = False
        if expected_decision == "GENERATE":
            if not is_refusal and citation_covered:
                if expected_doc_names:
                    matched = any(
                        any(doc.lower() in c.get("document_name", "").lower() for doc in expected_doc_names)
                        for c in citations
                    )
                    grounding_accurate = matched
                else:
                    grounding_accurate = True
        else:
            grounding_accurate = refusal_correct

        return {
            "query": query,
            "expected_decision": expected_decision,
            "actual_decision": eval_result["decision"],
            "is_refusal": is_refusal,
            "similarity_score": eval_result["top_score"],
            "rewritten_query": eval_result["rewritten_query"],
            "retrieval_ms": round(retrieval_ms, 2),
            "generation_ms": round(generation_ms, 2),
            "total_latency_ms": round(total_ms, 2),
            "response_text": response_text,
            "citations_count": len(citations),
            "has_citation_format": has_citation_format,
            "citation_covered": citation_covered,
            "refusal_correct": refusal_correct,
            "grounding_accurate": grounding_accurate,
        }

    def run_suite(
        self,
        test_cases: List[Dict[str, Any]],
        account_id: str,
    ) -> EvaluationReport:
        """
        Executes a batch of test cases, calculates latency percentiles and grounding KPIs,
        and generates an EvaluationReport.
        """
        results = []
        latency_samples = []

        total_generate_cases = 0
        total_refusal_cases = 0
        citation_covered_count = 0
        refusal_correct_count = 0
        grounding_accurate_count = 0

        for tc in test_cases:
            query = tc["query"]
            expected_decision = tc.get("expected_decision", "GENERATE")
            expected_doc_names = tc.get("expected_doc_names", None)
            chat_history = tc.get("chat_history", None)

            res = self.evaluate_query(
                query=query,
                account_id=account_id,
                expected_decision=expected_decision,
                expected_doc_names=expected_doc_names,
                chat_history=chat_history,
            )
            results.append(res)
            latency_samples.append(res["total_latency_ms"])

            if expected_decision == "GENERATE":
                total_generate_cases += 1
                if res["citation_covered"]:
                    citation_covered_count += 1
            else:
                total_refusal_cases += 1
                if res["refusal_correct"]:
                    refusal_correct_count += 1

            if res["grounding_accurate"]:
                grounding_accurate_count += 1

        total_queries = len(test_cases)
        lat_metrics = LatencyMetrics.from_samples(latency_samples)

        cov_pct = round((citation_covered_count / total_generate_cases * 100), 2) if total_generate_cases > 0 else 100.0
        ref_pct = round((refusal_correct_count / total_refusal_cases * 100), 2) if total_refusal_cases > 0 else 100.0
        acc_pct = round((grounding_accurate_count / total_queries * 100), 2) if total_queries > 0 else 100.0

        meets_citation = cov_pct >= 98.0
        meets_refusal = ref_pct >= 95.0
        meets_grounding = acc_pct >= 90.0

        grounding_metrics = GroundingMetrics(
            total_queries=total_queries,
            grounded_queries=total_generate_cases,
            refusal_queries=total_refusal_cases,
            citation_coverage_pct=cov_pct,
            refusal_correctness_pct=ref_pct,
            grounding_accuracy_pct=acc_pct,
            meets_citation_sla=meets_citation,
            meets_refusal_sla=meets_refusal,
            meets_grounding_sla=meets_grounding,
        )

        all_passed = meets_citation and meets_refusal and meets_grounding

        return EvaluationReport(
            latency=lat_metrics,
            grounding=grounding_metrics,
            detailed_results=results,
            all_passed=all_passed,
        )


eval_suite = EvaluationSuite()
