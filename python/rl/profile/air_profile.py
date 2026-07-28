from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import ef_py

from python.coercion import coerce_nonnegative_int
from python.rl.profile.common_core_base import (
    coerce_positive_int,
    enum_or_default,
    enum_value,
    is_default_enum,
)
from python.rl.profile.common_core_defaults import (
    authority_scope_default,
    command_relationship_default,
    coordination_mode_attached,
    coordination_mode_default,
    coordination_mode_independent,
    coordination_mode_recover,
    infer_recovery_site_id,
    infer_tactical_unit_id,
    infer_tactical_unit_type,
    runway_slot_default,
    service_profile_default,
    takeoff_clearance_default,
    takeoff_procedure_default,
    tactical_unit_type_default,
    task_family_default,
)
from python.rl.control.mission_defs import (
    COMMAND_CODE_LANDING,
    LANDING_PHASE_NAMES,
    command_code_for_phase_name,
    is_landing_command_code,
)


# Local name preserved as a thin alias; semantics owned by python.coercion.
_coerce_nonnegative_int = coerce_nonnegative_int


def _recovery_approach_none() -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "None", 0)


def _takeoff_procedure_unspecified() -> Any:
    return takeoff_procedure_default()


def _takeoff_clearance_unspecified() -> Any:
    return takeoff_clearance_default()


def _runway_slot_unspecified() -> Any:
    return runway_slot_default()


def _resolve_int_field(
    leader_intent: Any,
    mission_cmd: dict[str, Any],
    field_name: str,
    default: int = 0,
) -> int:
    if leader_intent is not None and hasattr(leader_intent, field_name):
        return _coerce_nonnegative_int(getattr(leader_intent, field_name, default))
    return _coerce_nonnegative_int(mission_cmd.get(field_name, default))


def _task_name_from_task_type(task_type: Any) -> str | None:
    mapping = {
        enum_value(getattr(ef_py.TaskType, "Scramble")): "TASK_SCRAMBLE",
        enum_value(getattr(ef_py.TaskType, "CAP")): "TASK_CAP",
        enum_value(getattr(ef_py.TaskType, "CAPMission")): "TASK_CAP",
        enum_value(getattr(ef_py.TaskType, "RTB")): "TASK_RTB",
        enum_value(getattr(ef_py.TaskType, "RecoverLand")): "TASK_RECOVER_LAND",
    }
    return mapping.get(enum_value(task_type), None)


def infer_air_task_family(*, task_name: str | None = None, task_type: Any = None, phase_name: str | None = None) -> Any:
    name = str(task_name or "").strip().upper()
    if not name:
        name = str(_task_name_from_task_type(task_type) or "").strip().upper()
    if name == "TASK_SCRAMBLE":
        return getattr(ef_py.TaskFamily, "Transit")
    if name == "TASK_CAP":
        return getattr(ef_py.TaskFamily, "Patrol")
    if name in {"TASK_RTB", "TASK_RECOVER_LAND"}:
        return getattr(ef_py.TaskFamily, "Recover")

    phase = str(phase_name or "").strip().lower()
    if phase in {"scramble", "takeoff"}:
        return getattr(ef_py.TaskFamily, "Transit")
    if phase in {"departure", "transit_to_station", "establish_cap", "on_station", "reposition"}:
        return getattr(ef_py.TaskFamily, "Patrol")
    if phase in {"rtb", "approach_armed", "landing_final", "rollout"}:
        return getattr(ef_py.TaskFamily, "Recover")
    return task_family_default()


def infer_air_task_type(*, task_family: Any = None, task_name: str | None = None, has_waypoints: bool = False) -> Any:
    name = str(task_name or "").strip().upper()
    if name == "TASK_SCRAMBLE":
        return getattr(ef_py.TaskType, "Scramble")
    if name == "TASK_CAP":
        return getattr(ef_py.TaskType, "CAPMission") if bool(has_waypoints) else getattr(ef_py.TaskType, "CAP")
    if name == "TASK_RTB":
        return getattr(ef_py.TaskType, "RTB")
    if name == "TASK_RECOVER_LAND":
        return getattr(ef_py.TaskType, "RecoverLand")

    family_value = enum_value(task_family, enum_value(task_family_default()))
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Transit")):
        return getattr(ef_py.TaskType, "Scramble")
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Patrol")):
        return getattr(ef_py.TaskType, "CAPMission") if bool(has_waypoints) else getattr(ef_py.TaskType, "CAP")
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Recover")):
        return getattr(ef_py.TaskType, "RTB")
    return getattr(ef_py.TaskType, "Idle")


def resolved_task_family(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> Any:
    if task is not None:
        task_family = getattr(task, "task_family", task_family_default())
        if not is_default_enum(task_family, task_family_default()):
            return task_family
        task_type = getattr(task, "task_type", None)
    else:
        task_type = None
    return infer_air_task_family(task_name=task_name, task_type=task_type, phase_name=phase_name)


def is_patrol_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Patrol"))


def is_recover_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Recover"))


def infer_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
) -> Any:
    recover_family = getattr(ef_py.TaskFamily, "Recover")
    if enum_value(task_family) == enum_value(recover_family):
        return coordination_mode_recover()

    name = str(task_name or "").strip().upper()
    if name in {"TASK_RTB", "TASK_RECOVER_LAND"}:
        return coordination_mode_recover()

    phase = str(phase_name or "").strip().lower()
    if phase in {"rtb", "approach_armed", "landing_final", "rollout"}:
        return coordination_mode_recover()

    unit_type_value = enum_value(tactical_unit_type)
    if unit_type_value in {
        enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")),
        enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")),
    }:
        return coordination_mode_attached()
    return coordination_mode_independent()


def normalize_task_order_spec(order_spec: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(order_spec, dict):
        return {}

    normalized = dict(order_spec)
    enum_fields = {
        "task_type": ef_py.TaskType,
        "service_profile": ef_py.ServiceProfile,
        "task_family": ef_py.TaskFamily,
        "tactical_unit_type": ef_py.TacticalUnitType,
        "command_relationship": ef_py.CommandRelationship,
        "authority_scope": ef_py.AuthorityScope,
        "coordination_mode": ef_py.CoordinationMode,
        "assignee_kind": ef_py.AssigneeKind,
        "station_type": ef_py.StationType,
    }
    if hasattr(ef_py, "TakeoffProcedureType"):
        enum_fields["takeoff_procedure_id"] = ef_py.TakeoffProcedureType
    if hasattr(ef_py, "TakeoffClearanceState"):
        enum_fields["takeoff_clearance_id"] = ef_py.TakeoffClearanceState
    if hasattr(ef_py, "RunwaySlotPosition"):
        enum_fields["runway_slot_id"] = ef_py.RunwaySlotPosition
    for field_name, namespace in enum_fields.items():
        if field_name in normalized:
            default_value = normalized.get(field_name)
            if field_name == "task_type":
                default_value = getattr(ef_py.TaskType, "Idle")
            elif field_name == "service_profile":
                default_value = service_profile_default()
            elif field_name == "task_family":
                default_value = task_family_default()
            elif field_name == "tactical_unit_type":
                default_value = tactical_unit_type_default()
            elif field_name == "command_relationship":
                default_value = command_relationship_default()
            elif field_name == "authority_scope":
                default_value = authority_scope_default()
            elif field_name == "coordination_mode":
                default_value = coordination_mode_default()
            normalized[field_name] = enum_or_default(namespace, normalized.get(field_name), default_value)

    has_waypoints = bool(list(normalized.get("waypoints", []) or []))
    task_family = enum_or_default(
        ef_py.TaskFamily,
        normalized.get("task_family"),
        infer_air_task_family(task_type=normalized.get("task_type")),
    )
    if "task_family" not in normalized:
        normalized["task_family"] = task_family

    if "task_type" not in normalized:
        normalized["task_type"] = infer_air_task_type(
            task_family=normalized.get("task_family", task_family),
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            has_waypoints=has_waypoints,
        )

    if "service_profile" not in normalized:
        normalized["service_profile"] = service_profile_default()
    if "command_relationship" not in normalized:
        normalized["command_relationship"] = command_relationship_default()
    if "authority_scope" not in normalized:
        normalized["authority_scope"] = authority_scope_default()

    task_group_id = coerce_positive_int(normalized.get("task_group_id", 0))
    package_id = coerce_positive_int(normalized.get("package_id", 0))
    if task_group_id <= 0 and package_id > 0:
        normalized["task_group_id"] = int(package_id)

    tactical_unit_type = enum_or_default(
        ef_py.TacticalUnitType,
        normalized.get("tactical_unit_type"),
        tactical_unit_type_default(),
    )
    if is_default_enum(tactical_unit_type, tactical_unit_type_default()):
        if package_id > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "MissionPackage")
        elif coerce_positive_int(normalized.get("element_id", 0)) > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "TacticalUnit")
        else:
            assignee_kind = enum_or_default(
                ef_py.AssigneeKind,
                normalized.get("assignee_kind"),
                getattr(ef_py.AssigneeKind, "Aircraft"),
            )
            if enum_value(assignee_kind) == enum_value(getattr(ef_py.AssigneeKind, "Package")):
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "MissionPackage")
            elif enum_value(assignee_kind) == enum_value(getattr(ef_py.AssigneeKind, "Element")):
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "TacticalUnit")
            else:
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "Platform")
        normalized["tactical_unit_type"] = tactical_unit_type

    recovery_site_id = coerce_positive_int(normalized.get("recovery_site_id", 0))
    if recovery_site_id <= 0:
        runway_id = coerce_positive_int(normalized.get("recovery_runway_id", 0))
        base_id = coerce_positive_int(normalized.get("recovery_base_id", 0))
        recovery_site_id = runway_id if runway_id > 0 else base_id
        if recovery_site_id > 0:
            normalized["recovery_site_id"] = int(recovery_site_id)

    if "coordination_mode" not in normalized:
        normalized["coordination_mode"] = infer_coordination_mode(
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            task_family=normalized.get("task_family", task_family),
            tactical_unit_type=normalized.get("tactical_unit_type", tactical_unit_type),
        )
    return normalized


def task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
    if task is None:
        return float(0.0), float(0.0), float(fallback_phase_id)

    task_type = enum_value(getattr(task, "task_type", 0))
    if task_type <= 0:
        task_type = enum_value(
            infer_air_task_type(
                task_family=getattr(task, "task_family", task_family_default()),
                has_waypoints=enum_value(getattr(task, "station_type", 0))
                == enum_value(getattr(ef_py.StationType, "RouteCAP")),
            )
        )
    station_type = enum_value(getattr(task, "station_type", 0))
    coordination_mode = enum_value(getattr(task, "coordination_mode", 0))
    return float(task_type), float(station_type if station_type > 0 else coordination_mode), float(fallback_phase_id)


def _recovery_approach_type_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return enum_or_default(namespace, raw_value, default_value)


def _takeoff_procedure_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "TakeoffProcedureType", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return enum_or_default(namespace, raw_value, default_value)


def _takeoff_clearance_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "TakeoffClearanceState", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return enum_or_default(namespace, raw_value, default_value)


def _runway_slot_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "RunwaySlotPosition", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return enum_or_default(namespace, raw_value, default_value)


def _landing_mode_to_recovery_approach_type(landing_mode: Any, default_value: Any) -> Any:
    mode = str(landing_mode or "").strip().lower()
    if not mode:
        return default_value
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        mapping = {"straight_in": 1, "ils_final": 2, "ils": 2, "visual": 3, "overhead": 4, "tacan": 5}
        return int(mapping.get(mode, _coerce_nonnegative_int(default_value)))
    mapping = {
        "straight_in": getattr(namespace, "StraightIn", default_value),
        "ils_final": getattr(namespace, "ILS", default_value),
        "ils": getattr(namespace, "ILS", default_value),
        "visual": getattr(namespace, "Visual", default_value),
        "overhead": getattr(namespace, "Overhead", default_value),
        "tacan": getattr(namespace, "TACAN", default_value),
    }
    return mapping.get(mode, default_value)


def _scenario_task_order_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    task_order = scenario_data.get("task_order", None)
    return task_order if isinstance(task_order, dict) else None


def _scenario_mission_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    mission_cfg = scenario_data.get("mission_command", None)
    return mission_cfg if isinstance(mission_cfg, dict) else None


def _mission_cmd_dict(loader: Any) -> dict[str, Any]:
    mission_cmd = getattr(loader, "mission_cmd", {}) or {}
    return mission_cmd if isinstance(mission_cmd, dict) else {}


def _post_transition_cfg(loader: Any) -> dict[str, Any] | None:
    post = getattr(loader, "post_waypoint_transition", None)
    if isinstance(post, dict) and post:
        return post
    mission_cfg = _scenario_mission_cfg(loader)
    if not isinstance(mission_cfg, dict):
        return None
    post = mission_cfg.get("post_waypoint_transition", None)
    return post if isinstance(post, dict) and post else None


def _stable_ref_id(payload: Any) -> int:
    try:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        text = repr(payload)
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    ref_id = int.from_bytes(digest[:8], "big", signed=False)
    return ref_id if ref_id > 0 else 1


def infer_route_ref_id(loader: Any) -> int:
    cached = getattr(loader, "_cached_route_ref_id", None)
    if cached is not None:
        try:
            return int(cached)
        except Exception:
            pass
    mission_cmd = _mission_cmd_dict(loader)
    mission_cfg = _scenario_mission_cfg(loader)
    for raw_value in (
        mission_cmd.get("route_ref_id", 0),
        mission_cfg.get("route_ref_id", 0) if isinstance(mission_cfg, dict) else 0,
    ):
        value = coerce_positive_int(raw_value)
        if value > 0:
            try:
                loader._cached_route_ref_id = int(value)
            except Exception:
                pass
            return value
    waypoints = list(getattr(loader, "waypoints", []) or [])
    if not waypoints:
        try:
            loader._cached_route_ref_id = 0
        except Exception:
            pass
        return 0
    payload = []
    for idx, wp in enumerate(waypoints):
        if not isinstance(wp, dict):
            payload.append({"idx": idx, "value": wp})
            continue
        payload.append(
            {
                "idx": idx,
                "x": round(float(wp.get("x", 0.0)), 3),
                "y": round(float(wp.get("y", 0.0)), 3),
                "z": round(float(wp.get("z", wp.get("altitude_m", 0.0))), 3),
                "speed_mps": round(float(wp.get("speed_mps", 0.0)), 3),
                "radius_m": round(float(wp.get("radius_m", 0.0)), 3),
                "waypoint_mode": str(wp.get("waypoint_mode", "")),
            }
        )
    value = int(_stable_ref_id(payload))
    try:
        loader._cached_route_ref_id = int(value)
    except Exception:
        pass
    return value


def has_active_waypoint_leg(loader: Any) -> bool:
    waypoints = list(getattr(loader, "waypoints", []) or [])
    if not waypoints:
        return False
    waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
    return 0 <= waypoint_idx < len(waypoints)


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    mission_cmd = _mission_cmd_dict(loader)
    post = _post_transition_cfg(loader)
    scenario_order = _scenario_task_order_cfg(loader)
    mission_cfg = _scenario_mission_cfg(loader)
    for raw_value in (
        getattr(task, "recovery_base_id", 0) if task is not None else 0,
        mission_cmd.get("recovery_base_id", 0),
        post.get("recovery_base_id", 0) if isinstance(post, dict) else 0,
        scenario_order.get("recovery_base_id", 0) if isinstance(scenario_order, dict) else 0,
        mission_cfg.get("recovery_base_id", 0) if isinstance(mission_cfg, dict) else 0,
    ):
        value = coerce_positive_int(raw_value)
        if value > 0:
            return value
    return 0


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    mission_cmd = _mission_cmd_dict(loader)
    post = _post_transition_cfg(loader)
    scenario_order = _scenario_task_order_cfg(loader)
    mission_cfg = _scenario_mission_cfg(loader)
    for raw_value in (
        getattr(task, "recovery_runway_id", 0) if task is not None else 0,
        mission_cmd.get("recovery_runway_id", 0),
        post.get("recovery_runway_id", 0) if isinstance(post, dict) else 0,
        scenario_order.get("recovery_runway_id", 0) if isinstance(scenario_order, dict) else 0,
        mission_cfg.get("recovery_runway_id", 0) if isinstance(mission_cfg, dict) else 0,
    ):
        value = coerce_positive_int(raw_value)
        if value > 0:
            return value
    return 0


def infer_recovery_approach_type(loader: Any, task: Any | None = None) -> Any:
    mission_cmd = _mission_cmd_dict(loader)
    post = _post_transition_cfg(loader)
    scenario_order = _scenario_task_order_cfg(loader)
    default_value = _recovery_approach_none()
    if task is not None and hasattr(task, "recovery_approach_type"):
        task_value = _recovery_approach_type_or_default(getattr(task, "recovery_approach_type", default_value), default_value)
        if int(task_value) != int(default_value):
            return task_value
    for raw_value in (
        mission_cmd.get("recovery_approach_type", None),
        post.get("recovery_approach_type", None) if isinstance(post, dict) else None,
        scenario_order.get("recovery_approach_type", None) if isinstance(scenario_order, dict) else None,
    ):
        value = _recovery_approach_type_or_default(raw_value, default_value)
        if int(value) != int(default_value):
            return value
    for landing_mode in (
        mission_cmd.get("landing_mode", ""),
        post.get("landing_mode", "") if isinstance(post, dict) else "",
    ):
        value = _landing_mode_to_recovery_approach_type(landing_mode, default_value)
        if int(value) != int(default_value):
            return value
    if infer_recovery_base_id(loader, task=task) > 0 or infer_recovery_runway_id(loader, task=task) > 0:
        return _landing_mode_to_recovery_approach_type("straight_in", default_value)
    return default_value


def _landing_reference_heading_deg(loader: Any, default_heading_deg: float) -> float:
    post = _post_transition_cfg(loader)
    if not isinstance(post, dict) or not post:
        return float(default_heading_deg)
    target_heading = float(post.get("target_heading", default_heading_deg))
    if bool(getattr(loader, "rotate_mission_heading_with_world", False)) and abs(float(getattr(loader, "world_yaw_deg", 0.0))) > 1.0e-6:
        target_heading = (target_heading + float(getattr(loader, "world_yaw_deg", 0.0))) % 360.0
    return float(target_heading)


def build_kernel_mission_command(loader: Any) -> ef_py.MissionCommand:
    cmd = ef_py.MissionCommand()
    cmd.active = True
    mission_cmd = getattr(loader, "mission_cmd", {}) or {}
    leader_intent = getattr(loader, "leader_intent", None)
    cmd.command_code = int(getattr(leader_intent, "command_code", mission_cmd.get("command_code", 0)))
    cmd.cmd_heading_deg = float(getattr(leader_intent, "cmd_heading_deg", mission_cmd.get("target_heading", 0.0)))
    cmd.cmd_altitude_m = float(getattr(leader_intent, "cmd_altitude_m", mission_cmd.get("target_altitude", 0.0)))
    cmd.cmd_speed_mps = float(getattr(leader_intent, "cmd_speed_mps", mission_cmd.get("target_speed", 0.0)))
    cmd.takeoff_procedure_id = _takeoff_procedure_or_default(
        getattr(leader_intent, "takeoff_procedure_id", mission_cmd.get("takeoff_procedure_code", None)),
        _takeoff_procedure_unspecified(),
    )
    cmd.takeoff_clearance_id = _takeoff_clearance_or_default(
        getattr(leader_intent, "takeoff_clearance_id", mission_cmd.get("takeoff_clearance_code", None)),
        _takeoff_clearance_unspecified(),
    )
    cmd.takeoff_interval_s = float(getattr(leader_intent, "takeoff_interval_s", mission_cmd.get("takeoff_interval_s", 0.0)))
    cmd.runway_slot_id = _runway_slot_or_default(
        getattr(leader_intent, "runway_slot_id", mission_cmd.get("runway_slot_code", None)),
        _runway_slot_unspecified(),
    )
    leader_takeoff_procedure_id = _takeoff_procedure_or_default(
        getattr(leader_intent, "takeoff_procedure_id", None),
        _takeoff_procedure_unspecified(),
    )
    leader_takeoff_clearance_id = _takeoff_clearance_or_default(
        getattr(leader_intent, "takeoff_clearance_id", None),
        _takeoff_clearance_unspecified(),
    )
    leader_takeoff_interval_s = float(getattr(leader_intent, "takeoff_interval_s", 0.0))
    leader_runway_slot_id = _runway_slot_or_default(
        getattr(leader_intent, "runway_slot_id", None),
        _runway_slot_unspecified(),
    )
    if (
        int(leader_takeoff_procedure_id) != int(_takeoff_procedure_unspecified())
        or int(leader_takeoff_clearance_id) != int(_takeoff_clearance_unspecified())
        or abs(leader_takeoff_interval_s) > 1.0e-9
        or int(leader_runway_slot_id) != int(_runway_slot_unspecified())
    ):
        cmd.takeoff_procedure_id = leader_takeoff_procedure_id
        cmd.takeoff_clearance_id = leader_takeoff_clearance_id
        cmd.takeoff_interval_s = leader_takeoff_interval_s
        cmd.runway_slot_id = leader_runway_slot_id

    leader_formation_id = int(getattr(leader_intent, "formation_id", 0))
    leader_form_offset_x = float(getattr(leader_intent, "form_offset_x", 0.0))
    leader_form_offset_y = float(getattr(leader_intent, "form_offset_y", 0.0))
    leader_form_offset_z = float(getattr(leader_intent, "form_offset_z", 0.0))
    if (
        leader_formation_id != 0
        or abs(leader_form_offset_x) > 1.0e-9
        or abs(leader_form_offset_y) > 1.0e-9
        or abs(leader_form_offset_z) > 1.0e-9
    ):
        cmd.formation_id = leader_formation_id
        cmd.form_offset_x = leader_form_offset_x
        cmd.form_offset_y = leader_form_offset_y
        cmd.form_offset_z = leader_form_offset_z
    else:
        cmd.formation_id = int(mission_cmd.get("formation_id", 0))
        cmd.form_offset_x = float(mission_cmd.get("form_offset_x", 0.0))
        cmd.form_offset_y = float(mission_cmd.get("form_offset_y", 0.0))
        cmd.form_offset_z = float(mission_cmd.get("form_offset_z", 0.0))

    cmd.roe_state = _resolve_int_field(leader_intent, mission_cmd, "roe_state")
    cmd.engagement_authority_holder_id = _resolve_int_field(
        leader_intent,
        mission_cmd,
        "engagement_authority_holder_id",
    )
    cmd.engagement_authority_grantor_id = _resolve_int_field(
        leader_intent,
        mission_cmd,
        "engagement_authority_grantor_id",
    )

    leader_assigned_target_id = int(getattr(leader_intent, "assigned_target_id", 0))
    leader_authorization_to_fire = bool(getattr(leader_intent, "authorization_to_fire", False))
    if leader_assigned_target_id > 0 or leader_authorization_to_fire:
        cmd.assigned_target_id = leader_assigned_target_id
        cmd.authorization_to_fire = leader_authorization_to_fire
    else:
        cmd.assigned_target_id = int(mission_cmd.get("assigned_target_id", 0))
        cmd.authorization_to_fire = bool(mission_cmd.get("authorization_to_fire", False))

    route_ref_id = coerce_positive_int(getattr(leader_intent, "route_ref_id", 0))
    if route_ref_id <= 0:
        route_ref_id = (
            coerce_positive_int(mission_cmd.get("route_ref_id", 0)) or infer_route_ref_id(loader)
        ) if has_active_waypoint_leg(loader) else 0

    recovery_base_id = coerce_positive_int(getattr(leader_intent, "recovery_base_id", 0))
    if recovery_base_id <= 0:
        recovery_base_id = infer_recovery_base_id(loader, task=getattr(loader, "task_order", None))
    recovery_runway_id = coerce_positive_int(getattr(leader_intent, "recovery_runway_id", 0))
    if recovery_runway_id <= 0:
        recovery_runway_id = infer_recovery_runway_id(loader, task=getattr(loader, "task_order", None))
    recovery_approach_type = _recovery_approach_type_or_default(
        getattr(leader_intent, "recovery_approach_type", None),
        infer_recovery_approach_type(loader, task=getattr(loader, "task_order", None)),
    )
    if hasattr(cmd, "route_ref_id"):
        cmd.route_ref_id = int(route_ref_id if int(cmd.command_code) == 3 else 0)
    if hasattr(cmd, "recovery_base_id"):
        cmd.recovery_base_id = int(recovery_base_id if int(cmd.command_code) == COMMAND_CODE_LANDING else 0)
    if hasattr(cmd, "recovery_runway_id"):
        cmd.recovery_runway_id = int(recovery_runway_id if int(cmd.command_code) == COMMAND_CODE_LANDING else 0)
    if hasattr(cmd, "recovery_approach_type"):
        cmd.recovery_approach_type = recovery_approach_type if int(cmd.command_code) == COMMAND_CODE_LANDING else _recovery_approach_none()
    return cmd
