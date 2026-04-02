#pragma once

#include <cstdint>

namespace gpu::aircraft_tail_cuda {

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

struct Mass {
    double empty_mass_kg = 0.0;
    double fuel_mass_kg = 0.0;
    double stores_mass_kg = 0.0;
};

struct Inertia {
    double ixx = 10000.0;
    double iyy = 10000.0;
    double izz = 10000.0;
};

struct AeroState {
    double dynamic_pressure = 0.0;
    double angle_of_attack = 0.0;
    double sideslip_angle = 0.0;
    double mach_number = 0.0;
    double lift_coefficient = 0.0;
    double drag_coefficient = 0.0;
};

struct Propulsion {
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double current_thrust_n = 0.0;
    bool afterburner_active = false;
};

struct FuelSystem {
    double internal_fuel_kg = 0.0;
    double external_fuel_kg = 0.0;
    double current_flow_rate = 0.0;
    bool afterburner_active = false;
    double mil_power_flow_rate = 0.0;
    double ab_flow_rate_multiplier = 0.0;
};

struct MassProperties {
    double empty_mass_kg = 0.0;
    double current_total_mass_kg = 0.0;
    double current_drag_index = 0.0;
    double reference_area_m2 = 0.0;
    double wing_span_m = 10.0;
    double chord_m = 3.0;
};

struct InstrumentState {
    double alt_baro_m = 0.0;
    double alt_radar_m = 0.0;
    double ias_mps = 0.0;
    double mach = 0.0;
    double vvi_mps = 0.0;
    double pitch_deg = 0.0;
    double roll_deg = 0.0;
    double heading_deg = 0.0;
    double aoa_deg = 0.0;
    double beta_deg = 0.0;
    double g_load_normal = 0.0;
    double g_load_axial = 0.0;
    double p_deg_s = 0.0;
    double q_deg_s = 0.0;
    double r_deg_s = 0.0;
    double engine_rpm_pct = 0.0;
    double engine_temp_c = 0.0;
    double fuel_flow_kg_h = 0.0;
    double throttle_pos = 0.0;
    double fuel_internal_kg = 0.0;
    double fuel_external_kg = 0.0;
    float gear_pos = 0.0f;
    float flaps_pos = 0.0f;
    float speedbrake_pos = 0.0f;
    bool master_arm = false;
    double oat_c = 0.0;
    double cmd_heading_deg = 0.0;
    double cmd_alt_m = 0.0;
    double cmd_speed_mps = 0.0;
    bool rwr_active = false;
    int weapon_selected = 0;
    int missiles_remaining = 0;
    double lat_deg = 0.0;
    double lon_deg = 0.0;
    double vn_mps = 0.0;
    double ve_mps = 0.0;
    double vd_mps = 0.0;
    double ground_speed_mps = 0.0;
    double ground_track_deg = 0.0;
    double wind_speed_mps = 0.0;
    double wind_dir_deg = 0.0;
    bool gps_available = false;
    double position_uncertainty_m = 0.0;
    double gear_stress = 0.0;
    bool gear_collapsed = false;
    bool on_runway = true;
};

struct EGI {
    double lat_deg = 0.0;
    double lon_deg = 0.0;
    double alt_baro_m = 0.0;
    double alt_radar_m = 0.0;
    double vn_mps = 0.0;
    double ve_mps = 0.0;
    double vd_mps = 0.0;
    double heading_deg = 0.0;
    double pitch_deg = 0.0;
    double roll_deg = 0.0;
    double wind_speed_mps = 0.0;
    double wind_dir_deg = 0.0;
    double drift_lat_m = 0.0;
    double drift_lon_m = 0.0;
    double drift_alt_m = 0.0;
    double position_uncertainty_m = 0.0;
    double time_since_last_gps_fix = 0.0;
    double ins_drift_rate_mps = 0.5;
    bool gps_available = false;
};

struct PilotAction {
    double throttle = 0.0;
    float flaps = 0.0f;
    float speedbrake = 0.0f;
    bool master_arm = false;
    int weapon_select_id = 0;
    bool active = false;
};

struct MovementCommand {
    double throttle_cmd = 0.0;
    bool active = false;
};

struct ActionCommand {
    double accel_cmd = 0.0;
    bool active = false;
};

struct MissionCommand {
    int command_code = 0;
    double cmd_heading_deg = 0.0;
    double cmd_altitude_m = 0.0;
    double cmd_speed_mps = 0.0;
    bool active = false;
};

struct LandingGear {
    double extension_state = 1.0;
};

struct GearState {
    double stress = 0.0;
    bool collapsed = false;
    bool on_runway = true;
};

struct Ammo {
    int missiles_remaining = 0;
};

struct RwrSummary {
    std::uint32_t detected_count = 0;
};

struct EnvironmentSample {
    double terrain_elevation_m = 0.0;
    double wind_vx_mps = 0.0;
    double wind_vy_mps = 0.0;
    std::uint8_t terrain_surface_code = 0;
    double runway_heading_deg = 0.0;
};

struct ExactWorldStepAircraftTailCudaState {
    double time_step_s = 1.0 / 60.0;

    Transform transform{};
    Velocity velocity{};
    AngularVelocity angular_velocity{};
    ForceAccumulator force_accumulator{};
    Mass mass{};
    Inertia inertia{};
    AeroState aero_state{};
    Propulsion propulsion{};
    FuelSystem fuel_system{};
    MassProperties mass_properties{};
    InstrumentState instrument_state{};
    EGI egi{};
    PilotAction pilot_action{};
    MovementCommand movement_command{};
    ActionCommand action_command{};
    MissionCommand mission_command{};
    LandingGear landing_gear{};
    GearState gear_state{};
    Ammo ammo{};
    RwrSummary rwr_summary{};
    EnvironmentSample environment_sample{};

    bool has_angular_velocity = false;
    bool has_force_accumulator = false;
    bool has_mass = false;
    bool has_inertia = false;
    bool has_aero_state = false;
    bool has_propulsion = false;
    bool has_fuel_system = false;
    bool has_mass_properties = false;
    bool has_instrument_state = false;
    bool has_egi = false;
    bool has_pilot_action = false;
    bool has_movement_command = false;
    bool has_action_command = false;
    bool has_mission_command = false;
    bool has_landing_gear = false;
    bool has_gear_state = false;
    bool has_ammo = false;
    bool has_rwr_summary = false;
    bool has_environment_sample = false;
};

}  // namespace gpu::aircraft_tail_cuda
