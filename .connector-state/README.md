# Repo-Local State

This is the default local state root used when `CONNECTOR_DATA_ROOT`,
`CONNECTOR_CACHE_ROOT`, and `CONNECTOR_ARTIFACT_ROOT` are not set.

```text
.connector-state/
  data/       raw public snapshots and normalized records
  cache/      rebuildable indexes and parser/cache state
  artifacts/  graph exports, receipts, and evidence packets
```

Only this scaffold is tracked. Generated files are ignored by Git.

For larger runs, point the three variables at an operator-approved external
storage layout. `connector/STORAGE_POLICY.md` owns the variable semantics and
the CLI storage surface owns exact inspection and initialization syntax.
