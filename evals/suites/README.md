# Eval Suites

Local eval suites for connector retrieval quality live here.

The active starter suites are:

- `starter_search_quality.json`, a public-safe synthetic query suite
- `starter_graph_relations.json`, a sanitized live-shaped graph relation suite

Together they verify:

- exact model/version matching
- issue/fix retrieval
- source URL preservation
- no internal-search dependency
- chunk-level evidence refs
- post-to-entity graph edges for issue, fix, warning, file, and tool evidence
- starter `fixes_issue` and `warns_about` relation edges

Run it with:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
```

This is local connector evidence only. Central proof authority remains in
`aoa-evals`.
