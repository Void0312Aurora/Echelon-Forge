#include "simulation_kernel.h"
#include "simulation_kernel_engagement_event_store.h"

#include "components/basic/common.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/combat/common/weapon_common.h"
#include "core/interfaces/engagement_effects_event_builder.h"
#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <limits>
#include <cmath>
#include <string>
#include <utility>

namespace {

Transform local_body_point_to_world_transform(const Transform &target_transform,
                                              double local_forward_m, double local_right_m,
                                              double local_up_m) {
    const Math::Vector3 world_delta =
        Math::body_to_world({local_forward_m, -local_right_m, local_up_m}, target_transform);
    return {
        target_transform.x + world_delta.x,
        target_transform.y + world_delta.y,
        target_transform.z + world_delta.z,
        target_transform.heading,
        target_transform.pitch,
        target_transform.roll,
    };
}

std::array<double, 3> world_point_to_local_body(const Transform &target_transform, double world_x,
                                                double world_y, double world_z) {
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

std::array<double, 3> velocity_axis_in_target_body(const Transform &target_transform, double vx,
                                                   double vy, double vz) {
    const double norm = std::sqrt(vx * vx + vy * vy + vz * vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity =
        world_point_to_local_body(target_transform, target_transform.x + vx,
                                  target_transform.y + vy, target_transform.z + vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

double resolve_closure_from_impact(const Transform &target_transform,
                                   const Transform &impact_transform,
                                   const Velocity *target_velocity, double missile_vx,
                                   double missile_vy, double missile_vz) {
    const double target_vx = target_velocity ? target_velocity->vx : 0.0;
    const double target_vy = target_velocity ? target_velocity->vy : 0.0;
    const double target_vz = target_velocity ? target_velocity->vz : 0.0;
    const double rel_vx = target_vx - missile_vx;
    const double rel_vy = target_vy - missile_vy;
    const double rel_vz = target_vz - missile_vz;
    const double dx = target_transform.x - impact_transform.x;
    const double dy = target_transform.y - impact_transform.y;
    const double dz = target_transform.z - impact_transform.z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return std::sqrt(rel_vx * rel_vx + rel_vy * rel_vy + rel_vz * rel_vz);
    }
    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

double local_miss_distance_m(double local_forward_m, double local_right_m, double local_up_m) {
    return std::sqrt(local_forward_m * local_forward_m + local_right_m * local_right_m +
                     local_up_m * local_up_m);
}

struct DebugEffectsDamageEventRecordInput {
    uint64_t munition_entity_id;
    uint64_t target_id;
    const EngagementDamageStateSnapshot &before;
    const EngagementDamageStateSnapshot &after;
    const Missile &synthetic_missile;
    const EffectsResult &effects_result;
    const Transform &detonation_transform;
    std::array<double, 3> detonation_local;
    std::array<double, 3> missile_axis;
    const char *trigger_type;
    double event_time_s;
    double fuse_distance_m;
    double closure_mps;
    bool use_profiled_warhead_fields;
};

EngagementEffectsDamageEventRecord
build_debug_effects_damage_event_record(const DebugEffectsDamageEventRecordInput &input) {
    EngagementEffectsDamageEventRecord event_record{};
    event_record.munition_entity_id = input.munition_entity_id;
    event_record.target_id = input.target_id;
    event_record.before = input.before;
    event_record.after = input.after;

    EffectsEvent &effects = event_record.effects;
    effects.trigger_type = input.trigger_type;
    effects.outcome_state = "hit";
    effects.detonation_time_s = input.event_time_s;
    effects.nearest_approach_time_s = input.event_time_s;
    effects.miss_distance_m = local_miss_distance_m(
        input.detonation_local[0], input.detonation_local[1], input.detonation_local[2]);
    effects.detonation_local_forward_m = input.detonation_local[0];
    effects.detonation_local_right_m = input.detonation_local[1];
    effects.detonation_local_up_m = input.detonation_local[2];
    effects.detonation_heading_deg = input.detonation_transform.heading;
    effects.detonation_pitch_deg = input.detonation_transform.pitch;
    effects.detonation_roll_deg = input.detonation_transform.roll;
    effects.closure_mps = input.closure_mps;
    effects.missile_axis_forward = input.missile_axis[0];
    effects.missile_axis_right = input.missile_axis[1];
    effects.missile_axis_up = input.missile_axis[2];
    effects.quality = 1.0;
    effects.confidence = 1.0;
    effects.effect_family = warhead_effect_family(input.synthetic_missile.warhead_profile);
    if (input.use_profiled_warhead_fields) {
        effects.warhead_mass_kg = std::isfinite(input.synthetic_missile.warhead_profile.mass_kg)
                                      ? input.synthetic_missile.warhead_profile.mass_kg
                                      : 0.0;
        effects.warhead_lethal_radius_m =
            std::isfinite(input.synthetic_missile.warhead_profile.lethal_radius_m)
                ? input.synthetic_missile.warhead_profile.lethal_radius_m
                : input.fuse_distance_m;
        effects.warhead_profile_synthetic = input.synthetic_missile.warhead_profile.synthetic;
        effects.damage_scalar_synthetic =
            input.synthetic_missile.warhead_profile.damage_scalar_synthetic;
    } else {
        effects.warhead_lethal_radius_m = input.fuse_distance_m;
        effects.warhead_profile_synthetic = true;
        effects.damage_scalar_synthetic = true;
    }
    effects.fuze_type = fuze_profile_type(input.synthetic_missile.fuze_profile);
    effects.fuze_trigger_radius_m = input.synthetic_missile.fuze_profile.trigger_radius_m;
    effects.fuze_delay_s = input.synthetic_missile.fuze_profile.delay_s;
    effects.fuze_reliability = input.synthetic_missile.fuze_profile.reliability;
    effects.fuze_profile_synthetic = input.synthetic_missile.fuze_profile.synthetic;
    effects.fuze_signature_source = "debug";
    effects.fuze_signature_scale = 1.0;
    effects.fuze_effective_reliability = input.synthetic_missile.fuze_profile.reliability;
    engagement_events::apply_effects_result_fields(effects, input.effects_result);
    return event_record;
}

} // namespace

bool SimulationKernel::debug_apply_proximity_hit(uint64_t attacker_id, uint64_t target_id,
                                                 double damage, double fuse_distance) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform *target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef *effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before =
        engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile =
        make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile =
        make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const KeyEntity *target_key = target.get<KeyEntity>();
    const bool structured_air_target =
        target_key &&
        (target_key->type == UnitType::Aircraft || target_key->type == UnitType::C2Node) &&
        target.get<HitboxConfig>() != nullptr && target.get<SystemHealth>() != nullptr &&
        target.get<PlatformDamageState>() != nullptr;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform, 0.0, 0.0, structured_air_target ? 0.0 : 2.0);

    auto impact =
        ecs.entity().set<Transform>(impact_transform).set<Missile>(synthetic).add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after =
        engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t *info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(*target_transform, impact_transform.x,
                                                            impact_transform.y, impact_transform.z);
    EngagementEffectsDamageEventRecord event_record = build_debug_effects_damage_event_record({
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        synthetic,
        effects_result,
        impact_transform,
        detonation_local,
        {0.0, 0.0, 0.0},
        "debug_proximity_hit",
        current_time,
        fuse_distance,
        0.0,
        false,
    });
    (void)engagement_event_store_->record_effects_damage_event(std::move(event_record));
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_local_proximity_hit(uint64_t attacker_id, uint64_t target_id,
                                                       double local_forward_m, double local_right_m,
                                                       double local_up_m, double damage,
                                                       double fuse_distance) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform *target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef *effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before =
        engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile =
        make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile =
        make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform, local_forward_m, local_right_m, local_up_m);
    auto impact =
        ecs.entity().set<Transform>(impact_transform).set<Missile>(synthetic).add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after =
        engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t *info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(*target_transform, impact_transform.x,
                                                            impact_transform.y, impact_transform.z);
    EngagementEffectsDamageEventRecord event_record = build_debug_effects_damage_event_record({
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        synthetic,
        effects_result,
        impact_transform,
        detonation_local,
        {0.0, 0.0, 0.0},
        "debug_local_proximity_hit",
        current_time,
        fuse_distance,
        0.0,
        false,
    });
    (void)engagement_event_store_->record_effects_damage_event(std::move(event_record));
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit(
    uint64_t attacker_id, uint64_t target_id, double local_forward_m, double local_right_m,
    double local_up_m, const WarheadProfile &warhead_profile) {
    return debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id, target_id, local_forward_m, local_right_m, local_up_m, warhead_profile, 0.0,
        0.0, 0.0);
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity(
    uint64_t attacker_id, uint64_t target_id, double local_forward_m, double local_right_m,
    double local_up_m, const WarheadProfile &warhead_profile, double missile_vx_mps,
    double missile_vy_mps, double missile_vz_mps) {
    const auto target = ecs.entity(target_id);
    const Transform *target_transform = target.is_alive() ? target.get<Transform>() : nullptr;
    return debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
        attacker_id, target_id, local_forward_m, local_right_m, local_up_m, warhead_profile,
        missile_vx_mps, missile_vy_mps, missile_vz_mps,
        target_transform ? target_transform->heading : 0.0,
        target_transform ? target_transform->pitch : 0.0,
        target_transform ? target_transform->roll : 0.0);
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
    uint64_t attacker_id, uint64_t target_id, double local_forward_m, double local_right_m,
    double local_up_m, const WarheadProfile &warhead_profile, double missile_vx_mps,
    double missile_vy_mps, double missile_vz_mps, double detonation_heading_deg,
    double detonation_pitch_deg, double detonation_roll_deg) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_alive() || !target.is_alive()) {
        return false;
    }

    const Transform *target_transform_component = target.get<Transform>();
    if (!target_transform_component) {
        return false;
    }
    const Transform target_transform = *target_transform_component;
    const Velocity *target_velocity_component = target.get<Velocity>();
    const Velocity target_velocity_snapshot =
        target_velocity_component ? *target_velocity_component : Velocity{};
    const Velocity *target_velocity =
        target_velocity_component ? &target_velocity_snapshot : nullptr;

    const EffectsModelRef *effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const double damage =
        std::isfinite(warhead_profile.damage_scalar) ? warhead_profile.damage_scalar : 180.0;
    const double fuse_distance =
        std::isfinite(warhead_profile.lethal_radius_m) ? warhead_profile.lethal_radius_m : 80.0;
    WarheadProfile resolved_profile = warhead_profile;
    if (!std::isfinite(resolved_profile.damage_scalar)) {
        resolved_profile.damage_scalar = damage;
        resolved_profile.damage_scalar_synthetic = true;
    }
    if (!std::isfinite(resolved_profile.lethal_radius_m)) {
        resolved_profile.lethal_radius_m = fuse_distance;
    }

    const EngagementDamageStateSnapshot before =
        engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile = resolved_profile;
    synthetic.fuze_profile =
        make_synthetic_fuze_profile(fuse_distance, "debug_profiled_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        target_transform, local_forward_m, local_right_m, local_up_m);
    Transform detonation_transform = impact_transform;
    detonation_transform.heading = detonation_heading_deg;
    detonation_transform.pitch = detonation_pitch_deg;
    detonation_transform.roll = detonation_roll_deg;
    auto impact = ecs.entity()
                      .set<Transform>(detonation_transform)
                      .set<Velocity>({missile_vx_mps, missile_vy_mps, missile_vz_mps})
                      .set<Missile>(synthetic)
                      .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after =
        engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t *info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(target_transform, impact_transform.x,
                                                            impact_transform.y, impact_transform.z);
    const auto missile_axis = velocity_axis_in_target_body(target_transform, missile_vx_mps,
                                                           missile_vy_mps, missile_vz_mps);
    const double closure_mps =
        resolve_closure_from_impact(target_transform, impact_transform, target_velocity,
                                    missile_vx_mps, missile_vy_mps, missile_vz_mps);
    EngagementEffectsDamageEventRecord event_record = build_debug_effects_damage_event_record({
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        synthetic,
        effects_result,
        detonation_transform,
        detonation_local,
        missile_axis,
        "debug_profiled_local_proximity_hit",
        current_time,
        fuse_distance,
        closure_mps,
        true,
    });
    (void)engagement_event_store_->record_effects_damage_event(std::move(event_record));
    impact.destruct();
    return true;
}
