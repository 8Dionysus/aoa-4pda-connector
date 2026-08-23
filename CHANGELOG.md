# Changelog

## [Unreleased]

_No unreleased changes._

## [0.1.1] - 2026-08-23

### Summary

Corrective source release for the provider-before-consumer validation
boundary. The direct `aoa-stats` checkout now resolves to the exact commit
published by `aoa-stats@v0.2.0`, so a green ancestor-only validation can no
longer be mistaken for exact published-provider compatibility. The immutable
`v0.1.0` source release and GitHub Release are preserved unchanged.

### Added

- An owner-local release preflight and regression test for exact published
  `aoa-stats` provider identity.
- Decision record `AOA-4PDA-D-0039` documenting the direct-provider equality
  rule and its boundary from generated KAG action/family pins.

### Changed

- The validation workflow replaces the ancestor-only stats pin with
  `AOA_STATS_REVISION=dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`, the peeled
  commit of the published `aoa-stats@v0.2.0` tag.
- Release law, version markers, roadmap posture, and the release-surface
  checker now describe and enforce the corrective `v0.1.1` identity.

### Fixed

- Prevented an older contained `aoa-stats` commit from satisfying the direct
  provider compatibility check for a new connector release.

### Deprecated

- No public connector API is deprecated.

### Removed

- No connector route, schema, source-policy rule, or runtime boundary was
  removed.

### Security

- No network, account, private-source, attachment, credential, or secret
  boundary changed. The release remains source-only and does not add an
  artifact class, public asset, admission, deployment, runtime, proof, or
  acceptance claim.

### Compatibility and migration

- Direct `aoa-stats` provider identity is now an equality requirement:
  `AOA_STATS_REVISION` must equal the published `v0.2.0` tag's peeled commit
  `dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`. Ancestor-only pins are invalid.
- The generated `aoa-kag` action and owner-family pins remain separate
  identities governed by their documented ancestry rule.

### Deployment, observability, recovery, and rollback

- No deployment, MCP, runtime, storage, rollback, or recovery behavior was
  changed. Existing source-only and runtime-owner boundaries remain in force.
- The release publisher continues to refuse tag/release overwrite; `v0.1.0`
  is not moved or rewritten.

### Validation

- Fresh live provider resolution: GitHub Release `aoa-stats@v0.2.0` is
  published, its annotated tag object is
  `a12ffb39e4bfee0426ea84647aa3e90597002189`, and it peels exactly to
  `dc608fd5de3fcaf0301f356c9efd52e2bdd350ce`.
- The owner-local release checker rejects the former ancestor pin
  `ae87240bd5f1b64769fcf39b4eae67363cee9f38`; the complete owner and CI gate
  results are recorded in the release execution report.
- `connector-ready-v1` remains `not_ready`/`ready=false`; source publication
  does not prove runtime health, corpus freshness, semantic quality, central
  proof, artifact admission, or human acceptance.

### Notes and non-claims

- This is a compatible 0.x patch correcting release compatibility identity;
  it does not broaden the connector's public method boundary.
- The source release has no public package assets or admitted artifact
  record. GitHub publication is not artifact trust, deployment, runtime,
  proof, delivery, closure, or acceptance.

### First-Parent Reconciliation

This corrective range starts after immutable `v0.1.0` at
`702fd73982282e43cbf2b8fe77333a1b4bb86a11` and contains one source correction
commit before the GitHub squash release carrier. The carrier is publication
bookkeeping, not a second product change, and its exact landed identity is
recorded in the owner release execution report and the `v0.1.1` tag. The
source commit is named here after the release-prep branch is sealed.

| Range item | Exact source ref | URL | Subject | Classification |
|---|---|---|---|---|
| prep-1 | `pending-release-prep-source-commit` | release-prep branch commit URL recorded at handoff | Enforce exact published aoa-stats provider identity | changelog-worthy corrective source and owner-law change |

## [0.1.0] - 2026-08-23

### Summary

Initial public method-boundary release for bounded, policy-gated retrieval
over public 4PDA topic and post pages. The package provides a local CLI,
evidence-aware search/graph/answer contracts, fixtures and eval routes, and
owner-local KAG/stats integration surfaces. It is a publishable connector
method boundary, not a full 4PDA mirror or production runtime.

### Added

- Python 3.11+ package and `aoa-4pda` CLI with doctor, storage, policy,
  profile, crawl, normalize, index/vector/graph, query, answer, proof, eval,
  export, and serve command families.
- Public-only source policy with explicit route allow/deny behavior and source
  URL preservation; network work remains explicit and bounded.
- Normalized topic/post, evidence, crawl, index, vector, graph, query, claim,
  conflict, freshness, applicability, warning, and answer packet schemas.
- Starter search scoring, chunk-level indexing, technical token normalization,
  heuristic/entity extraction, relation-intent reranking, graph relations,
  and graph query packets.
- Xiaomi 13T and Redmi Note 10 Pro focused profiles, KernelSU/root extraction
  fixtures, root/recovery answer packets, and bounded starter/live-shaped eval
  suites.
- Claim-aware answer packets with answer reports, evidence chains, nuance
  reports, agent answer briefs, gap awareness, conflict/freshness context, and
  explicit `network_touched`/`read_only` fields.
- Local ignored state and materialization storage status, deterministic
  fresh-copy install verification, connector-ready audit,
  coverage/refresh/discovery/review routes, and a portable read-only MCP
  rollout contract.
- Owner-local KAG provider home, source registry/build path, provider-record
  validation, deterministic parity/artifact gates, repository KAG index family,
  and portable content-addressed shard family.
- Owner-local `aoa_stats_local_port_v1` reference-only port with an explicit
  authority ceiling.

### Changed

- Search and answer grounding became receipt-aware, claim-aware, and explicit
  about insufficiency rather than returning an unqualified success.
- Graph, answer, and eval surfaces distinguish source evidence, normalized
  records, relations, freshness, and uncertainty.
- Repository KAG indexes moved from earlier monolithic generated
  representations to the portable content-addressed family described by
  `kag/indexes/index_family.manifest.json`, with adaptive-prefix shards and
  tracked-byte budget evidence.
- Validation now includes local KAG provider/index parity, deterministic family
  gates, heavy-artifact guards, no-network route checks, fresh-copy
  verification, and the accepted immutable `aoa-kag` owner-family pin.
- This release adds the owner-local release law and preserves the manifest's
  `skeleton`/`not_ready` maturity state as a separate truth from publication.
- Runtime responsibility is explicit: this repository owns source/CLI/packet
  contracts; `abyss-stack` owns deployment and MCP access.

### Fixed

- Paginated crawl ranking and page accumulation behavior.
- Live-shaped parser fixtures and technical token/entity handling.
- Local eval-port contract and domain-specific answer/evidence gaps.
- Codex review/policy guards, workflow guard indentation, KAG provider JSON
  validation, index parity, and deterministic artifact admission.
- Generated KAG family layout and source/event shard placement after the
  portable-family migration.

### Deprecated

- No authored public API is marked deprecated.
- The pre-portable monolithic generated KAG representation is superseded for
  generated consumers by the portable family; this is not an authored
  connector-schema deprecation.

### Removed

- Six prior monolithic generated repository KAG index files were removed as
  part of the portable-family migration.
- No source-policy route, public answer field, or authored connector schema
  was removed in the release range.

### Security

- Network is off by default for local and first MCP access.
- Public topic/post allowlisting is retained; internal search,
  authentication, private/user routes, attachments, downloads, and broad
  uncontrolled discovery are denied.
- The first MCP route is read-only and local; crawl, refresh, materialize,
  reindex, writes, seed edits, network access, and approval operations remain
  outside it.
- Stats packets are public/reference-only and do not carry raw corpus content
  or authority to claim quality, readiness, freshness, or proof.
- No secret, credential, private corpus, or authenticated route is included in
  the repository.

### Compatibility and migration

- Provider-before-consumer compatibility is pinned to published
  `aoa-kag@v0.5.0` and `aoa-stats@v0.2.0`; the consumer workflow pins are
  ancestors of those exact provider tags.
- The portable KAG family is the generated consumer surface. Consumers must
  use its manifest, shard budget, and validator rather than restoring removed
  monolithic files.
- The 0.x package is an initial method boundary. Runtime consumers must follow
  the `abyss-stack` adapter contract and must not infer deployment or health
  from this repository's local receipts.

### Deployment, observability, recovery, and rollback

- Deployment and MCP exposure remain an `abyss-stack` concern; this release
  contains no deployment mutation or runtime activation.
- Local doctor, storage, readiness, freshness, coverage, discovery/review, and
  packet receipts expose bounded observability without claiming a live service.
- The release publisher refuses force-tagging or release overwrite. A bad
  publication is corrected by a new owner decision/release, not rewritten
  history; generated state and full corpora remain outside Git.

### Validation

- Owner-local release-surface preflight, connector validator, local stats-port
  validator, package compilation, and the complete no-network test/eval route
  are required release gates.
- The release-prep PR's required `Validate` check is the authoritative CI
  result for the landed release candidate; its exact PR, run, job, and commit
  are recorded in the release execution report.
- `aoa-4pda ready` remains `not_ready`/`ready=false`: the focused profile and
  receipt chain do not constitute one coherent current crawl-to-graph
  pipeline. This is an honest maturity result, not a publication failure.
- Existing local evidence included 121 passing tests, 38 required directories,
  80 required files, 17 schemas, and zero validator warnings/errors before the
  release-prep changes; the final landed rerun is recorded in the execution
  report.

### Notes and non-claims

- This is a 0.x initial method boundary. It does not claim complete 4PDA
  availability, a full corpus, stable production embeddings/models, semantic
  answer correctness, or a deployed runtime.
- GitHub CI, a tag, or a GitHub Release does not prove runtime activation,
  runtime health, central proof, semantic quality, source adequacy, or human
  acceptance.
- The local KAG family digest is an index-family identity, not a package
  release digest. Generated consumers remain subordinate to authored source.
- This source-only release has no public package assets or attestation. The
  OS artifact policy was consulted and has no connector-owned artifact class;
  a future package asset requires a new owner decision and admitted trust
  sidecars.

### First-Parent Reconciliation

This is the complete root-to-main first-parent range: 54 first-parent commits,
zero merge commits, and no exact duplicate. Each row is classified as a
separate changelog item, combined material, generated churn, migration-worthy
generated material, internal/noise, or direct landing. Direct commits use a
`D` suffix in the FP column and are not silently omitted.

| FP | Exact landed ref | PR or direct URL | Landed subject | Classification |
|---:|---|---|---|---|
| 0 | 8b3b767e5bab7f63a3fa443881185d0138d8510d | https://github.com/8Dionysus/aoa-4pda-connector/commit/8b3b767e5bab7f63a3fa443881185d0138d8510d | Initial aoa-4pda connector skeleton | changelog-worthy: separate initial boundary |
| 1 | 17ee4f7442323e6f000eef8675b3ba6ff8efada6 | https://github.com/8Dionysus/aoa-4pda-connector/pull/1 | Add CI and starter proof gate | changelog-worthy: separate CI/proof foundation |
| 2 | 86706415e3317a919f8fadde38f7860388fe2a65 | https://github.com/8Dionysus/aoa-4pda-connector/pull/2 | Improve starter search scoring | changelog-worthy: combined search foundation with #6 and #16 |
| 3 | a6f0c4c84defd6c8cc58e3bfd45353b16dc50d64 | https://github.com/8Dionysus/aoa-4pda-connector/pull/3 | Add heuristic entity extraction | changelog-worthy: combined entity/search foundation with #18 |
| 4 | 83c6b9931ea33e9ad789ea5d2ba4389b1b66d846 | https://github.com/8Dionysus/aoa-4pda-connector/pull/4 | Add live starter proof gate | changelog-worthy: separate live-shaped proof gate |
| 5 | e4d6ad371c7c7381c6656ca97b284b107240b7f9 | https://github.com/8Dionysus/aoa-4pda-connector/pull/5 | Harden live-shaped parser fixtures | changelog-worthy: separate fixture/parser hardening |
| 6 | ac9d28c029ba1c3c831c4207bd84cc2bbb072e2d | https://github.com/8Dionysus/aoa-4pda-connector/pull/6 | Add chunk-level search indexing | changelog-worthy: combined search foundation with #2 |
| 7 | 81341d748c7c85c234ddbc1f93d519a92195d658 | https://github.com/8Dionysus/aoa-4pda-connector/pull/7 | Add starter search eval pack | changelog-worthy: separate eval surface |
| 8 | 93f3d9ab5426b7b0e948faeaa4f091386172e953 | https://github.com/8Dionysus/aoa-4pda-connector/pull/8 | Add starter graph relation eval | changelog-worthy: separate graph eval surface |
| 9 | 7e9049de7cae2c670f6a7661cc32ce75b9b6df0d | https://github.com/8Dionysus/aoa-4pda-connector/pull/9 | Add starter graph relation edges | changelog-worthy: separate graph relation model |
| 10 | 675f5469be99e5e7ee3622933c22c8a5a6613ec7 | https://github.com/8Dionysus/aoa-4pda-connector/pull/10 | Add starter graph query packets | changelog-worthy: separate graph query contract |
| 11 | 37e6b181faee80ddf094f6eed2ef1facd6420542 | https://github.com/8Dionysus/aoa-4pda-connector/pull/11 | Add starter answer packets | changelog-worthy: separate answer ABI |
| 12 | 15d66ca39774723b70bedda75d6ee00fc72ee06f | https://github.com/8Dionysus/aoa-4pda-connector/pull/12 | Add repo-local state root | changelog-worthy: separate state/storage boundary |
| 13 | 01019d3be399b9a1c80d5726ea8a05796ae6fe3b | https://github.com/8Dionysus/aoa-4pda-connector/pull/13 | Add fixture materialization storage status | changelog-worthy: combined state/materialization contract with #12 |
| 14 | cc074ed8aa34c42dd34ce40464ea7a78bc4df0dd | https://github.com/8Dionysus/aoa-4pda-connector/pull/14 | Add paginated starter crawl ranking | changelog-worthy: separate crawl/ranking behavior |
| 15 | 993cdc785c1edb1daee43c888bee06e2956ff392 | https://github.com/8Dionysus/aoa-4pda-connector/pull/15 | Add live starter search eval | changelog-worthy: combined search eval story with #7 |
| 16 | 61436380a1121b20d6b5bca293ea6d7bd46d2c3a | https://github.com/8Dionysus/aoa-4pda-connector/pull/16 | Add technical token normalization | changelog-worthy: combined search normalization with #2 |
| 17 | 425dda1ff0243d6044a749153c86e125f5488ffb | https://github.com/8Dionysus/aoa-4pda-connector/pull/17 | Add Xiaomi 13T focused profile | changelog-worthy: separate focused profile |
| 18 | edf4b887faeb4adb0f73ce4eb47afaa5ea66867c | https://github.com/8Dionysus/aoa-4pda-connector/pull/18 | Add Xiaomi entity extraction v2 | changelog-worthy: combined entity extraction with #3 |
| 19 | 25a779fe7feb9e5cddf78932d1db4ba9e302f455 | https://github.com/8Dionysus/aoa-4pda-connector/pull/19 | Add live Xiaomi graph query eval | changelog-worthy: separate focused graph eval |
| 20 | 95594f7e24aeea96a3969331c42ad95486e7fdcb | https://github.com/8Dionysus/aoa-4pda-connector/pull/20 | Add root recovery answer packets | changelog-worthy: separate recovery/answer fixture |
| 21 | f64cde1e3103349c238026ef119ce384f4a4b23c | https://github.com/8Dionysus/aoa-4pda-connector/pull/21 | Expand Xiaomi answer quality diagnostics | changelog-worthy: separate diagnostics |
| 22 | 692c05130b5ff3b59f05111d60d92e1617c155eb | https://github.com/8Dionysus/aoa-4pda-connector/pull/22 | Add Xiaomi ranking pressure eval | changelog-worthy: combined ranking/eval coverage with #7 and #15 |
| 23 | da2a39ea9f08b3d2dad6d2f2354630698fa46003 | https://github.com/8Dionysus/aoa-4pda-connector/pull/23 | Add KernelSU root extraction | changelog-worthy: separate domain extraction |
| 24 | d679f52d9b7895729c98cccfa51e916a8b9a34e5 | https://github.com/8Dionysus/aoa-4pda-connector/pull/24 | Add relation intent rerank | changelog-worthy: separate query/rerank behavior |
| 25 | c62e081148cdd5ffc10624ed5f6b9d96610f488c | https://github.com/8Dionysus/aoa-4pda-connector/pull/25 | Add connector ready audit | changelog-worthy: separate readiness contract; current ready remains false |
| 26 | de57536cd471e7134010df0c1cd8b5e4f5f72564 | https://github.com/8Dionysus/aoa-4pda-connector/pull/26 | Add answer freshness context | changelog-worthy: separate freshness contract |
| 27 | 712603b7299e608112e359752f6c8291d5b7273d | https://github.com/8Dionysus/aoa-4pda-connector/pull/27 | Add Redmi representative profile | changelog-worthy: separate profile surface |
| 28 | 85de7ef3141f8617e46d4833122547816bc29a6e | https://github.com/8Dionysus/aoa-4pda-connector/pull/28 | Repair local eval port contract | changelog-worthy: separate eval-port repair |
| 29 | 43428aa95ec59e9dc308036dcb718532b8acab83 | https://github.com/8Dionysus/aoa-4pda-connector/pull/29 | Reach connector ready deep proof | changelog-worthy: separate deep-proof attempt; current ready remains not_ready |
| 30 | 0446d803dd30bf5fd40db4a21e41e72effa9cb03 | https://github.com/8Dionysus/aoa-4pda-connector/pull/30 | Add answer gap awareness | changelog-worthy: separate answer limitation awareness |
| 31 | 5e4c56d32aac517871b5e79816d2025316672b47 | https://github.com/8Dionysus/aoa-4pda-connector/pull/31 | Add answer evidence chains | changelog-worthy: separate evidence-chain ABI |
| 32 | 1268153c22c8889716232d9dd2179bab704aefc3 | https://github.com/8Dionysus/aoa-4pda-connector/pull/32 | Add deterministic agent answer briefs | changelog-worthy: separate agent-facing answer surface |
| 33 | adb729af95c29084a8b1913d4760eb92ac1ccc37 | https://github.com/8Dionysus/aoa-4pda-connector/pull/33 | Add portable MCP rollout contract | changelog-worthy: separate runtime/MCP boundary |
| 34 | 4d536494412153ae3e0851a59b3bd3afb34198a5 | https://github.com/8Dionysus/aoa-4pda-connector/pull/34 | Add claim conflict freshness runtime | changelog-worthy: separate claim/conflict/freshness behavior |
| 35 | 038d773d17cdd33cd99d29bbb7a626df168312d8 | https://github.com/8Dionysus/aoa-4pda-connector/pull/35 | Document connector-family claim contract | changelog-worthy: separate family claim boundary |
| 36 | ad2b30a51cf276a3bb90fac93ba6b71ea7fc313f | https://github.com/8Dionysus/aoa-4pda-connector/pull/36 | Add local KAG provider home | changelog-worthy: separate owner-local KAG provider |
| 37 | b67062779b0c0204b239e10518704dbd704c184a | https://github.com/8Dionysus/aoa-4pda-connector/pull/37 | Add repo-local KAG indexes | generated churn: combined KAG index consumer surface with #40, #42, #44-#48, #50, #51 |
| 38D | 77f987478382427951dd0546fb8d8072c47ea2be | https://github.com/8Dionysus/aoa-4pda-connector/commit/77f987478382427951dd0546fb8d8072c47ea2be | Add operator source planning | changelog-worthy: combined source-registry/build pipeline with #38 and #39 |
| 39D | faf6a9b1baedaafa819057354240656cf3985bf5 | https://github.com/8Dionysus/aoa-4pda-connector/commit/faf6a9b1baedaafa819057354240656cf3985bf5 | Fix workflow guard indentation | internal/noise: CI-only recovery, no independent user-facing capability |
| 38 | 77694422e85e3712bee352dd2790bbe3453d4f32 | https://github.com/8Dionysus/aoa-4pda-connector/pull/38 | Add source registry crawl pipeline | changelog-worthy: combined source-registry/build pipeline with direct #38D and #39 |
| 39 | 97e75d2a2ad0846c53307736947f83179060e6c6 | https://github.com/8Dionysus/aoa-4pda-connector/pull/39 | Add source build pipeline | changelog-worthy: combined source-registry/build pipeline with direct #38D and #38 |
| 40 | 677adf7b5dc6e9e7ac031e813f92bb7d150d6692 | https://github.com/8Dionysus/aoa-4pda-connector/pull/40 | Refresh repo-local KAG source index | generated churn: regenerated derived source index |
| 41 | 573c980ff8bd701a5b4f2373ff6b3421b32e6bb7 | https://github.com/8Dionysus/aoa-4pda-connector/pull/41 | Harden 4PDA Codex review guards | changelog-worthy: separate policy/CI/fixture/eval hardening |
| 42 | 75561ac4638a436701db5450e7f2a14955b7d24e | https://github.com/8Dionysus/aoa-4pda-connector/pull/42 | Backfill live KAG source surface index | generated churn: derived KAG source index |
| 43 | 89ee3a5703d97687657135d493182c48ac84e543 | https://github.com/8Dionysus/aoa-4pda-connector/pull/43 | Validate KAG provider JSON records | changelog-worthy: separate provider-record validation |
| 44 | 4078302d5ee8796f7083ebe904202fa41747aa1a | https://github.com/8Dionysus/aoa-4pda-connector/pull/44 | Enforce repo-local KAG index parity | generated churn: derived parity gate |
| 45 | 2022c9fccdcf8d17d8087ac80763bfb23fcb3f58 | https://github.com/8Dionysus/aoa-4pda-connector/pull/45 | Pin deterministic repo-local KAG index gate | generated churn: deterministic gate metadata |
| 46 | cee1216c5ae0bbd0f2440c69dd7881d4f7b77893 | https://github.com/8Dionysus/aoa-4pda-connector/pull/46 | Add repository KAG index family | migration/consumer-visible generated family, combined with later portable family |
| 47 | 3bd3ecd68b2b6c081a67c900654e500f1176b878 | https://github.com/8Dionysus/aoa-4pda-connector/pull/47 | Allow repository KAG indexes in artifact guard | generated churn: artifact admission allowance |
| 48 | a06acc2bc288a3be6b3bc4d654eb350f7aa7171a | https://github.com/8Dionysus/aoa-4pda-connector/pull/48 | Publish canonical repository KAG indexes | generated churn/consumer-visible: canonical derived read model |
| 49 | 01170c4df4c926078a81f982c157edcbb4e3e227 | https://github.com/8Dionysus/aoa-4pda-connector/pull/49 | Add 4PDA local stats port | changelog-worthy: separate owner-local stats federation surface |
| 50 | a273f71c6fcc30c34759b2ef1e2f08cd8fc6baa3 | https://github.com/8Dionysus/aoa-4pda-connector/pull/50 | Adopt portable KAG index family | migration-worthy generated change: monolith-to-portable family, manifest, shard budget, validator/action updates |
| 51 | a70fc99d8779d1ea834b11244d3832d2ae8f4092 | https://github.com/8Dionysus/aoa-4pda-connector/pull/51 | Pin accepted aoa-kag owner-family DAG | changelog-worthy: separate immutable provider/owner-family admission pin |

### Reconciled changed-path and generated-consumer ledger

- The root commit established the connector skeleton across `.github`,
  `connector`, `docs`, `evals`, `scripts`, `src`, `tests`, manifests, and
  README/ROADMAP.
- PRs 1-16 established policy, storage, parser, search/chunk, crawl, proof,
  and eval surfaces; PRs 17-24 established focused profiles, entity/graph/
  answer behavior, and relation reranking.
- PRs 25-35 established readiness, freshness, gap/evidence chains, agent
  briefs, MCP rollout, and claim-family boundaries.
- PRs 36-48 established local KAG provider/build/index, source registry,
  review guards, provider JSON validation, parity gates, and the derived index
  family. Generated rows are retained in the ledger but combined here as
  consumer-visible derived work rather than repeated feature claims.
- Direct landings `77f9874` and `faf6a9b`, PRs 38-39, and PR 41 account for
  source planning/build, CI recovery, pipeline, and policy hardening.
- PR 49 introduced the local reference-only stats port. PR 50 migrated six
  monolithic KAG indexes to 221 portable shards with a budget receipt. PR 51
  accepted the immutable `aoa-kag` owner-family pin and moved the generated
  family's event/source shard placement.
- No duplicate or intentional exclusion was found. The exact changed-path
  evidence is the first-parent reconciliation in the Wave-1 report and the
  landed Git history; this changelog preserves every first-parent row above.
