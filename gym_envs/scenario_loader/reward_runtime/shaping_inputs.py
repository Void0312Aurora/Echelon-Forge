import ef_py


def build_flight_shaping_runtime_inputs(
    loader,
    cfg: dict,
    *,
    steps: int,
    truth,
    inst_vec,
    curr_ias: float,
    curr_alt_agl: float,
    curr_gear: float,
    curr_roll: float,
    heading_error_deg: float,
    ground_track_error_deg: float,
    waypoint_turn_relief_activation: float,
    preliftoff: bool,
    on_runway_task: bool,
    airborne: bool,
    runway_cross_m,
    runway_wid_m,
    ils_valid: float,
    ils_loc: float,
):
    inputs = ef_py.FlightShapingRuntimeInputs()
    inputs.truth_altitude_m = float(getattr(truth, "z", 0.0))
    inputs.truth_speed_mps = float(getattr(truth, "speed", 0.0))
    inputs.prev_altitude_m = float(getattr(loader, "prev_alt", 0.0))
    inputs.prev_ias_mps = float(getattr(loader, "prev_speed", 0.0))
    inputs.curr_ias_mps = float(curr_ias)
    inputs.curr_alt_baro_m = float(inst_vec[2]) if len(inst_vec) > 2 else float(getattr(truth, "z", 0.0))
    inputs.curr_alt_agl_m = float(curr_alt_agl)
    inputs.curr_gear_fraction = float(curr_gear)
    inputs.curr_roll_deg = float(curr_roll)
    inputs.curr_pitch_deg = float(inst_vec[7]) if len(inst_vec) > 7 else 0.0
    inputs.curr_beta_deg = float(inst_vec[6]) if len(inst_vec) > 6 else 0.0
    inputs.curr_yaw_rate_deg_s = float(inst_vec[14]) if len(inst_vec) > 14 else 0.0
    inputs.curr_g_load = float(inst_vec[10]) if len(inst_vec) > 10 else 1.0
    inputs.step_count = int(steps)
    route_target_altitude_m = loader._current_route_target_altitude_m(truth=truth)
    base_target_altitude_m = (
        loader.mission_cmd.get("target_altitude", 0.0) if route_target_altitude_m is None else route_target_altitude_m
    )
    inputs.target_altitude_m = float(cfg.get("altitude_progress_target", base_target_altitude_m) or 0.0)
    inputs.target_speed_mps = float(cfg.get("speed_progress_target", loader.mission_cmd.get("target_speed", 180.0)) or 0.0)
    inputs.heading_error_deg = float(heading_error_deg)
    inputs.ground_track_error_deg = float(ground_track_error_deg)
    inputs.waypoint_turn_relief_activation = float(waypoint_turn_relief_activation)
    inputs.preliftoff = bool(preliftoff)
    inputs.on_runway_task = bool(on_runway_task)
    inputs.airborne = bool(airborne)
    inputs.has_runway_cross_m = runway_cross_m is not None and runway_wid_m is not None
    if inputs.has_runway_cross_m:
        inputs.runway_cross_m = float(runway_cross_m)
        inputs.runway_width_m = float(runway_wid_m)
    inputs.ils_valid = bool(float(ils_valid) > 0.5)
    inputs.ils_loc_dev = float(ils_loc)
    inputs.liftoff_awarded = bool(getattr(loader, "liftoff_awarded", False))
    inputs.gear_bonus_awarded = bool(getattr(loader, "gear_bonus_awarded", False))

    inputs.altitude_progress_weight = float(cfg.get("altitude_progress_weight", 0.0))
    inputs.speed_progress_weight = float(cfg.get("speed_progress_weight", 0.0))
    inputs.speed_progress_negative_weight = float(cfg.get("speed_progress_weight_negative", 0.0))
    inputs.stationary_penalty = float(cfg.get("stationary_penalty", 0.0))
    inputs.stationary_grace_steps = int(cfg.get("stationary_grace_steps", 20))
    inputs.stationary_speed_threshold_mps = float(cfg.get("stationary_speed_threshold", 5.0))
    inputs.stationary_alt_threshold_m = float(cfg.get("stationary_alt_threshold", 5.0))
    inputs.liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
    inputs.liftoff_speed_threshold_mps = float(cfg.get("liftoff_speed_threshold", 80.0))
    inputs.liftoff_alt_threshold_m = float(cfg.get("liftoff_alt_threshold", 5.0))
    inputs.rotation_reward_weight = float(cfg.get("rotation_reward_weight", 0.0))
    inputs.rotation_speed_threshold_mps = float(cfg.get("rotation_speed_threshold", 80.0))
    inputs.rotation_alt_threshold_m = float(cfg.get("rotation_alt_threshold", 5.0))
    inputs.rotation_pitch_cap_deg = float(cfg.get("rotation_pitch_cap", 15.0))
    inputs.rotation_overpitch_penalty_weight = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
    inputs.gear_up_bonus = float(cfg.get("gear_up_bonus", 0.0))
    inputs.gear_up_bonus_min_alt_agl_m = 50.0
    inputs.roll_stability_weight = float(cfg.get("roll_stability_weight", 0.0))
    inputs.heading_error_weight = float(cfg.get("heading_error_weight", 0.0))
    inputs.heading_hold_deadband_deg = float(cfg.get("heading_hold_deadband_deg", 0.0))
    inputs.heading_hold_bonus = float(cfg.get("heading_hold_bonus", 0.0))
    inputs.waypoint_turn_heading_relief_max = float(
        cfg.get("waypoint_turn_heading_relief_max", cfg.get("waypoint_turn_relief_max", 0.0))
    )

    inputs.altitude_error_weight = float(cfg.get("altitude_error_weight", 0.0))
    inputs.altitude_error_min_alt_m = float(cfg.get("altitude_error_min_alt", 0.0))
    inputs.altitude_error_target_m = float(
        cfg.get(
            "altitude_error_target",
            (
                base_target_altitude_m
                if route_target_altitude_m is not None
                else loader.mission_cmd.get("target_altitude", inputs.curr_alt_baro_m)
            ),
        )
        or inputs.curr_alt_baro_m
    )
    inputs.altitude_error_deadband_m = float(cfg.get("altitude_error_deadband_m", cfg.get("altitude_error_band_m", 0.0)))
    inputs.altitude_error_norm_m = float(cfg.get("altitude_error_norm_m", 100.0))
    inputs.altitude_error_power = float(cfg.get("altitude_error_power", 1.0))
    inputs.altitude_error_clip = float(cfg.get("altitude_error_clip", 0.0))
    inputs.altitude_hold_bonus = float(cfg.get("altitude_hold_bonus", 0.0))

    inputs.speed_error_weight = float(cfg.get("speed_error_weight", 0.0))
    inputs.speed_error_min_ias_mps = float(cfg.get("speed_error_min_ias", 0.0))
    inputs.speed_error_target_mps = float(
        cfg.get("speed_error_target", loader.mission_cmd.get("target_speed", inputs.curr_ias_mps)) or inputs.curr_ias_mps
    )
    inputs.speed_error_deadband_mps = float(cfg.get("speed_error_deadband", cfg.get("speed_error_band", 0.0)))
    inputs.speed_error_norm_mps = float(cfg.get("speed_error_norm", 30.0))
    inputs.speed_error_power = float(cfg.get("speed_error_power", 1.0))
    inputs.speed_error_clip = float(cfg.get("speed_error_clip", 0.0))
    inputs.speed_hold_bonus = float(cfg.get("speed_hold_bonus", 0.0))

    inputs.roll_abs_weight = float(cfg.get("roll_abs_weight", 0.0))
    inputs.roll_abs_deadband_deg = float(cfg.get("roll_abs_deadband_deg", 0.0))
    inputs.roll_abs_norm_deg = float(cfg.get("roll_abs_norm_deg", 30.0))
    inputs.roll_abs_power = float(cfg.get("roll_abs_power", 1.0))
    inputs.pitch_abs_weight = float(cfg.get("pitch_abs_weight", 0.0))
    inputs.pitch_abs_deadband_deg = float(cfg.get("pitch_abs_deadband_deg", 0.0))
    inputs.pitch_abs_norm_deg = float(cfg.get("pitch_abs_norm_deg", 20.0))
    inputs.pitch_abs_power = float(cfg.get("pitch_abs_power", 1.0))
    inputs.yaw_rate_abs_weight = float(cfg.get("yaw_rate_abs_weight", 0.0))
    inputs.yaw_rate_abs_deadband_deg_s = float(cfg.get("yaw_rate_abs_deadband_deg_s", 0.0))
    inputs.yaw_rate_abs_norm_deg_s = float(cfg.get("yaw_rate_abs_norm_deg_s", 10.0))
    inputs.yaw_rate_abs_power = float(cfg.get("yaw_rate_abs_power", 1.0))
    inputs.beta_abs_weight = float(cfg.get("beta_abs_weight", 0.0))
    inputs.beta_abs_deadband_deg = float(cfg.get("beta_abs_deadband_deg", 0.0))
    inputs.beta_abs_norm_deg = float(cfg.get("beta_abs_norm_deg", 10.0))
    inputs.beta_abs_power = float(cfg.get("beta_abs_power", 1.0))
    inputs.g_deviation_weight = float(cfg.get("g_deviation_weight", 0.0))
    inputs.g_deviation_deadband = float(cfg.get("g_deviation_deadband", 0.0))
    inputs.g_deviation_norm = float(cfg.get("g_deviation_norm", 0.5))
    inputs.g_deviation_power = float(cfg.get("g_deviation_power", 1.0))
    inputs.g_deviation_min_alt_agl_m = float(cfg.get("g_deviation_min_alt_agl_m", 5.0))

    inputs.speed_reward_weight = float(cfg.get("speed_reward_weight", 0.0))
    inputs.runway_centerline_penalty_min_ias_mps = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
    inputs.runway_centerline_penalty_max_ias_mps = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
    inputs.runway_centerline_m_penalty_weight = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
    inputs.runway_centerline_m_deadband_m = float(cfg.get("runway_centerline_m_deadband_m", 0.0))
    inputs.runway_centerline_m_norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
    inputs.runway_centerline_m_power = float(cfg.get("runway_centerline_m_power", 2.0))
    inputs.runway_centerline_m_clip = float(cfg.get("runway_centerline_m_clip", 0.0))
    inputs.runway_centerline_penalty_weight = float(cfg.get("runway_centerline_penalty_weight", 0.0))
    inputs.runway_centerline_safe_frac = float(cfg.get("runway_centerline_safe_frac", 0.0))
    inputs.runway_centerline_penalty_power = float(cfg.get("runway_centerline_penalty_power", 2.0))
    inputs.runway_centerline_barrier_weight = float(cfg.get("runway_centerline_barrier_weight", 0.0))
    inputs.runway_centerline_barrier_clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
    inputs.departure_centerline_max_alt_agl_m = float(cfg.get("departure_centerline_max_alt_agl_m", 0.0))
    inputs.departure_centerline_m_penalty_weight = float(cfg.get("departure_centerline_m_penalty_weight", 0.0))
    inputs.departure_centerline_m_deadband_m = float(cfg.get("departure_centerline_m_deadband_m", 0.0))
    inputs.departure_centerline_m_norm_m = float(cfg.get("departure_centerline_m_norm_m", 20.0))
    inputs.departure_centerline_m_power = float(cfg.get("departure_centerline_m_power", 2.0))
    inputs.departure_centerline_m_clip = float(cfg.get("departure_centerline_m_clip", 0.0))
    inputs.departure_centerline_reward_weight = float(cfg.get("departure_centerline_reward_weight", 0.0))
    inputs.departure_centerline_reward_band_m = float(
        cfg.get("departure_centerline_reward_band_m", max(1.0, inputs.departure_centerline_m_deadband_m))
    )
    inputs.departure_track_error_weight = float(cfg.get("departure_track_error_weight", 0.0))
    inputs.departure_track_error_deadband_deg = float(cfg.get("departure_track_error_deadband_deg", 0.0))
    inputs.departure_track_error_norm_deg = float(cfg.get("departure_track_error_norm_deg", 10.0))
    inputs.departure_track_error_power = float(cfg.get("departure_track_error_power", 2.0))
    inputs.departure_track_error_clip = float(cfg.get("departure_track_error_clip", 0.0))
    inputs.departure_track_reward_weight = float(cfg.get("departure_track_reward_weight", 0.0))
    inputs.departure_track_reward_band_deg = float(cfg.get("departure_track_reward_band_deg", 10.0))
    inputs.alignment_reward_weight = float(cfg.get("alignment_reward_weight", 0.0))
    inputs.mission_alignment_min_alt_m = float(cfg.get("mission_alignment_min_alt", 120.0))
    return inputs


