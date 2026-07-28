from __future__ import annotations

from typing import Any

import ef_py

from python.rl.profile.common_core_base import (
    coerce_positive_int,
    enum_value,
    is_default_enum,
)
from python.tasking_contracts.agency_registry import (
    DEFAULT_AUTHORITY_SCOPE as _DEFAULT_AUTHORITY_SCOPE,
    DEFAULT_COMMAND_RELATIONSHIP as _DEFAULT_COMMAND_RELATIONSHIP,
)


def service_profile_default() -> Any:
    return getattr(ef_py.ServiceProfile, "AirForce")


def task_family_default() -> Any:
    return getattr(ef_py.TaskFamily, "Unspecified")


def tactical_unit_type_default() -> Any:
    return getattr(ef_py.TacticalUnitType, "Unspecified")


def command_relationship_default() -> Any:
    # Default relationship name is owned by the agency registry (declaration
    # layer); resolved against the compiled enum here so the runtime value stays
    # byte-identical to the former ``"TACON"`` literal (census EN/ZH §9).
    return getattr(ef_py.CommandRelationship, _DEFAULT_COMMAND_RELATIONSHIP)


def authority_scope_default() -> Any:
    # Default scope name is owned by the agency registry (declaration layer);
    # resolved against the compiled enum here so the runtime value stays
    # byte-identical to the former ``"Tactical"`` literal (census EN/ZH §9).
    return getattr(ef_py.AuthorityScope, _DEFAULT_AUTHORITY_SCOPE)


def coordination_mode_default() -> Any:
    return getattr(ef_py.CoordinationMode, "Unspecified")


def coordination_mode_independent() -> Any:
    return getattr(ef_py.CoordinationMode, "Independent")


def coordination_mode_attached() -> Any:
    return getattr(ef_py.CoordinationMode, "Attached")


def coordination_mode_recover() -> Any:
    return getattr(ef_py.CoordinationMode, "Recover")


def takeoff_procedure_default() -> Any:
    namespace = getattr(ef_py, "TakeoffProcedureType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def takeoff_clearance_default() -> Any:
    namespace = getattr(ef_py, "TakeoffClearanceState", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def runway_slot_default() -> Any:
    namespace = getattr(ef_py, "RunwaySlotPosition", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def infer_tactical_unit_type(order: Any | None) -> Any:
    if order is None:
        return getattr(ef_py.TacticalUnitType, "Platform")
    current = getattr(order, "tactical_unit_type", tactical_unit_type_default())
    if not is_default_enum(current, tactical_unit_type_default()):
        return current

    if coerce_positive_int(getattr(order, "package_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if coerce_positive_int(getattr(order, "element_id", 0)) > 0:
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")

    assignee_kind = enum_value(getattr(order, "assignee_kind", 0))
    if assignee_kind == enum_value(getattr(ef_py.AssigneeKind, "Package")):
        return getattr(ef_py.TacticalUnitType, "MissionPackage")
    if assignee_kind == enum_value(getattr(ef_py.AssigneeKind, "Element")):
        return getattr(ef_py.TacticalUnitType, "TacticalUnit")
    return getattr(ef_py.TacticalUnitType, "Platform")


def infer_recovery_site_id(order: Any | None) -> int:
    if order is None:
        return 0
    current = coerce_positive_int(getattr(order, "recovery_site_id", 0))
    if current > 0:
        return current
    runway_id = coerce_positive_int(getattr(order, "recovery_runway_id", 0))
    if runway_id > 0:
        return runway_id
    return coerce_positive_int(getattr(order, "recovery_base_id", 0))


def infer_tactical_unit_id(order: Any | None, *, tactical_unit_type: Any = None, default_id: int = 0) -> int:
    if order is None:
        return coerce_positive_int(default_id)
    unit_type = tactical_unit_type if tactical_unit_type is not None else infer_tactical_unit_type(order)
    unit_type_value = enum_value(unit_type)
    candidates: tuple[Any, ...]
    if unit_type_value == enum_value(getattr(ef_py.TacticalUnitType, "MissionPackage")):
        candidates = (
            getattr(order, "package_id", 0),
            getattr(order, "task_group_id", 0),
            getattr(order, "assignee_id", 0),
            default_id,
        )
    elif unit_type_value == enum_value(getattr(ef_py.TacticalUnitType, "TacticalUnit")):
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
        value = coerce_positive_int(raw_value)
        if value > 0:
            return value
    return 0
