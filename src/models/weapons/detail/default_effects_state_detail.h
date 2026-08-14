// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

struct DefaultEffectsScratch {
    explicit DefaultEffectsScratch(std::uint64_t initial_component_rng_state)
        : component_rng_state(initial_component_rng_state) {}

    bool structure_hit = false;
    bool direct_hitbox_intersection = false;
    std::unordered_set<std::string> processed_air_systems;

    bool air_sensor_hit = false;
    bool air_propulsion_or_fuel_hit = false;
    bool air_propulsion_hit = false;
    bool air_fuel_hit = false;
    bool air_control_hit = false;
    bool air_crew_hit = false;
    bool air_pilot_hit = false;
    bool air_mission_crew_hit = false;
    bool air_command_navigation_hit = false;
    bool air_mission_or_combat_hit = false;
    bool air_fire_suppression_hit = false;
    bool air_lateral_fuel_storage_hit = false;
    bool air_hydraulic_supply_hit = false;
    bool air_engine_fire_zone_hit = false;
    bool air_wing_fire_zone_hit = false;
    bool air_fuselage_fire_zone_hit = false;
    bool air_mission_fire_zone_hit = false;

    double air_sensor_spatial_scale = 0.0;
    double air_propulsion_or_fuel_spatial_scale = 0.0;
    double air_propulsion_spatial_scale = 0.0;
    double air_fuel_spatial_scale = 0.0;
    double air_control_spatial_scale = 0.0;
    double air_crew_spatial_scale = 0.0;
    double air_pilot_spatial_scale = 0.0;
    double air_mission_crew_spatial_scale = 0.0;
    double air_command_navigation_spatial_scale = 0.0;
    double air_mission_or_combat_spatial_scale = 0.0;
    double air_fire_suppression_spatial_scale = 0.0;
    double air_lateral_fuel_storage_spatial_scale = 0.0;
    double air_hydraulic_supply_spatial_scale = 0.0;
    double air_engine_fire_zone_spatial_scale = 0.0;
    double air_wing_fire_zone_spatial_scale = 0.0;
    double air_fuselage_fire_zone_spatial_scale = 0.0;
    double air_mission_fire_zone_spatial_scale = 0.0;
    double air_structure_spatial_scale = 0.0;

    double spatial_effect_scale = 0.0;
    double sampled_mechanism_scale = 0.0;
    double sampled_armor_scale = 1.0;
    double sampled_exposure_scale = 1.0;
    double sampled_mechanism_fragment_energy_j = 0.0;
    double sampled_mechanism_fragment_areal_density_per_m2 = 0.0;
    double sampled_mechanism_penetration_margin = 0.0;
    double sampled_mechanism_blast_overpressure_kpa = 0.0;
    double sampled_mechanism_blast_impulse_kpa_ms = 0.0;
    double sampled_mechanism_blast_scaled_distance_m_kg13 = 0.0;
    double sampled_mechanism_rod_cut_margin = 0.0;
    double sampled_mechanism_surface_incidence_cos = 0.0;
    bool sampled_mechanism_surface_incidence_seen = false;

    std::uint32_t sampled_warhead_spatial_sample_count = 0;
    double sampled_warhead_spatial_hit_estimate = 0.0;
    double sampled_warhead_spatial_hit_fraction = 0.0;
    double sampled_warhead_spatial_energy_scale = 1.0;
    double sampled_warhead_spatial_pattern_scale = 0.0;
    double sampled_warhead_orientation_pattern_scale = 0.0;

    double sampled_component_threshold_scale = 1.0;
    double sampled_component_failure_probability = 0.0;
    bool sampled_component_failure_probability_seen = false;
    std::string sampled_component_failure_probability_source = "none";
    bool sampled_component_failure_probability_calibrated = false;
    std::string sampled_component_failure_probability_evidence_dataset_ref;
    std::string sampled_component_failure_probability_evidence_row_id;
    std::string sampled_component_failure_probability_evidence_source_ref;
    std::string sampled_component_failure_probability_evidence_provenance;
    double sampled_component_failure_sample = 1.0;
    std::uint32_t component_failure_count = 0;
    std::uint64_t component_rng_state;

