# Starter Proof

`aoa-4pda proof starter` is the fresh-clone proof route for the connector. It
proves that the local search and graph path works without touching the network
and without requiring external storage roots.

## What It Checks

The command uses `connector/fixtures/normalized/synthetic_topic.json` and builds
temporary artifacts in a system temp directory:

```text
synthetic normalized topic
-> BM25 + exact keyword index
-> graph export
-> local query
-> evidence packet checks
```

The temporary artifacts are deleted after the run.

## Run It

```bash
aoa-4pda proof starter
```

Expected posture:

- `network_touched: false`
- `external_storage_required: false`
- `internal_search_unused: true`
- query result returns the synthetic bootloop post
- evidence packet includes matched terms and score breakdowns

## Why This Exists

The real 4PDA starter crawl is deliberately explicit and bounded. CI and fresh
clones still need a reliable proof that the connector method is wired together.
The starter proof keeps that confidence local, small, and GitHub-safe.

## What It Does Not Prove

- live 4PDA availability
- public topic crawl behavior
- full-corpus quality
- vector search
- production graph extraction quality

Those belong to later bounded runs with configured external storage roots.

## Live Starter Proof

`aoa-4pda proof live-starter` verifies an already-built bounded public starter
run in external storage. The proof command itself does not touch the network;
it checks receipts and local artifacts produced by the explicit live route.

Run the live stages in order:

```bash
aoa-4pda crawl --profile starter --max-topics 3
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter --run latest
aoa-4pda build-graph --profile starter --run latest
aoa-4pda proof live-starter --run latest --query "Redmi Note 10 Pro TWRP boot.img"
```

Do not parallelize `normalize`, `build-index`, and `build-graph`; each stage
depends on the receipt written by the previous stage. A successful live starter
proof checks:

- external storage roots are configured outside the repository
- crawl policy preserved public-topic-only intake
- internal search and attachments were not used
- normalized topic count matches fetched topics
- keyword index and graph artifacts exist and are non-empty
- local query returns at least one evidence result
- only the crawl stage touched the network
