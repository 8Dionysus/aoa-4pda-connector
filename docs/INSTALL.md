# Install

## Executable Owners

- `AGENTS.md` owns the short operator validation route.
- `pyproject.toml` owns package metadata and the installed `aoa-4pda` entrypoint.
- `scripts/verify_agent_install_route.py` owns the fresh-copy execution plan.
- `scripts/validate_connector.py` owns repository validation.
- `.github/workflows/validate.yml` owns the required CI sequence.

This document explains installation posture; it is not a second command
catalog. Exact CLI syntax is exposed by the installed entrypoint and its
built-in help.

## Fresh Clone Posture

Install the project with its development dependencies in an isolated Python
environment, then use the fresh-copy verifier when end-to-end installation
confidence is required. The verifier copies the repository into temporary
space, installs the package, routes generated state to temporary storage,
executes repository validation and the bounded starter path, and removes its
temporary state after success.

Python dependency installation may use the network. The connector portion of
the verifier does not crawl 4PDA, use internal search, or download attachments.
Its plan-only output is the inspectable source for the exact sequence.

## Storage

Without environment overrides, small starter state belongs under the ignored
`.connector-state/` scaffold. Larger or long-lived runs use the three roots
defined by `connector/STORAGE_POLICY.md`: `CONNECTOR_DATA_ROOT`,
`CONNECTOR_CACHE_ROOT`, and `CONNECTOR_ARTIFACT_ROOT`. The CLI owns storage
initialization, diagnosis, and status reporting; `docs/EXTERNAL_STORAGE.md`
explains portable layouts.

## Starter and Focused Routes

The executable verifier owns the no-network starter proof, fixture
materialization, query, answer, and local eval sequence. Live work starts only
after explicit operator intent and policy/storage review. The CLI profile
surface owns bounded crawl and derived-stage syntax; receipt-dependent stages
remain sequential for a single named run.

For Xiaomi 13T, the profile owns the seed file, information-need matrix, and
quality-gate suite map. Discovery, seed review, coverage, refresh, and focused
quality surfaces inspect an already selected run; they do not grant crawl
permission. The prepared Redmi Note 10 Pro profile is a separate bounded route,
not evidence that a second live run has already been materialized.
