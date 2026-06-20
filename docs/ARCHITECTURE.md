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
-> local indexes and graph
-> graph-enriched evidence packets
-> deterministic answer packets
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
| Graph DB | artifact root | derived navigation |
| Evidence packet | examples/exported packets | answer support, not site truth |
| Graph query context | `graph_context` in packets | derived navigation over cited posts |
| Answer packet | `aoa_4pda_answer_packet_v1` | deterministic agent handoff, not source truth |

Generated indexes and graphs help navigation. They do not replace source URLs or
policy receipts.

Current answer packets can summarize starter issue/fix/warning context and
focused Xiaomi root/recovery/file/tool/firmware relation labels from cited graph
context.

Configured storage may be the ignored repo-local `.connector-state/` scaffold
for small starter runs or an external storage root for larger materialization.

`aoa-4pda materialize fixture` is the no-network materialization route. It
starts at the sanitized live-shaped fixture, runs the same parser/normalizer,
keyword-index, graph, and answer-ready receipt path as a bounded crawl-derived
run, and writes generated state only to configured storage roots.

## Runtime Boundary

Future MCP/runtime exposure belongs in `abyss-stack` and should consume an
installed connector through configured data/artifact roots.
