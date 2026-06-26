# AOA-4PDA-D-0035: Deep Runtime Answer Grounding

## Status

Accepted.

## Context

The Xiaomi 13T reference profile moved from a narrow answer smoke path to a
deep runtime contract. Agents should be able to ask current-method,
brick/bootloop, warning, freshness, and out-of-scope questions without the
connector fabricating confidence from unrelated graph context.

The previous answer grounding allowed any relation edge to count as relation
support. That could turn a weakly matched question about unrelated topics, or a
warning-intent query with no warning semantics, into an ordinary recovery/root
answer.

## Decision

Tighten answer grounding and live answer evals:

- relation support must align with relation-rerank intent when that diagnostic
  is present;
- broad content queries need stronger term grounding than compact questions;
- explicit warning-intent queries require warning semantics in graph context
  (`warnings`, `warned_targets`, or `warns_about`);
- live answer eval cases can assert `agent_answer`, `answer_report`,
  `nuance_report`, freshness, policy, `network_touched=false`, grounded
  candidate counts, and warning-request/support state;
- the Xiaomi 13T information-need matrix distinguishes grounded answers,
  warning-supported answers, insufficient-evidence guardrails, and deeper
  claim/conflict semantics.

## Rationale

This keeps the connector useful for agents without claiming more than the local
evidence proves. A correct insufficient-evidence packet is better than an
unsupported answer because it drives the next bounded seed, crawl, graph, or
eval slice.

## Alternatives

- Keep accepting any graph relation as enough answer grounding. Rejected
  because unrelated recovery/root relations can mask real coverage gaps.
- Treat warning words as normal recovery/root search terms. Rejected because a
  warning question has a different safety contract than a recovery how-to.
- Mark conflict/supersession as covered without explicit graph semantics.
  Rejected here; the later AOA-4PDA-D-0036 layer covers it through claim-level
  graph semantics.

## Consequences

- Some queries now return `insufficient_evidence` where they previously returned
  a weak snippet or unrelated relation summary.
- Warning-intent queries can become answered when warning semantics are present,
  but the answer must preserve warning reports instead of flattening the risk
  into an ordinary recovery instruction.
- AOA-4PDA-D-0036 extends this grounding layer with explicit
  conflict/supersession/freshness semantics.

## Verification

- `src/aoa_4pda_connector/answer/__init__.py` checks intent-aligned relation
  support and warning semantics.
- `src/aoa_4pda_connector/evaluation/__init__.py` supports runtime-contract
  expectations for answer reports, agent answers, freshness, policy, and
  warning grounding.
- `evals/suites/live_xiaomi_13t_answer_quality.json` includes current-method,
  brick/bootloop gap, warning-supported answer, and unrelated-topic gap cases.
- `connector/profiles/xiaomi_13t_information_needs.json` reports the warning
  case as a covered warning-supported answer route.
