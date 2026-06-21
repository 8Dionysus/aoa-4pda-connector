# Query Model

The connector should answer through local evidence packets.

## Search Layers

- exact token search for device models, build IDs, versions, and error strings
- BM25 keyword search over evidence chunks from public topic/post text
- exact-term and exact-phrase boosts for tokens such as `boot.img`,
  `V14.0.7.0`, device model numbers, and model phrases
- deterministic local vector search for lightweight similarity recall without
  a model download or API dependency
- entity search for devices, apps, firmware, versions, issues, fixes, warnings
- graph traversal for relations between topics, posts, fixes, and warnings

Entity extraction currently covers devices, device models, codenames, firmware
families, firmware versions, build IDs, tools, files, root actions, recovery
actions, issues, fixes, and warnings through local heuristics.

## Local Scoring

The starter and focused-device keyword query paths use `bm25_exact_v1`:

- split normalized posts into deterministic overlapping evidence chunks
- tokenize public topic titles and post text with Cyrillic/Latin/digit support
- preserve dotted and dashed technical tokens such as `boot.img`
- add technical aliases for split forms such as `boot img`,
  `recovery img`, `V 14 0 7 0`, separated model strings such as `SM G991B`,
  split Xiaomi model strings such as `2306 EPN60G`, and device aliases such as
  `sweet` for `Redmi Note 10 Pro` or `aristotle` for `Xiaomi 13T`
- compute BM25 over the local chunk inverted index
- boost exact terms and exact model/version phrases
- return matched terms, matched exact terms, matched phrases, and score
  breakdowns in the evidence packet
- report derived aliases as `technical_terms` so evals can check normalization
  separately from top-result rank
- build snippets around the first matched query term instead of always cutting
  from the beginning of the post or chunk
- return `chunk_id`, `chunk_index`, source character offsets, and both
  `chunk:*` and `post:*` evidence refs
- derive default packet ids from a stable SHA-256 query digest so repeated
  processes export the same packet id for the same query

## Deterministic Hybrid Query Packets

`aoa-4pda build-vector` builds a compact `aoa_4pda_vector_index_v1` artifact
from normalized evidence chunks. The starter algorithm is
`hashed_char_ngram_vector_v1`: it hashes token and character n-gram features
into a fixed-size normalized sparse vector. It is deliberately model-free so a
fresh clone can build and test vector participation without downloading
embeddings, calling an API, or committing a vector store.

`aoa-4pda query-hybrid` reads the keyword index, deterministic vector index,
and graph export for the same run. When graph receipts are available it scores
with `hybrid_bm25_vector_graph_v1`: normalized keyword and vector scores remain
visible, while matching root/recovery relation evidence contributes a bounded
`relation_intent_saturation_v1` boost. `score_breakdown` preserves
`keyword_raw`, `vector_raw`, `graph_raw`, normalized components, graph boost,
and the pre-graph hybrid score so ranking changes stay auditable.

The graph boost is intentionally narrow. It is derived from `relation_rerank`
evidence: matching relation edge count, distinct relation kinds, and confidence
for the query intent. A post that merely has graph context does not receive a
boost; a post must match root/recovery relation evidence such as
`root_targets_file`, `root_uses_tool`, `recovery_targets_file`, or
`recovery_uses_tool`.

This vector layer is a portable recall contract, not a claim of production
semantic quality. A later embedding backend can replace or supplement it if the
adapter writes compatible receipts and remains outside Git-tracked heavy data.

## Starter Graph Query Packets

`aoa-4pda query-graph` adds graph context to the local keyword result packet.
It reads an already-built local keyword index and graph export from external
storage receipts, runs the same BM25/exact query, and adds `graph_context` to
each result.

The starter graph context is post-local:

- `entity_node_ids` lists entities mentioned by the matched post.
- `relation_edges` includes source-ref-matching relation edges touching those
  entities. The starter relation set includes `fixes_issue`, `warns_about`,
  root action edges to files/tools/firmware, and recovery action edges to
  files/tools/firmware.
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
- `root_action_labels`, `recovery_action_labels`, `target_file_labels`,
  `tool_labels`, and `firmware_context_labels` are derived from cited
  root/recovery relation edges when present.
- `answer_text` is a short reproducible summary of those labels.
- `source_url`, `evidence_refs`, score details, and source refs remain attached
  to each answer.
- `posted_at`, `captured_at`, and `freshness` carry the public post timestamp,
  local capture timestamp, and fallback packet-created context when older
  indexes do not yet include capture metadata.
- `confidence` names the starter graph context as the basis and keeps relation
  confidence visible.
- `answer_report.answer_status` is `answered` only when local candidates have
  enough content grounding or relation support. Weak device-anchor candidates
  are filtered out, duplicate chunks from the same post are collapsed, and
  `answer_report` reports candidate, grounded, filtered, and deduplicated
  counts.
- `evidence_chain` mirrors the grounded answer handoff as ordered chain steps
  with role, source URL, topic/post/chunk ids, matched content terms, relation
  kinds, evidence refs, and freshness.
- `nuance_report` summarizes the chain breadth, relation kinds, matched
  content terms, freshness spread, and limitations such as weak filtered
  candidates or duplicate same-post chunks.
