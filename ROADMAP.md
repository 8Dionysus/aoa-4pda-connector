# Roadmap

## Wave 0: Skeleton

- repository route cards
- source and storage policy
- CLI skeleton
- schemas and synthetic fixtures
- validator and tests

## Wave 1: Starter Corpus

- policy-confirmed starter crawl over 10-30 public topic pages
- normalized topic/post snapshots
- local BM25 search over starter data
- evidence packet query route

## Wave 2: Deep Search

- chunking and exact-token search for device models, firmware versions, and
  error strings
- entity extraction for devices, apps, versions, firmware, warnings, and fixes
- vector search adapter behind an optional dependency

## Wave 3: Graph Evidence

- graph node/edge builder
- issue/fix/warning relation extraction
- graph query packets

## Wave 4: Runtime Access

- `abyss-stack` MCP/runtime adapter that consumes installed connector roots
  without moving corpora into Git

