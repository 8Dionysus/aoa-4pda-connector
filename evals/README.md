# Local Eval Port

`evals/` is the connector-local eval pressure port for
`aoa-4pda-connector`.

It keeps public-safe suites, bounded fixture checks, focused profile quality
checks, and compact local notes close to the connector implementation. Central
proof doctrine, accepted verdicts, scoring authority, regression truth, and
central bundle adoption stay in `aoa-evals`.

## Surfaces

| Surface | Role |
| --- | --- |
| `PORT.yaml` | Declares local port ownership and central boundary |
| `suites/` | Connector-native JSON suites plus local suite notes |
| `intake/` | Future `eval_need_v1` pressure packets before suite design |
| `reports/` | Small curated local report notes |

## Local Suites

The connector-native JSON suites are runner inputs for local CLI checks such
as:

```bash
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
aoa-4pda eval live-search-quality --run <run-id>
aoa-4pda eval live-graph-query-quality --run <run-id>
aoa-4pda eval live-answer-quality --run <run-id>
```

No-network suites use synthetic or sanitized fixtures. Live suites read an
already-materialized bounded run from configured storage and must not crawl or
commit generated artifacts.

## Boundary

This port may preserve connector-local cases, suite descriptions, and compact
reports. It must not create central eval bundles, compute accepted proof
verdicts, define scoring doctrine, mark regression truth, publish receipts, or
promote generated/live evidence into central proof.
