// X-macro list of WaypointRewardProducts fields.
//
// Consumers define EF_WAYPOINT_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_WAYPOINT_PRODUCT(bool, valid, false)
EF_WAYPOINT_PRODUCT(double, waypoint_progress, 0.0)
EF_WAYPOINT_PRODUCT(double, waypoint_distance, 0.0)
EF_WAYPOINT_PRODUCT(double, waypoint_cross_track, 0.0)
EF_WAYPOINT_PRODUCT(double, waypoint_proximity, 0.0)
EF_WAYPOINT_PRODUCT(double, waypoint_reached_bonus, 0.0)
EF_WAYPOINT_PRODUCT(bool, arrived, false)
EF_WAYPOINT_PRODUCT(bool, next_prev_dist_valid, false)
EF_WAYPOINT_PRODUCT(double, next_prev_dist_m, 0.0)

#undef EF_WAYPOINT_PRODUCT
