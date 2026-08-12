// X-macro list of TypedPlatformSpawnValidationResult fields.
//
// Consumers define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion. The reject()/add_error() helper methods
// are hand-written and declared after this X-macro block.

EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(bool, valid, false)
EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(bool, fail_closed, false)
EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(std::string, rejection_reason, {})
EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(std::vector<std::string>, errors, {})

#undef EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD
