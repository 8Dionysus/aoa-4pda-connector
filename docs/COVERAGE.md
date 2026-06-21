# Coverage Audit

`reference-profile-coverage-v1` is the local coverage target for a bounded
profile such as Xiaomi 13T. It is not a claim that all of 4PDA, or even every
possible device question, has been exhausted. It is a no-network way to inspect
whether the configured profile seed plan has actually been materialized into a
receipt-backed local corpus, keyword index, deterministic vector index, graph,
quality-gate route, and explicit information-need coverage.

## Command

```bash
aoa-4pda coverage audit xiaomi-13t
```

Inspect a named receipt run:

```bash
aoa-4pda coverage audit xiaomi-13t --run <run-id>
```

Use strict mode when a workflow should fail unless the reference profile has
complete seed-window materialization and usable derived artifacts:

```bash
aoa-4pda coverage audit xiaomi-13t --run <run-id> --strict
```

The command does not touch the network, crawl, rebuild indexes, write generated
artifacts, or download attachments. It reads:

- `connector/profiles/<profile>.yaml`
- the profile `information_need_matrix` file, such as
  `connector/profiles/xiaomi_13t_information_needs.json`
- the profile seed file under `connector/seeds/`
- configured storage receipts under `CONNECTOR_ARTIFACT_ROOT/receipts`
- the named keyword index, vector index, and graph paths from those receipts
- the profile live quality-gate suite paths

## Statuses

| Status | Meaning |
| --- | --- |
| `no_run` | The profile route exists, but no crawl receipt was found for the selected run. |
| `partial` | Some evidence exists, but one or more seed, receipt, index, vector, graph, quality-gate, or information-need checks are incomplete. |
| `coverage_ready` | The expected seed pages were fetched, derived stages are receipt-linked and no-network, index, vector, and graph artifacts are present, quality-gate suites exist, and required deep information needs are covered. |
| `error` | The requested profile route is missing or unreadable. |

## What It Proves

For a profile such as Xiaomi 13T, the audit checks:

- expected seed count and expected public page windows
- fetched seed ids and page offsets from the crawl receipt
- missing seed pages and missing focus areas
- crawl policy posture: public-only, no internal search, no attachment download
- normalize/index/vector/graph receipt chain consistency
- index document and term counts
- deterministic vector document and feature counts
- graph node and edge counts
- live search, ranking-pressure, graph-query, and answer suite presence
- `aoa_4pda_information_need_matrix_v1` coverage for useful question classes,
  including whether each class has seed focus, materialized focus, and eval
  case routes
- `deep_information_needs_covered`, which stays false while any deep Xiaomi
  13T information need has only materialized pages but no eval route

This gives the loop an explicit answer to "how much of the reference profile is
actually in our local base right now?" and "which classes of questions can we
claim are covered by local eval routes?"

## What It Does Not Prove

The audit does not prove:

- full Xiaomi 13T knowledge completeness
- freshness beyond the captured receipt timestamps
- semantic answer correctness by itself
- production embedding/model recall beyond the deterministic local vector
  contract
- unseeded topic discovery
- future answer quality for information needs that are added later but not yet
  routed through eval cases
- central proof verdicts owned by `aoa-evals`

Those require broader discovery, stronger evals, freshness checks, and
answer-quality gates over the same named run.

## Typical Route

```bash
aoa-4pda profile inspect xiaomi-13t
aoa-4pda coverage audit xiaomi-13t
aoa-4pda crawl --profile xiaomi-13t
aoa-4pda normalize --run latest
aoa-4pda build-index --profile xiaomi-13t --run latest
aoa-4pda build-vector --profile xiaomi-13t --run latest
aoa-4pda build-graph --profile xiaomi-13t --run latest
aoa-4pda coverage audit xiaomi-13t --run latest
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_search_quality.json
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_ranking_pressure.json
aoa-4pda eval live-hybrid-query-quality --run latest --suite evals/suites/live_xiaomi_13t_hybrid_query_quality.json
aoa-4pda eval live-graph-query-quality --run latest --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run latest --suite evals/suites/live_xiaomi_13t_answer_quality.json
```

Only the explicit `crawl` step touches the network. The audit is safe to run
before and after the materialization sequence.

On the current local Xiaomi 13T reference run, keyword ranking-pressure is a
top-N recall gate. Relation-aware top ranking for hard root/recovery queries is
validated by the graph-query and answer suites. The information-need matrix now
reports 10/10 covered classes on run `20260621T194521Z__crawl`, including
battery/power, camera, purchase/variants, firmware source, and late-window
regression watch.
