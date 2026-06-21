# Architecture

`aoa-4pda-connector` is a source connector, not a runtime service and not a
corpus archive.

## Pipeline

```text
seeds/profile
-> policy gate
-> public topic fetch
-> crawl receipts
-> parse topic/post HTML
-> normalize topic/post records
-> chunk and entity extraction
-> local keyword/vector indexes and graph
-> graph-enriched evidence packets
-> graph-aware hybrid keyword/vector evidence packets
-> deterministic answer packets
-> discovery audit over stored public snapshot links
-> seed-review audit over discovery candidates
-> coverage and quality audits over the named run
-> freshness and refresh audit before reusing or updating the run
```

## Parser Posture

The parser is fixture-backed, not raw-corpus-backed. Tiny sanitized HTML
fixtures may mimic live 4PDA structure, but raw live pages stay in configured
storage roots and must not be committed.

Current parser coverage includes:

- old table-based public topic posts with `data-post` and `post-main-*` ids
- post author labels from the public post header
- raw public post date labels from the public post header
- quote, edit-note, and signature text removal before indexing

## Chunking Posture

Chunking is a derived navigation layer. It splits normalized post text into
deterministic overlapping evidence chunks so local search can rank and cite a
precise fragment inside a long post. Chunks carry the original topic id, post
id, source URL, chunk index, and source character offsets. They do not replace
the normalized post or public source URL as evidence authority.

## Source and Derived Layers

| Layer | Example | Authority |
| --- | --- | --- |
| Source policy | `connector/SOURCE_POLICY.md` | repository |
| Raw public snapshot | `CONNECTOR_DATA_ROOT` | source URL + receipt |
| Normalized record | data root | parser output with source refs |
| Search index | cache root | derived chunk navigation |
| Vector index | cache root | deterministic no-model similarity navigation |
| Graph DB | artifact root | derived navigation |
| Evidence packet | examples/exported packets | answer support, not site truth |
| Graph query context | `graph_context` in packets | derived navigation over cited posts |
| Answer packet | `aoa_4pda_answer_packet_v1` | deterministic agent handoff, not source truth |

Generated indexes, vectors, and graphs help navigation. They do not replace
source URLs or policy receipts.

Current answer packets can summarize starter issue/fix/warning context and
focused Xiaomi root/recovery/file/tool/firmware relation labels from cited graph
context. They also preserve public post timestamps, local capture timestamps
when available, and fallback packet-created freshness context for older indexes.

Configured storage may be the ignored repo-local `.connector-state/` scaffold
for small starter runs or an external storage root for larger materialization.

`aoa-4pda materialize fixture` is the no-network materialization route. It
starts at the sanitized live-shaped fixture, runs the same parser/normalizer,
keyword-index, vector-index, graph, and answer-ready receipt path as a bounded
crawl-derived run, and writes generated state only to configured storage roots.

## Runtime Boundary

Future MCP/runtime exposure belongs in `abyss-stack` and should consume an
installed connector through configured data/artifact roots.

`docs/RUNTIME_CONTRACT.md` names the current CLI, JSON, and storage handoff
surfaces. `aoa-4pda ready` audits whether those surfaces and the broader
`connector-ready-v1` maturity target are present without touching the network.
`aoa-4pda discovery audit <profile>` audits review-ready public topic/window
candidates already visible in stored raw snapshots before seed expansion. It
excludes windows already covered by the seed plan and emits source/anchor
evidence plus review priority for the remaining candidates.
`aoa-4pda discovery review <profile>` compares those candidates with the
repo-local seed-review manifest and reports accepted candidates that still need
seed updates.
`aoa-4pda coverage audit <profile>` audits whether a bounded profile's seed
windows, receipts, index, vector index, graph, and local quality gates are
actually present for a named run, also without touching the network.
`aoa-4pda refresh audit
<profile>` audits crawl age, derived receipt ordering, and refresh need before
an operator chooses whether to run another bounded crawl.