    std::uint32_t projected_hitbox_count = 0;
    std::uint32_t component_hit_count = 0;
    std::vector<ComponentMechanismLoadRow> component_mechanism_load_rows;
    std::vector<ComponentResponseRow> component_response_rows;
    std::string component_primary_name;
    std::string component_primary_system;
    double component_primary_redundancy_group = 0.0;
    bool component_primary_critical = false;
    std::string component_primary_redundancy_group_id;
    double component_primary_integrity = 1.0;
    double component_redundancy_group_availability = 1.0;
    std::uint32_t component_redundancy_group_member_count = 0;
    std::uint32_t component_redundancy_group_failed_count = 0;
    VulnerabilityAdjustment sampled_vulnerability_adjustment;
    double component_primary_effect_scale = -1.0;
    double component_primary_priority = -1.0;
    WarheadMechanismLoadEvidence component_primary_mechanism_load{};
};

ComponentMechanismLoadRow make_default_effects_component_mechanism_load_row(
    const DamageComponent &component, double effect_scale, double component_scale, bool direct_hit,
    double distance_m, const WarheadMechanismLoadEvidence &mechanism_load) {
    (void)component_scale;
    ComponentMechanismLoadRow row{};
    row.component_name = component.name.empty() ? component.system : component.name;
    row.component_system = component.system;
    row.component_redundancy_group_id = damage_component_redundancy_group_key(component);
    row.direct_hit = direct_hit;
    row.distance_m = std::max(0.0, distance_m);
    row.effect_scale = effect_scale;
    row.mechanism_fragment_energy_j = mechanism_load.fragment_energy_j;
    row.mechanism_fragment_areal_density_per_m2 = mechanism_load.fragment_areal_density_per_m2;
    row.mechanism_penetration_margin = mechanism_load.penetration_margin;
    row.mechanism_blast_overpressure_kpa = mechanism_load.blast_overpressure_kpa;
    row.mechanism_blast_impulse_kpa_ms = mechanism_load.blast_impulse_kpa_ms;
    row.mechanism_blast_scaled_distance_m_kg13 = mechanism_load.blast_scaled_distance_m_kg13;
    row.mechanism_rod_cut_margin = mechanism_load.rod_cut_margin;
    row.mechanism_surface_incidence_cos = mechanism_load.surface_incidence_cos;
    return row;
}

ComponentMechanismLoadRow *
record_default_effects_component_hit(DefaultEffectsScratch &scratch,
                                     const DamageComponent &component, double effect_scale,
                                     double component_scale, bool direct_hit, double distance_m,
                                     const WarheadMechanismLoadEvidence &mechanism_load) {
    ++scratch.component_hit_count;
    scratch.component_mechanism_load_rows.push_back(
        make_default_effects_component_mechanism_load_row(component, effect_scale, component_scale,
                                                          direct_hit, distance_m, mechanism_load));
    ComponentMechanismLoadRow &row = scratch.component_mechanism_load_rows.back();
    if (effect_scale > scratch.component_primary_effect_scale) {
        scratch.component_primary_effect_scale = effect_scale;
        scratch.component_primary_name = component.name.empty() ? component.system : component.name;
        scratch.component_primary_system = component.system;
        scratch.component_primary_redundancy_group = component.redundancy_group;
        scratch.component_primary_critical = component.critical;
        scratch.component_primary_redundancy_group_id =
            damage_component_redundancy_group_key(component);
        scratch.component_primary_mechanism_load = mechanism_load;
    }
    return &row;
}

std::uint32_t default_effects_component_load_row_index(const DefaultEffectsScratch &scratch,
                                                       const ComponentMechanismLoadRow *row) {
    if (!row || scratch.component_mechanism_load_rows.empty()) {
        return 0;
    }
    const ComponentMechanismLoadRow *begin = scratch.component_mechanism_load_rows.data();
    const ComponentMechanismLoadRow *end = begin + scratch.component_mechanism_load_rows.size();
    if (row < begin || row >= end) {
        return 0;
    }
    return static_cast<std::uint32_t>(row - begin);
}

