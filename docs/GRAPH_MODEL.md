# Graph Model

The graph is a derived navigation layer, not source truth.

## Node Kinds

- `forum`
- `topic`
- `post`
- `header_post`
- `device`
- `codename`
- `firmware_family`
- `firmware_version`
- `build_id`
- `tool`
- `file`
- `issue`
- `fix`
- `warning`
- `external_link`

Entity node ids are scoped by kind: `entity:<kind>:<value>`. This avoids
collapsing different facts that happen to share similar values.

## Edge Kinds

- `topic_contains_post`
- `post_mentions_entity`
- `topic_about_device`
- `fixes_issue`
- `warns_about`
- `supersedes`
- `quotes`
- `same_device_alias`

## Evidence

Every node or edge derived from content must include source refs and confidence.

## Starter Entity Extraction

Entity extraction v1 is heuristic and local:

- regexes for firmware versions, build IDs, files, and common device names
- small dictionaries for tools, firmware families, known codenames, and common
  issue words
- bounded fix/warning patterns around technical files such as `boot.img`

It is a navigation layer, not a final classifier.

## Starter Relation Edges

Relation edges v1 are heuristic and post-local:

- `fixes_issue` links a `fix` entity to an `issue` entity mentioned in the same
  post.
- `warns_about` links a `warning` entity to file, codename, device, firmware,
  or build entities explicitly named inside the warning text.

These edges preserve the source post ref and use lower confidence than direct
post/topic structure. They are useful navigation hints, not final proof that a
fix is universally correct or a warning applies outside its cited post.

## Starter Query Context

`aoa-4pda query-graph` uses the graph as an enrichment layer for local keyword
results. For each matched post it collects the post's mentioned entity nodes,
then attaches source-ref-matching `fixes_issue` and `warns_about` edges that
touch those entities.

The resulting `graph_context` stays inside the evidence packet result. It is
not a standalone graph verdict and does not make relation edges stronger than
their cited source refs and confidence values.

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
warning, and warned-target labels into a handoff surface for agents.
