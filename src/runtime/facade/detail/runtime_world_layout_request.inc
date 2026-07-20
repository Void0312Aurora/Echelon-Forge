// X-macro list of RuntimeWorldLayoutRequest fields.
//
// Consumers define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::uint64_t, world_index, 0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::uint32_t, seed, 42)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::string, terrain_type, {})
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, wind_speed_mps, 0.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, wind_dir_from_deg, 0.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, wind_shear_mps_per_km, 0.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(bool, maritime_configured, false)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, sea_state, 0.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, wave_heading_deg, 0.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(double, wave_period_s, 8.0)
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::vector<WorldZoneDefinition>, zones, {})
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::vector<WorldSpawnRequest>, spawn_requests, {})
EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(std::vector<double>, time_steps, {})

#undef EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD
