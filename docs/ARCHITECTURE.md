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
-> evidence packets
```

## Parser Posture

The parser is fixture-backed, not raw-corpus-backed. Tiny sanitized HTML
fixtures may mimic live 4PDA structure, but raw live pages stay in external
storage.

Current parser coverage includes:

- old table-based public topic posts with `data-post` and `post-main-*` ids
- post author labels from the public post header
- raw public post date labels from the public post header
- quote, edit-note, and signature text removal before indexing

## Source and Derived Layers

| Layer | Example | Authority |
| --- | --- | --- |
| Source policy | `connector/SOURCE_POLICY.md` | repository |
| Raw public snapshot | external `CONNECTOR_DATA_ROOT` | source URL + receipt |
| Normalized record | external data root | parser output with source refs |
| Search index | external cache root | derived navigation |
| Graph DB | external artifact root | derived navigation |
| Evidence packet | examples/exported packets | answer support, not site truth |

Generated indexes and graphs help navigation. They do not replace source URLs or
policy receipts.

## Runtime Boundary

Future MCP/runtime exposure belongs in `abyss-stack` and should consume an
installed connector through configured data/artifact roots.
