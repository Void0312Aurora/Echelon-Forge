#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident {

// RB5 freezes one bounded direct-pilot Phase A trace against the maintained
// CPU FlightControl stage. The CPU and CUDA tests execute independently and
// consume these values only as fixture inputs and expected stage-local output.
inline constexpr std::string_view kCudaResidentPhaseAFixtureId =
    "cuda_resident.phase_a.direct_pilot.v1";
inline constexpr double kCudaResidentPhaseAManualDeadband = 0.05;
inline constexpr double kCudaResidentPhaseAStickTauS = 0.15;

// Flecs currently compiles ecs_ftime_t/ecs_float_t as float. Keep the resident
// stage's filter trace on that same scalar boundary before doing the double
// arithmetic used by the stored SoA values.
inline constexpr double phase_a_cpu_time_step(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

inline constexpr double phase_a_lpf(double previous, double input, double time_step_s) {
    const double quantized_time_step = phase_a_cpu_time_step(time_step_s);
    const double alpha = quantized_time_step / (kCudaResidentPhaseAStickTauS + quantized_time_step);
    return previous + alpha * (input - previous);
}

struct CudaResidentPhaseAFixtureInput {
    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double rudder = 0.0;
    bool active = false;
};

struct CudaResidentPhaseAFixtureExpected {
    double stick_roll_filt = 0.0;
    double stick_pitch_filt = 0.0;
    double stick_yaw_filt = 0.0;
    double stick_yaw_cmd = 0.0;
    bool manual_takeover = false;
    std::uint64_t phase_version = 0;
};

inline constexpr std::array<double, 2> kCudaResidentPhaseAFixtureTimeSteps = {0.05, 0.125};

inline constexpr std::array<CudaResidentPhaseAFixtureInput, 2> kCudaResidentPhaseAFirstInputs = {
    CudaResidentPhaseAFixtureInput{-0.20, 0.10, 0.03, true},
    CudaResidentPhaseAFixtureInput{-0.15, 0.15, 0.03, true},
};

inline constexpr std::array<CudaResidentPhaseAFixtureExpected, 2> kCudaResidentPhaseAFirstExpected =
    {
        CudaResidentPhaseAFixtureExpected{
            phase_a_lpf(0.0, kCudaResidentPhaseAFirstInputs[0].stick_roll,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(0.0, kCudaResidentPhaseAFirstInputs[0].stick_pitch,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(0.0, -kCudaResidentPhaseAFirstInputs[0].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(0.0, -kCudaResidentPhaseAFirstInputs[0].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            true, 1},
        CudaResidentPhaseAFixtureExpected{
            phase_a_lpf(0.0, kCudaResidentPhaseAFirstInputs[1].stick_roll,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(0.0, kCudaResidentPhaseAFirstInputs[1].stick_pitch,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(0.0, -kCudaResidentPhaseAFirstInputs[1].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(0.0, -kCudaResidentPhaseAFirstInputs[1].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            true, 1},
};

inline constexpr std::array<CudaResidentPhaseAFixtureInput, 2> kCudaResidentPhaseAEdgeInputs = {
    CudaResidentPhaseAFixtureInput{0.05, -0.05, 0.05, true},
    CudaResidentPhaseAFixtureInput{-0.20, 0.20, 0.20, false},
};

inline constexpr std::array<CudaResidentPhaseAFixtureExpected, 2> kCudaResidentPhaseAEdgeExpected =
    {
        CudaResidentPhaseAFixtureExpected{
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[0].stick_roll_filt, 0.0,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[0].stick_pitch_filt, 0.0,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[0].stick_yaw_filt, 0.0,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[0].stick_yaw_cmd, 0.0,
                        kCudaResidentPhaseAFixtureTimeSteps[0]),
            false, 2},
        CudaResidentPhaseAFixtureExpected{
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[1].stick_roll_filt,
                        kCudaResidentPhaseAEdgeInputs[1].stick_roll,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[1].stick_pitch_filt,
                        kCudaResidentPhaseAEdgeInputs[1].stick_pitch,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[1].stick_yaw_filt,
                        -kCudaResidentPhaseAEdgeInputs[1].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            phase_a_lpf(kCudaResidentPhaseAFirstExpected[1].stick_yaw_cmd,
                        -kCudaResidentPhaseAEdgeInputs[1].rudder,
                        kCudaResidentPhaseAFixtureTimeSteps[1]),
            true, 2},
};

static_assert(kCudaResidentPhaseAFirstInputs.size() == kCudaResidentPhaseAFixtureTimeSteps.size());
static_assert(kCudaResidentPhaseAFirstExpected.size() ==
              kCudaResidentPhaseAFixtureTimeSteps.size());

} // namespace runtime::cuda_resident
