# AOA-4PDA-D-0002 CI and Starter Proof Gate

Status: accepted
Date: 2026-06-18

## Decision

Add a GitHub Actions validation workflow and an offline starter proof command.
The proof command is `aoa-4pda proof starter`.

The proof route uses synthetic fixtures only. It builds temporary keyword index
and graph artifacts, queries them, checks the evidence packet posture, and then
lets the temporary artifacts be deleted.

## Rationale

The repository is public and GitHub-safe method, not a corpus. Future changes
need a small proof that the connector path is wired together without requiring
network access, external storage, or a live 4PDA crawl.

CI should protect the repo's source boundary before deeper retrieval work begins.

## Consequences

- Fresh clones can validate the skeleton, tests, Python compilation, and offline
  proof route.
- Pull requests get an automatic guard against committed heavy artifact
  directories.
- Live starter crawls remain explicit operator actions with configured external
  storage roots.

## Boundaries

- The proof command must not touch the network.
- The proof command must not require `CONNECTOR_DATA_ROOT`,
  `CONNECTOR_CACHE_ROOT`, or `CONNECTOR_ARTIFACT_ROOT`.
- The proof command must not write raw captures, indexes, graphs, or packets
  into the repository.
- GitHub Actions must not run live crawls.

## Source Surfaces

- `.github/workflows/validate.yml`
- `src/aoa_4pda_connector/cli.py`
- `docs/STARTER_PROOF.md`
- `scripts/validate_connector.py`
- `tests/contract/test_fixtures_and_cli.py`
