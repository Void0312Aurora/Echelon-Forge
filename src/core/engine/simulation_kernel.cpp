#include "simulation_kernel.h"
#include "systems/physics/movement_system.h"
#include "systems/core/operation_system.h"
#include "systems/systems/command_link_system.h"
#include "systems/physics/control_system.h"
#include "systems/combat/guidance_system.h"
#include "systems/combat/damage_system.h"
#include "systems/systems/sensor_system.h"
#include "systems/systems/data_link_system.h"
#include "components/physics/action.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h" // Added logistics.h
#include "systems/systems/ew_system.h"
#include "systems/systems/logistics_system.h" // Added logistics_system.h
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/unit_factory.h"
#include "models/core/default_unit_factory.h"
#include <algorithm>
#include <limits>
#include <spdlog/spdlog.h>

#include "components/physics/performance.h"
#include "components/combat/scoring.h" // Added scoring
#include "components/combat/weapon.h"

SimulationKernel::SimulationKernel()
    : unit_factory_(std::make_unique<DefaultUnitFactory>()),
      effects_model_(make_default_effects_model()),
      sensor_model_(make_default_sensor_model()),
      control_model_(make_default_control_model()),
      guidance_model_(make_default_guidance_model()),
      environment_model_(make_default_environment_model()) {
    // EW System: Reset RWR state each frame before sensors run
    ecs.system<RWR>("RWR_Reset")
       .kind(flecs::PreUpdate)
       .each([](flecs::entity e, RWR& rwr) {
           rwr.detected_radar_ids.clear();
           rwr.is_locked = false;
           rwr.is_missile_launch = false;
       });

    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();
    ecs.component<MovementCommand>();
    ecs.component<ActionCommand>();
    ecs.component<ActionSpaceConfig>();
    ecs.component<CommandLag>();
    ecs.component<LaggedCommand>();
    ecs.component<CommandLink>();
    ecs.component<PendingMovementCommand>();
    ecs.component<PendingActionCommand>();
    ecs.component<Missile>();
    ecs.component<Ammo>();
    ecs.component<WeaponCooldown>();
    ecs.component<Missile>();
    ecs.component<Ammo>();
    ecs.component<WeaponCooldown>();
    
    // EW Components
    ecs.component<Jammer>();
    ecs.component<Countermeasures>();
    ecs.component<RWR>();
    ecs.component<RCSProfile>();
    ecs.component<Lifetime>();
    ecs.component<FuelSystem>();
    ecs.component<MassProperties>();
    ecs.component<Loadout>();
    ecs.component<LogisticsNode>();
    ecs.component<ResupplyState>();

    ecs.component<Sensor>();
    ecs.component<ContactList>();
    ecs.component<FlightModel>(); 
    ecs.component<Score>();
    ecs.component<DataLink>(); // New Component

    ecs.component<EffectsModelRef>();
    ecs.component<SensorModelRef>();
    ecs.component<ControlModelRef>();
    ecs.component<GuidanceModelRef>();
    ecs.component<EnvironmentModelRef>();

    // Define Pipeline Phases (explicit ordering)
    // Phase 1: Control - writes platform Velocity based on commands
    // Phase 2: Guidance - writes weapon Velocity (missiles)
    // Phase 3: Movement - integrates Velocity → Transform
    // Phase 4: Sensor - scans for contacts
    // Phase 5: Damage - proximity fuse, hit effects
    
    // Note: With flecs, systems registered on OnUpdate run in registration order.
    // For guaranteed ordering, we use .kind() with custom phases or depends_on.
    // For MVP, registration order is sufficient as long as it's explicit.
    
    // Register Systems IN ORDER (dependency chain)
    register_command_link_system(ecs);   // Phase 0: Command Link
    register_action_mapping_system(ecs); // Phase 1: Action Mapping
    register_command_lag_system(ecs);    // Phase 2: Command Lag
    register_control_system(ecs);        // Phase 3: Control
    register_guidance_system(ecs);       // Phase 4: Guidance
    register_movement_system(ecs);       // Phase 5: Movement (integrate)
    register_sensor_system(ecs);         // Phase 6: Sensor
    register_data_link_system(ecs);      // Phase 6.5: Data Link Fusion (Post-Sensor)
    register_damage_system(ecs);         // Phase 7: Damage/Effects
    register_ew_system(ecs);             // Phase 8: EW Actions
    register_logistics_system(ecs);      // Phase 9: Logistics

    ecs.set<EffectsModelRef>({effects_model_.get()});
    ecs.set<SensorModelRef>({sensor_model_.get()});
    ecs.set<ControlModelRef>({control_model_.get()});
    ecs.set<GuidanceModelRef>({guidance_model_.get()});
    ecs.set<EnvironmentModelRef>({environment_model_.get()});

    reset(42); // Default reset
}

