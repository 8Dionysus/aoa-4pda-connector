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

