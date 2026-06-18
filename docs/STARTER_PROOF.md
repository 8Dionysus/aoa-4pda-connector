# Starter Proof

`aoa-4pda proof starter` is the fresh-clone proof route for the connector. It
proves that the local search and graph path works without touching the network
and without requiring external storage roots.

## What It Checks

The command uses `connector/fixtures/normalized/synthetic_topic.json` and builds
temporary artifacts in a system temp directory:

```text
synthetic normalized topic
-> keyword index
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
