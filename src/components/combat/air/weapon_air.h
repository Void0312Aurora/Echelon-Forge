#pragma once

// Air-owned release latch state used by pilot weapon-release systems.
struct PilotWeaponReleaseState {
    bool fire_weapon_was_down = false;
    bool release_consumed = false;
};
