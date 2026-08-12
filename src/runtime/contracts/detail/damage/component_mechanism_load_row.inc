// X-macro list of ComponentMechanismLoadRow fields.
//
// Consumers define EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_name, {})
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_system, {})
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_redundancy_group_id, {})
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(bool, direct_hit, false)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, distance_m, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, effect_scale, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::uint32_t, component_dependency_propagation_count, 0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_dependency_target_system, {})
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_dependency_edge_type, "none")
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, component_dependency_threshold, 1.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, component_dependency_delay_s, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_dependency_direction, "one_way")
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(std::string, component_dependency_provenance, {})
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, component_dependency_source_availability, 1.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, component_dependency_effective_scale, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(bool, component_dependency_propagated, false)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_fragment_energy_j, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_fragment_areal_density_per_m2, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_penetration_margin, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_blast_overpressure_kpa, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_blast_impulse_kpa_ms, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_blast_scaled_distance_m_kg13, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_rod_cut_margin, 0.0)
EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(double, mechanism_surface_incidence_cos, 0.0)

#undef EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD
