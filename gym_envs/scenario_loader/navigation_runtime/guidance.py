import math

import ef_py
import numpy as np


def normalize_waypoint_mode(mode_value) -> str:
    mode = str(mode_value if mode_value is not None else "flyby").strip().lower()
    if mode in ("fly-over", "fly_over", "overfly"):
        return "flyover"
    if mode in ("flyby", "flyover"):
        return mode
    return "flyby"


def cfg_value_for_waypoint_mode(loader, cfg: dict, key: str, mode_value, default=None):
    mode = normalize_waypoint_mode(mode_value)
    mode_key = f"{key}_{mode}"
    if isinstance(cfg, dict) and mode_key in cfg:
        return cfg.get(mode_key)
    if isinstance(cfg, dict) and key in cfg:
        return cfg.get(key)
    return default


def active_waypoint_mode(loader, idx: int | None = None) -> str:
    if not loader.waypoints:
        return normalize_waypoint_mode(loader.mission_cmd.get("waypoint_mode", "flyby"))
    if idx is None:
        idx = int(getattr(loader, "waypoint_idx", 0))
    idx = int(np.clip(int(idx), 0, max(0, len(loader.waypoints) - 1)))
    wp = loader.waypoints[idx]
    return normalize_waypoint_mode(wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby")))


def formation_slot_offsets_m(loader) -> tuple[float, float, float]:
    return (
        float(loader.mission_cmd.get("form_offset_x", 0.0) or 0.0),
        float(loader.mission_cmd.get("form_offset_y", 0.0) or 0.0),
        float(loader.mission_cmd.get("form_offset_z", 0.0) or 0.0),
    )


def route_leg_frame(loader, waypoint_index: int) -> tuple[float, float, float, float] | None:
    if not loader.waypoints:
        return None
    idx = int(np.clip(int(waypoint_index), 0, max(0, len(loader.waypoints) - 1)))
    end_wp = loader.waypoints[idx]
    if idx > 0:
        start_wp = loader.waypoints[idx - 1]
        sx = float(start_wp.get("x", 0.0))
        sy = float(start_wp.get("y", 0.0))
    else:
        sx = float(getattr(loader, "_waypoint_leg_origin_x", 0.0))
        sy = float(getattr(loader, "_waypoint_leg_origin_y", 0.0))
    ex = float(end_wp.get("x", 0.0))
    ey = float(end_wp.get("y", 0.0))
    dx = ex - sx
    dy = ey - sy
    leg_len = math.hypot(dx, dy)
    if leg_len <= 1.0e-6:
        return None
    forward_x = dx / leg_len
    forward_y = dy / leg_len
    left_x = -forward_y
    left_y = forward_x
    return forward_x, forward_y, left_x, left_y


def route_reference_xy(loader, own_x_m: float, own_y_m: float, waypoint_index: int) -> tuple[float, float]:
    frame = route_leg_frame(loader, int(waypoint_index))
    if frame is None:
        return float(own_x_m), float(own_y_m)
    forward_x, forward_y, left_x, left_y = frame
    form_offset_x, form_offset_y, _form_offset_z = formation_slot_offsets_m(loader)
    ref_x = float(own_x_m) + forward_x * float(form_offset_x) - left_x * float(form_offset_y)
    ref_y = float(own_y_m) + forward_y * float(form_offset_x) - left_y * float(form_offset_y)
    return float(ref_x), float(ref_y)


def slot_target_altitude_for_waypoint(loader, waypoint: dict | None, *, fallback_m: float | None = None) -> float:
    default_alt = float(loader.mission_cmd.get("target_altitude", 0.0) if fallback_m is None else fallback_m)
    base_alt = default_alt
    if isinstance(waypoint, dict):
        base_alt = float(waypoint.get("altitude_m", waypoint.get("z", default_alt)))
    _form_offset_x, _form_offset_y, form_offset_z = formation_slot_offsets_m(loader)
    return float(base_alt + float(form_offset_z))


def query_route_guidance_result(loader, truth=None, inst=None):
    if loader._spatial_geometry is None or not loader.waypoints or loader.agent_id is None:
        return None
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    if cmd_code != 3:
        return None

    if truth is None:
        try:
            truth = loader.sim.get_agent_observation(loader.agent_id)
        except Exception:
            return None
    if inst is None:
        try:
            inst = loader.sim.get_instrument_state(loader.agent_id)
        except Exception:
            inst = None

    speed_mps = float(getattr(truth, "speed", 0.0))
    if inst is not None:
        try:
            ias = float(getattr(inst, "ias", speed_mps))
            if math.isfinite(ias) and ias > 1.0:
                speed_mps = ias
        except Exception:
            pass
    cache_key = (
        int(cmd_code),
        int(np.clip(int(getattr(loader, "waypoint_idx", 0)), 0, max(0, len(loader.waypoints) - 1))),
        float(getattr(truth, "x", 0.0)),
        float(getattr(truth, "y", 0.0)),
        float(speed_mps),
        float(loader.mission_cmd.get("form_offset_x", 0.0) or 0.0),
        float(loader.mission_cmd.get("form_offset_y", 0.0) or 0.0),
    )
    cache = getattr(loader, "_runtime_eval_cache", None)
    if isinstance(cache, dict) and cache.get("route_guidance_key") == cache_key:
        cached_result = cache.get("route_guidance_result")
        return cached_result if cached_result is not None else None

    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = int(cache_key[1])
    ref_x_m, ref_y_m = route_reference_xy(
        loader,
        float(getattr(truth, "x", 0.0)),
        float(getattr(truth, "y", 0.0)),
        int(cache_key[1]),
    )
    opts.own_x_m = float(ref_x_m)
    opts.own_y_m = float(ref_y_m)
    opts.own_speed_mps = float(speed_mps)
    lnav_cfg = loader._lnav_runtime_cfg
    opts.base_lookahead_m = float(lnav_cfg.lookahead_m)
    opts.lnav_max_intercept_deg = float(lnav_cfg.max_intercept_deg)
    opts.lnav_capture_max_intercept_deg = float(lnav_cfg.capture_max_intercept_deg)
    opts.lnav_capture_xtrack_m = float(lnav_cfg.capture_xtrack_m)
    opts.lnav_capture_course_error_deg = float(lnav_cfg.capture_course_error_deg)
    opts.lnav_direct_to_final_fix = bool(lnav_cfg.direct_to_final_fix)
    opts.lnav_flyover_capture_window_m = (
        0.0 if lnav_cfg.flyover_capture_window_m is None else float(lnav_cfg.flyover_capture_window_m)
    )
    opts.lnav_bank_limit_deg = float(lnav_cfg.bank_limit_deg)
    opts.lnav_sequence_gate_scale = float(lnav_cfg.sequence_gate_scale)
    opts.lnav_sequence_gate_min_m = (
        0.0 if lnav_cfg.sequence_gate_min_m is None else float(lnav_cfg.sequence_gate_min_m)
    )
    opts.lnav_sequence_gate_max_m = (
        0.0 if lnav_cfg.sequence_gate_max_m is None else float(lnav_cfg.sequence_gate_max_m)
    )

    result = loader._spatial_geometry.query_route_guidance(opts)
    out = result if bool(getattr(result, "valid", False)) else None
    if isinstance(cache, dict):
        cache["route_guidance_key"] = cache_key
        cache["route_guidance_result"] = out
    return out


def current_route_target_altitude_m(loader, *, truth=None, inst=None) -> float | None:
    result = query_route_guidance_result(loader, truth=truth, inst=inst)
    if result is None or not bool(getattr(result, "valid", False)):
        return None
    idx = int(getattr(result, "idx", -1))
    if idx < 0 or idx >= len(loader.waypoints):
        return None
    return float(slot_target_altitude_for_waypoint(loader, loader.waypoints[idx]))


def command_tracking_error_deg(loader, inst, truth_heading_deg: float) -> float:
    try:
        tgt = float(loader.mission_cmd.get("target_heading", 0.0))
    except Exception:
        tgt = 0.0
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    ground_track = loader._instrument_scalar(inst, "ground_track", 30)
    return float(
        ef_py.compute_command_tracking_error_deg(
            float(tgt),
            float(truth_heading_deg),
            int(cmd_code),
            float(ground_track),
        )
    )


def ground_track_from_inst(loader, inst, fallback_heading_deg: float) -> float:
    ground_track = loader._instrument_scalar(inst, "ground_track", 30)
    return float(ef_py.resolve_ground_track_deg(float(fallback_heading_deg), float(ground_track)))


def turn_lead_distance_m(loader, turn_angle_deg: float, speed_mps: float, bank_limit_deg: float) -> float:
    turn_abs_deg = abs(float(turn_angle_deg))
    if turn_abs_deg <= 1.0e-6:
        return 0.0
    bank_lim = float(np.clip(bank_limit_deg, 5.0, 70.0))
    tanb = math.tan(math.radians(bank_lim))
    if abs(tanb) <= 1.0e-6:
        return 0.0
    v = max(30.0, float(speed_mps))
    r_turn = (v * v) / (9.80665 * abs(tanb))
    turn_half_rad = 0.5 * min(math.pi - 1.0e-3, math.radians(turn_abs_deg))
    return max(0.0, float(r_turn * math.tan(turn_half_rad)))


def compute_waypoint_guidance_state(loader, truth=None, inst=None):
    cache = getattr(loader, "_runtime_eval_cache", None)
    route_key_ready = isinstance(cache, dict) and "route_guidance_key" in cache
    route_key = cache.get("route_guidance_key") if route_key_ready else None
    if route_key_ready and cache.get("waypoint_guidance_state_key") == route_key:
        cached_state = cache.get("waypoint_guidance_state")
        return cached_state if cached_state is not None else None

    result = query_route_guidance_result(loader, truth=truth, inst=inst)
    route_key_ready = isinstance(cache, dict) and "route_guidance_key" in cache
    route_key = cache.get("route_guidance_key") if route_key_ready else None
    if result is None:
        if route_key_ready:
            cache["waypoint_guidance_state_key"] = route_key
            cache["waypoint_guidance_state"] = None
        return None

    wp = loader.waypoints[int(result.idx)]
    state = {
        "idx": int(result.idx),
        "count": int(result.count),
        "wp": wp,
        "waypoint_mode": str(result.waypoint_mode),
        "sx": float(result.sx_m),
        "sy": float(result.sy_m),
        "lx": float(result.lx_m),
        "ly": float(result.ly_m),
        "dist_m": float(result.dist_m),
        "direct_to_track_deg": float(result.direct_to_track_deg),
        "desired_track_deg": float(result.desired_track_deg),
        "reward_desired_track_deg": float(result.reward_desired_track_deg),
        "xtk_m": float(result.xtk_m),
        "reward_xtk_m": float(result.reward_xtk_m),
        "along_m": float(result.along_m),
        "dtg_m": float(result.dtg_m),
        "reward_dtg_m": float(result.reward_dtg_m),
        "leg_len_m": float(result.leg_len_m),
        "ex": float(result.ex_m),
        "ey": float(result.ey_m),
        "waypoint_radius_m": float(result.waypoint_radius_m),
        "cmd_track_deg": float(result.cmd_track_deg),
        "use_direct_to": bool(result.use_direct_to),
        "direct_to_fix_guidance": bool(result.direct_to_fix_guidance),
        "next_turn_deg": float(result.next_turn_deg),
        "next_turn_abs_deg": float(result.next_turn_abs_deg),
        "prev_turn_abs_deg": float(result.prev_turn_abs_deg),
        "lead_turn_m": float(result.lead_turn_m),
        "sequence_gate_m": float(result.sequence_gate_m),
        "distance_to_turn_m": float(result.distance_to_turn_m),
        "dist_to_next_turn_start_m": float(result.dist_to_next_turn_start_m),
        "distance_from_prev_turn_m": float(result.distance_from_prev_turn_m),
        "final_leg": bool(result.final_leg),
        "passed_fix": bool(result.passed_fix),
    }
    if route_key_ready:
        cache["waypoint_guidance_state_key"] = route_key
        cache["waypoint_guidance_state"] = state
    return state


def active_waypoint_arrival_products(loader):
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    if cmd_code != 3 or not loader.waypoints or loader.agent_id is None:
        return None

    idx = int(np.clip(int(getattr(loader, "waypoint_idx", 0)), 0, max(0, len(loader.waypoints) - 1)))
    n = int(len(loader.waypoints))
    wp = loader.waypoints[idx]
    mode = normalize_waypoint_mode(wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby")))

    try:
        truth = loader.sim.get_agent_observation(loader.agent_id)
    except Exception:
        return None
    try:
        inst = loader.sim.get_instrument_state(loader.agent_id)
    except Exception:
        inst = None

    gstate = compute_waypoint_guidance_state(loader, truth=truth, inst=inst)
    dist_m = float(
        math.hypot(
            float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0)),
            float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0)),
        )
    )
    rad = max(1.0, float(wp.get("radius_m", loader.mission_cmd.get("waypoint_radius_m", 500.0))))
    if isinstance(gstate, dict) and int(gstate.get("idx", -1)) == idx:
        mode = str(gstate.get("waypoint_mode", mode))
        dist_m = float(gstate.get("dist_m", dist_m))
        rad = max(1.0, float(gstate.get("waypoint_radius_m", rad)))

    out = {
        "active_idx": int(idx),
        "count": int(n),
        "waypoint_mode": str(mode),
        "arrival_radius_m": float(rad),
        "sequence_gate_m": float(rad),
        "turn_lead_m": 0.0,
        "distance_to_waypoint_m": float(dist_m),
    }

    if mode != "flyby" or idx >= (n - 1):
        return out
    if gstate is None:
        return out

    out["sequence_gate_m"] = float(gstate.get("sequence_gate_m", rad))
    out["turn_lead_m"] = float(gstate.get("lead_turn_m", 0.0))
    out["cross_track_m"] = float(gstate.get("reward_xtk_m", 0.0))
    out["distance_to_turn_m"] = float(gstate.get("distance_to_turn_m", gstate.get("reward_dtg_m", dist_m)))
    return out


