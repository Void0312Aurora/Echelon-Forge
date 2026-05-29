#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <limits>
#include <string>
#include <unordered_set>
#include <vector>
#include <spdlog/spdlog.h>

#include "components/combat/health.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/combat/weapon.h"
#include "components/combat/damage.h"
#include "components/physics/dynamics.h"
#include "components/basic/common.h"

namespace {

// Geometry Helpers
struct Vec3 { double x, y, z; };

double vec3_norm(const Vec3& value) {
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

Vec3 vec3_normalize(const Vec3& value) {
    const double norm = vec3_norm(value);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    return {value.x / norm, value.y / norm, value.z / norm};
}

double vec3_dot(const Vec3& lhs, const Vec3& rhs) {
    return lhs.x * rhs.x + lhs.y * rhs.y + lhs.z * rhs.z;
}

bool vec3_is_finite(const Vec3& value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

Vec3 math_to_vec3(const Math::Vector3& value) {
    return {value.x, value.y, value.z};
}

Vec3 math_body_to_local_right_frame(const Math::Vector3& value) {
    return {value.x, -value.y, value.z};
}

Vec3 world_to_body(const Transform& t, double wx, double wy, double wz) {
    return math_body_to_local_right_frame(
        Math::world_to_body(
            {wx - t.x, wy - t.y, wz - t.z},
            t));
}

uint64_t splitmix64(uint64_t& state) {
    uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double rand_uniform01(uint64_t& state) {
    // 53 random bits / 2^53
    return (splitmix64(state) >> 11) * (1.0 / 9007199254740992.0);
}

bool check_hitbox(const Vec3& local_p, const Hitbox& box) {
    // Check if point is inside box (centered at offset)
    double min_x = box.offset_x - box.dim_l * 0.5;
    double max_x = box.offset_x + box.dim_l * 0.5;
    double min_y = box.offset_y - box.dim_w * 0.5;
    double max_y = box.offset_y + box.dim_w * 0.5;
    double min_z = box.offset_z - box.dim_h * 0.5;
    double max_z = box.offset_z + box.dim_h * 0.5;
    
    return (local_p.x >= min_x && local_p.x <= max_x &&
            local_p.y >= min_y && local_p.y <= max_y &&
            local_p.z >= min_z && local_p.z <= max_z);
}

double hitbox_surface_distance(const Vec3& local_p, const Hitbox& box) {
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;

    const double dx = std::max({min_x - local_p.x, 0.0, local_p.x - max_x});
    const double dy = std::max({min_y - local_p.y, 0.0, local_p.y - max_y});
    const double dz = std::max({min_z - local_p.z, 0.0, local_p.z - max_z});
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 hitbox_nearest_point(const Vec3& local_p, const Hitbox& box) {
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;
    return {
        std::clamp(local_p.x, min_x, max_x),
        std::clamp(local_p.y, min_y, max_y),
        std::clamp(local_p.z, min_z, max_z),
    };
}

double hitbox_surface_incidence_cos(
    const Vec3& local_p,
    const Hitbox& box,
    const Vec3& missile_axis_body
) {
    const Vec3 axis = vec3_normalize(missile_axis_body);
    if (!vec3_is_finite(local_p) || !vec3_is_finite(axis) || vec3_norm(axis) <= 1.0e-9 ||
        !std::isfinite(box.offset_x) || !std::isfinite(box.offset_y) ||
        !std::isfinite(box.offset_z) || !std::isfinite(box.dim_l) ||
        !std::isfinite(box.dim_w) || !std::isfinite(box.dim_h) ||
        box.dim_l <= 0.0 || box.dim_w <= 0.0 || box.dim_h <= 0.0) {
        return 0.0;
    }

    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;

    bool has_candidate = false;
    double incidence_cos = 1.0;
    const auto consider_face = [&](const Vec3& normal) {
        const double candidate =
            std::clamp(std::abs(vec3_dot(axis, normal)), 0.0, 1.0);
        incidence_cos = has_candidate ? std::min(incidence_cos, candidate) : candidate;
        has_candidate = true;
    };

    if (local_p.x < min_x) {
        consider_face({-1.0, 0.0, 0.0});
    } else if (local_p.x > max_x) {
        consider_face({1.0, 0.0, 0.0});
    }
    if (local_p.y < min_y) {
        consider_face({0.0, -1.0, 0.0});
    } else if (local_p.y > max_y) {
        consider_face({0.0, 1.0, 0.0});
    }
    if (local_p.z < min_z) {
        consider_face({0.0, 0.0, -1.0});
    } else if (local_p.z > max_z) {
        consider_face({0.0, 0.0, 1.0});
    }
    if (has_candidate) {
        return incidence_cos;
    }

    const double distances[] = {
        std::abs(local_p.x - min_x),
        std::abs(max_x - local_p.x),
        std::abs(local_p.y - min_y),
        std::abs(max_y - local_p.y),
        std::abs(local_p.z - min_z),
        std::abs(max_z - local_p.z),
    };
    const double nearest_distance = *std::min_element(std::begin(distances), std::end(distances));
    const double epsilon = 1.0e-9;
    if (distances[0] <= nearest_distance + epsilon) {
        consider_face({-1.0, 0.0, 0.0});
    }
    if (distances[1] <= nearest_distance + epsilon) {
        consider_face({1.0, 0.0, 0.0});
    }
    if (distances[2] <= nearest_distance + epsilon) {
        consider_face({0.0, -1.0, 0.0});
    }
    if (distances[3] <= nearest_distance + epsilon) {
        consider_face({0.0, 1.0, 0.0});
    }
    if (distances[4] <= nearest_distance + epsilon) {
        consider_face({0.0, 0.0, -1.0});
    }
    if (distances[5] <= nearest_distance + epsilon) {
        consider_face({0.0, 0.0, 1.0});
    }
    return has_candidate ? incidence_cos : 0.0;
}

bool check_component(const Vec3& local_p, const DamageComponent& component) {
    const double min_x = component.offset_x - component.dim_l * 0.5;
    const double max_x = component.offset_x + component.dim_l * 0.5;
    const double min_y = component.offset_y - component.dim_w * 0.5;
    const double max_y = component.offset_y + component.dim_w * 0.5;
    const double min_z = component.offset_z - component.dim_h * 0.5;
    const double max_z = component.offset_z + component.dim_h * 0.5;

    return (local_p.x >= min_x && local_p.x <= max_x &&
            local_p.y >= min_y && local_p.y <= max_y &&
            local_p.z >= min_z && local_p.z <= max_z);
}

double component_surface_distance(const Vec3& local_p, const DamageComponent& component) {
    const double min_x = component.offset_x - component.dim_l * 0.5;
    const double max_x = component.offset_x + component.dim_l * 0.5;
    const double min_y = component.offset_y - component.dim_w * 0.5;
    const double max_y = component.offset_y + component.dim_w * 0.5;
    const double min_z = component.offset_z - component.dim_h * 0.5;
    const double max_z = component.offset_z + component.dim_h * 0.5;

    const double dx = std::max({min_x - local_p.x, 0.0, local_p.x - max_x});
    const double dy = std::max({min_y - local_p.y, 0.0, local_p.y - max_y});
    const double dz = std::max({min_z - local_p.z, 0.0, local_p.z - max_z});
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 component_nearest_point(const Vec3& local_p, const DamageComponent& component) {
    const double min_x = component.offset_x - component.dim_l * 0.5;
    const double max_x = component.offset_x + component.dim_l * 0.5;
    const double min_y = component.offset_y - component.dim_w * 0.5;
    const double max_y = component.offset_y + component.dim_w * 0.5;
    const double min_z = component.offset_z - component.dim_h * 0.5;
    const double max_z = component.offset_z + component.dim_h * 0.5;
    return {
        std::clamp(local_p.x, min_x, max_x),
        std::clamp(local_p.y, min_y, max_y),
        std::clamp(local_p.z, min_z, max_z),
    };
}

double component_projected_exposure_scale(const Vec3& local_imp, const DamageComponent& component) {
    const Vec3 nearest = component_nearest_point(local_imp, component);
    const Vec3 ray = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(ray) <= 1.0e-9) {
        return 1.0;
    }

    const double area_forward = std::max(1.0e-6, component.dim_w * component.dim_h);
    const double area_side = std::max(1.0e-6, component.dim_l * component.dim_h);
    const double area_top = std::max(1.0e-6, component.dim_l * component.dim_w);
    const double projected_area =
        (std::abs(ray.x) * area_forward) +
        (std::abs(ray.y) * area_side) +
        (std::abs(ray.z) * area_top);
    const double reference_area = std::max({area_forward, area_side, area_top, 1.0e-6});
    return std::clamp(0.45 + 0.55 * (projected_area / reference_area), 0.45, 1.0);
}

Hitbox component_as_hitbox(const DamageComponent& component, const Hitbox& parent) {
    Hitbox box = parent;
    box.offset_x = component.offset_x;
    box.offset_y = component.offset_y;
    box.offset_z = component.offset_z;
    box.dim_l = component.dim_l;
    box.dim_w = component.dim_w;
    box.dim_h = component.dim_h;
    box.armor_mm = component.armor_mm;
    box.protected_systems = {component.system};
    box.components.clear();
    return box;
}

bool system_name_matches(const std::string& system, const char* token) {
    return system.find(token) != std::string::npos;
}

bool system_is_air_control_surface(const std::string& system) {
    return system_name_matches(system, "flight_control") ||
        system_name_matches(system, "control") ||
        system_name_matches(system, "hydraulic");
}

bool system_is_air_sensor(const std::string& system) {
    return system_name_matches(system, "radar") ||
        system_name_matches(system, "sensor") ||
        system_name_matches(system, "rwr") ||
        system_name_matches(system, "esm");
}

bool system_is_air_propulsion_or_fuel(const std::string& system) {
    return system_name_matches(system, "engineering") ||
        system_name_matches(system, "engine") ||
        system_name_matches(system, "fuel") ||
        system_name_matches(system, "propeller") ||
        system_name_matches(system, "transmission");
}

bool system_is_air_propulsion(const std::string& system) {
    return system_name_matches(system, "engineering") ||
        system_name_matches(system, "engine") ||
        system_name_matches(system, "propeller") ||
        system_name_matches(system, "transmission");
}

bool system_is_air_fuel(const std::string& system) {
    return system_name_matches(system, "fuel");
}

bool system_is_crew_or_cockpit(const std::string& system) {
    return system_name_matches(system, "cockpit") ||
        system_name_matches(system, "pilot") ||
        system_name_matches(system, "crew");
}

bool system_is_command_navigation(const std::string& system) {
    return system_name_matches(system, "command") ||
        system_name_matches(system, "navigation");
}

bool system_is_mission_crew_station(const std::string& system) {
    return system_name_matches(system, "operator") ||
        system_name_matches(system, "crew");
}

enum class CrewConsequenceKind {
    None,
    Pilot,
    MissionCrew,
    CommandNavigation,
};

CrewConsequenceKind classify_crew_consequence(
    const std::string& system,
    const std::string& component_name
) {
    const std::string& name = component_name.empty() ? system : component_name;
    if (system_name_matches(system, "cockpit") ||
        system_name_matches(system, "pilot") ||
        system_name_matches(name, "flight_deck") ||
        system_name_matches(name, "cockpit") ||
        system_name_matches(name, "pilot")) {
        return CrewConsequenceKind::Pilot;
    }
    if (system_name_matches(system, "command") ||
        system_name_matches(system, "navigation") ||
        system_name_matches(name, "command") ||
        system_name_matches(name, "navigation")) {
        return CrewConsequenceKind::CommandNavigation;
    }
    if (system_name_matches(name, "mission_operator") ||
        system_name_matches(name, "operator") ||
        system_name_matches(name, "console")) {
        return CrewConsequenceKind::MissionCrew;
    }
    if (system_is_crew_or_cockpit(system)) {
        return CrewConsequenceKind::Pilot;
    }
    return CrewConsequenceKind::None;
}

void apply_aircraft_crew_consequence(
    AircraftDamageState& aircraft_damage,
    CrewConsequenceKind kind,
    double delta
) {
    const double resolved_delta = std::clamp(delta, 0.0, 1.0);
    if (resolved_delta <= 0.0 || kind == CrewConsequenceKind::None) {
        return;
    }
    if (kind == CrewConsequenceKind::Pilot) {
        aircraft_damage.pilot_effectiveness -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.85 * resolved_delta;
        aircraft_damage.flight_control_integrity -= 0.18 * resolved_delta;
    } else if (kind == CrewConsequenceKind::MissionCrew) {
        aircraft_damage.mission_crew_effectiveness -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.55 * resolved_delta;
        aircraft_damage.avionics_integrity -= 0.18 * resolved_delta;
    } else if (kind == CrewConsequenceKind::CommandNavigation) {
        aircraft_damage.command_navigation_integrity -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.65 * resolved_delta;
        aircraft_damage.avionics_integrity -= 0.10 * resolved_delta;
    }
}

bool system_is_mission_or_combat(const std::string& system) {
    return system_name_matches(system, "combat") ||
        system_name_matches(system, "command") ||
        system_name_matches(system, "data_link") ||
        system_name_matches(system, "vls") ||
        system_name_matches(system, "gun") ||
        system_name_matches(system, "radar") ||
        system_name_matches(system, "avionics") ||
        system_name_matches(system, "navigation") ||
        system_name_matches(system, "mission");
}

bool system_is_air_structure(const std::string& system) {
    return system_name_matches(system, "wing") ||
        system_name_matches(system, "airframe") ||
        system_name_matches(system, "fuselage") ||
        system_name_matches(system, "structure") ||
        system_name_matches(system, "rotor") ||
        system_name_matches(system, "tail");
}

double component_mechanism_threshold_scale(
    const WarheadProfile& profile,
    const std::string& system
) {
    const std::string family = warhead_effect_family(profile);
    double scale = 1.0;

    if (system_is_air_control_surface(system)) {
        if (family == "continuous_rod") {
            scale = 1.35;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.10;
        } else if (family == "hit_to_kill") {
            scale = 1.15;
        } else if (family == "blast") {
            scale = 0.75;
        }
    } else if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
        if (family == "hit_to_kill") {
            scale = 1.30;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.20;
        } else if (family == "continuous_rod") {
            scale = 0.90;
        } else if (family == "blast") {
            scale = 0.80;
        }
    } else if (system_is_air_propulsion(system)) {
        if (family == "hit_to_kill") {
            scale = 1.20;
        } else if (family == "blast" || family == "fragmentation" ||
                   family == "blast_fragmentation") {
            scale = 1.05;
        } else if (family == "continuous_rod") {
            scale = 0.95;
        }
    } else if (system_is_air_fuel(system)) {
        if (family == "blast") {
            scale = 1.25;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.10;
        } else if (family == "continuous_rod") {
            scale = 0.85;
        } else if (family == "hit_to_kill") {
            scale = 0.95;
        }
    } else if (system_is_crew_or_cockpit(system)) {
        if (family == "hit_to_kill") {
            scale = 1.25;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.20;
        } else if (family == "continuous_rod") {
            scale = 1.05;
        } else if (family == "blast") {
            scale = 0.90;
        }
    } else if (system_is_air_structure(system)) {
        if (family == "blast") {
            scale = 1.25;
        } else if (family == "continuous_rod") {
            scale = 1.20;
        } else if (family == "hit_to_kill") {
            scale = 1.15;
        }
    }

    return std::clamp(scale, 0.55, 1.45);
}

double component_authored_mechanism_threshold_scale(
    const WarheadProfile& profile,
    const DamageComponent& component
) {
    const std::string family = warhead_effect_family(profile);
    const auto exact = component.mechanism_threshold_scales.find(family);
    if (exact != component.mechanism_threshold_scales.end()) {
        return std::clamp(exact->second, 0.35, 2.40);
    }
    if ((family == "fragmentation" || family == "blast_fragmentation") &&
        component.mechanism_threshold_scales.find("fragmentation") !=
            component.mechanism_threshold_scales.end()) {
        return std::clamp(
            component.mechanism_threshold_scales.at("fragmentation"),
            0.35,
            2.40);
    }
    if (family == "blast_fragmentation" &&
        component.mechanism_threshold_scales.find("blast") !=
            component.mechanism_threshold_scales.end()) {
        return std::clamp(
            component.mechanism_threshold_scales.at("blast"),
            0.35,
            2.40);
    }
    return 1.0;
}

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

double component_failure_probability(
    double severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load
) {
    const double fragment_load = std::clamp(
        std::log1p(std::max(0.0, mechanism_load.fragment_energy_j)) / std::log(2501.0),
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
    const double mechanism_load_scale = std::clamp(
            0.74 +
            0.16 * fragment_load +
            0.22 * penetration_load +
            0.18 * blast_load +
            0.24 * rod_load,
        0.70,
        1.55);
    const double impulse =
        std::clamp(severity, 0.0, 1.0) *
        std::clamp(mechanism_scale, 0.0, 1.25) *
        std::clamp(component_scale, 0.40, 1.60) *
        mechanism_load_scale;
    const double threshold = direct_hit ? 0.42 : 0.58;
    const double slope = direct_hit ? 5.2 : 4.4;
    const double probability = 1.0 / (1.0 + std::exp(-slope * (impulse - threshold)));
    return std::clamp(probability, direct_hit ? 0.02 : 0.0, direct_hit ? 0.92 : 0.65);
}

void apply_component_failure_impulse(
    const std::string& system,
    double probability,
    double component_scale,
    double mechanism_scale,
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
        }
        if (system_is_air_propulsion(system)) {
            aircraft_damage->propulsion_integrity -= 0.08 + 0.14 * impulse;
        }
        if (system_is_air_fuel(system)) {
            aircraft_damage->fuel_system_integrity -= 0.08 + 0.12 * impulse;
            aircraft_damage->fuel_leak_severity += 0.06 + 0.12 * impulse;
            aircraft_damage->fire_severity += 0.02 + 0.06 * impulse;
        }
        if (system_is_air_control_surface(system)) {
            aircraft_damage->flight_control_integrity -= 0.10 + 0.14 * impulse;
            aircraft_damage->hydraulic_integrity -= 0.08 + 0.12 * impulse;
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
        if (system_is_air_propulsion(system) || system_is_air_control_surface(system)) {
            platform_damage->mobility_capability -= 0.05 + 0.08 * impulse;
        }
        if (system_is_crew_or_cockpit(system)) {
            platform_damage->mission_capability -= 0.05 + 0.10 * impulse;
        }
        if (system_is_air_structure(system) || system_is_air_fuel(system)) {
            platform_damage->survivability_margin -= 0.04 + 0.08 * impulse;
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
    double integrity = 1.0;
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
    double& integrity = component_damage->component_integrity[component_key];

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
    sample.group_availability =
        std::clamp(live_weight / std::max(total_weight, 1.0e-6), 0.0, 1.0);
    sample.group_member_count = member_count;
    sample.group_failed_count = failed_count;
    sample.integrity = integrity;

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
        if (sys_health) {
            sys_health->systems[target_system] =
                std::min(sys_health->systems[target_system], availability);
        }

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
        if (aircraft_damage) {
            if (system_is_air_control_surface(target_system)) {
                aircraft_damage->flight_control_integrity -= 0.06 + 0.12 * impulse;
            }
            if (system_name_matches(target_system, "hydraulic")) {
                aircraft_damage->hydraulic_integrity -= 0.06 + 0.14 * impulse;
                aircraft_damage->flight_control_integrity -= 0.03 + 0.08 * impulse;
            }
            if (system_is_air_sensor(target_system) ||
                system_name_matches(target_system, "avionics")) {
                aircraft_damage->avionics_integrity -= 0.05 + 0.10 * impulse;
            }
            if (system_is_air_propulsion(target_system)) {
                aircraft_damage->propulsion_integrity -= 0.05 + 0.12 * impulse;
            }
            if (system_is_air_fuel(target_system)) {
                aircraft_damage->fuel_system_integrity -= 0.04 + 0.10 * impulse;
                aircraft_damage->fuel_leak_severity += 0.02 + 0.05 * impulse;
            }
            if (system_is_mission_or_combat(target_system)) {
                aircraft_damage->avionics_integrity -= 0.03 + 0.08 * impulse;
            }
        }
        if (platform_damage) {
            if (system_is_air_sensor(target_system) ||
                system_name_matches(target_system, "avionics")) {
                platform_damage->sensor_capability -= 0.02 + 0.06 * impulse;
            }
            if (system_is_air_control_surface(target_system) ||
                system_name_matches(target_system, "hydraulic") ||
                system_is_air_propulsion(target_system)) {
                platform_damage->mobility_capability -= 0.02 + 0.06 * impulse;
            }
            if (system_is_mission_or_combat(target_system)) {
                platform_damage->mission_capability -= 0.02 + 0.06 * impulse;
            }
            if (system_is_air_fuel(target_system)) {
                platform_damage->survivability_margin -= 0.02 + 0.05 * impulse;
            }
        }
    }
    return summary;
}

struct WarheadEffectProfile {
    double system_damage_scale = 1.0;
    double structure_scale = 1.0;
    double sensor_scale = 1.0;
    double propulsion_scale = 1.0;
    double control_scale = 1.0;
    double crew_scale = 1.0;
    double mission_scale = 1.0;
    double fire_scale = 1.0;
    double breach_scale = 1.0;
};

struct WarheadSpatialProjectionProfile {
    double radius_fraction = 0.35;
    double min_radius_m = 1.0;
    double max_radius_m = 12.0;
    double min_effect_scale = 0.05;
    double max_effect_scale = 0.80;
    double falloff_exponent = 1.0;
    std::size_t max_projected_hitboxes = 1;
};

struct SpatialProjectionCandidate {
    const Hitbox* box = nullptr;
    const DamageComponent* component = nullptr;
    double distance_m = std::numeric_limits<double>::infinity();
    double effect_scale = 0.0;
    double axis_weight = 1.0;
    double orientation_weight = 1.0;
    double armor_scale = 1.0;
    double exposure_scale = 1.0;
    std::uint32_t spatial_sample_count = 0;
    double spatial_hit_estimate = 0.0;
    double spatial_hit_fraction = 0.0;
    double spatial_energy_scale = 1.0;
    double spatial_pattern_scale = 1.0;
    double surface_incidence_cos = 0.0;
    WarheadMechanismLoadEvidence mechanism_load;
};

struct WarheadSpatialSample {
    std::uint32_t sample_count = 0;
    double hit_estimate = 0.0;
    double hit_fraction = 0.0;
    double areal_density_per_m2 = 0.0;
    double energy_scale = 1.0;
    double pattern_scale = 1.0;
    double orientation_pattern_scale = 1.0;
};

struct VulnerabilityAdjustment {
    double scale = 1.0;
    double family_scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    std::string aspect_bucket = "unknown";
    double closure_mps = 0.0;
    bool profile_present = false;
    bool synthetic = true;
    bool calibrated_evidence = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    bool evidence_dataset_valid = false;
    std::string provenance;
    std::string calibration_status = "none";
    std::string evidence_dataset_ref;
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
    std::string effect_scale_source = "profile_scale";
    std::string effect_scale_evidence_row_id;
    std::string effect_scale_evidence_source_ref;
    std::string effect_scale_evidence_provenance;
};

WarheadEffectProfile make_warhead_effect_profile(const WarheadProfile& profile) {
    const std::string family = warhead_effect_family(profile);
    WarheadEffectProfile out{};

    if (family == "blast") {
        out.system_damage_scale = 0.85;
        out.structure_scale = 1.35;
        out.sensor_scale = 0.70;
        out.propulsion_scale = 1.15;
        out.control_scale = 0.65;
        out.crew_scale = 0.75;
        out.mission_scale = 0.85;
        out.fire_scale = 1.60;
        out.breach_scale = 1.30;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        out = WarheadEffectProfile{};
    } else if (family == "continuous_rod") {
        out.system_damage_scale = 1.20;
        out.structure_scale = 1.05;
        out.sensor_scale = 0.85;
        out.propulsion_scale = 1.00;
        out.control_scale = 1.45;
        out.crew_scale = 1.00;
        out.mission_scale = 1.05;
        out.fire_scale = 0.70;
        out.breach_scale = 0.85;
    } else if (family == "hit_to_kill") {
        out.system_damage_scale = 1.55;
        out.structure_scale = 1.25;
        out.sensor_scale = 1.25;
        out.propulsion_scale = 1.25;
        out.control_scale = 1.25;
        out.crew_scale = 1.35;
        out.mission_scale = 1.35;
        out.fire_scale = 0.45;
        out.breach_scale = 0.50;
    }

    return out;
}

WarheadSpatialProjectionProfile make_warhead_spatial_projection_profile(const WarheadProfile& profile) {
    const std::string family = warhead_effect_family(profile);
    WarheadSpatialProjectionProfile out{};

    if (family == "blast") {
        out.radius_fraction = 0.55;
        out.max_radius_m = 20.0;
        out.min_effect_scale = 0.05;
        out.max_effect_scale = 0.70;
        out.falloff_exponent = 1.65;
        out.max_projected_hitboxes = 4;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        out.radius_fraction = 0.45;
        out.max_radius_m = 18.0;
        out.min_effect_scale = 0.06;
        out.max_effect_scale = 0.78;
        out.falloff_exponent = 1.15;
        out.max_projected_hitboxes = 3;
    } else if (family == "continuous_rod") {
        out.radius_fraction = 0.32;
        out.max_radius_m = 11.0;
        out.min_effect_scale = 0.05;
        out.max_effect_scale = 0.85;
        out.falloff_exponent = 1.25;
        out.max_projected_hitboxes = 2;
    } else if (family == "hit_to_kill") {
        out.radius_fraction = 0.24;
        out.max_radius_m = 6.0;
        out.min_effect_scale = 0.04;
        out.max_effect_scale = 0.90;
        out.falloff_exponent = 2.20;
        out.max_projected_hitboxes = 1;
    }

    return out;
}

double resolve_spatial_projection_radius_m(
    const Missile& missile,
    const WarheadSpatialProjectionProfile& projection
) {
    const double warhead_radius_m = std::isfinite(missile.warhead_profile.lethal_radius_m)
        ? missile.warhead_profile.lethal_radius_m
        : missile.fuse_distance;
    return std::clamp(
        warhead_radius_m * projection.radius_fraction,
        projection.min_radius_m,
        projection.max_radius_m);
}

double projected_spatial_effect_scale(
    double distance_m,
    double radius_m,
    const WarheadSpatialProjectionProfile& projection
) {
    if (radius_m <= 0.0 || !std::isfinite(distance_m)) {
        return 0.0;
    }
    const double quality = std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double shaped_quality = std::pow(quality, projection.falloff_exponent);
    return std::clamp(
        projection.min_effect_scale +
            (projection.max_effect_scale - projection.min_effect_scale) * shaped_quality,
        projection.min_effect_scale,
        projection.max_effect_scale);
}

double resolved_warhead_effective_mass_kg(const Missile& missile) {
    if (std::isfinite(missile.warhead_profile.mass_kg) && missile.warhead_profile.mass_kg > 0.0) {
        return missile.warhead_profile.mass_kg;
    }
    if (std::isfinite(missile.warhead_profile.damage_scalar) &&
        missile.warhead_profile.damage_scalar > 0.0) {
        return std::max(1.0, missile.warhead_profile.damage_scalar * 0.12);
    }
    return std::max(1.0, missile.damage * 0.12);
}

double hitbox_projected_exposure_scale(const Vec3& local_imp, const Hitbox& box) {
    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 ray = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(ray) <= 1.0e-9) {
        return 1.0;
    }

    const double area_forward = std::max(1.0e-6, box.dim_w * box.dim_h);
    const double area_side = std::max(1.0e-6, box.dim_l * box.dim_h);
    const double area_top = std::max(1.0e-6, box.dim_l * box.dim_w);
    const double projected_area =
        (std::abs(ray.x) * area_forward) +
        (std::abs(ray.y) * area_side) +
        (std::abs(ray.z) * area_top);
    const double reference_area = std::max({area_forward, area_side, area_top, 1.0e-6});
    return std::clamp(0.45 + 0.55 * (projected_area / reference_area), 0.45, 1.0);
}

double warhead_mechanism_armor_scale(
    const Missile& missile,
    const Hitbox& box,
    double distance_m,
    double radius_m,
    double axis_weight,
    bool direct_hit
) {
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality = direct_hit || radius_m <= 1.0e-6
        ? 1.0
        : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);

    double mechanism_capacity_mm = 4.0 + 0.45 * std::sqrt(mass_kg);
    double armor_coupling = 1.0;
    double lower_bound = 0.55;
    double upper_bound = 1.05;

    if (family == "blast") {
        mechanism_capacity_mm = 7.0 + 0.30 * std::sqrt(mass_kg);
        armor_coupling = 0.45;
        lower_bound = 0.70;
        upper_bound = 1.02;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        mechanism_capacity_mm = 3.6 + 0.55 * std::sqrt(mass_kg);
        armor_coupling = 1.00;
        lower_bound = 0.52;
        upper_bound = 1.06;
    } else if (family == "continuous_rod") {
        mechanism_capacity_mm = 7.5 + 1.10 * std::sqrt(mass_kg);
        armor_coupling = 0.80;
        lower_bound = 0.62;
        upper_bound = 1.08;
    } else if (family == "hit_to_kill") {
        mechanism_capacity_mm = 14.0 + 1.35 * std::sqrt(mass_kg);
        armor_coupling = 0.55;
        lower_bound = 0.78;
        upper_bound = 1.10;
    }

    mechanism_capacity_mm *= 0.40 + 0.60 * radius_quality;
    if (family == "continuous_rod") {
        mechanism_capacity_mm *= std::clamp(0.80 + 0.20 * axis_weight, 0.75, 1.15);
    }

    const double effective_armor_mm = std::max(0.0, box.armor_mm) * armor_coupling;
    const double ratio = mechanism_capacity_mm /
        std::max(1.0e-6, mechanism_capacity_mm + effective_armor_mm);
    return std::clamp(0.48 + 0.58 * ratio, lower_bound, upper_bound);
}

WarheadMechanismLoadEvidence estimate_warhead_mechanism_load(
    const Missile& missile,
    const Hitbox& target_shape,
    double distance_m,
    double radius_m,
    double axis_weight,
    double orientation_weight,
    double exposure_scale,
    bool direct_hit,
    double closure_mps,
    const WarheadSpatialSample& spatial_sample
) {
    WarheadMechanismLoadEvidence evidence{};
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality = direct_hit || radius_m <= 1.0e-6
        ? 1.0
        : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double standoff_m = std::max(direct_hit ? 1.0 : distance_m, 1.0);
    const double armor_mm = std::max(0.0, target_shape.armor_mm);
    const double exposure = std::clamp(exposure_scale, 0.05, 1.25);
    const double pattern = std::clamp(axis_weight * orientation_weight, 0.20, 1.60);
    const double closure = std::clamp(closure_mps, 0.0, 1600.0);

    if (family == "fragmentation" || family == "blast_fragmentation") {
        const double fragment_count = std::clamp(18.0 * mass_kg, 80.0, 1200.0);
        const double fragment_mass_kg =
            std::clamp((0.36 * mass_kg) / fragment_count, 0.003, 0.055);
        const double fragment_velocity_mps =
            std::clamp(1120.0 + 18.0 * std::sqrt(mass_kg) + 0.18 * closure, 550.0, 1850.0) *
            (0.42 + 0.58 * radius_quality);
        evidence.fragment_energy_j =
            0.5 * fragment_mass_kg * fragment_velocity_mps * fragment_velocity_mps *
            std::clamp(spatial_sample.energy_scale, 0.05, 1.20);
        evidence.fragment_areal_density_per_m2 =
            std::max(0.0, spatial_sample.areal_density_per_m2);
        const double penetration_capacity_mm =
            (1.2 + 0.028 * std::sqrt(std::max(0.0, evidence.fragment_energy_j))) *
            std::clamp(0.65 + 0.35 * spatial_sample.pattern_scale, 0.45, 1.30);
        evidence.penetration_margin = std::clamp(
            (penetration_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0),
            0.0,
            8.0);
    }

    if (family == "blast" || family == "blast_fragmentation") {
        const double cube_root_mass_kg = std::cbrt(std::max(0.1, mass_kg));
        const double inverse_scaled_distance = cube_root_mass_kg / standoff_m;
        evidence.blast_scaled_distance_m_kg13 =
            standoff_m / std::max(1.0e-6, cube_root_mass_kg);
        evidence.blast_overpressure_kpa =
            std::clamp(
                115.0 * inverse_scaled_distance * inverse_scaled_distance *
                    (0.30 + 0.70 * radius_quality) *
                    exposure,
                0.0,
                1800.0);
        evidence.blast_impulse_kpa_ms =
            evidence.blast_overpressure_kpa *
            std::clamp(1.1 + 0.32 * std::cbrt(std::max(0.1, mass_kg)), 1.0, 5.0);
    }

    if (family == "continuous_rod") {
        const double rod_count = std::clamp(3.2 * mass_kg, 24.0, 96.0);
        const double rod_segment_mass_kg =
            std::clamp((0.42 * mass_kg) / rod_count, 0.035, 0.42);
        const double rod_velocity_mps =
            std::clamp(920.0 + 0.16 * closure, 450.0, 1450.0) *
            (0.50 + 0.50 * radius_quality);
        const double rod_energy_j =
            0.5 * rod_segment_mass_kg * rod_velocity_mps * rod_velocity_mps *
            std::clamp(spatial_sample.energy_scale, 0.08, 1.20);
        const double cut_capacity_mm =
            (3.0 + 0.022 * std::sqrt(std::max(0.0, rod_energy_j))) *
            pattern *
            std::clamp(0.60 + 0.40 * spatial_sample.hit_estimate, 0.45, 1.35);
        evidence.rod_cut_margin = std::clamp(
            (cut_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0),
            0.0,
            8.0);
        evidence.penetration_margin = std::max(evidence.penetration_margin, evidence.rod_cut_margin);
    }

    if (family == "hit_to_kill") {
        const double body_mass_kg = std::max(8.0, mass_kg * 4.0);
        const double impact_velocity_mps =
            std::clamp(std::max({missile.max_speed, closure, 300.0}), 300.0, 1700.0);
        const double kinetic_energy_j = 0.5 * body_mass_kg * impact_velocity_mps * impact_velocity_mps;
        const double penetration_capacity_mm =
            8.0 + 0.012 * std::sqrt(std::max(0.0, kinetic_energy_j));
        evidence.penetration_margin = std::clamp(
            (penetration_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0),
            0.0,
            10.0);
    }

    return evidence;
}

WarheadSpatialSample sample_warhead_spatial_effect(
    const Missile& missile,
    const Hitbox& target_shape,
    double distance_m,
    double radius_m,
    double axis_weight,
    double orientation_weight,
    double exposure_scale,
    bool direct_hit
) {
    WarheadSpatialSample sample{};
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality = direct_hit || radius_m <= 1.0e-6
        ? 1.0
        : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double exposed_area_m2 = std::max(
        1.0e-4,
        std::max({target_shape.dim_l * target_shape.dim_w,
                  target_shape.dim_l * target_shape.dim_h,
                  target_shape.dim_w * target_shape.dim_h}) *
            std::clamp(exposure_scale, 0.05, 1.25));
    const double sphere_area_m2 =
        4.0 * M_PI * std::max(distance_m * distance_m, 1.0);

    if (family == "fragmentation" || family == "blast_fragmentation") {
        const double fragment_count = std::clamp(18.0 * mass_kg, 80.0, 1200.0);
        sample.sample_count = static_cast<std::uint32_t>(std::round(fragment_count));
        const double pattern_scale = std::clamp(
            (0.70 + 0.30 * axis_weight) * std::clamp(orientation_weight, 0.70, 1.18),
            0.50,
            1.35);
        sample.areal_density_per_m2 =
            fragment_count / sphere_area_m2 *
            pattern_scale *
            (0.35 + 0.65 * radius_quality);
        sample.hit_estimate = fragment_count *
            std::clamp(exposed_area_m2 / sphere_area_m2, 0.0, 0.35) *
            pattern_scale *
            (0.35 + 0.65 * radius_quality);
        sample.energy_scale = std::clamp(
            (0.35 + 0.65 * radius_quality) *
                (0.70 + 0.30 * std::sqrt(mass_kg / std::max(1.0, mass_kg + 20.0))),
            0.05,
            1.10);
        sample.pattern_scale = pattern_scale;
    } else if (family == "continuous_rod") {
        const double rod_count = std::clamp(3.2 * mass_kg, 24.0, 96.0);
        sample.sample_count = static_cast<std::uint32_t>(std::round(rod_count));
        const double side_sweep = std::clamp(
            (axis_weight / 1.25) * std::clamp(orientation_weight, 0.42, 1.30),
            0.15,
            1.25);
        const double span_m = std::max(target_shape.dim_w, target_shape.dim_l);
        const double ring_circumference_m =
            2.0 * M_PI * std::max(distance_m, 1.0);
        sample.hit_estimate = rod_count *
            std::clamp(span_m / ring_circumference_m, 0.0, 0.60) *
            side_sweep *
            (0.45 + 0.55 * radius_quality);
        sample.energy_scale = std::clamp(0.45 + 0.55 * radius_quality, 0.08, 1.15);
        sample.pattern_scale = side_sweep;
    } else if (family == "blast") {
        sample.sample_count = 1;
        sample.hit_estimate = std::clamp(exposed_area_m2 / sphere_area_m2, 0.0, 1.0) *
            (0.65 + 0.35 * radius_quality);
        sample.energy_scale = std::clamp(std::pow(radius_quality, 1.6), 0.05, 1.0);
        sample.pattern_scale = std::clamp(orientation_weight, 0.94, 1.02);
    } else {
        sample.sample_count = 1;
        sample.hit_estimate = direct_hit ? 1.0 : std::clamp(radius_quality, 0.0, 1.0);
        sample.energy_scale = direct_hit ? 1.0 : std::clamp(radius_quality, 0.0, 1.0);
        sample.pattern_scale =
            std::clamp(axis_weight * orientation_weight, 0.25, 1.35);
    }

    sample.hit_estimate = std::max(0.0, sample.hit_estimate);
    sample.hit_fraction = sample.sample_count > 0
        ? std::clamp(sample.hit_estimate / static_cast<double>(sample.sample_count), 0.0, 1.0)
        : 0.0;
    sample.orientation_pattern_scale = std::clamp(orientation_weight, 0.0, 2.0);
    return sample;
}

double scaled_effect_delta(double base, double slope, double severity, double scale) {
    return std::clamp((base + slope * severity) * scale, 0.0, 0.95);
}

double localized_effect_delta(
    double base,
    double slope,
    double severity,
    double warhead_scale,
    double spatial_scale
) {
    const double resolved_spatial_scale = std::clamp(spatial_scale, 0.0, 1.0);
    return std::clamp(
        scaled_effect_delta(base, slope, severity, warhead_scale) * resolved_spatial_scale,
        0.0,
        0.95);
}

double horizontal_speed_mps(const Velocity* velocity) {
    if (!velocity) {
        return 0.0;
    }
    return std::hypot(velocity->vx, velocity->vy);
}

double resolve_closure_mps(flecs::entity missile_entity, flecs::entity target_entity) {
    const Transform* missile_transform = missile_entity.get<Transform>();
    const Transform* target_transform = target_entity.get<Transform>();
    const Velocity* missile_velocity = missile_entity.get<Velocity>();
    const Velocity* target_velocity = target_entity.get<Velocity>();
    if (!missile_transform || !target_transform || !missile_velocity || !target_velocity) {
        return 0.0;
    }

    const double dx = target_transform->x - missile_transform->x;
    const double dy = target_transform->y - missile_transform->y;
    const double dz = target_transform->z - missile_transform->z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return horizontal_speed_mps(missile_velocity) + horizontal_speed_mps(target_velocity);
    }

    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    const double rel_vx = target_velocity->vx - missile_velocity->vx;
    const double rel_vy = target_velocity->vy - missile_velocity->vy;
    const double rel_vz = target_velocity->vz - missile_velocity->vz;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

Vec3 missile_velocity_axis_in_target_body(flecs::entity missile_entity, const Transform& target_transform) {
    const Velocity* missile_velocity = missile_entity.get<Velocity>();
    if (!missile_velocity) {
        return {0.0, 0.0, 0.0};
    }
    return vec3_normalize(
        world_to_body(
            target_transform,
            target_transform.x + missile_velocity->vx,
            target_transform.y + missile_velocity->vy,
            target_transform.z + missile_velocity->vz));
}

Vec3 missile_forward_axis_in_target_body(
    const Transform& missile_transform,
    const Transform& target_transform
) {
    const Math::Vector3 missile_forward_world =
        Math::body_to_world({1.0, 0.0, 0.0}, missile_transform);
    return vec3_normalize(
        math_body_to_local_right_frame(
            Math::world_to_body(missile_forward_world, target_transform)));
}

double warhead_axis_projection_weight(
    const WarheadProfile& profile,
    const Vec3& local_imp,
    const Hitbox& box,
    const Vec3& velocity_axis_body
) {
    const double axis_norm = vec3_norm(velocity_axis_body);
    if (axis_norm <= 1.0e-9) {
        return 1.0;
    }

    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 radial = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    const double radial_norm = vec3_norm(radial);
    if (radial_norm <= 1.0e-9) {
        return 1.0;
    }

    const double axial_alignment = std::abs(vec3_dot(radial, velocity_axis_body));
    const double side_alignment = std::sqrt(std::max(0.0, 1.0 - axial_alignment * axial_alignment));
    const std::string family = warhead_effect_family(profile);

    if (family == "continuous_rod") {
        return std::clamp(0.35 + 0.95 * side_alignment, 0.35, 1.25);
    }
    if (family == "hit_to_kill") {
        return std::clamp(0.70 + 0.45 * axial_alignment, 0.70, 1.15);
    }
    if (family == "blast") {
        return std::clamp(0.85 + 0.20 * axial_alignment, 0.85, 1.05);
    }
    if (family == "fragmentation" || family == "blast_fragmentation") {
        return std::clamp(0.75 + 0.45 * side_alignment, 0.75, 1.20);
    }
    return 1.0;
}

double warhead_orientation_pattern_weight(
    const WarheadProfile& profile,
    const Vec3& local_imp,
    const Hitbox& box,
    const Vec3& orientation_axis_body
) {
    const double axis_norm = vec3_norm(orientation_axis_body);
    if (axis_norm <= 1.0e-9) {
        return 1.0;
    }

    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 radial = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(radial) <= 1.0e-9) {
        return 1.0;
    }

    const double axial_alignment = std::abs(vec3_dot(radial, orientation_axis_body));
    const double side_alignment = std::sqrt(std::max(0.0, 1.0 - axial_alignment * axial_alignment));
    const std::string family = warhead_effect_family(profile);

    if (family == "continuous_rod") {
        return std::clamp(0.42 + 0.88 * side_alignment, 0.42, 1.30);
    }
    if (family == "fragmentation" || family == "blast_fragmentation") {
        return std::clamp(0.78 + 0.34 * side_alignment + 0.08 * axial_alignment, 0.70, 1.18);
    }
    if (family == "hit_to_kill") {
        return std::clamp(0.82 + 0.28 * axial_alignment, 0.82, 1.10);
    }
    if (family == "blast") {
        return std::clamp(0.94 + 0.08 * axial_alignment, 0.94, 1.02);
    }
    return 1.0;
}

std::string classify_local_aspect_bucket(const Vec3& local_imp) {
    if (std::abs(local_imp.x) >= std::abs(local_imp.y)) {
        return local_imp.x >= 0.0 ? "nose" : "tail";
    }
    return "beam";
}

std::string classify_closure_bucket(double closure_mps) {
    if (closure_mps >= 700.0) {
        return "high";
    }
    if (closure_mps > 0.0 && closure_mps <= 250.0) {
        return "low";
    }
    return "medium";
}

std::string classify_miss_distance_bucket(bool direct_structure_hit) {
    return direct_structure_hit ? "direct_hit" : "near_miss";
}

const AircraftVulnerabilityEvidenceRow* find_matching_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile& vulnerability,
    const std::string& family,
    const std::string& aspect_bucket,
    const std::string& closure_bucket,
    const std::string& miss_distance_bucket
) {
    if (!aircraft_vulnerability_has_calibrated_evidence(vulnerability)) {
        return nullptr;
    }
    for (const AircraftVulnerabilityEvidenceRow& row : vulnerability.evidence_rows) {
        if (row.weapon_family == family &&
            row.aspect_bucket == aspect_bucket &&
            row.closure_bucket == closure_bucket &&
            row.miss_distance_bucket == miss_distance_bucket &&
            row.component_name.empty() &&
            row.component_system.empty() &&
            row.component_redundancy_group_id.empty()) {
            return &row;
        }
    }
    return nullptr;
}

bool vulnerability_row_matches_component(
    const AircraftVulnerabilityEvidenceRow& row,
    const DamageComponent* component
) {
    if (!component) {
        return row.component_name.empty() &&
            row.component_system.empty() &&
            row.component_redundancy_group_id.empty();
    }
    if (!row.component_name.empty() && row.component_name != damage_component_key(*component)) {
        return false;
    }
    if (!row.component_system.empty() && row.component_system != component->system) {
        return false;
    }
    if (!row.component_redundancy_group_id.empty() &&
        row.component_redundancy_group_id != damage_component_redundancy_group_key(*component)) {
        return false;
    }
    return true;
}

bool vulnerability_row_matches_mechanism_load(
    const AircraftVulnerabilityEvidenceRow& row,
    const WarheadMechanismLoadEvidence& mechanism_load
) {
    const auto passes_min = [](bool has_value, double threshold, double value) {
        return !has_value || value + 1.0e-9 >= threshold;
    };
    const auto passes_max = [](bool has_value, double threshold, double value) {
        return !has_value || value <= threshold + 1.0e-9;
    };

    return passes_min(
               row.has_min_fragment_energy_j,
               row.min_fragment_energy_j,
               mechanism_load.fragment_energy_j) &&
        passes_max(
               row.has_max_fragment_energy_j,
               row.max_fragment_energy_j,
               mechanism_load.fragment_energy_j) &&
        passes_min(
               row.has_min_fragment_areal_density_per_m2,
               row.min_fragment_areal_density_per_m2,
               mechanism_load.fragment_areal_density_per_m2) &&
        passes_max(
               row.has_max_fragment_areal_density_per_m2,
               row.max_fragment_areal_density_per_m2,
               mechanism_load.fragment_areal_density_per_m2) &&
        passes_min(
               row.has_min_penetration_margin,
               row.min_penetration_margin,
               mechanism_load.penetration_margin) &&
        passes_max(
               row.has_max_penetration_margin,
               row.max_penetration_margin,
               mechanism_load.penetration_margin) &&
        passes_min(
               row.has_min_blast_overpressure_kpa,
               row.min_blast_overpressure_kpa,
               mechanism_load.blast_overpressure_kpa) &&
        passes_max(
               row.has_max_blast_overpressure_kpa,
               row.max_blast_overpressure_kpa,
               mechanism_load.blast_overpressure_kpa) &&
        passes_min(
               row.has_min_blast_impulse_kpa_ms,
               row.min_blast_impulse_kpa_ms,
               mechanism_load.blast_impulse_kpa_ms) &&
        passes_max(
               row.has_max_blast_impulse_kpa_ms,
               row.max_blast_impulse_kpa_ms,
               mechanism_load.blast_impulse_kpa_ms) &&
        passes_min(
               row.has_min_blast_scaled_distance_m_kg13,
               row.min_blast_scaled_distance_m_kg13,
               mechanism_load.blast_scaled_distance_m_kg13) &&
        passes_max(
               row.has_max_blast_scaled_distance_m_kg13,
               row.max_blast_scaled_distance_m_kg13,
               mechanism_load.blast_scaled_distance_m_kg13) &&
        passes_min(
               row.has_min_rod_cut_margin,
               row.min_rod_cut_margin,
               mechanism_load.rod_cut_margin) &&
        passes_max(
               row.has_max_rod_cut_margin,
               row.max_rod_cut_margin,
               mechanism_load.rod_cut_margin) &&
        passes_min(
               row.has_min_surface_incidence_cos,
               row.min_surface_incidence_cos,
               mechanism_load.surface_incidence_cos) &&
        passes_max(
               row.has_max_surface_incidence_cos,
               row.max_surface_incidence_cos,
               mechanism_load.surface_incidence_cos);
}

bool vulnerability_row_has_mechanism_load_gate(
    const AircraftVulnerabilityEvidenceRow& row
) {
    return row.has_min_fragment_energy_j ||
        row.has_max_fragment_energy_j ||
        row.has_min_fragment_areal_density_per_m2 ||
        row.has_max_fragment_areal_density_per_m2 ||
        row.has_min_penetration_margin ||
        row.has_max_penetration_margin ||
        row.has_min_blast_overpressure_kpa ||
        row.has_max_blast_overpressure_kpa ||
        row.has_min_blast_impulse_kpa_ms ||
        row.has_max_blast_impulse_kpa_ms ||
        row.has_min_blast_scaled_distance_m_kg13 ||
        row.has_max_blast_scaled_distance_m_kg13 ||
        row.has_min_rod_cut_margin ||
        row.has_max_rod_cut_margin ||
        row.has_min_surface_incidence_cos ||
        row.has_max_surface_incidence_cos;
}

int vulnerability_row_specificity(const AircraftVulnerabilityEvidenceRow& row) {
    int specificity = 0;
    if (!row.component_name.empty()) {
        specificity += 400;
    }
    if (!row.component_system.empty()) {
        specificity += 200;
    }
    if (!row.component_redundancy_group_id.empty()) {
        specificity += 100;
    }
    if (row.has_min_fragment_energy_j) {
        specificity += 1;
    }
    if (row.has_max_fragment_energy_j) {
        specificity += 1;
    }
    if (row.has_min_fragment_areal_density_per_m2) {
        specificity += 1;
    }
    if (row.has_max_fragment_areal_density_per_m2) {
        specificity += 1;
    }
    if (row.has_min_penetration_margin) {
        specificity += 1;
    }
    if (row.has_max_penetration_margin) {
        specificity += 1;
    }
    if (row.has_min_blast_overpressure_kpa) {
        specificity += 1;
    }
    if (row.has_max_blast_overpressure_kpa) {
        specificity += 1;
    }
    if (row.has_min_blast_impulse_kpa_ms) {
        specificity += 1;
    }
    if (row.has_max_blast_impulse_kpa_ms) {
        specificity += 1;
    }
    if (row.has_min_blast_scaled_distance_m_kg13) {
        specificity += 1;
    }
    if (row.has_max_blast_scaled_distance_m_kg13) {
        specificity += 1;
    }
    if (row.has_min_rod_cut_margin) {
        specificity += 1;
    }
    if (row.has_max_rod_cut_margin) {
        specificity += 1;
    }
    if (row.has_min_surface_incidence_cos) {
        specificity += 1;
    }
    if (row.has_max_surface_incidence_cos) {
        specificity += 1;
    }
    return specificity;
}

const AircraftVulnerabilityEvidenceRow* find_effect_scale_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile& vulnerability,
    const std::string& family,
    const std::string& aspect_bucket,
    const std::string& closure_bucket,
    const std::string& miss_distance_bucket,
    const WarheadMechanismLoadEvidence* mechanism_load
) {
    if (!vulnerability.effect_scale_authority) {
        return nullptr;
    }
    const AircraftVulnerabilityEvidenceRow* best_row = nullptr;
    int best_specificity = -1;
    for (const AircraftVulnerabilityEvidenceRow& row : vulnerability.evidence_rows) {
        if (row.weapon_family != family ||
            row.aspect_bucket != aspect_bucket ||
            row.closure_bucket != closure_bucket ||
            row.miss_distance_bucket != miss_distance_bucket ||
            !row.component_name.empty() ||
            !row.component_system.empty() ||
            !row.component_redundancy_group_id.empty()) {
            continue;
        }
        if (!mechanism_load && vulnerability_row_has_mechanism_load_gate(row)) {
            continue;
        }
        if (mechanism_load &&
            !vulnerability_row_matches_mechanism_load(row, *mechanism_load)) {
            continue;
        }
        const int specificity = vulnerability_row_specificity(row);
        if (specificity > best_specificity) {
            best_specificity = specificity;
            best_row = &row;
        }
    }
    return best_row;
}

