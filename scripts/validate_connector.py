#!/usr/bin/env python3
"""Validate the GitHub-publishable connector skeleton."""

from __future__ import annotations

import json
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
    "connector/SOURCE_POLICY.md",
    "connector/STORAGE_POLICY.md",
    "connector/profiles/starter.yaml",
    "connector/profiles/focused-device.yaml",
    "connector/profiles/full-public.yaml",
    "connector/seeds/starter_topics.yaml",
    "connector/seeds/forum_sections.yaml",
    "connector/manifests/connector_manifest.yaml",
    "connector/manifests/artifact_classes.yaml",
    "connector/manifests/route_allowlist.yaml",
    "evals/PORT.yaml",
    "evals/suites/starter_graph_relations.json",
    "evals/suites/starter_search_quality.json",
    "docs/ARCHITECTURE.md",
    "docs/INSTALL.md",
    "docs/AGENT_INSTALL_ROUTE.md",
    "docs/EXTERNAL_STORAGE.md",
    "docs/STARTER_PROOF.md",
    "docs/QUERY_MODEL.md",
    "docs/GRAPH_MODEL.md",
    "docs/OPERATIONS.md",
    "docs/LIMITS_AND_ETHICS.md",
    "docs/decisions/README.md",
    ".github/workflows/validate.yml",
    "src/aoa_4pda_connector/cli.py",
]

REQUIRED_DIRS = [
    "src/aoa_4pda_connector/fetch",
    "src/aoa_4pda_connector/parse",
    "src/aoa_4pda_connector/normalize",
    "src/aoa_4pda_connector/chunk",
    "src/aoa_4pda_connector/index",
    "src/aoa_4pda_connector/graph",
    "src/aoa_4pda_connector/query",
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
    "generated",
    ".github/workflows",
]

REQUIRED_SCHEMAS = [
    "crawl_receipt.schema.json",
    "normalized_topic.schema.json",
    "normalized_post.schema.json",
    "evidence_packet.schema.json",
    "index_manifest.schema.json",
    "graph_node.schema.json",
    "graph_edge.schema.json",
]

REQUIRED_GITIGNORE = [
    "data/",
    "cache/",
    "artifacts/",
    "raw/",
    "indexes/",
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
    "graphs",
    "exports/full",
]

FORBIDDEN_ARTIFACT_DIR_NAMES = {
    "data",
    "cache",
    "artifacts",
    "raw",
    "indexes",
    "graphs",
}

IGNORED_LOCAL_CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
}


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
        *repo_root.glob("evals/suites/**/*.json"),
        *repo_root.glob("generated/**/*.json"),
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
        if ".git" in path.parts:
            continue
        if any(part in IGNORED_LOCAL_CACHE_DIR_NAMES for part in path.relative_to(repo_root).parts):
            continue
        if path.is_dir() and path.name in FORBIDDEN_ARTIFACT_DIR_NAMES:
            errors.append(f"forbidden artifact directory exists inside repository: {path.relative_to(repo_root)}")

    _check_text(repo_root, errors, warnings)
    _check_eval_port(repo_root, errors)

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


def _check_text(repo_root: Path, errors: list[str], warnings: list[str]) -> None:
    source_policy = (repo_root / "connector" / "SOURCE_POLICY.md").read_text(encoding="utf-8")
    route_policy = (repo_root / "connector" / "manifests" / "route_allowlist.yaml").read_text(encoding="utf-8")
    storage_policy = (repo_root / "connector" / "STORAGE_POLICY.md").read_text(encoding="utf-8")
    env_example = (repo_root / ".env.example").read_text(encoding="utf-8")

    for token in ["act=search", "act=Search", "act=attach", "/forum/dl"]:
        if token not in source_policy or token not in route_policy:
            errors.append(f"policy missing denied token: {token}")

    for var in ["CONNECTOR_DATA_ROOT", "CONNECTOR_CACHE_ROOT", "CONNECTOR_ARTIFACT_ROOT"]:
        if var not in storage_policy or var not in env_example:
            errors.append(f"storage root variable missing from docs/env: {var}")

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


if __name__ == "__main__":
    sys.exit(main())
