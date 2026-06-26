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
4. Run `python scripts/verify_agent_install_route.py` if the operator wants a
   one-command fresh-copy install verification before manual continuation. The
   verifier creates an isolated temporary copy, uses temporary external storage
   roots, materializes only the fixture database, and does not crawl 4PDA.
5. Run `python scripts/validate_connector.py`.
6. Run `python -m pytest -q`.
7. Run `aoa-4pda doctor` and `aoa-4pda storage status`.
8. Run `aoa-4pda ready` to inspect current `connector-ready-v1` gaps.
9. Run `aoa-4pda discovery audit xiaomi-13t` to inspect review-ready public
   candidates visible in stored snapshots without touching the network.
10. Run `aoa-4pda discovery review xiaomi-13t` to compare candidates with the
   repo-local review manifest before any seed edit.
11. Run `aoa-4pda coverage audit xiaomi-13t` to inspect the current
   `reference-profile-coverage-v1` state without touching the network.
12. Run `aoa-4pda refresh audit xiaomi-13t` to inspect current run freshness
   and refresh need without touching the network.
13. Run `aoa-4pda proof starter`.
14. Run `aoa-4pda init --apply` to create the default ignored repo-local
    `.connector-state/` roots, unless the operator supplied external roots.
15. Run `aoa-4pda materialize fixture` to create the tiny no-network local
   database.
16. Run:
    ```bash
    aoa-4pda query-graph "bootloop recovery.img camellia" --run starter-fixture
    ```
17. Run:
    ```bash
    aoa-4pda query-hybrid "bootloop recovery.img camellia" --run starter-fixture
    ```
18. Run:
    ```bash
    aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
    ```
19. Run `aoa-4pda eval search-quality`.
20. Run `aoa-4pda eval graph-relations`.
21. Run `aoa-4pda eval graph-query-packets`.
22. Run `aoa-4pda eval hybrid-query-packets`.
23. Run `aoa-4pda eval answer-packets`.
24. Run `aoa-4pda eval claim-relations`.
25. Run `aoa-4pda eval claim-answer-packets`.
26. Ask the operator for external storage roots before larger or long-lived
    crawls.
27. Run `aoa-4pda policy check`.
28. Stop before any network crawl unless the operator explicitly asks for it.
29. If the operator asks for a starter run, use `--profile starter` with a
    small `--max-topics` value first.
30. After a starter crawl, run `normalize`, `build-index`, `build-vector`,
    `build-graph`, and `proof live-starter` sequentially against the same run.
29. Run `aoa-4pda eval live-search-quality --run <run-id>` only after that
    named live run has an index receipt.
30. For a Xiaomi 13T run, run
    `aoa-4pda discovery audit xiaomi-13t --run <run-id>` before seed changes.
    Inspect `review_priority`, `anchor_texts`, `evidence_contexts`, and
    `covered_seed_window_link_count`; do not auto-add noisy or already covered
    navigation windows.
31. Then run `aoa-4pda discovery review xiaomi-13t --run <run-id>` and inspect
    `accepted_missing_from_seed` before editing seed scope.
32. Then run
    `aoa-4pda coverage audit xiaomi-13t --run <run-id>` before quality gates.
33. Then run `aoa-4pda refresh audit xiaomi-13t --run <run-id>` to check
    whether the selected run is fresh or needs an operator-confirmed refresh.
34. For a Xiaomi 13T run with vector and graph receipts, run
    `aoa-4pda query-hybrid "Xiaomi 13T boot.img Magisk KSU" --run <run-id>`
    as a local hybrid retrieval smoke.
35. Then run
    `aoa-4pda eval live-hybrid-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_hybrid_query_quality.json`
    to verify hybrid retrieval over the same stored run.
36. For a Xiaomi 13T run with a graph receipt, run
    `aoa-4pda eval live-graph-query-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_graph_query_quality.json`.
37. Then run
    `aoa-4pda eval live-answer-quality --run <run-id> --suite evals/suites/live_xiaomi_13t_answer_quality.json`
    to verify deterministic answer packets over the same stored run.
38. Inspect `aoa-4pda profile inspect redmi-note-10-pro` as the prepared next
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
- do not treat `eval hybrid-query-packets` as production semantic coverage; it
  is a no-network starter contract for keyword+deterministic-vector merging
- do not treat `eval live-hybrid-query-quality` as permission to crawl; it
  reads existing keyword/vector/graph receipts only
- do not treat `eval live-answer-quality` as permission to crawl or rebuild a
  corpus; it renders answers from existing index and graph receipts only
- do not treat `coverage audit` as a semantic answer-quality verdict; it checks
  profile materialization and gaps over existing receipts only
- do not treat `refresh audit` as permission to crawl; it reports freshness and
  a bounded plan, while the crawl itself still requires operator intent
- do not treat `discovery audit` as permission to crawl or auto-edit seeds; it
  reports review-priority candidates from existing snapshots and excludes
  already covered seed-plan windows from candidate gaps
- do not treat `discovery review` as permission to crawl; accepted candidates
  are pending seed updates and still require operator-confirmed bounded crawl
- do not treat the prepared Redmi Note 10 Pro profile as already receipt-proven;
  it is the next bounded representative route
