#include "simulation_kernel.h"
#include "systems/movement_system.h"
#include "systems/control_system.h"
#include "systems/guidance_system.h"
#include "systems/damage_system.h"
#include "components/action.h"
#include <spdlog/spdlog.h>

SimulationKernel::SimulationKernel() {
    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();
    ecs.component<MovementCommand>();
    ecs.component<Missile>();

    // Register Systems
    register_control_system(ecs); // Control updates Velocity
    register_guidance_system(ecs); // Guidance updates Velocity (PN)
    register_movement_system(ecs); // Movement updates Transform
    register_damage_system(ecs);   // Damage destroys entities


    reset(42); // Default reset
}

void SimulationKernel::reset(unsigned int seed) {
    // Determine the cleanup strategy. 
    // ecs.reset() might be too aggressive (clearing systems/components).
    // Usage of .delete_with(flecs::Wildcard) cleans up all entities.
    
    // However, since we might have singleton entities or system entities, 
    // we should be careful. 
    // For now, let's just delete all entities that have Transform (our units).
    // Or iterate the root scope.
    
    // ecs.delete_with(flecs::Wildcard); // UNSAFE: Deletes component definitions
    ecs.delete_with<Transform>();
    
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
        .set<KeyEntity>({type});
    
    return e;
}

void SimulationKernel::set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        e.set<MovementCommand>({heading_deg, speed_mps, true});
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
        .set<Missile>({target_id, 1000.0, 30.0, 100.0, true}); // 1000m/s, 30deg/s, 100m fuse
        
    spdlog::info("FOX 2! Missile {} fired by {} at {}", m.id(), attacker_id, target_id);
    return m;
}
