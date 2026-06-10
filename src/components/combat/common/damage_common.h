#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

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
    std::unordered_map<std::string, double> failure_mode_weights;
    double redundancy_group = 0.0;
    double redundancy_weight = 1.0;
    bool critical = true;
};

inline std::string canonical_part_failure_mode(const std::string &mode) {
    if (mode == "blast-deformation") {
        return "blast_deformation";
    }
    if (mode == "fuel-leak") {
        return "fuel_leak";
    }
    if (mode == "hydraulic-pressure-loss") {
        return "hydraulic_pressure_loss";
    }
    if (mode == "electrical-loss") {
        return "electrical_loss";
    }
    if (mode == "data-loss") {
        return "data_loss";
    }
    if (mode == "fire-source") {
        return "fire_source";
    }
    if (mode == "structural-weakening") {
        return "structural_weakening";
    }
    return mode;
}

inline bool is_known_part_failure_mode(const std::string &mode) {
    const std::string canonical = canonical_part_failure_mode(mode);
    return canonical == "puncture" || canonical == "cut" || canonical == "blast_deformation" ||
           canonical == "fuel_leak" || canonical == "hydraulic_pressure_loss" ||
           canonical == "electrical_loss" || canonical == "data_loss" ||
           canonical == "fire_source" || canonical == "structural_weakening";
}

inline std::string damage_component_key(const DamageComponent &component) {
    if (!component.name.empty()) {
        return component.name;
    }
    if (!component.system.empty()) {
        return component.system;
    }
    return "unnamed_component";
}

inline std::string damage_component_redundancy_group_key(const DamageComponent &component) {
    if (!component.redundancy_group_id.empty()) {
        return component.redundancy_group_id;
    }
    if (component.redundancy_group > 0.0) {
        return component.system + ":rg:" + std::to_string(component.redundancy_group);
    }
    return damage_component_key(component);
}

struct Hitbox {
    int id;
    double offset_x, offset_y, offset_z;
    double dim_l, dim_w, dim_h;
    double armor_mm;
    std::vector<std::string> protected_systems;
    std::vector<DamageComponent> components;
};

struct HitboxConfig {
    std::vector<Hitbox> hitboxes;
};

struct SystemHealth {
    std::unordered_map<std::string, double> systems;
};

struct ComponentDamageState {
    std::unordered_map<std::string, double> component_integrity;
    std::unordered_map<std::string, std::string> component_redundancy_group;
    std::unordered_map<std::string, std::string> component_system;
    std::unordered_map<std::string, double> component_redundancy_weight;
    std::unordered_map<std::string, std::unordered_map<std::string, double>>
        component_failure_mode_severity;
    std::unordered_map<std::string, std::string> component_primary_failure_mode;
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

// Shared platform damage capability state used by common routing and
// domain-owned damage systems. Domain-specific helpers may project the fields
// they own without reintroducing a public aggregate header.
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