const AircraftVulnerabilityEvidenceRow*
find_component_failure_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile& vulnerability,
    const std::string& family,
    const std::string& aspect_bucket,
    const std::string& closure_bucket,
    const std::string& miss_distance_bucket,
    const DamageComponent* component,
    const WarheadMechanismLoadEvidence& mechanism_load,
    bool* component_specific = nullptr
) {
    if (!vulnerability.component_failure_probability_authority) {
        return nullptr;
    }
    const AircraftVulnerabilityEvidenceRow* best_row = nullptr;
    int best_specificity = -1;
    for (const AircraftVulnerabilityEvidenceRow& row : vulnerability.evidence_rows) {
        if (row.weapon_family != family ||
            row.aspect_bucket != aspect_bucket ||
            row.closure_bucket != closure_bucket ||
            row.miss_distance_bucket != miss_distance_bucket ||
            !row.has_component_failure_probability ||
            !vulnerability_row_matches_component(row, component) ||
            !vulnerability_row_matches_mechanism_load(row, mechanism_load)) {
            continue;
        }
        const int specificity = vulnerability_row_specificity(row);
        if (specificity > best_specificity) {
            best_specificity = specificity;
            best_row = &row;
        }
    }
    if (component_specific) {
        *component_specific = best_specificity > 0;
    }
    return best_row;
}

VulnerabilityAdjustment make_vulnerability_adjustment(
    const WarheadProfile& warhead_profile,
    const AircraftVulnerabilityProfile* vulnerability,
    const Vec3& local_imp,
    double closure_mps,
    double spatial_effect_scale,
    bool direct_structure_hit,
    const WarheadMechanismLoadEvidence* mechanism_load
) {
    VulnerabilityAdjustment out{};
    if (!vulnerability) {
        return out;
    }
    out.profile_present = true;
    out.synthetic = vulnerability->synthetic;
    out.calibrated_evidence = aircraft_vulnerability_has_calibrated_evidence(*vulnerability);
    out.pk_authority = aircraft_vulnerability_pk_authority(*vulnerability);
    out.deterministic_fuze_authority =
        aircraft_vulnerability_deterministic_fuze_authority(*vulnerability);
    out.evidence_dataset_valid = vulnerability->evidence_dataset_valid;
    out.provenance = vulnerability->provenance;
    out.calibration_status = vulnerability->calibration_status;
    out.evidence_dataset_ref = vulnerability->evidence_dataset_ref;
    out.evidence_schema_version = vulnerability->evidence_schema_version;
    out.evidence_source_kind = vulnerability->evidence_source_kind;
    out.evidence_source_ref = vulnerability->evidence_source_ref;
    out.evidence_validation_artifact_ref =
        vulnerability->evidence_validation_artifact_ref;
    out.evidence_validation_manifest_schema_version =
        vulnerability->evidence_validation_manifest_schema_version;
    out.evidence_validation_status =
        vulnerability->evidence_validation_status;
    out.evidence_validation_artifact_sha256 =
        vulnerability->evidence_validation_artifact_sha256;
    out.evidence_validated_surrogate_model_ref =
        vulnerability->evidence_validated_surrogate_model_ref;
    out.evidence_validation_benchmark_ref =
        vulnerability->evidence_validation_benchmark_ref;
    out.evidence_validation_metrics_ref =
        vulnerability->evidence_validation_metrics_ref;
    out.evidence_validation_acceptance_criteria_ref =
        vulnerability->evidence_validation_acceptance_criteria_ref;

    const std::string family = warhead_effect_family(warhead_profile);
    double family_scale = vulnerability->fragmentation_scale;
    if (family == "blast") {
        family_scale = vulnerability->blast_scale;
    } else if (family == "continuous_rod") {
        family_scale = vulnerability->continuous_rod_scale;
    } else if (family == "hit_to_kill") {
        family_scale = vulnerability->hit_to_kill_scale;
    }
    out.family_scale = family_scale;

    out.aspect_bucket = classify_local_aspect_bucket(local_imp);
    if (out.aspect_bucket == "nose") {
        out.aspect_scale = vulnerability->nose_aspect_scale;
    } else if (out.aspect_bucket == "tail") {
        out.aspect_scale = vulnerability->tail_aspect_scale;
    } else if (out.aspect_bucket == "beam") {
        out.aspect_scale = vulnerability->beam_aspect_scale;
    }

    out.closure_mps = closure_mps;
    const std::string closure_bucket = classify_closure_bucket(closure_mps);
    if (closure_mps >= 700.0) {
        out.closure_scale = vulnerability->high_closure_scale;
    } else if (closure_mps > 0.0 && closure_mps <= 250.0) {
        out.closure_scale = vulnerability->low_closure_scale;
    }

    out.miss_distance_scale = direct_structure_hit
        ? vulnerability->direct_hit_scale
        : vulnerability->near_miss_scale;

    const std::string miss_distance_bucket =
        classify_miss_distance_bucket(direct_structure_hit);
    const AircraftVulnerabilityEvidenceRow* evidence_row =
        find_effect_scale_vulnerability_evidence_row(
            *vulnerability,
            family,
            out.aspect_bucket,
            closure_bucket,
            miss_distance_bucket,
            mechanism_load);
    if (evidence_row) {
        out.family_scale = evidence_row->family_scale;
        out.aspect_scale = evidence_row->aspect_scale;
        out.closure_scale = evidence_row->closure_scale;
        out.miss_distance_scale = evidence_row->miss_distance_scale;
        out.scale = evidence_row->effect_scale;
        out.effect_scale_source = "vulnerability_evidence_row";
        out.effect_scale_evidence_row_id = evidence_row->row_id;
        out.effect_scale_evidence_source_ref = evidence_row->source_ref;
        out.effect_scale_evidence_provenance = evidence_row->provenance;
    }

    const double raw_scale =
        out.family_scale * out.aspect_scale * out.closure_scale * out.miss_distance_scale;
    const double authority_floor = vulnerability->synthetic ? 0.80 : 0.55;
    const double authority_ceiling = vulnerability->synthetic ? 1.25 : 1.60;
    if (!evidence_row) {
        out.scale = std::clamp(raw_scale, authority_floor, authority_ceiling);
    } else {
        out.scale = std::clamp(out.scale, authority_floor, authority_ceiling);
    }

    if (!direct_structure_hit) {
        out.scale = std::clamp(out.scale * (0.85 + 0.15 * std::clamp(spatial_effect_scale, 0.0, 1.0)),
                               authority_floor,
                               authority_ceiling);
    }

    return out;
}

bool is_structured_damage_air_target(flecs::entity target_entity) {
    const KeyEntity* key = target_entity.get<KeyEntity>();
    return key &&
        (key->type == UnitType::Aircraft || key->type == UnitType::C2Node) &&
        target_entity.get<HitboxConfig>() != nullptr &&
        target_entity.get<SystemHealth>() != nullptr &&
        target_entity.get<PlatformDamageState>() != nullptr;
}

void clamp_platform_damage_state(PlatformDamageState* state) {
    if (!state) return;
    state->mission_capability = std::clamp(state->mission_capability, 0.0, 1.0);
    state->mobility_capability = std::clamp(state->mobility_capability, 0.0, 1.0);
    state->sensor_capability = std::clamp(state->sensor_capability, 0.0, 1.0);
    state->survivability_margin = std::clamp(state->survivability_margin, 0.0, 1.0);

    state->mission_kill = state->mission_capability <= 0.25;
    state->mobility_kill = state->mobility_capability <= 0.25;
    state->sensor_kill = state->sensor_capability <= 0.25;

    if (state->survivability_margin <= 0.0) {
        state->loss_state = PlatformLossState::Lost;
    } else if (state->mobility_kill) {
        state->loss_state = PlatformLossState::MobilityKill;
    } else if (state->sensor_kill) {
        state->loss_state = PlatformLossState::SensorKill;
    } else if (state->mission_kill) {
        state->loss_state = PlatformLossState::MissionKill;
    } else {
        state->loss_state = PlatformLossState::CombatCapable;
    }
}

class DefaultEffectsModel : public IEffectsModel {
public:
    EffectsResult on_proximity_hit(flecs::world world,
                                   flecs::entity missile_entity,
                                   const Missile& missile,
                                   flecs::entity target_entity) override {
        EffectsResult result;

        Score* score = nullptr;
        auto attacker = world.entity(missile.attacker_id);
        if (attacker.is_valid()) {
            score = attacker.get_mut<Score>();
        }
        
        const bool structured_air_target = is_structured_damage_air_target(target_entity);

        // --- 1. Generic Health Handling (Legacy) ---
        Health* hp = target_entity.get_mut<Health>();
        if (hp && !structured_air_target) {
            hp->current_hp -= missile.damage;
            if (score) {
                score->total_reward += missile.damage;
                score->hits_landed++;
            }
            if (hp->current_hp <= 0) {
                target_entity.destruct();
                if (score) { 
                    score->total_reward += 1000.0; 
                    score->kills_confirmed++;
                }
                spdlog::info("SPLASH! Target {} Destroyed.", target_entity.id());
                return result; // Target dead, exit
            }
        }

        // --- 2. Geometric Damage Logic (New) ---
        const HitboxConfig* hitboxes = target_entity.get<HitboxConfig>();
        SystemHealth* sys_health = target_entity.get_mut<SystemHealth>();
        PlatformDamageState* platform_damage = target_entity.get_mut<PlatformDamageState>();
        AircraftDamageState* aircraft_damage = target_entity.get_mut<AircraftDamageState>();
        ComponentDamageState* component_damage = target_entity.get_mut<ComponentDamageState>();
        const AircraftVulnerabilityProfile* aircraft_vulnerability =
            target_entity.get<AircraftVulnerabilityProfile>();
        const Transform* t_tgt = target_entity.get<Transform>();
        const Transform* t_msl = missile_entity.get<Transform>();

        if (hitboxes && sys_health && t_tgt && t_msl) {
            // Transform Missile Pos to Target Body Frame
            Vec3 local_imp = world_to_body(*t_tgt, t_msl->x, t_msl->y, t_msl->z);
            const double closure_mps = resolve_closure_mps(missile_entity, target_entity);
            const Vec3 missile_axis_body = missile_velocity_axis_in_target_body(missile_entity, *t_tgt);
            const Vec3 warhead_orientation_axis_body =
                missile_forward_axis_in_target_body(*t_msl, *t_tgt);
            
            // Check Intersections
            bool structure_hit = false;
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
            bool direct_hitbox_intersection = false;
            std::unordered_set<std::string> processed_air_systems;
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
            double air_structure_spatial_scale = 0.0;
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
            std::uint64_t component_rng_state = missile.rng_state;
            std::uint32_t projected_hitbox_count = 0;
            const double severity = std::clamp(missile.damage / 180.0, 0.15, 0.65);
            std::uint32_t component_hit_count = 0;
            std::vector<ComponentMechanismLoadRow> component_mechanism_load_rows;
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
            WarheadMechanismLoadEvidence component_primary_mechanism_load{};
            const auto make_component_mechanism_load_row = [&](
                const DamageComponent& component,
                double effect_scale,
                double component_scale,
                bool direct_hit,
                double distance_m,
                const WarheadMechanismLoadEvidence& mechanism_load) {
                ComponentMechanismLoadRow row{};
                row.component_name = component.name.empty() ? component.system : component.name;
                row.component_system = component.system;
                row.component_redundancy_group_id =
                    damage_component_redundancy_group_key(component);
                row.direct_hit = direct_hit;
                row.distance_m = std::max(0.0, distance_m);
                row.effect_scale = effect_scale;
                row.component_threshold_scale = component_scale;
                row.mechanism_fragment_energy_j = mechanism_load.fragment_energy_j;
                row.mechanism_fragment_areal_density_per_m2 =
                    mechanism_load.fragment_areal_density_per_m2;
                row.mechanism_penetration_margin = mechanism_load.penetration_margin;
                row.mechanism_blast_overpressure_kpa = mechanism_load.blast_overpressure_kpa;
                row.mechanism_blast_impulse_kpa_ms = mechanism_load.blast_impulse_kpa_ms;
                row.mechanism_blast_scaled_distance_m_kg13 =
                    mechanism_load.blast_scaled_distance_m_kg13;
                row.mechanism_rod_cut_margin = mechanism_load.rod_cut_margin;
                row.mechanism_surface_incidence_cos = mechanism_load.surface_incidence_cos;
                return row;
            };
            const auto record_component_hit = [&](
                const DamageComponent& component,
                double effect_scale,
                double component_scale,
                bool direct_hit,
                double distance_m,
                const WarheadMechanismLoadEvidence& mechanism_load) -> ComponentMechanismLoadRow* {
                ++component_hit_count;
                component_mechanism_load_rows.push_back(
                    make_component_mechanism_load_row(
                        component,
                        effect_scale,
                        component_scale,
                        direct_hit,
                        distance_m,
                        mechanism_load));
                ComponentMechanismLoadRow& row = component_mechanism_load_rows.back();
                if (effect_scale > component_primary_effect_scale) {
                    component_primary_effect_scale = effect_scale;
                    component_primary_name = component.name.empty() ? component.system : component.name;
                    component_primary_system = component.system;
                    component_primary_redundancy_group = component.redundancy_group;
                    component_primary_critical = component.critical;
                    component_primary_redundancy_group_id =
                        damage_component_redundancy_group_key(component);
                    component_primary_mechanism_load = mechanism_load;
                }
                return &row;
            };
            const auto sample_component_failure = [&](
                const std::string& system,
                double base_severity,
                double mechanism_scale,
                double component_scale,
                bool direct_hit,
                const WarheadMechanismLoadEvidence& mechanism_load,
                bool component_critical,
                double redundancy_group,
                const DamageComponent* component,
                ComponentMechanismLoadRow* component_row
            ) {
                if (!structured_air_target) {
                    return;
                }
                double resolved_component_scale = component_scale;
                if (!component_critical) {
                    resolved_component_scale *= 0.72;
                }
                if (redundancy_group > 0.0) {
                    resolved_component_scale *=
                        std::clamp(1.0 / std::sqrt(1.0 + redundancy_group), 0.45, 1.0);
                }
                double failure_probability = component_failure_probability(
                    base_severity,
                    mechanism_scale,
                    resolved_component_scale,
                    direct_hit,
                    mechanism_load);
                std::string failure_probability_source = "synthetic_sigmoid";
                bool failure_probability_calibrated = false;
                bool failure_probability_component_specific = false;
                std::string failure_probability_evidence_dataset_ref;
                std::string failure_probability_evidence_row_id;
                std::string failure_probability_evidence_source_ref;
                std::string failure_probability_evidence_provenance;
                std::string failure_probability_evidence_component_name;
                std::string failure_probability_evidence_component_system;
                std::string failure_probability_evidence_component_redundancy_group_id;
                const std::string failure_family =
                    warhead_effect_family(missile.warhead_profile);
                const std::string failure_aspect_bucket =
                    classify_local_aspect_bucket(local_imp);
                const std::string failure_closure_bucket =
                    classify_closure_bucket(closure_mps);
                const std::string failure_miss_distance_bucket =
                    classify_miss_distance_bucket(direct_hit);
                if (aircraft_vulnerability) {
                    const AircraftVulnerabilityEvidenceRow* failure_row =
                        find_component_failure_vulnerability_evidence_row(
                            *aircraft_vulnerability,
                            failure_family,
                            failure_aspect_bucket,
                            failure_closure_bucket,
                            failure_miss_distance_bucket,
                            component,
                            mechanism_load,
                            &failure_probability_component_specific);
                    if (failure_row) {
                        failure_probability = std::clamp(
                            failure_row->component_failure_probability,
                            0.0,
                            1.0);
                        failure_probability_source = "vulnerability_evidence_row";
                        failure_probability_calibrated = true;
                        failure_probability_evidence_dataset_ref =
                            aircraft_vulnerability->evidence_dataset_ref;
                        failure_probability_evidence_row_id =
                            failure_row->row_id;
                        failure_probability_evidence_source_ref =
                            failure_row->source_ref;
                        failure_probability_evidence_provenance =
                            failure_row->provenance;
                        failure_probability_evidence_component_name =
                            failure_row->component_name;
                        failure_probability_evidence_component_system =
                            failure_row->component_system;
                        failure_probability_evidence_component_redundancy_group_id =
                            failure_row->component_redundancy_group_id;
                    }
                }
                const double failure_sample = rand_uniform01(component_rng_state);
                if (component_row) {
                    component_row->component_failure_probability = failure_probability;
                    component_row->component_failure_probability_source =
                        failure_probability_source;
                    component_row->component_failure_probability_calibrated =
                        failure_probability_calibrated;
                    component_row->component_failure_probability_evidence_dataset_ref =
                        failure_probability_evidence_dataset_ref;
                    component_row->component_failure_probability_evidence_row_id =
                        failure_probability_evidence_row_id;
                    component_row->component_failure_probability_evidence_source_ref =
                        failure_probability_evidence_source_ref;
                    component_row->component_failure_probability_evidence_provenance =
                        failure_probability_evidence_provenance;
                    component_row->component_failure_sample = failure_sample;
                    component_row->component_failure_probability_authority =
                        failure_probability_source == "vulnerability_evidence_row";
                    component_row->component_failure_probability_component_specific =
                        failure_probability_component_specific;
                    component_row->component_failure_probability_weapon_family =
                        failure_family;
                    component_row->component_failure_probability_aspect_bucket =
                        failure_aspect_bucket;
                    component_row->component_failure_probability_closure_bucket =
                        failure_closure_bucket;
                    component_row->component_failure_probability_miss_distance_bucket =
                        failure_miss_distance_bucket;
                    component_row->component_failure_probability_evidence_component_name =
                        failure_probability_evidence_component_name;
                    component_row->component_failure_probability_evidence_component_system =
                        failure_probability_evidence_component_system;
                    component_row->component_failure_probability_evidence_component_redundancy_group_id =
                        failure_probability_evidence_component_redundancy_group_id;
                }
                if (!sampled_component_failure_probability_seen ||
                    failure_probability > sampled_component_failure_probability) {
                    sampled_component_failure_probability_seen = true;
                    sampled_component_failure_probability =
                        failure_probability;
                    sampled_component_failure_probability_source =
                        failure_probability_source;
                    sampled_component_failure_probability_calibrated =
                        failure_probability_calibrated;
                    sampled_component_failure_probability_evidence_dataset_ref =
                        failure_probability_evidence_dataset_ref;
                    sampled_component_failure_probability_evidence_row_id =
                        failure_probability_evidence_row_id;
                    sampled_component_failure_probability_evidence_source_ref =
                        failure_probability_evidence_source_ref;
                    sampled_component_failure_probability_evidence_provenance =
                        failure_probability_evidence_provenance;
                }
                sampled_component_failure_sample =
                    std::min(sampled_component_failure_sample, failure_sample);
                if (component) {
                    const ComponentDamageSample component_sample =
                        apply_component_damage_state(
                            *component,
                            failure_probability,
                            mechanism_scale * resolved_component_scale,
                            component_damage,
                            sys_health);
                    const std::string component_key = damage_component_key(*component);
                    if (component_key == component_primary_name) {
                        component_primary_integrity = component_sample.integrity;
                        component_redundancy_group_availability =
                            component_sample.group_availability;
                        component_redundancy_group_member_count =
                            component_sample.group_member_count;
                        component_redundancy_group_failed_count =
                            component_sample.group_failed_count;
                    }
                    const ComponentDependencyPropagationSummary dependency_summary =
                        apply_component_dependency_damage(
                            *component,
                            component_sample,
                            failure_probability,
                            mechanism_scale * resolved_component_scale,
                            sys_health,
                            aircraft_damage,
                            platform_damage);
                    if (component_row) {
                        component_row->component_dependency_propagation_count =
                            dependency_summary.propagation_count;
                        component_row->component_dependency_target_system =
                            dependency_summary.target_system;
                        component_row->component_dependency_edge_type =
                            dependency_summary.edge_type;
                        component_row->component_dependency_threshold =
                            dependency_summary.threshold;
                        component_row->component_dependency_delay_s =
                            dependency_summary.delay_s;
                        component_row->component_dependency_direction =
                            dependency_summary.direction;
                        component_row->component_dependency_provenance =
                            dependency_summary.provenance;
                        component_row->component_dependency_source_availability =
                            dependency_summary.source_availability;
                        component_row->component_dependency_effective_scale =
                            dependency_summary.effective_scale;
                        component_row->component_dependency_propagated =
                            dependency_summary.propagated;
                    }
                }
                if (failure_sample <= failure_probability) {
                    ++component_failure_count;
                    apply_component_failure_impulse(
                        system,
                        failure_probability,
                        resolved_component_scale,
                        mechanism_scale,
                        aircraft_damage,
                        platform_damage);
                }
            };
            const auto note_air_system_hit = [&](
                const std::string& system,
                double system_spatial_scale,
                const DamageComponent* component = nullptr
            ) {
                const double resolved_spatial_scale = std::clamp(system_spatial_scale, 0.0, 1.0);
                if (system_is_air_sensor(system)) {
                    air_sensor_hit = true;
                    air_sensor_spatial_scale =
                        std::max(air_sensor_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_air_propulsion_or_fuel(system)) {
                    air_propulsion_or_fuel_hit = true;
                    air_propulsion_or_fuel_spatial_scale =
                        std::max(air_propulsion_or_fuel_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_air_propulsion(system)) {
                    air_propulsion_hit = true;
                    air_propulsion_spatial_scale =
                        std::max(air_propulsion_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_air_fuel(system)) {
                    air_fuel_hit = true;
                    air_fuel_spatial_scale = std::max(air_fuel_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_air_control_surface(system)) {
                    air_control_hit = true;
                    air_control_spatial_scale =
                        std::max(air_control_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_crew_or_cockpit(system)) {
                    air_crew_hit = true;
                    air_crew_spatial_scale = std::max(air_crew_spatial_scale, resolved_spatial_scale);
                }
                const CrewConsequenceKind crew_kind = classify_crew_consequence(
                    system,
                    component ? damage_component_key(*component) : "");
                if (crew_kind == CrewConsequenceKind::Pilot) {
                    air_pilot_hit = true;
                    air_pilot_spatial_scale =
                        std::max(air_pilot_spatial_scale, resolved_spatial_scale);
                } else if (crew_kind == CrewConsequenceKind::MissionCrew) {
                    air_mission_crew_hit = true;
                    air_mission_crew_spatial_scale =
                        std::max(air_mission_crew_spatial_scale, resolved_spatial_scale);
                } else if (crew_kind == CrewConsequenceKind::CommandNavigation) {
                    air_command_navigation_hit = true;
                    air_command_navigation_spatial_scale =
                        std::max(air_command_navigation_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_mission_or_combat(system)) {
                    air_mission_or_combat_hit = true;
                    air_mission_or_combat_spatial_scale =
                        std::max(air_mission_or_combat_spatial_scale, resolved_spatial_scale);
                }
                if (system_is_air_structure(system)) {
                    air_structure_spatial_scale =
                        std::max(air_structure_spatial_scale, resolved_spatial_scale);
                }
            };
            const auto apply_system_effect = [&](
                const std::string& system,
                double system_base_severity,
                double mechanism_scale,
                double component_scale,
                bool direct_hit,
                const WarheadMechanismLoadEvidence& mechanism_load = WarheadMechanismLoadEvidence{},
                bool component_critical = true,
                double redundancy_group = 0.0,
                const DamageComponent* component = nullptr,
                ComponentMechanismLoadRow* component_row = nullptr
            ) {
                const double resolved_component_scale = std::clamp(component_scale, 0.40, 1.80);
                sys_health->systems[system] = std::max(
                    0.0,
                    sys_health->systems[system] -
                        std::clamp(
                            system_base_severity * mechanism_scale * resolved_component_scale,
                            0.02,
                            0.95));
                sample_component_failure(
                    system,
                    system_base_severity,
                    mechanism_scale,
                    resolved_component_scale,
                    direct_hit,
                    mechanism_load,
                    component_critical,
                    redundancy_group,
                    component,
                    component_row);
                if (structured_air_target && component) {
                    apply_control_axis_component_damage(
                        *component,
                        system_base_severity,
                        mechanism_scale,
                        resolved_component_scale,
                        direct_hit,
                        aircraft_damage);
                }

                if (platform_damage) {
                    if (structured_air_target) {
                        note_air_system_hit(system, mechanism_scale, component);
                    } else {
                        platform_damage->survivability_margin -= 0.08 + 0.08 * severity;
                        if (system_name_matches(system, "radar")) {
                            platform_damage->sensor_capability -= 0.35 + 0.20 * severity;
                            platform_damage->fire_severity += 0.05 + 0.05 * severity;
                        }
                        if (system_name_matches(system, "engineering") ||
                            system_name_matches(system, "engine") ||
                            system_name_matches(system, "fuel")) {
                            platform_damage->mobility_capability -= 0.25 + 0.20 * severity;
                            platform_damage->fire_severity += 0.08 + 0.08 * severity;
                            platform_damage->flooding_severity += 0.04 + 0.05 * severity;
                            platform_damage->ongoing_hull_breach += 0.03 + 0.04 * severity;
                        }
                        if (system_name_matches(system, "combat") ||
                            system_name_matches(system, "command") ||
                            system_name_matches(system, "data_link") ||
                            system_name_matches(system, "vls") ||
                            system_name_matches(system, "gun") ||
                            system_name_matches(system, "radar")) {
                            platform_damage->mission_capability -= 0.20 + 0.20 * severity;
                            platform_damage->fire_severity += 0.04 + 0.04 * severity;
                        }
                        platform_damage->fire_severity =
                            std::clamp(platform_damage->fire_severity, 0.0, 1.0);
                        platform_damage->flooding_severity =
                            std::clamp(platform_damage->flooding_severity, 0.0, 1.0);
                        platform_damage->ongoing_hull_breach =
                            std::clamp(platform_damage->ongoing_hull_breach, 0.0, 1.0);
                    }
                }

                if (sys_health->systems[system] <= 0.5) {
                    if (system == "radar" || system_name_matches(system, "radar")) {
                        if (Sensor* s = target_entity.get_mut<Sensor>()) {
                            s->max_range *= 0.4;
                            spdlog::warn("   -> RADAR DEGRADED!");
                        }
                    } else if (!aircraft_damage &&
                               (system == "engineering" || system == "engine" ||
                                system == "engine_left" || system == "engine_right")) {
                        if (Propulsion* p = target_entity.get_mut<Propulsion>()) {
                            p->mil_thrust_n *= 0.75;
                            p->ab_thrust_n *= 0.75;
                            spdlog::warn("   -> ENGINE DAMAGE! Thrust reduced.");
                        }
                    } else if (!aircraft_damage && system == "fuel") {
                        if (Mass* m = target_entity.get_mut<Mass>()) {
                            m->fuel_leak_rate_kg_s += 5.0;
                            spdlog::warn("   -> FUEL TANK RUPTURED! Massive Leak Started.");
                        }
                    } else if (!aircraft_damage && system_is_air_control_surface(system)) {
                        if (FlightModel* f = target_entity.get_mut<FlightModel>()) {
                            f->max_g *= 0.65;
                            f->max_turn_rate *= 0.70;
                            f->max_accel *= 0.80;
                            f->max_climb_rate *= 0.75;
                            spdlog::warn("   -> FLIGHT CONTROL DAMAGE! Maneuver limits reduced.");
                        }
                    }
                }
            };
            const WarheadEffectProfile warhead_effects =
                structured_air_target ? make_warhead_effect_profile(missile.warhead_profile) : WarheadEffectProfile{};
            const WarheadSpatialProjectionProfile warhead_projection = structured_air_target
                ? make_warhead_spatial_projection_profile(missile.warhead_profile)
                : WarheadSpatialProjectionProfile{};
            const double vulnerability_system_scale =
                structured_air_target && aircraft_vulnerability
                    ? make_vulnerability_adjustment(
                          missile.warhead_profile,
                          aircraft_vulnerability,
                          local_imp,
                          closure_mps,
                          1.0,
                          true,
                          nullptr).scale
                    : 1.0;
            const double system_severity = structured_air_target
                ? std::clamp(
                    severity * warhead_effects.system_damage_scale * vulnerability_system_scale,
                    0.05,
                    0.95)
                : severity;
            double spatial_effect_scale = 0.0;
            const auto record_warhead_spatial_sample = [&](const WarheadSpatialSample& sample) {
                sampled_warhead_spatial_sample_count += sample.sample_count;
                sampled_warhead_spatial_hit_estimate += sample.hit_estimate;
                sampled_warhead_spatial_energy_scale =
                    std::min(sampled_warhead_spatial_energy_scale, sample.energy_scale);
                sampled_warhead_spatial_pattern_scale =
                    std::max(sampled_warhead_spatial_pattern_scale, sample.pattern_scale);
                sampled_warhead_orientation_pattern_scale =
                    std::max(
                        sampled_warhead_orientation_pattern_scale,
                        sample.orientation_pattern_scale);
                sampled_warhead_spatial_hit_fraction =
                    sampled_warhead_spatial_sample_count > 0
                        ? std::clamp(
                              sampled_warhead_spatial_hit_estimate /
                                  static_cast<double>(sampled_warhead_spatial_sample_count),
                              0.0,
                              1.0)
                        : 0.0;
            };
            const auto record_mechanism_load = [&](const WarheadMechanismLoadEvidence& load) {
                sampled_mechanism_fragment_energy_j =
                    std::max(sampled_mechanism_fragment_energy_j, load.fragment_energy_j);
                sampled_mechanism_fragment_areal_density_per_m2 =
                    std::max(
                        sampled_mechanism_fragment_areal_density_per_m2,
                        load.fragment_areal_density_per_m2);
                sampled_mechanism_penetration_margin =
                    std::max(sampled_mechanism_penetration_margin, load.penetration_margin);
                sampled_mechanism_blast_overpressure_kpa =
                    std::max(sampled_mechanism_blast_overpressure_kpa, load.blast_overpressure_kpa);
                sampled_mechanism_blast_impulse_kpa_ms =
                    std::max(sampled_mechanism_blast_impulse_kpa_ms, load.blast_impulse_kpa_ms);
                if (load.blast_scaled_distance_m_kg13 > 0.0 &&
                    (sampled_mechanism_blast_scaled_distance_m_kg13 <= 0.0 ||
                     load.blast_scaled_distance_m_kg13 <
                         sampled_mechanism_blast_scaled_distance_m_kg13)) {
                    sampled_mechanism_blast_scaled_distance_m_kg13 =
                        load.blast_scaled_distance_m_kg13;
                }
                sampled_mechanism_rod_cut_margin =
                    std::max(sampled_mechanism_rod_cut_margin, load.rod_cut_margin);
                const double incidence_cos =
                    std::clamp(load.surface_incidence_cos, 0.0, 1.0);
                sampled_mechanism_surface_incidence_cos =
                    sampled_mechanism_surface_incidence_seen
                        ? std::min(sampled_mechanism_surface_incidence_cos, incidence_cos)
                        : incidence_cos;
                sampled_mechanism_surface_incidence_seen = true;
            };
            for (const auto& box : hitboxes->hitboxes) {
                if (check_hitbox(local_imp, box)) {
                    structure_hit = true;
                    direct_hitbox_intersection = true;
                    spdlog::info("HITBOX >>> Box {} HIT! Protected Systems:", box.id);

                    bool component_direct_hit = false;
                    if (structured_air_target && !box.components.empty()) {
                        for (const auto& component : box.components) {
                            if (!check_component(local_imp, component)) {
                                continue;
                            }
                            component_direct_hit = true;
                            const Hitbox component_box = component_as_hitbox(component, box);
                            const double armor_scale = warhead_mechanism_armor_scale(
                                missile,
                                component_box,
                                0.0,
                                1.0,
                                1.0,
                                true);
                            const double exposure_scale =
                                component_projected_exposure_scale(local_imp, component);
                            const double orientation_weight = warhead_orientation_pattern_weight(
                                missile.warhead_profile,
                                local_imp,
                                component_box,
                                warhead_orientation_axis_body);
                            const WarheadSpatialSample spatial_sample =
                                sample_warhead_spatial_effect(
                                    missile,
                                    component_box,
                                    0.0,
                                    1.0,
                                    1.0,
                                    orientation_weight,
                                    exposure_scale,
                                    true);
                            record_warhead_spatial_sample(spatial_sample);
                            const WarheadMechanismLoadEvidence mechanism_load =
                                with_surface_incidence(
                                    estimate_warhead_mechanism_load(
                                        missile,
                                        component_box,
                                        0.0,
                                        1.0,
                                        1.0,
                                        orientation_weight,
                                        exposure_scale,
                                        true,
                                        closure_mps,
                                        spatial_sample),
                                    hitbox_surface_incidence_cos(
                                        local_imp,
                                        component_box,
                                        missile_axis_body));
                            record_mechanism_load(mechanism_load);
                            const double direct_mechanism_scale =
                                std::clamp(armor_scale * exposure_scale, 0.05, 1.10);
                            spatial_effect_scale =
                                std::max(spatial_effect_scale, direct_mechanism_scale);
                            sampled_mechanism_scale =
                                std::max(sampled_mechanism_scale, direct_mechanism_scale);
                            sampled_armor_scale = std::min(sampled_armor_scale, armor_scale);
                            sampled_exposure_scale = std::min(sampled_exposure_scale, exposure_scale);

                            const double component_scale =
                                component_mechanism_threshold_scale(
                                    missile.warhead_profile,
                                    component.system) *
                                std::clamp(component.threshold_scale, 0.40, 1.80) *
                                component_authored_mechanism_threshold_scale(
                                    missile.warhead_profile,
                                    component);
                            sampled_component_threshold_scale =
                                std::max(sampled_component_threshold_scale, component_scale);
                            ComponentMechanismLoadRow* component_row = record_component_hit(
                                component,
                                direct_mechanism_scale,
                                component_scale,
                                true,
                                0.0,
                                mechanism_load);
                            apply_system_effect(
                                component.system,
                                system_severity,
                                direct_mechanism_scale,
                                component_scale,
                                true,
                                mechanism_load,
                                component.critical,
                                component.redundancy_group,
                                &component,
                                component_row);
                            spdlog::info(
                                "   - component {}:{} Status: {:.2f} component_scale={:.2f}",
                                component.name.empty() ? component.system : component.name,
                                component.system,
                                sys_health->systems[component.system],
                                component_scale);
                        }
                    }

                    if (!structured_air_target || box.components.empty() || !component_direct_hit) {
                        const double armor_scale = structured_air_target
                            ? warhead_mechanism_armor_scale(
                                  missile,
                                  box,
                                  0.0,
                                  1.0,
                                  1.0,
                                  true)
                            : 1.0;
                        const double exposure_scale = structured_air_target
                            ? hitbox_projected_exposure_scale(local_imp, box)
                            : 1.0;
                        WarheadMechanismLoadEvidence mechanism_load{};
                        if (structured_air_target) {
                            const double orientation_weight = warhead_orientation_pattern_weight(
                                missile.warhead_profile,
                                local_imp,
                                box,
                                warhead_orientation_axis_body);
                            const WarheadSpatialSample spatial_sample =
                                sample_warhead_spatial_effect(
                                    missile,
                                    box,
                                    0.0,
                                    1.0,
                                    1.0,
                                    orientation_weight,
                                    exposure_scale,
                                    true);
                            record_warhead_spatial_sample(spatial_sample);
                            mechanism_load = with_surface_incidence(
                                estimate_warhead_mechanism_load(
                                    missile,
                                    box,
                                    0.0,
                                    1.0,
                                    1.0,
                                    orientation_weight,
                                    exposure_scale,
                                    true,
                                    closure_mps,
                                    spatial_sample),
                                hitbox_surface_incidence_cos(
                                    local_imp,
                                    box,
                                    missile_axis_body));
                            record_mechanism_load(mechanism_load);
                        }
                        const double direct_mechanism_scale =
                            std::clamp(armor_scale * exposure_scale, 0.05, 1.10);
                        spatial_effect_scale = std::max(spatial_effect_scale, direct_mechanism_scale);
                        sampled_mechanism_scale =
                            std::max(sampled_mechanism_scale, direct_mechanism_scale);
                        sampled_armor_scale = std::min(sampled_armor_scale, armor_scale);
                        sampled_exposure_scale = std::min(sampled_exposure_scale, exposure_scale);

                        for (const auto& system : box.protected_systems) {
                            if (structured_air_target &&
                                !processed_air_systems.insert(system).second) {
                                continue;
                            }
                            const double component_scale = structured_air_target
                                ? component_mechanism_threshold_scale(missile.warhead_profile, system)
                                : 1.0;
                            sampled_component_threshold_scale =
                                std::max(sampled_component_threshold_scale, component_scale);
                            apply_system_effect(
                                system,
                                system_severity,
                                direct_mechanism_scale,
                                component_scale,
                                true,
                                mechanism_load);
                            spdlog::info(
                                "   - {} Status: {:.2f} component_scale={:.2f}",
                                system,
                                sys_health->systems[system],
                                component_scale);
                        }
                    }
                }
            }

            if (structured_air_target && !structure_hit && !hitboxes->hitboxes.empty()) {
                std::vector<SpatialProjectionCandidate> candidates;
                candidates.reserve(hitboxes->hitboxes.size());
                const double spatial_radius_m =
                    resolve_spatial_projection_radius_m(missile, warhead_projection);
                const bool broad_spatial_projection =
                    warhead_effect_family(missile.warhead_profile) == "blast" ||
                    warhead_effect_family(missile.warhead_profile) == "fragmentation" ||
                    warhead_effect_family(missile.warhead_profile) == "blast_fragmentation";
                for (const auto& box : hitboxes->hitboxes) {
                    if (broad_spatial_projection) {
                        const double distance_m = hitbox_surface_distance(local_imp, box);
                        if (distance_m <= spatial_radius_m) {
                            const double axis_weight = warhead_axis_projection_weight(
                                missile.warhead_profile,
                                local_imp,
                                box,
                                missile_axis_body);
                            const double armor_scale = warhead_mechanism_armor_scale(
                                missile,
                                box,
                                distance_m,
                                spatial_radius_m,
                                axis_weight,
                                false);
                            const double exposure_scale = hitbox_projected_exposure_scale(local_imp, box);
                            const double orientation_weight = warhead_orientation_pattern_weight(
                                missile.warhead_profile,
                                local_imp,
                                box,
                                warhead_orientation_axis_body);
                            const WarheadSpatialSample spatial_sample =
                                sample_warhead_spatial_effect(
                                    missile,
                                    box,
                                    distance_m,
                                    spatial_radius_m,
                                    axis_weight,
                                    orientation_weight,
                                    exposure_scale,
                                    false);
                            const double sampling_scale = std::clamp(
                                0.55 +
                                    0.35 * std::clamp(spatial_sample.hit_estimate, 0.0, 3.0) / 3.0 +
                                    0.10 * spatial_sample.energy_scale,
                                0.35,
                                1.20);
                            candidates.push_back(SpatialProjectionCandidate{
                                .box = &box,
                                .distance_m = distance_m,
                                .effect_scale = std::clamp(
                                    projected_spatial_effect_scale(
                                        distance_m,
                                        spatial_radius_m,
                                        warhead_projection) *
                                        axis_weight *
                                        orientation_weight *
                                        armor_scale *
                                        exposure_scale *
                                        sampling_scale,
                                    warhead_projection.min_effect_scale,
                                    warhead_projection.max_effect_scale),
                                .axis_weight = axis_weight,
                                .orientation_weight = orientation_weight,
                                .armor_scale = armor_scale,
                                .exposure_scale = exposure_scale,
                                .spatial_sample_count = spatial_sample.sample_count,
                                .spatial_hit_estimate = spatial_sample.hit_estimate,
                                .spatial_hit_fraction = spatial_sample.hit_fraction,
                                .spatial_energy_scale = spatial_sample.energy_scale,
                                .spatial_pattern_scale = spatial_sample.pattern_scale,
                                .surface_incidence_cos = hitbox_surface_incidence_cos(
                                    local_imp,
                                    box,
                                    missile_axis_body),
                                .mechanism_load = with_surface_incidence(
                                    estimate_warhead_mechanism_load(
                                        missile,
                                        box,
                                        distance_m,
                                        spatial_radius_m,
                                        axis_weight,
                                        orientation_weight,
                                        exposure_scale,
                                        false,
                                        closure_mps,
                                        spatial_sample),
                                    hitbox_surface_incidence_cos(
                                        local_imp,
                                        box,
                                        missile_axis_body)),
                            });
                        }
                    }
                    if (!broad_spatial_projection && !box.components.empty()) {
                        for (const auto& component : box.components) {
                            const double distance_m = component_surface_distance(local_imp, component);
                            if (distance_m > spatial_radius_m) {
                                continue;
                            }
                            const Hitbox component_box = component_as_hitbox(component, box);
                            const double axis_weight = warhead_axis_projection_weight(
                                missile.warhead_profile,
                                local_imp,
                                component_box,
                                missile_axis_body);
                            const double armor_scale = warhead_mechanism_armor_scale(
                                missile,
                                component_box,
                                distance_m,
                                spatial_radius_m,
                                axis_weight,
                                false);
                            const double exposure_scale =
                                component_projected_exposure_scale(local_imp, component);
                            const double orientation_weight = warhead_orientation_pattern_weight(
                                missile.warhead_profile,
                                local_imp,
                                component_box,
                                warhead_orientation_axis_body);
                            const WarheadSpatialSample spatial_sample =
                                sample_warhead_spatial_effect(
                                    missile,
                                    component_box,
                                    distance_m,
                                    spatial_radius_m,
                                    axis_weight,
                                    orientation_weight,
                                    exposure_scale,
                                    false);
                            const double sampling_scale = std::clamp(
                                0.55 +
                                    0.35 * std::clamp(spatial_sample.hit_estimate, 0.0, 3.0) / 3.0 +
                                    0.10 * spatial_sample.energy_scale,
                                0.35,
                                1.20);
                            candidates.push_back(SpatialProjectionCandidate{
                                .box = &box,
                                .component = &component,
                                .distance_m = distance_m,
                                .effect_scale = std::clamp(
                                    projected_spatial_effect_scale(
                                        distance_m,
                                        spatial_radius_m,
                                        warhead_projection) *
                                        axis_weight *
                                        orientation_weight *
                                        armor_scale *
                                        exposure_scale *
                                        sampling_scale,
                                    warhead_projection.min_effect_scale,
                                    warhead_projection.max_effect_scale),
                                .axis_weight = axis_weight,
                                .orientation_weight = orientation_weight,
                                .armor_scale = armor_scale,
                                .exposure_scale = exposure_scale,
                                .spatial_sample_count = spatial_sample.sample_count,
                                .spatial_hit_estimate = spatial_sample.hit_estimate,
                                .spatial_hit_fraction = spatial_sample.hit_fraction,
                                .spatial_energy_scale = spatial_sample.energy_scale,
                                .spatial_pattern_scale = spatial_sample.pattern_scale,
                                .surface_incidence_cos = hitbox_surface_incidence_cos(
                                    local_imp,
                                    component_box,
                                    missile_axis_body),
                                .mechanism_load = with_surface_incidence(
                                    estimate_warhead_mechanism_load(
                                        missile,
                                        component_box,
                                        distance_m,
                                        spatial_radius_m,
                                        axis_weight,
                                        orientation_weight,
                                        exposure_scale,
                                        false,
                                        closure_mps,
                                        spatial_sample),
                                    hitbox_surface_incidence_cos(
                                        local_imp,
                                        component_box,
                                        missile_axis_body)),
                            });
                        }
                    } else if (!broad_spatial_projection) {
                        const double distance_m = hitbox_surface_distance(local_imp, box);
                        if (distance_m <= spatial_radius_m) {
                            const double axis_weight = warhead_axis_projection_weight(
                                missile.warhead_profile,
                                local_imp,
                                box,
                                missile_axis_body);
                            const double armor_scale = warhead_mechanism_armor_scale(
                                missile,
                                box,
                                distance_m,
                                spatial_radius_m,
                                axis_weight,
                                false);
                            const double exposure_scale = hitbox_projected_exposure_scale(local_imp, box);
                            const double orientation_weight = warhead_orientation_pattern_weight(
                                missile.warhead_profile,
                                local_imp,
                                box,
                                warhead_orientation_axis_body);
                            const WarheadSpatialSample spatial_sample =
                                sample_warhead_spatial_effect(
                                    missile,
                                    box,
                                    distance_m,
                                    spatial_radius_m,
                                    axis_weight,
                                    orientation_weight,
                                    exposure_scale,
                                    false);
                            const double sampling_scale = std::clamp(
                                0.55 +
                                    0.35 * std::clamp(spatial_sample.hit_estimate, 0.0, 3.0) / 3.0 +
                                    0.10 * spatial_sample.energy_scale,
                                0.35,
                                1.20);
                            candidates.push_back(SpatialProjectionCandidate{
                                .box = &box,
                                .distance_m = distance_m,
                                .effect_scale = std::clamp(
                                    projected_spatial_effect_scale(
                                        distance_m,
                                        spatial_radius_m,
                                        warhead_projection) *
                                        axis_weight *
                                        orientation_weight *
                                        armor_scale *
                                        exposure_scale *
                                        sampling_scale,
                                    warhead_projection.min_effect_scale,
                                    warhead_projection.max_effect_scale),
                                .axis_weight = axis_weight,
                                .orientation_weight = orientation_weight,
                                .armor_scale = armor_scale,
                                .exposure_scale = exposure_scale,
                                .spatial_sample_count = spatial_sample.sample_count,
                                .spatial_hit_estimate = spatial_sample.hit_estimate,
                                .spatial_hit_fraction = spatial_sample.hit_fraction,
                                .spatial_energy_scale = spatial_sample.energy_scale,
                                .spatial_pattern_scale = spatial_sample.pattern_scale,
                                .surface_incidence_cos = hitbox_surface_incidence_cos(
                                    local_imp,
                                    box,
                                    missile_axis_body),
                                .mechanism_load = with_surface_incidence(
                                    estimate_warhead_mechanism_load(
                                        missile,
                                        box,
                                        distance_m,
                                        spatial_radius_m,
                                        axis_weight,
                                        orientation_weight,
                                        exposure_scale,
                                        false,
                                        closure_mps,
                                        spatial_sample),
                                    hitbox_surface_incidence_cos(
                                        local_imp,
                                        box,
                                        missile_axis_body)),
                            });
                        }
                    }
                }

                std::sort(
                    candidates.begin(),
                    candidates.end(),
                    [](const SpatialProjectionCandidate& lhs, const SpatialProjectionCandidate& rhs) {
                        if (lhs.distance_m == rhs.distance_m) {
                            return lhs.effect_scale > rhs.effect_scale;
                        }
                        return lhs.distance_m < rhs.distance_m;
                    });

                const std::size_t projected_count =
                    std::min(candidates.size(), warhead_projection.max_projected_hitboxes);
                for (std::size_t candidate_index = 0; candidate_index < projected_count; ++candidate_index) {
                    const SpatialProjectionCandidate& candidate = candidates[candidate_index];
                    const Hitbox* projected_box = candidate.box;
                    if (!projected_box) {
                        continue;
                    }
                    const DamageComponent* projected_component = candidate.component;
                    spatial_effect_scale = std::max(spatial_effect_scale, candidate.effect_scale);
                    sampled_mechanism_scale =
                        std::max(sampled_mechanism_scale, candidate.armor_scale * candidate.exposure_scale);
                    sampled_armor_scale = std::min(sampled_armor_scale, candidate.armor_scale);
                    sampled_exposure_scale = std::min(sampled_exposure_scale, candidate.exposure_scale);
                    record_warhead_spatial_sample(WarheadSpatialSample{
                        .sample_count = candidate.spatial_sample_count,
                        .hit_estimate = candidate.spatial_hit_estimate,
                        .hit_fraction = candidate.spatial_hit_fraction,
                        .energy_scale = candidate.spatial_energy_scale,
                        .pattern_scale = candidate.spatial_pattern_scale,
                        .orientation_pattern_scale = candidate.orientation_weight,
                    });
                    record_mechanism_load(candidate.mechanism_load);
                    ++projected_hitbox_count;
                    structure_hit = true;
                    spdlog::info(
                        "PROXIMITY FIELD >>> Box {}{} NEAR HIT at {:.2f} m, quality {:.2f}, armor {:.2f}, exposure {:.2f}",
                        projected_box->id,
                        projected_component ? " component" : "",
                        candidate.distance_m,
                        candidate.effect_scale,
                        candidate.armor_scale,
                        candidate.exposure_scale);

                    const double projected_system_severity =
                        std::clamp(system_severity * candidate.effect_scale, 0.02, 0.95);
                    if (projected_component) {
                        const double component_scale =
                            component_mechanism_threshold_scale(
                                missile.warhead_profile,
                                projected_component->system) *
                            std::clamp(projected_component->threshold_scale, 0.40, 1.80) *
                            component_authored_mechanism_threshold_scale(
                                missile.warhead_profile,
                                *projected_component);
                        sampled_component_threshold_scale =
                            std::max(sampled_component_threshold_scale, component_scale);
                        ComponentMechanismLoadRow* component_row = record_component_hit(
                            *projected_component,
                            candidate.effect_scale,
                            component_scale,
                            false,
                            candidate.distance_m,
                            candidate.mechanism_load);
                        apply_system_effect(
                            projected_component->system,
                            projected_system_severity,
	                            candidate.effect_scale,
	                            component_scale,
	                            false,
	                            candidate.mechanism_load,
	                            projected_component->critical,
	                            projected_component->redundancy_group,
	                            projected_component,
	                            component_row);
                        spdlog::info(
                            "   - component {}:{} Status: {:.2f}",
                            projected_component->name.empty()
                                ? projected_component->system
                                : projected_component->name,
                            projected_component->system,
                            sys_health->systems[projected_component->system]);
                    } else {
                        for (const auto& system : projected_box->protected_systems) {
                            if (!processed_air_systems.insert(system).second) {
                                continue;
                            }
                            const double component_scale =
                                component_mechanism_threshold_scale(missile.warhead_profile, system);
                            sampled_component_threshold_scale =
                                std::max(sampled_component_threshold_scale, component_scale);
                            apply_system_effect(
                                system,
                                projected_system_severity,
	                                candidate.effect_scale,
	                                component_scale,
	                                false,
	                                candidate.mechanism_load);
                            spdlog::info("   - {} Status: {:.2f}", system, sys_health->systems[system]);
                        }
                    }
                }
            }

            if (platform_damage && structured_air_target && structure_hit) {
                const bool direct_structure_hit = direct_hitbox_intersection;
                WarheadMechanismLoadEvidence vulnerability_effect_mechanism_load =
                    component_primary_mechanism_load;
                if (vulnerability_effect_mechanism_load.fragment_energy_j <= 0.0 &&
                    vulnerability_effect_mechanism_load.fragment_areal_density_per_m2 <= 0.0 &&
                    vulnerability_effect_mechanism_load.penetration_margin <= 0.0 &&
                    vulnerability_effect_mechanism_load.blast_overpressure_kpa <= 0.0 &&
                    vulnerability_effect_mechanism_load.blast_impulse_kpa_ms <= 0.0 &&
                    vulnerability_effect_mechanism_load.blast_scaled_distance_m_kg13 <= 0.0 &&
                    vulnerability_effect_mechanism_load.rod_cut_margin <= 0.0 &&
                    vulnerability_effect_mechanism_load.surface_incidence_cos <= 0.0) {
                    vulnerability_effect_mechanism_load.fragment_energy_j =
                        sampled_mechanism_fragment_energy_j;
                    vulnerability_effect_mechanism_load.fragment_areal_density_per_m2 =
                        sampled_mechanism_fragment_areal_density_per_m2;
                    vulnerability_effect_mechanism_load.penetration_margin =
                        sampled_mechanism_penetration_margin;
                    vulnerability_effect_mechanism_load.blast_overpressure_kpa =
                        sampled_mechanism_blast_overpressure_kpa;
                    vulnerability_effect_mechanism_load.blast_impulse_kpa_ms =
                        sampled_mechanism_blast_impulse_kpa_ms;
                    vulnerability_effect_mechanism_load.blast_scaled_distance_m_kg13 =
                        sampled_mechanism_blast_scaled_distance_m_kg13;
                    vulnerability_effect_mechanism_load.rod_cut_margin =
                        sampled_mechanism_rod_cut_margin;
                    vulnerability_effect_mechanism_load.surface_incidence_cos =
                        sampled_mechanism_surface_incidence_cos;
                }
                const VulnerabilityAdjustment vulnerability_adjustment =
                    make_vulnerability_adjustment(
                        missile.warhead_profile,
                        aircraft_vulnerability,
                        local_imp,
                        closure_mps,
                        spatial_effect_scale,
                        direct_structure_hit,
                        &vulnerability_effect_mechanism_load);
                sampled_vulnerability_adjustment = vulnerability_adjustment;
                const double resolved_severity =
                    std::clamp(
                        severity *
                            std::max(0.05, spatial_effect_scale) *
                            sampled_mechanism_scale *
                            vulnerability_adjustment.scale,
                        0.02,
                        0.65);
                if (aircraft_vulnerability) {
                    spdlog::info(
                        "AIR VULNERABILITY >>> provenance={} synthetic={} calibrated={} pk_authority={} deterministic_fuze_authority={} dataset={} status={} aspect={} closure={:.1f} scale={:.2f}",
                        aircraft_vulnerability->provenance,
                        aircraft_vulnerability->synthetic,
                        vulnerability_adjustment.calibrated_evidence,
                        vulnerability_adjustment.pk_authority,
                        vulnerability_adjustment.deterministic_fuze_authority,
                        vulnerability_adjustment.evidence_dataset_ref,
                        vulnerability_adjustment.calibration_status,
                        vulnerability_adjustment.aspect_bucket,
                        vulnerability_adjustment.closure_mps,
                        vulnerability_adjustment.scale);
                }
                const double sensor_scale = air_sensor_hit
                    ? std::max(0.05, air_sensor_spatial_scale)
                    : 0.0;
                const double propulsion_or_fuel_scale = air_propulsion_or_fuel_hit
                    ? std::max(0.05, air_propulsion_or_fuel_spatial_scale)
                    : 0.0;
                const double propulsion_scale = air_propulsion_hit
                    ? std::max(0.05, air_propulsion_spatial_scale)
                    : 0.0;
                const double fuel_scale = air_fuel_hit
                    ? std::max(0.05, air_fuel_spatial_scale)
                    : 0.0;
                const double control_scale = air_control_hit
                    ? std::max(0.05, air_control_spatial_scale)
                    : 0.0;
                const double crew_scale = air_crew_hit
                    ? std::max(0.05, air_crew_spatial_scale)
                    : 0.0;
                const double pilot_scale = air_pilot_hit
                    ? std::max(0.05, air_pilot_spatial_scale)
                    : 0.0;
                const double mission_crew_scale = air_mission_crew_hit
                    ? std::max(0.05, air_mission_crew_spatial_scale)
                    : 0.0;
                const double command_navigation_scale = air_command_navigation_hit
                    ? std::max(0.05, air_command_navigation_spatial_scale)
                    : 0.0;
                const double mission_or_combat_scale = air_mission_or_combat_hit
                    ? std::max(0.05, air_mission_or_combat_spatial_scale)
                    : 0.0;
                const double structure_scale = std::max(0.05, air_structure_spatial_scale);
                platform_damage->survivability_margin -=
                    localized_effect_delta(
                        0.08,
                        0.08,
                        resolved_severity,
                        warhead_effects.structure_scale,
                        std::max(structure_scale, spatial_effect_scale));
                if (air_sensor_hit) {
                    platform_damage->sensor_capability -=
                        localized_effect_delta(
                            0.35,
                            0.20,
                            resolved_severity,
                            warhead_effects.sensor_scale,
                            sensor_scale);
                    platform_damage->fire_severity +=
                        localized_effect_delta(
                            0.05,
                            0.05,
                            resolved_severity,
                            warhead_effects.fire_scale,
                            sensor_scale);
                }
                if (aircraft_damage) {
                    aircraft_damage->structural_integrity -=
                        localized_effect_delta(
                            0.05,
                            0.07,
                            resolved_severity,
                            warhead_effects.structure_scale,
                            std::max(structure_scale, spatial_effect_scale));
                    if (air_sensor_hit) {
                        aircraft_damage->avionics_integrity -=
                            localized_effect_delta(
                                0.25,
                                0.20,
                                resolved_severity,
                                warhead_effects.sensor_scale,
                                sensor_scale);
                        aircraft_damage->fire_severity +=
                            localized_effect_delta(
                                0.03,
                                0.04,
                                resolved_severity,
                                warhead_effects.fire_scale,
                                sensor_scale);
                    }
                    if (air_propulsion_hit) {
                        aircraft_damage->propulsion_integrity -=
                            localized_effect_delta(
                                0.22,
                                0.22,
                                resolved_severity,
                                warhead_effects.propulsion_scale,
                                propulsion_scale);
                    }
                    if (air_fuel_hit) {
                        aircraft_damage->fuel_system_integrity -=
                            localized_effect_delta(
                                0.25,
                                0.20,
                                resolved_severity,
                                warhead_effects.propulsion_scale,
                                fuel_scale);
                        aircraft_damage->fuel_leak_severity +=
                            localized_effect_delta(
                                0.18,
                                0.25,
                                resolved_severity,
                                warhead_effects.breach_scale,
                                fuel_scale);
                        aircraft_damage->fire_severity +=
                            localized_effect_delta(
                                0.08,
                                0.10,
                                resolved_severity,
                                warhead_effects.fire_scale,
                                fuel_scale);
                    }
                    if (air_control_hit) {
                        aircraft_damage->flight_control_integrity -=
                            localized_effect_delta(
                                0.28,
                                0.24,
                                resolved_severity,
                                warhead_effects.control_scale,
                                control_scale);
                        aircraft_damage->hydraulic_integrity -=
                            localized_effect_delta(
                                0.20,
                                0.20,
                                resolved_severity,
                                warhead_effects.control_scale,
                                control_scale);
                        aircraft_damage->structural_integrity -=
                            localized_effect_delta(
                                0.05,
                                0.06,
                                resolved_severity,
                                warhead_effects.control_scale,
                                control_scale);
                    }
                    if (air_pilot_hit) {
                        apply_aircraft_crew_consequence(
                            *aircraft_damage,
                            CrewConsequenceKind::Pilot,
                            localized_effect_delta(
                                0.42,
                                0.25,
                                resolved_severity,
                                warhead_effects.crew_scale,
                                pilot_scale));
                    }
                    if (air_mission_crew_hit) {
                        apply_aircraft_crew_consequence(
                            *aircraft_damage,
                            CrewConsequenceKind::MissionCrew,
                            localized_effect_delta(
                                0.32,
                                0.22,
                                resolved_severity,
                                warhead_effects.crew_scale,
                                mission_crew_scale));
                    }
                    if (air_command_navigation_hit) {
                        apply_aircraft_crew_consequence(
                            *aircraft_damage,
                            CrewConsequenceKind::CommandNavigation,
                            localized_effect_delta(
                                0.34,
                                0.22,
                                resolved_severity,
                                warhead_effects.mission_scale,
                                command_navigation_scale));
                    }
                    if (air_crew_hit &&
                        !(air_pilot_hit || air_mission_crew_hit || air_command_navigation_hit)) {
                        aircraft_damage->crew_effectiveness -=
                            localized_effect_delta(
                                0.42,
                                0.25,
                                resolved_severity,
                                warhead_effects.crew_scale,
                                crew_scale);
                    }
                    if (air_mission_or_combat_hit) {
                        aircraft_damage->avionics_integrity -=
                            localized_effect_delta(
                                0.18,
                                0.20,
                                resolved_severity,
                                warhead_effects.mission_scale,
                                mission_or_combat_scale);
                        aircraft_damage->fire_severity +=
                            localized_effect_delta(
                                0.04,
                                0.04,
                                resolved_severity,
                                warhead_effects.fire_scale,
                                mission_or_combat_scale);
                    }

                    if (air_structure_spatial_scale > 0.0) {
                        aircraft_damage->structural_integrity -=
                            localized_effect_delta(
                                0.06,
                                0.07,
                                resolved_severity,
                                warhead_effects.structure_scale,
                                structure_scale);
                    }
                    clamp_aircraft_damage_state(*aircraft_damage);
                    apply_aircraft_damage_state_to_platform(*aircraft_damage, *platform_damage);
                }
                if (air_propulsion_or_fuel_hit) {
                    platform_damage->fire_severity +=
                        localized_effect_delta(
                            0.08,
                            0.08,
                            resolved_severity,
                            warhead_effects.fire_scale,
                            propulsion_or_fuel_scale);
                    platform_damage->ongoing_hull_breach +=
                        localized_effect_delta(
                            0.03,
                            0.04,
                            resolved_severity,
                            warhead_effects.breach_scale,
                            propulsion_or_fuel_scale);
                }
                if (air_control_hit) {
                    platform_damage->survivability_margin -=
                        localized_effect_delta(
                            0.06,
                            0.08,
                            resolved_severity,
                            warhead_effects.control_scale,
                            control_scale);
                }
                if (air_crew_hit || air_pilot_hit || air_mission_crew_hit ||
                    air_command_navigation_hit) {
                    platform_damage->survivability_margin -=
                        localized_effect_delta(
                            0.10,
                            0.10,
                            resolved_severity,
                            warhead_effects.crew_scale,
                            std::max({
                                crew_scale,
                                pilot_scale,
                                mission_crew_scale,
                                command_navigation_scale}));
                }
                if (air_mission_or_combat_hit) {
                    platform_damage->fire_severity +=
                        localized_effect_delta(
                            0.04,
                            0.04,
                            resolved_severity,
                            warhead_effects.fire_scale,
                            mission_or_combat_scale);
                }
                platform_damage->fire_severity = std::clamp(platform_damage->fire_severity, 0.0, 1.0);
                platform_damage->flooding_severity = std::clamp(platform_damage->flooding_severity, 0.0, 1.0);
                platform_damage->ongoing_hull_breach = std::clamp(platform_damage->ongoing_hull_breach, 0.0, 1.0);
            }

            if (platform_damage) {
                clamp_platform_damage_state(platform_damage);
                if (hp) {
                    hp->mission_kill = platform_damage->mission_kill;
                    hp->mobility_kill = platform_damage->mobility_kill;
                    hp->sensor_kill = platform_damage->sensor_kill;
                    if (platform_damage->loss_state == PlatformLossState::Lost) {
                        hp->current_hp = 0.0;
                    }
                }
                if (platform_damage->loss_state == PlatformLossState::Lost) {
                    target_entity.destruct();
                    result.direct_hitbox_intersection = direct_hitbox_intersection;
                    result.projected_hitbox_count = projected_hitbox_count;
                    result.spatial_effect_scale = spatial_effect_scale;
                    result.mechanism_armor_scale = sampled_armor_scale;
                    result.mechanism_exposure_scale = sampled_exposure_scale;
                    result.mechanism_effect_scale = sampled_mechanism_scale;
                    result.mechanism_fragment_energy_j = sampled_mechanism_fragment_energy_j;
                    result.mechanism_fragment_areal_density_per_m2 =
                        sampled_mechanism_fragment_areal_density_per_m2;
                    result.mechanism_penetration_margin = sampled_mechanism_penetration_margin;
                    result.mechanism_blast_overpressure_kpa =
                        sampled_mechanism_blast_overpressure_kpa;
                    result.mechanism_blast_impulse_kpa_ms =
                        sampled_mechanism_blast_impulse_kpa_ms;
                    result.mechanism_blast_scaled_distance_m_kg13 =
                        sampled_mechanism_blast_scaled_distance_m_kg13;
                    result.mechanism_rod_cut_margin = sampled_mechanism_rod_cut_margin;
                    result.mechanism_surface_incidence_cos =
                        sampled_mechanism_surface_incidence_cos;
                    result.warhead_spatial_sample_count = sampled_warhead_spatial_sample_count;
                    result.warhead_spatial_hit_estimate = sampled_warhead_spatial_hit_estimate;
                    result.warhead_spatial_hit_fraction = sampled_warhead_spatial_hit_fraction;
                    result.warhead_spatial_energy_scale = sampled_warhead_spatial_energy_scale;
                    result.warhead_spatial_pattern_scale =
                        sampled_warhead_spatial_sample_count > 0
                            ? sampled_warhead_spatial_pattern_scale
                            : 1.0;
                    result.warhead_orientation_axis_forward = warhead_orientation_axis_body.x;
                    result.warhead_orientation_axis_right = warhead_orientation_axis_body.y;
                    result.warhead_orientation_axis_up = warhead_orientation_axis_body.z;
                    result.warhead_orientation_pattern_scale =
                        sampled_warhead_spatial_sample_count > 0
                            ? sampled_warhead_orientation_pattern_scale
                            : 1.0;
                    result.component_threshold_scale = sampled_component_threshold_scale;
                    result.component_failure_probability = sampled_component_failure_probability;
                    result.component_failure_probability_source =
                        sampled_component_failure_probability_source;
                    result.component_failure_probability_calibrated =
                        sampled_component_failure_probability_calibrated;
                    result.component_failure_probability_evidence_dataset_ref =
                        sampled_component_failure_probability_evidence_dataset_ref;
                    result.component_failure_probability_evidence_row_id =
                        sampled_component_failure_probability_evidence_row_id;
                    result.component_failure_probability_evidence_source_ref =
                        sampled_component_failure_probability_evidence_source_ref;
                    result.component_failure_probability_evidence_provenance =
                        sampled_component_failure_probability_evidence_provenance;
                    result.component_failure_sample = sampled_component_failure_sample;
                    result.component_failure_count = component_failure_count;
                    result.component_hit_count = component_hit_count;
                    result.component_mechanism_load_rows = component_mechanism_load_rows;
                    result.component_primary_name = component_primary_name;
                    result.component_primary_system = component_primary_system;
                    result.component_primary_redundancy_group = component_primary_redundancy_group;
                    result.component_primary_critical = component_primary_critical;
                    result.component_primary_redundancy_group_id = component_primary_redundancy_group_id;
                    result.component_primary_integrity = component_primary_integrity;
                    result.component_primary_mechanism_fragment_energy_j =
                        component_primary_mechanism_load.fragment_energy_j;
                    result.component_primary_mechanism_fragment_areal_density_per_m2 =
                        component_primary_mechanism_load.fragment_areal_density_per_m2;
                    result.component_primary_mechanism_penetration_margin =
                        component_primary_mechanism_load.penetration_margin;
                    result.component_primary_mechanism_blast_overpressure_kpa =
                        component_primary_mechanism_load.blast_overpressure_kpa;
                    result.component_primary_mechanism_blast_impulse_kpa_ms =
                        component_primary_mechanism_load.blast_impulse_kpa_ms;
                    result.component_primary_mechanism_blast_scaled_distance_m_kg13 =
                        component_primary_mechanism_load.blast_scaled_distance_m_kg13;
                    result.component_primary_mechanism_rod_cut_margin =
                        component_primary_mechanism_load.rod_cut_margin;
                    result.component_primary_mechanism_surface_incidence_cos =
                        component_primary_mechanism_load.surface_incidence_cos;
                    result.component_redundancy_group_availability =
                        component_redundancy_group_availability;
                    result.component_redundancy_group_member_count =
                        component_redundancy_group_member_count;
                    result.component_redundancy_group_failed_count =
                        component_redundancy_group_failed_count;
                    result.vulnerability_profile_present =
                        sampled_vulnerability_adjustment.profile_present;
                    result.vulnerability_profile_synthetic =
                        sampled_vulnerability_adjustment.synthetic;
                    result.vulnerability_calibrated_evidence =
                        sampled_vulnerability_adjustment.calibrated_evidence;
                    result.vulnerability_pk_authority =
                        sampled_vulnerability_adjustment.pk_authority;
                    result.vulnerability_deterministic_fuze_authority =
                        sampled_vulnerability_adjustment.deterministic_fuze_authority;
                    result.vulnerability_evidence_dataset_valid =
                        sampled_vulnerability_adjustment.evidence_dataset_valid;
                    result.vulnerability_evidence_dataset_ref =
                        sampled_vulnerability_adjustment.evidence_dataset_ref;
                    result.vulnerability_calibration_status =
                        sampled_vulnerability_adjustment.calibration_status;
                    result.vulnerability_provenance =
                        sampled_vulnerability_adjustment.provenance;
                    result.vulnerability_evidence_schema_version =
                        sampled_vulnerability_adjustment.evidence_schema_version;
                    result.vulnerability_evidence_source_kind =
                        sampled_vulnerability_adjustment.evidence_source_kind;
                    result.vulnerability_evidence_source_ref =
                        sampled_vulnerability_adjustment.evidence_source_ref;
                    result.vulnerability_evidence_validation_artifact_ref =
                        sampled_vulnerability_adjustment.evidence_validation_artifact_ref;
                    result.vulnerability_evidence_validation_manifest_schema_version =
                        sampled_vulnerability_adjustment.evidence_validation_manifest_schema_version;
                    result.vulnerability_evidence_validation_status =
                        sampled_vulnerability_adjustment.evidence_validation_status;
                    result.vulnerability_evidence_validation_artifact_sha256 =
                        sampled_vulnerability_adjustment.evidence_validation_artifact_sha256;
                    result.vulnerability_evidence_validated_surrogate_model_ref =
                        sampled_vulnerability_adjustment.evidence_validated_surrogate_model_ref;
                    result.vulnerability_evidence_validation_benchmark_ref =
                        sampled_vulnerability_adjustment.evidence_validation_benchmark_ref;
                    result.vulnerability_evidence_validation_metrics_ref =
                        sampled_vulnerability_adjustment.evidence_validation_metrics_ref;
                    result.vulnerability_evidence_validation_acceptance_criteria_ref =
                        sampled_vulnerability_adjustment.evidence_validation_acceptance_criteria_ref;
                    result.vulnerability_aspect_bucket =
                        sampled_vulnerability_adjustment.aspect_bucket;
                    result.vulnerability_family_scale =
                        sampled_vulnerability_adjustment.family_scale;
                    result.vulnerability_aspect_scale =
                        sampled_vulnerability_adjustment.aspect_scale;
                    result.vulnerability_closure_mps =
                        sampled_vulnerability_adjustment.closure_mps;
                    result.vulnerability_closure_scale =
                        sampled_vulnerability_adjustment.closure_scale;
                    result.vulnerability_miss_distance_scale =
                        sampled_vulnerability_adjustment.miss_distance_scale;
                    result.vulnerability_effect_scale =
                        sampled_vulnerability_adjustment.scale;
                    result.vulnerability_effect_scale_source =
                        sampled_vulnerability_adjustment.effect_scale_source;
                    result.vulnerability_effect_scale_evidence_row_id =
                        sampled_vulnerability_adjustment.effect_scale_evidence_row_id;
                    result.vulnerability_effect_scale_evidence_source_ref =
                        sampled_vulnerability_adjustment.effect_scale_evidence_source_ref;
                    result.vulnerability_effect_scale_evidence_provenance =
                        sampled_vulnerability_adjustment.effect_scale_evidence_provenance;
                    return result;
                }
            }
            
            if (!structure_hit) {
                spdlog::info("PROXIMITY HIT BUT NO STRUCTURAL IMPACT (Near Miss or Gap)");
            }
            result.direct_hitbox_intersection = direct_hitbox_intersection;
            result.projected_hitbox_count = projected_hitbox_count;
            result.spatial_effect_scale = spatial_effect_scale;
            result.mechanism_armor_scale = sampled_armor_scale;
            result.mechanism_exposure_scale = sampled_exposure_scale;
            result.mechanism_effect_scale = sampled_mechanism_scale;
            result.mechanism_fragment_energy_j = sampled_mechanism_fragment_energy_j;
            result.mechanism_fragment_areal_density_per_m2 =
                sampled_mechanism_fragment_areal_density_per_m2;
            result.mechanism_penetration_margin = sampled_mechanism_penetration_margin;
            result.mechanism_blast_overpressure_kpa = sampled_mechanism_blast_overpressure_kpa;
            result.mechanism_blast_impulse_kpa_ms = sampled_mechanism_blast_impulse_kpa_ms;
            result.mechanism_blast_scaled_distance_m_kg13 =
                sampled_mechanism_blast_scaled_distance_m_kg13;
            result.mechanism_rod_cut_margin = sampled_mechanism_rod_cut_margin;
            result.mechanism_surface_incidence_cos =
                sampled_mechanism_surface_incidence_cos;
            result.warhead_spatial_sample_count = sampled_warhead_spatial_sample_count;
            result.warhead_spatial_hit_estimate = sampled_warhead_spatial_hit_estimate;
            result.warhead_spatial_hit_fraction = sampled_warhead_spatial_hit_fraction;
            result.warhead_spatial_energy_scale = sampled_warhead_spatial_energy_scale;
            result.warhead_spatial_pattern_scale =
                sampled_warhead_spatial_sample_count > 0
                    ? sampled_warhead_spatial_pattern_scale
                    : 1.0;
            result.warhead_orientation_axis_forward = warhead_orientation_axis_body.x;
            result.warhead_orientation_axis_right = warhead_orientation_axis_body.y;
            result.warhead_orientation_axis_up = warhead_orientation_axis_body.z;
            result.warhead_orientation_pattern_scale =
                sampled_warhead_spatial_sample_count > 0
                    ? sampled_warhead_orientation_pattern_scale
                    : 1.0;
            result.component_threshold_scale = sampled_component_threshold_scale;
            result.component_failure_probability = sampled_component_failure_probability;
            result.component_failure_probability_source =
                sampled_component_failure_probability_source;
            result.component_failure_probability_calibrated =
                sampled_component_failure_probability_calibrated;
            result.component_failure_probability_evidence_dataset_ref =
                sampled_component_failure_probability_evidence_dataset_ref;
            result.component_failure_probability_evidence_row_id =
                sampled_component_failure_probability_evidence_row_id;
            result.component_failure_probability_evidence_source_ref =
                sampled_component_failure_probability_evidence_source_ref;
            result.component_failure_probability_evidence_provenance =
                sampled_component_failure_probability_evidence_provenance;
            result.component_failure_sample = sampled_component_failure_sample;
            result.component_failure_count = component_failure_count;
            result.component_hit_count = component_hit_count;
            result.component_mechanism_load_rows = component_mechanism_load_rows;
            result.component_primary_name = component_primary_name;
            result.component_primary_system = component_primary_system;
            result.component_primary_redundancy_group = component_primary_redundancy_group;
            result.component_primary_critical = component_primary_critical;
            result.component_primary_redundancy_group_id = component_primary_redundancy_group_id;
            result.component_primary_integrity = component_primary_integrity;
            result.component_primary_mechanism_fragment_energy_j =
                component_primary_mechanism_load.fragment_energy_j;
            result.component_primary_mechanism_fragment_areal_density_per_m2 =
                component_primary_mechanism_load.fragment_areal_density_per_m2;
            result.component_primary_mechanism_penetration_margin =
                component_primary_mechanism_load.penetration_margin;
            result.component_primary_mechanism_blast_overpressure_kpa =
                component_primary_mechanism_load.blast_overpressure_kpa;
            result.component_primary_mechanism_blast_impulse_kpa_ms =
                component_primary_mechanism_load.blast_impulse_kpa_ms;
            result.component_primary_mechanism_blast_scaled_distance_m_kg13 =
                component_primary_mechanism_load.blast_scaled_distance_m_kg13;
            result.component_primary_mechanism_rod_cut_margin =
                component_primary_mechanism_load.rod_cut_margin;
            result.component_primary_mechanism_surface_incidence_cos =
                component_primary_mechanism_load.surface_incidence_cos;
            result.component_redundancy_group_availability =
                component_redundancy_group_availability;
            result.component_redundancy_group_member_count =
                component_redundancy_group_member_count;
            result.component_redundancy_group_failed_count =
                component_redundancy_group_failed_count;
            result.vulnerability_profile_present =
                sampled_vulnerability_adjustment.profile_present;
            result.vulnerability_profile_synthetic =
                sampled_vulnerability_adjustment.synthetic;
            result.vulnerability_calibrated_evidence =
                sampled_vulnerability_adjustment.calibrated_evidence;
            result.vulnerability_pk_authority =
                sampled_vulnerability_adjustment.pk_authority;
            result.vulnerability_deterministic_fuze_authority =
                sampled_vulnerability_adjustment.deterministic_fuze_authority;
            result.vulnerability_evidence_dataset_valid =
                sampled_vulnerability_adjustment.evidence_dataset_valid;
            result.vulnerability_evidence_dataset_ref =
                sampled_vulnerability_adjustment.evidence_dataset_ref;
            result.vulnerability_calibration_status =
                sampled_vulnerability_adjustment.calibration_status;
            result.vulnerability_provenance =
                sampled_vulnerability_adjustment.provenance;
            result.vulnerability_evidence_schema_version =
                sampled_vulnerability_adjustment.evidence_schema_version;
            result.vulnerability_evidence_source_kind =
                sampled_vulnerability_adjustment.evidence_source_kind;
            result.vulnerability_evidence_source_ref =
                sampled_vulnerability_adjustment.evidence_source_ref;
            result.vulnerability_evidence_validation_artifact_ref =
                sampled_vulnerability_adjustment.evidence_validation_artifact_ref;
            result.vulnerability_evidence_validation_manifest_schema_version =
                sampled_vulnerability_adjustment.evidence_validation_manifest_schema_version;
            result.vulnerability_evidence_validation_status =
                sampled_vulnerability_adjustment.evidence_validation_status;
            result.vulnerability_evidence_validation_artifact_sha256 =
                sampled_vulnerability_adjustment.evidence_validation_artifact_sha256;
            result.vulnerability_evidence_validated_surrogate_model_ref =
                sampled_vulnerability_adjustment.evidence_validated_surrogate_model_ref;
            result.vulnerability_evidence_validation_benchmark_ref =
                sampled_vulnerability_adjustment.evidence_validation_benchmark_ref;
            result.vulnerability_evidence_validation_metrics_ref =
                sampled_vulnerability_adjustment.evidence_validation_metrics_ref;
            result.vulnerability_evidence_validation_acceptance_criteria_ref =
                sampled_vulnerability_adjustment.evidence_validation_acceptance_criteria_ref;
            result.vulnerability_aspect_bucket =
                sampled_vulnerability_adjustment.aspect_bucket;
            result.vulnerability_family_scale =
                sampled_vulnerability_adjustment.family_scale;
            result.vulnerability_aspect_scale =
                sampled_vulnerability_adjustment.aspect_scale;
            result.vulnerability_closure_mps =
                sampled_vulnerability_adjustment.closure_mps;
            result.vulnerability_closure_scale =
                sampled_vulnerability_adjustment.closure_scale;
            result.vulnerability_miss_distance_scale =
                sampled_vulnerability_adjustment.miss_distance_scale;
            result.vulnerability_effect_scale =
                sampled_vulnerability_adjustment.scale;
            result.vulnerability_effect_scale_source =
                sampled_vulnerability_adjustment.effect_scale_source;
            result.vulnerability_effect_scale_evidence_row_id =
                sampled_vulnerability_adjustment.effect_scale_evidence_row_id;
            result.vulnerability_effect_scale_evidence_source_ref =
                sampled_vulnerability_adjustment.effect_scale_evidence_source_ref;
            result.vulnerability_effect_scale_evidence_provenance =
                sampled_vulnerability_adjustment.effect_scale_evidence_provenance;
        } 
        // --- 3. Fallback to Randomized Effects (Legacy) ---
        else {
             // ... preserve existing random code if no geometry ...
             // (Copying simplified random logic for fallback)
             double severity = 0.5;
             if (hp && hp->max_hp > 0) severity = missile.damage / hp->max_hp;
             
             // Randomly damage sensor
             double p = std::clamp(0.3 + 0.5 * severity, 0.0, 1.0);
             uint64_t rng_state = missile.rng_state;
             double u = rand_uniform01(rng_state);
             if (u < p) {
                 // if (Sensor* s = target_entity.get_mut<Sensor>()) apply_sensor_damage(*s, severity);
                 // Skip apply_sensor_damage for now as helpers are gone, simple blind
                 if (Sensor* s = target_entity.get_mut<Sensor>()) {
                    s->max_range *= 0.5;
                 }
             }
             if (Missile* m = missile_entity.get_mut<Missile>()) {
                 m->rng_state = rng_state;
             }
        }

        return result;
    }
};

} // namespace

std::unique_ptr<IEffectsModel> make_default_effects_model() {
    return std::make_unique<DefaultEffectsModel>();
}
