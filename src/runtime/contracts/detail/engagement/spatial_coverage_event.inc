// X-macro list of SpatialCoverageEvent fields.
//
// Consumers define EF_SPATIAL_COVERAGE_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_SPATIAL_COVERAGE_EVENT_FIELD(LethalityChainHeader, header, {})
EF_SPATIAL_COVERAGE_EVENT_FIELD(std::uint32_t, projected_hitbox_count, 0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(std::uint32_t, sample_count, 0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, hit_estimate, 0.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, hit_fraction, 0.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, energy_scale, 1.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, pattern_scale, 1.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, orientation_axis_forward, 0.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, orientation_axis_right, 0.0)
EF_SPATIAL_COVERAGE_EVENT_FIELD(double, orientation_axis_up, 0.0)

#undef EF_SPATIAL_COVERAGE_EVENT_FIELD
