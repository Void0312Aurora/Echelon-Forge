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
    assert unit["_training_boundary"]["weapon_employment"] == "bounded_native_direct_fire_v1"
    assert unit["_training_boundary"]["runtime_status"] == "native_single_step_contract"
    assert any("passability" in claim for claim in unit["_deferred_runtime_claims"])


def test_single_infantry_contract_is_staged_before_runtime_training_entry() -> None:
    contract = _load(CONTRACT)

    assert contract["contract_version"] == "ground_infantry_training.v1"
    assert contract["status"] == "contract_only"
    assert contract["safety_boundary"]["weapon_employment"] is False
    assert contract["agent"]["count"] == 1
    assert contract["native_runtime_surfaces"]["direct_fire"]["status"] == "bounded_native_probe"
    assert contract["native_runtime_surfaces"]["direct_fire"]["entrypoint"] == "SimulationKernel.fire_ground_weapon"
    assert contract["native_runtime_surfaces"]["direct_fire"]["command_entrypoint"] == "SimulationKernel.fire_ground_weapon_from_mission_command"
    assert contract["native_runtime_surfaces"]["direct_fire"]["observation_entrypoint"] == "SimulationKernel.get_ground_weapon_state"
    assert contract["native_runtime_surfaces"]["direct_fire"]["observation_fields"] == [
        "present",
        "selected_type",
        "ammunition",
        "maximum_ammunition",
        "damage_per_hit",
        "engagement_range_m",
        "hit_probability",
        "cooldown_remaining",
    ]
    assert contract["native_runtime_surfaces"]["field_semantics"]["status"] == "bounded_metadata_observation"
    assert contract["native_runtime_surfaces"]["field_semantics"]["load_entrypoint"] == "SimulationKernel.load_arnis_field_overlay"
    assert contract["native_runtime_surfaces"]["field_semantics"]["entrypoint"] == "SimulationKernel.get_ground_field_semantic_observation"
    assert contract["native_runtime_surfaces"]["field_semantics"]["fields"] == [
        "configured",
        "tree_distance_m",
        "tree_bearing_deg",
        "settlement_distance_m",
        "settlement_bearing_deg",
        "in_tree_line",
        "in_settlement",
    ]
    assert contract["map_profile"]["arnis_bundle_status"] == "verified_export_snapshot"
    assert contract["map_profile"]["companion_overlay"] == "field_overlay.v1"
    assert contract["map_profile"]["runtime_consumption"].startswith("held_until_")
    assert contract["rl_harness"]["status"] == "proxy_only"
    assert contract["rl_harness"]["authority"] == "engineering_proxy_only"
    assert contract["rl_harness"]["native_probe"]["status"] == "native_probe_only"
    assert contract["rl_harness"]["native_probe"]["entrypoint"] == "python.rl.ground.native_probe:GroundInfantryNativeProbe"
    assert contract["rl_harness"]["native_probe"]["production_boundary"] == "not_world_batch"
    assert contract["command_projection"]["status"] == "partial_transport_only"
    assert contract["command_projection"]["held_fields"] == ["route_intent"]
    assert contract["observation_space"]["proxy_status"] == "implemented_in_engineering_proxy_only"
    assert [stage["stage"] for stage in contract["curriculum"]] == [
        "S0_contract_and_reset",
        "S1_flat_waypoint",
        "S2_terrain_cost",
        "S3_tree_line_and_settlement_observation",
        "S4_team_transition",
    ]
    assert contract["termination"]["fail_closed_on_missing_semantics"] is True
    assert "same seed produces byte-equivalent reset observation" in contract["acceptance_gates"]
