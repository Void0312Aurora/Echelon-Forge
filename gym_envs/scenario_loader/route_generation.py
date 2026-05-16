import math

import numpy as np


def sample_uniform(loader, value, default: float) -> float:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(loader.rng.uniform(float(value[0]), float(value[1])))
        except Exception:
            return float(default)
    try:
        return float(value)
    except Exception:
        return float(default)


def sample_int(loader, value, default: int) -> int:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            lo = int(math.floor(float(value[0])))
            hi = int(math.floor(float(value[1])))
            if hi < lo:
                lo, hi = hi, lo
            return int(loader.rng.randint(lo, hi + 1))
        except Exception:
            return int(default)
    try:
        return int(value)
    except Exception:
        return int(default)


def sample_entity_spawn(loader, ent_cfg: dict) -> tuple[list[float], list[float], float, float, float]:
    pos = list(ent_cfg.get("pos", [0.0, 0.0, 0.0]))
    vel = list(ent_cfg.get("vel", [0.0, 0.0, 0.0]))
    heading = float(ent_cfg.get("heading", 0.0))
    pitch = float(ent_cfg.get("pitch", 0.0))
    roll = float(ent_cfg.get("roll", 0.0))

    rand_cfg = ent_cfg.get("randomization", None)
    if not isinstance(rand_cfg, dict):
        return pos, vel, heading, pitch, roll

    heading += sample_uniform(loader, rand_cfg.get("heading_offset_deg_range", [0.0, 0.0]), 0.0)
    pitch += sample_uniform(loader, rand_cfg.get("pitch_offset_deg_range", [0.0, 0.0]), 0.0)
    roll += sample_uniform(loader, rand_cfg.get("roll_offset_deg_range", [0.0, 0.0]), 0.0)

    h_rad = math.radians(float(heading))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)

    along_off = sample_uniform(loader, rand_cfg.get("along_body_m_range", [0.0, 0.0]), 0.0)
    cross_off = sample_uniform(loader, rand_cfg.get("cross_body_m_range", [0.0, 0.0]), 0.0)
    alt_off = sample_uniform(loader, rand_cfg.get("altitude_offset_m_range", [0.0, 0.0]), 0.0)

    try:
        pos[0] = float(pos[0]) + along_off * fwd_x + cross_off * right_x
        pos[1] = float(pos[1]) + along_off * fwd_y + cross_off * right_y
        pos[2] = float(pos[2]) + alt_off
    except Exception:
        pass

    try:
        base_horiz_speed = math.sqrt(float(vel[0]) * float(vel[0]) + float(vel[1]) * float(vel[1]))
    except Exception:
        base_horiz_speed = 0.0
    speed_scale = sample_uniform(loader, rand_cfg.get("speed_scale_range", [1.0, 1.0]), 1.0)
    speed_off = sample_uniform(loader, rand_cfg.get("speed_offset_mps_range", [0.0, 0.0]), 0.0)
    horiz_speed = max(0.0, float(base_horiz_speed) * float(speed_scale) + float(speed_off))
    sink_rate = sample_uniform(
        loader,
        rand_cfg.get(
            "sink_rate_mps_range",
            [float(vel[2]) if len(vel) > 2 else 0.0, float(vel[2]) if len(vel) > 2 else 0.0],
        ),
        float(vel[2]) if len(vel) > 2 else 0.0,
    )

    if len(vel) < 3:
        vel = [0.0, 0.0, 0.0]
    vel[0] = float(horiz_speed * fwd_x)
    vel[1] = float(horiz_speed * fwd_y)
    vel[2] = float(sink_rate)
    return pos, vel, float(heading), float(pitch), float(roll)


