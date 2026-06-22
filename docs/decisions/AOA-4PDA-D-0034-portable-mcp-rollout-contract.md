# AOA-4PDA-D-0034: Portable MCP Rollout Contract

## Status

Accepted.

## Context

The connector now produces agent-ready answer packets with `agent_answer`,
`evidence_chain`, `nuance_report`, and freshness/limitation context. Agents need
an MCP access plane over those packets, but runtime services belong in
`abyss-stack`, not in this public connector repository.

At the same time, the public repository must remain useful outside OS Abyss. A
third-party agent should be able to fork the repository, configure storage, and
build or install a compatible MCP adapter without inheriting private stack
paths or local heavy data.

## Decision

Add `docs/MCP_ROLLOUT.md` as the portable MCP contract for a service named
`aoa-4pda-connector-mcp`.

The document defines:

- the owner split between this repository and `abyss-stack`;
- the required connector storage roots;
- the read-only wrapped CLI commands;
- the minimal `status`, `answer`, and `source_route` MCP surface;
- packet preservation requirements for `aoa_4pda_answer_packet_v1`;
- standalone and OS Abyss rollout routes.

The connector repository owns this contract and the source packet behavior.
`abyss-stack` owns the OS Abyss runtime MCP implementation.

## Rationale

This keeps the public repository portable while preventing runtime authority
from drifting into a source connector repo. The MCP service can evolve as an
adapter over stable CLI and JSON contracts, while heavy mutable data remains in
configured storage roots outside Git.

## Alternatives

- Put the MCP implementation directly in this repository. Rejected because it
  would make the source connector own runtime deployment and stack lifecycle.
- Put only stack-local documentation in `abyss-stack`. Rejected because outside
  users would not have a portable contract for building a compatible adapter.
- Expose crawl, refresh, build, or reindex tools immediately. Rejected because
  the first MCP slice should be a safe read-only answer/status plane over
  already materialized local data.

## Consequences

- Future MCP adapters must preserve source answer packet fields instead of
  reconstructing weaker summaries.
- OS Abyss should implement `aoa-4pda-connector-mcp` under
  `abyss-stack/mcp/services/`.
- Network, crawl, refresh-build, and write operations remain outside the first
  MCP slice until a separate decision widens the surface.

## Verification

- `docs/MCP_ROLLOUT.md` names `aoa-4pda-connector-mcp`, required storage roots,
  read-only/no-network boundaries, and answer packet preservation.
- `docs/RUNTIME_CONTRACT.md` links the portable MCP rollout contract.
- `scripts/validate_connector.py` requires the rollout document and key
  boundary tokens.
