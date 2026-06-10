#pragma once

#include <algorithm>
#include <cmath>
#include <tuple>
#include <vector>
#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/domains/air/command/control_input_resolution.h"
#include "components/command/legacy_command_bridge.h"
#include "components/command/pilot_action.h"
#include "components/physics/dynamics.h"
#include "components/physics/propulsion_readouts.h"
#include "components/systems/logistics.h"

inline void register_logistics_system(flecs::world &ecs) {
    // 1. Fuel Consumption System
    ecs.system<FuelSystem, const Propulsion>("FuelConsumption").run([](flecs::iter &it) {
        while (it.next()) {
            auto fuel = it.field<FuelSystem>(0);
            auto propulsion = it.field<const Propulsion>(1);
            double dt = it.delta_time();

            for (auto i : it) {
                fuel[i].current_flow_rate = propulsion_readouts::fuel_flow_kg_per_s(
                    propulsion[i], fuel[i].mil_power_flow_rate, fuel[i].ab_flow_rate_multiplier);
                fuel[i].afterburner_active = propulsion[i].afterburner_active;

                double fuel_consumed = fuel[i].current_flow_rate * dt;

                // Consume Config
                // Prioritize External
                if (fuel[i].external_fuel_kg > 0) {
                    if (fuel[i].external_fuel_kg >= fuel_consumed) {
                        fuel[i].external_fuel_kg -= fuel_consumed;
                        fuel_consumed = 0;
                    } else {
                        fuel_consumed -= fuel[i].external_fuel_kg;
                        fuel[i].external_fuel_kg = 0;
                    }
                }

                if (fuel_consumed > 0) {
                    fuel[i].internal_fuel_kg -= fuel_consumed;
                    if (fuel[i].internal_fuel_kg < 0) {
                        fuel[i].internal_fuel_kg = 0;
                        // Flameout!
                        // TODO: Set flag or disable ActionCommand?
                        // For now, logging.
                        // spdlog::trace("Unit {} Flameout!", it.entity(i).id());
                    }
                }
            }
        }
    });

    // 2. Mass Update System
    ecs.system<MassProperties, Mass, const FuelSystem>("MassUpdate").run([](flecs::iter &it) {
        while (it.next()) {
            auto mass = it.field<MassProperties>(0);
            auto rigid_mass = it.field<Mass>(1);
            auto fuel = it.field<const FuelSystem>(2);
            // Optional: const Loadout* loadout = it.field<const Loadout>(2);

            for (auto i : it) {
                double load_mass = 0.0;
                // TODO: Iterate loadout if present

                const double fuel_kg = std::max(0.0, fuel[i].internal_fuel_kg) +
                                       std::max(0.0, fuel[i].external_fuel_kg);

                // Keep the physics mass component consistent with the fuel system.
                rigid_mass[i].fuel_mass_kg = fuel_kg;
                // Phase-1 boundary: Mass remains the runtime authority for decomposed mass terms
                // that physics systems consume, while MassProperties mirrors the empty/total
                // readout surface.
                mass[i].empty_mass_kg = rigid_mass[i].empty_mass_kg;
                mass[i].current_total_mass_kg = rigid_mass[i].get_total_kg() + load_mass;
            }
        }
    });

    // 3. Jettison System (Action)
    ecs.system<FuelSystem, MassProperties>("LogisticsAction").run([](flecs::iter &it) {
        while (it.next()) {
            auto fuel = it.field<FuelSystem>(0);

            for (auto i : it) {
                if (resolved_compatibility_jettison_tanks(it.entity(i))) {
                    fuel[i].external_fuel_kg = 0;
                    // Reduce drag if tracked (TODO)
                    spdlog::info("Unit {} jettisoned tanks.", it.entity(i).id());
                }
            }
        }
    });

    // 4. Resupply System
    // Need to query bases. We can do this by creating a cached query outside the system loop if we
    // want, or just iterating inside. Since bases are few, it's fine. Note: We need access to world
    // to query bases.

    // We register the system to run on Units that *might* resupply
    ecs.system<Transform, Velocity>("ResupplyLogic").run([&](flecs::iter &it) {
        while (it.next()) {
            // Pre-fetch bases to avoid query every entity
            std::vector<std::tuple<flecs::entity, double, double, double, double>> bases;
            auto base_q = it.world().query<const LogisticsNode, const Transform>();
            base_q.each([&](flecs::entity e, const LogisticsNode &node, const Transform &t) {
                if (node.supply_radius_m > 0.0) {
                    bases.emplace_back(e, t.x, t.y, t.z, node.supply_radius_m);
                }
            });

            auto pos = it.field<Transform>(0);
            auto vel = it.field<Velocity>(1); // Check speed

            for (auto i : it) {
                flecs::entity unit = it.entity(i);
                double speed = std::sqrt(vel[i].vx * vel[i].vx + vel[i].vy * vel[i].vy +
                                         vel[i].vz * vel[i].vz);
                FuelSystem *fuel = unit.get_mut<FuelSystem>();
                ResupplyState *state = unit.get_mut<ResupplyState>();

                if (state) {
                    // Continue Resupply Process
                    state->time_remaining_s -= it.delta_time();

                    // Refill Logic (Instant refill every frame or once?)
                    // Continuous top-up ensures if we leave we are full-ish
                    if (fuel) {
                        fuel->internal_fuel_kg = fuel->max_internal_fuel_kg;
                        fuel->external_fuel_kg =
                            fuel->max_external_fuel_kg; // Magic refill of empty tanks
                    }

                    if (state->time_remaining_s <= 0) {
                        state->time_remaining_s = 0.0;
                        state->is_refueling = false;
                        state->is_rearming = false;
                        spdlog::info("Unit {} resupply complete.", unit.id());
                    }

                    // Check if moved (Abort if taxiing too fast?)
                    if (speed > 10.0) {
                        state->time_remaining_s = 0.0;
                        state->is_refueling = false;
                        state->is_rearming = false;
                        spdlog::info("Unit {} broke resupply connection (moving).", unit.id());
                    }

                } else {
                    // Check conditions to Start Resupply
                    // 1. Speed < 5 m/s (Stopped)
                    // 2. Near Base
                    if (fuel && speed < 5.0) {
                        for (const auto &[base_ent, bx, by, bz, radius] : bases) {
                            double dx = pos[i].x - bx;
                            double dy = pos[i].y - by;
                            double dist_sq =
                                dx * dx + dy * dy; // Ignore Z for ground base? or check Alt?
                            // Assuming Base is at Z=0 and Plane at Z=0 (Ground)

                            if (dist_sq < radius * radius) {
                                // Trigger Resupply
                                unit.set<ResupplyState>(
                                    {30.0, true, true, ResupplyKind::BaseRefuel, 0,
                                     NavalResupplyStage::None}); // 30s turnaround
                                spdlog::info("Unit {} started resupply at Base {}.", unit.id(),
                                             base_ent.id());
                                break; // Only one base
                            }
                        }
                    }
                }
            }
        }
    });
}
