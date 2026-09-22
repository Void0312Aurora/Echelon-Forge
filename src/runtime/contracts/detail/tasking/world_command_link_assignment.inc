// X-macro list of WorldCommandLinkAssignment fields.
//
// Consumers define EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(std::uint64_t, entity_id, 0)
EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(double, latency_s, 0.0)
EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD(double, drop_probability, 0.0)

#undef EF_WORLD_COMMAND_LINK_ASSIGNMENT_FIELD
