#pragma once

#include <cstdint>

class IWeaponReleaseDamageBridge {
  public:
    virtual ~IWeaponReleaseDamageBridge() = default;

    virtual bool apply_proximity_hit(std::uint64_t attacker_id, std::uint64_t target_id,
                                     double damage, double fuse_distance) = 0;

    // Bounded direct-hit path used by native ground weapons. The provider
    // keeps the actual effects and event recording in the shared damage model.
    virtual bool apply_direct_hit(std::uint64_t attacker_id, std::uint64_t target_id,
                                  double damage) = 0;
};
