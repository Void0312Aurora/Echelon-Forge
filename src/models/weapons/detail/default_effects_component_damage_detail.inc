// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

struct WarheadMechanismLoadEvidence {
    double fragment_energy_j = 0.0;
    double fragment_areal_density_per_m2 = 0.0;
    double penetration_margin = 0.0;
    double blast_overpressure_kpa = 0.0;
    double blast_impulse_kpa_ms = 0.0;
    double blast_scaled_distance_m_kg13 = 0.0;
    double rod_cut_margin = 0.0;
    double surface_incidence_cos = 0.0;
};

WarheadMechanismLoadEvidence with_surface_incidence(
    WarheadMechanismLoadEvidence evidence,
    double surface_incidence_cos
) {
    evidence.surface_incidence_cos = std::clamp(surface_incidence_cos, 0.0, 1.0);
    return evidence;
}

double smoothstep01(double value) {
    const double x = std::clamp(value, 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

struct ComponentFragilityRuntimeState {
    double integrity = 1.0;
    double group_availability = 1.0;
    std::uint32_t group_member_count = 0;
    std::uint32_t group_failed_count = 0;
};

ComponentFragilityRuntimeState resolve_component_fragility_runtime_state(
    const DamageComponent* component,
    const ComponentDamageState* component_damage
) {
    ComponentFragilityRuntimeState state{};
    if (!component || !component_damage) {
        return state;
    }

    const std::string component_key = damage_component_key(*component);
    const std::string group_key = damage_component_redundancy_group_key(*component);
    if (const auto integrity_it = component_damage->component_integrity.find(component_key);
        integrity_it != component_damage->component_integrity.end()) {
        state.integrity = std::clamp(integrity_it->second, 0.0, 1.0);
    }
    if (const auto availability_it =
            component_damage->redundancy_group_availability.find(group_key);
        availability_it != component_damage->redundancy_group_availability.end()) {
        state.group_availability = std::clamp(availability_it->second, 0.0, 1.0);
    }
    if (const auto member_it =
            component_damage->redundancy_group_member_count.find(group_key);
        member_it != component_damage->redundancy_group_member_count.end()) {
        state.group_member_count = member_it->second;
    }
    if (const auto failed_it =
            component_damage->redundancy_group_failed_count.find(group_key);
        failed_it != component_damage->redundancy_group_failed_count.end()) {
        state.group_failed_count = failed_it->second;
    }
    return state;
}

double component_dependency_complexity_scale(const DamageComponent* component) {
    if (!component) {
        return 1.0;
    }

    double scale = 1.0;
    bool typed_dependency_present = false;
    for (const auto& dependency : component->dependencies) {
        if (!dependency.edge_type.empty() && dependency.edge_type != "generic") {
            typed_dependency_present = true;
        }
    }
    scale += 0.025 * std::min<std::size_t>(component->dependencies.size(), 4U);
    if (typed_dependency_present) {
        scale += 0.035;
    }
    return std::clamp(scale, 1.0, 1.16);
}

double component_system_fragility_scale(
    const std::string& system,
    const DamageComponent* component
) {
    double scale = 1.0;
    if (system_is_crew_or_cockpit(system)) {
        scale = 1.16;
    } else if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
        scale = 1.08;
    } else if (component && component_is_hydraulic_supply_path(*component)) {
        scale = 1.10;
    } else if (system_is_air_control_surface(system)) {
        scale = 1.06;
    } else if (system_is_air_propulsion(system)) {
        scale = 1.02;
    } else if (system_is_air_fuel(system)) {
        scale = 1.01;
    } else if (system_is_air_structure(system)) {
        scale = 0.94;
    }
    if (component && component_is_fire_suppression_path(*component)) {
        scale *= 0.92;
    }
    return std::clamp(scale, 0.84, 1.20);
}

struct PartFailureModeEntry {
    std::string mode;
    double severity = 0.0;
};

struct PartFailureModeAssessment {
    std::vector<PartFailureModeEntry> entries;
    std::string primary_mode;
    double primary_severity = 0.0;
    bool explicit_weights = false;
};

void populate_component_failure_mode_row(
    ComponentResponseRow& row,
    const PartFailureModeAssessment& assessment
) {
    row.failure_mode =
        assessment.primary_mode.empty() ? "none" : assessment.primary_mode;
    row.failure_severity =
        std::clamp(assessment.primary_severity, 0.0, 1.0);
    row.failure_mode_names.clear();
    row.failure_mode_severities.clear();
    row.failure_mode_names.reserve(assessment.entries.size());
    row.failure_mode_severities.reserve(assessment.entries.size());
    for (const auto& entry : assessment.entries) {
        row.failure_mode_names.push_back(entry.mode);
        row.failure_mode_severities.push_back(
            std::clamp(entry.severity, 0.0, 1.0));
    }
    row.failure_mode_source = assessment.entries.empty()
        ? "none"
        : (assessment.explicit_weights
            ? "component_failure_mode_weights"
            : "synthetic_inferred_part_failure_modes");
    row.failure_mode_authority = false;
}

double inferred_part_failure_mode_weight(
    const std::string& mode,
    const std::string& system,
    const DamageComponent* component
) {
    const std::string component_name =
        component ? damage_component_key(*component) : std::string{};
    const std::string group_key =
        component ? damage_component_redundancy_group_key(*component) : std::string{};

    if (mode == "puncture") {
        if (system_is_air_fuel(system) ||
            system_is_air_propulsion(system) ||
            system_is_air_sensor(system) ||
            system_name_matches(system, "avionics") ||
            system_name_matches(system, "data_link") ||
            system_name_matches(system, "hydraulic")) {
            return 1.0;
        }
        return system_is_air_structure(system) ? 0.70 : 0.45;
    }
    if (mode == "cut") {
        if (system_is_air_control_surface(system) ||
            system_is_air_structure(system) ||
            system_is_air_propulsion(system) ||
            system_is_air_fuel(system) ||
            system_name_matches(component_name, "spar") ||
            system_name_matches(component_name, "propeller")) {
            return 1.0;
        }
        return 0.35;
    }
    if (mode == "blast_deformation") {
        if (system_is_air_structure(system) ||
            system_is_air_control_surface(system) ||
            system_is_air_propulsion(system) ||
            system_is_air_sensor(system) ||
            system_name_matches(system, "avionics")) {
            return 1.0;
        }
        return 0.55;
    }
    if (mode == "fuel_leak") {
        return system_is_air_fuel(system) ? 1.0 : 0.0;
    }
    if (mode == "hydraulic_pressure_loss") {
        const bool named_control_actuator =
            system_is_air_control_surface(system) &&
            (system_name_matches(component_name, "actuator") ||
             system_name_matches(component_name, "servo") ||
             system_name_matches(component_name, "cyclic") ||
             system_name_matches(component_name, "collective"));
        if (component && (component_is_hydraulic_supply_path(*component) ||
                          named_control_actuator)) {
            return 1.0;
        }
        return system_name_matches(system, "hydraulic") ? 1.0 : 0.0;
    }
    if (mode == "electrical_loss") {
        if (system_name_matches(system, "avionics") ||
            system_name_matches(system, "electrical") ||
            system_name_matches(system, "power") ||
            system_name_matches(component_name, "power") ||
            system_name_matches(component_name, "generator") ||
            system_name_matches(group_key, "power")) {
            return 1.0;
        }
        return 0.0;
    }
    if (mode == "data_loss") {
        if (system_is_air_sensor(system) ||
            system_name_matches(system, "data_link") ||
            system_name_matches(system, "avionics") ||
            system_name_matches(system, "command") ||
            system_name_matches(system, "navigation")) {
            return 1.0;
        }
        return 0.0;
    }
    if (mode == "fire_source") {
        if (system_is_air_fuel(system) ||
            system_is_air_propulsion(system) ||
            system_name_matches(system, "avionics") ||
            system_name_matches(system, "electrical") ||
            system_name_matches(system, "power") ||
            system_name_matches(component_name, "power") ||
            system_name_matches(component_name, "generator")) {
            return 1.0;
        }
        return 0.0;
    }
    if (mode == "structural_weakening") {
        if (system_is_air_structure(system) ||
            system_is_air_propulsion(system) ||
            system_name_matches(component_name, "spar") ||
            system_name_matches(component_name, "hub") ||
            system_name_matches(component_name, "mount")) {
            return 1.0;
        }
        return 0.0;
    }
    return 0.0;
}

double part_failure_mode_weight(
    const std::string& mode,
    const std::string& system,
    const DamageComponent* component
) {
    if (component && !component->failure_mode_weights.empty()) {
        const auto it = component->failure_mode_weights.find(mode);
        return it == component->failure_mode_weights.end()
            ? 0.0
            : std::clamp(it->second, 0.0, 2.0);
    }
    return inferred_part_failure_mode_weight(mode, system, component);
}

void add_part_failure_mode(
    PartFailureModeAssessment& assessment,
    const std::string& raw_mode,
    double raw_severity,
    const std::string& system,
    const DamageComponent* component
) {
    const std::string mode = canonical_part_failure_mode(raw_mode);
    if (!is_known_part_failure_mode(mode)) {
        return;
    }
    const double weight = part_failure_mode_weight(mode, system, component);
    const double severity = std::clamp(raw_severity * weight, 0.0, 1.0);
    if (severity <= 0.015) {
        return;
    }
    for (auto& entry : assessment.entries) {
        if (entry.mode == mode) {
            entry.severity = std::max(entry.severity, severity);
            if (entry.severity > assessment.primary_severity) {
                assessment.primary_mode = entry.mode;
                assessment.primary_severity = entry.severity;
            }
            return;
        }
    }
    assessment.entries.push_back({mode, severity});
    if (severity > assessment.primary_severity) {
        assessment.primary_mode = mode;
        assessment.primary_severity = severity;
    }
}

PartFailureModeAssessment assess_part_failure_modes(
    double failure_probability,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load,
    const std::string& system,
    const DamageComponent* component
) {
    PartFailureModeAssessment assessment{};
    assessment.explicit_weights =
        component && !component->failure_mode_weights.empty();
    const double fragment_load = std::clamp(
        std::log1p(std::max(0.0, mechanism_load.fragment_energy_j)) / std::log(2501.0),
        0.0,
        1.35);
    const double density_load = std::clamp(
        mechanism_load.fragment_areal_density_per_m2 / 140.0,
        0.0,
        1.35);
    const double penetration_load =
        std::clamp(mechanism_load.penetration_margin / 2.0, 0.0, 1.35);
    const double blast_load = std::clamp(
        (mechanism_load.blast_overpressure_kpa / 240.0) +
            (mechanism_load.blast_impulse_kpa_ms / 850.0),
        0.0,
        1.35);
    const double rod_load =
        std::clamp(mechanism_load.rod_cut_margin / 1.6, 0.0, 1.35);
    const double incidence_load = std::clamp(
        0.45 + 0.55 * std::max(0.0, mechanism_load.surface_incidence_cos),
        0.45,
        1.0);
    const double part_coupling = std::clamp(
        (direct_hit ? 0.30 : 0.16) +
            0.46 * std::clamp(failure_probability, 0.0, 1.0) +
            0.16 * std::clamp(mechanism_scale, 0.0, 1.25) +
            0.08 * std::clamp(component_scale, 0.40, 1.80),
        0.0,
        1.0);
    const double puncture_channel = std::clamp(
        0.42 * fragment_load +
            0.24 * density_load +
            0.24 * penetration_load +
            0.10 * incidence_load,
        0.0,
        1.45);
    const double cut_channel = std::clamp(
        0.66 * rod_load +
            0.24 * penetration_load +
            0.10 * incidence_load,
        0.0,
        1.45);
    const double blast_channel = std::clamp(
        0.82 * blast_load +
            0.10 * fragment_load +
            0.08 * incidence_load,
        0.0,
        1.45);
    const double puncture = smoothstep01(puncture_channel / 0.95) * part_coupling;
    const double cut = smoothstep01(cut_channel / 0.92) * part_coupling;
    const double blast_deformation =
        smoothstep01(blast_channel / 0.90) * part_coupling;
    const double breach = std::max({puncture, cut, 0.45 * blast_deformation});
    const double power_data_damage =
        std::max({0.65 * puncture, 0.55 * cut, 0.85 * blast_deformation});
    const double thermal_source =
        std::max({0.65 * puncture, 0.50 * cut, 0.75 * blast_deformation});
    const double structural_damage =
        std::max({0.45 * puncture, 0.85 * cut, 0.80 * blast_deformation});

    add_part_failure_mode(assessment, "puncture", puncture, system, component);
    add_part_failure_mode(assessment, "cut", cut, system, component);
    add_part_failure_mode(
        assessment,
        "blast_deformation",
        blast_deformation,
        system,
        component);
    add_part_failure_mode(
        assessment,
        "fuel_leak",
        breach,
        system,
        component);
    add_part_failure_mode(
        assessment,
        "hydraulic_pressure_loss",
        std::max(0.72 * breach, 0.55 * cut),
        system,
        component);
    add_part_failure_mode(
        assessment,
        "electrical_loss",
        power_data_damage,
        system,
        component);
    add_part_failure_mode(
        assessment,
        "data_loss",
        power_data_damage,
        system,
        component);
    add_part_failure_mode(
        assessment,
        "fire_source",
        thermal_source,
        system,
        component);
    add_part_failure_mode(
        assessment,
        "structural_weakening",
        structural_damage,
        system,
        component);
    return assessment;
}

bool is_structural_part_failure_mode(const std::string& mode) {
    return mode == "puncture" || mode == "cut" || mode == "blast_deformation" ||
           mode == "structural_weakening";
}

PartFailureModeAssessment structural_part_failure_modes(
    const PartFailureModeAssessment& assessment
) {
    PartFailureModeAssessment structural_assessment{};
    structural_assessment.explicit_weights = assessment.explicit_weights;
    for (const auto& entry : assessment.entries) {
        if (!is_structural_part_failure_mode(entry.mode)) {
            continue;
        }
        structural_assessment.entries.push_back(entry);
        if (entry.severity > structural_assessment.primary_severity) {
            structural_assessment.primary_mode = entry.mode;
            structural_assessment.primary_severity = entry.severity;
        }
    }
    return structural_assessment;
}

double component_failure_probability(
    double severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load,
    const std::string& system,
    const DamageComponent* component,
    const ComponentFragilityRuntimeState& runtime_state
) {
    const double fragment_load = std::clamp(
        std::log1p(std::max(0.0, mechanism_load.fragment_energy_j)) / std::log(2501.0),
        0.0,
        1.35);
    const double density_load = std::clamp(
        mechanism_load.fragment_areal_density_per_m2 / 140.0,
        0.0,
        1.35);
    const double penetration_load =
        std::clamp(mechanism_load.penetration_margin / 2.0, 0.0, 1.35);
    const double blast_load = std::clamp(
        (mechanism_load.blast_overpressure_kpa / 240.0) +
            (mechanism_load.blast_impulse_kpa_ms / 850.0),
        0.0,
        1.35);
    const double rod_load =
        std::clamp(mechanism_load.rod_cut_margin / 1.6, 0.0, 1.35);
    const double incidence_load = std::clamp(
        0.45 + 0.55 * std::max(0.0, mechanism_load.surface_incidence_cos),
        0.45,
        1.0);
    const double fragment_channel = std::clamp(
        0.34 * fragment_load +
            0.22 * density_load +
            0.30 * penetration_load +
            0.14 * incidence_load,
        0.0,
        1.45);
    const double blast_channel = std::clamp(
        0.76 * blast_load +
            0.14 * fragment_load +
            0.10 * incidence_load,
        0.0,
        1.45);
    const double rod_channel = std::clamp(
        0.68 * rod_load +
            0.22 * penetration_load +
            0.10 * incidence_load,
        0.0,
        1.45);
    const double dominant_channel = std::max({fragment_channel, blast_channel, rod_channel});
    const double support_channel =
        fragment_channel + blast_channel + rod_channel - dominant_channel -
        std::min({fragment_channel, blast_channel, rod_channel});
    const double mechanism_load_scale = std::clamp(
        0.62 +
            0.24 * dominant_channel +
            0.10 * support_channel +
            0.04 * incidence_load,
        0.55,
        1.45);
    const double failed_fraction = runtime_state.group_member_count == 0
        ? 0.0
        : static_cast<double>(runtime_state.group_failed_count) /
            static_cast<double>(runtime_state.group_member_count);
    const double pre_damage_scale = std::clamp(
        1.0 +
            0.32 * (1.0 - std::clamp(runtime_state.integrity, 0.0, 1.0)) +
            0.18 * (1.0 - std::clamp(runtime_state.group_availability, 0.0, 1.0)) +
            0.06 * std::clamp(failed_fraction, 0.0, 1.0),
        1.0,
        1.55);
    const double impulse =
        std::clamp(severity, 0.0, 1.0) *
        std::clamp(mechanism_scale, 0.0, 1.25) *
        std::clamp(component_scale, 0.40, 1.60) *
        mechanism_load_scale *
        component_system_fragility_scale(system, component) *
        component_dependency_complexity_scale(component) *
        pre_damage_scale;
    const double threshold = direct_hit ? 0.40 : 0.56;
    const double spread = direct_hit ? 0.58 : 0.68;
    const double band =
        smoothstep01((impulse - (threshold - 0.12)) / spread);
    const double probability_floor = direct_hit ? 0.02 : 0.0;
    const double probability_ceiling = direct_hit ? 0.92 : 0.68;
    double probability =
        probability_floor + (probability_ceiling - probability_floor) * band;
    if (direct_hit) {
        const double direct_load_response = smoothstep01(dominant_channel / 0.62);
        const double direct_component_response = std::clamp(
            0.90 + 0.10 * component_system_fragility_scale(system, component),
            0.82,
            1.08);
        const double direct_load_floor =
            (0.22 + 0.46 * direct_load_response) * direct_component_response;
        probability = std::max(probability, direct_load_floor);
    }
    if (!direct_hit) {
        const double normalized_impulse =
            std::clamp(impulse / std::max(0.15, threshold), 0.0, 1.0);
        const double subthreshold_tail =
            0.05 *
            smoothstep01(normalized_impulse) *
            smoothstep01(dominant_channel / 0.55) *
            std::clamp(
                0.90 + 0.10 * component_system_fragility_scale(system, component),
                0.80,
                1.08);
        probability = std::max(probability, subthreshold_tail);
        const double fragment_breach_response =
            smoothstep01(density_load / 0.04) *
            smoothstep01((fragment_load + penetration_load) / 0.85);
        const double blast_response = smoothstep01(blast_load / 0.55);
        const double rod_cut_response =
            smoothstep01(rod_load / 0.45) *
            smoothstep01((penetration_load + incidence_load) / 0.90);
        const double proximity_load_response =
            std::max({fragment_breach_response, blast_response, rod_cut_response});
        const double projection_scale = std::clamp(mechanism_scale, 0.0, 1.25);
        const double proximity_projection_response =
            smoothstep01((projection_scale - 0.12) / 0.58);
        const double close_projection_response =
            smoothstep01((projection_scale - 0.24) / 0.36);
        const double mechanism_intensity_response =
            smoothstep01((dominant_channel - 0.18) / 0.62);
        const double proximity_response = std::clamp(
            (0.65 * proximity_load_response) +
                (0.35 * mechanism_intensity_response),
            0.0,
            1.0);
        const double proximity_component_response = std::clamp(
            0.92 + 0.08 * component_system_fragility_scale(system, component),
            0.86,
            1.06);
        const double proximity_pre_damage_response = std::clamp(
            0.86 + 0.14 * pre_damage_scale,
            1.0,
            1.08);
        const double proximity_tail_ceiling =
            0.12 + 0.52 * close_projection_response;
        const double proximity_tail =
            proximity_tail_ceiling *
            proximity_response *
            (0.45 + 0.55 * proximity_projection_response) *
            proximity_component_response *
            proximity_pre_damage_response;
        probability = std::max(probability, proximity_tail);
    }
    if (impulse > threshold) {
        probability +=
            (direct_hit ? 0.04 : 0.03) *
            (1.0 - std::exp(-2.8 * (impulse - threshold)));
    }
    return std::clamp(
        probability,
        probability_floor,
        direct_hit ? 0.95 : 0.72);
}

double component_primary_priority_score(
    double failure_probability,
    double mechanism_scale,
    double component_scale,
    bool direct_hit
) {
    const double consequence_scale =
        std::clamp(mechanism_scale, 0.05, 1.25) *
        std::sqrt(std::clamp(component_scale, 0.40, 1.80));
    return
        std::clamp(failure_probability, 0.0, 1.0) *
        consequence_scale *
        (direct_hit ? 1.05 : 1.0);
}

void apply_component_failure_impulse(
    const std::string& system,
    double probability,
    double component_scale,
    double mechanism_scale,
    bool engine_fuel_feed_path,
    bool fire_suppression_path,
    bool lateral_fuel_storage_path,
    bool hydraulic_supply_path,
    bool hydraulic_consumer_path,
    AircraftDamageState* aircraft_damage,
    PlatformDamageState* platform_damage
) {
    if (!aircraft_damage && !platform_damage) {
        return;
    }
    const double impulse = std::clamp(probability * component_scale * mechanism_scale, 0.0, 1.0);
    if (aircraft_damage) {
        if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
            aircraft_damage->avionics_integrity -= 0.10 + 0.12 * impulse;
            aircraft_damage->fire_severity += 0.015 + 0.025 * impulse;
            aircraft_damage->ignition_source_severity += 0.03 + 0.08 * impulse;
        }
        if (system_is_air_propulsion(system)) {
            aircraft_damage->propulsion_integrity -= 0.08 + 0.14 * impulse;
            aircraft_damage->ignition_source_severity += 0.03 + 0.09 * impulse;
        }
        if (system_is_air_fuel(system) && !fire_suppression_path) {
            aircraft_damage->fuel_system_integrity -= 0.08 + 0.12 * impulse;
            aircraft_damage->fuel_leak_severity += 0.06 + 0.12 * impulse;
            aircraft_damage->fire_severity += 0.02 + 0.06 * impulse;
            aircraft_damage->flammable_fluid_exposure += 0.05 + 0.14 * impulse;
            if (lateral_fuel_storage_path) {
                aircraft_damage->fuel_imbalance_severity += 0.04 + 0.12 * impulse;
                aircraft_damage->control_asymmetry += 0.006 + 0.018 * impulse;
            }
        }
        if (engine_fuel_feed_path && system_is_air_fuel(system)) {
            aircraft_damage->propulsion_integrity -= 0.06 + 0.12 * impulse;
            aircraft_damage->flammable_fluid_exposure += 0.02 + 0.08 * impulse;
            aircraft_damage->ignition_source_severity += 0.02 + 0.05 * impulse;
        }
        if (system_is_air_control_surface(system)) {
            aircraft_damage->flight_control_integrity -= 0.045 + 0.08 * impulse;
            aircraft_damage->hydraulic_integrity -= 0.045 + 0.08 * impulse;
            if (system_name_matches(system, "hydraulic")) {
                aircraft_damage->hydraulic_pressure_availability -= 0.06 + 0.12 * impulse;
                aircraft_damage->flammable_fluid_exposure += 0.02 + 0.06 * impulse;
            }
        }
        if (hydraulic_supply_path) {
            aircraft_damage->hydraulic_pressure_availability -= 0.12 + 0.20 * impulse;
            aircraft_damage->hydraulic_integrity -= 0.04 + 0.08 * impulse;
            aircraft_damage->flammable_fluid_exposure += 0.03 + 0.08 * impulse;
        } else if (hydraulic_consumer_path) {
            aircraft_damage->hydraulic_pressure_availability -= 0.035 + 0.08 * impulse;
            aircraft_damage->flammable_fluid_exposure += 0.01 + 0.04 * impulse;
        }
        if (system_is_crew_or_cockpit(system)) {
            apply_aircraft_crew_consequence(
                *aircraft_damage,
                classify_crew_consequence(system, ""),
                0.12 + 0.16 * impulse);
        }
        if (system_is_command_navigation(system)) {
            apply_aircraft_crew_consequence(
                *aircraft_damage,
                CrewConsequenceKind::CommandNavigation,
                0.08 + 0.12 * impulse);
        }
        if (system_is_mission_crew_station(system)) {
            apply_aircraft_crew_consequence(
                *aircraft_damage,
                CrewConsequenceKind::MissionCrew,
                0.07 + 0.11 * impulse);
        }
        if (system_is_air_structure(system)) {
            aircraft_damage->structural_integrity -= 0.06 + 0.10 * impulse;
            aircraft_damage->structural_overstress += 0.02 + 0.04 * impulse;
        }
    }
    if (platform_damage) {
        if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
            platform_damage->sensor_capability -= 0.04 + 0.08 * impulse;
            platform_damage->mission_capability -= 0.03 + 0.06 * impulse;
        }
        if (system_is_air_propulsion(system) || system_is_air_control_surface(system) ||
            (engine_fuel_feed_path && system_is_air_fuel(system))) {
            platform_damage->mobility_capability -= 0.05 + 0.08 * impulse;
        }
        if (system_is_crew_or_cockpit(system)) {
            platform_damage->mission_capability -= 0.05 + 0.10 * impulse;
        }
        if (system_is_air_structure(system) || system_is_air_fuel(system) ||
            fire_suppression_path || system_is_air_fire_suppression(system)) {
            platform_damage->survivability_margin -= 0.04 + 0.08 * impulse;
        }
    }
}

