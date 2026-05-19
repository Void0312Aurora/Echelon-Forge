#include "simulation_kernel.h"

#include "components/basic/common.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <cstdio>
#include <limits>
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

}  // namespace

SimulationKernel::EngagementDamageStateSnapshot SimulationKernel::capture_engagement_damage_state(
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
    double quality,
    double confidence,
    const std::string& effect_family
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
    const std::uint64_t chain_id =
        pending_effects_launch_event_id_ != 0 ? pending_effects_launch_event_id_ : effects_event_id;

    EffectsEvent effects{};
    effects.event_id = effects_event_id;
    effects.munition = engagement_ref(munition_entity_id);
    effects.target = engagement_ref(target_id);
    effects.trigger_type = trigger_type;
    effects.outcome_state = outcome_state;
    effects.detonation_time_s = event_time_s;
    effects.nearest_approach_time_s = nearest_approach_time_s;
    effects.quality = quality;
    effects.confidence = confidence;
    effects.effect_family = effect_family;
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
    trace.launch_event_id = pending_effects_launch_event_id_;
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
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    auto impact = ecs.entity()
        .set<Transform>({
            target_transform->x,
            target_transform->y,
            target_transform->z + 2.0,
            target_transform->heading,
            0.0,
            0.0,
        })
        .set<Missile>(synthetic)
        .add<SimObject>();

    effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    (void)record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_proximity_hit",
        "hit",
        current_time,
        current_time,
        1.0,
        1.0,
        "blast_fragmentation");
    impact.destruct();
    return true;
}
