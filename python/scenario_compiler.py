from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Any

import ef_py


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SCALAR_TYPES = (str, int, float, bool, type(None))

_OBJECTIVE_PROPERTY_MAP = {
    "altitude": ef_py.ConditionalObjectiveProperty.Altitude,
    "altitude_agl": ef_py.ConditionalObjectiveProperty.AltitudeAGL,
    "speed": ef_py.ConditionalObjectiveProperty.Speed,
    "ground_speed": ef_py.ConditionalObjectiveProperty.GroundSpeed,
    "gear": ef_py.ConditionalObjectiveProperty.Gear,
    "heading_error_deg": ef_py.ConditionalObjectiveProperty.HeadingErrorDeg,
    "command_code": ef_py.ConditionalObjectiveProperty.CommandCode,
    "ground_track_error_deg": ef_py.ConditionalObjectiveProperty.GroundTrackErrorDeg,
    "runway_cross_abs_m": ef_py.ConditionalObjectiveProperty.RunwayCrossAbsM,
    "runway_from_threshold_m": ef_py.ConditionalObjectiveProperty.RunwayFromThresholdM,
    "on_runway_geom": ef_py.ConditionalObjectiveProperty.OnRunwayGeom,
    "on_runway": ef_py.ConditionalObjectiveProperty.OnRunway,
    "on_ground": ef_py.ConditionalObjectiveProperty.OnGround,
    "sink_rate_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "vertical_speed_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "ils_localizer_abs": ef_py.ConditionalObjectiveProperty.IlsLocalizerAbs,
    "ils_glideslope_abs": ef_py.ConditionalObjectiveProperty.IlsGlideslopeAbs,
    "dme_m": ef_py.ConditionalObjectiveProperty.DmeM,
    "heading": ef_py.ConditionalObjectiveProperty.Heading,
    "x": ef_py.ConditionalObjectiveProperty.X,
    "y": ef_py.ConditionalObjectiveProperty.Y,
}

_OBJECTIVE_OP_MAP = {
    ">=": ef_py.ConditionalObjectiveOp.GreaterEqual,
    ">": ef_py.ConditionalObjectiveOp.GreaterThan,
    "<=": ef_py.ConditionalObjectiveOp.LessEqual,
    "<": ef_py.ConditionalObjectiveOp.LessThan,
}

_OBJECTIVE_DYNAMIC_TARGET_MAP = {
    "CMD_ALT": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_ALTITUDE": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_SPEED": (ef_py.ConditionalObjectiveTargetKind.CommandSpeed, 0.90),
    "CMD_HDG": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
    "CMD_HEADING": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
}

_SURFACE_TYPE_MAP = {
    "Concrete": 0,
    "Asphalt": 1,
    "HardPacked": 2,
    "SoftDirt": 3,
    "Water": 4,
    "Obstacle": 5,
}


def _mtime_ns(path: str) -> int:
    return int(os.stat(path).st_mtime_ns)


def _clone_scenario_value(value: Any) -> Any:
    value_type = type(value)
    if value_type in _SCALAR_TYPES:
        return value
    if value_type is dict:
        return {key: _clone_scenario_value(item) for key, item in value.items()}
    if value_type is list:
        return [_clone_scenario_value(item) for item in value]
    if value_type is tuple:
        return tuple(_clone_scenario_value(item) for item in value)

    # Inline test scenarios should remain supported even if they contain a small
    # amount of non-JSON data. Keep a slow fallback for those cases.
    if isinstance(value, dict):
        return {key: _clone_scenario_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_scenario_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_scenario_value(item) for item in value)
    return copy.deepcopy(value)


def _coerce_nonnegative_int(value: Any, default: int = 0) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


def _normalize_waypoint_mode(mode_value: Any) -> str:
    mode = str(mode_value if mode_value is not None else "flyby").strip().lower()
    if mode in ("fly-over", "fly_over", "overfly"):
        return "flyover"
    if mode in ("flyby", "flyover"):
        return mode
    return "flyby"


def _canonical_recovery_approach_name(value: Any, *, landing_mode: str = "") -> str:
    default_by_mode = {
        "ils": "ILS",
        "ils_final": "ILS",
        "visual": "Visual",
        "overhead": "Overhead",
        "tacan": "TACAN",
    }
    default_name = default_by_mode.get(str(landing_mode or "").strip().lower(), "StraightIn")
    if value is None:
        return default_name
    try:
        if hasattr(value, "name"):
            value = value.name
    except Exception:
        pass
    if isinstance(value, str):
        key = str(value).strip().lower()
        mapping = {
            "": default_name,
            "none": "None",
            "straightin": "StraightIn",
            "straight_in": "StraightIn",
            "ils": "ILS",
            "ils_final": "ILS",
            "visual": "Visual",
            "overhead": "Overhead",
            "tacan": "TACAN",
        }
        return mapping.get(key, default_name)
    mapping_by_int = {
        0: "None",
        1: "StraightIn",
        2: "ILS",
        3: "Visual",
        4: "Overhead",
        5: "TACAN",
    }
    return mapping_by_int.get(_coerce_nonnegative_int(value, 0), default_name)


def _stable_ref_id(payload: Any) -> int:
    try:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        text = repr(payload)
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    ref_id = int.from_bytes(digest[:8], "big", signed=False)
    return ref_id if ref_id > 0 else 1


