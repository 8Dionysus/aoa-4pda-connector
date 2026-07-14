# AOA-4PDA-D-0012: Live Starter Search Quality Eval

- Status: accepted
- Date: 2026-06-19

## Context

The connector can now crawl a bounded starter set, normalize multiple public
topic pages, build a keyword index, and prove that the live starter route is
wired. That proof is necessary, but it mostly checks artifact presence and
policy boundaries. It does not separately protect whether live starter queries
continue to surface the expected technical posts first.

The repository must still remain GitHub-publishable method and code. Raw live
captures, indexes, graph exports, and repeated reports belong in configured
storage roots, not Git.

## Decision

Add a local live search-quality eval whose execution is owned by the CLI. The
action reads `evals/suites/live_starter_search_quality.json`, loads the
crawl, normalize, and index receipts for the named run, then queries the
existing keyword index. It checks expected top evidence, source URLs, exact
terms, specific-term reporting, and the internal-search boundary.

The suite is connector-owned local evidence. It is not a central `aoa-evals`
verdict and it does not create or commit live corpus artifacts.

## Consequences

- Live starter ranking now has a quality gate beyond "the pipeline runs."
- Agents can rerun the gate after ranking changes without crawling again.
- Fresh clones can still run the no-network starter evals; this live eval
  requires an operator-materialized run.
- Future broader retrieval eval expansion can add more cases and run profiles
  without changing the public corpus boundary.

## Boundaries

- `aoa-4pda-connector` owns the local suite, runner, CLI command, and compact
  report shape.
- `aoa-evals` remains the proof owner for doctrine, accepted verdicts, scoring
  authority, and regression truth.
- The command must not crawl, use 4PDA internal search, download attachments,
  rebuild broad corpora, or commit generated data.
- Missing run receipts should fail as setup errors, not silently fall back to
  synthetic fixtures.

## Source Surfaces

- `evals/PORT.yaml`
- `evals/suites/live_starter_search_quality.json`
- `src/aoa_4pda_connector/evaluation/__init__.py`
- `src/aoa_4pda_connector/cli.py`
- `docs/QUERY_MODEL.md`
- `docs/OPERATIONS.md`
