# AOA-4PDA-D-0017: Root/Recovery Answer Packets

## Status

Accepted.

## Context

The Xiaomi 13T graph slice can now extract root and recovery action edges such
as `root_targets_file`, `root_uses_tool`, `recovery_targets_file`, and
`recovery_uses_tool`. `query-graph` exposes those edges, but the answer packet
renderer only summarized starter issue/fix/warning context. That made the agent
handoff weaker than the graph evidence already available.

The repository must remain a public method skeleton. It can commit deterministic
renderer logic, public-safe fixtures, and receipt-driven live eval definitions,
but it must not commit live corpora, indexes, graph exports, or generated answer
artifacts.

## Decision

Extend `aoa_4pda_answer_packet_v1` with additive root/recovery fields while
keeping the packet schema version stable:

- `root_action_labels`
- `recovery_action_labels`
- `target_file_labels`
- `tool_labels`
- `firmware_context_labels`

The renderer identifies those labels from cited graph relation edges and marks
the renderer as `starter_graph_context_v2`. It still does not use an LLM,
4PDA internal search, attachments, or network access.

Add two eval surfaces:

- `evals/suites/xiaomi_13t_answer_packets.json`, a public-safe fixture suite
  proving the answer shape without network access.
- `evals/suites/live_xiaomi_13t_answer_quality.json`, a receipt-driven live
  suite over an already-built Xiaomi 13T run in configured storage.

Add `aoa-4pda eval live-answer-quality` so operators can verify deterministic
answer packets after crawl, normalize, index, and graph receipts exist.

## Consequences

Agents and future UI/API adapters can consume compact answer packets for Xiaomi
root/recovery questions without reimplementing graph traversal. The source URL,
evidence refs, score details, and policy route remain attached to each answer.

The answer packet remains a handoff surface, not source truth. The local evals
prove connector-owned behavior only; central verdicts, scoring doctrine, and
regression authority remain outside this repository.
