# AOA-4PDA-D-0010: Starter Answer Packets

- Status: accepted
- Date: 2026-06-19

## Context

`AOA-4PDA-D-0009` exposed post-local graph relation context inside evidence
packets. That is useful for agents, but a caller still has to interpret
`issues`, `fixes`, `warnings`, and warned targets before it can show or hand
off a practical answer.

The connector needs an answer surface, but it must not turn starter graph
heuristics into unsupported prose. It also must not introduce an LLM dependency,
live crawl, internal search route, or generated answer artifact in Git.

## Decision

Add starter answer packets:

- `aoa-4pda answer` reads the existing local index and graph receipts, builds a
  graph-enriched evidence packet, and renders `aoa_4pda_answer_packet_v1`.
- The renderer is deterministic and local. It copies issue, fix, warning, and
  warned-target labels from `graph_context` into structured answer fields.
- `answer_text` is a compact reproducible summary of those same labels.
- Each answer keeps source URL, evidence refs, score details, source refs, and
  confidence basis visible.
- `aoa-4pda eval answer-packets` checks the rendered answer shape against a
  sanitized live-shaped fixture without touching the network.

## Alternatives Considered

- Use an LLM to synthesize the answer. Rejected for this starter layer because
  it would add runtime/provider concerns before the evidence contract is stable.
- Leave answer rendering to downstream agents only. Rejected because every
  agent would need to rediscover the same safe mapping from graph context to
  user-facing issue/fix/warning fields.
- Replace evidence packets with answer packets. Rejected because answer packets
  are handoff convenience, while evidence packets and source refs remain the
  stronger evidence surface.

## Consequences

- Agents and future UI/API adapters can consume a compact answer packet without
  manually traversing starter graph context.
- The output is intentionally conservative: it summarizes cited post-local
  relation hints and does not claim global correctness.
- Future richer answer synthesis can add multi-post reasoning or LLM-assisted
  prose, but must keep source refs, policy boundaries, and confidence basis
  visible.

## Boundaries

- `aoa-4pda-connector` owns the local renderer, CLI command, answer schema,
  suite, and compact eval report.
- `aoa-evals` remains the proof owner for central verdicts, scoring authority,
  and regression truth.
- No live crawl, internal search route, attachment route, vector index, graph
  database, LLM dependency, or generated answer export is introduced.
- Answer packets are deterministic agent handoff surfaces, not source truth and
  not a claim that a fix or warning applies outside the cited post.

## Source Surfaces

- `connector/schemas/answer_packet.schema.json`
- `src/aoa_4pda_connector/answer/__init__.py`
- `src/aoa_4pda_connector/cli.py`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `evals/suites/starter_answer_packets.json`
- `tests/unit/test_answer_packet.py`
- `docs/QUERY_MODEL.md`
