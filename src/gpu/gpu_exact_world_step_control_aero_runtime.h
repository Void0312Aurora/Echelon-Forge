#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu {

struct ExactWorldStepControlAeroStats {
    std::size_t state_count = 0;
    double total_ms = 0.0;
};

struct ExactWorldStepControlAeroSoA {
    std::size_t size = 0;

    std::vector<double> time_step_s;

    std::vector<Transform> transform;
    std::vector<Velocity> velocity;
    std::vector<AngularVelocity> angular_velocity;
    std::vector<ForceAccumulator> force_accumulator;
    std::vector<AeroState> aero_state;
    std::vector<ControlLawState> control_law_state;
    std::vector<PilotAction> pilot_action;
    std::vector<MissionCommand> mission_command;
    std::vector<LaggedCommand> lagged_command;
    std::vector<FlightModel> flight_model;
    std::vector<LandingGear> landing_gear;
    std::vector<GroundState> ground_state;
    std::vector<ExactWorldStepEnvironmentSampleV1> environment_sample;

    std::vector<std::uint8_t> has_angular_velocity;
    std::vector<std::uint8_t> has_force_accumulator;
    std::vector<std::uint8_t> has_aero_state;
    std::vector<std::uint8_t> has_control_law_state;
    std::vector<std::uint8_t> has_pilot_action;
    std::vector<std::uint8_t> has_mission_command;
    std::vector<std::uint8_t> has_lagged_command;
    std::vector<std::uint8_t> has_flight_model;
    std::vector<std::uint8_t> has_landing_gear;
    std::vector<std::uint8_t> has_ground_state;
    std::vector<std::uint8_t> has_environment_sample;
};

ExactWorldStepControlAeroSoA pack_exact_world_step_states_v1_control_aero_soa(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_control_aero_soa(
    const ExactWorldStepControlAeroSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_control_aero_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

const ExactWorldStepControlAeroStats& last_exact_world_step_control_aero_stats() noexcept;

}  // namespace gpu
