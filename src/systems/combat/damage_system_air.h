#pragma once

#include <flecs.h>
#include <algorithm>
#include <cmath>
#include <string>

#include "systems/combat/damage_system_common.h"

#include "components/basic/common.h"
#include "components/command/pilot_action.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/health.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/performance.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"

namespace {
inline void accumulate_aircraft_structural_envelope_damage(const AircraftDamageBaseline &baseline,
                                                           const AeroState &aero, double dt_s,
                                                           AircraftDamageState &aircraft) {
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
    const double high_energy_gate =
        std::clamp((std::max(q_ratio, aero.mach_number / flutter_mach) - 0.90) / 0.25, 0.0, 1.0);
    const double stall_exposure = std::clamp((aero.stall_progress - 0.35) / 0.65, 0.0, 1.0) *
                                  high_energy_gate * std::max(0.0, prior_damage - 0.10);

    const double flutter_rate =
        ((0.035 * q_excess) + (0.025 * mach_excess) + (0.015 * stall_exposure)) * prior_damage;
    const double overstress_rate =
        ((0.020 * std::max(0.0, q_ratio - 1.20)) +
         (0.018 * std::max(0.0, aero.mach_number - (flutter_mach + 0.10)))) *
        prior_damage;

    if (flutter_rate <= 0.0 && overstress_rate <= 0.0) {
        return;
    }

    aircraft.flutter_exposure += flutter_rate * dt_s;
    aircraft.structural_overstress += overstress_rate * dt_s;

    const double structural_loss = ((0.018 * flutter_rate) + (0.030 * overstress_rate)) * dt_s;
    aircraft.structural_integrity -= structural_loss;
}

inline void apply_aircraft_damage_state_to_sensor(const AircraftDamageBaseline &baseline,
                                                  const AircraftDamageState &aircraft,
                                                  Sensor &sensor) {
    if (baseline.sensor_max_range <= 0.0) {
        return;
    }

    const double avionics = std::clamp(aircraft.avionics_integrity, 0.0, 1.0);
    const double crew = std::clamp(aircraft.crew_effectiveness, 0.0, 1.0);
    const double mission_crew = std::clamp(aircraft.mission_crew_effectiveness, 0.0, 1.0);
    const double command_navigation = std::clamp(aircraft.command_navigation_integrity, 0.0, 1.0);
    const double mission_operator = std::min({crew, mission_crew, command_navigation});
    const double mission_scale =
        aircraft_damage_capability_floor(std::min(avionics, mission_operator), 0.12);
    const double avionics_scale = aircraft_damage_capability_floor(avionics, 0.10);
    const double crew_scale = aircraft_damage_capability_floor(mission_operator, 0.35);

    sensor.max_range = baseline.sensor_max_range * mission_scale;
    sensor.detection_prob =
        std::clamp(baseline.sensor_detection_prob * avionics_scale * crew_scale, 0.0, 1.0);
    sensor.bearing_noise_std = baseline.sensor_bearing_noise_std * (1.0 + 2.5 * (1.0 - avionics));
    sensor.range_noise_std = baseline.sensor_range_noise_std * (1.0 + 2.0 * (1.0 - avionics));
    sensor.track_memory_s =
        baseline.sensor_track_memory_s * aircraft_damage_capability_floor(avionics, 0.25);
}

inline double drain_aircraft_fuel_leak(AircraftDamageState &aircraft, double dt_s, FuelSystem *fuel,
                                       Mass *mass) {
    if (dt_s <= 0.0 || aircraft.fuel_leak_severity <= 1.0e-6) {
        return 0.0;
    }

    const double leak_rate_kg_s = 1.5 + (11.0 * std::clamp(aircraft.fuel_leak_severity, 0.0, 1.0));
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

inline void propagate_aircraft_damage_cascade(AircraftDamageState &aircraft, double dt_s,
                                              double leaked_fuel_kg) {
    if (dt_s <= 0.0) {
        return;
    }

    // Early exit: if no cascade sources are active, the function is a no-op.
    // All guarded blocks below will be skipped, and the unguarded float math
    // (fire growth, flammable/ignition decay, fire extinguish) evaluates to
    // zero-delta clamped to [0,1] — equivalent to idempotent pass-through.
    if (aircraft.fire_severity <= 0.0 && aircraft.fuel_leak_severity <= 0.0 &&
        aircraft.fuel_imbalance_severity <= 0.0 && aircraft.flammable_fluid_exposure <= 0.0 &&
        aircraft.ignition_source_severity <= 0.0 && aircraft.smoke_heat_exposure <= 0.0 &&
        aircraft.engine_fire_zone_severity <= 0.0 && aircraft.wing_fire_zone_severity <= 0.0 &&
        aircraft.fuselage_fire_zone_severity <= 0.0 && aircraft.mission_fire_zone_severity <= 0.0 &&
        aircraft.hydraulic_integrity >= 1.0 && aircraft.hydraulic_pressure_availability >= 1.0 &&
        aircraft.structural_integrity >= 1.0 && leaked_fuel_kg <= 0.0) {
        return;
    }

    const double fuel_damage = std::clamp(1.0 - aircraft.fuel_system_integrity, 0.0, 1.0);
    const double hydraulic_pressure_loss =
        std::clamp(1.0 - aircraft.hydraulic_pressure_availability, 0.0, 1.0);
    const double hydraulic_damage =
        std::max(std::clamp(1.0 - aircraft.hydraulic_integrity, 0.0, 1.0), hydraulic_pressure_loss);
    const double avionics_damage = std::clamp(1.0 - aircraft.avionics_integrity, 0.0, 1.0);
    const double leak_activity =
        std::clamp(leaked_fuel_kg / std::max(1.0e-6, dt_s * 8.0), 0.0, 1.0);
    const double flammable_exposure =
        std::clamp(aircraft.flammable_fluid_exposure + 0.45 * fuel_damage +
                       0.25 * hydraulic_damage + 0.65 * leak_activity,
                   0.0, 1.0);
    const double ignition_source = std::clamp(
        aircraft.ignition_source_severity + 0.25 * avionics_damage + 0.12 * fuel_damage, 0.0, 1.0);
    const double suppression = std::clamp(aircraft.fire_suppression_integrity, 0.0, 1.0);
    const double suppression_growth_scale = 1.15 - 0.35 * suppression;

    aircraft.fire_severity +=
        ((0.0040 * fuel_damage) + (0.0025 * hydraulic_damage) + (0.0020 * avionics_damage) +
         (0.0035 * leak_activity) + (0.0025 * flammable_exposure * (0.35 + ignition_source))) *
        suppression_growth_scale * dt_s;

    const double engine_fire_zone = std::clamp(aircraft.engine_fire_zone_severity, 0.0, 1.0);
    const double wing_fire_zone = std::clamp(aircraft.wing_fire_zone_severity, 0.0, 1.0);
    const double fuselage_fire_zone = std::clamp(aircraft.fuselage_fire_zone_severity, 0.0, 1.0);
    const double mission_fire_zone = std::clamp(aircraft.mission_fire_zone_severity, 0.0, 1.0);
    const double active_zone_fire =
        std::max({engine_fire_zone, wing_fire_zone, fuselage_fire_zone, mission_fire_zone});
    const double pre_zone_fire = std::clamp(aircraft.fire_severity, 0.0, 1.0);
    if (active_zone_fire > 0.0) {
        aircraft.fire_severity += 0.0015 * active_zone_fire * (0.35 + flammable_exposure) *
                                  (1.05 - 0.30 * suppression) * dt_s;
        aircraft.smoke_heat_exposure += (0.0018 * engine_fire_zone + 0.0020 * wing_fire_zone +
                                         0.0040 * fuselage_fire_zone + 0.0045 * mission_fire_zone) *
                                        (0.45 + pre_zone_fire + 0.35 * flammable_exposure) *
                                        (1.10 - 0.25 * suppression) * dt_s;
    }

    const double fire = std::clamp(aircraft.fire_severity, 0.0, 1.0);
    if (fire > 0.0) {
        aircraft.structural_integrity -= 0.0060 * fire * dt_s;
        aircraft.avionics_integrity -= 0.0065 * fire * dt_s;
        aircraft.crew_effectiveness -= 0.0035 * fire * dt_s;
        aircraft.pilot_effectiveness -= 0.0025 * fire * dt_s;
        aircraft.mission_crew_effectiveness -= 0.0030 * fire * dt_s;
        aircraft.command_navigation_integrity -= 0.0020 * fire * dt_s;
        aircraft.hydraulic_integrity -= 0.0045 * fire * dt_s;
        aircraft.hydraulic_pressure_availability -= 0.0035 * fire * dt_s;
        aircraft.fuel_system_integrity -= 0.0040 * fire * dt_s;
    }

    if (active_zone_fire > 0.0) {
        const double spread = (1.0 - 0.65 * suppression) * fire * dt_s;
        aircraft.fuselage_fire_zone_severity +=
            0.0006 * (engine_fire_zone + wing_fire_zone + mission_fire_zone) * spread;
        aircraft.engine_fire_zone_severity += 0.0003 * fuselage_fire_zone * spread;
        aircraft.wing_fire_zone_severity += 0.0004 * fuselage_fire_zone * spread;
        aircraft.mission_fire_zone_severity += 0.0005 * fuselage_fire_zone * spread;

        aircraft.propulsion_integrity -= 0.0045 * engine_fire_zone * dt_s;
        aircraft.fuel_system_integrity -= 0.0020 * engine_fire_zone * dt_s;
        aircraft.flight_control_integrity -= 0.0025 * wing_fire_zone * dt_s;
        aircraft.hydraulic_integrity -= 0.0018 * wing_fire_zone * dt_s;
        aircraft.hydraulic_pressure_availability -= 0.0015 * wing_fire_zone * dt_s;
        aircraft.fuel_system_integrity -= 0.0022 * wing_fire_zone * dt_s;
        aircraft.structural_integrity -=
            (0.0020 * wing_fire_zone + 0.0018 * fuselage_fire_zone) * dt_s;
        aircraft.crew_effectiveness -= 0.0020 * fuselage_fire_zone * dt_s;
        aircraft.avionics_integrity -= 0.0038 * mission_fire_zone * dt_s;
        aircraft.mission_crew_effectiveness -= 0.0024 * mission_fire_zone * dt_s;
        aircraft.command_navigation_integrity -= 0.0022 * mission_fire_zone * dt_s;

        const double zone_decay = (0.0005 + 0.0014 * suppression) *
                                  (1.0 - std::clamp(fire + flammable_exposure, 0.0, 1.0));
        aircraft.engine_fire_zone_severity =
            std::clamp(aircraft.engine_fire_zone_severity - zone_decay * dt_s, 0.0, 1.0);
        aircraft.wing_fire_zone_severity =
            std::clamp(aircraft.wing_fire_zone_severity - zone_decay * dt_s, 0.0, 1.0);
        aircraft.fuselage_fire_zone_severity =
            std::clamp(aircraft.fuselage_fire_zone_severity - zone_decay * dt_s, 0.0, 1.0);
        aircraft.mission_fire_zone_severity =
            std::clamp(aircraft.mission_fire_zone_severity - zone_decay * dt_s, 0.0, 1.0);
    }

    if (hydraulic_damage > 0.0) {
        aircraft.hydraulic_pressure_availability -=
            0.0012 * std::clamp(1.0 - aircraft.hydraulic_integrity, 0.0, 1.0) * dt_s;
        aircraft.flight_control_integrity -=
            (0.0025 * hydraulic_pressure_loss + 0.0030 * hydraulic_damage) * dt_s;
        if (hydraulic_damage > 0.65) {
            aircraft.structural_overstress += 0.0020 * (hydraulic_damage - 0.65) * dt_s;
        }
    }

    const double smoke_heat = std::clamp(aircraft.smoke_heat_exposure, 0.0, 1.0);
    if (smoke_heat > 0.0) {
        aircraft.crew_effectiveness -= 0.0020 * smoke_heat * dt_s;
        aircraft.pilot_effectiveness -= 0.0016 * smoke_heat * (0.35 + fuselage_fire_zone) * dt_s;
        aircraft.mission_crew_effectiveness -=
            0.0026 * smoke_heat * (0.45 + mission_fire_zone) * dt_s;
        aircraft.command_navigation_integrity -=
            0.0022 * smoke_heat * (0.40 + mission_fire_zone + 0.35 * fuselage_fire_zone) * dt_s;
        aircraft.avionics_integrity -= 0.0008 * smoke_heat * mission_fire_zone * dt_s;
        aircraft.smoke_heat_exposure =
            std::clamp(aircraft.smoke_heat_exposure -
                           (0.0007 + 0.0009 * suppression) *
                               (1.0 - std::clamp(fire + active_zone_fire, 0.0, 1.0)) * dt_s,
                       0.0, 1.0);
    }

    const double fuel_imbalance = std::clamp(aircraft.fuel_imbalance_severity, 0.0, 1.0);
    if (fuel_imbalance > 0.0) {
        aircraft.control_asymmetry += 0.0014 * fuel_imbalance * dt_s;
        aircraft.roll_control_integrity -= 0.0009 * fuel_imbalance * dt_s;
        aircraft.fuel_imbalance_severity =
            std::clamp(aircraft.fuel_imbalance_severity - 0.0004 * dt_s, 0.0, 1.0);
    }

    aircraft.flammable_fluid_exposure =
        std::clamp(aircraft.flammable_fluid_exposure - (0.0010 + 0.0015 * suppression) * dt_s +
                       0.0010 * leak_activity * dt_s,
                   0.0, 1.0);
    aircraft.ignition_source_severity =
        std::clamp(aircraft.ignition_source_severity - (0.0010 + 0.0008 * suppression) * dt_s +
                       0.0008 * fire * dt_s,
                   0.0, 1.0);

    const double extinguish_rate =
        (0.0010 + 0.0012 * suppression) *
        (1.0 - std::clamp(fuel_damage + leak_activity + 0.5 * flammable_exposure, 0.0, 1.0));
    aircraft.fire_severity = std::clamp(aircraft.fire_severity - extinguish_rate * dt_s, 0.0, 1.0);
}

inline void consume_pending_component_dependency_effects(ComponentDamageState &component_damage,
                                                         double dt_s, SystemHealth *sys_health,
                                                         AircraftDamageState &aircraft,
                                                         PlatformDamageState &platform) {
    if (dt_s <= 0.0 || component_damage.pending_dependency_effects.empty()) {
        return;
    }

    std::size_t write_index = 0;
    auto &pending = component_damage.pending_dependency_effects;
    for (std::size_t read_index = 0; read_index < pending.size(); ++read_index) {
        auto effect = pending[read_index];
        effect.remaining_delay_s = std::max(0.0, effect.remaining_delay_s - dt_s);
        if (effect.remaining_delay_s > 1.0e-9) {
            pending[write_index++] = effect;
            continue;
        }
        apply_damage_component_dependency_impulse(effect.target_system, effect.edge_type,
                                                  effect.availability, effect.impulse, sys_health,
                                                  &aircraft, &platform);
    }
    pending.resize(write_index);
}

inline bool component_damage_key_is_fire_suppression(const std::string &key) {
    return damage_dependency_system_is_fire_suppression(key);
}

inline void
derive_aircraft_fire_suppression_from_component_state(const ComponentDamageState &component_damage,
                                                      AircraftDamageState &aircraft) {
    // Early exit: most aircraft (F-16, Su-35, MQ-9, MH-60R) have no fire
    // suppression components.  Skip the two hash-map scans when it is known
    // at spawn time that no suppression component exists.
    if (!component_damage.has_fire_suppression_components) {
        return;
    }

    bool saw_suppression_component = false;
    double suppression_availability = 1.0;

    for (const auto &[group_key, availability] : component_damage.redundancy_group_availability) {
        if (!component_damage_key_is_fire_suppression(group_key)) {
            continue;
        }
        saw_suppression_component = true;
        suppression_availability =
            std::min(suppression_availability, std::clamp(availability, 0.0, 1.0));
    }

    for (const auto &[component_key, integrity] : component_damage.component_integrity) {
        const auto group_it = component_damage.component_redundancy_group.find(component_key);
        if (group_it != component_damage.component_redundancy_group.end() &&
            component_damage_key_is_fire_suppression(group_it->second)) {
            continue;
        }
        if (!component_damage_key_is_fire_suppression(component_key)) {
            continue;
        }
        saw_suppression_component = true;
        suppression_availability =
            std::min(suppression_availability, std::clamp(integrity, 0.0, 1.0));
    }

    if (saw_suppression_component) {
        aircraft.fire_suppression_integrity =
            std::min(aircraft.fire_suppression_integrity, suppression_availability);
    }
}

inline bool aircraft_has_progressive_fire_or_fuel_terminal_source(
    const AircraftDamageState &aircraft) {
    const double fire_source =
        std::max({std::clamp(aircraft.fire_severity, 0.0, 1.0),
                  std::clamp(aircraft.engine_fire_zone_severity, 0.0, 1.0),
                  std::clamp(aircraft.wing_fire_zone_severity, 0.0, 1.0),
                  std::clamp(aircraft.fuselage_fire_zone_severity, 0.0, 1.0),
                  std::clamp(aircraft.mission_fire_zone_severity, 0.0, 1.0),
                  std::clamp(aircraft.smoke_heat_exposure, 0.0, 1.0)});
    const double fuel_source =
        std::max({std::clamp(aircraft.fuel_leak_severity, 0.0, 1.0),
                  std::clamp(1.0 - aircraft.fuel_system_integrity, 0.0, 1.0),
                  std::clamp(aircraft.flammable_fluid_exposure, 0.0, 1.0),
                  std::clamp(aircraft.ignition_source_severity, 0.0, 1.0)});
    const double burn_weakened_structure =
        std::clamp(1.0 - aircraft.structural_integrity, 0.0, 1.0);
    return fire_source >= 0.20 || fuel_source >= 0.35 ||
           (burn_weakened_structure >= 0.80 && (fire_source > 0.05 || fuel_source > 0.05));
}

inline bool aircraft_loss_should_remain_observable_until_ground(flecs::entity entity,
                                                                const KeyEntity &key,
                                                                const AircraftDamageState *aircraft) {
    if (!aircraft || key.type != UnitType::Aircraft) {
        return false;
    }
    if (!aircraft_has_progressive_fire_or_fuel_terminal_source(*aircraft)) {
        return false;
    }
    if (const GroundState *ground = entity.get<GroundState>()) {
        if (ground->on_ground ||
            ground->lifecycle == GroundImpactLifecycle::CrashedWreck ||
            ground->lifecycle == GroundImpactLifecycle::DebrisFragmentResidue) {
            return true;
        }
    }
    return true;
}

inline void apply_aircraft_terminal_descent_state(flecs::entity entity,
                                                  AircraftDamageState &aircraft,
                                                  PlatformDamageState &platform,
                                                  Health &health) {
    aircraft.forced_landing_required = true;
    aircraft.flight_control_kill = true;
    aircraft.propulsion_kill = true;
    aircraft.structural_integrity = std::min(aircraft.structural_integrity, 0.05);
    aircraft.flight_control_integrity = std::min(aircraft.flight_control_integrity, 0.08);
    aircraft.roll_control_integrity = std::min(aircraft.roll_control_integrity, 0.12);
    aircraft.pitch_control_integrity = std::min(aircraft.pitch_control_integrity, 0.12);
    aircraft.yaw_control_integrity = std::min(aircraft.yaw_control_integrity, 0.12);
    aircraft.hydraulic_integrity = std::min(aircraft.hydraulic_integrity, 0.12);
    aircraft.hydraulic_pressure_availability =
        std::min(aircraft.hydraulic_pressure_availability, 0.12);
    aircraft.propulsion_integrity = std::min(aircraft.propulsion_integrity, 0.05);
    aircraft.control_asymmetry = std::max(aircraft.control_asymmetry, 0.65);

    platform.mobility_capability = 0.0;
    platform.survivability_margin = 0.0;
    platform.loss_state = PlatformLossState::Lost;
    health.current_hp = 0.0;

    if (PilotAction *pilot = entity.get_mut<PilotAction>()) {
        pilot->stick_pitch = 0.0;
        pilot->stick_roll = 0.0;
        pilot->rudder = 0.0;
        pilot->throttle = 0.0;
        pilot->speedbrake = 1.0f;
        pilot->brake = 0.0;
        pilot->brake_left = false;
        pilot->brake_right = false;
        pilot->active = true;
    }
    if (Propulsion *propulsion = entity.get_mut<Propulsion>()) {
        propulsion->throttle_command = 0.0;
        propulsion->throttle_state = 0.0;
        propulsion->dry_thrust_command_n = 0.0;
        propulsion->dry_thrust_state_n = 0.0;
        propulsion->ab_command = 0.0;
        propulsion->ab_state = 0.0;
        propulsion->current_thrust_n = 0.0;
        propulsion->afterburner_active = false;
    }
}
} // namespace

inline void register_aircraft_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, const KeyEntity>("AircraftDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter &it) {
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

                    if (AircraftDamageState *aircraft = e.get_mut<AircraftDamageState>()) {
                        clamp_aircraft_damage_state(*aircraft);
                        if (ComponentDamageState *component_damage =
                                e.get_mut<ComponentDamageState>()) {
                            consume_pending_component_dependency_effects(*component_damage, dt_s,
                                                                         e.get_mut<SystemHealth>(),
                                                                         *aircraft, damage[i]);
                            derive_aircraft_fire_suppression_from_component_state(*component_damage,
                                                                                  *aircraft);
                            derive_aircraft_damage_from_component_state(*component_damage,
                                                                        *aircraft);
                            clamp_aircraft_damage_state(*aircraft);
                        }

                        if (const AircraftDamageBaseline *baseline =
                                e.get<AircraftDamageBaseline>()) {
                            Mass *mass = e.get_mut<Mass>();
                            const double leaked_fuel_kg = drain_aircraft_fuel_leak(
                                *aircraft, dt_s, e.get_mut<FuelSystem>(), mass);
                            propagate_aircraft_damage_cascade(*aircraft, dt_s, leaked_fuel_kg);
                            clamp_aircraft_damage_state(*aircraft);

                            if (const AeroState *aero = e.get<AeroState>()) {
                                accumulate_aircraft_structural_envelope_damage(*baseline, *aero,
                                                                               dt_s, *aircraft);
                                clamp_aircraft_damage_state(*aircraft);
                            }

                            if (FlightModel *flight_model = e.get_mut<FlightModel>()) {
                                const double aggregate_control =
                                    std::min(aircraft->flight_control_integrity,
                                             std::min(aircraft->hydraulic_integrity,
                                                      aircraft->hydraulic_pressure_availability));
                                const double pilot_control = aircraft_damage_capability_floor(
                                    aircraft->pilot_effectiveness, 0.18);
                                const double roll_control =
                                    aircraft_damage_capability_floor(
                                        std::min(aggregate_control,
                                                 aircraft->roll_control_integrity),
                                        0.20) *
                                    std::clamp(1.0 - (0.60 * aircraft->control_asymmetry), 0.45,
                                               1.0) *
                                    pilot_control;
                                const double pitch_control =
                                    aircraft_damage_capability_floor(
                                        std::min(aggregate_control,
                                                 aircraft->pitch_control_integrity),
                                        0.20) *
                                    pilot_control;
                                const double yaw_control =
                                    aircraft_damage_capability_floor(
                                        std::min(aggregate_control,
                                                 aircraft->yaw_control_integrity),
                                        0.20) *
                                    std::clamp(1.0 - (0.35 * aircraft->control_asymmetry), 0.55,
                                               1.0) *
                                    pilot_control;
                                const double control =
                                    std::min({roll_control, pitch_control, yaw_control});
                                const double structure = aircraft_damage_capability_floor(
                                    aircraft->structural_integrity, 0.35);
                                const double mobility = aircraft_damage_capability_floor(
                                    std::min(control, structure), 0.20);

                                flight_model->max_turn_rate = baseline->max_turn_rate * control;
                                flight_model->max_accel = baseline->max_accel * mobility;
                                flight_model->max_climb_rate = baseline->max_climb_rate * mobility;
                                flight_model->max_g = baseline->max_g * structure;
                                flight_model->min_g = baseline->min_g * structure;
                                flight_model->max_speed =
                                    baseline->max_speed * aircraft_damage_capability_floor(
                                                              aircraft->propulsion_integrity, 0.45);
                                flight_model->min_speed =
                                    baseline->min_speed *
                                    (1.0 + (0.35 * (1.0 - aircraft->structural_integrity)));
                                flight_model->takeoff_speed =
                                    baseline->takeoff_speed *
                                    (1.0 + (0.20 * (1.0 - aircraft->structural_integrity)));
                                flight_model->landing_speed =
                                    baseline->landing_speed *
                                    (1.0 + (0.25 * (1.0 - pitch_control)));
                                flight_model->taxi_turn_rate =
                                    baseline->taxi_turn_rate * yaw_control;
                            }

                            if (Propulsion *propulsion = e.get_mut<Propulsion>()) {
                                const double propulsion_scale = aircraft_damage_capability_floor(
                                    aircraft->propulsion_integrity, 0.15);
                                propulsion->mil_thrust_n =
                                    baseline->mil_thrust_n * propulsion_scale;
                                propulsion->ab_thrust_n =
                                    std::max(propulsion->mil_thrust_n,
                                             baseline->ab_thrust_n * propulsion_scale);
                            }

                            if (mass) {
                                mass->fuel_leak_rate_kg_s =
                                    baseline->fuel_leak_rate_kg_s +
                                    (8.0 * std::clamp(aircraft->fuel_leak_severity, 0.0, 1.0));
                            }

                            if (Sensor *sensor = e.get_mut<Sensor>()) {
                                apply_aircraft_damage_state_to_sensor(*baseline, *aircraft,
                                                                      *sensor);
                            }
                        }
                        apply_aircraft_damage_state_to_platform(*aircraft, damage[i]);
                        const double fire_progress = std::clamp(aircraft->fire_severity, 0.0, 1.0);
                        const double leak_progress =
                            std::clamp(aircraft->fuel_leak_severity, 0.0, 1.0);
                        const double hydraulic_damage = std::max(
                            std::clamp(1.0 - aircraft->hydraulic_integrity, 0.0, 1.0),
                            std::clamp(1.0 - aircraft->hydraulic_pressure_availability, 0.0, 1.0));
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
                        AircraftDamageState *aircraft = e.get_mut<AircraftDamageState>();
                        if (aircraft_loss_should_remain_observable_until_ground(
                                e, key[i], aircraft)) {
                            apply_aircraft_terminal_descent_state(e, *aircraft, damage[i],
                                                                  health[i]);
                        } else {
                            health[i].current_hp = 0.0;
                            e.destruct();
                        }
                    }
                }
            }
        });
}