def _merge_prefab_data(target: dict[str, Any], prefab: dict[str, Any]) -> None:
    if "zones" in prefab:
        if "environment" not in target or not isinstance(target.get("environment"), dict):
            target["environment"] = {}
        current_zones = target["environment"].get("zones", [])
        if not isinstance(current_zones, list):
            current_zones = []
        current_zones.extend(_clone_scenario_value(prefab["zones"]))
        target["environment"]["zones"] = current_zones

    if "entities" in prefab:
        current_entities = target.get("entities", [])
        if not isinstance(current_entities, list):
            current_entities = []
        current_entities.extend(_clone_scenario_value(prefab["entities"]))
        target["entities"] = current_entities


def _compile_merged_scenario_data(
    raw_scenario_data: dict[str, Any],
    *,
    project_root: str,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    merged = _clone_scenario_value(raw_scenario_data)
    imports = merged.get("imports", None)
    imported_files: list[str] = []
    warnings: list[str] = []

    if isinstance(imports, list):
        for imp in imports:
            if not isinstance(imp, dict):
                continue
            rel_path = imp.get("file")
            if not rel_path:
                continue

            full_path = os.path.abspath(os.path.join(project_root, str(rel_path)))
            if not os.path.exists(full_path):
                warnings.append(f"Warning: Import file not found: {full_path}")
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                prefab = json.load(f)
            if not isinstance(prefab, dict):
                continue

            _merge_prefab_data(merged, prefab)
            imported_files.append(full_path)

    return merged, tuple(imported_files), tuple(warnings)


def _clone_runtime_environment(env_cfg: Any) -> Any:
    if not isinstance(env_cfg, dict):
        return _clone_scenario_value(env_cfg)
    cloned = dict(env_cfg)
    if "zones" in env_cfg:
        cloned["zones"] = _clone_scenario_value(env_cfg.get("zones", []))
    return cloned


def _clone_runtime_entity(entity_cfg: Any) -> Any:
    if not isinstance(entity_cfg, dict):
        return _clone_scenario_value(entity_cfg)
    cloned = dict(entity_cfg)
    if "pos" in entity_cfg:
        pos = entity_cfg.get("pos")
        if isinstance(pos, list):
            cloned["pos"] = list(pos)
        elif isinstance(pos, tuple):
            cloned["pos"] = list(pos)
        else:
            cloned["pos"] = _clone_scenario_value(pos)
    if "vel" in entity_cfg:
        vel = entity_cfg.get("vel")
        if isinstance(vel, list):
            cloned["vel"] = list(vel)
        elif isinstance(vel, tuple):
            cloned["vel"] = list(vel)
        else:
            cloned["vel"] = _clone_scenario_value(vel)
    return cloned


def _clone_runtime_entities(entities_cfg: Any) -> Any:
    if not isinstance(entities_cfg, list):
        return _clone_scenario_value(entities_cfg)
    return [_clone_runtime_entity(entity_cfg) for entity_cfg in entities_cfg]


def _clone_runtime_mission_command(cmd_cfg: Any) -> Any:
    if not isinstance(cmd_cfg, dict):
        return _clone_scenario_value(cmd_cfg)
    cloned = dict(cmd_cfg)
    if "waypoints" in cmd_cfg:
        cloned["waypoints"] = _clone_scenario_value(cmd_cfg.get("waypoints", []))
    if isinstance(cmd_cfg.get("post_waypoint_transition"), dict):
        cloned["post_waypoint_transition"] = _clone_runtime_mission_command(cmd_cfg["post_waypoint_transition"])
    return cloned


def _clone_runtime_task_order(task_cfg: Any) -> Any:
    if not isinstance(task_cfg, dict):
        return _clone_scenario_value(task_cfg)
    return dict(task_cfg)


def _clone_runtime_environment_context(env_cfg: Any) -> Any:
    if not isinstance(env_cfg, dict):
        return _clone_scenario_value(env_cfg)
    cloned: dict[str, Any] = {}
    if "max_steps" in env_cfg:
        cloned["max_steps"] = _clone_scenario_value(env_cfg.get("max_steps"))
    if "time_step" in env_cfg:
        cloned["time_step"] = _clone_scenario_value(env_cfg.get("time_step"))
    return cloned


def _extract_runtime_agent_spawn_context(entities_cfg: Any) -> dict[str, Any] | None:
    if not isinstance(entities_cfg, list) or not entities_cfg:
        return None

    spawn = None
    for ent_cfg in entities_cfg:
        if isinstance(ent_cfg, dict) and bool(ent_cfg.get("is_agent", False)):
            spawn = ent_cfg
            break
    if spawn is None:
        spawn = entities_cfg[0] if isinstance(entities_cfg[0], dict) else None
    if not isinstance(spawn, dict):
        return None

    context: dict[str, Any] = {
        "name": str(spawn.get("name", "")),
        "is_agent": bool(spawn.get("is_agent", False)),
    }
    if "heading" in spawn:
        try:
            context["heading"] = float(spawn.get("heading", 0.0))
        except Exception:
            pass
    if "pos" in spawn:
        pos = spawn.get("pos")
        if isinstance(pos, list):
            context["pos"] = list(pos)
        elif isinstance(pos, tuple):
            context["pos"] = list(pos)
        else:
            context["pos"] = _clone_scenario_value(pos)
    return context


def _clone_runtime_scenario_data(merged_scenario_data: dict[str, Any]) -> dict[str, Any]:
    runtime_data = dict(merged_scenario_data)
    if "environment" in merged_scenario_data:
        runtime_data["environment"] = _clone_runtime_environment(merged_scenario_data.get("environment"))
    if "entities" in merged_scenario_data:
        runtime_data["entities"] = _clone_runtime_entities(merged_scenario_data.get("entities"))
    if "mission_command" in merged_scenario_data:
        runtime_data["mission_command"] = _clone_runtime_mission_command(merged_scenario_data.get("mission_command"))
    if "task_order" in merged_scenario_data:
        runtime_data["task_order"] = _clone_runtime_task_order(merged_scenario_data.get("task_order"))
    return runtime_data


def _clone_runtime_context_scenario_data(merged_scenario_data: dict[str, Any]) -> dict[str, Any]:
    runtime_data: dict[str, Any] = {}
    if "environment" in merged_scenario_data:
        runtime_data["environment"] = _clone_runtime_environment_context(merged_scenario_data.get("environment"))
    if "mission_command" in merged_scenario_data:
        runtime_data["mission_command"] = _clone_runtime_mission_command(merged_scenario_data.get("mission_command"))
    if "task_order" in merged_scenario_data:
        runtime_data["task_order"] = _clone_runtime_task_order(merged_scenario_data.get("task_order"))
    if "meta" in merged_scenario_data:
        runtime_data["meta"] = _clone_scenario_value(merged_scenario_data.get("meta"))
    if "rewards" in merged_scenario_data:
        runtime_data["rewards"] = _clone_scenario_value(merged_scenario_data.get("rewards"))
    if "objectives" in merged_scenario_data:
        runtime_data["objectives"] = _clone_scenario_value(merged_scenario_data.get("objectives"))

    agent_spawn = _extract_runtime_agent_spawn_context(merged_scenario_data.get("entities"))
    if agent_spawn is not None:
        runtime_data["_runtime_agent_spawn"] = agent_spawn
    return runtime_data


def _normalize_runtime_mission_command(cmd: dict[str, Any] | None, task_cfg: dict[str, Any] | None = None) -> dict[str, Any]:
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
        }

    task_cfg = task_cfg if isinstance(task_cfg, dict) else {}
    normalized = _clone_runtime_mission_command(cmd)
    normalized["command_code"] = int(normalized.get("command_code", 0))
    normalized["target_heading"] = float(normalized.get("target_heading", 0.0))
    normalized["target_altitude"] = float(normalized.get("target_altitude", 0.0))
    normalized["target_speed"] = float(normalized.get("target_speed", 0.0))
    normalized["route_ref_id"] = _coerce_nonnegative_int(normalized.get("route_ref_id", 0), 0)

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


