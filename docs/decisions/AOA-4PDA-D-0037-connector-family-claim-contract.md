# AOA-4PDA-D-0037: Connector-Family Claim Contract Boundary

## Status

Accepted.

## Context

The 4PDA connector now has claim, conflict, freshness, applicability, warning,
and answer-packet behavior over a bounded Xiaomi 13T proof corpus. That proves
usefulness for 4PDA, but one source does not prove connector-family
architecture.

The next proof source is XDA, which has similar forum shape but a distinct
source policy, parser, route boundary, and Android-device heuristics.

## Decision

Keep the connector-family claim/report doctrine duplicated in each connector
repo for now, using the same vocabulary and answer-packet field contract.

Do not extract a shared connector monorepo or shared package yet. The second
source proof should reveal what is actually portable before a shared owner is
created.

## Options Considered

- Keep the contract implicit in 4PDA code: rejected because future connector
  agents would copy 4PDA/Xiaomi assumptions without seeing the boundary.
- Create a shared `aoa-connectors` repo immediately: rejected because the
  common layer is not yet proven by multiple sources.
- Document the portable doctrine locally in 4PDA and XDA: chosen because it
  preserves a clear contract while keeping each connector independently
  publishable.

## Consequences

- 4PDA remains the implementation reference, not the universal package.
- XDA can use the same claim/report vocabulary while owning XDA parsing and
  policy.
- `abyss-stack` remains the runtime/MCP owner.
- `aoa-evals` remains central proof doctrine owner; connector repos own local
  eval ports only.
- Future extraction into a shared doctrine/package requires evidence from more
  than one connector and should not be done as a naming cleanup alone.

## Boundary Lenses

- Owner/source: this ADR owns 4PDA's local boundary and references XDA,
  `abyss-stack`, and `aoa-evals` as separate owners.
- Portability/overlay: relation vocabulary is portable; parser/extractor
  heuristics remain source/profile overlays.
- Lifecycle/time: shared extraction is deferred until a third connector or
  repeated duplication makes the common layer obvious.
