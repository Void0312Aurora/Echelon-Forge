// X-macro list of DamageReport fields.
//
// Consumers define EF_DAMAGE_REPORT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_DAMAGE_REPORT_FIELD(std::uint64_t, report_id, 0)
EF_DAMAGE_REPORT_FIELD(EngagementEntityRef, target, {})
EF_DAMAGE_REPORT_FIELD(std::uint64_t, source_event_id, 0)
EF_DAMAGE_REPORT_FIELD(double, hp_delta, 0.0)
EF_DAMAGE_REPORT_FIELD(double, system_health_delta, 0.0)
EF_DAMAGE_REPORT_FIELD(std::string, platform_damage_state_delta, {})
EF_DAMAGE_REPORT_FIELD(bool, mission_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, mobility_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, sensor_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, survivability_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, forced_landing, false)
EF_DAMAGE_REPORT_FIELD(bool, flight_control_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, propulsion_kill, false)
EF_DAMAGE_REPORT_FIELD(bool, crew_kill, false)
EF_DAMAGE_REPORT_FIELD(std::string, loss_state_from, "unknown")
EF_DAMAGE_REPORT_FIELD(std::string, loss_state_to, "unknown")
EF_DAMAGE_REPORT_FIELD(bool, destroyed, false)
EF_DAMAGE_REPORT_FIELD(double, report_time_s, 0.0)
EF_DAMAGE_REPORT_FIELD(std::string, producer_node_id, {})

#undef EF_DAMAGE_REPORT_FIELD