def _resolve_route_ref_id(mission_cmd: dict[str, Any] | None, normalized_waypoints: list[dict[str, Any]] | None = None) -> int:
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


def _compile_normalized_waypoint_templates(mission_cmd_template: dict[str, Any] | None) -> tuple[tuple[dict[str, Any], ...], ...]:
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


def _extract_ils_beacons(env_cfg: dict[str, Any] | None) -> list[dict[str, Any]]:
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
    beacons: list[dict[str, Any]] = []
    zones = env_cfg.get("zones", [])
    if not isinstance(zones, list):
        return beacons
    for idx, zone in enumerate(zones):
        if not isinstance(zone, dict):
            continue
        name = str(zone.get("name", ""))
        surface = str(zone.get("surface", ""))
        ils_cfg = zone.get("ils", {})
        if not isinstance(ils_cfg, dict):
            ils_cfg = {}
        enabled = bool(ils_cfg.get("enabled", False))
        if not enabled:
            if ("runway" in name.lower()) and surface in ("Concrete", "Asphalt"):
                enabled = True
            else:
                continue
        try:
            cx = float(zone.get("x", 0.0))
            cy = float(zone.get("y", 0.0))
            width = float(zone.get("width", 0.0))
            length = float(zone.get("length", 0.0))
            heading = float(zone.get("heading", 0.0)) % 360.0
        except Exception:
            continue
        if length <= 1.0:
            continue
        if width <= 1.0:
            width = float(ils_cfg.get("width_m", 60.0))
        glide_slope_deg = float(ils_cfg.get("glide_slope_deg", 3.0))
        loc_max_deg = float(ils_cfg.get("loc_max_deg", 2.5))
        gs_max_deg = float(ils_cfg.get("gs_max_deg", 0.7))
        range_m = float(ils_cfg.get("range_m", 25000.0))
        elev_m = float(ils_cfg.get("elev_m", 0.0))
        h_rad = math.radians(heading)
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        thr_x = cx - fwd_x * (length * 0.5)
        thr_y = cy - fwd_y * (length * 0.5)
        beacons.append(
            {
                "runway_id": int(zone.get("runway_id", idx)),
                "name": name,
                "cx": cx,
                "cy": cy,
                "thr_x": thr_x,
                "thr_y": thr_y,
                "heading": heading,
                "length": length,
                "width": width,
                "elev_m": elev_m,
                "glide_slope_deg": glide_slope_deg,
                "loc_max_deg": max(0.1, loc_max_deg),
                "gs_max_deg": max(0.1, gs_max_deg),
                "range_m": max(100.0, range_m),
            }
        )
    return beacons


