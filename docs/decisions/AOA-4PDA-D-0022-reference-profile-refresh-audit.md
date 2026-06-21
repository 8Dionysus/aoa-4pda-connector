# AOA-4PDA-D-0022: Reference Profile Refresh Audit

## Status

Accepted.

## Context

Coverage makes the Xiaomi 13T seed-window materialization visible, but it does
not say whether the selected run is still fresh enough to trust for current
answers. Answer packets carry freshness metadata for cited evidence, yet future
agents also need a run-level surface that can decide whether to reuse the
current local base or ask the operator for an explicit bounded refresh.

The owner route forbids hidden broad crawls. That means refresh planning must
be inspectable before any network request happens.

## Decision

Add a no-network `aoa-4pda refresh audit <profile>` command and document it as
the `reference-profile-refresh-v1` target.

The audit reads configured receipts, checks crawl age, policy, crawl errors,
derived stage timestamps, derived no-network posture, and the existing coverage
audit. It reports `missing_run`, `needs_refresh`, or `fresh`, plus
`strict_ready`, gaps, and a bounded operator-confirmed refresh command sequence.

## Rationale

This gives agents and operators a stable pre-crawl decision point. A stale or
missing run can be reported without touching the network; a fresh run can be
used for search, graph, answer, and eval gates with a visible age threshold.

The audit keeps freshness local and receipt-driven. It does not create a
central proof verdict, does not discover new topics, and does not treat answer
freshness notes as a substitute for run-level refresh state.

## Alternatives

- Put freshness only inside answer packets. Rejected because answer freshness is
  per cited result, not a run-level update decision.
- Make `coverage audit` decide refresh state too. Rejected because coverage and
  freshness answer different operational questions.
- Recrawl automatically when stale. Rejected because network crawl still
  requires explicit operator intent and storage review.

## Consequences

- Fresh agents can check whether a reference profile should be refreshed before
  running live answer gates.
- CI can keep the command fresh-clone safe without requiring a live corpus.
- Future incremental refresh work has a stable report shape to extend with
  per-topic or per-window refresh decisions.
- The command remains local connector evidence and does not replace
  `aoa-evals` proof ownership.

## Verification

- `docs/REFRESH.md` documents the target and command.
- `aoa-4pda refresh audit xiaomi-13t` reports run freshness without touching
  the network.
- Contract tests cover missing-run and stale-run behavior.
- The validator requires the refresh doc and install-route command token.
