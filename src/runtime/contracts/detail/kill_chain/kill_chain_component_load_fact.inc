// X-macro list of KillChainComponentLoadFact fields.
//
// Consumers define EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(std::string, owner_stage, "warhead_load_field")
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(std::string, component_name, {})
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(std::string, component_system, {})
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(std::string, component_redundancy_group_id, {})
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(bool, direct_hit, false)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, distance_m, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, effect_scale, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, spatial_intersection_fraction, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, pattern_weight, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, orientation_weight, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, receiver_exposure_fraction, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, armor_transmission, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, sampling_confidence, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, load_intensity_scale, 1.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, fragment_energy_j, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, fragment_areal_density_per_m2, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, penetration_margin, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, blast_overpressure_kpa, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, blast_impulse_kpa_ms, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, blast_scaled_distance_m_kg13, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, rod_cut_margin, 0.0)
EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(double, surface_incidence_cos, 0.0)

#undef EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD
