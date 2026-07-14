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

## Connector Family Layout

For external storage, keep a head folder for connector databases and place each
connector under its own instance root, then map that instance's data, cache,
and artifact subdirectories to the three `CONNECTOR_*_ROOT` variables.

This shape works for a local disk, NAS, object-store mount, or operator-managed
vault. Public docs must keep `/path/to/...` placeholders instead of personal
machine paths. Host-specific mounts belong in local shell config, not in Git.

The CLI storage surface owns active-route inspection and optional size
measurement before data is created or rotated.

## Recommended Local Route

Start with `.connector-state/` when the expected data size is small and the
machine has enough local disk. For larger runs, prefer an operator-approved
external disk/NAS/object store. If using host-managed AbyssOS storage, follow
`/etc/abyss-machine/storage-policy.json`.

Before the first focused run, inspect both the storage route and the selected
profile through their CLI surfaces. Exact invocation syntax remains owned by
the CLI help and `AGENTS.md`.

## Repository Boundary

The repository may contain synthetic fixtures, tiny examples, and the
`.connector-state/` empty scaffold only. It must not commit real full corpora,
graph databases, vector stores, or full exports.
