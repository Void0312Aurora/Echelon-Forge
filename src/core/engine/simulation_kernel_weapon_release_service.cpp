#include "simulation_kernel_weapon_release_service.h"
#include "simulation_kernel_missile_tuning.h"

#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/engagement_launch_recorder.h"

#include "components/basic/tags.h"
#include "components/combat/scoring.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/logistics.h"
#include "components/systems/sensor.h"
#include "content/unit_definition.h"
#include "core/interfaces/unit_factory.h"
#include "models/weapons/missile_guidance_types.h"
#include "models/weapons/naval_weapon_mounts.h"

#include <spdlog/spdlog.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <utility>

namespace {
uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

bool contact_matches_target_id(const ContactList *contacts, uint64_t target_id) {
    if (!contacts || target_id == 0) {
        return false;
    }
    for (const auto &c : contacts->contacts) {
        if (c.target_id == target_id) {
            return true;
        }
    }
    return false;
}

const Detection *find_contact_by_target_id(const ContactList *contacts, uint64_t target_id) {
    if (!contacts || target_id == 0) {
        return nullptr;
    }
    for (const auto &c : contacts->contacts) {
        if (c.target_id == target_id) {
            return &c;
        }
    }
    return nullptr;
}

bool entity_is_missile(flecs::world &world, uint64_t entity_id) {
    const auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        return false;
    }
    const KeyEntity *key = entity.get<KeyEntity>();
    return entity.has<Missile>() || (key && key->type == UnitType::Missile);
}

bool entity_is_surface_target(flecs::world &world, uint64_t entity_id) {
    const auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        return false;
    }
    const KeyEntity *key = entity.get<KeyEntity>();
    return key && (key->type == UnitType::Ship || key->type == UnitType::Submarine);
}

bool mission_authority_matches_shooter(const MissionCommand *mission, uint64_t shooter_id) {
    if (!mission || !mission->active) {
        return false;
    }
    return mission->engagement_authority_holder_id == 0 ||
           mission->engagement_authority_holder_id == shooter_id;
}

bool mission_explicit_release_target_available(const MissionCommand *mission,
                                               const ContactList *contacts, uint64_t shooter_id) {
    if (!mission || !mission->active || !mission->authorization_to_fire ||
        mission->assigned_target_id == 0) {
        return false;
    }
    if (!mission_authority_matches_shooter(mission, shooter_id)) {
        return false;
    }
    return contact_matches_target_id(contacts, mission->assigned_target_id);
}

uint64_t select_closest_matching_contact_id(flecs::world &world, const ContactList *contacts,
                                            bool (*predicate)(flecs::world &, uint64_t)) {
    if (!contacts || !predicate) {
        return 0;
    }

    const Detection *best = nullptr;
    for (const auto &c : contacts->contacts) {
        if (c.target_id == 0 || !predicate(world, c.target_id)) {
            continue;
        }
        if (best == nullptr || c.range < best->range) {
            best = &c;
        }
    }
    return best ? best->target_id : 0;
}

uint64_t select_ciws_mission_target_id(flecs::world &world, const ContactList *contacts,
                                       const MissionCommand *mission) {
    if (mission && mission->assigned_target_id != 0 &&
        find_contact_by_target_id(contacts, mission->assigned_target_id) != nullptr) {
        const auto assigned_target = world.entity(mission->assigned_target_id);
        if (!assigned_target.is_valid() || entity_is_missile(world, mission->assigned_target_id)) {
            return mission->assigned_target_id;
        }
    }
    return select_closest_matching_contact_id(world, contacts, entity_is_missile);
}

uint64_t select_surface_gun_mission_target_id(flecs::world &world, const ContactList *contacts,
                                              const MissionCommand *mission) {
    if (mission && mission->assigned_target_id != 0 &&
        find_contact_by_target_id(contacts, mission->assigned_target_id) != nullptr) {
        const auto assigned_target = world.entity(mission->assigned_target_id);
        if (!assigned_target.is_valid() ||
            entity_is_surface_target(world, mission->assigned_target_id)) {
            return mission->assigned_target_id;
        }
    }
    return select_closest_matching_contact_id(world, contacts, entity_is_surface_target);
}

double default_propellant_mass_kg(double total_mass_kg) {
    const double scaled = total_mass_kg * MissileGuidanceDefaults::kPropellantMassFraction;
    return std::clamp(
        scaled, MissileGuidanceDefaults::kMinPropellantMassKg,
        std::max(MissileGuidanceDefaults::kMinPropellantMassKg, total_mass_kg * 0.55));
}

double default_reference_area_m2() {
    return MissileGuidanceDefaults::kReferenceAreaM2;
}

double fallback_max_lateral_g(double turn_rate_deg_s) {
    return std::clamp(12.0 + 0.4 * std::max(0.0, turn_rate_deg_s), 12.0, 35.0);
}

