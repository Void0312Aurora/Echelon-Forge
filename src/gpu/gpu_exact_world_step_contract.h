#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "components/basic/common.h"
#include "components/combat/weapon.h"
#include "components/physics/action.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/combat/health.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"

namespace gpu {

inline constexpr std::size_t kExactWorldStepContactSummaryCapacity = 8;

struct ExactWorldStepEnvironmentSampleV1 {
    double terrain_elevation_m = 0.0;
    double wind_vx_mps = 0.0;
    double wind_vy_mps = 0.0;
    std::uint8_t terrain_surface_code = 0;
    double runway_heading_deg = 0.0;
};

struct ExactWorldStepRwrSummaryV1 {
    std::uint32_t detected_count = 0;
    std::uint32_t locking_count = 0;
    bool is_missile_launch = false;
};

struct ExactWorldStepContactListSummaryV1 {
    std::uint32_t count = 0;
    bool truncated = false;
    std::array<Detection, kExactWorldStepContactSummaryCapacity> contacts{};
};

struct ExactWorldStepStateV1 {
    std::uint64_t entity_id = 0;
    double time_step_s = 1.0 / 60.0;
    double world_time_s = 0.0;

    Transform transform{};
    Velocity velocity{};

    AngularVelocity angular_velocity{};
    ForceAccumulator force_accumulator{};
    AeroState aero_state{};
    ControlLawState control_law_state{};
    PilotAction pilot_action{};
    MissionCommand mission_command{};
    MovementCommand movement_command{};
    ActionCommand action_command{};
    ActionSpaceConfig action_space_config{};
    CommandLag command_lag{};
    LaggedCommand lagged_command{};
    CommandLink command_link{};
    PendingMovementCommand pending_movement_command{};
    PendingActionCommand pending_action_command{};
    PendingMissionCommand pending_mission_command{};
    FlightModel flight_model{};
    Inertia inertia{};
    LandingGear landing_gear{};
    GearState gear_state{};
    FuelSystem fuel_system{};
    Mass mass{};
    Propulsion propulsion{};
    MassProperties mass_properties{};
    GroundState ground_state{};
    Health health{};
    Ammo ammo{};
    Missile missile{};
    ExactWorldStepRwrSummaryV1 rwr_summary{};
    ExactWorldStepContactListSummaryV1 contact_list_summary{};
    InstrumentState instrument_state{};
    EGI egi{};
    ExactWorldStepEnvironmentSampleV1 environment_sample{};

    bool has_environment_sample = false;
    bool has_angular_velocity = false;
    bool has_force_accumulator = false;
    bool has_aero_state = false;
    bool has_control_law_state = false;
    bool has_pilot_action = false;
    bool has_mission_command = false;
    bool has_movement_command = false;
    bool has_action_command = false;
    bool has_action_space_config = false;
    bool has_command_lag = false;
    bool has_lagged_command = false;
    bool has_command_link = false;
    bool has_pending_movement_command = false;
    bool has_pending_action_command = false;
    bool has_pending_mission_command = false;
    bool has_flight_model = false;
    bool has_inertia = false;
    bool has_landing_gear = false;
    bool has_gear_state = false;
    bool has_fuel_system = false;
    bool has_mass = false;
    bool has_propulsion = false;
    bool has_mass_properties = false;
    bool has_ground_state = false;
    bool has_health = false;
    bool has_ammo = false;
    bool has_missile = false;
    bool has_rwr_summary = false;
    bool has_contact_list_summary = false;
    bool has_instrument_state = false;
    bool has_egi = false;
};

std::size_t exact_world_step_state_v1_size_bytes() noexcept;

std::string pack_exact_world_step_states_v1(const std::vector<ExactWorldStepStateV1>& states);

std::vector<ExactWorldStepStateV1> unpack_exact_world_step_states_v1(std::string_view packed);

std::uint64_t exact_world_step_state_v1_apply_signature(const ExactWorldStepStateV1& state) noexcept;

std::vector<std::uint64_t> exact_world_step_state_v1_apply_signatures(
    const std::vector<ExactWorldStepStateV1>& states
);

std::vector<std::pair<std::string, std::uint64_t>> exact_world_step_state_v1_component_digests(
    const ExactWorldStepStateV1& state
);

}  // namespace gpu
