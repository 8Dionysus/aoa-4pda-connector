# aoa-4pda-connector

`aoa-4pda-connector` is a GitHub-publishable skeleton for an AoA external
connector that can build local, policy-gated search and graph evidence from
public 4PDA topic/post pages.

It stores method, code, schemas, policy, tiny fixtures, seed profiles, eval
queries, an install route, and an ignored repo-local state scaffold. It does
not commit full crawls, raw corpora, large indexes, vector stores, or graph
databases.

## What This Repository Does

| Function | Surface |
| --- | --- |
| Connector identity and boundaries | `CHARTER.md`, `BOUNDARIES.md` |
| Agent route and validation | `AGENTS.md` |
| Source and crawl policy | `connector/SOURCE_POLICY.md`, `connector/manifests/route_allowlist.yaml` |
| Storage contract | `connector/STORAGE_POLICY.md`, `.env.example` |
| Repo-local state scaffold | `.connector-state/` |
| Executable skeleton | `src/aoa_4pda_connector/` |
| CLI entrypoint | `aoa-4pda` |
| Schemas | `connector/schemas/` |
| Synthetic fixtures | `connector/fixtures/` |
| Local eval port | `evals/PORT.yaml`, `evals/suites/` |
| Starter profiles and seeds | `connector/profiles/`, `connector/seeds/` |
| Install and proof routes | `docs/INSTALL.md`, `docs/AGENT_INSTALL_ROUTE.md`, `docs/STARTER_PROOF.md` |
| Validation | `scripts/validate_connector.py`, `tests/` |

## Safe Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda storage status
aoa-4pda policy check
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

The default skeleton does not crawl 4PDA. Crawling requires explicit operator
intent and a bounded profile. If storage roots are not configured, the CLI uses
the ignored repo-local `.connector-state/` root for small starter runs.

## Storage Roots

By default, generated connector state goes to ignored repo-local storage:

```bash
aoa-4pda init --apply
```

This creates or confirms:

```text
.connector-state/data
.connector-state/cache
.connector-state/artifacts
```

For larger runs, override the roots with external storage:

```bash
export CONNECTOR_DATA_ROOT=/path/to/storage/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/storage/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/storage/aoa-4pda-connector/artifacts
```

The `.connector-state/` scaffold is tracked, but generated content inside it is
ignored by Git.

To create a tiny no-network local database for smoke testing:

```bash
aoa-4pda materialize fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
```

## Search Posture

The connector must not use 4PDA internal search as a crawler API. Instead it
builds local search from allowed public topic/post snapshots:

```text
public topic pages -> normalized posts -> evidence chunks -> BM25 + exact local index
-> graph/entity layers -> evidence packets with source URLs and query reports
```

## Current Status

Starter pipeline is available: offline fixture proof, bounded public topic
crawl, normalization, BM25/exact keyword index, tiny graph export, query report,
heuristic entity extraction, stable evidence-packet ids, evidence-packet export,
live-shaped parser fixtures, author/date extraction, quote/edit/signature noise
cleanup, chunk-level evidence search, and a live starter proof over configured
storage. It also has a no-network fixture materialization route, local starter
search and graph eval packs, and a live search-quality eval for already-built
bounded starter runs. The evals check expected top evidence, graph entity edges,
starter relation edges, and live-run specific-term retrieval. Starter graph
query packets can enrich top local search results with post-local `fixes_issue`
and `warns_about` context from the graph. Starter answer packets render that
graph context into deterministic issue/fix/warning summaries for agents. It
remains starter-grade: no attachment downloads, no internal 4PDA search, no
broad section discovery, no vector index, and no full-corpus mode.

## Local Eval Route

`evals/` is a repo-local evidence port. It owns connector-specific suites,
small public-safe cases, and compact runner reports. Central proof doctrine,
accepted verdicts, scoring authority, and regression truth stay in `aoa-evals`.

Run the starter retrieval eval:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

After a bounded live starter run has been crawled, normalized, and indexed, run
the live search-quality gate:

```bash
aoa-4pda eval live-search-quality --run latest
```

The no-network evals build temporary chunk/index/graph artifacts from synthetic
or sanitized fixtures and delete them after the run. The live search-quality
eval reads existing configured storage receipts and the named keyword index; it
does not crawl, commit generated artifacts, or create central proof verdicts.
