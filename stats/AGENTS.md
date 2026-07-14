# AGENTS.md

Route card for owner-local statistical questions in `aoa-4pda-connector`.
Read the root `AGENTS.md` first.

## Applies To

Everything under `stats/`.

## Role

This directory owns bounded statistics over connector-authored 4PDA route
objects. Shared measurement grammar and cross-owner composition remain owned
by `aoa-stats`; eval verdicts remain owned by `aoa-evals`.

## Read Before Editing

1. Root `AGENTS.md`, `CHARTER.md`, `BOUNDARIES.md`, and `ROADMAP.md`.
2. `connector/profiles/xiaomi-13t.yaml` and its information-need matrix.
3. The profile-mapped suites under `evals/suites/` and `evals/AGENTS.md`.
4. `docs/decisions/AOA-4PDA-D-0030-information-need-coverage.md`.
5. `stats/README.md`, `stats/port.manifest.json`, and the central contracts
   under `aoa-stats/stats/`.

## Boundaries

- The population is the complete non-empty set of unique deep-required needs
  in the supported Xiaomi 13T information-need matrix.
- A need enters the numerator only when it declares at least one eval case and
  every declared case id resolves in the suite mapped by the current profile.
- A valid population with no declared routes is an observed zero.
- Missing, malformed, empty, duplicate, unsupported, or profile-mismatched
  input is unknown, not zero.
- The reference packet is weaker than the profile, matrix, suites, executable
  audits, eval results, and source evidence.
- Route coverage does not prove that cases ran or passed, that a corpus is
  materialized or fresh, that answers are correct, or that the connector is
  ready.

## Validation

Inspect the matrix, profile suite map, referenced case ids, and packet first.
The port validator requires a compatible `aoa-stats` checkout through
`AOA_STATS_ROOT`, `.deps/aoa-stats`, or the workspace sibling route; CI supplies
its pinned checkout explicitly. Then run:

```bash
python scripts/validate_local_stats_port.py
python -m pytest -q tests/unit/test_local_stats_port.py
```

Use the root route for repository-wide validation.

## Closeout

Report the exact need population, resolved-route numerator, manual positive and
negative cases, packet posture, central validation, and repository validation.
