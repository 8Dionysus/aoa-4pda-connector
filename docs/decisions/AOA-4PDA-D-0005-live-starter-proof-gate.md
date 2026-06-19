# AOA-4PDA-D-0005: Live Starter Proof Gate

- Status: accepted
- Date: 2026-06-18

## Context

The offline starter proof keeps fresh clones and CI safe, but it cannot prove
that the public 4PDA starter route still works against live topic pages. The
connector also must not commit raw captures, indexes, graph exports, or evidence
packets into Git.

## Decision

Add a live starter proof command that verifies an already-built bounded starter
run in external storage:

```bash
aoa-4pda proof live-starter --run latest --query "Redmi Note 10 Pro TWRP boot.img"
```

The live route remains explicitly staged:

```text
crawl -> normalize -> build-index -> build-graph -> proof live-starter
```

`proof live-starter` does not crawl. It reads receipts, the keyword index, the
graph export, and a local query result from configured external roots. It checks
that policy was preserved, only the crawl stage touched the network, normalized
topic count matches fetched topics, index and graph artifacts are non-empty, and
the local query returns evidence.

Index and graph build commands accept `--run` so agents can rebuild artifacts
for a named normalized run instead of relying only on whichever receipt is
latest. Evidence packet ids use a stable SHA-256 query digest by default so the
same query produces the same packet id across processes.

## Consequences

- Live 4PDA availability can be tested without moving live artifacts into Git.
- Future agents get a clear post-crawl proof gate instead of treating a crawl
  receipt as sufficient.
- Dependent live-run stages must run sequentially because each stage consumes
  the previous stage's receipt.
- Query packet ids are reproducible across Python processes.

## Boundaries

- No internal 4PDA search is used.
- No attachments or downloads are fetched.
- No raw public captures, indexes, graphs, or live evidence packets are
  committed.
- The command is starter-grade proof, not full-corpus quality validation.
