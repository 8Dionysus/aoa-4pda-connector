# AOA-4PDA-D-0039 — Exact published-provider identity for corrective releases

## Status

Accepted for the `0.1.1` corrective release and all later direct provider
preflights until a newer provider release supersedes the recorded identity.

## Decision

The direct `aoa-stats` body-provider checkout in this connector must equal the
peeled commit of the currently required published provider tag. For the
`v0.1.1` corrective release, `aoa-stats@v0.2.0` is the required provider and
its annotated tag object `a12ffb39e4bfee0426ea84647aa3e90597002189` peels to
`dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`. The workflow pin and its fetched
checkout must use that exact commit.

An ancestor-only check is not an exact compatibility check: an older commit
may be contained by the published provider while still failing the published
identity contract. The owner release law, workflow, release preflight, and
regression test must retain the equality requirement.

This decision applies to the direct provider body pin only. Generated KAG
actions and owner-family pins remain separate identities under their own
owner law and may use their documented ancestry rule. The source release
remains source-only; no artifact class, admission verdict, deployment,
runtime, proof, or acceptance claim is introduced.

## Consequences

- `v0.1.0` and its tag/Release remain unchanged historical evidence.
- `v0.1.1` is a patch because it corrects release validation and compatibility
  exactness without changing the connector's public method scope.
- A future `aoa-stats` release requires a new owner-approved provider identity
  update before this connector can publish a consumer release.
- The current direct pin is checked in CI by exact checkout equality and in
  the owner-local release preflight by a regression-tested source invariant.
