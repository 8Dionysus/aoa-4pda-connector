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

- fresh-clone install route is documented and exposes the `aoa-4pda`
  entrypoint
- `doctor`, `storage status`, fixture materialization, starter proof, and
  starter eval surfaces exist
- Xiaomi 13T focused-device profile has profile, seed, suite, and receipt
  evidence
- a second representative profile is prepared or explicitly deferred
- crawl, normalize, index, and graph receipts form a reproducible run chain
- search quality covers exact/BM25 technical retrieval and ranking-pressure
  cases
- graph quality covers issue/fix/warning/root/recovery/tool/file/firmware
  relations with source refs and confidence
- answer packets are cited, deterministic, and freshness-aware
- heavy generated data remains ignored and outside tracked Git surfaces
- runtime/API contract is documented for future `abyss-stack` consumption
- validator, pytest, evals, and GitHub CI remain wired into the repo route

## Interpretation

`not_ready` is expected while the loop is still active. A `partial` criterion
usually means a route exists but lacks stronger evidence. A `missing` criterion
means the repository does not yet expose the required surface.

The readiness audit is local connector evidence only. It does not create
central eval verdicts, accepted proof claims, or broad 4PDA quality scores;
those stay with the owning AoA proof surfaces.
