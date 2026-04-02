#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu {

struct ExactWorldStepForceGroundStats {
    std::size_t state_count = 0;
    double total_ms = 0.0;
};

struct ExactWorldStepForceGroundSoA {
    std::size_t size = 0;

    std::vector<double> time_step_s;

    std::vector<Transform> transform;
    std::vector<Velocity> velocity;
    std::vector<AngularVelocity> angular_velocity;
    std::vector<ForceAccumulator> force_accumulator;
    std::vector<AeroState> aero_state;
    std::vector<ControlLawState> control_law_state;
    std::vector<PilotAction> pilot_action;
    std::vector<MovementCommand> movement_command;
    std::vector<Mass> mass;
    std::vector<Propulsion> propulsion;
    std::vector<FlightModel> flight_model;
    std::vector<MassProperties> mass_properties;
    std::vector<LandingGear> landing_gear;
    std::vector<GearState> gear_state;
    std::vector<GroundState> ground_state;
    std::vector<Health> health;
    std::vector<ExactWorldStepEnvironmentSampleV1> environment_sample;

    std::vector<std::uint8_t> has_angular_velocity;
    std::vector<std::uint8_t> has_force_accumulator;
    std::vector<std::uint8_t> has_aero_state;
    std::vector<std::uint8_t> has_control_law_state;
    std::vector<std::uint8_t> has_pilot_action;
    std::vector<std::uint8_t> has_movement_command;
    std::vector<std::uint8_t> has_mass;
    std::vector<std::uint8_t> has_propulsion;
    std::vector<std::uint8_t> has_flight_model;
    std::vector<std::uint8_t> has_mass_properties;
    std::vector<std::uint8_t> has_landing_gear;
    std::vector<std::uint8_t> has_gear_state;
    std::vector<std::uint8_t> has_ground_state;
    std::vector<std::uint8_t> has_health;
    std::vector<std::uint8_t> has_environment_sample;
};

ExactWorldStepForceGroundSoA pack_exact_world_step_states_v1_force_ground_soa(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_force_ground_soa(
    const ExactWorldStepForceGroundSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_force_ground_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

const ExactWorldStepForceGroundStats& last_exact_world_step_force_ground_stats() noexcept;

}  // namespace gpu
