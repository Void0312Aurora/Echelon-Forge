// X-macro list of RuntimeWindowResult fields.
//
// Consumers define EF_RUNTIME_WINDOW_RESULT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_RESULT_FIELD(RuntimeWindowSchedulingContext, context, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<RuntimeWindowBarrierRecord>, barrier_trace, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<RuntimeWindowVisibilityRecord>, visibility_trace, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<RuntimeWindowNodeExecutionRecord>, executed_nodes, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(RuntimeWindowCadenceConfig, cadence_config, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<RuntimeWindowCadenceTraceRecord>, cadence_trace, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<RuntimeWindowInputRecord>, injected_inputs, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(ObservationBatchPacket, observation_packet, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(EngagementEventPacket, engagement_packet, {})
EF_RUNTIME_WINDOW_RESULT_FIELD(std::vector<DiagnosticsTrace>, diagnostics_traces, {})

#undef EF_RUNTIME_WINDOW_RESULT_FIELD
