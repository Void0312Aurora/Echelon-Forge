def randomize_task_order(loader):
    """Randomize top-level C2 task parameters when ranges are specified in scenario.task_order."""
    task_cfg = loader.scenario_data.get("task_order", None)
    if not isinstance(task_cfg, dict):
        return

    rand_cfg = task_cfg.get("randomization", None)
    if not isinstance(rand_cfg, dict) or not rand_cfg:
        return

    def _sample_uniform(name: str):
        raw = rand_cfg.get(name, None)
        if not isinstance(raw, (list, tuple)) or len(raw) < 2:
            return None
        try:
            return float(loader.rng.uniform(float(raw[0]), float(raw[1])))
        except Exception:
            return None

    def _sample_int(name: str):
        raw = rand_cfg.get(name, None)
        if not isinstance(raw, (list, tuple)) or len(raw) < 2:
            return None
        try:
            lo = int(raw[0])
            hi = int(raw[1])
        except Exception:
            return None
        if hi < lo:
            lo, hi = hi, lo
        try:
            return int(loader.rng.randint(lo, hi + 1))
        except Exception:
            return None

    def _f(value, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return float(default)

    def _waypoint_anchor_from_mission():
        raw_index = rand_cfg.get("anchor_from_waypoint_index", None)
        if raw_index is None:
            return None
        waypoints = list(loader.mission_cmd.get("waypoints", []) or [])
        if not waypoints:
            return None
        if isinstance(raw_index, str) and str(raw_index).strip().lower() == "midpoint":
            idx = len(waypoints) // 2
        else:
            try:
                idx = int(raw_index)
            except Exception:
                return None
            if idx < 0:
                idx += len(waypoints)
        if idx < 0 or idx >= len(waypoints):
            return None
        wp = waypoints[idx]
        if not isinstance(wp, dict):
            return None
        try:
            anchor_x = float(wp.get("x", 0.0))
            anchor_y = float(wp.get("y", 0.0))
            anchor_z = float(
                wp.get(
                    "z",
                    wp.get(
                        "altitude_m",
                        task_cfg.get("anchor_z_m", task_cfg.get("target_altitude_m", 0.0)),
                    ),
                )
            )
        except Exception:
            return None
        return idx, anchor_x, anchor_y, anchor_z

    base_target_alt = _f(task_cfg.get("target_altitude_m", task_cfg.get("anchor_z_m", 0.0)), 0.0)
    base_alt_lo = _f(
        task_cfg.get("altitude_block_min_m", max(0.0, base_target_alt - 500.0)),
        max(0.0, base_target_alt - 500.0),
    )
    base_alt_hi = _f(
        task_cfg.get("altitude_block_max_m", base_target_alt + 500.0),
        base_target_alt + 500.0,
    )
    base_target_speed = _f(task_cfg.get("target_speed_mps", 0.0), 0.0)
    base_spd_lo = _f(
        task_cfg.get("speed_min_mps", max(0.0, base_target_speed - 40.0)),
        max(0.0, base_target_speed - 40.0),
    )
    base_spd_hi = _f(
        task_cfg.get("speed_max_mps", base_target_speed + 40.0),
        base_target_speed + 40.0,
    )

    alt_target = _sample_uniform("target_altitude_range_m")
    if alt_target is not None:
        task_cfg["target_altitude_m"] = float(alt_target)
    speed_target = _sample_uniform("target_speed_range_mps")
    if speed_target is not None:
        task_cfg["target_speed_mps"] = float(speed_target)

    for rand_key, field_name in (
        ("anchor_x_range_m", "anchor_x_m"),
        ("anchor_y_range_m", "anchor_y_m"),
        ("anchor_z_range_m", "anchor_z_m"),
        ("station_radius_range_m", "station_radius_m"),
        ("station_leg_length_range_m", "station_leg_length_m"),
        ("station_heading_range_deg", "station_heading_deg"),
        ("on_station_time_range_s", "on_station_time_s"),
        ("fuel_bingo_override_range_kg", "fuel_bingo_override_kg"),
    ):
        sampled = _sample_uniform(rand_key)
        if sampled is not None:
            task_cfg[field_name] = float(sampled)

    priority = _sample_int("priority_range")
    if priority is not None:
        task_cfg["priority"] = int(priority)

    task_id = _sample_int("task_id_range")
    if task_id is not None:
        task_cfg["task_id"] = int(task_id)

    waypoint_anchor = _waypoint_anchor_from_mission()
    if waypoint_anchor is not None:
        anchor_idx, anchor_x, anchor_y, anchor_z = waypoint_anchor
        task_cfg["anchor_x_m"] = float(anchor_x)
        task_cfg["anchor_y_m"] = float(anchor_y)
        task_cfg["anchor_z_m"] = float(anchor_z)
        task_cfg["_anchor_waypoint_idx"] = int(anchor_idx)

    station_choices = rand_cfg.get("station_type_choices", None)
    if isinstance(station_choices, list):
        station_choices = [str(x) for x in station_choices if str(x).strip()]
        if station_choices:
            try:
                idx = int(loader.rng.randint(0, len(station_choices)))
            except Exception:
                idx = 0
            task_cfg["station_type"] = str(station_choices[idx])

    target_alt = _f(task_cfg.get("target_altitude_m", base_target_alt), base_target_alt)
    alt_halfspan = _sample_uniform("altitude_block_halfspan_range_m")
    if alt_halfspan is not None:
        alt_halfspan = max(0.0, float(alt_halfspan))
        task_cfg["altitude_block_min_m"] = max(0.0, target_alt - alt_halfspan)
        task_cfg["altitude_block_max_m"] = max(float(task_cfg["altitude_block_min_m"]), target_alt + alt_halfspan)
    else:
        lo_offset = max(0.0, base_target_alt - base_alt_lo)
        hi_offset = max(0.0, base_alt_hi - base_target_alt)
        task_cfg["altitude_block_min_m"] = max(0.0, target_alt - lo_offset)
        task_cfg["altitude_block_max_m"] = max(float(task_cfg["altitude_block_min_m"]), target_alt + hi_offset)

    target_speed = _f(task_cfg.get("target_speed_mps", base_target_speed), base_target_speed)
    speed_halfspan = _sample_uniform("speed_block_halfspan_range_mps")
    if speed_halfspan is not None:
        speed_halfspan = max(0.0, float(speed_halfspan))
        task_cfg["speed_min_mps"] = max(0.0, target_speed - speed_halfspan)
        task_cfg["speed_max_mps"] = max(float(task_cfg["speed_min_mps"]), target_speed + speed_halfspan)
    else:
        lo_offset = max(0.0, base_target_speed - base_spd_lo)
        hi_offset = max(0.0, base_spd_hi - base_target_speed)
        task_cfg["speed_min_mps"] = max(0.0, target_speed - lo_offset)
        task_cfg["speed_max_mps"] = max(float(task_cfg["speed_min_mps"]), target_speed + hi_offset)

    task_cfg["target_altitude_m"] = float(task_cfg.get("target_altitude_m", target_alt))
    task_cfg["target_speed_mps"] = float(task_cfg.get("target_speed_mps", target_speed))
    task_cfg["anchor_z_m"] = float(task_cfg.get("anchor_z_m", task_cfg["target_altitude_m"]))
    task_cfg["station_heading_deg"] = float(task_cfg.get("station_heading_deg", 0.0)) % 360.0
