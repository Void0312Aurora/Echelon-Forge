#include "core/mission/episode/detail/episode_reward_breakdown.h"

#include <cmath>
#include <string>
#include <utility>

#include <nlohmann/json.hpp>

#include "core/mission/episode/detail/mission_command_codec.h"

namespace episode_controller_detail {

namespace {

void add_breakdown_term(nlohmann::json* breakdown, const std::string& name, double value) {
    if (breakdown == nullptr) {
        return;
    }
    const double current = breakdown->contains(name) ? (*breakdown)[name].get<double>() : 0.0;
    (*breakdown)[name] = current + value;
}

void apply_flight_shaping_breakdown_terms(
    const FlightShapingRuntimeProducts& products,
    bool include_roll_stability,
    nlohmann::json* breakdown
) {
    const std::pair<const char*, double> gated_terms[] = {
        {"altitude_progress", products.altitude_progress},
        {"low_alt_descent_penalty", products.low_alt_descent_penalty},
        {"speed_progress", products.speed_progress},
        {"speed_regress", products.speed_regress},
        {"stationary_penalty", products.stationary_penalty},
        {"liftoff_bonus", products.liftoff_bonus},
        {"rotation_reward", products.rotation_reward},
        {"rotation_overpitch_penalty", products.rotation_overpitch_penalty},
        {"gear_up_bonus", products.gear_up_bonus},
        {"heading_error_penalty", products.heading_error_penalty},
        {"heading_hold_bonus", products.heading_hold_bonus},
        {"altitude_error_penalty", products.altitude_error_penalty},
        {"altitude_hold_bonus", products.altitude_hold_bonus},
        {"speed_error_penalty", products.speed_error_penalty},
        {"speed_hold_bonus", products.speed_hold_bonus},
        {"roll_abs_penalty", products.roll_abs_penalty},
        {"pitch_abs_penalty", products.pitch_abs_penalty},
        {"yaw_rate_abs_penalty", products.yaw_rate_abs_penalty},
        {"beta_abs_penalty", products.beta_abs_penalty},
        {"g_deviation_penalty", products.g_deviation_penalty},
        {"runway_centerline_m_penalty", products.runway_centerline_m_penalty},
        {"runway_centerline_penalty", products.runway_centerline_penalty},
        {"runway_centerline_barrier", products.runway_centerline_barrier},
        {"departure_centerline_m_penalty", products.departure_centerline_m_penalty},
        {"departure_centerline_reward", products.departure_centerline_reward},
        {"departure_track_error_penalty", products.departure_track_error_penalty},
        {"departure_track_reward", products.departure_track_reward},
        {"alignment_reward", products.alignment_reward},
    };
    for (const auto& [name, value] : gated_terms) {
        if (value != 0.0) {
            add_breakdown_term(breakdown, name, value);
        }
    }
    add_breakdown_term(breakdown, "speed_reward", products.speed_reward);
    if (include_roll_stability) {
        add_breakdown_term(breakdown, "roll_stability", products.roll_stability);
    }
}

}  // namespace

std::string build_episode_reward_breakdown_json(
    const ExecutionEpisodeRuntimeInputs& runtime_inputs,
    const ExecutionEpisodeRuntimeProducts& products,
    double reward_total,
    bool waypoint_arrived,
    bool had_post_waypoint_transition_before,
    double phase_transition_bonus
) {
    nlohmann::json breakdown = nlohmann::json::object();
    if (!products.execution_step_evaluated) {
        breakdown["tracked_total"] = 0.0;
        breakdown["untracked"] = reward_total;
        breakdown["total"] = reward_total;
        return stable_json_dump(breakdown);
    }

    const auto& execution_step = products.execution_step;
    const auto& safety_terms = execution_step.safety;
    if (double(safety_terms.crash_penalty) != 0.0) {
        add_breakdown_term(&breakdown, "crash_penalty", double(safety_terms.crash_penalty));
        if (double(safety_terms.nan_guard_marker) != 0.0) {
            add_breakdown_term(&breakdown, "nan_guard", double(safety_terms.nan_guard_marker));
        }
    } else {
        add_breakdown_term(&breakdown, "survival", double(safety_terms.survival));
        if (products.flight_shaping_evaluated) {
            apply_flight_shaping_breakdown_terms(
                products.flight_shaping,
                runtime_inputs.include_roll_stability,
                &breakdown
            );
        }
        if (double(safety_terms.stall_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "stall_penalty", double(safety_terms.stall_penalty));
        }
        if (double(safety_terms.overload_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "overload_penalty", double(safety_terms.overload_penalty));
        }
        if (double(safety_terms.failfast_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "failfast_penalty", double(safety_terms.failfast_penalty));
        }
        if (double(safety_terms.gear_collapse_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "gear_collapse_penalty", double(safety_terms.gear_collapse_penalty));
        }
        if (double(safety_terms.off_runway_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "off_runway_penalty", double(safety_terms.off_runway_penalty));
        }
        if (double(safety_terms.gear_stress_penalty) != 0.0) {
            add_breakdown_term(&breakdown, "gear_stress_penalty", double(safety_terms.gear_stress_penalty));
        }
        if (double(safety_terms.off_runway_terminate_penalty) != 0.0) {
            add_breakdown_term(
                &breakdown,
                "off_runway_terminate_penalty",
                double(safety_terms.off_runway_terminate_penalty)
            );
        }

        if (runtime_inputs.execution_step.has_approach && execution_step.approach_evaluated) {
            const auto& approach_inputs = runtime_inputs.execution_step.approach;
            const auto& approach_terms = execution_step.approach;
            if (double(approach_terms.approach_localizer) != 0.0) {
                add_breakdown_term(&breakdown, "approach_localizer", double(approach_terms.approach_localizer));
            }
            if (double(approach_inputs.localizer_improve_weight) != 0.0 && bool(approach_inputs.has_prev_loc)) {
                add_breakdown_term(
                    &breakdown,
                    "approach_localizer_improve",
                    double(approach_terms.approach_localizer_improve)
                );
            }
            if (double(approach_terms.approach_glideslope) != 0.0) {
                add_breakdown_term(&breakdown, "approach_glideslope", double(approach_terms.approach_glideslope));
            }
            if (double(approach_inputs.glideslope_improve_weight) != 0.0 && bool(approach_inputs.has_prev_gs)) {
                add_breakdown_term(
                    &breakdown,
                    "approach_glideslope_improve",
                    double(approach_terms.approach_glideslope_improve)
                );
            }
            if (
                double(approach_inputs.dme_progress_weight) != 0.0 &&
                bool(approach_inputs.has_prev_dme) &&
                std::isfinite(double(approach_inputs.ils_dme_m))
            ) {
                add_breakdown_term(
                    &breakdown,
                    "approach_dme_progress",
                    double(approach_terms.approach_dme_progress)
                );
            }
            if (double(approach_terms.approach_capture_bonus) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "approach_capture_bonus",
                    double(approach_terms.approach_capture_bonus)
                );
            }
            if (double(approach_terms.landing_sink_rate_penalty) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "landing_sink_rate_penalty",
                    double(approach_terms.landing_sink_rate_penalty)
                );
            }
        }

