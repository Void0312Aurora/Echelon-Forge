from __future__ import annotations

from typing import Any

import ef_py
from python.rl.profile import air_profile as _air_profile
from python.rl.profile import naval_profile as _naval_profile
from python.rl.profile import common_core_defaults as _common_defaults
from python.rl.profile.common_core_base import (
    coerce_positive_int as _coerce_positive_int,
    enum_or_default as _enum_or_default,
    enum_value as _enum_value,
    is_default_enum as _is_default_enum,
)


def _sync_profile_modules() -> None:
    _air_profile.ef_py = ef_py
    _naval_profile.ef_py = ef_py
    _common_defaults.ef_py = ef_py


def _profile_name_from_context(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None) -> str:
    candidates: list[Any] = []
    if spec is not None:
        candidates.extend([spec.get("tasking_profile", None), spec.get("service_profile", None)])
    if order is not None:
        candidates.extend(
            [
                getattr(order, "tasking_profile", None),
                getattr(order, "service_profile", None),
            ]
        )
    if loader is not None:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        if isinstance(scenario_data, dict):
            candidates.extend(
                [
                    scenario_data.get("tasking_profile", None),
                    scenario_data.get("service_profile", None),
                ]
            )
            mission_cmd = scenario_data.get("mission_command", None)
            if isinstance(mission_cmd, dict):
                candidates.extend(
                    [
                        mission_cmd.get("tasking_profile", None),
                        mission_cmd.get("service_profile", None),
                    ]
                )
    for raw in candidates:
        if raw is None:
            continue
        if raw == getattr(ef_py.ServiceProfile, "Navy", object()):
            return "naval"
        text = str(getattr(raw, "name", raw)).strip().lower()
        if text in {"naval", "navy"}:
            return "naval"
    return "air"


def _profile_module_for_context(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None):
    _sync_profile_modules()
    if _profile_name_from_context(order, loader=loader, spec=spec) == "naval":
        return _naval_profile
    return _air_profile


def _infer_tactical_unit_type_for_profile(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None):
    profile = _profile_module_for_context(order, loader=loader, spec=spec)
    infer_fn = getattr(profile, "infer_tactical_unit_type", None)
    if callable(infer_fn):
        return infer_fn(order)
    return _common_defaults.infer_tactical_unit_type(order)


def _service_profile_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.service_profile_default()


def _task_family_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.task_family_default()


def _tactical_unit_type_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.tactical_unit_type_default()


def _command_relationship_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.command_relationship_default()


def _authority_scope_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.authority_scope_default()


def _coordination_mode_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.coordination_mode_default()


def _coordination_mode_independent() -> Any:
    _sync_profile_modules()
    return _common_defaults.coordination_mode_independent()


def _coordination_mode_attached() -> Any:
    _sync_profile_modules()
    return _common_defaults.coordination_mode_attached()


def _coordination_mode_recover() -> Any:
    _sync_profile_modules()
    return _common_defaults.coordination_mode_recover()


def _takeoff_procedure_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.takeoff_procedure_default()


def _takeoff_clearance_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.takeoff_clearance_default()


def _runway_slot_default() -> Any:
    _sync_profile_modules()
    return _common_defaults.runway_slot_default()


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
    _sync_profile_modules()
    return _air_profile.infer_air_task_family(task_name=task_name, task_type=task_type, phase_name=phase_name)


def infer_air_task_type(*, task_family: Any = None, task_name: str | None = None, has_waypoints: bool = False) -> Any:
    _sync_profile_modules()
    return _air_profile.infer_air_task_type(
        task_family=task_family,
        task_name=task_name,
        has_waypoints=has_waypoints,
    )


