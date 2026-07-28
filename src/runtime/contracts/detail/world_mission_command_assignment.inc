// X-macro list of WorldMissionCommandAssignment fields.
//
// Consumers define EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(std::uint64_t, entity_id, 0)
EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(shell_type, command, {})

#undef EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD
