# AGENTS.md

Local route card for `aoa-4pda-connector/evals/`.

## Purpose

This directory is the repo-local eval port for connector-specific evidence
pressure. It keeps 4PDA retrieval, graph, answer, focused-profile, and
receipt-driven live-run quality checks close to the connector code while
central proof authority stays in `aoa-evals`.

## Owner Lane

This local port owns:

- connector-specific suite inputs under `evals/suites/`;
- public-safe synthetic and sanitized fixture cases;
- bounded named-run quality checks over already-materialized configured
  storage receipts;
- compact local suite and report notes that describe connector pressure.

It does not own:

- central `aoa-evals` bundle creation;
- accepted proof verdicts, scoring, regression truth, or proof doctrine;
- broad live-corpus scoring;
- committed raw captures, large reports, indexes, graph databases, or exports.

## Start Here

1. `README.md`
2. `PORT.yaml`
3. `suites/README.md`
4. `reports/README.md`
5. root `AGENTS.md`
6. `docs/STARTER_PROOF.md`
7. `docs/RUNTIME_CONTRACT.md`

## Validation

From the repository root:

```bash
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root . --json
python scripts/validate_connector.py
python -m pytest -q
```

Run live eval suites only against an existing bounded configured-storage run.
Do not crawl, refresh, or materialize new live data from this route unless the
operator explicitly asks for that network step.

## Closeout

Report which local suite, intake, or report note changed, whether any network
or storage-backed live run was used, and confirm that `aoa-evals` remains the
proof owner for verdicts, scoring, regression, and proof doctrine.
