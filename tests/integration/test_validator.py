from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_validator_passes():
    result = subprocess.run(
        [sys.executable, "scripts/validate_connector.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"


def test_repo_validator_rejects_malformed_kag_json():
    manifest = REPO_ROOT / "kag" / "manifest.json"
    original = manifest.read_text(encoding="utf-8")
    try:
        manifest.write_text("{not-json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "scripts/validate_connector.py"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        manifest.write_text(original, encoding="utf-8")

    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any("invalid json" in error and "kag/manifest.json" in error for error in payload["errors"])


def test_repo_validator_rejects_command_block_outside_agents():
    command_doc = REPO_ROOT / "docs" / "_validator_command_block_test.md"
    try:
        command_doc.write_text(
            "# Temporary command catalog\n\n  ~~~shell\n  python -m pytest -q\n  ~~~\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, "scripts/validate_connector.py"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        command_doc.unlink(missing_ok=True)

    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any(
        "command block outside AGENTS.md" in error
        and "docs/_validator_command_block_test.md" in error
        for error in payload["errors"]
    )


def test_repo_validator_rejects_unterminated_command_block_outside_agents():
    command_doc = REPO_ROOT / "docs" / "_validator_unterminated_command_block_test.md"
    try:
        command_doc.write_text(
            "# Temporary command catalog\n\n```bash title=\"validation\"\npython -m pytest -q\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, "scripts/validate_connector.py"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        command_doc.unlink(missing_ok=True)

    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any(
        "unterminated command block outside AGENTS.md" in error
        and "docs/_validator_unterminated_command_block_test.md" in error
        for error in payload["errors"]
    )
