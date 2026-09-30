from __future__ import annotations

import pytest

from python.tasking_contracts.air.tasking.leader_approach_policy import (
    LeaderApproachInput,
    ScriptedLeaderApproachPolicy,
)


def _state(**overrides: object) -> LeaderApproachInput:
    values: dict[str, object] = {
        "post_transition_pending": True,
        "c2_task_allows_approach": True,
        "c2_recovery_task": False,
        "current_command_code": 0,
        "post_transition_command_code": 4,
        "remaining_waypoints": 2,
        "terminal_waypoint_count": 2,
        "post_transition_ready": False,
        "altitude_agl_m": 900.0,
        "rollout_alt_agl_m": 5.0,
        "max_altitude_agl_m": 1400.0,
        "ils_valid": True,
        "dme_m": 9000.0,
        "max_dme_m": 12000.0,
        "localizer_abs": 0.2,
        "max_localizer_abs": 0.55,
        "glide_slope_abs": 0.4,
        "max_glide_slope_abs": 1.25,
        "runway_heading_error_deg": 10.0,
        "max_runway_heading_error_deg": 45.0,
        "runway_frame_valid": True,
        "require_runway_frame": True,
        "runway_along_m": 0.0,
        "min_runway_along_m": -1000.0,
        "runway_cross_m": 100.0,
        "max_runway_cross_abs_m": 3500.0,
    }
    values.update(overrides)
    return LeaderApproachInput(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"post_transition_pending": False},
        {"c2_task_allows_approach": False},
        {"current_command_code": 4},
        {"post_transition_command_code": 2},
        {"remaining_waypoints": 3},
        {"altitude_agl_m": 1500.0},
        {"ils_valid": False},
        {"dme_m": 13000.0},
        {"localizer_abs": 0.8},
        {"glide_slope_abs": 1.5},
        {"runway_heading_error_deg": 50.0},
        {"runway_frame_valid": False},
        {"runway_along_m": -1200.0},
        {"runway_cross_m": 3600.0},
    ],
)
def test_scripted_approach_policy_fails_closed_for_invalid_geometry(overrides: dict[str, object]) -> None:
    assert not ScriptedLeaderApproachPolicy().decide(_state(**overrides)).arm


def test_scripted_approach_policy_accepts_terminal_geometry() -> None:
    assert ScriptedLeaderApproachPolicy().decide(_state()).arm


def test_scripted_approach_policy_uses_explicit_recovery_transition_readiness() -> None:
    assert not ScriptedLeaderApproachPolicy().decide(
        _state(c2_recovery_task=True, remaining_waypoints=0, post_transition_ready=False)
    ).arm
    assert ScriptedLeaderApproachPolicy().decide(
        _state(c2_recovery_task=True, remaining_waypoints=0, post_transition_ready=True)
    ).arm
