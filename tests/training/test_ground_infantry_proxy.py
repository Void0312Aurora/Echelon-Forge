from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.ground import (
    GroundFieldProxy,
    GroundInfantryProxyEnv,
    GroundInfantryProxyError,
    build_ground_infantry_command,
    build_ground_infantry_maintained_assignment,
    build_ground_infantry_mission_command,
    normalize_ground_infantry_action,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
)


def _proxy() -> GroundFieldProxy:
    return GroundFieldProxy.from_fixture(FIXTURE)


def test_ground_action_vector_is_normalized_without_hidden_air_fields() -> None:
    action = normalize_ground_infantry_action([450.0, 2.0, 1.8, 3.2])

    assert action.desired_heading_deg == 90.0
    assert action.desired_speed_fraction == 1.0
    assert action.stance == "prone"
    assert action.route_intent == "cross_bridge"
    assert action.vector() == (90.0, 1.0, 2.0, 3.0)

    command = build_ground_infantry_command(action, entity_id=17)
    assert command == {
        "contract_version": "ground_infantry_proxy.v1",
        "command_kind": "ground_infantry_step_v1",
        "entity_id": 17,
        "active": True,
        "desired_heading_deg": 90.0,
        "desired_speed_fraction": 1.0,
        "stance": "prone",
        "route_intent": "cross_bridge",
        "authority": "engineering_proxy_only",
    }


def test_ground_action_rejects_wrong_shape() -> None:
    with pytest.raises(GroundInfantryProxyError, match="expects four values"):
        normalize_ground_infantry_action([0.0, 1.0])


def test_representable_ground_action_projects_to_native_command_and_batch_slice() -> None:
    command = build_ground_infantry_mission_command(
        [90.0, 0.5, 0.0, 0.0],
        max_speed_mps=2.0,
        objective_area_id=41,
        objective_node_id=42,
        ground_commander_id=43,
    )

    assert bool(command.active) is True
    assert float(command.cmd_heading_deg) == 90.0
    assert float(command.cmd_speed_mps) == 1.0
    assert command.ground_task_mode == ef_py.GroundTaskMode.MoveStatic
    assert command.ground_stance == ef_py.GroundStance.Stand
    assert int(command.objective_node_id) == 42

    assignment = build_ground_infantry_maintained_assignment(
        [90.0, 0.5, 0.0, 0.0],
        world_index=3,
        entity_id=17,
        objective_node_id=42,
    )
    assert int(assignment.world_index) == 3
    assert int(assignment.entity_id) == 17
    assert (
        assignment.mission_command.ground_static_task.ground_task_mode
        == ef_py.GroundTaskMode.MoveStatic
    )
    assert assignment.mission_command.ground_static_task.ground_stance == ef_py.GroundStance.Stand
    assert int(assignment.mission_command.ground_static_task.objective_node_id) == 42


def test_native_command_projection_supports_bounded_static_hold_tasks() -> None:
    for mode, expected in (
        ("occupy_static", ef_py.GroundTaskMode.OccupyStatic),
        ("support_static", ef_py.GroundTaskMode.SupportStatic),
    ):
        command = build_ground_infantry_mission_command(
            [90.0, 1.0, 2.0, 0.0], ground_task_mode=mode
        )
        assert command.ground_task_mode == expected
        assert float(command.cmd_speed_mps) == 0.0
        assert command.ground_stance == ef_py.GroundStance.Prone


def test_native_command_projection_rejects_unrepresentable_tactical_fields() -> None:
    crouched = build_ground_infantry_mission_command([0.0, 1.0, 1.0, 0.0])
    assert crouched.ground_stance == ef_py.GroundStance.Crouch
    with pytest.raises(GroundInfantryProxyError, match="cannot represent route_intent"):
        build_ground_infantry_mission_command([0.0, 1.0, 0.0, 3.0])


def test_proxy_loads_frozen_lineage_and_exposes_explicit_terrain_provenance() -> None:
    proxy = _proxy()

    sample = proxy.sample(400.0, 100.0)

    assert proxy.acceptance["valid"] is True
    assert sample.known is True
    assert sample.landcover_label in {"grassland", "cropland"}
    assert sample.elevation_m is not None
    assert sample.slope_deg is not None
    assert sample.provenance == "arnis_bundle_plus_field_overlay"

    context = proxy.semantic_context(400.0, 100.0)
    assert context["authority"] == "engineering_proxy_only"
    assert context["nearest_tree_line_distance_and_bearing"][0] >= 0.0
    assert context["nearest_settlement_distance_and_bearing"][0] >= 0.0
    assert context["river_active"] is False


