# Storage Policy

The repository stores method, small fixtures, and an ignored repo-local state
scaffold. Heavy mutable artifacts must stay outside Git history.

## Environment Roots

| Variable | Purpose |
| --- | --- |
| `CONNECTOR_DATA_ROOT` | raw public snapshots and normalized corpus data |
| `CONNECTOR_CACHE_ROOT` | rebuildable indexes and parser/cache state |
| `CONNECTOR_ARTIFACT_ROOT` | graph DBs, evidence exports, and run receipts |

Example:

```bash
export CONNECTOR_DATA_ROOT=.connector-state/data
export CONNECTOR_CACHE_ROOT=.connector-state/cache
export CONNECTOR_ARTIFACT_ROOT=.connector-state/artifacts
```

If these variables are unset, the CLI uses the same repo-local default rooted
at `.connector-state/`.

Use `aoa-4pda storage status` to inspect which route is active. Add
`--measure` when you need recursive file counts and byte totals.

## Repo-Local State

`.connector-state/` is allowed for small starter databases on machines where
repo-local storage is acceptable. It is tracked only as an empty scaffold:

```text
.connector-state/
  data/
  cache/
  artifacts/
```

Generated files inside `.connector-state/` are ignored by Git. Do not commit
raw captures, indexes, graph databases, vector stores, receipts, or full
exports from this tree.

## External Storage Route

For larger runs, point the roots to external storage:

```bash
export CONNECTOR_DATA_ROOT=/path/to/storage/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/storage/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/storage/aoa-4pda-connector/artifacts
```

## AbyssOS Machine Route

On AbyssOS machines, follow `/etc/abyss-machine/storage-policy.json`: large or
fast-growing connector data should use `/srv/abyss-machine/storage` or an
operator-approved external disk/NAS/object store, not `/` and not Git.

## Git Exclusions

The root `.gitignore` must exclude generated content under `.connector-state/`
plus raw data, indexes, graphs, full exports, SQLite databases, vector stores,
and cache directories.

## Fresh Clone Rule

`python scripts/validate_connector.py` and `aoa-4pda doctor` must work on a
fresh clone without external storage mounted. Missing environment roots should
fall back to `.connector-state/` until the operator chooses an external route.
`aoa-4pda materialize fixture` may create a tiny queryable local database under
the configured roots without touching the network.
