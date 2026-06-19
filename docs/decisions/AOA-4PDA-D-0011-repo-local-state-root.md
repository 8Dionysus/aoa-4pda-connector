# AOA-4PDA-D-0011 Repo-Local State Root

Status: accepted
Date: 2026-06-19

## Context

The connector repository must remain public and GitHub-safe, but early users may
not have a separate disk, NAS, vault, or object store available. Requiring
external storage before any small crawl or index run makes the connector harder
to install and test. At the same time, committing real corpora, indexes, graph
databases, vector stores, or full exports would break the publication boundary.

## Decision

Add `.connector-state/` as the portable repo-local state root for small starter
databases. It is the default when `CONNECTOR_DATA_ROOT`,
`CONNECTOR_CACHE_ROOT`, and `CONNECTOR_ARTIFACT_ROOT` are unset:

```text
.connector-state/data
.connector-state/cache
.connector-state/artifacts
```

The scaffold and route cards are tracked. Generated files under the scaffold
are ignored by Git.

For larger or long-lived runs, operators should override the roots with
external storage:

```bash
export CONNECTOR_DATA_ROOT=/path/to/storage/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/storage/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/storage/aoa-4pda-connector/artifacts
```

## Rationale

This gives fresh clones a complete local working shape without baking personal
paths into public documentation. It also lets bounded starter runs grow
naturally from local disk to external storage when size or operational needs
justify that move.

## Consequences

- `aoa-4pda init --apply` can prepare local storage without environment
  variables.
- `aoa-4pda storage status` can report active storage readiness without
  touching the network.
- Small starter runs can materialize inside the repository checkout while still
  staying outside Git history.
- `aoa-4pda materialize fixture` can create a tiny queryable local database for
  fresh clones before any live crawl.
- Validators and `doctor` must distinguish the allowed `.connector-state/`
  workspace from forbidden root-level heavy directories such as `data/`,
  `cache/`, `indexes/`, and `graphs/`.
- External storage remains the route for large crawls, full indexes, graph
  databases, vector stores, and long-lived materialization.

## Boundaries

- Do not commit generated `.connector-state/` contents.
- Do not use machine-specific paths as public defaults.
- Do not treat `.connector-state/` as source truth; it is local generated
  state.
- Do not weaken source policy, crawl bounds, internal-search denial, or
  attachment/download denial.

## Source Surfaces

- `.connector-state/`
- `.gitignore`
- `.env.example`
- `connector/STORAGE_POLICY.md`
- `docs/INSTALL.md`
- `scripts/validate_connector.py`
- `src/aoa_4pda_connector/config.py`
- `src/aoa_4pda_connector/storage/__init__.py`
- `src/aoa_4pda_connector/cli.py`
