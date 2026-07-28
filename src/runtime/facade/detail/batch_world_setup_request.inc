// X-macro list of BatchWorldSetupRequest fields.
//
// Consumers define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<std::uint32_t>, seeds, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<WorldTerrainAssignment>, terrain_assignments, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<WorldWindAssignment>, wind_assignments, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<WorldSunAssignment>, sun_assignments, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<WorldZoneDefinition>, zones, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<WorldSpawnRequest>, spawn_requests, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<TypedPlatformSpawnRequest>, typed_platform_spawn_requests, {})
EF_BATCH_WORLD_SETUP_REQUEST_FIELD(std::vector<double>, time_steps, {})

#undef EF_BATCH_WORLD_SETUP_REQUEST_FIELD
