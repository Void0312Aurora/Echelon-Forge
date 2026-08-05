// X-macro list of RuntimeWindowCadenceTraceRecord fields.
//
// Consumers define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, domain, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::uint32_t, tick, 0)
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, node_id, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, decision, "skipped")
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, decision_reason, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, source, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, barrier_id, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, clock_domain, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, clock_merge_policy, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, cadence_merge_policy, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(std::string, relation, {})
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(bool, held, false)
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(bool, expired, false)
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(bool, deferred, false)
EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(bool, diagnostics_only, false)

#undef EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD
