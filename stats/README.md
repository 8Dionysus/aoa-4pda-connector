# aoa-4pda-connector local stats port

This directory exposes statistical questions whose domain meaning belongs to
the 4PDA connector. It uses the shared `aoa-stats` grammar without moving
information-need ownership, eval verdicts, source evidence, or runtime state
into the central stats organ.

## Current reference measurement

| Measurement | Question | Reference value |
| --- | --- | --- |
| `aoa-4pda-connector/xiaomi-13t-deep-information-need-eval-route-ratio` | What fraction of current deep-required Xiaomi 13T information needs have complete declared routes to case ids in their profile-mapped local eval suites? | `15 / 15` at evidence revision `a06acc2bc288a3be6b3bc4d654eb350f7aa7171a` |

The population is a census of unique needs marked
`required_for_deep_profile=true` in the supported Xiaomi 13T information-need
matrix. A need enters the numerator only when it declares at least one eval
case and every declared case id exists in the suite selected by the current
profile. A valid population with no routes is an observed zero. Missing,
malformed, empty, duplicate, unsupported, or profile-mismatched input is
unknown.

## Evidence posture

The packet is a public reference snapshot of connector-authored route
declarations at a named source revision. It does not read raw captures or
configured storage, execute eval cases, or inspect a live run. Its terminal
progress means only that the declared census was processed.

## Authority

The ratio reports static route coverage only. It does not establish case
execution, case success, retrieval or answer quality, source adequacy, corpus
materialization, freshness, discovery completeness, connector readiness,
central proof verdicts, or runtime health.

## Surfaces

- `port.manifest.json` declares the owner-local question and measurement.
- `packets/xiaomi-13t-deep-information-need-eval-route-ratio.reference.json`
  records the evidence-linked reference observation.
- the Xiaomi 13T profile and information-need matrix own the population and
  declared suite routes;
- the mapped local suites own their case ids, while `aoa-evals` retains proof
  and verdict authority;
- `aoa-stats` owns shared validation and cross-owner composition.
