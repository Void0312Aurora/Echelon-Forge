// X-macro list of WorldWindAssignment fields.
//
// Consumers define EF_WORLD_WIND_ASSIGNMENT_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_WORLD_WIND_ASSIGNMENT_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_WIND_ASSIGNMENT_FIELD(double, speed_mps, 0.0)
EF_WORLD_WIND_ASSIGNMENT_FIELD(double, dir_from_deg, 0.0)
EF_WORLD_WIND_ASSIGNMENT_FIELD(double, shear_mps_per_km, 0.0)

#undef EF_WORLD_WIND_ASSIGNMENT_FIELD
