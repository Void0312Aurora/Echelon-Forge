#pragma once

#include <flecs.h>

#include <algorithm>
#include <cstdint>
#include <string>
#include <utility>

#include "components/basic/common.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/combat/structural_failure.h"
#include "components/domains/air/combat/damage_air.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "systems/combat/damage_system_common.h"

namespace structural_consequence {

inline void lower_to(double &field, double ceiling) {
    field = std::min(field, std::clamp(ceiling, 0.0, 1.0));
}

inline void raise_to(double &field, double floor) {
    field = std::max(field, std::clamp(floor, 0.0, 1.0));
}

inline bool has_consequence_source(const StructuralBreakupState &breakup) {
    return breakup.active_break_modes != 0u || breakup.airframe_breakup;
}

inline void apply_wing_loss_consequence(AircraftDamageState &aircraft,
                                        PlatformDamageState &platform) {
    lower_to(aircraft.structural_integrity, 0.35);
    lower_to(aircraft.flight_control_integrity, 0.45);
    lower_to(aircraft.roll_control_integrity, 0.18);
    lower_to(aircraft.hydraulic_pressure_availability, 0.55);
    raise_to(aircraft.control_asymmetry, 0.78);
    aircraft.forced_landing_required = true;

    lower_to(platform.mobility_capability, 0.0);
    lower_to(platform.survivability_margin, 0.45);
}

inline void apply_tail_loss_consequence(AircraftDamageState &aircraft,
                                        PlatformDamageState &platform) {
    lower_to(aircraft.flight_control_integrity, 0.60);
    lower_to(aircraft.pitch_control_integrity, 0.45);
    lower_to(aircraft.yaw_control_integrity, 0.50);
    lower_to(aircraft.hydraulic_integrity, 0.78);
    lower_to(aircraft.hydraulic_pressure_availability, 0.76);
    raise_to(aircraft.control_asymmetry, 0.20);
    aircraft.forced_landing_required = true;

    lower_to(platform.mobility_capability, 0.30);
    lower_to(platform.survivability_margin, 0.75);
}

inline void apply_engine_detach_consequence(AircraftDamageState &aircraft,
                                            PlatformDamageState &platform) {
    lower_to(aircraft.propulsion_integrity, 0.30);
    lower_to(aircraft.fuel_system_integrity, 0.72);
    raise_to(aircraft.fuel_leak_severity, 0.30);
    raise_to(aircraft.flammable_fluid_exposure, 0.25);
    raise_to(aircraft.ignition_source_severity, 0.20);
    aircraft.forced_landing_required = true;

    lower_to(platform.mobility_capability, 0.30);
    lower_to(platform.survivability_margin, 0.72);
}

inline void apply_fuselage_rupture_consequence(AircraftDamageState &aircraft,
                                               PlatformDamageState &platform) {
    lower_to(aircraft.structural_integrity, 0.50);
    lower_to(aircraft.fuel_system_integrity, 0.65);
    lower_to(aircraft.crew_effectiveness, 0.85);
    lower_to(aircraft.pilot_effectiveness, 0.88);
    raise_to(aircraft.fuel_leak_severity, 0.45);
    raise_to(aircraft.flammable_fluid_exposure, 0.35);
    raise_to(aircraft.fire_severity, 0.15);
    raise_to(aircraft.fuselage_fire_zone_severity, 0.20);
    aircraft.forced_landing_required = true;

    lower_to(platform.mission_capability, 0.65);
    lower_to(platform.survivability_margin, 0.50);
}

inline void apply_multi_axis_consequence(AircraftDamageState &aircraft,
                                         PlatformDamageState &platform) {
    lower_to(aircraft.structural_integrity, 0.20);
    lower_to(aircraft.flight_control_integrity, 0.30);
    lower_to(aircraft.roll_control_integrity, 0.25);
    lower_to(aircraft.pitch_control_integrity, 0.25);
    lower_to(aircraft.yaw_control_integrity, 0.30);
    lower_to(aircraft.hydraulic_integrity, 0.35);
    lower_to(aircraft.hydraulic_pressure_availability, 0.30);
    lower_to(aircraft.propulsion_integrity, 0.25);
    lower_to(aircraft.command_navigation_integrity, 0.45);
    raise_to(aircraft.control_asymmetry, 0.65);
    raise_to(aircraft.structural_overstress, 0.75);
    aircraft.forced_landing_required = true;

    lower_to(platform.mobility_capability, 0.0);
    lower_to(platform.mission_capability, 0.25);
    lower_to(platform.sensor_capability, 0.50);
    lower_to(platform.survivability_margin, 0.0);
}

inline void apply_structural_breakup_consequence(const StructuralBreakupState &breakup,
                                                 AircraftDamageState &aircraft,
                                                 PlatformDamageState &platform, Health &health) {
    if (!has_consequence_source(breakup)) {
        return;
    }

    if (structural_breakup_has_mode(breakup, StructuralBreakMode::WingLoss)) {
        apply_wing_loss_consequence(aircraft, platform);
    }
    if (structural_breakup_has_mode(breakup, StructuralBreakMode::TailLoss)) {
        apply_tail_loss_consequence(aircraft, platform);
    }
    if (structural_breakup_has_mode(breakup, StructuralBreakMode::EngineDetach)) {
        apply_engine_detach_consequence(aircraft, platform);
    }
    if (structural_breakup_has_mode(breakup, StructuralBreakMode::FuselageRupture)) {
        apply_fuselage_rupture_consequence(aircraft, platform);
    }
    if (structural_breakup_has_mode(breakup, StructuralBreakMode::MultiAxis)) {
        apply_multi_axis_consequence(aircraft, platform);
    }
    if (breakup.airframe_breakup) {
        lower_to(platform.survivability_margin, 0.0);
    }

    clamp_aircraft_damage_state(aircraft);
    apply_aircraft_damage_state_to_platform(aircraft, platform);
    sync_platform_damage_loss_state(health, platform, breakup.airframe_breakup);
}

inline void record_platform_consequence_event(IEngagementEventRecorder &recorder,
                                              std::uint64_t target_id,
                                              const StructuralBreakupState &breakup,
                                              const EngagementDamageStateSnapshot &before,
                                              const EngagementDamageStateSnapshot &after,
                                              double source_time_s) {
    PlatformConsequenceEvent event{};
    event.header.source_time_s = source_time_s;
    event.header.confidence = 1.0;
    event.header.reason = "generic_research_structural_consequence_projection";
    event.header.producer_node_id = "damage_system.structural_consequence";
    event.header.consumer_visibility = std::string(kLethalityConsumerVisibilityDiagnosticsOnly);
    event.air_system_hit_flags =
        "structural_break_modes=" + std::to_string(breakup.active_break_modes);
    event.air_system_spatial_scales =
        "detached_parts=" + std::to_string(breakup.detached_part_count);
    event.vulnerability_scale_trace = "structural_breakup_state=" +
                                      std::string(structural_breakup_phase_name(
                                          breakup.breakup_state));

    (void)recorder.record_platform_consequence_event({
        .target_id = target_id,
        .parent_event_id = breakup.last_breakup_event_id,
        .before = before,
        .after = after,
        .event = std::move(event),
    });
}

} // namespace structural_consequence

inline void register_structural_consequence_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, AircraftDamageState, const StructuralBreakupState,
               const KeyEntity>("StructuralConsequenceUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto health = it.field<Health>(0);
                auto platform = it.field<PlatformDamageState>(1);
                auto aircraft = it.field<AircraftDamageState>(2);
                auto breakup = it.field<const StructuralBreakupState>(3);
                auto key = it.field<const KeyEntity>(4);
                const EngagementEventRecorderRef *recorder_ref =
                    it.world().get<EngagementEventRecorderRef>();
                const ecs_world_info_t *world_info = ecs_get_world_info(it.world().c_ptr());
                const double current_time =
                    world_info ? static_cast<double>(world_info->world_time_total) : 0.0;
                for (auto i : it) {
                    if (key[i].type != UnitType::Aircraft) {
                        continue;
                    }
                    IEngagementEventRecorder *recorder =
                        recorder_ref ? recorder_ref->recorder : nullptr;
                    const bool should_record =
                        recorder != nullptr && breakup[i].last_breakup_event_id != 0 &&
                        structural_consequence::has_consequence_source(breakup[i]);
                    EngagementDamageStateSnapshot before{};
                    if (should_record) {
                        before = recorder->capture_engagement_damage_state(
                            static_cast<std::uint64_t>(it.entity(i).id()));
                    }
                    structural_consequence::apply_structural_breakup_consequence(
                        breakup[i], aircraft[i], platform[i], health[i]);
                    if (!should_record) {
                        continue;
                    }
                    const EngagementDamageStateSnapshot after =
                        recorder->capture_engagement_damage_state(
                            static_cast<std::uint64_t>(it.entity(i).id()));
                    if (!engagement_damage_snapshot_changed(before, after)) {
                        continue;
                    }
                    structural_consequence::record_platform_consequence_event(
                        *recorder, static_cast<std::uint64_t>(it.entity(i).id()), breakup[i],
                        before, after, current_time);
                }
            }
        });
}
