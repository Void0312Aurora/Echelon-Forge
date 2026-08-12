// X-macro list of KillChainWarheadLoadField fields.
//
// Consumers define EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(std::string, owner_stage, "warhead_load_field")
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(std::string, effect_family, "unknown")
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, warhead_mass_kg, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, lethal_radius_m, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, spatial_effect_scale, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, armor_transmission, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, receiver_exposure_fraction, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, mechanism_effect_scale, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(std::uint32_t, projected_hitbox_count, 0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(std::uint32_t, spatial_sample_count, 0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, spatial_hit_estimate, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, spatial_hit_fraction, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, spatial_energy_scale, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, spatial_pattern_scale, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, orientation_pattern_scale, 1.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, fragment_energy_j, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, fragment_areal_density_per_m2, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, penetration_margin, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, blast_overpressure_kpa, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, blast_impulse_kpa_ms, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, blast_scaled_distance_m_kg13, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, rod_cut_margin, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(double, surface_incidence_cos, 0.0)
EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(std::vector<KillChainComponentLoadFact>, component_loads, {})

#undef EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD
