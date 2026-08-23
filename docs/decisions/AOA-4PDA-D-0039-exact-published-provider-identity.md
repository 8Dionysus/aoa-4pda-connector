# AOA-4PDA-D-0039 — Exact published-provider identity for corrective releases

## Status

Accepted for the immutable `0.1.1` corrective release's historical identity;
the active identity for `0.1.2` and later direct provider preflights is recorded
below until a newer provider release supersedes it.

## Decision

The direct `aoa-stats` body-provider checkout in this connector must equal the
peeled commit of the currently required published provider tag. The immutable
`v0.1.1` corrective release used `aoa-stats@v0.2.0`; its annotated tag object
`a12ffb39e4bfee0426ea84647aa3e90597002189` peels to
`dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`. That identity remains historical
and is not rewritten.

For the current `v0.1.2` corrective release, `aoa-stats@v0.2.1` is the
required provider. Its annotated tag object
`45ec36ced2117bc387e3bd51fa1af52c2e70f83c` peels to
`339ecb2db22ac4552fa88756b650896ebbff5b56`. The workflow pin, its fetched
checkout, and the owner-local release preflight must use that exact commit.

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
- `v0.1.1` remains the immutable patch that first corrected release validation
  and compatibility exactness against `aoa-stats@v0.2.0`.
- `v0.1.2` is the successor patch that revalidates the same compatibility rule
  against the newer exact `aoa-stats@v0.2.1` identity without changing the
  connector's public method scope.
- A future `aoa-stats` release requires a new owner-approved provider identity
  update before this connector can publish a consumer release.
- The current direct pin is checked in CI by exact checkout equality and in
  the owner-local release preflight by a regression-tested source invariant.
