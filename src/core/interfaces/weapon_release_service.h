#pragma once

#include <cstdint>

#include <flecs.h>

class IWeaponReleaseService {
public:
    virtual ~IWeaponReleaseService() = default;

    virtual flecs::entity fire_missile(
        std::uint64_t attacker_id,
        std::uint64_t target_id
    ) = 0;
    virtual bool fire_naval_weapon(
        std::uint64_t attacker_id,
        std::uint64_t target_id,
        int weapon_type_code
    ) = 0;
    virtual flecs::entity fire_weapon_from_pilot_action(std::uint64_t attacker_id) = 0;
    virtual bool fire_naval_weapon_from_mission_command(std::uint64_t attacker_id) = 0;
};
