from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from python.tasking_contracts.air.tasking.c2_policy import (
    C2TransitionInput,
    ScriptedC2TransitionPolicy,
    TASK_CAP,
    TASK_RECOVER_LAND,
    TASK_RTB,
    TASK_SCRAMBLE,
)
from python.tasking_contracts.air.tasking.c2_manager import ScriptedC2TaskManager


def _state(**overrides):
    base = C2TransitionInput(
        current_task_name=TASK_SCRAMBLE,
        sim_time_s=0.0,
        altitude_agl_m=0.0,
        ground_speed_mps=0.0,
        station_entry_time_s=None,
        on_station_time_s=30.0,
        near_station=False,
        report_type=0,
        report_valid=False,
        report_reason="",
        rep_rtb_type=3,
        warn_bingo_type=4,
        rep_unable_type=5,
        route_exhausted=False,
        recovery_ready=False,
        scramble_complete_alt_agl_m=120.0,
        scramble_complete_ground_speed_mps=65.0,
        auto_rtb_on_station_complete=True,
    )
    return replace(base, **overrides)


def test_scramble_transition_is_threshold_based() -> None:
    result = ScriptedC2TransitionPolicy().decide(
        _state(altitude_agl_m=120.0, ground_speed_mps=65.0)
    )
    assert result.task_name == TASK_CAP
    assert result.transitioned is True
    assert result.reason == "scramble_complete"


def test_cap_station_timer_and_report_transitions_are_explicit() -> None:
    policy = ScriptedC2TransitionPolicy()
    entered = policy.decide(_state(current_task_name=TASK_CAP, sim_time_s=10.0, near_station=True))
    assert entered.task_name == TASK_CAP
    assert entered.station_entry_time_s == 10.0

    timed = policy.decide(
        _state(
            current_task_name=TASK_CAP,
            sim_time_s=40.0,
            station_entry_time_s=10.0,
            near_station=True,
        )
    )
    assert timed.task_name == TASK_RTB
    assert timed.reason == "station_time_complete"

    reported = policy.decide(
        _state(
            current_task_name=TASK_CAP,
            report_type=3,
            report_valid=True,
            report_reason="rtb_report",
        )
    )
    assert reported.task_name == TASK_RTB
    assert reported.reason == "rtb_report"


def test_recovery_route_exhaustion_precedes_window_gate() -> None:
    result = ScriptedC2TransitionPolicy().decide(
        _state(
            current_task_name=TASK_RTB,
            report_type=3,
            report_valid=True,
            recovery_ready=False,
            route_exhausted=True,
        )
    )
    assert result.task_name == TASK_RECOVER_LAND
    assert result.reason == "route_exhausted_recovery_final"


def test_recovery_window_requires_report_and_geometry_readiness() -> None:
    policy = ScriptedC2TransitionPolicy()
    blocked = policy.decide(
        _state(current_task_name=TASK_RTB, report_type=3, report_valid=True, recovery_ready=False)
    )
    assert blocked.task_name == TASK_RTB

    admitted = policy.decide(
        _state(current_task_name=TASK_RTB, report_type=3, report_valid=True, recovery_ready=True)
    )
    assert admitted.task_name == TASK_RECOVER_LAND
    assert admitted.reason == "recovery_window_open"


def test_malformed_post_transition_command_does_not_become_landing() -> None:
    malformed = SimpleNamespace(post_waypoint_transition={"command_code": "not-a-command"})

    assert ScriptedC2TaskManager._landing_post_transition_pending(malformed) is False


def test_c2_task_name_validation_rejects_unknown_policy_output() -> None:
    with pytest.raises(ValueError, match="unknown task name"):
        ScriptedC2TaskManager._validate_task_name("TASK_INTERCEPT")