def apply_compiled_flight_shaping_terms(loader, products, add_reward_term, *, include_roll_stability: bool) -> None:
    term_names = (
        "altitude_progress",
        "low_alt_descent_penalty",
        "speed_progress",
        "speed_regress",
        "stationary_penalty",
        "liftoff_bonus",
        "rotation_reward",
        "rotation_overpitch_penalty",
        "gear_up_bonus",
        "heading_error_penalty",
        "heading_hold_bonus",
        "altitude_error_penalty",
        "altitude_hold_bonus",
        "speed_error_penalty",
        "speed_hold_bonus",
        "roll_abs_penalty",
        "pitch_abs_penalty",
        "yaw_rate_abs_penalty",
        "beta_abs_penalty",
        "g_deviation_penalty",
        "runway_centerline_m_penalty",
        "runway_centerline_penalty",
        "runway_centerline_barrier",
        "departure_centerline_m_penalty",
        "departure_centerline_reward",
        "departure_track_error_penalty",
        "departure_track_reward",
        "alignment_reward",
    )
    for name in term_names:
        value = float(getattr(products, name, 0.0))
        if value != 0.0:
            add_reward_term(name, value)
    add_reward_term("speed_reward", float(getattr(products, "speed_reward", 0.0)))
    if include_roll_stability:
        add_reward_term("roll_stability", float(getattr(products, "roll_stability", 0.0)))
    loader.liftoff_awarded = bool(getattr(products, "next_liftoff_awarded", loader.liftoff_awarded))
    loader.gear_bonus_awarded = bool(getattr(products, "next_gear_bonus_awarded", loader.gear_bonus_awarded))


def compute_flight_shaping_products(loader, shaping_inputs, *, use_gpu: bool):
    if shaping_inputs is None:
        return None
    if use_gpu and hasattr(ef_py, "compute_flight_shaping_batch"):
        try:
            batch = ef_py.compute_flight_shaping_batch([shaping_inputs], True)
            if len(batch) == 1:
                return batch[0]
        except Exception:
            pass
    try:
        return ef_py.compute_flight_shaping_terms(shaping_inputs)
    except Exception:
        return None


def add_breakdown_term(breakdown: dict, name: str, value: float) -> None:
    v = float(value)
    breakdown[name] = float(breakdown.get(name, 0.0) + v)
