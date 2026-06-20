# Eval Suites

Local eval suites for connector retrieval quality live here.

The active starter suites are:

- `starter_search_quality.json`, a public-safe synthetic query suite
- `starter_graph_relations.json`, a sanitized live-shaped graph relation suite
- `starter_graph_query_packets.json`, a graph-enriched query packet suite
- `starter_answer_packets.json`, a deterministic rendered answer packet suite
- `live_starter_search_quality.json`, a named-run search quality suite for
  already-built bounded live starter indexes

Together they verify:

- exact model/version matching
- issue/fix retrieval
- source URL preservation
- no internal-search dependency
- chunk-level evidence refs
- post-to-entity graph edges for issue, fix, warning, file, and tool evidence
- starter `fixes_issue` and `warns_about` relation edges
- relation-aware `graph_context` in evidence packet results
- issue/fix/warning labels and answer text in rendered answer packets
- live-run exact and specific-term retrieval over existing configured storage

Run it with:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
aoa-4pda eval live-search-quality --run <run-id>
```

This is local connector evidence only. Central proof authority remains in
`aoa-evals`.
