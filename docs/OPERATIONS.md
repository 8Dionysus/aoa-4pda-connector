# Operations

## Executable Route

`AGENTS.md` owns the short operator route. The `aoa-4pda` CLI owns exact
operational syntax, `scripts/verify_agent_install_route.py` owns the bounded
fresh-copy sequence, and `.github/workflows/validate.yml` owns automated
checks. This document describes ordering and evidence boundaries.

## Safe Inspection

Policy, storage, profile, readiness, discovery, seed-review, coverage, and
refresh actions are read-only or no-network inspections. The starter proof and
fixture materialization path use public-safe repository fixtures. Their reports
must not be interpreted as permission to crawl or as central proof verdicts.

## Live Pipeline

A live crawl requires explicit operator intent, an allowed bounded profile,
and confirmed storage roots. For one named run, derived stages remain ordered:
normalize the captured pages, build the keyword index, build the deterministic
vector index, build the graph, then run query, answer, and quality consumers.
Receipts under `CONNECTOR_ARTIFACT_ROOT` carry the handoff between stages.

The connector writes raw snapshots and normalized records to the data root,
rebuildable indexes to the cache root, and graphs, exports, and receipts to the
artifact root. None of those generated surfaces belongs in Git.

## Xiaomi 13T

`connector/profiles/xiaomi-13t.yaml` owns the first focused-device route. Its
reviewed seed plan contains 23 bounded entries and 70 expected public pages,
including selected firmware windows rather than an unbounded topic sweep. The
information-need matrix and profile-mapped suites make declared question-class
pressure explicit.

The historical named reference run remains local runtime evidence, not
repository truth. Coverage and refresh reports must be read against the actual
configured receipts before any current claim. The local stats packet measures
only static route declarations at its named source revision; it does not reuse
historical runtime counts as live evidence.

Discovery candidates are review inputs. Already-covered pagination windows do
not become automatic seed gaps, and accepted candidates still require an
operator-confirmed bounded update.

## Redmi Note 10 Pro

`connector/profiles/redmi-note-10-pro.yaml` is the prepared second focused
route. Its seed windows and local suite are source-authored, but no live receipt
chain is implied. Treat it as a future bounded operator choice rather than a
broad crawl grant.

## Cleanup

Delete or rotate repo-local or external generated state only after checking
active processes, the storage policy, receipt consumers, and operator intent.
