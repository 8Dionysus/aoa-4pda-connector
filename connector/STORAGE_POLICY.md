# Storage Policy

The repository stores method, small fixtures, and an ignored repo-local state
scaffold. Heavy mutable artifacts must stay outside Git history.

## Environment Roots

| Variable | Purpose |
| --- | --- |
| `CONNECTOR_DATA_ROOT` | raw public snapshots and normalized corpus data |
| `CONNECTOR_CACHE_ROOT` | rebuildable indexes and parser/cache state |
| `CONNECTOR_ARTIFACT_ROOT` | graph DBs, evidence exports, and run receipts |

If these variables are unset, the CLI uses the same repo-local default rooted
at `.connector-state/`.

The CLI storage status surface reports which route is active and can optionally
measure recursive file counts and byte totals. Exact syntax belongs to the CLI
help and the executable operator route in `AGENTS.md`.

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

`CONNECTOR_FAMILY_ROOT` is a documentation convention rather than a required
CLI variable. It gives agents and operators a portable head folder for many
future connector databases while keeping the three explicit `CONNECTOR_*_ROOT`
variables as the runtime contract.

## AbyssOS Machine Route

On AbyssOS machines, follow `/etc/abyss-machine/storage-policy.json`: large or
fast-growing connector data should use `/srv/abyss-machine/storage` or an
operator-approved external disk/NAS/object store, not `/` and not Git.

## Git Exclusions

The root `.gitignore` must exclude generated content under `.connector-state/`
plus raw data, indexes, graphs, full exports, SQLite databases, vector stores,
and cache directories.

## Fresh Clone Rule

The repository validator and CLI doctor path must work on a fresh clone without
external storage mounted. Missing environment roots fall back to
`.connector-state/` until the operator chooses an external route. Fixture
materialization may create a tiny queryable local database under the configured
roots without touching the network; exact execution belongs to the CLI and
fresh-copy verifier.