SimulationKernel::~SimulationKernel() = default;

namespace {
uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double deterministic_uniform01(uint64_t seed) {
    uint64_t z = splitmix64(seed);
    return (z >> 11) * (1.0 / 9007199254740992.0);
}
} // namespace

void SimulationKernel::set_unit_factory(std::unique_ptr<IUnitFactory> factory) {
    if (factory) {
        unit_factory_ = std::move(factory);
    } else {
        spdlog::warn("Attempted to set a null unit factory; keeping current factory.");
    }
}

void SimulationKernel::set_effects_model(std::unique_ptr<IEffectsModel> model) {
    if (model) {
        effects_model_ = std::move(model);
        ecs.set<EffectsModelRef>({effects_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null effects model; keeping current model.");
    }
}

void SimulationKernel::set_sensor_model(std::unique_ptr<ISensorModel> model) {
    if (model) {
        sensor_model_ = std::move(model);
        ecs.set<SensorModelRef>({sensor_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null sensor model; keeping current model.");
    }
}

void SimulationKernel::set_control_model(std::unique_ptr<IControlModel> model) {
    if (model) {
        control_model_ = std::move(model);
        ecs.set<ControlModelRef>({control_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null control model; keeping current model.");
    }
}

void SimulationKernel::set_guidance_model(std::unique_ptr<IGuidanceModel> model) {
    if (model) {
        guidance_model_ = std::move(model);
        ecs.set<GuidanceModelRef>({guidance_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null guidance model; keeping current model.");
    }
}

void SimulationKernel::set_environment_model(std::unique_ptr<IEnvironmentModel> model) {
    if (model) {
        environment_model_ = std::move(model);
        ecs.set<EnvironmentModelRef>({environment_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null environment model; keeping current model.");
    }
}

bool SimulationKernel::load_unit_definitions(const std::string& path, std::string* error) {
    if (!unit_factory_) {
        if (error) *error = "Unit factory not set.";
        return false;
    }
    return unit_factory_->load_definitions(path, error);
}

void SimulationKernel::set_missile_tuning(const MissileTuning& tuning) {
    missile_tuning_ = tuning;
}

void SimulationKernel::reset(unsigned int seed) {
    // Delete all simulation entities (tagged with SimObject)
    // This is safer than delete_with<Transform> as it won't affect
    // potential non-simulation entities (e.g., UI, config singletons)
    ecs.delete_with<SimObject>();
    
    rng.seed(seed);
    
    spdlog::info("Simulation Reset with seed {}", seed);
}

void SimulationKernel::step() {
    // Fixed timestep update
    // We pass the fixed delta_time to progress
    // This overrides the internal clock measuring
    ecs.progress(time_step);
}

bool SimulationKernel::load_database(const std::string& path) {
    std::string error;
    if (unit_factory_->load_definitions(path, &error)) {
        spdlog::info("Database loaded from: {}", path);
        return true;
    }
    spdlog::error("Failed to load database: {}", error);
    return false;
}

flecs::entity SimulationKernel::spawn_unit(Side side, const std::string& unit_name, 
                                           double x, double y, double z, 
                                           double vx, double vy, double vz) {
    if (!unit_factory_) {
        spdlog::error("Unit factory not set; cannot spawn unit.");
        return flecs::entity::null();
    }

    // Optional: Check existence first or trust spawn to handle it.
    // The factory->spawn is responsible for lookup now.
    SpawnParams params{side, x, y, z, vx, vy, vz};
    auto e = unit_factory_->spawn(ecs, unit_name, params);
    if (e.is_valid()) {
        e.add<SimObject>(); // Tag for cleanup
    }
    return e;
}

void SimulationKernel::set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps, double altitude_m) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        const CommandLink* link = e.get<CommandLink>();
        if (link && (link->latency_s > 0.0 || link->drop_prob > 0.0)) {
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0xbf58476d1ce4e5b9ULL) ^ 0x12345678ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                PendingMovementCommand pending{{heading_deg, speed_mps, altitude_m, true},
                                               current_time + link->latency_s,
                                               true};
                e.set<PendingMovementCommand>(pending);
            }
        } else {
            e.set<MovementCommand>({heading_deg, speed_mps, altitude_m, true});
            if (!e.has<LaggedCommand>()) {
                e.set<LaggedCommand>({heading_deg, speed_mps, altitude_m, true});
            }
        }
    } else {
        spdlog::warn("Attempted to set command for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_unit_action(uint64_t entity_id,
                                       double turn_rate_cmd,
                                       double accel_cmd,
                                       double climb_rate_cmd,
                                       double fire_cmd,
                                       bool release_chaff,
                                       bool release_flare,
                                       bool jettison_tanks) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        auto clamp_cmd = [](double v) { return std::clamp(v, -1.0, 1.0); };
        double fire = std::clamp(fire_cmd, 0.0, 1.0);
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        const CommandLink* link = e.get<CommandLink>();
        if (link && (link->latency_s > 0.0 || link->drop_prob > 0.0)) {
            if (!e.has<ActionCommand>()) {
                e.set<ActionCommand>({0.0, 0.0, 0.0, 0.0, false});
            }
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0x94d049bb133111ebULL) ^ 0x87654321ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                PendingActionCommand pending{{
                                                clamp_cmd(turn_rate_cmd),
                                                clamp_cmd(accel_cmd),
                                                clamp_cmd(climb_rate_cmd),
                                                fire,
                                                release_chaff,
                                                release_flare,
                                                jettison_tanks,
                                                true
                                            },
                                            current_time + link->latency_s,
                                            true};
                e.set<PendingActionCommand>(pending);
            }
        } else {
            e.set<ActionCommand>({
                clamp_cmd(turn_rate_cmd),
                clamp_cmd(accel_cmd),
                clamp_cmd(climb_rate_cmd),
                fire,
                release_chaff,
                release_flare,
                jettison_tanks,
                true
            });
        }
    } else {
        spdlog::warn("Attempted to set action for invalid entity ID: {}", entity_id);
    }
}

std::vector<double> SimulationKernel::get_unit_position(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Transform* t = e.get<Transform>();
        if (t) {
            return {t->x, t->y, t->z};
        }
    }
    return {0.0, 0.0, 0.0};
}

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
    Score* score = attacker.get_mut<Score>();
    
    if (!p || !v || !side) return flecs::entity::null();

    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    double current_time = info ? (double)info->world_time_total : 0.0;

    if (cooldown && cooldown->cooldown_s > 0.0 && cooldown->last_fire_time >= 0.0) {
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

    if (ammo) {
        if (ammo->missiles_remaining <= 0) {
            spdlog::warn("Attacker {} has no missiles remaining.", attacker_id);
            return flecs::entity::null();
        }
        ammo->missiles_remaining -= 1;
    }
    if (score) {
        score->missiles_fired += 1;
    }
    if (cooldown) {
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

    // Spawn Missile slightly in front
    double heading = std::atan2(v->vy, v->vx);
    double launch_x = p->x + 20.0 * std::cos(heading);
    double launch_y = p->y + 20.0 * std::sin(heading);

    uint64_t missile_seed = splitmix64(static_cast<uint64_t>(current_time * 1000.0) ^
                                       (attacker_id * 0x9e3779b97f4a7c15ULL) ^
                                       (target_id * 0xbf58476d1ce4e5b9ULL));
    
    auto m = ecs.entity()
        .set<Transform>({launch_x, launch_y, p->z, p->heading, 0, 0})
        .set<Velocity>({v->vx, v->vy, v->vz}) // Inherit platform velocity
        .set<Alliance>({side->side})
        .set<KeyEntity>({UnitType::Missile})
        .set<Missile>({
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
        }) // 1000m/s, 35deg/s, 300m fuse, 120 DMG
        .set<Sensor>({sensor_max_range, sensor_fov_deg, sensor_scan_period, -1.0,
                      sensor_detection_prob, 2.0, sensor_bearing_noise,
                      sensor_range_noise, sensor_track_memory, 0.2}) // Seeker sensor
        .set<ContactList>({})
        .add<SimObject>(); // Tag for cleanup
        
    spdlog::info("FOX 2! Missile {} fired by {} at {}", m.id(), attacker_id, target_id);
    return m;
}

std::vector<Detection> SimulationKernel::get_detections(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList* c = e.get<ContactList>();
        if (c) {
            return c->contacts;
        }
    }
    return {};
}

double SimulationKernel::debug_get_last_scan_time(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Sensor* s = e.get<Sensor>();
        if (s) return s->last_scan_time;
    }
    return std::numeric_limits<double>::quiet_NaN();
}

int SimulationKernel::debug_get_contact_count(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList* c = e.get<ContactList>();
        if (c) return static_cast<int>(c->contacts.size());
    }
    return -1;
}

