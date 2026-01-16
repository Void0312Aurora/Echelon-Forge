#pragma once

#include <flecs.h>
#include <cmath>
#include <random>
#include "components/common.h"
#include "components/sensor.h"
#include "unit_data.h"
#include "observation.h"

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

    // Action Interface: Set command for a unit
    void set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps, double altitude_m);
    
    // Observation Interface
    std::vector<double> get_unit_position(uint64_t entity_id); // Returns [x, y, z]
    std::vector<UnitData> get_all_units(); // Bulk observation
    AgentObservation get_agent_observation(uint64_t entity_id); // RL Observation
    std::vector<Detection> get_detections(uint64_t entity_id); // Sensor Output
    std::vector<double> get_unit_health(uint64_t entity_id);   // Returns [current, max]

    // Weapon Interface: Fire missile
    flecs::entity fire_missile(uint64_t attacker_id, uint64_t target_id);

private:
    flecs::world ecs;
    double time_step = 1.0 / 60.0; // 60 Hz by default
    
    // Deterministic RNG (using std::mt19937 for MVP as planned, better than rand())
    // In production we might use Xoshiro/PCG
    std::mt19937 rng;
};

// Tag Component for Reset Logic
struct SimObject {};
