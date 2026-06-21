# AOA-4PDA-D-0025: Discovery Review Manifest

## Status

Accepted.

## Context

`aoa-4pda discovery audit` can now produce review-ready Xiaomi 13T candidates
from stored snapshots. That still leaves a workflow gap: the repository needs a
portable way to record which candidates are accepted, rejected, or deferred
without immediately changing crawl scope or running a network update.

The goal requires a deep, useful reference profile, but source policy and the
repo route both require explicit operator intent before new crawls.

## Decision

Add `reference-profile-seed-review-v1` as a no-network review stage and expose
it through `aoa-4pda discovery review <profile>`.

The command compares current discovery candidates with a repo-local JSON
manifest. The first manifest is
`connector/seeds/reviews/xiaomi_13t_discovery_review.json`. It records exact
candidate decisions and bounded rules such as accepting additional page windows
inside already seeded Xiaomi 13T topics.

## Rationale

This keeps seed expansion reviewable and reproducible. A future agent can see
which candidates are pending seed updates without treating the discovery audit
as permission to crawl or relying on conversation memory.

The review manifest is source-controlled because it is method and review state,
not heavy generated data. It does not contain raw 4PDA content, indexes, graph
artifacts, or corpus snapshots.

## Alternatives

- Edit `connector/seeds/xiaomi_13t_topics.yaml` directly from discovery
  output. Rejected because it would collapse review, seed scope, and crawl
  planning into one risky step.
- Keep review decisions only in a chat summary. Rejected because a fresh agent
  could not reproduce the seed-review state.
- Store the review as generated output under `.connector-state/`. Rejected
  because this is a portable repository method artifact, not local runtime
  state.

## Consequences

- `aoa-4pda ready` can distinguish unreviewed candidates from accepted
  candidates that are still missing from seeds.
- Accepted candidates still require a seed edit and an operator-confirmed
  bounded crawl before coverage can become mature.
- The manifest may need updates when future discovery runs produce new
  candidates or stale decisions.

## Verification

- `aoa-4pda discovery review xiaomi-13t` reports the review state without
  touching the network.
- `docs/SEED_REVIEW.md` documents statuses and manifest semantics.
- `scripts/validate_connector.py` requires the review manifest and review docs.
