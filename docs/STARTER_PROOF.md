# Starter Proof

`aoa-4pda proof starter` is the fresh-clone proof route for the connector. It
proves that the local search and graph path works without touching the network
and without requiring configured storage roots.

## What It Checks

The command uses `connector/fixtures/normalized/synthetic_topic.json` and builds
temporary artifacts in a system temp directory:

```text
synthetic normalized topic
-> evidence chunks
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
- evidence packet includes matched terms, score breakdowns, and chunk refs

## Why This Exists

The real 4PDA starter crawl is deliberately explicit and bounded. CI and fresh
clones still need a reliable proof that the connector method is wired together.
The starter proof keeps that confidence local, small, and GitHub-safe.

## Materialized Fixture Route

`aoa-4pda materialize fixture` writes the sanitized live-shaped fixture into
configured storage roots without touching the network:

```bash
aoa-4pda init --apply
aoa-4pda materialize fixture
aoa-4pda query-graph "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
```

This is the first durable local database route for fresh clones. It writes
normalized data, a keyword index, a graph export, and receipts to configured
storage roots while leaving generated files ignored by Git.

## Starter Search Eval

`aoa-4pda eval search-quality` is the companion retrieval-quality check for
the same fresh-clone posture. It runs tiny public-safe cases from
`evals/suites/starter_search_quality.json`, verifies expected top posts and
chunk refs, and deletes temporary indexes after the run.

`aoa-4pda eval graph-relations` is the companion graph-quality check. It uses a
sanitized live-shaped HTML fixture, verifies expected issue/fix/warning entity
nodes, post-to-entity graph edges, `fixes_issue` edges, and `warns_about`
edges, and deletes temporary graph artifacts after the run.

`aoa-4pda eval graph-relations --suite evals/suites/xiaomi_13t_graph_relations.json`
is the focused Xiaomi 13T graph-quality check. It uses a public-safe firmware
fixture and verifies expected device, model, codename, HyperOS, tool, image
file, root-action, recovery-action, and relation-edge evidence without touching
the network.

`aoa-4pda eval graph-query-packets` is the companion graph-answer check. It
uses the same sanitized live-shaped fixture, builds temporary local index and
graph artifacts, runs a graph-enriched query packet, and verifies that expected
relation context and source refs survive into the answer surface.

`aoa-4pda eval answer-packets` checks the deterministic rendered answer packet.
It verifies that issue, fix, warning, warned-target labels, answer text
fragments, and source refs survive the full local query -> graph context ->
answer renderer path.

This eval is local connector evidence. It does not create central proof
verdicts, broad regression scores, or full-corpus quality claims.

## What It Does Not Prove

- live 4PDA availability
- public topic crawl behavior
- full-corpus quality
- vector search
- production graph extraction quality

Those belong to later bounded runs with configured storage roots.

## Live Starter Proof

`aoa-4pda proof live-starter` verifies an already-built bounded public starter
run in configured storage. The proof command itself does not touch the network;
it checks receipts and local artifacts produced by the explicit live route.

Run the live stages in order:

```bash
aoa-4pda crawl --profile starter --max-topics 3
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter --run latest
aoa-4pda build-graph --profile starter --run latest
aoa-4pda proof live-starter --run latest --query "Redmi Note 10 Pro TWRP boot.img"
```

For an already-built Xiaomi 13T focused run, use the matching graph-query gate:

```bash
aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json
```

Those evals read configured crawl, normalize, index, and graph receipts and
check that cited root/recovery relation context survives into `query-graph`
packets and deterministic answer packets. They do not crawl, rebuild a corpus,
or commit generated artifacts.

Do not parallelize `normalize`, `build-index`, and `build-graph`; each stage
depends on the receipt written by the previous stage. A successful live starter
proof checks:

- configured storage roots exist and are Git-ignored when repo-local
- crawl policy preserved public-topic-only intake
- internal search and attachments were not used
- normalized page count matches fetched public topic pages
- keyword index and graph artifacts exist and are non-empty
- local query returns at least one evidence result
- only the crawl stage touched the network
