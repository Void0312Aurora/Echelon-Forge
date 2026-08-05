// X-macro list of RuntimeWorldlineComparison fields.
//
// Consumers define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(bool, comparable, false)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(std::string, comparison_id, {})
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(std::string, parent_worldline_id, {})
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(std::string, branch_worldline_id, {})
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(std::string, barrier_id, "counterfactual_selected_slice")
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dx, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dy, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dz, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dvx, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dvy, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dvz, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(double, dheading, 0.0)
EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(std::vector<std::string>, evidence_refs, {})

#undef EF_RUNTIME_WORLDLINE_COMPARISON_FIELD
