from __future__ import annotations

from typing import Any

import ef_py

from python.coercion import coerce_nonnegative_int
from python.rl.profile.common_core_base import coerce_positive_int, enum_or_default, enum_value, is_default_enum
from python.rl.profile.common_core_defaults import (
    authority_scope_default,
    command_relationship_default,
    coordination_mode_default,
    coordination_mode_independent,
    infer_tactical_unit_id as _infer_common_tactical_unit_id,
    tactical_unit_type_default,
    task_family_default,
)


def _army_service_profile() -> Any:
    return getattr(ef_py.ServiceProfile, "Army")


def _support_command_relationship() -> Any:
    return getattr(ef_py.CommandRelationship, "Support")


def _support_coordination_mode() -> Any:
    return getattr(ef_py.CoordinationMode, "Support")


def _tactical_unit_type() -> Any:
    return getattr(ef_py.TacticalUnitType, "TacticalUnit")


def _transit_task_family() -> Any:
    return getattr(ef_py.TaskFamily, "Transit")


def _defend_task_family() -> Any:
    return getattr(ef_py.TaskFamily, "Defend")


def _ground_task_mode_default() -> Any:
    namespace = getattr(ef_py, "GroundTaskMode", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _ground_status_phase_default() -> Any:
    namespace = getattr(ef_py, "GroundStatusPhase", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def infer_ground_task_mode(
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    order: Any | None = None,
) -> Any:
    namespace = getattr(ef_py, "GroundTaskMode", None)
    if namespace is None:
        return 0

    current = getattr(order, "ground_task_mode", _ground_task_mode_default()) if order is not None else _ground_task_mode_default()
    if not is_default_enum(current, _ground_task_mode_default()):
        return current

    name = str(task_name or "").strip().upper()
    if name == "TASK_OCCUPY":
        return getattr(namespace, "OccupyStatic", _ground_task_mode_default())
    if name == "TASK_SUPPORT":
        return getattr(namespace, "SupportStatic", _ground_task_mode_default())
    if name == "TASK_MOVE":
        return getattr(namespace, "MoveStatic", _ground_task_mode_default())

    phase = str(phase_name or "").strip().lower()
    if phase in {"move", "movement", "advance", "transit"}:
        return getattr(namespace, "MoveStatic", _ground_task_mode_default())
    if phase in {"occupy", "defend"}:
        return getattr(namespace, "OccupyStatic", _ground_task_mode_default())
    if phase == "support":
        return getattr(namespace, "SupportStatic", _ground_task_mode_default())
    if phase in {"hold", "holding", "static"}:
        return getattr(namespace, "MoveStatic", _ground_task_mode_default())
    return _ground_task_mode_default()


def infer_ground_status_phase(
    *,
    ground_task_mode: Any = None,
    phase_name: str | None = None,
) -> Any:
    namespace = getattr(ef_py, "GroundStatusPhase", None)
    if namespace is None:
        return 0

    phase = str(phase_name or "").strip().lower()
    if phase in {"complete", "completed"}:
        return getattr(namespace, "Complete", _ground_status_phase_default())
    if phase in {"preparing", "prepare"}:
        return getattr(namespace, "Preparing", _ground_status_phase_default())

    mode_value = enum_value(ground_task_mode, enum_value(_ground_task_mode_default()))
    task_mode = getattr(ef_py, "GroundTaskMode", None)
    if task_mode is not None:
        if mode_value == enum_value(getattr(task_mode, "OccupyStatic", 0)):
            return getattr(namespace, "OccupyingStatic", _ground_status_phase_default())
        if mode_value == enum_value(getattr(task_mode, "SupportStatic", 0)):
            return getattr(namespace, "SupportingStatic", _ground_status_phase_default())
        if mode_value == enum_value(getattr(task_mode, "MoveStatic", 0)):
            return getattr(namespace, "HoldingStatic", _ground_status_phase_default())
    return getattr(namespace, "Assigned", _ground_status_phase_default())


def infer_ground_task_family(*, task_name: str | None = None, task_type: Any = None, phase_name: str | None = None) -> Any:
    name = str(task_name or "").strip().upper()
    if name == "TASK_MOVE":
        return _transit_task_family()
    if name in {"TASK_OCCUPY", "TASK_SUPPORT"}:
        return _defend_task_family()

    phase = str(phase_name or "").strip().lower()
    if phase in {"move", "movement", "advance", "transit"}:
        return _transit_task_family()
    if phase in {"occupy", "support", "defend", "hold"}:
        return _defend_task_family()

    task_type_value = enum_value(task_type)
    if task_type_value == enum_value(getattr(ef_py.TaskType, "RTB", 0)):
        return getattr(ef_py.TaskFamily, "Recover", task_family_default())
    return task_family_default()


def infer_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
) -> Any:
    _ = (task_family, tactical_unit_type)
    name = str(task_name or "").strip().upper()
    if name == "TASK_SUPPORT":
        return _support_coordination_mode()

    phase = str(phase_name or "").strip().lower()
    if phase == "support":
        return _support_coordination_mode()
    return coordination_mode_independent()


def infer_command_relationship(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
) -> Any:
    _ = task_family
    name = str(task_name or "").strip().upper()
    if name == "TASK_SUPPORT":
        return _support_command_relationship()

    phase = str(phase_name or "").strip().lower()
    if phase == "support":
        return _support_command_relationship()
    return command_relationship_default()


def infer_tactical_unit_type(order: Any | None) -> Any:
    if order is None:
        return _tactical_unit_type()
    current = getattr(order, "tactical_unit_type", tactical_unit_type_default())
    if not is_default_enum(current, tactical_unit_type_default()):
        return current
    return _tactical_unit_type()


def infer_tactical_unit_id(order: Any | None, *, tactical_unit_type: Any = None, default_id: int = 0) -> int:
    if order is None:
        return coerce_positive_int(default_id)
    unit_type = tactical_unit_type if tactical_unit_type is not None else infer_tactical_unit_type(order)
    if enum_value(unit_type) != enum_value(_tactical_unit_type()):
        return _infer_common_tactical_unit_id(order, tactical_unit_type=unit_type, default_id=default_id)

    for raw_value in (
        getattr(order, "supporting_node_id", 0),
        getattr(order, "element_id", 0),
        getattr(order, "assignee_id", 0),
        default_id,
    ):
        value = coerce_positive_int(raw_value)
        if value > 0:
            return value
    return 0


def resolved_task_family(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> Any:
    if task is not None:
        task_family = getattr(task, "task_family", task_family_default())
        if not is_default_enum(task_family, task_family_default()):
            return task_family
    return infer_ground_task_family(
        task_name=task_name,
        task_type=getattr(task, "task_type", None) if task is not None else None,
        phase_name=phase_name,
    )


def is_patrol_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Patrol", 0))


def is_recover_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return enum_value(family) == enum_value(getattr(ef_py.TaskFamily, "Recover", 0))


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
    if hasattr(ef_py, "GroundTaskMode"):
        enum_fields["ground_task_mode"] = ef_py.GroundTaskMode
    if hasattr(ef_py, "GroundStatusPhase"):
        enum_fields["ground_status_phase"] = ef_py.GroundStatusPhase
    for field_name, namespace in enum_fields.items():
        if field_name not in normalized:
            continue
        default_value = normalized.get(field_name)
        if field_name == "task_type":
            default_value = getattr(ef_py.TaskType, "Idle")
        elif field_name == "service_profile":
            default_value = _army_service_profile()
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
        elif field_name == "ground_task_mode":
            default_value = _ground_task_mode_default()
        elif field_name == "ground_status_phase":
            default_value = _ground_status_phase_default()
        normalized[field_name] = enum_or_default(namespace, normalized.get(field_name), default_value)

    if "service_profile" not in normalized:
        normalized["service_profile"] = _army_service_profile()

    task_name = str(normalized.get("task_name", "") or "").strip().upper() or None
    phase_name = str(normalized.get("phase_name", "") or "").strip().lower() or None
    task_family = enum_or_default(
        ef_py.TaskFamily,
        normalized.get("task_family"),
        infer_ground_task_family(task_name=task_name, task_type=normalized.get("task_type"), phase_name=phase_name),
    )
    if "task_family" not in normalized:
        normalized["task_family"] = task_family

    tactical_unit_type = enum_or_default(
        ef_py.TacticalUnitType,
        normalized.get("tactical_unit_type"),
        tactical_unit_type_default(),
    )
    if "tactical_unit_type" not in normalized or is_default_enum(tactical_unit_type, tactical_unit_type_default()):
        normalized["tactical_unit_type"] = _tactical_unit_type()

    if "authority_scope" not in normalized:
        normalized["authority_scope"] = authority_scope_default()

    if task_name == "TASK_SUPPORT":
        if "command_relationship" not in normalized:
            normalized["command_relationship"] = _support_command_relationship()
        if "coordination_mode" not in normalized:
            normalized["coordination_mode"] = _support_coordination_mode()
    else:
        if "command_relationship" not in normalized:
            normalized["command_relationship"] = command_relationship_default()
        if "coordination_mode" not in normalized:
            normalized["coordination_mode"] = infer_coordination_mode(
                task_name=task_name,
                task_family=normalized.get("task_family", task_family),
                phase_name=phase_name,
                tactical_unit_type=normalized.get("tactical_unit_type"),
            )
    return normalized


def task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
    if task is None:
        return 0.0, 0.0, float(fallback_phase_id)
    primary = float(enum_value(getattr(task, "task_family", task_family_default())))
    secondary = float(enum_value(getattr(task, "coordination_mode", coordination_mode_default())))
    tertiary = float(enum_value(getattr(task, "tactical_unit_type", tactical_unit_type_default())))
    return primary, secondary, tertiary if tertiary > 0.0 else float(fallback_phase_id)


# Local name preserved as a thin alias; semantics owned by python.coercion.
_coerce_nonnegative_int = coerce_nonnegative_int


def _mission_int_value(leader_intent: Any, mission_cmd: dict[str, Any], field_name: str, default: int = 0) -> int:
    if leader_intent is not None and hasattr(leader_intent, field_name):
        return _coerce_nonnegative_int(getattr(leader_intent, field_name, default))
    return _coerce_nonnegative_int(mission_cmd.get(field_name, default))


def _mission_float_value(leader_intent: Any, mission_cmd: dict[str, Any], field_name: str, fallback_name: str, default: float = 0.0) -> float:
    if leader_intent is not None and hasattr(leader_intent, field_name):
        return float(getattr(leader_intent, field_name, default))
    return float(mission_cmd.get(field_name, mission_cmd.get(fallback_name, default)))


def _mission_positive_int_value(
    *,
    leader_intent: Any,
    task_order: Any,
    mission_cmd: dict[str, Any],
    field_name: str,
    fallback_names: tuple[str, ...] = (),
) -> int:
    for source in (leader_intent, task_order):
        if source is None:
            continue
        for name in (field_name, *fallback_names):
            if not hasattr(source, name):
                continue
            value = coerce_positive_int(getattr(source, name, 0))
            if value > 0:
                return value
    for name in (field_name, *fallback_names):
        value = coerce_positive_int(mission_cmd.get(name, 0))
        if value > 0:
            return value
    return 0


def _mission_positive_float_value(
    *,
    leader_intent: Any,
    task_order: Any,
    mission_cmd: dict[str, Any],
    field_name: str,
    default: float,
) -> float:
    for source in (leader_intent, task_order):
        if source is None or not hasattr(source, field_name):
            continue
        try:
            value = float(getattr(source, field_name, default))
        except Exception:
            continue
        if value > 0.0:
            return value
    try:
        value = float(mission_cmd.get(field_name, default))
    except Exception:
        return float(default)
    return value if value > 0.0 else float(default)


def _mission_ground_task_mode(
    *,
    leader_intent: Any,
    task_order: Any,
    mission_cmd: dict[str, Any],
    task_name: str | None,
    phase_name: str | None,
) -> Any:
    namespace = getattr(ef_py, "GroundTaskMode", None)
    if namespace is None:
        return 0
    default_value = _ground_task_mode_default()
    for source in (leader_intent, task_order):
        if source is None or not hasattr(source, "ground_task_mode"):
            continue
        value = enum_or_default(namespace, getattr(source, "ground_task_mode", default_value), default_value)
        if not is_default_enum(value, default_value):
            return value
    if "ground_task_mode" in mission_cmd:
        value = enum_or_default(namespace, mission_cmd.get("ground_task_mode"), default_value)
        if not is_default_enum(value, default_value):
            return value
    return infer_ground_task_mode(task_name=task_name, phase_name=phase_name, order=task_order)


def build_kernel_mission_command(loader: Any) -> ef_py.MissionCommand:
    """Build the G0/G1 ground static command slice through MissionCommandGround."""

    cmd = ef_py.MissionCommand()
    cmd.active = True
    mission_cmd = getattr(loader, "mission_cmd", {}) or {}
    leader_intent = getattr(loader, "leader_intent", None)
    task_order = getattr(loader, "task_order", None)
    task_name = str(getattr(loader, "c2_task_name", "") or mission_cmd.get("task_name", "") or "").strip().upper() or None
    phase_name = str(getattr(loader, "mission_phase_name", "") or mission_cmd.get("phase_name", "") or "").strip().lower() or None

    cmd.command_code = _mission_int_value(leader_intent, mission_cmd, "command_code")
    cmd.cmd_heading_deg = _mission_float_value(leader_intent, mission_cmd, "cmd_heading_deg", "target_heading")
    cmd.cmd_altitude_m = _mission_float_value(leader_intent, mission_cmd, "cmd_altitude_m", "target_altitude")
    cmd.cmd_speed_mps = _mission_float_value(leader_intent, mission_cmd, "cmd_speed_mps", "target_speed")

    cmd.formation_id = _mission_int_value(leader_intent, mission_cmd, "formation_id")
    cmd.form_offset_x = _mission_float_value(leader_intent, mission_cmd, "form_offset_x", "form_offset_x")
    cmd.form_offset_y = _mission_float_value(leader_intent, mission_cmd, "form_offset_y", "form_offset_y")
    cmd.form_offset_z = _mission_float_value(leader_intent, mission_cmd, "form_offset_z", "form_offset_z")

    cmd.assigned_target_id = _mission_int_value(leader_intent, mission_cmd, "assigned_target_id")
    if leader_intent is not None and hasattr(leader_intent, "authorization_to_fire"):
        cmd.authorization_to_fire = bool(getattr(leader_intent, "authorization_to_fire", False))
    else:
        cmd.authorization_to_fire = bool(mission_cmd.get("authorization_to_fire", False))
    if hasattr(cmd, "ground_task_mode"):
        cmd.ground_task_mode = _mission_ground_task_mode(
            leader_intent=leader_intent,
            task_order=task_order,
            mission_cmd=mission_cmd,
            task_name=task_name,
            phase_name=phase_name,
        )
    if hasattr(cmd, "objective_area_id"):
        cmd.objective_area_id = _mission_positive_int_value(
            leader_intent=leader_intent,
            task_order=task_order,
            mission_cmd=mission_cmd,
            field_name="objective_area_id",
            fallback_names=("supported_node_id", "task_group_id"),
        )
    if hasattr(cmd, "objective_node_id"):
        cmd.objective_node_id = _mission_positive_int_value(
            leader_intent=leader_intent,
            task_order=task_order,
            mission_cmd=mission_cmd,
            field_name="objective_node_id",
            fallback_names=("supported_node_id", "supporting_node_id", "assignee_id"),
        )
    if hasattr(cmd, "ground_commander_id"):
        cmd.ground_commander_id = _mission_positive_int_value(
            leader_intent=leader_intent,
            task_order=task_order,
            mission_cmd=mission_cmd,
            field_name="ground_commander_id",
            fallback_names=("officer_in_tactical_command", "parent_node_id", "task_group_id"),
        )
    if hasattr(cmd, "tactical_cadence_hz"):
        cmd.tactical_cadence_hz = _mission_positive_float_value(
            leader_intent=leader_intent,
            task_order=task_order,
            mission_cmd=mission_cmd,
            field_name="tactical_cadence_hz",
            default=1.0,
        )
    return cmd


def infer_route_ref_id(loader: Any) -> int:
    _ = loader
    return 0


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    _ = (loader, task)
    return 0


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    _ = (loader, task)
    return 0


def infer_recovery_approach_type(loader: Any, task: Any | None = None):
    _ = loader
    namespace = getattr(ef_py, "RecoveryApproachType", object())
    default_value = getattr(namespace, "None", 0)
    if task is not None and hasattr(task, "recovery_approach_type"):
        return enum_or_default(namespace, getattr(task, "recovery_approach_type", default_value), default_value)
    return default_value
