#pragma once

#include <string>
#include <vector>

// Ground weapon ownership placeholder only. No ground fires runtime consumes
// this shell yet, so it must not be treated as complete ground weapon support.
enum class GroundWeaponType : int {
    Unknown = 0,
};

struct GroundWeapon {
    GroundWeaponType weapon_type = GroundWeaponType::Unknown;
    std::string ownership_note = "ground_weapon_ownership_placeholder";
};

struct GroundWeaponState {
    std::vector<GroundWeapon> weapons;
};