def resolved_task_family(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> Any:
    _sync_profile_modules()
    return _air_profile.resolved_task_family(task, task_name=task_name, phase_name=phase_name)


def is_patrol_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    _sync_profile_modules()
    return _air_profile.is_patrol_task(task, task_name=task_name, phase_name=phase_name)


def is_recover_task(task: Any | None = None, *, task_name: str | None = None, phase_name: str | None = None) -> bool:
    _sync_profile_modules()
    return _air_profile.is_recover_task(task, task_name=task_name, phase_name=phase_name)


def infer_tactical_unit_type(order: Any | None) -> Any:
    _sync_profile_modules()
    return _common_defaults.infer_tactical_unit_type(order)


def infer_recovery_site_id(order: Any | None) -> int:
    _sync_profile_modules()
    return _common_defaults.infer_recovery_site_id(order)


def normalize_task_order_spec(order_spec: dict[str, Any] | None) -> dict[str, Any]:
    return _profile_module_for_context(spec=order_spec).normalize_task_order_spec(order_spec)


def task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
    return _profile_module_for_context(task).task_observation_codes(task, fallback_phase_id=fallback_phase_id)


def infer_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
    order: Any | None = None,
    loader: Any | None = None,
) -> Any:
    profile = _profile_module_for_context(order, loader=loader)
    return profile.infer_coordination_mode(
        task_name=task_name,
        task_family=task_family,
        phase_name=phase_name,
        tactical_unit_type=tactical_unit_type,
    )


def infer_tactical_unit_id(order: Any | None, *, tactical_unit_type: Any = None, default_id: int = 0) -> int:
    _sync_profile_modules()
    return _common_defaults.infer_tactical_unit_id(
        order,
        tactical_unit_type=tactical_unit_type,
        default_id=default_id,
    )


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
    if "warfare_role_code" in spec and hasattr(order, "warfare_role_code"):
        namespace = getattr(ef_py, "NavalWarfareRole", None)
        if namespace is not None:
            order.warfare_role_code = int(
                _enum_or_default(namespace, spec.get("warfare_role_code"), getattr(order, "warfare_role_code", 0))
            )
    for name in (
        "parent_node_id",
        "task_group_id",
        "supported_node_id",
        "supporting_node_id",
        "role_code",
        "relative_slot_code",
        "recovery_site_id",
        "officer_in_tactical_command",
    ):
        if name in spec:
            setattr(order, name, int(spec.get(name, getattr(order, name))))
    if "naval_station_type" in spec and hasattr(order, "naval_station_type"):
        namespace = getattr(ef_py, "NavalStationType", None)
        if namespace is not None:
            order.naval_station_type = _enum_or_default(namespace, spec.get("naval_station_type"), order.naval_station_type)
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
    if "warfare_role_code" in spec and hasattr(intent, "warfare_role_code"):
        namespace = getattr(ef_py, "NavalWarfareRole", None)
        if namespace is not None:
            intent.warfare_role_code = int(
                _enum_or_default(namespace, spec.get("warfare_role_code"), getattr(intent, "warfare_role_code", 0))
            )
    for field_name, namespace in (
        ("takeoff_procedure_id", getattr(ef_py, "TakeoffProcedureType", None)),
        ("takeoff_clearance_id", getattr(ef_py, "TakeoffClearanceState", None)),
        ("runway_slot_id", getattr(ef_py, "RunwaySlotPosition", None)),
    ):
        if field_name in spec and namespace is not None:
            setattr(intent, field_name, _enum_or_default(namespace, spec.get(field_name), getattr(intent, field_name)))
    for name in (
        "tactical_unit_id",
        "task_group_id",
        "role_code",
        "warfare_role_code",
        "relative_slot_code",
        "recovery_site_id",
        "officer_in_tactical_command",
    ):
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
    if "warfare_role_code" in spec and hasattr(report, "warfare_role_code"):
        namespace = getattr(ef_py, "NavalWarfareRole", None)
        if namespace is not None:
            report.warfare_role_code = int(
                _enum_or_default(namespace, spec.get("warfare_role_code"), getattr(report, "warfare_role_code", 0))
            )
    for name in ("tactical_unit_id", "task_group_id", "role_code", "officer_in_tactical_command", "element_id"):
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
        profile_name = _profile_name_from_context(order, spec=None)
        order.service_profile = getattr(ef_py.ServiceProfile, "Navy") if profile_name == "naval" else _service_profile_default()

    profile = _profile_module_for_context(order)
    infer_task_family = getattr(profile, "infer_naval_task_family", None)
    if infer_task_family is None:
        infer_task_family = getattr(profile, "infer_air_task_family")
    inferred_task_family = infer_task_family(
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
        order.tactical_unit_type = _infer_tactical_unit_type_for_profile(order)

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
            order=order,
        )

    if hasattr(order, "warfare_role_code") and int(getattr(order, "warfare_role_code", 0)) == 0:
        infer_warfare_role = getattr(profile, "infer_warfare_role_code", None)
        if callable(infer_warfare_role):
            order.warfare_role_code = infer_warfare_role(
                task_name=task_name,
                task_family=getattr(order, "task_family", _task_family_default()),
                coordination_mode=getattr(order, "coordination_mode", _coordination_mode_default()),
            )

    if hasattr(order, "naval_station_type") and _is_default_enum(getattr(order, "naval_station_type", 0), 0):
        infer_station_type = getattr(profile, "infer_naval_station_type", None)
        if callable(infer_station_type):
            order.naval_station_type = infer_station_type(
                task_name=task_name,
                task_family=getattr(order, "task_family", _task_family_default()),
                coordination_mode=getattr(order, "coordination_mode", _coordination_mode_default()),
            )

    if hasattr(order, "officer_in_tactical_command") and _coerce_positive_int(getattr(order, "officer_in_tactical_command", 0)) <= 0:
        otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
        if otc_id <= 0:
            otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
        if otc_id > 0:
            order.officer_in_tactical_command = int(otc_id)
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
        if order is not None:
            intent.service_profile = getattr(order, "service_profile", _service_profile_default())
        else:
            intent.service_profile = getattr(ef_py.ServiceProfile, "Navy") if _profile_name_from_context(intent) == "naval" else _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(intent, "task_family", _task_family_default()), _task_family_default()):
        profile = _profile_module_for_context(order if order is not None else intent)
        infer_task_family = getattr(profile, "infer_naval_task_family", None)
        if infer_task_family is None:
            infer_task_family = getattr(profile, "infer_air_task_family")
        inferred_task_family = infer_task_family(task_name=task_name, task_type=None, phase_name=phase_name)
        if not _is_default_enum(inferred_task_family, _task_family_default()):
            intent.task_family = inferred_task_family
        elif not _is_default_enum(order_task_family, _task_family_default()):
            intent.task_family = order_task_family
        else:
            intent.task_family = inferred_task_family

    order_unit_type = _infer_tactical_unit_type_for_profile(order)
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

    if hasattr(intent, "warfare_role_code") and int(getattr(intent, "warfare_role_code", 0)) == 0 and order is not None:
        intent.warfare_role_code = int(getattr(order, "warfare_role_code", 0))

    if hasattr(intent, "officer_in_tactical_command") and _coerce_positive_int(getattr(intent, "officer_in_tactical_command", 0)) <= 0 and order is not None:
        otc_id = _coerce_positive_int(getattr(order, "officer_in_tactical_command", 0))
        if otc_id <= 0:
            otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
        if otc_id <= 0:
            otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
        if otc_id > 0:
            intent.officer_in_tactical_command = int(otc_id)

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
                order=order if order is not None else intent,
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
        if order is not None:
            report.service_profile = getattr(order, "service_profile", _service_profile_default())
        else:
            report.service_profile = getattr(ef_py.ServiceProfile, "Navy") if _profile_name_from_context(report) == "naval" else _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(report, "task_family", _task_family_default()), _task_family_default()):
        profile = _profile_module_for_context(order if order is not None else report)
        infer_task_family = getattr(profile, "infer_naval_task_family", None)
        if infer_task_family is None:
            infer_task_family = getattr(profile, "infer_air_task_family")
        inferred_task_family = infer_task_family(task_name=task_name, task_type=None, phase_name=phase_name)
        if not _is_default_enum(inferred_task_family, _task_family_default()):
            report.task_family = inferred_task_family
        elif not _is_default_enum(order_task_family, _task_family_default()):
            report.task_family = order_task_family
        else:
            report.task_family = inferred_task_family

    order_unit_type = _infer_tactical_unit_type_for_profile(order)
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

    if hasattr(report, "warfare_role_code") and int(getattr(report, "warfare_role_code", 0)) == 0 and order is not None:
        report.warfare_role_code = int(getattr(order, "warfare_role_code", 0))

    if hasattr(report, "officer_in_tactical_command") and _coerce_positive_int(getattr(report, "officer_in_tactical_command", 0)) <= 0 and order is not None:
        otc_id = _coerce_positive_int(getattr(order, "officer_in_tactical_command", 0))
        if otc_id <= 0:
            otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
        if otc_id <= 0:
            otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
        if otc_id > 0:
            report.officer_in_tactical_command = int(otc_id)

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
                order=order if order is not None else report,
            )
    return report
