// X-macro list of RuntimeCounterfactualSnapshot fields.
//
// Consumers define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, parent_worldline_id, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::uint64_t, deterministic_seed, 0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::uint64_t, world_index, 0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::uint64_t, entity_id, 0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, x, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, y, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, z, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, vx, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, vy, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, vz, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, heading, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, pitch, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(double, roll, 0.0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::uint64_t, snapshot_version, 0)
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, barrier_id, "counterfactual_selected_slice")
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, fidelity_profile_id, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, provider_family, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, selected_stage_node_id, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::string, cadence_reason, {})
EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD
