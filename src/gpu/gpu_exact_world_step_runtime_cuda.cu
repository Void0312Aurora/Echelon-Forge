#include "gpu/gpu_exact_world_step_runtime_types.h"

#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kCanonicalQuantum = 1e-8;
constexpr double kGravityMps2 = 9.80665;

struct DeviceSoA {
    std::size_t count = 0;

    double* time_step_s = nullptr;
    double* world_time_s = nullptr;
    double* x_m = nullptr;
    double* y_m = nullptr;
    double* z_m = nullptr;
    double* heading_deg = nullptr;
    double* pitch_deg = nullptr;
    double* roll_deg = nullptr;
    double* vx_mps = nullptr;
    double* vy_mps = nullptr;
    double* vz_mps = nullptr;
    double* p_rad_s = nullptr;
    double* q_rad_s = nullptr;
    double* r_rad_s = nullptr;
    double* g_load_normal = nullptr;
    double* g_load_axial = nullptr;
    double* wind_vx_mps = nullptr;
    double* wind_vy_mps = nullptr;
    double* terrain_elevation_m = nullptr;
    double* target_heading_deg = nullptr;
    double* target_speed_mps = nullptr;
    double* target_altitude_m = nullptr;
    double* heading_tau_s = nullptr;
    double* speed_tau_s = nullptr;
    double* altitude_tau_s = nullptr;
    std::uint8_t* has_command_lag = nullptr;
    double* lagged_heading_deg = nullptr;
    double* lagged_speed_mps = nullptr;
    double* lagged_altitude_m = nullptr;
    std::uint8_t* lagged_active = nullptr;
    std::uint8_t* output_has_lagged_command = nullptr;
    double* max_speed_mps = nullptr;
    double* min_speed_mps = nullptr;
    double* max_accel_mps2 = nullptr;
    double* max_climb_rate_mps = nullptr;
    double* reference_area_m2 = nullptr;
    double* wing_span_m = nullptr;
    double* chord_m = nullptr;
    double* current_drag_index = nullptr;
    double* gear_extension_state = nullptr;
    double* aero_dynamic_pressure_pa = nullptr;
    double* aero_mach_number = nullptr;
    double* aero_angle_of_attack_deg = nullptr;
    double* aero_sideslip_angle_deg = nullptr;
    double* aero_lift_coefficient = nullptr;
    double* aero_drag_coefficient = nullptr;
    double* force_fx_n = nullptr;
    double* force_fy_n = nullptr;
    double* force_fz_n = nullptr;
    double* force_torque_roll_nm = nullptr;
    double* force_torque_pitch_nm = nullptr;
    double* force_torque_yaw_nm = nullptr;
    double* control_stick_roll_filt = nullptr;
    double* control_stick_pitch_filt = nullptr;
    double* control_stick_yaw_filt = nullptr;
    double* control_stick_yaw_cmd = nullptr;
    std::int32_t* control_profile_code = nullptr;
    std::uint8_t* has_angular_velocity = nullptr;
    std::uint8_t* has_force_accumulator = nullptr;
    std::uint8_t* has_aero_state = nullptr;
    std::uint8_t* has_control_law_state = nullptr;
    double* fuel_internal_kg = nullptr;
    double* fuel_external_kg = nullptr;
    double* fuel_flow_rate_kgps = nullptr;
    double* fuel_ab_multiplier = nullptr;
    std::uint8_t* fuel_afterburner_active = nullptr;
    std::uint8_t* has_fuel_system = nullptr;
    double* propulsion_current_thrust_n = nullptr;
    std::uint8_t* has_propulsion = nullptr;
    double* mass_empty_kg = nullptr;
    double* mass_stores_kg = nullptr;
    double* mass_fuel_kg = nullptr;
    double* mass_fuel_leak_rate_kgps = nullptr;
    std::uint8_t* has_mass = nullptr;
    double* total_mass_kg = nullptr;
    std::uint8_t* has_mass_properties = nullptr;
    std::uint8_t* has_ground_state = nullptr;
    std::uint8_t* has_instrument_state = nullptr;
    std::uint8_t* has_egi = nullptr;
};

template <typename T>
void free_device_ptr(T*& ptr) {
    if (ptr != nullptr) {
        cudaFree(ptr);
        ptr = nullptr;
    }
}

void release(DeviceSoA& device) {
    free_device_ptr(device.time_step_s);
    free_device_ptr(device.world_time_s);
    free_device_ptr(device.x_m);
    free_device_ptr(device.y_m);
    free_device_ptr(device.z_m);
    free_device_ptr(device.heading_deg);
    free_device_ptr(device.pitch_deg);
    free_device_ptr(device.roll_deg);
    free_device_ptr(device.vx_mps);
    free_device_ptr(device.vy_mps);
    free_device_ptr(device.vz_mps);
    free_device_ptr(device.p_rad_s);
    free_device_ptr(device.q_rad_s);
    free_device_ptr(device.r_rad_s);
    free_device_ptr(device.g_load_normal);
    free_device_ptr(device.g_load_axial);
    free_device_ptr(device.wind_vx_mps);
    free_device_ptr(device.wind_vy_mps);
    free_device_ptr(device.terrain_elevation_m);
    free_device_ptr(device.target_heading_deg);
    free_device_ptr(device.target_speed_mps);
    free_device_ptr(device.target_altitude_m);
    free_device_ptr(device.heading_tau_s);
    free_device_ptr(device.speed_tau_s);
    free_device_ptr(device.altitude_tau_s);
    free_device_ptr(device.has_command_lag);
    free_device_ptr(device.lagged_heading_deg);
    free_device_ptr(device.lagged_speed_mps);
    free_device_ptr(device.lagged_altitude_m);
    free_device_ptr(device.lagged_active);
    free_device_ptr(device.output_has_lagged_command);
    free_device_ptr(device.max_speed_mps);
    free_device_ptr(device.min_speed_mps);
    free_device_ptr(device.max_accel_mps2);
    free_device_ptr(device.max_climb_rate_mps);
    free_device_ptr(device.reference_area_m2);
    free_device_ptr(device.wing_span_m);
    free_device_ptr(device.chord_m);
    free_device_ptr(device.current_drag_index);
    free_device_ptr(device.gear_extension_state);
    free_device_ptr(device.aero_dynamic_pressure_pa);
    free_device_ptr(device.aero_mach_number);
    free_device_ptr(device.aero_angle_of_attack_deg);
    free_device_ptr(device.aero_sideslip_angle_deg);
    free_device_ptr(device.aero_lift_coefficient);
    free_device_ptr(device.aero_drag_coefficient);
    free_device_ptr(device.force_fx_n);
    free_device_ptr(device.force_fy_n);
    free_device_ptr(device.force_fz_n);
    free_device_ptr(device.force_torque_roll_nm);
    free_device_ptr(device.force_torque_pitch_nm);
    free_device_ptr(device.force_torque_yaw_nm);
    free_device_ptr(device.control_stick_roll_filt);
    free_device_ptr(device.control_stick_pitch_filt);
    free_device_ptr(device.control_stick_yaw_filt);
    free_device_ptr(device.control_stick_yaw_cmd);
    free_device_ptr(device.control_profile_code);
    free_device_ptr(device.has_angular_velocity);
    free_device_ptr(device.has_force_accumulator);
    free_device_ptr(device.has_aero_state);
    free_device_ptr(device.has_control_law_state);
    free_device_ptr(device.fuel_internal_kg);
    free_device_ptr(device.fuel_external_kg);
    free_device_ptr(device.fuel_flow_rate_kgps);
    free_device_ptr(device.fuel_ab_multiplier);
    free_device_ptr(device.fuel_afterburner_active);
    free_device_ptr(device.has_fuel_system);
    free_device_ptr(device.propulsion_current_thrust_n);
    free_device_ptr(device.has_propulsion);
    free_device_ptr(device.mass_empty_kg);
    free_device_ptr(device.mass_stores_kg);
    free_device_ptr(device.mass_fuel_kg);
    free_device_ptr(device.mass_fuel_leak_rate_kgps);
    free_device_ptr(device.has_mass);
    free_device_ptr(device.total_mass_kg);
    free_device_ptr(device.has_mass_properties);
    free_device_ptr(device.has_ground_state);
    free_device_ptr(device.has_instrument_state);
    free_device_ptr(device.has_egi);
    device.count = 0;
}

