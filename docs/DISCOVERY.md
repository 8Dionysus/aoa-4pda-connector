# Discovery Audit

`reference-profile-discovery-v1` is the no-network discovery target for a
bounded profile. It does not search 4PDA and does not crawl. It inspects
already-stored public crawl snapshots and reports public topic links that are
visible in the local evidence but not yet represented by the profile seed
plan or already-fetched seed windows.

## Executable Surface

The CLI discovery-audit action owns profile, named-run, and result-limit
syntax. It reads the crawl receipt and raw snapshot paths from configured
storage. It does not touch the network, write generated artifacts, use 4PDA
internal search, or download attachments.

## Statuses

| Status | Meaning |
| --- | --- |
| `missing_run` | No crawl receipt exists for the selected run. |
| `needs_seed_review` | Stored snapshots contain public topic/window candidates outside the current seed plan. |
| `no_new_candidates` | Stored snapshots were inspected and no new public topic candidates were found. |
| `error` | The requested profile route is missing. |

## Candidate Kinds

| Kind | Meaning |
| --- | --- |
| `unseeded_topic` | A public topic id appears in stored snapshots but is not in the profile seed topic ids. |
| `seed_topic_new_window` | The topic id is already seeded, but the specific `st=` window is outside the current seed plan and fetched seed windows. |

Denied service routes such as `act=search` are counted separately and are never
returned as public candidates.

## Review Evidence

The audit is seed-plan aware. It computes the page windows implied by each seed
and its `max_pages` value, excludes those covered windows from candidates, and
reports them as `covered_seed_window_link_count`.

Each candidate includes review evidence:

- `anchor_texts` from the stored page links
- `evidence_contexts` with source seed id, source URL, source title, and source
  page start
- `target_hits` and `source_target_hits` against the profile device aliases and
  search terms
- `review_priority` and `review_reasons`

These fields are hints for seed review. They are not permission to crawl and
not proof that an unseeded topic belongs in the reference profile.

## Review Route

When candidates appear, review the high-priority JSON evidence, then either:

- use the CLI seed-review action to compare current candidates with the
  seed-review manifest
- add accepted public topic windows to `connector/seeds/xiaomi_13t_topics.yaml`
- leave rejected candidates out of seeds with a short rationale in a follow-up
  note or decision
- inspect coverage, refresh, and live quality gates after the next bounded
  crawl

The audit is a discovery review surface, not permission to crawl broadly.
