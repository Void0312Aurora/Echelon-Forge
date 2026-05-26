#include "simulation_kernel.h"

#include "components/basic/common.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <limits>
#include <cmath>
#include <string>

namespace {

EngagementEntityRef engagement_ref(uint64_t entity_id) {
    return EngagementEntityRef{
        .world_index = 0,
        .entity_id = entity_id,
    };
}

std::string loss_state_to_string(PlatformLossState state) {
    switch (state) {
        case PlatformLossState::CombatCapable:
            return "combat_capable";
        case PlatformLossState::MissionKill:
            return "mission_kill";
        case PlatformLossState::MobilityKill:
            return "mobility_kill";
        case PlatformLossState::SensorKill:
            return "sensor_kill";
        case PlatformLossState::Lost:
            return "lost";
    }
    return "unknown";
}

Transform local_body_point_to_world_transform(
    const Transform& target_transform,
    double local_forward_m,
    double local_right_m,
    double local_up_m
) {
    constexpr double kPi = 3.14159265358979323846;
    const double heading_rad = target_transform.heading * kPi / 180.0;
    const double fwd_x = std::sin(heading_rad);
    const double fwd_y = std::cos(heading_rad);
    const double right_x = std::cos(heading_rad);
    const double right_y = -std::sin(heading_rad);
    return {
        target_transform.x + (local_forward_m * fwd_x) + (local_right_m * right_x),
        target_transform.y + (local_forward_m * fwd_y) + (local_right_m * right_y),
        target_transform.z + local_up_m,
        target_transform.heading,
        0.0,
        0.0,
    };
}

std::array<double, 3> world_point_to_local_body(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z
) {
    constexpr double kPi = 3.14159265358979323846;
    const double dx = world_x - target_transform.x;
    const double dy = world_y - target_transform.y;
    const double dz = world_z - target_transform.z;
    const double heading_rad = target_transform.heading * kPi / 180.0;
    const double fwd_x = std::sin(heading_rad);
    const double fwd_y = std::cos(heading_rad);
    const double right_x = std::cos(heading_rad);
    const double right_y = -std::sin(heading_rad);
    return {
        dx * fwd_x + dy * fwd_y,
        dx * right_x + dy * right_y,
        dz,
    };
}

std::array<double, 3> velocity_axis_in_target_body(
    const Transform& target_transform,
    double vx,
    double vy,
    double vz
) {
    const double norm = std::sqrt(vx * vx + vy * vy + vz * vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity = world_point_to_local_body(
        target_transform,
        target_transform.x + vx,
        target_transform.y + vy,
        target_transform.z + vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

double resolve_closure_from_impact(
    const Transform& target_transform,
    const Transform& impact_transform,
    const Velocity* target_velocity,
    double missile_vx,
    double missile_vy,
    double missile_vz
) {
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

double local_miss_distance_m(
    double local_forward_m,
    double local_right_m,
    double local_up_m
) {
    return std::sqrt(
        local_forward_m * local_forward_m +
        local_right_m * local_right_m +
        local_up_m * local_up_m);
}

}  // namespace

EngagementDamageStateSnapshot SimulationKernel::capture_engagement_damage_state(
    uint64_t target_id
) const {
    EngagementDamageStateSnapshot snapshot{};
    const auto target = ecs.entity(target_id);
    snapshot.entity_active = target.is_valid();
    if (!snapshot.entity_active) {
        return snapshot;
    }

    if (const Health* health = target.get<Health>()) {
        snapshot.has_health = true;
        snapshot.hp = health->current_hp;
        snapshot.max_hp = health->max_hp;
        snapshot.mission_kill = health->mission_kill;
        snapshot.mobility_kill = health->mobility_kill;
        snapshot.sensor_kill = health->sensor_kill;
    }

    if (const PlatformDamageState* damage = target.get<PlatformDamageState>()) {
        snapshot.has_platform_damage = true;
        snapshot.mission_capability = damage->mission_capability;
        snapshot.mobility_capability = damage->mobility_capability;
        snapshot.sensor_capability = damage->sensor_capability;
        snapshot.survivability_margin = damage->survivability_margin;
        snapshot.mission_kill = snapshot.mission_kill || damage->mission_kill;
        snapshot.mobility_kill = snapshot.mobility_kill || damage->mobility_kill;
        snapshot.sensor_kill = snapshot.sensor_kill || damage->sensor_kill;
        snapshot.loss_state = loss_state_to_string(damage->loss_state);
    } else if (snapshot.has_health) {
        snapshot.loss_state = snapshot.hp <= 0.0 ? "lost" : "combat_capable";
    }
    return snapshot;
}

std::uint64_t SimulationKernel::record_effects_damage_event(
    uint64_t munition_entity_id,
    uint64_t target_id,
    const EngagementDamageStateSnapshot& before,
    const EngagementDamageStateSnapshot& after,
    const std::string& trigger_type,
    const std::string& outcome_state,
    double event_time_s,
    double nearest_approach_time_s,
    double miss_distance_m,
    double detonation_local_forward_m,
    double detonation_local_right_m,
    double detonation_local_up_m,
    double closure_mps,
    double missile_axis_forward,
    double missile_axis_right,
    double missile_axis_up,
    double quality,
    double confidence,
    const std::string& effect_family,
    double warhead_mass_kg,
    double warhead_lethal_radius_m,
    bool warhead_profile_synthetic,
    bool damage_scalar_synthetic,
    const std::string& fuze_type,
    double fuze_trigger_radius_m,
    double fuze_delay_s,
    double fuze_reliability,
    bool fuze_profile_synthetic,
    bool direct_hitbox_intersection,
    std::uint32_t projected_hitbox_count,
    double spatial_effect_scale,
    double mechanism_armor_scale,
    double mechanism_exposure_scale,
    double mechanism_effect_scale,
    double component_threshold_scale,
    double component_failure_probability,
    double component_failure_sample,
    std::uint32_t component_failure_count,
    std::uint32_t component_hit_count,
    const std::string& component_primary_name,
    const std::string& component_primary_system,
    double component_primary_redundancy_group,
    bool component_primary_critical
) {
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const std::int64_t frame_count = info ? info->frame_count_total : 0;
    if (event_time_s < recent_engagement_event_epoch_time_s_ ||
        frame_count < recent_engagement_event_epoch_frame_) {
        clear_recent_engagement_events();
    }
    recent_engagement_event_epoch_time_s_ = event_time_s;
    recent_engagement_event_epoch_frame_ = frame_count;

    const std::uint64_t effects_event_id = next_engagement_event_id_++;
    const std::uint64_t damage_report_id = next_engagement_event_id_++;
    const std::uint64_t trace_id = next_engagement_event_id_++;
    std::uint64_t launch_event_id = pending_effects_launch_event_id_;
    if (launch_event_id == 0 && munition_entity_id != 0) {
        for (auto it = recent_engagement_events_.launch_events.rbegin();
             it != recent_engagement_events_.launch_events.rend();
             ++it) {
            if (it->has_spawned_munition &&
                it->spawned_munition.entity_id == munition_entity_id) {
                launch_event_id = it->event_id;
                break;
            }
        }
    }
    const std::uint64_t chain_id = launch_event_id != 0 ? launch_event_id : effects_event_id;

    EffectsEvent effects{};
    effects.event_id = effects_event_id;
    effects.munition = engagement_ref(munition_entity_id);
    effects.target = engagement_ref(target_id);
    effects.trigger_type = trigger_type;
    effects.outcome_state = outcome_state;
    effects.detonation_time_s = event_time_s;
    effects.nearest_approach_time_s = nearest_approach_time_s;
    effects.miss_distance_m = miss_distance_m;
    effects.detonation_local_forward_m = detonation_local_forward_m;
    effects.detonation_local_right_m = detonation_local_right_m;
    effects.detonation_local_up_m = detonation_local_up_m;
    effects.closure_mps = closure_mps;
    effects.missile_axis_forward = missile_axis_forward;
    effects.missile_axis_right = missile_axis_right;
    effects.missile_axis_up = missile_axis_up;
    effects.quality = quality;
    effects.confidence = confidence;
    effects.effect_family = effect_family;
    effects.warhead_mass_kg = warhead_mass_kg;
    effects.warhead_lethal_radius_m = warhead_lethal_radius_m;
    effects.warhead_profile_synthetic = warhead_profile_synthetic;
    effects.damage_scalar_synthetic = damage_scalar_synthetic;
    effects.fuze_type = fuze_type;
    effects.fuze_trigger_radius_m = fuze_trigger_radius_m;
    effects.fuze_delay_s = fuze_delay_s;
    effects.fuze_reliability = fuze_reliability;
    effects.fuze_profile_synthetic = fuze_profile_synthetic;
    effects.direct_hitbox_intersection = direct_hitbox_intersection;
    effects.projected_hitbox_count = projected_hitbox_count;
    effects.spatial_effect_scale = spatial_effect_scale;
    effects.mechanism_armor_scale = mechanism_armor_scale;
    effects.mechanism_exposure_scale = mechanism_exposure_scale;
    effects.mechanism_effect_scale = mechanism_effect_scale;
    effects.component_threshold_scale = component_threshold_scale;
    effects.component_failure_probability = component_failure_probability;
    effects.component_failure_sample = component_failure_sample;
    effects.component_failure_count = component_failure_count;
    effects.component_hit_count = component_hit_count;
    effects.component_primary_name = component_primary_name;
    effects.component_primary_system = component_primary_system;
    effects.component_primary_redundancy_group = component_primary_redundancy_group;
    effects.component_primary_critical = component_primary_critical;
    recent_engagement_events_.effects_events.push_back(effects);
    while (recent_engagement_events_.effects_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.effects_events.erase(recent_engagement_events_.effects_events.begin());
    }

    const auto min_damage_capability = [](const EngagementDamageStateSnapshot& snapshot) {
        return std::min(
            std::min(snapshot.mission_capability, snapshot.mobility_capability),
            std::min(snapshot.sensor_capability, snapshot.survivability_margin));
    };

    char damage_delta[160];
    std::snprintf(
        damage_delta,
        sizeof(damage_delta),
        "mission=%.6f,mobility=%.6f,sensor=%.6f,survivability=%.6f",
        after.mission_capability - before.mission_capability,
        after.mobility_capability - before.mobility_capability,
        after.sensor_capability - before.sensor_capability,
        after.survivability_margin - before.survivability_margin);

    DamageReport report{};
    report.report_id = damage_report_id;
    report.target = engagement_ref(target_id);
    report.source_event_id = effects_event_id;
    report.hp_delta = (before.has_health || after.has_health) ? after.hp - before.hp : 0.0;
    report.system_health_delta = min_damage_capability(after) - min_damage_capability(before);
    report.platform_damage_state_delta = std::string(damage_delta);
    report.mission_kill = after.mission_kill;
    report.mobility_kill = after.mobility_kill;
    report.sensor_kill = after.sensor_kill;
    report.survivability_kill = after.survivability_margin <= 0.0 || !after.entity_active;
    report.loss_state_from = before.loss_state;
    report.loss_state_to = after.entity_active ? after.loss_state : "lost";
    report.destroyed = !after.entity_active || report.loss_state_to == "lost";
    report.report_time_s = event_time_s;
    recent_engagement_events_.damage_reports.push_back(report);
    while (recent_engagement_events_.damage_reports.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.damage_reports.erase(recent_engagement_events_.damage_reports.begin());
    }

    DiagnosticsTrace trace{};
    trace.trace_id = trace_id;
    trace.chain_id = chain_id;
    trace.launch_event_id = launch_event_id;
    trace.munition = engagement_ref(munition_entity_id);
    trace.effects_event_id = effects_event_id;
    trace.damage_report_id = damage_report_id;
    recent_engagement_events_.diagnostics_traces.push_back(trace);
    while (recent_engagement_events_.diagnostics_traces.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.diagnostics_traces.erase(recent_engagement_events_.diagnostics_traces.begin());
    }
    pending_effects_launch_event_id_ = 0;
    return effects_event_id;
}

void SimulationKernel::clear_recent_engagement_events() {
    recent_engagement_events_ = RecentEngagementEvents{};
    next_engagement_event_id_ = 1;
    pending_effects_launch_event_id_ = 0;
    recent_engagement_event_epoch_time_s_ = 0.0;
    recent_engagement_event_epoch_frame_ = 0;
}

bool SimulationKernel::debug_apply_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double damage,
    double fuse_distance
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before = capture_engagement_damage_state(target_id);

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
    synthetic.warhead_profile = make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const KeyEntity* target_key = target.get<KeyEntity>();
    const bool structured_air_target = target_key &&
        (target_key->type == UnitType::Aircraft || target_key->type == UnitType::C2Node) &&
        target.get<HitboxConfig>() != nullptr &&
        target.get<SystemHealth>() != nullptr &&
        target.get<PlatformDamageState>() != nullptr;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        0.0,
        0.0,
        structured_air_target ? 0.0 : 2.0);

    auto impact = ecs.entity()
        .set<Transform>(impact_transform)
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    (void)record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        0.0,
        fuse_distance,
        true,
        true,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical);
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_local_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    double damage,
    double fuse_distance
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before = capture_engagement_damage_state(target_id);

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
    synthetic.warhead_profile = make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        local_forward_m,
        local_right_m,
        local_up_m);
    auto impact = ecs.entity()
        .set<Transform>(impact_transform)
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    (void)record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_local_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        0.0,
        fuse_distance,
        true,
        true,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical);
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    const WarheadProfile& warhead_profile
) {
    return debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        local_forward_m,
        local_right_m,
        local_up_m,
        warhead_profile,
        0.0,
        0.0,
        0.0);
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    const WarheadProfile& warhead_profile,
    double missile_vx_mps,
    double missile_vy_mps,
    double missile_vz_mps
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const double damage = std::isfinite(warhead_profile.damage_scalar)
        ? warhead_profile.damage_scalar
        : 180.0;
    const double fuse_distance = std::isfinite(warhead_profile.lethal_radius_m)
        ? warhead_profile.lethal_radius_m
        : 80.0;
    WarheadProfile resolved_profile = warhead_profile;
    if (!std::isfinite(resolved_profile.damage_scalar)) {
        resolved_profile.damage_scalar = damage;
        resolved_profile.damage_scalar_synthetic = true;
    }
    if (!std::isfinite(resolved_profile.lethal_radius_m)) {
        resolved_profile.lethal_radius_m = fuse_distance;
    }

    const EngagementDamageStateSnapshot before = capture_engagement_damage_state(target_id);

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
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_profiled_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        local_forward_m,
        local_right_m,
        local_up_m);
    auto impact = ecs.entity()
        .set<Transform>(impact_transform)
        .set<Velocity>({missile_vx_mps, missile_vy_mps, missile_vz_mps})
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    const auto missile_axis = velocity_axis_in_target_body(
        *target_transform,
        missile_vx_mps,
        missile_vy_mps,
        missile_vz_mps);
    const double closure_mps = resolve_closure_from_impact(
        *target_transform,
        impact_transform,
        target.get<Velocity>(),
        missile_vx_mps,
        missile_vy_mps,
        missile_vz_mps);
    (void)record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_profiled_local_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        closure_mps,
        missile_axis[0],
        missile_axis[1],
        missile_axis[2],
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        std::isfinite(synthetic.warhead_profile.mass_kg)
            ? synthetic.warhead_profile.mass_kg
            : 0.0,
        std::isfinite(synthetic.warhead_profile.lethal_radius_m)
            ? synthetic.warhead_profile.lethal_radius_m
            : fuse_distance,
        synthetic.warhead_profile.synthetic,
        synthetic.warhead_profile.damage_scalar_synthetic,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical);
    impact.destruct();
    return true;
}
