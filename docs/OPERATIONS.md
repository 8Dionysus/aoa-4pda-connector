# Operations

## Daily Safe Commands

```bash
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda policy check
```

## Crawl Commands

Crawl commands require explicit operator intent and configured storage roots.
Use the starter profile first:

```bash
aoa-4pda crawl --profile starter --max-topics 10
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter
aoa-4pda build-graph --profile starter
aoa-4pda query "redmi note 10 twrp bootloop firmware"
```

The command path writes raw snapshots, normalized topics, indexes, graphs, and
evidence packets outside Git.

## Receipts

Future crawl/index/graph runs should write receipts to
`CONNECTOR_ARTIFACT_ROOT`, not to Git.

## Cleanup

Delete or rotate external artifacts only after checking active processes,
storage policy, and operator intent.
