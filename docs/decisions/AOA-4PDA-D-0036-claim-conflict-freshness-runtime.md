# AOA-4PDA-D-0036: Claim Conflict Freshness Runtime

## Status

Accepted.

## Context

Post-level search can find relevant forum text, but it cannot safely answer
questions such as "is this still current?", "which post is primary?", "does a
newer post supersede this?", or "does this warning apply to my context?" Forum
knowledge ages, conflicts, and depends on device, firmware, file, tool, region,
and state.

## Decision

Add a portable claim layer to the graph and answer packet contract:

- deterministic first-pass claim extraction over normalized posts;
- claim/method/action/target/tool/condition/context/risk/warning structure;
- relation edges for applies-to-context, uses-tool, targets-object,
  requires-condition, warning-targets, supports, warns, updates, supersedes,
  contradicts, contextualizes, and deprecated-for-context;
- relation audit metadata: source refs, confidence, extraction basis, relation
  reason, freshness basis, and manual-review status;
- answer packet reports for conflict, freshness, applicability, and warnings;
- local eval suites before any crawl expansion.

The layer is connector-family doctrine. 4PDA owns its source adapter and
heuristics, but the public claim/report contracts are reusable by future XDA,
StackOverflow, Telegram, Discord, Facebook, and similar connectors.

## Consequences

- Post-level graph context remains useful but is no longer sufficient for
  current-method or risky-action answers.
- Insufficient evidence is a successful bounded result when freshness,
  conflict, warning, context, or source coverage is missing.
- MCP must preserve conflict/freshness/applicability/warning reports and claim
  ids instead of flattening answer packets.
- Generated claim graphs remain runtime artifacts outside Git; Git stores the
  method, schemas, fixtures, tests, and eval suites.
