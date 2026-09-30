"""Pure Air approach-arm gate policy.

This module owns the deterministic safety gates for entering the landing
approach phase.  Loader access, ILS acquisition, runway-frame calculation, and
post-waypoint activation remain adapter responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from python.tasking_contracts.common.mission_defs import is_landing_command_code


@dataclass(frozen=True)
class LeaderApproachInput:
    """Normalized facts required by the approach-arm gate."""

    post_transition_pending: bool
    c2_task_allows_approach: bool
    c2_recovery_task: bool
    current_command_code: int
    post_transition_command_code: int
    remaining_waypoints: int
    terminal_waypoint_count: int
    post_transition_ready: bool
    altitude_agl_m: float
    rollout_alt_agl_m: float
    max_altitude_agl_m: float
    ils_valid: bool
    dme_m: float
    max_dme_m: float
    localizer_abs: float
    max_localizer_abs: float
    glide_slope_abs: float
    max_glide_slope_abs: float
    runway_heading_error_deg: float
    max_runway_heading_error_deg: float
    runway_frame_valid: bool
    require_runway_frame: bool
    runway_along_m: float
    min_runway_along_m: float
    runway_cross_m: float
    max_runway_cross_abs_m: float


@dataclass(frozen=True)
class LeaderApproachDecision:
    """Pure approach-arm result."""

    arm: bool


@runtime_checkable
class LeaderApproachPolicy(Protocol):
    def decide(self, state: LeaderApproachInput) -> LeaderApproachDecision: ...


class ScriptedLeaderApproachPolicy:
    """Fail-closed terminal geometry gate for the scripted baseline."""

    def decide(self, state: LeaderApproachInput) -> LeaderApproachDecision:
        if not bool(state.post_transition_pending):
            return LeaderApproachDecision(False)
        if not bool(state.c2_task_allows_approach):
            return LeaderApproachDecision(False)
        if is_landing_command_code(int(state.current_command_code)):
            return LeaderApproachDecision(False)
        if not is_landing_command_code(int(state.post_transition_command_code)):
            return LeaderApproachDecision(False)
        if bool(state.c2_recovery_task) and int(state.remaining_waypoints) <= 0:
            return LeaderApproachDecision(bool(state.post_transition_ready))
        if int(state.remaining_waypoints) > max(int(state.terminal_waypoint_count), 0):
            return LeaderApproachDecision(False)
        if float(state.altitude_agl_m) <= float(state.rollout_alt_agl_m):
            return LeaderApproachDecision(False)
        if not bool(state.ils_valid):
            return LeaderApproachDecision(False)
        if float(state.dme_m) > float(state.max_dme_m):
            return LeaderApproachDecision(False)
        if float(state.altitude_agl_m) > float(state.max_altitude_agl_m):
            return LeaderApproachDecision(False)
        if float(state.localizer_abs) > float(state.max_localizer_abs):
            return LeaderApproachDecision(False)
        if float(state.glide_slope_abs) > float(state.max_glide_slope_abs):
            return LeaderApproachDecision(False)
        if float(state.runway_heading_error_deg) > float(state.max_runway_heading_error_deg):
            return LeaderApproachDecision(False)
        if bool(state.require_runway_frame) and not bool(state.runway_frame_valid):
            return LeaderApproachDecision(False)
        if bool(state.runway_frame_valid):
            if float(state.runway_along_m) < float(state.min_runway_along_m):
                return LeaderApproachDecision(False)
            if abs(float(state.runway_cross_m)) > float(state.max_runway_cross_abs_m):
                return LeaderApproachDecision(False)
        return LeaderApproachDecision(True)


__all__ = [
    "LeaderApproachDecision",
    "LeaderApproachInput",
    "LeaderApproachPolicy",
    "ScriptedLeaderApproachPolicy",
]
