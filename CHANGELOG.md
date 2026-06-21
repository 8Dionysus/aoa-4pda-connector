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