void persist_part_failure_mode_state(
    const DamageComponent* component,
    const PartFailureModeAssessment& assessment,
    ComponentDamageState* component_damage
) {
    if (!component || !component_damage || assessment.entries.empty()) {
        return;
    }

    const std::string component_key = damage_component_key(*component);
    auto& mode_severity =
        component_damage->component_failure_mode_severity[component_key];
    for (const auto& entry : assessment.entries) {
        double& accumulated = mode_severity[entry.mode];
        accumulated = std::max(accumulated, std::clamp(entry.severity, 0.0, 1.0));
    }
    if (!assessment.primary_mode.empty()) {
        component_damage->component_primary_failure_mode[component_key] =
            assessment.primary_mode;
    }
}

void apply_part_failure_mode_state(
    const std::string& system,
    const DamageComponent* component,
    const PartFailureModeAssessment& assessment,
    ComponentDamageState* component_damage,
    AircraftDamageState* aircraft_damage,
    PlatformDamageState* platform_damage
) {
    if (assessment.entries.empty()) {
        return;
    }

    if (component && component_damage) {
        const std::string component_key = damage_component_key(*component);
        auto& mode_severity =
            component_damage->component_failure_mode_severity[component_key];
        for (const auto& entry : assessment.entries) {
            double& accumulated = mode_severity[entry.mode];
            accumulated = std::max(accumulated, std::clamp(entry.severity, 0.0, 1.0));
        }
        if (!assessment.primary_mode.empty()) {
            component_damage->component_primary_failure_mode[component_key] =
                assessment.primary_mode;
        }
    }

    if (!assessment.explicit_weights) {
        if (aircraft_damage && component && system_is_air_structure(system)) {
            for (const auto& entry : assessment.entries) {
                if (entry.mode != "structural_weakening") {
                    continue;
                }
                const double impulse = std::clamp(entry.severity, 0.0, 1.0);
                if (impulse > 1.0e-9) {
                    aircraft_damage->flutter_exposure += 0.01 + 0.05 * impulse;
                }
            }
        }
        return;
    }

    for (const auto& entry : assessment.entries) {
        const double impulse = std::clamp(entry.severity, 0.0, 1.0);
        if (impulse <= 1.0e-9) {
            continue;
        }

        if (aircraft_damage) {
            if (entry.mode == "puncture") {
                if (system_is_air_fuel(system)) {
                    aircraft_damage->fuel_leak_severity += 0.03 + 0.09 * impulse;
                    aircraft_damage->flammable_fluid_exposure += 0.02 + 0.06 * impulse;
                }
                if (system_is_air_propulsion(system)) {
                    aircraft_damage->propulsion_integrity -= 0.02 + 0.06 * impulse;
                    aircraft_damage->ignition_source_severity += 0.01 + 0.04 * impulse;
                }
                if (system_is_air_structure(system)) {
                    aircraft_damage->structural_integrity -= 0.015 + 0.05 * impulse;
                }
                if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
                    aircraft_damage->avionics_integrity -= 0.015 + 0.04 * impulse;
                }
            } else if (entry.mode == "cut") {
                if (system_is_air_control_surface(system)) {
                    aircraft_damage->flight_control_integrity -= 0.025 + 0.08 * impulse;
                    aircraft_damage->hydraulic_pressure_availability -= 0.015 + 0.06 * impulse;
                }
                if (system_is_air_propulsion(system)) {
                    aircraft_damage->propulsion_integrity -= 0.025 + 0.07 * impulse;
                }
                aircraft_damage->structural_integrity -= 0.015 + 0.05 * impulse;
                aircraft_damage->structural_overstress += 0.01 + 0.04 * impulse;
            } else if (entry.mode == "blast_deformation") {
                aircraft_damage->structural_integrity -= 0.02 + 0.06 * impulse;
                aircraft_damage->structural_overstress += 0.015 + 0.05 * impulse;
                if (system_is_air_control_surface(system)) {
                    aircraft_damage->flight_control_integrity -= 0.015 + 0.05 * impulse;
                    aircraft_damage->control_asymmetry += 0.004 + 0.014 * impulse;
                }
                if (system_is_air_propulsion(system)) {
                    aircraft_damage->propulsion_integrity -= 0.015 + 0.05 * impulse;
                }
            } else if (entry.mode == "fuel_leak") {
                aircraft_damage->fuel_system_integrity -= 0.035 + 0.08 * impulse;
                aircraft_damage->fuel_leak_severity += 0.05 + 0.16 * impulse;
                aircraft_damage->flammable_fluid_exposure += 0.04 + 0.12 * impulse;
                if (component && component_is_lateral_fuel_storage_path(*component)) {
                    aircraft_damage->fuel_imbalance_severity += 0.03 + 0.09 * impulse;
                    aircraft_damage->control_asymmetry += 0.004 + 0.015 * impulse;
                }
            } else if (entry.mode == "hydraulic_pressure_loss") {
                aircraft_damage->hydraulic_pressure_availability -= 0.06 + 0.16 * impulse;
                aircraft_damage->hydraulic_integrity -= 0.025 + 0.08 * impulse;
                aircraft_damage->flight_control_integrity -= 0.025 + 0.07 * impulse;
                aircraft_damage->flammable_fluid_exposure += 0.015 + 0.05 * impulse;
            } else if (entry.mode == "electrical_loss") {
                aircraft_damage->avionics_integrity -= 0.045 + 0.11 * impulse;
                aircraft_damage->command_navigation_integrity -= 0.02 + 0.07 * impulse;
                aircraft_damage->ignition_source_severity += 0.01 + 0.04 * impulse;
            } else if (entry.mode == "data_loss") {
                aircraft_damage->avionics_integrity -= 0.035 + 0.08 * impulse;
                aircraft_damage->command_navigation_integrity -= 0.04 + 0.10 * impulse;
                aircraft_damage->mission_crew_effectiveness -= 0.01 + 0.03 * impulse;
            } else if (entry.mode == "fire_source") {
                aircraft_damage->ignition_source_severity += 0.04 + 0.14 * impulse;
                aircraft_damage->fire_severity += 0.02 + 0.08 * impulse;
                if (system_is_air_fuel(system)) {
                    aircraft_damage->flammable_fluid_exposure += 0.02 + 0.07 * impulse;
                }
            } else if (entry.mode == "structural_weakening") {
                aircraft_damage->structural_integrity -= 0.035 + 0.11 * impulse;
                aircraft_damage->structural_overstress += 0.02 + 0.08 * impulse;
                aircraft_damage->flutter_exposure += 0.01 + 0.05 * impulse;
            }
        }

        if (platform_damage) {
            if (entry.mode == "fuel_leak" || entry.mode == "fire_source" ||
                entry.mode == "structural_weakening" ||
                entry.mode == "blast_deformation") {
                platform_damage->survivability_margin -= 0.015 + 0.05 * impulse;
            }
            if (entry.mode == "hydraulic_pressure_loss" ||
                (entry.mode == "cut" && system_is_air_control_surface(system))) {
                platform_damage->mobility_capability -= 0.015 + 0.05 * impulse;
            }
            if (entry.mode == "data_loss" || entry.mode == "electrical_loss") {
                platform_damage->mission_capability -= 0.015 + 0.05 * impulse;
                platform_damage->sensor_capability -= 0.01 + 0.04 * impulse;
            }
            if (entry.mode == "fire_source") {
                platform_damage->fire_severity += 0.015 + 0.05 * impulse;
            }
        }
    }
}

void apply_control_axis_component_damage(
    const DamageComponent& component,
    double base_severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    AircraftDamageState* aircraft_damage
) {
    if (!aircraft_damage || !system_is_air_control_surface(component.system)) {
        return;
    }

    const std::string& component_name =
        component.name.empty() ? component.system : component.name;
    const bool side_specific =
        system_name_matches(component_name, "left") ||
        system_name_matches(component_name, "right");
    const bool aileron_like =
        system_name_matches(component_name, "aileron") ||
        system_name_matches(component_name, "elevon") ||
        system_name_matches(component_name, "flaperon");
    const bool elevator_like =
        system_name_matches(component_name, "elevator") ||
        system_name_matches(component_name, "horizontal_tail") ||
        system_name_matches(component_name, "stabilator") ||
        system_name_matches(component_name, "elevon");
    const bool flap_like = system_name_matches(component_name, "flap");
    const bool spoiler_like = system_name_matches(component_name, "spoiler");
    const bool thrust_vector_like =
        system_name_matches(component_name, "thrust_vector") ||
        system_name_matches(component_name, "vector_actuator");
    const bool cyclic_like = system_name_matches(component_name, "cyclic");
    const bool collective_like = system_name_matches(component_name, "collective");
    const bool rudder_like = system_name_matches(component_name, "rudder");

    double roll_weight = 0.0;
    double pitch_weight = 0.0;
    double yaw_weight = 0.0;
    if (aileron_like) {
        roll_weight = std::max(roll_weight, 1.0);
    }
    if (spoiler_like) {
        roll_weight = std::max(roll_weight, 0.85);
    }
    if (flap_like && side_specific) {
        roll_weight = std::max(roll_weight, 0.55);
    }
    if (cyclic_like) {
        roll_weight = std::max(roll_weight, 0.80);
    }
    if (elevator_like) {
        pitch_weight = std::max(pitch_weight, 0.70);
    }
    if (flap_like) {
        pitch_weight = std::max(pitch_weight, 0.55);
    }
    if (thrust_vector_like) {
        pitch_weight = std::max(pitch_weight, 0.75);
        yaw_weight = std::max(yaw_weight, 0.75);
    }
    if (cyclic_like) {
        pitch_weight = std::max(pitch_weight, 0.65);
    }
    if (collective_like) {
        pitch_weight = std::max(pitch_weight, 0.80);
    }
    if (rudder_like) {
        yaw_weight = std::max(yaw_weight, 1.0);
    }
    if (roll_weight <= 0.0 && pitch_weight <= 0.0 && yaw_weight <= 0.0) {
        return;
    }

    const double impulse = std::clamp(
        base_severity *
            std::clamp(mechanism_scale, 0.0, 1.25) *
            std::clamp(component_scale, 0.40, 1.80),
        0.0,
        1.0);
    const double axis_loss = (direct_hit ? 0.08 : 0.03) +
        ((direct_hit ? 0.18 : 0.10) * impulse);

    if (roll_weight > 0.0) {
        const double roll_loss = axis_loss * roll_weight;
        aircraft_damage->roll_control_integrity -= roll_loss;
        aircraft_damage->control_asymmetry +=
            (side_specific ? 1.05 : 0.45) * roll_loss;
    }
    if (pitch_weight > 0.0) {
        aircraft_damage->pitch_control_integrity -= pitch_weight * axis_loss;
    }
    if (yaw_weight > 0.0) {
        const double yaw_loss = axis_loss * yaw_weight;
        aircraft_damage->yaw_control_integrity -= yaw_loss;
        aircraft_damage->control_asymmetry +=
            (side_specific || thrust_vector_like ? 0.75 : 0.55) * yaw_loss;
    }
}

struct ComponentDamageSample {
    double integrity_before = 1.0;
    double integrity_after = 1.0;
    double integrity = 1.0;
    double group_availability_before = 1.0;
    double group_availability_after = 1.0;
    double group_availability = 1.0;
    std::uint32_t group_member_count = 0;
    std::uint32_t group_failed_count = 0;
};

struct ComponentDependencyPropagationSummary {
    std::uint32_t propagation_count = 0;
    std::string target_system;
    std::string edge_type = "none";
    double threshold = 1.0;
    double delay_s = 0.0;
    std::string direction = "one_way";
    std::string provenance;
    double source_availability = 1.0;
    double effective_scale = 0.0;
    bool propagated = false;
};

ComponentDamageSample apply_component_damage_state(
    const DamageComponent& component,
    double failure_probability,
    double effect_scale,
    ComponentDamageState* component_damage,
    SystemHealth* sys_health
) {
    ComponentDamageSample sample{};
    if (!component_damage) {
        return sample;
    }

    const std::string component_key = damage_component_key(component);
    const std::string group_key = damage_component_redundancy_group_key(component);
    const auto integrity_it = component_damage->component_integrity.find(component_key);
    if (integrity_it == component_damage->component_integrity.end()) {
        component_damage->component_integrity[component_key] = 1.0;
        component_damage->component_redundancy_group[component_key] = group_key;
        component_damage->component_redundancy_weight[component_key] =
            std::clamp(component.redundancy_weight, 0.15, 2.50);
    }
    component_damage->component_system[component_key] = component.system;
    double& integrity = component_damage->component_integrity[component_key];
    sample.integrity_before = std::clamp(integrity, 0.0, 1.0);
    if (const auto availability_it =
            component_damage->redundancy_group_availability.find(group_key);
        availability_it != component_damage->redundancy_group_availability.end()) {
        sample.group_availability_before =
            std::clamp(availability_it->second, 0.0, 1.0);
    }

    const double weight = std::clamp(component.redundancy_weight, 0.15, 2.50);
    const double directness = component.critical ? 1.0 : 0.68;
    const double integrity_loss = std::clamp(
        (0.04 + 0.32 * std::clamp(failure_probability, 0.0, 1.0)) *
            std::clamp(effect_scale, 0.05, 1.20) *
            directness / weight,
        0.0,
        0.65);
    integrity = std::clamp(integrity - integrity_loss, 0.0, 1.0);

    if (component_damage->redundancy_group_member_count[group_key] == 0) {
        component_damage->redundancy_group_member_count[group_key] = 1;
    }

    double total_weight = 0.0;
    double live_weight = 0.0;
    std::uint32_t failed_count = 0;
    std::uint32_t observed_count = 0;
    for (const auto& [candidate_key, candidate_integrity] :
         component_damage->component_integrity) {
        const auto group_it = component_damage->component_redundancy_group.find(candidate_key);
        if (group_it == component_damage->component_redundancy_group.end() ||
            group_it->second != group_key) {
            continue;
        }
        ++observed_count;
        const auto weight_it = component_damage->component_redundancy_weight.find(candidate_key);
        const double candidate_weight = weight_it == component_damage->component_redundancy_weight.end()
            ? 1.0
            : std::clamp(weight_it->second, 0.15, 2.50);
        total_weight += candidate_weight;
        live_weight += std::max(0.0, candidate_integrity) * candidate_weight;
        if (candidate_integrity <= 0.35) {
            ++failed_count;
        }
    }

    const std::uint32_t member_count = std::max<std::uint32_t>(
        observed_count,
        std::max<std::uint32_t>(1U, component_damage->redundancy_group_member_count[group_key]));
    const double unknown_weight =
        observed_count < member_count ? static_cast<double>(member_count - observed_count) : 0.0;
    total_weight += unknown_weight;
    live_weight += unknown_weight;
    sample.group_availability_after =
        std::clamp(live_weight / std::max(total_weight, 1.0e-6), 0.0, 1.0);
    sample.group_availability = sample.group_availability_after;
    sample.group_member_count = member_count;
    sample.group_failed_count = failed_count;
    sample.integrity_after = std::clamp(integrity, 0.0, 1.0);
    sample.integrity = sample.integrity_after;

    component_damage->redundancy_group_availability[group_key] = sample.group_availability;
    component_damage->redundancy_group_failed_count[group_key] = sample.group_failed_count;
    if (sys_health && !component.system.empty()) {
        sys_health->systems[component.system] =
            std::min(sys_health->systems[component.system], sample.group_availability);
    }
    return sample;
}

std::string component_dependency_target_system(const DamageComponentDependency& dependency) {
    if (!dependency.target_system.empty()) {
        return dependency.target_system;
    }
    return dependency.system;
}

double component_dependency_source_availability(const ComponentDamageSample& sample) {
    return std::min(
        std::clamp(sample.integrity, 0.0, 1.0),
        std::clamp(sample.group_availability, 0.0, 1.0));
}

double component_dependency_edge_scale(
    const DamageComponentDependency& dependency,
    const std::string& target_system
) {
    const std::string& edge_type = dependency.edge_type;
    if (edge_type.empty() || edge_type == "generic") {
        return 1.0;
    }
    if (edge_type == "hydraulic_power" || edge_type == "hydraulic-power") {
        return system_name_matches(target_system, "hydraulic") ||
                system_is_air_control_surface(target_system)
            ? 1.05
            : 0.60;
    }
    if (edge_type == "electrical_power" || edge_type == "electrical-power" ||
        edge_type == "supply") {
        return system_name_matches(target_system, "avionics") ||
                system_is_mission_or_combat(target_system) ||
                system_is_air_control_surface(target_system)
            ? 1.00
            : 0.70;
    }
    if (edge_type == "control_signal" || edge_type == "control-signal") {
        return system_is_air_control_surface(target_system) ||
                system_name_matches(target_system, "avionics")
            ? 0.95
            : 0.55;
    }
    if (edge_type == "data_path" || edge_type == "data") {
        return system_name_matches(target_system, "data_link") ||
                system_name_matches(target_system, "avionics") ||
                system_is_mission_or_combat(target_system) ||
                system_is_air_sensor(target_system)
            ? 0.95
            : 0.45;
    }
    if (edge_type == "fuel_feed" || edge_type == "fuel-feed") {
        return system_is_air_fuel(target_system) || system_is_air_propulsion(target_system)
            ? 1.05
            : 0.55;
    }
    if (edge_type == "structural_support" || edge_type == "structural-support") {
        return system_is_air_structure(target_system) ||
                system_is_air_control_surface(target_system)
            ? 1.00
            : 0.60;
    }
    if (edge_type == "crew_operated" || edge_type == "crew-operated") {
        return system_is_crew_or_cockpit(target_system) ||
                system_is_mission_or_combat(target_system) ||
                system_name_matches(target_system, "flight_control")
            ? 0.90
            : 0.55;
    }
    return 1.0;
}

bool component_dependency_threshold_allows(
    const DamageComponentDependency& dependency,
    const ComponentDamageSample& sample
) {
    const double threshold = std::clamp(dependency.threshold, 0.0, 1.0);
    if (threshold >= 1.0) {
        return true;
    }
    return component_dependency_source_availability(sample) <= threshold;
}

ComponentDependencyPropagationSummary apply_component_dependency_damage(
    const DamageComponent& component,
    const ComponentDamageSample& sample,
    double failure_probability,
    double effect_scale,
    ComponentDamageState* component_damage,
    SystemHealth* sys_health,
    AircraftDamageState* aircraft_damage,
    PlatformDamageState* platform_damage
) {
    ComponentDependencyPropagationSummary summary{};
    if (component.dependencies.empty()) {
        return summary;
    }

    const double dependency_loss = std::clamp(
        (1.0 - sample.group_availability) +
            (0.20 * std::clamp(failure_probability, 0.0, 1.0)) +
            (0.10 * std::clamp(effect_scale, 0.0, 1.25)),
        0.0,
        0.85);
    if (dependency_loss <= 1.0e-6) {
        return summary;
    }

    for (const auto& dependency : component.dependencies) {
        const std::string target_system = component_dependency_target_system(dependency);
        if (target_system.empty()) {
            continue;
        }
        if (!component_dependency_threshold_allows(dependency, sample)) {
            continue;
        }
        const double dependency_scale =
            std::clamp(
                dependency.scale * component_dependency_edge_scale(dependency, target_system),
                0.05,
                2.0);
        const double availability = std::clamp(
            1.0 - dependency_loss * dependency_scale,
            0.0,
            1.0);
        const double impulse =
            std::clamp(dependency_loss * dependency_scale, 0.0, 1.0);
        ++summary.propagation_count;
        if (!summary.propagated || dependency_scale > summary.effective_scale) {
            summary.target_system = target_system;
            summary.edge_type = dependency.edge_type.empty() ? "generic" : dependency.edge_type;
            summary.threshold = std::clamp(dependency.threshold, 0.0, 1.0);
            summary.delay_s = std::max(0.0, dependency.delay_s);
            summary.direction = dependency.direction.empty() ? "one_way" : dependency.direction;
            summary.provenance = dependency.provenance;
            summary.source_availability = component_dependency_source_availability(sample);
            summary.effective_scale = dependency_scale;
            summary.propagated = true;
        }
        const double delay_s = std::max(0.0, dependency.delay_s);
        if (delay_s > 1.0e-6 && component_damage && aircraft_damage) {
            ComponentDamageState::PendingDependencyEffect pending{};
            pending.target_system = target_system;
            pending.edge_type = dependency.edge_type.empty() ? "generic" : dependency.edge_type;
            pending.remaining_delay_s = delay_s;
            pending.availability = availability;
            pending.impulse = impulse;
            pending.effective_scale = dependency_scale;
            pending.source_availability = component_dependency_source_availability(sample);
            pending.direction = dependency.direction.empty() ? "one_way" : dependency.direction;
            pending.provenance = dependency.provenance;
            component_damage->pending_dependency_effects.push_back(pending);
        } else {
            apply_damage_component_dependency_impulse(
                target_system,
                dependency.edge_type.empty() ? "generic" : dependency.edge_type,
                availability,
                impulse,
                sys_health,
                aircraft_damage,
                platform_damage);
        }
    }
    return summary;
}
