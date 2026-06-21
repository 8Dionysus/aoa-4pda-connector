# AOA-4PDA-D-0026: Xiaomi 13T Reviewed Seed Expansion

## Status

Accepted.

## Context

`AOA-4PDA-D-0025` introduced a discovery review manifest for Xiaomi 13T. The
manifest reviewed all current discovery candidates and marked 48 candidates as
accepted for future seed expansion, with rejected and deferred candidates kept
out of crawl scope.

The accepted candidates are not enough by themselves. Until the seed plan
represents them, a future agent cannot run the bounded reference-profile crawl
that should prove the expanded Xiaomi 13T corpus.

## Decision

Apply the accepted Xiaomi 13T discovery review candidates to
`connector/seeds/xiaomi_13t_topics.yaml` and raise the profile's `max_topics`
to cover the expanded seed plan.

The seed expansion stays compact. Contiguous accepted windows inside already
seeded topics are represented by increasing `max_pages` or adding short
adjacent window seeds, rather than adding one seed entry for every accepted page
link.

## Rationale

This moves the repository from reviewed candidates to an actionable bounded
seed plan while preserving the no-network boundary. The change is source-level
method and scope; it does not crawl, normalize, index, graph, or commit any
generated 4PDA content.

The expanded seed plan intentionally makes current stored coverage partial
until an operator confirms the bounded crawl and rebuilds derived artifacts.
That is a truthful readiness state: review is done, seed scope moved, and the
stored run must catch up.

## Alternatives

- Keep accepted candidates only in the review manifest. Rejected because the
  reference profile would still have no executable seed scope for the next
  materialization.
- Add all 48 accepted URLs as one-page seed entries. Rejected because adjacent
  page windows are clearer and less noisy when represented as bounded
  `max_pages` ranges.
- Run the crawl immediately after editing seeds. Rejected because crawl still
  requires explicit operator confirmation and configured storage review.

## Consequences

- Xiaomi 13T seed count grows from 9 to 23 seed entries.
- Expected seed pages grow from 22 to 70.
- `aoa-4pda discovery review xiaomi-13t` can report `reviewed` because
  accepted candidates are represented by seeds.
- `aoa-4pda coverage audit xiaomi-13t` becomes `partial` against the older
  stored run until the expanded seed plan is crawled and rebuilt.

## Verification

- `aoa-4pda discovery review xiaomi-13t` reports no accepted candidates missing
  from seeds.
- `aoa-4pda profile inspect xiaomi-13t` reports the expanded seed count and
  profile limit.
- `aoa-4pda coverage audit xiaomi-13t` reports the current materialization gap
  without touching the network.
