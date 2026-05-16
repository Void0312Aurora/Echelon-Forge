from python.scenario_compiler import (
    _build_lnav_runtime_config,
    _clone_runtime_mission_command,
    _clone_scenario_value,
    cache_runtime_waypoint_cache,
    materialize_runtime_waypoint_cache,
)
from python.rl.tasking.bridge import build_kernel_mission_command

from .common import safe_json_dict_loads, stable_json_dumps


def build_execution_episode_state(loader):
    if not hasattr(loader.sim, "__class__"):
        pass
    if not hasattr(__import__("ef_py"), "ExecutionEpisodeState"):
        raise RuntimeError("ef_py.ExecutionEpisodeState is not available")

    import ef_py

    state = ef_py.ExecutionEpisodeState()
    state.agent_id = int(loader.agent_id or 0)
    state.step_count = int(getattr(loader, "steps", 0))

    mission_cmd = getattr(loader, "mission_cmd", None)
    if isinstance(mission_cmd, dict):
        state.has_mission_command_json = True
        state.mission_command_json = stable_json_dumps(_clone_runtime_mission_command(mission_cmd))
        try:
            state.mission_command = build_kernel_mission_command(loader)
            state.has_mission_command = True
        except Exception:
            state.has_mission_command = False

    route_waypoints = []
    for wp in list(getattr(loader, "waypoints", []) or []):
        if not isinstance(wp, dict):
            continue
        route_wp = ef_py.SpatialRouteWaypoint()
        route_wp.x_m = float(wp.get("x", 0.0))
        route_wp.y_m = float(wp.get("y", 0.0))
        route_wp.z_m = float(wp.get("z", wp.get("altitude_m", 0.0)))
        route_wp.radius_m = float(wp.get("radius_m", 500.0))
        route_wp.altitude_m = float(wp.get("altitude_m", route_wp.z_m))
        route_wp.speed_mps = float(wp.get("speed_mps", 0.0))
        route_wp.waypoint_mode = str(wp.get("waypoint_mode", "flyby"))
        route_waypoints.append(route_wp)
    state.route_waypoints = route_waypoints
    state.waypoint_index = int(getattr(loader, "waypoint_idx", 0) or 0)
    state.waypoint_total_route_length_m = float(getattr(loader, "waypoint_total_route_length_m", 0.0))
    state.waypoint_leg_origin_x_m = float(getattr(loader, "_waypoint_leg_origin_x", 0.0))
    state.waypoint_leg_origin_y_m = float(getattr(loader, "_waypoint_leg_origin_y", 0.0))
    if getattr(loader, "_waypoint_prev_dist_m", None) is not None:
        state.has_waypoint_prev_dist_m = True
        state.waypoint_prev_dist_m = float(loader._waypoint_prev_dist_m)

    state.prev_altitude_m = float(getattr(loader, "prev_alt", 0.0))
    state.prev_ias_mps = float(getattr(loader, "prev_speed", 0.0))
    state.liftoff_awarded = bool(getattr(loader, "liftoff_awarded", False))
    state.gear_bonus_awarded = bool(getattr(loader, "gear_bonus_awarded", False))
    state.off_runway_steps = int(getattr(loader, "off_runway_steps", 0))

    if getattr(loader, "_approach_prev_dme_m", None) is not None:
        state.has_approach_prev_dme_m = True
        state.approach_prev_dme_m = float(loader._approach_prev_dme_m)
    if getattr(loader, "_approach_prev_loc_abs", None) is not None:
        state.has_approach_prev_loc_abs = True
        state.approach_prev_loc_abs = float(loader._approach_prev_loc_abs)
    if getattr(loader, "_approach_prev_gs_abs", None) is not None:
        state.has_approach_prev_gs_abs = True
        state.approach_prev_gs_abs = float(loader._approach_prev_gs_abs)

    post_waypoint_transition = getattr(loader, "post_waypoint_transition", None)
    if isinstance(post_waypoint_transition, dict) and post_waypoint_transition:
        state.has_post_waypoint_transition_json = True
        state.post_waypoint_transition_json = stable_json_dumps(
            _clone_runtime_mission_command(post_waypoint_transition)
        )
    state.mission_phase_name = str(getattr(loader, "mission_phase_name", "idle") or "idle")

    cached_route_ref_id = getattr(loader, "_cached_route_ref_id", None)
    if cached_route_ref_id is not None:
        state.has_cached_route_ref_id = True
        state.cached_route_ref_id = int(cached_route_ref_id)

    reward_breakdown = dict(getattr(loader, "last_reward_breakdown", {}) or {})
    state.last_termination_reason = str(getattr(loader, "last_termination_reason", "idle") or "idle")
    state.last_reward_total = float(reward_breakdown.get("total", 0.0))
    state.last_reward_breakdown_json = stable_json_dumps(reward_breakdown)
    return state


def _coerce_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off", ""}:
            return False
    return bool(default)


def apply_execution_episode_state(loader, state) -> None:
    import ef_py

    if not hasattr(ef_py, "ExecutionEpisodeState") or not isinstance(state, ef_py.ExecutionEpisodeState):
        raise TypeError("state must be an ef_py.ExecutionEpisodeState")

    loader.agent_id = int(state.agent_id) if int(state.agent_id) > 0 else None
    loader.steps = int(state.step_count)

    mission_cmd = None
    mission_cmd_from_json = False
    if bool(state.has_mission_command_json) and str(state.mission_command_json).strip():
        mission_cmd = safe_json_dict_loads(state.mission_command_json)
        mission_cmd_from_json = isinstance(mission_cmd, dict)
    if not isinstance(mission_cmd, dict):
        mission_cmd = {
            "command_code": int(state.mission_command.command_code),
            "target_heading": float(state.mission_command.cmd_heading_deg),
            "target_altitude": float(state.mission_command.cmd_altitude_m),
            "target_speed": float(state.mission_command.cmd_speed_mps),
            "recovery_approach_type": getattr(state.mission_command.recovery_approach_type, "name", "None"),
            "takeoff_procedure_code": int(getattr(state.mission_command, "takeoff_procedure_id", 0)),
            "takeoff_clearance_code": int(getattr(state.mission_command, "takeoff_clearance_id", 0)),
            "takeoff_interval_s": float(getattr(state.mission_command, "takeoff_interval_s", 0.0)),
            "runway_slot_code": int(getattr(state.mission_command, "runway_slot_id", 0)),
            "formation_id": int(getattr(state.mission_command, "formation_id", 0)),
            "form_offset_x": float(getattr(state.mission_command, "form_offset_x", 0.0)),
            "form_offset_y": float(getattr(state.mission_command, "form_offset_y", 0.0)),
            "form_offset_z": float(getattr(state.mission_command, "form_offset_z", 0.0)),
            "assigned_target_id": int(getattr(state.mission_command, "assigned_target_id", 0)),
            "authorization_to_fire": bool(getattr(state.mission_command, "authorization_to_fire", False)),
            "active": bool(getattr(state.mission_command, "active", False)),
        }
        if hasattr(state.mission_command, "route_ref_id"):
            mission_cmd["route_ref_id"] = int(state.mission_command.route_ref_id)
        if hasattr(state.mission_command, "recovery_base_id"):
            mission_cmd["recovery_base_id"] = int(state.mission_command.recovery_base_id)
        if hasattr(state.mission_command, "recovery_runway_id"):
            mission_cmd["recovery_runway_id"] = int(state.mission_command.recovery_runway_id)
    loader.waypoints = []
    for route_wp in list(state.route_waypoints):
        loader.waypoints.append(
            {
                "x": float(route_wp.x_m),
                "y": float(route_wp.y_m),
                "z": float(route_wp.z_m),
                "radius_m": float(route_wp.radius_m),
                "altitude_m": float(route_wp.altitude_m),
                "speed_mps": float(route_wp.speed_mps),
                "waypoint_mode": str(route_wp.waypoint_mode),
            }
        )
    if loader.waypoints and not list(mission_cmd.get("waypoints", []) or []):
        mission_cmd["waypoints"] = _clone_scenario_value(loader.waypoints)

    route_ref_id = int(state.cached_route_ref_id) if bool(state.has_cached_route_ref_id) else 0
    if route_ref_id > 0:
        mission_cmd["route_ref_id"] = int(route_ref_id)
        cache_runtime_waypoint_cache(mission_cmd, loader.waypoints, route_ref_id=route_ref_id)
    else:
        materialize_runtime_waypoint_cache(mission_cmd)

    if not mission_cmd_from_json:
        mission_cmd["active"] = _coerce_bool(
            mission_cmd.get("active", getattr(state.mission_command, "active", False)),
            bool(getattr(state.mission_command, "active", False)),
        )
    elif "active" in mission_cmd:
        mission_cmd["active"] = _coerce_bool(
            mission_cmd.get("active", getattr(state.mission_command, "active", False)),
            bool(getattr(state.mission_command, "active", False)),
        )

    loader.mission_cmd = mission_cmd
    if isinstance(loader.scenario_data, dict):
        loader.scenario_data["mission_command"] = loader.mission_cmd

    loader.waypoint_idx = int(state.waypoint_index)
    loader._waypoint_prev_dist_m = (
        float(state.waypoint_prev_dist_m) if bool(state.has_waypoint_prev_dist_m) else None
    )
    loader.waypoint_total_route_length_m = float(state.waypoint_total_route_length_m)
    loader._waypoint_leg_origin_x = float(state.waypoint_leg_origin_x_m)
    loader._waypoint_leg_origin_y = float(state.waypoint_leg_origin_y_m)

    loader.prev_alt = float(state.prev_altitude_m)
    loader.prev_speed = float(state.prev_ias_mps)
    loader.liftoff_awarded = bool(state.liftoff_awarded)
    loader.gear_bonus_awarded = bool(state.gear_bonus_awarded)
    loader.off_runway_steps = int(state.off_runway_steps)

    loader._approach_prev_dme_m = (
        float(state.approach_prev_dme_m) if bool(state.has_approach_prev_dme_m) else None
    )
    loader._approach_prev_loc_abs = (
        float(state.approach_prev_loc_abs) if bool(state.has_approach_prev_loc_abs) else None
    )
    loader._approach_prev_gs_abs = (
        float(state.approach_prev_gs_abs) if bool(state.has_approach_prev_gs_abs) else None
    )

    loader.post_waypoint_transition = None
    if bool(state.has_post_waypoint_transition_json) and str(state.post_waypoint_transition_json).strip():
        loader.post_waypoint_transition = safe_json_dict_loads(state.post_waypoint_transition_json)
    loader.mission_phase_name = str(state.mission_phase_name or "idle")
    loader._cached_route_ref_id = route_ref_id if route_ref_id > 0 else None

    reward_breakdown = safe_json_dict_loads(state.last_reward_breakdown_json)
    loader.last_reward_breakdown = dict(reward_breakdown or {})
    if "total" not in loader.last_reward_breakdown:
        loader.last_reward_breakdown["total"] = float(state.last_reward_total)
    loader.last_termination_reason = str(state.last_termination_reason or "idle")
    loader._lnav_runtime_cfg = _build_lnav_runtime_config(loader.mission_cmd)
    loader._cached_route_ref_id = int(loader.mission_cmd.get("route_ref_id", loader._cached_route_ref_id or 0)) or None
    loader._rebuild_spatial_geometry()


