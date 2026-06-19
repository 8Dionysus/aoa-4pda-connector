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

For larger runs, point the environment variables at external storage instead:

```bash
export CONNECTOR_DATA_ROOT=/path/to/storage/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/storage/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/storage/aoa-4pda-connector/artifacts
```

