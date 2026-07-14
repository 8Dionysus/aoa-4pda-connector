# Seed Review

`reference-profile-seed-review-v1` is the no-network review target between
discovery and seed expansion. It compares current discovery candidates with a
repo-local review manifest and reports what is accepted, rejected, deferred, or
still unreviewed.

## Executable Surface

The CLI discovery-review action owns profile, named-run, and manifest override
syntax. It reads the discovery audit and the review manifest. It does not
touch the network, edit seeds, crawl, rebuild artifacts, use 4PDA internal
search, or download attachments.

## Manifest

The Xiaomi 13T review manifest lives at:

```text
connector/seeds/reviews/xiaomi_13t_discovery_review.json
```

The manifest can contain exact `decisions` by candidate URL and bounded
`rules`. Exact decisions are used for accepted seed expansion. Generic
additional page windows inside already seeded topics are deferred by default,
because many of them are ordinary pagination/navigation links rather than a
reviewed information need. Valid decisions are:

| Decision | Meaning |
| --- | --- |
| `accept` | Candidate is accepted for a future seed update, still requiring operator-confirmed crawl. |
| `reject` | Candidate is not part of the reference-profile seed scope. |
| `defer` | Candidate is reviewed but kept out of the current seed expansion. |

Accepted entries use `accepted_pending_seed_update` until they are represented
by the profile seed plan. The current Xiaomi 13T seed plan already represents
the first reviewed expansion: 23 bounded seed entries and 70 expected public
pages. Future page-window expansion should be added as exact accept decisions,
not by turning all pagination into seed scope.

## Statuses

| Status | Meaning |
| --- | --- |
| `missing_run` | No discovery run exists for review. |
| `missing_review` | Discovery candidates exist but no review manifest exists. |
| `invalid_review` | The manifest exists but fails the review contract. |
| `needs_review` | Some current candidates are not covered by exact decisions or rules. |
| `reviewed_pending_seed_update` | All candidates are reviewed, but accepted candidates are not yet in seeds. |
| `reviewed` | All current candidates are reviewed and accepted candidates are represented by seeds. |

## Route

When `reviewed_pending_seed_update` appears:

1. edit `connector/seeds/xiaomi_13t_topics.yaml` with only accepted public
   candidates
2. do not crawl until the operator confirms the bounded update
3. materialize the confirmed profile through one ordered crawl, normalize,
   keyword-index, vector-index, and graph chain
4. re-inspect discovery review, coverage, refresh, and live quality gates
   against that same named run

The review manifest is a seed-review surface, not a source-of-truth claim about
4PDA and not permission to crawl.

When seed review reports `reviewed` but coverage reports `partial`, the
next missing step is materialization of the current seed plan, not more seed
review.

When `coverage audit` is ready but discovery sees more pagination windows,
review those windows as future expansion pressure. Do not treat ordinary
numbered forum navigation as an automatic crawl requirement.
