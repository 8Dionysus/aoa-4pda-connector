# AOA-4PDA-D-0001 Public Evidence Connector Skeleton

Status: accepted
Date: 2026-06-15

## Decision

Create `aoa-4pda-connector` as a standalone external-source connector
repository under `/srv/AbyssOS/connectors/`. The repository stores method,
policy, code, schemas, tiny fixtures, and install routes. It does not store full
corpora, raw captures, large indexes, graph databases, vector stores, or full
exports.

## Rationale

4PDA-scale data will exceed practical GitHub and local root storage boundaries.
The durable value of the repository is reproducibility: a forkable method that
an operator or agent can install, validate, configure with external storage,
and then use to build local evidence/search/graph surfaces.

## Boundaries

- Internal 4PDA search routes are not source APIs for this connector.
- Public topic/post snapshots are the source material for local deep search.
- External storage roots carry mass.
- Runtime access belongs in `abyss-stack`.
- Generated indexes and graphs are navigation layers, not source truth.

## Source Surfaces

- `AGENTS.md`
- `BOUNDARIES.md`
- `connector/SOURCE_POLICY.md`
- `connector/STORAGE_POLICY.md`
- `docs/ARCHITECTURE.md`
- `scripts/validate_connector.py`

