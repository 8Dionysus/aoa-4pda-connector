# Roadmap

## Wave 0: Skeleton

- repository route cards
- source and storage policy
- CLI skeleton
- schemas and synthetic fixtures
- validator and tests

## Wave 1: Starter Corpus

- offline starter proof over synthetic fixtures
- policy-confirmed starter crawl over 10-30 public topic pages
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

## Wave 2: Deep Search

- stronger exact-token search for device models, firmware versions, and error
  strings
- stronger entity extraction for devices, apps, versions, firmware, warnings,
  and fixes
- vector search adapter behind an optional dependency
- retrieval eval expansion against bounded external-storage starter runs

## Wave 3: Graph Evidence

- graph node/edge builder
- broader issue/fix/warning relation extraction beyond starter heuristics
- broader graph query traversal beyond starter post-local packets

## Wave 4: Runtime Access

- `abyss-stack` MCP/runtime adapter that consumes installed connector roots
  without moving corpora into Git
