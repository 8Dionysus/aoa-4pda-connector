# AOA-4PDA-D-0018: Connector Ready Audit

## Status

Accepted.

## Context

The repository has grown from a public skeleton into a working starter and
focused-device connector slice. The long loop target is now
`connector-ready-v1`: a fresh-clone reproducible, storage-aware,
receipt-driven connector with local search, graph evidence, deterministic
answer packets, and quality gates.

Without a repository-local readiness surface, future agents would have to
reconstruct that target from conversation context, memory, or scattered docs.
That makes the loop fragile and risks closing work because the latest slice
passed rather than because the maturity target is actually met.

## Decision

Add a no-network `aoa-4pda ready` audit that maps `connector-ready-v1` into
explicit local criteria and reports each one as `achieved`, `partial`, or
`missing`.

The audit reads repository surfaces and configured storage receipts. It does
not crawl, rebuild indexes, write generated artifacts, or create central proof
verdicts. `--strict` returns a non-zero status until every criterion is
achieved.

## Rationale

This keeps the long connector loop grounded in current repo state rather than
chat memory. It also makes unfinished maturity gaps visible in a machine-readable
JSON report, including profile expansion, answer freshness, receipt
reproducibility, runtime contract coverage, and validator wiring.

## Alternatives

- Keep the maturity target only in `ROADMAP.md`: readable, but hard for agents
  and CI to check consistently.
- Put the target in central `aoa-evals`: too strong for this local connector
  maturity audit and risks moving proof authority into the wrong place.
- Treat passing pytest/validator as readiness: useful but too narrow; those
  checks do not prove live receipts, profile depth, runtime handoff, or answer
  contract maturity.

## Consequences

- Readiness is now inspectable through `aoa-4pda ready`.
- A `not_ready` result is expected while the loop continues; it is a guide, not
  a failure by itself.
- The audit must stay local and source-linked. It should not become a broad
  quality verdict over all of 4PDA or a replacement for central proof doctrine
  in `aoa-evals`.
- Future maturity slices should either make one criterion stronger or add a
  clearly justified criterion when the connector-ready target changes.

## Verification

- `docs/CONNECTOR_READY.md` documents the target and command.
- `docs/RUNTIME_CONTRACT.md` documents the runtime handoff surface.
- `scripts/validate_connector.py` requires the readiness and runtime docs.
- Contract tests cover `aoa-4pda ready` and `aoa-4pda ready --strict`.
