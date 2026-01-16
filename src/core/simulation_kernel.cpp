#include "simulation_kernel.h"
#include "systems/movement_system.h"
#include <spdlog/spdlog.h>

SimulationKernel::SimulationKernel() {
    // Initialize common components
    ecs.component<Transform>();
    ecs.component<Velocity>();
    ecs.component<Alliance>();
    ecs.component<KeyEntity>();

    // Register Systems
    register_movement_system(ecs);

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
