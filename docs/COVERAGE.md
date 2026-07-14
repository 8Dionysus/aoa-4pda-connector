# Coverage Audit

`reference-profile-coverage-v1` is the local coverage target for a bounded
profile such as Xiaomi 13T. It is not a claim that all of 4PDA, or even every
possible device question, has been exhausted. It is a no-network way to inspect
whether the configured profile seed plan has actually been materialized into a
receipt-backed local corpus, keyword index, deterministic vector index, graph,
quality-gate route, and explicit information-need coverage.

## Executable Surface

The CLI coverage action owns profile, named-run, and strict-mode syntax. It
does not touch the network, crawl, rebuild indexes, write generated
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
- live search, ranking-pressure, graph-query, answer, claim-graph, and
  claim-answer suite presence
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

## Materialization Relationship

Coverage may be inspected before materialization to expose gaps and after a
single ordered crawl, normalize, keyword-index, vector-index, and graph chain
to confirm what is present. Focused quality actions consume that same named
run. Only the separately authorized crawl touches the network; the coverage
action itself remains no-network. Exact execution belongs to the CLI,
`AGENTS.md`, and CI.

On the current local Xiaomi 13T reference run, keyword ranking-pressure is a
top-N recall gate. Relation-aware top ranking for hard root/recovery queries is
validated by the graph-query and answer suites. Conflict/supersession semantics
are now routed through `claim_graph_suite` and `claim_answer_suite`, so
`conflicting_superseded_instructions` is deep-required instead of a mapped
non-required gap. The audit reports claim counters from graph artifacts when a
run has been rebuilt with the claim extractor.
