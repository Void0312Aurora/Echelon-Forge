// X-macro list of TaskOrderAirStationingDirective fields.
//
// Consumers define EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, anchor_x_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, anchor_y_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, anchor_z_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(StationType, station_type, StationType::Orbit)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, station_radius_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, station_leg_length_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, station_heading_deg, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, altitude_block_min_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, altitude_block_max_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, target_altitude_m, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, speed_min_mps, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, speed_max_mps, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, target_speed_mps, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(int, entry_condition_code, 0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(int, exit_condition_code, 0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, on_station_time_s, 0.0)
EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD(double, fuel_bingo_override_kg, 0.0)

#undef EF_TASK_ORDER_AIR_STATIONING_DIRECTIVE_FIELD
