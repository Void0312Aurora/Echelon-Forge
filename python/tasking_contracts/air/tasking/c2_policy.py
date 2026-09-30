"""Pure Air C2 task transition policy.

The policy decides only the next task state and transition provenance. It does
not read a loader, author a command, inspect a kernel, import RL, or depend on
native bindings. The existing C2 manager remains responsible for projecting
this decision into domain task/report DTOs and synchronizing them through the
authoritative command-chain owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


TASK_IDLE = "TASK_IDLE"
TASK_SCRAMBLE = "TASK_SCRAMBLE"
TASK_CAP = "TASK_CAP"
TASK_RTB = "TASK_RTB"
TASK_RECOVER_LAND = "TASK_RECOVER_LAND"


@dataclass(frozen=True)
class C2TransitionInput:
    """Information-state projection required by the default C2 policy."""

    current_task_name: str
    sim_time_s: float
    altitude_agl_m: float
    ground_speed_mps: float
    station_entry_time_s: float | None
    on_station_time_s: float
    near_station: bool
    report_type: int
    report_valid: bool
    report_reason: str
    rep_rtb_type: int
    warn_bingo_type: int
    rep_unable_type: int
    route_exhausted: bool
    recovery_ready: bool
    scramble_complete_alt_agl_m: float
    scramble_complete_ground_speed_mps: float
    auto_rtb_on_station_complete: bool


@dataclass(frozen=True)
class C2TransitionDecision:
    """Pure result of one C2 update."""

    task_name: str
    transitioned: bool
    reason: str
    station_entry_time_s: float | None


@runtime_checkable
class C2TransitionPolicy(Protocol):
    def decide(self, state: C2TransitionInput) -> C2TransitionDecision: ...


class ScriptedC2TransitionPolicy:
    """Deterministic rule policy for the maintained Air scripted baseline."""

    def decide(self, state: C2TransitionInput) -> C2TransitionDecision:
        current = str(state.current_task_name or TASK_IDLE).strip().upper()
        station_entry_time_s = state.station_entry_time_s
        transitioned = False
        reason = ""

        if current == TASK_SCRAMBLE:
            if (
                float(state.altitude_agl_m) >= float(state.scramble_complete_alt_agl_m)
                and float(state.ground_speed_mps) >= float(state.scramble_complete_ground_speed_mps)
            ):
                current = TASK_CAP
                transitioned = True
                reason = "scramble_complete"

        elif current == TASK_CAP:
            if bool(state.near_station):
                if station_entry_time_s is None:
                    station_entry_time_s = float(state.sim_time_s)
            else:
                station_entry_time_s = None

            report_triggers_rtb = state.report_type in {
                int(state.rep_rtb_type),
                int(state.warn_bingo_type),
                int(state.rep_unable_type),
            }
            if report_triggers_rtb and bool(state.report_valid):
                current = TASK_RTB
                transitioned = True
                reason = str(state.report_reason or "report_valid")
            elif (
                bool(state.auto_rtb_on_station_complete)
                and station_entry_time_s is not None
                and float(state.on_station_time_s) > 1.0
                and float(state.sim_time_s) - float(station_entry_time_s) >= float(state.on_station_time_s)
            ):
                current = TASK_RTB
                transitioned = True
                reason = "station_time_complete"

        elif current == TASK_RTB:
            if bool(state.route_exhausted):
                current = TASK_RECOVER_LAND
                transitioned = True
                reason = "route_exhausted_recovery_final"
            elif bool(state.recovery_ready) and state.report_type in {
                int(state.rep_rtb_type),
                int(state.warn_bingo_type),
                int(state.rep_unable_type),
            }:
                current = TASK_RECOVER_LAND
                transitioned = True
                reason = "recovery_window_open"

        return C2TransitionDecision(
            task_name=current,
            transitioned=transitioned,
            reason=reason,
            station_entry_time_s=station_entry_time_s,
        )


__all__ = [
    "C2TransitionDecision",
    "C2TransitionInput",
    "C2TransitionPolicy",
    "ScriptedC2TransitionPolicy",
    "TASK_CAP",
    "TASK_IDLE",
    "TASK_RECOVER_LAND",
    "TASK_RTB",
    "TASK_SCRAMBLE",
]