def rotate_waypoints_inplace(loader, waypoints: list[dict]) -> None:
    if abs(float(loader.world_yaw_deg)) <= 1.0e-6:
        return
    for wp in waypoints:
        if not isinstance(wp, dict):
            if isinstance(wp, list) and len(wp) >= 2:
                px, py = loader._rotate_xy_clockwise(
                    wp[0],
                    wp[1],
                    loader.world_yaw_origin_x,
                    loader.world_yaw_origin_y,
                    loader.world_yaw_deg,
                )
                wp[0] = px
                wp[1] = py
            continue
        if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
            px, py = loader._rotate_xy_clockwise(
                wp["pos"][0],
                wp["pos"][1],
                loader.world_yaw_origin_x,
                loader.world_yaw_origin_y,
                loader.world_yaw_deg,
            )
            wp["pos"][0] = px
            wp["pos"][1] = py
        elif "x" in wp and "y" in wp:
            px, py = loader._rotate_xy_clockwise(
                wp.get("x", 0.0),
                wp.get("y", 0.0),
                loader.world_yaw_origin_x,
                loader.world_yaw_origin_y,
                loader.world_yaw_deg,
            )
            wp["x"] = px
            wp["y"] = py


def turn_radius_m(loader, speed_mps: float, bank_limit_deg: float) -> float:
    _ = loader
    bank_rad = math.radians(float(np.clip(bank_limit_deg, 1.0, 80.0)))
    tanb = math.tan(bank_rad)
    if abs(tanb) <= 1.0e-6:
        return float("inf")
    v = max(30.0, float(speed_mps))
    return (v * v) / (9.80665 * abs(tanb))


def route_turn_cost_m(loader, turn_abs_deg: float, *, speed_mps: float, bank_limit_deg: float, cost_scale: float) -> float:
    turn_abs_deg = abs(float(turn_abs_deg))
    if turn_abs_deg <= 1.0e-6 or float(cost_scale) <= 1.0e-6:
        return 0.0
    turn_radius = turn_radius_m(loader, float(speed_mps), float(bank_limit_deg))
    if not math.isfinite(turn_radius) or turn_radius <= 0.0:
        return 0.0
    turn_arc_m = turn_radius * math.radians(turn_abs_deg)
    return max(0.0, float(turn_arc_m) * float(cost_scale))


def generate_route_waypoints(loader, cfg: dict) -> list[dict]:
    def _range_lo(value, default: float) -> float:
        if isinstance(value, (list, tuple)) and len(value) >= 1:
            try:
                if len(value) >= 2:
                    return float(min(value[0], value[1]))
                return float(value[0])
            except Exception:
                return float(default)
        try:
            return float(value)
        except Exception:
            return float(default)

    spawn = None
    runtime_spawn = loader.scenario_data.get("_runtime_agent_spawn", None)
    if isinstance(runtime_spawn, dict):
        spawn = runtime_spawn
    else:
        entities = loader.scenario_data.get("entities", [])
        for ent in entities:
            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                spawn = ent
                break
        if spawn is None and isinstance(entities, list) and entities:
            spawn = entities[0] if isinstance(entities[0], dict) else None

    spawn_pos = spawn.get("pos", [0.0, 0.0, 0.0]) if isinstance(spawn, dict) else [0.0, 0.0, 0.0]
    try:
        x = float(spawn_pos[0])
        y = float(spawn_pos[1])
        spawn_alt = float(spawn_pos[2])
    except Exception:
        x = 0.0
        y = 0.0
        spawn_alt = float(loader.mission_cmd.get("target_altitude", 1200.0))

    try:
        base_heading = float(
            loader.mission_cmd.get("target_heading", spawn.get("heading", 90.0) if isinstance(spawn, dict) else 90.0)
        )
    except Exception:
        base_heading = 90.0
    if loader.rotate_mission_heading_with_world and abs(float(loader.world_yaw_deg)) > 1.0e-6:
        base_heading = (float(base_heading) + float(loader.world_yaw_deg)) % 360.0
    initial_abs = cfg.get("initial_course_deg_range", None)
    if initial_abs is not None:
        course_deg = sample_uniform(loader, initial_abs, base_heading) % 360.0
    else:
        delta = sample_uniform(loader, cfg.get("first_leg_heading_delta_deg_range", [0.0, 0.0]), 0.0)
        course_deg = (base_heading + float(delta)) % 360.0

    count = max(2, sample_int(loader, cfg.get("waypoint_count_range", [3, 5]), 4))
    leg_default = float(cfg.get("leg_length_m", 16000.0))
    leg_range = cfg.get("leg_length_m_range", [leg_default, leg_default])
    first_leg_range = cfg.get("first_leg_length_m_range", leg_range)
    subsequent_leg_range = cfg.get("subsequent_leg_length_m_range", leg_range)
    config_min_leg_m = float(
        cfg.get(
            "min_leg_length_m",
            min(
                float(first_leg_range[0] if isinstance(first_leg_range, (list, tuple)) and len(first_leg_range) >= 1 else leg_default),
                float(subsequent_leg_range[0] if isinstance(subsequent_leg_range, (list, tuple)) and len(subsequent_leg_range) >= 1 else leg_default),
            ),
        )
    )
    min_leg_m = max(2000.0, config_min_leg_m)
    first_leg_min_m = max(min_leg_m, _range_lo(first_leg_range, leg_default))
    subsequent_leg_min_m = max(min_leg_m, _range_lo(subsequent_leg_range, leg_default))
    radius_range = cfg.get("waypoint_radius_m_range", [900.0, 1400.0])
    speed_range = cfg.get(
        "speed_mps_range",
        [float(loader.mission_cmd.get("target_speed", 210.0)), float(loader.mission_cmd.get("target_speed", 210.0))],
    )
    altitude_range = cfg.get(
        "altitude_m_range",
        [float(loader.mission_cmd.get("target_altitude", spawn_alt)), float(loader.mission_cmd.get("target_altitude", spawn_alt))],
    )
    altitude_step_range = cfg.get("altitude_step_m_range", [0.0, 0.0])
    turn_range = cfg.get("turn_angle_deg_range", [-60.0, 60.0])
    min_turn_abs = max(0.0, float(cfg.get("min_turn_abs_deg", 10.0)))
    max_turn_abs = abs(float(cfg.get("max_turn_abs_deg", 120.0)))
    turn_feasibility_enabled = bool(cfg.get("turn_feasibility_enabled", False))
    turn_leg_usage_fraction_limit = float(np.clip(float(cfg.get("turn_leg_usage_fraction_limit", 0.30)), 0.05, 0.49))
    turn_clearance_m = max(
        0.0,
        float(cfg.get("turn_clearance_m", max(800.0, float(loader.mission_cmd.get("waypoint_radius_m", 1000.0))))),
    )
    turn_budget_cost_scale = float(cfg.get("turn_budget_cost_scale", 0.0))
    if turn_budget_cost_scale <= 0.0:
        turn_budget_cost_scale = 0.75 if turn_feasibility_enabled else 0.0
    turn_budget_cost_scale = float(np.clip(turn_budget_cost_scale, 0.0, 2.0))
    env_cfg = loader.scenario_data.get("environment", {}) if isinstance(loader.scenario_data.get("environment", {}), dict) else {}
    time_step_s = float(env_cfg.get("time_step", 0.05))
    max_steps = int(env_cfg.get("max_steps", loader.get_max_steps()))
    route_budget_fraction = float(np.clip(float(cfg.get("route_budget_fraction", 0.80)), 0.25, 1.00))
    route_budget_margin_fraction = float(np.clip(float(cfg.get("route_budget_margin_fraction", 0.0)), 0.0, 0.50))
    target_speed_mps = max(80.0, float(loader.mission_cmd.get("target_speed", 210.0)))
    turn_speed_ref_mps = max(
        80.0,
        float(cfg.get("turn_feasibility_speed_mps", max(target_speed_mps, _range_lo(speed_range, target_speed_mps)))),
    )
    bank_limit_deg = float(loader.mission_cmd.get("lnav_bank_limit_deg", 30.0))
    route_budget_m = target_speed_mps * time_step_s * float(max_steps) * route_budget_fraction
    if route_budget_margin_fraction > 0.0:
        route_budget_m *= 1.0 - route_budget_margin_fraction
    route_budget_m = max(first_leg_min_m + subsequent_leg_min_m, float(route_budget_m))

    min_turn_cost_per_turn_m = 0.0
    if turn_budget_cost_scale > 0.0:
        min_turn_cost_per_turn_m = route_turn_cost_m(
            loader,
            min_turn_abs,
            speed_mps=turn_speed_ref_mps,
            bank_limit_deg=bank_limit_deg,
            cost_scale=turn_budget_cost_scale,
        )

    def _min_route_distance_for_count(route_count: int) -> float:
        route_count = max(2, int(route_count))
        return first_leg_min_m + subsequent_leg_min_m * float(max(0, route_count - 1))

    def _min_budget_for_count(route_count: int) -> float:
        route_count = max(2, int(route_count))
        return _min_route_distance_for_count(route_count) + min_turn_cost_per_turn_m * float(max(0, route_count - 1))

    max_count = max(2, int(route_budget_m // max(min_leg_m, 1.0)))
    while max_count > 2 and _min_budget_for_count(max_count) > route_budget_m + 1.0e-6:
        max_count -= 1
    count = min(count, max_count)
    while count > 2 and _min_budget_for_count(count) > route_budget_m + 1.0e-6:
        count -= 1

    max_route_distance_m = max(
        _min_route_distance_for_count(count),
        route_budget_m - min_turn_cost_per_turn_m * float(max(0, count - 1)),
    )

    try:
        alt_lo = float(min(altitude_range[0], altitude_range[1]))
        alt_hi = float(max(altitude_range[0], altitude_range[1]))
    except Exception:
        alt_lo = alt_hi = float(loader.mission_cmd.get("target_altitude", spawn_alt))
    altitude = float(
        np.clip(
            sample_uniform(loader, altitude_range, float(loader.mission_cmd.get("target_altitude", spawn_alt))),
            alt_lo,
            alt_hi,
        )
    )
    default_mode = loader._normalize_waypoint_mode(loader.mission_cmd.get("waypoint_mode", "flyby"))
    waypoint_mode_cycle = cfg.get("waypoint_mode_cycle", None)
    if not isinstance(waypoint_mode_cycle, (list, tuple)):
        waypoint_mode_cycle = []
    waypoint_mode_cycle = [loader._normalize_waypoint_mode(x) for x in waypoint_mode_cycle if str(x).strip()]
    final_waypoint_mode = loader._normalize_waypoint_mode(cfg.get("final_waypoint_mode", "flyover"))

    min_turn_cost_m = (
        route_turn_cost_m(
            loader,
            min_turn_abs,
            speed_mps=turn_speed_ref_mps,
            bank_limit_deg=bank_limit_deg,
            cost_scale=turn_budget_cost_scale,
        )
        if turn_budget_cost_scale > 0.0
        else 0.0
    )
    waypoints: list[dict] = []
    remaining_route_budget_m = float(max_route_distance_m)
    for idx in range(count):
        legs_left = max(1, count - idx)
        current_leg_min_m = first_leg_min_m if idx == 0 else subsequent_leg_min_m
        leg_sample_cfg = first_leg_range if idx == 0 else subsequent_leg_range
        leg_sample_m = max(current_leg_min_m, float(sample_uniform(loader, leg_sample_cfg, leg_default)))
        future_turns_after_this = max(0, legs_left - 1)
        min_remaining_after_this_m = 0.0
        if future_turns_after_this > 0:
            min_remaining_after_this_m += subsequent_leg_min_m * float(future_turns_after_this)
        if turn_budget_cost_scale > 0.0 and future_turns_after_this > 0:
            min_remaining_after_this_m += min_turn_cost_m * float(future_turns_after_this)
        leg_cap_m = max(current_leg_min_m, remaining_route_budget_m - min_remaining_after_this_m)
        leg_m = min(leg_sample_m, leg_cap_m)
        remaining_route_budget_m = max(0.0, remaining_route_budget_m - leg_m)
        h_rad = math.radians(course_deg)
        x += leg_m * math.sin(h_rad)
        y += leg_m * math.cos(h_rad)
        if idx > 0:
            altitude += float(sample_uniform(loader, altitude_step_range, 0.0))
            altitude = float(np.clip(altitude, alt_lo, alt_hi))
        radius_m = max(300.0, float(sample_uniform(loader, radius_range, 1000.0)))
        speed_mps = max(80.0, float(sample_uniform(loader, speed_range, float(loader.mission_cmd.get("target_speed", 210.0)))))
        if idx >= count - 1:
            waypoint_mode = final_waypoint_mode
        elif waypoint_mode_cycle:
            waypoint_mode = waypoint_mode_cycle[idx % len(waypoint_mode_cycle)]
        else:
            waypoint_mode = default_mode
        waypoints.append(
            {
                "x": float(x),
                "y": float(y),
                "z": float(altitude),
                "altitude_m": float(altitude),
                "speed_mps": float(speed_mps),
                "radius_m": float(radius_m),
                "waypoint_mode": str(waypoint_mode),
            }
        )
        if idx >= count - 1:
            continue

        lower_bound_m = max(subsequent_leg_min_m, _range_lo(subsequent_leg_range, leg_default))
        legs_remaining_after_next = max(0, count - idx - 2)

        def _next_leg_floor_after_turn(turn_abs_deg: float) -> float:
            remaining_after_turn_m = float(remaining_route_budget_m)
            if turn_budget_cost_scale > 0.0:
                remaining_after_turn_m = max(
                    0.0,
                    remaining_after_turn_m
                    - route_turn_cost_m(
                        loader,
                        turn_abs_deg,
                        speed_mps=turn_speed_ref_mps,
                        bank_limit_deg=bank_limit_deg,
                        cost_scale=turn_budget_cost_scale,
                    ),
                )
            min_remaining_after_next_m = subsequent_leg_min_m * float(legs_remaining_after_next)
            if turn_budget_cost_scale > 0.0 and legs_remaining_after_next > 0:
                min_remaining_after_next_m += min_turn_cost_m * float(legs_remaining_after_next)
            next_leg_cap_m = max(subsequent_leg_min_m, remaining_after_turn_m - min_remaining_after_next_m)
            return max(subsequent_leg_min_m, min(lower_bound_m, next_leg_cap_m))

        turn_deg = float(sample_uniform(loader, turn_range, 0.0))
        turn_range_abs_max = max(abs(float(turn_range[0])), abs(float(turn_range[1])))
        if abs(turn_deg) < min_turn_abs and turn_range_abs_max >= min_turn_abs:
            sign = 1.0 if turn_deg >= 0.0 else -1.0
            if abs(turn_deg) < 1.0e-6:
                sign = 1.0 if float(loader.rng.rand()) >= 0.5 else -1.0
            turn_deg = sign * min_turn_abs
        feasible_turn_abs_deg = float(max_turn_abs)
        if turn_feasibility_enabled:
            turn_radius = turn_radius_m(loader, turn_speed_ref_mps, bank_limit_deg)

            def _turn_is_feasible(turn_abs_deg: float) -> bool:
                next_leg_floor_turn_m = _next_leg_floor_after_turn(turn_abs_deg)
                lead_budget_m = (
                    min(float(leg_m), float(next_leg_floor_turn_m)) * turn_leg_usage_fraction_limit
                    - max(turn_clearance_m, radius_m)
                )
                if lead_budget_m <= 0.0:
                    return False
                required_lead_m = turn_radius * math.tan(0.5 * math.radians(float(turn_abs_deg)))
                return bool(required_lead_m <= lead_budget_m + 1.0e-6)

            if not math.isfinite(turn_radius) or turn_radius <= 0.0:
                feasible_turn_abs_deg = 0.0
            elif _turn_is_feasible(float(max_turn_abs)):
                feasible_turn_abs_deg = float(max_turn_abs)
            else:
                lo = 0.0
                hi = float(max_turn_abs)
                for _ in range(20):
                    mid = 0.5 * (lo + hi)
                    if _turn_is_feasible(mid):
                        lo = mid
                    else:
                        hi = mid
                feasible_turn_abs_deg = max(0.0, float(lo))

        if feasible_turn_abs_deg < min_turn_abs and turn_range_abs_max >= min_turn_abs:
            turn_deg = float(np.clip(turn_deg, -feasible_turn_abs_deg, feasible_turn_abs_deg))
        else:
            turn_deg = float(np.clip(turn_deg, -min(max_turn_abs, feasible_turn_abs_deg), min(max_turn_abs, feasible_turn_abs_deg)))
        if turn_budget_cost_scale > 0.0:
            turn_cost_m = route_turn_cost_m(
                loader,
                abs(turn_deg),
                speed_mps=turn_speed_ref_mps,
                bank_limit_deg=bank_limit_deg,
                cost_scale=turn_budget_cost_scale,
            )
            remaining_route_budget_m = max(0.0, remaining_route_budget_m - turn_cost_m)
        course_deg = (course_deg + turn_deg) % 360.0
    return waypoints
