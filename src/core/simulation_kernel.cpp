#include "simulation_kernel.h"
#include "systems/movement_system.h"
#include "systems/operation_system.h"
#include "systems/command_link_system.h"
#include "systems/control_system.h"
#include "systems/guidance_system.h"
#include "systems/damage_system.h"
#include "systems/sensor_system.h"
#include "components/action.h"
#include "core/control_model.h"
#include "core/effects_model.h"
#include "core/guidance_model.h"
#include "core/sensor_model.h"
#include "core/unit_factory.h"
#include "models/default_unit_factory.h"
#include <algorithm>
#include <limits>
#include <spdlog/spdlog.h>

#include "components/performance.h"
#include "components/scoring.h" // Added scoring
#include "components/weapon.h"

SimulationKernel::SimulationKernel()
    : unit_factory_(std::make_unique<DefaultUnitFactory>()),
      effects_model_(make_default_effects_model()),
      sensor_model_(make_default_sensor_model()),
      control_model_(make_default_control_model()),
      guidance_model_(make_default_guidance_model()) {
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
    ecs.component<Sensor>();
    ecs.component<ContactList>();
    ecs.component<FlightModel>(); 
    ecs.component<Score>();
    ecs.component<EffectsModelRef>();
    ecs.component<SensorModelRef>();
    ecs.component<ControlModelRef>();
    ecs.component<GuidanceModelRef>();

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
    register_damage_system(ecs);         // Phase 7: Damage/Effects

    ecs.set<EffectsModelRef>({effects_model_.get()});
    ecs.set<SensorModelRef>({sensor_model_.get()});
    ecs.set<ControlModelRef>({control_model_.get()});
    ecs.set<GuidanceModelRef>({guidance_model_.get()});

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

bool SimulationKernel::load_unit_definitions(const std::string& path, std::string* error) {
    if (!unit_factory_) {
        if (error) *error = "Unit factory not set.";
        return false;
    }
    return unit_factory_->load_definitions(path, error);
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

flecs::entity SimulationKernel::spawn_unit(Side side, UnitType type, 
                                           double x, double y, double z, 
                                           double vx, double vy, double vz) {
    if (!unit_factory_) {
        spdlog::error("Unit factory not set; cannot spawn unit.");
        return flecs::entity::null();
    }

    const UnitDefinition* def = unit_factory_->get_definition(type);
    if (!def) {
        spdlog::warn("No UnitDefinition found for type {}", static_cast<int>(type));
        return flecs::entity::null();
    }

    SpawnParams params{side, x, y, z, vx, vy, vz};
    auto e = unit_factory_->spawn(ecs, *def, params);
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
                                       double fire_cmd) {
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
            1000.0,
            35.0,
            300.0,
            120.0,
            180.0,
            30000.0,
            0.0,
            0.0,
            -1.0,
            current_time,
            15.0,
            3.0,
            true,
            missile_seed,
            std::numeric_limits<double>::infinity(),
            std::numeric_limits<double>::infinity(),
            false
        }) // 1000m/s, 35deg/s, 300m fuse, 120 DMG
        .set<Sensor>({30000.0, 180.0, 0.05, -1.0, 0.98, 2.0, 0.2, 10.0, 2.0, 0.2}) // Seeker 30km, 180deg
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
    if (e.is_valid()) {
        const Health* h = e.get<Health>();
        if (h) {
            return {h->current_hp, h->max_hp};
        }
    }
    return {-1.0, -1.0}; // Error/Not Found
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
    AgentObservation obs;
    obs.id = entity_id;
    obs.sim_time = 0.0;
    
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
            
            // Elevation: Need Target Z. Detection struct currently doesn't store Target Z (only 2D bearing).
            // Sensor System (Phase 1/2) only calculated 2D bearing range.
            // Temp-03.md says "don't give true pos".
            // So we can assume Elevation is 0 OR update Detection to include Elevation.
            // For now, let's leave elevation 0.0 if not available in Detection.
            track.elevation = 0.0;
            
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
