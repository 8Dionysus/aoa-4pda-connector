# Runtime Contract

`aoa-4pda-connector` is a source connector package. Runtime services and MCP
adapters belong in `abyss-stack`, but they should be able to consume this
repository through stable command and storage contracts without moving corpora,
indexes, graphs, or receipts into Git.

## Storage Inputs

Runtime consumers configure the same roots as operators:

```bash
export CONNECTOR_DATA_ROOT=/path/to/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/aoa-4pda-connector/artifacts
```

All generated state remains under those roots or under the ignored
`.connector-state/` fallback for small local runs.

## Stable CLI Surfaces

The runtime access plane should call `aoa-4pda` commands and read JSON from
stdout:

- `aoa-4pda doctor`
- `aoa-4pda storage status`
- `aoa-4pda ready`
- `aoa-4pda query "<query>" --run <run-id>`
- `aoa-4pda query-graph "<query>" --run <run-id>`
- `aoa-4pda answer "<query>" --run <run-id>`
- `aoa-4pda eval live-search-quality --run <run-id> --suite <suite>`
- `aoa-4pda eval live-graph-query-quality --run <run-id> --suite <suite>`
- `aoa-4pda eval live-answer-quality --run <run-id> --suite <suite>`

These commands must not use 4PDA internal search, private routes, attachment
downloads, or generated Git artifacts.

## JSON Outputs

Runtime consumers should route by the `schema` field and preserve source
evidence:

- `aoa_4pda_doctor_v1`
- `aoa_4pda_storage_status_v1`
- `aoa_4pda_connector_ready_audit_v1`
- `aoa_4pda_evidence_packet_v1`
- `aoa_4pda_answer_packet_v1`
- `aoa_4pda_live_search_eval_report_v1`
- `aoa_4pda_live_graph_query_eval_report_v1`
- `aoa_4pda_live_answer_eval_report_v1`

Evidence and answer packets carry source URLs, topic/post ids when known,
evidence refs, query diagnostics, score details, and graph context when
requested. Runtime layers may summarize or display them, but source URLs and
receipts remain the authority.

## Stop Line

`abyss-stack` may wrap these commands or call an installed package API later,
but this repository remains the source-specific connector authority. It does
not own long-running runtime deployment, central proof verdicts, full-corpus
quality claims, or cross-connector orchestration.