def rotate_ils_beacon_templates(
    templates: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> list[dict[str, Any]]:
    if not templates:
        return []
    import math

    rad = -math.radians(float(yaw_deg))
    c = math.cos(rad)
    s = math.sin(rad)

    def _rot(x: float, y: float) -> tuple[float, float]:
        dx = float(x) - float(origin_x)
        dy = float(y) - float(origin_y)
        rx = float(origin_x) + c * dx - s * dy
        ry = float(origin_y) + s * dx + c * dy
        return rx, ry

    rotated = []
    for beacon in templates:
        if not isinstance(beacon, dict):
            continue
        item = dict(beacon)
        item["cx"], item["cy"] = _rot(float(beacon.get("cx", 0.0)), float(beacon.get("cy", 0.0)))
        item["thr_x"], item["thr_y"] = _rot(float(beacon.get("thr_x", 0.0)), float(beacon.get("thr_y", 0.0)))
        item["heading"] = (float(beacon.get("heading", 0.0)) + float(yaw_deg)) % 360.0
        rotated.append(item)
    return rotated


def _primary_runway_heading_deg(env_cfg: dict[str, Any] | None) -> float | None:
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
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


def _infer_wind_ref_alt_m(merged_scenario_data: dict[str, Any]) -> float:
    try:
        for ent in merged_scenario_data.get("entities", []):
            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                pos = ent.get("pos", None)
                if isinstance(pos, list) and len(pos) >= 3:
                    return float(pos[2])
    except Exception:
        return 0.0
    try:
        entities = merged_scenario_data.get("entities", [])
        if isinstance(entities, list) and entities:
            pos = entities[0].get("pos", None) if isinstance(entities[0], dict) else None
            if isinstance(pos, list) and len(pos) >= 3:
                return float(pos[2])
    except Exception:
        return 0.0
    return 0.0


def _compile_world_layout_template(merged_scenario_data: dict[str, Any]) -> CompiledWorldLayoutTemplate:
    env_cfg = merged_scenario_data.get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    wind_cfg = env_cfg.get("wind", {})
    if not isinstance(wind_cfg, dict):
        wind_cfg = {}

    zones_out: list[CompiledZoneLayoutTemplate] = []
    zone_defs = env_cfg.get("zones", [])
    if isinstance(zone_defs, list):
        for zone in zone_defs:
            if not isinstance(zone, dict):
                continue
            zones_out.append(
                CompiledZoneLayoutTemplate(
                    name=str(zone.get("name", "Zone")),
                    x=float(zone.get("x", 0.0)),
                    y=float(zone.get("y", 0.0)),
                    width=float(zone.get("width", 1000.0)),
                    length=float(zone.get("length", 1000.0)),
                    heading=float(zone.get("heading", 0.0)),
                    surface_type=int(_SURFACE_TYPE_MAP.get(zone.get("surface", "SoftDirt"), 3)),
                )
            )

    spawns_out: list[CompiledSpawnLayoutTemplate] = []
    entities = merged_scenario_data.get("entities", [])
    if isinstance(entities, list):
        for ent_cfg in entities:
            if not isinstance(ent_cfg, dict):
                continue
            pos = ent_cfg.get("pos", [0.0, 0.0, 0.0])
            vel = ent_cfg.get("vel", [0.0, 0.0, 0.0])
            pos_vals = list(pos) if isinstance(pos, (list, tuple)) else [0.0, 0.0, 0.0]
            vel_vals = list(vel) if isinstance(vel, (list, tuple)) else [0.0, 0.0, 0.0]
            while len(pos_vals) < 3:
                pos_vals.append(0.0)
            while len(vel_vals) < 3:
                vel_vals.append(0.0)
            rand_cfg = ent_cfg.get("randomization", {})
            if not isinstance(rand_cfg, dict):
                rand_cfg = {}
            spawns_out.append(
                CompiledSpawnLayoutTemplate(
                    entity_name=str(ent_cfg.get("name", "")),
                    side_name=str(ent_cfg.get("side", "Neutral")),
                    type_name=str(ent_cfg.get("type", "")),
                    is_agent=bool(ent_cfg.get("is_agent", False)),
                    x=float(pos_vals[0]),
                    y=float(pos_vals[1]),
                    z=float(pos_vals[2]),
                    heading=float(ent_cfg.get("heading", 0.0)),
                    pitch=float(ent_cfg.get("pitch", 0.0)),
                    roll=float(ent_cfg.get("roll", 0.0)),
                    vx=float(vel_vals[0]),
                    vy=float(vel_vals[1]),
                    vz=float(vel_vals[2]),
                    randomization=_clone_scenario_value(rand_cfg),
                )
            )

    return CompiledWorldLayoutTemplate(
        time_step_s=float(env_cfg["time_step"]) if "time_step" in env_cfg else None,
        terrain_type=str(env_cfg.get("terrain_type", "legacy")).strip() or "legacy",
        wind_speed_mps=float(wind_cfg.get("speed_mps", 10.0)),
        wind_dir_from_deg=float(wind_cfg.get("dir_from_deg", 270.0)),
        wind_shear_mps_per_km=float(wind_cfg.get("shear_mps_per_km", 4.0)),
        env_randomization=_clone_scenario_value(env_cfg.get("randomization", {}))
        if isinstance(env_cfg.get("randomization", {}), dict)
        else {},
        primary_runway_heading_deg=_primary_runway_heading_deg(env_cfg),
        wind_ref_alt_m=float(_infer_wind_ref_alt_m(merged_scenario_data)),
        zones=tuple(zones_out),
        spawns=tuple(spawns_out),
    )


def _compile_conditional_objectives(objectives: Any) -> tuple[Any, ...]:
    compiled = []
    if not isinstance(objectives, list):
        return tuple(compiled)
    for obj in objectives:
        if not isinstance(obj, dict):
            continue
        if str(obj.get("type", "")).strip().lower() != "conditional":
            continue
        spec = ef_py.ConditionalObjectiveSpec()
        spec.reward_bonus = float(obj.get("reward", 1000.0))
        conds = []
        for cond in obj.get("conditions", []):
            if not isinstance(cond, dict):
                continue
            compiled_cond = ef_py.ConditionalObjectiveCondition()
            prop_key = str(cond.get("property", "")).strip()
            compiled_cond.property_code = _OBJECTIVE_PROPERTY_MAP.get(prop_key, ef_py.ConditionalObjectiveProperty.Unknown)
            compiled_cond.op_code = _OBJECTIVE_OP_MAP.get(str(cond.get("op", ">=")).strip(), ef_py.ConditionalObjectiveOp.GreaterEqual)
            compiled_cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
            compiled_cond.target_scale = 1.0
            tgt = cond.get("value", 0.0)
            if isinstance(tgt, str):
                target_info = _OBJECTIVE_DYNAMIC_TARGET_MAP.get(tgt.strip().upper())
                if target_info is not None:
                    compiled_cond.target_kind = target_info[0]
                    compiled_cond.target_scale = float(cond.get("scale", target_info[1]))
                    compiled_cond.target_value = 0.0
                else:
                    try:
                        compiled_cond.target_value = float(tgt)
                    except Exception:
                        compiled_cond.target_value = 0.0
            else:
                try:
                    compiled_cond.target_value = float(tgt)
                except Exception:
                    compiled_cond.target_value = 0.0
            conds.append(compiled_cond)
        spec.conditions = conds
        compiled.append(spec)
    return tuple(compiled)


def _build_objective_shaping_config(cfg: dict[str, Any] | None) -> Any:
    cfg = cfg if isinstance(cfg, dict) else {}
    shaping = ef_py.ObjectiveShapingConfig()
    shaping.runway_cross_penalty_weight = float(cfg.get("success_runway_cross_penalty_weight", 0.0))
    shaping.runway_cross_deadband_m = float(cfg.get("success_runway_cross_deadband_m", 0.0))
    shaping.runway_cross_norm_m = float(cfg.get("success_runway_cross_norm_m", 20.0))
    shaping.runway_cross_power = float(cfg.get("success_runway_cross_power", 2.0))
    shaping.runway_cross_clip = float(cfg.get("success_runway_cross_clip", 0.0))
    shaping.ground_track_penalty_weight = float(cfg.get("success_ground_track_error_penalty_weight", 0.0))
    shaping.ground_track_deadband_deg = float(cfg.get("success_ground_track_error_deadband_deg", 0.0))
    shaping.ground_track_norm_deg = float(cfg.get("success_ground_track_error_norm_deg", 10.0))
    shaping.ground_track_power = float(cfg.get("success_ground_track_error_power", 2.0))
    shaping.ground_track_clip = float(cfg.get("success_ground_track_error_clip", 0.0))
    return shaping


@dataclass(frozen=True)
class WaypointModeRewardConfig:
    progress_weight: float = 0.0
    progress_negative_scale: float = 1.0
    distance_weight: float = 0.0
    distance_clip_m: float = 0.0
    distance_scale_by_route: bool = False
    distance_route_ref_m: float = 55000.0
    distance_route_scale_min: float = 0.5
    distance_route_scale_max: float = 1.0
    cross_track_weight: float = 0.0
    cross_track_deadband_m: float = 0.0
    cross_track_norm_m: float = 1000.0
    cross_track_power: float = 1.0
    cross_track_clip: float = 0.0
    turn_relief_max: float = 0.0
    proximity_weight: float = 0.0
    proximity_ref_m: float = 1500.0
    proximity_power: float = 1.0
    reached_bonus: float = 0.0
    heading_relief_max: float = 0.0
    turn_relief_window_m: float = 3000.0
    turn_relief_min_turn_deg: float = 15.0
    turn_relief_angle_ref_deg: float = 90.0
    turn_relief_power: float = 1.0


@dataclass(frozen=True)
class ApproachRewardConfig:
    localizer_weight: float = 0.0
    localizer_deadband: float = 0.0
    localizer_norm: float = 1.0
    localizer_power: float = 2.0
    localizer_clip: float = 0.0
    localizer_improve_weight: float = 0.0
    glideslope_weight: float = 0.0
    glideslope_deadband: float = 0.0
    glideslope_norm: float = 1.0
    glideslope_power: float = 2.0
    glideslope_clip: float = 0.0
    glideslope_improve_weight: float = 0.0
    dme_progress_weight: float = 0.0
    dme_progress_localizer_band: float = 0.0
    dme_progress_glideslope_band: float = 0.0
    dme_progress_quality_power: float = 1.0
    capture_bonus: float = 0.0
    capture_localizer_band: float = 0.20
    capture_glideslope_band: float = 0.20
    sink_rate_weight: float = 0.0
    flare_agl_m: float = 20.0
    sink_rate_deadband_mps: float = 0.0
    sink_rate_norm_mps: float = 2.0
    sink_rate_power: float = 2.0
    sink_rate_clip: float = 0.0
    active: bool = False


@dataclass(frozen=True)
class SafetyRewardConfig:
    crash_penalty: float = -1000.0
    survival_reward: float = 0.01
    stall_threshold_deg: float = 15.0
    stall_penalty_weight: float = -1.0
    stall_penalty_clip: float = 0.0
    overload_g_threshold: float = 6.0
    overload_penalty_weight: float = -1.0
    overload_penalty_clip: float = 0.0
    overload_min_alt_agl_m: float = 5.0
    failfast_penalty: float = -50.0
    gear_collapse_penalty: float = -500.0
    gear_stress_penalty_weight: float = -10.0
    off_runway_penalty: float = -1.0
    off_runway_terminate_speed: float = 0.0
    off_runway_terminate_grace_s: float = 0.0
    off_runway_terminate_penalty: float = -200.0
    on_ground_alt_threshold: float = 2.5
    airborne_alt_threshold: float = 5.0
    runway_width_margin_m: float = 2.0
    runway_length_margin_m: float = 0.0
    waypoint_mission_success_bonus: float = 1000.0


@dataclass(frozen=True)
class LNavRuntimeConfig:
    cdi_full_scale_m: float = 1500.0
    lookahead_m: float = 1500.0
    max_intercept_deg: float = 25.0
    capture_max_intercept_deg: float = 45.0
    capture_xtrack_m: float = 0.0
    capture_course_error_deg: float = 45.0
    direct_to_final_fix: bool = True
    flyover_capture_window_m: float | None = None
    bank_limit_deg: float = 30.0
    sequence_gate_scale: float = 0.35
    sequence_gate_min_m: float | None = None
    sequence_gate_max_m: float | None = None


@dataclass(frozen=True)
class CompiledZoneLayoutTemplate:
    name: str
    x: float
    y: float
    width: float
    length: float
    heading: float
    surface_type: int


@dataclass(frozen=True)
class CompiledSpawnLayoutTemplate:
    entity_name: str
    side_name: str
    type_name: str
    is_agent: bool
    x: float
    y: float
    z: float
    heading: float
    pitch: float
    roll: float
    vx: float
    vy: float
    vz: float
    randomization: dict[str, Any]


@dataclass(frozen=True)
class CompiledWorldLayoutTemplate:
    time_step_s: float | None
    terrain_type: str
    wind_speed_mps: float
    wind_dir_from_deg: float
    wind_shear_mps_per_km: float
    env_randomization: dict[str, Any]
    primary_runway_heading_deg: float | None
    wind_ref_alt_m: float
    zones: tuple[CompiledZoneLayoutTemplate, ...]
    spawns: tuple[CompiledSpawnLayoutTemplate, ...]


@dataclass(frozen=True)
class CompiledScenarioRuntimeMetadata:
    mission_command_template: dict[str, Any]
    rewards_config: dict[str, Any]
    normalized_route_waypoints: tuple[dict[str, Any], ...]
    normalized_waypoint_templates: tuple[tuple[dict[str, Any], ...], ...]
    waypoint_template_route_ref_ids: tuple[int, ...]
    compiled_conditional_objectives: tuple[Any, ...]
    objective_shaping_cfg: Any
    ils_beacon_templates: tuple[dict[str, Any], ...]
    waypoint_mode_configs: dict[str, WaypointModeRewardConfig]
    approach_reward_config: ApproachRewardConfig
    safety_reward_config: SafetyRewardConfig
    lnav_config: LNavRuntimeConfig
    layout_template: CompiledWorldLayoutTemplate


def _cfg_value_for_waypoint_mode(cfg: dict[str, Any], key: str, mode_value: Any, default: Any = None) -> Any:
    mode = _normalize_waypoint_mode(mode_value)
    mode_key = f"{key}_{mode}"
    if mode_key in cfg:
        return cfg.get(mode_key)
    if key in cfg:
        return cfg.get(key)
    return default


def _build_waypoint_mode_reward_config(cfg: dict[str, Any], *, mode: str) -> WaypointModeRewardConfig:
    mode = _normalize_waypoint_mode(mode)
    default_proximity_ref_m = 1500.0
    return WaypointModeRewardConfig(
        progress_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_progress_weight", mode, 0.0)),
        progress_negative_scale=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_progress_negative_scale", mode, 1.0)),
        distance_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_weight", mode, 0.0)),
        distance_clip_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_clip_m", mode, 0.0)),
        distance_scale_by_route=bool(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_scale_by_route", mode, False)),
        distance_route_ref_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_ref_m", mode, 55000.0)),
        distance_route_scale_min=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_min", mode, 0.5)),
        distance_route_scale_max=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_max", mode, 1.0)),
        cross_track_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_weight", mode, 0.0)),
        cross_track_deadband_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_deadband_m", mode, 0.0)),
        cross_track_norm_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_norm_m", mode, 1000.0)),
        cross_track_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_power", mode, 1.0)),
        cross_track_clip=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_clip", mode, 0.0)),
        turn_relief_max=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0)),
        proximity_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_weight", mode, 0.0)),
        proximity_ref_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_ref_m", mode, default_proximity_ref_m)),
        proximity_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_power", mode, 1.0)),
        reached_bonus=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_reached_bonus", mode, 0.0)),
        heading_relief_max=float(
            _cfg_value_for_waypoint_mode(
                cfg,
                "waypoint_turn_heading_relief_max",
                mode,
                _cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0),
            )
        ),
        turn_relief_window_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_window_m", mode, 3000.0)),
        turn_relief_min_turn_deg=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_min_turn_deg", mode, 15.0)),
        turn_relief_angle_ref_deg=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_angle_ref_deg", mode, 90.0)),
        turn_relief_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_power", mode, 1.0)),
    )


