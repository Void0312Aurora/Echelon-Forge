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


def test_step_execution_batch_populates_typed_reward_and_termination_reports() -> None:
    entity_id = 77
    facade = ef_py.RuntimeFacade(1)
    facade.prime_execution_episode_batch([_world_ref(0, entity_id)], [_route_state(entity_id)])

    request = ef_py.ExecutionBatchStepRequest()
    request.step_requests = [_route_step_request(entity_id)]
    request.include_agent_observations = False
    request.include_instrument_states = True

    result = facade.step_execution_batch(request)

    assert len(result.reward_reports) == 1
    assert len(result.termination_specs) == 1

    reward_report = result.reward_reports[0]
    termination_spec = result.termination_specs[0]

    assert reward_report.term_owner == "split"
    assert int(reward_report.fact_snapshot_version) == 1
    assert [term.name for term in reward_report.fact_terms]
    assert [term.name for term in reward_report.shaping_terms]
    assert all(term.term_owner == "simulation" for term in reward_report.fact_terms)
    assert any(term.term_owner == "experiment" for term in reward_report.shaping_terms)
    assert any(term.name == "reward_total" for term in reward_report.shaping_terms)

    assert termination_spec.reason == result.termination_reasons[0]
    assert termination_spec.reason_source == "policy"
    assert int(termination_spec.snapshot_version) == 1


def test_step_execution_batch_preserves_compatibility_reward_strings_alongside_typed_reports() -> None:
    entity_id = 91
    facade = ef_py.RuntimeFacade(1)
    facade.prime_execution_episode_batch([_world_ref(0, entity_id)], [_route_state(entity_id)])

    request = ef_py.ExecutionBatchStepRequest()
    request.step_requests = [_route_step_request(entity_id)]
    request.include_agent_observations = False

    result = facade.step_execution_batch(request)

    assert len(result.reward_breakdown_jsons) == 1
    assert len(result.reward_reports) == 1

    reward_breakdown = json.loads(result.reward_breakdown_jsons[0])
    assert reward_breakdown["total"] == result.rewards[0]
    assert reward_breakdown["phase_transition_bonus"] == 123.0
    assert any(term.name == "reward_total" for term in result.reward_reports[0].shaping_terms)


def test_observation_packet_export_populates_provenance_metadata() -> None:
    facade = ef_py.RuntimeFacade(1)
    ref = _world_ref(0, 1234)

    packet = facade.export_observation_packet([ref])

    assert int(packet.snapshot_version) == 1
    assert packet.barrier_id == "export"
    assert float(packet.source_time_s) >= 0.0
    assert packet.provenance.information_state_layer == "AgentObservation"
    assert packet.provenance.source_label == "facade_observation_packet"
    assert packet.provenance.maintained_status == "maintained"
    assert list(packet.provenance.observation_packet_ids) == ["obs:1"]
    assert list(packet.provenance.source_observation_versions) == ["global:1"]
    assert [(int(item.world_index), int(item.entity_id)) for item in packet.refs] == [(0, 1234)]


def test_step_execution_batch_observation_packet_exposes_metadata() -> None:
    entity_id = 131
    facade = ef_py.RuntimeFacade(1)
    facade.prime_execution_episode_batch([_world_ref(0, entity_id)], [_route_state(entity_id)])

    request = ef_py.ExecutionBatchStepRequest()
    request.step_requests = [_route_step_request(entity_id)]
    request.include_agent_observations = False
    request.include_instrument_states = True

    result = facade.step_execution_batch(request)

    assert int(result.observation_packet.snapshot_version) == 1
    assert result.observation_packet.barrier_id == "export"
    assert float(result.observation_packet.source_time_s) >= 0.0
    assert result.observation_packet.provenance.maintained_status == "maintained"
    assert result.observation_packet.provenance.information_state_layer == "AgentObservation"
    assert len(result.observation_packet.instrument_states) == 1


def test_observation_view_spec_compatibility_major_minor_rules_are_exercised_from_python() -> None:
    checkpoint = ef_py.ObservationViewSpec()
    checkpoint.schema_version = "1.0"
    checkpoint.required_fields = ["pose", "health"]
    checkpoint.optional_fields = ["legacy_heading_raw"]

    provider_minor = ef_py.ObservationViewSpec()
    provider_minor.schema_version = "1.3"
    provider_minor.required_fields = ["pose", "health"]
    provider_minor.optional_fields = ["radar_altitude"]

    provider_major = ef_py.ObservationViewSpec()
    provider_major.schema_version = "2.0"
    provider_major.required_fields = ["pose", "health"]

    minor_report = ef_py.evaluate_observation_view_checkpoint_compatibility(
        checkpoint,
        provider_minor,
    )
    major_report = ef_py.evaluate_observation_view_checkpoint_compatibility(
        checkpoint,
        provider_major,
    )

    assert bool(minor_report.compatible)
    assert bool(minor_report.major_compatible)
    assert not bool(major_report.compatible)
    assert not bool(major_report.major_compatible)