def test_proxy_observation_keeps_last_route_intent_and_bridge_semantics() -> None:
    proxy = _proxy()
    state = proxy.reset(x_m=820.0, y_m=667.0)

    transition = proxy.step(state, [90.0, 1.0, 0.0, 3.0], dt_s=1.0)

    assert transition.observation["route_intent"] == "cross_bridge"
    assert transition.observation["semantic_context"]["bridge_active"] is True


def test_proxy_step_is_deterministic_and_replayable() -> None:
    actions = [
        [0.0, 0.5, 0.0, 0.0],
        [90.0, 0.75, 1.0, 1.0],
        [-90.0, 0.25, 2.0, 2.0],
    ]

    def run() -> list[dict]:
        proxy = _proxy()
        state = proxy.reset(x_m=400.0, y_m=100.0)
        traces = []
        for action in actions:
            transition = proxy.step(state, action)
            traces.append(transition.trace)
            state = transition.state
        return traces

    first = run()
    second = run()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_direct_river_crossing_is_blocked_without_advancing_position() -> None:
    proxy = _proxy()
    state = proxy.reset(x_m=820.0, y_m=667.0)

    transition = proxy.step(
        state,
        {
            "desired_heading_deg": 90.0,
            "desired_speed_fraction": 1.0,
            "stance": "stand",
            "route_intent": "direct",
        },
        dt_s=30.0,
    )

    assert transition.blocked is True
    assert transition.blocked_reason == "river_crossing_requires_bridge_intent"
    assert transition.moved_distance_m == 0.0
    assert (transition.state.x_m, transition.state.y_m) == (state.x_m, state.y_m)
    assert transition.state.step_index == state.step_index + 1
    assert transition.state.sim_time_s == state.sim_time_s + 30.0


def test_bridge_intent_is_the_only_proxy_admission_for_crossing() -> None:
    proxy = _proxy()
    state = proxy.reset(x_m=820.0, y_m=667.0)

    transition = proxy.step(
        state,
        [90.0, 1.0, 0.0, 3.0],
        dt_s=30.0,
    )

    assert transition.blocked is False
    assert transition.blocked_reason is None
    assert transition.moved_distance_m > 0.0
    assert transition.state.x_m > state.x_m
    assert "bridge_crossing" in transition.terrain.semantic_kinds


def test_unknown_or_outside_terrain_fails_closed() -> None:
    proxy = _proxy()
    state = proxy.reset(x_m=400.0, y_m=100.0)

    transition = proxy.step(state, [0.0, 1.0, 0.0, 0.0], dt_s=2000.0)

    assert transition.blocked is True
    assert transition.blocked_reason == "outside_map_extent"
    assert transition.moved_distance_m == 0.0
    assert transition.observation["unknown_value_policy"] == "explicit_unknown_with_provenance"


def test_proxy_gym_reset_is_seed_stable_and_emits_fixed_observation_contract() -> None:
    first_env = GroundInfantryProxyEnv(_proxy(), max_steps=4)
    second_env = GroundInfantryProxyEnv(_proxy(), max_steps=4)

    first_obs, first_info = first_env.reset(seed=42)
    second_obs, second_info = second_env.reset(seed=42)

    assert first_env.action_space.shape == (4,)
    assert first_env.observation_space.contains(first_obs)
    assert first_info["authority"] == "engineering_proxy_only"
    assert second_info["authority"] == "engineering_proxy_only"
    for key in first_obs:
        assert (first_obs[key] == second_obs[key]).all()


def test_proxy_gym_step_exposes_blocking_and_replay_trace_without_native_claim() -> None:
    env = GroundInfantryProxyEnv(
        _proxy(),
        start_xy_m=(820.0, 667.0),
        goal_xy_m=(1000.0, 667.0),
        blocked_step_limit=2,
    )
    observation, _info = env.reset(seed=7)
    assert env.observation_space.contains(observation)

    _observation, reward, terminated, truncated, info = env.step(
        [90.0, 1.0, 0.0, 0.0]
    )

    assert reward < 0.0
    assert terminated is False
    assert truncated is False
    assert info["blocked"] is True
    assert info["blocked_reason"] == "river_crossing_requires_bridge_intent"
    assert info["authority"] == "engineering_proxy_only"
    assert len(env.trace) == 1
