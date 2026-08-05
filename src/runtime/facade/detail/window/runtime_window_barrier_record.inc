// X-macro list of RuntimeWindowBarrierRecord fields.
//
// Consumers define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(std::uint64_t, sequence, 0)
EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(std::string, barrier_id, {})
EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(std::string, node_id, {})

#undef EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD
