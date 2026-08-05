// X-macro list of runtime::platform_capabilities::Capability fields.
//
// Consumers define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_PLATFORM_CAPABILITY_FIELD(std::string, capability_id, {})
EF_PLATFORM_CAPABILITY_FIELD(std::string, family, {})
EF_PLATFORM_CAPABILITY_FIELD(std::string, capability_type, {})
EF_PLATFORM_CAPABILITY_FIELD(std::string, implementation_ref, {})
EF_PLATFORM_CAPABILITY_FIELD(std::vector<std::string>, requires_capability_ids, {})
EF_PLATFORM_CAPABILITY_FIELD(std::vector<std::string>, evidence_refs, {})
EF_PLATFORM_CAPABILITY_FIELD(bool, required, true)
EF_PLATFORM_CAPABILITY_FIELD(bool, supported, true)
EF_PLATFORM_CAPABILITY_FIELD(std::string, unsupported_reason, {})

#undef EF_PLATFORM_CAPABILITY_FIELD
