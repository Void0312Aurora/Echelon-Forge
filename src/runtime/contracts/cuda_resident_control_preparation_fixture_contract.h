#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident {

// This fixture freezes one bounded direct-pilot control-preparation trace against
// the maintained CPU FlightControl stage. The CPU and CUDA tests execute independently and
// consume these values only as fixture inputs and expected stage-local output.
inline constexpr std::string_view kCudaResidentControlPreparationFixtureId =
    // internal-code: compatibility -- serialized fixture schema v1
    "cuda_resident.phase_a.direct_pilot.v1";
inline constexpr double kCudaResidentControlPreparationManualDeadband = 0.05;
inline constexpr double kCudaResidentControlPreparationStickTauS = 0.15;

// Flecs currently compiles ecs_ftime_t/ecs_float_t as float. Keep the resident
// stage's filter trace on that same scalar boundary before doing the double
// arithmetic used by the stored SoA values.
inline constexpr double control_preparation_cpu_time_step(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

inline constexpr double control_preparation_lpf(double previous, double input, double time_step_s) {
    const double quantized_time_step = control_preparation_cpu_time_step(time_step_s);
    const double alpha =
        quantized_time_step / (kCudaResidentControlPreparationStickTauS + quantized_time_step);
    return previous + alpha * (input - previous);
}

struct CudaResidentControlPreparationFixtureInput {
    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double rudder = 0.0;
    bool active = false;
};

struct CudaResidentControlPreparationFixtureExpected {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;
    bool manual_takeover = false;
    std::uint64_t control_version = 0;
};

inline constexpr std::array<double, 2> kCudaResidentControlPreparationFixtureTimeSteps = {0.05,
                                                                                          0.125};

inline constexpr std::array<CudaResidentControlPreparationFixtureInput, 2>
    kCudaResidentControlPreparationFirstInputs = {
        CudaResidentControlPreparationFixtureInput{-0.20, 0.10, 0.03, true},
        CudaResidentControlPreparationFixtureInput{-0.15, 0.15, 0.03, true},
};

inline constexpr std::array<CudaResidentControlPreparationFixtureExpected, 2>
    kCudaResidentControlPreparationFirstExpected = {
        CudaResidentControlPreparationFixtureExpected{
            control_preparation_lpf(0.0, kCudaResidentControlPreparationFirstInputs[0].stick_roll,
                                    kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(0.0, kCudaResidentControlPreparationFirstInputs[0].stick_pitch,
                                    kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(0.0, -kCudaResidentControlPreparationFirstInputs[0].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(0.0, -kCudaResidentControlPreparationFirstInputs[0].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[0]),
            true, 1},
        CudaResidentControlPreparationFixtureExpected{
            control_preparation_lpf(0.0, kCudaResidentControlPreparationFirstInputs[1].stick_roll,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(0.0, kCudaResidentControlPreparationFirstInputs[1].stick_pitch,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(0.0, -kCudaResidentControlPreparationFirstInputs[1].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(0.0, -kCudaResidentControlPreparationFirstInputs[1].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            true, 1},
};

inline constexpr std::array<CudaResidentControlPreparationFixtureInput, 2>
    kCudaResidentControlPreparationEdgeInputs = {
        CudaResidentControlPreparationFixtureInput{0.05, -0.05, 0.05, true},
        CudaResidentControlPreparationFixtureInput{-0.20, 0.20, 0.20, false},
};

inline constexpr std::array<CudaResidentControlPreparationFixtureExpected, 2>
    kCudaResidentControlPreparationEdgeExpected = {
        CudaResidentControlPreparationFixtureExpected{
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[0].stick_roll_filt,
                                    0.0, kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(
                kCudaResidentControlPreparationFirstExpected[0].stick_pitch_filt, 0.0,
                kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[0].stick_yaw_filt,
                                    0.0, kCudaResidentControlPreparationFixtureTimeSteps[0]),
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[0].stick_yaw_cmd,
                                    0.0, kCudaResidentControlPreparationFixtureTimeSteps[0]),
            false, 2},
        CudaResidentControlPreparationFixtureExpected{
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[1].stick_roll_filt,
                                    kCudaResidentControlPreparationEdgeInputs[1].stick_roll,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(
                kCudaResidentControlPreparationFirstExpected[1].stick_pitch_filt,
                kCudaResidentControlPreparationEdgeInputs[1].stick_pitch,
                kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[1].stick_yaw_filt,
                                    -kCudaResidentControlPreparationEdgeInputs[1].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            control_preparation_lpf(kCudaResidentControlPreparationFirstExpected[1].stick_yaw_cmd,
                                    -kCudaResidentControlPreparationEdgeInputs[1].rudder,
                                    kCudaResidentControlPreparationFixtureTimeSteps[1]),
            true, 2},
};

static_assert(kCudaResidentControlPreparationFirstInputs.size() ==
              kCudaResidentControlPreparationFixtureTimeSteps.size());
static_assert(kCudaResidentControlPreparationFirstExpected.size() ==
              kCudaResidentControlPreparationFixtureTimeSteps.size());

} // namespace runtime::cuda_resident
