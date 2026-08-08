#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace runtime::cuda_resident {

// This contract owns only the learner-facing projection of the fixed-air fixture.
// These values are deliberately fixture constants; they are not a claim about
// every maintained aircraft, mission, environment, or reward configuration.
inline constexpr std::string_view kCudaResidentObservationProjectionFixtureId =
    // internal-code: compatibility -- serialized fixture schema v1
    "cuda_resident.phase_d.projection.v1";
inline constexpr std::string_view kCudaResidentObservationProjectionSnapshotSchemaV3 =
    "cuda_resident.fixed_air_snapshot.v3";
inline constexpr std::string_view kCudaResidentObservationProjectionSnapshotProvenance =
    // internal-code: compatibility -- serialized snapshot provenance v3
    "cuda_resident.rb7.explicit_phase_d_projection";
inline constexpr std::string_view kCudaResidentObservationProjectionDeviceViewSchemaV1 =
    "cuda_resident.device_observation_view.v1";
inline constexpr std::string_view kCudaResidentObservationProjectionDeviceViewProvenance =
    // internal-code: compatibility -- serialized device-view provenance v1
    "cuda_resident.rb7.explicit_d2d_ownership_copy";

inline constexpr double kObservationProjectionHealth = 100.0;
inline constexpr double kObservationProjectionTargetAltitudeM = 1500.0;
inline constexpr double kObservationProjectionSurvivalReward = 0.01;
inline constexpr double kObservationProjectionSpeedRewardWeight = 0.0;
inline constexpr double kObservationProjectionFuelFlowTsfcNhPerN = 2.0e-5;
inline constexpr double kObservationProjectionObservationFloatClip = 1.0e6;

inline constexpr std::size_t kObservationProjectionInstrumentValueCount = 23;
inline constexpr std::size_t kObservationProjectionObservationValueCount = 15;
inline constexpr std::size_t kObservationProjectionRewardTermCount = 2;

inline constexpr std::array<std::string_view, kObservationProjectionInstrumentValueCount>
    kObservationProjectionInstrumentFieldNames = {
        "alt_baro_m",     "alt_radar_m",  "ias_mps",          "mach",
        "vvi_mps",        "pitch_deg",    "roll_deg",         "heading_deg",
        "aoa_deg",        "beta_deg",     "g_load_normal",    "g_load_axial",
        "p_deg_s",        "q_deg_s",      "r_deg_s",          "engine_rpm_pct",
        "fuel_flow_kg_h", "throttle_pos", "fuel_internal_kg", "fuel_external_kg",
        "gear_pos",       "flaps_pos",    "speedbrake_pos",
};

inline constexpr std::array<std::string_view, kObservationProjectionObservationValueCount>
    kObservationProjectionObservationFieldNames = {
        "sim_time", "x",    "y",     "z",      "vx",         "vy",       "vz",           "heading",
        "pitch",    "roll", "speed", "health", "gear_state", "throttle", "total_reward",
};

inline constexpr std::array<std::string_view, kObservationProjectionRewardTermCount>
    kObservationProjectionRewardTermNames = {"survival", "speed"};
inline constexpr std::array<std::string_view, kObservationProjectionRewardTermCount>
    kObservationProjectionRewardTermOwners = {"simulation", "simulation"};

inline constexpr double observation_projection_speed_reward(double speed_mps) noexcept {
    return speed_mps * kObservationProjectionSpeedRewardWeight;
}

} // namespace runtime::cuda_resident
