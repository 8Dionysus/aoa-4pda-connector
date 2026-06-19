# Eval Suites

Local eval suites for connector retrieval quality live here.

The first active suite is `starter_search_quality.json`, a starter set of
public-safe synthetic queries that verify:

- exact model/version matching
- issue/fix retrieval
- source URL preservation
- no internal-search dependency
- chunk-level evidence refs

Run it with:

```bash
aoa-4pda eval search-quality
```

This is local connector evidence only. Central proof authority remains in
`aoa-evals`.
