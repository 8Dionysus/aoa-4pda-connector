# AOA-4PDA-D-0023: Reference Profile Discovery Audit

## Status

Accepted.

## Context

The long connector goal requires discovering relevant public forum material,
not only crawling a static seed list. At the same time, this repository must
not use 4PDA internal search as a crawler API and must not broaden crawl scope
without explicit operator intent.

The current Xiaomi 13T run already stores raw public topic snapshots. Those
snapshots may contain links to related public topics or additional windows of
known topics. Future agents need a safe way to surface those candidates before
editing seed files or asking to crawl more.

## Decision

Add a no-network `aoa-4pda discovery audit <profile>` command and document it
as the `reference-profile-discovery-v1` target.

The audit reads crawl receipts and raw snapshot paths from configured storage,
extracts public `showtopic` links, filters them through the existing source
policy, and reports candidates as `unseeded_topic` or
`seed_topic_new_window`. Denied service routes are counted separately and never
become candidates.

`AOA-4PDA-D-0024` extends this route with seed-plan-aware window exclusion and
review evidence, so later implementations should not treat already covered
`max_pages` windows as new discovery gaps.

## Rationale

This creates a source-aware discovery review surface without changing the crawl
boundary. It lets an agent say "these public links are visible in our current
evidence and may deserve seed review" instead of silently expanding scope or
pretending the current seed list is complete.

The audit is deliberately local and receipt-driven. It does not search 4PDA,
does not fetch new pages, does not write generated artifacts, and does not
replace operator review of seed changes.

## Alternatives

- Use 4PDA internal search for discovery. Rejected by source policy and by the
  public-evidence connector boundary.
- Treat coverage gaps as discovery. Rejected because coverage only checks the
  current seed plan; it cannot reveal related public topics visible in stored
  snapshots.
- Add candidates directly to seed files automatically. Rejected because related
  links need human or agent review before they become crawl scope.

## Consequences

- Discovery becomes inspectable through a no-network CLI command.
- Future seed expansion can cite concrete local evidence from existing raw
  snapshots.
- The command may produce noisy candidates; review is required before seed
  changes.
- Broad discovery, central proof verdicts, and crawler policy changes remain
  outside this local audit.

## Verification

- `docs/DISCOVERY.md` documents the target and command.
- `aoa-4pda discovery audit xiaomi-13t` reports candidates without touching the
  network.
- Contract tests cover missing-run and candidate extraction behavior.
- The validator requires the discovery doc and install-route command token.
