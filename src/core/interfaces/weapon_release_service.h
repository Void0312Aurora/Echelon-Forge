#pragma once

#include <cstdint>

#include <flecs.h>

class IWeaponReleaseService {
public:
    virtual ~IWeaponReleaseService() = default;

    virtual flecs::entity fire_weapon_from_pilot_action(std::uint64_t attacker_id) = 0;
    virtual bool fire_naval_weapon_from_mission_command(std::uint64_t attacker_id) = 0;
};