std::vector<double> SimulationKernel::get_unit_health(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {0.0, 0.0};

    if (const Health* h = e.get<Health>()) {
        return {h->current_hp, h->max_hp};
    }
    return {0.0, 0.0};
}

std::vector<double> SimulationKernel::get_unit_fuel(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const FuelSystem* f = e.get<FuelSystem>()) {
            return {f->internal_fuel_kg, f->max_internal_fuel_kg, 
                    f->external_fuel_kg, f->max_external_fuel_kg};
        }
    }
    return {0.0, 0.0, 0.0, 0.0}; // Error/Not Found
}

std::vector<CommPacket> SimulationKernel::get_unit_messages(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const CommQueue* q = e.get<CommQueue>()) {
            return q->inbox;
        }
    }
    return {};
}

void SimulationKernel::send_message_command(uint64_t entity_id, uint64_t recipient_id, int msg_type, uint64_t msg_arg) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return;

    ActionCommand* cmd = e.get_mut<ActionCommand>();
    if (cmd) {
        cmd->send_msg = true;
        cmd->msg_recipient = recipient_id;
        cmd->msg_type = msg_type;
        cmd->msg_arg = msg_arg;
        cmd->active = true;
    }
}

std::vector<UnitData> SimulationKernel::get_all_units() {
    std::vector<UnitData> units;

    auto query = ecs.query<const KeyEntity, const Transform, const Velocity, const Alliance>();
    query.each([&](flecs::entity e,
                   const KeyEntity& k,
                   const Transform& p,
                   const Velocity& /*v*/,
                   const Alliance& a) {
        UnitData data;
        data.id = e.id();
        data.side = static_cast<int>(a.side);
        data.type = static_cast<int>(k.type);
        data.x = p.x;
        data.y = p.y;
        data.z = p.z;
        data.heading = p.heading;
        units.push_back(data);
    });

    return units;
}

