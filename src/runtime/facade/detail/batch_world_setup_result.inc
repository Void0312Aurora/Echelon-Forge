// X-macro list of BatchWorldSetupResult fields.
//
// Consumers define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_BATCH_WORLD_SETUP_RESULT_FIELD(std::vector<std::uint64_t>, entity_ids, {})
EF_BATCH_WORLD_SETUP_RESULT_FIELD(std::vector<TypedPlatformSpawnResult>, typed_platform_spawn_results, {})

#undef EF_BATCH_WORLD_SETUP_RESULT_FIELD
