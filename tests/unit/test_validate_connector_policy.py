from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from validate_connector import _forbidden_artifact_path_error


def test_forbidden_artifact_scan_skips_ignored_pytest_cache(tmp_path):
    cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
    cache_dir.mkdir(parents=True)

    assert _forbidden_artifact_path_error(tmp_path, cache_dir) is None


def test_forbidden_artifact_scan_rejects_heavy_file_patterns(tmp_path):
    sqlite_path = tmp_path / "starter.sqlite3"
    parquet_path = tmp_path / "dump.parquet"
    qdrant_dir = tmp_path / "vectors.qdrant"
    sqlite_path.write_bytes(b"sqlite")
    parquet_path.write_bytes(b"parquet")
    qdrant_dir.mkdir()

    assert _forbidden_artifact_path_error(tmp_path, sqlite_path) == (
        "forbidden artifact file exists inside repository: starter.sqlite3"
    )
    assert _forbidden_artifact_path_error(tmp_path, parquet_path) == (
        "forbidden artifact file exists inside repository: dump.parquet"
    )
    assert _forbidden_artifact_path_error(tmp_path, qdrant_dir) == (
        "forbidden artifact directory exists inside repository: vectors.qdrant"
    )
