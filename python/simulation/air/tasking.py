"""Compiled Air tasking adapter for the neutral scripted C2 manager.

This is a simulation-side adapter, not a policy implementation.  It owns
compiled DTO construction and enum projection so the neutral C2 state machine
can be instantiated without importing the learning or environment packages.
"""

from __future__ import annotations

from typing import Any

import ef_py

from python.tasking_contracts.air.tasking.c2_manager import ScriptedC2TaskManager
from python.tasking_contracts.air.tasking.c2_observation import C2ReportTypeCodes
from python.tasking_contracts.air.tasking.c2_policy import (
    TASK_CAP,
    TASK_IDLE,
    TASK_RECOVER_LAND,
    TASK_RTB,
    TASK_SCRAMBLE,
)
from python.tasking_contracts.common.bridge_views import mission_command_view
from python.tasking_contracts.common.mission_defs import is_landing_command_code
from python.tasking_contracts.common.task_order import (
    apply_common_task_order_defaults,
    apply_common_task_order_overrides,
    infer_common_tactical_unit_type,
)


def _enum_or_default(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, raw_value, default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        try:
            return int(raw_value)
        except Exception:
            return default_value


def _scenario_task_order_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    value = scenario_data.get("task_order")
    return value if isinstance(value, dict) else None


def _apply_authored_order_fields(order: Any, spec: dict[str, Any] | None, *, assignee_id: int) -> None:
    if not isinstance(spec, dict):
        return
    apply_common_task_order_overrides(order, spec, assignee_id=assignee_id)
    if hasattr(order, "active"):
        order.active = bool(spec.get("active", True))
    if hasattr(order, "assignee_id"):
        order.assignee_id = int(spec.get("assignee_id", assignee_id))
    if "task_type" in spec:
        order.task_type = _enum_or_default(ef_py.TaskType, spec["task_type"], order.task_type)
    if "station_type" in spec:
        order.station_type = _enum_or_default(ef_py.StationType, spec["station_type"], order.station_type)
    if "service_profile" in spec and hasattr(order, "service_profile"):
        order.service_profile = _enum_or_default(ef_py.ServiceProfile, spec["service_profile"], order.service_profile)
    if "task_family" in spec and hasattr(order, "task_family"):
        order.task_family = _enum_or_default(ef_py.TaskFamily, spec["task_family"], order.task_family)
    if "tactical_unit_type" in spec and hasattr(order, "tactical_unit_type"):
        order.tactical_unit_type = _enum_or_default(
            ef_py.TacticalUnitType, spec["tactical_unit_type"], order.tactical_unit_type
        )
    if "command_relationship" in spec and hasattr(order, "command_relationship"):
        order.command_relationship = _enum_or_default(
            ef_py.CommandRelationship, spec["command_relationship"], order.command_relationship
        )
    if "authority_scope" in spec and hasattr(order, "authority_scope"):
        order.authority_scope = _enum_or_default(ef_py.AuthorityScope, spec["authority_scope"], order.authority_scope)
    if "coordination_mode" in spec and hasattr(order, "coordination_mode"):
        order.coordination_mode = _enum_or_default(ef_py.CoordinationMode, spec["coordination_mode"], order.coordination_mode)
    if "recovery_approach_type" in spec and hasattr(order, "recovery_approach_type"):
        namespace = getattr(ef_py, "RecoveryApproachType", None)
        if namespace is not None:
            order.recovery_approach_type = _enum_or_default(
                namespace, spec["recovery_approach_type"], order.recovery_approach_type
            )
    if "naval_station_type" in spec and hasattr(order, "naval_station_type"):
        namespace = getattr(ef_py, "NavalStationType", None)
        if namespace is not None:
            order.naval_station_type = _enum_or_default(namespace, spec["naval_station_type"], order.naval_station_type)


def apply_task_order_overrides(
    order: Any,
    order_spec: dict[str, Any] | None,
    *,
    default_assignee_id: int,
) -> Any:
    """Apply authored task-order fields at the compiled simulation boundary."""

    if not isinstance(order_spec, dict):
        return order
    _apply_authored_order_fields(order, order_spec, assignee_id=int(default_assignee_id))
    apply_common_task_order_defaults(order)
    return order


def _task_family(task_name: str) -> Any:
    if task_name == TASK_SCRAMBLE:
        return ef_py.TaskFamily.Transit
    if task_name == TASK_CAP:
        return ef_py.TaskFamily.Patrol
    if task_name in {TASK_RTB, TASK_RECOVER_LAND}:
        return ef_py.TaskFamily.Recover
    return getattr(ef_py.TaskFamily, "Unspecified", 0)


def _apply_air_defaults(order: Any, *, task_name: str) -> None:
    if hasattr(order, "service_profile") and int(order.service_profile) == int(getattr(ef_py.ServiceProfile, "Unspecified", 0)):
        order.service_profile = ef_py.ServiceProfile.AirForce
    if hasattr(order, "task_family"):
        task_family = _task_family(task_name)
        if int(task_family) != int(getattr(ef_py.TaskFamily, "Unspecified", 0)):
            order.task_family = task_family
    if hasattr(order, "tactical_unit_type") and int(order.tactical_unit_type) == int(getattr(ef_py.TacticalUnitType, "Unspecified", 0)):
        order.tactical_unit_type = getattr(
            ef_py.TacticalUnitType,
            infer_common_tactical_unit_type(order),
            ef_py.TacticalUnitType.Platform,
        )
    if hasattr(order, "command_relationship") and int(order.command_relationship) == int(getattr(ef_py.CommandRelationship, "None", 0)):
        order.command_relationship = getattr(ef_py.CommandRelationship, "TACON", order.command_relationship)
    if hasattr(order, "authority_scope") and int(order.authority_scope) == int(getattr(ef_py.AuthorityScope, "Unspecified", 0)):
        order.authority_scope = getattr(ef_py.AuthorityScope, "Tactical", order.authority_scope)
    if hasattr(order, "coordination_mode"):
        tactical_unit_type = int(getattr(order, "tactical_unit_type", getattr(ef_py.TacticalUnitType, "Platform", 0)))
        attached_types = {
            int(getattr(ef_py.TacticalUnitType, "TacticalUnit", -1)),
            int(getattr(ef_py.TacticalUnitType, "MissionPackage", -1)),
        }
        mode_name = "Recover" if task_name in {TASK_RTB, TASK_RECOVER_LAND} else (
            "Attached" if tactical_unit_type in attached_types else "Independent"
        )
        order.coordination_mode = getattr(ef_py.CoordinationMode, mode_name, order.coordination_mode)
    if hasattr(order, "recovery_site_id") and int(getattr(order, "recovery_site_id", 0) or 0) <= 0:
        runway_id = int(getattr(order, "recovery_runway_id", 0) or 0)
        base_id = int(getattr(order, "recovery_base_id", 0) or 0)
        if runway_id > 0 or base_id > 0:
            order.recovery_site_id = runway_id or base_id


class CompiledAirC2TaskOrderProjection:
    """Project neutral C2 task names into compiled Air task-order DTOs."""

    @staticmethod
    def _targets(loader: Any) -> tuple[float, float, float | None, float | None]:
        view = mission_command_view(loader)
        altitude = view.float_field("target_altitude", 0.0)
        speed = view.float_field("target_speed", 0.0)
        anchor_x = anchor_y = None
        waypoints = list(getattr(loader, "waypoints", []) or [])
        index = int(getattr(loader, "waypoint_idx", 0) or 0)
        if 0 <= index < len(waypoints):
            waypoint = waypoints[index]
            altitude = float(waypoint.get("altitude_m", altitude))
            speed = float(waypoint.get("speed_mps", speed))
            anchor_x = float(waypoint.get("x", 0.0))
            anchor_y = float(waypoint.get("y", 0.0))
        return altitude, speed, anchor_x, anchor_y

    @staticmethod
    def _retarget_block(order: Any, target: float, target_name: str, lower_name: str, upper_name: str, *, lower: float, upper: float, floor: float) -> None:
        current_target = float(getattr(order, target_name, target))
        current_min = float(getattr(order, lower_name, floor))
        current_max = float(getattr(order, upper_name, floor))
        if current_max > current_min + 1.0e-6:
            lower_margin = max(0.0, current_target - current_min)
            upper_margin = max(0.0, current_max - current_target)
        else:
            lower_margin, upper_margin = lower, upper
        setattr(order, target_name, float(target))
        setattr(order, lower_name, max(float(floor), float(target) - lower_margin))
        setattr(order, upper_name, max(getattr(order, lower_name), float(target) + upper_margin))

    def retask_order(self, loader: Any, *, task_name: str, sim_time_s: float) -> None:
        task_name = str(task_name).strip().upper()
        order = getattr(loader, "task_order", None)
        created_order = order is None
        if order is None:
            order = ef_py.TaskOrder()
            loader.task_order = order
        if created_order:
            order.active = True
            order.task_id = int(getattr(order, "task_id", 0) or 1)
            order.assignee_id = int(getattr(loader, "agent_id", 0) or 0)
            order.issue_time_s = float(sim_time_s)
        task_types = {
            TASK_IDLE: ef_py.TaskType.Idle,
            TASK_SCRAMBLE: ef_py.TaskType.Scramble,
            TASK_CAP: ef_py.TaskType.CAP,
            TASK_RTB: ef_py.TaskType.RTB,
            TASK_RECOVER_LAND: ef_py.TaskType.RecoverLand,
        }
        order.task_type = task_types.get(task_name, ef_py.TaskType.Idle)
        waypoints = list(getattr(loader, "waypoints", []) or [])
        if created_order and hasattr(order, "station_type"):
            order.station_type = ef_py.StationType.RouteCAP if waypoints else ef_py.StationType.Orbit
        altitude, speed, anchor_x, anchor_y = self._targets(loader)
        if created_order and anchor_x is not None:
            order.anchor_x_m = anchor_x
            order.anchor_y_m = anchor_y
        if created_order:
            order.anchor_z_m = altitude
            order.target_altitude_m = altitude
            order.target_speed_mps = speed
        scenario_order_cfg = _scenario_task_order_cfg(loader)
        if created_order or task_name in {TASK_SCRAMBLE, TASK_CAP}:
            _apply_authored_order_fields(order, scenario_order_cfg, assignee_id=order.assignee_id)
            # Authored metadata may describe the order, but live C2 owns its
            # current task state and must win over a static task_type field.
            order.task_type = task_types.get(task_name, ef_py.TaskType.Idle)
            if task_name in {TASK_SCRAMBLE, TASK_CAP} and isinstance(scenario_order_cfg, dict) and scenario_order_cfg:
                order.issue_time_s = float(sim_time_s)
        if task_name in {TASK_SCRAMBLE, TASK_CAP} and waypoints:
            self._retarget_block(order, altitude, "target_altitude_m", "altitude_block_min_m", "altitude_block_max_m", lower=500.0, upper=500.0, floor=0.0)
            self._retarget_block(order, speed, "target_speed_mps", "speed_min_mps", "speed_max_mps", lower=40.0, upper=40.0, floor=40.0)
        elif task_name == TASK_RTB:
            order.anchor_z_m = altitude
            order.target_altitude_m = altitude
            order.target_speed_mps = speed
            order.issue_time_s = float(sim_time_s)
            if anchor_x is not None:
                order.anchor_x_m = anchor_x
                order.anchor_y_m = anchor_y
            self._retarget_block(order, altitude, "target_altitude_m", "altitude_block_min_m", "altitude_block_max_m", lower=500.0, upper=500.0, floor=0.0)
            self._retarget_block(order, speed, "target_speed_mps", "speed_min_mps", "speed_max_mps", lower=40.0, upper=40.0, floor=40.0)
        elif task_name == TASK_RECOVER_LAND:
            order.anchor_z_m = altitude
            order.target_altitude_m = altitude
            order.target_speed_mps = speed
            order.issue_time_s = float(sim_time_s)
            if anchor_x is not None:
                order.anchor_x_m = anchor_x
                order.anchor_y_m = anchor_y
            order.altitude_block_min_m = 0.0
            order.altitude_block_max_m = max(350.0, altitude + 350.0)
            order.speed_min_mps = max(55.0, speed - 20.0)
            order.speed_max_mps = max(order.speed_min_mps, speed + 20.0)
        _apply_air_defaults(order, task_name=task_name)
        apply_common_task_order_defaults(order)


def _compiled_report_type_codes() -> C2ReportTypeCodes:
    msg = ef_py.CommMsgType
    return C2ReportTypeCodes(
        none=int(getattr(msg, "None")),
        on_station=int(getattr(msg, "REP_ON_STATION")),
        rtb=int(getattr(msg, "REP_RTB")),
        bingo=int(getattr(msg, "WARN_BINGO")),
        unable=int(getattr(msg, "REP_UNABLE")),
        wilco=int(getattr(msg, "REP_WILCO")),
    )


def make_scripted_c2_task_manager(**kwargs: object) -> ScriptedC2TaskManager:
    options = dict(kwargs)
    options.setdefault("report_type_codes", _compiled_report_type_codes())
    options.setdefault("task_order_projection", CompiledAirC2TaskOrderProjection())
    return ScriptedC2TaskManager(**options)


__all__ = [
    "CompiledAirC2TaskOrderProjection",
    "apply_task_order_overrides",
    "make_scripted_c2_task_manager",
]
