from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UNIT = REPO_ROOT / "examples" / "config" / "database" / "ground" / "units" / "ground_infantry_soldier_mvp.json"
CONTRACT = REPO_ROOT / "examples" / "config" / "training" / "active" / "ground" / "eastern_plain_infantry_single_v1.contract.json"


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, dict)
    return value


def test_ground_infantry_unit_is_an_individual_native_ground_schema() -> None:
    unit = _load(UNIT)
    schema = unit["_ground_schema"]

    assert unit["name"] == "Ground_Infantry_Soldier_MVP"
    assert unit["type"] == "Ground"
    assert schema["service_profile"] == "Army"
    assert schema["tasking_profile"] == "ground"
    assert schema["echelon"] == "individual"
    assert schema["platform_family"] == "dismounted_infantry"
    assert unit["_training_boundary"]["weapon_employment"] == "not_in_this_slice"
    assert unit["_training_boundary"]["runtime_status"] == "schema_and_contract_only"
    assert any("passability" in claim for claim in unit["_deferred_runtime_claims"])


def test_single_infantry_contract_is_staged_before_runtime_training_entry() -> None:
    contract = _load(CONTRACT)

    assert contract["contract_version"] == "ground_infantry_training.v1"
    assert contract["status"] == "contract_only"
    assert contract["safety_boundary"]["weapon_employment"] is False
    assert contract["agent"]["count"] == 1
    assert contract["map_profile"]["arnis_bundle_status"] == "verified_export_snapshot"
    assert contract["map_profile"]["companion_overlay"] == "field_overlay.v1"
    assert contract["map_profile"]["runtime_consumption"].startswith("held_until_")
    assert contract["rl_harness"]["status"] == "proxy_only"
    assert contract["rl_harness"]["authority"] == "engineering_proxy_only"
    assert [stage["stage"] for stage in contract["curriculum"]] == [
        "S0_contract_and_reset",
        "S1_flat_waypoint",
        "S2_terrain_cost",
        "S3_tree_line_and_settlement_observation",
        "S4_team_transition",
    ]
    assert contract["termination"]["fail_closed_on_missing_semantics"] is True
    assert "same seed produces byte-equivalent reset observation" in contract["acceptance_gates"]
