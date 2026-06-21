"""Connector-ready maturity audit."""

from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, find_repo_root
from aoa_4pda_connector.storage import storage_status


READY_TARGET = "connector-ready-v1"

REQUIRED_INSTALL_TOKENS = [
    'python -m pip install -e ".[dev]"',
    "python scripts/validate_connector.py",
    "python -m pytest -q",
    "aoa-4pda doctor",
    "aoa-4pda storage status",
    "aoa-4pda proof starter",
    "aoa-4pda materialize fixture",
    "aoa-4pda eval search-quality",
    "aoa-4pda eval graph-relations",
    "aoa-4pda eval graph-query-packets",
    "aoa-4pda eval answer-packets",
]

REQUIRED_STARTER_SURFACES = [
    "connector/fixtures/normalized/synthetic_topic.json",
    "connector/fixtures/html/live_shape_topic.html",
    "evals/suites/starter_search_quality.json",
    "evals/suites/starter_graph_relations.json",
    "evals/suites/starter_graph_query_packets.json",
    "evals/suites/starter_answer_packets.json",
]

REQUIRED_FOCUSED_SURFACES = [
    "connector/profiles/xiaomi-13t.yaml",
    "connector/seeds/xiaomi_13t_topics.yaml",
    "evals/suites/live_xiaomi_13t_search_quality.json",
    "evals/suites/live_xiaomi_13t_ranking_pressure.json",
    "evals/suites/live_xiaomi_13t_graph_query_quality.json",
    "evals/suites/live_xiaomi_13t_answer_quality.json",
    "evals/suites/xiaomi_13t_graph_relations.json",
    "evals/suites/xiaomi_13t_answer_packets.json",
]

