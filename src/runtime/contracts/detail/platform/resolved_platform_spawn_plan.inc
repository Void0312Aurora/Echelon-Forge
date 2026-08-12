// X-macro list of runtime::platform_capabilities::ResolvedPlatformSpawnPlan
// fields.
//
// Consumers define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, plan_id, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, source_request_kind, std::string(kPlatformSpawnRequestKindTypeNameProjection))
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, source_type_name, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, capability_bundle_id, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, resolved_platform_definition_ref, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, materialization_strategy, std::string(kPlatformMaterializationStrategyFactoryProjection))
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, template_evidence_ref, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, resolution_evidence_ref, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, materialization_evidence_ref, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::vector<std::string>, evidence_refs, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::vector<Capability>, resolved_capabilities, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::vector<std::string>, rejected_capability_ids, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(bool, type_name_projection_preserved, true)
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(bool, admitted, false)
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, rejection_reason, {})
EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(std::string, diagnostics_reason, {})

#undef EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD
