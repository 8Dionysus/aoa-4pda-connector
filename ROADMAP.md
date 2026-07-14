# Roadmap

## Wave 0: Skeleton

- repository route cards
- source and storage policy
- ignored repo-local state scaffold
- CLI skeleton
- schemas and synthetic fixtures
- validator and tests

## Wave 1: Starter Corpus

- offline starter proof over synthetic fixtures
- no-network materialized fixture database for fresh-clone query smoke tests
- policy-confirmed starter crawl over 10-30 public topics with bounded page
  offsets
- live starter proof over external storage artifacts
- normalized topic/post snapshots
- live-shaped sanitized parser fixtures
- chunking v1 for evidence chunks inside long posts
- local BM25 and exact-token search over starter data
- starter search eval pack for expected top evidence checks
- starter graph relation eval pack for issue/fix/warning entity-edge checks
- heuristic entity extraction for starter graph nodes
- heuristic `fixes_issue` and `warns_about` relation edges v1
- evidence packet query route
- starter graph query packets with post-local relation context
- starter answer packets rendered from graph-enriched evidence
- live starter search quality eval over named configured-storage runs

## Wave 2: Deep Search

- focused-device profile route with Xiaomi 13T seed set, profile inspection,
  and a live-run eval suite
  - focused Xiaomi 13T graph-query eval over already-built live index and graph
    receipts
  - focused Xiaomi 13T answer eval over already-built live index and graph
    receipts
  - expanded Xiaomi 13T answer-quality diagnostics across root, recovery,
    accessory, and HyperOS notification cases
  - Xiaomi 13T ranking-pressure gate for keyword top-N recall on harder
    OrangeFox, vendor_boot, KernelSU, and HyperOS recovery queries
  - relation-intent rerank for graph/answer packets with original keyword rank
    diagnostics
  - answer packet freshness/capture context for cited local evidence
  - second representative Redmi Note 10 Pro profile with bounded seed windows
    and live search gate prepared for the next focused run
  - reference-profile discovery audit for review-priority public topic/window
    candidates visible in stored snapshots before seed expansion, excluding
    already covered seed-plan windows from candidate gaps
  - reference-profile seed-review audit and Xiaomi 13T review manifest for
    accept/reject/defer classification before seed updates
  - reviewed Xiaomi 13T seed expansion applied to the profile seed plan and
    materialized in local configured storage as 23 seeds, 70 public pages,
    1,448 normalized posts, a 1,559-document keyword index, and a
    1,508-node/2,855-edge graph export
  - discovery pagination defer rule so ordinary numbered page windows stay
    reviewed future expansion pressure unless exact review accepts them
  - reference-profile coverage audit for Xiaomi 13T seed windows, receipt
    chain, index, graph, quality gates, and explicit gap reporting
  - reference-profile refresh audit for crawl age, derived artifact freshness,
    and bounded operator-confirmed refresh planning
  - deterministic no-model vector index and graph-aware hybrid keyword/vector
    query route with starter and Xiaomi 13T live eval coverage
- stronger exact-token search for device models, firmware versions, and error
  strings
  - starter technical token aliases for split file/version/model forms
- stronger entity extraction for devices, apps, versions, firmware, warnings,
  and fixes
  - focused Xiaomi 13T extraction for model numbers, codenames, HyperOS
    versions, root actions, recovery actions, image files, and
    Magisk/KSU/TWRP/OrangeFox/fastboot evidence
  - KernelSU spelling alias for KSU root evidence near `boot.img`
- optional external embedding/vector-store adapter behind an explicit
  dependency and receipt-compatible contract
- broader retrieval eval expansion against bounded external-storage runs

## Wave 3: Graph Evidence

- graph node/edge builder
- broader issue/fix/warning relation extraction beyond starter heuristics
- broader graph query traversal beyond starter post-local packets
- richer answer synthesis over multiple posts and relation paths
  - deterministic Xiaomi root/recovery answer packets from cited graph context

## Wave 4: Runtime Access

- no-network `connector-ready-v1` maturity audit for install, storage,
  receipt, quality-gate, heavy-data, and runtime-contract readiness
  - local materialized Xiaomi 13T run proves the retrieval path while
    information-need coverage keeps future deep-profile expansion gaps visible
  - current Xiaomi 13T matrix has 15/15 deep-required classes covered by local
    eval routes before strict ready can honestly claim the reference profile is
    useful
- `abyss-stack` MCP/runtime adapter that consumes installed connector roots
  without moving corpora into Git
- root `stats/` port for the static Xiaomi 13T deep information-need eval-route
  ratio, with central `aoa-stats` contract validation and no runtime/eval
  verdict claim
