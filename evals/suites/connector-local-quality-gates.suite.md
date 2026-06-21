---
schema_version: local_eval_suite_note_v1
owner_repo: aoa-4pda-connector
status: reviewed
authority_boundary: no verdict, scoring, regression, or proof doctrine authority
---

# Connector Local Quality Gates

## Scope

This local suite note records the active connector-local quality gates already
implemented as JSON runner suites under `evals/suites/`.

The JSON files remain connector-native runner inputs. This note only gives the
OS Abyss local eval-port inventory a standard local pressure surface so the
port can be classified as active without turning connector-local checks into
central `aoa-evals` proof.

## Active Suite Families

- `starter_search_quality.json` protects public-safe retrieval over synthetic
  normalized topic fixtures.
- `starter_graph_relations.json` and `xiaomi_13t_graph_relations.json` protect
  public-safe graph relation extraction.
- `starter_graph_query_packets.json` protects graph-enriched evidence packet
  shape.
- `starter_answer_packets.json` and `xiaomi_13t_answer_packets.json` protect
  deterministic rendered answer packets.
- `live_*` suites read already-materialized bounded configured-storage runs for
  starter, Xiaomi 13T, and Redmi Note 10 Pro profile quality checks.

## Owner Boundary

`aoa-4pda-connector` owns the local suite files, fixtures, CLI runner behavior,
and compact local notes. `aoa-evals` owns central proof doctrine, accepted
verdicts, scoring, regression truth, and any future central bundle adoption.

Live suites must keep their no-crawl posture: they may read existing configured
storage receipts and artifacts, but they must not fetch 4PDA pages or commit
generated corpora, indexes, graph databases, or repeated large reports.
