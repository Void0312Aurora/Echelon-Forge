#pragma once

#include <algorithm>
#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>

struct DamageComponentDependency {
    std::string system;
    std::string target_system;
    std::string edge_type = "generic";
    double scale = 1.0;
    double threshold = 1.0;
    double delay_s = 0.0;
    std::string direction = "one_way";
    std::string provenance = "synthetic_engineering";
};

struct DamageComponent {
    std::string name;
    std::string system;
    std::string redundancy_group_id;
    std::vector<DamageComponentDependency> dependencies;
    double offset_x = 0.0;
    double offset_y = 0.0;
    double offset_z = 0.0;
    double dim_l = 0.0;
    double dim_w = 0.0;
    double dim_h = 0.0;
    double armor_mm = 0.0;
    double threshold_scale = 1.0;
    std::unordered_map<std::string, double> mechanism_threshold_scales;
    double redundancy_group = 0.0;
    double redundancy_weight = 1.0;
    bool critical = true;
};

inline std::string damage_component_key(const DamageComponent& component) {
    if (!component.name.empty()) {
        return component.name;
    }
    if (!component.system.empty()) {
        return component.system;
    }
    return "unnamed_component";
}

inline std::string damage_component_redundancy_group_key(const DamageComponent& component) {
    if (!component.redundancy_group_id.empty()) {
        return component.redundancy_group_id;
    }
    if (component.redundancy_group > 0.0) {
        return component.system + ":rg:" + std::to_string(component.redundancy_group);
    }
    return damage_component_key(component);
}

// Geometric shape approximation (OBB/Box oriented aligned for now)
struct Hitbox {
    int id;
    // Relative position from unit center (Forward, Right, Up)
    double offset_x, offset_y, offset_z;
    // Dimensions (Length, Width, Height)
    double dim_l, dim_w, dim_h; 
    
    double armor_mm;
    
    // Critical systems protected by this box
    std::vector<std::string> protected_systems;
    std::vector<DamageComponent> components;
};

// Static Configuration (Shared Component candidate)
struct HitboxConfig {
    std::vector<Hitbox> hitboxes;
};

struct AircraftVulnerabilityEvidenceRow {
    std::string row_id;
    std::string source_ref;
    std::string provenance;
    std::string weapon_family;
    std::string aspect_bucket;
    std::string closure_bucket;
    std::string miss_distance_bucket;
    std::string component_name;
    std::string component_system;
    std::string component_redundancy_group_id;
    double family_scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    double effect_scale = 1.0;
    bool has_component_failure_probability = false;
    double component_failure_probability = 0.0;
    bool has_min_fragment_energy_j = false;
    double min_fragment_energy_j = 0.0;
    bool has_max_fragment_energy_j = false;
    double max_fragment_energy_j = 0.0;
    bool has_min_fragment_areal_density_per_m2 = false;
    double min_fragment_areal_density_per_m2 = 0.0;
    bool has_max_fragment_areal_density_per_m2 = false;
    double max_fragment_areal_density_per_m2 = 0.0;
    bool has_min_penetration_margin = false;
    double min_penetration_margin = 0.0;
    bool has_max_penetration_margin = false;
    double max_penetration_margin = 0.0;
    bool has_min_blast_overpressure_kpa = false;
    double min_blast_overpressure_kpa = 0.0;
    bool has_max_blast_overpressure_kpa = false;
    double max_blast_overpressure_kpa = 0.0;
    bool has_min_blast_impulse_kpa_ms = false;
    double min_blast_impulse_kpa_ms = 0.0;
    bool has_max_blast_impulse_kpa_ms = false;
    double max_blast_impulse_kpa_ms = 0.0;
    bool has_min_blast_scaled_distance_m_kg13 = false;
    double min_blast_scaled_distance_m_kg13 = 0.0;
    bool has_max_blast_scaled_distance_m_kg13 = false;
    double max_blast_scaled_distance_m_kg13 = 0.0;
    bool has_min_rod_cut_margin = false;
    double min_rod_cut_margin = 0.0;
    bool has_max_rod_cut_margin = false;
    double max_rod_cut_margin = 0.0;
    bool has_min_surface_incidence_cos = false;
    double min_surface_incidence_cos = 0.0;
    bool has_max_surface_incidence_cos = false;
    double max_surface_incidence_cos = 0.0;
};

struct AircraftVulnerabilityProfile {
    bool synthetic = true;
    bool calibrated = false;
    bool evidence_dataset_valid = false;
    bool effect_scale_authority = false;
    bool component_failure_probability_authority = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    std::string provenance = "synthetic_unvalidated_vulnerability";
    std::string evidence_dataset_ref;
    std::string calibration_status = "unvalidated";
    std::string evidence_schema_version;
    std::string evidence_source_kind;
    std::string evidence_source_ref;
    std::string evidence_validation_artifact_ref;
    std::string evidence_validation_manifest_schema_version;
    std::string evidence_validation_status;
    std::string evidence_validation_artifact_sha256;
    std::string evidence_validated_surrogate_model_ref;
    std::string evidence_validation_benchmark_ref;
    std::string evidence_validation_metrics_ref;
    std::string evidence_validation_acceptance_criteria_ref;
    std::vector<AircraftVulnerabilityEvidenceRow> evidence_rows;
    double blast_scale = 1.0;
    double fragmentation_scale = 1.0;
    double continuous_rod_scale = 1.0;
    double hit_to_kill_scale = 1.0;
    double nose_aspect_scale = 1.0;
    double beam_aspect_scale = 1.0;
    double tail_aspect_scale = 1.0;
    double high_closure_scale = 1.0;
    double low_closure_scale = 1.0;
    double near_miss_scale = 1.0;
    double direct_hit_scale = 1.0;
};

inline bool aircraft_vulnerability_has_calibrated_evidence(
    const AircraftVulnerabilityProfile& profile
) {
    return !profile.synthetic &&
        profile.calibrated &&
        profile.evidence_dataset_valid &&
        !profile.evidence_dataset_ref.empty() &&
        profile.calibration_status == "calibrated";
}

inline bool aircraft_vulnerability_pk_authority(
    const AircraftVulnerabilityProfile& profile
) {
    return aircraft_vulnerability_has_calibrated_evidence(profile) && profile.pk_authority;
}

inline bool aircraft_vulnerability_deterministic_fuze_authority(
    const AircraftVulnerabilityProfile& profile
) {
    return aircraft_vulnerability_has_calibrated_evidence(profile) &&
        profile.deterministic_fuze_authority;
}

// Runtime State
struct SystemHealth {
    // 0.0 = Dead, 1.0 = Fully Operational
    // Key: System Name (e.g., "radar", "engine", "flight_control")
    std::unordered_map<std::string, double> systems;
};

struct ComponentDamageState {
    std::unordered_map<std::string, double> component_integrity;
    std::unordered_map<std::string, std::string> component_redundancy_group;
    std::unordered_map<std::string, std::string> component_system;
    std::unordered_map<std::string, double> component_redundancy_weight;
    std::unordered_map<std::string, double> redundancy_group_availability;
    std::unordered_map<std::string, std::uint32_t> redundancy_group_member_count;
    std::unordered_map<std::string, std::uint32_t> redundancy_group_failed_count;
    struct PendingDependencyEffect {
        std::string target_system;
        std::string edge_type = "generic";
        double remaining_delay_s = 0.0;
        double availability = 1.0;
        double impulse = 0.0;
        double effective_scale = 0.0;
        double source_availability = 1.0;
        std::string direction = "one_way";
        std::string provenance = "synthetic_engineering";
    };
    std::vector<PendingDependencyEffect> pending_dependency_effects;
    bool has_fire_suppression_components = false;
};

enum class PlatformLossState : int {
    CombatCapable = 0,
    MissionKill = 1,
    MobilityKill = 2,
    SensorKill = 3,
    Lost = 4,
};

struct PlatformDamageState {
    double mission_capability = 1.0;
    double mobility_capability = 1.0;
    double sensor_capability = 1.0;
    double survivability_margin = 1.0;
    double flooding_severity = 0.0;
    double fire_severity = 0.0;
    double ongoing_hull_breach = 0.0;
    bool mission_kill = false;
    bool mobility_kill = false;
    bool sensor_kill = false;
    PlatformLossState loss_state = PlatformLossState::CombatCapable;
};

struct AircraftDamageState {
    double structural_integrity = 1.0;
    double flight_control_integrity = 1.0;
    double hydraulic_integrity = 1.0;
    double hydraulic_pressure_availability = 1.0;
    double roll_control_integrity = 1.0;
    double pitch_control_integrity = 1.0;
    double yaw_control_integrity = 1.0;
    double control_asymmetry = 0.0;
    double propulsion_integrity = 1.0;
    double fuel_system_integrity = 1.0;
    double avionics_integrity = 1.0;
    double crew_effectiveness = 1.0;
    double pilot_effectiveness = 1.0;
    double mission_crew_effectiveness = 1.0;
    double command_navigation_integrity = 1.0;
    double fire_severity = 0.0;
    double fuel_leak_severity = 0.0;
    double fuel_imbalance_severity = 0.0;
    double flammable_fluid_exposure = 0.0;
    double ignition_source_severity = 0.0;
    double fire_suppression_integrity = 1.0;
    double smoke_heat_exposure = 0.0;
    double engine_fire_zone_severity = 0.0;
    double wing_fire_zone_severity = 0.0;
    double fuselage_fire_zone_severity = 0.0;
    double mission_fire_zone_severity = 0.0;
    double structural_overstress = 0.0;
    double flutter_exposure = 0.0;
    bool forced_landing_required = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool crew_kill = false;
};

inline bool damage_dependency_system_name_matches(const std::string& system, const char* token) {
    return system.find(token) != std::string::npos;
}

inline bool damage_dependency_system_is_air_control_surface(const std::string& system) {
    return damage_dependency_system_name_matches(system, "flight_control") ||
        damage_dependency_system_name_matches(system, "control") ||
        damage_dependency_system_name_matches(system, "hydraulic");
}

inline bool damage_dependency_system_is_air_sensor(const std::string& system) {
    return damage_dependency_system_name_matches(system, "radar") ||
        damage_dependency_system_name_matches(system, "sensor") ||
        damage_dependency_system_name_matches(system, "rwr") ||
        damage_dependency_system_name_matches(system, "esm");
}

inline bool damage_dependency_system_is_air_propulsion(const std::string& system) {
    return damage_dependency_system_name_matches(system, "engineering") ||
        damage_dependency_system_name_matches(system, "engine") ||
        damage_dependency_system_name_matches(system, "propeller") ||
        damage_dependency_system_name_matches(system, "transmission");
}

inline bool damage_dependency_system_is_air_fuel(const std::string& system) {
    return damage_dependency_system_name_matches(system, "fuel");
}

inline bool damage_dependency_system_is_air_structure(const std::string& system) {
    return damage_dependency_system_name_matches(system, "wing") ||
        damage_dependency_system_name_matches(system, "airframe") ||
        damage_dependency_system_name_matches(system, "fuselage") ||
        damage_dependency_system_name_matches(system, "structure") ||
        damage_dependency_system_name_matches(system, "rotor") ||
        damage_dependency_system_name_matches(system, "tail");
}

inline bool damage_dependency_system_is_fire_suppression(const std::string& system) {
    return damage_dependency_system_name_matches(system, "fire_suppression") ||
        damage_dependency_system_name_matches(system, "fire_bottle") ||
        damage_dependency_system_name_matches(system, "suppression") ||
        damage_dependency_system_name_matches(system, "extinguish");
}

inline bool damage_dependency_system_is_mission_or_combat(const std::string& system) {
    return damage_dependency_system_name_matches(system, "combat") ||
        damage_dependency_system_name_matches(system, "command") ||
        damage_dependency_system_name_matches(system, "data_link") ||
        damage_dependency_system_name_matches(system, "vls") ||
        damage_dependency_system_name_matches(system, "gun") ||
        damage_dependency_system_name_matches(system, "radar") ||
        damage_dependency_system_name_matches(system, "avionics") ||
        damage_dependency_system_name_matches(system, "navigation") ||
        damage_dependency_system_name_matches(system, "mission");
}

inline bool damage_dependency_edge_is_fuel_feed(const std::string& edge_type) {
    return edge_type == "fuel_feed" || edge_type == "fuel-feed";
}

inline bool damage_dependency_edge_is_hydraulic_power(const std::string& edge_type) {
    return edge_type == "hydraulic_power" || edge_type == "hydraulic-power";
}

inline bool damage_dependency_edge_is_electrical_power(const std::string& edge_type) {
    return edge_type == "electrical_power" || edge_type == "electrical-power" ||
        edge_type == "supply";
}

