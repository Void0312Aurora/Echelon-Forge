#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident {

// RB6 owns a deliberately closed, airborne Phase-B fixture.  These constants
// are the cold configuration uploaded with the fixture; they are not a claim
// that every Flecs aircraft has the same mass, atmosphere, or tuning.
inline constexpr std::string_view kCudaResidentPhaseBFixtureId =
    "cuda_resident.phase_b.airframe_dynamics.v1";
inline constexpr std::string_view kCudaResidentPhaseBSnapshotSchemaV2 =
    "cuda_resident.fixed_air_snapshot.v2";
inline constexpr std::string_view kCudaResidentPhaseBSnapshotProvenance =
    "cuda_resident.rb6.explicit_device_reconstruction";
inline constexpr double kPhaseBGravityMps2 = 9.80665;
inline constexpr double kPhaseBMinTimeStepS = 1.0e-4;
inline constexpr double kPhaseBMaxTimeStepS = 0.25;
inline constexpr double kPhaseBSeaLevelDensityKgM3 = 1.225;
inline constexpr double kPhaseBSeaLevelTemperatureK = 288.15;
inline constexpr double kPhaseBSeaLevelPressurePa = 101325.0;
inline constexpr double kPhaseBGasConstantDryAir = 287.0;
inline constexpr double kPhaseBLapseRateKPerM = 0.0065;
inline constexpr double kPhaseBSpecificHeatRatioAir = 1.4;
inline constexpr double kPhaseBTropopauseAltitudeM = 11000.0;
inline constexpr double kPhaseBTropopauseTemperatureK = 216.65;
inline constexpr double kPhaseBTropopausePressurePa = 22632.1;

// The admitted setup has no EnvironmentModelRef assignment, so the maintained
// aero stage uses its standard-atmosphere fallback with zero wind.
inline constexpr double kPhaseBWindBaseMps = 0.0;
inline constexpr double kPhaseBWindShearMpsPerKm = 0.0;

inline constexpr double kPhaseBEmptyMassKg = 10000.0;
inline constexpr double kPhaseBFuelMassKg = 3000.0;
inline constexpr double kPhaseBStoresMassKg = 0.0;
inline constexpr double kPhaseBReferenceAreaM2 = 27.0;
inline constexpr double kPhaseBWingSpanM = 10.0;
inline constexpr double kPhaseBChordM = 2.7;
inline constexpr double kPhaseBInertiaRollKgM2 = 52083.333333333336;
inline constexpr double kPhaseBInertiaPitchKgM2 = 104166.66666666667;
inline constexpr double kPhaseBInertiaYawKgM2 = 135416.66666666669;
inline constexpr double kPhaseBMilThrustN = 40000.0;
inline constexpr double kPhaseBAbThrustN = 70000.0;

inline constexpr double kPhaseBEngineAbThreshold = 0.9;
inline constexpr double kPhaseBEngineIdleBias = 0.08;
inline constexpr double kPhaseBEngineSpoolUpTauS = 2.5;
inline constexpr double kPhaseBEngineSpoolDownTauS = 1.5;
inline constexpr double kPhaseBEngineAbLightTauS = 1.0;
inline constexpr double kPhaseBEngineAbExtinguishTauS = 0.5;
inline constexpr double kPhaseBEngineRamRiseGain = 0.3;
inline constexpr double kPhaseBEngineRamRiseMachCap = 1.2;
inline constexpr double kPhaseBEngineRamDecayStartMach = 1.5;
inline constexpr double kPhaseBEngineRamDecayGain = 0.2;

inline constexpr double kPhaseBAeroClAlphaPerDeg = 0.1;
inline constexpr double kPhaseBAeroCd0Clean = 0.02;
inline constexpr double kPhaseBAeroInducedDragK = 0.1;
inline constexpr double kPhaseBAeroCmAlphaPerRad = -0.8;
inline constexpr double kPhaseBAeroCmQ = -12.0;
inline constexpr double kPhaseBAeroElevatorMaxDeflectionDeg = 25.0;
inline constexpr double kPhaseBAeroAileronMaxDeflectionDeg = 21.5;
inline constexpr double kPhaseBAeroRudderMaxDeflectionDeg = 30.0;
inline constexpr double kPhaseBAeroCmDeltaEPerRad = 1.2;
inline constexpr double kPhaseBAeroClDeltaAPerRad = 0.10;
inline constexpr double kPhaseBAeroCnDeltaRPerRad = 0.13;
inline constexpr double kPhaseBAeroElevatorTauS = 0.10;
inline constexpr double kPhaseBAeroAileronTauS = 0.08;
inline constexpr double kPhaseBAeroRudderTauS = 0.12;
inline constexpr double kPhaseBStickTauS = 0.15;

// The fixture keeps the existing RB5 two-world replay shape and exercises all
// primary flight axes plus throttle. Secondary/avionics/weapon fields remain
// zero and are rejected by the admission surface.
struct CudaResidentPhaseBFixtureInput {
    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double rudder = 0.0;
    double throttle = 0.0;
};

struct CudaResidentPhaseBFixtureExpected {
    // x, y, z, vx, vy, vz, heading, pitch, roll
    std::array<double, 9> kinematics{};
    // p, q, r, elevator, aileron, rudder, qbar, alpha, beta, mach, Cd
    std::array<double, 11> dynamics{};
};

inline constexpr std::array<double, 2> kCudaResidentPhaseBFixtureTimeSteps = {0.05, 0.125};
inline constexpr std::array<CudaResidentPhaseBFixtureInput, 2> kCudaResidentPhaseBFirstInputs = {
    CudaResidentPhaseBFixtureInput{-0.20, 0.10, 0.03, 0.65},
    CudaResidentPhaseBFixtureInput{-0.15, 0.15, 0.03, 0.65},
};

inline constexpr std::array<CudaResidentPhaseBFixtureExpected, 2> kCudaResidentPhaseBFirstExpected =
    {
        CudaResidentPhaseBFixtureExpected{
            {1009.9965188876647, 0.0, 1499.9877416871348, 199.86074954819867, 0.0,
             -0.49033250730652361, 89.998693077259475, 0.11747601665236991, -0.016330949094538028},
            {-0.0057005765485626291, 0.041006865043180928, 0.00045620209102684492,
             0.10575000122655182, -0.027692308255730297, 0.0031764706571467197, 21164.5380321995,
             0.0, 0.0, 0.59798517047693167, 0.063357407309520358}},
        CudaResidentPhaseBFixtureExpected{
            {1125.1032256273397, 0.0, 1499.9233855468749, 200.6516100374364, 0.0,
             -1.2258312499999999, 89.984821146008343, 1.5539351773958143, -0.22287000251162681},
            {-0.031118522782048703, 0.21697028166495297, 0.0021193678306710897, 0.22159090909090909,
             -0.059866962305986683, 0.0058441558441558409, 21376.7125259723, 0.0, 0.0,
             0.60097509632942092, 0.062776094352058873}},
};

inline constexpr double phase_b_cpu_time_step(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

} // namespace runtime::cuda_resident
