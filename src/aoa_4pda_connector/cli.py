"""Command line interface for the connector skeleton."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.answer import render_answer_packet
from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, find_repo_root
from aoa_4pda_connector.evaluation import (
    DEFAULT_ANSWER_EVAL_SUITE,
    DEFAULT_GRAPH_EVAL_SUITE,
    DEFAULT_GRAPH_QUERY_EVAL_SUITE,
    DEFAULT_LIVE_GRAPH_QUERY_EVAL_SUITE,
    DEFAULT_LIVE_ANSWER_EVAL_SUITE,
    DEFAULT_LIVE_SEARCH_EVAL_SUITE,
    DEFAULT_SEARCH_EVAL_SUITE,
    run_answer_eval_suite,
    run_graph_eval_suite,
    run_graph_query_eval_suite,
    run_live_answer_eval_suite,
    run_live_graph_query_eval_suite,
    run_live_search_eval_suite,
    run_search_eval_suite,
)
from aoa_4pda_connector.fetch import fetch_public_topic, polite_sleep, topic_id_from_url, topic_page_url
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.policy import is_url_allowed
from aoa_4pda_connector.query import query_graph_packet, query_keyword_index
from aoa_4pda_connector.readiness import audit_connector_ready
from aoa_4pda_connector.storage import create_storage_roots, storage_status, storage_warnings


LIVE_SHAPE_FIXTURE_URL = "https://4pda.to/forum/index.php?showtopic=42&st=0"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aoa-4pda")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check local skeleton and storage posture.")
    doctor.set_defaults(func=cmd_doctor)

    init = sub.add_parser("init", help="Prepare configured storage roots.")
    init.add_argument("--apply", action="store_true", help="Create configured roots instead of printing a plan.")
    init.set_defaults(func=cmd_init)

    storage = sub.add_parser("storage", help="Inspect configured storage roots.")
    storage_sub = storage.add_subparsers(dest="storage_command", required=True)
    storage_status_parser = storage_sub.add_parser("status", help="Report configured storage root readiness.")
    storage_status_parser.add_argument(
        "--measure",
        action="store_true",
        help="Measure recursive file counts and bytes.",
    )
    storage_status_parser.set_defaults(func=cmd_storage_status)

    materialize = sub.add_parser("materialize", help="Materialize small no-network starter datasets.")
    materialize_sub = materialize.add_subparsers(dest="materialize_command", required=True)
    materialize_fixture = materialize_sub.add_parser(
        "fixture",
        help="Write a sanitized fixture run into configured storage roots.",
    )
    materialize_fixture.add_argument("--run", default="starter-fixture")
    materialize_fixture.add_argument("--profile", default="starter")
    materialize_fixture.set_defaults(func=cmd_materialize_fixture)

    policy = sub.add_parser("policy", help="Policy commands.")
    policy_sub = policy.add_subparsers(dest="policy_command", required=True)
    policy_check = policy_sub.add_parser("check", help="Check route policy files and sample URLs.")
    policy_check.set_defaults(func=cmd_policy_check)

    profile = sub.add_parser("profile", help="Inspect bounded crawl/search profiles.")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_inspect = profile_sub.add_parser("inspect", help="Inspect a profile, its seed file, and storage route.")
    profile_inspect.add_argument("profile", nargs="?", default="focused-device")
    profile_inspect.set_defaults(func=cmd_profile_inspect)

    ready = sub.add_parser("ready", help="Audit connector-ready-v1 maturity status.")
    ready.add_argument("--run", default="latest", help="Receipt run id to inspect, or latest.")
    ready.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when connector-ready-v1 is not fully achieved.",
    )
    ready.set_defaults(func=cmd_ready)

    crawl = sub.add_parser("crawl", help="Bounded public topic crawl.")
    crawl.add_argument("--profile", default="starter")
    crawl.add_argument("--max-topics", type=int, default=None)
    crawl.add_argument("--delay-seconds", type=float, default=None)
    crawl.set_defaults(func=cmd_crawl)

    normalize = sub.add_parser("normalize", help="Normalize latest or named crawl run.")
    normalize.add_argument("--run", default="latest")
    normalize.set_defaults(func=cmd_normalize)

    build_index = sub.add_parser("build-index", help="Build starter keyword index.")
    build_index.add_argument("--profile", default="starter")
    build_index.add_argument("--run", default="latest")
    build_index.set_defaults(func=cmd_build_index)

    build_graph = sub.add_parser("build-graph", help="Build starter graph export.")
    build_graph.add_argument("--profile", default="starter")
    build_graph.add_argument("--run", default="latest")
    build_graph.set_defaults(func=cmd_build_graph)

    query = sub.add_parser("query", help="Query local keyword index or fixture fallback.")
    query.add_argument("query")
    query.set_defaults(func=cmd_query)

    query_graph = sub.add_parser("query-graph", help="Query local keyword index with graph relation context.")
    query_graph.add_argument("query")
    query_graph.add_argument("--run", default="latest")
    query_graph.add_argument("--limit", type=int, default=5)
    query_graph.set_defaults(func=cmd_query_graph)

    answer = sub.add_parser("answer", help="Render a structured answer from local keyword and graph evidence.")
    answer.add_argument("query")
    answer.add_argument("--run", default="latest")
    answer.add_argument("--limit", type=int, default=5)
    answer.set_defaults(func=cmd_answer)

    export_packet = sub.add_parser("export-packet", help="Export an evidence packet.")
    export_packet.add_argument("--query-id", default=None)
    export_packet.add_argument("--query", default=None)
    export_packet.set_defaults(func=cmd_export_packet)

    proof = sub.add_parser("proof", help="Run reproducible proof routes.")
    proof_sub = proof.add_subparsers(dest="proof_command", required=True)
    starter_proof = proof_sub.add_parser("starter", help="Run offline starter proof over fixtures.")
    starter_proof.add_argument("--query", default="bootloop boot.img firmware")
    starter_proof.set_defaults(func=cmd_proof_starter)
    live_starter_proof = proof_sub.add_parser(
        "live-starter",
        help="Verify an already-built bounded live starter run in configured storage.",
    )
    live_starter_proof.add_argument("--run", default="latest")
    live_starter_proof.add_argument("--query", default="Redmi Note 10 Pro TWRP boot.img")
    live_starter_proof.set_defaults(func=cmd_proof_live_starter)

    eval_parser = sub.add_parser("eval", help="Run local connector eval suites.")
    eval_sub = eval_parser.add_subparsers(dest="eval_command", required=True)
    search_quality = eval_sub.add_parser("search-quality", help="Run the starter search quality eval.")
    search_quality.add_argument("--suite", default=str(DEFAULT_SEARCH_EVAL_SUITE))
    search_quality.set_defaults(func=cmd_eval_search_quality)
    live_search_quality = eval_sub.add_parser(
        "live-search-quality",
        help="Run search quality eval against an already-built bounded live run.",
    )
    live_search_quality.add_argument("--suite", default=str(DEFAULT_LIVE_SEARCH_EVAL_SUITE))
    live_search_quality.add_argument("--run", default="latest")
    live_search_quality.set_defaults(func=cmd_eval_live_search_quality)
    live_graph_query_quality = eval_sub.add_parser(
        "live-graph-query-quality",
        help="Run graph-query quality eval against an already-built bounded live run.",
    )
    live_graph_query_quality.add_argument("--suite", default=str(DEFAULT_LIVE_GRAPH_QUERY_EVAL_SUITE))
    live_graph_query_quality.add_argument("--run", default="latest")
    live_graph_query_quality.set_defaults(func=cmd_eval_live_graph_query_quality)
    live_answer_quality = eval_sub.add_parser(
        "live-answer-quality",
        help="Run rendered answer quality eval against an already-built bounded live run.",
    )
    live_answer_quality.add_argument("--suite", default=str(DEFAULT_LIVE_ANSWER_EVAL_SUITE))
    live_answer_quality.add_argument("--run", default="latest")
    live_answer_quality.set_defaults(func=cmd_eval_live_answer_quality)
    graph_relations = eval_sub.add_parser("graph-relations", help="Run the starter graph relation eval.")
    graph_relations.add_argument("--suite", default=str(DEFAULT_GRAPH_EVAL_SUITE))
    graph_relations.set_defaults(func=cmd_eval_graph_relations)
    graph_query_packets = eval_sub.add_parser("graph-query-packets", help="Run the starter graph query packet eval.")
    graph_query_packets.add_argument("--suite", default=str(DEFAULT_GRAPH_QUERY_EVAL_SUITE))
    graph_query_packets.set_defaults(func=cmd_eval_graph_query_packets)
    answer_packets = eval_sub.add_parser("answer-packets", help="Run the starter rendered answer packet eval.")
    answer_packets.add_argument("--suite", default=str(DEFAULT_ANSWER_EVAL_SUITE))
    answer_packets.set_defaults(func=cmd_eval_answer_packets)

    serve = sub.add_parser("serve", help="Safe serve stub.")
    serve.set_defaults(func=lambda args: cmd_stub("serve", args))

    return parser


def cmd_doctor(_args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    warnings = storage_warnings(repo_root, roots)
    required = [
        repo_root / "connector" / "SOURCE_POLICY.md",
        repo_root / "connector" / "STORAGE_POLICY.md",
        repo_root / "connector" / "profiles" / "starter.yaml",
        repo_root / "connector" / "manifests" / "route_allowlist.yaml",
        repo_root / ".gitignore",
    ]
    required_schemas = [
        "crawl_receipt.schema.json",
        "normalized_topic.schema.json",
        "normalized_post.schema.json",
        "evidence_packet.schema.json",
        "answer_packet.schema.json",
        "materialize_receipt.schema.json",
        "index_manifest.schema.json",
        "graph_node.schema.json",
        "graph_edge.schema.json",
    ]
    required_ignore_patterns = [
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
        "graphs/",
        "exports/full/",
        "*.sqlite",
        "*.sqlite3",
        "*.parquet",
        "*.qdrant/",
        "*.lancedb/",
    ]
    forbidden_heavy_dirs = ["data", "cache", "artifacts", "raw", "indexes", "graphs"]
    missing = [str(path.relative_to(repo_root)) for path in required if not path.exists()]
    missing.extend(
        f"connector/schemas/{name}"
        for name in required_schemas
        if not (repo_root / "connector" / "schemas" / name).exists()
    )
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8") if (repo_root / ".gitignore").exists() else ""
    missing.extend(
        f".gitignore pattern {pattern}"
        for pattern in required_ignore_patterns
        if pattern not in gitignore
    )
    heavy_dirs = [name for name in forbidden_heavy_dirs if (repo_root / name).exists()]
    status = "ok" if not missing and not heavy_dirs else "error"
    _emit(
        {
            "schema": "aoa_4pda_doctor_v1",
            "status": status,
            "repo_root": str(repo_root),
            "storage_mode": roots.mode,
            "local_state_dir": LOCAL_STATE_DIR,
            "storage_roots": roots.as_dict(),
            "warnings": warnings,
            "missing": missing,
            "heavy_dirs_inside_repo": heavy_dirs,
            "network_touched": False,
        }
    )
    return 0 if status == "ok" else 1


def cmd_init(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    missing = roots.missing()
    warnings = storage_warnings(repo_root, roots)
    if args.apply and missing:
        _emit(
            {
                "schema": "aoa_4pda_init_v1",
                "status": "error",
                "message": "storage roots must be set before --apply",
                "missing": missing,
                "network_touched": False,
            }
        )
        return 2
    created = create_storage_roots(roots) if args.apply else []
    _emit(
        {
            "schema": "aoa_4pda_init_v1",
            "status": "ok",
            "apply": bool(args.apply),
            "storage_mode": roots.mode,
            "local_state_dir": LOCAL_STATE_DIR,
            "storage_roots": roots.as_dict(),
            "created": created,
            "warnings": warnings,
            "network_touched": False,
        }
    )
    return 0


def cmd_storage_status(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    _emit(storage_status(repo_root, roots, measure=bool(args.measure)))
    return 0


def cmd_policy_check(_args: argparse.Namespace) -> int:
    samples = {
        "allowed_topic": "https://4pda.to/forum/index.php?showtopic=000001",
        "denied_search": "https://4pda.to/forum/index.php?act=search&q=test",
        "denied_attach": "https://4pda.to/forum/index.php?act=attach&type=post&id=1",
    }
    results = {name: is_url_allowed(url) for name, url in samples.items()}
    ok = results == {"allowed_topic": True, "denied_search": False, "denied_attach": False}
    _emit(
        {
            "schema": "aoa_4pda_policy_check_v1",
            "status": "ok" if ok else "error",
            "samples": results,
            "internal_search_allowed": False,
            "attachments_allowed": False,
            "network_touched": False,
        }
    )
    return 0 if ok else 1


def cmd_profile_inspect(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    try:
        profile = _read_profile(repo_root, args.profile)
        seed_rel = str(profile.get("seed_file", "connector/seeds/starter_topics.yaml"))
        seed_path = repo_root / seed_rel
        seeds = _read_seed_urls(seed_path) if seed_path.is_file() else []
    except Exception as exc:  # noqa: BLE001 - inspect output should preserve route failure detail.
        _emit(
            {
                "schema": "aoa_4pda_profile_inspect_v1",
                "status": "error",
                "profile_id": args.profile,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1

    seed_checks = [
        {"seed_id": seed.get("id"), "url": seed.get("url"), "allowed_public_topic": is_url_allowed(seed.get("url", ""))}
        for seed in seeds
    ]
    checks = {
        "profile_file_exists": (repo_root / "connector" / "profiles" / f"{args.profile}.yaml").is_file(),
        "network_default_disabled": profile.get("network_default") == "disabled",
        "seed_file_exists": (repo_root / str(profile.get("seed_file"))).is_file(),
        "seed_urls_allowed_public_topics": all(check["allowed_public_topic"] for check in seed_checks),
        "internal_search_unused": True,
    }
    status = "ok" if all(checks.values()) else "error"
    _emit(
        {
            "schema": "aoa_4pda_profile_inspect_v1",
            "status": status,
            "profile_id": profile.get("profile_id", args.profile),
            "requested_profile": args.profile,
            "profile_kind": profile.get("profile_kind"),
            "description": profile.get("description"),
            "target": {
                "device_id": profile.get("target_device_id"),
                "label": profile.get("target_label"),
                "codename": profile.get("target_codename"),
                "model_aliases": _split_csv(profile.get("target_model_aliases")),
                "search_terms": _split_csv(profile.get("target_search_terms")),
            },
            "network_default": profile.get("network_default"),
            "limits": {
                "max_topics": profile.get("max_topics"),
                "max_pages_per_topic": profile.get("max_pages_per_topic"),
                "max_posts_per_topic": profile.get("max_posts_per_topic"),
            },
            "politeness": {
                "min_delay_seconds": profile.get("min_delay_seconds"),
                "max_concurrency": profile.get("max_concurrency"),
            },
            "routes": {
                "seed_file": profile.get("seed_file"),
                "allowlist_manifest": profile.get("allowlist_manifest"),
            },
            "quality_gates": {
                "live_search_suite": profile.get("live_search_suite"),
                "live_graph_query_suite": profile.get("live_graph_query_suite"),
                "live_answer_suite": profile.get("live_answer_suite"),
            },
            "seed": {
                "path": str(profile.get("seed_file")),
                "topic_count": len(seeds),
                "topic_ids": [seed.get("id") for seed in seeds],
                "topics": seeds,
                "checks": seed_checks,
            },
            "storage_mode": roots.mode,
            "storage_roots": roots.as_dict(),
            "checks": checks,
            "network_touched": False,
        }
    )
    return 0 if status == "ok" else 1


def cmd_ready(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    report = audit_connector_ready(repo_root, roots, run=args.run)
    _emit(report)
    if args.strict and report.get("status") != "ready":
        return 1
    return 0


def cmd_materialize_fixture(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    error = _require_roots(roots, ["data", "cache", "artifact"])
    if error:
        return error
    create_storage_roots(roots)
    run_id = args.run
    normalized_dir = roots.data / "normalized" / run_id
    fixture_path = repo_root / "connector" / "fixtures" / "html" / "live_shape_topic.html"
    normalized_path = normalize_snapshot(fixture_path, LIVE_SHAPE_FIXTURE_URL, normalized_dir)
    index_path = build_keyword_index(normalized_dir, roots.cache / "indexes" / run_id, args.profile)
    graph_path = build_graph(normalized_dir, roots.artifact / "graphs" / run_id, args.profile)

    index = json.loads(index_path.read_text(encoding="utf-8"))
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    receipt_dir = roots.artifact / "receipts"
    normalized_receipt = {
        "schema": "aoa_4pda_normalize_receipt_v1",
        "run_id": run_id,
        "source_run_id": run_id,
        "finished_at": _now(),
        "normalized": [{"source_url": LIVE_SHAPE_FIXTURE_URL, "path": str(normalized_path)}],
        "counts": {"topics": 1},
        "network_touched": False,
    }
    index_receipt = {
        "schema": "aoa_4pda_index_manifest_v1",
        "index_id": run_id,
        "profile_id": args.profile,
        "built_at": _now(),
        "source_run_ids": [run_id],
        "index_kinds": ["keyword"],
        "artifact_root": str(index_path.parent),
        "index_path": str(index_path),
        "network_touched": False,
    }
    graph_receipt = {
        "schema": "aoa_4pda_graph_receipt_v1",
        "run_id": run_id,
        "profile_id": args.profile,
        "built_at": _now(),
        "graph_path": str(graph_path),
        "network_touched": False,
    }
    materialize_receipt = {
        "schema": "aoa_4pda_materialize_receipt_v1",
        "run_id": run_id,
        "profile_id": args.profile,
        "fixture": "live_shape_topic",
        "source_url": LIVE_SHAPE_FIXTURE_URL,
        "finished_at": _now(),
        "storage_mode": roots.mode,
        "storage_roots": roots.as_dict(),
        "normalized_path": str(normalized_path),
        "index_path": str(index_path),
        "graph_path": str(graph_path),
        "counts": {
            "topics": 1,
            "index_docs": int(index.get("doc_count", 0)),
            "index_terms": int(index.get("term_count", 0)),
            "graph_nodes": int(graph.get("node_count", 0)),
            "graph_edges": int(graph.get("edge_count", 0)),
        },
        "policy": {
            "allowed_public_only": True,
            "internal_search_used": False,
            "attachments_downloaded": False,
        },
        "network_touched": False,
    }
    normalize_receipt_path = _write_receipt(receipt_dir, run_id, "normalize", normalized_receipt)
    index_receipt_path = _write_receipt(receipt_dir, run_id, "index", index_receipt)
    graph_receipt_path = _write_receipt(receipt_dir, run_id, "graph", graph_receipt)
    materialize_receipt_path = _write_receipt(receipt_dir, run_id, "materialize", materialize_receipt)
    _emit(
        {
            "status": "ok",
            "receipt": str(materialize_receipt_path),
            "receipts": {
                "normalize": str(normalize_receipt_path),
                "index": str(index_receipt_path),
                "graph": str(graph_receipt_path),
                "materialize": str(materialize_receipt_path),
            },
            **materialize_receipt,
        }
    )
    return 0


def cmd_crawl(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    error = _require_roots(roots, ["data", "artifact"])
    if error:
        return error
    create_storage_roots(roots)
    profile = _read_profile(repo_root, args.profile)
    max_topics = args.max_topics or int(profile.get("max_topics", 10))
    max_pages_per_topic = int(profile.get("max_pages_per_topic", 1))
    delay = args.delay_seconds if args.delay_seconds is not None else float(profile.get("min_delay_seconds", 8))
    seeds = _read_seed_urls(repo_root / str(profile.get("seed_file", "connector/seeds/starter_topics.yaml")))
    run_id = _new_run_id("crawl")
    raw_dir = roots.data / "raw" / run_id
    receipt_dir = roots.artifact / "receipts"
    fetched = []
    errors = []
    selected = seeds[:max_topics]
    total_requests = sum(_seed_page_count(seed, max_pages_per_topic) for seed in selected)
    request_index = 0
    for seed in selected:
        seed_pages = _seed_page_count(seed, max_pages_per_topic)
        for page_index in range(seed_pages):
            request_index += 1
            page_url = topic_page_url(seed["url"], page_index)
            page_start = topic_page_url(seed["url"], page_index).rsplit("st=", 1)[-1]
            try:
                result = fetch_public_topic(page_url, raw_dir)
                fetched.append(
                    {
                        "seed_id": seed["id"],
                        "label": seed["label"],
                        "page_index": page_index,
                        "page_start": int(page_start),
                        "url": result.url,
                        "path": str(result.path),
                        "bytes": result.bytes_written,
                        "sha256": result.sha256,
                        "status": result.status,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - receipt should preserve crawl failure detail.
                errors.append(
                    {
                        "seed_id": seed["id"],
                        "page_index": page_index,
                        "page_start": page_start,
                        "url": page_url,
                        "error": str(exc),
                    }
                )
            if request_index < total_requests:
                polite_sleep(delay)
    fetched_topic_ids = sorted({item["seed_id"] for item in fetched})
    receipt = {
        "schema": "aoa_4pda_crawl_receipt_v1",
        "run_id": run_id,
        "profile_id": args.profile,
        "started_at": run_id.split("__", 1)[0],
        "finished_at": _now(),
        "source_urls": [item["url"] for item in fetched],
        "policy": {
            "allowed_public_only": True,
            "internal_search_used": False,
            "attachments_downloaded": False,
        },
        "counts": {
            "requested": len(selected),
            "fetched": len(fetched),
            "requested_topics": len(selected),
            "requested_pages": total_requests,
            "fetched_topics": len(fetched_topic_ids),
            "fetched_pages": len(fetched),
            "errors": len(errors),
        },
        "snapshots": fetched,
        "errors": errors,
        "network_touched": True,
    }
    receipt_path = _write_receipt(receipt_dir, run_id, "crawl", receipt)
    _emit({"status": "ok" if fetched else "error", "receipt": str(receipt_path), **receipt})
    return 0 if fetched else 1


def cmd_normalize(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["data", "artifact"])
    if error:
        return error
    receipt = _load_latest_or_named_receipt(roots.artifact, args.run, "crawl")
    run_id = receipt["run_id"]
    output_dir = roots.data / "normalized" / run_id
    normalized = []
    for snapshot in receipt.get("snapshots", []):
        path = normalize_snapshot(Path(snapshot["path"]), snapshot["url"], output_dir)
        normalized.append({"source_url": snapshot["url"], "path": str(path)})
    topic_ids = sorted({topic_id_from_url(str(item["source_url"])) for item in normalized})
    payload = {
        "schema": "aoa_4pda_normalize_receipt_v1",
        "run_id": run_id,
        "source_run_id": receipt["run_id"],
        "finished_at": _now(),
        "normalized": normalized,
        "counts": {"topics": len(topic_ids), "pages": len(normalized)},
        "network_touched": False,
    }
    receipt_path = _write_receipt(roots.artifact / "receipts", run_id, "normalize", payload)
    _emit({"status": "ok", "receipt": str(receipt_path), **payload})
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["data", "cache", "artifact"])
    if error:
        return error
    receipt = _load_latest_or_named_receipt(roots.artifact, args.run, "normalize")
    run_id = receipt["run_id"]
    normalized_dir = roots.data / "normalized" / run_id
    output_dir = roots.cache / "indexes" / run_id
    index_path = build_keyword_index(normalized_dir, output_dir, args.profile)
    payload = {
        "schema": "aoa_4pda_index_manifest_v1",
        "index_id": run_id,
        "profile_id": args.profile,
        "built_at": _now(),
        "source_run_ids": [run_id],
        "index_kinds": ["keyword"],
        "artifact_root": str(output_dir),
        "index_path": str(index_path),
        "network_touched": False,
    }
    receipt_path = _write_receipt(roots.artifact / "receipts", run_id, "index", payload)
    _emit({"status": "ok", "receipt": str(receipt_path), **payload})
    return 0


def cmd_build_graph(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["data", "artifact"])
    if error:
        return error
    receipt = _load_latest_or_named_receipt(roots.artifact, args.run, "normalize")
    run_id = receipt["run_id"]
    normalized_dir = roots.data / "normalized" / run_id
    output_dir = roots.artifact / "graphs" / run_id
    graph_path = build_graph(normalized_dir, output_dir, args.profile)
    payload = {
        "schema": "aoa_4pda_graph_receipt_v1",
        "run_id": run_id,
        "profile_id": args.profile,
        "built_at": _now(),
        "graph_path": str(graph_path),
        "network_touched": False,
    }
    receipt_path = _write_receipt(roots.artifact / "receipts", run_id, "graph", payload)
    _emit({"status": "ok", "receipt": str(receipt_path), **payload})
    return 0


def cmd_stub(name: str, args: argparse.Namespace) -> int:
    _emit(
        {
            "schema": "aoa_4pda_safe_stub_v1",
            "command": name,
            "status": "not_implemented_safe_stub",
            "args": vars(args),
            "network_touched": False,
            "message": "Skeleton command only; implement after policy and storage gates are active.",
        }
    )
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    if roots.cache and roots.artifact:
        try:
            receipt = _load_latest_or_named_receipt(roots.artifact, "latest", "index")
            packet = query_keyword_index(Path(receipt["index_path"]), args.query)
            _emit({"status": "ok", **packet, "network_touched": False})
            return 0
        except Exception:
            pass
    fixture = Path("connector/fixtures/expected_packets/synthetic_bootloop_packet.json")
    packet = json.loads(fixture.read_text(encoding="utf-8"))
    packet["query"] = args.query
    _emit({"status": "fixture_fallback", **packet, "network_touched": False})
    return 0


def cmd_query_graph(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["cache", "artifact"])
    if error:
        return error
    try:
        packet = _query_graph_packet_from_roots(roots.artifact, args.run, args.query, args.limit)
    except Exception as exc:  # noqa: BLE001 - CLI report should preserve setup failure detail.
        _emit(
            {
                "schema": "aoa_4pda_graph_query_error_v1",
                "status": "error",
                "run": args.run,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1
    _emit({"status": "ok", **packet, "network_touched": False})
    return 0


def cmd_answer(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["cache", "artifact"])
    if error:
        return error
    try:
        evidence_packet = _query_graph_packet_from_roots(roots.artifact, args.run, args.query, args.limit)
        answer_packet = render_answer_packet(evidence_packet, limit=args.limit)
    except Exception as exc:  # noqa: BLE001 - CLI report should preserve setup failure detail.
        _emit(
            {
                "schema": "aoa_4pda_answer_error_v1",
                "status": "error",
                "run": args.run,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1
    _emit({"status": "ok", **answer_packet, "network_touched": False})
    return 0


def cmd_export_packet(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["artifact"])
    if error:
        return error
    if args.query:
        index_receipt = _load_latest_or_named_receipt(roots.artifact, "latest", "index")
        packet = query_keyword_index(Path(index_receipt["index_path"]), args.query)
        if args.query_id:
            packet["packet_id"] = args.query_id
    else:
        fixture = Path("connector/fixtures/expected_packets/synthetic_bootloop_packet.json")
        packet = json.loads(fixture.read_text(encoding="utf-8"))
        packet["packet_id"] = args.query_id or "fixture-packet-bootloop"
    output_dir = roots.artifact / "evidence_packets"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{packet['packet_id']}.json"
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    _emit({"schema": "aoa_4pda_export_packet_v1", "status": "ok", "path": str(path), "network_touched": False})
    return 0


def cmd_proof_starter(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    fixture = repo_root / "connector" / "fixtures" / "normalized" / "synthetic_topic.json"
    with tempfile.TemporaryDirectory(prefix="aoa-4pda-proof-") as tmp:
        proof_root = Path(tmp)
        normalized_dir = proof_root / "normalized" / "fixture-starter-proof"
        normalized_dir.mkdir(parents=True)
        shutil.copy2(fixture, normalized_dir / "topic-synthetic-topic-1.json")

        index_path = build_keyword_index(normalized_dir, proof_root / "cache" / "indexes", "starter")
        graph_path = build_graph(normalized_dir, proof_root / "artifacts" / "graphs", "starter")
        packet = query_keyword_index(index_path, args.query, limit=3)

        index = json.loads(index_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        first_result = packet["results"][0] if packet.get("results") else {}
        topic = json.loads(fixture.read_text(encoding="utf-8"))
        checks = {
            "fixture_topic_loaded": fixture.is_file(),
            "index_doc_count_is_2": index.get("doc_count") == 2,
            "term_count_positive": int(index.get("term_count", 0)) > 0,
            "graph_has_topic_post_entity_nodes": int(graph.get("node_count", 0)) >= 5,
            "graph_has_edges": int(graph.get("edge_count", 0)) >= 4,
            "query_returns_bootloop_post": first_result.get("post_id") == "1002",
            "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
        }

    status = "ok" if all(checks.values()) else "error"
    _emit(
        {
            "schema": "aoa_4pda_starter_proof_v1",
            "status": status,
            "profile_id": "starter",
            "source": "synthetic_fixture",
            "external_storage_required": False,
            "network_touched": False,
            "artifact_lifecycle": "temporary_deleted_after_run",
            "query": args.query,
            "counts": {
                "topics": 1,
                "posts": len(topic.get("posts", [])),
                "index_docs": index.get("doc_count", 0),
                "terms": index.get("term_count", 0),
                "graph_nodes": graph.get("node_count", 0),
                "graph_edges": graph.get("edge_count", 0),
                "query_results": len(packet.get("results", [])),
            },
            "checks": checks,
            "top_result": first_result,
        }
    )
    return 0 if status == "ok" else 1


def cmd_proof_live_starter(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env(repo_root)
    error = _require_roots(roots, ["data", "cache", "artifact"])
    if error:
        return error
    try:
        crawl_receipt = _load_latest_or_named_receipt(roots.artifact, args.run, "crawl")
        run_id = str(crawl_receipt["run_id"])
        normalize_receipt = _load_latest_or_named_receipt(roots.artifact, run_id, "normalize")
        index_receipt = _load_latest_or_named_receipt(roots.artifact, run_id, "index")
        graph_receipt = _load_latest_or_named_receipt(roots.artifact, run_id, "graph")
        index_path = Path(str(index_receipt["index_path"]))
        graph_path = Path(str(graph_receipt["graph_path"]))
        packet = query_keyword_index(index_path, args.query, limit=5)
        index = json.loads(index_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - proof output should preserve route failure detail.
        _emit(
            {
                "schema": "aoa_4pda_live_starter_proof_v1",
                "status": "error",
                "run": args.run,
                "error": str(exc),
                "proof_command_network_touched": False,
            }
        )
        return 1

    crawl_counts = crawl_receipt.get("counts", {})
    normalize_counts = normalize_receipt.get("counts", {})
    requested_topics = int(crawl_counts.get("requested_topics", crawl_counts.get("requested", 0)))
    requested_pages = int(crawl_counts.get("requested_pages", crawl_counts.get("requested", 0)))
    fetched_topics = int(crawl_counts.get("fetched_topics", crawl_counts.get("fetched", 0)))
    fetched_pages = int(crawl_counts.get("fetched_pages", crawl_counts.get("fetched", 0)))
    normalized_topics = int(normalize_counts.get("topics", normalize_counts.get("pages", 0)))
    normalized_pages = int(normalize_counts.get("pages", normalize_counts.get("topics", 0)))
    policy = crawl_receipt.get("policy", {})
    storage_warning_list = storage_warnings(repo_root, roots)
    first_result = packet["results"][0] if packet.get("results") else {}
    checks = {
        "external_roots_ready": not storage_warning_list,
        "crawl_fetched_public_topics": fetched_topics > 0
        and int(crawl_counts.get("errors", 0)) == 0,
        "policy_preserved": policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False
        and packet.get("policy", {}).get("internal_search_used") is False,
        "normalized_pages_match_fetched": normalized_pages == fetched_pages,
        "index_has_posts": int(index.get("doc_count", 0)) > 0,
        "graph_has_nodes_edges": int(graph.get("node_count", 0)) > 0 and int(graph.get("edge_count", 0)) > 0,
        "query_returns_result": bool(packet.get("results")),
        "network_limited_to_crawl": crawl_receipt.get("network_touched") is True
        and normalize_receipt.get("network_touched") is False
        and index_receipt.get("network_touched") is False
        and graph_receipt.get("network_touched") is False,
    }
    status = "ok" if all(checks.values()) else "error"
    _emit(
        {
            "schema": "aoa_4pda_live_starter_proof_v1",
            "status": status,
            "run_id": run_id,
            "profile_id": crawl_receipt.get("profile_id"),
            "storage_mode": roots.mode,
            "query": args.query,
            "proof_command_network_touched": False,
            "source_run_network_touched": bool(crawl_receipt.get("network_touched")),
            "storage_roots": roots.as_dict(),
            "storage_warnings": storage_warning_list,
            "artifact_paths": {
                "index_path": str(index_path),
                "graph_path": str(graph_path),
            },
            "counts": {
                "requested_topics": requested_topics,
                "requested_pages": requested_pages,
                "fetched_topics": fetched_topics,
                "fetched_pages": fetched_pages,
                "normalized_topics": normalized_topics,
                "normalized_pages": normalized_pages,
                "index_docs": int(index.get("doc_count", 0)),
                "index_terms": int(index.get("term_count", 0)),
                "graph_nodes": int(graph.get("node_count", 0)),
                "graph_edges": int(graph.get("edge_count", 0)),
                "query_results": len(packet.get("results", [])),
            },
            "checks": checks,
            "top_result": first_result,
        }
    )
    return 0 if status == "ok" else 1


def cmd_eval_search_quality(args: argparse.Namespace) -> int:
    report = run_search_eval_suite(Path(args.suite), find_repo_root())
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_live_search_quality(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["artifact"])
    if error:
        return error
    try:
        report = run_live_search_eval_suite(args.run, Path(args.suite), find_repo_root(), roots.artifact)
    except Exception as exc:  # noqa: BLE001 - CLI report should preserve setup failure detail.
        _emit(
            {
                "schema": "aoa_4pda_live_search_eval_error_v1",
                "status": "error",
                "run": args.run,
                "suite": args.suite,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_live_graph_query_quality(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["artifact"])
    if error:
        return error
    try:
        report = run_live_graph_query_eval_suite(args.run, Path(args.suite), find_repo_root(), roots.artifact)
    except Exception as exc:  # noqa: BLE001 - CLI report should preserve setup failure detail.
        _emit(
            {
                "schema": "aoa_4pda_live_graph_query_eval_error_v1",
                "status": "error",
                "run": args.run,
                "suite": args.suite,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_live_answer_quality(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env(find_repo_root())
    error = _require_roots(roots, ["artifact"])
    if error:
        return error
    try:
        report = run_live_answer_eval_suite(args.run, Path(args.suite), find_repo_root(), roots.artifact)
    except Exception as exc:  # noqa: BLE001 - CLI report should preserve setup failure detail.
        _emit(
            {
                "schema": "aoa_4pda_live_answer_eval_error_v1",
                "status": "error",
                "run": args.run,
                "suite": args.suite,
                "error": str(exc),
                "network_touched": False,
            }
        )
        return 1
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_graph_relations(args: argparse.Namespace) -> int:
    report = run_graph_eval_suite(Path(args.suite), find_repo_root())
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_graph_query_packets(args: argparse.Namespace) -> int:
    report = run_graph_query_eval_suite(Path(args.suite), find_repo_root())
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def cmd_eval_answer_packets(args: argparse.Namespace) -> int:
    report = run_answer_eval_suite(Path(args.suite), find_repo_root())
    _emit(report)
    return 0 if report.get("status") == "ok" else 1


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_run_id(kind: str) -> str:
    return f"{_now().replace(':', '').replace('-', '')}__{kind}"


def _require_roots(roots: StorageRoots, names: list[str]) -> int:
    mapping = {"data": roots.data, "cache": roots.cache, "artifact": roots.artifact}
    missing = [name for name in names if mapping[name] is None]
    if missing:
        _emit(
            {
                "schema": "aoa_4pda_missing_storage_roots_v1",
                "status": "error",
                "missing": missing,
                "storage_roots": roots.as_dict(),
                "network_touched": False,
            }
        )
        return 2
    return 0


def _read_profile(repo_root: Path, profile_id: str) -> dict[str, object]:
    path = repo_root / "connector" / "profiles" / f"{profile_id}.yaml"
    values: dict[str, object] = {
        "profile_path": str(path.relative_to(repo_root)),
        "seed_file": "connector/seeds/starter_topics.yaml",
    }
    string_keys = {
        "schema",
        "profile_id",
        "profile_kind",
        "description",
        "target_device_id",
        "target_label",
        "target_codename",
        "target_model_aliases",
        "target_search_terms",
        "network_default",
        "seed_file",
        "allowlist_manifest",
        "live_search_suite",
        "live_graph_query_suite",
        "live_answer_suite",
    }
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {"max_topics", "max_pages_per_topic", "max_posts_per_topic", "min_delay_seconds", "max_concurrency"}:
            try:
                values[key] = int(value)
            except ValueError:
                values[key] = float(value)
        elif key in string_keys and value:
            values[key] = value
    if "min_delay_seconds" not in values:
        values["min_delay_seconds"] = 8
    return values


def _read_seed_urls(path: Path) -> list[dict[str, str]]:
    seeds: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- id:"):
            if current:
                seeds.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current and line.startswith("url:"):
            current["url"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("label:"):
            current["label"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("focus:"):
            current["focus"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("max_pages:"):
            current["max_pages"] = line.split(":", 1)[1].strip()
    if current:
        seeds.append(current)
    return [seed for seed in seeds if seed.get("url")]


def _seed_page_count(seed: dict[str, str], default_pages: int) -> int:
    try:
        return max(1, int(seed.get("max_pages", default_pages)))
    except ValueError:
        return default_pages


def _split_csv(value: object) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _write_receipt(receipt_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    path = receipt_dir / f"{run_id}.{kind}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = receipt_dir / f"latest_{kind}.json"
    latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_latest_or_named_receipt(artifact_root: Path, run: str, kind: str) -> dict[str, object]:
    receipt_dir = artifact_root / "receipts"
    path = receipt_dir / f"latest_{kind}.json" if run == "latest" else receipt_dir / f"{run}.{kind}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_graph_receipt_for_query(artifact_root: Path, requested_run: str, index_run_id: str) -> dict[str, object]:
    receipt_dir = artifact_root / "receipts"
    named_graph = receipt_dir / f"{index_run_id}.graph.json"
    if named_graph.is_file():
        return json.loads(named_graph.read_text(encoding="utf-8"))
    return _load_latest_or_named_receipt(artifact_root, requested_run, "graph")


def _query_graph_packet_from_roots(artifact_root: Path, run: str, query: str, limit: int) -> dict[str, object]:
    index_receipt = _load_latest_or_named_receipt(artifact_root, run, "index")
    run_id = str(index_receipt.get("index_id") or index_receipt.get("run_id") or run)
    graph_receipt = _load_graph_receipt_for_query(artifact_root, run, run_id)
    return query_graph_packet(
        Path(str(index_receipt["index_path"])),
        Path(str(graph_receipt["graph_path"])),
        query,
        limit=limit,
    )


if __name__ == "__main__":
    sys.exit(main())
