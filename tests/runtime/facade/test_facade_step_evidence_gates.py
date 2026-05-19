from __future__ import annotations

import json

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def _world_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _route_state(entity_id: int) -> ef_py.ExecutionEpisodeState:
    state = ef_py.ExecutionEpisodeState()
    state.agent_id = int(entity_id)
    state.has_mission_command = True
    state.mission_command.command_code = 3
    state.mission_command.cmd_heading_deg = 90.0
    state.mission_command.cmd_altitude_m = 1200.0
    state.mission_command.cmd_speed_mps = 180.0
    state.mission_command.active = True
    state.has_mission_command_json = True
    state.mission_command_json = json.dumps(
        {
            "command_code": 3,
            "route_ref_id": int(entity_id),
            "target_altitude": 1200.0,
            "target_heading": 90.0,
            "target_speed": 180.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
            ],
        },
        ensure_ascii=True,
        sort_keys=True,
    )

    waypoint = ef_py.SpatialRouteWaypoint()
    waypoint.x_m = -1350.0
    waypoint.y_m = 0.0
    waypoint.z_m = 1200.0
    waypoint.radius_m = 1200.0
    waypoint.altitude_m = 1200.0
    waypoint.speed_mps = 180.0
    waypoint.waypoint_mode = "flyby"
    state.route_waypoints = [waypoint]

    state.has_post_waypoint_transition_json = True
    state.post_waypoint_transition_json = json.dumps(
        {
            "command_code": 2,
            "phase_name": "post_route",
            "target_altitude": 900.0,
            "target_heading": 45.0,
            "target_speed": 160.0,
            "transition_reward": 123.0,
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return state


def _route_step_request(entity_id: int) -> ef_py.WorldExecutionEpisodeStepRequest:
    request = ef_py.WorldExecutionEpisodeStepRequest()
    request.world_index = 0
    request.entity_id = int(entity_id)
    request.config = ef_py.StepEvaluationBatchConfig()
    request.env_state.steps = 1
    request.env_state.truth_x = -1400.0
    request.env_state.truth_y = 0.0
    request.env_state.truth_z = 1200.0
    request.env_state.truth_speed = 180.0
    request.env_state.has_safety = True
    request.env_state.safety.finite_state_valid = True
    request.env_state.safety.health = 100.0
    request.env_state.safety.survival_reward = 0.02
    request.env_state.has_waypoint = True
    request.env_state.waypoint.valid = True
    request.env_state.waypoint.waypoint_index = 0
    request.env_state.waypoint.waypoint_count = 1
    request.env_state.waypoint.dist_m = 50.0
    request.env_state.waypoint.waypoint_radius_m = 1200.0
    request.env_state.waypoint.has_prev_dist = True
    request.env_state.waypoint.prev_dist_m = 120.0
    request.env_state.waypoint.progress_weight = 0.1
    request.env_state.waypoint.distance_weight = -0.001
    request.env_state.waypoint.reached_bonus = 20.0
    return request


def test_execution_batch_step_result_semantic_shape_is_facade_visible() -> None:
    entity_id = 77
    facade = ef_py.RuntimeFacade(1)
    facade.prime_execution_episode_batch([_world_ref(0, entity_id)], [_route_state(entity_id)])

    request = ef_py.ExecutionBatchStepRequest()
    request.step_requests = [_route_step_request(entity_id)]
    request.include_agent_observations = False
    request.include_instrument_states = True

    result = facade.step_execution_batch(request)

    assert len(result.step_results) == 1
    assert len(result.rewards) == 1
    assert len(result.terminated) == 1
    assert len(result.truncated) == 1
    assert len(result.status_vectors) == 1
    assert len(result.termination_reasons) == 1
    assert len(result.reward_breakdown_jsons) == 1
    assert len(result.step_infos) == 1
    assert len(result.step_info_valid_flags) == 1
    assert len(result.controller_state_changed_flags) == 1

    step_result = result.step_results[0]
    assert bool(step_result.valid)
    assert result.rewards[0] == step_result.reward_total
    assert bool(result.terminated[0]) == bool(step_result.terminated)
    assert bool(result.truncated[0]) == bool(step_result.truncated)
    assert list(result.status_vectors[0]) == [
        step_result.status0,
        step_result.status1,
        step_result.status2,
        step_result.status3,
    ]
    assert result.termination_reasons[0] == step_result.controller_state.last_termination_reason
    assert result.reward_breakdown_jsons[0] == step_result.controller_state.last_reward_breakdown_json
    assert bool(result.controller_state_changed_flags[0]) == bool(step_result.structural_state_changed)

    reward_breakdown = json.loads(result.reward_breakdown_jsons[0])
    assert reward_breakdown["total"] == result.rewards[0]
    assert reward_breakdown["phase_transition_bonus"] == 123.0
    assert "waypoint_reached_bonus" in reward_breakdown
    assert "survival" in reward_breakdown

    assert result.termination_reasons[0] == "running"
    assert not bool(result.terminated[0])
    assert not bool(result.truncated[0])
    assert step_result.controller_state.mission_phase_name == "post_route"
    assert step_result.controller_state.step_count == 1

    assert [(int(ref.world_index), int(ref.entity_id)) for ref in result.observation_packet.refs] == [(0, entity_id)]
    assert len(result.observation_packet.agent_observations) == 0
    assert len(result.observation_packet.instrument_states) == 1
