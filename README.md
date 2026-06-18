# aoa-4pda-connector

`aoa-4pda-connector` is a GitHub-publishable skeleton for an AoA external
connector that can build local, policy-gated search and graph evidence from
public 4PDA topic/post pages.

It stores method, code, schemas, policy, tiny fixtures, seed profiles, eval
queries, and an install route. It does not store full crawls, raw corpora,
large indexes, vector stores, or graph databases.

## What This Repository Does

| Function | Surface |
| --- | --- |
| Connector identity and boundaries | `CHARTER.md`, `BOUNDARIES.md` |
| Agent route and validation | `AGENTS.md` |
| Source and crawl policy | `connector/SOURCE_POLICY.md`, `connector/manifests/route_allowlist.yaml` |
| Storage contract | `connector/STORAGE_POLICY.md`, `.env.example` |
| Executable skeleton | `src/aoa_4pda_connector/` |
| CLI entrypoint | `aoa-4pda` |
| Schemas | `connector/schemas/` |
| Synthetic fixtures | `connector/fixtures/` |
| Starter profiles and seeds | `connector/profiles/`, `connector/seeds/` |
| Install route | `docs/INSTALL.md`, `docs/AGENT_INSTALL_ROUTE.md` |
| Validation | `scripts/validate_connector.py`, `tests/` |

## Safe Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda policy check
```

The default skeleton does not crawl 4PDA. Crawling requires explicit operator
intent, a bounded profile, and external storage roots.

## External Storage

Set storage roots before any crawl or index build:

```bash
export CONNECTOR_DATA_ROOT=/mnt/external/abyss-connectors/4pda/data
export CONNECTOR_CACHE_ROOT=/mnt/external/abyss-connectors/4pda/cache
export CONNECTOR_ARTIFACT_ROOT=/mnt/external/abyss-connectors/4pda/artifacts
```

These roots are intentionally outside the repository.

## Search Posture

The connector must not use 4PDA internal search as a crawler API. Instead it
builds local search from allowed public topic/post snapshots:

```text
public topic pages -> normalized posts -> chunks -> BM25/vector/entity/graph
indexes -> evidence packets with source URLs
```

## Current Status

Starter pipeline is available: bounded public topic crawl, normalization,
keyword index, tiny graph export, query, and evidence-packet export. It remains
starter-grade: no attachment downloads, no internal 4PDA search, no broad
section discovery, no vector index, and no full-corpus mode.
