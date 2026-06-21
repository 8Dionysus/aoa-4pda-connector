# AOA-4PDA-D-0032: Answer Evidence Chain

## Status

Accepted.

## Context

Gap-aware answer packets prevent weak candidates from becoming fake answers,
but a downstream agent still needs more than a flat list of snippets. For a
4PDA connector, the expected behavior is to find a usable chain of source
evidence: which post is primary, which posts add context, which query terms and
graph relations grounded the answer, how fresh the evidence is, and what was
filtered out.

If the answer layer only returns top-N candidates, runtime agents must rebuild
that reasoning themselves and can easily overstate noisy device-anchor matches.

## Decision

Make chain-aware handoff part of `aoa_4pda_answer_packet_v1`.

`aoa-4pda answer` now filters weak candidates, collapses duplicate chunks from
the same post, and emits:

- `answer_report.grounded_candidate_count`
- `answer_report.filtered_candidate_count`
- `answer_report.deduplicated_candidate_count`
- `answer_report.primary_evidence_grounding`
- `evidence_chain`
- `nuance_report`

`answers` remains a compact deterministic summary surface, but it is not the
raw retrieval top-N. The evidence packet and graph export remain the broader
candidate and relation surfaces.

## Rationale

This keeps the public connector useful for agent handoff without claiming that
the current corpus is complete. An answer packet should help an agent compose a
careful user-facing response from cited local evidence, while still exposing
freshness, filtered evidence, duplicate collapse, matched content terms, and
relation kinds.

## Alternatives

- Keep `answers` as a raw top-N rendering. Rejected because it preserves noisy
  matches and makes nuance invisible to downstream agents.
- Put chain construction only in the future runtime/MCP layer. Rejected because
  the source-specific connector already knows the local query, graph, source
  refs, and grounding details.
- Replace answer packets with an LLM synthesis step. Rejected for this layer:
  the repository needs a deterministic, no-network, inspectable contract first.

## Consequences

- Runtime consumers should prefer `evidence_chain` and `nuance_report` when
  composing an answer.
- Answer tests and readiness now protect chain awareness as part of answer
  quality.
- Future richer synthesis can sit above this packet, but it must preserve the
  chain and insufficient-evidence semantics.

## Verification

- `connector/schemas/answer_packet.schema.json` requires `evidence_chain` and
  `nuance_report`.
- `src/aoa_4pda_connector/answer/__init__.py` builds grounded, deduplicated
  chain steps and a nuance report.
- `docs/QUERY_MODEL.md`, `docs/RUNTIME_CONTRACT.md`, and
  `docs/CONNECTOR_READY.md` document chain-aware answer handoff.
- Unit and readiness tests cover chain fields and the readiness evidence flag.
