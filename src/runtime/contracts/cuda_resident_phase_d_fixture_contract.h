#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace runtime::cuda_resident {

// RB7 owns only the learner-facing projection of the RB6 fixed-air fixture.
// These values are deliberately fixture constants; they are not a claim about
// every maintained aircraft, mission, environment, or reward configuration.
inline constexpr std::string_view kCudaResidentPhaseDFixtureId =
    "cuda_resident.phase_d.projection.v1";
inline constexpr std::string_view kCudaResidentPhaseDSnapshotSchemaV3 =
    "cuda_resident.fixed_air_snapshot.v3";
inline constexpr std::string_view kCudaResidentPhaseDSnapshotProvenance =
    "cuda_resident.rb7.explicit_phase_d_projection";
inline constexpr std::string_view kCudaResidentPhaseDDeviceViewSchemaV1 =
    "cuda_resident.device_observation_view.v1";
inline constexpr std::string_view kCudaResidentPhaseDDeviceViewProvenance =
    "cuda_resident.rb7.explicit_d2d_ownership_copy";

inline constexpr double kPhaseDHealth = 100.0;
inline constexpr double kPhaseDTargetAltitudeM = 1500.0;
inline constexpr double kPhaseDSurvivalReward = 0.01;
inline constexpr double kPhaseDSpeedRewardWeight = 0.0;
inline constexpr double kPhaseDFuelFlowTsfcNhPerN = 2.0e-5;
inline constexpr double kPhaseDObservationFloatClip = 1.0e6;

inline constexpr std::size_t kPhaseDInstrumentValueCount = 23;
inline constexpr std::size_t kPhaseDObservationValueCount = 15;
inline constexpr std::size_t kPhaseDRewardTermCount = 2;

inline constexpr std::array<std::string_view, kPhaseDInstrumentValueCount>
    kPhaseDInstrumentFieldNames = {
        "alt_baro_m",     "alt_radar_m",  "ias_mps",          "mach",
        "vvi_mps",        "pitch_deg",    "roll_deg",         "heading_deg",
        "aoa_deg",        "beta_deg",     "g_load_normal",    "g_load_axial",
        "p_deg_s",        "q_deg_s",      "r_deg_s",          "engine_rpm_pct",
        "fuel_flow_kg_h", "throttle_pos", "fuel_internal_kg", "fuel_external_kg",
        "gear_pos",       "flaps_pos",    "speedbrake_pos",
};

inline constexpr std::array<std::string_view, kPhaseDObservationValueCount>
    kPhaseDObservationFieldNames = {
        "sim_time", "x",    "y",     "z",      "vx",         "vy",       "vz",           "heading",
        "pitch",    "roll", "speed", "health", "gear_state", "throttle", "total_reward",
};

inline constexpr std::array<std::string_view, kPhaseDRewardTermCount> kPhaseDRewardTermNames = {
    "survival", "speed"};
inline constexpr std::array<std::string_view, kPhaseDRewardTermCount> kPhaseDRewardTermOwners = {
    "simulation", "simulation"};

inline constexpr double phase_d_speed_reward(double speed_mps) noexcept {
    return speed_mps * kPhaseDSpeedRewardWeight;
}

} // namespace runtime::cuda_resident
