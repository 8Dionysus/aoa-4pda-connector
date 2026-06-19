"""Local eval runners for connector-owned retrieval checks."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from aoa_4pda_connector.config import find_repo_root
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.query import query_keyword_index


DEFAULT_SEARCH_EVAL_SUITE = Path("evals/suites/starter_search_quality.json")


def run_search_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe search eval suite without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_SEARCH_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("topic_fixture", ""))))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-search-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalized_dir.mkdir(parents=True)
        fixture_topic = json.loads(fixture_path.read_text(encoding="utf-8"))
        topic_id = str(fixture_topic.get("topic_id", "fixture"))
        shutil.copy2(fixture_path, normalized_dir / f"topic-{topic_id}.json")
        index_path = build_keyword_index(normalized_dir, eval_root / "index", "eval")
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))

        case_reports = [
            _run_case(case, index_path)
            for case in suite.get("cases", [])
        ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_search_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": str(path.relative_to(root)),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def _run_case(case: dict[str, object], index_path: Path) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    packet = query_keyword_index(index_path, query, limit=3)
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    evidence_refs = [str(ref) for ref in top_result.get("evidence_refs", [])]
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": top_result.get("post_id") == expect.get("top_post_id"),
        "top_chunk_ref_prefix": _any_prefix(evidence_refs, str(expect.get("top_chunk_ref_prefix", ""))),
        "matched_terms_any": _any_expected(expect.get("matched_terms_any", []), top_result.get("matched_terms", [])),
        "matched_exact_terms_any": _any_expected(
            expect.get("matched_exact_terms_any", []),
            top_result.get("matched_exact_terms", []),
        ),
        "source_url_contains": str(expect.get("source_url_contains", "")) in str(top_result.get("source_url", "")),
        "query_report_unit": packet.get("query_report", {}).get("unit") == expect.get("query_report_unit"),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "top_result": top_result,
    }


def _resolve_repo_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _any_prefix(values: list[str], prefix: str) -> bool:
    return bool(prefix) and any(value.startswith(prefix) for value in values)


def _any_expected(expected: object, actual: object) -> bool:
    expected_values = {str(item).lower() for item in expected if str(item)}
    actual_values = {str(item).lower() for item in actual}
    return bool(expected_values.intersection(actual_values))
