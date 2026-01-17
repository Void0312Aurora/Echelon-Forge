#pragma once

#include <flecs.h>
#include <cmath>
#include <limits>
#include <memory>
#include <random>
#include <string>
#include "components/common.h"
#include "components/sensor.h"
#include "components/tags.h"
#include "unit_data.h"
#include "observation.h"

class IUnitFactory;
class IEffectsModel;
class ISensorModel;
class IControlModel;
class IGuidanceModel;

struct MissileTuning {
    double max_speed = std::numeric_limits<double>::quiet_NaN();
    double turn_rate = std::numeric_limits<double>::quiet_NaN();
    double fuse_distance = std::numeric_limits<double>::quiet_NaN();
    double damage = std::numeric_limits<double>::quiet_NaN();
    double seeker_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double seeker_lock_range = std::numeric_limits<double>::quiet_NaN();
    double guidance_delay_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_update_period_s = std::numeric_limits<double>::quiet_NaN();
    double max_flight_time_s = std::numeric_limits<double>::quiet_NaN();
    double nav_gain = std::numeric_limits<double>::quiet_NaN();
    double sensor_max_range = std::numeric_limits<double>::quiet_NaN();
    double sensor_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double sensor_scan_period = std::numeric_limits<double>::quiet_NaN();
    double sensor_detection_prob = std::numeric_limits<double>::quiet_NaN();
    double sensor_bearing_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_range_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_track_memory_s = std::numeric_limits<double>::quiet_NaN();
};

class SimulationKernel {
public:
    SimulationKernel();
    ~SimulationKernel();

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
    void set_unit_action(uint64_t entity_id,
                         double turn_rate_cmd,
                         double accel_cmd,
                         double climb_rate_cmd,
                         double fire_cmd);
    
    // Observation Interface
    std::vector<double> get_unit_position(uint64_t entity_id); // Returns [x, y, z]
    std::vector<UnitData> get_all_units(); // Bulk observation
    AgentObservation get_agent_observation(uint64_t entity_id); // RL Observation
    std::vector<Detection> get_detections(uint64_t entity_id); // Sensor Output
    std::vector<double> get_unit_health(uint64_t entity_id);   // Returns [current, max]
    double debug_get_last_scan_time(uint64_t entity_id);
    int debug_get_contact_count(uint64_t entity_id);

    // Weapon Interface: Fire missile
    flecs::entity fire_missile(uint64_t attacker_id, uint64_t target_id);

    // Unit factory override (for modular swaps)
    void set_unit_factory(std::unique_ptr<IUnitFactory> factory);
    void set_effects_model(std::unique_ptr<IEffectsModel> model);
    void set_sensor_model(std::unique_ptr<ISensorModel> model);
    void set_control_model(std::unique_ptr<IControlModel> model);
    void set_guidance_model(std::unique_ptr<IGuidanceModel> model);
    bool load_unit_definitions(const std::string& path, std::string* error = nullptr);
    void set_missile_tuning(const MissileTuning& tuning);

private:
    flecs::world ecs;
    double time_step = 1.0 / 60.0; // 60 Hz by default
    
    // Deterministic RNG (using std::mt19937 for MVP as planned, better than rand())
    // In production we might use Xoshiro/PCG
    std::mt19937 rng;

    std::unique_ptr<IUnitFactory> unit_factory_;
    std::unique_ptr<IEffectsModel> effects_model_;
    std::unique_ptr<ISensorModel> sensor_model_;
    std::unique_ptr<IControlModel> control_model_;
    std::unique_ptr<IGuidanceModel> guidance_model_;
    MissileTuning missile_tuning_;
};
