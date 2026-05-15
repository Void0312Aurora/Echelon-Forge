from __future__ import annotations

from typing import Any

import ef_py


def _coerce_positive_int(raw_value: Any) -> int:
    try:
        value = int(raw_value)
    except Exception:
        return 0
    return value if value > 0 else 0


def _enum_or_default(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        text = str(raw_value).strip()
        if not text:
            return default_value
        direct = getattr(namespace, text, None)
        if direct is not None:
            return direct
        normalized = text.replace("_", "").replace(" ", "").lower()
        for name in dir(namespace):
            if name.startswith("_"):
                continue
            if name.replace("_", "").lower() == normalized:
                return getattr(namespace, name)
        return default_value
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value


def _enum_value(raw_value: Any, default_value: int = 0) -> int:
    try:
        return int(raw_value)
    except Exception:
        return int(default_value)


def _is_default_enum(raw_value: Any, default_value: Any) -> bool:
    return _enum_value(raw_value) == _enum_value(default_value)


def _service_profile_default() -> Any:
    return getattr(ef_py.ServiceProfile, "AirForce")


def _task_family_default() -> Any:
    return getattr(ef_py.TaskFamily, "Unspecified")


def _tactical_unit_type_default() -> Any:
    return getattr(ef_py.TacticalUnitType, "Unspecified")


def _command_relationship_default() -> Any:
    return getattr(ef_py.CommandRelationship, "TACON")


def _authority_scope_default() -> Any:
    return getattr(ef_py.AuthorityScope, "Tactical")


def _coordination_mode_default() -> Any:
    return getattr(ef_py.CoordinationMode, "Unspecified")


def _coordination_mode_independent() -> Any:
    return getattr(ef_py.CoordinationMode, "Independent")


def _coordination_mode_attached() -> Any:
    return getattr(ef_py.CoordinationMode, "Attached")


def _coordination_mode_recover() -> Any:
    return getattr(ef_py.CoordinationMode, "Recover")


def _takeoff_procedure_default() -> Any:
    namespace = getattr(ef_py, "TakeoffProcedureType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _takeoff_clearance_default() -> Any:
    namespace = getattr(ef_py, "TakeoffClearanceState", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _runway_slot_default() -> Any:
    namespace = getattr(ef_py, "RunwaySlotPosition", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _task_name_from_task_type(task_type: Any) -> str | None:
    mapping = {
        _enum_value(getattr(ef_py.TaskType, "Scramble")): "TASK_SCRAMBLE",
        _enum_value(getattr(ef_py.TaskType, "CAP")): "TASK_CAP",
        _enum_value(getattr(ef_py.TaskType, "CAPMission")): "TASK_CAP",
        _enum_value(getattr(ef_py.TaskType, "RTB")): "TASK_RTB",
        _enum_value(getattr(ef_py.TaskType, "RecoverLand")): "TASK_RECOVER_LAND",
    }
    return mapping.get(_enum_value(task_type), None)


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
    if phase in {
        "departure",
        "transit_to_station",
        "establish_cap",
        "on_station",
        "reposition",
    }:
        return getattr(ef_py.TaskFamily, "Patrol")
    if phase in {"rtb", "approach_armed", "landing_final", "rollout"}:
        return getattr(ef_py.TaskFamily, "Recover")
    return _task_family_default()


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

    family_value = _enum_value(task_family, _enum_value(_task_family_default()))
    if family_value == _enum_value(getattr(ef_py.TaskFamily, "Transit")):
        return getattr(ef_py.TaskType, "Scramble")
    if family_value == _enum_value(getattr(ef_py.TaskFamily, "Patrol")):
        return getattr(ef_py.TaskType, "CAPMission") if bool(has_waypoints) else getattr(ef_py.TaskType, "CAP")
    if family_value == _enum_value(getattr(ef_py.TaskFamily, "Recover")):
        return getattr(ef_py.TaskType, "RTB")
    return getattr(ef_py.TaskType, "Idle")


def resolved_task_family(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> Any:
    if task is not None:
        task_family = getattr(task, "task_family", _task_family_default())
        if not _is_default_enum(task_family, _task_family_default()):
            return task_family
        task_type = getattr(task, "task_type", None)
    else:
        task_type = None
    return infer_air_task_family(task_name=task_name, task_type=task_type, phase_name=phase_name)


def is_patrol_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return _enum_value(family) == _enum_value(getattr(ef_py.TaskFamily, "Patrol"))


def is_recover_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    family = resolved_task_family(task, task_name=task_name, phase_name=phase_name)
    return _enum_value(family) == _enum_value(getattr(ef_py.TaskFamily, "Recover"))


def infer_tactical_unit_type(order: Any | None) -> Any:
    if order is None:
        return getattr(ef_py.TacticalUnitType, "Platform")
    current = getattr(order, "tactical_unit_type", _tactical_unit_type_default())
    if not _is_default_enum(current, _tactical_unit_type_default()):
        return current

    if _coerce_positive_int(getattr(order, "package_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if _coerce_positive_int(getattr(order, "element_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")

    assignee_kind = _enum_value(getattr(order, "assignee_kind", 0))
    if assignee_kind == _enum_value(getattr(ef_py.AssigneeKind, "Package")):
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if assignee_kind == _enum_value(getattr(ef_py.AssigneeKind, "Element")):
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")
    return getattr(ef_py.TacticalUnitType, "Platform")


def infer_recovery_site_id(order: Any | None) -> int:
    if order is None:
        return 0
    current = _coerce_positive_int(getattr(order, "recovery_site_id", 0))
    if current > 0:
        return current
    runway_id = _coerce_positive_int(getattr(order, "recovery_runway_id", 0))
    if runway_id > 0:
        return runway_id
    return _coerce_positive_int(getattr(order, "recovery_base_id", 0))


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
                default_value = _service_profile_default()
            elif field_name == "task_family":
                default_value = _task_family_default()
            elif field_name == "tactical_unit_type":
                default_value = _tactical_unit_type_default()
            elif field_name == "command_relationship":
                default_value = _command_relationship_default()
            elif field_name == "authority_scope":
                default_value = _authority_scope_default()
            elif field_name == "coordination_mode":
                default_value = _coordination_mode_default()
            normalized[field_name] = _enum_or_default(namespace, normalized.get(field_name), default_value)

    has_waypoints = bool(list(normalized.get("waypoints", []) or []))
    task_family = _enum_or_default(
        ef_py.TaskFamily,
        normalized.get("task_family"),
        infer_air_task_family(task_type=normalized.get("task_type")),
    )
    if "task_family" not in normalized:
        normalized["task_family"] = task_family

    if "task_type" not in normalized:
        inferred_task_type = infer_air_task_type(
            task_family=normalized.get("task_family", task_family),
            task_name=str(normalized.get("task_name", "") or "").strip().upper() or None,
            has_waypoints=has_waypoints,
        )
        normalized["task_type"] = inferred_task_type

    if "service_profile" not in normalized:
        normalized["service_profile"] = _service_profile_default()
    if "command_relationship" not in normalized:
        normalized["command_relationship"] = _command_relationship_default()
    if "authority_scope" not in normalized:
        normalized["authority_scope"] = _authority_scope_default()

    task_group_id = _coerce_positive_int(normalized.get("task_group_id", 0))
    package_id = _coerce_positive_int(normalized.get("package_id", 0))
    if task_group_id <= 0 and package_id > 0:
        normalized["task_group_id"] = int(package_id)

    tactical_unit_type = _enum_or_default(
        ef_py.TacticalUnitType,
        normalized.get("tactical_unit_type"),
        _tactical_unit_type_default(),
    )
    if _is_default_enum(tactical_unit_type, _tactical_unit_type_default()):
        if package_id > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "MissionPackage")
        elif _coerce_positive_int(normalized.get("element_id", 0)) > 0:
            tactical_unit_type = getattr(ef_py.TacticalUnitType, "TacticalUnit")
        else:
            assignee_kind = _enum_or_default(
                ef_py.AssigneeKind,
                normalized.get("assignee_kind"),
                getattr(ef_py.AssigneeKind, "Aircraft"),
            )
            if _enum_value(assignee_kind) == _enum_value(getattr(ef_py.AssigneeKind, "Package")):
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "MissionPackage")
            elif _enum_value(assignee_kind) == _enum_value(getattr(ef_py.AssigneeKind, "Element")):
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "TacticalUnit")
            else:
                tactical_unit_type = getattr(ef_py.TacticalUnitType, "Platform")
        normalized["tactical_unit_type"] = tactical_unit_type

    recovery_site_id = _coerce_positive_int(normalized.get("recovery_site_id", 0))
    if recovery_site_id <= 0:
        runway_id = _coerce_positive_int(normalized.get("recovery_runway_id", 0))
        base_id = _coerce_positive_int(normalized.get("recovery_base_id", 0))
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

    task_type = _enum_value(getattr(task, "task_type", 0))
    if task_type <= 0:
        task_type = _enum_value(
            infer_air_task_type(
                task_family=getattr(task, "task_family", _task_family_default()),
                has_waypoints=_enum_value(getattr(task, "station_type", 0)) == _enum_value(getattr(ef_py.StationType, "RouteCAP")),
            )
        )
    station_type = _enum_value(getattr(task, "station_type", 0))
    coordination_mode = _enum_value(getattr(task, "coordination_mode", 0))

    primary_code = float(task_type)
    detail_code = float(station_type if station_type > 0 else coordination_mode)
    phase_code = float(fallback_phase_id)
    return primary_code, detail_code, phase_code


def infer_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
) -> Any:
    recover_family = getattr(ef_py.TaskFamily, "Recover")
    if _enum_value(task_family) == _enum_value(recover_family):
        return _coordination_mode_recover()

    name = str(task_name or "").strip().upper()
    if name in {"TASK_RTB", "TASK_RECOVER_LAND"}:
        return _coordination_mode_recover()

    phase = str(phase_name or "").strip().lower()
    if phase in {"rtb", "approach_armed", "landing_final", "rollout"}:
        return _coordination_mode_recover()

    unit_type_value = _enum_value(tactical_unit_type)
    if unit_type_value in {
        _enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")),
        _enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")),
    }:
        return _coordination_mode_attached()
    return _coordination_mode_independent()


def infer_tactical_unit_id(order: Any | None, *, tactical_unit_type: Any = None, default_id: int = 0) -> int:
    if order is None:
        return _coerce_positive_int(default_id)
    unit_type = tactical_unit_type if tactical_unit_type is not None else infer_tactical_unit_type(order)
    unit_type_value = _enum_value(unit_type)
    candidates: tuple[Any, ...]
    if unit_type_value == _enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")):
        candidates = (
            getattr(order, "package_id", 0),
            getattr(order, "task_group_id", 0),
            getattr(order, "assignee_id", 0),
            default_id,
        )
    elif unit_type_value == _enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")):
        candidates = (
            getattr(order, "element_id", 0),
            getattr(order, "assignee_id", 0),
            default_id,
        )
    else:
        candidates = (
            getattr(order, "assignee_id", 0),
            getattr(order, "lead_aircraft_id", 0),
            default_id,
        )
    for raw_value in candidates:
        value = _coerce_positive_int(raw_value)
        if value > 0:
            return value
    return 0


def apply_task_order_common_core_spec(order: Any, spec: dict[str, Any] | None) -> Any:
    if not isinstance(spec, dict):
        return order
    if "service_profile" in spec:
        order.service_profile = _enum_or_default(ef_py.ServiceProfile, spec.get("service_profile"), order.service_profile)
    if "task_family" in spec:
        order.task_family = _enum_or_default(ef_py.TaskFamily, spec.get("task_family"), order.task_family)
    if "tactical_unit_type" in spec:
        order.tactical_unit_type = _enum_or_default(
            ef_py.TacticalUnitType,
            spec.get("tactical_unit_type"),
            order.tactical_unit_type,
        )
    if "command_relationship" in spec:
        order.command_relationship = _enum_or_default(
            ef_py.CommandRelationship,
            spec.get("command_relationship"),
            order.command_relationship,
        )
    if "authority_scope" in spec:
        order.authority_scope = _enum_or_default(
            ef_py.AuthorityScope,
            spec.get("authority_scope"),
            order.authority_scope,
        )
    if "coordination_mode" in spec:
        order.coordination_mode = _enum_or_default(
            ef_py.CoordinationMode,
            spec.get("coordination_mode"),
            order.coordination_mode,
        )
    for name in (
        "parent_node_id",
        "task_group_id",
        "supported_node_id",
        "supporting_node_id",
        "role_code",
        "relative_slot_code",
        "recovery_site_id",
    ):
        if name in spec:
            setattr(order, name, int(spec.get(name, getattr(order, name))))
    if "takeoff_interval_s" in spec:
        order.takeoff_interval_s = float(spec.get("takeoff_interval_s", getattr(order, "takeoff_interval_s", 0.0)))
    return order


def apply_leader_intent_common_core_spec(intent: Any, spec: dict[str, Any] | None) -> Any:
    if not isinstance(spec, dict):
        return intent
    if "service_profile" in spec:
        intent.service_profile = _enum_or_default(ef_py.ServiceProfile, spec.get("service_profile"), intent.service_profile)
    if "task_family" in spec:
        intent.task_family = _enum_or_default(ef_py.TaskFamily, spec.get("task_family"), intent.task_family)
    if "tactical_unit_type" in spec:
        intent.tactical_unit_type = _enum_or_default(
            ef_py.TacticalUnitType,
            spec.get("tactical_unit_type"),
            intent.tactical_unit_type,
        )
    if "coordination_mode" in spec:
        intent.coordination_mode = _enum_or_default(
            ef_py.CoordinationMode,
            spec.get("coordination_mode"),
            intent.coordination_mode,
        )
    for field_name, namespace in (
        ("takeoff_procedure_id", getattr(ef_py, "TakeoffProcedureType", None)),
        ("takeoff_clearance_id", getattr(ef_py, "TakeoffClearanceState", None)),
        ("runway_slot_id", getattr(ef_py, "RunwaySlotPosition", None)),
    ):
        if field_name in spec and namespace is not None:
            setattr(intent, field_name, _enum_or_default(namespace, spec.get(field_name), getattr(intent, field_name)))
    for name in ("tactical_unit_id", "task_group_id", "role_code", "relative_slot_code", "recovery_site_id"):
        if name in spec:
            setattr(intent, name, int(spec.get(name, getattr(intent, name))))
    if "takeoff_interval_s" in spec:
        intent.takeoff_interval_s = float(spec.get("takeoff_interval_s", getattr(intent, "takeoff_interval_s", 0.0)))
    return intent


def apply_pilot_report_common_core_spec(report: Any, spec: dict[str, Any] | None) -> Any:
    if not isinstance(spec, dict):
        return report
    if "service_profile" in spec:
        report.service_profile = _enum_or_default(ef_py.ServiceProfile, spec.get("service_profile"), report.service_profile)
    if "task_family" in spec:
        report.task_family = _enum_or_default(ef_py.TaskFamily, spec.get("task_family"), report.task_family)
    if "tactical_unit_type" in spec:
        report.tactical_unit_type = _enum_or_default(
            ef_py.TacticalUnitType,
            spec.get("tactical_unit_type"),
            report.tactical_unit_type,
        )
    if "coordination_mode" in spec:
        report.coordination_mode = _enum_or_default(
            ef_py.CoordinationMode,
            spec.get("coordination_mode"),
            report.coordination_mode,
        )
    for name in ("tactical_unit_id", "task_group_id", "role_code", "element_id"):
        if name in spec:
            setattr(report, name, int(spec.get(name, getattr(report, name))))
    return report


def apply_task_order_common_core_defaults(
    order: Any,
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    force_task_family: bool = False,
    force_coordination_mode: bool = False,
) -> Any:
    if order is None:
        return order
    if _is_default_enum(getattr(order, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        order.service_profile = _service_profile_default()

    inferred_task_family = infer_air_task_family(
        task_name=task_name,
        task_type=getattr(order, "task_type", None),
        phase_name=phase_name,
    )
    task_family = getattr(order, "task_family", _task_family_default())
    if force_task_family and not _is_default_enum(inferred_task_family, _task_family_default()):
        order.task_family = inferred_task_family
    elif _is_default_enum(task_family, _task_family_default()):
        order.task_family = inferred_task_family

    if _is_default_enum(getattr(order, "tactical_unit_type", _tactical_unit_type_default()), _tactical_unit_type_default()):
        order.tactical_unit_type = infer_tactical_unit_type(order)

    if _is_default_enum(getattr(order, "command_relationship", _command_relationship_default()), getattr(ef_py.CommandRelationship, "None")):
        order.command_relationship = _command_relationship_default()

    if _is_default_enum(getattr(order, "authority_scope", _authority_scope_default()), getattr(ef_py.AuthorityScope, "Unspecified")):
        order.authority_scope = _authority_scope_default()

    if _coerce_positive_int(getattr(order, "task_group_id", 0)) <= 0 and _coerce_positive_int(getattr(order, "package_id", 0)) > 0:
        order.task_group_id = int(getattr(order, "package_id", 0))

    if _coerce_positive_int(getattr(order, "recovery_site_id", 0)) <= 0:
        order.recovery_site_id = int(infer_recovery_site_id(order))

    if force_coordination_mode or _is_default_enum(getattr(order, "coordination_mode", _coordination_mode_default()), _coordination_mode_default()):
        order.coordination_mode = infer_coordination_mode(
            task_name=task_name,
            task_family=getattr(order, "task_family", _task_family_default()),
            phase_name=phase_name,
            tactical_unit_type=getattr(order, "tactical_unit_type", _tactical_unit_type_default()),
        )
    return order


def apply_leader_intent_common_core_defaults(
    intent: Any,
    *,
    order: Any | None = None,
    task_name: str | None = None,
    phase_name: str | None = None,
    default_tactical_unit_id: int = 0,
) -> Any:
    if intent is None:
        return intent
    if _is_default_enum(getattr(intent, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        intent.service_profile = getattr(order, "service_profile", _service_profile_default()) if order is not None else _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(intent, "task_family", _task_family_default()), _task_family_default()):
        inferred_task_family = infer_air_task_family(task_name=task_name, task_type=None, phase_name=phase_name)
        if not _is_default_enum(inferred_task_family, _task_family_default()):
            intent.task_family = inferred_task_family
        elif not _is_default_enum(order_task_family, _task_family_default()):
            intent.task_family = order_task_family
        else:
            intent.task_family = inferred_task_family

    order_unit_type = infer_tactical_unit_type(order)
    if _is_default_enum(getattr(intent, "tactical_unit_type", _tactical_unit_type_default()), _tactical_unit_type_default()):
        intent.tactical_unit_type = order_unit_type

    if _coerce_positive_int(getattr(intent, "task_group_id", 0)) <= 0:
        group_id = _coerce_positive_int(getattr(order, "task_group_id", 0)) if order is not None else 0
        if group_id <= 0 and order is not None:
            group_id = _coerce_positive_int(getattr(order, "package_id", 0))
        if group_id > 0:
            intent.task_group_id = int(group_id)

    if int(getattr(intent, "role_code", 0)) == 0 and order is not None:
        intent.role_code = int(getattr(order, "role_code", 0))

    if int(getattr(intent, "relative_slot_code", 0)) == 0 and order is not None:
        intent.relative_slot_code = int(getattr(order, "relative_slot_code", 0))

    if _is_default_enum(
        getattr(intent, "takeoff_procedure_id", _takeoff_procedure_default()),
        _takeoff_procedure_default(),
    ) and order is not None:
        intent.takeoff_procedure_id = getattr(order, "takeoff_procedure_id", _takeoff_procedure_default())

    if _is_default_enum(
        getattr(intent, "takeoff_clearance_id", _takeoff_clearance_default()),
        _takeoff_clearance_default(),
    ) and order is not None:
        intent.takeoff_clearance_id = getattr(order, "takeoff_clearance_id", _takeoff_clearance_default())

    if _is_default_enum(
        getattr(intent, "runway_slot_id", _runway_slot_default()),
        _runway_slot_default(),
    ) and order is not None:
        intent.runway_slot_id = getattr(order, "runway_slot_id", _runway_slot_default())

    if abs(float(getattr(intent, "takeoff_interval_s", 0.0))) <= 1.0e-9 and order is not None:
        intent.takeoff_interval_s = float(getattr(order, "takeoff_interval_s", 0.0))

    if _coerce_positive_int(getattr(intent, "recovery_site_id", 0)) <= 0:
        recovery_site_id = infer_recovery_site_id(order)
        if recovery_site_id > 0:
            intent.recovery_site_id = int(recovery_site_id)

    if _coerce_positive_int(getattr(intent, "tactical_unit_id", 0)) <= 0:
        intent.tactical_unit_id = int(
            infer_tactical_unit_id(
                order,
                tactical_unit_type=getattr(intent, "tactical_unit_type", order_unit_type),
                default_id=default_tactical_unit_id,
            )
        )

    if _is_default_enum(getattr(intent, "coordination_mode", _coordination_mode_default()), _coordination_mode_default()):
        inherited = getattr(order, "coordination_mode", _coordination_mode_default()) if order is not None else _coordination_mode_default()
        if not _is_default_enum(inherited, _coordination_mode_default()):
            intent.coordination_mode = inherited
        else:
            intent.coordination_mode = infer_coordination_mode(
                task_name=task_name,
                task_family=getattr(intent, "task_family", _task_family_default()),
                phase_name=phase_name,
                tactical_unit_type=getattr(intent, "tactical_unit_type", order_unit_type),
            )
    return intent


def apply_pilot_report_common_core_defaults(
    report: Any,
    *,
    order: Any | None = None,
    task_name: str | None = None,
    phase_name: str | None = None,
    default_tactical_unit_id: int = 0,
) -> Any:
    if report is None:
        return report
    if _is_default_enum(getattr(report, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        report.service_profile = getattr(order, "service_profile", _service_profile_default()) if order is not None else _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(report, "task_family", _task_family_default()), _task_family_default()):
        inferred_task_family = infer_air_task_family(task_name=task_name, task_type=None, phase_name=phase_name)
        if not _is_default_enum(inferred_task_family, _task_family_default()):
            report.task_family = inferred_task_family
        elif not _is_default_enum(order_task_family, _task_family_default()):
            report.task_family = order_task_family
        else:
            report.task_family = inferred_task_family

    order_unit_type = infer_tactical_unit_type(order)
    if _is_default_enum(getattr(report, "tactical_unit_type", _tactical_unit_type_default()), _tactical_unit_type_default()):
        report.tactical_unit_type = order_unit_type

    if _coerce_positive_int(getattr(report, "task_group_id", 0)) <= 0:
        group_id = _coerce_positive_int(getattr(order, "task_group_id", 0)) if order is not None else 0
        if group_id <= 0 and order is not None:
            group_id = _coerce_positive_int(getattr(order, "package_id", 0))
        if group_id > 0:
            report.task_group_id = int(group_id)

    if int(getattr(report, "role_code", 0)) == 0 and order is not None:
        report.role_code = int(getattr(order, "role_code", 0))

    if _coerce_positive_int(getattr(report, "element_id", 0)) <= 0 and order is not None:
        element_id = _coerce_positive_int(getattr(order, "element_id", 0))
        if element_id > 0:
            report.element_id = int(element_id)

    if _coerce_positive_int(getattr(report, "tactical_unit_id", 0)) <= 0:
        report.tactical_unit_id = int(
            infer_tactical_unit_id(
                order,
                tactical_unit_type=getattr(report, "tactical_unit_type", order_unit_type),
                default_id=default_tactical_unit_id,
            )
        )

    if _is_default_enum(getattr(report, "coordination_mode", _coordination_mode_default()), _coordination_mode_default()):
        inherited = getattr(order, "coordination_mode", _coordination_mode_default()) if order is not None else _coordination_mode_default()
        if not _is_default_enum(inherited, _coordination_mode_default()):
            report.coordination_mode = inherited
        else:
            report.coordination_mode = infer_coordination_mode(
                task_name=task_name,
                task_family=getattr(report, "task_family", _task_family_default()),
                phase_name=phase_name,
                tactical_unit_type=getattr(report, "tactical_unit_type", order_unit_type),
            )
    return report
