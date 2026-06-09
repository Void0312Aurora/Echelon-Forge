#pragma once

#include <string>
#include <vector>

enum class NavalWeaponType : int {
    Unknown = 0,
    VlsSam = 1,
    DeckGun = 2,
    Ciws = 3,
};

struct NavalWeaponMountDefinition {
    std::string mount_id;
    NavalWeaponType weapon_type = NavalWeaponType::Unknown;
    int ready_count = 0;
    int max_ready_count = 0;
    int ammo_per_shot = 1;
    double cooldown_s = 0.0;
    double last_fire_time = -1.0;
    double engagement_range_m = 0.0;
    double projectile_speed_mps = 0.0;
    double hit_probability = 0.0;
    double damage_per_hit = 0.0;
    bool consumes_ready_count = true;
    bool can_intercept_missiles = false;
    std::string fire_control_channel;
    std::string target_domain;
    std::string provenance_note;
};

struct NavalWeaponSystem {
    std::vector<NavalWeaponMountDefinition> mounts;
};
