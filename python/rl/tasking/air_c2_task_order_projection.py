"""Compiled task-order projection for the Air scripted C2 adapter.

This module is deliberately an adapter: it owns ``ef_py`` DTO mutation and
the RL profile's common-core defaults, while the C2 decision layer consumes
the neutral ``C2TaskOrderProjection`` port. A future native or alternate
runtime can provide another implementation without changing C2 algorithms.
"""

from __future__ import annotations

from typing import Any

import ef_py

from python.coercion import coerce_nonnegative_int
from python.tasking_contracts.air.tasking.c2_policy import (
    TASK_CAP,
    TASK_IDLE,
    TASK_RECOVER_LAND,
    TASK_RTB,
    TASK_SCRAMBLE,
)
from python.tasking_contracts.common.bridge_views import mission_command_view
from python.tasking_contracts.common.mission_defs import COMMAND_CODE_LANDING, is_landing_command_code

from .common_core_profile import (
    apply_task_order_common_core_defaults,
    apply_task_order_common_core_spec,
)


def _enum_or_default(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, str(raw_value), default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value


def _recovery_approach_none() -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "None", 0)


def _recovery_approach_type_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        return default_value if raw_value is None else coerce_nonnegative_int(raw_value)
    try:
        default_member = namespace(int(default_value))
    except Exception:
        default_member = default_value
    if raw_value is None:
        return default_member
    if isinstance(raw_value, str):
        text = str(raw_value).strip()
        if not text:
            return default_member
        direct = getattr(namespace, text, None)
        if direct is not None:
            return direct
        normalized = text.replace("_", "").replace(" ", "").lower()
        for name in dir(namespace):
            if name.startswith("_"):
                continue
            if name.replace("_", "").lower() == normalized:
                return getattr(namespace, name)
        return default_member
    try:
        return namespace(int(raw_value))
    except Exception:
        return default_member


def _scenario_task_order_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    order_cfg = scenario_data.get("task_order", None)
    return order_cfg if isinstance(order_cfg, dict) else None


def apply_task_order_overrides(
    order: Any,
    order_spec: dict[str, Any] | None,
    *,
    default_assignee_id: int,
) -> Any:
    """Apply authored task-order fields before common-core normalization."""

    if not isinstance(order_spec, dict):
        return order

    order.active = bool(order_spec.get("active", True))
    if "task_id" in order_spec:
        order.task_id = int(order_spec.get("task_id", order.task_id))
    if "task_type" in order_spec:
        order.task_type = _enum_or_default(ef_py.TaskType, order_spec.get("task_type"), order.task_type)
    if "priority" in order_spec:
        order.priority = int(order_spec.get("priority", order.priority))
    if "issuer_id" in order_spec:
        order.issuer_id = int(order_spec.get("issuer_id", order.issuer_id))
    order.assignee_id = int(order_spec.get("assignee_id", default_assignee_id))
    if "issue_time_s" in order_spec:
        order.issue_time_s = float(order_spec.get("issue_time_s", order.issue_time_s))

    for name in (
        "anchor_x_m",
        "anchor_y_m",
        "anchor_z_m",
        "station_radius_m",
        "station_leg_length_m",
        "station_heading_deg",
        "altitude_block_min_m",
        "altitude_block_max_m",
        "target_altitude_m",
        "speed_min_mps",
        "speed_max_mps",
        "target_speed_mps",
        "on_station_time_s",
        "fuel_bingo_override_kg",
    ):
        if name in order_spec:
            setattr(order, name, float(order_spec.get(name, getattr(order, name))))

    for name in ("entry_condition_code", "exit_condition_code", "recovery_base_id", "recovery_runway_id"):
        if name in order_spec:
            setattr(order, name, int(order_spec.get(name, getattr(order, name))))

    if "station_type" in order_spec:
        order.station_type = _enum_or_default(ef_py.StationType, order_spec.get("station_type"), order.station_type)
    if "recovery_approach_type" in order_spec and hasattr(order, "recovery_approach_type"):
        order.recovery_approach_type = _recovery_approach_type_or_default(
            order_spec.get("recovery_approach_type", getattr(order, "recovery_approach_type", _recovery_approach_none())),
            getattr(order, "recovery_approach_type", _recovery_approach_none()),
        )
    apply_task_order_common_core_spec(order, order_spec)
    return order


