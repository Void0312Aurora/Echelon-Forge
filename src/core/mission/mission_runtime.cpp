#include "core/mission/mission_runtime.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace {

enum class MissionObservationMode {
    Basic = 0,
    NavV1 = 1,
    NavV2 = 2,
};

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

struct MissionKinematics {
    double own_heading_deg = 0.0;
    double ground_track_deg = 0.0;
    double reference_speed_mps = 0.0;
};

MissionKinematics resolve_mission_kinematics(const MissionNavInputs& inputs) {
    MissionKinematics out{};
    out.own_heading_deg = inputs.truth_heading_deg;
    out.ground_track_deg = inputs.truth_heading_deg;
    out.reference_speed_mps = inputs.truth_speed_mps;

    if (std::isfinite(inputs.inst_heading_deg)) {
        out.own_heading_deg = inputs.inst_heading_deg;
    }
    if (std::isfinite(inputs.inst_ground_track_deg)) {
        out.ground_track_deg = inputs.inst_ground_track_deg;
    }
    if (std::isfinite(inputs.inst_ias_mps) && inputs.inst_ias_mps > 1.0) {
        out.reference_speed_mps = inputs.inst_ias_mps;
    }

    if (std::abs(wrap_angle_deg(out.ground_track_deg - out.own_heading_deg)) > 85.0
        && out.reference_speed_mps > 80.0) {
        out.ground_track_deg = out.own_heading_deg;
    }
    return out;
}

MissionObservationMode parse_mission_observation_mode(int mode_code) {
    switch (mode_code) {
        case 0:
            return MissionObservationMode::Basic;
        case 1:
            return MissionObservationMode::NavV1;
        case 2:
            return MissionObservationMode::NavV2;
        default:
            throw std::invalid_argument("Unknown mission observation mode code");
    }
}

size_t mission_observation_nav_fields(MissionObservationMode mode) {
    switch (mode) {
        case MissionObservationMode::Basic:
            return 0;
        case MissionObservationMode::NavV1:
            return 7;
        case MissionObservationMode::NavV2:
            return 10;
        default:
            return 0;
    }
}

}  // namespace

double resolve_ground_track_deg(double fallback_heading_deg, double inst_ground_track_deg) {
    return std::isfinite(inst_ground_track_deg) ? inst_ground_track_deg : fallback_heading_deg;
}

double compute_ground_track_error_deg(double target_heading_deg, double fallback_heading_deg, double inst_ground_track_deg) {
    const double ground_track_deg = resolve_ground_track_deg(fallback_heading_deg, inst_ground_track_deg);
    return std::abs(wrap_angle_deg(target_heading_deg - ground_track_deg));
}

double compute_command_tracking_error_deg(
    double target_heading_deg,
    double truth_heading_deg,
    int command_code,
    double inst_ground_track_deg
) {
    double reference_deg = truth_heading_deg;
    if (command_code == 3 && std::isfinite(inst_ground_track_deg)) {
        reference_deg = inst_ground_track_deg;
    }
    return std::abs(wrap_angle_deg(target_heading_deg - reference_deg));
}

MissionNavProducts compute_waypoint_mission_nav(
    const SpatialRouteQueryResult& route_result,
    const MissionNavInputs& inputs
) {
    MissionNavProducts out{};
    if (!route_result.valid) {
        return out;
    }

    const MissionKinematics kin = resolve_mission_kinematics(inputs);
    const double cdi_full_scale_m = std::max(1.0, inputs.cdi_full_scale_m);
    const double distance_to_turn_m = std::isfinite(route_result.distance_to_turn_m)
        ? route_result.distance_to_turn_m
        : route_result.reward_dtg_m;

    out.valid = true;
    out.active_wp_idx = static_cast<double>(route_result.idx);
    out.total_wps = static_cast<double>(route_result.count);
    out.selected_steerpoint = static_cast<double>(route_result.idx + 1);
    out.steerpoint_mode_code = route_result.waypoint_mode == "flyover" ? 1.0 : 0.0;
    out.dist_m = route_result.dist_m;
    out.xtk_m = route_result.reward_xtk_m;
    out.dtg_m = route_result.reward_dtg_m;
    out.direct_bearing_deg = route_result.direct_to_track_deg;
    out.desired_leg_track_deg = route_result.reward_desired_track_deg;
    out.bearing_rel_deg = wrap_angle_deg(route_result.direct_to_track_deg - kin.own_heading_deg);
    out.altitude_delta_m = inputs.waypoint_altitude_m - inputs.own_altitude_m;
    out.cdi_norm = clamp_value(route_result.reward_xtk_m / cdi_full_scale_m, -1.0, 1.0);
    out.track_angle_error_deg = wrap_angle_deg(route_result.reward_desired_track_deg - kin.ground_track_deg);
    out.next_turn_deg = route_result.next_turn_deg;
    out.distance_to_turn_m = distance_to_turn_m;
    out.own_heading_deg = kin.own_heading_deg;
    out.ground_track_deg = kin.ground_track_deg;
    out.reference_speed_mps = kin.reference_speed_mps;
    return out;
}

