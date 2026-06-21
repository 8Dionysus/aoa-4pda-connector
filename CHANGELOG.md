# Changelog

## Unreleased

- Initial GitHub-publishable skeleton for `aoa-4pda-connector`.
- Added policy, storage, schemas, fixtures, CLI stubs, validator, and tests.
- Added BM25 + exact-token starter search with query reports, score
  breakdowns, matched terms, matched phrases, and focused snippets.
- Added heuristic entity extraction v1 for devices, codenames, firmware
  versions, tools, files, issues, fixes, warnings, and kind-scoped graph nodes.
- Added live starter proof for externally stored public crawl artifacts, named
  run support for index/graph builds, and stable query-derived packet ids.
- Hardened parser coverage with a sanitized live-shaped fixture, public
  author/date extraction, and quote/edit/signature noise cleanup.
- Added chunking v1 so BM25/exact search indexes evidence chunks inside posts
  and returns chunk ids, offsets, and chunk-level evidence refs.
- Added a repo-local starter search eval pack with a no-network runner and CI
  gate for expected top chunk/post evidence.
- Added a repo-local starter graph relation eval over the sanitized live-shaped
  fixture to protect post-to-entity graph edges for issue/fix/warning evidence.
- Added starter graph relation semantics v1 with heuristic `fixes_issue` and
  `warns_about` edges plus eval coverage.
- Added starter graph query packets that enrich keyword evidence results with
  post-local `fixes_issue` and `warns_about` graph context plus eval coverage.
- Added deterministic starter answer packets that render graph-enriched
  evidence into issue/fix/warning summaries plus local eval coverage.
- Added an ignored repo-local `.connector-state/` storage scaffold and default
  fallback roots for small starter databases before external storage is needed.
- Added `storage status` and no-network `materialize fixture` commands for
  inspecting storage and writing a tiny queryable fixture database.
- Made starter crawls honor `max_pages_per_topic` and write page-distinct
  normalized snapshots instead of overwriting later topic pages.
- Added `eval live-search-quality` for checking expected top evidence and
  specific-term matches against an already-built bounded live starter run.
- Added technical token normalization for split file names, firmware versions,
  separated model strings, and starter device aliases such as `sweet`.
- Added a Xiaomi 13T focused-device profile, public topic seed set,
  profile-inspection CLI route, focused live-search eval suite, and portable
  connector-family storage recipe.
- Added seed-window crawl support for preserving source `st=` offsets and
  per-seed page limits, then used it for high-signal Xiaomi 13T firmware
  windows.
- Added focused Xiaomi 13T entity extraction v2 for model/codename/HyperOS,
  root/recovery actions, image files, Magisk/KSU/TWRP/OrangeFox/fastboot
  evidence, plus a public-safe graph relation eval suite.
- Added a receipt-driven Xiaomi 13T live graph-query quality eval that checks
  root/recovery relation context over existing configured-storage index and
  graph artifacts without recrawling.
- Added root/recovery answer packet rendering with public-safe Xiaomi 13T
  answer eval coverage and a receipt-driven live answer-quality gate over
  existing configured-storage index and graph artifacts.
- Expanded the Xiaomi 13T live answer-quality suite across root, recovery,
  Russian-language, accessory, and HyperOS notification queries, with compact
  per-case diagnostics for top evidence, matched terms, scores, answer labels,
  and relation edges.
- Added a Xiaomi 13T live ranking-pressure suite and optional expected-result
  rank diagnostics for hard OrangeFox, vendor_boot, KernelSU, and HyperOS
  recovery queries over existing configured-storage indexes.
- Added KernelSU alias extraction for Xiaomi root evidence so `boot.img`
  mentions near KernelSU produce KSU tool nodes and root relation edges.
- Added relation-intent rerank for graph-query/answer packets so hard
  root/recovery queries can promote cited relation-rich evidence while keeping
  original keyword ranks in diagnostics.
