"""Command line interface for the connector skeleton."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.config import StorageRoots, find_repo_root
from aoa_4pda_connector.fetch import fetch_public_topic, polite_sleep
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.policy import is_url_allowed
from aoa_4pda_connector.query import query_keyword_index
from aoa_4pda_connector.storage import create_storage_roots, storage_warnings


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aoa-4pda")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check local skeleton and storage posture.")
    doctor.set_defaults(func=cmd_doctor)

    init = sub.add_parser("init", help="Prepare external storage roots.")
    init.add_argument("--apply", action="store_true", help="Create external roots instead of printing a plan.")
    init.set_defaults(func=cmd_init)

    policy = sub.add_parser("policy", help="Policy commands.")
    policy_sub = policy.add_subparsers(dest="policy_command", required=True)
    policy_check = policy_sub.add_parser("check", help="Check route policy files and sample URLs.")
    policy_check.set_defaults(func=cmd_policy_check)

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
    build_index.set_defaults(func=cmd_build_index)

    build_graph = sub.add_parser("build-graph", help="Build starter graph export.")
    build_graph.add_argument("--profile", default="starter")
    build_graph.set_defaults(func=cmd_build_graph)

    query = sub.add_parser("query", help="Query local keyword index or fixture fallback.")
    query.add_argument("query")
    query.set_defaults(func=cmd_query)

    export_packet = sub.add_parser("export-packet", help="Export an evidence packet.")
    export_packet.add_argument("--query-id", default="fixture-packet-bootloop")
    export_packet.add_argument("--query", default=None)
    export_packet.set_defaults(func=cmd_export_packet)

    serve = sub.add_parser("serve", help="Safe serve stub.")
    serve.set_defaults(func=lambda args: cmd_stub("serve", args))

    return parser


def cmd_doctor(_args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env()
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
        "index_manifest.schema.json",
        "graph_node.schema.json",
        "graph_edge.schema.json",
    ]
    required_ignore_patterns = [
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
    roots = StorageRoots.from_env()
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
            "storage_roots": roots.as_dict(),
            "created": created,
            "warnings": warnings,
            "network_touched": False,
        }
    )
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


def cmd_crawl(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    roots = StorageRoots.from_env()
    error = _require_roots(roots, ["data", "artifact"])
    if error:
        return error
    create_storage_roots(roots)
    profile = _read_profile(repo_root, args.profile)
    max_topics = args.max_topics or int(profile.get("max_topics", 10))
    delay = args.delay_seconds if args.delay_seconds is not None else float(profile.get("min_delay_seconds", 8))
    seeds = _read_seed_urls(repo_root / str(profile.get("seed_file", "connector/seeds/starter_topics.yaml")))
    run_id = _new_run_id("crawl")
    raw_dir = roots.data / "raw" / run_id
    receipt_dir = roots.artifact / "receipts"
    fetched = []
    errors = []
    selected = seeds[:max_topics]
    for index, seed in enumerate(selected):
        try:
            result = fetch_public_topic(seed["url"], raw_dir)
            fetched.append(
                {
                    "seed_id": seed["id"],
                    "label": seed["label"],
                    "url": result.url,
                    "path": str(result.path),
                    "bytes": result.bytes_written,
                    "sha256": result.sha256,
                    "status": result.status,
                }
            )
        except Exception as exc:  # noqa: BLE001 - receipt should preserve crawl failure detail.
            errors.append({"seed_id": seed["id"], "url": seed["url"], "error": str(exc)})
        if index + 1 < len(selected):
            polite_sleep(delay)
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
        "counts": {"requested": len(selected), "fetched": len(fetched), "errors": len(errors)},
        "snapshots": fetched,
        "errors": errors,
        "network_touched": True,
    }
    receipt_path = _write_receipt(receipt_dir, run_id, "crawl", receipt)
    _emit({"status": "ok" if fetched else "error", "receipt": str(receipt_path), **receipt})
    return 0 if fetched else 1


def cmd_normalize(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env()
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
    payload = {
        "schema": "aoa_4pda_normalize_receipt_v1",
        "run_id": run_id,
        "source_run_id": receipt["run_id"],
        "finished_at": _now(),
        "normalized": normalized,
        "counts": {"topics": len(normalized)},
        "network_touched": False,
    }
    receipt_path = _write_receipt(roots.artifact / "receipts", run_id, "normalize", payload)
    _emit({"status": "ok", "receipt": str(receipt_path), **payload})
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env()
    error = _require_roots(roots, ["data", "cache", "artifact"])
    if error:
        return error
    receipt = _load_latest_or_named_receipt(roots.artifact, "latest", "normalize")
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
    roots = StorageRoots.from_env()
    error = _require_roots(roots, ["data", "artifact"])
    if error:
        return error
    receipt = _load_latest_or_named_receipt(roots.artifact, "latest", "normalize")
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
    roots = StorageRoots.from_env()
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


def cmd_export_packet(args: argparse.Namespace) -> int:
    roots = StorageRoots.from_env()
    error = _require_roots(roots, ["artifact"])
    if error:
        return error
    if args.query:
        packet = query_keyword_index(Path(_load_latest_or_named_receipt(roots.artifact, "latest", "index")["index_path"]), args.query)
    else:
        fixture = Path("connector/fixtures/expected_packets/synthetic_bootloop_packet.json")
        packet = json.loads(fixture.read_text(encoding="utf-8"))
        packet["packet_id"] = args.query_id
    output_dir = roots.artifact / "evidence_packets"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{packet['packet_id']}.json"
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    _emit({"schema": "aoa_4pda_export_packet_v1", "status": "ok", "path": str(path), "network_touched": False})
    return 0


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
    values: dict[str, object] = {"seed_file": "connector/seeds/starter_topics.yaml"}
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
        elif key == "seed_file":
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
    if current:
        seeds.append(current)
    return [seed for seed in seeds if seed.get("url")]


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


if __name__ == "__main__":
    sys.exit(main())
