#include "simulation_kernel_engagement_event_store.h"

#include "components/combat/damage.h"
#include "components/combat/health.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace {

EngagementEntityRef engagement_ref(uint64_t entity_id) {
    return EngagementEntityRef{
        .world_index = 0,
        .entity_id = entity_id,
    };
}

std::uint64_t current_source_frame(flecs::world& ecs) {
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    return info && info->frame_count_total > 0
        ? static_cast<std::uint64_t>(info->frame_count_total)
        : 0;
}

std::uint64_t find_launch_event_id_for_munition(
    const RecentEngagementEvents& events,
    std::uint64_t munition_entity_id
) {
    if (munition_entity_id == 0) {
        return 0;
    }
    for (auto it = events.launch_events.rbegin(); it != events.launch_events.rend(); ++it) {
        if (it->has_spawned_munition && it->spawned_munition.entity_id == munition_entity_id) {
            return it->event_id;
        }
    }
    return 0;
}

template <typename Event>
void cap_recent_events(std::vector<Event>& events, std::size_t max_size) {
    while (events.size() > max_size) {
        events.erase(events.begin());
    }
}

void complete_lethality_header(
    LethalityChainHeader& header,
    const std::string& stage,
    const std::string& default_status,
    double event_time_s,
    std::uint64_t event_id,
    std::uint64_t chain_id,
    std::uint64_t parent_event_id,
    std::uint64_t munition_entity_id,
    std::uint64_t shooter_id,
    std::uint64_t target_id,
    std::uint64_t source_frame
) {
    header.event_id = event_id;
    header.chain_id = chain_id != 0 ? chain_id : event_id;
    header.parent_event_id = parent_event_id;
    header.stage = stage;
    if (header.status.empty() || header.status == "not_evaluated") {
        header.status = default_status;
    }
    header.source_time_s = event_time_s;
    if (header.source_frame == 0) {
        header.source_frame = source_frame;
    }
    header.munition = engagement_ref(munition_entity_id);
    header.shooter = engagement_ref(shooter_id);
    header.target = engagement_ref(target_id);
    if (header.producer_node_id.empty()) {
        header.producer_node_id = "damage_system.warhead_effects";
    }
    if (header.fidelity_mode.empty() || header.fidelity_mode == "unspecified") {
        header.fidelity_mode = "research_runtime";
    }
    if (header.evidence_level.empty() || header.evidence_level == "uncalibrated") {
        header.evidence_level = "engineering_assumption";
    }
    if (header.confidence <= 0.0) {
        header.confidence = 1.0;
    } else {
        header.confidence = std::clamp(header.confidence, 0.0, 1.0);
    }
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

std::uint64_t SimulationKernelEngagementEventStore::record_nearest_approach_event(
    EngagementNearestApproachEventRecord record
) {
    const double event_time_s = std::isfinite(record.event.nearest_approach_time_s)
        ? record.event.nearest_approach_time_s
        : record.event.header.source_time_s;
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    std::uint64_t launch_event_id = 0;
    if (record.munition_entity_id != 0) {
        for (auto it = recent_engagement_events_.launch_events.rbegin();
             it != recent_engagement_events_.launch_events.rend();
             ++it) {
            if (it->has_spawned_munition &&
                it->spawned_munition.entity_id == record.munition_entity_id) {
                launch_event_id = it->event_id;
                break;
            }
        }
    }

    NearestApproachEvent event = std::move(record.event);
    event.header.event_id = event_id;
    event.header.chain_id = launch_event_id != 0 ? launch_event_id : event_id;
    event.header.parent_event_id = launch_event_id;
    event.header.stage = "nearest_approach";
    if (event.header.status.empty() || event.header.status == "not_evaluated") {
        event.header.status = "observed";
    }
    event.header.source_time_s = event_time_s;
    event.header.munition = engagement_ref(record.munition_entity_id);
    event.header.shooter = engagement_ref(record.shooter_id);
    event.header.target = engagement_ref(record.target_id);
    event.header.producer_node_id = "damage_system.proximity_fuze";
    if (event.header.fidelity_mode.empty() || event.header.fidelity_mode == "unspecified") {
        event.header.fidelity_mode = "runtime";
    }
    if (event.header.evidence_level.empty() || event.header.evidence_level == "uncalibrated") {
        event.header.evidence_level = "observed_runtime";
    }
    if (event.header.confidence <= 0.0) {
        event.header.confidence = 1.0;
    }

    recent_engagement_events_.nearest_approach_events.push_back(std::move(event));
    while (recent_engagement_events_.nearest_approach_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.nearest_approach_events.erase(
            recent_engagement_events_.nearest_approach_events.begin());
    }
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_fuze_evaluation_event(
    EngagementFuzeEvaluationEventRecord record
) {
    const double event_time_s = record.event.header.source_time_s;
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    std::uint64_t launch_event_id = 0;
    if (record.munition_entity_id != 0) {
        for (auto it = recent_engagement_events_.launch_events.rbegin();
             it != recent_engagement_events_.launch_events.rend();
             ++it) {
            if (it->has_spawned_munition &&
                it->spawned_munition.entity_id == record.munition_entity_id) {
                launch_event_id = it->event_id;
                break;
            }
        }
    }

    std::uint64_t nearest_event_id = 0;
    if (record.munition_entity_id != 0) {
        for (auto it = recent_engagement_events_.nearest_approach_events.rbegin();
             it != recent_engagement_events_.nearest_approach_events.rend();
             ++it) {
            if (it->header.munition.entity_id == record.munition_entity_id) {
                nearest_event_id = it->header.event_id;
                break;
            }
        }
    }

    FuzeEvaluationEvent event = std::move(record.event);
    event.header.event_id = event_id;
    event.header.chain_id = launch_event_id != 0 ? launch_event_id : event_id;
    event.header.parent_event_id = nearest_event_id != 0 ? nearest_event_id : launch_event_id;
    event.header.stage = "fuze_evaluation";
    if (event.header.status.empty() || event.header.status == "not_evaluated") {
        event.header.status = "evaluated";
    }
    event.header.source_time_s = event_time_s;
    event.header.munition = engagement_ref(record.munition_entity_id);
    event.header.shooter = engagement_ref(record.shooter_id);
    event.header.target = engagement_ref(record.target_id);
    event.header.producer_node_id = "damage_system.proximity_fuze";
    if (event.header.fidelity_mode.empty() || event.header.fidelity_mode == "unspecified") {
        event.header.fidelity_mode = "runtime";
    }
    if (event.header.evidence_level.empty() || event.header.evidence_level == "uncalibrated") {
        event.header.evidence_level = "observed_runtime";
    }
    if (event.header.confidence <= 0.0) {
        event.header.confidence = event.triggered ? 1.0 : std::clamp(event.reliability, 0.0, 1.0);
    }

    recent_engagement_events_.fuze_evaluation_events.push_back(std::move(event));
    while (recent_engagement_events_.fuze_evaluation_events.size() > kMaxRecentEngagementEvents) {
        recent_engagement_events_.fuze_evaluation_events.erase(
            recent_engagement_events_.fuze_evaluation_events.begin());
    }
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_warhead_mechanism_event(
    EngagementWarheadMechanismEventRecord record
) {
    const double event_time_s = record.event.header.source_time_s;
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    const std::uint64_t launch_event_id = record.chain_id != 0
        ? record.chain_id
        : find_launch_event_id_for_munition(
            recent_engagement_events_,
            record.munition_entity_id);

    WarheadMechanismEvent event = std::move(record.event);
    complete_lethality_header(
        event.header,
        "warhead_mechanism",
        "applied",
        event_time_s,
        event_id,
        launch_event_id,
        record.parent_event_id,
        record.munition_entity_id,
        record.shooter_id,
        record.target_id,
        current_source_frame(ecs_));

    recent_engagement_events_.warhead_mechanism_events.push_back(std::move(event));
    cap_recent_events(
        recent_engagement_events_.warhead_mechanism_events,
        kMaxRecentEngagementEvents);
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_spatial_coverage_event(
    EngagementSpatialCoverageEventRecord record
) {
    const double event_time_s = record.event.header.source_time_s;
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    const std::uint64_t launch_event_id = record.chain_id != 0
        ? record.chain_id
        : find_launch_event_id_for_munition(
            recent_engagement_events_,
            record.munition_entity_id);

    SpatialCoverageEvent event = std::move(record.event);
    complete_lethality_header(
        event.header,
        "spatial_coverage",
        "projected",
        event_time_s,
        event_id,
        launch_event_id,
        record.parent_event_id,
        record.munition_entity_id,
        record.shooter_id,
        record.target_id,
        current_source_frame(ecs_));

    recent_engagement_events_.spatial_coverage_events.push_back(std::move(event));
    cap_recent_events(
        recent_engagement_events_.spatial_coverage_events,
        kMaxRecentEngagementEvents);
    return event_id;
}

std::uint64_t SimulationKernelEngagementEventStore::record_component_load_event(
    EngagementComponentLoadEventRecord record
) {
    const double event_time_s = record.event.header.source_time_s;
    reset_if_event_clock_rewound(event_time_s);

    const std::uint64_t event_id = next_engagement_event_id_++;
    const std::uint64_t launch_event_id = record.chain_id != 0
        ? record.chain_id
        : find_launch_event_id_for_munition(
            recent_engagement_events_,
            record.munition_entity_id);

    ComponentLoadEvent event = std::move(record.event);
    complete_lethality_header(
        event.header,
        "component_load",
        "projected",
        event_time_s,
        event_id,
        launch_event_id,
        record.parent_event_id,
        record.munition_entity_id,
        record.shooter_id,
        record.target_id,
        current_source_frame(ecs_));

    recent_engagement_events_.component_load_events.push_back(std::move(event));
    cap_recent_events(
        recent_engagement_events_.component_load_events,
        kMaxRecentEngagementEvents);
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

    const bool effects_reached_warhead_loads =
        effects.outcome_state != "fuze_no_detonation" &&
        effects.outcome_state != "fuze_no_terminal_track";
    if (effects_reached_warhead_loads) {
        WarheadMechanismEvent warhead_event{};
        warhead_event.header.source_time_s = event_time_s;
        warhead_event.header.confidence = effects.confidence;
        warhead_event.header.reason = effects.warhead_profile_synthetic
            ? "generic_research_synthetic_warhead_profile"
            : "generic_research_warhead_profile";
        warhead_event.mechanism_family = effects.effect_family;
        warhead_event.warhead_mass_kg = effects.warhead_mass_kg;
        warhead_event.lethal_radius_m = effects.warhead_lethal_radius_m;
        warhead_event.fragment_energy_j = effects.mechanism_fragment_energy_j;
        warhead_event.fragment_density_per_m2 =
            effects.mechanism_fragment_areal_density_per_m2;
        warhead_event.blast_overpressure_kpa = effects.mechanism_blast_overpressure_kpa;
        warhead_event.blast_impulse_kpa_ms = effects.mechanism_blast_impulse_kpa_ms;
        warhead_event.blast_scaled_distance_m_kg13 =
            effects.mechanism_blast_scaled_distance_m_kg13;
        warhead_event.rod_cut_margin = effects.mechanism_rod_cut_margin;
        warhead_event.penetration_margin = effects.mechanism_penetration_margin;
        warhead_event.surface_incidence_cos = effects.mechanism_surface_incidence_cos;
        (void)record_warhead_mechanism_event({
            .munition_entity_id = munition_entity_id,
            .target_id = target_id,
            .chain_id = chain_id,
            .parent_event_id = effects_event_id,
            .event = std::move(warhead_event),
        });

        SpatialCoverageEvent spatial_event{};
        spatial_event.header.source_time_s = event_time_s;
        spatial_event.header.confidence = effects.confidence;
        spatial_event.header.reason = "generic_research_spatial_projection";
        spatial_event.projected_hitbox_count = effects.projected_hitbox_count;
        spatial_event.sample_count = effects.warhead_spatial_sample_count;
        spatial_event.hit_estimate = effects.warhead_spatial_hit_estimate;
        spatial_event.hit_fraction = effects.warhead_spatial_hit_fraction;
        spatial_event.energy_scale = effects.warhead_spatial_energy_scale;
        spatial_event.pattern_scale = effects.warhead_spatial_pattern_scale;
        spatial_event.orientation_axis_forward = effects.warhead_orientation_axis_forward;
        spatial_event.orientation_axis_right = effects.warhead_orientation_axis_right;
        spatial_event.orientation_axis_up = effects.warhead_orientation_axis_up;
        (void)record_spatial_coverage_event({
            .munition_entity_id = munition_entity_id,
            .target_id = target_id,
            .chain_id = chain_id,
            .parent_event_id = effects_event_id,
            .event = std::move(spatial_event),
        });

        for (const ComponentMechanismLoadRow& row : effects.component_mechanism_load_rows) {
            if (row.component_name.empty() && row.component_system.empty()) {
                continue;
            }
            ComponentLoadEvent component_event{};
            component_event.header.source_time_s = event_time_s;
            component_event.header.confidence = effects.confidence;
            component_event.header.reason = "generic_research_component_load_projection";
            component_event.component_name = row.component_name;
            component_event.component_system = row.component_system;
            component_event.component_redundancy_group_id =
                row.component_redundancy_group_id;
            component_event.direct_hit = row.direct_hit;
            component_event.distance_m = row.distance_m;
            component_event.effect_scale = row.effect_scale;
            component_event.fragment_energy_j = row.mechanism_fragment_energy_j;
            component_event.fragment_density_per_m2 =
                row.mechanism_fragment_areal_density_per_m2;
            component_event.penetration_margin = row.mechanism_penetration_margin;
            component_event.blast_overpressure_kpa = row.mechanism_blast_overpressure_kpa;
            component_event.blast_impulse_kpa_ms = row.mechanism_blast_impulse_kpa_ms;
            component_event.blast_scaled_distance_m_kg13 =
                row.mechanism_blast_scaled_distance_m_kg13;
            component_event.rod_cut_margin = row.mechanism_rod_cut_margin;
            component_event.surface_incidence_cos = row.mechanism_surface_incidence_cos;
            component_event.load_source = row.direct_hit
                ? "direct_component_hit"
                : "spatial_component_projection";
            (void)record_component_load_event({
                .munition_entity_id = munition_entity_id,
                .target_id = target_id,
                .chain_id = chain_id,
                .parent_event_id = effects_event_id,
                .event = std::move(component_event),
            });
        }
    }

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
        out.nearest_approach_events.begin(),
        out.nearest_approach_events.end(),
        [](const NearestApproachEvent& lhs, const NearestApproachEvent& rhs) {
            return lhs.header.event_id < rhs.header.event_id;
        });
    std::sort(
        out.fuze_evaluation_events.begin(),
        out.fuze_evaluation_events.end(),
        [](const FuzeEvaluationEvent& lhs, const FuzeEvaluationEvent& rhs) {
            return lhs.header.event_id < rhs.header.event_id;
        });
    std::sort(
        out.warhead_mechanism_events.begin(),
        out.warhead_mechanism_events.end(),
        [](const WarheadMechanismEvent& lhs, const WarheadMechanismEvent& rhs) {
            return lhs.header.event_id < rhs.header.event_id;
        });
    std::sort(
        out.spatial_coverage_events.begin(),
        out.spatial_coverage_events.end(),
        [](const SpatialCoverageEvent& lhs, const SpatialCoverageEvent& rhs) {
            return lhs.header.event_id < rhs.header.event_id;
        });
    std::sort(
        out.component_load_events.begin(),
        out.component_load_events.end(),
        [](const ComponentLoadEvent& lhs, const ComponentLoadEvent& rhs) {
            return lhs.header.event_id < rhs.header.event_id;
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
