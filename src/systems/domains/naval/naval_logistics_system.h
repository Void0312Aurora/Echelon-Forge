#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>
#include <flecs.h>

#include "components/basic/common.h"
#include "components/systems/logistics.h"

inline void register_naval_logistics_system(flecs::world& ecs) {
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
