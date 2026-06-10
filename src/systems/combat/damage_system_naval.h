#pragma once

#include <flecs.h>
#include <algorithm>

#include "systems/combat/damage_system_common.h"

#include "components/combat/health.h"
#include "components/domains/naval/combat/damage_naval.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/physics/dynamics.h"

inline void register_naval_damage_system(flecs::world &ecs) {
    ecs.system<Health, PlatformDamageState, const ShipPlatform>("NavalDamageStateUpdate")
        .kind(flecs::OnUpdate)
        .each([](flecs::entity e, Health &health, PlatformDamageState &damage,
                 const ShipPlatform &ship) {
            const double fire_decay = 0.0008;
            const double flooding_decay = 0.0002;
            const double breach_decay = 0.0001;

            const double fire_progress = damage.fire_severity;
            const double flooding_progress = damage.flooding_severity;
            const double breach_progress = damage.ongoing_hull_breach;

            damage.fire_severity = std::clamp(damage.fire_severity - fire_decay, 0.0, 1.0);
            damage.flooding_severity = std::clamp(
                damage.flooding_severity + 0.003 * breach_progress - flooding_decay, 0.0, 1.0);
            damage.ongoing_hull_breach =
                std::clamp(damage.ongoing_hull_breach - breach_decay, 0.0, 1.0);

            damage.mission_capability -= 0.0015 * fire_progress;
            damage.sensor_capability -= 0.0012 * fire_progress;
            damage.mobility_capability -= 0.0018 * flooding_progress;
            damage.survivability_margin -= 0.0022 * flooding_progress + 0.0010 * fire_progress;

            sync_platform_damage_loss_state(health, damage);

            if (Propulsion *propulsion = e.get_mut<Propulsion>()) {
                const double mobility_scale = std::clamp(damage.mobility_capability, 0.2, 1.0);
                propulsion->mil_thrust_n = std::min(propulsion->mil_thrust_n,
                                                    ship.max_speed_mps * 100000.0 * mobility_scale);
                propulsion->ab_thrust_n = std::min(propulsion->ab_thrust_n,
                                                   ship.max_speed_mps * 120000.0 * mobility_scale);
            }

            if (damage.loss_state == PlatformLossState::Lost) {
                health.current_hp = 0.0;
                e.destruct();
            }
        });
}
