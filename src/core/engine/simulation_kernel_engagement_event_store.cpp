#include "simulation_kernel_engagement_event_store.h"

#include "components/combat/damage.h"
#include "components/combat/health.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>

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

SimulationKernelEngagementEventStore::SimulationKernelEngagementEventStore(flecs::world& ecs)
    : ecs_(ecs) {}

void SimulationKernelEngagementEventStore::reset_if_event_clock_rewound(double event_time_s) {
    const ecs_world_info_t* info = ecs_get_world_info(ecs_.c_ptr());
    const std::int64_t frame_count = info ? info->frame_count_total : 0;
    if (event_time_s < recent_engagement_event_epoch_time_s_ ||
        frame_count < recent_engagement_event_epoch_frame_) {
        clear();
    }
    recent_engagement_event_epoch_time_s_ = event_time_s;
    recent_engagement_event_epoch_frame_ = frame_count;
}

EngagementDamageStateSnapshot SimulationKernelEngagementEventStore::capture_engagement_damage_state(
    uint64_t target_id
) const {
    EngagementDamageStateSnapshot snapshot{};
    const auto target = ecs_.entity(target_id);
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
    if (const AircraftDamageState* aircraft = target.get<AircraftDamageState>()) {
        snapshot.forced_landing = aircraft->forced_landing_required;
        snapshot.flight_control_kill = aircraft->flight_control_kill;
        snapshot.propulsion_kill = aircraft->propulsion_kill;
        snapshot.crew_kill = aircraft->crew_kill;
    }
    return snapshot;
}

std::uint64_t SimulationKernelEngagementEventStore::record_legacy_launch_event(
    uint64_t shooter_id,
    uint64_t,
    uint64_t spawned_munition_id,
    const std::string& selected_launcher,
    const std::string& selected_munition,
    int ammo_delta,
    double cooldown_delta_s,
    double event_time_s
) {
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    LaunchEvent event{};
    event.event_id = event_id;
    event.request_id = event_id;
    event.accepted = true;
    event.selected_launcher = selected_launcher;
    event.selected_munition = selected_munition;
    event.ammo_delta = ammo_delta;
    event.cooldown_delta_s = cooldown_delta_s;
    event.spawned_munition = engagement_ref(spawned_munition_id);
    event.has_spawned_munition = spawned_munition_id != 0;
    event.event_time_s = event_time_s;
    recent_engagement_events_.launch_events.push_back(event);
    while (recent_engagement_events_.launch_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.launch_events.erase(recent_engagement_events_.launch_events.begin());
    }

    DiagnosticsTrace trace{};
    trace.trace_id = next_engagement_event_id_++;
    trace.chain_id = event_id;
    trace.launch_request_id = event.request_id;
    trace.launch_event_id = event_id;
    trace.munition = event.spawned_munition;
    recent_engagement_events_.diagnostics_traces.push_back(trace);
    while (recent_engagement_events_.diagnostics_traces.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.diagnostics_traces.erase(recent_engagement_events_.diagnostics_traces.begin());
    }
    (void)shooter_id;
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_effects_damage_event(
    EngagementEffectsDamageEventRecord record
) {
    const std::uint64_t munition_entity_id = record.munition_entity_id;
    const std::uint64_t target_id = record.target_id;
    const EngagementDamageStateSnapshot& before = record.before;
    const EngagementDamageStateSnapshot& after = record.after;
    const double event_time_s = record.effects.detonation_time_s;

    reset_if_event_clock_rewound(event_time_s);

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
    effects = std::move(record.effects);
    effects.event_id = effects_event_id;
    effects.munition = engagement_ref(munition_entity_id);
    effects.target = engagement_ref(target_id);
    recent_engagement_events_.effects_events.push_back(std::move(effects));
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
    report.forced_landing = after.forced_landing;
    report.flight_control_kill = after.flight_control_kill;
    report.propulsion_kill = after.propulsion_kill;
    report.crew_kill = after.crew_kill;
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

void SimulationKernelEngagementEventStore::set_pending_effects_launch_event_id(
    std::uint64_t launch_event_id
) {
    pending_effects_launch_event_id_ = launch_event_id;
}

RecentEngagementEvents SimulationKernelEngagementEventStore::export_recent_events_sorted() const {
    RecentEngagementEvents out = recent_engagement_events_;

    std::sort(
        out.launch_events.begin(),
        out.launch_events.end(),
        [](const LaunchEvent& lhs, const LaunchEvent& rhs) {
            return lhs.event_id < rhs.event_id;
        });
    std::sort(
        out.effects_events.begin(),
        out.effects_events.end(),
        [](const EffectsEvent& lhs, const EffectsEvent& rhs) {
            return lhs.event_id < rhs.event_id;
        });
    std::sort(
        out.damage_reports.begin(),
        out.damage_reports.end(),
        [](const DamageReport& lhs, const DamageReport& rhs) {
            return lhs.report_id < rhs.report_id;
        });
    std::sort(
        out.diagnostics_traces.begin(),
        out.diagnostics_traces.end(),
        [](const DiagnosticsTrace& lhs, const DiagnosticsTrace& rhs) {
            return lhs.trace_id < rhs.trace_id;
        });
    return out;
}

void SimulationKernelEngagementEventStore::clear() {
    recent_engagement_events_ = RecentEngagementEvents{};
    next_engagement_event_id_ = 1;
    pending_effects_launch_event_id_ = 0;
    recent_engagement_event_epoch_time_s_ = 0.0;
    recent_engagement_event_epoch_frame_ = 0;
}
