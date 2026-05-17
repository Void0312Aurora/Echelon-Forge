from __future__ import annotations

from typing import Any

def _int_equal(lhs: Any, rhs: Any) -> bool:
    try:
        return int(lhs) == int(rhs)
    except Exception:
        return lhs == rhs

def _check_fields(actual: Any, expected: Any, field_names: tuple[str, ...], *, label: str) -> tuple[bool, str]:
    for field_name in field_names:
        actual_value = getattr(actual, field_name)
        expected_value = getattr(expected, field_name)
        if not _int_equal(actual_value, expected_value):
            return False, f"stored {label} {field_name} mismatch: {actual_value} != {expected_value}"
    return True, ""

def _recovery_approach_enum(raw_value, default_name: str = "None"):
    import ef_py

    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        try:
            return int(raw_value)
        except Exception:
            return 0
    default_value = getattr(namespace, default_name, 0)
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, raw_value, default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value

def _common_core_field_names(kind: str) -> tuple[str, ...]:
    if kind == "task_order":
        return (
            "service_profile",
            "task_family",
            "tactical_unit_type",
            "command_relationship",
            "authority_scope",
            "parent_node_id",
            "task_group_id",
            "supported_node_id",
            "supporting_node_id",
            "role_code",
            "coordination_mode",
            "relative_slot_code",
            "recovery_site_id",
            "warfare_role_code",
            "officer_in_tactical_command",
        )
    if kind == "leader_intent":
        return (
            "service_profile",
            "task_family",
            "tactical_unit_type",
            "tactical_unit_id",
            "task_group_id",
            "role_code",
            "coordination_mode",
            "relative_slot_code",
            "recovery_site_id",
            "warfare_role_code",
            "officer_in_tactical_command",
        )
    if kind == "pilot_report":
        return (
            "service_profile",
            "task_family",
            "tactical_unit_type",
            "tactical_unit_id",
            "task_group_id",
            "role_code",
            "coordination_mode",
            "element_id",
            "warfare_role_code",
            "officer_in_tactical_command",
        )
    raise ValueError(f"Unknown common-core field kind: {kind}")

def _air_task_order_field_names() -> tuple[str, ...]:
    return (
        "task_type",
        "station_type",
        "recovery_base_id",
        "recovery_runway_id",
        "recovery_approach_type",
    )

def _air_leader_intent_field_names() -> tuple[str, ...]:
    return (
        "phase_id",
        "command_code",
        "route_ref_id",
        "recovery_base_id",
        "recovery_runway_id",
        "recovery_approach_type",
    )

def _air_pilot_report_field_names() -> tuple[str, ...]:
    return (
        "report_type",
        "task_id",
        "phase_id",
    )

def _task_order_enum_fields():
    import ef_py

    return {
        "task_type": ef_py.TaskType,
        "service_profile": ef_py.ServiceProfile,
        "task_family": ef_py.TaskFamily,
        "tactical_unit_type": ef_py.TacticalUnitType,
        "command_relationship": ef_py.CommandRelationship,
        "authority_scope": ef_py.AuthorityScope,
        "coordination_mode": ef_py.CoordinationMode,
        "station_type": ef_py.StationType,
        "naval_station_type": getattr(ef_py, "NavalStationType", None),
        "warfare_role_code": getattr(ef_py, "NavalWarfareRole", None),
    }

def _enum_value_or_default(namespace: Any, raw_value: Any, default_name: str):
    default_value = getattr(namespace, default_name)
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, raw_value, default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value
