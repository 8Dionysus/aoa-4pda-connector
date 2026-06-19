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
- local BM25 and exact-token search over starter data
- heuristic entity extraction for starter graph nodes
- evidence packet query route

## Wave 2: Deep Search

- chunking and stronger exact-token search for device models, firmware
  versions, and error strings
- stronger entity extraction for devices, apps, versions, firmware, warnings,
  and fixes
- vector search adapter behind an optional dependency

## Wave 3: Graph Evidence

- graph node/edge builder
- issue/fix/warning relation extraction
- graph query packets

## Wave 4: Runtime Access

- `abyss-stack` MCP/runtime adapter that consumes installed connector roots
  without moving corpora into Git
