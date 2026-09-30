"""Domain-neutral authored task-order fields.

The helper deliberately excludes domain enums and role codes. Domain adapters
remain responsible for converting those values into their native DTO types.
"""

from __future__ import annotations

from typing import Any


_COMMON_CASTERS = {
    "active": bool,
    "task_id": int,
    "priority": int,
    "issuer_id": int,
    "assignee_id": int,
    "assignee_kind": int,
    "element_id": int,
    "package_id": int,
    "formation_contract_id": int,
    "formation_role_id": int,
    "formation_template_id": int,
    "lead_aircraft_id": int,
    "join_policy_id": int,
    "mutual_support_mode": int,
    "objective_area_id": int,
    "objective_node_id": int,
    "parent_node_id": int,
    "rejoin_policy_id": int,
    "support_sector_id": int,
    "task_group_id": int,
    "wingman_slot_id": int,
    "supported_node_id": int,
    "supporting_node_id": int,
    "role_code": int,
    "relative_slot_code": int,
    "recovery_site_id": int,
    "officer_in_tactical_command": int,
    "issue_time_s": float,
    "anchor_x_m": float,
    "anchor_y_m": float,
    "anchor_z_m": float,
    "station_radius_m": float,
    "station_leg_length_m": float,
    "station_heading_deg": float,
    "altitude_block_min_m": float,
    "altitude_block_max_m": float,
    "target_altitude_m": float,
    "speed_min_mps": float,
    "speed_max_mps": float,
    "target_speed_mps": float,
    "on_station_time_s": float,
    "fuel_bingo_override_kg": float,
    "takeoff_interval_s": float,
    "tactical_cadence_hz": float,
    "entry_condition_code": int,
    "exit_condition_code": int,
    "recovery_base_id": int,
    "recovery_runway_id": int,
}


def _value(source: Any, name: str, default: Any = 0) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def infer_common_tactical_unit_type(source: Any) -> str:
    """Infer common unit granularity with package precedence."""

    try:
        if int(_value(source, "package_id", 0) or 0) > 0:
            return "MissionPackage"
        if int(_value(source, "element_id", 0) or 0) > 0:
            return "TacticalUnit"
        raw_assignee_kind = _value(source, "assignee_kind", "")
        assignee_kind = str(getattr(raw_assignee_kind, "name", raw_assignee_kind) or "").strip().lower()
        if "." in assignee_kind:
            assignee_kind = assignee_kind.rsplit(".", 1)[-1]
        if assignee_kind in {"package", "missionpackage", "mission_package"}:
            return "MissionPackage"
        if assignee_kind in {"element", "tacticalunit", "tactical_unit"}:
            return "TacticalUnit"
        if int(raw_assignee_kind) == 2:
            return "MissionPackage"
        if int(raw_assignee_kind) == 1:
            return "TacticalUnit"
    except (TypeError, ValueError):
        pass
    return "Platform"


def apply_common_task_order_overrides(order: Any, spec: dict[str, Any] | None, *, assignee_id: int) -> Any:
    """Apply common authored fields while leaving domain conversion to adapters."""

    if not isinstance(spec, dict):
        return order
    for name, caster in _COMMON_CASTERS.items():
        if name in spec and hasattr(order, name):
            setattr(order, name, caster(spec[name]))
    if "warfare_role_code" in spec and hasattr(order, "warfare_role_code"):
        # This field is a domain-owned code: Air may expose an integer enum,
        # while Naval may expose a string token. Preserve the authored value.
        order.warfare_role_code = spec["warfare_role_code"]
    if hasattr(order, "assignee_id"):
        order.assignee_id = int(spec.get("assignee_id", assignee_id))
    return order


def apply_common_task_order_defaults(order: Any) -> Any:
    """Fill common identity links without inventing domain-specific values."""

    if hasattr(order, "task_group_id") and int(getattr(order, "task_group_id", 0) or 0) <= 0:
        package_id = int(getattr(order, "package_id", 0) or 0)
        if package_id > 0:
            order.task_group_id = package_id
    if hasattr(order, "recovery_site_id") and int(getattr(order, "recovery_site_id", 0) or 0) <= 0:
        runway_id = int(getattr(order, "recovery_runway_id", 0) or 0)
        base_id = int(getattr(order, "recovery_base_id", 0) or 0)
        order.recovery_site_id = runway_id or base_id
    return order


__all__ = [
    "apply_common_task_order_defaults",
    "apply_common_task_order_overrides",
    "infer_common_tactical_unit_type",
]