double default_boost_thrust_n(double total_mass_kg, double max_speed_mps,
                              double current_speed_mps) {
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

double positive_or_default(double value, double fallback) {
    return (std::isfinite(value) && value > 0.0) ? value : fallback;
}

double nonnegative_or_default(double value, double fallback) {
    return (std::isfinite(value) && value >= 0.0) ? value : fallback;
}

bool has_explicit_global_missile_tuning(const MissileTuning &tuning) {
    return std::isfinite(tuning.max_speed) || std::isfinite(tuning.turn_rate) ||
           std::isfinite(tuning.fuse_distance) || std::isfinite(tuning.damage) ||
           std::isfinite(tuning.seeker_fov_deg) || std::isfinite(tuning.seeker_lock_range) ||
           std::isfinite(tuning.guidance_delay_s) ||
           std::isfinite(tuning.guidance_update_period_s) ||
           std::isfinite(tuning.max_flight_time_s) || std::isfinite(tuning.nav_gain) ||
           std::isfinite(tuning.sensor_max_range) || std::isfinite(tuning.sensor_fov_deg) ||
           std::isfinite(tuning.sensor_scan_period) ||
           std::isfinite(tuning.sensor_detection_prob) ||
           std::isfinite(tuning.sensor_bearing_noise_std) ||
           std::isfinite(tuning.sensor_range_noise_std) ||
           std::isfinite(tuning.sensor_track_memory_s) || tuning.seeker_type >= 0 ||
           std::isfinite(tuning.seeker_activation_range_m) ||
           std::isfinite(tuning.seeker_gimbal_limit_deg) || std::isfinite(tuning.seeker_ifov_deg) ||
           std::isfinite(tuning.bearing_filter_tau_s) ||
           std::isfinite(tuning.elevation_filter_tau_s) ||
           std::isfinite(tuning.range_filter_tau_s) || std::isfinite(tuning.track_break_time_s) ||
           std::isfinite(tuning.boost_time_s) || std::isfinite(tuning.sustain_time_s) ||
           std::isfinite(tuning.boost_thrust_n) || std::isfinite(tuning.sustain_thrust_n) ||
           std::isfinite(tuning.reference_area_m2) || std::isfinite(tuning.cd0_subsonic) ||
           std::isfinite(tuning.cd0_supersonic) || std::isfinite(tuning.induced_drag_k) ||
           std::isfinite(tuning.propellant_mass_kg) || std::isfinite(tuning.max_lateral_g) ||
           std::isfinite(tuning.autopilot_tau_s) ||
           std::isfinite(tuning.max_accel_response_g_per_s) ||
           std::isfinite(tuning.min_launch_range_m) ||
           std::isfinite(tuning.max_launch_off_boresight_deg) || tuning.lobl_required ||
           tuning.midcourse_datalink_supported || tuning.has_warhead_profile ||
           tuning.has_fuze_profile;
}

std::string naval_weapon_type_name(NavalWeaponType weapon_type) {
    switch (weapon_type) {
    case NavalWeaponType::VlsSam:
        return "naval:vls_sam";
    case NavalWeaponType::DeckGun:
        return "naval:deck_gun";
    case NavalWeaponType::Ciws:
        return "naval:ciws";
    case NavalWeaponType::Unknown:
        break;
    }
    return "naval:unknown";
}

MissileTuning to_runtime_missile_tuning(const MissileTuningDefinition &src) {
    MissileTuning out{};
    out.max_speed = src.max_speed;
    out.turn_rate = src.turn_rate;
    out.fuse_distance = src.fuse_distance;
    out.damage = src.damage;
    out.seeker_fov_deg = src.seeker_fov_deg;
    out.seeker_lock_range = src.seeker_lock_range;
    out.guidance_delay_s = src.guidance_delay_s;
    out.guidance_update_period_s = src.guidance_update_period_s;
    out.max_flight_time_s = src.max_flight_time_s;
    out.nav_gain = src.nav_gain;
    out.sensor_max_range = src.sensor_max_range;
    out.sensor_fov_deg = src.sensor_fov_deg;
    out.sensor_scan_period = src.sensor_scan_period;
    out.sensor_detection_prob = src.sensor_detection_prob;
    out.sensor_bearing_noise_std = src.sensor_bearing_noise_std;
    out.sensor_range_noise_std = src.sensor_range_noise_std;
    out.sensor_track_memory_s = src.sensor_track_memory_s;
    out.seeker_type = src.seeker_type;
    out.seeker_activation_range_m = src.seeker_activation_range_m;
    out.seeker_gimbal_limit_deg = src.seeker_gimbal_limit_deg;
    out.seeker_ifov_deg = src.seeker_ifov_deg;
    out.bearing_filter_tau_s = src.bearing_filter_tau_s;
    out.elevation_filter_tau_s = src.elevation_filter_tau_s;
    out.range_filter_tau_s = src.range_filter_tau_s;
    out.track_break_time_s = src.track_break_time_s;
    out.boost_time_s = src.boost_time_s;
    out.sustain_time_s = src.sustain_time_s;
    out.boost_thrust_n = src.boost_thrust_n;
    out.sustain_thrust_n = src.sustain_thrust_n;
    out.reference_area_m2 = src.reference_area_m2;
    out.cd0_subsonic = src.cd0_subsonic;
    out.cd0_supersonic = src.cd0_supersonic;
    out.induced_drag_k = src.induced_drag_k;
    out.propellant_mass_kg = src.propellant_mass_kg;
    out.max_lateral_g = src.max_lateral_g;
    out.autopilot_tau_s = src.autopilot_tau_s;
    out.max_accel_response_g_per_s = src.max_accel_response_g_per_s;
    out.min_launch_range_m = src.min_launch_range_m;
    out.max_launch_off_boresight_deg = src.max_launch_off_boresight_deg;
    out.lobl_required = src.lobl_required;
    out.midcourse_datalink_supported = src.midcourse_datalink_supported;
    out.warhead_profile = src.warhead_profile;
    out.has_warhead_profile = src.has_warhead_profile;
    out.fuze_profile = src.fuze_profile;
    out.has_fuze_profile = src.has_fuze_profile;
    return out;
}

void overlay_missile_tuning(MissileTuning *base, const MissileTuning &overlay) {
    if (!base) {
        return;
    }
    if (std::isfinite(overlay.max_speed)) base->max_speed = overlay.max_speed;
    if (std::isfinite(overlay.turn_rate)) base->turn_rate = overlay.turn_rate;
    if (std::isfinite(overlay.fuse_distance)) base->fuse_distance = overlay.fuse_distance;
    if (std::isfinite(overlay.damage)) base->damage = overlay.damage;
    if (std::isfinite(overlay.seeker_fov_deg)) base->seeker_fov_deg = overlay.seeker_fov_deg;
    if (std::isfinite(overlay.seeker_lock_range))
        base->seeker_lock_range = overlay.seeker_lock_range;
    if (std::isfinite(overlay.guidance_delay_s)) base->guidance_delay_s = overlay.guidance_delay_s;
    if (std::isfinite(overlay.guidance_update_period_s))
        base->guidance_update_period_s = overlay.guidance_update_period_s;
    if (std::isfinite(overlay.max_flight_time_s))
        base->max_flight_time_s = overlay.max_flight_time_s;
    if (std::isfinite(overlay.nav_gain)) base->nav_gain = overlay.nav_gain;
    if (std::isfinite(overlay.sensor_max_range)) base->sensor_max_range = overlay.sensor_max_range;
    if (std::isfinite(overlay.sensor_fov_deg)) base->sensor_fov_deg = overlay.sensor_fov_deg;
    if (std::isfinite(overlay.sensor_scan_period))
        base->sensor_scan_period = overlay.sensor_scan_period;
    if (std::isfinite(overlay.sensor_detection_prob))
        base->sensor_detection_prob = overlay.sensor_detection_prob;
    if (std::isfinite(overlay.sensor_bearing_noise_std))
        base->sensor_bearing_noise_std = overlay.sensor_bearing_noise_std;
    if (std::isfinite(overlay.sensor_range_noise_std))
        base->sensor_range_noise_std = overlay.sensor_range_noise_std;
    if (std::isfinite(overlay.sensor_track_memory_s))
        base->sensor_track_memory_s = overlay.sensor_track_memory_s;
    if (overlay.seeker_type >= 0) base->seeker_type = overlay.seeker_type;
    if (std::isfinite(overlay.seeker_activation_range_m))
        base->seeker_activation_range_m = overlay.seeker_activation_range_m;
    if (std::isfinite(overlay.seeker_gimbal_limit_deg))
        base->seeker_gimbal_limit_deg = overlay.seeker_gimbal_limit_deg;
    if (std::isfinite(overlay.seeker_ifov_deg)) base->seeker_ifov_deg = overlay.seeker_ifov_deg;
    if (std::isfinite(overlay.bearing_filter_tau_s))
        base->bearing_filter_tau_s = overlay.bearing_filter_tau_s;
    if (std::isfinite(overlay.elevation_filter_tau_s))
        base->elevation_filter_tau_s = overlay.elevation_filter_tau_s;
    if (std::isfinite(overlay.range_filter_tau_s))
        base->range_filter_tau_s = overlay.range_filter_tau_s;
    if (std::isfinite(overlay.track_break_time_s))
        base->track_break_time_s = overlay.track_break_time_s;
    if (std::isfinite(overlay.boost_time_s)) base->boost_time_s = overlay.boost_time_s;
    if (std::isfinite(overlay.sustain_time_s)) base->sustain_time_s = overlay.sustain_time_s;
    if (std::isfinite(overlay.boost_thrust_n)) base->boost_thrust_n = overlay.boost_thrust_n;
    if (std::isfinite(overlay.sustain_thrust_n)) base->sustain_thrust_n = overlay.sustain_thrust_n;
    if (std::isfinite(overlay.reference_area_m2))
        base->reference_area_m2 = overlay.reference_area_m2;
    if (std::isfinite(overlay.cd0_subsonic)) base->cd0_subsonic = overlay.cd0_subsonic;
    if (std::isfinite(overlay.cd0_supersonic)) base->cd0_supersonic = overlay.cd0_supersonic;
    if (std::isfinite(overlay.induced_drag_k)) base->induced_drag_k = overlay.induced_drag_k;
    if (std::isfinite(overlay.propellant_mass_kg))
        base->propellant_mass_kg = overlay.propellant_mass_kg;
    if (std::isfinite(overlay.max_lateral_g)) base->max_lateral_g = overlay.max_lateral_g;
    if (std::isfinite(overlay.autopilot_tau_s)) base->autopilot_tau_s = overlay.autopilot_tau_s;
    if (std::isfinite(overlay.max_accel_response_g_per_s))
        base->max_accel_response_g_per_s = overlay.max_accel_response_g_per_s;
    if (std::isfinite(overlay.min_launch_range_m))
        base->min_launch_range_m = overlay.min_launch_range_m;
    if (std::isfinite(overlay.max_launch_off_boresight_deg))
        base->max_launch_off_boresight_deg = overlay.max_launch_off_boresight_deg;
    if (overlay.lobl_required) base->lobl_required = true;
    if (overlay.midcourse_datalink_supported) base->midcourse_datalink_supported = true;
    if (overlay.has_fuze_profile) {
        base->fuze_profile = overlay.fuze_profile;
        base->has_fuze_profile = true;
        if (std::isfinite(overlay.fuze_profile.trigger_radius_m)) {
            base->fuse_distance = overlay.fuze_profile.trigger_radius_m;
        }
    }
    if (overlay.has_warhead_profile) {
        base->warhead_profile = overlay.warhead_profile;
        base->has_warhead_profile = true;
        if (std::isfinite(overlay.warhead_profile.lethal_radius_m)) {
            base->fuse_distance = overlay.warhead_profile.lethal_radius_m;
        }
        if (std::isfinite(overlay.warhead_profile.damage_scalar)) {
            base->damage = overlay.warhead_profile.damage_scalar;
        }
    }
}

std::optional<std::string> platform_definition_name_from_munition_name(const char *munition_name,
                                                                       int station_id) {
    if (!munition_name || station_id <= 0) {
        return std::nullopt;
    }
    const std::string suffix = "_Stn_" + std::to_string(station_id);
    const std::string full_name = munition_name;
    if (full_name.size() <= suffix.size()) {
        return std::nullopt;
    }
    if (full_name.rfind(suffix) != full_name.size() - suffix.size()) {
        return std::nullopt;
    }
    return full_name.substr(0, full_name.size() - suffix.size());
}

bool missile_launch_envelope_allows(const MissileTuning &tuning, const Detection &det) {
    if (std::isfinite(tuning.min_launch_range_m) && tuning.min_launch_range_m > 0.0 &&
        det.range < tuning.min_launch_range_m) {
        return false;
    }
    if (std::isfinite(tuning.max_launch_off_boresight_deg) &&
        tuning.max_launch_off_boresight_deg >= 0.0 &&
        std::abs(det.bearing) > tuning.max_launch_off_boresight_deg) {
        return false;
    }
    if (tuning.lobl_required && (!det.local_sensor_hit || det.range <= 0.0)) {
        return false;
    }
    return true;
}

} // namespace

