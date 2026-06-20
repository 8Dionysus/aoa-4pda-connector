# AOA-4PDA-D-0014: Focused Xiaomi 13T Profile

- Status: accepted
- Date: 2026-06-20

## Context

The connector has a starter pipeline and local retrieval evals, but useful
deep search needs a bridge from tiny smoke data to a bounded real device
corpus. A broad crawl would make review, storage, and quality control worse.

The operator selected Xiaomi 13T as the first focused device target. The repo
must remain public and portable, so it cannot hard-code personal vault paths or
commit generated indexes, graph databases, or raw snapshots.

## Decision

Add Xiaomi 13T as the first focused-device profile:

- `connector/profiles/xiaomi-13t.yaml` owns the concrete profile route
- `connector/profiles/focused-device.yaml` points at the current focused
  target as an alias
- `connector/seeds/xiaomi_13t_topics.yaml` owns the bounded public seed
  windows, including high-signal firmware `st=` offsets
- `aoa-4pda profile inspect xiaomi-13t` reports the route, limits, seeds,
  storage roots, and policy checks without touching the network
- `evals/suites/live_xiaomi_13t_search_quality.json` provides the focused
  no-crawl quality gate for already-materialized runs
- external storage docs use a portable connector-family layout rooted at
  `/path/to/connector-databases`, not host-personal paths

## Consequences

- The next live run can be bounded to Xiaomi 13T discussion, firmware,
  firmware high-signal windows, battery/runtime, and accessories topics.
- Agents can inspect the profile and storage route before any crawl.
- The public repo contains method, seeds, profile contracts, and evals, while
  heavy data remains in configured storage.
- Future device profiles can copy the instance pattern without changing the
  storage runtime contract.

## Boundaries

- Do not run a live crawl merely because the profile exists.
- Do not use 4PDA internal search as a crawler/API.
- Do not download attachments or private/account-gated content.
- Do not commit raw captures, indexes, graph databases, vector stores, or full
  exports.
- Do not hard-code local vault, home, or machine-specific paths in public docs.

## Source Surfaces

- `connector/profiles/xiaomi-13t.yaml`
- `connector/profiles/focused-device.yaml`
- `connector/seeds/xiaomi_13t_topics.yaml`
- `evals/suites/live_xiaomi_13t_search_quality.json`
- `src/aoa_4pda_connector/cli.py`
- `docs/EXTERNAL_STORAGE.md`
- `docs/OPERATIONS.md`
