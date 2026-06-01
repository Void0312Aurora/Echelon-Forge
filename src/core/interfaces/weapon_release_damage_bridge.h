#pragma once

#include <cstdint>

class IWeaponReleaseDamageBridge {
public:
    virtual ~IWeaponReleaseDamageBridge() = default;

    virtual bool apply_proximity_hit(
        std::uint64_t attacker_id,
        std::uint64_t target_id,
        double damage,
        double fuse_distance
    ) = 0;
};
