# AOA-4PDA-D-0006: Local Starter Search Eval Pack

- Status: accepted
- Date: 2026-06-19

## Context

The connector now has BM25/exact scoring and chunk-level evidence, but the
offline starter proof mostly proves that the pipeline is wired. It does not
separately protect retrieval expectations such as "this query should surface
this post/chunk first" or "exact firmware strings should stay matched."

The repository already has an `evals/` surface, while central proof doctrine and
accepted eval verdicts belong to `aoa-evals`.

## Decision

Activate `evals/` as a repo-local eval port and add a starter search quality
suite:

```bash
aoa-4pda eval search-quality
```

The command reads `evals/suites/starter_search_quality.json`, builds a
temporary chunk index from public-safe synthetic normalized fixtures, checks
expected top posts/chunks, source refs, exact terms, query report unit, and the
internal-search boundary, then deletes the temporary artifacts.

The suite and runner are connector-owned. They are local evidence and CI gates,
not central proof verdicts.

## Consequences

- Search changes now have a small quality gate beyond "the pipeline runs."
- Fresh clones can run the eval without external storage or network access.
- CI can catch accidental regressions in top evidence selection and chunk refs.
- The suite is intentionally tiny; broader live-corpus or longitudinal scoring
  remains future work.

## Boundaries

- `aoa-4pda-connector` owns local cases, runner code, and compact reports.
- `aoa-evals` remains the proof owner for doctrine, accepted verdicts, scoring
  authority, and regression truth.
- No raw live captures, generated indexes, graph exports, or repeated reports
  are committed.
- No internal 4PDA search or attachment route is used.

## Source Surfaces

- `evals/PORT.yaml`
- `evals/suites/starter_search_quality.json`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `.github/workflows/validate.yml`
- `docs/QUERY_MODEL.md`
