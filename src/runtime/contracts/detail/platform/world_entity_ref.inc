// X-macro list of WorldEntityRef fields.
//
// Consumers define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_WORLD_ENTITY_REF_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_ENTITY_REF_FIELD(std::uint64_t, entity_id, 0)

#undef EF_WORLD_ENTITY_REF_FIELD
