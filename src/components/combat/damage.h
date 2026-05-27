#pragma once

#include <algorithm>
#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>

struct DamageComponentDependency {
    std::string system;
    double scale = 1.0;
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
    std::string weapon_family;
    std::string aspect_bucket;
    std::string closure_bucket;
    std::string miss_distance_bucket;
    double family_scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    double effect_scale = 1.0;
    bool has_component_failure_probability = false;
    double component_failure_probability = 0.0;
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
    std::unordered_map<std::string, double> component_redundancy_weight;
    std::unordered_map<std::string, double> redundancy_group_availability;
    std::unordered_map<std::string, std::uint32_t> redundancy_group_member_count;
    std::unordered_map<std::string, std::uint32_t> redundancy_group_failed_count;
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
    double structural_overstress = 0.0;
    double flutter_exposure = 0.0;
    bool forced_landing_required = false;
    bool flight_control_kill = false;
    bool propulsion_kill = false;
    bool crew_kill = false;
};

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
    state.structural_overstress = std::clamp(state.structural_overstress, 0.0, 1.0);
    state.flutter_exposure = std::clamp(state.flutter_exposure, 0.0, 1.0);

    const double axis_control_integrity = std::min({
        state.flight_control_integrity,
        state.roll_control_integrity,
        state.pitch_control_integrity,
        state.yaw_control_integrity});
    state.flight_control_kill =
        axis_control_integrity <= 0.25 ||
        state.hydraulic_integrity <= 0.20 ||
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
            std::min(aircraft.hydraulic_integrity, aircraft.propulsion_integrity)));
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