def get_waypoint_visualization_products(loader):
    if not loader.waypoints:
        return None
    active = active_waypoint_arrival_products(loader)
    active_idx = (
        int(active["active_idx"])
        if isinstance(active, dict) and "active_idx" in active
        else int(np.clip(int(getattr(loader, "waypoint_idx", 0)), 0, max(0, len(loader.waypoints) - 1)))
    )
    markers = []
    for i, wp in enumerate(loader.waypoints):
        mode = normalize_waypoint_mode(wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby")))
        entry = {
            "name": f"WP_{i+1}",
            "x": float(wp.get("x", 0.0)),
            "y": float(wp.get("y", 0.0)),
            "z": float(wp.get("z", loader.mission_cmd.get("target_altitude", 0.0))),
            "waypoint_mode": str(mode),
            "arrival_radius_m": float(wp.get("radius_m", loader.mission_cmd.get("waypoint_radius_m", 500.0))),
            "is_active": bool(i == active_idx),
        }
        if i == active_idx and isinstance(active, dict):
            entry["sequence_gate_m"] = float(active.get("sequence_gate_m", entry["arrival_radius_m"]))
            entry["turn_lead_m"] = float(active.get("turn_lead_m", 0.0))
            entry["distance_to_waypoint_m"] = float(active.get("distance_to_waypoint_m", 0.0))
        markers.append(entry)
    return {
        "markers": markers,
        "active_idx": int(active_idx),
        "active": active,
    }


def active_waypoint_turn_relief_activation(loader, cfg: dict, truth=None, inst=None) -> float:
    mode = active_waypoint_mode(loader)
    mode_cfg = loader._waypoint_mode_reward_cfgs.get(
        str(mode),
        loader._waypoint_mode_reward_cfgs.get("flyby", None),
    )
    if mode_cfg is None:
        max_relief = float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_max", mode, 0.0))
        heading_relief = float(
            cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_heading_relief_max", mode, max_relief)
        )
        base_window_m = max(
            1.0,
            float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_window_m", mode, 3000.0)),
        )
        min_turn_deg = max(
            0.0,
            float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_min_turn_deg", mode, 15.0)),
        )
        angle_ref_deg = max(
            min_turn_deg + 1.0,
            float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_angle_ref_deg", mode, 90.0)),
        )
        power = float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_power", mode, 1.0))
    else:
        max_relief = float(mode_cfg.turn_relief_max)
        heading_relief = float(mode_cfg.heading_relief_max)
        base_window_m = max(1.0, float(mode_cfg.turn_relief_window_m))
        min_turn_deg = max(0.0, float(mode_cfg.turn_relief_min_turn_deg))
        angle_ref_deg = max(min_turn_deg + 1.0, float(mode_cfg.turn_relief_angle_ref_deg))
        power = float(mode_cfg.turn_relief_power)
    if max(max_relief, heading_relief) <= 1.0e-6:
        return 0.0
    if not loader.waypoints or loader.agent_id is None:
        return 0.0
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    if cmd_code != 3:
        return 0.0

    idx = int(getattr(loader, "waypoint_idx", 0))
    n = int(len(loader.waypoints))
    if idx < 0 or idx >= n:
        return 0.0

    if truth is None:
        try:
            truth = loader.sim.get_agent_observation(loader.agent_id)
        except Exception:
            return 0.0
    if inst is None:
        try:
            inst = loader.sim.get_instrument_state(loader.agent_id)
        except Exception:
            inst = None

    gstate = compute_waypoint_guidance_state(loader, truth=truth, inst=inst)
    if gstate is None:
        return 0.0

    idx = int(gstate.get("idx", idx))
    n = int(gstate.get("count", n))
    power = float(np.clip(power, 1.0, 8.0))

    def _turn_strength(turn_abs_deg: float, distance_from_turn_m: float) -> float:
        if turn_abs_deg <= min_turn_deg:
            return 0.0
        angle_x = (turn_abs_deg - min_turn_deg) / max(1.0e-6, angle_ref_deg - min_turn_deg)
        angle_x = float(np.clip(angle_x, 0.0, 1.0))
        prox_x = 1.0 - float(distance_from_turn_m) / base_window_m
        prox_x = float(np.clip(prox_x, 0.0, 1.0))
        return float((angle_x**power) * prox_x)

    relief = 0.0
    if idx < n - 1:
        next_turn_abs = abs(float(gstate.get("next_turn_abs_deg", 0.0)))
        dist_to_turn_start_m = max(
            0.0,
            float(gstate.get("dist_to_next_turn_start_m", gstate.get("distance_to_turn_m", 0.0))),
        )
        relief = max(relief, _turn_strength(next_turn_abs, dist_to_turn_start_m))
    if idx > 0:
        prev_turn_abs = abs(float(gstate.get("prev_turn_abs_deg", 0.0)))
        distance_from_prev_turn_m = max(
            0.0,
            float(gstate.get("distance_from_prev_turn_m", gstate.get("along_m", 0.0))),
        )
        relief = max(relief, _turn_strength(prev_turn_abs, distance_from_prev_turn_m))
    return float(np.clip(relief, 0.0, 1.0))


def apply_waypoint_guidance_update(loader, *, truth=None, inst=None) -> None:
    if loader.agent_id is None:
        return
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    if loader.waypoints and cmd_code == 3:
        idx = int(getattr(loader, "waypoint_idx", 0))
        if idx < 0:
            idx = 0
        if idx < len(loader.waypoints):
            if truth is None:
                try:
                    truth = loader.sim.get_agent_observation(loader.agent_id)
                except Exception:
                    truth = None
            if inst is None:
                try:
                    inst = loader.sim.get_instrument_state(loader.agent_id)
                except Exception:
                    inst = None
            if truth is not None:
                gstate = compute_waypoint_guidance_state(loader, truth=truth, inst=inst)
                if gstate is not None:
                    wp = gstate["wp"]
                    loader.mission_cmd["target_heading"] = float(gstate["cmd_track_deg"])
                    try:
                        loader.mission_cmd["target_altitude"] = float(
                            slot_target_altitude_for_waypoint(loader, wp)
                        )
                    except Exception:
                        pass
                    try:
                        loader.mission_cmd["target_speed"] = float(
                            wp.get("speed_mps", loader.mission_cmd.get("target_speed", 0.0))
                        )
                    except Exception:
                        pass
