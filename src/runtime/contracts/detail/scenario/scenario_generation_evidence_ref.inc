// X-macro list of ScenarioGenerationEvidenceMetadataRef fields.
//
// Consumers define EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.
//
// counterfactual_replay_contract_types.h includes this file at the
// struct's original seam, so this list is the single C++ member-order
// owner (ABI: additive/append-only); the cross-language gate is
// tests/architecture/governance/test_scenario_generation_lineage_parity.py.

EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD(std::string, ref_id, "")
EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD(std::string, evidence_kind, "")
EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD(std::string, provenance_label, "")

#undef EF_SCENARIO_GENERATION_EVIDENCE_REF_FIELD
