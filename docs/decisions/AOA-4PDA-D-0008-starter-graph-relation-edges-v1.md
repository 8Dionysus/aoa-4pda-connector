# AOA-4PDA-D-0008: Starter Graph Relation Edges v1

- Status: accepted
- Date: 2026-06-19

## Context

The graph already has kind-scoped entity nodes and a local graph relation eval
that proves expected entities stay attached to the source post. The next useful
step is to add small relation edges so graph navigation can answer basic
"what fixes this issue?" and "what is this warning about?" questions.

The relation layer must stay dependency-free, source-ref-preserving, and safe
for fresh clones. It must not pretend to be a central proof verdict.

## Decision

Add starter relation edges v1:

- `fixes_issue`: from a `fix` entity to an `issue` entity mentioned in the same
  post.
- `warns_about`: from a `warning` entity to file, codename, device, firmware,
  or build entities explicitly named inside the warning text.

The relation edges keep the source post refs and use lower confidence than
topic/post structure. The local graph eval now checks both post-to-entity edges
and these starter relation edges.

## Consequences

- Graph consumers can navigate from fixes to issues and warnings to affected
  artifacts without waiting for a full semantic relation extractor.
- The rule is intentionally post-local and heuristic, so recall is limited.
- `AOA-4PDA-D-0009` records the first answer-packet consumer of these relation
  edges.
- Future stronger extraction can replace or augment this layer with richer
  evidence, but must preserve source refs and eval coverage.

## Boundaries

- No ML model, external dictionary, live crawl, internal search route, or
  generated graph artifact is introduced.
- `aoa-4pda-connector` owns the local relation heuristic and eval cases.
- `aoa-evals` remains the proof owner for central verdicts, scoring authority,
  and regression truth.
- These edges are navigation hints, not claims that a fix is universally correct
  or a warning applies outside the cited post.

## Source Surfaces

- `src/aoa_4pda_connector/graph/__init__.py`
- `evals/suites/starter_graph_relations.json`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `tests/unit/test_entities_and_graph.py`
- `docs/GRAPH_MODEL.md`
