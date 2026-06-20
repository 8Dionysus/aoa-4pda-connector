# Query Model

The connector should answer through local evidence packets.

## Search Layers

- exact token search for device models, build IDs, versions, and error strings
- BM25 keyword search over evidence chunks from public topic/post text
- exact-term and exact-phrase boosts for tokens such as `boot.img`,
  `V14.0.7.0`, device model numbers, and model phrases
- optional vector search for paraphrase recall
- entity search for devices, apps, firmware, versions, issues, fixes, warnings
- graph traversal for relations between topics, posts, fixes, and warnings

Entity extraction v1 currently covers devices, codenames, firmware families,
firmware versions, build IDs, tools, files, issues, fixes, and warnings through
local heuristics.

## Starter Scoring

The starter query path uses `bm25_exact_v1`:

- split normalized posts into deterministic overlapping evidence chunks
- tokenize public topic titles and post text with Cyrillic/Latin/digit support
- preserve dotted and dashed technical tokens such as `boot.img`
- compute BM25 over the local chunk inverted index
- boost exact terms and exact model/version phrases
- return matched terms, matched exact terms, matched phrases, and score
  breakdowns in the evidence packet
- build snippets around the first matched query term instead of always cutting
  from the beginning of the post or chunk
- return `chunk_id`, `chunk_index`, source character offsets, and both
  `chunk:*` and `post:*` evidence refs
- derive default packet ids from a stable SHA-256 query digest so repeated
  processes export the same packet id for the same query

## Starter Graph Query Packets

`aoa-4pda query-graph` adds graph context to the local keyword result packet.
It reads an already-built local keyword index and graph export from external
storage receipts, runs the same BM25/exact query, and adds `graph_context` to
each result.

The starter graph context is post-local:

- `entity_node_ids` lists entities mentioned by the matched post.
- `relation_edges` includes source-ref-matching `fixes_issue` and
  `warns_about` edges touching those entities.
- `issues`, `fixes`, `warnings`, and `warned_targets` summarize the graph
  nodes needed to answer "what fixes this?" and "what is this warning about?"

The packet remains an evidence packet, not a graph proof verdict. The graph
context is a navigation layer over cited posts, and it inherits the starter
relation heuristics and their limits.

## Starter Answer Packets

`aoa-4pda answer` renders a graph-enriched evidence packet into a compact
`aoa_4pda_answer_packet_v1` answer packet. It uses deterministic local rules,
not an LLM:

- `issue_labels`, `fix_labels`, `warning_labels`, and
  `warned_target_labels` are copied from `graph_context`.
- `answer_text` is a short reproducible summary of those labels.
- `source_url`, `evidence_refs`, score details, and source refs remain attached
  to each answer.
- `confidence` names the starter graph context as the basis and keeps relation
  confidence visible.

Answer packets are for agent handoff and UI/API ergonomics. They do not replace
the evidence packet, graph export, or source URL as the truth surface.

## Starter Search Eval

`aoa-4pda eval search-quality` runs the local
`evals/suites/starter_search_quality.json` suite. It builds a temporary chunk
index from synthetic normalized fixtures and checks expected top posts,
chunk refs, exact-term matches, source URLs, query report unit, and the
internal-search boundary. The report is connector-local evidence, not a central
`aoa-evals` verdict.

`aoa-4pda eval live-search-quality --run <run-id>` runs
`evals/suites/live_starter_search_quality.json` against an already-built
bounded live starter run. It reads configured storage receipts and the keyword
index for the named run, then checks expected top posts, source URLs, exact
terms, specific-term reporting, and the internal-search boundary. It does not
crawl, rebuild a corpus, or commit generated artifacts.

`aoa-4pda eval graph-query-packets` runs
`evals/suites/starter_graph_query_packets.json`. It builds temporary local
index and graph artifacts from the sanitized live-shaped fixture and checks
that graph-enriched query packets preserve expected relation context and source
refs without touching the network.

`aoa-4pda eval answer-packets` runs
`evals/suites/starter_answer_packets.json`. It checks that deterministic answer
packets preserve expected issue/fix/warning labels, source refs, and the
internal-search boundary.

## Answer Contract

Every answer should carry:

- source URL
- topic id and post id when known
- observed/captured timestamps
- matched chunks or post refs
- graph context when relation traversal was requested
- deterministic answer text when answer rendering was requested
- query report and score breakdown when produced by a local index
- freshness note
- policy route note
