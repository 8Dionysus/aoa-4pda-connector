# AOA-4PDA-D-0031: Answer Gap Awareness

## Status

Accepted.

## Context

The connector-ready goal requires source-grounded answers with explicit gap
awareness. A local keyword/graph query can legitimately return candidate posts
for broad device anchors such as `Xiaomi 13T`, while still failing to match the
actual user intent. If the answer renderer turns those weak candidates into
snippet answers, downstream agents may treat noise as knowledge.

The answer layer must stay deterministic and local, but it also needs a small
grounding gate between "search found candidates" and "the connector can answer
this question".

## Decision

Make answer grounding status part of `aoa_4pda_answer_packet_v1`.

`aoa-4pda answer` now renders ordinary answers only when top evidence has
sufficient content grounding or graph relation support. If there are no
candidates, unmatched structured query terms, or only weak device-anchor
matches, the packet keeps `answers` empty and reports:

- `answer_report.answer_status=insufficient_evidence`
- `answer_report.gap_reason`
- `answer_report.missing_evidence_note`
- `answer_report.top_evidence_grounding`

The CLI command can still exit successfully because the local route worked; the
packet itself tells the caller that the configured database is not enough for a
reliable answer.

## Rationale

This keeps answer packets useful without pretending that starter search is a
complete semantic oracle. Search and graph packets remain candidate-evidence
surfaces. Answer packets add a deterministic handoff contract: answer when the
local evidence is grounded, otherwise expose the gap in machine-readable form.

## Alternatives

- Always return the top snippet. Rejected because device-anchor matches can
  produce plausible but unsupported answers.
- Fail the CLI when no reliable answer exists. Rejected because a no-answer
  packet is a valid local result and can guide coverage, refresh, or seed
  expansion.
- Push gap detection entirely to downstream agents. Rejected because the public
  connector skeleton should protect its own answer handoff contract.

## Consequences

- Positive answer evals now require `answer_status=answered`.
- Fresh clones and runtime consumers can distinguish command success from
  knowledge sufficiency.
- Future richer answer synthesis must preserve the insufficient-evidence route
  instead of silently filling gaps.

## Verification

- `connector/schemas/answer_packet.schema.json` requires answer status and
  candidate result count.
- `src/aoa_4pda_connector/answer/__init__.py` emits insufficient-evidence
  packets when grounding is weak.
- Unit and contract tests cover weak-candidate and no-candidate answer gaps.
- `aoa-4pda ready` includes gap awareness in `answer_quality_gates`.
