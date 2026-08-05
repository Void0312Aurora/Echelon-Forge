// X-macro list of TypedPlatformSpawnRequest fields.
//
// Consumers define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(std::uint64_t, world_index, 0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(Side, side, Side::Neutral)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(std::string, request_id, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(std::string, source_type_name, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(std::string, entity_name, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(bool, is_agent, false)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, x, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, y, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, z, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, heading, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, pitch, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, roll, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, vx, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, vy, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(double, vz, 0.0)
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(runtime::platform_capabilities::CapabilityBundle, capability_bundle, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(runtime::platform_capabilities::ResolvedPlatformSpawnPlan, resolved_spawn_plan, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(std::vector<std::string>, facade_evidence_refs, {})
EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(bool, type_name_projection_preserved, true)

#undef EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD
