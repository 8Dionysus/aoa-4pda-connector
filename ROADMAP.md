# Roadmap

## Wave 0: Skeleton

- repository route cards
- source and storage policy
- ignored repo-local state scaffold
- CLI skeleton
- schemas and synthetic fixtures
- validator and tests

## Wave 1: Starter Corpus

- offline starter proof over synthetic fixtures
- no-network materialized fixture database for fresh-clone query smoke tests
- policy-confirmed starter crawl over 10-30 public topics with bounded page
  offsets
- live starter proof over external storage artifacts
- normalized topic/post snapshots
- live-shaped sanitized parser fixtures
- chunking v1 for evidence chunks inside long posts
- local BM25 and exact-token search over starter data
- starter search eval pack for expected top evidence checks
- starter graph relation eval pack for issue/fix/warning entity-edge checks
- heuristic entity extraction for starter graph nodes
- heuristic `fixes_issue` and `warns_about` relation edges v1
- evidence packet query route
- starter graph query packets with post-local relation context
- starter answer packets rendered from graph-enriched evidence
- live starter search quality eval over named configured-storage runs

## Wave 2: Deep Search

- stronger exact-token search for device models, firmware versions, and error
  strings
  - starter technical token aliases for split file/version/model forms
- stronger entity extraction for devices, apps, versions, firmware, warnings,
  and fixes
- vector search adapter behind an optional dependency
- broader retrieval eval expansion against bounded external-storage runs

## Wave 3: Graph Evidence

- graph node/edge builder
- broader issue/fix/warning relation extraction beyond starter heuristics
- broader graph query traversal beyond starter post-local packets
- richer answer synthesis over multiple posts and relation paths

## Wave 4: Runtime Access

- `abyss-stack` MCP/runtime adapter that consumes installed connector roots
  without moving corpora into Git