- `agent_answer` is a deterministic cited brief built from `evidence_chain`
  and `nuance_report`. It is not LLM synthesis: it carries bracket citations,
  freshness, limitations, and insufficient-evidence text directly from the
  local answer packet.
- When candidates are empty or below the grounding threshold, `answers` and
  `evidence_chain` stay empty, `agent_answer.citations` stays empty, and
  `answer_report.missing_evidence_note` says `В базе недостаточно данных...`.
  This is the connector's starter insufficient evidence guard, not an LLM
  refusal layer.

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
terms, specific-term reporting, technical-term normalization, and the
internal-search boundary. It does not crawl, rebuild a corpus, or commit
generated artifacts.

For an already-built Xiaomi 13T focused run, pass
`--suite evals/suites/live_xiaomi_13t_search_quality.json`. That suite checks
`aristotle`, split `2306 EPN60G`, `boot.img`, and `recovery.img` retrieval over
configured local storage only.

`aoa-4pda eval live-search-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_ranking_pressure.json`
runs a Xiaomi 13T ranking-pressure gate over the same existing keyword index.
It checks that known high-signal root/recovery posts remain present within a
bounded top-N window for harder OrangeFox, vendor_boot, KernelSU, and HyperOS
recovery queries, and returns compact diagnostics with the top result plus the
ranked expected result. It does not crawl or rebuild the run.

`aoa-4pda eval live-hybrid-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_hybrid_query_quality.json`
runs the focused Xiaomi 13T hybrid gate against an already-built bounded run.
It reads configured crawl, normalize, index, vector, and graph receipts, then
checks that local `query-hybrid` packets preserve keyword/vector/graph score
participation, promote relation-rich root and recovery evidence, preserve
source URLs and graph context, and keep the internal-search boundary. It does
not crawl, rebuild the corpus, use 4PDA internal search, or commit generated
artifacts.

`aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json`
runs the focused Xiaomi 13T graph-query gate against an already-built bounded
run. It reads configured crawl, normalize, index, and graph receipts, then
checks that local `query-graph` packets preserve root/recovery relation context
such as `root_targets_file`, `root_uses_tool`, `recovery_targets_file`, and
`recovery_uses_tool`. For root/recovery-intent queries, graph packets preserve
the original `keyword_rank` and may rerank candidates by matching
tool/file/firmware relation endpoints to concrete query terms. It does not
crawl, rebuild the corpus, use 4PDA internal search, or commit generated
artifacts.

`aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json`
runs the focused Xiaomi 13T answer gate against the same existing receipts. It
renders local graph-query packets into answer packets and checks that
root/recovery actions, target files, tools, firmware context, source refs, and
freshness notes, answer grounding, and the internal-search boundary survive the
answer renderer. The rendered packet is chain-aware: weak candidates are
filtered, duplicate post chunks are collapsed, and downstream agents can follow
`agent_answer`, `evidence_chain`, and `nuance_report` before composing a
user-facing answer.
Each live answer case also returns compact diagnostics: failed check names,
matched terms, score breakdown, top evidence refs, answer context label counts,
freshness context, and relation edges that reached the answer.

`aoa-4pda eval graph-query-packets` runs
`evals/suites/starter_graph_query_packets.json`. It builds temporary local
index and graph artifacts from the sanitized live-shaped fixture and checks
that graph-enriched query packets preserve expected relation context and source
refs without touching the network.

`aoa-4pda eval hybrid-query-packets` runs
`evals/suites/starter_hybrid_query_packets.json`. It builds temporary keyword,
deterministic vector, and graph artifacts from the sanitized live-shaped
fixture and checks that a hybrid packet returns the expected cited post,
preserves vector and graph score participation, graph context, source refs, and
the internal-search boundary.

`aoa-4pda eval graph-relations --suite evals/suites/xiaomi_13t_graph_relations.json`
runs the focused Xiaomi 13T graph suite. It checks that sanitized firmware
fixture evidence yields Xiaomi 13T, model number, codename, HyperOS, Magisk/KSU,
TWRP/OrangeFox/fastboot, boot/recovery image nodes, and root/recovery relation
edges in the graph export.

`aoa-4pda eval answer-packets` runs
`evals/suites/starter_answer_packets.json`. It checks that deterministic answer
packets preserve expected issue/fix/warning labels, source refs, freshness
notes, and the internal-search boundary.

`aoa-4pda eval answer-packets --suite evals/suites/xiaomi_13t_answer_packets.json`
runs the focused public-safe answer suite over the sanitized Xiaomi 13T fixture.
It checks deterministic root/recovery/file/tool/firmware labels without using
network or committing generated artifacts, and verifies that the rendered
answer carries freshness context.

## Answer Contract

Every answer should carry:

- source URL
- topic id and post id when known
- observed/captured timestamps
- matched chunks or post refs
- graph context when relation traversal was requested
- vector report and hybrid score breakdown when hybrid retrieval was requested
- deterministic answer text when answer rendering was requested
- ordered `evidence_chain` steps for grounded answer handoff
- `nuance_report` with filtered/deduplicated candidate counts and chain
  freshness context
- deterministic `agent_answer` brief with bracket citations and no extra facts
  beyond the answer chain
- `answer_status`, gap reason, and missing-evidence note when answer grounding
  is insufficient
- query report and score breakdown when produced by a local index
- freshness note
- policy route note