class AirC2TaskOrderProjection:
    """Default compiled Air task-order projector."""

    @staticmethod
    def _has_route_waypoints(loader: Any) -> bool:
        return bool(list(getattr(loader, "waypoints", []) or []))

    @staticmethod
    def _active_waypoint_targets(loader: Any) -> tuple[float, float, float | None, float | None]:
        cmd_view = mission_command_view(loader)
        target_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        target_speed_mps = cmd_view.float_field("target_speed", 0.0)
        anchor_x_m = None
        anchor_y_m = None
        waypoints = list(getattr(loader, "waypoints", []) or [])
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
        if 0 <= waypoint_idx < len(waypoints):
            wp = waypoints[waypoint_idx]
            target_altitude_m = float(wp.get("altitude_m", target_altitude_m))
            target_speed_mps = float(wp.get("speed_mps", target_speed_mps))
            anchor_x_m = float(wp.get("x", 0.0))
            anchor_y_m = float(wp.get("y", 0.0))
        return target_altitude_m, target_speed_mps, anchor_x_m, anchor_y_m

    @staticmethod
    def _retarget_block(
        order: Any,
        *,
        target_attr: str,
        min_attr: str,
        max_attr: str,
        target_value: float,
        default_lower_margin: float,
        default_upper_margin: float,
        floor_value: float = 0.0,
    ) -> None:
        current_target = float(getattr(order, target_attr, target_value))
        current_min = float(getattr(order, min_attr, floor_value))
        current_max = float(getattr(order, max_attr, floor_value))
        if current_max > current_min + 1.0e-6:
            lower_margin = max(0.0, current_target - current_min)
            upper_margin = max(0.0, current_max - current_target)
        else:
            lower_margin = max(0.0, float(default_lower_margin))
            upper_margin = max(0.0, float(default_upper_margin))
        target_value = float(target_value)
        setattr(order, target_attr, target_value)
        new_min = max(float(floor_value), target_value - lower_margin)
        new_max = max(new_min, target_value + upper_margin)
        setattr(order, min_attr, float(new_min))
        setattr(order, max_attr, float(new_max))

    def retask_order(self, loader: Any, *, task_name: str, sim_time_s: float) -> None:
        order = getattr(loader, "task_order", None)
        if order is None:
            return
        task_name = str(task_name).strip().upper()
        task_type_by_name = {
            TASK_IDLE: getattr(ef_py.TaskType, "Idle"),
            TASK_SCRAMBLE: getattr(ef_py.TaskType, "Scramble"),
            TASK_CAP: getattr(ef_py.TaskType, "CAP"),
            TASK_RTB: getattr(ef_py.TaskType, "RTB"),
            TASK_RECOVER_LAND: getattr(ef_py.TaskType, "RecoverLand"),
        }
        order.task_type = task_type_by_name.get(task_name, getattr(order, "task_type", getattr(ef_py.TaskType, "Idle")))

        if task_name in (TASK_SCRAMBLE, TASK_CAP):
            scenario_order_cfg = _scenario_task_order_cfg(loader)
            if isinstance(scenario_order_cfg, dict) and scenario_order_cfg:
                apply_task_order_overrides(
                    order,
                    scenario_order_cfg,
                    default_assignee_id=int(getattr(loader, "agent_id", 0) or 0),
                )
                order.issue_time_s = float(sim_time_s)
            order.task_type = task_type_by_name.get(task_name, getattr(order, "task_type", getattr(ef_py.TaskType, "Idle")))
            if self._has_route_waypoints(loader):
                target_altitude_m, target_speed_mps, _anchor_x_m, _anchor_y_m = self._active_waypoint_targets(loader)
                self._retarget_block(
                    order,
                    target_attr="target_altitude_m",
                    min_attr="altitude_block_min_m",
                    max_attr="altitude_block_max_m",
                    target_value=float(target_altitude_m),
                    default_lower_margin=500.0,
                    default_upper_margin=500.0,
                    floor_value=0.0,
                )
                self._retarget_block(
                    order,
                    target_attr="target_speed_mps",
                    min_attr="speed_min_mps",
                    max_attr="speed_max_mps",
                    target_value=float(target_speed_mps),
                    default_lower_margin=40.0,
                    default_upper_margin=40.0,
                    floor_value=40.0,
                )
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        target_altitude_m, target_speed_mps, anchor_x_m, anchor_y_m = self._active_waypoint_targets(loader)
        if anchor_x_m is not None:
            order.anchor_x_m = float(anchor_x_m)
        if anchor_y_m is not None:
            order.anchor_y_m = float(anchor_y_m)
        order.anchor_z_m = float(target_altitude_m)
        order.target_altitude_m = float(target_altitude_m)
        order.target_speed_mps = float(target_speed_mps)
        order.issue_time_s = float(sim_time_s)

        if task_name == TASK_RTB:
            order.altitude_block_min_m = max(0.0, float(target_altitude_m) - 500.0)
            order.altitude_block_max_m = max(float(order.altitude_block_min_m), float(target_altitude_m) + 500.0)
            order.speed_min_mps = max(40.0, float(target_speed_mps) - 40.0)
            order.speed_max_mps = max(float(order.speed_min_mps), float(target_speed_mps) + 40.0)
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        if task_name == TASK_RECOVER_LAND:
            order.altitude_block_min_m = 0.0
            order.altitude_block_max_m = max(350.0, float(target_altitude_m) + 350.0)
            order.speed_min_mps = max(55.0, float(target_speed_mps) - 20.0)
            order.speed_max_mps = max(float(order.speed_min_mps), float(target_speed_mps) + 20.0)
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        apply_task_order_common_core_defaults(
            order,
            task_name=task_name,
            force_task_family=True,
            force_coordination_mode=True,
        )


__all__ = ["AirC2TaskOrderProjection", "apply_task_order_overrides"]
