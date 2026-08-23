# AOA-4PDA-D-0039 — Exact published-provider identity for corrective releases

## Status

Accepted for the immutable `0.1.1` corrective release's historical identity;
the active identity for `0.1.3` and later direct provider preflights is recorded
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

For the current `v0.1.3` corrective release, `aoa-stats@v0.2.2` is the
required direct provider. Its annotated tag object
`119f434918e8218e43e977b2edec3e4feab6b493` peels to
`f119805cda69b3edeb2a4c5e407368d70e68650d`. The workflow pin, its fetched
checkout, and the owner-local release preflight must use that exact commit.

The same release also requires the repo-local KAG action and generated
owner-family declaration to resolve to the exact published `aoa-kag@v0.5.2`
commit `8136d3eb629da28cea1206d13a8f1df52ee14739` (annotated tag object
`251846823f49d18b06c32374b3434e6e11002e96`). An ancestor-only KAG action or
generated-family pin is not provider-before-consumer proof.

An ancestor-only check is not an exact compatibility check: an older commit
may be contained by the published provider while still failing the published
identity contract. The owner release law, workflow, release preflight, and
regression test must retain the equality requirement.

This decision applies to the direct provider body pin and the exact-current
KAG consumer declaration. The KAG action and owner-family pin remain separate
identities from the stats body pin, but both are checked against the published
KAG successor commit rather than an ancestor-only green result. The source release
remains source-only; no artifact class, admission verdict, deployment,
runtime, proof, or acceptance claim is introduced.

## Consequences

- `v0.1.0` and its tag/Release remain unchanged historical evidence.
- `v0.1.1` remains the immutable patch that first corrected release validation
  and compatibility exactness against `aoa-stats@v0.2.0`.
- `v0.1.2` is the historical successor patch that revalidated the same
  compatibility rule against the exact `aoa-stats@v0.2.1` identity.
- `v0.1.3` is the current successor patch that revalidates the direct stats
  identity against `v0.2.2` and the repo-local KAG consumer against exact
  `v0.5.2`, without changing the connector's public method scope.
- A future `aoa-stats` release requires a new owner-approved provider identity
  update before this connector can publish a consumer release.
- The current direct pin is checked in CI by exact checkout equality and in
  the owner-local release preflight by a regression-tested source invariant.
