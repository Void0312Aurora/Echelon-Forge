#pragma once

#include <string>
#include <vector>

struct SpatialRunwayDefinition {
    int runway_id = -1;
    std::string name;
    double center_x_m = 0.0;
    double center_y_m = 0.0;
    double threshold_x_m = 0.0;
    double threshold_y_m = 0.0;
    double heading_deg = 0.0;
    double length_m = 0.0;
    double width_m = 0.0;
    double elevation_m = 0.0;
    double glide_slope_deg = 3.0;
    double localizer_max_deg = 10.0;
    double glideslope_max_deg = 3.0;
    double range_m = 30000.0;
};

struct SpatialRouteWaypoint {
    double x_m = 0.0;
    double y_m = 0.0;
    double z_m = 0.0;
    double radius_m = 500.0;
    double altitude_m = 0.0;
    double speed_mps = 0.0;
    std::string waypoint_mode = "flyby";
};

struct SpatialRunwayFrameResult {
    bool valid = false;
    int runway_id = -1;
    double along_m = 0.0;
    double cross_m = 0.0;
    double length_m = 0.0;
    double width_m = 0.0;
    double heading_deg = 0.0;
};

struct SpatialILSResult {
    bool valid = false;
    int runway_id = -1;
    double loc_dev = 0.0;
    double gs_dev = 0.0;
    double dme_m = 0.0;
    double approach_dist_m = 0.0;
    double heading_deg = 0.0;
};

struct SpatialRouteQueryOptions {
    int waypoint_index = 0;
    double own_x_m = 0.0;
    double own_y_m = 0.0;
    double own_speed_mps = 0.0;
    double base_lookahead_m = 1500.0;
    double lnav_max_intercept_deg = 25.0;
    double lnav_capture_max_intercept_deg = 45.0;
    double lnav_capture_xtrack_m = 0.0;
    double lnav_capture_course_error_deg = 45.0;
    bool lnav_direct_to_final_fix = true;
    double lnav_flyover_capture_window_m = 0.0;
    double lnav_bank_limit_deg = 30.0;
    double lnav_sequence_gate_scale = 0.35;
    double lnav_sequence_gate_min_m = 0.0;
    double lnav_sequence_gate_max_m = 0.0;
};

struct SpatialRouteQueryResult {
    bool valid = false;
    int idx = 0;
    int count = 0;
    std::string waypoint_mode = "flyby";
    double sx_m = 0.0;
    double sy_m = 0.0;
    double ex_m = 0.0;
    double ey_m = 0.0;
    double lx_m = 0.0;
    double ly_m = 0.0;
    double leg_len_m = 0.0;
    double dist_m = 0.0;
    double direct_to_track_deg = 0.0;
    double desired_track_deg = 0.0;
    double reward_desired_track_deg = 0.0;
    double xtk_m = 0.0;
    double reward_xtk_m = 0.0;
    double along_m = 0.0;
    double dtg_m = 0.0;
    double reward_dtg_m = 0.0;
    double waypoint_radius_m = 0.0;
    double cmd_track_deg = 0.0;
    double lookahead_m = 0.0;
    double next_turn_deg = 0.0;
    double next_turn_abs_deg = 0.0;
    double prev_turn_abs_deg = 0.0;
    double lead_turn_m = 0.0;
    double sequence_gate_m = 0.0;
    double distance_to_turn_m = 0.0;
    double dist_to_next_turn_start_m = 0.0;
    double distance_from_prev_turn_m = 0.0;
    bool use_direct_to = false;
    bool direct_to_fix_guidance = false;
    bool final_leg = false;
    bool passed_fix = false;
};

class CompiledScenarioGeometry {
  public:
    void clear();

    void clear_runways();
    void add_runway(const SpatialRunwayDefinition &runway);

    void clear_route();
    void set_route_leg_origin(double x_m, double y_m);
    void add_route_waypoint(const SpatialRouteWaypoint &waypoint);

    SpatialRunwayFrameResult query_runway_local_frame(double x_m, double y_m) const;
    SpatialILSResult query_ils(double x_m, double y_m, double alt_m,
                               double threshold_crossing_height_m) const;
    SpatialRouteQueryResult query_route_guidance(const SpatialRouteQueryOptions &options) const;

  private:
    std::vector<SpatialRunwayDefinition> runways_;
    std::vector<SpatialRouteWaypoint> route_waypoints_;
    double route_leg_origin_x_m_ = 0.0;
    double route_leg_origin_y_m_ = 0.0;
};
