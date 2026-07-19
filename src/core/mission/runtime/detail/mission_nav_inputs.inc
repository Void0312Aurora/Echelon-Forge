// X-macro list of MissionNavInputs fields.
//
// Consumers define EF_NAV_INPUT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.

EF_NAV_INPUT(double, own_altitude_m, 0.0)
EF_NAV_INPUT(double, truth_heading_deg, 0.0)
EF_NAV_INPUT(double, truth_speed_mps, 0.0)
EF_NAV_INPUT(double, inst_heading_deg, 0.0)
EF_NAV_INPUT(double, inst_ground_track_deg, 0.0)
EF_NAV_INPUT(double, inst_ias_mps, 0.0)
EF_NAV_INPUT(double, waypoint_altitude_m, 0.0)
EF_NAV_INPUT(double, cdi_full_scale_m, 1500.0)

#undef EF_NAV_INPUT
