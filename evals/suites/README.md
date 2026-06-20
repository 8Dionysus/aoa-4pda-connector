# Eval Suites

Local eval suites for connector retrieval quality live here.

The active starter suites are:

- `starter_search_quality.json`, a public-safe synthetic query suite
- `starter_graph_relations.json`, a sanitized live-shaped graph relation suite
- `starter_graph_query_packets.json`, a graph-enriched query packet suite
- `starter_answer_packets.json`, a deterministic rendered answer packet suite
- `live_starter_search_quality.json`, a named-run search quality suite for
  already-built bounded live starter indexes
- `live_xiaomi_13t_search_quality.json`, a focused named-run search quality
  suite for already-built Xiaomi 13T indexes
- `live_xiaomi_13t_graph_query_quality.json`, a focused named-run graph-query
  suite for already-built Xiaomi 13T index and graph artifacts
- `xiaomi_13t_graph_relations.json`, a focused public-safe graph relation
  suite for Xiaomi 13T firmware/root/recovery evidence
- `xiaomi_13t_answer_packets.json`, a focused public-safe rendered answer
  packet suite for Xiaomi 13T root/recovery evidence
- `live_xiaomi_13t_answer_quality.json`, a focused named-run rendered answer
  suite for already-built Xiaomi 13T index and graph artifacts

Together they verify:

- exact model/version matching
- split technical token normalization for file names, firmware versions, model
  strings, and starter device aliases
- issue/fix retrieval
- source URL preservation
- no internal-search dependency
- chunk-level evidence refs
- post-to-entity graph edges for issue, fix, warning, file, and tool evidence
- starter `fixes_issue` and `warns_about` relation edges
- focused Xiaomi 13T entity nodes and root/recovery relation edges
- relation-aware `graph_context` in evidence packet results
- issue/fix/warning labels and answer text in rendered answer packets
- live-run exact and specific-term retrieval over existing configured storage
- live-run Xiaomi 13T graph-query packets with root/recovery relation context
- Xiaomi 13T root/recovery/file/tool/firmware labels in deterministic answer
  packets

Run it with:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
aoa-4pda eval answer-packets --suite evals/suites/xiaomi_13t_answer_packets.json
aoa-4pda eval live-search-quality --run <run-id>
aoa-4pda eval live-search-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_search_quality.json
aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json
aoa-4pda eval graph-relations --suite evals/suites/xiaomi_13t_graph_relations.json
```

This is local connector evidence only. Central proof authority remains in
`aoa-evals`.
