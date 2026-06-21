# AOA-4PDA-D-0030: Information Need Coverage

## Status

Accepted.

## Context

The Xiaomi 13T reference run can now materialize a bounded seed plan, build
keyword, vector, and graph artifacts, and pass focused search, hybrid, graph,
and answer gates. That proves an important base route, but it still does not
answer the user's harder question: can the local database find everything
important about the device?

Seed-window coverage and receipt-chain coverage are necessary, but they are
not the same as useful knowledge coverage. A run can include camera, battery,
purchase, firmware-source, and late-window discussion pages while having no
eval route that proves those classes can be retrieved or answered.

## Decision

Add `connector/profiles/xiaomi_13t_information_needs.json` as the profile's
information-need matrix and wire it into the no-network coverage and readiness
audits.

The matrix records Xiaomi 13T question classes, the seed focus areas that are
expected to support each class, and the live eval case routes that currently
prove retrieval or answer behavior. `aoa-4pda coverage audit xiaomi-13t` now
reports `information_needs`, including connector-ready coverage, deep-profile
coverage, missing need IDs, and per-need statuses such as `covered`,
`unmaterialized`, and `missing_eval_route`.

`aoa-4pda ready` exposes this as
`reference_profile_information_need_coverage`. The criterion reports partial
whenever deep-profile needs are materialized but lack dedicated eval routes.

## Rationale

This keeps the connector honest as it grows. The repository can now distinguish
between:

- pages that are present in a bounded local corpus
- classes of questions that have a local search, graph, hybrid, or answer eval
  route
- classes that are seeded or materialized but not yet proven useful

That distinction matters because the repository is public method and skeleton,
not a giant committed corpus. Future agents need a compact, versioned surface
that says where to add eval pressure next without recrawling or guessing from
conversation history.

## Alternatives

- Keep coverage based only on seed pages and receipts. Rejected because it can
  overstate deep device usefulness.
- Expand answer suites opportunistically without a matrix. Rejected because it
  hides which device-question classes are intentional and which remain gaps.
- Treat every materialized focus area as covered. Rejected because local data
  presence does not prove retrievability, ranking, graph context, or grounded
  answer quality.

## Consequences

- The current Xiaomi 13T run is still strong materialized evidence, but it is
  no longer treated as complete deep-profile proof by default.
- Battery/power, camera, purchase/variants, firmware source, and late-window
  regression watch are covered in the current matrix by focused live answer
  eval cases over the named Xiaomi 13T run.
- `coverage_ready`, refresh strict readiness, and connector strict readiness
  can become stricter when the matrix says deep-profile coverage is incomplete.
- Future deepening work should add eval routes for missing need IDs before
  expanding crawl scope again.

## Verification

- `connector/profiles/xiaomi-13t.yaml` names the information-need matrix.
- `aoa-4pda profile inspect xiaomi-13t` exposes `information_need_matrix`.
- `aoa-4pda coverage audit xiaomi-13t --run <run-id>` reports
  `information_needs.summary.deep_profile_missing_need_ids`.
- `aoa-4pda ready --run <run-id>` reports
  `reference_profile_information_need_coverage`.
- The validator requires the matrix and documentation tokens.
- Contract tests cover no-run, partial-run, readiness, and profile-inspect
  behavior without network access.
