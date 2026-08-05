// X-macro list of RuntimeWorldLayoutResult fields.
//
// Consumers define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(std::uint64_t, world_index, 0)
EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(std::vector<std::uint64_t>, entity_ids, {})

#undef EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD
