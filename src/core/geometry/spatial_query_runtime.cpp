#include "core/geometry/spatial_query_runtime.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>

namespace {

double clamp_value(double value, double lo, double hi) {
    return std::min(std::max(value, lo), hi);
}

double wrap_angle_deg(double angle_deg) {
    double wrapped = std::fmod(angle_deg + 180.0, 360.0);
    if (wrapped < 0.0) {
        wrapped += 360.0;
    }
    return wrapped - 180.0;
}

double bearing_to_deg(double dx, double dy) {
    double angle = std::atan2(dx, dy) * 180.0 / M_PI;
    angle = std::fmod(angle, 360.0);
    if (angle < 0.0) {
        angle += 360.0;
    }
    return angle;
}

std::string normalize_waypoint_mode(const std::string& raw_mode) {
    std::string mode;
    mode.reserve(raw_mode.size());
    for (char ch : raw_mode) {
        if (ch == '-' || ch == ' ') {
            continue;
        }
        mode.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    if (mode == "flyover" || mode == "overfly") {
        return "flyover";
    }
    return "flyby";
}

double turn_lead_distance_m(double turn_angle_deg, double speed_mps, double bank_limit_deg) {
    double turn_abs_deg = std::abs(turn_angle_deg);
    if (turn_abs_deg <= 1.0e-6) {
        return 0.0;
    }
    double bank_lim = clamp_value(bank_limit_deg, 5.0, 70.0);
    double tanb = std::tan(bank_lim * M_PI / 180.0);
    if (std::abs(tanb) <= 1.0e-6) {
        return 0.0;
    }
    double v = std::max(30.0, speed_mps);
    double turn_radius = (v * v) / (9.80665 * std::abs(tanb));
    double half_turn_rad = 0.5 * std::min(M_PI - 1.0e-3, turn_abs_deg * M_PI / 180.0);
    return std::max(0.0, turn_radius * std::tan(half_turn_rad));
}

}  // namespace

void CompiledScenarioGeometry::clear() {
    clear_runways();
    clear_route();
}

void CompiledScenarioGeometry::clear_runways() {
    runways_.clear();
}

void CompiledScenarioGeometry::add_runway(const SpatialRunwayDefinition& runway) {
    runways_.push_back(runway);
}

void CompiledScenarioGeometry::clear_route() {
    route_waypoints_.clear();
    route_leg_origin_x_m_ = 0.0;
    route_leg_origin_y_m_ = 0.0;
}

void CompiledScenarioGeometry::set_route_leg_origin(double x_m, double y_m) {
    route_leg_origin_x_m_ = x_m;
    route_leg_origin_y_m_ = y_m;
}

void CompiledScenarioGeometry::add_route_waypoint(const SpatialRouteWaypoint& waypoint) {
    SpatialRouteWaypoint next = waypoint;
    next.waypoint_mode = normalize_waypoint_mode(next.waypoint_mode);
    route_waypoints_.push_back(next);
}

std::size_t CompiledScenarioGeometry::runway_count() const {
    return runways_.size();
}

std::size_t CompiledScenarioGeometry::route_waypoint_count() const {
    return route_waypoints_.size();
}

SpatialRunwayFrameResult CompiledScenarioGeometry::query_runway_local_frame(double x_m, double y_m) const {
    SpatialRunwayFrameResult out{};
    if (runways_.empty()) {
        return out;
    }

    const SpatialRunwayDefinition* best = nullptr;
    double best_d2 = std::numeric_limits<double>::infinity();
    for (const auto& runway : runways_) {
        double dx = x_m - runway.center_x_m;
        double dy = y_m - runway.center_y_m;
        double d2 = dx * dx + dy * dy;
        if (d2 < best_d2) {
            best_d2 = d2;
            best = &runway;
        }
    }
    if (best == nullptr) {
        return out;
    }

    double h_rad = best->heading_deg * M_PI / 180.0;
    double fwd_x = std::sin(h_rad);
    double fwd_y = std::cos(h_rad);
    double right_x = std::cos(h_rad);
    double right_y = -std::sin(h_rad);

    double dx = x_m - best->center_x_m;
    double dy = y_m - best->center_y_m;

    out.runway_id = best->runway_id;
    out.along_m = dx * fwd_x + dy * fwd_y;
    out.cross_m = dx * right_x + dy * right_y;
    out.length_m = best->length_m;
    out.width_m = best->width_m;
    out.heading_deg = best->heading_deg;
    out.valid = (best->length_m > 1.0 && best->width_m > 1.0);
    return out;
}

SpatialILSResult CompiledScenarioGeometry::query_ils(
    double x_m,
    double y_m,
    double alt_m,
    double threshold_crossing_height_m
) const {
    SpatialILSResult out{};
    if (runways_.empty()) {
        return out;
    }

    const SpatialRunwayDefinition* best = nullptr;
    double best_d2 = std::numeric_limits<double>::infinity();
    for (const auto& runway : runways_) {
        double dx = x_m - runway.center_x_m;
        double dy = y_m - runway.center_y_m;
        double d2 = dx * dx + dy * dy;
        if (d2 < best_d2) {
            best_d2 = d2;
            best = &runway;
        }
    }
    if (best == nullptr) {
        return out;
    }

    double h_rad = best->heading_deg * M_PI / 180.0;
    double fwd_x = std::sin(h_rad);
    double fwd_y = std::cos(h_rad);
    double right_x = std::cos(h_rad);
    double right_y = -std::sin(h_rad);

    double loc_x = best->center_x_m + fwd_x * (0.5 * best->length_m);
    double loc_y = best->center_y_m + fwd_y * (0.5 * best->length_m);
    double dx = x_m - loc_x;
    double dy = y_m - loc_y;

    double along = -(dx * fwd_x + dy * fwd_y);
    double cross = dx * right_x + dy * right_y;
    double along_abs = std::max(std::abs(along), 1.0);
    double loc_angle_deg = std::atan2(cross, along_abs) * 180.0 / M_PI;

    double thr_dx = x_m - best->threshold_x_m;
    double thr_dy = y_m - best->threshold_y_m;
    double approach_dist_m = -(thr_dx * fwd_x + thr_dy * fwd_y);
    double dme_m = std::sqrt(thr_dx * thr_dx + thr_dy * thr_dy + (alt_m - best->elevation_m) * (alt_m - best->elevation_m));

    double gs_ref_alt_m = best->elevation_m + std::max(0.0, threshold_crossing_height_m);
    double gs_dev = 0.0;
    if (approach_dist_m > 1.0) {
        double gs_angle_deg = std::atan2(alt_m - gs_ref_alt_m, approach_dist_m) * 180.0 / M_PI;
        gs_dev = clamp_value(
            (gs_angle_deg - best->glide_slope_deg) / std::max(0.1, best->glideslope_max_deg),
            -1.0,
            1.0
        );
    }

    out.runway_id = best->runway_id;
    out.heading_deg = best->heading_deg;
    out.loc_dev = clamp_value(loc_angle_deg / std::max(0.1, best->localizer_max_deg), -1.0, 1.0);
    out.gs_dev = gs_dev;
    out.dme_m = dme_m;
    out.approach_dist_m = approach_dist_m;
    out.valid = (dme_m <= best->range_m);
    return out;
}

SpatialRouteQueryResult CompiledScenarioGeometry::query_route_guidance(const SpatialRouteQueryOptions& options) const {
    SpatialRouteQueryResult out{};
    if (route_waypoints_.empty()) {
        return out;
    }

    int idx = std::clamp(options.waypoint_index, 0, static_cast<int>(route_waypoints_.size()) - 1);
    const auto& wp = route_waypoints_[static_cast<std::size_t>(idx)];

    double sx = route_leg_origin_x_m_;
    double sy = route_leg_origin_y_m_;
    if (idx > 0) {
        const auto& prev = route_waypoints_[static_cast<std::size_t>(idx - 1)];
        sx = prev.x_m;
        sy = prev.y_m;
    }

    double ex = wp.x_m;
    double ey = wp.y_m;
    double lx = ex - sx;
    double ly = ey - sy;
    double leg_len = std::hypot(lx, ly);

    double dx = ex - options.own_x_m;
    double dy = ey - options.own_y_m;
    double dist_m = std::hypot(dx, dy);
    double direct_to_track_deg = bearing_to_deg(dx, dy);
    double desired_track_deg = direct_to_track_deg;
    double xtk_m = 0.0;
    double along_m = 0.0;
    double dtg_m = dist_m;

    if (leg_len > 1.0e-6) {
        desired_track_deg = bearing_to_deg(lx, ly);
        double ux = lx / leg_len;
        double uy = ly / leg_len;
        double rx = uy;
        double ry = -ux;
        double px = options.own_x_m - sx;
        double py = options.own_y_m - sy;
        xtk_m = px * rx + py * ry;
        along_m = px * ux + py * uy;
        dtg_m = std::max(0.0, leg_len - along_m);
    }

    double speed_mps = std::isfinite(options.own_speed_mps) ? options.own_speed_mps : 0.0;
    double lookahead_m = options.base_lookahead_m;
    if (std::isfinite(speed_mps) && speed_mps > 1.0) {
        lookahead_m = clamp_value(speed_mps * 8.0, 500.0, 5000.0);
    }
    lookahead_m = std::max(200.0, lookahead_m);

    double max_int = options.lnav_max_intercept_deg;
    double capture_max_int = std::max(max_int, options.lnav_capture_max_intercept_deg);
    double waypoint_radius_m = std::max(1.0, wp.radius_m);
    double capture_xtrack_m = options.lnav_capture_xtrack_m;
    if (capture_xtrack_m <= 0.0) {
        capture_xtrack_m = std::max(2.0 * waypoint_radius_m, std::min(8000.0, 0.35 * std::max(1.0, leg_len)));
    }
    capture_xtrack_m = std::max(waypoint_radius_m, capture_xtrack_m);

    double capture_course_err_deg = options.lnav_capture_course_error_deg;
    bool final_leg = idx >= (static_cast<int>(route_waypoints_.size()) - 1);
    bool passed_fix = along_m >= leg_len;

    double flyover_capture_window_m = options.lnav_flyover_capture_window_m;
    if (flyover_capture_window_m <= 0.0) {
        flyover_capture_window_m = std::max(2.0 * waypoint_radius_m, std::min(5000.0, 0.30 * std::max(1.0, leg_len)));
    }
    flyover_capture_window_m = std::max(waypoint_radius_m, flyover_capture_window_m);

    bool before_leg = along_m < -0.25 * lookahead_m;
    bool far_off_course = std::abs(xtk_m) > capture_xtrack_m;
    bool large_to_from_angle = std::abs(wrap_angle_deg(direct_to_track_deg - desired_track_deg)) > capture_course_err_deg;
    bool near_flyover_terminal = (
        wp.waypoint_mode == "flyover" &&
        (dist_m <= flyover_capture_window_m || along_m >= std::max(0.0, leg_len - flyover_capture_window_m))
    );
    bool missed_flyby_recovery = (wp.waypoint_mode == "flyby" && passed_fix);
    bool use_direct_to = (
        (final_leg && options.lnav_direct_to_final_fix) ||
        before_leg ||
        (far_off_course && large_to_from_angle) ||
        near_flyover_terminal ||
        (wp.waypoint_mode == "flyover" && passed_fix) ||
        missed_flyby_recovery
    );
    bool direct_to_fix_guidance = (
        use_direct_to &&
        ((final_leg && options.lnav_direct_to_final_fix) || wp.waypoint_mode == "flyover" || missed_flyby_recovery)
    );

    double cmd_track_deg = desired_track_deg;
    if (use_direct_to) {
        if (direct_to_fix_guidance) {
            cmd_track_deg = direct_to_track_deg;
        } else {
            double capture_delta_deg = wrap_angle_deg(direct_to_track_deg - desired_track_deg);
            capture_delta_deg = clamp_value(capture_delta_deg, -capture_max_int, capture_max_int);
            cmd_track_deg = std::fmod(desired_track_deg + capture_delta_deg + 360.0, 360.0);
        }
    } else {
        double intercept_rad = std::atan2(-xtk_m, lookahead_m);
        double intercept_deg = intercept_rad * 180.0 / M_PI;
        if (max_int > 0.0) {
            intercept_deg = clamp_value(intercept_deg, -max_int, max_int);
        }
        cmd_track_deg = std::fmod(desired_track_deg + intercept_deg + 360.0, 360.0);
    }

    double reward_desired_track_deg = direct_to_fix_guidance ? direct_to_track_deg : desired_track_deg;
    double reward_xtk_m = direct_to_fix_guidance ? 0.0 : xtk_m;
    double reward_dtg_m = direct_to_fix_guidance ? dist_m : dtg_m;

    double next_turn_deg = 0.0;
    double next_turn_abs_deg = 0.0;
    double prev_turn_abs_deg = 0.0;
    double lead_turn_m = 0.0;
    double distance_to_turn_m = direct_to_fix_guidance ? dist_m : dtg_m;
    double dist_to_next_turn_start_m = distance_to_turn_m;
    double distance_from_prev_turn_m = std::max(0.0, along_m);
    double sequence_gate_scale = options.lnav_sequence_gate_scale;
    double sequence_gate_min_m = options.lnav_sequence_gate_min_m > 0.0 ? options.lnav_sequence_gate_min_m : waypoint_radius_m;
    double default_seq_gate_max = std::max(2.5 * waypoint_radius_m, waypoint_radius_m + 1500.0);
    double sequence_gate_max_m = options.lnav_sequence_gate_max_m > 0.0 ? options.lnav_sequence_gate_max_m : default_seq_gate_max;
    double sequence_gate_m = waypoint_radius_m;

    if (idx < static_cast<int>(route_waypoints_.size()) - 1) {
        const auto& next_wp = route_waypoints_[static_cast<std::size_t>(idx + 1)];
        double next_dx = next_wp.x_m - ex;
        double next_dy = next_wp.y_m - ey;
        if ((next_dx * next_dx + next_dy * next_dy) > 1.0e-9) {
            double cur_track_deg = bearing_to_deg(lx, ly);
            double next_track_deg = bearing_to_deg(next_dx, next_dy);
            next_turn_deg = wrap_angle_deg(next_track_deg - desired_track_deg);
            next_turn_abs_deg = std::abs(wrap_angle_deg(next_track_deg - cur_track_deg));
            lead_turn_m = turn_lead_distance_m(next_turn_abs_deg, std::max(30.0, speed_mps), options.lnav_bank_limit_deg);
            sequence_gate_m = std::max(
                sequence_gate_min_m,
                std::min(sequence_gate_max_m, waypoint_radius_m + sequence_gate_scale * std::max(0.0, lead_turn_m))
            );
            dist_to_next_turn_start_m = std::max(0.0, dtg_m - lead_turn_m);
            if (!direct_to_fix_guidance) {
                distance_to_turn_m = dist_to_next_turn_start_m;
            }
        }
    }

    if (idx > 0) {
        double psx = route_leg_origin_x_m_;
        double psy = route_leg_origin_y_m_;
        if (idx > 1) {
            const auto& prev_prev = route_waypoints_[static_cast<std::size_t>(idx - 2)];
            psx = prev_prev.x_m;
            psy = prev_prev.y_m;
        }
        double prev_lx = sx - psx;
        double prev_ly = sy - psy;
        if ((prev_lx * prev_lx + prev_ly * prev_ly) > 1.0e-9 && (lx * lx + ly * ly) > 1.0e-9) {
            double prev_track_deg = bearing_to_deg(prev_lx, prev_ly);
            double cur_track_deg = bearing_to_deg(lx, ly);
            prev_turn_abs_deg = std::abs(wrap_angle_deg(cur_track_deg - prev_track_deg));
        }
    }

    out.valid = true;
    out.idx = idx;
    out.count = static_cast<int>(route_waypoints_.size());
    out.waypoint_mode = wp.waypoint_mode;
    out.sx_m = sx;
    out.sy_m = sy;
    out.ex_m = ex;
    out.ey_m = ey;
    out.lx_m = lx;
    out.ly_m = ly;
    out.leg_len_m = leg_len;
    out.dist_m = dist_m;
    out.direct_to_track_deg = direct_to_track_deg;
    out.desired_track_deg = desired_track_deg;
    out.reward_desired_track_deg = reward_desired_track_deg;
    out.xtk_m = xtk_m;
    out.reward_xtk_m = reward_xtk_m;
    out.along_m = along_m;
    out.dtg_m = dtg_m;
    out.reward_dtg_m = reward_dtg_m;
    out.waypoint_radius_m = waypoint_radius_m;
    out.cmd_track_deg = cmd_track_deg;
    out.lookahead_m = lookahead_m;
    out.next_turn_deg = next_turn_deg;
    out.next_turn_abs_deg = next_turn_abs_deg;
    out.prev_turn_abs_deg = prev_turn_abs_deg;
    out.lead_turn_m = lead_turn_m;
    out.sequence_gate_m = sequence_gate_m;
    out.distance_to_turn_m = distance_to_turn_m;
    out.dist_to_next_turn_start_m = dist_to_next_turn_start_m;
    out.distance_from_prev_turn_m = distance_from_prev_turn_m;
    out.use_direct_to = use_direct_to;
    out.direct_to_fix_guidance = direct_to_fix_guidance;
    out.final_leg = final_leg;
    out.passed_fix = passed_fix;
    return out;
}
