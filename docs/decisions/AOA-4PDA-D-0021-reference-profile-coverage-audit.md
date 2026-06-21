# AOA-4PDA-D-0021: Reference Profile Coverage Audit

## Status

Accepted.

## Context

`connector-ready-v1` proved that the repository can expose a reproducible
public skeleton with storage routes, receipts, local search, graph context,
answer packets, and quality gates. That is still weaker than the larger loop
goal: a connector that can tell an operator whether a focused profile has
enough locally indexed knowledge to be useful for deep device retrieval.

Xiaomi 13T is the first acceptance profile, but claiming "everything about the
device is available from our base" would be dishonest without a coverage
surface. Passing answer or search evals can prove selected questions, not seed
window materialization, missing focus areas, or whether a local run actually
contains the expected profile corpus.

## Decision

Add a no-network `aoa-4pda coverage audit <profile>` command and document it as
the `reference-profile-coverage-v1` target.

The audit compares the profile and seed plan with configured storage receipts,
derived index and graph artifacts, and live quality-gate suite surfaces. It
reports `no_run`, `partial`, `coverage_ready`, or `error`, plus seed-page gaps,
missing focus areas, receipt-chain status, index/graph counts, and next
actions.

## Rationale

This makes coverage a first-class loop surface rather than an implication of
the latest crawl or eval. It also gives future agents a safe command to run
before asking for more crawl scope: inspect the current local base, see what is
missing, then expand seed windows or evals deliberately.

The command remains repo-local and receipt-driven. It does not crawl, rebuild,
download attachments, use 4PDA internal search, or create central proof
verdicts.

## Alternatives

- Treat `aoa-4pda ready` as the coverage audit. Rejected because readiness is a
  repo maturity target, while profile coverage needs seed-window and run-level
  diagnostics.
- Treat live search or answer evals as coverage proof. Rejected because evals
  prove selected cases and can pass while large seed/focus gaps remain.
- Crawl broader topics immediately. Rejected for this slice because the owner
  route requires explicit operator intent for crawls, and broad collection
  without a coverage map would hide the gaps it is supposed to solve.

## Consequences

- Fresh agents can run a coverage command as part of install/bootstrap
  verification.
- Xiaomi 13T can be used as a reference profile without pretending that the
  current local run is complete by default.
- Future profile expansion should be driven by missing seed pages, missing
  focus areas, freshness gaps, and failed quality gates.
- The audit does not replace semantic answer evals, freshness checks, vector
  recall work, discovery, or central `aoa-evals` proof authority.

## Verification

- `docs/COVERAGE.md` documents the target and command.
- `aoa-4pda coverage audit xiaomi-13t` reports profile coverage without
  touching the network.
- Contract tests cover both a no-run profile and a partial Xiaomi 13T stored
  run.
- The validator requires the coverage doc and command token in the public
  install surfaces.