- Added a no-network `aoa-4pda ready` maturity audit for the
  `connector-ready-v1` loop target, plus connector-ready/runtime contract docs
  and validator coverage for those surfaces.
- Added freshness/capture context to evidence and answer packets, including
  schema coverage, deterministic answer eval checks, and live answer
  diagnostics.
- Added the prepared Redmi Note 10 Pro representative focused-device profile,
  bounded seed windows, local live-search quality suite, readiness checks, and
  profile inspection coverage.
- Added `aoa-4pda coverage audit` for no-network reference-profile coverage
  checks over seed windows, receipts, indexes, graph artifacts, quality gates,
  and explicit Xiaomi 13T gap reporting.
- Added `aoa-4pda refresh audit` for no-network run freshness checks, stale
  receipt detection, derived artifact timestamp checks, and bounded refresh
  planning.
- Added `aoa-4pda discovery audit` for no-network, review-priority public
  topic/window candidate extraction from already-stored raw snapshots before
  seed expansion, with seed-plan-covered windows excluded from candidate gaps.
- Added a readiness seed-review gate so `aoa-4pda ready` stays `not_ready`
  while the Xiaomi 13T reference run still has unreviewed discovery candidates.
- Added the Xiaomi 13T `information_need_matrix` and deep information-need
  coverage checks so materialized seed windows are not mistaken for full
  answerable device coverage.
- Added answer eval coverage for the five Xiaomi 13T expansion classes:
  battery/power, camera, purchase/variants, firmware source, and late-window
  regression watch.
- Added `aoa-4pda discovery review` and the first Xiaomi 13T review manifest
  for no-network accept/reject/defer classification before seed updates.
- Applied the reviewed Xiaomi 13T seed expansion, growing the profile to 23
  bounded seed entries and 70 expected public pages pending the next bounded
  crawl/rebuild.
- Materialized the reviewed Xiaomi 13T seed expansion in local configured
  storage with run `20260621T194521Z__crawl`: 23 fetched seeds, 70 fetched
  public pages, 1,448 normalized posts, a 1,559-document keyword index, and a
  1,508-node/2,855-edge graph export.
- Added the discovery pagination defer rule for ordinary numbered page-window
  links inside already seeded topics, plus a refreshed Xiaomi 13T review
  manifest covering 105/105 current discovery candidates.
- Updated Xiaomi 13T live eval expectations against the materialized run:
  KSU+Magisk root evidence now resolves to the more specific post, while
  ranking-pressure remains a keyword top-N recall gate and graph-query/answer
  gates own relation-aware top ranking.
- Reached local `connector-ready-v1` on the materialized Xiaomi 13T run with
  strict coverage, refresh, discovery-review, search, ranking-pressure, graph,
  answer, validator, pytest, compile, and diff checks green.
- The information-need gate now reports the current Xiaomi 13T matrix as 10/10
  covered on run `20260621T194521Z__crawl`, while still making future
  expansion gaps explicit.
- Added a deterministic no-model vector index, `build-vector`, `query-hybrid`,
  vector receipts/schemas, and a starter hybrid query eval so keyword/vector
  merging is reproducible in a fresh clone without external embeddings.
- Added a receipt-driven Xiaomi 13T live hybrid query quality gate over
  existing keyword, vector, and graph artifacts.
- Upgraded `query-hybrid` to `hybrid_bm25_vector_graph_v1` when graph receipts
  are present: matching root/recovery relation evidence now contributes an
  auditable bounded score boost, and the Xiaomi 13T live hybrid suite protects
  recovery top-ranking cases such as `recovery.img fastboot` and OrangeFox/TWRP.
- Added `scripts/verify_agent_install_route.py`, a fresh-copy agent install
  verifier that creates an isolated temporary checkout, installs the package,
  routes generated state to temporary external storage roots, materializes the
  fixture database, and runs the no-network starter query/answer/eval route.