SimulationKernelWeaponReleaseService::SimulationKernelWeaponReleaseService(
    flecs::world &ecs, const std::unique_ptr<IUnitFactory> &unit_factory,
    MissileTuning &missile_tuning, IEngagementLaunchRecorder &launch_recorder,
    IEngagementEventRecorder &damage_recorder, IWeaponReleaseDamageBridge &damage_bridge)
    : ecs_(ecs), unit_factory_(unit_factory), missile_tuning_(missile_tuning),
      launch_recorder_(launch_recorder), damage_recorder_(damage_recorder),
      damage_bridge_(damage_bridge) {}

std::optional<SimulationKernelWeaponReleaseService::ResolvedMissileLaunchDefinition>
SimulationKernelWeaponReleaseService::resolve_missile_launch_definition(
    flecs::entity attacker, const PilotAction *pilot) const {
    if (!attacker.is_valid() || !unit_factory_) {
        return std::nullopt;
    }

    const int selected_station_id =
        (pilot && pilot->weapon_select_id > 0) ? pilot->weapon_select_id : 0;
    if (selected_station_id <= 0) {
        return std::nullopt;
    }

    ecs_iter_t it = ecs_children(ecs_.c_ptr(), attacker.id());
    while (ecs_children_next(&it)) {
        for (int i = 0; i < it.count; ++i) {
            const ecs_entity_t child_id = it.entities[i];
            auto child = ecs_.entity(child_id);
            const Munition *munition = child.get<Munition>();
            if (!munition || munition->is_fired) {
                continue;
            }

            const KeyEntity *child_key = child.get<KeyEntity>();
            if (!child_key || child_key->type != UnitType::Missile) {
                continue;
            }

            const auto platform_name = platform_definition_name_from_munition_name(
                ecs_get_name(ecs_.c_ptr(), child_id), munition->station_id);
            if (!platform_name.has_value()) {
                continue;
            }

            const UnitDefinition *platform_definition =
                unit_factory_->get_definition(*platform_name);
            if (!platform_definition) {
                continue;
            }

            const auto weapon_it = platform_definition->default_loadout.find(munition->station_id);
            if (weapon_it == platform_definition->default_loadout.end()) {
                continue;
            }

            const UnitDefinition *weapon_definition =
                unit_factory_->get_definition(weapon_it->second);
            if (!weapon_definition || weapon_definition->type != UnitType::Missile) {
                continue;
            }

            ResolvedMissileLaunchDefinition resolved{};
            resolved.munition_entity_id = static_cast<uint64_t>(child_id);
            resolved.platform_definition_name = *platform_name;
            resolved.weapon_definition_name = weapon_it->second;
            resolved.station_id = munition->station_id;
            resolved.platform_definition = platform_definition;
            resolved.weapon_definition = weapon_definition;

            if (munition->station_id == selected_station_id) {
                return resolved;
            }
        }
    }

    return std::nullopt;
}

