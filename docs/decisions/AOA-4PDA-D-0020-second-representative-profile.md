# AOA-4PDA-D-0020: Second Representative Profile

## Status

Accepted.

## Context

`connector-ready-v1` requires the connector to prove one focused-device profile
deeply and to prepare at least one more representative profile so the method is
not overfit to Xiaomi 13T. A broad `full-public` crawl remains deferred because
it would hide profile quality, increase storage pressure, and weaken review.

The starter route already carries public Redmi Note 10 Pro topics and eval
coverage for `sweet`, `boot.img`, `recovery.img`, Magisk, and TWRP search
behavior. That makes Redmi Note 10 Pro a small but useful second-device route:
it exercises the same technical retrieval primitives without introducing a new
wide discovery problem.

## Decision

Prepare Redmi Note 10 Pro as the second representative focused-device profile:

- `connector/profiles/redmi-note-10-pro.yaml` owns the profile route.
- `connector/seeds/redmi_note_10_pro_topics.yaml` owns bounded public seed
  windows derived from reviewed starter seeds.
- `evals/suites/live_redmi_note_10_pro_search_quality.json` defines the local
  live search gate for an already-materialized named run.
- `aoa-4pda ready` now requires a second focused profile to have a seed file,
  bounded seed windows, and a matching live-search suite before it counts as
  prepared.

## Rationale

This closes the profile-expansion maturity gap without pretending that a second
device is already deeply receipt-proven. Xiaomi 13T remains the deeply proven
focused run. Redmi Note 10 Pro becomes the next bounded run path with enough
seed and eval structure for an operator or agent to continue safely.

The profile stays public-repo friendly: it commits method, seed windows, and
eval expectations only. Raw pages, normalized data, indexes, and future graph
artifacts still belong in configured storage roots.

## Alternatives

- Treat `full-public` as the second profile. Rejected because it is deliberately
  deferred and too broad for a next maturity step.
- Add another new device through fresh web discovery. Rejected for this slice
  because the starter route already contains a reviewed representative device
  with existing technical-search coverage.
- Require a full Redmi receipt chain before marking the second profile
  prepared. Rejected because the done criterion separates "deeply proven first
  focused profile" from "one more representative profile prepared".

## Consequences

- `connector-ready-v1` can distinguish a real prepared second profile from a
  deferred broad-crawl placeholder.
- Future work has a concrete next-device command route and quality gate.
- The Redmi profile is not a claim of live proof until a crawl/normalize/index
  receipt chain exists and the live suite has run over that named run.

## Verification

- `aoa-4pda profile inspect redmi-note-10-pro` reports the route without
  touching the network.
- `aoa-4pda ready` reports the second representative profile criterion as
  achieved when the profile, seed windows, and suite are present.
- Unit coverage runs the Redmi live-search suite over a temporary no-network
  normalized dataset and receipt set.
