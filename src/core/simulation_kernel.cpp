#include "simulation_kernel.h"
#include "systems/movement_system.h"
#include "systems/control_system.h"
#include "systems/guidance_system.h"
#include "systems/damage_system.h"
#include "systems/sensor_system.h"
#include "components/action.h"
#include <spdlog/spdlog.h>

#include "components/performance.h"
#include "components/scoring.h" // Added scoring

// ... (previous includes)

SimulationKernel::SimulationKernel() {
    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();
    ecs.component<MovementCommand>();
    ecs.component<Missile>();
    ecs.component<FlightModel>(); 
    ecs.component<Score>();

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
    register_control_system(ecs);   // Phase 1: Control
    register_guidance_system(ecs);  // Phase 2: Guidance
    register_movement_system(ecs);  // Phase 3: Movement (integrate)
    register_sensor_system(ecs);    // Phase 4: Sensor
    register_damage_system(ecs);    // Phase 5: Damage/Effects

    reset(42); // Default reset
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
    auto e = ecs.entity()
        .set<Transform>({x, y, z, 0, 0, 0})
        .set<Velocity>({vx, vy, vz})
        .set<Alliance>({side})
        .set<KeyEntity>({type})
        .set<Health>({100.0, 100.0}) // Default 100 HP
        .set<Sensor>({30000.0, 120.0, 1.0, -1.0}) // Default 30km, 120deg
        .set<ContactList>({})
        .add<SimObject>(); // Tag for cleanup

    // Add Flight Model based on Type
    if (type == UnitType::Aircraft) {
        // Generic Fighter Performance
        e.set<FlightModel>({
            600.0,  // max_speed (m/s) ~ Mach 1.8
            50.0,   // min_speed (m/s)
            20.0,   // max_turn_rate (deg/s)
            50.0,   // max_accel (m/s^2)
            300.0,  // max_climb_rate (m/s)
            9.0     // max_g
        });
        // Init command to maintain current state
        double heading = std::atan2(vy, vx) * 180.0 / M_PI;
        double speed = std::sqrt(vx*vx + vy*vy + vz*vz);
        e.set<MovementCommand>({heading, speed, z, true});
    } else if (type == UnitType::Missile) {
        // Missile Performance
        e.set<FlightModel>({
            1200.0, // max_speed
            100.0,  // min_speed
            40.0,   // max_turn_rate
            100.0,  // max_accel
            600.0,  // max_climb_rate
            30.0    // max_g
        });
        double heading = std::atan2(vy, vx) * 180.0 / M_PI;
        double speed = std::sqrt(vx*vx + vy*vy + vz*vz);
        e.set<MovementCommand>({heading, speed, z, true});
    }
    
    return e;
}

void SimulationKernel::set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps, double altitude_m) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        e.set<MovementCommand>({heading_deg, speed_mps, altitude_m, true});
    } else {
        spdlog::warn("Attempted to set command for invalid entity ID: {}", entity_id);
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
    
    if (!p || !v || !side) return flecs::entity::null();
    
    // Spawn Missile slightly in front
    double heading = std::atan2(v->vy, v->vx);
    double launch_x = p->x + 20.0 * std::cos(heading);
    double launch_y = p->y + 20.0 * std::sin(heading);
    
    auto m = ecs.entity()
        .set<Transform>({launch_x, launch_y, p->z, 0, 0, 0})
        .set<Velocity>({v->vx, v->vy, v->vz}) // Inherit platform velocity
        .set<Alliance>({side->side})
        .set<KeyEntity>({UnitType::Missile})
        .set<Missile>({attacker_id, target_id, 1000.0, 30.0, 100.0, 55.0, true}) // 1000m/s, 30deg/s, 100m fuse, 55 DMG
        .set<Sensor>({15000.0, 45.0, 0.1, -1.0}) // Seeker 15km, 45deg
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
    
    // Brute Force Iteration: Iterate ALL entities and filter manually.
    // This is 100% safe against Flecs C++ API version quirks regarding filters/queries.
    ecs.each([&](flecs::entity e) {
        // Fast filtering: Must have KeyEntity and SimObject (implied)
        const KeyEntity* k = e.get<KeyEntity>();
        if (!k) return; 
        
        const Transform* p = e.get<Transform>();
        const Velocity* v = e.get<Velocity>();
        const Alliance* a = e.get<Alliance>();
        
        if (p && v && a) {
            UnitData data;
            data.id = e.id();
            data.side = static_cast<int>(a->side);
            data.type = static_cast<int>(k->type);
            data.x = p->x;
            data.y = p->y;
            data.z = p->z;
            // Convert Math angle (0=East, CCW) to NAV angle (0=North, CW)
            double math_deg = std::atan2(v->vy, v->vx) * 180.0 / M_PI;
            double nav_deg = 90.0 - math_deg;
            // Normalize to [0, 360)
            while (nav_deg < 0) nav_deg += 360.0;
            while (nav_deg >= 360.0) nav_deg -= 360.0;
            data.heading = nav_deg;
            
            units.push_back(data);
        }
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
            
            // Calculate Azimuth/Elev Relative to Nose
            // det.bearing is absolute ENU bearing
            // self heading is ENU heading
            double az = det.bearing - (p ? p->heading : 0.0);
            while (az > 180.0) az -= 360.0;
            while (az < -180.0) az += 360.0;
            track.azimuth = az;
            
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
    obs.missiles_remaining = 4; // Infinite for now
    obs.can_fire = true;
    
    const Score* s = e.get<Score>();
    obs.total_reward = s ? s->total_reward : 0.0;
    
    return obs;
}
