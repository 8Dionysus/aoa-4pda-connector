from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from aoa_4pda_connector.coverage import _quality_gates, _read_profile


REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = REPO_ROOT / "connector" / "profiles" / "xiaomi-13t.yaml"
MATRIX_PATH = REPO_ROOT / "connector" / "profiles" / "xiaomi_13t_information_needs.json"
PORT_PATH = REPO_ROOT / "stats" / "port.manifest.json"
PACKET_PATH = (
    REPO_ROOT
    / "stats"
    / "packets"
    / "xiaomi-13t-deep-information-need-eval-route-ratio.reference.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def current_profile_and_gates() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    profile = _read_profile(PROFILE_PATH)
    return profile, _quality_gates(REPO_ROOT, profile)


def derive_eval_route_ratio(
    matrix: object,
    profile: object,
    quality_gates: object,
) -> dict[str, object]:
    if not isinstance(matrix, dict):
        return {"status": "unknown", "reason": "missing_or_malformed_matrix"}
    if matrix.get("schema") != "aoa_4pda_information_need_matrix_v1":
        return {"status": "unknown", "reason": "unsupported_matrix_schema"}
    if not isinstance(profile, dict) or profile.get("schema") != "aoa_4pda_profile_v1":
        return {"status": "unknown", "reason": "unsupported_profile"}
    if matrix.get("profile_id") != profile.get("profile_id"):
        return {"status": "unknown", "reason": "profile_mismatch"}
    if profile.get("information_need_matrix") != "connector/profiles/xiaomi_13t_information_needs.json":
        return {"status": "unknown", "reason": "matrix_route_mismatch"}
    if not isinstance(quality_gates, dict):
        return {"status": "unknown", "reason": "malformed_quality_gates"}

    raw_needs = matrix.get("needs")
    if not isinstance(raw_needs, list) or not raw_needs:
        return {"status": "unknown", "reason": "malformed_or_empty_population"}
    if any(not isinstance(need, dict) for need in raw_needs):
        return {"status": "unknown", "reason": "malformed_need"}

    need_ids = [need.get("need_id") for need in raw_needs]
    if any(not isinstance(need_id, str) or not need_id for need_id in need_ids):
        return {"status": "unknown", "reason": "malformed_need_identity"}
    if len(need_ids) != len(set(need_ids)):
        return {"status": "unknown", "reason": "duplicate_need_identity"}

    deep_needs = [need for need in raw_needs if need.get("required_for_deep_profile") is True]
    if not deep_needs:
        return {"status": "unknown", "reason": "empty_deep_population"}

    complete_need_ids: list[str] = []
    gap_need_ids: list[str] = []
    for need in deep_needs:
        eval_cases = need.get("eval_cases")
        if not isinstance(eval_cases, dict):
            return {"status": "unknown", "reason": "malformed_eval_routes"}

        declared_count = 0
        unresolved: list[str] = []
        for suite_key, case_ids in eval_cases.items():
            if (
                not isinstance(suite_key, str)
                or not isinstance(case_ids, list)
                or any(not isinstance(case_id, str) or not case_id for case_id in case_ids)
            ):
                return {"status": "unknown", "reason": "malformed_eval_route"}
            gate = quality_gates.get(suite_key)
            if not isinstance(gate, dict) or gate.get("exists") is not True:
                return {"status": "unknown", "reason": "missing_profile_mapped_suite"}
            declared_count += len(case_ids)
            available = set(str(case_id) for case_id in gate.get("case_ids", []))
            unresolved.extend(case_id for case_id in case_ids if case_id not in available)

        need_id = str(need["need_id"])
        if declared_count > 0 and not unresolved:
            complete_need_ids.append(need_id)
        else:
            gap_need_ids.append(need_id)

    numerator = len(complete_need_ids)
    denominator = len(deep_needs)
    return {
        "status": "observed",
        "reason": "complete_census",
        "numerator": numerator,
        "denominator": denominator,
        "ratio": numerator / denominator,
        "gap_need_ids": gap_need_ids,
    }


def test_reference_packet_matches_current_declared_eval_routes() -> None:
    profile, gates = current_profile_and_gates()
    derived = derive_eval_route_ratio(load_json(MATRIX_PATH), profile, gates)
    packet = load_json(PACKET_PATH)

    assert derived["status"] == "observed"
    assert derived["gap_need_ids"] == []
    assert packet["population"]["size"] == derived["denominator"] == 15
    assert packet["sample"]["size"] == derived["denominator"]
    assert packet["value"]["numerator"] == derived["numerator"] == 15
    assert packet["value"]["denominator"] == derived["denominator"]
    assert packet["value"]["number"] == derived["ratio"] == 1.0
    assert packet["progress"] == {"state": "terminal", "completed": 15, "total": 15}


def test_one_missing_case_is_an_observed_route_gap() -> None:
    profile, gates = current_profile_and_gates()
    matrix = load_json(MATRIX_PATH)
    matrix["needs"][0]["eval_cases"]["live_search_suite"][0] = "does-not-exist"

    derived = derive_eval_route_ratio(matrix, profile, gates)

    assert derived["status"] == "observed"
    assert derived["numerator"] == 14
    assert derived["denominator"] == 15
    assert derived["gap_need_ids"] == ["device_identity_aliases"]


def test_valid_population_without_routes_is_observed_zero() -> None:
    profile, gates = current_profile_and_gates()
    matrix = load_json(MATRIX_PATH)
    for need in matrix["needs"]:
        if need.get("required_for_deep_profile") is True:
            need["eval_cases"] = {}

    derived = derive_eval_route_ratio(matrix, profile, gates)

    assert derived["status"] == "observed"
    assert derived["numerator"] == 0
    assert derived["denominator"] == 15
    assert derived["ratio"] == 0.0


def test_malformed_empty_duplicate_unsupported_and_missing_sources_are_unknown() -> None:
    profile, gates = current_profile_and_gates()
    matrix = load_json(MATRIX_PATH)

    duplicate = deepcopy(matrix)
    duplicate["needs"][1]["need_id"] = duplicate["needs"][0]["need_id"]
    empty = deepcopy(matrix)
    empty["needs"] = []
    unsupported = deepcopy(matrix)
    unsupported["schema"] = "aoa_4pda_information_need_matrix_v2"
    mismatched = deepcopy(matrix)
    mismatched["profile_id"] = "other-profile"
    malformed_routes = deepcopy(matrix)
    malformed_routes["needs"][0]["eval_cases"] = ["not", "a", "mapping"]
    missing_suite = deepcopy(gates)
    missing_suite["live_search_suite"]["exists"] = False

    cases = (
        derive_eval_route_ratio(None, profile, gates),
        derive_eval_route_ratio(duplicate, profile, gates),
        derive_eval_route_ratio(empty, profile, gates),
        derive_eval_route_ratio(unsupported, profile, gates),
        derive_eval_route_ratio(mismatched, profile, gates),
        derive_eval_route_ratio(malformed_routes, profile, gates),
        derive_eval_route_ratio(matrix, profile, missing_suite),
    )

    assert all(case["status"] == "unknown" for case in cases)


def test_measurement_stays_reference_only_and_below_connector_and_eval_authority() -> None:
    port = load_json(PORT_PATH)
    measurement = port["measurements"][0]
    ceiling = measurement["authority_ceiling"]

    assert port["evidence_posture"] == {
        "live_state": "reference_only",
        "privacy": "public",
        "raw_content_allowed": False,
    }
    assert measurement["live_state"] == {"capability": "reference_only"}
    assert measurement["dimensions"]["allowed"] == []
    assert "case execution or success" in ceiling
    assert "connector readiness" in ceiling
    assert "central proof verdicts" in ceiling
