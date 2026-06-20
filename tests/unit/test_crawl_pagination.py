from __future__ import annotations

import json
from types import SimpleNamespace

from aoa_4pda_connector import cli
from aoa_4pda_connector.config import ENV_ARTIFACT_ROOT, ENV_CACHE_ROOT, ENV_DATA_ROOT
from aoa_4pda_connector.fetch import FetchResult


def test_crawl_uses_profile_page_bounds_without_network(tmp_path, monkeypatch, capsys):
    calls: list[str] = []

    def fake_fetch_public_topic(url, output_dir):  # noqa: ANN001 - mirrors CLI dependency shape.
        calls.append(url)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"page-{len(calls)}.html"
        path.write_text("<html><body>fixture</body></html>", encoding="utf-8")
        return FetchResult(
            url=url,
            path=path,
            bytes_written=path.stat().st_size,
            sha256=f"sha-{len(calls)}",
            status=200,
        )

    monkeypatch.setenv(ENV_DATA_ROOT, str(tmp_path / "data"))
    monkeypatch.setenv(ENV_CACHE_ROOT, str(tmp_path / "cache"))
    monkeypatch.setenv(ENV_ARTIFACT_ROOT, str(tmp_path / "artifacts"))
    monkeypatch.setattr(
        cli,
        "_read_profile",
        lambda _repo_root, _profile_id: {
            "seed_file": "unused.yaml",
            "max_topics": 1,
            "max_pages_per_topic": 3,
            "min_delay_seconds": 0,
        },
    )
    monkeypatch.setattr(
        cli,
        "_read_seed_urls",
        lambda _path: [
            {
                "id": "topic-42",
                "label": "Topic 42",
                "url": "https://4pda.to/forum/index.php?showtopic=42",
            }
        ],
    )
    monkeypatch.setattr(cli, "fetch_public_topic", fake_fetch_public_topic)
    monkeypatch.setattr(cli, "polite_sleep", lambda _seconds: None)
    monkeypatch.setattr(cli, "_new_run_id", lambda _kind: "crawl-pagination-test")

    rc = cli.cmd_crawl(SimpleNamespace(profile="starter", max_topics=None, delay_seconds=0))
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert calls == [
        "https://4pda.to/forum/index.php?showtopic=42&st=0",
        "https://4pda.to/forum/index.php?showtopic=42&st=20",
        "https://4pda.to/forum/index.php?showtopic=42&st=40",
    ]
    assert payload["counts"]["requested_topics"] == 1
    assert payload["counts"]["requested_pages"] == 3
    assert payload["counts"]["fetched_topics"] == 1
    assert payload["counts"]["fetched_pages"] == 3
    assert payload["snapshots"][2]["page_start"] == 40


def test_crawl_uses_seed_start_offset_and_seed_page_bounds_without_network(tmp_path, monkeypatch, capsys):
    calls: list[str] = []

    def fake_fetch_public_topic(url, output_dir):  # noqa: ANN001 - mirrors CLI dependency shape.
        calls.append(url)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"page-{len(calls)}.html"
        path.write_text("<html><body>fixture</body></html>", encoding="utf-8")
        return FetchResult(
            url=url,
            path=path,
            bytes_written=path.stat().st_size,
            sha256=f"sha-{len(calls)}",
            status=200,
        )

    monkeypatch.setenv(ENV_DATA_ROOT, str(tmp_path / "data"))
    monkeypatch.setenv(ENV_CACHE_ROOT, str(tmp_path / "cache"))
    monkeypatch.setenv(ENV_ARTIFACT_ROOT, str(tmp_path / "artifacts"))
    monkeypatch.setattr(
        cli,
        "_read_profile",
        lambda _repo_root, _profile_id: {
            "seed_file": "unused.yaml",
            "max_topics": 1,
            "max_pages_per_topic": 8,
            "min_delay_seconds": 0,
        },
    )
    monkeypatch.setattr(
        cli,
        "_read_seed_urls",
        lambda _path: [
            {
                "id": "firmware-window",
                "label": "Firmware Window",
                "url": "https://4pda.to/forum/index.php?showtopic=1076859&st=1800",
                "max_pages": "2",
            }
        ],
    )
    monkeypatch.setattr(cli, "fetch_public_topic", fake_fetch_public_topic)
    monkeypatch.setattr(cli, "polite_sleep", lambda _seconds: None)
    monkeypatch.setattr(cli, "_new_run_id", lambda _kind: "crawl-offset-test")

    rc = cli.cmd_crawl(SimpleNamespace(profile="xiaomi-13t", max_topics=None, delay_seconds=0))
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert calls == [
        "https://4pda.to/forum/index.php?showtopic=1076859&st=1800",
        "https://4pda.to/forum/index.php?showtopic=1076859&st=1820",
    ]
    assert payload["counts"]["requested_topics"] == 1
    assert payload["counts"]["requested_pages"] == 2
    assert payload["counts"]["fetched_pages"] == 2
    assert payload["snapshots"][0]["page_start"] == 1800
    assert payload["snapshots"][1]["page_start"] == 1820
