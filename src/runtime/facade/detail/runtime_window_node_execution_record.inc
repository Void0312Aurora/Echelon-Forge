// X-macro list of RuntimeWindowNodeExecutionRecord fields.
//
// Consumers define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, node_id, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, clock_domain, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, read_snapshot_policy, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, write_commit_policy, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::size_t, visible_input_count, 0)
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, execution_state, "skipped")
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, decision_reason, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, trigger_source, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, decision_barrier_id, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, clock_merge_policy, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, source_snapshot_version, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(double, source_time_s, 0.0)
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::string, target_window_id, {})
EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(std::vector<std::string>, barrier_order, {})

#undef EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD
