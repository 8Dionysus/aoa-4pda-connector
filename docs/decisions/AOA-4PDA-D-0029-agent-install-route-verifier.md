# AOA-4PDA-D-0029: Agent Install Route Verifier

## Status

Accepted.

## Context

The connector goal is not only to keep the current checkout green. The public
repository must be installable by a fresh agent or developer that clones it,
creates an isolated environment, configures universal storage roots, and proves
the starter search, graph, answer, eval, and readiness route without depending
on private paths or committed generated state.

The existing CI and starter proof gate check important pieces in place, but
they do not fully prove the fresh-agent route. They do not copy the repository
as a new clone, install console scripts in an isolated virtual environment,
route generated artifacts outside the copied source tree, or check that
repo-local `.connector-state` remains only a portable scaffold.

## Decision

Add `scripts/verify_agent_install_route.py` as an executable bootstrap verifier
and wire it into install docs, runtime contract docs, readiness checks,
validator checks, tests, and CI.

The verifier creates a temporary fresh copy of the repository, prunes generated
state from `.connector-state`, installs the package in an isolated virtual
environment, configures temporary external storage roots, and runs the offline
bootstrap route: validation, optional pytest, doctor, storage policy checks,
readiness, discovery and coverage audits without live crawling, fixture
materialization, keyword/vector/graph query paths, answer packets, and starter
evals.

CI runs the verifier with `--skip-pytest` because pytest already has a separate
workflow step. Local full verification keeps pytest enabled by default.

## Rationale

Agent installability is a first-class acceptance condition for this repository.
A contributor should be able to hand the repo to an agent and receive a working
connector method without relying on chat history, this host's personal paths, or
large prebuilt artifacts.

Making the route executable keeps the public method honest. It proves that the
documented install path, console entrypoint, storage routing, fixture pipeline,
receipt-producing commands, and no-generated-leak boundary all survive outside
the current working tree.

The verifier also keeps heavy data policy explicit: Python dependency install
may use the network, but the connector bootstrap route itself does not crawl
4PDA, call internal 4PDA search, or commit indexes, graphs, packets, caches, or
raw captures into Git.

## Alternatives

- Keep fresh installability as documentation only. Rejected because the loop
  goal needs a machine-checkable route, not only instructions.
- Treat normal CI as enough. Rejected because in-place CI can pass while a
  fresh copied repo leaks generated state, misses console entrypoints, or
  depends on local storage defaults.
- Put generated starter artifacts in Git to simplify install. Rejected because
  the repository is method and skeleton; mutable corpora, indexes, graphs, and
  packets belong under configured storage roots.

## Consequences

- Fresh-agent bootstrap is now a distinct quality gate, separate from unit
  tests and live Xiaomi 13T evidence.
- The verifier report is bootstrap evidence, not a runtime query API and not a
  claim that the repository fully covers all Xiaomi 13T knowledge.
- CI gains a stronger public-install guard while still avoiding live crawls and
  heavy artifact generation.
- Future install-route changes must update the verifier, docs, readiness
  criteria, and validator expectations together.
- External storage remains the expected route for large corpora, while
  repo-local `.connector-state` remains a scaffold for small starter databases
  and ignored generated state.

## Verification

- `python scripts/verify_agent_install_route.py` should pass from the current
  repository and clean up its temporary copy on success.
- `.github/workflows/validate.yml` should run
  `python scripts/verify_agent_install_route.py --skip-pytest`.
- `python scripts/validate_connector.py` should require the verifier script,
  install docs entry, agent install route entry, and runtime contract schema.
- `aoa-4pda ready --run <run-id> --strict` should report the fresh-clone
  install route and validation/CI contract criteria as achieved once the route
  is wired.
