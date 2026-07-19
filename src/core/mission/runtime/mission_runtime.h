#pragma once

#include <vector>

#include "core/geometry/spatial_query_runtime.h"

struct MissionNavInputs {
#define EF_NAV_INPUT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/mission_nav_inputs.inc"
};

struct MissionNavProducts {
#define EF_NAV_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/mission_nav_products.inc"
};

struct MissionObservationInputs {
    int mode_code = 0;
    double command_code = 0.0;
    double target_heading_deg = 0.0;
    double target_altitude_m = 0.0;
    double target_speed_mps = 0.0;
    double takeoff_procedure_code = 0.0;
    double takeoff_clearance_code = 0.0;
    double takeoff_interval_s = 0.0;
    double runway_slot_code = 0.0;
    double form_offset_x = 0.0;
    double form_offset_y = 0.0;
    double form_offset_z = 0.0;
    double self_role_code = 0.0;
    double self_formation_role_code = 0.0;
    double relative_slot_code = 0.0;
    double reference_relative_slot_code = 0.0;
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
#define EF_STEP_INFO_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/step_info_products.inc"
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
