#include "simulation_kernel.h"

flecs::entity SimulationKernel::fire_missile(uint64_t attacker_id, uint64_t target_id) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("fire_missile");
    IWeaponReleaseService *service = weapon_release_service();
    if (service == nullptr) {
        return flecs::entity::null();
    }
    return service->fire_missile(attacker_id, target_id);
}

bool SimulationKernel::fire_naval_weapon(uint64_t attacker_id, uint64_t target_id,
                                         int weapon_type_code) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("fire_naval_weapon");
    IWeaponReleaseService *service = weapon_release_service();
    return service != nullptr &&
           service->fire_naval_weapon(attacker_id, target_id, weapon_type_code);
}
