#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "gpu/gpu_exact_world_step_contract.h"

namespace gpu {

enum class ExactWorldStepAircraftTailStopStage : int {
    RotationalIntegrate = 0,
    LeapfrogIntegrate = 1,
    NavigationSystem = 2,
    UpdateInstruments = 3,
    FuelConsumption = 4,
    MassUpdate = 5,
};

struct ExactWorldStepAircraftTailStats {
    std::size_t state_count = 0;
    double total_ms = 0.0;
};

struct ExactWorldStepAircraftTailSoA {
    std::size_t size = 0;

    std::vector<double> time_step_s;
    std::vector<Transform> transform;
    std::vector<Velocity> velocity;
    std::vector<AngularVelocity> angular_velocity;
    std::vector<ForceAccumulator> force_accumulator;
    std::vector<Mass> mass;
    std::vector<Inertia> inertia;
    std::vector<AeroState> aero_state;
    std::vector<Propulsion> propulsion;
    std::vector<FuelSystem> fuel_system;
    std::vector<MassProperties> mass_properties;
    std::vector<InstrumentState> instrument_state;
    std::vector<EGI> egi;
    std::vector<PilotAction> pilot_action;
    std::vector<MovementCommand> movement_command;
    std::vector<ActionCommand> action_command;
    std::vector<MissionCommand> mission_command;
    std::vector<LandingGear> landing_gear;
    std::vector<GearState> gear_state;
    std::vector<Ammo> ammo;
    std::vector<ExactWorldStepRwrSummaryV1> rwr_summary;
    std::vector<ExactWorldStepEnvironmentSampleV1> environment_sample;

    std::vector<std::uint8_t> has_angular_velocity;
    std::vector<std::uint8_t> has_force_accumulator;
    std::vector<std::uint8_t> has_mass;
    std::vector<std::uint8_t> has_inertia;
    std::vector<std::uint8_t> has_aero_state;
    std::vector<std::uint8_t> has_propulsion;
    std::vector<std::uint8_t> has_fuel_system;
    std::vector<std::uint8_t> has_mass_properties;
    std::vector<std::uint8_t> has_instrument_state;
    std::vector<std::uint8_t> has_egi;
    std::vector<std::uint8_t> has_pilot_action;
    std::vector<std::uint8_t> has_movement_command;
    std::vector<std::uint8_t> has_action_command;
    std::vector<std::uint8_t> has_mission_command;
    std::vector<std::uint8_t> has_landing_gear;
    std::vector<std::uint8_t> has_gear_state;
    std::vector<std::uint8_t> has_ammo;
    std::vector<std::uint8_t> has_rwr_summary;
    std::vector<std::uint8_t> has_environment_sample;
};

ExactWorldStepAircraftTailSoA pack_exact_world_step_states_v1_aircraft_tail_soa(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1_aircraft_tail_soa(
    const ExactWorldStepAircraftTailSoA& soa,
    const std::vector<ExactWorldStepStateV1>& basis_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_reference_cpu_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states
);

std::vector<ExactWorldStepStateV1> step_exact_world_step_aircraft_tail_until_stage_batch(
    const std::vector<ExactWorldStepStateV1>& initial_states,
    ExactWorldStepAircraftTailStopStage stop_stage
);

const ExactWorldStepAircraftTailStats& last_exact_world_step_aircraft_tail_stats() noexcept;

}  // namespace gpu
