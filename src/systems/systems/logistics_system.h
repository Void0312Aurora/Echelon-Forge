#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <tuple>
#include <vector>
#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/command/air/control_input_resolution.h"
#include "components/command/legacy_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"
#include "systems/physics/propulsion_system.h"

inline void register_logistics_system(flecs::world& ecs) {
    // 1. Fuel Consumption System
    ecs.system<FuelSystem, const Propulsion>("FuelConsumption")
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto fuel = it.field<FuelSystem>(0);
                auto propulsion = it.field<const Propulsion>(1);
                double dt = it.delta_time();

                for (auto i : it) {
                    fuel[i].current_flow_rate = flight_dynamics::propulsion_fuel_flow_kg_per_s(
                        propulsion[i],
                        fuel[i].mil_power_flow_rate,
                        fuel[i].ab_flow_rate_multiplier
                    );
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
                    // Phase-1 boundary: Mass remains the runtime authority for decomposed mass terms that
                    // physics systems consume, while MassProperties mirrors the empty/total readout surface.
                    mass[i].empty_mass_kg = rigid_mass[i].empty_mass_kg;
                    mass[i].current_total_mass_kg = rigid_mass[i].get_total_kg() + load_mass;
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
    ecs.system<Transform, Velocity>("ResupplyLogic")
       .run([&](flecs::iter& it) {
           while (it.next()) {
               // Pre-fetch bases to avoid query every entity
               std::vector<std::tuple<flecs::entity, double, double, double, double>> bases;
               auto base_q = it.world().query<const LogisticsNode, const Transform>();
               base_q.each([&](flecs::entity e, const LogisticsNode& node, const Transform& t) {
                   if (node.supply_radius_m > 0.0) {
                       bases.emplace_back(e, t.x, t.y, t.z, node.supply_radius_m);
                   }
               });
               
               auto pos = it.field<Transform>(0);
               auto vel = it.field<Velocity>(1); // Check speed
               
               for (auto i : it) {
                   flecs::entity unit = it.entity(i);
                   double speed = std::sqrt(vel[i].vx*vel[i].vx + vel[i].vy*vel[i].vy + vel[i].vz*vel[i].vz);
                   FuelSystem* fuel = unit.get_mut<FuelSystem>();
                   ResupplyState* state = unit.get_mut<ResupplyState>();
                   
                   if (state) {
                       // Continue Resupply Process
                       state->time_remaining_s -= it.delta_time();
                       
                       // Refill Logic (Instant refill every frame or once?)
                       // Continuous top-up ensures if we leave we are full-ish
                       if (fuel) {
                           fuel->internal_fuel_kg = fuel->max_internal_fuel_kg;
                           fuel->external_fuel_kg = fuel->max_external_fuel_kg; // Magic refill of empty tanks
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
                           for (const auto& [base_ent, bx, by, bz, radius] : bases) {
                               double dx = pos[i].x - bx;
                               double dy = pos[i].y - by;
                               double dist_sq = dx*dx + dy*dy; // Ignore Z for ground base? or check Alt?
                               // Assuming Base is at Z=0 and Plane at Z=0 (Ground)
                               
                               if (dist_sq < radius * radius) {
                                   // Trigger Resupply
                                   unit.set<ResupplyState>({
                                       30.0,
                                       true,
                                       true,
                                       ResupplyKind::BaseRefuel,
                                       0,
                                       NavalResupplyStage::None
                                   }); // 30s turnaround
                                   spdlog::info("Unit {} started resupply at Base {}.", unit.id(), base_ent.id());
                                   break; // Only one base
                               }
                           }
                       }
                   }
               }
           }
       });

    ecs.system<ResupplyState, NavalStores, const Transform, const Velocity>("NavalUnderwayResupply")
       .run([&](flecs::iter& it) {
           while (it.next()) {
               struct UnderwayProviderSnapshot {
                   flecs::entity entity;
                   LogisticsNode node;
                   double x;
                   double y;
                   double vx;
                   double vy;
                   double vz;
                   double fuel_units_current;
                   double missile_units_current;
                   double dry_cargo_units_current;
               };

               std::vector<UnderwayProviderSnapshot> providers;
               auto provider_q = it.world().query<const LogisticsNode, const Transform, const Velocity, const NavalStores>();
               provider_q.each([&](flecs::entity e,
                                   const LogisticsNode& node,
                                   const Transform& t,
                                   const Velocity& v,
                                   const NavalStores& naval_stores) {
                   if (!node.underway_replenishment_enabled) {
                       return;
                   }
                   providers.push_back({
                       e,
                       node,
                       t.x,
                       t.y,
                       v.vx,
                       v.vy,
                       v.vz,
                       naval_stores.fuel_units_current,
                       naval_stores.missile_units_current,
                       naval_stores.dry_cargo_units_current,
                   });
               });

               auto state = it.field<ResupplyState>(0);
               auto stores = it.field<NavalStores>(1);
               auto pos = it.field<const Transform>(2);
               auto vel = it.field<const Velocity>(3);

               auto transfer_axis = [](double* provider_current,
                                       double provider_rate_per_s,
                                       double* receiver_current,
                                       double receiver_max,
                                       double dt) -> double {
                   if (!provider_current || !receiver_current || provider_rate_per_s <= 0.0) {
                       return 0.0;
                   }
                   const double missing = std::max(0.0, receiver_max - *receiver_current);
                   const double available = std::max(0.0, *provider_current);
                   const double delta = std::min({provider_rate_per_s * dt, missing, available});
                   if (delta <= 0.0) {
                       return 0.0;
                   }
                   *provider_current -= delta;
                   *receiver_current += delta;
                   return delta;
               };

               for (auto i : it) {
                   const bool receiver_needs_any =
                       stores[i].fuel_units_current < stores[i].fuel_units_max - 1.0e-6 ||
                       stores[i].missile_units_current < stores[i].missile_units_max - 1.0e-6 ||
                       stores[i].dry_cargo_units_current < stores[i].dry_cargo_units_max - 1.0e-6;
                   if (!receiver_needs_any) {
                       if (state[i].kind == ResupplyKind::NavalUnderway) {
                           state[i].kind = ResupplyKind::BaseRefuel;
                           state[i].naval_stage = NavalResupplyStage::None;
                           state[i].partner_entity_id = 0;
                           state[i].time_remaining_s = 0.0;
                           state[i].is_refueling = false;
                           state[i].is_rearming = false;
                       }
                       continue;
                   }

                   if (state[i].kind == ResupplyKind::NavalUnderway && state[i].partner_entity_id != 0) {
                       auto provider = it.world().entity(state[i].partner_entity_id);
                       const LogisticsNode* provider_node = provider.get<LogisticsNode>();
                       const Transform* provider_pos = provider.get<Transform>();
                       const Velocity* provider_vel = provider.get<Velocity>();
                       NavalStores* provider_stores = provider.get_mut<NavalStores>();
                       if (!provider.is_valid() || !provider_node || !provider_pos || !provider_vel ||
                           !provider_stores || !provider_node->underway_replenishment_enabled) {
                           state[i].naval_stage = NavalResupplyStage::Aborted;
                       } else {
                           const double dx = pos[i].x - provider_pos->x;
                           const double dy = pos[i].y - provider_pos->y;
                           const double separation_m = std::sqrt(dx * dx + dy * dy);
                           const double dvx = vel[i].vx - provider_vel->vx;
                           const double dvy = vel[i].vy - provider_vel->vy;
                           const double dvz = vel[i].vz - provider_vel->vz;
                           const double rel_speed_mps = std::sqrt(dvx * dvx + dvy * dvy + dvz * dvz);
                           if (separation_m < provider_node->underway_min_separation_m ||
                               separation_m > provider_node->underway_max_separation_m ||
                               rel_speed_mps > provider_node->underway_max_relative_speed_mps) {
                               state[i].naval_stage = NavalResupplyStage::Aborted;
                           } else {
                               if (state[i].naval_stage == NavalResupplyStage::ApproachWindow) {
                                   state[i].naval_stage = NavalResupplyStage::Connected;
                               }
                               if (state[i].naval_stage == NavalResupplyStage::Connected) {
                                   state[i].naval_stage = NavalResupplyStage::Transferring;
                               }
                               if (state[i].naval_stage == NavalResupplyStage::Transferring) {
                                   const double dt = it.delta_time();
                                   const double transferred_fuel = transfer_axis(
                                       &provider_stores->fuel_units_current,
                                       provider_node->transfer_rate_fuel_units_per_s,
                                       &stores[i].fuel_units_current,
                                       stores[i].fuel_units_max,
                                       dt
                                   );
                                   const double transferred_missiles = transfer_axis(
                                       &provider_stores->missile_units_current,
                                       provider_node->transfer_rate_missile_units_per_s,
                                       &stores[i].missile_units_current,
                                       stores[i].missile_units_max,
                                       dt
                                   );
                                   const double transferred_dry = transfer_axis(
                                       &provider_stores->dry_cargo_units_current,
                                       provider_node->transfer_rate_dry_cargo_units_per_s,
                                       &stores[i].dry_cargo_units_current,
                                       stores[i].dry_cargo_units_max,
                                       dt
                                   );
                                   state[i].time_remaining_s = std::max(0.0, state[i].time_remaining_s - dt);
                                   state[i].is_refueling = transferred_fuel > 0.0;
                                   state[i].is_rearming = (transferred_missiles > 0.0) || (transferred_dry > 0.0);

                                   const bool receiver_full =
                                       stores[i].fuel_units_current >= stores[i].fuel_units_max - 1.0e-6 &&
                                       stores[i].missile_units_current >= stores[i].missile_units_max - 1.0e-6 &&
                                       stores[i].dry_cargo_units_current >= stores[i].dry_cargo_units_max - 1.0e-6;
                                   const bool provider_empty =
                                       provider_stores->fuel_units_current <= 1.0e-6 &&
                                       provider_stores->missile_units_current <= 1.0e-6 &&
                                       provider_stores->dry_cargo_units_current <= 1.0e-6;
                                   const bool no_transfer_possible =
                                       transferred_fuel <= 0.0 && transferred_missiles <= 0.0 && transferred_dry <= 0.0;
                                   if (receiver_full || provider_empty || no_transfer_possible ||
                                       state[i].time_remaining_s <= 0.0) {
                                       state[i].naval_stage = NavalResupplyStage::Complete;
                                   }
                               }
                           }
                       }

                       if (state[i].naval_stage == NavalResupplyStage::Complete ||
                           state[i].naval_stage == NavalResupplyStage::Aborted) {
                           state[i].kind = ResupplyKind::BaseRefuel;
                           state[i].partner_entity_id = 0;
                           state[i].time_remaining_s = 0.0;
                           state[i].is_refueling = false;
                           state[i].is_rearming = false;
                           state[i].naval_stage = NavalResupplyStage::None;
                       }
                       continue;
                   }

                   flecs::entity selected_provider;
                   double best_separation = std::numeric_limits<double>::max();
                   for (const auto& provider : providers) {
                       if (provider.entity == it.entity(i)) {
                           continue;
                       }
                       if (provider.fuel_units_current <= 1.0e-6 &&
                           provider.missile_units_current <= 1.0e-6 &&
                           provider.dry_cargo_units_current <= 1.0e-6) {
                           continue;
                       }
                       const double dx = pos[i].x - provider.x;
                       const double dy = pos[i].y - provider.y;
                       const double separation_m = std::sqrt(dx * dx + dy * dy);
                       if (separation_m < provider.node.underway_min_separation_m ||
                           separation_m > provider.node.underway_max_separation_m) {
                           continue;
                       }
                       const double dvx = vel[i].vx - provider.vx;
                       const double dvy = vel[i].vy - provider.vy;
                       const double dvz = vel[i].vz - provider.vz;
                       const double rel_speed_mps = std::sqrt(dvx * dvx + dvy * dvy + dvz * dvz);
                       if (rel_speed_mps > provider.node.underway_max_relative_speed_mps) {
                           continue;
                       }
                       if (separation_m < best_separation) {
                           best_separation = separation_m;
                           selected_provider = provider.entity;
                       }
                   }

                   if (selected_provider.is_valid()) {
                       state[i].time_remaining_s = 20.0 * 60.0;
                       state[i].is_refueling = false;
                       state[i].is_rearming = false;
                       state[i].kind = ResupplyKind::NavalUnderway;
                       state[i].partner_entity_id = selected_provider.id();
                       state[i].naval_stage = NavalResupplyStage::ApproachWindow;
                   }
               }
           }
       });
}
