# Agent Install Route

Use this when a user asks an agent to install the connector.

## Route

1. Read `AGENTS.md`, `README.md`, `BOUNDARIES.md`,
   `connector/SOURCE_POLICY.md`, and `connector/STORAGE_POLICY.md`.
2. Create or enter a virtual environment.
3. Install the package in editable mode.
4. Run `python scripts/validate_connector.py`.
5. Run `python -m pytest -q`.
6. Run `aoa-4pda proof starter`.
7. Run `aoa-4pda eval search-quality`.
8. Run `aoa-4pda eval graph-relations`.
9. Run `aoa-4pda eval graph-query-packets`.
10. Run `aoa-4pda eval answer-packets`.
11. Ask the operator for external storage roots if they are not set.
12. Run `aoa-4pda init --apply` only after roots are confirmed.
13. Run `aoa-4pda doctor` and `aoa-4pda policy check`.
14. Stop before any network crawl unless the operator explicitly asks for it.
15. If the operator asks for a starter run, use `--profile starter` with a
    small `--max-topics` value first.
16. After a starter crawl, run `normalize`, `build-index`, `build-graph`, and
    `proof live-starter` sequentially against the same run.

## Do Not

- do not use 4PDA internal search routes
- do not download attachments
- do not create large data inside the repository
- do not run full-public profile without explicit policy and storage review
- do not parallelize dependent live-run stages that consume prior receipts
