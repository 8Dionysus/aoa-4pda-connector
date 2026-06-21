# AOA-4PDA-D-0019: Answer Freshness Context

## Status

Accepted.

## Context

Answer packets are now the compact handoff surface for agents and future
runtime adapters. They cite source URLs and evidence refs, but a user also
needs to know whether the answer came from a public post timestamp, a local
capture timestamp, or only the packet creation time of an older index.

The connector must stay deterministic and public-repo friendly. It can preserve
metadata already parsed from public posts and local receipts, but it must not
rebuild live corpora, recrawl, or commit generated answer artifacts just to make
freshness visible.

## Decision

Make freshness context part of `aoa_4pda_answer_packet_v1` without changing the
schema version:

- propagate `posted_at` and `captured_at` from normalized posts through chunks,
  keyword indexes, evidence packets, and answer packets;
- require answer items to include `posted_at`, `captured_at`, and a structured
  `freshness` object;
- use `source_post_and_capture_metadata` when capture metadata is present;
- use `packet_created_at_fallback` when older indexes lack source capture
  metadata;
- expose the same freshness object in live answer diagnostics.

## Rationale

This keeps answer packets useful for agent/UI handoff without making them the
source of truth. Source URLs, local receipts, and generated indexes still own
the evidence chain; the answer packet only reports what freshness metadata
reached the handoff layer.

The fallback path is important because existing configured-storage runs may
have been indexed before capture metadata was propagated. They should remain
readable and evaluable while newer indexes become more precise.

## Alternatives

- Require a rebuild of every live index before answers can pass freshness
  gates. Rejected because it would make a public method change depend on heavy
  local generated state.
- Keep freshness only in docs or readiness audit prose. Rejected because future
  runtime consumers need a stable machine-readable field.
- Treat answer packet `created_at` as enough freshness context. Rejected because
  it describes rendering time, not when the source post was public or captured.

## Consequences

- Future answer consumers can display or reason over freshness without parsing
  snippets or receipts themselves.
- Older indexes produce a visible fallback note instead of pretending source
  capture metadata exists.
- Eval gates now fail if answer packets lose the freshness object or note.
- The packet remains a deterministic handoff surface; broad freshness verdicts
  and central proof claims stay outside this repository.

## Verification

- `connector/schemas/answer_packet.schema.json` requires answer freshness
  fields.
- `tests/unit/test_answer_packet.py` checks rendered packets from fixture and
  CLI paths.
- `tests/unit/test_search_eval.py` checks local and live answer eval freshness
  assertions.
- `docs/QUERY_MODEL.md` and `docs/RUNTIME_CONTRACT.md` document the handoff
  contract.
