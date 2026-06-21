# AOA-4PDA-D-0027: Discovery Pagination Defer Rule

## Status

Accepted.

## Context

After the Xiaomi 13T reviewed seed expansion was materialized, the new
70-page run exposed many additional `seed_topic_new_window` discovery
candidates. Most were ordinary forum pagination links inside already seeded
topics, such as the next numbered page after a covered window.

The previous review rule accepted every new page window inside an already
seeded topic. That was useful for the first expansion, but after materializing
the expanded profile it would make readiness chase pagination forever.

## Decision

Treat `seed_topic_new_window` candidates as reviewed `defer` by default.

Future seed expansion may still accept a page window, but only through an exact
review decision with rationale. Exact decisions remain stronger than the
default rule.

## Rationale

Discovery should reveal useful expansion pressure without turning navigation
links into mandatory crawl scope. A bounded reference profile needs a stable
acceptance target: once the reviewed seed plan is materialized, further
pagination is evidence for future work, not an automatic failure.

This preserves quality because real high-signal windows can still be accepted
explicitly. It also preserves reproducibility because `ready` no longer flips
red merely because crawled pages contain links to their next numbered pages.

## Alternatives

- Keep accepting all seeded-topic windows. Rejected because it creates an
  unbounded crawl loop driven by pagination.
- Ignore all seeded-topic windows in discovery. Rejected because future
  high-signal windows should remain visible for review.
- Add every newly observed window to the seed file. Rejected because it would
  inflate the reference profile without a reviewed information need.

## Consequences

- The review manifest can mark the current materialized run as reviewed without
  requiring every adjacent page link to be added as a seed.
- Future accepted page-window expansion must be explicit and traceable.
- Coverage remains scoped to the current reviewed seed plan instead of the
  whole forum topic.

## Verification

- `aoa-4pda discovery review xiaomi-13t --run 20260621T194521Z__crawl` should
  report no unreviewed candidates and no accepted candidates missing from
  seeds.
- `aoa-4pda ready --run 20260621T194521Z__crawl --strict` should not fail only
  because of ordinary pagination windows.
