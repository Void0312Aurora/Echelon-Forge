#include "simulation_kernel.h"

#include "components/combat/scoring.h"
#include "components/combat/weapon.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "models/weapons/missile_guidance_types.h"

#include <spdlog/spdlog.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace {
uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

bool contact_matches_target_id(const ContactList* contacts, uint64_t target_id) {
    if (!contacts || target_id == 0) {
        return false;
    }
    for (const auto& c : contacts->contacts) {
        if (c.target_id == target_id) {
            return true;
        }
    }
    return false;
}

const Detection* find_contact_by_target_id(const ContactList* contacts, uint64_t target_id) {
    if (!contacts || target_id == 0) {
        return nullptr;
    }
    for (const auto& c : contacts->contacts) {
        if (c.target_id == target_id) {
            return &c;
        }
    }
    return nullptr;
}

uint64_t select_primary_hostile_contact_id(const ContactList* contacts) {
    if (!contacts) {
        return 0;
    }
    const Detection* best = nullptr;
    for (const auto& c : contacts->contacts) {
        if (c.target_id == 0) {
            continue;
        }
        if (best == nullptr || c.range < best->range) {
            best = &c;
        }
    }
    return best ? best->target_id : 0;
}

bool entity_is_missile(flecs::world& world, uint64_t entity_id) {
    const auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        return false;
    }
    const KeyEntity* key = entity.get<KeyEntity>();
    return entity.has<Missile>() || (key && key->type == UnitType::Missile);
}

bool entity_is_surface_target(flecs::world& world, uint64_t entity_id) {
    const auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        return false;
    }
    const KeyEntity* key = entity.get<KeyEntity>();
    return key && (key->type == UnitType::Ship || key->type == UnitType::Submarine);
}

bool mission_authority_matches_shooter(const MissionCommand* mission, uint64_t shooter_id) {
    if (!mission || !mission->active) {
        return false;
    }
    return mission->engagement_authority_holder_id == 0 ||
        mission->engagement_authority_holder_id == shooter_id;
}

bool mission_explicit_release_target_available(
    const MissionCommand* mission,
    const ContactList* contacts,
    uint64_t shooter_id
) {
    if (!mission || !mission->active || !mission->authorization_to_fire || mission->assigned_target_id == 0) {
        return false;
    }
    if (!mission_authority_matches_shooter(mission, shooter_id)) {
        return false;
    }
    return contact_matches_target_id(contacts, mission->assigned_target_id);
}

uint64_t select_closest_matching_contact_id(
    flecs::world& world,
    const ContactList* contacts,
    bool (*predicate)(flecs::world&, uint64_t)
) {
    if (!contacts || !predicate) {
        return 0;
    }

    const Detection* best = nullptr;
    for (const auto& c : contacts->contacts) {
        if (c.target_id == 0 || !predicate(world, c.target_id)) {
            continue;
        }
        if (best == nullptr || c.range < best->range) {
            best = &c;
        }
    }
    return best ? best->target_id : 0;
}

uint64_t select_ciws_mission_target_id(
    flecs::world& world,
    const ContactList* contacts,
    const MissionCommand* mission
) {
    if (mission && mission->assigned_target_id != 0 &&
        find_contact_by_target_id(contacts, mission->assigned_target_id) != nullptr &&
        entity_is_missile(world, mission->assigned_target_id)) {
        return mission->assigned_target_id;
    }
    return select_closest_matching_contact_id(world, contacts, entity_is_missile);
}

uint64_t select_surface_gun_mission_target_id(
    flecs::world& world,
    const ContactList* contacts,
    const MissionCommand* mission
) {
    if (mission && mission->assigned_target_id != 0 &&
        find_contact_by_target_id(contacts, mission->assigned_target_id) != nullptr &&
        entity_is_surface_target(world, mission->assigned_target_id)) {
        return mission->assigned_target_id;
    }
    return select_closest_matching_contact_id(world, contacts, entity_is_surface_target);
}

double default_propellant_mass_kg(double total_mass_kg) {
    const double scaled = total_mass_kg * MissileGuidanceDefaults::kPropellantMassFraction;
    return std::clamp(
        scaled,
        MissileGuidanceDefaults::kMinPropellantMassKg,
        std::max(MissileGuidanceDefaults::kMinPropellantMassKg, total_mass_kg * 0.55));
}

double default_reference_area_m2() {
    return MissileGuidanceDefaults::kReferenceAreaM2;
}

double default_boost_thrust_n(double total_mass_kg, double max_speed_mps, double current_speed_mps) {
    const double delta_v = std::max(200.0, max_speed_mps - current_speed_mps);
    const double nominal_accel = delta_v / std::max(0.5, MissileGuidanceDefaults::kBoostTimeS);
    return std::max(15000.0, total_mass_kg * nominal_accel * 1.10);
}

double default_sustain_thrust_n(double boost_thrust_n) {
    return boost_thrust_n * 0.35;
}

double finite_or_default(double value, double fallback) {
    return std::isfinite(value) ? value : fallback;
}

NavalWeaponMountDefinition* select_ready_vls_mount(NavalWeaponSystem* system, double current_time) {
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

NavalWeaponMountDefinition* select_ready_mount(
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

bool consume_mount_shot(NavalWeaponMountDefinition* mount, double current_time) {
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
} // namespace

flecs::entity SimulationKernel::fire_missile(uint64_t attacker_id, uint64_t target_id) {
    auto attacker = ecs.entity(attacker_id);
    if (!attacker.is_valid()) {
        spdlog::warn("Invalid attacker ID: {}", attacker_id);
        return flecs::entity::null();
    }
    
    const Transform* p = attacker.get<Transform>();
    const Velocity* v = attacker.get<Velocity>();
    const Alliance* side = attacker.get<Alliance>();
    Ammo* ammo = attacker.get_mut<Ammo>();
    WeaponCooldown* cooldown = attacker.get_mut<WeaponCooldown>();
    NavalWeaponSystem* naval_weapons = attacker.get_mut<NavalWeaponSystem>();
    Score* score = attacker.get_mut<Score>();
    
    if (!p || !v || !side) return flecs::entity::null();

    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    double current_time = info ? (double)info->world_time_total : 0.0;

    const bool has_naval_weapon_system = naval_weapons != nullptr;
    if (!has_naval_weapon_system && cooldown && cooldown->cooldown_s > 0.0 && cooldown->last_fire_time >= 0.0) {
        if (current_time - cooldown->last_fire_time < cooldown->cooldown_s) {
            return flecs::entity::null();
        }
    }

    // Require an active track on the target to fire (prevents blind spam).
    const ContactList* contacts = attacker.get<ContactList>();
    if (!contacts) {
        return flecs::entity::null();
    }
    bool has_track = false;
    Detection det{};
    for (const auto& c : contacts->contacts) {
        if (c.target_id != target_id) continue;
        det = c;
        has_track = true;
        break;
    }
    if (!has_track) {
        return flecs::entity::null();
    }

    NavalWeaponMountDefinition* vls_mount = select_ready_vls_mount(naval_weapons, current_time);
    const bool use_naval_vls = vls_mount != nullptr;
    if (use_naval_vls) {
        if (!consume_mount_shot(vls_mount, current_time)) {
            return flecs::entity::null();
        }
    } else if (naval_weapons) {
        spdlog::warn("Attacker {} has no ready VLS-SAM mount.", attacker_id);
        return flecs::entity::null();
    } else if (ammo) {
        if (ammo->missiles_remaining <= 0) {
            spdlog::warn("Attacker {} has no missiles remaining.", attacker_id);
            return flecs::entity::null();
        }
        ammo->missiles_remaining -= 1;
    }
    if (score) {
        score->missiles_fired += 1;
    }
    if (cooldown && !use_naval_vls) {
        cooldown->last_fire_time = current_time;
    }
    
    double missile_max_speed = 1000.0;
    double missile_turn_rate = 35.0;
    double missile_fuse_distance = 300.0;
    double missile_damage = 120.0;
    double missile_seeker_fov = 180.0;
    double missile_seeker_range = 30000.0;
    double missile_guidance_delay = 0.0;
    double missile_guidance_period = 0.0;
    double missile_max_flight_time = 15.0;
    double missile_nav_gain = 3.0;

    if (use_naval_vls && vls_mount) {
        missile_max_speed = std::max(300.0, vls_mount->projectile_speed_mps);
        missile_turn_rate = 20.0;
        missile_fuse_distance = 120.0;
        missile_damage = 180.0;
        missile_seeker_fov = 120.0;
        missile_seeker_range = std::max(1000.0, vls_mount->engagement_range_m);
        missile_guidance_delay = 1.0;
        missile_guidance_period = 0.2;
        missile_max_flight_time = 80.0;
        missile_nav_gain = 3.5;
    }

    if (std::isfinite(missile_tuning_.max_speed)) missile_max_speed = missile_tuning_.max_speed;
    if (std::isfinite(missile_tuning_.turn_rate)) missile_turn_rate = missile_tuning_.turn_rate;
    if (std::isfinite(missile_tuning_.fuse_distance)) missile_fuse_distance = missile_tuning_.fuse_distance;
    if (std::isfinite(missile_tuning_.damage)) missile_damage = missile_tuning_.damage;
    if (std::isfinite(missile_tuning_.seeker_fov_deg)) missile_seeker_fov = missile_tuning_.seeker_fov_deg;
    if (std::isfinite(missile_tuning_.seeker_lock_range)) missile_seeker_range = missile_tuning_.seeker_lock_range;
    if (std::isfinite(missile_tuning_.guidance_delay_s)) missile_guidance_delay = missile_tuning_.guidance_delay_s;
    if (std::isfinite(missile_tuning_.guidance_update_period_s)) missile_guidance_period = missile_tuning_.guidance_update_period_s;
    if (std::isfinite(missile_tuning_.max_flight_time_s)) missile_max_flight_time = missile_tuning_.max_flight_time_s;
    if (std::isfinite(missile_tuning_.nav_gain)) missile_nav_gain = missile_tuning_.nav_gain;

    double sensor_max_range = missile_seeker_range;
    double sensor_fov_deg = missile_seeker_fov;
    double sensor_scan_period = 0.05;
    double sensor_detection_prob = 0.98;
    double sensor_bearing_noise = 0.2;
    double sensor_range_noise = 10.0;
    double sensor_track_memory = 2.0;

    if (std::isfinite(missile_tuning_.sensor_max_range)) sensor_max_range = missile_tuning_.sensor_max_range;
    if (std::isfinite(missile_tuning_.sensor_fov_deg)) sensor_fov_deg = missile_tuning_.sensor_fov_deg;
    if (std::isfinite(missile_tuning_.sensor_scan_period)) sensor_scan_period = missile_tuning_.sensor_scan_period;
    if (std::isfinite(missile_tuning_.sensor_detection_prob)) sensor_detection_prob = missile_tuning_.sensor_detection_prob;
    if (std::isfinite(missile_tuning_.sensor_bearing_noise_std)) sensor_bearing_noise = missile_tuning_.sensor_bearing_noise_std;
    if (std::isfinite(missile_tuning_.sensor_range_noise_std)) sensor_range_noise = missile_tuning_.sensor_range_noise_std;
    if (std::isfinite(missile_tuning_.sensor_track_memory_s)) sensor_track_memory = missile_tuning_.sensor_track_memory_s;

    const double missile_total_mass_kg = 80.0;
    double propellant_mass_kg = finite_or_default(
        missile_tuning_.propellant_mass_kg,
        default_propellant_mass_kg(missile_total_mass_kg));
    propellant_mass_kg = std::clamp(propellant_mass_kg, 0.0, std::max(0.0, missile_total_mass_kg - 1.0));
    const double empty_mass_kg = std::max(1.0, missile_total_mass_kg - propellant_mass_kg);
    const double reference_area_m2 = std::max(
        1.0e-4,
        finite_or_default(missile_tuning_.reference_area_m2, default_reference_area_m2()));
    const double boost_time_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.boost_time_s, MissileGuidanceDefaults::kBoostTimeS));
    const double sustain_time_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.sustain_time_s, MissileGuidanceDefaults::kSustainTimeS));
    const double track_memory_timeout_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.track_break_time_s, MissileGuidanceDefaults::kTrackMemoryTimeoutS));
    const double bearing_filter_tau_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.bearing_filter_tau_s, MissileGuidanceDefaults::kTrackFilterTauS));
    const double elevation_filter_tau_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.elevation_filter_tau_s, MissileGuidanceDefaults::kTrackFilterTauS));
    const double range_filter_tau_s = std::max(
        0.0,
        finite_or_default(missile_tuning_.range_filter_tau_s, MissileGuidanceDefaults::kTrackFilterTauS));
    const double max_lateral_g = std::max(
        0.1,
        finite_or_default(
            missile_tuning_.max_lateral_g,
            std::clamp(12.0 + 0.4 * std::max(0.0, missile_turn_rate), 12.0, 35.0)));
    const double autopilot_tau_s = std::max(
        1.0e-3,
        finite_or_default(missile_tuning_.autopilot_tau_s, MissileGuidanceDefaults::kAutopilotTauS));
    const double max_accel_response_g_per_s = std::max(
        0.1,
        finite_or_default(
            missile_tuning_.max_accel_response_g_per_s,
            MissileGuidanceDefaults::kAccelResponseGps));
    const double cd0_subsonic = std::max(
        1.0e-4,
        finite_or_default(
            missile_tuning_.cd0_subsonic,
            MissileGuidanceDefaults::kCd0Subsonic));
    const double cd0_supersonic = std::max(
        1.0e-4,
        finite_or_default(
            missile_tuning_.cd0_supersonic,
            MissileGuidanceDefaults::kCd0Supersonic));
    const double induced_drag_k = std::max(
        0.0,
        finite_or_default(
            missile_tuning_.induced_drag_k,
            MissileGuidanceDefaults::kInducedDragScale));
    // Spawn Missile slightly in front
    double heading = std::atan2(v->vy, v->vx);
    double launch_x = p->x + 20.0 * std::cos(heading);
    double launch_y = p->y + 20.0 * std::sin(heading);
    const double launch_speed_mps = std::sqrt(v->vx * v->vx + v->vy * v->vy + v->vz * v->vz);
    const double boost_thrust_n = std::max(
        0.0,
        finite_or_default(
            missile_tuning_.boost_thrust_n,
            default_boost_thrust_n(missile_total_mass_kg, missile_max_speed, launch_speed_mps)));
    const double sustain_thrust_n = std::max(
        0.0,
        finite_or_default(
            missile_tuning_.sustain_thrust_n,
            default_sustain_thrust_n(boost_thrust_n)));

    uint64_t missile_seed = splitmix64(static_cast<uint64_t>(current_time * 1000.0) ^
                                       (attacker_id * 0x9e3779b97f4a7c15ULL) ^
                                       (target_id * 0xbf58476d1ce4e5b9ULL));

    Mass mass{};
    mass.empty_mass_kg = empty_mass_kg;
    mass.fuel_mass_kg = propellant_mass_kg;
    mass.stores_mass_kg = 0.0;

    MassProperties mass_properties{};
    mass_properties.empty_mass_kg = empty_mass_kg;
    mass_properties.current_total_mass_kg = mass.get_total_kg();
    mass_properties.base_drag_index = 0.0;
    mass_properties.current_drag_index = 0.0;
    mass_properties.reference_area_m2 = reference_area_m2;

    Missile missile{
        attacker_id,
        target_id,
        missile_max_speed,
        missile_turn_rate,
        missile_fuse_distance,
        missile_damage,
        missile_seeker_fov,
        missile_seeker_range,
        missile_guidance_delay,
        missile_guidance_period,
        -1.0,
        current_time,
        missile_max_flight_time,
        missile_nav_gain,
        true,
        missile_seed,
        std::numeric_limits<double>::infinity(),
        std::numeric_limits<double>::infinity(),
        false
    };
    missile.p0_runtime_initialized = true;
    missile.seeker_has_valid_track = true;
    missile.seeker_has_range = det.range > 1.0e-3;
    missile.seeker_mode = static_cast<int>(MissileSeekerMode::Track);
    missile.filtered_bearing_deg = det.bearing;
    missile.filtered_elevation_deg = det.elevation;
    missile.filtered_range_m = std::max(0.0, det.range);
    missile.filtered_closing_speed_mps = det.closing_speed;
    missile.bearing_rate_deg_s = 0.0;
    missile.elevation_rate_deg_s = 0.0;
    missile.last_track_time_s = current_time;
    missile.track_memory_timeout_s = track_memory_timeout_s;
    missile.current_speed_mps = launch_speed_mps;
    missile.commanded_lateral_accel_mps2 = 0.0;
    missile.achieved_lateral_accel_mps2 = 0.0;
    missile.burnout_time_s = current_time + boost_time_s + sustain_time_s;
    missile.boost_duration_s = boost_time_s;
    missile.sustain_duration_s = sustain_time_s;
    missile.guidance_bearing_filter_tau_s = bearing_filter_tau_s;
    missile.guidance_elevation_filter_tau_s = elevation_filter_tau_s;
    missile.guidance_range_filter_tau_s = range_filter_tau_s;
    missile.guidance_boost_thrust_n = boost_thrust_n;
    missile.guidance_sustain_thrust_n = sustain_thrust_n;
    missile.guidance_cd0_subsonic = cd0_subsonic;
    missile.guidance_cd0_supersonic = cd0_supersonic;
    missile.guidance_induced_drag_k = induced_drag_k;
    missile.guidance_max_lateral_g = max_lateral_g;
    missile.guidance_autopilot_tau_s = autopilot_tau_s;
    missile.guidance_max_accel_response_g_per_s = max_accel_response_g_per_s;

    Sensor sensor{};
    sensor.max_range = sensor_max_range;
    sensor.fov_deg = sensor_fov_deg;
    sensor.scan_period = sensor_scan_period;
    sensor.last_scan_time = -1.0;
    sensor.detection_prob = sensor_detection_prob;
    sensor.range_power = 2.0;
    sensor.bearing_noise_std = sensor_bearing_noise;
    sensor.range_noise_std = sensor_range_noise;
    sensor.track_memory_s = sensor_track_memory;
    sensor.aspect_influence = 0.2;
    sensor.doppler_notch_width = 20.0;
    sensor.reference_snr_db = 13.0;
    sensor.reference_range_m = std::max(1000.0, sensor_max_range);
    sensor.reference_rcs_m2 = 5.0;
    sensor.pfa = 1.0e-6;
    sensor.confirm_hits_m = 2;
    sensor.confirm_window_n = 3;
    sensor.velocity_noise_std = 3.0;
    sensor.alpha_beta_alpha = 0.65;
    sensor.alpha_beta_beta = 0.12;
    sensor.antenna_height_m = 10.0;
    sensor.target_height_bias_m = 5.0;
    sensor.sea_clutter_sensitivity = 0.0;
    sensor.sea_state_loss_per_level = 0.0;
    sensor.ducting_gain_factor = 1.0;
    sensor.ducting_max_bonus_m = 0.0;
    sensor.bearing_only_min_range_m = 0.0;
    sensor.environment_domain = static_cast<int>(SensorEnvironmentDomain::Air);
    sensor.enforce_radar_horizon = false;
    sensor.enable_ducting = false;
    sensor.sea_clutter_enabled = false;
    sensor.bearing_only = false;
    sensor.type = missile_tuning_.seeker_type >= 0
        ? missile_tuning_.seeker_type
        : static_cast<int>(sensor_max_range > 8000.0 ? SensorType::Radar : SensorType::Infrared);

    auto m = ecs.entity()
        .set<Transform>({launch_x, launch_y, p->z, p->heading, 0, 0})
        .set<Velocity>({v->vx, v->vy, v->vz}) // Inherit platform velocity
        .set<Alliance>({side->side})
        .set<KeyEntity>({UnitType::Missile})
        .set<Mass>(mass)
        .set<MassProperties>(mass_properties)
        .set<ForceAccumulator>({})
        .set<Missile>(missile)
        .set<Sensor>(sensor)
        .set<ContactList>({})
        .add<SimObject>(); // Tag for cleanup
        
    spdlog::info("FOX 2! Missile {} fired by {} at {}", m.id(), attacker_id, target_id);
    return m;
}