flecs::entity SimulationKernelWeaponReleaseService::fire_missile(uint64_t attacker_id,
                                                                 uint64_t target_id) {
    auto attacker = ecs_.entity(attacker_id);
    if (!attacker.is_valid()) {
        spdlog::warn("Invalid attacker ID: {}", attacker_id);
        return flecs::entity::null();
    }

    const Transform *p = attacker.get<Transform>();
    const Velocity *v = attacker.get<Velocity>();
    const Alliance *side = attacker.get<Alliance>();
    Ammo *ammo = attacker.get_mut<Ammo>();
    WeaponCooldown *cooldown = attacker.get_mut<WeaponCooldown>();
    NavalWeaponSystem *naval_weapons = attacker.get_mut<NavalWeaponSystem>();
    Score *score = attacker.get_mut<Score>();
    const PilotAction *pilot = attacker.get<PilotAction>();

    if (!p || !v || !side) return flecs::entity::null();

    const ecs_world_info_t *info = ecs_get_world_info(ecs_.c_ptr());
    double current_time = info ? (double)info->world_time_total : 0.0;

    const bool has_naval_weapon_system = naval_weapons != nullptr;
    if (!has_naval_weapon_system && cooldown && cooldown->cooldown_s > 0.0 &&
        cooldown->last_fire_time >= 0.0) {
        if (current_time - cooldown->last_fire_time < cooldown->cooldown_s) {
            return flecs::entity::null();
        }
    }

    // Require an active track on the target to fire (prevents blind spam).
    const ContactList *contacts = attacker.get<ContactList>();
    if (!contacts) {
        return flecs::entity::null();
    }
    bool has_track = false;
    Detection det{};
    for (const auto &c : contacts->contacts) {
        if (c.target_id != target_id) continue;
        det = c;
        has_track = true;
        break;
    }
    if (!has_track) {
        return flecs::entity::null();
    }

    const auto resolved_launch_definition = resolve_missile_launch_definition(attacker, pilot);
    MissileTuning resolved_tuning{};
    double missile_total_mass_kg = 80.0;
    if (resolved_launch_definition.has_value() && resolved_launch_definition->weapon_definition) {
        const UnitDefinition &weapon_definition = *resolved_launch_definition->weapon_definition;
        missile_total_mass_kg =
            std::max(1.0, weapon_definition.mass_kg > 0.0 ? weapon_definition.mass_kg : 80.0);
        if (weapon_definition.has_missile_tuning) {
            resolved_tuning = to_runtime_missile_tuning(weapon_definition.missile_tuning);
        }
    }
    if (has_explicit_global_missile_tuning(missile_tuning_)) {
        overlay_missile_tuning(&resolved_tuning, missile_tuning_);
    }
    if (!missile_launch_envelope_allows(resolved_tuning, det)) {
        return flecs::entity::null();
    }

    NavalWeaponMountDefinition *vls_mount =
        naval_weapon_mounts::select_ready_vls_mount(naval_weapons, current_time);
    const bool use_naval_vls = vls_mount != nullptr;
    if (use_naval_vls) {
        if (!naval_weapon_mounts::consume_mount_shot(vls_mount, current_time)) {
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
    if (resolved_launch_definition.has_value() &&
        resolved_launch_definition->munition_entity_id != 0) {
        auto munition = ecs_.entity(resolved_launch_definition->munition_entity_id);
        if (munition.is_valid()) {
            if (Munition *mun = munition.get_mut<Munition>()) {
                mun->is_fired = true;
                munition.modified<Munition>();
            }
        }
    }

    if (use_naval_vls && vls_mount) {
        resolved_tuning.max_speed = std::max(300.0, vls_mount->projectile_speed_mps);
        resolved_tuning.turn_rate = 20.0;
        resolved_tuning.fuse_distance = 120.0;
        resolved_tuning.damage = 180.0;
        resolved_tuning.seeker_fov_deg = 120.0;
        resolved_tuning.seeker_lock_range = std::max(1000.0, vls_mount->engagement_range_m);
        resolved_tuning.guidance_delay_s = 1.0;
        resolved_tuning.guidance_update_period_s = 0.2;
        resolved_tuning.max_flight_time_s = 80.0;
        resolved_tuning.nav_gain = 3.5;
    }

    if (has_explicit_global_missile_tuning(missile_tuning_)) {
        overlay_missile_tuning(&resolved_tuning, missile_tuning_);
    }

    const double missile_max_speed = positive_or_default(resolved_tuning.max_speed, 1000.0);
    const double missile_turn_rate = positive_or_default(resolved_tuning.turn_rate, 35.0);
    const double missile_fuse_distance = positive_or_default(resolved_tuning.fuse_distance, 300.0);
    const double missile_damage = positive_or_default(resolved_tuning.damage, 120.0);
    WarheadProfile missile_warhead_profile =
        resolved_tuning.has_warhead_profile
            ? resolved_tuning.warhead_profile
            : make_synthetic_warhead_profile(missile_damage, missile_fuse_distance);
    if (!std::isfinite(missile_warhead_profile.lethal_radius_m)) {
        missile_warhead_profile.lethal_radius_m = missile_fuse_distance;
    }
    if (!std::isfinite(missile_warhead_profile.damage_scalar)) {
        missile_warhead_profile.damage_scalar = missile_damage;
        missile_warhead_profile.damage_scalar_synthetic = true;
    }
    FuzeProfile missile_fuze_profile = resolved_tuning.has_fuze_profile
                                           ? resolved_tuning.fuze_profile
                                           : make_synthetic_fuze_profile(missile_fuse_distance);
    if (!std::isfinite(missile_fuze_profile.trigger_radius_m)) {
        missile_fuze_profile.trigger_radius_m = missile_fuse_distance;
    }
    missile_fuze_profile.delay_s = std::max(0.0, missile_fuze_profile.delay_s);
    missile_fuze_profile.reliability = std::clamp(missile_fuze_profile.reliability, 0.0, 1.0);
    const double missile_seeker_fov = positive_or_default(resolved_tuning.seeker_fov_deg, 180.0);
    const double missile_seeker_range =
        positive_or_default(resolved_tuning.seeker_lock_range, 30000.0);
    const double missile_guidance_delay =
        nonnegative_or_default(resolved_tuning.guidance_delay_s, 0.0);
    const double missile_guidance_period =
        nonnegative_or_default(resolved_tuning.guidance_update_period_s, 0.0);
    const double missile_max_flight_time =
        positive_or_default(resolved_tuning.max_flight_time_s, 15.0);
    const double missile_nav_gain = positive_or_default(resolved_tuning.nav_gain, 3.0);

    double sensor_max_range = missile_seeker_range;
    double sensor_fov_deg = missile_seeker_fov;
    double sensor_scan_period = 0.05;
    double sensor_detection_prob = 0.98;
    double sensor_bearing_noise = 0.2;
    double sensor_range_noise = 10.0;
    double sensor_track_memory = 2.0;

    if (std::isfinite(resolved_tuning.sensor_max_range))
        sensor_max_range = resolved_tuning.sensor_max_range;
    if (std::isfinite(resolved_tuning.sensor_fov_deg))
        sensor_fov_deg = resolved_tuning.sensor_fov_deg;
    if (std::isfinite(resolved_tuning.sensor_scan_period))
        sensor_scan_period = resolved_tuning.sensor_scan_period;
    if (std::isfinite(resolved_tuning.sensor_detection_prob))
        sensor_detection_prob = resolved_tuning.sensor_detection_prob;
    if (std::isfinite(resolved_tuning.sensor_bearing_noise_std))
        sensor_bearing_noise = resolved_tuning.sensor_bearing_noise_std;
    if (std::isfinite(resolved_tuning.sensor_range_noise_std))
        sensor_range_noise = resolved_tuning.sensor_range_noise_std;
    if (std::isfinite(resolved_tuning.sensor_track_memory_s))
        sensor_track_memory = resolved_tuning.sensor_track_memory_s;

    const double propellant_mass_kg = clamp_missile_propellant_mass_kg(
        missile_total_mass_kg,
        finite_or_default(resolved_tuning.propellant_mass_kg,
                          default_propellant_mass_kg(missile_total_mass_kg)));
    const double reference_area_m2 = clamp_missile_reference_area_m2(
        resolved_tuning.reference_area_m2, default_reference_area_m2());
    const double boost_time_s = std::max(
        0.0, finite_or_default(resolved_tuning.boost_time_s, MissileGuidanceDefaults::kBoostTimeS));
    const double sustain_time_s =
        std::max(0.0, finite_or_default(resolved_tuning.sustain_time_s,
                                        MissileGuidanceDefaults::kSustainTimeS));
    const double track_memory_timeout_s =
        std::max(0.0, finite_or_default(resolved_tuning.track_break_time_s,
                                        MissileGuidanceDefaults::kTrackMemoryTimeoutS));
    const double bearing_filter_tau_s =
        std::max(0.0, finite_or_default(resolved_tuning.bearing_filter_tau_s,
                                        MissileGuidanceDefaults::kTrackFilterTauS));
    const double elevation_filter_tau_s =
        std::max(0.0, finite_or_default(resolved_tuning.elevation_filter_tau_s,
                                        MissileGuidanceDefaults::kTrackFilterTauS));
    const double range_filter_tau_s =
        std::max(0.0, finite_or_default(resolved_tuning.range_filter_tau_s,
                                        MissileGuidanceDefaults::kTrackFilterTauS));
    const double seeker_activation_range_m = finite_or_default(
        resolved_tuning.seeker_activation_range_m, std::numeric_limits<double>::quiet_NaN());
    const bool midcourse_datalink_supported = resolved_tuning.midcourse_datalink_supported;
    const bool terminal_seeker_active = !std::isfinite(seeker_activation_range_m) ||
                                        seeker_activation_range_m <= 0.0 ||
                                        det.range <= seeker_activation_range_m;
    const double max_lateral_g =
        std::max(0.1, finite_or_default(resolved_tuning.max_lateral_g,
                                        fallback_max_lateral_g(missile_turn_rate)));
    const double autopilot_tau_s =
        std::max(1.0e-3, finite_or_default(resolved_tuning.autopilot_tau_s,
                                           MissileGuidanceDefaults::kAutopilotTauS));
    const double max_accel_response_g_per_s =
        std::max(0.1, finite_or_default(resolved_tuning.max_accel_response_g_per_s,
                                        MissileGuidanceDefaults::kAccelResponseGps));
    const double cd0_subsonic =
        std::max(1.0e-4, finite_or_default(resolved_tuning.cd0_subsonic,
                                           MissileGuidanceDefaults::kCd0Subsonic));
    const double cd0_supersonic =
        std::max(1.0e-4, finite_or_default(resolved_tuning.cd0_supersonic,
                                           MissileGuidanceDefaults::kCd0Supersonic));
    const double induced_drag_k =
        std::max(0.0, finite_or_default(resolved_tuning.induced_drag_k,
                                        MissileGuidanceDefaults::kInducedDragScale));
    // Spawn Missile slightly in front
    double heading = std::atan2(v->vy, v->vx);
    double launch_x = p->x + 20.0 * std::cos(heading);
    double launch_y = p->y + 20.0 * std::sin(heading);
    const double launch_speed_mps = std::sqrt(v->vx * v->vx + v->vy * v->vy + v->vz * v->vz);
    const double boost_thrust_n = std::max(
        0.0, finite_or_default(resolved_tuning.boost_thrust_n,
                               default_boost_thrust_n(missile_total_mass_kg, missile_max_speed,
                                                      launch_speed_mps)));
    const double sustain_thrust_n =
        std::max(0.0, finite_or_default(resolved_tuning.sustain_thrust_n,
                                        default_sustain_thrust_n(boost_thrust_n)));

    uint64_t missile_seed =
        splitmix64(static_cast<uint64_t>(current_time * 1000.0) ^
                   (attacker_id * 0x9e3779b97f4a7c15ULL) ^ (target_id * 0xbf58476d1ce4e5b9ULL));

    const Mass mass = make_missile_mass_state(missile_total_mass_kg, propellant_mass_kg);
    const MassProperties mass_properties = make_missile_mass_properties(mass, reference_area_m2);

    Missile missile{};
    missile.attacker_id = attacker_id;
    missile.target_id = target_id;
    missile.max_speed = missile_max_speed;
    missile.turn_rate = missile_turn_rate;
    missile.fuse_distance = missile_fuse_distance;
    missile.damage = missile_damage;
    missile.seeker_fov_deg = missile_seeker_fov;
    missile.seeker_lock_range = missile_seeker_range;
    missile.guidance_delay_s = missile_guidance_delay;
    missile.guidance_update_period_s = missile_guidance_period;
    missile.last_guidance_time = -1.0;
    missile.launch_time = current_time;
    missile.max_flight_time_s = missile_max_flight_time;
    missile.nav_gain = missile_nav_gain;
    missile.active = true;
    missile.warhead_profile = missile_warhead_profile;
    missile.fuze_profile = missile_fuze_profile;
    missile.rng_state = missile_seed;
    missile.proximity_min_dist_m = std::numeric_limits<double>::infinity();
    missile.proximity_min_time_s = std::numeric_limits<double>::quiet_NaN();
    missile.proximity_last_dist_m = std::numeric_limits<double>::infinity();
    missile.proximity_min_local_forward_m = std::numeric_limits<double>::quiet_NaN();
    missile.proximity_min_local_right_m = std::numeric_limits<double>::quiet_NaN();
    missile.proximity_min_local_up_m = std::numeric_limits<double>::quiet_NaN();
    missile.proximity_engaged = false;
    missile.fuze_delay_armed = false;
    missile.fuze_nearest_approach_time_s = std::numeric_limits<double>::quiet_NaN();
    missile.fuze_detonation_time_s = std::numeric_limits<double>::quiet_NaN();
    missile.fuze_detonation_heading_deg = std::numeric_limits<double>::quiet_NaN();
    missile.fuze_detonation_pitch_deg = std::numeric_limits<double>::quiet_NaN();
    missile.fuze_detonation_roll_deg = std::numeric_limits<double>::quiet_NaN();
    initialize_missile_launch_runtime(missile, MissileSharedLaunchRuntimeState{
                                                   current_time,
                                                   launch_speed_mps,
                                                   true,
                                                   det.range > 1.0e-3,
                                                   static_cast<int>(MissileSeekerMode::Track),
                                                   det.bearing,
                                                   det.elevation,
                                                   det.range,
                                                   det.closing_speed,
                                                   current_time,
                                                   track_memory_timeout_s,
                                                   current_time + boost_time_s + sustain_time_s,
                                                   boost_time_s,
                                                   sustain_time_s,
                                                   bearing_filter_tau_s,
                                                   elevation_filter_tau_s,
                                                   range_filter_tau_s,
                                                   boost_thrust_n,
                                                   sustain_thrust_n,
                                                   cd0_subsonic,
                                                   cd0_supersonic,
                                                   induced_drag_k,
                                                   max_lateral_g,
                                                   autopilot_tau_s,
                                                   max_accel_response_g_per_s,
                                                   seeker_activation_range_m,
                                                   midcourse_datalink_supported,
                                                   terminal_seeker_active,
                                               });

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
    sensor.type = resolved_tuning.seeker_type >= 0
                      ? resolved_tuning.seeker_type
                      : static_cast<int>(sensor_max_range > 8000.0 ? SensorType::Radar
                                                                   : SensorType::Infrared);

    auto m = ecs_.entity()
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

    const int ammo_delta =
        use_naval_vls && vls_mount ? -std::max(1, vls_mount->ammo_per_shot) : (ammo ? -1 : 0);
    const double cooldown_delta_s = use_naval_vls && vls_mount
                                        ? vls_mount->cooldown_s
                                        : (cooldown ? cooldown->cooldown_s : 0.0);
    const std::string selected_launcher =
        use_naval_vls && vls_mount ? vls_mount->mount_id : "legacy:air_missile";
    const std::string selected_munition =
        resolved_launch_definition.has_value() &&
                !resolved_launch_definition->weapon_definition_name.empty()
            ? resolved_launch_definition->weapon_definition_name
            : (use_naval_vls ? "naval:vls_sam" : "legacy:missile");
    (void)launch_recorder_.record_legacy_launch_event(
        attacker_id, target_id, static_cast<uint64_t>(m.id()), selected_launcher, selected_munition,
        ammo_delta, cooldown_delta_s, current_time);

    spdlog::info("FOX 2! Missile {} fired by {} at {}", m.id(), attacker_id, target_id);
    return m;
}

bool SimulationKernelWeaponReleaseService::fire_naval_weapon(uint64_t attacker_id,
                                                             uint64_t target_id,
                                                             int weapon_type_code) {
    auto attacker = ecs_.entity(attacker_id);
    if (!attacker.is_valid() || target_id == 0) {
        return false;
    }

    const Transform *attacker_pos = attacker.get<Transform>();
    const ContactList *contacts = attacker.get<ContactList>();
    NavalWeaponSystem *naval_weapons = attacker.get_mut<NavalWeaponSystem>();
    Score *score = attacker.get_mut<Score>();
    if (!attacker_pos || !contacts || !naval_weapons) {
        return false;
    }

    Detection det{};
    bool has_track = false;
    for (const auto &c : contacts->contacts) {
        if (c.target_id != target_id) continue;
        det = c;
        has_track = true;
        break;
    }
    if (!has_track) {
        return false;
    }

    const ecs_world_info_t *info = ecs_get_world_info(ecs_.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const NavalWeaponType weapon_type = static_cast<NavalWeaponType>(weapon_type_code);
    NavalWeaponMountDefinition *mount =
        naval_weapon_mounts::select_ready_mount(naval_weapons, weapon_type, current_time);
    if (!mount) {
        return false;
    }

    if (det.range > mount->engagement_range_m && mount->engagement_range_m > 0.0) {
        return false;
    }
    if (!naval_weapon_mounts::consume_mount_shot(mount, current_time)) {
        return false;
    }

    const std::uint64_t launch_event_id = launch_recorder_.record_legacy_launch_event(
        attacker_id, target_id, 0,
        mount->mount_id.empty() ? naval_weapon_type_name(weapon_type) : mount->mount_id,
        naval_weapon_type_name(weapon_type), -std::max(1, mount->ammo_per_shot), mount->cooldown_s,
        current_time);

    double hit_probability = std::clamp(mount->hit_probability, 0.05, 0.99);
    auto target = ecs_.entity(target_id);
    const bool target_valid = target.is_valid();
    const bool target_is_missile = entity_is_missile(ecs_, target_id);
    if (weapon_type == NavalWeaponType::Ciws && mount->can_intercept_missiles &&
        target_is_missile) {
        const double close_range_threshold_m = std::max(300.0, mount->engagement_range_m * 0.75);
        if (det.range <= close_range_threshold_m) {
            hit_probability = 1.0;
        }
    }
    uint64_t rng_state = splitmix64(
        static_cast<uint64_t>(current_time * 1000.0) ^ (attacker_id * 0x9e3779b97f4a7c15ULL) ^
        (target_id * 0xbf58476d1ce4e5b9ULL) ^ (static_cast<uint64_t>(weapon_type_code) << 32));
    const double u = (splitmix64(rng_state) >> 11) * (1.0 / 9007199254740992.0);
    const bool hit = u <= hit_probability;

    if (weapon_type == NavalWeaponType::Ciws && mount->can_intercept_missiles &&
        target_is_missile) {
        if (hit && target_valid) {
            const EngagementDamageStateSnapshot before =
                damage_recorder_.capture_engagement_damage_state(target_id);
            target.destruct();
            const EngagementDamageStateSnapshot after =
                damage_recorder_.capture_engagement_damage_state(target_id);
            launch_recorder_.set_pending_effects_launch_event_id(launch_event_id);
            EngagementEffectsDamageEventRecord event_record{};
            event_record.munition_entity_id = 0;
            event_record.target_id = target_id;
            event_record.before = before;
            event_record.after = after;
            event_record.effects.trigger_type = "naval_ciws_intercept";
            event_record.effects.outcome_state = "hit";
            event_record.effects.detonation_time_s = current_time;
            event_record.effects.nearest_approach_time_s = current_time;
            event_record.effects.quality = hit_probability;
            event_record.effects.confidence = 1.0;
            event_record.effects.effect_family = "kinetic_intercept";
            event_record.effects.warhead_profile_synthetic = true;
            event_record.effects.damage_scalar_synthetic = true;
            event_record.effects.fuze_type = "contact";
            event_record.effects.fuze_reliability = 1.0;
            event_record.effects.fuze_profile_synthetic = true;
            (void)damage_recorder_.record_effects_damage_event(std::move(event_record));
            if (score) {
                score->hits_landed += 1;
                score->kills_confirmed += 1;
            }
        }
        return true;
    }

    if (!hit || !target_valid) {
        return true;
    }

    const double applied_damage = mount->damage_per_hit > 0.0 ? mount->damage_per_hit : 60.0;
    const double fuse_distance = weapon_type == NavalWeaponType::DeckGun ? 25.0 : 40.0;
    launch_recorder_.set_pending_effects_launch_event_id(launch_event_id);
    (void)damage_bridge_.apply_proximity_hit(attacker_id, target_id, applied_damage, fuse_distance);
    return true;
}

bool SimulationKernelWeaponReleaseService::fire_naval_weapon_from_mission_command(
    uint64_t attacker_id) {
    auto attacker = ecs_.entity(attacker_id);
    if (!attacker.is_valid()) {
        return false;
    }

    const MissionCommand *mission = attacker.get<MissionCommand>();
    const ContactList *contacts = attacker.get<ContactList>();
    const NavalWeaponSystem *naval_weapons = attacker.get<NavalWeaponSystem>();
    if (!mission || !mission->active || !contacts || !naval_weapons ||
        naval_weapons->mounts.empty()) {
        return false;
    }
    if (!mission->authorization_to_fire ||
        !mission_authority_matches_shooter(mission, attacker_id)) {
        return false;
    }

    uint64_t target_id = 0;
    int weapon_type_code = 0;
    switch (mission->command_code) {
    case kMissionCommandCodeNavalAutoCloseInDefense:
        target_id = select_ciws_mission_target_id(ecs_, contacts, mission);
        weapon_type_code = static_cast<int>(NavalWeaponType::Ciws);
        break;
    case kMissionCommandCodeNavalSurfaceEngage:
        target_id = select_surface_gun_mission_target_id(ecs_, contacts, mission);
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

flecs::entity
SimulationKernelWeaponReleaseService::fire_weapon_from_pilot_action(uint64_t attacker_id) {
    auto attacker = ecs_.entity(attacker_id);
    if (!attacker.is_valid()) {
        return flecs::entity::null();
    }

    const PilotAction *pilot = attacker.get<PilotAction>();
    if (!pilot || !pilot->active || !pilot->master_arm || !pilot->fire_weapon) {
        return flecs::entity::null();
    }

    const MissionCommand *mission = attacker.get<MissionCommand>();
    if (mission && !mission->active) {
        mission = nullptr;
    }
    const ContactList *contacts = attacker.get<ContactList>();

    uint64_t target_id = 0;

    if (mission_explicit_release_target_available(mission, contacts, attacker_id)) {
        target_id = mission->assigned_target_id;
    }
    if (target_id == 0) {
        return flecs::entity::null();
    }
    return fire_missile(attacker_id, target_id);
}
