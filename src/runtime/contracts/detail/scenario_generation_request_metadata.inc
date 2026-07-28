// X-macro list of ScenarioGenerationRequestMetadata fields.
//
// Consumers define EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion. The contract_version default requires
// counterfactual_replay_contract_constants.h and the evidence_refs
// element type requires ScenarioGenerationEvidenceMetadataRef to be
// declared before expansion.
//
// counterfactual_replay_contract_types.h includes this file at the
// struct's original seam, so this list is the single C++ member-order
// owner (ABI: additive/append-only); the cross-language gate is
// tests/architecture/governance/test_scenario_generation_lineage_parity.py.

EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, request_id, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, request_version, "1")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, contract_version, std::string(kScenarioGenerationContractVersionRequestV1))
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, generation_kind, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, source, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, generator_version, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(bool, has_deterministic_seed, false)
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::uint64_t, deterministic_seed, 0)
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, baseline_scenario_ref, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, replay_envelope_ref, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::string, branch_point_ref, "")
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::vector<std::string>, capability_refs, {})
EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD(std::vector<ScenarioGenerationEvidenceMetadataRef>, evidence_refs, {})

#undef EF_SCENARIO_GENERATION_REQUEST_METADATA_FIELD
