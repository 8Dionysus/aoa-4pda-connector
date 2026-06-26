# Connector-Family Claim Contract

This document records which parts of the 4PDA claim runtime are portable
connector-family doctrine and which parts remain 4PDA/profile-specific.

## Portable Contract

The portable layer is the semantic vocabulary, not the 4PDA parser itself:

- `claim`
- `claim_relation`
- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`
- answer packet evidence chain
- source refs, post IDs, and claim IDs
- `read_only=true`
- `network_touched=false`
- `insufficient_evidence`

## Claim

A claim is a source-grounded assertion extracted from a public post. It can be
a method, warning, status, context, or risk claim.

Every claim needs:

- stable `claim_id`
- `claim_kind`
- action label
- target/tool/context labels when available
- source post reference
- evidence span
- freshness context
- confidence basis

## Claim Relation

Contract key: `claim_relation`.

Claim relations make forum information usable as a changing knowledge base:

- source supports or warns about a claim
- a method uses a tool
- a method targets an object
- a method requires a condition
- a warning targets an object or action
- a later claim supersedes an older claim
- claims contradict or contextualize each other

## Reports

The answer packet carries four portable report families:

- `conflict_report`
- `freshness_report`
- `applicability_report`
- `warning_report`

These reports are how the agent avoids treating old, risky, context-limited, or
disputed forum advice as timeless truth.

## Insufficient Evidence

`insufficient_evidence` is a first-class successful state. It means local
evidence cannot safely support an answer.

## 4PDA-Specific Boundary

The following stay source/profile-specific:

- 4PDA URL and route policy
- 4PDA HTML parser and quote/signature cleanup
- 4PDA internal-search denylist
- Xiaomi/Redmi aliases and firmware heuristics
- 4PDA profile seeds, discovery review, coverage, and refresh rules
- live Xiaomi 13T and Redmi Note 10 Pro eval cases

The following are conceptually reusable, but future connectors should adapt
them instead of importing 4PDA assumptions:

- claim/report vocabulary in `src/aoa_4pda_connector/claims`
- answer packet report shape in `src/aoa_4pda_connector/answer`
- graph claim relation semantics in `src/aoa_4pda_connector/graph`
- local eval pattern under `evals/`

Note that some current 4PDA packet and graph schema IDs still carry `aoa_4pda`
names for backwards compatibility. The stable connector-family layer is the
field contract and relation vocabulary; later extraction may introduce fully
generic package-level schema IDs once more connectors prove the shape.
