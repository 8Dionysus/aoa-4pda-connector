# Refresh Audit

`reference-profile-refresh-v1` is the no-network freshness and refresh-planning
target for a bounded profile run. It answers a different question than coverage:
coverage says whether the expected seed windows are present, while refresh says
whether the stored receipt chain is fresh enough and whether derived artifacts
were rebuilt after the crawl.

## Command

```bash
aoa-4pda refresh audit xiaomi-13t
```

Inspect a named run:

```bash
aoa-4pda refresh audit xiaomi-13t --run <run-id>
```

Set a tighter age limit:

```bash
aoa-4pda refresh audit xiaomi-13t --run <run-id> --max-age-hours 24
```

Use strict mode before a workflow that requires a fresh, coverage-ready
reference profile:

```bash
aoa-4pda refresh audit xiaomi-13t --run <run-id> --strict
```

The audit does not touch the network, crawl, rebuild indexes, write generated
artifacts, or download attachments. It reads configured storage receipts,
reuses the coverage audit, and emits a bounded refresh plan.

## Statuses

| Status | Meaning |
| --- | --- |
| `missing_run` | No crawl receipt exists for the selected run. |
| `needs_refresh` | Receipts exist but the crawl is stale, incomplete, policy-invalid, missing derived timestamps, or not coverage-ready. |
| `fresh` | Crawl, normalize, index, vector, graph, policy, age, and coverage checks all pass for the selected run. |

`strict_ready` is true only when the status is `fresh` and the coverage audit
reports `coverage_ready`.

## Checks

The audit checks:

- crawl receipt age against `--max-age-hours`
- crawl errors and public-only policy posture
- normalize/index/vector/graph receipts for the same selected run
- derived stage timestamps and ordering after the crawl
- no-network posture for derived stages
- `coverage_ready` from `aoa-4pda coverage audit`

## Refresh Plan

When the selected run is missing or stale, the report includes the bounded
operator-confirmed sequence:

```bash
aoa-4pda crawl --profile xiaomi-13t
aoa-4pda normalize --run latest
aoa-4pda build-index --profile xiaomi-13t --run latest
aoa-4pda build-vector --profile xiaomi-13t --run latest
aoa-4pda build-graph --profile xiaomi-13t --run latest
aoa-4pda coverage audit xiaomi-13t --run latest
aoa-4pda refresh audit xiaomi-13t --run latest
```

Only the explicit crawl step touches the network. The audit itself is safe to
run in CI, during install, and before live evals.

## Limits

The audit does not discover new topics, prove semantic answer quality, or
decide central proof verdicts. It makes freshness and refresh need visible so
the next crawl can be bounded and intentional.
