// X-macro list of PlatformConsequenceEvent fields.
//
// Consumers define EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(LethalityChainHeader, header, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, mission_capability_before, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, mission_capability_after, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, mobility_capability_before, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, mobility_capability_after, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, sensor_capability_before, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, sensor_capability_after, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, survivability_capability_before, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, survivability_capability_after, 1.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, mission_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, mobility_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, sensor_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, survivability_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, flight_control_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, propulsion_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, forced_landing, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(bool, crew_kill, false)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, control_delta, 0.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, engine_delta, 0.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(double, fuel_leak_delta, 0.0)
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, fire_state, "unknown")
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, aircraft_damage_state_before, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, aircraft_damage_state_after, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, aircraft_damage_state_delta, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, air_system_hit_flags, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, air_system_spatial_scales, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, vulnerability_scale_trace, {})
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, loss_state_from, "unknown")
EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(std::string, loss_state_to, "unknown")

#undef EF_PLATFORM_CONSEQUENCE_EVENT_FIELD
