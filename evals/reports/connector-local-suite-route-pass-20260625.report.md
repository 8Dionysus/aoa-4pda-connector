---
schema_version: local_eval_report_note_v1
owner_repo: aoa-4pda-connector
status: draft
title: connector local suite route pass
summary: Records the selected receipt-driven/offline apply route for the active
  connector local eval port and the no-network suite checks applied.
refs:
- evals/PORT.yaml
- evals/suites/connector-local-quality-gates.suite.md
- evals/suites/starter_search_quality.json
- evals/suites/starter_graph_relations.json
- evals/suites/starter_graph_query_packets.json
- evals/suites/starter_hybrid_query_packets.json
- evals/suites/starter_answer_packets.json
- docs/OPERATIONS.md
- scripts/validate_connector.py
authority_boundary: no verdict, scoring, regression, or proof doctrine authority
---

## Scope

This report records the 2026-06-25 route pass for `aoa-4pda-connector` as an
active repo-local eval port.

The active pressure is connector-local retrieval, graph, hybrid-query, and
answer quality over public-safe fixtures or already-materialized configured
storage receipts.

## Route Decision

Selected route: `aoa-eval-apply`.

Reason: the connector already owns active suite inputs and local runner
commands. The right smoke is to apply existing offline/no-network suites and
keep live suites receipt-driven. No recrawl, refresh, or new live materialization
is required for this route pass.

Stop-line: live suites may read existing bounded receipts, but this route must
not crawl, commit generated corpora, or promote local runner output into central
`aoa-evals` proof.

## Applied Checks

Local port:

```bash
python /srv/AbyssOS/aoa-evals/scripts/validate_local_eval_port.py --target-root /srv/AbyssOS/connectors/aoa-4pda-connector --json
```

Observed result: `ok: true`.

Connector validator:

```bash
python scripts/validate_connector.py
```

Observed result: `status: ok`.

Focused tests:

```bash
python -m pytest -q tests/integration/test_validator.py tests/integration/test_agent_install_verifier.py
```

Observed result:

```text
2 passed
```

No-network local suite runners:

```bash
PYTHONPATH=src python -m aoa_4pda_connector.cli eval search-quality
PYTHONPATH=src python -m aoa_4pda_connector.cli eval graph-relations
PYTHONPATH=src python -m aoa_4pda_connector.cli eval graph-query-packets
PYTHONPATH=src python -m aoa_4pda_connector.cli eval hybrid-query-packets
PYTHONPATH=src python -m aoa_4pda_connector.cli eval answer-packets
```

Observed result:

- `search-quality`: 4/4 cases passed, `network_touched: false`.
- `graph-relations`: 1/1 case passed, `network_touched: false`.
- `graph-query-packets`: 1/1 case passed, `network_touched: false`.
- `hybrid-query-packets`: 1/1 case passed, `network_touched: false`.
- `answer-packets`: 1/1 case passed, `network_touched: false`.
- Temporary runner artifacts were deleted after the runs.

## Result

The current connector route is apply existing connector-native suites. Live
quality gates remain receipt-driven and should run only against an existing
bounded configured-storage run. Central proof adoption is out of scope for this
local pass.
