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
| Profile discovery, seed review, coverage, and refresh audits | `docs/DISCOVERY.md`, `docs/SEED_REVIEW.md`, `docs/COVERAGE.md`, `docs/REFRESH.md` |
| Readiness and runtime handoff | `docs/CONNECTOR_READY.md`, `docs/RUNTIME_CONTRACT.md`, `docs/MCP_ROLLOUT.md` |
| Validation | `scripts/validate_connector.py`, `tests/` |

## Safe Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/verify_agent_install_route.py
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda storage status
aoa-4pda policy check
aoa-4pda profile inspect xiaomi-13t
aoa-4pda profile inspect redmi-note-10-pro
aoa-4pda ready
aoa-4pda discovery audit xiaomi-13t
aoa-4pda discovery review xiaomi-13t
aoa-4pda coverage audit xiaomi-13t
aoa-4pda refresh audit xiaomi-13t
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval hybrid-query-packets
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
export CONNECTOR_FAMILY_ROOT=/path/to/connector-databases
export CONNECTOR_INSTANCE_ROOT="$CONNECTOR_FAMILY_ROOT/aoa-4pda-connector"
export CONNECTOR_DATA_ROOT="$CONNECTOR_INSTANCE_ROOT/data"
export CONNECTOR_CACHE_ROOT="$CONNECTOR_INSTANCE_ROOT/cache"
export CONNECTOR_ARTIFACT_ROOT="$CONNECTOR_INSTANCE_ROOT/artifacts"
```

The `.connector-state/` scaffold is tracked, but generated content inside it is
ignored by Git.

To create a tiny no-network local database for smoke testing:

```bash
aoa-4pda materialize fixture
aoa-4pda query-hybrid "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
```

## Focused Device Route

The first focused-device profile is Xiaomi 13T:

```bash
aoa-4pda profile inspect xiaomi-13t
```

The profile uses `connector/seeds/xiaomi_13t_topics.yaml` and starts from
public seed windows for discussion, firmware, battery/runtime issues, and
accessories. The current seed plan is expanded from the Xiaomi 13T discovery
review manifest: it contains 23 bounded seed entries and 70 expected public
topic pages. Firmware seeds include high-signal `st=` offsets for `boot.img`,
`recovery.img`, TWRP, and HyperOS material instead of only the first pages of
the topic. It preserves aliases such as `aristotle`,
`2306EPN60G`, `2306EPN60R`, and `XIG04` for local deep search. It does not
crawl until the operator explicitly runs `aoa-4pda crawl --profile xiaomi-13t`.
Run `aoa-4pda coverage audit xiaomi-13t` before and after materialization to
see which seed windows, focus areas, receipts, indexes, and graph artifacts are
actually present in configured storage. Run `aoa-4pda refresh audit xiaomi-13t`
to check receipt age, derived artifact freshness, and the bounded refresh plan
without touching the network. Run `aoa-4pda discovery audit xiaomi-13t` to
surface review-priority public topic/window candidates already visible in
stored snapshots before expanding seeds. Discovery excludes seed-plan windows
that are already covered by `max_pages`, and reports those separately as
covered seed windows instead of treating them as gaps. Run
`aoa-4pda discovery review xiaomi-13t` to compare those candidates with
`connector/seeds/reviews/xiaomi_13t_discovery_review.json` before editing seed
scope.
For the materialized reference run, keyword ranking-pressure checks protect
top-N recall, while graph-query and answer gates own relation-aware top ranking
for hard root/recovery questions.

The second representative focused-device profile is prepared for Redmi Note
10 Pro:

```bash
aoa-4pda profile inspect redmi-note-10-pro
```

It reuses reviewed public starter-topic routes as its own bounded seed windows
for `sweet`, `boot.img`, `recovery.img`, Magisk, TWRP, and MIUI retrieval
coverage. Its local quality gate is
`evals/suites/live_redmi_note_10_pro_search_quality.json`, which reads an
already-materialized run and does not crawl or commit generated artifacts.

## Search Posture

The connector must not use 4PDA internal search as a crawler API. Instead it
builds local search from allowed public topic/post snapshots:

```text
public topic pages -> normalized posts -> evidence chunks -> BM25 + exact local index
-> deterministic local vector index -> graph/entity layers
-> evidence packets with source URLs and query reports
```

## Current Status

Starter pipeline is available: offline fixture proof, bounded public topic
crawl, normalization, BM25/exact keyword index, deterministic no-model vector
index, graph-aware hybrid keyword/vector query packets, tiny graph export, query report,
heuristic entity extraction, stable evidence-packet ids, evidence-packet export,
live-shaped parser fixtures, author/date extraction, quote/edit/signature noise
cleanup, chunk-level evidence search, technical token aliases, a concrete
Xiaomi 13T focused-device profile, and a live starter proof over configured
storage. It also has a no-network fixture materialization route, local starter
search/graph/hybrid/answer eval packs, and live quality evals for already-built
bounded starter and Xiaomi 13T runs. The evals check expected top evidence,
graph entity edges, starter relation edges, deterministic vector score
participation, relation-aware hybrid recovery/root ranking, split
file/version/model normalization, live-run specific-term retrieval, live hybrid
rank pressure, and Xiaomi root/recovery answer labels.
Starter graph query packets
can enrich top local search results with post-local `fixes_issue`,
`warns_about`, root, recovery, file, tool, and firmware context from the graph.
Starter hybrid packets merge keyword and deterministic vector scores, then add
a bounded boost for matching root/recovery graph relations while preserving
graph context and source URLs. Starter answer packets render that
graph context into deterministic issue/fix/warning and root/recovery summaries
for agents. `aoa-4pda ready` audits the repository against the
`connector-ready-v1` maturity target, while `aoa-4pda discovery audit
xiaomi-13t`, `aoa-4pda discovery review xiaomi-13t`,
`aoa-4pda coverage audit xiaomi-13t`, and `aoa-4pda refresh audit xiaomi-13t`
audit the first reference profile against `reference-profile-discovery-v1`,
`reference-profile-seed-review-v1`, `reference-profile-coverage-v1`, and
`reference-profile-refresh-v1`. Discovery candidates include anchor/source
evidence, target-term hits, and review priority, while already-covered
seed-plan windows are excluded from the candidate list. Review reports accepted
candidates that are still pending seed updates. All five report
remaining gaps without touching the network. It remains starter-grade: no
attachment downloads, no internal 4PDA search, no broad section discovery, no
external embedding/model dependency, and no full-corpus mode.
When discovery still reports unreviewed Xiaomi 13T candidates, or accepted
candidates are not yet reflected in seeds, `aoa-4pda ready` stays `not_ready`
through `reference_profile_seed_review_state`; that is the expected loop
signal, not an install failure.
After the reviewed seed expansion, `reference_profile_seed_review_state` can be
clean while `reference_profile_coverage_state` remains `partial` until the
expanded 70-page plan is crawled and rebuilt.
After that plan is materialized, ordinary new numbered page-window links are
treated as deferred expansion pressure unless an exact review decision accepts
them into seed scope.

A local configured-storage reference run, `20260621T194521Z__crawl`, has
materialized the reviewed Xiaomi 13T seed plan: 23/23 seeds, 70/70 public
pages, 1,448 normalized posts, 1,559 indexed chunks/posts, 8,016 index terms,
1,559 deterministic vector chunk docs, 26,701 vector features, 1,508 graph
nodes, and 2,855 graph edges. Against that named run, search,
ranking-pressure, live hybrid, graph-query, and answer gates are green for the
current information-need matrix: 10/10 Xiaomi 13T classes are covered by local
eval routes, including battery/power, camera, purchase/variants, firmware
source, and late-window regression watch. The generated raw snapshots, indexes,
vectors, graphs, and receipts are intentionally ignored local state, not
committed repository content.

## Local Eval Route

`evals/` is a repo-local evidence port. It owns connector-specific suites,
small public-safe cases, and compact runner reports. Central proof doctrine,
accepted verdicts, scoring authority, and regression truth stay in `aoa-evals`.

Run the starter retrieval eval:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval hybrid-query-packets
aoa-4pda eval answer-packets
aoa-4pda eval answer-packets --suite evals/suites/xiaomi_13t_answer_packets.json
```

After a bounded live starter run has been crawled, normalized, and indexed, run
the live search-quality gate:

```bash
aoa-4pda eval live-search-quality --run latest
```

For a Xiaomi 13T run, use the focused suite:

```bash
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_search_quality.json
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_ranking_pressure.json
aoa-4pda eval live-hybrid-query-quality --run latest --suite evals/suites/live_xiaomi_13t_hybrid_query_quality.json
aoa-4pda eval live-graph-query-quality --run latest --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run latest --suite evals/suites/live_xiaomi_13t_answer_quality.json
```

The no-network evals build temporary chunk/index/vector/graph artifacts from
synthetic or sanitized fixtures and delete them after the run. The live search,
graph-query, hybrid, and answer routes read existing configured storage
receipts and named keyword/vector/graph artifacts; they do not crawl, commit
generated artifacts, or create central proof verdicts.