REQUIRED_HEAVY_PATTERNS = [
    ".connector-state/",
    ".connector-state/**",
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


def audit_connector_ready(
    repo_root: Path | None = None,
    roots: StorageRoots | None = None,
    *,
    run: str = "latest",
) -> dict[str, object]:
    """Return a local maturity audit for the connector-ready target."""

    root = repo_root or find_repo_root()
    storage_roots = roots or StorageRoots.from_env(root)
    criteria = [
        _fresh_clone_install_route(root),
        _offline_starter_gates(root),
        _focused_profile_gate(root, storage_roots, run),
        _next_profile_gate(root),
        _receipt_pipeline_gate(root, storage_roots, run),
        _search_quality_gate(root),
        _graph_quality_gate(root),
        _answer_quality_gate(root),
        _heavy_data_boundary_gate(root),
        _runtime_contract_gate(root),
        _validation_ci_gate(root),
    ]
    counts = {
        "achieved": sum(1 for item in criteria if item["status"] == "achieved"),
        "partial": sum(1 for item in criteria if item["status"] == "partial"),
        "missing": sum(1 for item in criteria if item["status"] == "missing"),
    }
    ready = counts["partial"] == 0 and counts["missing"] == 0
    return {
        "schema": "aoa_4pda_connector_ready_audit_v1",
        "target_status": READY_TARGET,
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "repo_root": str(root),
        "storage_mode": storage_roots.mode,
        "local_state_dir": LOCAL_STATE_DIR,
        "storage_roots": storage_roots.as_dict(),
        "run": run,
        "counts": counts,
        "criteria": criteria,
        "next_actions": [
            item["next_action"]
            for item in criteria
            if item["status"] != "achieved" and item.get("next_action")
        ],
        "network_touched": False,
    }


def _criterion(
    criterion_id: str,
    status: str,
    requirement: str,
    evidence: dict[str, object],
    next_action: str = "",
) -> dict[str, object]:
    return {
        "id": criterion_id,
        "status": status,
        "requirement": requirement,
        "evidence": evidence,
        "next_action": next_action,
    }


def _fresh_clone_install_route(repo_root: Path) -> dict[str, object]:
    install_doc = repo_root / "docs" / "INSTALL.md"
    agent_doc = repo_root / "docs" / "AGENT_INSTALL_ROUTE.md"
    pyproject = repo_root / "pyproject.toml"
    install_text = _read_text(install_doc)
    agent_text = _read_text(agent_doc)
    missing_tokens = [
        token
        for token in REQUIRED_INSTALL_TOKENS
        if token not in install_text or token not in agent_text
    ]
    pyproject_text = _read_text(pyproject)
    script_declared = 'aoa-4pda = "aoa_4pda_connector.cli:main"' in pyproject_text
    status = "achieved" if not missing_tokens and script_declared else "missing"
    return _criterion(
        "fresh_clone_install_route",
        status,
        "Fresh clone install route is documented and exposes the aoa-4pda CLI entrypoint.",
        {
            "install_doc": _exists(install_doc),
            "agent_install_doc": _exists(agent_doc),
            "missing_install_tokens": missing_tokens,
            "cli_entrypoint_declared": script_declared,
        },
        "Align docs/INSTALL.md and docs/AGENT_INSTALL_ROUTE.md with the fresh-clone command set.",
    )


def _offline_starter_gates(repo_root: Path) -> dict[str, object]:
    missing = _missing_paths(repo_root, REQUIRED_STARTER_SURFACES)
    proof_doc = repo_root / "docs" / "STARTER_PROOF.md"
    proof_doc_mentions = all(
        token in _read_text(proof_doc)
        for token in ["aoa-4pda proof starter", "aoa-4pda materialize fixture", "network_touched: false"]
    )
    status = "achieved" if not missing and proof_doc_mentions else "missing"
    return _criterion(
        "offline_starter_gates",
        status,
        "Doctor, fixture materialization, starter proof, and no-network eval surfaces are present.",
        {
            "missing_surfaces": missing,
            "starter_proof_doc": _exists(proof_doc),
            "starter_proof_doc_mentions_offline_route": proof_doc_mentions,
        },
        "Restore starter fixture/eval surfaces and docs before expanding live routes.",
    )


def _focused_profile_gate(repo_root: Path, roots: StorageRoots, run: str) -> dict[str, object]:
    missing = _missing_paths(repo_root, REQUIRED_FOCUSED_SURFACES)
    receipts = _receipt_chain(roots, run)
    receipt_profile = receipts.get("crawl", {}).get("profile_id")
    receipts_ok = _receipts_share_run(receipts) and receipt_profile == "xiaomi-13t"
    status = "achieved" if not missing and receipts_ok else "partial" if not missing else "missing"
    return _criterion(
        "focused_profile_deep_proven",
        status,
        "At least one focused-device profile is deeply proven by profile docs, suites, and a receipt chain.",
        {
            "profile_id": "xiaomi-13t",
            "missing_surfaces": missing,
            "receipt_run_ids": _receipt_run_ids(receipts),
            "receipt_profile_id": receipt_profile,
            "receipt_chain_present": receipts_ok,
        },
        "Materialize or restore a Xiaomi 13T crawl/normalize/index/graph receipt chain and run focused live gates.",
    )


def _next_profile_gate(repo_root: Path) -> dict[str, object]:
    profile_dir = repo_root / "connector" / "profiles"
    focused_profiles = []
    deferred_profiles = []
    for path in sorted(profile_dir.glob("*.yaml")):
        text = _read_text(path)
        profile_id = _line_value(text, "profile_id")
        if profile_id in {"starter", "focused-device", "xiaomi-13t"}:
            continue
        if "profile_kind: focused-device" in text and "network_default: disabled" in text:
            focused_profiles.append(profile_id or path.stem)
        if "activation_status: deferred" in text and "network_default: disabled" in text:
            deferred_profiles.append(profile_id or path.stem)
    if focused_profiles:
        status = "achieved"
        next_action = ""
    elif deferred_profiles:
        status = "partial"
        next_action = "Prepare a second representative focused-device profile with seed windows and local quality gates."
    else:
        status = "missing"
        next_action = "Add an explicit next representative profile or a reviewed deferred profile route."
    return _criterion(
        "next_representative_profile_prepared",
        status,
        "At least one more representative profile exists or is explicitly prepared as the next profile.",
        {
            "focused_profiles_beyond_xiaomi": focused_profiles,
            "deferred_profiles": deferred_profiles,
            "forum_sections_seed": _exists(repo_root / "connector" / "seeds" / "forum_sections.yaml"),
        },
        next_action,
    )


def _receipt_pipeline_gate(repo_root: Path, roots: StorageRoots, run: str) -> dict[str, object]:
    receipts = _receipt_chain(roots, run)
    chain_ok = _receipts_share_run(receipts)
    artifacts = {
        "index_path_exists": _receipt_path_exists(receipts.get("index", {}), "index_path"),
        "graph_path_exists": _receipt_path_exists(receipts.get("graph", {}), "graph_path"),
    }
    storage = storage_status(repo_root, roots)
    storage_ok = storage.get("status") == "ok"
    policy = receipts.get("crawl", {}).get("policy", {})
    policy_ok = (
        isinstance(policy, dict)
        and policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False
    )
    derived_no_network = all(
        receipts.get(kind, {}).get("network_touched") is False
        for kind in ["normalize", "index", "graph"]
    )
    status = "achieved" if chain_ok and all(artifacts.values()) and storage_ok and policy_ok and derived_no_network else "partial"
    return _criterion(
        "receipt_reproducible_pipeline",
        status,
        "Bounded crawl/normalize/index/graph/query/answer pipeline is reproducible from receipts and storage roots.",
        {
            "storage_status": storage.get("status"),
            "receipt_run_ids": _receipt_run_ids(receipts),
            "artifact_paths": artifacts,
            "public_only_policy_preserved": policy_ok,
            "derived_stages_network_free": derived_no_network,
        },
        "Run or restore crawl -> normalize -> build-index -> build-graph for a bounded profile and keep receipts together.",
    )


def _search_quality_gate(repo_root: Path) -> dict[str, object]:
    search_suite = _load_json(repo_root / "evals" / "suites" / "live_xiaomi_13t_search_quality.json")
    pressure_suite = _load_json(repo_root / "evals" / "suites" / "live_xiaomi_13t_ranking_pressure.json")
    pressure_cases = pressure_suite.get("cases", []) if isinstance(pressure_suite, dict) else []
    docs = _read_text(repo_root / "docs" / "QUERY_MODEL.md")
    ok = (
        isinstance(search_suite, dict)
        and isinstance(pressure_suite, dict)
        and len(pressure_cases) >= 4
        and "BM25" in docs
        and "ranking-pressure" in docs
    )
    return _criterion(
        "search_quality_gates",
        "achieved" if ok else "missing",
        "Search quality covers exact/BM25 technical retrieval and hard rank-pressure cases.",
        {
            "live_search_suite": bool(search_suite),
            "ranking_pressure_case_count": len(pressure_cases),
            "query_model_mentions_bm25": "BM25" in docs,
            "query_model_mentions_ranking_pressure": "ranking-pressure" in docs,
        },
        "Restore live search and ranking-pressure suites with technical retrieval coverage.",
    )


def _graph_quality_gate(repo_root: Path) -> dict[str, object]:
    graph_suite = _load_json(repo_root / "evals" / "suites" / "xiaomi_13t_graph_relations.json")
    live_graph_suite = _load_json(repo_root / "evals" / "suites" / "live_xiaomi_13t_graph_query_quality.json")
    graph_doc = _read_text(repo_root / "docs" / "GRAPH_MODEL.md")
    relation_tokens = [
        "fixes_issue",
        "warns_about",
        "root_targets_file",
        "recovery_targets_file",
        "source refs",
        "confidence",
    ]
    ok = bool(graph_suite) and bool(live_graph_suite) and all(token in graph_doc for token in relation_tokens)
    return _criterion(
        "graph_quality_gates",
        "achieved" if ok else "missing",
        "Graph quality covers issue/fix/warning/root/recovery/tool/file/firmware relations with source refs.",
        {
            "focused_graph_suite": bool(graph_suite),
            "live_graph_query_suite": bool(live_graph_suite),
            "graph_doc_missing_tokens": [token for token in relation_tokens if token not in graph_doc],
        },
        "Restore graph relation docs and suites for both public-safe fixtures and receipt-driven live runs.",
    )


def _answer_quality_gate(repo_root: Path) -> dict[str, object]:
    answer_suite = _load_json(repo_root / "evals" / "suites" / "live_xiaomi_13t_answer_quality.json")
    answer_schema = _load_json(repo_root / "connector" / "schemas" / "answer_packet.schema.json")
    answer_doc = _read_text(repo_root / "docs" / "QUERY_MODEL.md")
    answer_code = _read_text(repo_root / "src" / "aoa_4pda_connector" / "answer" / "__init__.py")
    deterministic = "starter_graph_context_v2" in answer_code and "source_url" in answer_code
    cited = "source_refs" in answer_code and "evidence_refs" in answer_code
    freshness = "freshness" in json.dumps(answer_schema, ensure_ascii=False).casefold() or "freshness" in answer_code.casefold()
    status = "achieved" if answer_suite and deterministic and cited and freshness else "partial"
    return _criterion(
        "answer_quality_gates",
        status,
        "Answer quality returns cited, deterministic, freshness-aware answer packets.",
        {
            "live_answer_suite": bool(answer_suite),
            "deterministic_renderer": deterministic,
            "cited_answer_fields": cited,
            "freshness_field_or_note_present": freshness,
            "answer_contract_mentions_freshness": "freshness note" in answer_doc,
        },
        "Add freshness/capture context to answer packets and protect it with schema/tests/evals.",
    )


def _heavy_data_boundary_gate(repo_root: Path) -> dict[str, object]:
    gitignore = _read_text(repo_root / ".gitignore")
    missing_patterns = [pattern for pattern in REQUIRED_HEAVY_PATTERNS if pattern not in gitignore]
    present_heavy_roots = [path for path in FORBIDDEN_HEAVY_ROOTS if (repo_root / path).exists()]
    status = "achieved" if not missing_patterns and not present_heavy_roots else "missing"
    return _criterion(
        "heavy_data_boundary",
        status,
        "Repo validator protects Git from heavy generated data and large artifacts stay out of Git.",
        {
            "missing_gitignore_patterns": missing_patterns,
            "present_forbidden_heavy_roots": present_heavy_roots,
            "repo_local_state_scaffold": _exists(repo_root / ".connector-state" / "README.md"),
        },
        "Restore heavy-data .gitignore coverage and move generated roots outside tracked repo surfaces.",
    )


def _runtime_contract_gate(repo_root: Path) -> dict[str, object]:
    contract = repo_root / "docs" / "RUNTIME_CONTRACT.md"
    text = _read_text(contract)
    tokens = ["abyss-stack", "aoa-4pda", "JSON", "CONNECTOR_DATA_ROOT", "CONNECTOR_ARTIFACT_ROOT"]
    missing = [token for token in tokens if token not in text]
    status = "achieved" if contract.is_file() and not missing else "missing"
    return _criterion(
        "runtime_api_contract",
        status,
        "Runtime/API contract is documented for future abyss-stack consumption.",
        {
            "contract_doc": _exists(contract),
            "missing_tokens": missing,
        },
        "Document the stable CLI/JSON/storage contract consumed by future abyss-stack runtime adapters.",
    )


def _validation_ci_gate(repo_root: Path) -> dict[str, object]:
    workflow = repo_root / ".github" / "workflows" / "validate.yml"
    validator = repo_root / "scripts" / "validate_connector.py"
    workflow_text = _read_text(workflow)
    validator_text = _read_text(validator)
    local_contract_ok = all(
        token in workflow_text
        for token in ["python scripts/validate_connector.py", "python -m pytest -q"]
    )
    validator_mentions_ready = "docs/CONNECTOR_READY.md" in validator_text and "docs/RUNTIME_CONTRACT.md" in validator_text
    status = "achieved" if workflow.is_file() and local_contract_ok and validator_mentions_ready else "partial"
    return _criterion(
        "validation_and_ci_contract",
        status,
        "Validator, pytest, relevant eval suites, and GitHub CI are wired into the repo route.",
        {
            "workflow": _exists(workflow),
            "workflow_runs_validator": "python scripts/validate_connector.py" in workflow_text,
            "workflow_runs_pytest": "python -m pytest -q" in workflow_text,
            "validator_checks_ready_docs": validator_mentions_ready,
        },
        "Wire connector-ready docs into the validator and confirm GitHub CI during landing.",
    )


def _receipt_chain(roots: StorageRoots, run: str) -> dict[str, dict[str, object]]:
    receipts: dict[str, dict[str, object]] = {}
    if roots.artifact is None:
        return receipts
    receipt_dir = roots.artifact / "receipts"
    for kind in ["crawl", "normalize", "index", "graph"]:
        path = receipt_dir / f"latest_{kind}.json" if run == "latest" else receipt_dir / f"{run}.{kind}.json"
        receipts[kind] = _load_json(path)
    return receipts


def _receipts_share_run(receipts: dict[str, dict[str, object]]) -> bool:
    if set(receipts) != {"crawl", "normalize", "index", "graph"}:
        return False
    run_ids = [value for value in _receipt_run_ids(receipts).values() if value]
    return len(run_ids) == 4 and len(set(run_ids)) == 1


def _receipt_run_ids(receipts: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        kind: receipt.get("run_id") or receipt.get("index_id")
        for kind, receipt in sorted(receipts.items())
    }


def _receipt_path_exists(receipt: dict[str, object], key: str) -> bool:
    value = receipt.get(key)
    return bool(value) and Path(str(value)).is_file()


def _missing_paths(repo_root: Path, rel_paths: list[str]) -> list[str]:
    return [rel for rel in rel_paths if not (repo_root / rel).exists()]


def _exists(path: Path) -> bool:
    return path.exists()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _line_value(text: str, key: str) -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""
