// X-macro list of RuntimeWindowSchedulingContext fields.
//
// Consumers define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::string, window_id, {})
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::uint64_t, world_id, 0)
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(double, source_time_s, 0.0)
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::uint64_t, barrier_sequence, 0)
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::string, current_barrier_id, {})
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::vector<RuntimeWindowInputRecord>, accepted_inputs, {})
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::vector<RuntimeWindowInputRecord>, deferred_inputs, {})
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::vector<RuntimeWindowInputRecord>, rejected_inputs, {})
EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(std::vector<RuntimeWindowInputRecord>, expired_inputs, {})

#undef EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD
