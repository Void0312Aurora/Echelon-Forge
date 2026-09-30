#pragma once

#include <cstdint>
#include <limits>
#include <vector>

// Bounded ground direct-fire ownership slice. This is intentionally a small
// data contract for deterministic close-range infantry training; it does not
// encode ballistics, line of sight, cover, suppression, or combined-arms fire
// control.
enum class GroundWeaponType : int {
    Unknown = 0,
    Rifle = 1,
};

inline constexpr double kGroundWeaponNeverFiredTimeS = -1.0;

struct GroundWeapon {
    GroundWeaponType weapon_type = GroundWeaponType::Rifle;
    int ammunition = 0;
    int maximum_ammunition = 0;
    double damage_per_hit = 0.0;
    double engagement_range_m = 0.0;
    double hit_probability = 0.0;
    double cooldown_s = 0.0;
    double last_fire_time_s = kGroundWeaponNeverFiredTimeS;
};

struct GroundWeaponState {
    std::vector<GroundWeapon> weapons;
    std::int32_t selected_weapon_index = 0;
};

[[nodiscard]] inline GroundWeaponState make_default_ground_infantry_weapon_state() {
    GroundWeaponState state{};
    state.weapons.push_back({
        .weapon_type = GroundWeaponType::Rifle,
        .ammunition = 30,
        .maximum_ammunition = 30,
        .damage_per_hit = 8.0,
        .engagement_range_m = 300.0,
        .hit_probability = 1.0,
        .cooldown_s = 0.5,
        .last_fire_time_s = kGroundWeaponNeverFiredTimeS,
    });
    return state;
}
