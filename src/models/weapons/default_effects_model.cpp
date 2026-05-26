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

// Rotate vector into Body Frame (inverse rotation)
// Simplified sequence: Undo Heading, then Pitch, then Roll
// Note: Coordinate system is ENU. Heading 0=North (Y). 
// This math can be tricky. For MVP reliability, let's treat Heading as rotation around Z.
// Pitch around X, Roll around Y?
// Actually, standard Euler inverse: R_total = R_z(heading) * R_x(pitch) * R_y(roll). Inverse is R_y(-r)*R_x(-p)*R_z(-h).
// But standard aerospace sequence is usually Yaw -> Pitch -> Roll.
// Let's implement a simplified 2D+Height transformation for stability first.
// The most important is Relative Bearing.
Vec3 world_to_body(const Transform& t, double wx, double wy, double wz) {
    // Relative position
    double dx = wx - t.x;
    double dy = wy - t.y;
    double dz = wz - t.z;
    
    // Rotate -Heading (around Z) to align X with North?
    // Wait, Heading definition: 0=North(Y+), 90=East(X+).
    // Math angle (from X+, CCW): math_deg = 90 - heading.
    double math_rad = (90.0 - t.heading) * M_PI / 180.0;
    
    // Rotate by -math_math effectively aligns body X with world X? 
    // No, we want to align World Vector into Body Axis.
    // If Body Heading is 45 (NE), and Point is at (1,1) (NE), Local X should be +dist, Y=0.
    
    // Projection to horizontal plane
    double dist_h = std::sqrt(dx*dx + dy*dy);
    double bearing_rad = std::atan2(dy, dx); // Math angle of vector
    double relative_angle = bearing_rad - math_rad;
    
    double lx = dist_h * std::cos(relative_angle); // Forward axis? No, in math X is East.
    // Let's stick to standard Body Axis: X=Forward, Y=Right, Z=Up.
    // Current Sim: Heading is Nav. 
    // Let's assum "Forward" is unit vector logic.
    
    // Re-verify coordinate system: ENU.
    // Body X (Forward) = (sin(h), cos(h), 0) roughly (ignoring pitch).
    // Body Y (Right) = (cos(h), -sin(h), 0).
    // Let's do a Dot Product projection.
    double head_rad = t.heading * M_PI / 180.0;
    double fwd_x = std::sin(head_rad);
    double fwd_y = std::cos(head_rad);
    double right_x = std::cos(head_rad);
    double right_y = -std::sin(head_rad);
    
    // Project delta vector onto axes
    double local_x = dx * fwd_x + dy * fwd_y; // Dot(delta, fwd)
    double local_y = dx * right_x + dy * right_y; // Dot(delta, right)
    double local_z = dz; // Assuming flat pitch/roll for MVP interception
    
    return {local_x, local_y, local_z};
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

double component_failure_probability(
    double severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit
) {
    const double impulse =
        std::clamp(severity, 0.0, 1.0) *
        std::clamp(mechanism_scale, 0.0, 1.25) *
        std::clamp(component_scale, 0.40, 1.60);
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
            aircraft_damage->crew_effectiveness -= 0.12 + 0.16 * impulse;
            aircraft_damage->flight_control_integrity -= 0.03 + 0.05 * impulse;
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
    double armor_scale = 1.0;
    double exposure_scale = 1.0;
};

struct VulnerabilityAdjustment {
    double scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    std::string aspect_bucket = "unknown";
    double closure_mps = 0.0;
    bool calibrated_evidence = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    std::string calibration_status = "none";
    std::string evidence_dataset_ref;
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
        out.max_projected_hitboxes = 4;
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

std::string classify_local_aspect_bucket(const Vec3& local_imp) {
    if (std::abs(local_imp.x) >= std::abs(local_imp.y)) {
        return local_imp.x >= 0.0 ? "nose" : "tail";
    }
    return "beam";
}

VulnerabilityAdjustment make_vulnerability_adjustment(
    const WarheadProfile& warhead_profile,
    const AircraftVulnerabilityProfile* vulnerability,
    const Vec3& local_imp,
    double closure_mps,
    double spatial_effect_scale,
    bool direct_structure_hit
) {
    VulnerabilityAdjustment out{};
    if (!vulnerability) {
        return out;
    }
    out.calibrated_evidence = aircraft_vulnerability_has_calibrated_evidence(*vulnerability);
    out.pk_authority = aircraft_vulnerability_pk_authority(*vulnerability);
    out.deterministic_fuze_authority =
        aircraft_vulnerability_deterministic_fuze_authority(*vulnerability);
    out.calibration_status = vulnerability->calibration_status;
    out.evidence_dataset_ref = vulnerability->evidence_dataset_ref;

    const std::string family = warhead_effect_family(warhead_profile);
    double family_scale = vulnerability->fragmentation_scale;
    if (family == "blast") {
        family_scale = vulnerability->blast_scale;
    } else if (family == "continuous_rod") {
        family_scale = vulnerability->continuous_rod_scale;
    } else if (family == "hit_to_kill") {
        family_scale = vulnerability->hit_to_kill_scale;
    }

    out.aspect_bucket = classify_local_aspect_bucket(local_imp);
    if (out.aspect_bucket == "nose") {
        out.aspect_scale = vulnerability->nose_aspect_scale;
    } else if (out.aspect_bucket == "tail") {
        out.aspect_scale = vulnerability->tail_aspect_scale;
    } else if (out.aspect_bucket == "beam") {
        out.aspect_scale = vulnerability->beam_aspect_scale;
    }

    out.closure_mps = closure_mps;
    if (closure_mps >= 700.0) {
        out.closure_scale = vulnerability->high_closure_scale;
    } else if (closure_mps > 0.0 && closure_mps <= 250.0) {
        out.closure_scale = vulnerability->low_closure_scale;
    }

    out.miss_distance_scale = direct_structure_hit
        ? vulnerability->direct_hit_scale
        : vulnerability->near_miss_scale;

    const double raw_scale =
        family_scale * out.aspect_scale * out.closure_scale * out.miss_distance_scale;
    const double authority_floor = vulnerability->synthetic ? 0.80 : 0.55;
    const double authority_ceiling = vulnerability->synthetic ? 1.25 : 1.60;
    out.scale = std::clamp(raw_scale, authority_floor, authority_ceiling);

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
        const AircraftVulnerabilityProfile* aircraft_vulnerability =
            target_entity.get<AircraftVulnerabilityProfile>();
        const Transform* t_tgt = target_entity.get<Transform>();
        const Transform* t_msl = missile_entity.get<Transform>();

        if (hitboxes && sys_health && t_tgt && t_msl) {
            // Transform Missile Pos to Target Body Frame
            Vec3 local_imp = world_to_body(*t_tgt, t_msl->x, t_msl->y, t_msl->z);
            const double closure_mps = resolve_closure_mps(missile_entity, target_entity);
            const Vec3 missile_axis_body = missile_velocity_axis_in_target_body(missile_entity, *t_tgt);
            
            // Check Intersections
            bool structure_hit = false;
            bool air_sensor_hit = false;
            bool air_propulsion_or_fuel_hit = false;
            bool air_propulsion_hit = false;
            bool air_fuel_hit = false;
            bool air_control_hit = false;
            bool air_crew_hit = false;
            bool air_mission_or_combat_hit = false;
            bool direct_hitbox_intersection = false;
            std::unordered_set<std::string> processed_air_systems;
            double air_sensor_spatial_scale = 0.0;
            double air_propulsion_or_fuel_spatial_scale = 0.0;
            double air_propulsion_spatial_scale = 0.0;
            double air_fuel_spatial_scale = 0.0;
            double air_control_spatial_scale = 0.0;
            double air_crew_spatial_scale = 0.0;
            double air_mission_or_combat_spatial_scale = 0.0;
            double air_structure_spatial_scale = 0.0;
            double sampled_mechanism_scale = 0.0;
            double sampled_armor_scale = 1.0;
            double sampled_exposure_scale = 1.0;
            double sampled_component_threshold_scale = 1.0;
            double sampled_component_failure_probability = 0.0;
            double sampled_component_failure_sample = 1.0;
            std::uint32_t component_failure_count = 0;
            std::uint64_t component_rng_state = missile.rng_state;
            std::uint32_t projected_hitbox_count = 0;
            const double severity = std::clamp(missile.damage / 180.0, 0.15, 0.65);
            std::uint32_t component_hit_count = 0;
            std::string component_primary_name;
            std::string component_primary_system;
            double component_primary_redundancy_group = 0.0;
            bool component_primary_critical = false;
            double component_primary_effect_scale = -1.0;
            const auto record_component_hit = [&](const DamageComponent& component, double effect_scale) {
                ++component_hit_count;
                if (effect_scale > component_primary_effect_scale) {
                    component_primary_effect_scale = effect_scale;
                    component_primary_name = component.name.empty() ? component.system : component.name;
                    component_primary_system = component.system;
                    component_primary_redundancy_group = component.redundancy_group;
                    component_primary_critical = component.critical;
                }
            };
            const auto sample_component_failure = [&](
                const std::string& system,
                double base_severity,
                double mechanism_scale,
                double component_scale,
                bool direct_hit,
                bool component_critical,
                double redundancy_group
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
                const double failure_probability = component_failure_probability(
                    base_severity,
                    mechanism_scale,
                    resolved_component_scale,
                    direct_hit);
                const double failure_sample = rand_uniform01(component_rng_state);
                sampled_component_failure_probability =
                    std::max(sampled_component_failure_probability, failure_probability);
                sampled_component_failure_sample =
                    std::min(sampled_component_failure_sample, failure_sample);
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
            const auto note_air_system_hit = [&](const std::string& system, double system_spatial_scale) {
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
                bool component_critical = true,
                double redundancy_group = 0.0
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
                    component_critical,
                    redundancy_group);

                if (platform_damage) {
                    if (structured_air_target) {
                        note_air_system_hit(system, mechanism_scale);
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
                          true).scale
                    : 1.0;
            const double system_severity = structured_air_target
                ? std::clamp(
                    severity * warhead_effects.system_damage_scale * vulnerability_system_scale,
                    0.05,
                    0.95)
                : severity;
            double spatial_effect_scale = 0.0;
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
                                std::clamp(component.threshold_scale, 0.40, 1.80);
                            sampled_component_threshold_scale =
                                std::max(sampled_component_threshold_scale, component_scale);
                            apply_system_effect(
                                component.system,
                                system_severity,
                                direct_mechanism_scale,
                                component_scale,
                                true);
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
                                true);
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
                for (const auto& box : hitboxes->hitboxes) {
                    if (!box.components.empty()) {
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
                                        armor_scale *
                                        exposure_scale,
                                    warhead_projection.min_effect_scale,
                                    warhead_projection.max_effect_scale),
                                .axis_weight = axis_weight,
                                .armor_scale = armor_scale,
                                .exposure_scale = exposure_scale,
                            });
                        }
                    } else {
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
                            candidates.push_back(SpatialProjectionCandidate{
                                .box = &box,
                                .distance_m = distance_m,
                                .effect_scale = std::clamp(
                                    projected_spatial_effect_scale(
                                        distance_m,
                                        spatial_radius_m,
                                        warhead_projection) *
                                        axis_weight *
                                        armor_scale *
                                        exposure_scale,
                                    warhead_projection.min_effect_scale,
                                    warhead_projection.max_effect_scale),
                                .axis_weight = axis_weight,
                                .armor_scale = armor_scale,
                                .exposure_scale = exposure_scale,
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
                            std::clamp(projected_component->threshold_scale, 0.40, 1.80);
                        sampled_component_threshold_scale =
                            std::max(sampled_component_threshold_scale, component_scale);
                        apply_system_effect(
                            projected_component->system,
                            projected_system_severity,
                            candidate.effect_scale,
                            component_scale,
                            false);
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
                                false);
                            spdlog::info("   - {} Status: {:.2f}", system, sys_health->systems[system]);
                        }
                    }
                }
            }

            if (platform_damage && structured_air_target && structure_hit) {
                const bool direct_structure_hit = direct_hitbox_intersection;
                const VulnerabilityAdjustment vulnerability_adjustment =
                    make_vulnerability_adjustment(
                        missile.warhead_profile,
                        aircraft_vulnerability,
                        local_imp,
                        closure_mps,
                        spatial_effect_scale,
                        direct_structure_hit);
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
                    if (air_crew_hit) {
                        aircraft_damage->crew_effectiveness -=
                            localized_effect_delta(
                                0.42,
                                0.25,
                                resolved_severity,
                                warhead_effects.crew_scale,
                                crew_scale);
                        aircraft_damage->flight_control_integrity -=
                            localized_effect_delta(
                                0.08,
                                0.08,
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
                if (air_crew_hit) {
                    platform_damage->survivability_margin -=
                        localized_effect_delta(
                            0.10,
                            0.10,
                            resolved_severity,
                            warhead_effects.crew_scale,
                            crew_scale);
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
                    result.component_threshold_scale = sampled_component_threshold_scale;
                    result.component_failure_probability = sampled_component_failure_probability;
                    result.component_failure_sample = sampled_component_failure_sample;
                    result.component_failure_count = component_failure_count;
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
            result.component_threshold_scale = sampled_component_threshold_scale;
            result.component_failure_probability = sampled_component_failure_probability;
            result.component_failure_sample = sampled_component_failure_sample;
            result.component_failure_count = component_failure_count;
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
