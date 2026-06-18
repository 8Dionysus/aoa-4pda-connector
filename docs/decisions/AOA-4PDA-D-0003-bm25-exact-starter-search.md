# AOA-4PDA-D-0003 BM25 Exact Starter Search

Status: accepted
Date: 2026-06-18

## Decision

Upgrade the starter local search path from simple term-count scoring to
`bm25_exact_v1`: BM25 over the local inverted index, plus exact-term and
exact-phrase boosts for technical query terms.

## Rationale

4PDA searches often depend on exact strings: device models, firmware versions,
build IDs, error words, and files such as `boot.img`. Plain term counts are too
weak for this domain and make it hard to explain why a post was returned.

BM25 + exact boosts gives a better first retrieval layer while keeping the repo
small, dependency-free, offline-testable, and compatible with the existing
external-storage boundary.

## Consequences

- Evidence packets can include query reports, matched terms, matched exact
  terms, matched phrases, score breakdowns, and focused snippets.
- The starter proof now exercises a more realistic local retrieval path.
- This is still not semantic search, full entity extraction, or vector search.
  Those remain later layers.

## Boundaries

- Do not use 4PDA internal search as a source API.
- Do not introduce vector dependencies in this starter slice.
- Do not write generated indexes into Git.
- Keep source URLs and post IDs as the evidence anchor.

## Source Surfaces

- `src/aoa_4pda_connector/index/__init__.py`
- `src/aoa_4pda_connector/query/__init__.py`
- `tests/unit/test_parse_and_index.py`
- `docs/QUERY_MODEL.md`
- `docs/STARTER_PROOF.md`
