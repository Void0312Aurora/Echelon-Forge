import math

from python.scenario_compiler import _clone_scenario_value, materialize_runtime_waypoint_cache

from ..common import coerce_nonnegative_int


def parse_waypoints(loader) -> None:
    """
    Parse mission waypoints from scenario_data into a normalized internal list.

    Supported waypoint formats:
      - {"x":..., "y":..., "z":...}
      - {"pos":[x,y,z]}
      - [x, y, z]
    Optional per-waypoint overrides:
      - radius_m / arrival_radius_m
      - altitude_m / altitude / target_altitude / z
      - speed_mps / speed / target_speed
    """
    loader.waypoints = []
    loader.waypoint_idx = 0
    loader._waypoint_prev_dist_m = None
    loader.waypoint_total_route_length_m = 0.0
    loader._cached_route_ref_id = None

    mc = loader.scenario_data.get("mission_command", None)
    if not isinstance(mc, dict):
        return

    cached_waypoints = mc.get("_normalized_waypoints", None)
    if isinstance(cached_waypoints, list):
        _apply_cached_waypoints(loader, mc, cached_waypoints)
        return

    wps = mc.get("waypoints", None)
    if not isinstance(wps, list) or not wps:
        return

    def _f(x, default: float | None = None) -> float | None:
        if x is None:
            return default
        try:
            return float(x)
        except Exception:
            return default

    default_alt = _f(mc.get("target_altitude", 0.0), 0.0) or 0.0
    default_spd = _f(mc.get("target_speed", 0.0), 0.0) or 0.0
    default_rad = _f(mc.get("waypoint_radius_m", mc.get("arrival_radius_m", 500.0)), 500.0) or 500.0
    default_mode = loader._normalize_waypoint_mode(mc.get("waypoint_mode", "flyby"))

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
            alt = _f(
                wp.get("altitude_m", wp.get("altitude", wp.get("target_altitude", None))),
                z if z is not None else default_alt,
            )
            spd = _f(wp.get("speed_mps", wp.get("speed", wp.get("target_speed", None))), default_spd)
            mode = loader._normalize_waypoint_mode(
                wp.get("waypoint_mode", wp.get("mode", wp.get("pass_mode", default_mode)))
            )
        elif isinstance(wp, list) and len(wp) >= 2:
            x = _f(wp[0], 0.0)
            y = _f(wp[1], 0.0)
            z = _f(wp[2], default_alt) if len(wp) >= 3 else default_alt
            rad = default_rad
            alt = z
            spd = default_spd

        if x is None or y is None:
            continue

        loader.waypoints.append(
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

    materialize_runtime_waypoint_cache(mc)
    cached_waypoints = mc.get("_normalized_waypoints", None)
    if isinstance(cached_waypoints, list):
        _apply_cached_waypoints(loader, mc, cached_waypoints)


def _apply_cached_waypoints(loader, mission_cmd: dict, cached_waypoints: list) -> None:
    loader.waypoints = _clone_scenario_value(cached_waypoints)
    route_ref_id = coerce_nonnegative_int(mission_cmd.get("route_ref_id", 0), 0)
    loader._cached_route_ref_id = int(route_ref_id) if route_ref_id > 0 else None
    if loader.waypoints:
        px = float(getattr(loader, "_waypoint_leg_origin_x", 0.0))
        py = float(getattr(loader, "_waypoint_leg_origin_y", 0.0))
        total = 0.0
        for wp in loader.waypoints:
            wx = float(wp.get("x", 0.0))
            wy = float(wp.get("y", 0.0))
            total += float(math.hypot(wx - px, wy - py))
            px = wx
            py = wy
        loader.waypoint_total_route_length_m = float(total)
