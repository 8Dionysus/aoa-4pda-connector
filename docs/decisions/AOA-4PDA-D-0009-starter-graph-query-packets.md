# AOA-4PDA-D-0009: Starter Graph Query Packets

- Status: accepted
- Date: 2026-06-19

## Context

`AOA-4PDA-D-0008` added starter `fixes_issue` and `warns_about` relation
edges. The next useful consumer-facing step is to expose those edges in local
query results so an agent can answer "what fixes this issue?" or "what is this
warning about?" without manually reading the graph export.

The connector must keep source URLs, post refs, and local retrieval evidence as
the answer authority. The graph remains a derived navigation layer and the local
eval port remains connector-owned, not central proof authority.

## Decision

Add starter graph query packets:

- `aoa-4pda query-graph` reads an already-built local keyword index and graph
  export from external storage receipts.
- The command runs the existing BM25/exact local query and enriches each result
  with `graph_context`.
- `graph_context` is post-local: it includes entity nodes mentioned by the
  matched post plus source-ref-matching `fixes_issue` and `warns_about` edges
  touching those entities.
- `aoa-4pda eval graph-query-packets` checks the graph-enriched evidence packet
  shape against a sanitized live-shaped fixture without touching the network.

The packet keeps `schema: aoa_4pda_evidence_packet_v1` and adds graph fields
additively rather than creating a separate graph-answer truth surface.

## Alternatives Considered

- Create a separate graph answer schema. Rejected for the starter slice because
  it would split source refs, score reports, and graph context across two answer
  surfaces before the relation model is mature.
- Keep relation edges only in graph exports. Rejected because agents would need
  custom traversal logic before they can use the relation layer in answers.

## Consequences

- Agents can consume one evidence packet containing search ranking, source refs,
  and starter relation context.
- The result is still starter-grade: relation context is limited to source-ref
  matching post-local edges and does not perform global graph reasoning.
- `AOA-4PDA-D-0010` records the deterministic answer packet renderer built on
  top of this graph-enriched evidence packet.
- Future graph traversal can add broader context, but must keep source refs and
  policy boundaries visible in the answer packet.

## Boundaries

- `aoa-4pda-connector` owns the local packet enrichment, CLI command, suite, and
  compact eval report.
- `aoa-evals` remains the proof owner for central verdicts, scoring authority,
  and regression truth.
- No live crawl, internal search route, attachment route, vector index, graph
  database, or generated artifact is introduced by this decision.
- The graph context is evidence navigation over cited posts, not a claim that a
  fix or warning applies outside the source post.

## Source Surfaces

- `src/aoa_4pda_connector/query/__init__.py`
- `src/aoa_4pda_connector/cli.py`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `evals/suites/starter_graph_query_packets.json`
- `tests/unit/test_graph_query_packet.py`
- `docs/QUERY_MODEL.md`
- `docs/GRAPH_MODEL.md`
