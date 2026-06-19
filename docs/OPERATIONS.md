# Operations

## Daily Safe Commands

```bash
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda policy check
aoa-4pda proof starter
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

## Crawl Commands

Crawl commands require explicit operator intent and configured storage roots.
When no external roots are set, the connector uses ignored repo-local
`.connector-state/` roots. Run the offline proof before a live crawl:

```bash
aoa-4pda proof starter
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

Then use the starter profile first:

```bash
aoa-4pda crawl --profile starter --max-topics 10
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter --run latest
aoa-4pda build-graph --profile starter --run latest
aoa-4pda proof live-starter --run latest --query "redmi note 10 twrp bootloop firmware"
aoa-4pda query "redmi note 10 twrp bootloop firmware"
aoa-4pda query-graph "redmi note 10 twrp bootloop firmware"
aoa-4pda answer "redmi note 10 twrp bootloop firmware"
```

Run these stages sequentially. `build-index` and `build-graph` consume the
normalization receipt for the selected run.

The command path writes raw snapshots, normalized topics, indexes, graphs, and
evidence packets to configured storage roots outside Git history.

## Receipts

Future crawl/index/graph runs should write receipts to
`CONNECTOR_ARTIFACT_ROOT`, not to Git.

## Cleanup

Delete or rotate repo-local or external artifacts only after checking active
processes, storage policy, and operator intent.
