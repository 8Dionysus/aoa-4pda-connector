# AOA-4PDA-D-0039 — Exact published-provider identity for corrective releases

## Status

Accepted. The active consolidated source and sole final publication identity
is `v0.1.0`; the provider identities and release carriers from the same-day
campaign are retained as historical evidence in the content-conservation
ledger and historical changelog material. The existing target publication was
reconciled once after a digest-bound pre-mutation snapshot.

## Decision

The direct `aoa-stats` body-provider checkout in this connector must equal the
peeled commit of the required published provider tag. The current source
identity is `aoa-stats@v0.2.0`: annotated tag object
`a63dd6f95c6f0c87a371720885c2d90a1baa3436` peels to
`88ff38b1b38eef939f2c5b4541cbe8363a05fc8d`. The workflow pin, its fetched
checkout, and the owner-local release preflight must use that exact commit.

The active repo-local KAG action and generated owner-family declaration bind
to the exact published `aoa-kag@v0.5.0` commit
`f46f146cc79a26fa81ad0f400b9c5774df293e57`, whose annotated tag object is
`8f63e3ae558ea96d21ee06becfa6ef61d63d698a`. An ancestor-only KAG action or
generated-family pin is not provider-before-consumer proof.

An ancestor-only check is not an exact compatibility check: an older commit
may be contained by the published provider while still failing the published
identity contract. The owner release law, workflow, release preflight, and
regression test retain the equality requirement.

This decision applies to the direct provider body pin and the exact-current
KAG consumer declaration. The KAG action and owner-family pin remain separate
identities from the stats body pin. The source release remains source-only;
no artifact class, admission verdict, deployment, runtime, proof, or
acceptance claim is introduced.

## Historical identities preserved

- The initial `v0.1.0` source material used the provider identities recorded in
  its original release body and changelog section.
- The immutable corrective `v0.1.1` used `aoa-stats@v0.2.0`, tag object
  `a12ffb39e4bfee0426ea84647aa3e90597002189`, peeling to
  `dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`.
- The corrective `v0.1.2` used `aoa-stats@v0.2.1`, tag object
  `45ec36ced2117bc387e3bd51fa1af52c2e70f83c`, peeling to
  `339ecb2db22ac4552fa88756b650896ebbff5b56`.
- The corrective `v0.1.3` recorded direct `aoa-stats@v0.2.2` and
  `aoa-kag@v0.5.2` (`8136d3eb629da28cea1206d13a8f1df52ee14739`, tag object
  `251846823f49d18b06c32374b3434e6e11002e96`) as historical campaign
  material. Those lines are not the active consolidated KAG binding.
- No same-day Release body, tag-scoped changelog line, PR, commit, or
  provider-validation limitation is silently discarded by consolidation. The
  pre-reconciliation target identity and every deleted carrier remain
  recoverable from the task-local snapshot and ledger.

## Consequences

- `v0.1.0` is the sole active campaign version and final publication; the
  source and canonical release body bind the exact provider identities above.
- A future provider release requires a new owner-approved provider identity
  update before this connector can publish a consumer release.
- The exact direct pin is checked in CI by checkout equality and in the
  owner-local release preflight by regression-tested source invariants.
- Publication remains separate from artifact trust, deployment, runtime
  health, semantic proof, delivery, closure, and human acceptance.
