// X-macro list of WarheadMechanismEvent fields.
//
// Consumers define EF_WARHEAD_MECHANISM_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_WARHEAD_MECHANISM_EVENT_FIELD(LethalityChainHeader, header, {})
EF_WARHEAD_MECHANISM_EVENT_FIELD(std::string, mechanism_family, "unknown")
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, warhead_mass_kg, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, lethal_radius_m, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, fragment_energy_j, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, fragment_density_per_m2, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, blast_overpressure_kpa, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, blast_impulse_kpa_ms, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, blast_scaled_distance_m_kg13, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, rod_cut_margin, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, penetration_margin, 0.0)
EF_WARHEAD_MECHANISM_EVENT_FIELD(double, surface_incidence_cos, 0.0)

#undef EF_WARHEAD_MECHANISM_EVENT_FIELD
