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
aoa-4pda proof starter
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
```

## Configure External Storage

```bash
export CONNECTOR_DATA_ROOT=/mnt/external/abyss-connectors/4pda/data
export CONNECTOR_CACHE_ROOT=/mnt/external/abyss-connectors/4pda/cache
export CONNECTOR_ARTIFACT_ROOT=/mnt/external/abyss-connectors/4pda/artifacts
aoa-4pda init --apply
aoa-4pda doctor
```

## Safe Starter Route

The skeleton does not run network crawls by default. First run the offline proof:

```bash
aoa-4pda proof starter
aoa-4pda eval search-quality
aoa-4pda eval graph-relations
```

A live starter crawl should be explicit and bounded:

```bash
aoa-4pda policy check
aoa-4pda crawl --profile starter
aoa-4pda normalize --run latest
aoa-4pda build-index --profile starter
aoa-4pda build-graph --profile starter
aoa-4pda query "redmi note 10 twrp bootloop"
```

These commands write only to configured external storage roots. The default
starter profile remains bounded and conservative.
