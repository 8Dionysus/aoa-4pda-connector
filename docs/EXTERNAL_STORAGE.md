# External Storage

The connector expects data mass outside Git.

## Roots

```text
CONNECTOR_DATA_ROOT       raw public snapshots and normalized corpus
CONNECTOR_CACHE_ROOT      rebuildable indexes and parser caches
CONNECTOR_ARTIFACT_ROOT   graph DBs, evidence exports, run receipts
```

## Recommended Local Route

For local AbyssOS work, prefer an operator-approved external disk/NAS/object
store. If using host-managed storage, follow `/etc/abyss-machine/storage-policy.json`.

## Repository Boundary

The repository may contain synthetic fixtures and tiny examples only. It must
not contain real full corpora, graph databases, vector stores, or full exports.

