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
