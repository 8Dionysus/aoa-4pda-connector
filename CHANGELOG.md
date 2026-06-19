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
