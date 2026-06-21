# Agent Install Route

Use this when a user asks an agent to install the connector.

## Route

1. Read `AGENTS.md`, `README.md`, `BOUNDARIES.md`,
   `connector/SOURCE_POLICY.md`, and `connector/STORAGE_POLICY.md`.
2. Create or enter a virtual environment.
3. Install the package in editable mode:
   ```bash
   python -m pip install -e ".[dev]"
   ```
4. Run `python scripts/validate_connector.py`.
5. Run `python -m pytest -q`.
6. Run `aoa-4pda doctor` and `aoa-4pda storage status`.
7. Run `aoa-4pda ready` to inspect current `connector-ready-v1` gaps.
8. Run `aoa-4pda proof starter`.
9. Run `aoa-4pda init --apply` to create the default ignored repo-local
    `.connector-state/` roots, unless the operator supplied external roots.
10. Run `aoa-4pda materialize fixture` to create the tiny no-network local
   database.
11. Run:
    ```bash
    aoa-4pda query-graph "bootloop recovery.img camellia" --run starter-fixture
    ```
12. Run:
    ```bash
    aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
    ```
13. Run `aoa-4pda eval search-quality`.
14. Run `aoa-4pda eval graph-relations`.
15. Run `aoa-4pda eval graph-query-packets`.
16. Run `aoa-4pda eval answer-packets`.
17. Ask the operator for external storage roots before larger or long-lived
    crawls.
18. Run `aoa-4pda policy check`.
19. Stop before any network crawl unless the operator explicitly asks for it.
20. If the operator asks for a starter run, use `--profile starter` with a
    small `--max-topics` value first.
21. After a starter crawl, run `normalize`, `build-index`, `build-graph`, and
    `proof live-starter` sequentially against the same run.
22. Run `aoa-4pda eval live-search-quality --run <run-id>` only after that
    named live run has an index receipt.
23. For a Xiaomi 13T run with a graph receipt, run
    `aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json`.
24. Then run
    `aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json`
    to verify deterministic answer packets over the same stored run.
25. Inspect `aoa-4pda profile inspect redmi-note-10-pro` as the prepared next
    representative focused-device route. Do not crawl it unless the operator
    explicitly chooses that second profile and confirms storage.

## Do Not

- do not use 4PDA internal search routes
- do not download attachments
- do not commit generated data; repo-local `.connector-state/` is allowed only
  as ignored local state
- do not run full-public profile without explicit policy and storage review
- do not parallelize dependent live-run stages that consume prior receipts
- do not treat `eval live-search-quality` as permission to crawl; it reads an
  existing run only
- do not treat `eval live-graph-query-quality` as permission to crawl or
  rebuild a corpus; it reads existing index and graph receipts only
- do not treat `eval live-answer-quality` as permission to crawl or rebuild a
  corpus; it renders answers from existing index and graph receipts only
- do not treat the prepared Redmi Note 10 Pro profile as already receipt-proven;
  it is the next bounded representative route
