#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace gpu {

struct ExactWorldStepPrototypeStats {
    bool used_cuda = false;
    double host_to_device_ms = 0.0;
    double kernel_ms = 0.0;
    double device_to_host_ms = 0.0;
    double total_ms = 0.0;
};

struct ExactWorldStepPrototypeSoA {
    std::size_t size = 0;

    std::vector<double> time_step_s;
    std::vector<double> world_time_s;

    std::vector<double> x_m;
    std::vector<double> y_m;
    std::vector<double> z_m;
    std::vector<double> heading_deg;
    std::vector<double> pitch_deg;
    std::vector<double> roll_deg;

    std::vector<double> vx_mps;
    std::vector<double> vy_mps;
    std::vector<double> vz_mps;
    std::vector<double> p_rad_s;
    std::vector<double> q_rad_s;
    std::vector<double> r_rad_s;
    std::vector<double> g_load_normal;
    std::vector<double> g_load_axial;

    std::vector<double> wind_vx_mps;
    std::vector<double> wind_vy_mps;
    std::vector<double> terrain_elevation_m;

    std::vector<double> target_heading_deg;
    std::vector<double> target_speed_mps;
    std::vector<double> target_altitude_m;

    std::vector<double> heading_tau_s;
    std::vector<double> speed_tau_s;
    std::vector<double> altitude_tau_s;
    std::vector<std::uint8_t> has_command_lag;

    std::vector<double> lagged_heading_deg;
    std::vector<double> lagged_speed_mps;
    std::vector<double> lagged_altitude_m;
    std::vector<std::uint8_t> lagged_active;
    std::vector<std::uint8_t> output_has_lagged_command;

    std::vector<double> max_speed_mps;
    std::vector<double> min_speed_mps;
    std::vector<double> max_accel_mps2;
    std::vector<double> max_climb_rate_mps;
    std::vector<double> reference_area_m2;
    std::vector<double> wing_span_m;
    std::vector<double> chord_m;
    std::vector<double> current_drag_index;
    std::vector<double> gear_extension_state;
    std::vector<double> aero_dynamic_pressure_pa;
    std::vector<double> aero_mach_number;
    std::vector<double> aero_angle_of_attack_deg;
    std::vector<double> aero_sideslip_angle_deg;
    std::vector<double> aero_lift_coefficient;
    std::vector<double> aero_drag_coefficient;
    std::vector<double> force_fx_n;
    std::vector<double> force_fy_n;
    std::vector<double> force_fz_n;
    std::vector<double> force_torque_roll_nm;
    std::vector<double> force_torque_pitch_nm;
    std::vector<double> force_torque_yaw_nm;
    std::vector<double> control_stick_roll_filt;
    std::vector<double> control_stick_pitch_filt;
    std::vector<double> control_stick_yaw_filt;
    std::vector<double> control_stick_yaw_cmd;
    std::vector<std::int32_t> control_profile_code;
    std::vector<std::uint8_t> has_angular_velocity;
    std::vector<std::uint8_t> has_force_accumulator;
    std::vector<std::uint8_t> has_aero_state;
    std::vector<std::uint8_t> has_control_law_state;

    std::vector<double> fuel_internal_kg;
    std::vector<double> fuel_external_kg;
    std::vector<double> fuel_flow_rate_kgps;
    std::vector<double> fuel_ab_multiplier;
    std::vector<std::uint8_t> fuel_afterburner_active;
    std::vector<std::uint8_t> has_fuel_system;
    std::vector<double> propulsion_current_thrust_n;
    std::vector<std::uint8_t> has_propulsion;

    std::vector<double> mass_empty_kg;
    std::vector<double> mass_stores_kg;
    std::vector<double> mass_fuel_kg;
    std::vector<double> mass_fuel_leak_rate_kgps;
    std::vector<std::uint8_t> has_mass;

    std::vector<double> total_mass_kg;
    std::vector<std::uint8_t> has_mass_properties;

    std::vector<std::uint8_t> has_ground_state;
    std::vector<std::uint8_t> has_instrument_state;
    std::vector<std::uint8_t> has_egi;
};

}  // namespace gpu
