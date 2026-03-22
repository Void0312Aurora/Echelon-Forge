#include "core/mission/reward_runtime.h"

#include <algorithm>
#include <cmath>

namespace {

constexpr double kPi = 3.14159265358979323846;

double clamp_value(double value, double lo, double hi) {
    return std::min(std::max(value, lo), hi);
}

double clipped_power_term(double err, double norm, double power, double clip) {
    if (err <= 0.0) {
        return 0.0;
    }
    double use_norm = norm;
    if (use_norm <= 1.0e-6) {
        use_norm = 1.0;
    }
    double x = err / use_norm;
    if (clip > 0.0) {
        x = std::min(x, clip);
    }
    const double p = clamp_value(power, 1.0, 8.0);
    return std::pow(x, p);
}

}  // namespace

WaypointRewardProducts compute_waypoint_reward_terms(const WaypointRewardInputs& inputs) {
    WaypointRewardProducts out{};
    if (!inputs.valid) {
        return out;
    }

    out.valid = true;
    out.next_prev_dist_valid = true;
    out.next_prev_dist_m = inputs.dist_m;

    if (inputs.progress_weight != 0.0 && inputs.has_prev_dist) {
        double progress_delta_m = inputs.prev_dist_m - inputs.dist_m;
        if (progress_delta_m < 0.0) {
            progress_delta_m *= std::max(0.0, inputs.progress_negative_scale);
        }
        out.waypoint_progress = progress_delta_m * inputs.progress_weight;
    }

    if (inputs.distance_weight != 0.0) {
        double dist_term_m = inputs.dist_m;
        if (inputs.distance_clip_m > 0.0) {
            dist_term_m = std::min(dist_term_m, inputs.distance_clip_m);
        }
        double dist_scale = 1.0;
        if (inputs.distance_scale_by_route && inputs.route_length_m > 1.0e-6 && inputs.distance_route_ref_m > 1.0e-6) {
            dist_scale = inputs.distance_route_ref_m / inputs.route_length_m;
            double scale_min = inputs.distance_route_scale_min;
            double scale_max = inputs.distance_route_scale_max;
            if (scale_max < scale_min) {
                std::swap(scale_min, scale_max);
            }
            dist_scale = clamp_value(dist_scale, scale_min, scale_max);
        }
        out.waypoint_distance = dist_term_m * inputs.distance_weight * dist_scale;
    }

    if (inputs.cross_track_weight != 0.0 && inputs.has_guidance) {
        const double xtk_err_m = std::abs(inputs.xtk_m) - std::max(0.0, inputs.cross_track_deadband_m);
        if (xtk_err_m > 0.0) {
            const double x = clipped_power_term(
                xtk_err_m,
                inputs.cross_track_norm_m <= 1.0e-6 ? 1000.0 : inputs.cross_track_norm_m,
                inputs.cross_track_power,
                inputs.cross_track_clip
            );
            const double turn_relief_max = clamp_value(inputs.turn_relief_max, 0.0, 0.95);
            const double penalty_scale = 1.0 - turn_relief_max * inputs.turn_relief_activation;
            out.waypoint_cross_track = inputs.cross_track_weight * x * penalty_scale;
        }
    }

    if (inputs.proximity_weight != 0.0 && inputs.proximity_ref_m > 1.0e-6) {
        const double prox_p = clamp_value(inputs.proximity_power, 1.0, 8.0);
        const double prox_x = 1.0 - std::min(inputs.dist_m, inputs.proximity_ref_m) / inputs.proximity_ref_m;
        if (prox_x > 0.0) {
            out.waypoint_proximity = inputs.proximity_weight * std::pow(prox_x, prox_p);
        }
    }

    const bool is_intermediate_flyby = (!inputs.is_flyover) && (inputs.waypoint_index < (inputs.waypoint_count - 1));
    bool arrived = false;
    if (is_intermediate_flyby) {
        if (inputs.has_guidance && inputs.leg_len_m > 1.0e-6) {
            if (inputs.dist_m <= inputs.waypoint_radius_m) {
                arrived = true;
            } else if ((!inputs.passed_fix) && std::abs(inputs.xtk_m) <= inputs.sequence_gate_m && inputs.dtg_m <= std::max(inputs.lead_turn_m, 0.0)) {
                arrived = true;
            } else if (inputs.passed_fix && inputs.dist_m <= std::max(inputs.sequence_gate_m, inputs.waypoint_radius_m + 500.0)) {
                arrived = true;
            }
        }
    } else {
        arrived = inputs.dist_m <= inputs.waypoint_radius_m;
    }

    out.arrived = arrived;
    if (arrived) {
        out.waypoint_reached_bonus = inputs.reached_bonus;
    }
    return out;
}

