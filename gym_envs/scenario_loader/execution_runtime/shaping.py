import math

import numpy as np


def apply_legacy_flight_shaping_terms(
    loader,
    cfg: dict,
    *,
    truth,
    inst,
    curr_ias: float,
    curr_alt_agl: float,
    curr_gear: float,
    curr_roll: float,
    heading_error_deg: float,
    ground_track_error_deg: float,
    waypoint_turn_relief_activation: float,
    airborne: bool,
    preliftoff: bool,
    on_runway_task: bool,
    runway_cross_m,
    runway_wid_m,
    ils_valid: float,
    ils_loc: float,
    steps: int,
    add_reward_term,
) -> None:
    tgt_alt = cfg.get("altitude_progress_target", None)
    if tgt_alt is None:
        tgt_alt = loader.mission_cmd.get("target_altitude", 0.0)
    try:
        tgt_alt = float(tgt_alt)
    except Exception:
        tgt_alt = 0.0
    d_alt = truth.z - loader.prev_alt
    if (tgt_alt <= 0.0 or truth.z < tgt_alt) and d_alt > 0:
        add_reward_term("altitude_progress", d_alt * cfg.get("altitude_progress_weight", 0.0))
    elif truth.z < 10.0 and d_alt < -1.0:
        add_reward_term("low_alt_descent_penalty", d_alt * 0.1)

    tgt_spd = cfg.get("speed_progress_target", None)
    if tgt_spd is None:
        tgt_spd = loader.mission_cmd.get("target_speed", 180.0)
    try:
        tgt_spd = float(tgt_spd)
    except Exception:
        tgt_spd = 0.0
    d_spd = curr_ias - loader.prev_speed
    if (tgt_spd <= 0.0 or curr_ias < tgt_spd) and d_spd > 0:
        add_reward_term("speed_progress", d_spd * cfg.get("speed_progress_weight", 0.0))
    elif d_spd < 0:
        add_reward_term("speed_regress", d_spd * cfg.get("speed_progress_weight_negative", 0.0))

    stationary_penalty = cfg.get("stationary_penalty", 0.0)
    if stationary_penalty != 0.0:
        grace_steps = int(cfg.get("stationary_grace_steps", 20))
        speed_thr = float(cfg.get("stationary_speed_threshold", 5.0))
        alt_thr = float(cfg.get("stationary_alt_threshold", 5.0))
        if steps > grace_steps and truth.speed < speed_thr and truth.z < alt_thr:
            add_reward_term("stationary_penalty", float(stationary_penalty))

    liftoff_bonus = float(cfg.get("liftoff_bonus", 0.0))
    if liftoff_bonus != 0.0 and not loader.liftoff_awarded:
        liftoff_speed_thr = float(cfg.get("liftoff_speed_threshold", 80.0))
        liftoff_alt_thr = float(cfg.get("liftoff_alt_threshold", 5.0))
        if float(inst[0]) >= liftoff_speed_thr and float(inst[3]) >= liftoff_alt_thr:
            add_reward_term("liftoff_bonus", liftoff_bonus)
            loader.liftoff_awarded = True

    rotation_weight = float(cfg.get("rotation_reward_weight", 0.0))
    if rotation_weight != 0.0:
        rot_spd_thr = float(cfg.get("rotation_speed_threshold", 80.0))
        rot_alt_thr = float(cfg.get("rotation_alt_threshold", 5.0))
        rot_pitch_cap = float(cfg.get("rotation_pitch_cap", 15.0))
        if float(inst[0]) >= rot_spd_thr and float(inst[3]) <= rot_alt_thr:
            pitch_deg = float(inst[7])
            pitch_term = float(np.clip(pitch_deg, -rot_pitch_cap, rot_pitch_cap))
            add_reward_term("rotation_reward", pitch_term * rotation_weight)
            over_w = float(cfg.get("rotation_overpitch_penalty_weight", 0.0))
            if over_w != 0.0 and pitch_deg > rot_pitch_cap:
                add_reward_term("rotation_overpitch_penalty", (pitch_deg - rot_pitch_cap) * over_w)

    if curr_alt_agl > 50.0 and curr_gear < 0.1 and not loader.gear_bonus_awarded:
        add_reward_term("gear_up_bonus", cfg.get("gear_up_bonus", 0.0))
        loader.gear_bonus_awarded = True

    if truth.z < 100.0:
        add_reward_term("roll_stability", abs(curr_roll) * cfg.get("roll_stability_weight", 0.0))

    if cfg.get("heading_error_weight", 0.0) != 0.0:
        diff = heading_error_deg
        turn_heading_relief_max = float(
            cfg.get("waypoint_turn_heading_relief_max", cfg.get("waypoint_turn_relief_max", 0.0))
        )
        turn_heading_relief_max = float(np.clip(turn_heading_relief_max, 0.0, 0.95))
        heading_penalty_scale = 1.0 - turn_heading_relief_max * waypoint_turn_relief_activation
        add_reward_term("heading_error_penalty", diff * cfg.get("heading_error_weight") * heading_penalty_scale)
        hold_db = float(cfg.get("heading_hold_deadband_deg", 0.0))
        hold_bonus = float(cfg.get("heading_hold_bonus", 0.0))
        if hold_bonus != 0.0 and diff <= max(0.0, hold_db):
            add_reward_term("heading_hold_bonus", hold_bonus)

    if airborne:
        w_alt_err = float(cfg.get("altitude_error_weight", 0.0))
        if w_alt_err != 0.0:
            alt_baro = float(inst[2])
            min_alt = float(cfg.get("altitude_error_min_alt", 0.0))
            if alt_baro >= min_alt:
                tgt_alt = cfg.get("altitude_error_target", None)
                if tgt_alt is None:
                    tgt_alt = loader.mission_cmd.get("target_altitude", alt_baro)
                try:
                    tgt_alt = float(tgt_alt)
                except Exception:
                    tgt_alt = alt_baro
                deadband = float(cfg.get("altitude_error_deadband_m", cfg.get("altitude_error_band_m", 0.0)))
                norm = float(cfg.get("altitude_error_norm_m", 100.0))
                if norm <= 1.0e-6:
                    norm = 100.0
                p = float(cfg.get("altitude_error_power", 1.0))
                if p < 1.0:
                    p = 1.0
                if p > 8.0:
                    p = 8.0
                err = abs(alt_baro - float(tgt_alt)) - max(0.0, deadband)
                if err > 0.0:
                    x = err / norm
                    clip = float(cfg.get("altitude_error_clip", 0.0))
                    if clip > 0.0:
                        x = min(x, clip)
                    add_reward_term("altitude_error_penalty", w_alt_err * (x**p))
                else:
                    hold_bonus = float(cfg.get("altitude_hold_bonus", 0.0))
                    if hold_bonus != 0.0:
                        add_reward_term("altitude_hold_bonus", hold_bonus)

        w_spd_err = float(cfg.get("speed_error_weight", 0.0))
        if w_spd_err != 0.0:
            min_ias = float(cfg.get("speed_error_min_ias", 0.0))
            if float(curr_ias) >= min_ias:
                tgt_spd = cfg.get("speed_error_target", None)
                if tgt_spd is None:
                    tgt_spd = loader.mission_cmd.get("target_speed", float(curr_ias))
                try:
                    tgt_spd = float(tgt_spd)
                except Exception:
                    tgt_spd = float(curr_ias)
                deadband = float(cfg.get("speed_error_deadband", cfg.get("speed_error_band", 0.0)))
                norm = float(cfg.get("speed_error_norm", 30.0))
                if norm <= 1.0e-6:
                    norm = 30.0
                p = float(cfg.get("speed_error_power", 1.0))
                if p < 1.0:
                    p = 1.0
                if p > 8.0:
                    p = 8.0
                err = abs(float(curr_ias) - float(tgt_spd)) - max(0.0, deadband)
                if err > 0.0:
                    x = err / norm
                    clip = float(cfg.get("speed_error_clip", 0.0))
                    if clip > 0.0:
                        x = min(x, clip)
                    add_reward_term("speed_error_penalty", w_spd_err * (x**p))
                else:
                    hold_bonus = float(cfg.get("speed_hold_bonus", 0.0))
                    if hold_bonus != 0.0:
                        add_reward_term("speed_hold_bonus", hold_bonus)

        for name, value, deadband_key, norm_key, power_key, index in (
            ("roll_abs_penalty", float(cfg.get("roll_abs_weight", 0.0)), "roll_abs_deadband_deg", "roll_abs_norm_deg", "roll_abs_power", 8),
            ("pitch_abs_penalty", float(cfg.get("pitch_abs_weight", 0.0)), "pitch_abs_deadband_deg", "pitch_abs_norm_deg", "pitch_abs_power", 7),
            ("yaw_rate_abs_penalty", float(cfg.get("yaw_rate_abs_weight", 0.0)), "yaw_rate_abs_deadband_deg_s", "yaw_rate_abs_norm_deg_s", "yaw_rate_abs_power", 14),
            ("beta_abs_penalty", float(cfg.get("beta_abs_weight", 0.0)), "beta_abs_deadband_deg", "beta_abs_norm_deg", "beta_abs_power", 6),
        ):
            if value == 0.0:
                continue
            state_value = abs(float(inst[index])) if len(inst) > index else 0.0
            dead = float(cfg.get(deadband_key, 0.0))
            norm = float(cfg.get(norm_key, 30.0 if "roll" in name else 20.0))
            if norm <= 1.0e-6:
                norm = 30.0 if "roll" in name else 20.0
            p = float(cfg.get(power_key, 1.0))
            if p < 1.0:
                p = 1.0
            if p > 8.0:
                p = 8.0
            err = state_value - max(0.0, dead)
            if err > 0.0:
                add_reward_term(name, value * ((err / norm) ** p))

        w_g = float(cfg.get("g_deviation_weight", 0.0))
        if w_g != 0.0:
            g_load = float(inst[10])
            dead = float(cfg.get("g_deviation_deadband", 0.0))
            norm = float(cfg.get("g_deviation_norm", 0.5))
            if norm <= 1.0e-6:
                norm = 0.5
            p = float(cfg.get("g_deviation_power", 1.0))
            if p < 1.0:
                p = 1.0
            if p > 8.0:
                p = 8.0
            g_dev_min_alt_agl_m = float(cfg.get("g_deviation_min_alt_agl_m", 5.0))
            err = abs(g_load - 1.0) - max(0.0, dead)
            if airborne and curr_alt_agl > g_dev_min_alt_agl_m and err > 0.0:
                add_reward_term("g_deviation_penalty", w_g * ((err / norm) ** p))

    add_reward_term("speed_reward", truth.speed * cfg.get("speed_reward_weight", 0.0))

    if preliftoff and on_runway_task and runway_cross_m is not None and runway_wid_m is not None:
        half_w = 0.5 * float(runway_wid_m)
        if half_w > 1.0e-6:
            frac = abs(float(runway_cross_m)) / half_w
            if frac > 2.0:
                frac = 2.0
            min_ias = float(cfg.get("runway_centerline_penalty_min_ias", 0.0))
            max_ias = float(cfg.get("runway_centerline_penalty_max_ias", 0.0))
            scale = 1.0
            if max_ias > min_ias + 1.0e-6:
                scale = (float(curr_ias) - min_ias) / (max_ias - min_ias)
                scale = float(np.clip(scale, 0.0, 1.0))

            w_center_m = float(cfg.get("runway_centerline_m_penalty_weight", 0.0))
            if w_center_m != 0.0:
                dead_m = max(0.0, float(cfg.get("runway_centerline_m_deadband_m", 0.0)))
                norm_m = float(cfg.get("runway_centerline_m_norm_m", 5.0))
                if norm_m <= 1.0e-6:
                    norm_m = 5.0
                p_m = float(np.clip(float(cfg.get("runway_centerline_m_power", 2.0)), 1.0, 8.0))
                err_m = abs(float(runway_cross_m)) - dead_m
                if err_m > 0.0:
                    x_m = err_m / norm_m
                    clip_m = float(cfg.get("runway_centerline_m_clip", 0.0))
                    if clip_m > 0.0:
                        x_m = min(x_m, clip_m)
                    add_reward_term("runway_centerline_m_penalty", w_center_m * (x_m**p_m) * scale)

            w_center = float(cfg.get("runway_centerline_penalty_weight", 0.0))
            if w_center != 0.0:
                safe_frac = float(np.clip(float(cfg.get("runway_centerline_safe_frac", 0.0)), 0.0, 0.99))
                x = max(0.0, frac - safe_frac) / max(1.0 - safe_frac, 1.0e-6)
                p = float(np.clip(float(cfg.get("runway_centerline_penalty_power", 2.0)), 1.0, 8.0))
                add_reward_term("runway_centerline_penalty", w_center * (x**p) * scale)

            w_bar = float(cfg.get("runway_centerline_barrier_weight", 0.0))
            if w_bar != 0.0:
                clip_frac = float(cfg.get("runway_centerline_barrier_clip_frac", 0.995))
                clip_frac = float(np.clip(clip_frac, 1.0e-6, 0.999999))
                frac_c = min(max(frac, 0.0), clip_frac)
                barrier = -math.log(max(1.0e-6, 1.0 - frac_c))
                add_reward_term("runway_centerline_barrier", w_bar * barrier * scale)

    if runway_cross_m is not None:
        dep_max_alt = float(cfg.get("departure_centerline_max_alt_agl_m", 0.0))
        if airborne and dep_max_alt > 0.0 and curr_alt_agl <= dep_max_alt:
            w_dep_m = float(cfg.get("departure_centerline_m_penalty_weight", 0.0))
            dead_m = max(0.0, float(cfg.get("departure_centerline_m_deadband_m", 0.0)))
            if w_dep_m != 0.0:
                norm_m = float(cfg.get("departure_centerline_m_norm_m", 20.0))
                if norm_m <= 1.0e-6:
                    norm_m = 20.0
                p_m = float(np.clip(float(cfg.get("departure_centerline_m_power", 2.0)), 1.0, 8.0))
                err_m = abs(float(runway_cross_m)) - dead_m
                if err_m > 0.0:
                    x_m = err_m / norm_m
                    clip_m = float(cfg.get("departure_centerline_m_clip", 0.0))
                    if clip_m > 0.0:
                        x_m = min(x_m, clip_m)
                    add_reward_term("departure_centerline_m_penalty", w_dep_m * (x_m**p_m))
            w_dep_center = float(cfg.get("departure_centerline_reward_weight", 0.0))
            if w_dep_center != 0.0:
                band_m = float(cfg.get("departure_centerline_reward_band_m", max(1.0, dead_m)))
                if band_m <= 1.0e-6:
                    band_m = 1.0
                center_frac = max(0.0, 1.0 - abs(float(runway_cross_m)) / band_m)
                if center_frac > 0.0:
                    add_reward_term("departure_centerline_reward", w_dep_center * center_frac)

            dep_track_err = ground_track_error_deg
            w_dep_trk = float(cfg.get("departure_track_error_weight", 0.0))
            if w_dep_trk != 0.0:
                dead_deg = max(0.0, float(cfg.get("departure_track_error_deadband_deg", 0.0)))
                norm_deg = float(cfg.get("departure_track_error_norm_deg", 10.0))
                if norm_deg <= 1.0e-6:
                    norm_deg = 10.0
                p_deg = float(np.clip(float(cfg.get("departure_track_error_power", 2.0)), 1.0, 8.0))
                err_deg = dep_track_err - dead_deg
                if err_deg > 0.0:
                    x_deg = err_deg / norm_deg
                    clip_deg = float(cfg.get("departure_track_error_clip", 0.0))
                    if clip_deg > 0.0:
                        x_deg = min(x_deg, clip_deg)
                    add_reward_term("departure_track_error_penalty", w_dep_trk * (x_deg**p_deg))

            w_dep_trk_reward = float(cfg.get("departure_track_reward_weight", 0.0))
            if w_dep_trk_reward != 0.0:
                band_deg = float(cfg.get("departure_track_reward_band_deg", 10.0))
                if band_deg <= 1.0e-6:
                    band_deg = 10.0
                track_frac = max(0.0, 1.0 - dep_track_err / band_deg)
                if track_frac > 0.0:
                    add_reward_term("departure_track_reward", w_dep_trk_reward * track_frac)

    if cfg.get("alignment_reward_weight", 0.0) != 0.0:
        w = float(cfg.get("alignment_reward_weight"))
        if on_runway_task and preliftoff:
            if ils_valid > 0.5:
                add_reward_term("alignment_reward", (1.0 - min(abs(ils_loc), 1.0)) * w)
        else:
            min_alt_for_cmd_align = float(cfg.get("mission_alignment_min_alt", 120.0))
            if truth.z >= min_alt_for_cmd_align:
                diff = heading_error_deg
                align_factor = math.cos(math.radians(diff))
                if align_factor > 0:
                    add_reward_term("alignment_reward", align_factor * w)
