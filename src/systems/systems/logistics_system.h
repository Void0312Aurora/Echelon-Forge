#pragma once

#include <algorithm>
#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"

inline void register_logistics_system(flecs::world& ecs) {
    // 1. Fuel Consumption System
    ecs.system<FuelSystem>("FuelConsumption")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto fuel = it.field<FuelSystem>(0);
                double dt = it.delta_time();

                for (auto i : it) {
                    double throttle = 0.0; // [0, 1]
                    bool throttle_set = false;

                    // Priority 1: Digital Pilot
                    if (const PilotAction* pilot = it.entity(i).get<PilotAction>()) {
                        if (pilot->active) {
                            throttle = std::clamp(pilot->throttle, 0.0, 1.0);
                            throttle_set = true;
                        }
                    }

                    // Priority 2: Legacy MovementCommand
                    if (!throttle_set) {
                        if (const MovementCommand* legacy = it.entity(i).get<MovementCommand>()) {
                            if (legacy->active) {
                                throttle = std::clamp(legacy->throttle_cmd, 0.0, 1.0);
                                throttle_set = true;
                            }
                        }
                    }

                    // Priority 3: ActionCommand (normalized [-1,1] -> [0,1])
                    if (!throttle_set) {
                        if (const ActionCommand* act = it.entity(i).get<ActionCommand>()) {
                            if (act->active) {
                                throttle = std::clamp((act->accel_cmd + 1.0) * 0.5, 0.0, 1.0);
                                throttle_set = true;
                            }
                        }
                    }

                    // Mapping Throttle to Burn Rate
                    // Idle: 10% of Mil
                    // Mil: 100% of Mil (Throttle=0.5 to 0.8?)
                    // AB: Multiplier * Mil (Throttle > 0.9)

                    // Simple mapping:
                    // < 0: Idle flow (approx)
                    // 0.0 - 0.9: Linear interpolation 
                    // > 0.9: Afterburner

                    constexpr double kAfterburnerThreshold = 0.9;
                    if (throttle > kAfterburnerThreshold) {
                        fuel[i].current_flow_rate = fuel[i].mil_power_flow_rate * fuel[i].ab_flow_rate_multiplier;
                        fuel[i].afterburner_active = true;
                    } else {
                        // Linear interpolation from idle -> MIL as throttle goes 0..0.9
                        fuel[i].current_flow_rate =
                            fuel[i].mil_power_flow_rate * (0.1 + 0.9 * (throttle / kAfterburnerThreshold));
                        fuel[i].afterburner_active = false;
                    }

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
    ecs.system<MassProperties, Mass, const FuelSystem>("MassUpdate")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto mass = it.field<MassProperties>(0);
                auto rigid_mass = it.field<Mass>(1);
                auto fuel = it.field<const FuelSystem>(2);
                // Optional: const Loadout* loadout = it.field<const Loadout>(2); 

                for (auto i : it) {
                    double load_mass = 0.0;
                    // TODO: Iterate loadout if present
                    
                    const double fuel_kg =
                        std::max(0.0, fuel[i].internal_fuel_kg) + std::max(0.0, fuel[i].external_fuel_kg);

                    // Keep the physics mass component consistent with the fuel system.
                    rigid_mass[i].fuel_mass_kg = fuel_kg;

                    mass[i].current_total_mass_kg = mass[i].empty_mass_kg + 
                                                    fuel_kg +
                                                    load_mass;
                }
            }
        });

    // 3. Jettison System (Action)
    ecs.system<FuelSystem, MassProperties, const ActionCommand>("LogisticsAction")
        .run([](flecs::iter& it) {
             while (it.next()) {
                 auto fuel = it.field<FuelSystem>(0);
                 auto cmd = it.field<const ActionCommand>(2);
                 
                 for (auto i : it) {
                     if (cmd[i].jettison_tanks) {
                         fuel[i].external_fuel_kg = 0;
                         // Reduce drag if tracked (TODO)
                         spdlog::info("Unit {} jettisoned tanks.", it.entity(i).id());
                     }
                 }
             }
        });

    // 4. Resupply System
    // Need to query bases. We can do this by creating a cached query outside the system loop if we want,
    // or just iterating inside. Since bases are few, it's fine.
    // Note: We need access to world to query bases.
    
    // We register the system to run on Units that *might* resupply
    ecs.system<FuelSystem, const Transform, const Velocity>("ResupplyLogic")
       .run([&](flecs::iter& it) {
           // Pre-fetch bases to avoid query every entity
           std::vector<std::tuple<flecs::entity, double, double, double, double>> bases;
           auto base_q = it.world().query<const LogisticsNode, const Transform>();
           base_q.each([&](flecs::entity e, const LogisticsNode& node, const Transform& t) {
               bases.emplace_back(e, t.x, t.y, t.z, node.supply_radius_m);
           });
           
           if (bases.empty()) return;

           auto fuel = it.field<FuelSystem>(0);
           auto pos = it.field<const Transform>(1);
           auto vel = it.field<const Velocity>(2); // Check speed
           
           for (auto i : it) {
               flecs::entity unit = it.entity(i);
               double speed = std::sqrt(vel[i].vx*vel[i].vx + vel[i].vy*vel[i].vy + vel[i].vz*vel[i].vz);
               
               // Check if we are currently resupplying
               ResupplyState* state = unit.get_mut<ResupplyState>();
               
               if (state) {
                   // Continue Resupply Process
                   state->time_remaining_s -= it.delta_time();
                   
                   // Refill Logic (Instant refill every frame or once?)
                   // Continuous top-up ensures if we leave we are full-ish
                   fuel[i].internal_fuel_kg = fuel[i].max_internal_fuel_kg;
                   fuel[i].external_fuel_kg = fuel[i].max_external_fuel_kg; // Magic refill of empty tanks
                   
                   if (state->time_remaining_s <= 0) {
                       unit.remove<ResupplyState>();
                       spdlog::info("Unit {} resupply complete.", unit.id());
                   }
                   
                   // Check if moved (Abort if taxiing too fast?)
                   if (speed > 10.0) {
                        unit.remove<ResupplyState>(); // Break connection
                        spdlog::info("Unit {} broke resupply connection (moving).", unit.id());
                   }
                   
               } else {
                   // Check conditions to Start Resupply
                   // 1. Speed < 5 m/s (Stopped)
                   // 2. Near Base
                   if (speed < 5.0) {
                       for (const auto& [base_ent, bx, by, bz, radius] : bases) {
                           double dx = pos[i].x - bx;
                           double dy = pos[i].y - by;
                           double dist_sq = dx*dx + dy*dy; // Ignore Z for ground base? or check Alt?
                           // Assuming Base is at Z=0 and Plane at Z=0 (Ground)
                           
                           if (dist_sq < radius * radius) {
                               // Trigger Resupply
                               unit.set<ResupplyState>({30.0, true, true}); // 30s turnaround
                               spdlog::info("Unit {} started resupply at Base {}.", unit.id(), base_ent.id());
                               break; // Only one base
                           }
                       }
                   }
               }
           }
       });
}
