// X-macro list of WorldZoneDefinition fields.
//
// Consumers define EF_WORLD_ZONE_DEFINITION_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_WORLD_ZONE_DEFINITION_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_ZONE_DEFINITION_FIELD(std::string, name, "Zone")
EF_WORLD_ZONE_DEFINITION_FIELD(double, x, 0.0)
EF_WORLD_ZONE_DEFINITION_FIELD(double, y, 0.0)
EF_WORLD_ZONE_DEFINITION_FIELD(double, width, 1000.0)
EF_WORLD_ZONE_DEFINITION_FIELD(double, length, 1000.0)
EF_WORLD_ZONE_DEFINITION_FIELD(double, heading, 0.0)
EF_WORLD_ZONE_DEFINITION_FIELD(int, surface_type, 3)

#undef EF_WORLD_ZONE_DEFINITION_FIELD
