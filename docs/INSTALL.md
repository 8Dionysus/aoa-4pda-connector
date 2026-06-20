# Install

## Fresh Clone

```bash
git clone <repo-url> aoa-4pda-connector
cd aoa-4pda-connector
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate_connector.py
python -m pytest -q
aoa-4pda doctor
aoa-4pda storage status
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

## Configure Storage

```bash
aoa-4pda init --apply
aoa-4pda doctor
aoa-4pda storage status
```

Without environment variables, `init --apply` uses the ignored repo-local
`.connector-state/` root. For larger runs, set external roots first:

```bash
export CONNECTOR_DATA_ROOT=/path/to/storage/aoa-4pda-connector/data
export CONNECTOR_CACHE_ROOT=/path/to/storage/aoa-4pda-connector/cache
export CONNECTOR_ARTIFACT_ROOT=/path/to/storage/aoa-4pda-connector/artifacts
aoa-4pda init --apply
```

## Safe Starter Route

The skeleton does not run network crawls by default. First run the offline proof:

```bash
aoa-4pda proof starter
aoa-4pda materialize fixture
aoa-4pda query-graph "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda answer "bootloop recovery.img camellia" --run starter-fixture
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
aoa-4pda eval graph-query-packets
aoa-4pda eval answer-packets
```

A live starter crawl should be explicit and bounded:

```bash
aoa-4pda policy check
aoa-4pda crawl --profile starter
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter
aoa-4pda build-graph --profile starter
aoa-4pda proof live-starter --run latest --query "redmi note 10 twrp boot.img"
aoa-4pda eval live-search-quality --run latest
aoa-4pda query "redmi note 10 twrp bootloop"
aoa-4pda query-graph "redmi note 10 twrp bootloop"
aoa-4pda answer "redmi note 10 twrp bootloop"
```

These commands write to configured storage roots, defaulting to ignored
repo-local `.connector-state/` when no external roots are set. The default
starter profile remains bounded and conservative, including a small
`max_pages_per_topic` limit for public topic pagination.

`eval live-search-quality` reads the already-built keyword index for the named
run. It is a local quality gate over configured storage, not a new crawl and not
a committed corpus.

For focused Xiaomi 13T runs, `eval live-graph-query-quality --run <run-id>
--suite evals/suites/live_xiaomi_13t_graph_query_quality.json` also reads the
already-built graph export and checks root/recovery relation context in local
`query-graph` packets.
