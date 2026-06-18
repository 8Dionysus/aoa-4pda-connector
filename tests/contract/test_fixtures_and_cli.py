from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_with_src() -> dict[str, str]:
    env = os.environ.copy()
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}:{env['PYTHONPATH']}"
    return env


def test_fixture_packet_is_json_and_does_not_use_internal_search():
    packet = json.loads(
        (REPO_ROOT / "connector/fixtures/expected_packets/synthetic_bootloop_packet.json").read_text(
            encoding="utf-8"
        )
    )
    assert packet["schema"] == "aoa_4pda_evidence_packet_v1"
    assert packet["policy"]["internal_search_used"] is False
    assert packet["results"][0]["source_url"].startswith("https://4pda.to/forum/index.php?showtopic=")


def test_cli_doctor_is_safe_without_external_storage():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "doctor"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_doctor_v1"
    assert payload["network_touched"] is False


def test_cli_policy_check_denies_service_routes():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "policy", "check"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["internal_search_allowed"] is False
    assert payload["attachments_allowed"] is False


def test_cli_starter_proof_is_offline_and_queryable():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "proof", "starter"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_starter_proof_v1"
    assert payload["status"] == "ok"
    assert payload["network_touched"] is False
    assert payload["external_storage_required"] is False
    assert payload["checks"]["internal_search_unused"] is True
    assert payload["top_result"]["post_id"] == "1002"
