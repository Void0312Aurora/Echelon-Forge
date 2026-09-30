from __future__ import annotations

import pytest

from python.tasking_contracts.air.tasking.leader_phase_policy import (
    LeaderPhaseInput,
    ScriptedLeaderPhasePolicy,
)


def _state(**overrides: object) -> LeaderPhaseInput:
    values: dict[str, object] = {
        "command_code": 0,
        "on_ground": False,
        "ground_speed_mps": 120.0,
        "altitude_agl_m": 1000.0,
        "dme_m": 8000.0,
        "remaining_waypoints": 5,
        "total_waypoints": 5,
        "terminal_waypoint_count": 2,
        "scramble_ground_speed_max_mps": 15.0,
        "departure_route_alt_agl_m": 140.0,
        "landing_final_dme_m": 3500.0,
        "landing_final_alt_agl_m": 140.0,
    }
    values.update(overrides)
    return LeaderPhaseInput(**values)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"on_ground": True, "ground_speed_mps": 5.0}, "scramble"),
        ({"on_ground": True, "ground_speed_mps": 40.0}, "takeoff"),
        ({"remaining_waypoints": 5, "total_waypoints": 5, "altitude_agl_m": 100.0}, "departure"),
        ({"remaining_waypoints": 5, "total_waypoints": 5, "altitude_agl_m": 500.0}, "transit_to_station"),
        ({"remaining_waypoints": 2}, "rtb"),
        ({"command_code": 4, "dme_m": 5000.0, "altitude_agl_m": 500.0}, "approach_armed"),
        ({"command_code": 4, "dme_m": 3000.0, "altitude_agl_m": 500.0}, "landing_final"),
        ({"command_code": 4, "on_ground": True, "altitude_agl_m": 0.0}, "rollout"),
    ],
)
def test_scripted_phase_policy_selects_the_declared_phase(overrides: dict[str, object], expected: str) -> None:
    decision = ScriptedLeaderPhasePolicy().decide(_state(**overrides))
    assert decision.phase_name == expected


def test_scripted_phase_policy_keeps_terminal_route_boundary_at_rtb() -> None:
    decision = ScriptedLeaderPhasePolicy().decide(
        _state(remaining_waypoints=1, total_waypoints=5, altitude_agl_m=100.0)
    )
    assert decision.phase_name == "rtb"