template <typename T>
bool upload_vector(const std::vector<T>& host, T** device_ptr) {
    if (host.empty()) {
        *device_ptr = nullptr;
        return true;
    }
    if (cudaMalloc(device_ptr, host.size() * sizeof(T)) != cudaSuccess) {
        *device_ptr = nullptr;
        return false;
    }
    if (cudaMemcpy(*device_ptr, host.data(), host.size() * sizeof(T), cudaMemcpyHostToDevice) != cudaSuccess) {
        cudaFree(*device_ptr);
        *device_ptr = nullptr;
        return false;
    }
    return true;
}

template <typename T>
bool download_vector(std::vector<T>& host, const T* device_ptr) {
    if (host.empty() || device_ptr == nullptr) {
        return true;
    }
    return cudaMemcpy(host.data(), device_ptr, host.size() * sizeof(T), cudaMemcpyDeviceToHost) == cudaSuccess;
}

bool upload_soa(const gpu::ExactWorldStepPrototypeSoA& host, DeviceSoA& device) {
    release(device);
    device.count = host.size;
    return upload_vector(host.time_step_s, &device.time_step_s)
        && upload_vector(host.world_time_s, &device.world_time_s)
        && upload_vector(host.x_m, &device.x_m)
        && upload_vector(host.y_m, &device.y_m)
        && upload_vector(host.z_m, &device.z_m)
        && upload_vector(host.heading_deg, &device.heading_deg)
        && upload_vector(host.pitch_deg, &device.pitch_deg)
        && upload_vector(host.roll_deg, &device.roll_deg)
        && upload_vector(host.vx_mps, &device.vx_mps)
        && upload_vector(host.vy_mps, &device.vy_mps)
        && upload_vector(host.vz_mps, &device.vz_mps)
        && upload_vector(host.p_rad_s, &device.p_rad_s)
        && upload_vector(host.q_rad_s, &device.q_rad_s)
        && upload_vector(host.r_rad_s, &device.r_rad_s)
        && upload_vector(host.g_load_normal, &device.g_load_normal)
        && upload_vector(host.g_load_axial, &device.g_load_axial)
        && upload_vector(host.wind_vx_mps, &device.wind_vx_mps)
        && upload_vector(host.wind_vy_mps, &device.wind_vy_mps)
        && upload_vector(host.terrain_elevation_m, &device.terrain_elevation_m)
        && upload_vector(host.target_heading_deg, &device.target_heading_deg)
        && upload_vector(host.target_speed_mps, &device.target_speed_mps)
        && upload_vector(host.target_altitude_m, &device.target_altitude_m)
        && upload_vector(host.heading_tau_s, &device.heading_tau_s)
        && upload_vector(host.speed_tau_s, &device.speed_tau_s)
        && upload_vector(host.altitude_tau_s, &device.altitude_tau_s)
        && upload_vector(host.has_command_lag, &device.has_command_lag)
        && upload_vector(host.lagged_heading_deg, &device.lagged_heading_deg)
        && upload_vector(host.lagged_speed_mps, &device.lagged_speed_mps)
        && upload_vector(host.lagged_altitude_m, &device.lagged_altitude_m)
        && upload_vector(host.lagged_active, &device.lagged_active)
        && upload_vector(host.output_has_lagged_command, &device.output_has_lagged_command)
        && upload_vector(host.max_speed_mps, &device.max_speed_mps)
        && upload_vector(host.min_speed_mps, &device.min_speed_mps)
        && upload_vector(host.max_accel_mps2, &device.max_accel_mps2)
        && upload_vector(host.max_climb_rate_mps, &device.max_climb_rate_mps)
        && upload_vector(host.reference_area_m2, &device.reference_area_m2)
        && upload_vector(host.wing_span_m, &device.wing_span_m)
        && upload_vector(host.chord_m, &device.chord_m)
        && upload_vector(host.current_drag_index, &device.current_drag_index)
        && upload_vector(host.gear_extension_state, &device.gear_extension_state)
        && upload_vector(host.aero_dynamic_pressure_pa, &device.aero_dynamic_pressure_pa)
        && upload_vector(host.aero_mach_number, &device.aero_mach_number)
        && upload_vector(host.aero_angle_of_attack_deg, &device.aero_angle_of_attack_deg)
        && upload_vector(host.aero_sideslip_angle_deg, &device.aero_sideslip_angle_deg)
        && upload_vector(host.aero_lift_coefficient, &device.aero_lift_coefficient)
        && upload_vector(host.aero_drag_coefficient, &device.aero_drag_coefficient)
        && upload_vector(host.force_fx_n, &device.force_fx_n)
        && upload_vector(host.force_fy_n, &device.force_fy_n)
        && upload_vector(host.force_fz_n, &device.force_fz_n)
        && upload_vector(host.force_torque_roll_nm, &device.force_torque_roll_nm)
        && upload_vector(host.force_torque_pitch_nm, &device.force_torque_pitch_nm)
        && upload_vector(host.force_torque_yaw_nm, &device.force_torque_yaw_nm)
        && upload_vector(host.control_stick_roll_filt, &device.control_stick_roll_filt)
        && upload_vector(host.control_stick_pitch_filt, &device.control_stick_pitch_filt)
        && upload_vector(host.control_stick_yaw_filt, &device.control_stick_yaw_filt)
        && upload_vector(host.control_stick_yaw_cmd, &device.control_stick_yaw_cmd)
        && upload_vector(host.control_profile_code, &device.control_profile_code)
        && upload_vector(host.has_angular_velocity, &device.has_angular_velocity)
        && upload_vector(host.has_force_accumulator, &device.has_force_accumulator)
        && upload_vector(host.has_aero_state, &device.has_aero_state)
        && upload_vector(host.has_control_law_state, &device.has_control_law_state)
        && upload_vector(host.fuel_internal_kg, &device.fuel_internal_kg)
        && upload_vector(host.fuel_external_kg, &device.fuel_external_kg)
        && upload_vector(host.fuel_flow_rate_kgps, &device.fuel_flow_rate_kgps)
        && upload_vector(host.fuel_ab_multiplier, &device.fuel_ab_multiplier)
        && upload_vector(host.fuel_afterburner_active, &device.fuel_afterburner_active)
        && upload_vector(host.has_fuel_system, &device.has_fuel_system)
        && upload_vector(host.propulsion_current_thrust_n, &device.propulsion_current_thrust_n)
        && upload_vector(host.has_propulsion, &device.has_propulsion)
        && upload_vector(host.mass_empty_kg, &device.mass_empty_kg)
        && upload_vector(host.mass_stores_kg, &device.mass_stores_kg)
        && upload_vector(host.mass_fuel_kg, &device.mass_fuel_kg)
        && upload_vector(host.mass_fuel_leak_rate_kgps, &device.mass_fuel_leak_rate_kgps)
        && upload_vector(host.has_mass, &device.has_mass)
        && upload_vector(host.total_mass_kg, &device.total_mass_kg)
        && upload_vector(host.has_mass_properties, &device.has_mass_properties)
        && upload_vector(host.has_ground_state, &device.has_ground_state)
        && upload_vector(host.has_instrument_state, &device.has_instrument_state)
        && upload_vector(host.has_egi, &device.has_egi);
}

