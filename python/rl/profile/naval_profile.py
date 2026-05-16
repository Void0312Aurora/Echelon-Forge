from __future__ import annotations

from typing import Any

import ef_py

from python.rl.profile.common_core_base import coerce_positive_int, enum_or_default, enum_value, is_default_enum
from python.rl.profile.common_core_defaults import (
    authority_scope_default,
    command_relationship_default,
    coordination_mode_default,
    infer_recovery_site_id,
    infer_tactical_unit_type as _infer_common_tactical_unit_type,
    tactical_unit_type_default,
    task_family_default,
)


def _navy_service_profile() -> Any:
    return getattr(ef_py.ServiceProfile, "Navy")


def _naval_warfare_role_default() -> Any:
    namespace = getattr(ef_py, "NavalWarfareRole", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _naval_station_type_default() -> Any:
    namespace = getattr(ef_py, "NavalStationType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def infer_warfare_role_code(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    coordination_mode: Any = None,
) -> Any:
    namespace = getattr(ef_py, "NavalWarfareRole", None)
    if namespace is None:
        return 0

    name = str(task_name or "").strip().upper()
    if name == "TASK_SCREEN":
        return getattr(namespace, "ScreenCommander")
    if name == "TASK_SUPPORT":
        return getattr(namespace, "LogisticsCoordinator")
    if name in {"TASK_PATROL", "TASK_SEA_CONTROL"}:
        return getattr(namespace, "SeaControlCommander")
    if name in {"TASK_AIR_DEFENSE", "TASK_AAW"}:
        return getattr(namespace, "AirDefenseCommander")

    family_value = enum_value(task_family)
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Escort")):
        mode_value = enum_value(coordination_mode)
        if mode_value == enum_value(getattr(ef_py.CoordinationMode, "Support")):
            return getattr(namespace, "LogisticsCoordinator")
        return getattr(namespace, "ScreenCommander")
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Patrol")):
        return getattr(namespace, "SeaControlCommander")
    return getattr(namespace, "Unspecified")


def infer_naval_station_type(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    coordination_mode: Any = None,
) -> Any:
    namespace = getattr(ef_py, "NavalStationType", None)
    if namespace is None:
        return 0

    name = str(task_name or "").strip().upper()
    if name == "TASK_SCREEN":
        return getattr(namespace, "Screen")
    if name == "TASK_SUPPORT":
        return getattr(namespace, "Support")
    if name in {"TASK_PATROL", "TASK_SEA_CONTROL"}:
        return getattr(namespace, "PatrolStation")

    family_value = enum_value(task_family)
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Escort")):
        mode_value = enum_value(coordination_mode)
        if mode_value == enum_value(getattr(ef_py.CoordinationMode, "Support")):
            return getattr(namespace, "Support")
        return getattr(namespace, "Screen")
    if family_value == enum_value(getattr(ef_py.TaskFamily, "Patrol")):
        return getattr(namespace, "PatrolStation")
    return getattr(namespace, "Unspecified")


def infer_naval_task_family(*, task_name: str | None = None, task_type: Any = None, phase_name: str | None = None) -> Any:
    name = str(task_name or "").strip().upper()
    phase = str(phase_name or "").strip().lower()
    if name in {"TASK_SCREEN", "TASK_ESCORT", "TASK_SUPPORT"}:
        return getattr(ef_py.TaskFamily, "Escort")
    if name in {"TASK_PATROL", "TASK_STATION", "TASK_SEA_CONTROL"}:
        return getattr(ef_py.TaskFamily, "Patrol")
    if name in {"TASK_RECOVER", "TASK_RTB", "TASK_WITHDRAW"}:
        return getattr(ef_py.TaskFamily, "Recover")
    if phase in {"screen", "support", "escort"}:
        return getattr(ef_py.TaskFamily, "Escort")
    if phase in {"station", "patrol"}:
        return getattr(ef_py.TaskFamily, "Patrol")
    if phase in {"recover", "withdraw"}:
        return getattr(ef_py.TaskFamily, "Recover")
    if task_type is not None and int(enum_value(task_type)) > 0:
        if int(enum_value(task_type)) == int(enum_value(getattr(ef_py.TaskType, "RTB", 0))):
            return getattr(ef_py.TaskFamily, "Recover")
        if int(enum_value(task_type)) in {
            int(enum_value(getattr(ef_py.TaskType, "CAP", 0))),
            int(enum_value(getattr(ef_py.TaskType, "CAPMission", 0))),
        }:
            return getattr(ef_py.TaskFamily, "Patrol")
    return task_family_default()


def infer_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
) -> Any:
    name = str(task_name or "").strip().upper()
    if name in {"TASK_SCREEN", "TASK_ESCORT"}:
        return getattr(ef_py.CoordinationMode, "Screen")
    if name in {"TASK_SUPPORT"}:
        return getattr(ef_py.CoordinationMode, "Support")
    if name in {"TASK_RECOVER", "TASK_WITHDRAW", "TASK_RTB"}:
        return getattr(ef_py.CoordinationMode, "Detached")

    phase = str(phase_name or "").strip().lower()
    if phase in {"screen", "escort"}:
        return getattr(ef_py.CoordinationMode, "Screen")
    if phase in {"support"}:
        return getattr(ef_py.CoordinationMode, "Support")
    if phase in {"recover", "withdraw"}:
        return getattr(ef_py.CoordinationMode, "Detached")

    family = enum_value(task_family)
    if family == enum_value(getattr(ef_py.TaskFamily, "Escort")):
        return getattr(ef_py.CoordinationMode, "Screen")
    if family == enum_value(getattr(ef_py.TaskFamily, "Recover")):
        return getattr(ef_py.CoordinationMode, "Detached")

    unit_type_value = enum_value(tactical_unit_type)
    if unit_type_value in {
        enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")),
        enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")),
        enum_value(getattr(ef_py.TacticalUnitType, "CommandNode")),
    }:
        return getattr(ef_py.CoordinationMode, "Screen")
    return getattr(ef_py.CoordinationMode, "Independent")


def infer_tactical_unit_type(order: Any | None) -> Any:
    if order is None:
        return getattr(ef_py.TacticalUnitType, "Platform")
    current = getattr(order, "tactical_unit_type", tactical_unit_type_default())
    if not is_default_enum(current, tactical_unit_type_default()):
        return current
    if coerce_positive_int(getattr(order, "task_group_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "CommandNode")
    if coerce_positive_int(getattr(order, "parent_node_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")
    return _infer_common_tactical_unit_type(order)


def is_patrol_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Patrol"))


def is_recover_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Recover"))


def resolved_task_family(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> Any:
    if task is not None:
        task_family = getattr(task, "task_family", task_family_default())
        if not is_default_enum(task_family, task_family_default()):
            return task_family
        task_type = getattr(task, "task_type", None)
    else:
        task_type = None
    return infer_naval_task_family(task_name=task_name, task_type=task_type, phase_name=phase_name)


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
    }
    for field_name, namespace in enum_fields.items():
        if field_name not in normalized:
            continue
        default_value = normalized.get(field_name)
        if field_name == "task_type":
            default_value = getattr(ef_py.TaskType, "Idle")
        elif field_name == "service_profile":
            default_value = _navy_service_profile()
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

    if "service_profile" not in normalized:
        normalized["service_profile"] = _navy_service_profile()

    task_family = enum_or_default(
        ef_py.TaskFamily,
        normalized.get("task_family"),
        infer_naval_task_family(
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            task_type=normalized.get("task_type"),
            phase_name=str(normalized.get("phase_name", "") or "").strip().lower() or None,
        ),
    )
    if "task_family" not in normalized:
        normalized["task_family"] = task_family

    if "command_relationship" not in normalized:
        normalized["command_relationship"] = command_relationship_default()
    if "authority_scope" not in normalized:
        normalized["authority_scope"] = authority_scope_default()

    tactical_unit_type = enum_or_default(
        ef_py.TacticalUnitType,
        normalized.get("tactical_unit_type"),
        tactical_unit_type_default(),
    )
    if is_default_enum(tactical_unit_type, tactical_unit_type_default()):
        if coerce_positive_int(normalized.get("task_group_id", 0)) > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "CommandNode")
        elif coerce_positive_int(normalized.get("parent_node_id", 0)) > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "TacticalUnit")
        else:
            tactical_unit_type = infer_tactical_unit_type(type("_Proxy", (), normalized)())
        normalized["tactical_unit_type"] = tactical_unit_type

    if "coordination_mode" not in normalized:
        normalized["coordination_mode"] = infer_coordination_mode(
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            task_family=normalized.get("task_family", task_family),
            phase_name=str(normalized.get("phase_name", "") or "").strip().lower() or None,
            tactical_unit_type=normalized.get("tactical_unit_type", tactical_unit_type),
        )

    if "warfare_role_code" not in normalized:
        normalized["warfare_role_code"] = infer_warfare_role_code(
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            task_family=normalized.get("task_family", task_family),
            coordination_mode=normalized.get("coordination_mode"),
        )

    if "naval_station_type" not in normalized:
        normalized["naval_station_type"] = infer_naval_station_type(
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            task_family=normalized.get("task_family", task_family),
            coordination_mode=normalized.get("coordination_mode"),
        )

    if coerce_positive_int(normalized.get("officer_in_tactical_command", 0)) <= 0:
        otc_id = coerce_positive_int(normalized.get("task_group_id", 0))
        if otc_id <= 0:
            otc_id = coerce_positive_int(normalized.get("parent_node_id", 0))
        if otc_id > 0:
            normalized["officer_in_tactical_command"] = int(otc_id)

    recovery_site_id = coerce_positive_int(normalized.get("recovery_site_id", 0))
    if recovery_site_id <= 0:
        proxy = type("_Proxy", (), normalized)()
        recovery_site_id = infer_recovery_site_id(proxy)
        if recovery_site_id > 0:
            normalized["recovery_site_id"] = int(recovery_site_id)
    return normalized


def task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
    if task is None:
        return 0.0, 0.0, float(fallback_phase_id)
    primary = float(enum_value(getattr(task, "task_family", task_family_default())))
    secondary = float(enum_value(getattr(task, "coordination_mode", coordination_mode_default())))
    tertiary = float(enum_value(getattr(task, "tactical_unit_type", tactical_unit_type_default())))
    return primary, secondary, tertiary if tertiary > 0.0 else float(fallback_phase_id)


def infer_route_ref_id(loader: Any) -> int:
    _ = loader
    return 0


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    if task is not None:
        return coerce_positive_int(getattr(task, "recovery_base_id", 0))
    return coerce_positive_int(getattr(getattr(loader, "task_order", None), "recovery_base_id", 0))


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    if task is not None:
        return coerce_positive_int(getattr(task, "recovery_runway_id", 0))
    return coerce_positive_int(getattr(getattr(loader, "task_order", None), "recovery_runway_id", 0))


def infer_recovery_approach_type(loader: Any, task: Any | None = None):
    _ = loader
    if task is not None and hasattr(task, "recovery_approach_type"):
        return getattr(task, "recovery_approach_type")
    return 0


def build_kernel_mission_command(loader: Any):
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    task_order = getattr(loader, "task_order", None)
    if task_order is not None:
        heading_deg = float(getattr(task_order, "station_heading_deg", getattr(task_order, "target_heading_deg", 0.0)))
        altitude_m = float(getattr(task_order, "target_altitude_m", 0.0))
        speed_mps = float(getattr(task_order, "target_speed_mps", 0.0))
    else:
        mission_cmd = getattr(loader, "mission_cmd", {}) or {}
        heading_deg = float(mission_cmd.get("target_heading", 0.0))
        altitude_m = float(mission_cmd.get("target_altitude", 0.0))
        speed_mps = float(mission_cmd.get("target_speed", 0.0))

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = float(heading_deg)
    cmd.cmd_altitude_m = float(altitude_m)
    cmd.cmd_speed_mps = float(speed_mps)
    if hasattr(cmd, "route_ref_id"):
        cmd.route_ref_id = 0
    if hasattr(cmd, "recovery_base_id"):
        cmd.recovery_base_id = infer_recovery_base_id(loader, task=task_order)
    if hasattr(cmd, "recovery_runway_id"):
        cmd.recovery_runway_id = infer_recovery_runway_id(loader, task=task_order)
    if hasattr(cmd, "recovery_approach_type"):
        cmd.recovery_approach_type = infer_recovery_approach_type(loader, task=task_order)
    if isinstance(scenario_data, dict):
        mission_cfg = scenario_data.get("mission_command", None)
        if isinstance(mission_cfg, dict):
            cmd.command_code = int(mission_cfg.get("command_code", cmd.command_code))
            cmd.cmd_heading_deg = float(mission_cfg.get("target_heading", cmd.cmd_heading_deg))
            cmd.cmd_altitude_m = float(mission_cfg.get("target_altitude", cmd.cmd_altitude_m))
            cmd.cmd_speed_mps = float(mission_cfg.get("target_speed", cmd.cmd_speed_mps))
    return cmd
