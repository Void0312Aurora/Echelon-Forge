from __future__ import annotations

from typing import Any

import ef_py
from python.rl.profile import air_profile as _air_profile
from python.rl.profile import ground_profile as _ground_profile
from python.rl.profile import naval_profile as _naval_profile
from python.rl.profile import common_core_defaults as _common_defaults
from python.rl.profile.common_core_base import (
    coerce_positive_int as _coerce_positive_int,
    enum_or_default as _enum_or_default,
    enum_value as _enum_value,
    is_default_enum as _is_default_enum,
)

_COMMON_PROFILE_NAME = "common"


def _normalized_profile_name(raw: Any | None) -> str | None:
    if raw is None:
        return None

    service_profile = getattr(ef_py, "ServiceProfile", None)
    if service_profile is not None:
        if raw == getattr(service_profile, "Navy", object()):
            return "naval"
        if raw == getattr(service_profile, "Army", object()):
            return "ground"
        if raw == getattr(service_profile, "AirForce", object()):
            return "air"

    text = str(getattr(raw, "name", raw)).strip().lower()
    if text.startswith("serviceprofile."):
        text = text.rsplit(".", 1)[-1]

    if text in {"", "unspecified"}:
        return None
    if text in {"common", "default"}:
        return _COMMON_PROFILE_NAME
    if text in {"army", "ground", "land"}:
        return "ground"
    if text in {"naval", "navy"}:
        return "naval"
    if text in {"air", "airforce", "joint"}:
        return "air"
    return None


def _strict_explicit_profile_name(raw: Any | None) -> str | None:
    if raw is None:
        return None
    normalized = _normalized_profile_name(raw)
    if normalized is not None:
        return normalized

    text = str(getattr(raw, "name", raw)).strip().lower()
    if text.startswith("serviceprofile."):
        text = text.rsplit(".", 1)[-1]
    if text in {"", "unspecified"}:
        return None
    raise ValueError(f"Unknown tasking profile: {raw!r}")


def _profile_name_from_context(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None) -> str:
    explicit_candidates: list[Any] = []
    inferred_candidates: list[Any] = []
    if spec is not None:
        explicit_candidates.append(spec.get("tasking_profile", None))
        inferred_candidates.append(spec.get("service_profile", None))
    if order is not None:
        explicit_candidates.append(getattr(order, "tasking_profile", None))
        inferred_candidates.append(getattr(order, "service_profile", None))
    if loader is not None:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        if isinstance(scenario_data, dict):
            explicit_candidates.append(scenario_data.get("tasking_profile", None))
            inferred_candidates.append(scenario_data.get("service_profile", None))
            mission_cmd = scenario_data.get("mission_command", None)
            if isinstance(mission_cmd, dict):
                explicit_candidates.append(mission_cmd.get("tasking_profile", None))
                inferred_candidates.append(mission_cmd.get("service_profile", None))
    for raw in explicit_candidates:
        normalized = _strict_explicit_profile_name(raw)
        if normalized is not None:
            return normalized
    for raw in inferred_candidates:
        normalized = _normalized_profile_name(raw)
        if normalized is not None:
            return normalized
    return _COMMON_PROFILE_NAME


def _infer_common_task_family(*, task_name: str | None = None, task_type: Any = None, phase_name: str | None = None) -> Any:
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
    if phase in {"rtb", "recover", "approach_armed", "landing_final", "rollout"}:
        return getattr(ef_py.TaskFamily, "Recover")
    return _task_family_default()


def _infer_common_task_type(*, task_family: Any = None, task_name: str | None = None, has_waypoints: bool = False) -> Any:
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


def _infer_common_coordination_mode(
    *,
    task_name: str | None = None,
    task_family: Any = None,
    phase_name: str | None = None,
    tactical_unit_type: Any = None,
) -> Any:
    if _enum_value(task_family) == _enum_value(getattr(ef_py.TaskFamily, "Recover")):
        return _coordination_mode_recover()

    name = str(task_name or "").strip().upper()
    if name in {"TASK_RTB", "TASK_RECOVER_LAND"}:
        return _coordination_mode_recover()

    phase = str(phase_name or "").strip().lower()
    if phase in {"rtb", "recover", "approach_armed", "landing_final", "rollout"}:
        return _coordination_mode_recover()

    unit_type_value = _enum_value(tactical_unit_type)
    if unit_type_value in {
        _enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")),
        _enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")),
    }:
        return _coordination_mode_attached()
    return _coordination_mode_independent()


