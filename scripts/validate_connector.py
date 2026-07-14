#!/usr/bin/env python3
"""Validate the GitHub-publishable connector skeleton."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "CHARTER.md",
    "BOUNDARIES.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "pyproject.toml",
    ".env.example",
    ".gitignore",
    "scripts/verify_agent_install_route.py",
    "scripts/validate_local_stats_port.py",
    ".connector-state/AGENTS.md",
    ".connector-state/README.md",
    "connector/SOURCE_POLICY.md",
    "connector/STORAGE_POLICY.md",
    "connector/profiles/starter.yaml",
    "connector/profiles/focused-device.yaml",
    "connector/profiles/xiaomi-13t.yaml",
    "connector/profiles/redmi-note-10-pro.yaml",
    "connector/profiles/full-public.yaml",
    "connector/profiles/xiaomi_13t_information_needs.json",
    "connector/seeds/starter_topics.yaml",
    "connector/seeds/xiaomi_13t_topics.yaml",
    "connector/seeds/reviews/xiaomi_13t_discovery_review.json",
    "connector/seeds/redmi_note_10_pro_topics.yaml",
    "connector/seeds/forum_sections.yaml",
    "connector/manifests/connector_manifest.yaml",
    "connector/manifests/artifact_classes.yaml",
    "connector/manifests/route_allowlist.yaml",
    "evals/PORT.yaml",
    "stats/AGENTS.md",
    "stats/README.md",
    "stats/port.manifest.json",
    "stats/packets/xiaomi-13t-deep-information-need-eval-route-ratio.reference.json",
    "evals/suites/starter_answer_packets.json",
    "evals/suites/starter_claim_answer_packets.json",
    "evals/suites/starter_claim_conflict_relations.json",
    "evals/suites/starter_graph_relations.json",
    "evals/suites/starter_graph_query_packets.json",
    "evals/suites/starter_hybrid_query_packets.json",
    "evals/suites/starter_search_quality.json",
    "evals/suites/live_starter_search_quality.json",
    "evals/suites/live_xiaomi_13t_search_quality.json",
    "evals/suites/live_xiaomi_13t_ranking_pressure.json",
    "evals/suites/live_xiaomi_13t_hybrid_query_quality.json",
    "evals/suites/live_xiaomi_13t_graph_query_quality.json",
    "evals/suites/live_xiaomi_13t_answer_quality.json",
    "evals/suites/live_redmi_note_10_pro_search_quality.json",
    "evals/suites/xiaomi_13t_graph_relations.json",
    "evals/suites/xiaomi_13t_answer_packets.json",
    "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
    "docs/ARCHITECTURE.md",
    "docs/INSTALL.md",
    "docs/AGENT_INSTALL_ROUTE.md",
    "docs/EXTERNAL_STORAGE.md",
    "docs/CONNECTOR_READY.md",
    "docs/DISCOVERY.md",
    "docs/SEED_REVIEW.md",
    "docs/COVERAGE.md",
    "docs/REFRESH.md",
    "docs/RUNTIME_CONTRACT.md",
    "docs/MCP_ROLLOUT.md",
    "docs/STARTER_PROOF.md",
    "docs/QUERY_MODEL.md",
    "docs/GRAPH_MODEL.md",
    "docs/OPERATIONS.md",
    "docs/LIMITS_AND_ETHICS.md",
    "docs/decisions/README.md",
    ".github/workflows/validate.yml",
    "kag/AGENTS.md",
    "kag/README.md",
    "kag/manifest.json",
    "kag/nodes/source_home.json",
    "kag/nodes/storage_boundary.json",
    "kag/edges/source_routes_to_storage_boundary.json",
    "kag/indexes/source_inventory.json",
    "kag/indexes/source_surface_index.json",
    "kag/projections/source_return.json",
    "kag/receipts/validation_receipt.json",
    "src/aoa_4pda_connector/cli.py",
]

REQUIRED_DIRS = [
    ".connector-state",
    ".connector-state/data",
    ".connector-state/cache",
    ".connector-state/artifacts",
    "src/aoa_4pda_connector/fetch",
    "src/aoa_4pda_connector/parse",
    "src/aoa_4pda_connector/normalize",
    "src/aoa_4pda_connector/chunk",
    "src/aoa_4pda_connector/index",
    "src/aoa_4pda_connector/vector",
    "src/aoa_4pda_connector/graph",
    "src/aoa_4pda_connector/answer",
    "src/aoa_4pda_connector/query",
    "src/aoa_4pda_connector/readiness",
    "src/aoa_4pda_connector/discovery",
    "src/aoa_4pda_connector/coverage",
    "src/aoa_4pda_connector/refresh",
    "src/aoa_4pda_connector/storage",
    "src/aoa_4pda_connector/export",
    "src/aoa_4pda_connector/serve",
    "src/aoa_4pda_connector/evaluation",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "evals/suites",
    "evals/intake",
    "evals/reports",
    "stats",
    "stats/packets",
    "connector/seeds/reviews",
    "generated",
    "kag",
    "kag/nodes",
    "kag/edges",
    "kag/indexes",
    "kag/projections",
    "kag/receipts",
    ".github/workflows",
]

REQUIRED_SCHEMAS = [
    "crawl_receipt.schema.json",
    "normalized_topic.schema.json",
    "normalized_post.schema.json",
    "evidence_packet.schema.json",
    "answer_packet.schema.json",
    "materialize_receipt.schema.json",
    "index_manifest.schema.json",
    "vector_manifest.schema.json",
    "vector_index.schema.json",
    "graph_node.schema.json",
    "graph_edge.schema.json",
    "claim.schema.json",
    "claim_relation.schema.json",
    "conflict_report.schema.json",
    "freshness_report.schema.json",
    "applicability_report.schema.json",
    "warning_report.schema.json",
]

REQUIRED_GITIGNORE = [
    ".connector-state/",
    ".connector-state/**",
    "!.connector-state/README.md",
    "!.connector-state/AGENTS.md",
    "!.connector-state/**/.gitkeep",
    "data/",
    "cache/",
    "artifacts/",
    "raw/",
    "indexes/",
    "vectors/",
    "graphs/",
    "exports/full/",
    "*.sqlite",
    "*.sqlite3",
    "*.parquet",
    "*.qdrant/",
    "*.lancedb/",
]

FORBIDDEN_HEAVY_ROOTS = [
    "data",
    "cache",
    "artifacts",
    "raw",
    "indexes",
    "vectors",
    "graphs",
    "exports/full",
]

FORBIDDEN_ARTIFACT_DIR_NAMES = {
    "data",
    "cache",
    "artifacts",
    "raw",
    "indexes",
    "vectors",
    "graphs",
}

FORBIDDEN_ARTIFACT_FILE_SUFFIXES = {".sqlite", ".sqlite3", ".parquet"}
FORBIDDEN_ARTIFACT_DIR_SUFFIXES = {".qdrant", ".lancedb"}

IGNORED_LOCAL_CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
}

ALLOWED_REPO_LOCAL_STATE_ROOT = ".connector-state"
ALLOWED_KAG_RECORD_DIRS = {("kag", "indexes")}

SHELL_FENCE_LANGUAGES = {
    "bash",
    "cmd",
    "console",
    "powershell",
    "pwsh",
    "sh",
    "shell",
    "zsh",
}
COMMAND_LINE = re.compile(
    r"^\s*(?:[$>]\s*)?(?:aoa(?:-[a-z0-9-]+)?|cd|curl|docker|export|git|make|nox|pip|podman|pytest|python3?|systemctl|tox|uv|wget)\b",
    re.IGNORECASE,
)
MARKDOWN_SCAN_EXCLUDES = {".deps", ".git", ".pytest_cache", "archive", "legacy"}


def _is_allowed_kag_record_path(path: Path, rel_parts: tuple[str, ...]) -> bool:
    if len(rel_parts) == 2 and tuple(rel_parts) in ALLOWED_KAG_RECORD_DIRS:
        return True
    return (
        len(rel_parts) == 3
        and tuple(rel_parts[:2]) in ALLOWED_KAG_RECORD_DIRS
        and path.is_file()
        and path.suffix == ".json"
    )


def _forbidden_artifact_path_error(repo_root: Path, path: Path) -> str | None:
    if ".git" in path.parts:
        return None
    rel_path = path.relative_to(repo_root)
    rel_parts = rel_path.parts
    if any(part in IGNORED_LOCAL_CACHE_DIR_NAMES for part in rel_parts):
        return None
    if rel_parts and rel_parts[0] == ALLOWED_REPO_LOCAL_STATE_ROOT:
        return None
    if _is_allowed_kag_record_path(path, rel_parts):
        return None
    if path.is_dir() and (
        path.name in FORBIDDEN_ARTIFACT_DIR_NAMES
        or any(path.name.endswith(suffix) for suffix in FORBIDDEN_ARTIFACT_DIR_SUFFIXES)
    ):
        return f"forbidden artifact directory exists inside repository: {rel_path}"
    if path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_FILE_SUFFIXES:
        return f"forbidden artifact file exists inside repository: {rel_path}"
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).is_file():
            errors.append(f"missing required file: {rel}")

    for rel in REQUIRED_DIRS:
        if not (repo_root / rel).is_dir():
            errors.append(f"missing required directory: {rel}")

    schema_dir = repo_root / "connector" / "schemas"
    for name in REQUIRED_SCHEMAS:
        path = schema_dir / name
        if not path.is_file():
            errors.append(f"missing schema: connector/schemas/{name}")
            continue
        _load_json(path, errors)

    for path in [
        *repo_root.glob("connector/fixtures/**/*.json"),
        *repo_root.glob("connector/examples/**/*.json"),
        *repo_root.glob("connector/seeds/reviews/**/*.json"),
        *repo_root.glob("evals/suites/**/*.json"),
        *repo_root.glob("generated/**/*.json"),
        *repo_root.glob("kag/**/*.json"),
        *repo_root.glob("stats/**/*.json"),
    ]:
        _load_json(path, errors)

    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8") if (repo_root / ".gitignore").exists() else ""
    for pattern in REQUIRED_GITIGNORE:
        if pattern not in gitignore:
            errors.append(f".gitignore missing heavy-data pattern: {pattern}")

    for rel in FORBIDDEN_HEAVY_ROOTS:
        path = repo_root / rel
        if path.exists():
            errors.append(f"heavy artifact path exists inside repository: {rel}")

    for path in repo_root.rglob("*"):
        error = _forbidden_artifact_path_error(repo_root, path)
        if error:
            errors.append(error)

    _check_text(repo_root, errors, warnings)
    _check_markdown_command_blocks(repo_root, errors)
    _check_eval_port(repo_root, errors)
    _check_seed_review(repo_root, errors)

    payload = {
        "schema": "aoa_4pda_connector_validation_v1",
        "status": "ok" if not errors else "error",
        "repo_root": str(repo_root),
        "errors": errors,
        "warnings": warnings,
        "checked": {
            "required_files": len(REQUIRED_FILES),
            "required_dirs": len(REQUIRED_DIRS),
            "schemas": len(REQUIRED_SCHEMAS),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


def _load_json(path: Path, errors: list[str]) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json {path}: {exc}")


def _check_markdown_command_blocks(repo_root: Path, errors: list[str]) -> None:
    for path in sorted(repo_root.rglob("*.md")):
        rel = path.relative_to(repo_root)
        if path.name == "AGENTS.md" or any(part in MARKDOWN_SCAN_EXCLUDES for part in rel.parts):
            continue

        lines = path.read_text(encoding="utf-8").splitlines()
        fence_start: int | None = None
        fence_marker = ""
        fence_language = ""
        fence_body: list[str] = []
        for line_number, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            marker = stripped[:3] if stripped.startswith(("```", "~~~")) else ""
            if fence_start is None and marker:
                fence_start = line_number
                fence_marker = marker
                fence_info = stripped[3:].strip()
                fence_language = fence_info.split(maxsplit=1)[0].casefold() if fence_info else ""
                fence_body = []
                continue
            if fence_start is not None and stripped.startswith(fence_marker):
                command_like = fence_language in SHELL_FENCE_LANGUAGES or any(
                    COMMAND_LINE.match(body_line) for body_line in fence_body
                )
                if command_like:
                    errors.append(
                        f"command block outside AGENTS.md: {rel}:{fence_start}-{line_number}"
                    )
                fence_start = None
                fence_marker = ""
                fence_language = ""
                fence_body = []
                continue
            if fence_start is not None:
                fence_body.append(line)

        if fence_start is not None:
            command_like = fence_language in SHELL_FENCE_LANGUAGES or any(
                COMMAND_LINE.match(body_line) for body_line in fence_body
            )
            if command_like:
                errors.append(
                    f"unterminated command block outside AGENTS.md: {rel}:{fence_start}"
                )


def _check_text(repo_root: Path, errors: list[str], warnings: list[str]) -> None:
    source_policy = (repo_root / "connector" / "SOURCE_POLICY.md").read_text(encoding="utf-8")
    route_policy = (repo_root / "connector" / "manifests" / "route_allowlist.yaml").read_text(encoding="utf-8")
    storage_policy = (repo_root / "connector" / "STORAGE_POLICY.md").read_text(encoding="utf-8")
    env_example = (repo_root / ".env.example").read_text(encoding="utf-8")
    ready_doc = (repo_root / "docs" / "CONNECTOR_READY.md").read_text(encoding="utf-8")
    discovery_doc = (repo_root / "docs" / "DISCOVERY.md").read_text(encoding="utf-8")
    seed_review_doc = (repo_root / "docs" / "SEED_REVIEW.md").read_text(encoding="utf-8")
    coverage_doc = (repo_root / "docs" / "COVERAGE.md").read_text(encoding="utf-8")
    refresh_doc = (repo_root / "docs" / "REFRESH.md").read_text(encoding="utf-8")
    runtime_contract = (repo_root / "docs" / "RUNTIME_CONTRACT.md").read_text(encoding="utf-8")
    mcp_rollout = (repo_root / "docs" / "MCP_ROLLOUT.md").read_text(encoding="utf-8")
    install_doc = (repo_root / "docs" / "INSTALL.md").read_text(encoding="utf-8")
    agent_install_doc = (repo_root / "docs" / "AGENT_INSTALL_ROUTE.md").read_text(encoding="utf-8")

    for token in ["act=search", "act=Search", "act=attach", "/forum/dl"]:
        if token not in source_policy or token not in route_policy:
            errors.append(f"policy missing denied token: {token}")

    for var in ["CONNECTOR_DATA_ROOT", "CONNECTOR_CACHE_ROOT", "CONNECTOR_ARTIFACT_ROOT"]:
        if var not in storage_policy or var not in env_example:
            errors.append(f"storage root variable missing from docs/env: {var}")

    for token in [".connector-state", "repo-local", "external storage"]:
        if token not in storage_policy or token not in env_example:
            errors.append(f"repo-local storage token missing from docs/env: {token}")

    for token in [
        "connector-ready-v1",
        "achieved",
        "partial",
        "missing",
        "reference_profile_seed_review_state",
        "reference_profile_coverage_state",
    ]:
        if token not in ready_doc:
            errors.append(f"connector-ready doc missing token: {token}")

    for token in [
        "reference-profile-discovery-v1",
        "missing_run",
        "needs_seed_review",
        "no_new_candidates",
        "covered_seed_window_link_count",
        "review_priority",
    ]:
        if token not in discovery_doc:
            errors.append(f"discovery doc missing token: {token}")

    for token in [
        "reference-profile-seed-review-v1",
        "missing_review",
        "needs_review",
        "reviewed_pending_seed_update",
        "reviewed",
        "accepted_pending_seed_update",
    ]:
        if token not in seed_review_doc:
            errors.append(f"seed review doc missing token: {token}")

    for token in ["reference-profile-coverage-v1", "no_run", "coverage_ready"]:
        if token not in coverage_doc:
            errors.append(f"coverage doc missing token: {token}")

    for token in [
        "information_need_matrix",
        "aoa_4pda_information_need_matrix_v1",
        "deep_information_needs_covered",
        "reference_profile_information_need_coverage",
    ]:
        if token not in coverage_doc and token not in ready_doc:
            errors.append(f"information-need coverage docs missing token: {token}")

    for token in ["reference-profile-refresh-v1", "missing_run", "needs_refresh", "fresh"]:
        if token not in refresh_doc:
            errors.append(f"refresh doc missing token: {token}")

    for token in [
        "abyss-stack",
        "aoa-4pda",
        "JSON",
        "CONNECTOR_DATA_ROOT",
        "CONNECTOR_ARTIFACT_ROOT",
        "aoa_4pda_agent_install_route_verify_v1",
        "docs/MCP_ROLLOUT.md",
        "aoa-4pda-connector-mcp",
    ]:
        if token not in runtime_contract:
            errors.append(f"runtime contract missing token: {token}")

    for token in [
        "aoa-4pda-connector-mcp",
        "CONNECTOR_DATA_ROOT",
        "CONNECTOR_CACHE_ROOT",
        "CONNECTOR_ARTIFACT_ROOT",
        "aoa_4pda_answer_packet_v1",
        "agent_answer",
        "evidence_chain",
        "nuance_report",
        "answer_report",
        "network_touched",
        "read-only",
        "no-network",
        "mcp/services/aoa-4pda-connector-mcp/",
    ]:
        if token not in mcp_rollout:
            errors.append(f"MCP rollout doc missing token: {token}")

    for doc_name, doc_text in [
        ("docs/INSTALL.md", install_doc),
        ("docs/AGENT_INSTALL_ROUTE.md", agent_install_doc),
    ]:
        for owner_ref in ["AGENTS.md", "pyproject.toml", "scripts/verify_agent_install_route.py"]:
            if owner_ref not in doc_text:
                errors.append(f"{doc_name} missing executable owner ref: {owner_ref}")

    for profile in (repo_root / "connector" / "profiles").glob("*.yaml"):
        text = profile.read_text(encoding="utf-8")
        if "network_default: disabled" not in text:
            errors.append(f"profile does not default network to disabled: {profile.name}")

    if "internal search" not in source_policy.lower():
        warnings.append("source policy should mention internal search boundary")


def _check_eval_port(repo_root: Path, errors: list[str]) -> None:
    port = (repo_root / "evals" / "PORT.yaml").read_text(encoding="utf-8")
    required_tokens = [
        "schema_version: local_eval_port_v1",
        "owner_repo: aoa-4pda-connector",
        "proof_owner_repo: aoa-evals",
        "no verdict, scoring, regression, or proof doctrine authority",
    ]
    for token in required_tokens:
        if token not in port:
            errors.append(f"eval port missing boundary token: {token}")

    expected_suites = {
        "starter_search_quality.json": "aoa_4pda_search_eval_suite_v1",
        "starter_graph_relations.json": "aoa_4pda_graph_eval_suite_v1",
        "starter_graph_query_packets.json": "aoa_4pda_graph_query_eval_suite_v1",
        "starter_hybrid_query_packets.json": "aoa_4pda_hybrid_query_eval_suite_v1",
        "starter_answer_packets.json": "aoa_4pda_answer_eval_suite_v1",
        "live_starter_search_quality.json": "aoa_4pda_live_search_eval_suite_v1",
        "live_xiaomi_13t_ranking_pressure.json": "aoa_4pda_live_search_eval_suite_v1",
        "live_xiaomi_13t_hybrid_query_quality.json": "aoa_4pda_live_hybrid_query_eval_suite_v1",
        "live_redmi_note_10_pro_search_quality.json": "aoa_4pda_live_search_eval_suite_v1",
        "xiaomi_13t_answer_packets.json": "aoa_4pda_answer_eval_suite_v1",
        "live_xiaomi_13t_answer_quality.json": "aoa_4pda_live_answer_eval_suite_v1",
    }
    for suite_name, schema in expected_suites.items():
        suite_path = repo_root / "evals" / "suites" / suite_name
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
        if suite.get("schema") != schema:
            errors.append(f"{suite_name} has unexpected schema")
        if suite.get("proof_owner_repo") != "aoa-evals":
            errors.append(f"{suite_name} must keep aoa-evals as proof owner")
        if not suite.get("cases"):
            errors.append(f"{suite_name} must include at least one case")
        if suite_name == "starter_graph_relations.json":
            first_case = suite.get("cases", [{}])[0]
            expect = first_case.get("expect", {})
            if not expect.get("relation_edges"):
                errors.append("starter_graph_relations.json must include relation_edges expectations")
        if suite_name == "starter_graph_query_packets.json":
            first_case = suite.get("cases", [{}])[0]
            expect = first_case.get("expect", {})
            if not expect.get("relation_edges"):
                errors.append("starter_graph_query_packets.json must include relation_edges expectations")
        if suite_name == "starter_hybrid_query_packets.json":
            first_case = suite.get("cases", [{}])[0]
            expect = first_case.get("expect", {})
            if expect.get("query_report_algorithm") != "hybrid_bm25_vector_graph_v1":
                errors.append("starter_hybrid_query_packets.json must constrain the hybrid algorithm")
            if not expect.get("top_post_id"):
                errors.append("starter_hybrid_query_packets.json must name the expected top post")
        if suite_name == "starter_answer_packets.json":
            first_case = suite.get("cases", [{}])[0]
            expect = first_case.get("expect", {})
            if not expect.get("fix_labels") or not expect.get("answer_text_contains"):
                errors.append("starter_answer_packets.json must include answer label/text expectations")
        if suite_name == "xiaomi_13t_answer_packets.json":
            first_case = suite.get("cases", [{}])[0]
            expect = first_case.get("expect", {})
            if not expect.get("root_action_labels") or not expect.get("recovery_action_labels"):
                errors.append("xiaomi_13t_answer_packets.json must include root/recovery answer expectations")
        if suite_name == "live_xiaomi_13t_ranking_pressure.json":
            cases = suite.get("cases", [])
            if len(cases) < 4:
                errors.append("live_xiaomi_13t_ranking_pressure.json must include at least four pressure cases")
            if not any("OrangeFox" in str(case.get("query", "")) for case in cases):
                errors.append("live_xiaomi_13t_ranking_pressure.json must include OrangeFox/TWRP pressure")
            if not all(case.get("expect", {}).get("expected_result_rank_max") for case in cases):
                errors.append("live_xiaomi_13t_ranking_pressure.json must constrain expected result rank")
            if not all(case.get("expect", {}).get("expected_result_post_id") for case in cases):
                errors.append("live_xiaomi_13t_ranking_pressure.json must name expected result posts")
        if suite_name == "live_xiaomi_13t_hybrid_query_quality.json":
            cases = suite.get("cases", [])
            if len(cases) < 3:
                errors.append("live_xiaomi_13t_hybrid_query_quality.json must include at least three cases")
            if not all(case.get("expect", {}).get("query_report_algorithm") == "hybrid_bm25_vector_graph_v1" for case in cases):
                errors.append("live_xiaomi_13t_hybrid_query_quality.json must constrain the hybrid algorithm")
            if not any(case.get("expect", {}).get("top_vector_score_present") is True for case in cases):
                errors.append("live_xiaomi_13t_hybrid_query_quality.json must check top vector participation")
            if not any(case.get("expect", {}).get("top_graph_score_present") is True for case in cases):
                errors.append("live_xiaomi_13t_hybrid_query_quality.json must check top graph participation")
            if not any(case.get("expect", {}).get("expected_result_rank_max") for case in cases):
                errors.append("live_xiaomi_13t_hybrid_query_quality.json must include recall-pressure rank coverage")
        if suite_name == "live_redmi_note_10_pro_search_quality.json":
            cases = suite.get("cases", [])
            dataset = suite.get("dataset", {})
            if dataset.get("expected_profile") != "redmi-note-10-pro":
                errors.append("live_redmi_note_10_pro_search_quality.json must target redmi-note-10-pro")
            if dataset.get("seed_file") != "connector/seeds/redmi_note_10_pro_topics.yaml":
                errors.append("live_redmi_note_10_pro_search_quality.json must name the Redmi seed file")
            if len(cases) < 3:
                errors.append("live_redmi_note_10_pro_search_quality.json must include at least three cases")
            if not any("sweet" in str(case.get("query", "")).casefold() for case in cases):
                errors.append("live_redmi_note_10_pro_search_quality.json must include sweet codename coverage")
            if not any("recovery" in str(case.get("query", "")).casefold() for case in cases):
                errors.append("live_redmi_note_10_pro_search_quality.json must include recovery coverage")
        if suite_name == "live_xiaomi_13t_answer_quality.json":
            cases = suite.get("cases", [])
            first_case = cases[0] if cases else {}
            expect = first_case.get("expect", {})
            if not expect.get("recovery_action_labels") or not expect.get("target_file_labels"):
                errors.append("live_xiaomi_13t_answer_quality.json must include recovery/file answer expectations")
            if len(cases) < 14:
                errors.append("live_xiaomi_13t_answer_quality.json must include at least fourteen focused cases")
            if not any(case.get("expect", {}).get("answer_kind") == "snippet" for case in cases):
                errors.append("live_xiaomi_13t_answer_quality.json must include snippet answer coverage")
            if not any("прош" in str(case.get("query", "")).casefold() for case in cases):
                errors.append("live_xiaomi_13t_answer_quality.json must include a Russian recovery/root query")
            if not any(case.get("expect", {}).get("answer_context_labels_min") for case in cases):
                errors.append("live_xiaomi_13t_answer_quality.json must constrain answer context label count")
            case_ids = {str(case.get("case_id")) for case in cases}
            for case_id in [
                "xiaomi-13t-live-battery-night-drain-answer",
                "xiaomi-13t-live-camera-gcam-config-answer",
                "xiaomi-13t-live-purchase-price-answer",
                "xiaomi-13t-live-firmware-source-answer",
                "xiaomi-13t-live-late-update-reset-answer",
            ]:
                if case_id not in case_ids:
                    errors.append(f"live_xiaomi_13t_answer_quality.json missing information-need case: {case_id}")


def _check_seed_review(repo_root: Path, errors: list[str]) -> None:
    manifest_path = repo_root / "connector" / "seeds" / "reviews" / "xiaomi_13t_discovery_review.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seed_text = (repo_root / "connector" / "seeds" / "xiaomi_13t_topics.yaml").read_text(encoding="utf-8")
    profile_text = (repo_root / "connector" / "profiles" / "xiaomi-13t.yaml").read_text(encoding="utf-8")
    if manifest.get("schema") != "aoa_4pda_discovery_review_manifest_v1":
        errors.append("xiaomi_13t_discovery_review.json has unexpected schema")
    if manifest.get("profile_id") != "xiaomi-13t":
        errors.append("xiaomi_13t_discovery_review.json must target xiaomi-13t")
    policy = manifest.get("policy", {})
    if not isinstance(policy, dict):
        errors.append("xiaomi_13t_discovery_review.json policy must be an object")
    elif policy.get("network_touched") is not False or policy.get("review_is_crawl_permission") is not False:
        errors.append("xiaomi_13t_discovery_review.json must keep review no-network and non-crawl")
    if not manifest.get("rules"):
        errors.append("xiaomi_13t_discovery_review.json must include review rules")
    if not manifest.get("decisions"):
        errors.append("xiaomi_13t_discovery_review.json must include explicit decisions")
    if "max_topics: 23" not in profile_text:
        errors.append("xiaomi-13t profile must include the reviewed seed expansion max_topics")
    if "information_need_matrix: connector/profiles/xiaomi_13t_information_needs.json" not in profile_text:
        errors.append("xiaomi-13t profile must name the information-need matrix")
    if seed_text.count("- id:") < 23:
        errors.append("xiaomi_13t_topics.yaml must include the reviewed seed expansion")
    for token in ["accepted_candidate_count: 48", "accepted_pending_crawl", "xiaomi-13t-firmware-window-7140"]:
        if token not in seed_text:
            errors.append(f"xiaomi_13t_topics.yaml missing reviewed expansion token: {token}")

    matrix_path = repo_root / "connector" / "profiles" / "xiaomi_13t_information_needs.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    if matrix.get("schema") != "aoa_4pda_information_need_matrix_v1":
        errors.append("xiaomi_13t_information_needs.json has unexpected schema")
    if matrix.get("profile_id") != "xiaomi-13t":
        errors.append("xiaomi_13t_information_needs.json must target xiaomi-13t")
    needs = matrix.get("needs", [])
    if not isinstance(needs, list) or len(needs) < 10:
        errors.append("xiaomi_13t_information_needs.json must include at least ten needs")
    else:
        need_ids = {str(need.get("need_id")) for need in needs if isinstance(need, dict)}
        for need_id in [
            "root_boot_image",
            "recovery_fastboot_twrp",
            "battery_power_runtime",
            "camera_quality_issues",
            "firmware_download_source",
        ]:
            if need_id not in need_ids:
                errors.append(f"xiaomi_13t_information_needs.json missing need: {need_id}")
        for need in needs:
            if not isinstance(need, dict):
                continue
            if need.get("required_for_deep_profile") is True and not need.get("eval_cases"):
                errors.append(f"xiaomi_13t_information_needs.json deep need lacks eval route: {need.get('need_id')}")


if __name__ == "__main__":
    sys.exit(main())
