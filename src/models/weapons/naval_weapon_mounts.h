#pragma once

#include "components/domains/naval/combat/weapon_naval.h"

#include <algorithm>

namespace naval_weapon_mounts {

inline NavalWeaponMountDefinition* select_ready_vls_mount(
    NavalWeaponSystem* system,
    double current_time
) {
    if (!system) {
        return nullptr;
    }
    for (auto& mount : system->mounts) {
        if (mount.weapon_type != NavalWeaponType::VlsSam) continue;
        if (mount.ready_count <= 0) continue;
        if (mount.cooldown_s > 0.0 && mount.last_fire_time >= 0.0 &&
            current_time - mount.last_fire_time < mount.cooldown_s) {
            continue;
        }
        return &mount;
    }
    return nullptr;
}

inline NavalWeaponMountDefinition* select_ready_mount(
    NavalWeaponSystem* system,
    NavalWeaponType weapon_type,
    double current_time
) {
    if (!system) {
        return nullptr;
    }
    for (auto& mount : system->mounts) {
        if (mount.weapon_type != weapon_type) continue;
        const int ammo_per_shot = std::max(1, mount.ammo_per_shot);
        if (mount.consumes_ready_count && mount.ready_count < ammo_per_shot) continue;
        if (mount.cooldown_s > 0.0 && mount.last_fire_time >= 0.0 &&
            current_time - mount.last_fire_time < mount.cooldown_s) {
            continue;
        }
        return &mount;
    }
    return nullptr;
}

inline bool consume_mount_shot(NavalWeaponMountDefinition* mount, double current_time) {
    if (!mount) return false;
    const int ammo_per_shot = std::max(1, mount->ammo_per_shot);
    if (mount->consumes_ready_count) {
        if (mount->ready_count < ammo_per_shot) {
            return false;
        }
        mount->ready_count = std::max(0, mount->ready_count - ammo_per_shot);
    }
    mount->last_fire_time = current_time;
    return true;
}

} // namespace naval_weapon_mounts
