#pragma once

#include <vector>

#include "core/geometry/spatial_query_runtime.h"

struct MissionNavInputs {
    double own_altitude_m = 0.0;
    double truth_heading_deg = 0.0;
    double truth_speed_mps = 0.0;
    double inst_heading_deg = 0.0;
    double inst_ground_track_deg = 0.0;
    double inst_ias_mps = 0.0;
    double waypoint_altitude_m = 0.0;
    double cdi_full_scale_m = 1500.0;
};

struct MissionNavProducts {
    bool valid = false;
    double active_wp_idx = 0.0;
    double total_wps = 0.0;
    double selected_steerpoint = 0.0;
    double steerpoint_mode_code = 0.0;
    double dist_m = 0.0;
    double xtk_m = 0.0;
    double dtg_m = 0.0;
    double direct_bearing_deg = 0.0;
    double desired_leg_track_deg = 0.0;
    double bearing_rel_deg = 0.0;
    double altitude_delta_m = 0.0;
    double cdi_norm = 0.0;
    double track_angle_error_deg = 0.0;
    double next_turn_deg = 0.0;
    double distance_to_turn_m = 0.0;
    double own_heading_deg = 0.0;
    double ground_track_deg = 0.0;
    double reference_speed_mps = 0.0;
};

struct MissionObservationInputs {
    int mode_code = 0;
    double command_code = 0.0;
    double target_heading_deg = 0.0;
    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    bool has_route_guidance = false;
    SpatialRouteQueryResult route_guidance;
    MissionNavInputs nav_inputs;
};

struct MissionObservationProducts {
    bool valid = false;
    int mode_code = 0;
    bool nav_valid = false;
    MissionNavProducts nav;
    std::vector<float> values;
};

struct StepInfoInputs {
    bool on_runway = true;
    bool gear_collapsed = false;
    double gear_stress = 0.0;
    double alt_agl_m = 0.0;
    double on_ground_alt_threshold_m = 2.5;
    double airborne_alt_threshold_m = 5.0;
    bool has_runway_frame = false;
    SpatialRunwayFrameResult runway_frame;
    double runway_width_margin_m = 2.0;
    double runway_length_margin_m = 0.0;
};

struct StepInfoProducts {
    bool valid = false;
    bool on_runway = true;
    bool gear_collapsed = false;
    double gear_stress = 0.0;
    bool on_ground = false;
    bool airborne = false;
    bool preliftoff = true;
    bool has_runway_frame = false;
    bool on_runway_geom = false;
    double runway_cross_m = 0.0;
    double runway_along_m = 0.0;
};

double resolve_ground_track_deg(double fallback_heading_deg, double inst_ground_track_deg);
double compute_ground_track_error_deg(double target_heading_deg, double fallback_heading_deg, double inst_ground_track_deg);
double compute_command_tracking_error_deg(
    double target_heading_deg,
    double truth_heading_deg,
    int command_code,
    double inst_ground_track_deg
);
MissionNavProducts compute_waypoint_mission_nav(
    const SpatialRouteQueryResult& route_result,
    const MissionNavInputs& inputs
);
MissionObservationProducts compute_mission_observation(const MissionObservationInputs& inputs);
StepInfoProducts compute_step_info_runtime(const StepInfoInputs& inputs);
