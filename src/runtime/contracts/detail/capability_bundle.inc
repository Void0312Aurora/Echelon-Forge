// X-macro list of runtime::platform_capabilities::CapabilityBundle fields.
//
// Consumers define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_CAPABILITY_BUNDLE_FIELD(std::string, bundle_id, {})
EF_CAPABILITY_BUNDLE_FIELD(std::string, source_type_name, {})
EF_CAPABILITY_BUNDLE_FIELD(std::vector<Capability>, capabilities, {})
EF_CAPABILITY_BUNDLE_FIELD(std::string, template_evidence_ref, {})
EF_CAPABILITY_BUNDLE_FIELD(std::vector<std::string>, evidence_refs, {})
EF_CAPABILITY_BUNDLE_FIELD(bool, type_name_projection_preserved, true)
EF_CAPABILITY_BUNDLE_FIELD(std::string, diagnostics_reason, {})

#undef EF_CAPABILITY_BUNDLE_FIELD