def _build_approach_reward_config(cfg: dict[str, Any]) -> ApproachRewardConfig:
    out = ApproachRewardConfig(
        localizer_weight=float(cfg.get("approach_localizer_weight", 0.0)),
        localizer_deadband=float(cfg.get("approach_localizer_deadband", 0.0)),
        localizer_norm=float(cfg.get("approach_localizer_norm", 1.0)),
        localizer_power=float(cfg.get("approach_localizer_power", 2.0)),
        localizer_clip=float(cfg.get("approach_localizer_clip", 0.0)),
        localizer_improve_weight=float(cfg.get("approach_localizer_improve_weight", 0.0)),
        glideslope_weight=float(cfg.get("approach_glideslope_weight", 0.0)),
        glideslope_deadband=float(cfg.get("approach_glideslope_deadband", 0.0)),
        glideslope_norm=float(cfg.get("approach_glideslope_norm", 1.0)),
        glideslope_power=float(cfg.get("approach_glideslope_power", 2.0)),
        glideslope_clip=float(cfg.get("approach_glideslope_clip", 0.0)),
        glideslope_improve_weight=float(cfg.get("approach_glideslope_improve_weight", 0.0)),
        dme_progress_weight=float(cfg.get("approach_dme_progress_weight", 0.0)),
        dme_progress_localizer_band=float(cfg.get("approach_dme_progress_localizer_band", 0.0)),
        dme_progress_glideslope_band=float(cfg.get("approach_dme_progress_glideslope_band", 0.0)),
        dme_progress_quality_power=float(cfg.get("approach_dme_progress_quality_power", 1.0)),
        capture_bonus=float(cfg.get("approach_capture_bonus", 0.0)),
        capture_localizer_band=float(cfg.get("approach_capture_localizer_band", 0.20)),
        capture_glideslope_band=float(cfg.get("approach_capture_glideslope_band", 0.20)),
        sink_rate_weight=float(cfg.get("landing_sink_rate_penalty_weight", 0.0)),
        flare_agl_m=float(cfg.get("landing_flare_agl_m", 20.0)),
        sink_rate_deadband_mps=float(cfg.get("landing_sink_rate_deadband_mps", 0.0)),
        sink_rate_norm_mps=float(cfg.get("landing_sink_rate_norm_mps", 2.0)),
        sink_rate_power=float(cfg.get("landing_sink_rate_power", 2.0)),
        sink_rate_clip=float(cfg.get("landing_sink_rate_clip", 0.0)),
    )
    active = bool(
        out.localizer_weight != 0.0
        or out.glideslope_weight != 0.0
        or out.dme_progress_weight != 0.0
        or out.capture_bonus != 0.0
        or out.sink_rate_weight != 0.0
    )
    return ApproachRewardConfig(**{**out.__dict__, "active": active})


def _build_safety_reward_config(cfg: dict[str, Any]) -> SafetyRewardConfig:
    return SafetyRewardConfig(
        crash_penalty=float(cfg.get("crash_penalty", -1000.0)),
        survival_reward=float(cfg.get("survival", 0.01)),
        stall_threshold_deg=float(cfg.get("stall_aoa_threshold", 15.0)),
        stall_penalty_weight=float(cfg.get("stall_penalty", -1.0)),
        stall_penalty_clip=float(cfg.get("stall_penalty_clip", 0.0)),
        overload_g_threshold=float(cfg.get("overload_g_threshold", 6.0)),
        overload_penalty_weight=float(cfg.get("overload_penalty", -1.0)),
        overload_penalty_clip=float(cfg.get("overload_penalty_clip", 0.0)),
        overload_min_alt_agl_m=float(cfg.get("overload_min_alt_agl_m", 5.0)),
        failfast_penalty=float(cfg.get("failfast_penalty", -50.0)),
        gear_collapse_penalty=float(cfg.get("gear_collapse_penalty", -500.0)),
        gear_stress_penalty_weight=float(cfg.get("gear_stress_penalty", -10.0)),
        off_runway_penalty=float(cfg.get("off_runway_penalty", -1.0)),
        off_runway_terminate_speed=float(cfg.get("off_runway_terminate_speed", 0.0)),
        off_runway_terminate_grace_s=float(cfg.get("off_runway_terminate_grace_s", 0.0)),
        off_runway_terminate_penalty=float(cfg.get("off_runway_terminate_penalty", -200.0)),
        on_ground_alt_threshold=float(cfg.get("on_ground_alt_threshold", 2.5)),
        airborne_alt_threshold=float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0))),
        runway_width_margin_m=float(cfg.get("runway_width_margin_m", 2.0)),
        runway_length_margin_m=float(cfg.get("runway_length_margin_m", 0.0)),
        waypoint_mission_success_bonus=float(cfg.get("waypoint_mission_success_bonus", 1000.0)),
    )


def _build_lnav_runtime_config(mission_cmd: dict[str, Any]) -> LNavRuntimeConfig:
    cdi_full_scale_m = float(
        mission_cmd.get(
            "nav_course_dev_full_scale_m",
            mission_cmd.get(
                "course_dev_full_scale_m",
                max(1000.0, float(mission_cmd.get("waypoint_radius_m", 1000.0))),
            ),
        )
    )
    capture_xtrack = mission_cmd.get("lnav_capture_xtrack_m", None)
    flyover_capture_window = mission_cmd.get("lnav_flyover_capture_window_m", None)
    seq_gate_min = mission_cmd.get("lnav_sequence_gate_min_m", None)
    seq_gate_max = mission_cmd.get("lnav_sequence_gate_max_m", None)
    max_intercept_deg = float(mission_cmd.get("lnav_max_intercept_deg", 25.0))
    return LNavRuntimeConfig(
        cdi_full_scale_m=float(cdi_full_scale_m),
        lookahead_m=float(mission_cmd.get("lnav_lookahead_m", 1500.0)),
        max_intercept_deg=float(max_intercept_deg),
        capture_max_intercept_deg=float(mission_cmd.get("lnav_capture_max_intercept_deg", max(max_intercept_deg, 45.0))),
        capture_xtrack_m=0.0 if capture_xtrack is None else float(capture_xtrack),
        capture_course_error_deg=float(mission_cmd.get("lnav_capture_course_error_deg", 45.0)),
        direct_to_final_fix=bool(mission_cmd.get("lnav_direct_to_final_fix", True)),
        flyover_capture_window_m=None if flyover_capture_window is None else float(flyover_capture_window),
        bank_limit_deg=float(mission_cmd.get("lnav_bank_limit_deg", 30.0)),
        sequence_gate_scale=float(mission_cmd.get("lnav_sequence_gate_scale", 0.35)),
        sequence_gate_min_m=None if seq_gate_min is None else float(seq_gate_min),
        sequence_gate_max_m=None if seq_gate_max is None else float(seq_gate_max),
    )


