from __future__ import annotations

from types import SimpleNamespace

import ef_py

from python.simulation.air.director import AirDirectorInput, AirScriptedDirector
from python.tasking_contracts.air.tasking.leader_approach_policy import LeaderApproachInput


def _state(*, alt_radar: float, ground_speed: float, command_code: int, remaining: int, total: int):
    return AirDirectorInput(
        entity_id=581,
        sim_time_s=12.5,
        observation=SimpleNamespace(x=10.0, y=20.0, z=1200.0),
        instruments=SimpleNamespace(alt_radar=alt_radar, ground_speed=ground_speed),
        mission_command=SimpleNamespace(
            command_code=command_code,
            cmd_heading_deg=90.0,
            cmd_altitude_m=1500.0,
            cmd_speed_mps=200.0,
        ),
        remaining_waypoints=remaining,
        waypoint_count=total,
        ils=(1.0, 0.0, 0.0, 9000.0),
    )


def test_direct_air_director_emits_scramble_chain_without_rl() -> None:
    decision = AirScriptedDirector().decide(
        _state(alt_radar=0.0, ground_speed=0.0, command_code=1, remaining=3, total=3)
    )

    assert decision.phase_name == "scramble"
    assert decision.task_order.assignee_id == 581
    assert decision.leader_intent.phase_id == ef_py.LeaderPhase.Scramble
    assert decision.pilot_report.report_type == ef_py.CommMsgType.REP_WILCO
    assert decision.mission_command.command_code == decision.leader_intent.command_code


def test_direct_air_director_reaches_route_and_landing_phase_from_native_facts() -> None:
    director = AirScriptedDirector(terminal_waypoint_count=2)
    departure = director.decide(
        _state(alt_radar=120.0, ground_speed=90.0, command_code=1, remaining=3, total=3)
    )
    assert departure.phase_name == "departure"
    assert departure.leader_intent.command_code == 1

    landing = director.decide(
        _state(alt_radar=100.0, ground_speed=75.0, command_code=4, remaining=0, total=0)
    )
    assert landing.phase_name == "landing_final"
    assert landing.leader_intent.commit_to_land is True
    assert landing.pilot_report.report_type == ef_py.CommMsgType.REP_RTB


def test_direct_air_director_consumes_explicit_approach_gate() -> None:
    state = _state(alt_radar=900.0, ground_speed=84.0, command_code=3, remaining=0, total=2)
    state = AirDirectorInput(
        **{**state.__dict__, "approach_facts": LeaderApproachInput(
            post_transition_pending=True,
            c2_task_allows_approach=True,
            c2_recovery_task=True,
            current_command_code=3,
            post_transition_command_code=4,
            remaining_waypoints=0,
            terminal_waypoint_count=2,
            post_transition_ready=True,
            altitude_agl_m=900.0,
            rollout_alt_agl_m=5.0,
            max_altitude_agl_m=1400.0,
            ils_valid=True,
            dme_m=9000.0,
            max_dme_m=12000.0,
            localizer_abs=0.18,
            max_localizer_abs=0.55,
            glide_slope_abs=0.22,
            max_glide_slope_abs=1.25,
            runway_heading_error_deg=4.0,
            max_runway_heading_error_deg=45.0,
            runway_frame_valid=True,
            require_runway_frame=True,
            runway_along_m=-600.0,
            min_runway_along_m=-1000.0,
            runway_cross_m=100.0,
            max_runway_cross_abs_m=3500.0,
        )}
    )
    decision = AirScriptedDirector().decide(state)
    assert decision.phase_name == "approach_armed"
    assert decision.mission_command.command_code == 4


def test_direct_air_director_preserves_declared_authority_and_target_fields() -> None:
    state = _state(alt_radar=1200.0, ground_speed=180.0, command_code=2, remaining=0, total=0)
    state = AirDirectorInput(
        **{
            **state.__dict__,
            "mission_command": SimpleNamespace(
                command_code=2,
                cmd_heading_deg=90.0,
                cmd_altitude_m=1500.0,
                cmd_speed_mps=200.0,
                roe_state=3,
                authorization_to_fire=True,
                assigned_target_id=9002,
                assigned_target_track_id=7002,
                assigned_target_source_id=581,
                assigned_target_snapshot_time_s=12.5,
                engagement_authority_holder_id=581,
                engagement_authority_grantor_id=100,
                task_group_id=17,
                objective_node_id=42,
                objective_area_id=9,
                threat_state=4,
            ),
        }
    )

    decision = AirScriptedDirector().decide(state)

    leader_fields = (
        "roe_state",
        "authorization_to_fire",
        "assigned_target_id",
        "assigned_target_track_id",
        "assigned_target_source_id",
        "assigned_target_snapshot_time_s",
        "engagement_authority_holder_id",
        "engagement_authority_grantor_id",
        "task_group_id",
        "objective_node_id",
        "objective_area_id",
        "threat_state",
    )
    for name in leader_fields:
        assert getattr(decision.leader_intent, name) == getattr(state.mission_command, name)
    for name in (
        "roe_state",
        "authorization_to_fire",
        "assigned_target_id",
        "assigned_target_track_id",
        "assigned_target_source_id",
        "assigned_target_snapshot_time_s",
        "engagement_authority_holder_id",
        "engagement_authority_grantor_id",
        "objective_node_id",
        "objective_area_id",
        "threat_state",
    ):
        assert getattr(decision.leader_intent, name) == getattr(decision.mission_command, name)
    assert decision.task_order.task_group_id == 17
    assert decision.pilot_report.task_group_id == 17
    assert decision.leader_intent.authorization_to_fire is True
    assert decision.mission_command.assigned_target_id == 9002


def test_direct_air_director_preserves_incoming_task_identity_metadata() -> None:
    source = ef_py.TaskOrder()
    source.task_id = 91
    source.issuer_id = 7001
    source.priority = 8
    source.package_id = 5101
    source.element_id = 5201
    source.task_group_id = 5301
    source.recovery_base_id = 5401
    source.recovery_runway_id = 5402
    state = AirDirectorInput(
        **{
            **_state(alt_radar=1200.0, ground_speed=180.0, command_code=2, remaining=0, total=0).__dict__,
            "task_order": source,
        }
    )

    decision = AirScriptedDirector().decide(state)

    for name in (
        "task_id",
        "issuer_id",
        "priority",
        "package_id",
        "element_id",
        "task_group_id",
        "recovery_base_id",
        "recovery_runway_id",
    ):
        assert getattr(decision.task_order, name) == getattr(source, name)