        if (runtime_inputs.execution_step.has_waypoint && execution_step.waypoint_evaluated) {
            const auto& waypoint_inputs = runtime_inputs.execution_step.waypoint;
            const auto& waypoint_terms = execution_step.waypoint;
            if (double(waypoint_inputs.progress_weight) != 0.0 && bool(waypoint_inputs.has_prev_dist)) {
                add_breakdown_term(
                    &breakdown,
                    "waypoint_progress",
                    double(waypoint_terms.waypoint_progress)
                );
            }
            if (double(waypoint_inputs.distance_weight) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "waypoint_distance",
                    double(waypoint_terms.waypoint_distance)
                );
            }
            if (double(waypoint_terms.waypoint_cross_track) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "waypoint_cross_track",
                    double(waypoint_terms.waypoint_cross_track)
                );
            }
            if (double(waypoint_terms.waypoint_proximity) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "waypoint_proximity",
                    double(waypoint_terms.waypoint_proximity)
                );
            }
            if (waypoint_arrived) {
                add_breakdown_term(
                    &breakdown,
                    "waypoint_reached_bonus",
                    double(waypoint_terms.waypoint_reached_bonus)
                );
                if (
                    !had_post_waypoint_transition_before &&
                    execution_step.waypoint_episode_success
                ) {
                    add_breakdown_term(
                        &breakdown,
                        "waypoint_success_bonus",
                        double(execution_step.waypoint_episode_success_bonus)
                    );
                }
            }
        }

        if (phase_transition_bonus != 0.0) {
            add_breakdown_term(&breakdown, "phase_transition_bonus", phase_transition_bonus);
        }

        if (execution_step.objective_evaluated && execution_step.matched_objective_index >= 0) {
            if (double(execution_step.objective.success_runway_cross_penalty) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "success_runway_cross_penalty",
                    double(execution_step.objective.success_runway_cross_penalty)
                );
            }
            if (double(execution_step.objective.success_ground_track_error_penalty) != 0.0) {
                add_breakdown_term(
                    &breakdown,
                    "success_ground_track_error_penalty",
                    double(execution_step.objective.success_ground_track_error_penalty)
                );
            }
            add_breakdown_term(
                &breakdown,
                "objective_bonus",
                double(execution_step.objective.objective_bonus)
            );
        }
    }

    double tracked_total = 0.0;
    for (auto it = breakdown.begin(); it != breakdown.end(); ++it) {
        if (!it.value().is_number()) {
            continue;
        }
        tracked_total += it.value().get<double>();
    }
    breakdown["tracked_total"] = tracked_total;
    breakdown["untracked"] = reward_total - tracked_total;
    breakdown["total"] = reward_total;
    return stable_json_dump(breakdown);
}

}  // namespace episode_controller_detail