ApproachRewardProducts compute_approach_reward_terms(const ApproachRewardInputs& inputs) {
    ApproachRewardProducts out{};
    if (!inputs.valid) {
        return out;
    }

    out.valid = true;
    if (inputs.ils_valid) {
        const double curr_loc_abs = std::abs(inputs.ils_loc_dev);
        const double curr_gs_abs = std::abs(inputs.ils_gs_dev);

        if (inputs.localizer_weight != 0.0) {
            const double err = curr_loc_abs - std::max(0.0, inputs.localizer_deadband);
            if (err > 0.0) {
                const double norm = inputs.localizer_norm <= 1.0e-6 ? 1.0 : inputs.localizer_norm;
                out.approach_localizer = inputs.localizer_weight * clipped_power_term(
                    err,
                    norm,
                    inputs.localizer_power,
                    inputs.localizer_clip
                );
            }
        }

        if (inputs.localizer_improve_weight != 0.0 && inputs.has_prev_loc) {
            out.approach_localizer_improve = (inputs.prev_loc_abs - curr_loc_abs) * inputs.localizer_improve_weight;
        }

        if (inputs.glideslope_weight != 0.0) {
            const double err = curr_gs_abs - std::max(0.0, inputs.glideslope_deadband);
            if (err > 0.0) {
                const double norm = inputs.glideslope_norm <= 1.0e-6 ? 1.0 : inputs.glideslope_norm;
                out.approach_glideslope = inputs.glideslope_weight * clipped_power_term(
                    err,
                    norm,
                    inputs.glideslope_power,
                    inputs.glideslope_clip
                );
            }
        }

        if (inputs.glideslope_improve_weight != 0.0 && inputs.has_prev_gs) {
            out.approach_glideslope_improve = (inputs.prev_gs_abs - curr_gs_abs) * inputs.glideslope_improve_weight;
        }

        if (inputs.dme_progress_weight != 0.0 && std::isfinite(inputs.ils_dme_m) && inputs.has_prev_dme) {
            double quality = 1.0;
            if (inputs.dme_progress_localizer_band > 1.0e-6) {
                quality *= std::max(0.0, 1.0 - curr_loc_abs / inputs.dme_progress_localizer_band);
            }
            if (inputs.dme_progress_glideslope_band > 1.0e-6) {
                quality *= std::max(0.0, 1.0 - curr_gs_abs / inputs.dme_progress_glideslope_band);
            }
            const double quality_power = clamp_value(inputs.dme_progress_quality_power, 0.5, 4.0);
            quality = std::pow(clamp_value(quality, 0.0, 1.0), quality_power);
            out.approach_dme_progress = (inputs.prev_dme_m - inputs.ils_dme_m) * inputs.dme_progress_weight * quality;
        }

        if (inputs.capture_bonus != 0.0) {
            const double loc_band = std::max(0.0, inputs.capture_localizer_band);
            const double gs_band = std::max(0.0, inputs.capture_glideslope_band);
            if (curr_loc_abs <= loc_band && curr_gs_abs <= gs_band) {
                out.approach_capture_bonus = inputs.capture_bonus;
            }
        }

        out.next_prev_valid = true;
        out.next_prev_loc_abs = curr_loc_abs;
        out.next_prev_gs_abs = curr_gs_abs;
        out.next_prev_dme_m = inputs.ils_dme_m;
    } else {
        out.clear_history = true;
    }

    if (inputs.sink_rate_weight != 0.0 && inputs.curr_alt_agl_m <= std::max(0.0, inputs.flare_agl_m)) {
        const double err = std::abs(inputs.sink_rate_mps) - std::max(0.0, inputs.sink_rate_deadband_mps);
        if (err > 0.0) {
            const double norm = inputs.sink_rate_norm_mps <= 1.0e-6 ? 2.0 : inputs.sink_rate_norm_mps;
            out.landing_sink_rate_penalty = inputs.sink_rate_weight * clipped_power_term(
                err,
                norm,
                inputs.sink_rate_power,
                inputs.sink_rate_clip
            );
        }
    }
    return out;
}

FlightShapingRuntimeProducts compute_flight_shaping_terms(const FlightShapingRuntimeInputs& inputs) {
    FlightShapingRuntimeProducts out{};
    out.valid = true;
    out.next_liftoff_awarded = inputs.liftoff_awarded;
    out.next_gear_bonus_awarded = inputs.gear_bonus_awarded;

    const double d_alt = inputs.truth_altitude_m - inputs.prev_altitude_m;
    const double d_spd = inputs.curr_ias_mps - inputs.prev_ias_mps;

    if ((inputs.target_altitude_m <= 0.0 || inputs.truth_altitude_m < inputs.target_altitude_m) && d_alt > 0.0) {
        out.altitude_progress = d_alt * inputs.altitude_progress_weight;
    } else if (inputs.truth_altitude_m < 10.0 && d_alt < -1.0) {
        out.low_alt_descent_penalty = d_alt * 0.1;
    }

    if ((inputs.target_speed_mps <= 0.0 || inputs.curr_ias_mps < inputs.target_speed_mps) && d_spd > 0.0) {
        out.speed_progress = d_spd * inputs.speed_progress_weight;
    } else if (d_spd < 0.0) {
        out.speed_regress = d_spd * inputs.speed_progress_negative_weight;
    }

    if (
        inputs.stationary_penalty != 0.0
        && inputs.step_count > inputs.stationary_grace_steps
        && inputs.truth_speed_mps < inputs.stationary_speed_threshold_mps
        && inputs.truth_altitude_m < inputs.stationary_alt_threshold_m
    ) {
        out.stationary_penalty = inputs.stationary_penalty;
    }

    if (
        inputs.liftoff_bonus != 0.0
        && !inputs.liftoff_awarded
        && inputs.curr_ias_mps >= inputs.liftoff_speed_threshold_mps
        && inputs.curr_alt_agl_m >= inputs.liftoff_alt_threshold_m
    ) {
        out.liftoff_bonus = inputs.liftoff_bonus;
        out.next_liftoff_awarded = true;
    }

    if (
        inputs.rotation_reward_weight != 0.0
        && inputs.curr_ias_mps >= inputs.rotation_speed_threshold_mps
        && inputs.curr_alt_agl_m <= inputs.rotation_alt_threshold_m
    ) {
        const double rot_pitch_cap_deg = std::max(0.0, inputs.rotation_pitch_cap_deg);
        const double pitch_term = clamp_value(inputs.curr_pitch_deg, -rot_pitch_cap_deg, rot_pitch_cap_deg);
        out.rotation_reward = pitch_term * inputs.rotation_reward_weight;
        if (inputs.rotation_overpitch_penalty_weight != 0.0 && inputs.curr_pitch_deg > rot_pitch_cap_deg) {
            out.rotation_overpitch_penalty =
                (inputs.curr_pitch_deg - rot_pitch_cap_deg) * inputs.rotation_overpitch_penalty_weight;
        }
    }

    if (
        inputs.gear_up_bonus != 0.0
        && !inputs.gear_bonus_awarded
        && inputs.curr_alt_agl_m > inputs.gear_up_bonus_min_alt_agl_m
        && inputs.curr_gear_fraction < 0.1
    ) {
        out.gear_up_bonus = inputs.gear_up_bonus;
        out.next_gear_bonus_awarded = true;
    }

    if (inputs.truth_altitude_m < 100.0) {
        out.roll_stability = std::abs(inputs.curr_roll_deg) * inputs.roll_stability_weight;
    }

    if (inputs.heading_error_weight != 0.0) {
        const double turn_heading_relief_max = clamp_value(inputs.waypoint_turn_heading_relief_max, 0.0, 0.95);
        const double heading_penalty_scale = 1.0 - turn_heading_relief_max * inputs.waypoint_turn_relief_activation;
        out.heading_error_penalty = inputs.heading_error_deg * inputs.heading_error_weight * heading_penalty_scale;
        if (
            inputs.heading_hold_bonus != 0.0
            && inputs.heading_error_deg <= std::max(0.0, inputs.heading_hold_deadband_deg)
        ) {
            out.heading_hold_bonus = inputs.heading_hold_bonus;
        }
    }

    if (inputs.airborne) {
        if (inputs.altitude_error_weight != 0.0 && inputs.curr_alt_baro_m >= inputs.altitude_error_min_alt_m) {
            const double alt_err = std::abs(inputs.curr_alt_baro_m - inputs.altitude_error_target_m)
                - std::max(0.0, inputs.altitude_error_deadband_m);
            if (alt_err > 0.0) {
                out.altitude_error_penalty = inputs.altitude_error_weight * clipped_power_term(
                    alt_err,
                    inputs.altitude_error_norm_m <= 1.0e-6 ? 100.0 : inputs.altitude_error_norm_m,
                    inputs.altitude_error_power,
                    inputs.altitude_error_clip
                );
            } else if (inputs.altitude_hold_bonus != 0.0) {
                out.altitude_hold_bonus = inputs.altitude_hold_bonus;
            }
        }

        if (inputs.speed_error_weight != 0.0 && inputs.curr_ias_mps >= inputs.speed_error_min_ias_mps) {
            const double speed_err = std::abs(inputs.curr_ias_mps - inputs.speed_error_target_mps)
                - std::max(0.0, inputs.speed_error_deadband_mps);
            if (speed_err > 0.0) {
                out.speed_error_penalty = inputs.speed_error_weight * clipped_power_term(
                    speed_err,
                    inputs.speed_error_norm_mps <= 1.0e-6 ? 30.0 : inputs.speed_error_norm_mps,
                    inputs.speed_error_power,
                    inputs.speed_error_clip
                );
            } else if (inputs.speed_hold_bonus != 0.0) {
                out.speed_hold_bonus = inputs.speed_hold_bonus;
            }
        }

        if (inputs.roll_abs_weight != 0.0) {
            const double roll_err = std::abs(inputs.curr_roll_deg) - std::max(0.0, inputs.roll_abs_deadband_deg);
            if (roll_err > 0.0) {
                out.roll_abs_penalty = inputs.roll_abs_weight * clipped_power_term(
                    roll_err,
                    inputs.roll_abs_norm_deg <= 1.0e-6 ? 30.0 : inputs.roll_abs_norm_deg,
                    inputs.roll_abs_power,
                    0.0
                );
            }
        }

        if (inputs.pitch_abs_weight != 0.0) {
            const double pitch_err = std::abs(inputs.curr_pitch_deg) - std::max(0.0, inputs.pitch_abs_deadband_deg);
            if (pitch_err > 0.0) {
                out.pitch_abs_penalty = inputs.pitch_abs_weight * clipped_power_term(
                    pitch_err,
                    inputs.pitch_abs_norm_deg <= 1.0e-6 ? 20.0 : inputs.pitch_abs_norm_deg,
                    inputs.pitch_abs_power,
                    0.0
                );
            }
        }

        if (inputs.yaw_rate_abs_weight != 0.0) {
            const double yaw_rate_err = std::abs(inputs.curr_yaw_rate_deg_s) - std::max(0.0, inputs.yaw_rate_abs_deadband_deg_s);
            if (yaw_rate_err > 0.0) {
                out.yaw_rate_abs_penalty = inputs.yaw_rate_abs_weight * clipped_power_term(
                    yaw_rate_err,
                    inputs.yaw_rate_abs_norm_deg_s <= 1.0e-6 ? 10.0 : inputs.yaw_rate_abs_norm_deg_s,
                    inputs.yaw_rate_abs_power,
                    0.0
                );
            }
        }

        if (inputs.beta_abs_weight != 0.0) {
            const double beta_err = std::abs(inputs.curr_beta_deg) - std::max(0.0, inputs.beta_abs_deadband_deg);
            if (beta_err > 0.0) {
                out.beta_abs_penalty = inputs.beta_abs_weight * clipped_power_term(
                    beta_err,
                    inputs.beta_abs_norm_deg <= 1.0e-6 ? 10.0 : inputs.beta_abs_norm_deg,
                    inputs.beta_abs_power,
                    0.0
                );
            }
        }

        if (inputs.g_deviation_weight != 0.0 && inputs.curr_alt_agl_m > inputs.g_deviation_min_alt_agl_m) {
            const double g_dev_err = std::abs(inputs.curr_g_load - 1.0) - std::max(0.0, inputs.g_deviation_deadband);
            if (g_dev_err > 0.0) {
                out.g_deviation_penalty = inputs.g_deviation_weight * clipped_power_term(
                    g_dev_err,
                    inputs.g_deviation_norm <= 1.0e-6 ? 0.5 : inputs.g_deviation_norm,
                    inputs.g_deviation_power,
                    0.0
                );
            }
        }
    }

    out.speed_reward = inputs.truth_speed_mps * inputs.speed_reward_weight;

    if (inputs.preliftoff && inputs.on_runway_task && inputs.has_runway_cross_m && inputs.runway_width_m > 1.0e-6) {
        const double half_w = 0.5 * inputs.runway_width_m;
        double frac = std::abs(inputs.runway_cross_m) / half_w;
        frac = std::min(frac, 2.0);
        double runway_scale = 1.0;
        if (inputs.runway_centerline_penalty_max_ias_mps > inputs.runway_centerline_penalty_min_ias_mps + 1.0e-6) {
            runway_scale =
                (inputs.curr_ias_mps - inputs.runway_centerline_penalty_min_ias_mps)
                / (inputs.runway_centerline_penalty_max_ias_mps - inputs.runway_centerline_penalty_min_ias_mps);
            runway_scale = clamp_value(runway_scale, 0.0, 1.0);
        }

        if (inputs.runway_centerline_m_penalty_weight != 0.0) {
            const double err_m = std::abs(inputs.runway_cross_m) - std::max(0.0, inputs.runway_centerline_m_deadband_m);
            if (err_m > 0.0) {
                out.runway_centerline_m_penalty = inputs.runway_centerline_m_penalty_weight * clipped_power_term(
                    err_m,
                    inputs.runway_centerline_m_norm_m <= 1.0e-6 ? 5.0 : inputs.runway_centerline_m_norm_m,
                    inputs.runway_centerline_m_power,
                    inputs.runway_centerline_m_clip
                ) * runway_scale;
            }
        }

        if (inputs.runway_centerline_penalty_weight != 0.0) {
            const double safe_frac = clamp_value(inputs.runway_centerline_safe_frac, 0.0, 0.99);
            const double x = std::max(0.0, frac - safe_frac) / std::max(1.0 - safe_frac, 1.0e-6);
            out.runway_centerline_penalty =
                inputs.runway_centerline_penalty_weight
                * std::pow(x, clamp_value(inputs.runway_centerline_penalty_power, 1.0, 8.0))
                * runway_scale;
        }

        if (inputs.runway_centerline_barrier_weight != 0.0) {
            const double clip_frac = clamp_value(inputs.runway_centerline_barrier_clip_frac, 1.0e-6, 0.999999);
            const double frac_c = clamp_value(frac, 0.0, clip_frac);
            const double barrier = -std::log(std::max(1.0e-6, 1.0 - frac_c));
            out.runway_centerline_barrier = inputs.runway_centerline_barrier_weight * barrier * runway_scale;
        }
    }

    if (inputs.has_runway_cross_m) {
        if (inputs.airborne && inputs.departure_centerline_max_alt_agl_m > 0.0 && inputs.curr_alt_agl_m <= inputs.departure_centerline_max_alt_agl_m) {
            if (inputs.departure_centerline_m_penalty_weight != 0.0) {
                const double dep_err_m = std::abs(inputs.runway_cross_m) - std::max(0.0, inputs.departure_centerline_m_deadband_m);
                if (dep_err_m > 0.0) {
                    out.departure_centerline_m_penalty = inputs.departure_centerline_m_penalty_weight * clipped_power_term(
                        dep_err_m,
                        inputs.departure_centerline_m_norm_m <= 1.0e-6 ? 20.0 : inputs.departure_centerline_m_norm_m,
                        inputs.departure_centerline_m_power,
                        inputs.departure_centerline_m_clip
                    );
                }
            }

            if (inputs.departure_centerline_reward_weight != 0.0) {
                const double band_m = std::max(1.0, inputs.departure_centerline_reward_band_m);
                const double center_frac = std::max(0.0, 1.0 - std::abs(inputs.runway_cross_m) / band_m);
                if (center_frac > 0.0) {
                    out.departure_centerline_reward = inputs.departure_centerline_reward_weight * center_frac;
                }
            }

            if (inputs.departure_track_error_weight != 0.0) {
                const double dep_track_err = inputs.ground_track_error_deg - std::max(0.0, inputs.departure_track_error_deadband_deg);
                if (dep_track_err > 0.0) {
                    out.departure_track_error_penalty = inputs.departure_track_error_weight * clipped_power_term(
                        dep_track_err,
                        inputs.departure_track_error_norm_deg <= 1.0e-6 ? 10.0 : inputs.departure_track_error_norm_deg,
                        inputs.departure_track_error_power,
                        inputs.departure_track_error_clip
                    );
                }
            }

            if (inputs.departure_track_reward_weight != 0.0) {
                const double band_deg = std::max(1.0e-6, inputs.departure_track_reward_band_deg);
                const double track_frac = std::max(0.0, 1.0 - inputs.ground_track_error_deg / band_deg);
                if (track_frac > 0.0) {
                    out.departure_track_reward = inputs.departure_track_reward_weight * track_frac;
                }
            }
        }
    }

    if (inputs.alignment_reward_weight != 0.0) {
        if (inputs.on_runway_task && inputs.preliftoff) {
            if (inputs.ils_valid) {
                out.alignment_reward =
                    (1.0 - std::min(std::abs(inputs.ils_loc_dev), 1.0)) * inputs.alignment_reward_weight;
            }
        } else if (inputs.truth_altitude_m >= inputs.mission_alignment_min_alt_m) {
            const double align_factor = std::cos(inputs.heading_error_deg * kPi / 180.0);
            if (align_factor > 0.0) {
                out.alignment_reward = align_factor * inputs.alignment_reward_weight;
            }
        }
    }

    return out;
}