AgentObservation SimulationKernel::get_agent_observation(uint64_t entity_id) {
    AgentObservation obs{};
    obs.id = entity_id;
    obs.sim_time = 0.0;
    obs.missiles_remaining = -1;
    obs.can_fire = false;
    obs.health = 0.0;
    obs.total_reward = 0.0;
    
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return obs; // Empty
    
    // Time
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    if (info) obs.sim_time = (double)info->world_time_total;
    
    // Self State
    const Transform* p = e.get<Transform>();
    const Velocity* v = e.get<Velocity>();
    const Health* h = e.get<Health>();
    
    if (p) {
        obs.x = p->x; obs.y = p->y; obs.z = p->z;
        obs.heading = p->heading; obs.pitch = p->pitch; obs.roll = p->roll;
    }
    if (v) {
        obs.vx = v->vx; obs.vy = v->vy; obs.vz = v->vz;
        obs.speed = std::sqrt(v->vx*v->vx + v->vy*v->vy + v->vz*v->vz);
    }
    if (h) {
        obs.health = h->current_hp;
    } else {
        obs.health = 0.0;
    }
    
    // Sensors
    const ContactList* c = e.get<ContactList>();
    if (c) {
        for (const auto& det : c->contacts) {
            TrackData track;
            track.id = det.target_id;
            track.range = det.range;
            track.time_since_update = obs.sim_time - det.timestamp;
            
            // Sensor already provides relative azimuth in NAV degrees.
            track.azimuth = det.bearing;
            track.elevation = det.elevation;
            
            obs.contacts.push_back(track);
        }
    }
    
    // Weapons check (Placeholder)
    const Ammo* ammo = e.get<Ammo>();
    const WeaponCooldown* cooldown = e.get<WeaponCooldown>();
    if (ammo) {
        obs.missiles_remaining = ammo->missiles_remaining;
        obs.can_fire = ammo->missiles_remaining > 0;
        if (obs.can_fire && cooldown && cooldown->cooldown_s > 0.0 && cooldown->last_fire_time >= 0.0) {
            obs.can_fire = (obs.sim_time - cooldown->last_fire_time) >= cooldown->cooldown_s;
        }
    } else {
        obs.missiles_remaining = -1;
        obs.can_fire = true;
    }
    
    const Score* s = e.get<Score>();
    obs.total_reward = s ? s->total_reward : 0.0;
    
    return obs;
}
