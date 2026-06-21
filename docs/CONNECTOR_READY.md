# Connector Ready

`connector-ready-v1` is the repository-local maturity target for the long
4PDA connector loop. It is not a claim that all of 4PDA has been crawled. It
means the public method, storage route, bounded corpus pipeline, local
search/graph/answer path, and quality gates are reproducible enough for an
agent or operator to install and extend the connector safely.

## Audit Command

Run the local readiness audit:

```bash
aoa-4pda ready
```

The command does not touch the network, crawl, rebuild artifacts, or write
generated data. It reads repository surfaces and configured storage receipts,
then reports each criterion as `achieved`, `partial`, or `missing`.

Use strict mode when a workflow must fail until the maturity target is fully
met:

```bash
aoa-4pda ready --strict
```

## Criteria

The audit maps the active loop goal into concrete repository-local checks:

- fresh-clone install route is documented, exposes the `aoa-4pda` entrypoint,
  and has a one-command fresh-copy verifier
- `doctor`, `storage status`, fixture materialization, starter proof, and
  starter eval surfaces exist
- Xiaomi 13T focused-device profile has profile, seed, suite, and receipt
  evidence
- `reference-profile-discovery-v1` audit exists for review-ready public
  topic/window candidates visible in stored snapshots, with already covered
  seed-plan windows excluded from candidate gaps
- reference profile seed-review state is clean: Xiaomi 13T discovery candidates
  are reviewed through `reference-profile-seed-review-v1`, and accepted
  candidates are represented in the seed plan before seed maturity is claimed
- `reference-profile-coverage-v1` audit exists for profile seed-window,
  receipt, index, vector, graph, and quality-gate gap reporting
- reference profile coverage state is current: the active Xiaomi 13T seed plan
  is materialized by crawl, normalize, index, vector, and graph receipts
- `reference_profile_information_need_coverage` distinguishes materialized
  pages from covered classes of useful Xiaomi 13T questions
- `reference-profile-refresh-v1` audit exists for receipt age, derived artifact
  freshness, and bounded refresh planning
- a second representative focused-device profile has bounded seed windows and
  at least a local live-search quality gate
- crawl, normalize, index, vector, and graph receipts form a reproducible run
  chain
- search quality covers exact/BM25 technical retrieval, deterministic hybrid
  retrieval, and ranking-pressure cases
- graph quality covers issue/fix/warning/root/recovery/tool/file/firmware
  relations with source refs and confidence
- answer packets are cited, deterministic, freshness-aware, gap-aware, and
  chain-aware: weak evidence returns an explicit insufficient-evidence report
  instead of a fabricated snippet answer, while grounded answers carry
  `evidence_chain` and `nuance_report`
- heavy generated data remains ignored and outside tracked Git surfaces
- runtime/API contract is documented for future `abyss-stack` consumption
- validator, pytest, evals, and GitHub CI remain wired into the repo route
- CI runs the no-network coverage audit so the command stays fresh-clone safe
- CI runs the no-network refresh audit so the command stays fresh-clone safe
- CI runs the no-network discovery audit so the command stays fresh-clone safe
- CI runs the fresh-copy agent install verifier with duplicated pytest skipped
  because the test suite is already a separate required step

## Interpretation

`not_ready` is expected while the loop is still active. A `partial` criterion
usually means a route exists but lacks stronger evidence. A `missing` criterion
means the repository does not yet expose the required surface.

The readiness audit is local connector evidence only. It does not create
central eval verdicts, accepted proof claims, or broad 4PDA quality scores;
those stay with the owning AoA proof surfaces.

A fresh clone without materialized configured storage can still report partial
reference-profile criteria. That is expected: the repository commits the
method, contracts, seeds, evals, and validators, while raw snapshots, indexes,
vectors, graphs, and receipts are generated local state.

The current local reference run `20260621T194521Z__crawl` demonstrates the
materialized base target: 23/23 Xiaomi 13T seeds, 70/70 public pages, 1,448 normalized
posts, 1,559 indexed chunks/posts, 1,559 deterministic vector chunk docs,
26,701 vector features, 1,508 graph nodes, and 2,855 graph edges. Against that
run, search, ranking-pressure, hybrid smoke, graph-query, and answer gates pass
without additional network access for the current information-need matrix.
`reference_profile_information_need_coverage` reports 10/10 covered classes for
that run, including battery/power, camera, purchase/variants, firmware source,
and late-window regression watch.

If `reference_profile_seed_review_state` is `partial`, the connector may be
operational but the active Xiaomi 13T reference loop is not done. Run
`aoa-4pda discovery review xiaomi-13t`; if it reports
`reviewed_pending_seed_update`, update seeds only for accepted public scope,
then run a bounded refresh and quality gates again.

If `reference_profile_coverage_state` is `partial`, the seed plan has moved
ahead of the stored run. Run the bounded Xiaomi 13T crawl only after operator
confirmation, then rebuild normalized records, index, vector, graph, and live
quality gates against the same run.

If `reference_profile_information_need_coverage` is `partial`, inspect
`information_needs.summary.deep_profile_missing_need_ids` from
`aoa-4pda coverage audit xiaomi-13t --run <run-id>`. Add focused search,
hybrid, graph, or answer eval cases for those classes before calling the
reference profile deeply covered.
