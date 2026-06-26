# Graph Model

The graph is a derived navigation layer, not source truth.

## Node Kinds

- `forum`
- `topic`
- `post`
- `header_post`
- `device`
- `device_model`
- `codename`
- `firmware_family`
- `firmware_version`
- `build_id`
- `tool`
- `file`
- `root_action`
- `recovery_action`
- `issue`
- `fix`
- `warning`
- `claim`
- `method`
- `action`
- `target`
- `condition`
- `applicability_context`
- `risk`
- `external_link`

Entity node ids are scoped by kind: `entity:<kind>:<value>`. This avoids
collapsing different facts that happen to share similar values.

## Edge Kinds

- `topic_contains_post`
- `post_mentions_entity`
- `topic_about_device`
- `fixes_issue`
- `warns_about`
- `root_targets_file`
- `root_uses_tool`
- `root_mentions_firmware`
- `recovery_targets_file`
- `recovery_uses_tool`
- `recovery_mentions_firmware`
- `claim_applies_to_context`
- `method_uses_tool`
- `method_targets_object`
- `method_requires_condition`
- `warning_targets_action`
- `warning_targets_object`
- `claim_contextualizes_claim`
- `claim_supersedes_claim`
- `claim_contradicts_claim`
- `claim_deprecated_for_context`
- `source_supports_claim`
- `source_warns_about_claim`
- `source_updates_claim`
- `supersedes`
- `quotes`
- `same_device_alias`

## Evidence

Every node or edge derived from content must include source refs and confidence.

## Starter Entity Extraction

Entity extraction v1 is heuristic and local:

- regexes for firmware versions, OS builds, model numbers, files, and common
  device names
- small dictionaries for tools, firmware families, known codenames, and common
  issue words
- bounded fix/warning patterns around technical files such as `boot.img`
- focused Xiaomi firmware/root/recovery action patterns around `boot.img`,
  `vendor_boot*.img`, `recovery.img`, Magisk, KSU/KernelSU, TWRP, OrangeFox,
  and fastboot

It is a navigation layer, not a final classifier.

## Starter Relation Edges

Relation edges v1 are heuristic and post-local:

- `fixes_issue` links a `fix` entity to an `issue` entity mentioned in the same
  post.
- `warns_about` links a `warning` entity to file, codename, device, firmware,
  or build entities explicitly named inside the warning text.
- `root_targets_file`, `root_uses_tool`, and `root_mentions_firmware` link a
  root action in a post to boot/init_boot image files, Magisk/KSU/KernelSU
  tools, and firmware entities mentioned in the same evidence.
- `recovery_targets_file`, `recovery_uses_tool`, and
  `recovery_mentions_firmware` link a recovery flash action in a post to
  recovery/vendor_boot image files, fastboot/TWRP/OrangeFox tools, and
  firmware entities mentioned in the same evidence.

These edges preserve the source post ref and use lower confidence than direct
post/topic structure. They are useful navigation hints, not final proof that a
fix is universally correct or a warning applies outside its cited post.

## Claim Semantics

Post/entity edges are not enough for forum knowledge that ages, conflicts, or
applies only under a version, region, tool, file, or state. The graph therefore
adds a portable claim layer:

- `claim` nodes preserve source URL, post id, topic id, timestamps, evidence
  excerpt, extraction rule, confidence basis, freshness context, and profile id.
- `method`, `action`, `target`, `tool`, `condition`,
  `applicability_context`, `risk`, and `warning` nodes expose the structure
  agents need before turning a post into advice.
- `claim_supersedes_claim`, `claim_contradicts_claim`,
  `claim_contextualizes_claim`, and `claim_deprecated_for_context` model local
  evidence pressure. They do not assert absolute truth.
- Every claim relation edge carries source refs, confidence, extraction basis,
  relation reason, freshness basis, and manual-review status.

The first extractor is deterministic and heuristic. It recognizes root,
recovery, firmware/update/rollback language, warning/risk statements,
works/no-longer/current-context wording, firmware/version/region constraints,
tools, files, actions, and uncertainty. The public packet contract is generic
so later XDA, StackOverflow, Telegram, Discord, or Facebook connectors can
write compatible claims from different source adapters.

## Starter Query Context

`aoa-4pda query-graph` uses the graph as an enrichment layer for local keyword
results. For each matched post it collects the post's mentioned entity nodes,
then attaches source-ref-matching relation edges that touch those entities.
The starter relation set currently includes issue/fix, warning/target,
root/file/tool/firmware, and recovery/file/tool/firmware hints.

For root/recovery-intent queries, `query-graph` applies a small
relation-intent rerank after keyword retrieval and graph enrichment. The raw
keyword order is preserved as `keyword_rank`; the graph order is exposed as
`graph_rank`. Relation edges only contribute to this rerank when their
tool/file/firmware endpoint matches the concrete query terms, so a generic
`boot.img` root relation does not outrank a Magisk-specific relation for a
Magisk query.

The resulting `graph_context` stays inside the evidence packet result. It is
not a standalone graph verdict and does not make relation edges stronger than
their cited source refs and confidence values.

Claim-aware graph context additionally carries `claim_node_ids`, `claims`,
`methods`, and claim relation edges. This is the surface used by answer packets
and MCP to distinguish primary, supporting, conflicting, superseding, and
contextual evidence.

## Starter Graph Eval

`aoa-4pda eval graph-relations` runs
`evals/suites/starter_graph_relations.json`. It normalizes the sanitized
live-shaped HTML fixture, builds a temporary graph, and checks that expected
entity nodes, `post_mentions_entity` edges, `fixes_issue` edges, and
`warns_about` edges exist for issue, fix, warning, file, and tool evidence.

This is connector-local evidence only. It does not claim full relation
extraction quality and does not promote relation edges to a validated central
proof verdict.

`aoa-4pda eval graph-query-packets` additionally checks that a graph-enriched
query packet carries the expected relation context for the same public-safe
fixture without touching the network or committing generated graph artifacts.

`aoa-4pda answer` consumes that graph context to render deterministic answer
packets. The renderer does not add graph truth; it copies cited issue, fix,
warning, warned-target, root/recovery action, target file, tool, and firmware
labels into a handoff surface for agents.

`evals/suites/xiaomi_13t_graph_relations.json` is a focused graph relation
suite for the Xiaomi 13T profile. It checks public-safe fixture evidence for
`Xiaomi 13T`, `2306EPN60G`, `aristotle`, `HyperOS 2.0.2`, Magisk/KSU/KernelSU,
TWRP/OrangeFox/fastboot, boot/recovery image files, and the root/recovery
relation edges that make those posts navigable without using 4PDA internal
search.

`evals/suites/live_xiaomi_13t_graph_query_quality.json` is the matching
receipt-driven live gate. It does not build a new corpus; it reads an
operator-materialized Xiaomi 13T run from configured storage and checks that
`query-graph` returns cited root/recovery relation context from the existing
keyword index and graph export, including relation-intent rerank for hard
recovery queries whose rich evidence starts below keyword rank 1.

`evals/suites/live_xiaomi_13t_answer_quality.json` renders those existing local
graph-query packets into answer packets and checks the same root/recovery
context at the agent handoff layer.

`aoa-4pda eval claim-relations` runs
`evals/suites/starter_claim_conflict_relations.json`. It checks claim/method/
context/warning nodes, supersedes/contradicts/contextualizes/deprecated
relations, and relation audit metadata over a sanitized multi-post fixture.
