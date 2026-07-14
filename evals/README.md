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

The connector-native JSON suites are inputs to the local evaluation action
families documented in `suites/README.md`. The CLI evaluation parser owns exact
syntax, the fresh-copy verifier owns the starter execution sequence, and CI
owns the required automated route.

No-network suites use synthetic or sanitized fixtures. Live suites read an
already-materialized bounded run from configured storage and must not crawl or
commit generated artifacts.

## Boundary

This port may preserve connector-local cases, suite descriptions, and compact
reports. It must not create central eval bundles, compute accepted proof
verdicts, define scoring doctrine, mark regression truth, publish receipts, or
promote generated/live evidence into central proof.
