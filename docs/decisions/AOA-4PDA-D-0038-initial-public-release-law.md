# AOA-4PDA-D-0038 — Initial public release law

## Status

Accepted for the `0.1.0` release-preparation line.

## Decision

`aoa-4pda-connector` publishes its first public release as a conservative
`0.1.0` source/method boundary. The repository remains a skeleton and keeps
`connector-ready-v1` as a separate, evidence-bearing maturity target.

The connector is not registered in `aoa-sdk`'s owner-release federation, so
its release authority is an owner-local `docs/RELEASING.md` contract and the
checked-in `scripts/release_check.py` / `scripts/release_publish.py` route.
The route requires a dated human-first changelog, a complete first-parent
reconciliation ledger, exact provider release tags and pin ancestry, clean
landed `main`, an annotated immutable tag, and postpublish identity checks.

The release is source-only. Host artifact policy is consulted, but no
connector-owned artifact class is invented and no sibling artifact class is
borrowed. Wheels or sdists built for validation are local evidence unless a
future owner decision admits a package artifact class with its required
sidecars and public attestation.

## Boundary consequences

- `aoa-kag@v0.5.0` and `aoa-stats@v0.2.0` are provider-before-consumer
  prerequisites; their publication does not prove this connector's release.
- Publication does not prove deployment, runtime activation/health, corpus
  completeness, semantic quality, central proof, or human acceptance.
- Release notes must preserve policy, schema/evidence, compatibility,
  migration, security/privacy, generated-consumer, validation, rollback, and
  limitation facts without turning generated churn into duplicate feature
  claims.

## Rejected alternatives

- `1.0.0`: rejected because the connector-ready loop is still `not_ready` and
  runtime ownership belongs to `abyss-stack`.
- Generic `aoa release`: rejected because the SDK release registry does not
  own this connector.
- Publishing a package asset under `bootstrap_install_bundle` or another
  sibling class: rejected because that would cross the artifact owner boundary.
- Treating a GitHub Release or CI success as runtime/proof/acceptance: rejected
  by the repository claim contract.