MissionObservationProducts compute_mission_observation(const MissionObservationInputs& inputs) {
    MissionObservationProducts out{};
    const MissionObservationMode mode = parse_mission_observation_mode(inputs.mode_code);
    const size_t nav_fields = mission_observation_nav_fields(mode);

    out.valid = true;
    out.mode_code = inputs.mode_code;
    out.values.reserve(static_cast<size_t>(4) + nav_fields);
    out.values.push_back(static_cast<float>(inputs.command_code));
    out.values.push_back(static_cast<float>(inputs.target_heading_deg));
    out.values.push_back(static_cast<float>(inputs.target_altitude_m));
    out.values.push_back(static_cast<float>(inputs.target_speed_mps));

    if (mode == MissionObservationMode::Basic) {
        return out;
    }

    if (inputs.has_route_guidance && inputs.route_guidance.valid) {
        out.nav = compute_waypoint_mission_nav(inputs.route_guidance, inputs.nav_inputs);
        out.nav_valid = out.nav.valid;
    }

    if (!out.nav_valid) {
        out.values.insert(out.values.end(), nav_fields, 0.0f);
        return out;
    }

    if (mode == MissionObservationMode::NavV1) {
        out.values.push_back(static_cast<float>(out.nav.active_wp_idx));
        out.values.push_back(static_cast<float>(out.nav.total_wps));
        out.values.push_back(static_cast<float>(out.nav.dist_m));
        out.values.push_back(static_cast<float>(out.nav.xtk_m));
        out.values.push_back(static_cast<float>(out.nav.dtg_m));
        out.values.push_back(static_cast<float>(out.nav.direct_bearing_deg));
        out.values.push_back(static_cast<float>(out.nav.desired_leg_track_deg));
        return out;
    }

    out.values.push_back(static_cast<float>(out.nav.selected_steerpoint));
    out.values.push_back(static_cast<float>(out.nav.steerpoint_mode_code));
    out.values.push_back(static_cast<float>(out.nav.dist_m));
    out.values.push_back(static_cast<float>(out.nav.bearing_rel_deg));
    out.values.push_back(static_cast<float>(out.nav.altitude_delta_m));
    out.values.push_back(static_cast<float>(out.nav.cdi_norm));
    out.values.push_back(static_cast<float>(out.nav.track_angle_error_deg));
    out.values.push_back(static_cast<float>(out.nav.dtg_m));
    out.values.push_back(static_cast<float>(out.nav.next_turn_deg));
    out.values.push_back(static_cast<float>(out.nav.distance_to_turn_m));
    return out;
}

StepInfoProducts compute_step_info_runtime(const StepInfoInputs& inputs) {
    StepInfoProducts out{};
    out.valid = true;
    out.on_runway = inputs.on_runway;
    out.gear_collapsed = inputs.gear_collapsed;
    out.gear_stress = inputs.gear_stress;
    out.on_ground = inputs.alt_agl_m <= inputs.on_ground_alt_threshold_m;
    out.airborne = inputs.alt_agl_m >= inputs.airborne_alt_threshold_m;
    out.preliftoff = !out.airborne;

    if (
        inputs.has_runway_frame
        && inputs.runway_frame.valid
        && inputs.runway_frame.length_m > 1.0
        && inputs.runway_frame.width_m > 1.0
    ) {
        out.has_runway_frame = true;
        out.runway_cross_m = inputs.runway_frame.cross_m;
        out.runway_along_m = inputs.runway_frame.along_m;
        out.on_runway_geom =
            out.preliftoff
            && std::abs(inputs.runway_frame.cross_m) <= (0.5 * inputs.runway_frame.width_m + inputs.runway_width_margin_m)
            && std::abs(inputs.runway_frame.along_m) <= (0.5 * inputs.runway_frame.length_m + inputs.runway_length_margin_m);
    }
    return out;
}
