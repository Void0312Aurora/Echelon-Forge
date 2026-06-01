#include "simulation_kernel.h"

flecs::entity SimulationKernel::fire_missile(uint64_t attacker_id, uint64_t target_id) {
    if (!weapon_release_service_) {
        return flecs::entity::null();
    }
    return weapon_release_service_->fire_missile(attacker_id, target_id);
}

bool SimulationKernel::fire_naval_weapon(
    uint64_t attacker_id,
    uint64_t target_id,
    int weapon_type_code
) {
    return weapon_release_service_ &&
        weapon_release_service_->fire_naval_weapon(attacker_id, target_id, weapon_type_code);
}