@dataclass(frozen=True)
class CompiledScenario:
    source_path: str
    scenario_name: str
    merged_scenario_data: dict[str, Any]
    runtime_metadata: CompiledScenarioRuntimeMetadata
    imported_files: tuple[str, ...]
    dependency_mtimes_ns: tuple[tuple[str, int], ...]
    warnings: tuple[str, ...]
    zone_count: int
    entity_count: int

    def instantiate(self) -> dict[str, Any]:
        return _clone_scenario_value(self.merged_scenario_data)

    def instantiate_runtime(self) -> dict[str, Any]:
        return _clone_runtime_scenario_data(self.merged_scenario_data)

    def instantiate_runtime_context(self) -> dict[str, Any]:
        return _clone_runtime_context_scenario_data(self.merged_scenario_data)

    def is_fresh(self) -> bool:
        for path, expected_mtime_ns in self.dependency_mtimes_ns:
            try:
                if _mtime_ns(path) != int(expected_mtime_ns):
                    return False
            except OSError:
                return False
        return True


class ScenarioCompiler:
    _path_cache: dict[str, CompiledScenario] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._path_cache.clear()

    @classmethod
    def compile_path(cls, source_path: str) -> CompiledScenario:
        abs_path = os.path.abspath(source_path)
        cached = cls._path_cache.get(abs_path)
        if cached is not None and cached.is_fresh():
            return cached

        compiled = cls._compile_from_path(abs_path)
        cls._path_cache[abs_path] = compiled
        return compiled

    @classmethod
    def compile_data(cls, scenario_data: dict[str, Any], *, source_path: str | None = None) -> CompiledScenario:
        if not isinstance(scenario_data, dict):
            raise TypeError("scenario_data must be a dict")
        return cls._compile_from_data(
            scenario_data,
            source_path=os.path.abspath(source_path) if source_path else "<inline>",
        )

    @classmethod
    def _compile_from_path(cls, abs_path: str) -> CompiledScenario:
        with open(abs_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError(f"Scenario file must contain a JSON object: {abs_path}")
        return cls._compile_from_data(raw, source_path=abs_path)

    @classmethod
    def _compile_from_data(cls, raw_scenario_data: dict[str, Any], *, source_path: str) -> CompiledScenario:
        merged, imported_files, warnings = _compile_merged_scenario_data(
            raw_scenario_data,
            project_root=REPO_ROOT,
        )
        for line in warnings:
            print(line)

        env_cfg = merged.get("environment", {})
        if not isinstance(env_cfg, dict):
            env_cfg = {}
        zones = env_cfg.get("zones", [])
        if not isinstance(zones, list):
            zones = []
        entities = merged.get("entities", [])
        if not isinstance(entities, list):
            entities = []
        rewards_cfg = merged.get("rewards", {})
        if not isinstance(rewards_cfg, dict):
            rewards_cfg = {}
        task_cfg = merged.get("task_order", {})
        if not isinstance(task_cfg, dict):
            task_cfg = {}
        mission_cmd_template = _normalize_runtime_mission_command(merged.get("mission_command", {}), task_cfg)
        normalized_route_waypoints = materialize_runtime_waypoint_cache(mission_cmd_template)
        normalized_waypoint_templates = _compile_normalized_waypoint_templates(mission_cmd_template)
        runtime_metadata = CompiledScenarioRuntimeMetadata(
            mission_command_template=mission_cmd_template,
            rewards_config=_clone_scenario_value(rewards_cfg),
            normalized_route_waypoints=tuple(_clone_scenario_value(normalized_route_waypoints)),
            normalized_waypoint_templates=normalized_waypoint_templates,
            waypoint_template_route_ref_ids=_compile_waypoint_template_route_ref_ids(normalized_waypoint_templates),
            compiled_conditional_objectives=_compile_conditional_objectives(merged.get("objectives", [])),
            objective_shaping_cfg=_build_objective_shaping_config(rewards_cfg),
            ils_beacon_templates=tuple(_clone_scenario_value(_extract_ils_beacons(env_cfg))),
            waypoint_mode_configs={
                "flyby": _build_waypoint_mode_reward_config(rewards_cfg, mode="flyby"),
                "flyover": _build_waypoint_mode_reward_config(rewards_cfg, mode="flyover"),
            },
            approach_reward_config=_build_approach_reward_config(rewards_cfg),
            safety_reward_config=_build_safety_reward_config(rewards_cfg),
            lnav_config=_build_lnav_runtime_config(mission_cmd_template),
            layout_template=_compile_world_layout_template(merged),
        )

        dependency_mtimes_ns: list[tuple[str, int]] = []
        if source_path != "<inline>":
            dependency_mtimes_ns.append((source_path, _mtime_ns(source_path)))
        for imported_path in imported_files:
            dependency_mtimes_ns.append((imported_path, _mtime_ns(imported_path)))

        scenario_name = str(merged.get("scenario_name", os.path.basename(source_path))).strip() or os.path.basename(source_path)
        return CompiledScenario(
            source_path=source_path,
            scenario_name=scenario_name,
            merged_scenario_data=merged,
            runtime_metadata=runtime_metadata,
            imported_files=imported_files,
            dependency_mtimes_ns=tuple(dependency_mtimes_ns),
            warnings=warnings,
            zone_count=len(zones),
            entity_count=len(entities),
        )
