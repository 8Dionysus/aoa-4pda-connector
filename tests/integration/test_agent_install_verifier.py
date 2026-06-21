from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_agent_install_route_verifier_plan_is_public_and_bounded():
    result = subprocess.run(
        [sys.executable, "scripts/verify_agent_install_route.py", "--plan-only", "--skip-pytest"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_agent_install_route_verify_v1"
    assert payload["status"] == "plan"
    assert payload["connector_route_network_touched"] is False
    assert payload["package_install_may_use_network"] is True

    step_ids = [step["step_id"] for step in payload["steps"]]
    assert "install_editable_dev" in step_ids
    assert "validate_connector" in step_ids
    assert "materialize_fixture" in step_ids
    assert "query_hybrid_fixture" in step_ids
    assert "eval_hybrid_query_packets" in step_ids
    assert "eval_answer_packets" in step_ids
    assert "pytest" not in step_ids
