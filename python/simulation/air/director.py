"""Direct compiled Air scripted director.

The director consumes a small native-state snapshot and emits the maintained
Air command chain.  It is intentionally independent of scenario loaders, RL
profiles, and Gym environments; an adapter may provide the snapshot from a
facade, replay, or another simulation implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import ef_py

from python.tasking_contracts.air.tasking.leader_approach_policy import (
    LeaderApproachInput,
    LeaderApproachPolicy,
    ScriptedLeaderApproachPolicy,
)
from python.tasking_contracts.air.tasking.leader_phase_policy import (
    LeaderPhaseInput,
    LeaderPhasePolicy,
    ScriptedLeaderPhasePolicy,
)
from python.tasking_contracts.common.mission_defs import command_code_for_phase_name


@dataclass(frozen=True)
class AirDirectorInput:
    """Native facts required for one direct Air command-chain decision."""

    entity_id: int
    sim_time_s: float
    observation: Any
    instruments: Any
    mission_command: Any = None
    task_order: Any = None
    waypoint_count: int = 0
    remaining_waypoints: int = 0
    ils: Sequence[float] = (0.0, 0.0, 0.0, 0.0)
    task_name: str = "TASK_CAP"
    approach_facts: LeaderApproachInput | None = None


@dataclass(frozen=True)
class AirDirectorDecision:
    """Compiled command-chain DTOs emitted by the direct director."""

    phase_name: str
    task_order: Any
    leader_intent: Any
    pilot_report: Any
    mission_command: Any


class AirScriptedDirector:
    """Build a deterministic Air command chain from native state."""

    def __init__(
        self,
        *,
        terminal_waypoint_count: int = 2,
        rollout_alt_agl_m: float = 5.0,
        scramble_ground_speed_max_mps: float = 15.0,
        departure_route_alt_agl_m: float = 140.0,
        landing_final_dme_m: float = 3500.0,
        landing_final_alt_agl_m: float = 140.0,
        phase_policy: LeaderPhasePolicy | None = None,
        approach_policy: LeaderApproachPolicy | None = None,
    ) -> None:
        self.terminal_waypoint_count = max(0, int(terminal_waypoint_count))
        self.rollout_alt_agl_m = float(rollout_alt_agl_m)
        self.scramble_ground_speed_max_mps = float(scramble_ground_speed_max_mps)
        self.departure_route_alt_agl_m = max(self.rollout_alt_agl_m, float(departure_route_alt_agl_m))
        self.landing_final_dme_m = float(landing_final_dme_m)
        self.landing_final_alt_agl_m = float(landing_final_alt_agl_m)
        self.phase_policy = phase_policy or ScriptedLeaderPhasePolicy()
        self.approach_policy = approach_policy or ScriptedLeaderApproachPolicy()
        if not isinstance(self.phase_policy, LeaderPhasePolicy):
            raise TypeError("phase_policy must implement LeaderPhasePolicy")
        if not isinstance(self.approach_policy, LeaderApproachPolicy):
            raise TypeError("approach_policy must implement LeaderApproachPolicy")

    def decide(self, state: AirDirectorInput) -> AirDirectorDecision:
        if int(state.entity_id) <= 0:
            raise ValueError("Air director entity_id must be positive")
        alt_agl = _float(state.instruments, "alt_radar")
        ground_speed = _float(state.instruments, "ground_speed")
        dme_m = _ils(state.ils, 3, float("inf"))
        command_code = int(_field(state.mission_command, "command_code", 0))
        if state.approach_facts is not None and self.approach_policy.decide(state.approach_facts).arm:
            command_code = int(state.approach_facts.post_transition_command_code)
        on_ground = alt_agl <= self.rollout_alt_agl_m
        phase = self.phase_policy.decide(
            LeaderPhaseInput(
                command_code=command_code,
                on_ground=on_ground,
                ground_speed_mps=ground_speed,
                altitude_agl_m=alt_agl,
                dme_m=dme_m,
                remaining_waypoints=max(0, int(state.remaining_waypoints)),
                total_waypoints=max(0, int(state.waypoint_count)),
                terminal_waypoint_count=self.terminal_waypoint_count,
                scramble_ground_speed_max_mps=self.scramble_ground_speed_max_mps,
                departure_route_alt_agl_m=self.departure_route_alt_agl_m,
                landing_final_dme_m=self.landing_final_dme_m,
                landing_final_alt_agl_m=self.landing_final_alt_agl_m,
            )
        ).phase_name

        order = _task_order(state)
        intent = _leader_intent(state, phase_name=phase, task_order=order)
        report = _pilot_report(state, phase_name=phase, task_order=order)
        command = _mission_command(state, intent=intent)
        return AirDirectorDecision(
            phase_name=phase,
            task_order=order,
            leader_intent=intent,
            pilot_report=report,
            mission_command=command,
        )


def _task_order(state: AirDirectorInput) -> Any:
    order = ef_py.TaskOrder()
    task_name = str(state.task_name or "TASK_CAP").strip().upper()
    task_types = {
        "TASK_IDLE": getattr(ef_py.TaskType, "Idle"),
        "TASK_SCRAMBLE": getattr(ef_py.TaskType, "Scramble"),
        "TASK_CAP": getattr(ef_py.TaskType, "CAPMission" if int(state.waypoint_count) > 0 else "CAP"),
        "TASK_RTB": getattr(ef_py.TaskType, "RTB"),
        "TASK_RECOVER_LAND": getattr(ef_py.TaskType, "RecoverLand"),
    }
    order.active = True
    order.task_id = 1
    order.assignee_id = int(state.entity_id)
    order.issuer_id = 0
    order.issue_time_s = float(state.sim_time_s)
    order.task_type = task_types.get(task_name, task_types["TASK_CAP"])
    order.station_type = getattr(ef_py.StationType, "RouteCAP" if int(state.waypoint_count) > 0 else "Orbit")
    order.target_altitude_m = _field(state.mission_command, "cmd_altitude_m", 0.0)
    order.target_speed_mps = _field(state.mission_command, "cmd_speed_mps", 0.0)
    order.altitude_block_min_m = max(0.0, float(order.target_altitude_m) - 500.0)
    order.altitude_block_max_m = max(float(order.altitude_block_min_m), float(order.target_altitude_m) + 500.0)
    order.speed_min_mps = max(0.0, float(order.target_speed_mps) - 40.0)
    order.speed_max_mps = max(float(order.speed_min_mps), float(order.target_speed_mps) + 40.0)
    _set_enum(order, "service_profile", "AirForce")
    _set_enum(order, "task_family", _task_family_for(task_name))
    _set_enum(order, "tactical_unit_type", "Platform")
    _set_enum(order, "command_relationship", "TACON")
    _set_enum(order, "authority_scope", "Tactical")
    _set_enum(order, "coordination_mode", "Recover" if task_name in {"TASK_RTB", "TASK_RECOVER_LAND"} else "Independent")
    return order


def _leader_intent(state: AirDirectorInput, *, phase_name: str, task_order: Any) -> Any:
    intent = ef_py.LeaderIntent()
    intent.active = True
    intent.phase_id = _phase_id(phase_name)
    intent.command_code = int(
        command_code_for_phase_name(
            phase_name,
            has_waypoints=int(state.waypoint_count) > 0,
            mission_cmd_code=int(_field(state.mission_command, "command_code", 0)),
        )
    )
    intent.cmd_heading_deg = _field(state.mission_command, "cmd_heading_deg", 0.0)
    intent.cmd_altitude_m = _field(state.mission_command, "cmd_altitude_m", 0.0)
    intent.cmd_speed_mps = _field(state.mission_command, "cmd_speed_mps", 0.0)
    intent.approach_armed = phase_name in {"approach_armed", "landing_final", "rollout"}
    intent.commit_to_land = phase_name in {"landing_final", "rollout"}
    intent.abort_flag = phase_name == "abort"
    for name in ("task_family", "tactical_unit_type", "service_profile", "coordination_mode"):
        if hasattr(intent, name):
            setattr(intent, name, getattr(task_order, name))
    if hasattr(intent, "tactical_unit_id"):
        intent.tactical_unit_id = int(state.entity_id)
    if hasattr(intent, "takeoff_procedure_id"):
        intent.takeoff_procedure_id = getattr(task_order, "takeoff_procedure_id")
    if hasattr(intent, "takeoff_clearance_id"):
        intent.takeoff_clearance_id = getattr(task_order, "takeoff_clearance_id")
    if hasattr(intent, "runway_slot_id"):
        intent.runway_slot_id = getattr(task_order, "runway_slot_id")
    if hasattr(intent, "takeoff_interval_s"):
        intent.takeoff_interval_s = float(getattr(task_order, "takeoff_interval_s", 0.0))
    return intent


def _pilot_report(state: AirDirectorInput, *, phase_name: str, task_order: Any) -> Any:
    report = ef_py.PilotReport()
    report.active = True
    report.sender_id = int(state.entity_id)
    report.task_id = int(getattr(task_order, "task_id", 0))
    report.phase_id = _phase_id(phase_name)
    report.timestamp_s = float(state.sim_time_s)
    report.report_type = _report_type(phase_name)
    report.location_x_m = _float(state.observation, "x")
    report.location_y_m = _float(state.observation, "y")
    report.location_z_m = _float(state.observation, "z")
    for name in ("task_family", "tactical_unit_type", "service_profile"):
        if hasattr(report, name) and hasattr(task_order, name):
            setattr(report, name, getattr(task_order, name))
    if hasattr(report, "tactical_unit_id"):
        report.tactical_unit_id = int(state.entity_id)
    return report


def _mission_command(state: AirDirectorInput, *, intent: Any) -> Any:
    command = ef_py.MissionCommand()
    command.active = True
    command.command_code = int(getattr(intent, "command_code", 0))
    command.cmd_heading_deg = float(getattr(intent, "cmd_heading_deg", 0.0))
    command.cmd_altitude_m = float(getattr(intent, "cmd_altitude_m", 0.0))
    command.cmd_speed_mps = float(getattr(intent, "cmd_speed_mps", 0.0))
    for name in (
        "takeoff_procedure_id",
        "takeoff_clearance_id",
        "takeoff_interval_s",
        "runway_slot_id",
        "roe_state",
        "authorization_to_fire",
        "assigned_target_id",
        "engagement_authority_holder_id",
        "engagement_authority_grantor_id",
    ):
        if hasattr(command, name) and hasattr(intent, name):
            setattr(command, name, getattr(intent, name))
    return command


def _phase_id(phase_name: str) -> Any:
    mapping = {
        "idle": "Idle", "scramble": "Scramble", "takeoff": "Takeoff", "departure": "Departure",
        "transit_to_station": "TransitToStation", "establish_cap": "EstablishCAP", "on_station": "OnStation",
        "reposition": "Reposition", "rtb": "RTB", "approach_armed": "ApproachArmed",
        "landing_final": "LandingFinal", "rollout": "Rollout", "abort": "Abort",
    }
    return getattr(ef_py.LeaderPhase, mapping.get(str(phase_name).strip().lower(), "Idle"))


def _report_type(phase_name: str) -> Any:
    if phase_name in {"rtb", "approach_armed", "landing_final", "rollout"}:
        return getattr(ef_py.CommMsgType, "REP_RTB")
    if phase_name == "on_station":
        return getattr(ef_py.CommMsgType, "REP_ON_STATION")
    return getattr(ef_py.CommMsgType, "REP_WILCO")


def _task_family_for(task_name: str) -> Any:
    family = {
        "TASK_SCRAMBLE": "Transit",
        "TASK_CAP": "Patrol",
        "TASK_RTB": "Recover",
        "TASK_RECOVER_LAND": "Recover",
    }.get(task_name, "Unspecified")
    return getattr(ef_py.TaskFamily, family)


def _set_enum(target: Any, name: str, enum_name: str) -> None:
    namespace_name = {
        "service_profile": "ServiceProfile",
        "task_family": "TaskFamily",
        "tactical_unit_type": "TacticalUnitType",
        "command_relationship": "CommandRelationship",
        "authority_scope": "AuthorityScope",
        "coordination_mode": "CoordinationMode",
    }.get(name)
    namespace = getattr(ef_py, namespace_name, None)
    value = (
        getattr(namespace, enum_name, None)
        if namespace is not None and isinstance(enum_name, str)
        else enum_name
    )
    if value is not None and hasattr(target, name):
        setattr(target, name, value)


def _field(value: Any, name: str, default: Any) -> Any:
    if value is None:
        return default
    for candidate in (value, getattr(value, "shared_core", None), getattr(value, "air_takeoff", None)):
        if candidate is not None and hasattr(candidate, name):
            return getattr(candidate, name)
    return default


def _float(value: Any, name: str, default: float = 0.0) -> float:
    try:
        return float(getattr(value, name))
    except (AttributeError, TypeError, ValueError):
        return float(default)


def _ils(values: Sequence[float], index: int, default: float) -> float:
    try:
        return float(values[index])
    except (IndexError, TypeError, ValueError):
        return float(default)


__all__ = ["AirDirectorDecision", "AirDirectorInput", "AirScriptedDirector"]
