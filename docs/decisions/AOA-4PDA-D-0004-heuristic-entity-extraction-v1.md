# AOA-4PDA-D-0004 Heuristic Entity Extraction v1

Status: accepted
Date: 2026-06-18

## Decision

Add a dependency-free heuristic entity extraction layer to normalized posts and
kind-scoped entity nodes in the starter graph.

Entity extraction v1 covers:

- devices
- codenames
- firmware families and versions
- build IDs
- tools
- files
- issues
- fixes
- warnings

## Rationale

The connector needs graph evidence that is more useful than topic-post links.
The next durable step is to extract common 4PDA technical facts from public post
text while keeping the repository small, testable, and safe for fresh clones.

Regexes and small local dictionaries are enough for the first graph layer. They
also keep the boundary clear: this is navigation evidence, not a final semantic
classifier.

## Consequences

- Normalized posts can carry richer entity arrays.
- Graph nodes are now scoped as `entity:<kind>:<value>` to avoid collisions
  between different entity kinds.
- Graph edges remain `post_mentions_entity` in this slice; stronger relation
  extraction such as `fixes_issue` remains later work.
- `AOA-4PDA-D-0008` later adds starter relation edges v1 while keeping this
  entity extraction decision as the base layer.

## Boundaries

- No network access.
- No ML model or vector dependency.
- No external dictionary download.
- No generated graph artifacts committed to Git.
- Source URLs and post IDs remain the evidence anchor.

## Source Surfaces

- `src/aoa_4pda_connector/normalize/__init__.py`
- `src/aoa_4pda_connector/graph/__init__.py`
- `tests/unit/test_entities_and_graph.py`
- `docs/GRAPH_MODEL.md`
- `connector/fixtures/normalized/synthetic_topic.json`
