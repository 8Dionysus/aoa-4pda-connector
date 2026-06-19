# Storage Roots

The connector keeps data mass outside Git history. It can write small starter
runs to ignored repo-local state, then move larger runs to external storage.

## Roots

```text
CONNECTOR_DATA_ROOT       raw public snapshots and normalized corpus
CONNECTOR_CACHE_ROOT      rebuildable indexes and parser caches
CONNECTOR_ARTIFACT_ROOT   graph DBs, evidence exports, run receipts
```

If these variables are unset, the CLI uses:

```text
.connector-state/data
.connector-state/cache
.connector-state/artifacts
```

That repo-local root is portable and ignored by Git. It is meant for starter
or bounded local work, not for full corpus growth.

## Recommended Local Route

Start with `.connector-state/` when the expected data size is small and the
machine has enough local disk. For larger runs, prefer an operator-approved
external disk/NAS/object store. If using host-managed AbyssOS storage, follow
`/etc/abyss-machine/storage-policy.json`.

## Repository Boundary

The repository may contain synthetic fixtures, tiny examples, and the
`.connector-state/` empty scaffold only. It must not commit real full corpora,
graph databases, vector stores, or full exports.