bool SimulationKernel::fire_naval_weapon(uint64_t attacker_id, uint64_t target_id, int weapon_type_code) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* attacker_pos = attacker.get<Transform>();
    const Transform* target_pos = target.get<Transform>();
    const ContactList* contacts = attacker.get<ContactList>();
    NavalWeaponSystem* naval_weapons = attacker.get_mut<NavalWeaponSystem>();
    Score* score = attacker.get_mut<Score>();
    if (!attacker_pos || !target_pos || !contacts || !naval_weapons) {
        return false;
    }

    Detection det{};
    bool has_track = false;
    for (const auto& c : contacts->contacts) {
        if (c.target_id != target_id) continue;
        det = c;
        has_track = true;
        break;
    }
    if (!has_track) {
        return false;
    }

    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const NavalWeaponType weapon_type = static_cast<NavalWeaponType>(weapon_type_code);
    NavalWeaponMountDefinition* mount = select_ready_mount(naval_weapons, weapon_type, current_time);
    if (!mount) {
        return false;
    }

    if (det.range > mount->engagement_range_m && mount->engagement_range_m > 0.0) {
        return false;
    }
    if (!consume_mount_shot(mount, current_time)) {
        return false;
    }

    double hit_probability = std::clamp(mount->hit_probability, 0.05, 0.99);
    const bool target_is_missile = entity_is_missile(ecs, target_id);
    if (weapon_type == NavalWeaponType::Ciws && mount->can_intercept_missiles && target_is_missile) {
        const double close_range_threshold_m = std::max(300.0, mount->engagement_range_m * 0.75);
        if (det.range <= close_range_threshold_m) {
            hit_probability = 1.0;
        }
    }
    uint64_t rng_state = splitmix64(static_cast<uint64_t>(current_time * 1000.0) ^
                                    (attacker_id * 0x9e3779b97f4a7c15ULL) ^
                                    (target_id * 0xbf58476d1ce4e5b9ULL) ^
                                    (static_cast<uint64_t>(weapon_type_code) << 32));
    const double u = (splitmix64(rng_state) >> 11) * (1.0 / 9007199254740992.0);
    const bool hit = u <= hit_probability;

    if (weapon_type == NavalWeaponType::Ciws && mount->can_intercept_missiles && target_is_missile) {
        if (hit) {
            target.destruct();
            if (score) {
                score->hits_landed += 1;
                score->kills_confirmed += 1;
            }
            return true;
        }
        return false;
    }

    if (!hit) {
        return false;
    }

    const double applied_damage = mount->damage_per_hit > 0.0 ? mount->damage_per_hit : 60.0;
    const double fuse_distance = weapon_type == NavalWeaponType::DeckGun ? 25.0 : 40.0;
    return debug_apply_proximity_hit(attacker_id, target_id, applied_damage, fuse_distance);
}

bool SimulationKernel::try_fire_naval_mission_weapon(uint64_t attacker_id) {
    auto attacker = ecs.entity(attacker_id);
    if (!attacker.is_valid()) {
        return false;
    }

    const MissionCommand* mission = attacker.get<MissionCommand>();
    const ContactList* contacts = attacker.get<ContactList>();
    const NavalWeaponSystem* naval_weapons = attacker.get<NavalWeaponSystem>();
    if (!mission || !mission->active || !contacts || !naval_weapons || naval_weapons->mounts.empty()) {
        return false;
    }
    if (!mission->authorization_to_fire || !mission_authority_matches_shooter(mission, attacker_id)) {
        return false;
    }

    uint64_t target_id = 0;
    int weapon_type_code = 0;
    switch (mission->command_code) {
        case kMissionCommandCodeNavalAutoCloseInDefense:
            target_id = select_ciws_mission_target_id(ecs, contacts, mission);
            weapon_type_code = static_cast<int>(NavalWeaponType::Ciws);
            break;
        case kMissionCommandCodeNavalSurfaceEngage:
            target_id = select_surface_gun_mission_target_id(ecs, contacts, mission);
            weapon_type_code = static_cast<int>(NavalWeaponType::DeckGun);
            break;
        default:
            return false;
    }

    if (target_id == 0) {
        return false;
    }
    return fire_naval_weapon(attacker_id, target_id, weapon_type_code);
}

flecs::entity SimulationKernel::fire_weapon_from_pilot_action(uint64_t attacker_id) {
    auto attacker = ecs.entity(attacker_id);
    if (!attacker.is_valid()) {
        return flecs::entity::null();
    }

    const PilotAction* pilot = attacker.get<PilotAction>();
    if (!pilot || !pilot->active || !pilot->master_arm || !pilot->fire_weapon) {
        return flecs::entity::null();
    }

    const MissionCommand* mission = attacker.get<MissionCommand>();
    if (mission && !mission->active) {
        mission = nullptr;
    }
    const ContactList* contacts = attacker.get<ContactList>();

    const int roe_state = mission ? mission->roe_state : 0;
    uint64_t target_id = 0;

    if (mission_explicit_release_target_available(mission, contacts, attacker_id)) {
        target_id = mission->assigned_target_id;
    }

    if (target_id == 0 && (roe_state == 0 || roe_state >= 3)) {
        target_id = select_primary_hostile_contact_id(contacts);
    }
    if (target_id == 0) {
        return flecs::entity::null();
    }
    return fire_missile(attacker_id, target_id);
}
