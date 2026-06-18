# Storage Policy

The repository stores method and small fixtures. Heavy mutable artifacts must be
outside Git.

## Environment Roots

| Variable | Purpose |
| --- | --- |
| `CONNECTOR_DATA_ROOT` | raw public snapshots and normalized corpus data |
| `CONNECTOR_CACHE_ROOT` | rebuildable indexes and parser/cache state |
| `CONNECTOR_ARTIFACT_ROOT` | graph DBs, evidence exports, and run receipts |

Example:

```bash
export CONNECTOR_DATA_ROOT=/mnt/external/abyss-connectors/4pda/data
export CONNECTOR_CACHE_ROOT=/mnt/external/abyss-connectors/4pda/cache
export CONNECTOR_ARTIFACT_ROOT=/mnt/external/abyss-connectors/4pda/artifacts
```

## Local Machine Route

On AbyssOS machines, follow `/etc/abyss-machine/storage-policy.json`: large or
fast-growing connector data should use `/srv/abyss-machine/storage` or an
operator-approved external disk/NAS/object store, not `/` and not Git.

## Git Exclusions

The root `.gitignore` must exclude raw data, indexes, graphs, full exports,
SQLite databases, vector stores, and cache directories.

## Fresh Clone Rule

`python scripts/validate_connector.py` and `aoa-4pda doctor` must work on a
fresh clone without external storage mounted. Missing external roots should be a
warning until a crawl or index build is requested.