bool download_soa(gpu::ExactWorldStepPrototypeSoA& host, const DeviceSoA& device) {
    return download_vector(host.time_step_s, device.time_step_s)
        && download_vector(host.world_time_s, device.world_time_s)
        && download_vector(host.x_m, device.x_m)
        && download_vector(host.y_m, device.y_m)
        && download_vector(host.z_m, device.z_m)
        && download_vector(host.heading_deg, device.heading_deg)
        && download_vector(host.pitch_deg, device.pitch_deg)
        && download_vector(host.roll_deg, device.roll_deg)
        && download_vector(host.vx_mps, device.vx_mps)
        && download_vector(host.vy_mps, device.vy_mps)
        && download_vector(host.vz_mps, device.vz_mps)
        && download_vector(host.p_rad_s, device.p_rad_s)
        && download_vector(host.q_rad_s, device.q_rad_s)
        && download_vector(host.r_rad_s, device.r_rad_s)
        && download_vector(host.g_load_normal, device.g_load_normal)
        && download_vector(host.g_load_axial, device.g_load_axial)
        && download_vector(host.wind_vx_mps, device.wind_vx_mps)
        && download_vector(host.wind_vy_mps, device.wind_vy_mps)
        && download_vector(host.terrain_elevation_m, device.terrain_elevation_m)
        && download_vector(host.target_heading_deg, device.target_heading_deg)
        && download_vector(host.target_speed_mps, device.target_speed_mps)
        && download_vector(host.target_altitude_m, device.target_altitude_m)
        && download_vector(host.heading_tau_s, device.heading_tau_s)
        && download_vector(host.speed_tau_s, device.speed_tau_s)
        && download_vector(host.altitude_tau_s, device.altitude_tau_s)
        && download_vector(host.has_command_lag, device.has_command_lag)
        && download_vector(host.lagged_heading_deg, device.lagged_heading_deg)
        && download_vector(host.lagged_speed_mps, device.lagged_speed_mps)
        && download_vector(host.lagged_altitude_m, device.lagged_altitude_m)
        && download_vector(host.lagged_active, device.lagged_active)
        && download_vector(host.output_has_lagged_command, device.output_has_lagged_command)
        && download_vector(host.max_speed_mps, device.max_speed_mps)
        && download_vector(host.min_speed_mps, device.min_speed_mps)
        && download_vector(host.max_accel_mps2, device.max_accel_mps2)
        && download_vector(host.max_climb_rate_mps, device.max_climb_rate_mps)
        && download_vector(host.reference_area_m2, device.reference_area_m2)
        && download_vector(host.wing_span_m, device.wing_span_m)
        && download_vector(host.chord_m, device.chord_m)
        && download_vector(host.current_drag_index, device.current_drag_index)
        && download_vector(host.gear_extension_state, device.gear_extension_state)
        && download_vector(host.aero_dynamic_pressure_pa, device.aero_dynamic_pressure_pa)
        && download_vector(host.aero_mach_number, device.aero_mach_number)
        && download_vector(host.aero_angle_of_attack_deg, device.aero_angle_of_attack_deg)
        && download_vector(host.aero_sideslip_angle_deg, device.aero_sideslip_angle_deg)
        && download_vector(host.aero_lift_coefficient, device.aero_lift_coefficient)
        && download_vector(host.aero_drag_coefficient, device.aero_drag_coefficient)
        && download_vector(host.force_fx_n, device.force_fx_n)
        && download_vector(host.force_fy_n, device.force_fy_n)
        && download_vector(host.force_fz_n, device.force_fz_n)
        && download_vector(host.force_torque_roll_nm, device.force_torque_roll_nm)
        && download_vector(host.force_torque_pitch_nm, device.force_torque_pitch_nm)
        && download_vector(host.force_torque_yaw_nm, device.force_torque_yaw_nm)
        && download_vector(host.control_stick_roll_filt, device.control_stick_roll_filt)
        && download_vector(host.control_stick_pitch_filt, device.control_stick_pitch_filt)
        && download_vector(host.control_stick_yaw_filt, device.control_stick_yaw_filt)
        && download_vector(host.control_stick_yaw_cmd, device.control_stick_yaw_cmd)
        && download_vector(host.control_profile_code, device.control_profile_code)
        && download_vector(host.has_angular_velocity, device.has_angular_velocity)
        && download_vector(host.has_force_accumulator, device.has_force_accumulator)
        && download_vector(host.has_aero_state, device.has_aero_state)
        && download_vector(host.has_control_law_state, device.has_control_law_state)
        && download_vector(host.fuel_internal_kg, device.fuel_internal_kg)
        && download_vector(host.fuel_external_kg, device.fuel_external_kg)
        && download_vector(host.fuel_flow_rate_kgps, device.fuel_flow_rate_kgps)
        && download_vector(host.fuel_ab_multiplier, device.fuel_ab_multiplier)
        && download_vector(host.fuel_afterburner_active, device.fuel_afterburner_active)
        && download_vector(host.has_fuel_system, device.has_fuel_system)
        && download_vector(host.propulsion_current_thrust_n, device.propulsion_current_thrust_n)
        && download_vector(host.has_propulsion, device.has_propulsion)
        && download_vector(host.mass_empty_kg, device.mass_empty_kg)
        && download_vector(host.mass_stores_kg, device.mass_stores_kg)
        && download_vector(host.mass_fuel_kg, device.mass_fuel_kg)
        && download_vector(host.mass_fuel_leak_rate_kgps, device.mass_fuel_leak_rate_kgps)
        && download_vector(host.has_mass, device.has_mass)
        && download_vector(host.total_mass_kg, device.total_mass_kg)
        && download_vector(host.has_mass_properties, device.has_mass_properties)
        && download_vector(host.has_ground_state, device.has_ground_state)
        && download_vector(host.has_instrument_state, device.has_instrument_state)
        && download_vector(host.has_egi, device.has_egi);
}

struct ArrayRefs {
    double* time_step_s;
    double* world_time_s;
    double* x_m;
    double* y_m;
    double* z_m;
    double* heading_deg;
    double* pitch_deg;
    double* roll_deg;
    double* vx_mps;
    double* vy_mps;
    double* vz_mps;
    double* p_rad_s;
    double* q_rad_s;
    double* r_rad_s;
    double* g_load_normal;
    double* g_load_axial;
    double* wind_vx_mps;
    double* wind_vy_mps;
    double* terrain_elevation_m;
    double* target_heading_deg;
    double* target_speed_mps;
    double* target_altitude_m;
    double* heading_tau_s;
    double* speed_tau_s;
    double* altitude_tau_s;
    std::uint8_t* has_command_lag;
    double* lagged_heading_deg;
    double* lagged_speed_mps;
    double* lagged_altitude_m;
    std::uint8_t* lagged_active;
    std::uint8_t* output_has_lagged_command;
    double* max_speed_mps;
    double* min_speed_mps;
    double* max_accel_mps2;
    double* max_climb_rate_mps;
    double* reference_area_m2;
    double* wing_span_m;
    double* chord_m;
    double* current_drag_index;
    double* gear_extension_state;
    double* aero_dynamic_pressure_pa;
    double* aero_mach_number;
    double* aero_angle_of_attack_deg;
    double* aero_sideslip_angle_deg;
    double* aero_lift_coefficient;
    double* aero_drag_coefficient;
    double* force_fx_n;
    double* force_fy_n;
    double* force_fz_n;
    double* force_torque_roll_nm;
    double* force_torque_pitch_nm;
    double* force_torque_yaw_nm;
    double* control_stick_roll_filt;
    double* control_stick_pitch_filt;
    double* control_stick_yaw_filt;
    double* control_stick_yaw_cmd;
    std::int32_t* control_profile_code;
    std::uint8_t* has_angular_velocity;
    std::uint8_t* has_force_accumulator;
    std::uint8_t* has_aero_state;
    std::uint8_t* has_control_law_state;
    double* fuel_internal_kg;
    double* fuel_external_kg;
    double* fuel_flow_rate_kgps;
    double* fuel_ab_multiplier;
    std::uint8_t* fuel_afterburner_active;
    std::uint8_t* has_fuel_system;
    double* propulsion_current_thrust_n;
    std::uint8_t* has_propulsion;
    double* mass_empty_kg;
    double* mass_stores_kg;
    double* mass_fuel_kg;
    double* mass_fuel_leak_rate_kgps;
    std::uint8_t* has_mass;
    double* total_mass_kg;
    std::uint8_t* has_mass_properties;
    std::uint8_t* has_ground_state;
    std::uint8_t* has_instrument_state;
    std::uint8_t* has_egi;
};

__device__ __forceinline__ double wrap_heading_deg(double heading_deg) {
    while (heading_deg < 0.0) {
        heading_deg += 360.0;
    }
    while (heading_deg >= 360.0) {
        heading_deg -= 360.0;
    }
    return heading_deg;
}

__device__ __forceinline__ double shortest_heading_delta_deg(double target_deg, double current_deg) {
    double delta = target_deg - current_deg;
    while (delta > 180.0) {
        delta -= 360.0;
    }
    while (delta < -180.0) {
        delta += 360.0;
    }
    return delta;
}

__device__ __forceinline__ double lerp_tau(double current, double target, double tau_s, double dt) {
    if (tau_s <= 1e-4 || dt <= 0.0) {
        return target;
    }
    const double alpha = 1.0 - exp(-dt / tau_s);
    return current + (target - current) * alpha;
}

__device__ __forceinline__ double control_lpf(double current, double target, double tau_s, double dt) {
    if (tau_s <= 0.0 || dt <= 0.0) {
        return target;
    }
    const double alpha = dt / (tau_s + dt);
    return current + alpha * (target - current);
}

__device__ __forceinline__ double clamp_symmetric(double value, double limit) {
    return fmin(fmax(value, -limit), limit);
}

__device__ __forceinline__ double canonicalize_scalar(double value) {
    if (!isfinite(value) || kCanonicalQuantum <= 0.0) {
        return value;
    }
    if (fabs(value) <= (kCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = nearbyint(value / kCanonicalQuantum) * kCanonicalQuantum;
    return fabs(rounded) <= (kCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

__device__ __forceinline__ double smoothstep01(double x) {
    x = fmin(fmax(x, 0.0), 1.0);
    return x * x * (3.0 - 2.0 * x);
}

__device__ __forceinline__ void canonicalize_step_outputs(ArrayRefs refs, int i) {
    refs.world_time_s[i] = canonicalize_scalar(refs.world_time_s[i]);
    refs.x_m[i] = canonicalize_scalar(refs.x_m[i]);
    refs.y_m[i] = canonicalize_scalar(refs.y_m[i]);
    refs.z_m[i] = canonicalize_scalar(refs.z_m[i]);
    refs.heading_deg[i] = canonicalize_scalar(wrap_heading_deg(refs.heading_deg[i]));
    refs.pitch_deg[i] = canonicalize_scalar(refs.pitch_deg[i]);
    refs.roll_deg[i] = canonicalize_scalar(refs.roll_deg[i]);
    refs.vx_mps[i] = canonicalize_scalar(refs.vx_mps[i]);
    refs.vy_mps[i] = canonicalize_scalar(refs.vy_mps[i]);
    refs.vz_mps[i] = canonicalize_scalar(refs.vz_mps[i]);
    refs.p_rad_s[i] = canonicalize_scalar(refs.p_rad_s[i]);
    refs.q_rad_s[i] = canonicalize_scalar(refs.q_rad_s[i]);
    refs.r_rad_s[i] = canonicalize_scalar(refs.r_rad_s[i]);
    refs.g_load_normal[i] = canonicalize_scalar(refs.g_load_normal[i]);
    refs.g_load_axial[i] = canonicalize_scalar(refs.g_load_axial[i]);
    refs.lagged_heading_deg[i] = canonicalize_scalar(wrap_heading_deg(refs.lagged_heading_deg[i]));
    refs.lagged_speed_mps[i] = canonicalize_scalar(refs.lagged_speed_mps[i]);
    refs.lagged_altitude_m[i] = canonicalize_scalar(refs.lagged_altitude_m[i]);
    refs.current_drag_index[i] = canonicalize_scalar(refs.current_drag_index[i]);
    refs.gear_extension_state[i] = canonicalize_scalar(refs.gear_extension_state[i]);
    refs.aero_dynamic_pressure_pa[i] = canonicalize_scalar(refs.aero_dynamic_pressure_pa[i]);
    refs.aero_mach_number[i] = canonicalize_scalar(refs.aero_mach_number[i]);
    refs.aero_angle_of_attack_deg[i] = canonicalize_scalar(refs.aero_angle_of_attack_deg[i]);
    refs.aero_sideslip_angle_deg[i] = canonicalize_scalar(refs.aero_sideslip_angle_deg[i]);
    refs.aero_lift_coefficient[i] = canonicalize_scalar(refs.aero_lift_coefficient[i]);
    refs.aero_drag_coefficient[i] = canonicalize_scalar(refs.aero_drag_coefficient[i]);
    refs.force_torque_roll_nm[i] = canonicalize_scalar(refs.force_torque_roll_nm[i]);
    refs.force_torque_pitch_nm[i] = canonicalize_scalar(refs.force_torque_pitch_nm[i]);
    refs.force_torque_yaw_nm[i] = canonicalize_scalar(refs.force_torque_yaw_nm[i]);
    refs.control_stick_roll_filt[i] = canonicalize_scalar(refs.control_stick_roll_filt[i]);
    refs.control_stick_pitch_filt[i] = canonicalize_scalar(refs.control_stick_pitch_filt[i]);
    refs.control_stick_yaw_filt[i] = canonicalize_scalar(refs.control_stick_yaw_filt[i]);
    refs.control_stick_yaw_cmd[i] = canonicalize_scalar(refs.control_stick_yaw_cmd[i]);
    refs.fuel_internal_kg[i] = canonicalize_scalar(refs.fuel_internal_kg[i]);
    refs.fuel_external_kg[i] = canonicalize_scalar(refs.fuel_external_kg[i]);
    refs.fuel_flow_rate_kgps[i] = canonicalize_scalar(refs.fuel_flow_rate_kgps[i]);
    refs.mass_fuel_kg[i] = canonicalize_scalar(refs.mass_fuel_kg[i]);
    refs.total_mass_kg[i] = canonicalize_scalar(refs.total_mass_kg[i]);
}

struct ApproximateBodyVelocity {
    double x_mps;
    double y_mps;
    double z_mps;
};

struct ApproximateAeroOutputs {
    double dynamic_pressure;
    double mach_number;
    double angle_of_attack;
    double sideslip_angle;
};

struct ApproximateAeroCoefficients {
    double lift_coefficient;
    double drag_coefficient;
};

struct ApproximateVector3 {
    double x;
    double y;
    double z;
};

struct ApproximateInertia {
    double ixx;
    double iyy;
    double izz;
};

__device__ __forceinline__ ApproximateVector3 normalize_world_vector(ApproximateVector3 value) {
    const double norm = sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const double inv = 1.0 / norm;
    return {value.x * inv, value.y * inv, value.z * inv};
}

__device__ __forceinline__ ApproximateVector3 cross_world(ApproximateVector3 a, ApproximateVector3 b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

__device__ __forceinline__ ApproximateVector3 body_right_world(double heading_deg, double pitch_deg, double roll_deg) {
    const double psi = (90.0 - heading_deg) * (kPi / 180.0);
    const double theta = pitch_deg * (kPi / 180.0);
    const double phi = roll_deg * (kPi / 180.0);

    const double c_psi = cos(psi);
    const double s_psi = sin(psi);
    const double c_theta = cos(theta);
    const double s_theta = sin(theta);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);

    return {
        -s_psi * c_phi + c_psi * s_theta * s_phi,
        c_psi * c_phi + s_psi * s_theta * s_phi,
        c_theta * s_phi,
    };
}

__device__ __forceinline__ ApproximateBodyVelocity world_to_body_velocity(
    double vx_world_mps,
    double vy_world_mps,
    double vz_world_mps,
    double heading_deg,
    double pitch_deg,
    double roll_deg
) {
    const double psi = (90.0 - heading_deg) * (kPi / 180.0);
    const double theta = pitch_deg * (kPi / 180.0);
    const double phi = roll_deg * (kPi / 180.0);

    const double c_psi = cos(psi);
    const double s_psi = sin(psi);
    const double c_theta = cos(theta);
    const double s_theta = sin(theta);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);

    const double x1 = vx_world_mps * c_psi + vy_world_mps * s_psi;
    const double y1 = -vx_world_mps * s_psi + vy_world_mps * c_psi;
    const double z1 = vz_world_mps;

    const double x2 = x1 * c_theta + z1 * s_theta;
    const double y2 = y1;
    const double z2 = -x1 * s_theta + z1 * c_theta;

    return {
        x2,
        y2 * c_phi + z2 * s_phi,
        -y2 * s_phi + z2 * c_phi,
    };
}

__device__ __forceinline__ ApproximateAeroOutputs approximate_aero_outputs(ArrayRefs refs, int i) {
    const double vx_air = refs.vx_mps[i] - refs.wind_vx_mps[i];
    const double vy_air = refs.vy_mps[i] - refs.wind_vy_mps[i];
    const double vz_air = refs.vz_mps[i];

    const double v_sq = vx_air * vx_air + vy_air * vy_air + vz_air * vz_air;
    const double v_total = sqrt(v_sq);
    const double alt_km = fmax(0.0, refs.z_m[i]) / 1000.0;
    const double rho = 1.225 * exp(-alt_km / 7.2);
    double speed_of_sound = 340.29 - (4.0 * alt_km);
    if (speed_of_sound < 295.0) {
        speed_of_sound = 295.0;
    }

    const auto v_body = world_to_body_velocity(
        vx_air,
        vy_air,
        vz_air,
        refs.heading_deg[i],
        refs.pitch_deg[i],
        refs.roll_deg[i]
    );
    const double alpha_raw = atan2(-v_body.z_mps, v_body.x_mps) * (180.0 / kPi);
    double beta_arg = v_body.y_mps / fmax(v_total, 1.0e-6);
    beta_arg = fmin(fmax(beta_arg, -1.0), 1.0);
    const double beta_raw = asin(beta_arg) * (180.0 / kPi);

    double blend = 1.0;
    if (v_total <= 2.0) {
        blend = 0.0;
    } else if (v_total < 8.0) {
        blend = (v_total - 2.0) / 6.0;
    }
    blend = fmin(fmax(blend, 0.0), 1.0);
    return {
        0.5 * rho * v_sq,
        speed_of_sound > 1.0 ? (v_total / speed_of_sound) : 0.0,
        fmin(fmax((1.0 - blend) * refs.aero_angle_of_attack_deg[i] + blend * alpha_raw, -90.0), 90.0),
        fmin(fmax((1.0 - blend) * refs.aero_sideslip_angle_deg[i] + blend * beta_raw, -90.0), 90.0),
    };
}

__device__ __forceinline__ ApproximateAeroCoefficients approximate_aero_coefficients(
    double alpha_deg,
    double current_drag_index,
    double gear_extension_state
) {
    double cl = 0.1 * alpha_deg;
    const double alpha_abs = fabs(alpha_deg);
    const double alpha_sign = alpha_deg >= 0.0 ? 1.0 : -1.0;
    constexpr double alpha_stall_deg = 15.0;
    constexpr double alpha_peak_deg = 23.0;
    constexpr double alpha_deep_deg = 41.0;
    constexpr double cl_peak_mag = 1.25;
    constexpr double cl_deep_mag = 0.22;

    if (alpha_abs > alpha_stall_deg) {
        if (alpha_abs <= alpha_peak_deg) {
            const double t = smoothstep01((alpha_abs - alpha_stall_deg) / fmax(1.0e-6, alpha_peak_deg - alpha_stall_deg));
            cl = (1.0 - t) * cl + t * (alpha_sign * cl_peak_mag);
        } else if (alpha_abs <= alpha_deep_deg) {
            const double t = smoothstep01((alpha_abs - alpha_peak_deg) / fmax(1.0e-6, alpha_deep_deg - alpha_peak_deg));
            cl = (1.0 - t) * (alpha_sign * cl_peak_mag) + t * (alpha_sign * cl_deep_mag);
        } else {
            cl = alpha_sign * cl_deep_mag;
        }
    }

    double cd0 = 0.02;
    cd0 += current_drag_index * 0.001;
    cd0 += fmin(fmax(gear_extension_state, 0.0), 1.0) * 0.04;
    double stall_drag = 0.0;
    if (alpha_abs > alpha_stall_deg) {
        const double s1 = smoothstep01((alpha_abs - alpha_stall_deg) / fmax(1.0e-6, alpha_peak_deg - alpha_stall_deg));
        const double s2 = smoothstep01((alpha_abs - alpha_peak_deg) / fmax(1.0e-6, alpha_deep_deg - alpha_peak_deg));
        stall_drag = 0.25 * s1 + 0.55 * s2;
    }

    return {
        cl,
        cd0 + 0.1 * cl * cl + stall_drag,
    };
}

__device__ __forceinline__ ApproximateInertia estimate_inertia(
    double total_mass_kg,
    double wing_span_m,
    double chord_m
) {
    const double mass = fmax(1000.0, total_mass_kg);
    const double span = fmax(4.0, wing_span_m);
    const double chord_extent = fmax(2.0, chord_m * 2.0);
    const double depth_extent = fmax(1.0, chord_m * 0.35);
    return {
        fmax(5000.0, mass * ((depth_extent * depth_extent) + (span * span)) / 12.0),
        fmax(5000.0, mass * ((depth_extent * depth_extent) + (chord_extent * chord_extent)) / 12.0),
        fmax(5000.0, mass * ((span * span) + (chord_extent * chord_extent)) / 12.0),
    };
}

__device__ __forceinline__ void step_once(ArrayRefs refs, int i) {
    const double dt = fmax(0.0, refs.time_step_s[i]);
    if (dt <= 0.0) {
        return;
    }

    const double prev_vx = refs.vx_mps[i];
    const double prev_vy = refs.vy_mps[i];
    const double prev_vz = refs.vz_mps[i];
    const double prev_heading = refs.heading_deg[i];
    const double prev_pitch = refs.pitch_deg[i];
    const double prev_roll = refs.roll_deg[i];

    double lagged_heading = refs.lagged_heading_deg[i];
    double lagged_speed = refs.lagged_speed_mps[i];
    double lagged_altitude = refs.lagged_altitude_m[i];
    if (refs.has_command_lag[i] != 0u) {
        const double heading_delta = shortest_heading_delta_deg(refs.target_heading_deg[i], lagged_heading);
        lagged_heading = wrap_heading_deg(
            lagged_heading + lerp_tau(0.0, heading_delta, fmax(1e-4, refs.heading_tau_s[i]), dt)
        );
        lagged_speed = lerp_tau(lagged_speed, refs.target_speed_mps[i], fmax(1e-4, refs.speed_tau_s[i]), dt);
        lagged_altitude = lerp_tau(
            lagged_altitude,
            refs.target_altitude_m[i],
            fmax(1e-4, refs.altitude_tau_s[i]),
            dt
        );
    } else {
        lagged_heading = refs.target_heading_deg[i];
        lagged_speed = refs.target_speed_mps[i];
        lagged_altitude = refs.target_altitude_m[i];
    }
    refs.lagged_heading_deg[i] = wrap_heading_deg(lagged_heading);
    refs.lagged_speed_mps[i] = fmax(0.0, lagged_speed);
    refs.lagged_altitude_m[i] = lagged_altitude;
    refs.lagged_active[i] = 1u;
    refs.output_has_lagged_command[i] = 1u;

    const double guidance_heading_deg = refs.lagged_heading_deg[i];
    const double guidance_altitude_m = refs.lagged_altitude_m[i];

    const double min_speed = fmax(0.0, refs.min_speed_mps[i]);
    const double max_speed = fmax(min_speed, refs.max_speed_mps[i]);
    const double desired_speed = fmin(fmax(refs.lagged_speed_mps[i], min_speed), max_speed > 0.0 ? max_speed : refs.lagged_speed_mps[i]);
    const double heading_rad = refs.lagged_heading_deg[i] * (kPi / 180.0);
    const double desired_vx = sin(heading_rad) * desired_speed;
    const double desired_vy = cos(heading_rad) * desired_speed;
    const double max_climb_rate = fmax(1.0, refs.max_climb_rate_mps[i]);
    const double desired_vz = fmin(fmax((refs.lagged_altitude_m[i] - refs.z_m[i]) / 10.0, -max_climb_rate), max_climb_rate);

    const double dv_limit_xy = fmax(0.1, refs.max_accel_mps2[i] * dt);
    const double dv_limit_z = fmax(0.1, max_climb_rate * dt);
    refs.vx_mps[i] += clamp_symmetric(desired_vx - refs.vx_mps[i], dv_limit_xy);
    refs.vy_mps[i] += clamp_symmetric(desired_vy - refs.vy_mps[i], dv_limit_xy);
    refs.vz_mps[i] += clamp_symmetric(desired_vz - refs.vz_mps[i], dv_limit_z);

    refs.x_m[i] += (refs.vx_mps[i] + refs.wind_vx_mps[i]) * dt;
    refs.y_m[i] += (refs.vy_mps[i] + refs.wind_vy_mps[i]) * dt;
    refs.z_m[i] += refs.vz_mps[i] * dt;
    if (refs.z_m[i] < refs.terrain_elevation_m[i]) {
        refs.z_m[i] = refs.terrain_elevation_m[i];
        if (refs.vz_mps[i] < 0.0) {
            refs.vz_mps[i] = 0.0;
        }
    }

    const bool on_ground = refs.z_m[i] <= refs.terrain_elevation_m[i] + 0.25;
    refs.force_torque_roll_nm[i] = 0.0;
    refs.force_torque_pitch_nm[i] = 0.0;
    refs.force_torque_yaw_nm[i] = 0.0;
    const auto aero = approximate_aero_outputs(refs, i);
    const auto aero_coeff = approximate_aero_coefficients(
        aero.angle_of_attack,
        refs.current_drag_index[i],
        refs.gear_extension_state[i]
    );
    refs.aero_dynamic_pressure_pa[i] = aero.dynamic_pressure;
    refs.aero_mach_number[i] = aero.mach_number;
    refs.aero_angle_of_attack_deg[i] = aero.angle_of_attack;
    refs.aero_sideslip_angle_deg[i] = aero.sideslip_angle;
    refs.aero_lift_coefficient[i] = aero_coeff.lift_coefficient;
    refs.aero_drag_coefficient[i] = aero_coeff.drag_coefficient;

    const double total_mass = fmax(1.0, refs.total_mass_kg[i]);
    refs.force_fx_n[i] = 0.0;
    refs.force_fy_n[i] = 0.0;
    refs.force_fz_n[i] = 0.0;

    const double current_heading_deg = refs.heading_deg[i];
    const double current_track_deg = wrap_heading_deg(atan2(refs.vx_mps[i], refs.vy_mps[i]) * (180.0 / kPi));
    double lateral_reference_deg = current_heading_deg;
    double bank_limit_deg = 60.0;
    double heading_to_bank_gain = 2.0;
    double bank_to_stick_gain = 0.05;
    double altitude_to_pitch_gain = 0.1;
    double pitch_min_deg = -15.0;
    double pitch_max_deg = 20.0;
    double pitch_to_stick_gain = 0.1;

    if (refs.control_profile_code[i] == 3) {
        lateral_reference_deg = current_track_deg;
        bank_limit_deg = 45.0;
    } else if (refs.control_profile_code[i] == 4) {
        bank_limit_deg = on_ground ? 8.0 : 22.0;
        heading_to_bank_gain = 1.0;
        bank_to_stick_gain = 0.04;
        altitude_to_pitch_gain = 0.05;
        pitch_min_deg = on_ground ? -2.0 : -8.0;
        pitch_max_deg = on_ground ? 5.0 : 12.0;
        pitch_to_stick_gain = 0.08;
    } else if (refs.control_profile_code[i] == 1) {
        bank_limit_deg = 30.0;
        heading_to_bank_gain = 1.4;
    }

    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double stick_yaw = 0.0;
    if (refs.control_profile_code[i] != 0 || refs.lagged_active[i] != 0u) {
        const double heading_err = shortest_heading_delta_deg(guidance_heading_deg, lateral_reference_deg);
        const double target_bank = fmin(
            fmax(heading_err * heading_to_bank_gain, -bank_limit_deg),
            bank_limit_deg
        );
        const double bank_err = target_bank - refs.roll_deg[i];
        stick_roll = fmin(fmax(bank_err * bank_to_stick_gain, -1.0), 1.0);

        const double alt_err = guidance_altitude_m - refs.z_m[i];
        const double target_pitch = fmin(
            fmax(alt_err * altitude_to_pitch_gain, pitch_min_deg),
            pitch_max_deg
        );
        const double pitch_err = target_pitch - refs.pitch_deg[i];
        stick_pitch = fmin(fmax(pitch_err * pitch_to_stick_gain, -1.0), 1.0);
    }

    constexpr double kPMaxRadS = 1.2;
    constexpr double kQMaxRadS = 0.8;
    constexpr double kRMaxRadS = 0.8;
    constexpr double kRollGain = 40.0;
    constexpr double kPitchGain = 60.0;
    constexpr double kYawGain = 20.0;
    constexpr double kMaxRateCrossRadS = 50.0;
    constexpr double kMaxTorqueNm = 5.0e6;
    constexpr double kMaxAngAccelRadS2 = 1.0e4;
    constexpr double kMaxRateRadS = 6.0;
    constexpr double kMinAbsCosTheta = 0.08715574274765817;
    constexpr double kPitchLimitDeg = 89.0;

    constexpr double kStickTauS = 0.15;
    refs.control_stick_roll_filt[i] = control_lpf(refs.control_stick_roll_filt[i], stick_roll, kStickTauS, dt);
    refs.control_stick_pitch_filt[i] = control_lpf(refs.control_stick_pitch_filt[i], stick_pitch, kStickTauS, dt);
    refs.control_stick_yaw_filt[i] = control_lpf(refs.control_stick_yaw_filt[i], stick_yaw, kStickTauS, dt);
    refs.has_control_law_state[i] = 1u;

    const double stick_roll_f = fmin(fmax(refs.control_stick_roll_filt[i], -1.0), 1.0);
    const double stick_pitch_f = fmin(fmax(refs.control_stick_pitch_filt[i], -1.0), 1.0);
    const double stick_yaw_f = fmin(fmax(refs.control_stick_yaw_filt[i], -1.0), 1.0);

    double stick_yaw_cmd = stick_yaw_f;
    if (on_ground) {
        constexpr double kYawLimitStartMps = 5.0;
        constexpr double kYawLimitEndMps = 80.0;
        constexpr double kYawMaxLowSpeed = 1.0;
        constexpr double kYawMaxHighSpeed = 0.35;
        const double v_h = hypot(refs.vx_mps[i], refs.vy_mps[i]);
        double t = 0.0;
        if (v_h > kYawLimitStartMps) {
            t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
            t = fmin(fmax(t, 0.0), 1.0);
        }
        const double yaw_max = kYawMaxLowSpeed + t * (kYawMaxHighSpeed - kYawMaxLowSpeed);
        stick_yaw_cmd = fmin(fmax(stick_yaw_cmd, -yaw_max), yaw_max);
    }
    refs.control_stick_yaw_cmd[i] = stick_yaw_cmd;

    double p_cmd = stick_roll_f * kPMaxRadS;
    double q_cmd = stick_pitch_f * kQMaxRadS;
    double r_cmd = stick_yaw_cmd * kRMaxRadS;
    if (!on_ground) {
        const double beta_rad = aero.sideslip_angle * (kPi / 180.0);
        r_cmd += (-1.10 * beta_rad) + (-0.55 * refs.r_rad_s[i]);
        r_cmd = fmin(fmax(r_cmd, -kRMaxRadS), kRMaxRadS);
    }

    if (on_ground) {
        if (refs.pitch_deg[i] > 8.0 && q_cmd > 0.0) {
            const double t = (refs.pitch_deg[i] - 8.0) / 4.0;
            q_cmd *= 1.0 - fmin(fmax(t, 0.0), 1.0);
        }
        if (refs.pitch_deg[i] > 12.0) {
            q_cmd = fmin(q_cmd, -0.2);
        }
    } else {
        if (refs.pitch_deg[i] > 60.0 && q_cmd > 0.0) {
            const double t = (refs.pitch_deg[i] - 60.0) / 20.0;
            q_cmd *= 1.0 - fmin(fmax(t, 0.0), 1.0);
        }
        if (refs.pitch_deg[i] > 80.0) {
            q_cmd = fmin(q_cmd, -0.2);
        }
    }

    const double alpha_abs = fabs(aero.angle_of_attack);
    if (alpha_abs > 10.0) {
        const double t = (alpha_abs - 10.0) / 8.0;
        q_cmd *= 1.0 - fmin(fmax(t, 0.0), 1.0);
    }
    if (alpha_abs > 18.0) {
        q_cmd = fmin(q_cmd, -0.15);
    }

    const double q_bar_eff = fmin(aero.dynamic_pressure, 9000.0);
    const double control_roll_torque = (p_cmd - refs.p_rad_s[i]) * (kRollGain * q_bar_eff);
    const double control_pitch_torque = (q_cmd - refs.q_rad_s[i]) * (kPitchGain * q_bar_eff);
    const double control_yaw_torque = (r_cmd - refs.r_rad_s[i]) * (kYawGain * q_bar_eff);

    const double ref_area = fmax(1.0, refs.reference_area_m2[i]);
    const double wing_span = fmax(1.0, refs.wing_span_m[i]);
    const double chord = fmax(0.1, refs.chord_m[i]);
    const double speed_total = fmax(
        10.0,
        sqrt(
            refs.vx_mps[i] * refs.vx_mps[i] +
            refs.vy_mps[i] * refs.vy_mps[i] +
            refs.vz_mps[i] * refs.vz_mps[i]
        )
    );
    const double p_hat = refs.p_rad_s[i] * wing_span / (2.0 * speed_total);
    const double q_hat = refs.q_rad_s[i] * chord / (2.0 * speed_total);
    const double r_hat = refs.r_rad_s[i] * wing_span / (2.0 * speed_total);
    const double stall_rel = smoothstep01((alpha_abs - 15.0) / 18.0);
    const double damp_scale = fmin(fmax(1.0 - 0.7 * stall_rel, 0.25), 1.0);
    const double cm = (-0.8 * (aero.angle_of_attack * (kPi / 180.0))) + (-12.0 * damp_scale * q_hat);
    const double cl_mom =
        (-0.1 * (aero.sideslip_angle * (kPi / 180.0))) +
        (-0.45 * damp_scale * p_hat) +
        (0.1 * r_hat);
    const double cn_mom =
        (0.15 * (aero.sideslip_angle * (kPi / 180.0))) +
        (-0.25 * damp_scale * r_hat);
    const double aero_pitch_torque = aero.dynamic_pressure * ref_area * chord * cm;
    const double aero_roll_torque = aero.dynamic_pressure * ref_area * wing_span * cl_mom;
    const double aero_yaw_torque = aero.dynamic_pressure * ref_area * wing_span * cn_mom;

    refs.force_torque_roll_nm[i] = control_roll_torque + aero_roll_torque;
    refs.force_torque_pitch_nm[i] = control_pitch_torque + aero_pitch_torque;
    refs.force_torque_yaw_nm[i] = control_yaw_torque + aero_yaw_torque;

    const auto inertia = estimate_inertia(refs.total_mass_kg[i], wing_span, chord);
    const double p = fmin(fmax(refs.p_rad_s[i], -kMaxRateCrossRadS), kMaxRateCrossRadS);
    const double q = fmin(fmax(refs.q_rad_s[i], -kMaxRateCrossRadS), kMaxRateCrossRadS);
    const double r = fmin(fmax(refs.r_rad_s[i], -kMaxRateCrossRadS), kMaxRateCrossRadS);
    const double roll_torque = fmin(fmax(refs.force_torque_roll_nm[i], -kMaxTorqueNm), kMaxTorqueNm);
    const double pitch_torque = fmin(fmax(refs.force_torque_pitch_nm[i], -kMaxTorqueNm), kMaxTorqueNm);
    const double yaw_torque = fmin(fmax(refs.force_torque_yaw_nm[i], -kMaxTorqueNm), kMaxTorqueNm);
    const double p_dot = (roll_torque - (inertia.izz - inertia.iyy) * q * r) / inertia.ixx;
    const double q_dot = (pitch_torque - (inertia.ixx - inertia.izz) * p * r) / inertia.iyy;
    const double r_dot = (yaw_torque - (inertia.iyy - inertia.ixx) * p * q) / inertia.izz;
    refs.p_rad_s[i] = fmin(fmax(p + fmin(fmax(p_dot, -kMaxAngAccelRadS2), kMaxAngAccelRadS2) * dt, -kMaxRateRadS), kMaxRateRadS);
    refs.q_rad_s[i] = fmin(fmax(q + fmin(fmax(q_dot, -kMaxAngAccelRadS2), kMaxAngAccelRadS2) * dt, -kMaxRateRadS), kMaxRateRadS);
    refs.r_rad_s[i] = fmin(fmax(r + fmin(fmax(r_dot, -kMaxAngAccelRadS2), kMaxAngAccelRadS2) * dt, -kMaxRateRadS), kMaxRateRadS);

    const double phi = refs.roll_deg[i] * (kPi / 180.0);
    const double theta = refs.pitch_deg[i] * (kPi / 180.0);
    const double c_phi = cos(phi);
    const double s_phi = sin(phi);
    double c_theta = cos(theta);
    const double s_theta = sin(theta);
    if (fabs(c_theta) < kMinAbsCosTheta) {
        c_theta = copysign(kMinAbsCosTheta, c_theta);
    }
    const double t_theta = s_theta / c_theta;
    const double sec_theta = 1.0 / c_theta;
    const double d_phi = refs.p_rad_s[i] + (refs.q_rad_s[i] * s_phi + refs.r_rad_s[i] * c_phi) * t_theta;
    const double d_theta = refs.q_rad_s[i] * c_phi - refs.r_rad_s[i] * s_phi;
    const double d_psi = (refs.q_rad_s[i] * s_phi + refs.r_rad_s[i] * c_phi) * sec_theta;
    refs.roll_deg[i] += d_phi * dt * (180.0 / kPi);
    refs.pitch_deg[i] += d_theta * dt * (180.0 / kPi);
    refs.heading_deg[i] -= d_psi * dt * (180.0 / kPi);
    refs.roll_deg[i] = fmod(refs.roll_deg[i] + 180.0, 360.0);
    if (refs.roll_deg[i] < 0.0) {
        refs.roll_deg[i] += 360.0;
    }
    refs.roll_deg[i] -= 180.0;
    refs.pitch_deg[i] = fmin(fmax(refs.pitch_deg[i], -kPitchLimitDeg), kPitchLimitDeg);
    refs.heading_deg[i] = wrap_heading_deg(refs.heading_deg[i]);

    const auto sensed_force_body = world_to_body_velocity(
        (refs.vx_mps[i] - prev_vx) / dt,
        (refs.vy_mps[i] - prev_vy) / dt,
        ((refs.vz_mps[i] - prev_vz) / dt) + kGravityMps2,
        refs.heading_deg[i],
        refs.pitch_deg[i],
        refs.roll_deg[i]
    );
    const double inv_weight = 1.0 / kGravityMps2;
    refs.g_load_axial[i] = sensed_force_body.x_mps * inv_weight;
    refs.g_load_normal[i] = sensed_force_body.z_mps * inv_weight;
    refs.world_time_s[i] += dt;

    const double speed_metric = fabs(refs.vx_mps[i]) + fabs(refs.vy_mps[i]) + fabs(refs.vz_mps[i]);
    const double speed_ratio = max_speed > 1e-6 ? fmin(fmax(desired_speed / max_speed, 0.0), 1.0) : 0.0;
    double burn_rate = refs.fuel_flow_rate_kgps[i];
    if (burn_rate <= 0.0) {
        burn_rate = 0.05 + 0.0006 * speed_metric;
    } else {
        burn_rate *= 0.35 + 0.65 * speed_ratio;
    }
    if (refs.fuel_afterburner_active[i] != 0u) {
        burn_rate *= fmax(1.0, refs.fuel_ab_multiplier[i]);
    }
    const double leak_rate = fmax(0.0, refs.mass_fuel_leak_rate_kgps[i]);
    double remaining_burn = (burn_rate + leak_rate) * dt;
    const double external_burn = fmin(refs.fuel_external_kg[i], remaining_burn);
    refs.fuel_external_kg[i] -= external_burn;
    remaining_burn -= external_burn;
    const double internal_burn = fmin(refs.fuel_internal_kg[i], remaining_burn);
    refs.fuel_internal_kg[i] -= internal_burn;
    refs.mass_fuel_kg[i] = fmax(0.0, refs.fuel_internal_kg[i] + refs.fuel_external_kg[i]);
    refs.total_mass_kg[i] = refs.mass_empty_kg[i] + refs.mass_stores_kg[i] + refs.mass_fuel_kg[i];
    refs.fuel_flow_rate_kgps[i] = burn_rate;
    canonicalize_step_outputs(refs, i);
}

__global__ void step_exact_world_step_prototype_kernel(ArrayRefs refs, int count, int steps) {
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= count) {
        return;
    }
    for (int step_index = 0; step_index < steps; ++step_index) {
        step_once(refs, idx);
    }
}

ArrayRefs make_refs(DeviceSoA& device) {
    return ArrayRefs{
        device.time_step_s,
        device.world_time_s,
        device.x_m,
        device.y_m,
        device.z_m,
        device.heading_deg,
        device.pitch_deg,
        device.roll_deg,
        device.vx_mps,
        device.vy_mps,
        device.vz_mps,
        device.p_rad_s,
        device.q_rad_s,
        device.r_rad_s,
        device.g_load_normal,
        device.g_load_axial,
        device.wind_vx_mps,
        device.wind_vy_mps,
        device.terrain_elevation_m,
        device.target_heading_deg,
        device.target_speed_mps,
        device.target_altitude_m,
        device.heading_tau_s,
        device.speed_tau_s,
        device.altitude_tau_s,
        device.has_command_lag,
        device.lagged_heading_deg,
        device.lagged_speed_mps,
        device.lagged_altitude_m,
        device.lagged_active,
        device.output_has_lagged_command,
        device.max_speed_mps,
        device.min_speed_mps,
        device.max_accel_mps2,
        device.max_climb_rate_mps,
        device.reference_area_m2,
        device.wing_span_m,
        device.chord_m,
        device.current_drag_index,
        device.gear_extension_state,
        device.aero_dynamic_pressure_pa,
        device.aero_mach_number,
        device.aero_angle_of_attack_deg,
        device.aero_sideslip_angle_deg,
        device.aero_lift_coefficient,
        device.aero_drag_coefficient,
        device.force_fx_n,
        device.force_fy_n,
        device.force_fz_n,
        device.force_torque_roll_nm,
        device.force_torque_pitch_nm,
        device.force_torque_yaw_nm,
        device.control_stick_roll_filt,
        device.control_stick_pitch_filt,
        device.control_stick_yaw_filt,
        device.control_stick_yaw_cmd,
        device.control_profile_code,
        device.has_angular_velocity,
        device.has_force_accumulator,
        device.has_aero_state,
        device.has_control_law_state,
        device.fuel_internal_kg,
        device.fuel_external_kg,
        device.fuel_flow_rate_kgps,
        device.fuel_ab_multiplier,
        device.fuel_afterburner_active,
        device.has_fuel_system,
        device.propulsion_current_thrust_n,
        device.has_propulsion,
        device.mass_empty_kg,
        device.mass_stores_kg,
        device.mass_fuel_kg,
        device.mass_fuel_leak_rate_kgps,
        device.has_mass,
        device.total_mass_kg,
        device.has_mass_properties,
        device.has_ground_state,
        device.has_instrument_state,
        device.has_egi,
    };
}

}  // namespace

namespace gpu::detail {

bool step_exact_world_step_states_v1_prototype_cuda_inplace(
    ExactWorldStepPrototypeSoA& soa,
    int steps,
    ExactWorldStepPrototypeStats* stats
) {
    if (stats == nullptr) {
        return false;
    }
    *stats = ExactWorldStepPrototypeStats{};
    stats->used_cuda = true;
    if (soa.size == 0 || steps <= 0) {
        return true;
    }

    DeviceSoA device{};
    const auto h2d_t0 = std::chrono::steady_clock::now();
    if (!upload_soa(soa, device)) {
        release(device);
        return false;
    }
    const auto h2d_t1 = std::chrono::steady_clock::now();
    stats->host_to_device_ms = std::chrono::duration<double, std::milli>(h2d_t1 - h2d_t0).count();

    cudaEvent_t start_event = nullptr;
    cudaEvent_t stop_event = nullptr;
    cudaEventCreate(&start_event);
    cudaEventCreate(&stop_event);
    cudaEventRecord(start_event);
    const int threads = 256;
    const int blocks = static_cast<int>((device.count + static_cast<std::size_t>(threads) - 1u) / static_cast<std::size_t>(threads));
    step_exact_world_step_prototype_kernel<<<blocks, threads>>>(make_refs(device), static_cast<int>(device.count), steps);
    cudaEventRecord(stop_event);
    if (cudaDeviceSynchronize() != cudaSuccess) {
        cudaEventDestroy(start_event);
        cudaEventDestroy(stop_event);
        release(device);
        return false;
    }
    float kernel_ms = 0.0f;
    cudaEventElapsedTime(&kernel_ms, start_event, stop_event);
    cudaEventDestroy(start_event);
    cudaEventDestroy(stop_event);
    stats->kernel_ms = static_cast<double>(kernel_ms);

    const auto d2h_t0 = std::chrono::steady_clock::now();
    const bool ok = download_soa(soa, device);
    const auto d2h_t1 = std::chrono::steady_clock::now();
    stats->device_to_host_ms = std::chrono::duration<double, std::milli>(d2h_t1 - d2h_t0).count();
    stats->total_ms = stats->host_to_device_ms + stats->kernel_ms + stats->device_to_host_ms;
    release(device);
    return ok;
}

}  // namespace gpu::detail
