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

## Answer Contract

Every answer should carry:

- source URL
- topic id and post id when known
- observed/captured timestamps
- matched chunks or post refs
- query report and score breakdown when produced by a local index
- freshness note
- policy route note
