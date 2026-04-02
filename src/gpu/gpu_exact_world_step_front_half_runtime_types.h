#pragma once

#include <cstdint>

namespace gpu::front_half {

enum class RecoveryApproachType : int {
    None = 0,
    StraightIn = 1,
    ILS = 2,
    Visual = 3,
    Overhead = 4,
    TACAN = 5,
};

struct Transform {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
};

struct Velocity {
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
};

struct AngularVelocity {
    double p = 0.0;
    double q = 0.0;
    double r = 0.0;
};

struct ForceAccumulator {
    double fx = 0.0;
    double fy = 0.0;
    double fz = 0.0;
    double torque_roll = 0.0;
    double torque_pitch = 0.0;
    double torque_yaw = 0.0;
};

struct AeroState {
    double dynamic_pressure = 0.0;
    double angle_of_attack = 0.0;
    double sideslip_angle = 0.0;
    double mach_number = 0.0;
    double lift_coefficient = 0.0;
    double drag_coefficient = 0.0;
};

struct ControlLawState {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;
};

struct PilotAction {
    double stick_pitch = 0.0;
    double stick_roll = 0.0;
    double rudder = 0.0;
    double throttle = 0.0;
    float gear_handle = 0.0f;
    float flaps = 0.0f;
    float speedbrake = 0.0f;
    double brake = 0.0;
    bool brake_left = false;
    bool brake_right = false;
    bool active = false;
};

struct MissionCommand {
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    int command_code = 0;
    RecoveryApproachType recovery_approach_type = RecoveryApproachType::None;
    bool active = false;
};

struct MovementCommand {
    double throttle_cmd = 0.0;
    bool active = false;
};

struct LandingGear {
    double rolling_friction_coeff = 0.02;
    double contact_height_m = 2.0;
    double extension_state = 1.0;
    double transit_time_s = 5.0;
};

struct GearState {
    bool gear_down = true;
    double stress = 0.0;
    bool collapsed = false;
    double stress_rate = 0.0;
    bool on_runway = true;
};

struct Mass {
    double empty_mass_kg = 0.0;
    double fuel_mass_kg = 0.0;
    double stores_mass_kg = 0.0;
};

struct Propulsion {
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double current_thrust_n = 0.0;
    bool afterburner_active = false;
};

struct MassProperties {
    double current_drag_index = 0.0;
    double reference_area_m2 = 0.0;
    double wing_span_m = 10.0;
    double chord_m = 3.0;
};

struct GroundState {
    bool on_ground = false;
    double terrain_elevation = 0.0;
};

struct Health {
    double current_hp = 0.0;
};

struct EnvironmentSample {
    double terrain_elevation_m = 0.0;
    double wind_vx_mps = 0.0;
    double wind_vy_mps = 0.0;
    std::uint8_t terrain_surface_code = 0;
};

struct ExactWorldStepFrontHalfState {
    double time_step_s = 1.0 / 60.0;

    Transform transform{};
    Velocity velocity{};
    AngularVelocity angular_velocity{};
    ForceAccumulator force_accumulator{};
    AeroState aero_state{};
    ControlLawState control_law_state{};
    PilotAction pilot_action{};
    MissionCommand mission_command{};
    MovementCommand movement_command{};
    LandingGear landing_gear{};
    GearState gear_state{};
    Mass mass{};
    Propulsion propulsion{};
    MassProperties mass_properties{};
    GroundState ground_state{};
    Health health{};
    EnvironmentSample environment_sample{};

    bool has_angular_velocity = false;
    bool has_force_accumulator = false;
    bool has_aero_state = false;
    bool has_control_law_state = false;
    bool has_pilot_action = false;
    bool has_mission_command = false;
    bool has_movement_command = false;
    bool has_lagged_command = false;
    bool has_flight_model = false;
    bool has_landing_gear = false;
    bool has_gear_state = false;
    bool has_mass = false;
    bool has_propulsion = false;
    bool has_mass_properties = false;
    bool has_ground_state = false;
    bool has_health = false;
    bool has_environment_sample = false;
};

}  // namespace gpu::front_half
