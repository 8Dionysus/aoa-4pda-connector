# AOA-4PDA-D-0007: Local Starter Graph Relation Eval Pack

- Status: accepted
- Date: 2026-06-19

## Context

Entity extraction v1 already creates issue, fix, warning, file, tool, and
codename nodes. The starter search eval protects retrieval ranking, but it does
not prove that parser/normalizer/graph output keeps these entities connected to
the source post.

The connector needs a small fresh-clone graph-quality check before stronger
relation extraction such as `fixes_issue` or `warns_about` is implemented.

## Decision

Add a local graph relation eval:

```bash
aoa-4pda eval graph-relations
```

The command reads `evals/suites/starter_graph_relations.json`, normalizes the
sanitized live-shaped HTML fixture, builds a temporary graph, and checks that
expected entity nodes and `post_mentions_entity` edges exist for issue, fix,
warning, file, and tool evidence. Temporary normalized and graph artifacts are
deleted after the run.

## Consequences

- Parser, normalizer, entity extraction, and graph builder are checked together
  through one public-safe fixture path.
- CI can catch graph regressions where an entity is extracted but no longer
  linked to the source post.
- This remains a starter graph-quality gate, not full relation extraction.

## Boundaries

- `aoa-4pda-connector` owns this local suite, runner, and compact report.
- `aoa-evals` remains the proof owner for doctrine, verdicts, scoring, and
  regression truth.
- No live crawl, internal search route, attachment route, generated graph
  artifact, or repeated report is committed.
- `fixes_issue` and `warns_about` stay future relation-extraction work; this
  decision only protects post-to-entity edges.

## Source Surfaces

- `evals/suites/starter_graph_relations.json`
- `connector/fixtures/html/live_shape_topic.html`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `docs/GRAPH_MODEL.md`
- `.github/workflows/validate.yml`
