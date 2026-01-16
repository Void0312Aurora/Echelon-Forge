#pragma once

#include <flecs.h>
#include <random>
#include "components/common.h"

class SimulationKernel {
public:
    SimulationKernel();
    ~SimulationKernel() = default;

    // Reset the simulation to initial state with a specific random seed
    void reset(unsigned int seed);

    // Advance the simulation by one fixed time step
    void step();

    // Spawn a basic unit (for testing/gym API)
    flecs::entity spawn_unit(Side side, UnitType type, 
                             double x, double y, double z, 
                             double vx, double vy, double vz);

    // Get the Flecs world (for systems/bindings)
    flecs::world& get_world() { return ecs; }

    double get_time_step() const { return time_step; }
    void set_time_step(double dt) { time_step = dt; }

private:
    flecs::world ecs;
    double time_step = 1.0 / 60.0; // 60 Hz by default
    
    // Deterministic RNG (using std::mt19937 for MVP as planned, better than rand())
    // In production we might use Xoshiro/PCG
    std::mt19937 rng;
};
