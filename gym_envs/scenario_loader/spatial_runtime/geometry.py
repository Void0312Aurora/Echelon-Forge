import math


def extract_ils_beacons(loader):
    beacons = []
    zones = loader.scenario_data.get("environment", {}).get("zones", [])
    if not isinstance(zones, list):
        return beacons

    for zone_index, zone in enumerate(zones):
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
                "name": name,
                "runway_id": int(zone.get("runway_id", ils_cfg.get("runway_id", zone_index))),
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


def nearest_ils_beacon(loader, x_m: float, y_m: float):
    if not loader.ils_beacons:
        return None
    requested_id = declared_runway_id(loader)
    candidates = (
        [beacon for beacon in loader.ils_beacons if int(beacon.get("runway_id", -1)) == int(requested_id)]
        if requested_id is not None
        else list(loader.ils_beacons)
    )
    if not candidates:
        return None
    best = None
    best_d2 = float("inf")
    for beacon in candidates:
        dx = x_m - float(beacon.get("cx", 0.0))
        dy = y_m - float(beacon.get("cy", 0.0))
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best = beacon
    return best


def declared_runway_id(loader):
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    mission = scenario_data.get("mission_command", {}) if isinstance(scenario_data, dict) else {}
    post = getattr(loader, "post_waypoint_transition", None)
    if not isinstance(post, dict) or not post:
        post = mission.get("post_waypoint_transition", {}) if isinstance(mission, dict) else {}
    task = getattr(loader, "task_order", None)
    for raw in (
        getattr(task, "recovery_runway_id", 0) if task is not None else 0,
        getattr(loader, "mission_cmd", {}).get("recovery_runway_id", 0)
        if isinstance(getattr(loader, "mission_cmd", None), dict)
        else 0,
        post.get("recovery_runway_id", 0) if isinstance(post, dict) else 0,
    ):
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    reference_name = str(post.get("reference_runway", "")).strip() if isinstance(post, dict) else ""
    if reference_name:
        for beacon in list(getattr(loader, "ils_beacons", []) or []):
            if str(beacon.get("name", "")).strip() == reference_name:
                try:
                    return int(beacon.get("runway_id", -1))
                except (TypeError, ValueError):
                    return None
    return None


def select_ils_beacon(loader, x_m: float, y_m: float, runway_id: int | None = None):
    requested_id = declared_runway_id(loader) if runway_id is None else int(runway_id)
    beacons = list(getattr(loader, "ils_beacons", []) or [])
    if requested_id is not None:
        matches = [beacon for beacon in beacons if int(beacon.get("runway_id", -1)) == int(requested_id)]
        if matches:
            return min(
                matches,
                key=lambda beacon: (float(x_m) - float(beacon.get("cx", 0.0))) ** 2
                + (float(y_m) - float(beacon.get("cy", 0.0))) ** 2,
            )
        return None
    return nearest_ils_beacon(loader, x_m, y_m)


def rebuild_spatial_geometry(loader) -> None:
    import ef_py

    if not hasattr(ef_py, "CompiledScenarioGeometry"):
        loader._spatial_geometry = None
        return

    geom = ef_py.CompiledScenarioGeometry()

    for idx, beacon in enumerate(loader.ils_beacons or []):
        runway = ef_py.SpatialRunwayDefinition()
        runway.runway_id = int(beacon.get("runway_id", idx))
        runway.name = str(beacon.get("name", f"Runway_{idx}"))
        runway.center_x_m = float(beacon.get("cx", 0.0))
        runway.center_y_m = float(beacon.get("cy", 0.0))
        runway.threshold_x_m = float(beacon.get("thr_x", 0.0))
        runway.threshold_y_m = float(beacon.get("thr_y", 0.0))
        runway.heading_deg = float(beacon.get("heading", 0.0))
        runway.length_m = float(beacon.get("length", 0.0))
        runway.width_m = float(beacon.get("width", 0.0))
        runway.elevation_m = float(beacon.get("elev_m", 0.0))
        runway.glide_slope_deg = float(beacon.get("glide_slope_deg", 3.0))
        runway.localizer_max_deg = float(beacon.get("loc_max_deg", 10.0))
        runway.glideslope_max_deg = float(beacon.get("gs_max_deg", 3.0))
        runway.range_m = float(beacon.get("range_m", 30000.0))
        geom.add_runway(runway)

    geom.set_route_leg_origin(
        float(getattr(loader, "_waypoint_leg_origin_x", 0.0)),
        float(getattr(loader, "_waypoint_leg_origin_y", 0.0)),
    )
    for wp in loader.waypoints:
        waypoint = ef_py.SpatialRouteWaypoint()
        waypoint.x_m = float(wp.get("x", 0.0))
        waypoint.y_m = float(wp.get("y", 0.0))
        waypoint.z_m = float(wp.get("z", 0.0))
        waypoint.radius_m = float(wp.get("radius_m", loader.mission_cmd.get("waypoint_radius_m", 500.0)))
        waypoint.altitude_m = float(wp.get("altitude_m", waypoint.z_m))
        waypoint.speed_mps = float(wp.get("speed_mps", loader.mission_cmd.get("target_speed", 0.0)))
        waypoint.waypoint_mode = str(
            loader._normalize_waypoint_mode(
                wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby"))
            )
        )
        geom.add_route_waypoint(waypoint)

    loader._spatial_geometry = geom


def query_runway_frame_result(loader, x_m: float, y_m: float):
    if loader._spatial_geometry is None:
        return None
    runway_id = declared_runway_id(loader)
    cache_key = (float(x_m), float(y_m), None if runway_id is None else int(runway_id))
    cache = getattr(loader, "_runtime_eval_cache", None)
    if isinstance(cache, dict) and cache.get("runway_frame_key") == cache_key:
        cached_result = cache.get("runway_frame_result")
        return cached_result if cached_result is not None else None
    frame = loader._spatial_geometry.query_runway_local_frame(
        float(x_m), float(y_m), -1 if runway_id is None else int(runway_id)
    )
    out = frame if bool(getattr(frame, "valid", False)) else None
    if isinstance(cache, dict):
        cache["runway_frame_key"] = cache_key
        cache["runway_frame_result"] = out
    return out