inline bool damage_dependency_edge_is_data_path(const std::string& edge_type) {
    return edge_type == "data_path" || edge_type == "data";
}

inline bool damage_dependency_edge_is_control_signal(const std::string& edge_type) {
    return edge_type == "control_signal" || edge_type == "control-signal";
}

inline bool damage_dependency_edge_is_cooling(const std::string& edge_type) {
    return edge_type == "cooling";
}

inline bool damage_dependency_edge_is_crew_operated(const std::string& edge_type) {
    return edge_type == "crew_operated" || edge_type == "crew-operated";
}

inline bool damage_dependency_edge_is_structural_support(const std::string& edge_type) {
    return edge_type == "structural_support" || edge_type == "structural-support";
}

inline double damage_component_axis_availability(double availability, double axis_weight) {
    return std::clamp(
        1.0 - std::clamp(axis_weight, 0.0, 1.0) * (1.0 - std::clamp(availability, 0.0, 1.0)),
        0.0,
        1.0);
}

inline void derive_aircraft_damage_from_component_state(
    const ComponentDamageState& component_damage,
    AircraftDamageState& aircraft_damage
) {
    for (const auto& [component_key, integrity] : component_damage.component_integrity) {
        const auto system_it = component_damage.component_system.find(component_key);
        if (system_it == component_damage.component_system.end() ||
            system_it->second.empty()) {
            continue;
        }
        double availability = std::clamp(integrity, 0.0, 1.0);
        const auto group_it = component_damage.component_redundancy_group.find(component_key);
        if (group_it != component_damage.component_redundancy_group.end()) {
            const auto availability_it =
                component_damage.redundancy_group_availability.find(group_it->second);
            if (availability_it != component_damage.redundancy_group_availability.end()) {
                availability = std::clamp(availability_it->second, 0.0, 1.0);
            }
        }

        const std::string& system = system_it->second;
        if (damage_dependency_system_is_air_control_surface(system)) {
            aircraft_damage.flight_control_integrity =
                std::min(aircraft_damage.flight_control_integrity, availability);
            const bool side_specific =
                damage_dependency_system_name_matches(component_key, "left") ||
                damage_dependency_system_name_matches(component_key, "right");
            const bool aileron_like =
                damage_dependency_system_name_matches(component_key, "aileron") ||
                damage_dependency_system_name_matches(component_key, "elevon") ||
                damage_dependency_system_name_matches(component_key, "flaperon");
            const bool elevator_like =
                damage_dependency_system_name_matches(component_key, "elevator") ||
                damage_dependency_system_name_matches(component_key, "stabilator") ||
                damage_dependency_system_name_matches(component_key, "elevon");
            const bool flap_like =
                damage_dependency_system_name_matches(component_key, "flap");
            const bool spoiler_like =
                damage_dependency_system_name_matches(component_key, "spoiler");
            const bool thrust_vector_like =
                damage_dependency_system_name_matches(component_key, "thrust_vector") ||
                damage_dependency_system_name_matches(component_key, "vector_actuator");
            const bool cyclic_like =
                damage_dependency_system_name_matches(component_key, "cyclic");
            const bool collective_like =
                damage_dependency_system_name_matches(component_key, "collective");
            const bool rudder_like =
                damage_dependency_system_name_matches(component_key, "rudder");

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
            if (roll_weight > 0.0) {
                aircraft_damage.roll_control_integrity =
                    std::min(
                        aircraft_damage.roll_control_integrity,
                        damage_component_axis_availability(availability, roll_weight));
            }
            if (pitch_weight > 0.0) {
                aircraft_damage.pitch_control_integrity =
                    std::min(
                        aircraft_damage.pitch_control_integrity,
                        damage_component_axis_availability(availability, pitch_weight));
            }
            if (yaw_weight > 0.0) {
                aircraft_damage.yaw_control_integrity =
                    std::min(
                        aircraft_damage.yaw_control_integrity,
                        damage_component_axis_availability(availability, yaw_weight));
            }
            if (damage_dependency_system_name_matches(system, "hydraulic")) {
                aircraft_damage.hydraulic_integrity =
                    std::min(aircraft_damage.hydraulic_integrity, availability);
                aircraft_damage.hydraulic_pressure_availability =
                    std::min(aircraft_damage.hydraulic_pressure_availability, availability);
            }
        }
        if (damage_dependency_system_is_air_sensor(system) ||
            damage_dependency_system_name_matches(system, "avionics") ||
            damage_dependency_system_name_matches(system, "data_link")) {
            aircraft_damage.avionics_integrity =
                std::min(aircraft_damage.avionics_integrity, availability);
        }
        if (damage_dependency_system_name_matches(system, "command") ||
            damage_dependency_system_name_matches(system, "navigation")) {
            aircraft_damage.command_navigation_integrity =
                std::min(aircraft_damage.command_navigation_integrity, availability);
            aircraft_damage.avionics_integrity =
                std::min(aircraft_damage.avionics_integrity, availability);
        }
        if (damage_dependency_system_is_air_propulsion(system)) {
            aircraft_damage.propulsion_integrity =
                std::min(aircraft_damage.propulsion_integrity, availability);
        }
        if (damage_dependency_system_is_air_fuel(system)) {
            aircraft_damage.fuel_system_integrity =
                std::min(aircraft_damage.fuel_system_integrity, availability);
        }
        if (damage_dependency_system_is_air_structure(system)) {
            aircraft_damage.structural_integrity =
                std::min(aircraft_damage.structural_integrity, availability);
        }
        if (damage_dependency_system_is_fire_suppression(system)) {
            aircraft_damage.fire_suppression_integrity =
                std::min(aircraft_damage.fire_suppression_integrity, availability);
        }
        if (damage_dependency_system_name_matches(system, "cockpit") ||
            damage_dependency_system_name_matches(system, "pilot") ||
            damage_dependency_system_name_matches(system, "crew")) {
            aircraft_damage.crew_effectiveness =
                std::min(aircraft_damage.crew_effectiveness, availability);
            aircraft_damage.pilot_effectiveness =
                std::min(aircraft_damage.pilot_effectiveness, availability);
        }
    }
}

inline void apply_damage_component_dependency_impulse(
    const std::string& target_system,
    const std::string& edge_type,
    double availability,
    double impulse,
    SystemHealth* sys_health,
    AircraftDamageState* aircraft_damage,
    PlatformDamageState* platform_damage
) {
    if (target_system.empty()) {
        return;
    }

    const double bounded_availability = std::clamp(availability, 0.0, 1.0);
    const double bounded_impulse = std::clamp(impulse, 0.0, 1.0);
    const bool fuel_feed_edge = damage_dependency_edge_is_fuel_feed(edge_type);
    const bool hydraulic_power_edge = damage_dependency_edge_is_hydraulic_power(edge_type);
    const bool electrical_power_edge = damage_dependency_edge_is_electrical_power(edge_type);
    const bool data_path_edge = damage_dependency_edge_is_data_path(edge_type);
    const bool control_signal_edge = damage_dependency_edge_is_control_signal(edge_type);
    const bool cooling_edge = damage_dependency_edge_is_cooling(edge_type);
    const bool crew_operated_edge = damage_dependency_edge_is_crew_operated(edge_type);
    const bool structural_support_edge = damage_dependency_edge_is_structural_support(edge_type);
    if (bounded_impulse <= 1.0e-9 && bounded_availability >= 1.0) {
        return;
    }

    if (sys_health) {
        sys_health->systems[target_system] =
            std::min(sys_health->systems[target_system], bounded_availability);
    }

    if (aircraft_damage) {
        if (damage_dependency_system_is_air_control_surface(target_system)) {
            aircraft_damage->flight_control_integrity -= 0.06 + 0.12 * bounded_impulse;
        }
        if (control_signal_edge &&
            damage_dependency_system_is_air_control_surface(target_system)) {
            aircraft_damage->flight_control_integrity -= 0.03 + 0.08 * bounded_impulse;
            aircraft_damage->control_asymmetry += 0.01 + 0.04 * bounded_impulse;
        }
        if (damage_dependency_system_name_matches(target_system, "hydraulic")) {
            aircraft_damage->hydraulic_integrity -= 0.06 + 0.14 * bounded_impulse;
            aircraft_damage->hydraulic_pressure_availability -= 0.08 + 0.18 * bounded_impulse;
            aircraft_damage->flight_control_integrity -= 0.03 + 0.08 * bounded_impulse;
        }
        if (hydraulic_power_edge &&
            damage_dependency_system_is_air_control_surface(target_system) &&
            !damage_dependency_system_name_matches(target_system, "hydraulic")) {
            aircraft_damage->hydraulic_pressure_availability -= 0.04 + 0.10 * bounded_impulse;
            aircraft_damage->flight_control_integrity -= 0.02 + 0.06 * bounded_impulse;
        }
        if (electrical_power_edge) {
            aircraft_damage->avionics_integrity -= 0.04 + 0.09 * bounded_impulse;
            aircraft_damage->command_navigation_integrity -= 0.02 + 0.06 * bounded_impulse;
            if (damage_dependency_system_is_air_control_surface(target_system)) {
                aircraft_damage->flight_control_integrity -= 0.02 + 0.05 * bounded_impulse;
            }
            aircraft_damage->ignition_source_severity += 0.01 + 0.04 * bounded_impulse;
        }
        if (data_path_edge) {
            aircraft_damage->avionics_integrity -= 0.04 + 0.08 * bounded_impulse;
            aircraft_damage->command_navigation_integrity -= 0.02 + 0.05 * bounded_impulse;
            aircraft_damage->mission_crew_effectiveness -= 0.01 + 0.03 * bounded_impulse;
        }
        if (cooling_edge) {
            aircraft_damage->ignition_source_severity += 0.03 + 0.08 * bounded_impulse;
            aircraft_damage->fire_severity += 0.01 + 0.04 * bounded_impulse;
            if (damage_dependency_system_is_air_sensor(target_system) ||
                damage_dependency_system_name_matches(target_system, "avionics")) {
                aircraft_damage->avionics_integrity -= 0.02 + 0.05 * bounded_impulse;
            }
        }
        if (crew_operated_edge) {
            aircraft_damage->crew_effectiveness -= 0.02 + 0.05 * bounded_impulse;
            aircraft_damage->mission_crew_effectiveness -= 0.02 + 0.06 * bounded_impulse;
            aircraft_damage->command_navigation_integrity -= 0.02 + 0.05 * bounded_impulse;
        }
        if (structural_support_edge) {
            aircraft_damage->structural_integrity -= 0.03 + 0.08 * bounded_impulse;
            aircraft_damage->structural_overstress += 0.01 + 0.04 * bounded_impulse;
        }
        if (damage_dependency_system_is_air_sensor(target_system) ||
            damage_dependency_system_name_matches(target_system, "avionics")) {
            aircraft_damage->avionics_integrity -= 0.05 + 0.10 * bounded_impulse;
        }
        if (damage_dependency_system_is_air_propulsion(target_system)) {
            aircraft_damage->propulsion_integrity -= 0.05 + 0.12 * bounded_impulse;
            aircraft_damage->ignition_source_severity += 0.02 + 0.06 * bounded_impulse;
        }
        if (damage_dependency_system_is_air_fuel(target_system)) {
            aircraft_damage->fuel_system_integrity -= 0.04 + 0.10 * bounded_impulse;
            aircraft_damage->fuel_leak_severity += 0.02 + 0.05 * bounded_impulse;
            aircraft_damage->flammable_fluid_exposure += 0.03 + 0.08 * bounded_impulse;
        }
        if (fuel_feed_edge && damage_dependency_system_is_air_fuel(target_system)) {
            aircraft_damage->propulsion_integrity -= 0.04 + 0.09 * bounded_impulse;
            aircraft_damage->ignition_source_severity += 0.01 + 0.04 * bounded_impulse;
        }
        if (damage_dependency_system_is_mission_or_combat(target_system)) {
            aircraft_damage->avionics_integrity -= 0.03 + 0.08 * bounded_impulse;
            if (!data_path_edge && !crew_operated_edge) {
                aircraft_damage->ignition_source_severity += 0.01 + 0.04 * bounded_impulse;
            }
        }
        if (damage_dependency_system_is_fire_suppression(target_system)) {
            aircraft_damage->fire_suppression_integrity -= 0.08 + 0.16 * bounded_impulse;
        }
    }

    if (platform_damage) {
        if (damage_dependency_system_is_air_sensor(target_system) ||
            damage_dependency_system_name_matches(target_system, "avionics")) {
            platform_damage->sensor_capability -= 0.02 + 0.06 * bounded_impulse;
        }
        if (damage_dependency_system_is_air_control_surface(target_system) ||
            damage_dependency_system_name_matches(target_system, "hydraulic") ||
            damage_dependency_system_is_air_propulsion(target_system) ||
            (fuel_feed_edge && damage_dependency_system_is_air_fuel(target_system))) {
            platform_damage->mobility_capability -= 0.02 + 0.06 * bounded_impulse;
        }
        if (damage_dependency_system_is_mission_or_combat(target_system) ||
            electrical_power_edge || data_path_edge || crew_operated_edge) {
            platform_damage->mission_capability -= 0.02 + 0.06 * bounded_impulse;
        }
        if (data_path_edge ||
            (electrical_power_edge && damage_dependency_system_is_air_sensor(target_system))) {
            platform_damage->sensor_capability -= 0.01 + 0.04 * bounded_impulse;
        }
        if (damage_dependency_system_is_air_fuel(target_system)) {
            platform_damage->survivability_margin -= 0.02 + 0.05 * bounded_impulse;
        }
        if (cooling_edge || structural_support_edge) {
            platform_damage->survivability_margin -= 0.01 + 0.04 * bounded_impulse;
        }
        if (damage_dependency_system_is_fire_suppression(target_system)) {
            platform_damage->survivability_margin -= 0.01 + 0.04 * bounded_impulse;
        }
    }
}

struct AircraftDamageBaseline {
    double max_speed = 0.0;
    double min_speed = 0.0;
    double max_turn_rate = 0.0;
    double max_accel = 0.0;
    double max_climb_rate = 0.0;
    double max_g = 0.0;
    double min_g = 0.0;
    double takeoff_speed = 0.0;
    double landing_speed = 0.0;
    double taxi_turn_rate = 0.0;
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double fuel_leak_rate_kg_s = 0.0;
    double flutter_dynamic_pressure_pa = 65000.0;
    double flutter_mach = 0.95;
    double sensor_max_range = 0.0;
    double sensor_detection_prob = 0.0;
    double sensor_bearing_noise_std = 0.0;
    double sensor_range_noise_std = 0.0;
    double sensor_track_memory_s = 0.0;
};

inline void clamp_aircraft_damage_state(AircraftDamageState& state) {
    state.structural_integrity = std::clamp(state.structural_integrity, 0.0, 1.0);
    state.flight_control_integrity = std::clamp(state.flight_control_integrity, 0.0, 1.0);
    state.hydraulic_integrity = std::clamp(state.hydraulic_integrity, 0.0, 1.0);
    state.hydraulic_pressure_availability =
        std::clamp(state.hydraulic_pressure_availability, 0.0, 1.0);
    state.roll_control_integrity = std::clamp(state.roll_control_integrity, 0.0, 1.0);
    state.pitch_control_integrity = std::clamp(state.pitch_control_integrity, 0.0, 1.0);
    state.yaw_control_integrity = std::clamp(state.yaw_control_integrity, 0.0, 1.0);
    state.control_asymmetry = std::clamp(state.control_asymmetry, 0.0, 1.0);
    state.propulsion_integrity = std::clamp(state.propulsion_integrity, 0.0, 1.0);
    state.fuel_system_integrity = std::clamp(state.fuel_system_integrity, 0.0, 1.0);
    state.avionics_integrity = std::clamp(state.avionics_integrity, 0.0, 1.0);
    state.crew_effectiveness = std::clamp(state.crew_effectiveness, 0.0, 1.0);
    state.pilot_effectiveness = std::clamp(state.pilot_effectiveness, 0.0, 1.0);
    state.mission_crew_effectiveness =
        std::clamp(state.mission_crew_effectiveness, 0.0, 1.0);
    state.command_navigation_integrity =
        std::clamp(state.command_navigation_integrity, 0.0, 1.0);
    state.crew_effectiveness = std::min({
        state.crew_effectiveness,
        state.pilot_effectiveness,
        state.mission_crew_effectiveness,
        state.command_navigation_integrity});
    state.fire_severity = std::clamp(state.fire_severity, 0.0, 1.0);
    state.fuel_leak_severity = std::clamp(state.fuel_leak_severity, 0.0, 1.0);
    state.fuel_imbalance_severity = std::clamp(state.fuel_imbalance_severity, 0.0, 1.0);
    state.flammable_fluid_exposure = std::clamp(state.flammable_fluid_exposure, 0.0, 1.0);
    state.ignition_source_severity = std::clamp(state.ignition_source_severity, 0.0, 1.0);
    state.fire_suppression_integrity = std::clamp(state.fire_suppression_integrity, 0.0, 1.0);
    state.smoke_heat_exposure = std::clamp(state.smoke_heat_exposure, 0.0, 1.0);
    state.engine_fire_zone_severity = std::clamp(state.engine_fire_zone_severity, 0.0, 1.0);
    state.wing_fire_zone_severity = std::clamp(state.wing_fire_zone_severity, 0.0, 1.0);
    state.fuselage_fire_zone_severity = std::clamp(state.fuselage_fire_zone_severity, 0.0, 1.0);
    state.mission_fire_zone_severity = std::clamp(state.mission_fire_zone_severity, 0.0, 1.0);
    state.structural_overstress = std::clamp(state.structural_overstress, 0.0, 1.0);
    state.flutter_exposure = std::clamp(state.flutter_exposure, 0.0, 1.0);

    const double axis_control_integrity = std::min({
        state.flight_control_integrity,
        state.hydraulic_pressure_availability,
        state.roll_control_integrity,
        state.pitch_control_integrity,
        state.yaw_control_integrity});
    state.flight_control_kill =
        axis_control_integrity <= 0.25 ||
        state.hydraulic_integrity <= 0.20 ||
        state.hydraulic_pressure_availability <= 0.20 ||
        state.control_asymmetry >= 0.75;
    state.propulsion_kill = state.propulsion_integrity <= 0.20;
    state.crew_kill =
        state.crew_effectiveness <= 0.20 ||
        state.pilot_effectiveness <= 0.20;
    state.forced_landing_required =
        state.forced_landing_required ||
        state.structural_integrity <= 0.35 ||
        axis_control_integrity <= 0.40 ||
        state.control_asymmetry >= 0.60 ||
        state.hydraulic_integrity <= 0.35 ||
        state.hydraulic_pressure_availability <= 0.35 ||
        state.propulsion_integrity <= 0.35 ||
        state.fuel_leak_severity >= 0.70 ||
        state.crew_effectiveness <= 0.40 ||
        state.pilot_effectiveness <= 0.45;
}

inline void apply_aircraft_damage_state_to_platform(
    const AircraftDamageState& aircraft,
    PlatformDamageState& platform
) {
    const double axis_control_integrity = std::min({
        aircraft.flight_control_integrity,
        aircraft.hydraulic_pressure_availability,
        aircraft.roll_control_integrity,
        aircraft.pitch_control_integrity,
        aircraft.yaw_control_integrity});
    const double asymmetry_limited_control =
        std::min(axis_control_integrity, 1.0 - (0.55 * aircraft.control_asymmetry));
    const double pilot_limited_control =
        std::min(asymmetry_limited_control, aircraft.pilot_effectiveness);
    const double mission_crew_capability = std::min({
        aircraft.avionics_integrity,
        aircraft.crew_effectiveness,
        aircraft.mission_crew_effectiveness,
        aircraft.command_navigation_integrity});
    platform.mobility_capability = std::min(
        platform.mobility_capability,
        std::min(
            pilot_limited_control,
            std::min({
                aircraft.hydraulic_integrity,
                aircraft.hydraulic_pressure_availability,
                aircraft.propulsion_integrity})));
    platform.mission_capability = std::min(
        platform.mission_capability,
        mission_crew_capability);
    platform.survivability_margin = std::min(
        platform.survivability_margin,
        aircraft.structural_integrity);
    platform.fire_severity = std::max(platform.fire_severity, aircraft.fire_severity);

    if (aircraft.forced_landing_required) {
        platform.mobility_capability = std::min(platform.mobility_capability, 0.25);
        platform.mission_capability = std::min(platform.mission_capability, 0.35);
    }
    if (aircraft.flight_control_kill || aircraft.propulsion_kill) {
        platform.mobility_capability = 0.0;
    }
    if (aircraft.crew_kill) {
        platform.mission_capability = 0.0;
    }
}

inline double aircraft_damage_capability_floor(double integrity, double floor) {
    return std::clamp(floor + ((1.0 - floor) * std::clamp(integrity, 0.0, 1.0)), floor, 1.0);
}
