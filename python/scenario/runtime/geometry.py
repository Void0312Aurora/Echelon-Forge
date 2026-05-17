from __future__ import annotations

import math
from typing import Any


def rotate_xy_clockwise(x: float, y: float, origin_x: float, origin_y: float, yaw_deg: float) -> tuple[float, float]:
    rad = -math.radians(float(yaw_deg))
    c = math.cos(rad)
    s = math.sin(rad)
    dx = float(x) - float(origin_x)
    dy = float(y) - float(origin_y)
    rx = float(origin_x) + c * dx - s * dy
    ry = float(origin_y) + s * dx + c * dy
    return rx, ry


def _rotate_waypoint_list_inplace(
    waypoints: list[Any] | tuple[Any, ...] | None,
    *,
    origin_x: float,
    origin_y: float,
    yaw_deg: float,
) -> None:
    if not isinstance(waypoints, (list, tuple)):
        return
    for wp in waypoints:
        if isinstance(wp, dict):
            if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                pos_x, pos_y = rotate_xy_clockwise(
                    wp["pos"][0],
                    wp["pos"][1],
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                wp["pos"][0] = pos_x
                wp["pos"][1] = pos_y
            elif "x" in wp and "y" in wp:
                pos_x, pos_y = rotate_xy_clockwise(
                    wp.get("x", 0.0),
                    wp.get("y", 0.0),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                wp["x"] = pos_x
                wp["y"] = pos_y
        elif isinstance(wp, list) and len(wp) >= 2:
            pos_x, pos_y = rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
            wp[0] = pos_x
            wp[1] = pos_y


def apply_runtime_world_yaw_inplace(
    scenario_data: dict[str, Any],
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> None:
    if abs(float(yaw_deg)) <= 1.0e-9:
        return

    mission_cmd = scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict):
        _rotate_waypoint_list_inplace(
            mission_cmd.get("waypoints", None),
            origin_x=origin_x,
            origin_y=origin_y,
            yaw_deg=yaw_deg,
        )
        cached_waypoints = mission_cmd.get("_normalized_waypoints", None)
        if isinstance(cached_waypoints, list):
            _rotate_waypoint_list_inplace(
                cached_waypoints,
                origin_x=origin_x,
                origin_y=origin_y,
                yaw_deg=yaw_deg,
            )

    runtime_spawn = scenario_data.get("_runtime_agent_spawn", None)
    if isinstance(runtime_spawn, dict):
        pos = runtime_spawn.get("pos", None)
        if isinstance(pos, list) and len(pos) >= 2:
            pos_x, pos_y = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
            pos[0] = pos_x
            pos[1] = pos_y
        if "heading" in runtime_spawn:
            try:
                runtime_spawn["heading"] = (float(runtime_spawn.get("heading", 0.0)) + float(yaw_deg)) % 360.0
            except Exception:
                pass

    task_order = scenario_data.get("task_order", None)
    if isinstance(task_order, dict):
        if "anchor_x_m" in task_order and "anchor_y_m" in task_order:
            try:
                pos_x, pos_y = rotate_xy_clockwise(
                    float(task_order.get("anchor_x_m", 0.0)),
                    float(task_order.get("anchor_y_m", 0.0)),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                task_order["anchor_x_m"] = pos_x
                task_order["anchor_y_m"] = pos_y
            except Exception:
                pass
        if "station_heading_deg" in task_order:
            try:
                task_order["station_heading_deg"] = (
                    float(task_order.get("station_heading_deg", 0.0)) + float(yaw_deg)
                ) % 360.0
            except Exception:
                pass

    entities = scenario_data.get("entities", [])
    if not isinstance(entities, list) or not entities:
        return

    candidate_indices = [idx for idx, ent in enumerate(entities) if isinstance(ent, dict) and bool(ent.get("is_agent", False))]
    if not candidate_indices:
        for idx, ent in enumerate(entities):
            if isinstance(ent, dict):
                candidate_indices.append(idx)
                break

    for idx in candidate_indices:
        ent = entities[idx]
        if not isinstance(ent, dict):
            continue
        pos = ent.get("pos", None)
        vel = ent.get("vel", None)
        if isinstance(pos, list) and len(pos) >= 2:
            pos_x, pos_y = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
            pos[0] = pos_x
            pos[1] = pos_y
        if isinstance(vel, list) and len(vel) >= 2:
            vel_x, vel_y = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
            vel[0] = vel_x
            vel[1] = vel_y
        if "heading" in ent:
            try:
                ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
            except Exception:
                pass


def apply_world_yaw_inplace(
    scenario_data: dict[str, Any],
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> None:
    env = scenario_data.get("environment", {})
    zones = env.get("zones", [])
    if isinstance(zones, list):
        for zone in zones:
            if not isinstance(zone, dict):
                continue
            if "x" in zone and "y" in zone:
                zone_x, zone_y = rotate_xy_clockwise(
                    zone.get("x", 0.0),
                    zone.get("y", 0.0),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                zone["x"] = zone_x
                zone["y"] = zone_y
            if "heading" in zone:
                try:
                    zone["heading"] = (float(zone.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    entities = scenario_data.get("entities", [])
    if isinstance(entities, list):
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            pos = ent.get("pos", None)
            vel = ent.get("vel", None)
            if isinstance(pos, list) and len(pos) >= 2:
                pos_x, pos_y = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                pos[0] = pos_x
                pos[1] = pos_y
            if isinstance(vel, list) and len(vel) >= 2:
                vel_x, vel_y = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                vel[0] = vel_x
                vel[1] = vel_y
            if "heading" in ent:
                try:
                    ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    mission_cmd = scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict):
        _rotate_waypoint_list_inplace(
            mission_cmd.get("waypoints", None),
            origin_x=origin_x,
            origin_y=origin_y,
            yaw_deg=yaw_deg,
        )

    task_order = scenario_data.get("task_order", None)
    if isinstance(task_order, dict):
        if "anchor_x_m" in task_order and "anchor_y_m" in task_order:
            try:
                pos_x, pos_y = rotate_xy_clockwise(
                    float(task_order.get("anchor_x_m", 0.0)),
                    float(task_order.get("anchor_y_m", 0.0)),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                task_order["anchor_x_m"] = pos_x
                task_order["anchor_y_m"] = pos_y
            except Exception:
                pass
        if "station_heading_deg" in task_order:
            try:
                task_order["station_heading_deg"] = (
                    float(task_order.get("station_heading_deg", 0.0)) + float(yaw_deg)
                ) % 360.0
            except Exception:
                pass


def _primary_runway_heading_deg(env_cfg: dict[str, Any]) -> float | None:
    zones = env_cfg.get("zones", [])
    if not isinstance(zones, list):
        return None
    best_heading = None
    best_priority = -1
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        name = str(zone.get("name", "")).lower()
        surface = str(zone.get("surface", ""))
        ils_cfg = zone.get("ils", {})
        if not isinstance(ils_cfg, dict):
            ils_cfg = {}
        ils_enabled = bool(ils_cfg.get("enabled", False))
        is_runway = "runway" in name
        priority = 0
        if ils_enabled and is_runway:
            priority = 3
        elif ils_enabled:
            priority = 2
        elif is_runway and surface in ("Concrete", "Asphalt"):
            priority = 1
        if priority <= best_priority:
            continue
        try:
            best_heading = float(zone.get("heading", 0.0)) % 360.0
        except Exception:
            continue
        best_priority = priority
    return best_heading
