#pragma once

#include <flecs.h>
#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cmath>
#include <limits>
#include <string>
#include <utility>
#include <spdlog/spdlog.h>

#include "components/basic/common.h"
#include "components/command/legacy_command_bridge.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/combat/common/weapon_common.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/ew.h"
#include "core/interfaces/engagement_effects_event_builder.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/effects_model.h"

namespace {
inline uint64_t damage_splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

inline double damage_rand_uniform01(uint64_t &state) {
    state = damage_splitmix64(state);
    return (state >> 11) * (1.0 / 9007199254740992.0);
}

inline bool proximity_fuze_has_terminal_guidance_support(const Missile &missile) {
    if (missile.seeker_has_valid_track) {
        return true;
    }
    if (!missile.terminal_seeker_active) {
        return false;
    }
    return missile.seeker_mode == 1;
}

inline std::string damage_lower_ascii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return value;
}

inline std::string damage_resolved_fuze_type(const Missile &missile) {
    const std::string raw = damage_lower_ascii(fuze_profile_type(missile.fuze_profile));
    if (raw == "contact" || raw == "impact") {
        return "contact";
    }
    if (raw == "radarproximity" || raw == "radar_proximity" || raw == "rfproximity" ||
        raw == "rf_proximity") {
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

inline bool damage_fuze_is_contact(const std::string &fuze_type) {
    return fuze_type == "contact";
}

inline bool damage_fuze_is_timed(const std::string &fuze_type) {
    return fuze_type == "timed";
}

struct DamageFuzeSignatureEvidence {
    std::string source = "none";
    double target_signature = 0.0;
    double signature_scale = 1.0;
    double effective_reliability = 1.0;
};

inline double damage_target_rcs_from_aspect(const RCSProfile *rcs,
                                            const Transform &target_transform,
                                            const Transform &observer_transform) {
    if (!rcs) {
        return 5.0;
    }

    constexpr double kPi = 3.14159265358979323846;
    const double los_math_deg = std::atan2(observer_transform.y - target_transform.y,
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

inline double damage_target_projected_size_signature(const HitboxConfig *hitboxes) {
    if (!hitboxes || hitboxes->hitboxes.empty()) {
        return 5.0;
    }

    double max_cross_section_m2 = 0.0;
    for (const Hitbox &box : hitboxes->hitboxes) {
        const double forward_area = std::max(0.0, box.dim_w * box.dim_h);
        const double side_area = std::max(0.0, box.dim_l * box.dim_h);
        const double plan_area = std::max(0.0, box.dim_l * box.dim_w);
        max_cross_section_m2 =
            std::max(max_cross_section_m2, std::max({forward_area, side_area, plan_area}));
    }
    return std::max(0.1, max_cross_section_m2);
}

inline DamageFuzeSignatureEvidence
damage_fuze_signature_evidence(const std::string &fuze_type, const Transform &missile_transform,
                               const Transform &target_transform, const RCSProfile *target_rcs,
                               const HitboxConfig *target_hitboxes, double fuze_reliability) {
    DamageFuzeSignatureEvidence evidence{};
    evidence.effective_reliability = std::clamp(fuze_reliability, 0.0, 1.0);

    if (fuze_type == "radar_proximity") {
        const double rcs_m2 =
            damage_target_rcs_from_aspect(target_rcs, target_transform, missile_transform);
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

    evidence.effective_reliability =
        std::clamp(fuze_reliability * evidence.signature_scale, 0.0, 1.0);
    return evidence;
}

inline std::string damage_fuze_trigger_type(const Missile &missile) {
    const std::string fuze_type = damage_resolved_fuze_type(missile);
    if (damage_fuze_is_contact(fuze_type)) {
        return "contact_fuze";
    }
    if (damage_fuze_is_timed(fuze_type)) {
        return "timed_fuze";
    }
    return "proximity_fuze";
}

inline double damage_contact_fuze_surface_tolerance_m(const Missile &missile) {
    const double authored_trigger = missile.fuze_profile.trigger_radius_m;
    if (std::isfinite(authored_trigger) && authored_trigger > 0.0 && authored_trigger <= 2.0) {
        return authored_trigger;
    }
    return 0.25;
}

inline std::array<double, 3> damage_world_point_to_local_body(const Transform &target_transform,
                                                              double world_x, double world_y,
                                                              double world_z);

inline std::array<double, 3> damage_local_body_point_to_world(const Transform &target_transform,
                                                              double local_forward_m,
                                                              double local_right_m,
                                                              double local_up_m);

inline double damage_hitbox_surface_distance_local(const std::array<double, 3> &local_point,
                                                   const Hitbox &box) {
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

inline bool damage_point_inside_hitbox_local(const std::array<double, 3> &local_point,
                                             const Hitbox &box) {
    return local_point[0] >= box.offset_x - box.dim_l * 0.5 &&
           local_point[0] <= box.offset_x + box.dim_l * 0.5 &&
           local_point[1] >= box.offset_y - box.dim_w * 0.5 &&
           local_point[1] <= box.offset_y + box.dim_w * 0.5 &&
           local_point[2] >= box.offset_z - box.dim_h * 0.5 &&
           local_point[2] <= box.offset_z + box.dim_h * 0.5;
}

inline double damage_hitbox_penetration_depth_local(const std::array<double, 3> &local_point,
                                                    const Hitbox &box) {
    if (!damage_point_inside_hitbox_local(local_point, box)) {
        return 0.0;
    }
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;
    return std::max(0.0, std::min({
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

inline DamageContactFuzeEvidence damage_contact_fuze_evidence(const Transform &target_transform,
                                                              double world_x, double world_y,
                                                              double world_z,
                                                              const HitboxConfig *hitboxes) {
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
    for (const auto &box : hitboxes->hitboxes) {
        min_surface_distance_m = std::min(min_surface_distance_m,
                                          damage_hitbox_surface_distance_local(local_point, box));
        if (damage_point_inside_hitbox_local(local_point, box)) {
            inside_hitbox = true;
            max_penetration_depth_m = std::max(
                max_penetration_depth_m, damage_hitbox_penetration_depth_local(local_point, box));
        }
    }

    evidence.surface_distance_m =
        std::isfinite(min_surface_distance_m) ? min_surface_distance_m : 0.0;
    evidence.penetration_depth_m = max_penetration_depth_m;
    evidence.inside_hitbox = inside_hitbox;
    return evidence;
}

inline double damage_target_surface_distance_m(const Transform &target_transform, double world_x,
                                               double world_y, double world_z,
                                               const HitboxConfig *hitboxes) {
    if (!hitboxes || hitboxes->hitboxes.empty()) {
        const double dx = world_x - target_transform.x;
        const double dy = world_y - target_transform.y;
        const double dz = world_z - target_transform.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    const auto local_point =
        damage_world_point_to_local_body(target_transform, world_x, world_y, world_z);
    double min_surface_distance_m = std::numeric_limits<double>::infinity();
    for (const auto &box : hitboxes->hitboxes) {
        min_surface_distance_m = std::min(min_surface_distance_m,
                                          damage_hitbox_surface_distance_local(local_point, box));
    }
    return min_surface_distance_m;
}

inline void sync_platform_damage_loss_state(Health &health, PlatformDamageState &damage,
                                            bool force_lost = false) {
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

inline bool engagement_damage_snapshot_changed(const EngagementDamageStateSnapshot &before,
                                               const EngagementDamageStateSnapshot &after) {
    constexpr double epsilon = 1.0e-6;
    return before.entity_active != after.entity_active ||
           std::abs(before.hp - after.hp) > epsilon ||
           std::abs(before.mission_capability - after.mission_capability) > epsilon ||
           std::abs(before.mobility_capability - after.mobility_capability) > epsilon ||
           std::abs(before.sensor_capability - after.sensor_capability) > epsilon ||
           std::abs(before.survivability_margin - after.survivability_margin) > epsilon ||
           before.mission_kill != after.mission_kill ||
           before.mobility_kill != after.mobility_kill || before.sensor_kill != after.sensor_kill ||
           before.forced_landing != after.forced_landing ||
           before.flight_control_kill != after.flight_control_kill ||
           before.propulsion_kill != after.propulsion_kill || before.crew_kill != after.crew_kill ||
           before.loss_state != after.loss_state;
}

inline std::array<double, 3> damage_world_point_to_local_body(const Transform &target_transform,
                                                              double world_x, double world_y,
                                                              double world_z) {
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

inline std::array<double, 3> damage_local_body_point_to_world(const Transform &target_transform,
                                                              double local_forward_m,
                                                              double local_right_m,
                                                              double local_up_m) {
    const Math::Vector3 world_delta =
        Math::body_to_world({local_forward_m, -local_right_m, local_up_m}, target_transform);
    return {
        target_transform.x + world_delta.x,
        target_transform.y + world_delta.y,
        target_transform.z + world_delta.z,
    };
}

inline bool damage_has_proximity_min_local_point(const Missile &missile) {
    return std::isfinite(missile.proximity_min_local_forward_m) &&
           std::isfinite(missile.proximity_min_local_right_m) &&
           std::isfinite(missile.proximity_min_local_up_m);
}

inline void damage_record_proximity_min_point(Missile &missile, const Transform &target_transform,
                                              const Transform &missile_transform,
                                              double current_time, double distance_m) {
    missile.proximity_min_dist_m = distance_m;
    missile.proximity_min_time_s = current_time;
    const auto local_point = damage_world_point_to_local_body(
        target_transform, missile_transform.x, missile_transform.y, missile_transform.z);
    missile.proximity_min_local_forward_m = local_point[0];
    missile.proximity_min_local_right_m = local_point[1];
    missile.proximity_min_local_up_m = local_point[2];
}

inline std::array<double, 3>
damage_effective_detonation_world_point(const Missile &missile, const Transform &target_transform,
                                        const Transform &fallback_missile_transform,
                                        bool contact_fuze, bool timed_fuze) {
    if (!contact_fuze && !timed_fuze && damage_has_proximity_min_local_point(missile)) {
        return damage_local_body_point_to_world(
            target_transform, missile.proximity_min_local_forward_m,
            missile.proximity_min_local_right_m, missile.proximity_min_local_up_m);
    }

    if (std::isfinite(missile.fuze_detonation_x) && std::isfinite(missile.fuze_detonation_y) &&
        std::isfinite(missile.fuze_detonation_z)) {
        return {
            missile.fuze_detonation_x,
            missile.fuze_detonation_y,
            missile.fuze_detonation_z,
        };
    }

    return {
        fallback_missile_transform.x,
        fallback_missile_transform.y,
        fallback_missile_transform.z,
    };
}

inline std::array<double, 3> damage_velocity_axis_in_target_body(const Transform &target_transform,
                                                                 const Velocity *missile_velocity) {
    if (!missile_velocity) {
        return {0.0, 0.0, 0.0};
    }
    const double norm = std::sqrt(missile_velocity->vx * missile_velocity->vx +
                                  missile_velocity->vy * missile_velocity->vy +
                                  missile_velocity->vz * missile_velocity->vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity = damage_world_point_to_local_body(
        target_transform, target_transform.x + missile_velocity->vx,
        target_transform.y + missile_velocity->vy, target_transform.z + missile_velocity->vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

inline double damage_closure_mps(const Transform &missile_transform,
                                 const Transform &target_transform,
                                 const Velocity *missile_velocity,
                                 const Velocity *target_velocity) {
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

inline std::string damage_nearest_approach_aspect_bucket(double local_forward_m,
                                                         double local_right_m) {
    if (!std::isfinite(local_forward_m) || !std::isfinite(local_right_m)) {
        return "unknown";
    }
    if (std::abs(local_forward_m) >= std::abs(local_right_m)) {
        return local_forward_m >= 0.0 ? "nose" : "tail";
    }
    return "beam";
}

inline void damage_record_nearest_approach_event(flecs::entity munition_entity,
                                                 const Missile &missile,
                                                 const EngagementEventRecorderRef *recorder_ref,
                                                 const std::string &reason, double current_time,
                                                 double nearest_approach_time_s,
                                                 double miss_distance_m, double closure_mps) {
    if (!recorder_ref || !recorder_ref->recorder) {
        return;
    }
    if (!std::isfinite(miss_distance_m) || !damage_has_proximity_min_local_point(missile)) {
        return;
    }

    NearestApproachEvent event{};
    event.header.stage = "nearest_approach";
    event.header.status = "observed";
    event.header.reason = reason;
    event.header.source_time_s =
        std::isfinite(nearest_approach_time_s) ? nearest_approach_time_s : current_time;
    event.header.fidelity_mode = "runtime";
    event.header.evidence_level = "observed_runtime";
    event.header.confidence = 1.0;
    event.nearest_approach_time_s = event.header.source_time_s;
    event.miss_distance_m = miss_distance_m;
    event.local_forward_m = missile.proximity_min_local_forward_m;
    event.local_right_m = missile.proximity_min_local_right_m;
    event.local_up_m = missile.proximity_min_local_up_m;
    event.closure_mps = closure_mps;
    event.aspect_bucket =
        damage_nearest_approach_aspect_bucket(event.local_forward_m, event.local_right_m);

    EngagementNearestApproachEventRecord record{};
    record.munition_entity_id = static_cast<std::uint64_t>(munition_entity.id());
    record.shooter_id = missile.attacker_id;
    record.target_id = missile.target_id;
    record.event = std::move(event);
    (void)recorder_ref->recorder->record_nearest_approach_event(std::move(record));
}

inline void damage_record_fuze_evaluation_event(
    flecs::entity munition_entity, const Missile &missile,
    const EngagementEventRecorderRef *recorder_ref, const std::string &reason, bool armed,
    bool triggered, double current_time, double delay_s, double reliability, double sample,
    double trigger_radius_m, bool contact_fuze, const DamageContactFuzeEvidence &contact_evidence,
    bool direct_hitbox_intersection = false) {
    if (!recorder_ref || !recorder_ref->recorder) {
        return;
    }

    FuzeEvaluationEvent event{};
    event.header.stage = "fuze_evaluation";
    event.header.status = "evaluated";
    event.header.reason = reason;
    event.header.source_time_s = current_time;
    event.header.fidelity_mode = "runtime";
    event.header.evidence_level = "observed_runtime";
    event.header.confidence = 1.0;
    event.fuze_type = fuze_profile_type(missile.fuze_profile);
    event.armed = armed;
    event.triggered = triggered;
    event.failure_reason = triggered ? "" : reason;
    event.delay_s = std::max(0.0, delay_s);
    event.reliability = std::clamp(reliability, 0.0, 1.0);
    event.sample = std::clamp(sample, 0.0, 1.0);
    event.trigger_radius_m = trigger_radius_m;
    event.contact_surface_distance_m = contact_fuze ? contact_evidence.surface_distance_m : 0.0;
    event.contact_penetration_depth_m = contact_fuze ? contact_evidence.penetration_depth_m : 0.0;
    event.contact_surface_tolerance_m =
        contact_fuze ? damage_contact_fuze_surface_tolerance_m(missile) : 0.0;
    event.contact_inside_hitbox = contact_fuze && contact_evidence.inside_hitbox;
    event.direct_hitbox_intersection = direct_hitbox_intersection;

    EngagementFuzeEvaluationEventRecord record{};
    record.munition_entity_id = static_cast<std::uint64_t>(munition_entity.id());
    record.shooter_id = missile.attacker_id;
    record.target_id = missile.target_id;
    record.event = std::move(event);
    (void)recorder_ref->recorder->record_fuze_evaluation_event(std::move(record));
}

inline void damage_record_fuze_no_detonation_event(
    flecs::entity munition_entity, const Missile &missile, const Transform &target_transform,
    const Transform &missile_transform, const EngagementEventRecorderRef *recorder_ref,
    const std::string &trigger_type, const std::string &outcome_state, double current_time,
    double nearest_approach_time_s, double miss_distance_m, double trigger_radius_m, double quality,
    double confidence, const DamageFuzeSignatureEvidence &fuze_signature, bool contact_fuze,
    const DamageContactFuzeEvidence &contact_evidence, double closure_mps,
    const std::array<double, 3> &missile_axis) {
    if (!recorder_ref || !recorder_ref->recorder) {
        return;
    }

    const EngagementDamageStateSnapshot snapshot =
        recorder_ref->recorder->capture_engagement_damage_state(missile.target_id);
    const bool timed_fuze = false;
    const auto event_world = damage_effective_detonation_world_point(
        missile, target_transform, missile_transform, contact_fuze, timed_fuze);
    const auto event_local = damage_world_point_to_local_body(target_transform, event_world[0],
                                                              event_world[1], event_world[2]);
    const double fuze_reliability = std::clamp(missile.fuze_profile.reliability, 0.0, 1.0);

    EngagementEffectsDamageEventRecord event_record{};
    event_record.munition_entity_id = static_cast<std::uint64_t>(munition_entity.id());
    event_record.target_id = missile.target_id;
    event_record.before = snapshot;
    event_record.after = snapshot;
    EffectsEvent &effects = event_record.effects;
    effects.trigger_type = trigger_type;
    effects.outcome_state = outcome_state;
    effects.detonation_time_s = current_time;
    effects.nearest_approach_time_s =
        std::isfinite(nearest_approach_time_s) ? nearest_approach_time_s : current_time;
    effects.miss_distance_m = miss_distance_m;
    effects.detonation_local_forward_m = event_local[0];
    effects.detonation_local_right_m = event_local[1];
    effects.detonation_local_up_m = event_local[2];
    effects.detonation_heading_deg = missile_transform.heading;
    effects.detonation_pitch_deg = missile_transform.pitch;
    effects.detonation_roll_deg = missile_transform.roll;
    effects.closure_mps = closure_mps;
    effects.missile_axis_forward = missile_axis[0];
    effects.missile_axis_right = missile_axis[1];
    effects.missile_axis_up = missile_axis[2];
    effects.quality = quality;
    effects.confidence = confidence;
    effects.effect_family = warhead_effect_family(missile.warhead_profile);
    effects.warhead_mass_kg =
        std::isfinite(missile.warhead_profile.mass_kg) ? missile.warhead_profile.mass_kg : 0.0;
    effects.warhead_lethal_radius_m = std::isfinite(missile.warhead_profile.lethal_radius_m)
                                          ? missile.warhead_profile.lethal_radius_m
                                          : missile.fuse_distance;
    effects.warhead_profile_synthetic = missile.warhead_profile.synthetic;
    effects.damage_scalar_synthetic = missile.warhead_profile.damage_scalar_synthetic;
    effects.fuze_type = fuze_profile_type(missile.fuze_profile);
    effects.fuze_trigger_radius_m = trigger_radius_m;
    effects.fuze_delay_s = std::max(0.0, missile.fuze_profile.delay_s);
    effects.fuze_reliability = fuze_reliability;
    effects.fuze_profile_synthetic = missile.fuze_profile.synthetic;
    effects.fuze_signature_source = fuze_signature.source;
    effects.fuze_target_signature = fuze_signature.target_signature;
    effects.fuze_signature_scale = fuze_signature.signature_scale;
    effects.fuze_effective_reliability = fuze_signature.effective_reliability;
    effects.fuze_contact_surface_distance_m =
        contact_fuze ? contact_evidence.surface_distance_m : 0.0;
    effects.fuze_contact_penetration_depth_m =
        contact_fuze ? contact_evidence.penetration_depth_m : 0.0;
    effects.fuze_contact_surface_tolerance_m =
        contact_fuze ? damage_contact_fuze_surface_tolerance_m(missile) : 0.0;
    effects.fuze_contact_inside_hitbox = contact_fuze && contact_evidence.inside_hitbox;
    (void)recorder_ref->recorder->record_effects_damage_event(std::move(event_record));
}
} // namespace

inline void register_damage_system_common(flecs::world &ecs) {
    ecs.system<Transform, Missile>("ProximityFuze").kind(flecs::OnUpdate).run([](flecs::iter &it) {
        while (it.next()) {
            auto p = it.field<Transform>(0);
            auto m = it.field<Missile>(1);
            const EffectsModelRef *effects_ref = it.world().get<EffectsModelRef>();
            const EngagementEventRecorderRef *recorder_ref =
                it.world().get<EngagementEventRecorderRef>();
            const ecs_world_info_t *world_info = ecs_get_world_info(it.world().c_ptr());
            const double current_time =
                world_info ? static_cast<double>(world_info->world_time_total) : 0.0;

            for (auto i : it) {
                if (!m[i].active) continue;

                auto target_entity = it.world().entity(m[i].target_id);
                if (!target_entity.is_valid()) {
                    it.entity(i).destruct();
                    continue;
                }

                const Transform *t_pos = target_entity.get<Transform>();
                if (!t_pos) continue;

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
                        spdlog::warn(
                            "Effects model not configured; skipping delayed fuze resolution.");
                        it.entity(i).destruct();
                        continue;
                    }

                    const double trigger_radius_m =
                        std::isfinite(m[i].fuze_profile.trigger_radius_m)
                            ? m[i].fuze_profile.trigger_radius_m
                            : m[i].fuse_distance;
                    const double fuze_reliability =
                        std::clamp(m[i].fuze_profile.reliability, 0.0, 1.0);
                    const auto detonation_world = damage_effective_detonation_world_point(
                        m[i], *t_pos, p[i], contact_fuze, timed_fuze);
                    p[i].x = detonation_world[0];
                    p[i].y = detonation_world[1];
                    p[i].z = detonation_world[2];
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
                        before =
                            recorder_ref->recorder->capture_engagement_damage_state(m[i].target_id);
                    }
                    const EffectsResult effects_result = effects_ref->model->on_proximity_hit(
                        it.world(), it.entity(i), effective, target_entity);
                    if (can_record_damage) {
                        const EngagementDamageStateSnapshot after =
                            recorder_ref->recorder->capture_engagement_damage_state(m[i].target_id);
                        const double detonation_time_s = std::isfinite(m[i].fuze_detonation_time_s)
                                                             ? m[i].fuze_detonation_time_s
                                                             : current_time;
                        const auto detonation_local =
                            damage_world_point_to_local_body(*t_pos, p[i].x, p[i].y, p[i].z);
                        EngagementEffectsDamageEventRecord event_record{};
                        event_record.munition_entity_id =
                            static_cast<std::uint64_t>(it.entity(i).id());
                        event_record.target_id = m[i].target_id;
                        event_record.before = before;
                        event_record.after = after;
                        EffectsEvent &effects = event_record.effects;
                        effects.trigger_type = trigger_type;
                        effects.outcome_state = engagement_damage_snapshot_changed(before, after)
                                                    ? "damage_applied"
                                                    : "detonated_no_effect";
                        effects.detonation_time_s = detonation_time_s;
                        effects.nearest_approach_time_s =
                            std::isfinite(m[i].fuze_nearest_approach_time_s)
                                ? m[i].fuze_nearest_approach_time_s
                                : detonation_time_s;
                        effects.miss_distance_m = m[i].proximity_min_dist_m;
                        effects.detonation_local_forward_m = detonation_local[0];
                        effects.detonation_local_right_m = detonation_local[1];
                        effects.detonation_local_up_m = detonation_local[2];
                        effects.detonation_heading_deg = p[i].heading;
                        effects.detonation_pitch_deg = p[i].pitch;
                        effects.detonation_roll_deg = p[i].roll;
                        effects.closure_mps = m[i].fuze_closure_mps;
                        effects.missile_axis_forward = m[i].fuze_missile_axis_forward;
                        effects.missile_axis_right = m[i].fuze_missile_axis_right;
                        effects.missile_axis_up = m[i].fuze_missile_axis_up;
                        effects.quality = m[i].fuze_quality;
                        effects.confidence = m[i].fuze_hit_probability;
                        effects.effect_family = warhead_effect_family(effective.warhead_profile);
                        effects.warhead_mass_kg = std::isfinite(effective.warhead_profile.mass_kg)
                                                      ? effective.warhead_profile.mass_kg
                                                      : 0.0;
                        effects.warhead_lethal_radius_m =
                            std::isfinite(effective.warhead_profile.lethal_radius_m)
                                ? effective.warhead_profile.lethal_radius_m
                                : effective.fuse_distance;
                        effects.warhead_profile_synthetic = effective.warhead_profile.synthetic;
                        effects.damage_scalar_synthetic =
                            effective.warhead_profile.damage_scalar_synthetic;
                        effects.fuze_type = fuze_profile_type(effective.fuze_profile);
                        effects.fuze_trigger_radius_m = trigger_radius_m;
                        effects.fuze_delay_s = std::max(0.0, effective.fuze_profile.delay_s);
                        effects.fuze_reliability = fuze_reliability;
                        effects.fuze_profile_synthetic = effective.fuze_profile.synthetic;
                        effects.fuze_signature_source = m[i].fuze_signature_source;
                        effects.fuze_target_signature = m[i].fuze_target_signature;
                        effects.fuze_signature_scale = m[i].fuze_signature_scale;
                        effects.fuze_effective_reliability = m[i].fuze_effective_reliability;
                        effects.fuze_contact_surface_distance_m =
                            m[i].fuze_contact_surface_distance_m;
                        effects.fuze_contact_penetration_depth_m =
                            m[i].fuze_contact_penetration_depth_m;
                        effects.fuze_contact_surface_tolerance_m =
                            m[i].fuze_contact_surface_tolerance_m;
                        effects.fuze_contact_inside_hitbox = m[i].fuze_contact_inside_hitbox;
                        engagement_events::apply_effects_result_fields(effects, effects_result);
                        (void)recorder_ref->recorder->record_effects_damage_event(
                            std::move(event_record));
                    }
                    it.entity(i).destruct();
                    continue;
                }

                if (timed_fuze) {
                    const double fuze_delay_s = std::max(0.0, m[i].fuze_profile.delay_s);
                    const double elapsed_s = current_time - m[i].launch_time;
                    if (elapsed_s < fuze_delay_s) {
                        if (dist < m[i].proximity_min_dist_m) {
                            damage_record_proximity_min_point(m[i], *t_pos, p[i], current_time,
                                                              dist);
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

                    const Velocity *missile_velocity = it.entity(i).get<Velocity>();
                    const Velocity *target_velocity = target_entity.get<Velocity>();
                    const auto missile_axis =
                        damage_velocity_axis_in_target_body(*t_pos, missile_velocity);
                    const double closure_mps =
                        damage_closure_mps(p[i], *t_pos, missile_velocity, target_velocity);
                    const double event_closure_mps =
                        std::max(closure_mps, std::max(0.0, m[i].filtered_closing_speed_mps));
                    const double trigger_radius_m =
                        std::isfinite(m[i].fuze_profile.trigger_radius_m)
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
                    damage_record_proximity_min_point(m[i], *t_pos, p[i], current_time, dist);
                    continue;
                }

                if (dist < m[i].proximity_min_dist_m) {
                    damage_record_proximity_min_point(m[i], *t_pos, p[i], current_time, dist);
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

                const HitboxConfig *target_hitboxes = target_entity.get<HitboxConfig>();
                double min_dist = m[i].proximity_min_dist_m;
                const double trigger_radius_m = std::isfinite(m[i].fuze_profile.trigger_radius_m)
                                                    ? m[i].fuze_profile.trigger_radius_m
                                                    : m[i].fuse_distance;
                const double fuze_reliability = std::clamp(m[i].fuze_profile.reliability, 0.0, 1.0);
                double detonation_metric_m = min_dist;
                double effective_trigger_radius_m = trigger_radius_m;
                DamageContactFuzeEvidence contact_evidence{};
                if (contact_fuze) {
                    contact_evidence = damage_contact_fuze_evidence(*t_pos, p[i].x, p[i].y, p[i].z,
                                                                    target_hitboxes);
                    detonation_metric_m = contact_evidence.surface_distance_m;
                    effective_trigger_radius_m = damage_contact_fuze_surface_tolerance_m(m[i]);
                }
                const Velocity *missile_velocity = it.entity(i).get<Velocity>();
                const Velocity *target_velocity = target_entity.get<Velocity>();
                const auto missile_axis =
                    damage_velocity_axis_in_target_body(*t_pos, missile_velocity);
                const double closure_mps =
                    damage_closure_mps(p[i], *t_pos, missile_velocity, target_velocity);
                const double event_closure_mps =
                    std::max(closure_mps, std::max(0.0, m[i].filtered_closing_speed_mps));
                if (detonation_metric_m > effective_trigger_radius_m) {
                    damage_record_nearest_approach_event(
                        it.entity(i), m[i], recorder_ref, "miss_outside_trigger_radius",
                        current_time, m[i].proximity_min_time_s, min_dist, event_closure_mps);
                    damage_record_fuze_evaluation_event(
                        it.entity(i), m[i], recorder_ref, "miss_outside_trigger_radius", false,
                        false, current_time, m[i].fuze_profile.delay_s, fuze_reliability, 1.0,
                        trigger_radius_m, contact_fuze, contact_evidence, false);
                    it.entity(i).destruct();
                    continue;
                }

                double fuse = std::max(1e-6, effective_trigger_radius_m);
                double quality = contact_fuze
                                     ? std::clamp(1.0 - detonation_metric_m / fuse, 0.0, 1.0)
                                     : std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);
                const DamageFuzeSignatureEvidence fuze_signature =
                    contact_fuze
                        ? DamageFuzeSignatureEvidence{"contact_surface", 0.0, 1.0, fuze_reliability}
                        : damage_fuze_signature_evidence(fuze_type, p[i], *t_pos,
                                                         target_entity.get<RCSProfile>(),
                                                         target_hitboxes, fuze_reliability);

                if (!contact_fuze && !proximity_fuze_has_terminal_guidance_support(m[i])) {
                    damage_record_nearest_approach_event(
                        it.entity(i), m[i], recorder_ref, "fuze_no_terminal_track", current_time,
                        m[i].proximity_min_time_s, min_dist, event_closure_mps);
                    damage_record_fuze_evaluation_event(
                        it.entity(i), m[i], recorder_ref, "fuze_no_terminal_track", false, false,
                        current_time, m[i].fuze_profile.delay_s, fuze_reliability, 1.0,
                        trigger_radius_m, contact_fuze, contact_evidence, false);
                    damage_record_fuze_no_detonation_event(
                        it.entity(i), m[i], *t_pos, p[i], recorder_ref, trigger_type,
                        "fuze_no_terminal_track", current_time, m[i].proximity_min_time_s, min_dist,
                        trigger_radius_m, quality, 0.0, fuze_signature, contact_fuze,
                        contact_evidence, event_closure_mps, missile_axis);
                    it.entity(i).destruct();
                    continue;
                }

                const double evasion = resolved_compatibility_damage_evasion(target_entity);

                double base_hit = contact_fuze ? 1.0 : 0.35 + 0.65 * quality;
                double hit_prob = std::clamp(base_hit * fuze_signature.effective_reliability *
                                                 (contact_fuze ? 1.0 : (1.0 - 0.3 * evasion)),
                                             0.0, contact_fuze ? 1.0 : 0.98);
                const double fuze_sample = damage_rand_uniform01(m[i].rng_state);
                if (fuze_sample > hit_prob) {
                    damage_record_nearest_approach_event(
                        it.entity(i), m[i], recorder_ref, "fuze_no_detonation", current_time,
                        m[i].proximity_min_time_s, min_dist, event_closure_mps);
                    damage_record_fuze_evaluation_event(
                        it.entity(i), m[i], recorder_ref, "fuze_no_detonation", true, false,
                        current_time, m[i].fuze_profile.delay_s, hit_prob, fuze_sample,
                        trigger_radius_m, contact_fuze, contact_evidence,
                        contact_fuze && contact_evidence.inside_hitbox);
                    damage_record_fuze_no_detonation_event(
                        it.entity(i), m[i], *t_pos, p[i], recorder_ref, trigger_type,
                        "fuze_no_detonation", current_time, m[i].proximity_min_time_s, min_dist,
                        trigger_radius_m, quality, hit_prob, fuze_signature, contact_fuze,
                        contact_evidence, event_closure_mps, missile_axis);
                    it.entity(i).destruct();
                    continue;
                }

                const double fuze_delay_s = std::max(0.0, m[i].fuze_profile.delay_s);
                damage_record_nearest_approach_event(it.entity(i), m[i], recorder_ref, "fuze_armed",
                                                     current_time, m[i].proximity_min_time_s,
                                                     min_dist, event_closure_mps);
                damage_record_fuze_evaluation_event(
                    it.entity(i), m[i], recorder_ref, "fuze_armed", true, true, current_time,
                    fuze_delay_s, hit_prob, fuze_sample, trigger_radius_m, contact_fuze,
                    contact_evidence, contact_fuze && contact_evidence.inside_hitbox);
                m[i].fuze_delay_armed = true;
                m[i].fuze_nearest_approach_time_s = std::isfinite(m[i].proximity_min_time_s)
                                                        ? m[i].proximity_min_time_s
                                                        : current_time;
                m[i].fuze_detonation_time_s = current_time + fuze_delay_s;
                const auto detonation_world = damage_effective_detonation_world_point(
                    m[i], *t_pos, p[i], contact_fuze, timed_fuze);
                m[i].fuze_detonation_x = detonation_world[0];
                m[i].fuze_detonation_y = detonation_world[1];
                m[i].fuze_detonation_z = detonation_world[2];
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
                m[i].fuze_contact_inside_hitbox = contact_fuze && contact_evidence.inside_hitbox;
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
}
