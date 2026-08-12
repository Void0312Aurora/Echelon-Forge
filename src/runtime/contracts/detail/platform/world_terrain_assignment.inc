// X-macro list of WorldTerrainAssignment fields.
//
// Consumers define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(std::string, terrain_type, "flat")

#undef EF_WORLD_TERRAIN_ASSIGNMENT_FIELD
