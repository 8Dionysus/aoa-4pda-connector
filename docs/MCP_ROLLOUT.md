# Portable MCP Rollout

`aoa-4pda-connector` owns the portable source-specific connector contract.
It does not own the OS Abyss runtime MCP implementation. The expected MCP
service name is `aoa-4pda-connector-mcp`.

## Owner Split

This repository owns:

- the `aoa-4pda` CLI and JSON packet contracts;
- 4PDA source policy, parser, normalizer, index, graph, query, answer, eval,
  readiness, and storage contracts;
- small fixtures, seed plans, schemas, validators, and portable rollout
  guidance.

`abyss-stack` owns:

- the OS Abyss MCP runtime service package;
- deployment, lifecycle, stdio registration, and stack validation;
- runtime environment binding to local storage and source checkouts.

The MCP layer is an access plane over local connector outputs. It must not
become a second source of 4PDA truth and must not move corpora, indexes,
graphs, vector stores, receipts, or caches into Git.

## Required Roots

Runtime consumers configure the same storage roots as the connector CLI:

```bash
export CONNECTOR_DATA_ROOT=/path/to/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/aoa-4pda-connector/artifacts
```

For grouped connector storage, consumers may also set:

```bash
export CONNECTOR_FAMILY_ROOT=/path/to/connector-databases
export CONNECTOR_INSTANCE_ROOT="$CONNECTOR_FAMILY_ROOT/aoa-4pda-connector"
```

Fresh clones may use the ignored `.connector-state/` fallback for fixture and
small smoke runs. Larger crawls and reference runs should live in external
storage.

## Wrapped CLI Contract

The first MCP slice is read-only and local-only. It may wrap these commands:

- `aoa-4pda doctor`
- `aoa-4pda storage status`
- `aoa-4pda ready`
- `aoa-4pda query "<query>" --run <run-id>`
- `aoa-4pda query-graph "<query>" --run <run-id>`
- `aoa-4pda query-hybrid "<query>" --run <run-id>`
- `aoa-4pda answer "<query>" --run <run-id>`

The MCP service must not expose crawl, refresh-build, materialize, reindex,
write, seed-edit, or approval tools in the first slice. It must not touch the
network while answering and must not call 4PDA internal search, private/account
routes, QMS, post, attach, download, or login surfaces.

## Expected MCP Surface

Portable adapters should expose at least:

- `status`: connector CLI availability, storage roots, doctor/storage/ready
  evidence, and selected run information when available;
- `answer`: input `query`, optional `run`, and `limit`; output a compact
  packet that preserves the source answer packet fields;
- `source_route`: connector repo path, expected environment variables,
  owner-boundary notes, and no-network/read-only stop lines.

The OS Abyss implementation belongs at:

```text
mcp/services/aoa-4pda-connector-mcp/
```

inside `abyss-stack`.

## Answer Packet Preservation

Adapters must route by `schema` and preserve these source fields from
`aoa_4pda_answer_packet_v1`:

- `agent_answer`
- `evidence_chain`
- `nuance_report`
- `answer_report`
- `answers`
- `query_report`
- `network_touched`

`network_touched` must remain `false` for MCP answer calls. A packet with
`agent_answer.status=insufficient_evidence` is a successful local result that
reports missing evidence; it is not permission to crawl.

Runtime layers may display or synthesize from `agent_answer`, but source URLs,
post ids, topic ids, capture receipts, evidence refs, freshness context, and
limitations remain the authority.

## Standalone Route

A standalone agent outside OS Abyss should:

1. clone or fork this repository;
2. create a virtual environment and install the package;
3. configure `CONNECTOR_DATA_ROOT`, `CONNECTOR_CACHE_ROOT`, and
   `CONNECTOR_ARTIFACT_ROOT`, or intentionally use `.connector-state/` for a
   small starter run;
4. run `python scripts/validate_connector.py` and `python -m pytest -q`;
5. run `aoa-4pda doctor`, `aoa-4pda storage status`, and `aoa-4pda ready`;
6. point an MCP adapter named `aoa-4pda-connector-mcp` at the installed
   `aoa-4pda` CLI and configured storage roots;
7. smoke `aoa-4pda answer "Xiaomi 13T recovery.img fastboot TWRP" --run <run-id>`.

The standalone adapter may live in another runtime repository or local service
tree, but it should keep this repository as the connector source contract.

## OS Abyss Route

In OS Abyss, the runtime MCP service is stack-owned:

```text
/home/dionysus/src/abyss-stack/mcp/services/aoa-4pda-connector-mcp/
```

That package should wrap the local connector CLI and may use an environment
variable such as `AOA_4PDA_CONNECTOR_REPO` to locate this checkout during local
development. It should keep stdio/read-only exposure unless a later decision
explicitly widens the surface.

## Verification

Connector-side verification:

```bash
python scripts/validate_connector.py
python -m pytest -q
PYTHONPATH=src python -m aoa_4pda_connector.cli ready --run 20260621T194521Z__crawl --strict
PYTHONPATH=src python -m aoa_4pda_connector.cli answer "Xiaomi 13T recovery.img fastboot TWRP" --run 20260621T194521Z__crawl --limit 5
```

The named run check is optional for fresh clones and expected only when that
local reference run is present in configured storage. All commands above are
no-network checks.
