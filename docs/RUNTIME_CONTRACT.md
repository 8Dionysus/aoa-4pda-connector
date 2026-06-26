# Runtime Contract

`aoa-4pda-connector` is a source connector package. Runtime services and MCP
adapters belong in `abyss-stack`, but they should be able to consume this
repository through stable command and storage contracts without moving corpora,
indexes, graphs, or receipts into Git.

`docs/MCP_ROLLOUT.md` is the portable rollout contract for adapters named
`aoa-4pda-connector-mcp`. It describes the standalone route for external
agents and the OS Abyss route where the runtime package lives under
`abyss-stack/mcp/services/`.

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
- `aoa-4pda discovery audit <profile> --run <run-id>`
- `aoa-4pda discovery review <profile> --run <run-id>`
- `aoa-4pda coverage audit <profile> --run <run-id>`
- `aoa-4pda refresh audit <profile> --run <run-id>`
- `aoa-4pda query "<query>" --run <run-id>`
- `aoa-4pda query-graph "<query>" --run <run-id>`
- `aoa-4pda query-hybrid "<query>" --run <run-id>`
- `aoa-4pda answer "<query>" --run <run-id>`
- `aoa-4pda eval live-search-quality --run <run-id> --suite <suite>`
- `aoa-4pda eval live-hybrid-query-quality --run <run-id> --suite <suite>`
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
- `aoa_4pda_discovery_audit_v1`
- `aoa_4pda_discovery_review_audit_v1`
- `aoa_4pda_coverage_audit_v1`
- `aoa_4pda_refresh_audit_v1`
- `aoa_4pda_evidence_packet_v1`
- `aoa_4pda_answer_packet_v1`
- `aoa_4pda_vector_manifest_v1`
- `aoa_4pda_vector_index_v1`
- `aoa_4pda_hybrid_query_eval_report_v1`
- `aoa_4pda_live_search_eval_report_v1`
- `aoa_4pda_live_hybrid_query_eval_report_v1`
- `aoa_4pda_live_graph_query_eval_report_v1`
- `aoa_4pda_live_answer_eval_report_v1`
- `aoa_4pda_agent_install_route_verify_v1`

Evidence and answer packets carry source URLs, topic/post ids when known,
observed post timestamps, local capture timestamps when available, evidence
refs, query diagnostics, score details, vector/hybrid diagnostics when
requested, graph context when requested, answer freshness notes, and answer
grounding status. Answer packets also expose `agent_answer`, `evidence_chain`,
and `nuance_report`; runtime layers should treat `agent_answer` as a
deterministic cited brief and keep `evidence_chain` available for inspection or
richer synthesis. Claim-aware packets also expose `conflict_report`,
`freshness_report`, `applicability_report`, `warning_report`, and `claim_ids`
so agents can distinguish primary, supporting, conflicting, superseding, and
contextual evidence before making a stronger claim. `answers` is a filtered
and same-post-deduplicated answer list, not a raw top-N dump.
`answer_report.answer_status=insufficient_evidence` with empty `answers` and
`evidence_chain` arrays plus `agent_answer.status=insufficient_evidence` is a
successful local answer packet that says the configured database does not yet
support a reliable answer; it is not a crawl request or runtime failure.
Runtime layers may summarize or display packets, but source URLs and receipts
remain the authority.

MCP adapters must preserve `agent_answer`, `evidence_chain`, `nuance_report`,
`answer_report`, `conflict_report`, `freshness_report`,
`applicability_report`, `warning_report`, `claim_ids`,
`network_touched=false`, and `read_only=true` when wrapping `aoa-4pda answer`.

`query-hybrid` requires keyword, vector, and graph receipts for the selected
run. The starter vector route is deterministic and model-free; external
embedding stores can be introduced later only behind the same receipt and
heavy-data boundary.

`scripts/verify_agent_install_route.py` emits
`aoa_4pda_agent_install_route_verify_v1`. It is an installation verifier, not a
runtime query API: consumers should treat it as bootstrap evidence that the
package installs, no-network starter commands run, temporary external storage
receives generated artifacts, and the copied repo-local scaffold stays clean.

Discovery audit packets carry candidate `anchor_texts`, `evidence_contexts`,
`target_hits`, `source_target_hits`, `review_priority`, and
`covered_seed_window_link_count`. Runtime layers may use those fields to route
seed-review work, but they must not treat candidates as approved crawl scope.
Discovery review packets compare candidates with
`connector/seeds/reviews/xiaomi_13t_discovery_review.json` and expose
`accepted_missing_from_seed`, `unreviewed_candidates`, and stale decisions.
Accepted candidates are seed-update proposals, not runtime crawl permission.

## Stop Line

`abyss-stack` may wrap these commands or call an installed package API later,
but this repository remains the source-specific connector authority. It does
not own long-running runtime deployment, central proof verdicts, full-corpus
quality claims, or cross-connector orchestration.
