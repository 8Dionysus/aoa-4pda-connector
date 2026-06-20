# AOA-4PDA-D-0013: Technical Token Normalization

- Status: accepted
- Date: 2026-06-20

## Context

4PDA retrieval depends on exact technical strings, but those strings often
appear in several equivalent forms. Users may query `boot img` while posts say
`boot.img`, write `V 14 0 7 0` while posts say `V14.0.7.0`, or use codenames
such as `sweet` while topic titles use public device names such as
`Redmi Note 10 Pro`.

The connector already has BM25/exact scoring and live starter evals. The next
quality step should improve lexical matching before adding vector search.

## Decision

Add a small dependency-free technical alias layer to local tokenization:

- split file-image forms such as `boot img` and `recovery img` normalize to
  `boot.img` and `recovery.img`
- split firmware versions such as `V 14 0 7 0` normalize to `v14.0.7.0`
- separated model strings such as `SM G991B` normalize to `sm-g991b`
- starter device aliases map `Redmi Note 10 Pro` to `sweet` and
  `Redmi Note 10` to `mojito`

The alias tokens are appended to the local index/query token stream and exposed
in query reports as `technical_terms`.

## Consequences

- Exact matching improves for common 4PDA technical spelling variants without a
  vector dependency.
- Eval suites can assert that specific aliases were derived, not only that a
  top result happened to pass.
- Existing source URLs, post IDs, chunks, and BM25/exact score reports remain
  the evidence anchors.
- The alias map is intentionally starter-grade and should grow through eval
  cases rather than broad unreviewed dictionaries.

## Boundaries

- Do not use 4PDA internal search as a fallback for lexical gaps.
- Do not add an ML/vector dependency in this slice.
- Do not treat aliases as source truth; they are retrieval aids only.
- Do not commit generated indexes or live corpus artifacts after rebuilding
  storage indexes with the new tokenizer.

## Source Surfaces

- `src/aoa_4pda_connector/index/__init__.py`
- `src/aoa_4pda_connector/query/__init__.py`
- `evals/suites/starter_search_quality.json`
- `evals/suites/live_starter_search_quality.json`
- `tests/unit/test_parse_and_index.py`
- `tests/unit/test_search_eval.py`
