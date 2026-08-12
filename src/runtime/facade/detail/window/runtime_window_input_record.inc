// X-macro list of RuntimeWindowInputRecord fields.
//
// Consumers define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(RuntimeWindowActionRequest, request, {})
EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(std::string, reason, {})

#undef EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD
