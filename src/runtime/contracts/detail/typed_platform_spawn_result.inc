// X-macro list of TypedPlatformSpawnResult fields.
//
// Consumers define EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::uint64_t, request_index, 0)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::uint64_t, world_index, 0)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::uint64_t, entity_id, 0)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(bool, admitted, false)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(bool, materialized, false)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(bool, fail_closed, false)
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, request_id, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, source_type_name, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, plan_id, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, capability_bundle_id, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, setup_surface, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::string, rejection_reason, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::vector<std::string>, errors, {})
EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_TYPED_PLATFORM_SPAWN_RESULT_FIELD
