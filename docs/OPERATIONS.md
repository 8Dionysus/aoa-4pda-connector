# Operations

## Daily Safe Commands

```bash
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda storage status
aoa-4pda policy check
aoa-4pda profile inspect xiaomi-13t
aoa-4pda discovery audit xiaomi-13t
aoa-4pda discovery review xiaomi-13t
aoa-4pda coverage audit xiaomi-13t
aoa-4pda refresh audit xiaomi-13t
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval hybrid-query-packets
aoa-4pda eval answer-packets
```

## Crawl Commands

Crawl commands require explicit operator intent and configured storage roots.
When no external roots are set, the connector uses ignored repo-local
`.connector-state/` roots. Run the offline proof before a live crawl:

```bash
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval hybrid-query-packets
aoa-4pda eval answer-packets
```

Then use the starter profile first:

```bash
aoa-4pda crawl --profile starter --max-topics 10
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter --run latest
aoa-4pda build-vector --profile starter --run latest
aoa-4pda build-graph --profile starter --run latest
aoa-4pda proof live-starter --run latest --query "redmi note 10 twrp bootloop firmware"
aoa-4pda eval live-search-quality --run latest
aoa-4pda query "redmi note 10 twrp bootloop firmware"
aoa-4pda query-graph "redmi note 10 twrp bootloop firmware"
aoa-4pda query-hybrid "redmi note 10 twrp bootloop firmware"
aoa-4pda answer "redmi note 10 twrp bootloop firmware"
```

Run these stages sequentially. `build-index`, `build-vector`, and
`build-graph` consume the normalization receipt for the selected run.

The starter profile fetches bounded public page offsets per topic according to
`max_pages_per_topic`. The command path writes raw snapshots, normalized topic
pages, indexes, deterministic vector indexes, graphs, and evidence packets to
configured storage roots outside Git history.

`eval live-search-quality` is a no-network gate over an existing named run. It
reads crawl/normalize/index receipts and checks expected top evidence for
specific technical terms without writing live corpus data to Git.

## Focused Xiaomi 13T Route

Inspect the profile and storage roots before any live request:

```bash
aoa-4pda storage status --measure
aoa-4pda profile inspect xiaomi-13t
aoa-4pda discovery audit xiaomi-13t
aoa-4pda discovery review xiaomi-13t
aoa-4pda coverage audit xiaomi-13t
aoa-4pda refresh audit xiaomi-13t
```

Then run the bounded Xiaomi 13T profile only after explicit operator intent:

```bash
aoa-4pda crawl --profile xiaomi-13t
aoa-4pda normalize --run latest
aoa-4pda build-index --profile xiaomi-13t --run latest
aoa-4pda build-vector --profile xiaomi-13t --run latest
aoa-4pda build-graph --profile xiaomi-13t --run latest
aoa-4pda discovery audit xiaomi-13t --run latest
aoa-4pda discovery review xiaomi-13t --run latest
aoa-4pda coverage audit xiaomi-13t --run latest
aoa-4pda refresh audit xiaomi-13t --run latest
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_search_quality.json
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_xiaomi_13t_ranking_pressure.json
aoa-4pda eval live-hybrid-query-quality --run latest --suite evals/suites/live_xiaomi_13t_hybrid_query_quality.json
aoa-4pda eval live-graph-query-quality --run latest --suite evals/suites/live_xiaomi_13t_graph_query_quality.json
aoa-4pda eval live-answer-quality --run latest --suite evals/suites/live_xiaomi_13t_answer_quality.json
aoa-4pda query-hybrid "Xiaomi 13T boot.img Magisk KSU" --run latest
aoa-4pda answer "Xiaomi 13T aristotle TWRP boot.img" --run latest
```

The Xiaomi 13T seed set is intentionally small but not only first-page based:
it includes high-signal firmware `st=` windows for `boot.img`,
`recovery.img`, TWRP, and HyperOS material. The current reviewed seed expansion
contains 23 seed entries and 70 expected public pages. Expand it only through
reviewed seed files, coverage gaps, and eval cases before increasing topic
scope again.
The current local proof run for that seed plan is
`20260621T194521Z__crawl`: 23 fetched seeds, 70 fetched public pages, 1,448
normalized posts, a 1,559-document keyword index, a 1,559-document
deterministic vector index with 26,701 features, and a 1,508-node/2,855-edge
graph. Treat the run as reproducible local evidence, not as Git content.
It is not final deep-device coverage by itself. Check
`information_needs.summary.deep_profile_missing_need_ids` in
`aoa-4pda coverage audit xiaomi-13t --run 20260621T194521Z__crawl` before
claiming that a class of Xiaomi 13T questions is covered; the current matrix
reports 10/10 covered classes for that named run.
Use `discovery audit` to find public topic/window candidates already visible in
stored snapshots before changing seeds. Review `review_priority`,
`anchor_texts`, `evidence_contexts`, and `target_hits`; already covered
seed-plan windows are counted separately and should not become new seed gaps.
Use `discovery review` to compare those candidates with the review manifest;
accepted candidates are seed-update proposals and still require explicit
operator confirmation before a bounded crawl.
Use `refresh audit` to decide whether an existing named run can be reused or
needs an operator-confirmed bounded refresh before live answer gates.

## Prepared Redmi Note 10 Pro Route

Inspect the second representative profile before any live request:

```bash
aoa-4pda profile inspect redmi-note-10-pro
```

The Redmi Note 10 Pro profile is prepared for the next focused run, but it is
not deeply proven by receipts yet. It uses reviewed starter-topic public seed
windows for MIUI/unofficial firmware, `sweet`, `boot.img`, `recovery.img`,
Magisk, and TWRP coverage. After explicit operator intent and storage review,
the intended run sequence is:

```bash
aoa-4pda crawl --profile redmi-note-10-pro
aoa-4pda normalize --run latest
aoa-4pda build-index --profile redmi-note-10-pro --run latest
aoa-4pda build-vector --profile redmi-note-10-pro --run latest
aoa-4pda eval live-search-quality --run latest --suite evals/suites/live_redmi_note_10_pro_search_quality.json
```

Do not treat the prepared profile as a broad crawl permission; it is a bounded
next-device route.

## Receipts

Fixture materialization and future crawl/index/vector/graph runs should write
receipts to `CONNECTOR_ARTIFACT_ROOT`, not to Git.

## Cleanup

Delete or rotate repo-local or external artifacts only after checking active
processes, storage policy, and operator intent.
