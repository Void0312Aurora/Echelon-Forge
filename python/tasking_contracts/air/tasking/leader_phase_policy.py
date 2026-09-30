"""Pure Air leader-phase selection policy.

The policy maps declared flight and route facts to a phase name.  It does not
read a loader, create command DTOs, resolve compiled enums, or import RL/Gym
runtime code.  The tasking adapter owns observation collection and phase DTO
projection; this module owns only the replaceable phase-selection algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from python.tasking_contracts.common.mission_defs import is_landing_command_code


@dataclass(frozen=True)
class LeaderPhaseInput:
    """Normalized facts used by the default scripted phase policy."""

    command_code: int
    on_ground: bool
    ground_speed_mps: float
    altitude_agl_m: float
    dme_m: float
    remaining_waypoints: int
    total_waypoints: int
    terminal_waypoint_count: int
    scramble_ground_speed_max_mps: float
    departure_route_alt_agl_m: float
    landing_final_dme_m: float
    landing_final_alt_agl_m: float


@dataclass(frozen=True)
class LeaderPhaseDecision:
    """Pure result of one phase-selection evaluation."""

    phase_name: str


@runtime_checkable
class LeaderPhasePolicy(Protocol):
    """Replaceable Air phase-selection algorithm."""

    def decide(self, state: LeaderPhaseInput) -> LeaderPhaseDecision: ...


class ScriptedLeaderPhasePolicy:
    """Deterministic phase policy used by the maintained scripted baseline."""

    def decide(self, state: LeaderPhaseInput) -> LeaderPhaseDecision:
        if is_landing_command_code(int(state.command_code)):
            if bool(state.on_ground):
                phase_name = "rollout"
            elif (
                float(state.dme_m) <= float(state.landing_final_dme_m)
                or float(state.altitude_agl_m) <= float(state.landing_final_alt_agl_m)
            ):
                phase_name = "landing_final"
            else:
                phase_name = "approach_armed"
            return LeaderPhaseDecision(phase_name=phase_name)

        if bool(state.on_ground):
            phase_name = (
                "scramble"
                if float(state.ground_speed_mps) <= float(state.scramble_ground_speed_max_mps)
                else "takeoff"
            )
            return LeaderPhaseDecision(phase_name=phase_name)

        remaining = max(0, int(state.remaining_waypoints))
        terminal_count = max(int(state.terminal_waypoint_count), 2)
        if remaining > terminal_count:
            if (
                int(state.total_waypoints) > 0
                and remaining == int(state.total_waypoints)
                and float(state.altitude_agl_m) < float(state.departure_route_alt_agl_m)
            ):
                phase_name = "departure"
            else:
                phase_name = "transit_to_station"
        else:
            phase_name = "rtb"
        return LeaderPhaseDecision(phase_name=phase_name)


__all__ = [
    "LeaderPhaseDecision",
    "LeaderPhaseInput",
    "LeaderPhasePolicy",
    "ScriptedLeaderPhasePolicy",
]