def _common_tactical_unit_type_from_spec(order_spec: dict[str, Any]) -> Any:
    if _coerce_positive_int(order_spec.get("package_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if _coerce_positive_int(order_spec.get("element_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")

    assignee_kind = _enum_or_default(
        ef_py.AssigneeKind,
        order_spec.get("assignee_kind"),
        getattr(ef_py.AssigneeKind, "Aircraft", 0),
    )
    if _enum_value(assignee_kind) == _enum_value(getattr(ef_py.AssigneeKind, "Package")):
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if _enum_value(assignee_kind) == _enum_value(getattr(ef_py.AssigneeKind, "Element")):
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")
    return getattr(ef_py.TacticalUnitType, "Platform")


def _normalize_common_task_order_spec(order_spec: dict[str, Any] | None) -> dict[str, Any]:
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
        if field_name not in normalized:
            continue
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

    task_name = str(normalized.get("task_name", "") or "").strip().upper() or None
    phase_name = str(normalized.get("phase_name", "") or "").strip().lower() or None
    has_waypoints = bool(list(normalized.get("waypoints", []) or []))

    task_family = _enum_or_default(
        ef_py.TaskFamily,
        normalized.get("task_family"),
        _infer_common_task_family(
            task_name=task_name,
            task_type=normalized.get("task_type"),
            phase_name=phase_name,
        ),
    )
    if "task_family" not in normalized or _is_default_enum(task_family, _task_family_default()):
        normalized["task_family"] = task_family

    if "task_type" not in normalized:
        normalized["task_type"] = _infer_common_task_type(
            task_family=normalized.get("task_family", task_family),
            task_name=task_name,
            has_waypoints=has_waypoints,
        )

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
    if "tactical_unit_type" not in normalized or _is_default_enum(tactical_unit_type, _tactical_unit_type_default()):
        tactical_unit_type = _common_tactical_unit_type_from_spec(normalized)
        normalized["tactical_unit_type"] = tactical_unit_type

    recovery_site_id = _coerce_positive_int(normalized.get("recovery_site_id", 0))
    if recovery_site_id <= 0:
        runway_id = _coerce_positive_int(normalized.get("recovery_runway_id", 0))
        base_id = _coerce_positive_int(normalized.get("recovery_base_id", 0))
        recovery_site_id = runway_id if runway_id > 0 else base_id
        if recovery_site_id > 0:
            normalized["recovery_site_id"] = int(recovery_site_id)

    if "coordination_mode" not in normalized:
        normalized["coordination_mode"] = _infer_common_coordination_mode(
            task_name=task_name,
            task_family=normalized.get("task_family", task_family),
            phase_name=phase_name,
            tactical_unit_type=normalized.get("tactical_unit_type", tactical_unit_type),
        )
    return normalized


def _common_task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
    if task is None:
        return 0.0, 0.0, float(fallback_phase_id)

    task_type = _enum_value(getattr(task, "task_type", 0))
    idle_value = _enum_value(getattr(ef_py.TaskType, "Idle", 0))
    station_type = _enum_value(getattr(task, "station_type", 0))
    if task_type <= 0 or task_type == idle_value:
        task_type = _enum_value(
            _infer_common_task_type(
                task_family=getattr(task, "task_family", _task_family_default()),
                has_waypoints=station_type == _enum_value(getattr(ef_py.StationType, "RouteCAP", 0)),
            )
        )
    coordination_mode = _enum_value(getattr(task, "coordination_mode", 0))
    return float(task_type), float(station_type if station_type > 0 else coordination_mode), float(fallback_phase_id)


class _CommonCoreProfileAdapter:
    @staticmethod
    def infer_common_task_family(*, task_name: str | None = None, task_type: Any = None, phase_name: str | None = None) -> Any:
        return _infer_common_task_family(task_name=task_name, task_type=task_type, phase_name=phase_name)

    @staticmethod
    def infer_coordination_mode(
        *,
        task_name: str | None = None,
        task_family: Any = None,
        phase_name: str | None = None,
        tactical_unit_type: Any = None,
    ) -> Any:
        return _infer_common_coordination_mode(
            task_name=task_name,
            task_family=task_family,
            phase_name=phase_name,
            tactical_unit_type=tactical_unit_type,
        )

    @staticmethod
    def infer_tactical_unit_type(order: Any | None) -> Any:
        return _common_defaults.infer_tactical_unit_type(order)

    @staticmethod
    def infer_tactical_unit_id(order: Any | None, *, tactical_unit_type: Any = None, default_id: int = 0) -> int:
        return _common_defaults.infer_tactical_unit_id(
            order,
            tactical_unit_type=tactical_unit_type,
            default_id=default_id,
        )

    @staticmethod
    def normalize_task_order_spec(order_spec: dict[str, Any] | None) -> dict[str, Any]:
        return _normalize_common_task_order_spec(order_spec)

    @staticmethod
    def task_observation_codes(task: Any | None, *, fallback_phase_id: int = 0) -> tuple[float, float, float]:
        return _common_task_observation_codes(task, fallback_phase_id=fallback_phase_id)


_COMMON_PROFILE = _CommonCoreProfileAdapter()


def _profile_module_for_context(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None):
    profile_name = _profile_name_from_context(order, loader=loader, spec=spec)
    if profile_name == "ground":
        return _ground_profile
    if profile_name == "naval":
        return _naval_profile
    if profile_name == "air":
        return _air_profile
    return _COMMON_PROFILE


def _infer_tactical_unit_type_for_profile(order: Any | None = None, *, loader: Any | None = None, spec: dict[str, Any] | None = None):
    profile = _profile_module_for_context(order, loader=loader, spec=spec)
    infer_fn = getattr(profile, "infer_tactical_unit_type", None)
    if callable(infer_fn):
        return infer_fn(order)
    return _common_defaults.infer_tactical_unit_type(order)


def _infer_task_family_for_profile(
    profile: Any,
    *,
    task_name: str | None = None,
    task_type: Any = None,
    phase_name: str | None = None,
) -> Any:
    for infer_name in ("infer_common_task_family", "infer_ground_task_family", "infer_naval_task_family", "infer_air_task_family"):
        infer_fn = getattr(profile, infer_name, None)
        if callable(infer_fn):
            return infer_fn(task_name=task_name, task_type=task_type, phase_name=phase_name)
    return _task_family_default()


def _service_profile_default() -> Any:
    return _common_defaults.service_profile_default()


def _task_family_default() -> Any:
    return _common_defaults.task_family_default()


def _tactical_unit_type_default() -> Any:
    return _common_defaults.tactical_unit_type_default()


def _command_relationship_default() -> Any:
    return _common_defaults.command_relationship_default()


def _authority_scope_default() -> Any:
    return _common_defaults.authority_scope_default()


def _coordination_mode_default() -> Any:
    return _common_defaults.coordination_mode_default()


def _coordination_mode_independent() -> Any:
    return _common_defaults.coordination_mode_independent()


def _coordination_mode_attached() -> Any:
    return _common_defaults.coordination_mode_attached()


def _coordination_mode_recover() -> Any:
    return _common_defaults.coordination_mode_recover()


def _takeoff_procedure_default() -> Any:
    return _common_defaults.takeoff_procedure_default()


def _takeoff_clearance_default() -> Any:
    return _common_defaults.takeoff_clearance_default()


def _runway_slot_default() -> Any:
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


def infer_tactical_unit_type(order: Any | None) -> Any:
    return _common_defaults.infer_tactical_unit_type(order)


def infer_recovery_site_id(order: Any | None) -> int:
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
    profile = _profile_module_for_context(order)
    infer_fn = getattr(profile, "infer_tactical_unit_id", None)
    if callable(infer_fn):
        return infer_fn(order, tactical_unit_type=tactical_unit_type, default_id=default_id)
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
    profile_name = _profile_name_from_context(order, spec=None)
    if _is_default_enum(getattr(order, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        if profile_name == "naval":
            order.service_profile = getattr(ef_py.ServiceProfile, "Navy")
        elif profile_name == "ground":
            order.service_profile = getattr(ef_py.ServiceProfile, "Army")
        else:
            order.service_profile = _service_profile_default()

    profile = _profile_module_for_context(order)
    inferred_task_family = _infer_task_family_for_profile(
        profile,
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
        infer_command_relationship = getattr(profile, "infer_command_relationship", None)
        if callable(infer_command_relationship):
            order.command_relationship = infer_command_relationship(
                task_name=task_name,
                task_family=getattr(order, "task_family", _task_family_default()),
                phase_name=phase_name,
            )
        else:
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
        if profile_name == "ground":
            otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
            if otc_id <= 0:
                otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
        else:
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
    profile_name = _profile_name_from_context(order if order is not None else intent)
    if _is_default_enum(getattr(intent, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        if order is not None:
            intent.service_profile = getattr(order, "service_profile", _service_profile_default())
        else:
            if profile_name == "naval":
                intent.service_profile = getattr(ef_py.ServiceProfile, "Navy")
            elif profile_name == "ground":
                intent.service_profile = getattr(ef_py.ServiceProfile, "Army")
            else:
                intent.service_profile = _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(intent, "task_family", _task_family_default()), _task_family_default()):
        profile = _profile_module_for_context(order if order is not None else intent)
        inferred_task_family = _infer_task_family_for_profile(
            profile,
            task_name=task_name,
            task_type=None,
            phase_name=phase_name,
        )
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
            if profile_name == "ground":
                otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
                if otc_id <= 0:
                    otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
            else:
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
    profile_name = _profile_name_from_context(order if order is not None else report)
    if _is_default_enum(getattr(report, "service_profile", _service_profile_default()), getattr(ef_py.ServiceProfile, "Unspecified")):
        if order is not None:
            report.service_profile = getattr(order, "service_profile", _service_profile_default())
        else:
            if profile_name == "naval":
                report.service_profile = getattr(ef_py.ServiceProfile, "Navy")
            elif profile_name == "ground":
                report.service_profile = getattr(ef_py.ServiceProfile, "Army")
            else:
                report.service_profile = _service_profile_default()

    order_task_family = getattr(order, "task_family", _task_family_default()) if order is not None else _task_family_default()
    if _is_default_enum(getattr(report, "task_family", _task_family_default()), _task_family_default()):
        profile = _profile_module_for_context(order if order is not None else report)
        inferred_task_family = _infer_task_family_for_profile(
            profile,
            task_name=task_name,
            task_type=None,
            phase_name=phase_name,
        )
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
            if profile_name == "ground":
                otc_id = _coerce_positive_int(getattr(order, "parent_node_id", 0))
                if otc_id <= 0:
                    otc_id = _coerce_positive_int(getattr(order, "task_group_id", 0))
            else:
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
