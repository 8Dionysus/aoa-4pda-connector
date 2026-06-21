# AOA-4PDA-D-0033: Deterministic Agent Answer

## Status

Accepted.

## Context

`evidence_chain` and `nuance_report` make answer packets inspectable, but a
runtime agent still needs a small ready-to-use brief: cited text, freshness, and
limitations in one field. Without that field, every downstream adapter has to
rebuild the same handoff logic and may lose citation or insufficient-evidence
semantics.

The connector should help agents answer, but it must not pretend to own LLM
synthesis, central proof verdicts, or source truth.

## Decision

Add `agent_answer` to `aoa_4pda_answer_packet_v1`.

`agent_answer` is a deterministic cited brief generated only from the local
answer packet:

- `evidence_chain`
- `nuance_report`
- `answer_report`

For answered packets it emits `deterministic_cited_brief_v1` text with bracket
citations such as `[1]`, source citation metadata, freshness, and limitations.
For insufficient-evidence packets it emits the missing-evidence text and keeps
citations empty.

## Rationale

This gives runtime consumers an immediate handoff surface while preserving the
source route. The brief is useful for a first agent response, but source URLs,
receipts, evidence packets, and graph exports remain stronger authority.

## Alternatives

- Leave synthesis entirely to `abyss-stack`. Rejected because the connector has
  the source-specific chain, freshness, and grounding details needed to produce
  a safe deterministic brief.
- Add an LLM answer step inside this repository. Rejected because this public
  connector must remain no-network and deterministic for install, tests, and
  local evals.
- Only expose `answers`. Rejected because `answers` is a compact structured
  summary, not a cited text handoff with freshness and limitations.

## Consequences

- Runtime layers can display or further synthesize from `agent_answer`, but
  should keep `evidence_chain` available for inspection.
- Tests, schema, readiness, and live answer evals protect the field.
- Future richer synthesis must preserve citation refs and insufficient-evidence
  behavior.

## Verification

- `connector/schemas/answer_packet.schema.json` requires `agent_answer`.
- `src/aoa_4pda_connector/answer/__init__.py` emits
  `deterministic_cited_brief_v1`.
- `src/aoa_4pda_connector/evaluation/__init__.py` checks live answer packets
  for `agent_answer` presence, answered status, primary citation text, and top
  post citation.
- Unit and contract tests cover answered and insufficient-evidence briefs.
