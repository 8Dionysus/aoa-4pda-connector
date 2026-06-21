# AOA-4PDA-D-0024: Review-Ready Discovery Candidates

## Status

Accepted.

## Context

`reference-profile-discovery-v1` surfaced public topic and page-window
candidates from already-stored Xiaomi 13T snapshots. The first audit proved the
route was useful, but it also exposed two quality risks:

- links to page windows already covered by the seed plan could be mistaken for
  new gaps
- candidate URLs without anchor/source evidence were too weak for reliable
  seed review

The long connector goal requires deep retrieval coverage, but seed expansion
must still stay bounded, reviewable, and no-network until an operator chooses a
crawl.

## Decision

Make discovery candidates review-ready before they can influence seed files.

The discovery audit now computes seed-plan-covered page windows from each
seed's `max_pages` value, excludes those windows from candidate gaps, and
reports their count separately as `covered_seed_window_link_count`.

Remaining candidates carry anchor text, source title, source seed, source URL,
profile target hits, review priority, and review reasons. The audit remains
read-only and does not promote candidates into seeds.

`AOA-4PDA-D-0025` adds the follow-up review manifest stage that records
accept/reject/defer decisions for those candidates without changing crawl
scope.

## Rationale

This keeps discovery useful without letting navigation noise inflate the
reference-profile gap list. It gives a future agent enough local evidence to
review a candidate, while preserving the operator boundary around crawl scope.

The review metadata is intentionally a hint, not an approval. A high-priority
candidate may still be rejected if it is generic, off-device, too broad, or
better handled by an eval/query case rather than a seed expansion.

## Alternatives

- Keep URL-only candidates. Rejected because it forces seed review to rely on
  weak context and makes accidental seed expansion more likely.
- Auto-add high-priority candidates to `connector/seeds/xiaomi_13t_topics.yaml`.
  Rejected because candidate relevance is not the same as approved crawl
  scope.
- Treat every linked page in a seeded topic as a new gap. Rejected because
  `max_pages` already represents planned windows and coverage should not be
  double-counted as discovery debt.

## Consequences

- Discovery output is more verbose, but more useful for actual seed review.
- Review tooling can prioritize candidates without touching the network.
- Existing seed-plan windows disappear from candidate counts, so discovery
  counts better reflect remaining review work.
- The next loop step is still explicit: accept/reject candidates, edit seeds if
  warranted, then run an operator-confirmed bounded crawl and re-run quality
  gates.

## Verification

- `aoa-4pda discovery audit xiaomi-13t` reports `review_priority` and
  `covered_seed_window_link_count`.
- Contract tests verify covered seed-plan windows are excluded from candidates.
- `docs/DISCOVERY.md`, `docs/AGENT_INSTALL_ROUTE.md`, and
  `docs/RUNTIME_CONTRACT.md` document the review boundary.
