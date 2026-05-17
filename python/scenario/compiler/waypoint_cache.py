from __future__ import annotations

from typing import Any

from .clone import _clone_runtime_mission_command, _clone_scenario_value
from .common import (
    _canonical_recovery_approach_name,
    _coerce_nonnegative_int,
    _normalize_waypoint_mode,
    _stable_ref_id,
)


def _normalize_runtime_mission_command(
    cmd: dict[str, Any] | None,
    task_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(cmd, dict):
        return {
            "command_code": 0,
            "target_heading": 0.0,
            "target_altitude": 0.0,
            "target_speed": 0.0,
            "route_ref_id": 0,
            "recovery_base_id": 0,
            "recovery_runway_id": 0,
            "recovery_approach_type": "None",
            "takeoff_procedure_code": 0,
            "takeoff_clearance_code": 0,
            "takeoff_interval_s": 0.0,
            "runway_slot_code": 0,
        }

    task_cfg = task_cfg if isinstance(task_cfg, dict) else {}
    normalized = _clone_runtime_mission_command(cmd)
    normalized["command_code"] = int(normalized.get("command_code", 0))
    normalized["target_heading"] = float(normalized.get("target_heading", 0.0))
    normalized["target_altitude"] = float(normalized.get("target_altitude", 0.0))
    normalized["target_speed"] = float(normalized.get("target_speed", 0.0))
    normalized["route_ref_id"] = _coerce_nonnegative_int(normalized.get("route_ref_id", 0), 0)
    normalized["takeoff_procedure_code"] = _coerce_nonnegative_int(normalized.get("takeoff_procedure_code", 0), 0)
    normalized["takeoff_clearance_code"] = _coerce_nonnegative_int(normalized.get("takeoff_clearance_code", 0), 0)
    normalized["takeoff_interval_s"] = float(normalized.get("takeoff_interval_s", 0.0))
    normalized["runway_slot_code"] = _coerce_nonnegative_int(normalized.get("runway_slot_code", 0), 0)

    recovery_base_id = _coerce_nonnegative_int(
        normalized.get("recovery_base_id", task_cfg.get("recovery_base_id", 0)),
        0,
    )
    recovery_runway_id = _coerce_nonnegative_int(
        normalized.get("recovery_runway_id", task_cfg.get("recovery_runway_id", 0)),
        0,
    )
    landing_mode = str(normalized.get("landing_mode", "")).strip().lower()
    is_terminal_cmd = bool(
        int(normalized.get("command_code", 0)) == 4
        or landing_mode
        or recovery_base_id > 0
        or recovery_runway_id > 0
    )
    recovery_approach_raw = normalized.get(
        "recovery_approach_type",
        task_cfg.get("recovery_approach_type", None),
    )
    if recovery_approach_raw is None and is_terminal_cmd:
        recovery_approach_raw = "StraightIn"
    normalized["recovery_base_id"] = int(recovery_base_id)
    normalized["recovery_runway_id"] = int(recovery_runway_id)
    normalized["recovery_approach_type"] = _canonical_recovery_approach_name(
        recovery_approach_raw,
        landing_mode=landing_mode,
    )

    post = normalized.get("post_waypoint_transition", None)
    if isinstance(post, dict):
        normalized["post_waypoint_transition"] = _normalize_runtime_mission_command(post, task_cfg)
    return normalized


def _normalize_runtime_waypoints(mission_cmd: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(mission_cmd, dict):
        return []
    wps = mission_cmd.get("waypoints", None)
    if not isinstance(wps, list) or not wps:
        return []

    def _f(value: Any, default: float | None = None) -> float | None:
        if value is None:
            return default
        try:
            return float(value)
        except Exception:
            return default

    default_alt = _f(mission_cmd.get("target_altitude", 0.0), 0.0) or 0.0
    default_spd = _f(mission_cmd.get("target_speed", 0.0), 0.0) or 0.0
    default_rad = _f(mission_cmd.get("waypoint_radius_m", mission_cmd.get("arrival_radius_m", 500.0)), 500.0) or 500.0
    default_mode = _normalize_waypoint_mode(mission_cmd.get("waypoint_mode", "flyby"))

    normalized: list[dict[str, Any]] = []
    for wp in wps:
        x = y = z = None
        rad = None
        alt = None
        spd = None
        mode = default_mode
        if isinstance(wp, dict):
            if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                x = _f(wp["pos"][0], 0.0)
                y = _f(wp["pos"][1], 0.0)
                if len(wp["pos"]) >= 3:
                    z = _f(wp["pos"][2], default_alt)
            else:
                x = _f(wp.get("x", None), 0.0)
                y = _f(wp.get("y", None), 0.0)
                z = _f(
                    wp.get("z", wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None)))),
                    default_alt,
                )
            rad = _f(wp.get("radius_m", wp.get("arrival_radius_m", None)), default_rad)
            alt = _f(wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None))), z if z is not None else default_alt)
            spd = _f(wp.get("speed_mps", wp.get("speed", wp.get("target_speed", None))), default_spd)
            mode = _normalize_waypoint_mode(wp.get("waypoint_mode", wp.get("mode", wp.get("pass_mode", default_mode))))
        elif isinstance(wp, list) and len(wp) >= 2:
            x = _f(wp[0], 0.0)
            y = _f(wp[1], 0.0)
            z = _f(wp[2], default_alt) if len(wp) >= 3 else default_alt
            rad = default_rad
            alt = z
            spd = default_spd
        if x is None or y is None:
            continue
        normalized.append(
            {
                "x": float(x),
                "y": float(y),
                "z": float(z if z is not None else default_alt),
                "radius_m": float(rad if rad is not None else default_rad),
                "altitude_m": float(alt if alt is not None else (z if z is not None else default_alt)),
                "speed_mps": float(spd if spd is not None else default_spd),
                "waypoint_mode": str(mode),
            }
        )
    return normalized


def _resolve_route_ref_id(
    mission_cmd: dict[str, Any] | None,
    normalized_waypoints: list[dict[str, Any]] | None = None,
) -> int:
    mission_cmd = mission_cmd if isinstance(mission_cmd, dict) else {}
    route_ref_id = _coerce_nonnegative_int(mission_cmd.get("route_ref_id", 0), 0)
    if route_ref_id > 0:
        return route_ref_id
    waypoints = normalized_waypoints if normalized_waypoints is not None else _normalize_runtime_waypoints(mission_cmd)
    if not waypoints:
        return 0
    payload = []
    for idx, wp in enumerate(waypoints):
        payload.append(
            {
                "idx": idx,
                "x": round(float(wp.get("x", 0.0)), 3),
                "y": round(float(wp.get("y", 0.0)), 3),
                "z": round(float(wp.get("z", wp.get("altitude_m", 0.0))), 3),
                "speed_mps": round(float(wp.get("speed_mps", 0.0)), 3),
                "radius_m": round(float(wp.get("radius_m", 0.0)), 3),
                "waypoint_mode": str(wp.get("waypoint_mode", "")),
            }
        )
    return int(_stable_ref_id(payload))


def invalidate_runtime_waypoint_cache(mission_cmd: dict[str, Any] | None) -> None:
    if not isinstance(mission_cmd, dict):
        return
    mission_cmd.pop("_normalized_waypoints", None)
    mission_cmd["route_ref_id"] = 0
    mission_cmd["_runtime_waypoint_cache_valid"] = False


def cache_runtime_waypoint_cache(
    mission_cmd: dict[str, Any] | None,
    normalized_waypoints: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    route_ref_id: int | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(mission_cmd, dict):
        return []
    if not isinstance(normalized_waypoints, (list, tuple)):
        invalidate_runtime_waypoint_cache(mission_cmd)
        return []
    normalized_list = _clone_scenario_value(list(normalized_waypoints))
    mission_cmd["_normalized_waypoints"] = normalized_list
    resolved_route_ref_id = _coerce_nonnegative_int(route_ref_id, 0)
    if resolved_route_ref_id <= 0:
        resolved_route_ref_id = _resolve_route_ref_id(mission_cmd, normalized_list)
    mission_cmd["route_ref_id"] = int(resolved_route_ref_id) if resolved_route_ref_id > 0 else 0
    mission_cmd["_runtime_waypoint_cache_valid"] = True
    return normalized_list


def materialize_runtime_waypoint_cache(mission_cmd: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(mission_cmd, dict):
        return []
    cached_waypoints = mission_cmd.get("_normalized_waypoints", None)
    if bool(mission_cmd.get("_runtime_waypoint_cache_valid", False)) and isinstance(cached_waypoints, list):
        route_ref_id = _coerce_nonnegative_int(mission_cmd.get("route_ref_id", 0), 0)
        if route_ref_id <= 0:
            route_ref_id = _resolve_route_ref_id(mission_cmd, cached_waypoints)
            mission_cmd["route_ref_id"] = int(route_ref_id) if route_ref_id > 0 else 0
        return cached_waypoints
    normalized_waypoints = _normalize_runtime_waypoints(mission_cmd)
    return cache_runtime_waypoint_cache(mission_cmd, normalized_waypoints)


def _compile_normalized_waypoint_templates(
    mission_cmd_template: dict[str, Any] | None,
) -> tuple[tuple[dict[str, Any], ...], ...]:
    mission_cmd_template = mission_cmd_template if isinstance(mission_cmd_template, dict) else {}
    rand_cfg = mission_cmd_template.get("randomization", None)
    if not isinstance(rand_cfg, dict):
        return ()
    waypoint_templates = rand_cfg.get("waypoint_templates", None)
    if not isinstance(waypoint_templates, list) or not waypoint_templates:
        return ()

    compiled: list[tuple[dict[str, Any], ...]] = []
    for template in waypoint_templates:
        if not isinstance(template, list) or not template:
            compiled.append(tuple())
            continue
        temp_cmd = _clone_runtime_mission_command(mission_cmd_template)
        temp_cmd["waypoints"] = _clone_scenario_value(template)
        normalized = _normalize_runtime_waypoints(temp_cmd)
        compiled.append(tuple(_clone_scenario_value(normalized)))
    return tuple(compiled)


def _compile_waypoint_template_route_ref_ids(
    normalized_waypoint_templates: tuple[tuple[dict[str, Any], ...], ...],
) -> tuple[int, ...]:
    route_ref_ids: list[int] = []
    for template in normalized_waypoint_templates:
        if not template:
            route_ref_ids.append(0)
            continue
        route_ref_ids.append(int(_resolve_route_ref_id({}, list(template))))
    return tuple(route_ref_ids)


__all__ = [
    "_normalize_runtime_mission_command",
    "_normalize_runtime_waypoints",
    "_resolve_route_ref_id",
    "invalidate_runtime_waypoint_cache",
    "cache_runtime_waypoint_cache",
    "materialize_runtime_waypoint_cache",
    "_compile_normalized_waypoint_templates",
    "_compile_waypoint_template_route_ref_ids",
]
