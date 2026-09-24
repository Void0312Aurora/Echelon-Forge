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
    assert contract["native_runtime_surfaces"]["direct_fire"]["probe_entrypoint"] == "GroundInfantryNativeProbe.fire_from_mission_command"
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
    assert contract["native_runtime_surfaces"]["transition"]["status"] == "bounded_native_transition_probe"
    assert contract["native_runtime_surfaces"]["transition"]["entrypoint"] == "SimulationKernel.get_ground_transition_observation"
    assert contract["native_runtime_surfaces"]["transition"]["fields"] == [
        "configured",
        "passable",
        "destination_surface",
        "water_blocked",
        "obstacle_blocked",
        "bridge_admitted",
        "distance_m",
    ]
    assert contract["native_runtime_surfaces"]["transition"]["does_not_claim"] == [
        "route_graph",
        "waypoint_planning",
        "cover",
        "line_of_sight",
    ]
    assert contract["native_runtime_surfaces"]["transition_effects"]["status"] == "bounded_native_segment_movement_observation"
    assert contract["native_runtime_surfaces"]["transition_effects"]["entrypoint"] == "SimulationKernel.get_ground_transition_movement_observation"
    assert contract["native_runtime_surfaces"]["transition_effects"]["fields"] == [
        "configured",
        "passable",
        "destination_surface",
        "water_blocked",
        "obstacle_blocked",
        "bridge_admitted",
        "distance_m",
        "minimum_combined_multiplier",
        "average_combined_multiplier",
        "sample_count",
    ]
    assert contract["native_runtime_surfaces"]["terrain_effects"]["status"] == "bounded_native_observation"
    assert contract["native_runtime_surfaces"]["terrain_effects"]["entrypoint"] == "SimulationKernel.get_ground_movement_effect_observation"
    assert contract["native_runtime_surfaces"]["terrain_effects"]["fields"] == [
        "surface_type",
        "slope_deg",
        "vegetation_density",
        "surface_speed_multiplier",
        "slope_speed_multiplier",
        "vegetation_speed_multiplier",
        "stance_speed_multiplier",
        "combined_speed_multiplier",
    ]
    assert contract["native_runtime_surfaces"]["direct_sequence_validation"]["status"] == "bounded_native_read_only_validation"
    assert contract["native_runtime_surfaces"]["direct_sequence_validation"]["entrypoint"] == "GroundInfantryNativeProbe.validate_waypoint_sequence"
    assert contract["native_runtime_surfaces"]["direct_sequence_validation"]["fields"] == [
        "passable",
        "segment_count",
        "total_distance_m",
        "blocked_segment_index",
        "blocked_reason",
        "segment_observations",
    ]
    assert contract["native_runtime_surfaces"]["direct_sequence_validation"]["segment_movement_observation_fields"] == [
        "configured",
        "passable",
        "destination_surface",
        "water_blocked",
        "obstacle_blocked",
        "bridge_admitted",
        "distance_m",
        "minimum_combined_multiplier",
        "average_combined_multiplier",
        "sample_count",
    ]
    assert contract["native_runtime_surfaces"]["direct_sequence_validation"]["does_not_claim"] == [
        "route_graph",
        "path_planning",
        "cover",
        "line_of_sight",
    ]
    assert contract["map_profile"]["arnis_bundle_status"] == "verified_export_snapshot"
    assert contract["map_profile"]["companion_overlay"] == "field_overlay.v1"
    assert contract["map_profile"]["runtime_consumption"].startswith("held_until_")
    assert contract["action_space"]["status"] == "bounded_native_probe_and_proxy"
    assert contract["action_space"]["native_status"] == "implemented_in_native_probe_only"
    assert contract["action_space"]["native_action_fields"] == [
        "heading_normalized",
        "speed_fraction",
        "stance_normalized",
    ]
    assert contract["action_space"]["native_route_intent"] == "direct_only_metadata"
    assert contract["action_space"]["replay_entrypoint"] == "GroundInfantryNativeProbe.replay"
    assert contract["rl_harness"]["status"] == "non_production_proxy_and_native_probe"
    assert contract["rl_harness"]["authority"] == "native_probe_only_for_native_entrypoint"
    assert contract["rl_harness"]["native_probe"]["status"] == "native_probe_only"
    assert contract["rl_harness"]["native_probe"]["entrypoint"] == "python.rl.ground.native_probe:GroundInfantryNativeProbe"
    assert contract["rl_harness"]["native_probe"]["production_boundary"] == "not_world_batch"
    assert contract["rl_harness"]["native_probe"]["waypoint_boundary"] == "fixed_direct_sequence_only"
    assert contract["rl_harness"]["native_env"]["status"] == "native_probe_only"
    assert contract["rl_harness"]["native_env"]["entrypoint"] == "python.rl.ground.native_env:GroundInfantryNativeEnv"
    assert contract["rl_harness"]["native_env"]["production_boundary"] == "not_world_batch"
    assert contract["rl_harness"]["native_env"]["observation_bounds"] == "finite_source_backed_fixture_or_probe_horizon"
    assert contract["rl_harness"]["native_env"]["action_boundary"] == "normalized_heading_speed_stance_with_direct_route_metadata"
    assert "mission_state" in contract["rl_harness"]["native_env"]["observation_fields"]
    assert "waypoint_state" in contract["rl_harness"]["native_env"]["observation_fields"]
    assert contract["rl_harness"]["native_env"]["truncation_reasons"] == [
        "max_steps",
        "blocked_step_limit",
    ]
    assert contract["rl_harness"]["native_env"]["waypoint_boundary"] == "fixed_direct_sequence_only"
    assert "command_state" in contract["rl_harness"]["native_env"]["observation_fields"]
    assert "health_state" in contract["rl_harness"]["native_env"]["observation_fields"]
    assert contract["command_projection"]["status"] == "partial_transport_only"
    assert contract["command_projection"]["representable_fields"][-1] == "ground_static_task_mode"
    assert contract["command_projection"]["held_fields"] == ["route_intent"]
    assert contract["observation_space"]["status"] == "bounded_native_probe_and_proxy"
    assert contract["observation_space"]["proxy_status"] == "implemented_in_engineering_proxy_only"
    assert contract["observation_space"]["native_status"] == "implemented_in_native_probe_only"
    assert [stage["stage"] for stage in contract["curriculum"]] == [
        "S0_contract_and_reset",
        "S1_flat_waypoint",
        "S2_terrain_cost",
        "S3_tree_line_and_settlement_observation",
        "S4_team_transition",
    ]
    assert contract["termination"]["fail_closed_on_missing_semantics"] is True
    assert contract["reward"]["status"] == "bounded_native_probe_and_proxy"
    assert contract["reward"]["native_terms"] == ["distance_delta_to_waypoint", "blocked_attempt_penalty"]
    assert "same seed produces byte-equivalent reset observation" in contract["acceptance_gates"]
