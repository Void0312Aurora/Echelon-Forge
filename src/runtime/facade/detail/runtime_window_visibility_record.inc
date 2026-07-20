// X-macro list of RuntimeWindowVisibilityRecord fields.
//
// Consumers define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(std::string, barrier_id, {})
EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(std::size_t, visible_input_count, 0)

#undef EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD
