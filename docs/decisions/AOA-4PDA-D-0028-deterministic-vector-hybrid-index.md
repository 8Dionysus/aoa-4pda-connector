# AOA-4PDA-D-0028: Deterministic Vector Hybrid Index

## Status

Accepted.

## Context

The connector goal requires deep local search, not only keyword lookup. A
future production connector will likely need stronger embedding-backed semantic
retrieval, but this repository is public and must remain installable from a
fresh clone without committing heavy indexes, model blobs, or private runtime
state.

The current Xiaomi 13T reference route already proves a bounded keyword,
graph, answer, coverage, refresh, and discovery loop. Adding an immediate
external embedding dependency would make the fresh-clone route less portable
and would blur the method-in-Git boundary before the receipt chain has a stable
vector contract.

## Decision

Add a deterministic no-model vector index as the first vector contract.

The vector builder hashes token and character n-gram features from normalized
evidence chunks into a fixed-size sparse vector index. `build-vector` writes a
vector receipt and `query-hybrid` merges normalized BM25/exact keyword scores
with deterministic vector scores. When a graph receipt is available,
`query-hybrid` uses `hybrid_bm25_vector_graph_v1`: matching root/recovery
relation evidence contributes a bounded `relation_intent_saturation_v1` score
boost while graph context, source URLs, raw component scores, and the
pre-graph hybrid score remain visible. The starter hybrid eval runs entirely
from public-safe fixtures and does not download models, call embedding APIs,
crawl, or commit generated artifacts.
For the Xiaomi 13T reference profile, the live hybrid query eval reads existing
keyword, vector, and graph receipts from configured storage and checks bounded
root/recovery rank behavior without recrawling.

## Rationale

This gives the loop a real, testable keyword/vector/graph route now while
keeping the repository portable. Fresh clones, CI, and install agents can prove
that vector participation, hybrid score breakdowns, receipts, and heavy-data
boundaries work before a heavier semantic backend exists.

The graph boost is part of the hybrid scorer because the reference corpus
showed a concrete failure mode: large topic/index chunks can dominate raw BM25
while relation-rich posts answer the user's root/recovery intent. Keeping graph
only as display context made hybrid search look complete while still returning
weaker top results for Xiaomi 13T recovery queries.

The deterministic index is intentionally modest. Its job is not to claim
production semantic quality; it creates the contract that a later embedding
adapter must satisfy.

## Alternatives

- Add an embedding model dependency immediately. Rejected for this slice
  because it would introduce model download/storage questions before the public
  receipt and eval route is stable.
- Keep vector search as a roadmap-only item. Rejected because the loop goal
  needs an executable vector/hybrid surface, not only keyword and graph search.
- Build a vector store in Git. Rejected because generated vector artifacts are
  heavy mutable state and belong under configured storage roots.

## Consequences

- Coverage, refresh, readiness, and receipt-chain checks now include a vector
  stage.
- `query-hybrid` can be used as a local smoke route for bounded runs such as
  Xiaomi 13T.
- Xiaomi 13T quality gates include a receipt-driven live hybrid query suite,
  separate from graph-query and answer gates. It protects hybrid retrieval
  behavior, including graph-score participation and relation-aware root/recovery
  top ranking, not full answer correctness.
- Hybrid score breakdowns now include `graph_raw`, `graph_normalized`,
  `graph_relation_boost`, and `hybrid_without_graph` when graph receipts are
  present.
- Future embedding/vector-store adapters must remain behind explicit
  dependencies and must write compatible receipts outside Git.
- Quality claims must distinguish deterministic starter vector participation
  from stronger semantic recall that still needs future evals.

## Verification

- `aoa-4pda eval hybrid-query-packets` should pass from a fresh clone without
  network access.
- `aoa-4pda build-vector --profile xiaomi-13t --run <run-id>` should write a
  vector receipt for the same run as crawl, normalize, index, and graph.
- `aoa-4pda eval live-hybrid-query-quality --run <run-id> --suite
  evals/suites/live_xiaomi_13t_hybrid_query_quality.json` should pass against
  an operator-materialized Xiaomi 13T run with matching keyword, vector, and
  graph receipts, including recovery top-ranking cases for `recovery.img
  fastboot` and OrangeFox/TWRP.
- `aoa-4pda ready --run <run-id> --strict` should require the vector receipt
  once this decision is implemented.
