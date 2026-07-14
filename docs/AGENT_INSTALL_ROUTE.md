# Agent Install Route

Use this orientation when a user asks an agent to install or verify the
connector.

## Authority Map

- Read `AGENTS.md`, `README.md`, `BOUNDARIES.md`, the source policy, and the
  storage policy before acting.
- Read `pyproject.toml` for the package and console entrypoint contract.
- Treat `scripts/verify_agent_install_route.py` as the executable owner of the
  fresh-copy plan, not this document.
- Treat `scripts/validate_connector.py`, `tests/`, and
  `.github/workflows/validate.yml` as validation and automation owners.
- Use the installed CLI help for exact subcommand and option syntax.

## Bounded Route

Begin with an isolated environment and inspect the verifier plan. The complete
fresh-copy verifier is appropriate when package installation, repository
validation, offline fixture materialization, query/answer behavior, and starter
eval wiring all need one reproducible check. It routes generated state outside
the copied source tree and reports whether any state leaked back into the
repository scaffold.

After installation, inspect policy and storage posture before selecting a
profile. Readiness, discovery, seed review, coverage, and refresh actions are
no-network inspections over repository declarations or configured receipts.
The starter proof and fixture path are also no-network. A crawl is a separate
operator-authorized action.

Live receipt-dependent stages must use one named run and remain ordered:
source capture, normalization, keyword index, vector index, graph, then
query/answer/eval consumers. Before Xiaomi 13T seed changes, inspect discovery
and the review manifest; before quality claims, inspect coverage and freshness.
The prepared Redmi Note 10 Pro profile remains unmaterialized until an operator
chooses it and supplies an appropriate storage route.

## Stop Lines

- Do not use 4PDA internal search or account-gated routes.
- Do not download attachments or commit generated connector data.
- Do not turn discovery, review, coverage, refresh, or eval actions into crawl
  permission.
- Do not treat static information-need route coverage as case success, answer
  quality, corpus freshness, or connector readiness.
- Do not parallelize stages that consume receipts from the preceding stage.