void record_default_effects_warhead_spatial_sample(DefaultEffectsScratch &scratch,
                                                   const WarheadSpatialSample &sample) {
    scratch.sampled_warhead_spatial_sample_count += sample.sample_count;
    scratch.sampled_warhead_spatial_hit_estimate += sample.hit_estimate;
    scratch.sampled_warhead_spatial_energy_scale =
        std::min(scratch.sampled_warhead_spatial_energy_scale, sample.energy_scale);
    scratch.sampled_warhead_spatial_pattern_scale =
        std::max(scratch.sampled_warhead_spatial_pattern_scale, sample.pattern_scale);
    scratch.sampled_warhead_orientation_pattern_scale = std::max(
        scratch.sampled_warhead_orientation_pattern_scale, sample.orientation_pattern_scale);
    scratch.sampled_warhead_spatial_hit_fraction =
        scratch.sampled_warhead_spatial_sample_count > 0
            ? std::clamp(scratch.sampled_warhead_spatial_hit_estimate /
                             static_cast<double>(scratch.sampled_warhead_spatial_sample_count),
                         0.0, 1.0)
            : 0.0;
}

void record_default_effects_mechanism_load(DefaultEffectsScratch &scratch,
                                           const WarheadMechanismLoadEvidence &load) {
    scratch.sampled_mechanism_fragment_energy_j =
        std::max(scratch.sampled_mechanism_fragment_energy_j, load.fragment_energy_j);
    scratch.sampled_mechanism_fragment_areal_density_per_m2 =
        std::max(scratch.sampled_mechanism_fragment_areal_density_per_m2,
                 load.fragment_areal_density_per_m2);
    scratch.sampled_mechanism_penetration_margin =
        std::max(scratch.sampled_mechanism_penetration_margin, load.penetration_margin);
    scratch.sampled_mechanism_blast_overpressure_kpa =
        std::max(scratch.sampled_mechanism_blast_overpressure_kpa, load.blast_overpressure_kpa);
    scratch.sampled_mechanism_blast_impulse_kpa_ms =
        std::max(scratch.sampled_mechanism_blast_impulse_kpa_ms, load.blast_impulse_kpa_ms);
    if (load.blast_scaled_distance_m_kg13 > 0.0 &&
        (scratch.sampled_mechanism_blast_scaled_distance_m_kg13 <= 0.0 ||
         load.blast_scaled_distance_m_kg13 <
             scratch.sampled_mechanism_blast_scaled_distance_m_kg13)) {
        scratch.sampled_mechanism_blast_scaled_distance_m_kg13 = load.blast_scaled_distance_m_kg13;
    }
    scratch.sampled_mechanism_rod_cut_margin =
        std::max(scratch.sampled_mechanism_rod_cut_margin, load.rod_cut_margin);
    const double incidence_cos = std::clamp(load.surface_incidence_cos, 0.0, 1.0);
    scratch.sampled_mechanism_surface_incidence_cos =
        scratch.sampled_mechanism_surface_incidence_seen
            ? std::min(scratch.sampled_mechanism_surface_incidence_cos, incidence_cos)
            : incidence_cos;
    scratch.sampled_mechanism_surface_incidence_seen = true;
}

void record_default_effects_warhead_effect_sample(
    DefaultEffectsScratch &scratch, double spatial_effect_scale, double mechanism_scale,
    double armor_scale, double exposure_scale, const WarheadSpatialSample &spatial_sample,
    const WarheadMechanismLoadEvidence &mechanism_load) {
    scratch.spatial_effect_scale = std::max(scratch.spatial_effect_scale, spatial_effect_scale);
    scratch.sampled_mechanism_scale = std::max(scratch.sampled_mechanism_scale, mechanism_scale);
    scratch.sampled_armor_scale = std::min(scratch.sampled_armor_scale, armor_scale);
    scratch.sampled_exposure_scale = std::min(scratch.sampled_exposure_scale, exposure_scale);
    record_default_effects_warhead_spatial_sample(scratch, spatial_sample);
    record_default_effects_mechanism_load(scratch, mechanism_load);
}

void note_default_effects_air_system_hit(DefaultEffectsScratch &scratch, const std::string &system,
                                         double system_spatial_scale,
                                         const DamageComponent *component = nullptr) {
    const double resolved_spatial_scale = std::clamp(system_spatial_scale, 0.0, 1.0);
    const bool fire_suppression_path = component && component_is_fire_suppression_path(*component);
    switch (classify_aircraft_fire_zone(system, component)) {
    case AircraftFireZone::EngineBay:
        scratch.air_engine_fire_zone_hit = true;
        scratch.air_engine_fire_zone_spatial_scale =
            std::max(scratch.air_engine_fire_zone_spatial_scale, resolved_spatial_scale);
        break;
    case AircraftFireZone::Wing:
        scratch.air_wing_fire_zone_hit = true;
        scratch.air_wing_fire_zone_spatial_scale =
            std::max(scratch.air_wing_fire_zone_spatial_scale, resolved_spatial_scale);
        break;
    case AircraftFireZone::Fuselage:
        scratch.air_fuselage_fire_zone_hit = true;
        scratch.air_fuselage_fire_zone_spatial_scale =
            std::max(scratch.air_fuselage_fire_zone_spatial_scale, resolved_spatial_scale);
        break;
    case AircraftFireZone::MissionBay:
        scratch.air_mission_fire_zone_hit = true;
        scratch.air_mission_fire_zone_spatial_scale =
            std::max(scratch.air_mission_fire_zone_spatial_scale, resolved_spatial_scale);
        break;
    case AircraftFireZone::None:
        break;
    }
    if (system_is_air_sensor(system)) {
        scratch.air_sensor_hit = true;
        scratch.air_sensor_spatial_scale =
            std::max(scratch.air_sensor_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_air_propulsion_or_fuel(system) && !fire_suppression_path) {
        scratch.air_propulsion_or_fuel_hit = true;
        scratch.air_propulsion_or_fuel_spatial_scale =
            std::max(scratch.air_propulsion_or_fuel_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_air_propulsion(system)) {
        scratch.air_propulsion_hit = true;
        scratch.air_propulsion_spatial_scale =
            std::max(scratch.air_propulsion_spatial_scale, resolved_spatial_scale);
    }
    if (component && component_is_engine_fuel_feed_path(*component) && system_is_air_fuel(system)) {
        scratch.air_propulsion_hit = true;
        scratch.air_propulsion_spatial_scale =
            std::max(scratch.air_propulsion_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_air_fuel(system) && !fire_suppression_path) {
        scratch.air_fuel_hit = true;
        scratch.air_fuel_spatial_scale =
            std::max(scratch.air_fuel_spatial_scale, resolved_spatial_scale);
    }
    if (component && component_is_lateral_fuel_storage_path(*component)) {
        scratch.air_lateral_fuel_storage_hit = true;
        scratch.air_lateral_fuel_storage_spatial_scale =
            std::max(scratch.air_lateral_fuel_storage_spatial_scale, resolved_spatial_scale);
    }
    if ((component && component_is_hydraulic_supply_path(*component)) ||
        system_name_matches(system, "hydraulic")) {
        scratch.air_hydraulic_supply_hit = true;
        scratch.air_hydraulic_supply_spatial_scale =
            std::max(scratch.air_hydraulic_supply_spatial_scale, resolved_spatial_scale);
    }
    if (fire_suppression_path || system_is_air_fire_suppression(system)) {
        scratch.air_fire_suppression_hit = true;
        scratch.air_fire_suppression_spatial_scale =
            std::max(scratch.air_fire_suppression_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_air_control_surface(system)) {
        scratch.air_control_hit = true;
        scratch.air_control_spatial_scale =
            std::max(scratch.air_control_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_crew_or_cockpit(system)) {
        scratch.air_crew_hit = true;
        scratch.air_crew_spatial_scale =
            std::max(scratch.air_crew_spatial_scale, resolved_spatial_scale);
    }
    const CrewConsequenceKind crew_kind =
        classify_crew_consequence(system, component ? damage_component_key(*component) : "");
    if (crew_kind == CrewConsequenceKind::Pilot) {
        scratch.air_pilot_hit = true;
        scratch.air_pilot_spatial_scale =
            std::max(scratch.air_pilot_spatial_scale, resolved_spatial_scale);
    } else if (crew_kind == CrewConsequenceKind::MissionCrew) {
        scratch.air_mission_crew_hit = true;
        scratch.air_mission_crew_spatial_scale =
            std::max(scratch.air_mission_crew_spatial_scale, resolved_spatial_scale);
    } else if (crew_kind == CrewConsequenceKind::CommandNavigation) {
        scratch.air_command_navigation_hit = true;
        scratch.air_command_navigation_spatial_scale =
            std::max(scratch.air_command_navigation_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_mission_or_combat(system)) {
        scratch.air_mission_or_combat_hit = true;
        scratch.air_mission_or_combat_spatial_scale =
            std::max(scratch.air_mission_or_combat_spatial_scale, resolved_spatial_scale);
    }
    if (system_is_air_structure(system)) {
        scratch.air_structure_spatial_scale =
            std::max(scratch.air_structure_spatial_scale, resolved_spatial_scale);
    }
}
