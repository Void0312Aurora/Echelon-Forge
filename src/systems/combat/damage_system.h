#pragma once

#include <flecs.h>
#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cmath>
#include <limits>
#include <string>
#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/command/legacy_command_bridge.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "components/naval/ship_platform.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "components/systems/ew.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/effects_model.h"
#include <spdlog/spdlog.h>

namespace {
inline uint64_t damage_splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

inline double damage_rand_uniform01(uint64_t& state) {
    state = damage_splitmix64(state);
    return (state >> 11) * (1.0 / 9007199254740992.0);
}

inline bool proximity_fuze_has_terminal_guidance_support(const Missile& missile) {
    if (missile.seeker_has_valid_track) {
        return true;
    }
    if (!missile.terminal_seeker_active) {
        return false;
    }
    return missile.seeker_mode == 1;
}

inline std::string damage_lower_ascii(std::string value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return value;
}

inline std::string damage_resolved_fuze_type(const Missile& missile) {
    const std::string raw = damage_lower_ascii(fuze_profile_type(missile.fuze_profile));
    if (raw == "contact" || raw == "impact") {
        return "contact";
    }
    if (raw == "radarproximity" || raw == "radar_proximity" ||
        raw == "rfproximity" || raw == "rf_proximity") {
        return "radar_proximity";
    }
    if (raw == "laserproximity" || raw == "laser_proximity") {
        return "laser_proximity";
    }
    if (raw == "timed" || raw == "time") {
        return "timed";
    }
    return raw.empty() ? "proximity" : raw;
}

inline bool damage_fuze_is_contact(const std::string& fuze_type) {
    return fuze_type == "contact";
}

inline bool damage_fuze_is_timed(const std::string& fuze_type) {
    return fuze_type == "timed";
}

struct DamageFuzeSignatureEvidence {
    std::string source = "none";
    double target_signature = 0.0;
    double signature_scale = 1.0;
    double effective_reliability = 1.0;
};

inline double damage_target_rcs_from_aspect(
    const RCSProfile* rcs,
    const Transform& target_transform,
    const Transform& observer_transform
) {
    if (!rcs) {
        return 5.0;
    }

    constexpr double kPi = 3.14159265358979323846;
    const double los_math_deg =
        std::atan2(observer_transform.y - target_transform.y,
                  observer_transform.x - target_transform.x) *
        180.0 / kPi;
    double los_nav_deg = 90.0 - los_math_deg;
    while (los_nav_deg < 0.0) {
        los_nav_deg += 360.0;
    }
    while (los_nav_deg >= 360.0) {
        los_nav_deg -= 360.0;
    }
    double aspect_deg = los_nav_deg - target_transform.heading;
    while (aspect_deg > 180.0) {
        aspect_deg -= 360.0;
    }
    while (aspect_deg < -180.0) {
        aspect_deg += 360.0;
    }

    const double aspect_abs = std::abs(aspect_deg);
    if (aspect_abs <= 45.0) {
        return std::max(1.0e-6, rcs->frontal_rcs);
    }
    if (aspect_abs >= 135.0) {
        return std::max(1.0e-6, rcs->rear_rcs);
    }
    return std::max(1.0e-6, rcs->side_rcs);
}

inline double damage_target_projected_size_signature(
    const HitboxConfig* hitboxes
) {
    if (!hitboxes || hitboxes->hitboxes.empty()) {
        return 5.0;
    }

    double max_cross_section_m2 = 0.0;
    for (const Hitbox& box : hitboxes->hitboxes) {
        const double forward_area = std::max(0.0, box.dim_w * box.dim_h);
        const double side_area = std::max(0.0, box.dim_l * box.dim_h);
        const double plan_area = std::max(0.0, box.dim_l * box.dim_w);
        max_cross_section_m2 = std::max(
            max_cross_section_m2,
            std::max({forward_area, side_area, plan_area}));
    }
    return std::max(0.1, max_cross_section_m2);
}

inline DamageFuzeSignatureEvidence damage_fuze_signature_evidence(
    const std::string& fuze_type,
    const Transform& missile_transform,
    const Transform& target_transform,
    const RCSProfile* target_rcs,
    const HitboxConfig* target_hitboxes,
    double fuze_reliability
) {
    DamageFuzeSignatureEvidence evidence{};
    evidence.effective_reliability = std::clamp(fuze_reliability, 0.0, 1.0);

    if (fuze_type == "radar_proximity") {
        const double rcs_m2 = damage_target_rcs_from_aspect(
            target_rcs,
            target_transform,
            missile_transform);
        evidence.source = "target_rcs_aspect";
        evidence.target_signature = rcs_m2;
        evidence.signature_scale = std::clamp(std::sqrt(rcs_m2 / 5.0), 0.35, 1.25);
    } else if (fuze_type == "laser_proximity") {
        const double projected_area_m2 = damage_target_projected_size_signature(target_hitboxes);
        evidence.source = "target_projected_geometry";
        evidence.target_signature = projected_area_m2;
        evidence.signature_scale = std::clamp(std::sqrt(projected_area_m2 / 6.0), 0.45, 1.15);
    } else if (fuze_type == "proximity") {
        evidence.source = "generic_proximity";
        evidence.target_signature = 1.0;
        evidence.signature_scale = 1.0;
    }

    evidence.effective_reliability = std::clamp(
        fuze_reliability * evidence.signature_scale,
        0.0,
        1.0);
    return evidence;
}

inline std::string damage_fuze_trigger_type(const Missile& missile) {
    const std::string fuze_type = damage_resolved_fuze_type(missile);
    if (damage_fuze_is_contact(fuze_type)) {
        return "contact_fuze";
    }
    if (damage_fuze_is_timed(fuze_type)) {
        return "timed_fuze";
    }
    return "proximity_fuze";
}

inline double damage_contact_fuze_surface_tolerance_m(const Missile& missile) {
    const double authored_trigger = missile.fuze_profile.trigger_radius_m;
    if (std::isfinite(authored_trigger) && authored_trigger > 0.0 && authored_trigger <= 2.0) {
        return authored_trigger;
    }
    return 0.25;
}

inline std::array<double, 3> damage_world_point_to_local_body(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z
);

inline double damage_hitbox_surface_distance_local(
    const std::array<double, 3>& local_point,
    const Hitbox& box
) {
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;

    const double dx = std::max({min_x - local_point[0], 0.0, local_point[0] - max_x});
    const double dy = std::max({min_y - local_point[1], 0.0, local_point[1] - max_y});
    const double dz = std::max({min_z - local_point[2], 0.0, local_point[2] - max_z});
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

inline bool damage_point_inside_hitbox_local(
    const std::array<double, 3>& local_point,
    const Hitbox& box
) {
    return local_point[0] >= box.offset_x - box.dim_l * 0.5 &&
        local_point[0] <= box.offset_x + box.dim_l * 0.5 &&
        local_point[1] >= box.offset_y - box.dim_w * 0.5 &&
        local_point[1] <= box.offset_y + box.dim_w * 0.5 &&
        local_point[2] >= box.offset_z - box.dim_h * 0.5 &&
        local_point[2] <= box.offset_z + box.dim_h * 0.5;
}

inline double damage_hitbox_penetration_depth_local(
    const std::array<double, 3>& local_point,
    const Hitbox& box
) {
    if (!damage_point_inside_hitbox_local(local_point, box)) {
        return 0.0;
    }
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;
    return std::max(
        0.0,
        std::min({
            local_point[0] - min_x,
            max_x - local_point[0],
            local_point[1] - min_y,
            max_y - local_point[1],
            local_point[2] - min_z,
            max_z - local_point[2],
        }));
}

struct DamageContactFuzeEvidence {
    double surface_distance_m = 0.0;
    double penetration_depth_m = 0.0;
    bool inside_hitbox = false;
};

inline DamageContactFuzeEvidence damage_contact_fuze_evidence(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z,
    const HitboxConfig* hitboxes
) {
    DamageContactFuzeEvidence evidence{};
    if (!hitboxes || hitboxes->hitboxes.empty()) {
        const double dx = world_x - target_transform.x;
        const double dy = world_y - target_transform.y;
        const double dz = world_z - target_transform.z;
        evidence.surface_distance_m = std::sqrt(dx * dx + dy * dy + dz * dz);
        return evidence;
    }

    const auto local_point =
        damage_world_point_to_local_body(target_transform, world_x, world_y, world_z);
    double min_surface_distance_m = std::numeric_limits<double>::infinity();
    double max_penetration_depth_m = 0.0;
    bool inside_hitbox = false;
    for (const auto& box : hitboxes->hitboxes) {
        min_surface_distance_m = std::min(
            min_surface_distance_m,
            damage_hitbox_surface_distance_local(local_point, box));
        if (damage_point_inside_hitbox_local(local_point, box)) {
            inside_hitbox = true;
            max_penetration_depth_m = std::max(
                max_penetration_depth_m,
                damage_hitbox_penetration_depth_local(local_point, box));
        }
    }

    evidence.surface_distance_m =
        std::isfinite(min_surface_distance_m) ? min_surface_distance_m : 0.0;
    evidence.penetration_depth_m = max_penetration_depth_m;
    evidence.inside_hitbox = inside_hitbox;
    return evidence;
}

inline double damage_target_surface_distance_m(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z,
    const HitboxConfig* hitboxes
) {
    if (!hitboxes || hitboxes->hitboxes.empty()) {
        const double dx = world_x - target_transform.x;
        const double dy = world_y - target_transform.y;
        const double dz = world_z - target_transform.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    const auto local_point =
        damage_world_point_to_local_body(target_transform, world_x, world_y, world_z);
    double min_surface_distance_m = std::numeric_limits<double>::infinity();
    for (const auto& box : hitboxes->hitboxes) {
        min_surface_distance_m = std::min(
            min_surface_distance_m,
            damage_hitbox_surface_distance_local(local_point, box));
    }
    return min_surface_distance_m;
}

inline void sync_platform_damage_loss_state(
    Health& health,
    PlatformDamageState& damage,
    bool force_lost = false
) {
    damage.mission_capability = std::clamp(damage.mission_capability, 0.0, 1.0);
    damage.mobility_capability = std::clamp(damage.mobility_capability, 0.0, 1.0);
    damage.sensor_capability = std::clamp(damage.sensor_capability, 0.0, 1.0);
    damage.survivability_margin = std::clamp(damage.survivability_margin, 0.0, 1.0);

    damage.mission_kill = damage.mission_capability <= 0.25;
    damage.mobility_kill = damage.mobility_capability <= 0.25;
    damage.sensor_kill = damage.sensor_capability <= 0.25;

    if (force_lost || damage.survivability_margin <= 0.0 || health.current_hp <= 0.0) {
        damage.loss_state = PlatformLossState::Lost;
    } else if (damage.mobility_kill) {
        damage.loss_state = PlatformLossState::MobilityKill;
    } else if (damage.sensor_kill) {
        damage.loss_state = PlatformLossState::SensorKill;
    } else if (damage.mission_kill) {
        damage.loss_state = PlatformLossState::MissionKill;
    } else {
        damage.loss_state = PlatformLossState::CombatCapable;
    }

    health.mission_kill = damage.mission_kill;
    health.mobility_kill = damage.mobility_kill;
    health.sensor_kill = damage.sensor_kill;
}

inline bool engagement_damage_snapshot_changed(
    const EngagementDamageStateSnapshot& before,
    const EngagementDamageStateSnapshot& after
) {
    constexpr double epsilon = 1.0e-6;
    return before.entity_active != after.entity_active ||
        std::abs(before.hp - after.hp) > epsilon ||
        std::abs(before.mission_capability - after.mission_capability) > epsilon ||
        std::abs(before.mobility_capability - after.mobility_capability) > epsilon ||
        std::abs(before.sensor_capability - after.sensor_capability) > epsilon ||
        std::abs(before.survivability_margin - after.survivability_margin) > epsilon ||
        before.mission_kill != after.mission_kill ||
        before.mobility_kill != after.mobility_kill ||
        before.sensor_kill != after.sensor_kill ||
        before.loss_state != after.loss_state;
}

inline std::array<double, 3> damage_world_point_to_local_body(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z
) {
    const Math::Vector3 local = Math::world_to_body(
        {
            world_x - target_transform.x,
            world_y - target_transform.y,
            world_z - target_transform.z,
        },
        target_transform);
    return {
        local.x,
        -local.y,
        local.z,
    };
}

inline std::array<double, 3> damage_velocity_axis_in_target_body(
    const Transform& target_transform,
    const Velocity* missile_velocity
) {
    if (!missile_velocity) {
        return {0.0, 0.0, 0.0};
    }
    const double norm = std::sqrt(
        missile_velocity->vx * missile_velocity->vx +
        missile_velocity->vy * missile_velocity->vy +
        missile_velocity->vz * missile_velocity->vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity = damage_world_point_to_local_body(
        target_transform,
        target_transform.x + missile_velocity->vx,
        target_transform.y + missile_velocity->vy,
        target_transform.z + missile_velocity->vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

inline double damage_closure_mps(
    const Transform& missile_transform,
    const Transform& target_transform,
    const Velocity* missile_velocity,
    const Velocity* target_velocity
) {
    if (!missile_velocity) {
        return 0.0;
    }
    const double target_vx = target_velocity ? target_velocity->vx : 0.0;
    const double target_vy = target_velocity ? target_velocity->vy : 0.0;
    const double target_vz = target_velocity ? target_velocity->vz : 0.0;
    const double rel_vx = target_vx - missile_velocity->vx;
    const double rel_vy = target_vy - missile_velocity->vy;
    const double rel_vz = target_vz - missile_velocity->vz;
    const double dx = target_transform.x - missile_transform.x;
    const double dy = target_transform.y - missile_transform.y;
    const double dz = target_transform.z - missile_transform.z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return std::sqrt(rel_vx * rel_vx + rel_vy * rel_vy + rel_vz * rel_vz);
    }
    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

inline void accumulate_aircraft_structural_envelope_damage(
    const AircraftDamageBaseline& baseline,
    const AeroState& aero,
    double dt_s,
    AircraftDamageState& aircraft
) {
    if (dt_s <= 0.0 || aircraft.structural_integrity >= 0.985) {
        return;
    }

    const double flutter_q = std::max(1.0, baseline.flutter_dynamic_pressure_pa);
    const double flutter_mach = std::max(0.05, baseline.flutter_mach);
    const double prior_damage = std::clamp(1.0 - aircraft.structural_integrity, 0.0, 1.0);
    const double damage_bias = 1.0 - (0.12 * prior_damage);
    const double q_ratio = std::max(0.0, aero.dynamic_pressure) / flutter_q;
    const double q_excess = std::max(0.0, q_ratio - damage_bias);
    const double mach_excess = std::max(0.0, (aero.mach_number / flutter_mach) - damage_bias);
    const double high_energy_gate = std::clamp(
        (std::max(q_ratio, aero.mach_number / flutter_mach) - 0.90) / 0.25,
        0.0,
        1.0);
    const double stall_exposure = std::clamp((aero.stall_progress - 0.35) / 0.65, 0.0, 1.0) *
        high_energy_gate *
        std::max(0.0, prior_damage - 0.10);

    const double flutter_rate =
        ((0.035 * q_excess) + (0.025 * mach_excess) + (0.015 * stall_exposure)) *
        prior_damage;
    const double overstress_rate =
        ((0.020 * std::max(0.0, q_ratio - 1.20)) +
         (0.018 * std::max(0.0, aero.mach_number - (flutter_mach + 0.10)))) *
        prior_damage;

    if (flutter_rate <= 0.0 && overstress_rate <= 0.0) {
        return;
    }

    aircraft.flutter_exposure += flutter_rate * dt_s;
    aircraft.structural_overstress += overstress_rate * dt_s;

    const double structural_loss =
        ((0.018 * flutter_rate) + (0.030 * overstress_rate)) * dt_s;
    aircraft.structural_integrity -= structural_loss;
}

inline void apply_aircraft_damage_state_to_sensor(
    const AircraftDamageBaseline& baseline,
    const AircraftDamageState& aircraft,
    Sensor& sensor
) {
    if (baseline.sensor_max_range <= 0.0) {
        return;
    }

    const double avionics = std::clamp(aircraft.avionics_integrity, 0.0, 1.0);
    const double crew = std::clamp(aircraft.crew_effectiveness, 0.0, 1.0);
    const double mission_crew =
        std::clamp(aircraft.mission_crew_effectiveness, 0.0, 1.0);
    const double command_navigation =
        std::clamp(aircraft.command_navigation_integrity, 0.0, 1.0);
    const double mission_operator =
        std::min({crew, mission_crew, command_navigation});
    const double mission_scale =
        aircraft_damage_capability_floor(std::min(avionics, mission_operator), 0.12);
    const double avionics_scale = aircraft_damage_capability_floor(avionics, 0.10);
    const double crew_scale = aircraft_damage_capability_floor(mission_operator, 0.35);

    sensor.max_range = baseline.sensor_max_range * mission_scale;
    sensor.detection_prob = std::clamp(
        baseline.sensor_detection_prob * avionics_scale * crew_scale,
        0.0,
        1.0);
    sensor.bearing_noise_std = baseline.sensor_bearing_noise_std *
        (1.0 + 2.5 * (1.0 - avionics));
    sensor.range_noise_std = baseline.sensor_range_noise_std *
        (1.0 + 2.0 * (1.0 - avionics));
    sensor.track_memory_s = baseline.sensor_track_memory_s *
        aircraft_damage_capability_floor(avionics, 0.25);
}

inline double drain_aircraft_fuel_leak(
    AircraftDamageState& aircraft,
    double dt_s,
    FuelSystem* fuel,
    Mass* mass
) {
    if (dt_s <= 0.0 || aircraft.fuel_leak_severity <= 1.0e-6) {
        return 0.0;
    }

    const double leak_rate_kg_s =
        1.5 + (11.0 * std::clamp(aircraft.fuel_leak_severity, 0.0, 1.0));
    double leaked_kg = leak_rate_kg_s * dt_s;
    double drained_kg = 0.0;

    if (fuel) {
        const double external_drain = std::min(std::max(0.0, fuel->external_fuel_kg), leaked_kg);
        fuel->external_fuel_kg -= external_drain;
        leaked_kg -= external_drain;
        drained_kg += external_drain;

        const double internal_drain = std::min(std::max(0.0, fuel->internal_fuel_kg), leaked_kg);
        fuel->internal_fuel_kg -= internal_drain;
        leaked_kg -= internal_drain;
        drained_kg += internal_drain;
    } else if (mass) {
        const double mass_drain = std::min(std::max(0.0, mass->fuel_mass_kg), leaked_kg);
        mass->fuel_mass_kg -= mass_drain;
        drained_kg += mass_drain;
    }

    if (drained_kg <= 1.0e-6) {
        aircraft.fuel_system_integrity -= 0.010 * dt_s * aircraft.fuel_leak_severity;
    }
    if (fuel && fuel->internal_fuel_kg <= 1.0e-6 && fuel->external_fuel_kg <= 1.0e-6) {
        aircraft.propulsion_integrity -= 0.020 * dt_s;
        aircraft.forced_landing_required = true;
    }

    return drained_kg;
}

inline void propagate_aircraft_damage_cascade(
    AircraftDamageState& aircraft,
    double dt_s,
    double leaked_fuel_kg
) {
    if (dt_s <= 0.0) {
        return;
    }

    const double fuel_damage = std::clamp(1.0 - aircraft.fuel_system_integrity, 0.0, 1.0);
    const double hydraulic_damage = std::clamp(1.0 - aircraft.hydraulic_integrity, 0.0, 1.0);
    const double avionics_damage = std::clamp(1.0 - aircraft.avionics_integrity, 0.0, 1.0);
    const double leak_activity = std::clamp(leaked_fuel_kg / std::max(1.0e-6, dt_s * 8.0), 0.0, 1.0);

    aircraft.fire_severity +=
        ((0.0040 * fuel_damage) + (0.0025 * hydraulic_damage) +
         (0.0020 * avionics_damage) + (0.0035 * leak_activity)) *
        dt_s;

    const double fire = std::clamp(aircraft.fire_severity, 0.0, 1.0);
    if (fire > 0.0) {
        aircraft.structural_integrity -= 0.0060 * fire * dt_s;
        aircraft.avionics_integrity -= 0.0065 * fire * dt_s;
        aircraft.crew_effectiveness -= 0.0035 * fire * dt_s;
        aircraft.pilot_effectiveness -= 0.0025 * fire * dt_s;
        aircraft.mission_crew_effectiveness -= 0.0030 * fire * dt_s;
        aircraft.command_navigation_integrity -= 0.0020 * fire * dt_s;
        aircraft.hydraulic_integrity -= 0.0045 * fire * dt_s;
        aircraft.fuel_system_integrity -= 0.0040 * fire * dt_s;
    }

    if (hydraulic_damage > 0.0) {
        aircraft.flight_control_integrity -= 0.0040 * hydraulic_damage * dt_s;
        if (hydraulic_damage > 0.65) {
            aircraft.structural_overstress += 0.0020 * (hydraulic_damage - 0.65) * dt_s;
        }
    }

    const double extinguish_rate = 0.0015 * (1.0 - std::clamp(fuel_damage + leak_activity, 0.0, 1.0));
    aircraft.fire_severity = std::clamp(aircraft.fire_severity - extinguish_rate * dt_s, 0.0, 1.0);
}
} // namespace

inline void register_damage_system(flecs::world& ecs) {
    ecs.system<Transform, Missile>("ProximityFuze")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto p = it.field<Transform>(0);
                auto m = it.field<Missile>(1);
                const EffectsModelRef* effects_ref = it.world().get<EffectsModelRef>();
                const EngagementEventRecorderRef* recorder_ref = it.world().get<EngagementEventRecorderRef>();
                const ecs_world_info_t* world_info = ecs_get_world_info(it.world().c_ptr());
                const double current_time = world_info
                    ? static_cast<double>(world_info->world_time_total)
                    : 0.0;
                
                for (auto i : it) {
                    if (!m[i].active) continue;
                    
                    auto target_entity = it.world().entity(m[i].target_id);
                    if (!target_entity.is_valid()) {
                        it.entity(i).destruct();
                        continue;
                    }
                    
                    const Transform* t_pos = target_entity.get<Transform>();
                    if(!t_pos) continue;
                    
                    double dx = p[i].x - t_pos->x;
                    double dy = p[i].y - t_pos->y;
                    double dz = p[i].z - t_pos->z;
                    double dist_sq = dx * dx + dy * dy + dz * dz;
                    double dist = std::sqrt(std::max(0.0, dist_sq));
                    const std::string fuze_type = damage_resolved_fuze_type(m[i]);
                    const bool contact_fuze = damage_fuze_is_contact(fuze_type);
                    const bool timed_fuze = damage_fuze_is_timed(fuze_type);
                    const std::string trigger_type = damage_fuze_trigger_type(m[i]);

                    if (m[i].fuze_delay_armed) {
                        if (!std::isfinite(m[i].fuze_detonation_time_s) ||
                            current_time < m[i].fuze_detonation_time_s) {
                            continue;
                        }

                        if (!effects_ref || !effects_ref->model) {
                            spdlog::warn("Effects model not configured; skipping delayed fuze resolution.");
                            it.entity(i).destruct();
                            continue;
                        }

                        const double trigger_radius_m = std::isfinite(m[i].fuze_profile.trigger_radius_m)
                            ? m[i].fuze_profile.trigger_radius_m
                            : m[i].fuse_distance;
                        const double fuze_reliability =
                            std::clamp(m[i].fuze_profile.reliability, 0.0, 1.0);
                        p[i].x = std::isfinite(m[i].fuze_detonation_x) ? m[i].fuze_detonation_x : p[i].x;
                        p[i].y = std::isfinite(m[i].fuze_detonation_y) ? m[i].fuze_detonation_y : p[i].y;
                        p[i].z = std::isfinite(m[i].fuze_detonation_z) ? m[i].fuze_detonation_z : p[i].z;
                        p[i].heading = std::isfinite(m[i].fuze_detonation_heading_deg)
                            ? m[i].fuze_detonation_heading_deg
                            : p[i].heading;
                        p[i].pitch = std::isfinite(m[i].fuze_detonation_pitch_deg)
                            ? m[i].fuze_detonation_pitch_deg
                            : p[i].pitch;
                        p[i].roll = std::isfinite(m[i].fuze_detonation_roll_deg)
                            ? m[i].fuze_detonation_roll_deg
                            : p[i].roll;

                        Missile effective = m[i];
                        effective.damage = effective.damage * (0.6 + 0.4 * m[i].fuze_quality);
                        EngagementDamageStateSnapshot before{};
                        const bool can_record_damage =
                            recorder_ref && recorder_ref->recorder != nullptr;
                        if (can_record_damage) {
                            before = recorder_ref->recorder->capture_engagement_damage_state(m[i].target_id);
                        }
                        const EffectsResult effects_result = effects_ref->model->on_proximity_hit(
                            it.world(), it.entity(i), effective, target_entity);
                        if (can_record_damage) {
                            const EngagementDamageStateSnapshot after =
                                recorder_ref->recorder->capture_engagement_damage_state(m[i].target_id);
                            const double detonation_time_s = std::isfinite(m[i].fuze_detonation_time_s)
                                ? m[i].fuze_detonation_time_s
                                : current_time;
                            const auto detonation_local = damage_world_point_to_local_body(
                                *t_pos,
                                p[i].x,
                                p[i].y,
                                p[i].z);
                            (void)recorder_ref->recorder->record_effects_damage_event(
                                static_cast<std::uint64_t>(it.entity(i).id()),
                                m[i].target_id,
                                before,
                                after,
                                trigger_type,
                                engagement_damage_snapshot_changed(before, after)
                                    ? "damage_applied"
                                    : "detonated_no_effect",
                                detonation_time_s,
                                std::isfinite(m[i].fuze_nearest_approach_time_s)
                                    ? m[i].fuze_nearest_approach_time_s
                                    : detonation_time_s,
                                m[i].proximity_min_dist_m,
                                detonation_local[0],
                                detonation_local[1],
                                detonation_local[2],
                                p[i].heading,
                                p[i].pitch,
                                p[i].roll,
                                m[i].fuze_closure_mps,
                                m[i].fuze_missile_axis_forward,
                                m[i].fuze_missile_axis_right,
                                m[i].fuze_missile_axis_up,
                                m[i].fuze_quality,
                                m[i].fuze_hit_probability,
                                warhead_effect_family(effective.warhead_profile),
                                std::isfinite(effective.warhead_profile.mass_kg)
                                    ? effective.warhead_profile.mass_kg
                                    : 0.0,
                                std::isfinite(effective.warhead_profile.lethal_radius_m)
                                    ? effective.warhead_profile.lethal_radius_m
                                    : effective.fuse_distance,
                                effective.warhead_profile.synthetic,
                                effective.warhead_profile.damage_scalar_synthetic,
                                fuze_profile_type(effective.fuze_profile),
                                trigger_radius_m,
                                std::max(0.0, effective.fuze_profile.delay_s),
                                fuze_reliability,
                                effective.fuze_profile.synthetic,
                                m[i].fuze_signature_source,
                                m[i].fuze_target_signature,
                                m[i].fuze_signature_scale,
                                m[i].fuze_effective_reliability,
                                m[i].fuze_contact_surface_distance_m,
                                m[i].fuze_contact_penetration_depth_m,
                                m[i].fuze_contact_surface_tolerance_m,
                                m[i].fuze_contact_inside_hitbox,
                                effects_result.direct_hitbox_intersection,
                                effects_result.projected_hitbox_count,
                                effects_result.spatial_effect_scale,
                                effects_result.mechanism_armor_scale,
                                effects_result.mechanism_exposure_scale,
                                effects_result.mechanism_effect_scale,
                                effects_result.mechanism_fragment_energy_j,
                                effects_result.mechanism_fragment_areal_density_per_m2,
                                effects_result.mechanism_penetration_margin,
                                effects_result.mechanism_blast_overpressure_kpa,
                                effects_result.mechanism_blast_impulse_kpa_ms,
                                effects_result.mechanism_blast_scaled_distance_m_kg13,
                                effects_result.mechanism_rod_cut_margin,
                                effects_result.warhead_spatial_sample_count,
                                effects_result.warhead_spatial_hit_estimate,
                                effects_result.warhead_spatial_hit_fraction,
                                effects_result.warhead_spatial_energy_scale,
                                effects_result.warhead_spatial_pattern_scale,
                                effects_result.warhead_orientation_axis_forward,
                                effects_result.warhead_orientation_axis_right,
                                effects_result.warhead_orientation_axis_up,
                                effects_result.warhead_orientation_pattern_scale,
                                effects_result.component_threshold_scale,
                                effects_result.component_failure_probability,
                                effects_result.component_failure_probability_source,
                                effects_result.component_failure_probability_calibrated,
                                effects_result.component_failure_probability_evidence_dataset_ref,
                                effects_result.component_failure_probability_evidence_row_id,
                                effects_result.component_failure_probability_evidence_source_ref,
                                effects_result.component_failure_probability_evidence_provenance,
                                effects_result.component_failure_sample,
                                effects_result.component_failure_count,
                                effects_result.component_hit_count,
                                effects_result.component_mechanism_load_rows,
                                effects_result.component_primary_name,
                                effects_result.component_primary_system,
                                effects_result.component_primary_redundancy_group,
                                effects_result.component_primary_critical,
                                effects_result.component_primary_redundancy_group_id,
                                effects_result.component_primary_integrity,
                                effects_result.component_primary_mechanism_fragment_energy_j,
                                effects_result.component_primary_mechanism_fragment_areal_density_per_m2,
                                effects_result.component_primary_mechanism_penetration_margin,
                                effects_result.component_primary_mechanism_blast_overpressure_kpa,
                                effects_result.component_primary_mechanism_blast_impulse_kpa_ms,
                                effects_result.component_primary_mechanism_blast_scaled_distance_m_kg13,
                                effects_result.component_primary_mechanism_rod_cut_margin,
                                effects_result.component_redundancy_group_availability,
                                effects_result.component_redundancy_group_member_count,
                                effects_result.component_redundancy_group_failed_count,
                                effects_result.vulnerability_profile_present,
                                effects_result.vulnerability_profile_synthetic,
                                effects_result.vulnerability_calibrated_evidence,
                                effects_result.vulnerability_pk_authority,
                                effects_result.vulnerability_deterministic_fuze_authority,
                                effects_result.vulnerability_evidence_dataset_valid,
                                effects_result.vulnerability_evidence_dataset_ref,
                                effects_result.vulnerability_calibration_status,
                                effects_result.vulnerability_provenance,
                                effects_result.vulnerability_evidence_schema_version,
                                effects_result.vulnerability_evidence_source_kind,
                                effects_result.vulnerability_evidence_source_ref,
                                effects_result.vulnerability_evidence_validation_artifact_ref,
                                effects_result.vulnerability_evidence_validation_manifest_schema_version,
                                effects_result.vulnerability_evidence_validation_status,
                                effects_result.vulnerability_evidence_validation_artifact_sha256,
                                effects_result.vulnerability_evidence_validated_surrogate_model_ref,
                                effects_result.vulnerability_evidence_validation_benchmark_ref,
                                effects_result.vulnerability_evidence_validation_metrics_ref,
                                effects_result.vulnerability_evidence_validation_acceptance_criteria_ref,
                                effects_result.vulnerability_aspect_bucket,
                                effects_result.vulnerability_family_scale,
                                effects_result.vulnerability_aspect_scale,
                                effects_result.vulnerability_closure_mps,
                                effects_result.vulnerability_closure_scale,
                                effects_result.vulnerability_miss_distance_scale,
                                effects_result.vulnerability_effect_scale,
                                effects_result.vulnerability_effect_scale_source,
                                effects_result.vulnerability_effect_scale_evidence_row_id,
                                effects_result.vulnerability_effect_scale_evidence_source_ref,
                                effects_result.vulnerability_effect_scale_evidence_provenance,
                                effects_result.mechanism_surface_incidence_cos,
                                effects_result.component_primary_mechanism_surface_incidence_cos);
                        }
                        it.entity(i).destruct();
                        continue;
                    }

                    if (timed_fuze) {
                        const double fuze_delay_s = std::max(0.0, m[i].fuze_profile.delay_s);
                        const double elapsed_s = current_time - m[i].launch_time;
                        if (elapsed_s < fuze_delay_s) {
                            if (dist < m[i].proximity_min_dist_m) {
                                m[i].proximity_min_dist_m = dist;
                            }
                            if (std::isfinite(m[i].proximity_last_dist_m) &&
                                dist < m[i].proximity_last_dist_m - 1.0e-3) {
                                m[i].proximity_engaged = true;
                            }
                            m[i].proximity_last_dist_m = dist;
                            continue;
                        }

                        const double fuze_reliability =
                            std::clamp(m[i].fuze_profile.reliability, 0.0, 1.0);
                        if (damage_rand_uniform01(m[i].rng_state) > fuze_reliability) {
                            it.entity(i).destruct();
                            continue;
                        }

                        const Velocity* missile_velocity = it.entity(i).get<Velocity>();
                        const Velocity* target_velocity = target_entity.get<Velocity>();
                        const auto missile_axis =
                            damage_velocity_axis_in_target_body(*t_pos, missile_velocity);
                        const double closure_mps = damage_closure_mps(
                            p[i],
                            *t_pos,
                            missile_velocity,
                            target_velocity);
                        const double event_closure_mps =
                            std::max(closure_mps, std::max(0.0, m[i].filtered_closing_speed_mps));
                        const double trigger_radius_m = std::isfinite(m[i].fuze_profile.trigger_radius_m)
                            ? m[i].fuze_profile.trigger_radius_m
                            : m[i].fuse_distance;
                        const double fuse = std::max(1.0e-6, trigger_radius_m);
                        const double quality = std::clamp(1.0 - dist / fuse, 0.0, 1.0);

                        m[i].fuze_delay_armed = true;
                        m[i].fuze_nearest_approach_time_s = current_time;
                        m[i].fuze_detonation_time_s = current_time;
                        m[i].fuze_detonation_x = p[i].x;
                        m[i].fuze_detonation_y = p[i].y;
                        m[i].fuze_detonation_z = p[i].z;
                        m[i].fuze_detonation_heading_deg = p[i].heading;
                        m[i].fuze_detonation_pitch_deg = p[i].pitch;
                        m[i].fuze_detonation_roll_deg = p[i].roll;
                        m[i].fuze_quality = quality;
                        m[i].fuze_hit_probability = fuze_reliability;
                        m[i].fuze_signature_source = "timed";
                        m[i].fuze_target_signature = 0.0;
                        m[i].fuze_signature_scale = 1.0;
                        m[i].fuze_effective_reliability = fuze_reliability;
                        m[i].fuze_contact_surface_distance_m = 0.0;
                        m[i].fuze_contact_penetration_depth_m = 0.0;
                        m[i].fuze_contact_surface_tolerance_m = 0.0;
                        m[i].fuze_contact_inside_hitbox = false;
                        m[i].fuze_closure_mps = event_closure_mps;
                        m[i].fuze_missile_axis_forward = missile_axis[0];
                        m[i].fuze_missile_axis_right = missile_axis[1];
                        m[i].fuze_missile_axis_up = missile_axis[2];
                        continue;
                    }

                    if (!std::isfinite(m[i].proximity_last_dist_m)) {
                        m[i].proximity_last_dist_m = dist;
                        m[i].proximity_min_dist_m = dist;
                        continue;
                    }

                    if (dist < m[i].proximity_min_dist_m) {
                        m[i].proximity_min_dist_m = dist;
                    }

                    const double epsilon = 1e-3;
                    if (dist < m[i].proximity_last_dist_m - epsilon) {
                        m[i].proximity_engaged = true;
                        m[i].proximity_last_dist_m = dist;
                        continue;
                    }

                    if (!m[i].proximity_engaged) {
                        m[i].proximity_last_dist_m = dist;
                        continue;
                    }

                    if (!proximity_fuze_has_terminal_guidance_support(m[i])) {
                        it.entity(i).destruct();
                        continue;
                    }

                    const HitboxConfig* target_hitboxes = target_entity.get<HitboxConfig>();
                    double min_dist = m[i].proximity_min_dist_m;
                    const double trigger_radius_m = std::isfinite(m[i].fuze_profile.trigger_radius_m)
                        ? m[i].fuze_profile.trigger_radius_m
                        : m[i].fuse_distance;
                    double detonation_metric_m = min_dist;
                    double effective_trigger_radius_m = trigger_radius_m;
                    DamageContactFuzeEvidence contact_evidence{};
                    if (contact_fuze) {
                        contact_evidence = damage_contact_fuze_evidence(
                            *t_pos,
                            p[i].x,
                            p[i].y,
                            p[i].z,
                            target_hitboxes);
                        detonation_metric_m = contact_evidence.surface_distance_m;
                        effective_trigger_radius_m = damage_contact_fuze_surface_tolerance_m(m[i]);
                    }
                    if (detonation_metric_m > effective_trigger_radius_m) {
                        it.entity(i).destruct();
                        continue;
                    }

                    double fuse = std::max(1e-6, effective_trigger_radius_m);
                    double quality = contact_fuze
                        ? std::clamp(1.0 - detonation_metric_m / fuse, 0.0, 1.0)
                        : std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);
                    const double fuze_reliability =
                        std::clamp(m[i].fuze_profile.reliability, 0.0, 1.0);
                    const DamageFuzeSignatureEvidence fuze_signature =
                        contact_fuze
                            ? DamageFuzeSignatureEvidence{
                                  "contact_surface",
                                  0.0,
                                  1.0,
                                  fuze_reliability}
                            : damage_fuze_signature_evidence(
                                  fuze_type,
                                  p[i],
                                  *t_pos,
                                  target_entity.get<RCSProfile>(),
                                  target_hitboxes,
                                  fuze_reliability);

                    const double evasion = resolved_compatibility_damage_evasion(target_entity);

                    double base_hit = contact_fuze
                        ? 1.0
                        : 0.35 + 0.65 * quality;
                    double hit_prob = std::clamp(
                        base_hit *
                            fuze_signature.effective_reliability *
                            (contact_fuze ? 1.0 : (1.0 - 0.3 * evasion)),
                        0.0,
                        contact_fuze ? 1.0 : 0.98);
                    if (damage_rand_uniform01(m[i].rng_state) > hit_prob) {
                        it.entity(i).destruct();
                        continue;
                    }

                    const Velocity* missile_velocity = it.entity(i).get<Velocity>();
                    const Velocity* target_velocity = target_entity.get<Velocity>();
                    const auto missile_axis =
                        damage_velocity_axis_in_target_body(*t_pos, missile_velocity);
                    const double closure_mps = damage_closure_mps(
                        p[i],
                        *t_pos,
                        missile_velocity,
                        target_velocity);
                    const double event_closure_mps =
                        std::max(closure_mps, std::max(0.0, m[i].filtered_closing_speed_mps));
                    const double fuze_delay_s = std::max(0.0, m[i].fuze_profile.delay_s);
                    m[i].fuze_delay_armed = true;
                    m[i].fuze_nearest_approach_time_s = current_time;
                    m[i].fuze_detonation_time_s = current_time + fuze_delay_s;
                    m[i].fuze_detonation_x = p[i].x;
                    m[i].fuze_detonation_y = p[i].y;
                    m[i].fuze_detonation_z = p[i].z;
                    m[i].fuze_detonation_heading_deg = p[i].heading;
                    m[i].fuze_detonation_pitch_deg = p[i].pitch;
                    m[i].fuze_detonation_roll_deg = p[i].roll;
                    m[i].fuze_quality = quality;
                    m[i].fuze_hit_probability = hit_prob;
                    m[i].fuze_signature_source = fuze_signature.source;
                    m[i].fuze_target_signature = fuze_signature.target_signature;
                    m[i].fuze_signature_scale = fuze_signature.signature_scale;
                    m[i].fuze_effective_reliability = fuze_signature.effective_reliability;
                    m[i].fuze_contact_surface_distance_m =
                        contact_fuze ? contact_evidence.surface_distance_m : 0.0;
                    m[i].fuze_contact_penetration_depth_m =
                        contact_fuze ? contact_evidence.penetration_depth_m : 0.0;
                    m[i].fuze_contact_surface_tolerance_m =
                        contact_fuze ? effective_trigger_radius_m : 0.0;
                    m[i].fuze_contact_inside_hitbox =
                        contact_fuze && contact_evidence.inside_hitbox;
                    m[i].fuze_closure_mps = event_closure_mps;
                    m[i].fuze_missile_axis_forward = missile_axis[0];
                    m[i].fuze_missile_axis_right = missile_axis[1];
                    m[i].fuze_missile_axis_up = missile_axis[2];
                    if (fuze_delay_s <= 0.0) {
                        continue;
                    }
                }
            }
        });

    ecs.system<Health, PlatformDamageState, const KeyEntity>("AircraftDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            const double dt_s = it.delta_time() > 0.0 ? it.delta_time() : 1.0 / 60.0;
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto damage = it.field<PlatformDamageState>(1);
                auto key = it.field<const KeyEntity>(2);
                for (auto i : it) {
                    flecs::entity e = it.entity(i);
                    if (key[i].type != UnitType::Aircraft && key[i].type != UnitType::C2Node) {
                        continue;
                    }

                    if (AircraftDamageState* aircraft = e.get_mut<AircraftDamageState>()) {
                        clamp_aircraft_damage_state(*aircraft);

                        if (const AircraftDamageBaseline* baseline = e.get<AircraftDamageBaseline>()) {
                            Mass* mass = e.get_mut<Mass>();
                            const double leaked_fuel_kg =
                                drain_aircraft_fuel_leak(
                                    *aircraft,
                                    dt_s,
                                    e.get_mut<FuelSystem>(),
                                    mass);
                            propagate_aircraft_damage_cascade(*aircraft, dt_s, leaked_fuel_kg);
                            clamp_aircraft_damage_state(*aircraft);

                            if (const AeroState* aero = e.get<AeroState>()) {
                                accumulate_aircraft_structural_envelope_damage(
                                    *baseline,
                                    *aero,
                                    dt_s,
                                    *aircraft);
                                clamp_aircraft_damage_state(*aircraft);
                            }

                            if (FlightModel* flight_model = e.get_mut<FlightModel>()) {
                                const double aggregate_control = std::min(
                                    aircraft->flight_control_integrity,
                                    aircraft->hydraulic_integrity);
                                const double pilot_control = aircraft_damage_capability_floor(
                                    aircraft->pilot_effectiveness,
                                    0.18);
                                const double roll_control = aircraft_damage_capability_floor(
                                    std::min(aggregate_control, aircraft->roll_control_integrity),
                                    0.20) *
                                    std::clamp(1.0 - (0.60 * aircraft->control_asymmetry), 0.45, 1.0) *
                                    pilot_control;
                                const double pitch_control = aircraft_damage_capability_floor(
                                    std::min(aggregate_control, aircraft->pitch_control_integrity),
                                    0.20) *
                                    pilot_control;
                                const double yaw_control = aircraft_damage_capability_floor(
                                    std::min(aggregate_control, aircraft->yaw_control_integrity),
                                    0.20) *
                                    std::clamp(1.0 - (0.35 * aircraft->control_asymmetry), 0.55, 1.0) *
                                    pilot_control;
                                const double control = std::min({
                                    roll_control,
                                    pitch_control,
                                    yaw_control});
                                const double structure = aircraft_damage_capability_floor(
                                    aircraft->structural_integrity,
                                    0.35);
                                const double mobility = aircraft_damage_capability_floor(
                                    std::min(control, structure),
                                    0.20);

                                flight_model->max_turn_rate = baseline->max_turn_rate * control;
                                flight_model->max_accel = baseline->max_accel * mobility;
                                flight_model->max_climb_rate = baseline->max_climb_rate * mobility;
                                flight_model->max_g = baseline->max_g * structure;
                                flight_model->min_g = baseline->min_g * structure;
                                flight_model->max_speed = baseline->max_speed *
                                    aircraft_damage_capability_floor(aircraft->propulsion_integrity, 0.45);
                                flight_model->min_speed = baseline->min_speed *
                                    (1.0 + (0.35 * (1.0 - aircraft->structural_integrity)));
                                flight_model->takeoff_speed = baseline->takeoff_speed *
                                    (1.0 + (0.20 * (1.0 - aircraft->structural_integrity)));
                                flight_model->landing_speed = baseline->landing_speed *
                                    (1.0 + (0.25 * (1.0 - pitch_control)));
                                flight_model->taxi_turn_rate = baseline->taxi_turn_rate * yaw_control;
                            }

                            if (Propulsion* propulsion = e.get_mut<Propulsion>()) {
                                const double propulsion_scale = aircraft_damage_capability_floor(
                                    aircraft->propulsion_integrity,
                                    0.15);
                                propulsion->mil_thrust_n = baseline->mil_thrust_n * propulsion_scale;
                                propulsion->ab_thrust_n = std::max(
                                    propulsion->mil_thrust_n,
                                    baseline->ab_thrust_n * propulsion_scale);
                            }

                            if (mass) {
                                mass->fuel_leak_rate_kg_s = baseline->fuel_leak_rate_kg_s +
                                    (8.0 * std::clamp(aircraft->fuel_leak_severity, 0.0, 1.0));
                            }

                            if (Sensor* sensor = e.get_mut<Sensor>()) {
                                apply_aircraft_damage_state_to_sensor(*baseline, *aircraft, *sensor);
                            }
                        }
                        apply_aircraft_damage_state_to_platform(*aircraft, damage[i]);
                        const double fire_progress = std::clamp(aircraft->fire_severity, 0.0, 1.0);
                        const double leak_progress = std::clamp(aircraft->fuel_leak_severity, 0.0, 1.0);
                        const double hydraulic_damage =
                            std::clamp(1.0 - aircraft->hydraulic_integrity, 0.0, 1.0);
                        damage[i].fire_severity = std::max(damage[i].fire_severity, fire_progress);
                        damage[i].mission_capability -= 0.0012 * fire_progress * dt_s;
                        damage[i].sensor_capability -= 0.0010 * fire_progress * dt_s;
                        damage[i].mobility_capability -= 0.0010 * hydraulic_damage * dt_s;
                        damage[i].survivability_margin -=
                            ((0.0018 * fire_progress) + (0.0010 * leak_progress) +
                             (0.0012 * std::clamp(aircraft->structural_overstress, 0.0, 1.0))) *
                            dt_s;
                    }
                    sync_platform_damage_loss_state(health[i], damage[i]);
                    if (damage[i].loss_state == PlatformLossState::Lost) {
                        health[i].current_hp = 0.0;
                        e.destruct();
                    }
                }
            }
        });

    ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .each([](flecs::entity e, Health& health, PlatformDamageState& damage, const ShipPlatform& ship) {
            const double fire_decay = 0.0008;
            const double flooding_decay = 0.0002;
            const double breach_decay = 0.0001;

            const double fire_progress = damage.fire_severity;
            const double flooding_progress = damage.flooding_severity;
            const double breach_progress = damage.ongoing_hull_breach;

            damage.fire_severity = std::clamp(damage.fire_severity - fire_decay, 0.0, 1.0);
            damage.flooding_severity = std::clamp(
                damage.flooding_severity + 0.003 * breach_progress - flooding_decay,
                0.0,
                1.0
            );
            damage.ongoing_hull_breach = std::clamp(damage.ongoing_hull_breach - breach_decay, 0.0, 1.0);

            damage.mission_capability -= 0.0015 * fire_progress;
            damage.sensor_capability -= 0.0012 * fire_progress;
            damage.mobility_capability -= 0.0018 * flooding_progress;
            damage.survivability_margin -= 0.0022 * flooding_progress + 0.0010 * fire_progress;

            sync_platform_damage_loss_state(health, damage);

            if (Propulsion* propulsion = e.get_mut<Propulsion>()) {
                const double mobility_scale = std::clamp(damage.mobility_capability, 0.2, 1.0);
                propulsion->mil_thrust_n = std::min(propulsion->mil_thrust_n, ship.max_speed_mps * 100000.0 * mobility_scale);
                propulsion->ab_thrust_n = std::min(propulsion->ab_thrust_n, ship.max_speed_mps * 120000.0 * mobility_scale);
            }

            if (damage.loss_state == PlatformLossState::Lost) {
                health.current_hp = 0.0;
                e.destruct();
            }
        });
}