def apply_execution_episode_runtime_fields(loader, state, *, include_navigation_state: bool = True) -> None:
    import ef_py

    if not hasattr(ef_py, "ExecutionEpisodeState") or not isinstance(state, ef_py.ExecutionEpisodeState):
        raise TypeError("state must be an ef_py.ExecutionEpisodeState")

    loader.agent_id = int(state.agent_id) if int(state.agent_id) > 0 else None
    loader.steps = int(state.step_count)
    loader.prev_alt = float(state.prev_altitude_m)
    loader.prev_speed = float(state.prev_ias_mps)
    loader.liftoff_awarded = bool(state.liftoff_awarded)
    loader.gear_bonus_awarded = bool(state.gear_bonus_awarded)
    loader.off_runway_steps = int(state.off_runway_steps)
    reward_breakdown = safe_json_dict_loads(state.last_reward_breakdown_json)
    loader.last_reward_breakdown = dict(reward_breakdown or {})
    if "total" not in loader.last_reward_breakdown:
        loader.last_reward_breakdown["total"] = float(state.last_reward_total)
    loader.last_termination_reason = str(state.last_termination_reason or "idle")

    if not include_navigation_state:
        return

    loader.waypoint_idx = int(state.waypoint_index)
    loader._waypoint_prev_dist_m = (
        float(state.waypoint_prev_dist_m) if bool(state.has_waypoint_prev_dist_m) else None
    )
    loader.waypoint_total_route_length_m = float(state.waypoint_total_route_length_m)
    loader._waypoint_leg_origin_x = float(state.waypoint_leg_origin_x_m)
    loader._waypoint_leg_origin_y = float(state.waypoint_leg_origin_y_m)
    loader._approach_prev_dme_m = (
        float(state.approach_prev_dme_m) if bool(state.has_approach_prev_dme_m) else None
    )
    loader._approach_prev_loc_abs = (
        float(state.approach_prev_loc_abs) if bool(state.has_approach_prev_loc_abs) else None
    )
    loader._approach_prev_gs_abs = (
        float(state.approach_prev_gs_abs) if bool(state.has_approach_prev_gs_abs) else None
    )
