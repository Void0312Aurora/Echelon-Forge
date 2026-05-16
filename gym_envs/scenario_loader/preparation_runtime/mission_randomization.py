from python.scenario_compiler import (
    _clone_scenario_value,
    cache_runtime_waypoint_cache,
    invalidate_runtime_waypoint_cache,
)


def randomize_mission(loader):
    """Randomize mission parameters if ranges are specified in config."""
    base_cmd = loader.scenario_data.get("mission_command", {})
    rand_cfg = base_cmd.get("randomization", {})
    compiled_waypoint_templates = ()
    compiled_waypoint_template_route_ref_ids = ()
    if loader._compiled_runtime_metadata is not None:
        compiled_waypoint_templates = tuple(
            getattr(loader._compiled_runtime_metadata, "normalized_waypoint_templates", ())
        )
        compiled_waypoint_template_route_ref_ids = tuple(
            getattr(loader._compiled_runtime_metadata, "waypoint_template_route_ref_ids", ())
        )

    if "heading_range" in rand_cfg:
        r = rand_cfg["heading_range"]
        loader.mission_cmd["target_heading"] = loader.rng.uniform(r[0], r[1])

    if "altitude_range" in rand_cfg:
        r = rand_cfg["altitude_range"]
        loader.mission_cmd["target_altitude"] = loader.rng.uniform(r[0], r[1])

    if "speed_range" in rand_cfg:
        r = rand_cfg["speed_range"]
        loader.mission_cmd["target_speed"] = loader.rng.uniform(r[0], r[1])

    route_generated = False
    route_gen = rand_cfg.get("route_generator", None)
    if isinstance(route_gen, dict) and bool(route_gen.get("enabled", True)):
        generated = loader._generate_route_waypoints(route_gen)
        if generated:
            loader.mission_cmd["waypoints"] = generated
            loader.mission_cmd["_waypoint_template_idx"] = -1
            loader.mission_cmd["_route_generator_used"] = True
            invalidate_runtime_waypoint_cache(loader.mission_cmd)
            route_generated = True

    wp_templates = rand_cfg.get("waypoint_templates", None)
    if route_generated or not isinstance(wp_templates, list) or not wp_templates:
        return
    try:
        idx = int(loader.rng.randint(0, len(wp_templates)))
    except Exception:
        idx = 0
    chosen = wp_templates[idx]
    if not isinstance(chosen, list) or not chosen:
        return
    precompiled = compiled_waypoint_templates[idx] if idx < len(compiled_waypoint_templates) else ()
    if precompiled:
        waypoints = _clone_scenario_value(list(precompiled))
        loader._rotate_waypoints_inplace(waypoints)
        loader.mission_cmd["waypoints"] = _clone_scenario_value(waypoints)
        route_ref_id = (
            int(compiled_waypoint_template_route_ref_ids[idx])
            if idx < len(compiled_waypoint_template_route_ref_ids)
            else 0
        )
        cache_runtime_waypoint_cache(loader.mission_cmd, waypoints, route_ref_id=route_ref_id)
    else:
        waypoints = _clone_scenario_value(chosen)
        loader._rotate_waypoints_inplace(waypoints)
        loader.mission_cmd["waypoints"] = waypoints
        invalidate_runtime_waypoint_cache(loader.mission_cmd)
    loader.mission_cmd["_waypoint_template_idx"] = int(idx)
    loader.mission_cmd["_route_generator_used"] = False
