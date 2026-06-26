# Eval Suites

Local eval suites for connector retrieval quality live here.

The active starter suites are:

- `starter_search_quality.json`, a public-safe synthetic query suite
- `starter_graph_relations.json`, a sanitized live-shaped graph relation suite
- `starter_graph_query_packets.json`, a graph-enriched query packet suite
- `starter_answer_packets.json`, a deterministic rendered answer packet suite
- `starter_claim_conflict_relations.json`, a portable claim/conflict graph
  relation suite over a sanitized multi-post fixture
- `starter_claim_answer_packets.json`, a rendered answer suite for
  conflict/freshness/applicability/warning reports
- `live_starter_search_quality.json`, a named-run search quality suite for
  already-built bounded live starter indexes
- `live_xiaomi_13t_search_quality.json`, a focused named-run search quality
  suite for already-built Xiaomi 13T indexes
- `live_xiaomi_13t_ranking_pressure.json`, a focused named-run top-N
  ranking/recall pressure suite for already-built Xiaomi 13T indexes
- `live_xiaomi_13t_graph_query_quality.json`, a focused named-run graph-query
  suite for already-built Xiaomi 13T index and graph artifacts
- `live_redmi_note_10_pro_search_quality.json`, a prepared second focused
  named-run search suite for already-built Redmi Note 10 Pro indexes
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
- claim/method/context/warning nodes, supersedes/contradicts/contextualizes
  relation edges, and relation audit metadata
- conflict, freshness, applicability, warning reports, claim ids, read-only
  policy, and no-network answer packets
- live-run exact and specific-term retrieval over existing configured storage
- live-run Xiaomi 13T top-N recall for hard OrangeFox, vendor_boot, KernelSU,
  and HyperOS recovery queries
- live-run Xiaomi 13T graph-query packets with root/recovery relation context
  and relation-intent rerank diagnostics
- prepared Redmi Note 10 Pro search over `sweet`, `boot.img`, `recovery.img`,
  Magisk/TWRP-oriented seed windows
- Xiaomi 13T root/recovery/file/tool/firmware labels in deterministic answer
  packets
- Xiaomi 13T current-method freshness checks, brick/bootloop gap handling,
  warning-intent guardrails, and out-of-scope insufficient-evidence behavior
- live answer diagnostics with failed checks, matched query terms, score
  breakdowns, compact top evidence, keyword/graph ranks, answer context label
  counts, freshness context, deterministic cited agent-answer brief,
  evidence-chain handoff, nuance report, and relation edges

Run it with:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
aoa-4pda eval claim-relations
aoa-4pda eval claim-answer-packets
aoa-4pda eval answer-packets --suite evals/suites/xiaomi_13t_answer_packets.json
aoa-4pda eval live-search-quality --run <run-id>
aoa-4pda eval live-search-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_search_quality.json
aoa-4pda eval live-search-quality --run <run-id> --suite evals/suites/live_redmi_note_10_pro_search_quality.json
aoa-4pda eval live-search-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_ranking_pressure.json
aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json
aoa-4pda eval graph-relations --suite evals/suites/xiaomi_13t_graph_relations.json
```

This is local connector evidence only. Central proof authority remains in
`aoa-evals`.
