#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident {

// This contract owns a deliberately closed, airborne flight-dynamics fixture. These constants
// are the cold configuration uploaded with the fixture; they are not a claim
// that every Flecs aircraft has the same mass, atmosphere, or tuning.
inline constexpr std::string_view kCudaResidentFlightDynamicsFixtureId =
    // internal-code: compatibility -- serialized fixture schema v1
    "cuda_resident.phase_b.airframe_dynamics.v1";
inline constexpr std::string_view kCudaResidentFlightDynamicsSnapshotSchemaV2 =
    "cuda_resident.fixed_air_snapshot.v2";
inline constexpr std::string_view kCudaResidentFlightDynamicsSnapshotProvenance =
    // internal-code: compatibility -- serialized snapshot provenance v2
    "cuda_resident.rb6.explicit_device_reconstruction";
inline constexpr double kFlightDynamicsGravityMps2 = 9.80665;
inline constexpr double kFlightDynamicsMinTimeStepS = 1.0e-4;
inline constexpr double kFlightDynamicsMaxTimeStepS = 0.25;
inline constexpr double kFlightDynamicsSeaLevelDensityKgM3 = 1.225;
inline constexpr double kFlightDynamicsSeaLevelTemperatureK = 288.15;
inline constexpr double kFlightDynamicsSeaLevelPressurePa = 101325.0;
inline constexpr double kFlightDynamicsGasConstantDryAir = 287.0;
inline constexpr double kFlightDynamicsLapseRateKPerM = 0.0065;
inline constexpr double kFlightDynamicsSpecificHeatRatioAir = 1.4;
inline constexpr double kFlightDynamicsTropopauseAltitudeM = 11000.0;
inline constexpr double kFlightDynamicsTropopauseTemperatureK = 216.65;
inline constexpr double kFlightDynamicsTropopausePressurePa = 22632.1;

// The admitted setup has no EnvironmentModelRef assignment, so the maintained
// aero stage uses its standard-atmosphere fallback with zero wind.
inline constexpr double kFlightDynamicsWindBaseMps = 0.0;
inline constexpr double kFlightDynamicsWindShearMpsPerKm = 0.0;

inline constexpr double kFlightDynamicsEmptyMassKg = 10000.0;
inline constexpr double kFlightDynamicsFuelMassKg = 3000.0;
inline constexpr double kFlightDynamicsStoresMassKg = 0.0;
inline constexpr double kFlightDynamicsReferenceAreaM2 = 27.0;
inline constexpr double kFlightDynamicsWingSpanM = 10.0;
inline constexpr double kFlightDynamicsChordM = 2.7;
inline constexpr double kFlightDynamicsInertiaRollKgM2 = 52083.333333333336;
inline constexpr double kFlightDynamicsInertiaPitchKgM2 = 104166.66666666667;
inline constexpr double kFlightDynamicsInertiaYawKgM2 = 135416.66666666669;
inline constexpr double kFlightDynamicsMilThrustN = 40000.0;
inline constexpr double kFlightDynamicsAbThrustN = 70000.0;

inline constexpr double kFlightDynamicsEngineAbThreshold = 0.9;
inline constexpr double kFlightDynamicsEngineIdleBias = 0.08;
inline constexpr double kFlightDynamicsEngineSpoolUpTauS = 2.5;
inline constexpr double kFlightDynamicsEngineSpoolDownTauS = 1.5;
inline constexpr double kFlightDynamicsEngineAbLightTauS = 1.0;
inline constexpr double kFlightDynamicsEngineAbExtinguishTauS = 0.5;
inline constexpr double kFlightDynamicsEngineRamRiseGain = 0.3;
inline constexpr double kFlightDynamicsEngineRamRiseMachCap = 1.2;
inline constexpr double kFlightDynamicsEngineRamDecayStartMach = 1.5;
inline constexpr double kFlightDynamicsEngineRamDecayGain = 0.2;

inline constexpr double kFlightDynamicsAeroClAlphaPerDeg = 0.1;
inline constexpr double kFlightDynamicsAeroCd0Clean = 0.02;
inline constexpr double kFlightDynamicsAeroInducedDragK = 0.1;
inline constexpr double kFlightDynamicsAeroCmAlphaPerRad = -0.8;
inline constexpr double kFlightDynamicsAeroCmQ = -12.0;
inline constexpr double kFlightDynamicsAeroElevatorMaxDeflectionDeg = 25.0;
inline constexpr double kFlightDynamicsAeroAileronMaxDeflectionDeg = 21.5;
inline constexpr double kFlightDynamicsAeroRudderMaxDeflectionDeg = 30.0;
inline constexpr double kFlightDynamicsAeroCmDeltaEPerRad = 1.2;
inline constexpr double kFlightDynamicsAeroClDeltaAPerRad = 0.10;
inline constexpr double kFlightDynamicsAeroCnDeltaRPerRad = 0.13;
inline constexpr double kFlightDynamicsAeroElevatorTauS = 0.10;
inline constexpr double kFlightDynamicsAeroAileronTauS = 0.08;
inline constexpr double kFlightDynamicsAeroRudderTauS = 0.12;
inline constexpr double kFlightDynamicsStickTauS = 0.15;

// The fixture keeps the existing two-world replay shape and exercises all
// primary flight axes plus throttle. Secondary/avionics/weapon fields remain
// zero and are rejected by the admission surface.
struct CudaResidentFlightDynamicsFixtureInput {
    double stick_roll = 0.0;
    double stick_pitch = 0.0;
    double rudder = 0.0;
    double throttle = 0.0;
};

struct CudaResidentFlightDynamicsFixtureExpected {
    // x, y, z, vx, vy, vz, heading, pitch, roll
    std::array<double, 9> kinematics{};
    // p, q, r, elevator, aileron, rudder, qbar, alpha, beta, mach, Cd
    std::array<double, 11> dynamics{};
};

inline constexpr std::array<double, 2> kCudaResidentFlightDynamicsFixtureTimeSteps = {0.05, 0.125};
inline constexpr std::array<CudaResidentFlightDynamicsFixtureInput, 2>
    kCudaResidentFlightDynamicsFirstInputs = {
        CudaResidentFlightDynamicsFixtureInput{-0.20, 0.10, 0.03, 0.65},
        CudaResidentFlightDynamicsFixtureInput{-0.15, 0.15, 0.03, 0.65},
};

inline constexpr std::array<CudaResidentFlightDynamicsFixtureExpected, 2>
    kCudaResidentFlightDynamicsFirstExpected = {
        CudaResidentFlightDynamicsFixtureExpected{
            {1009.9965188876647, 0.0, 1499.9877416871348, 199.86074954819867, 0.0,
             -0.49033250730652361, 89.998693077259475, 0.11747601665236991, -0.016330949094538028},
            {-0.0057005765485626291, 0.041006865043180928, 0.00045620209102684492,
             0.10575000122655182, -0.027692308255730297, 0.0031764706571467197, 21164.5380321995,
             0.0, 0.0, 0.59798517047693167, 0.063357407309520358}},
        CudaResidentFlightDynamicsFixtureExpected{
            {1125.1032256273397, 0.0, 1499.9233855468749, 200.6516100374364, 0.0,
             -1.2258312499999999, 89.984821146008343, 1.5539351773958143, -0.22287000251162681},
            {-0.031118522782048703, 0.21697028166495297, 0.0021193678306710897, 0.22159090909090909,
             -0.059866962305986683, 0.0058441558441558409, 21376.7125259723, 0.0, 0.0,
             0.60097509632942092, 0.062776094352058873}},
};

inline constexpr double flight_dynamics_cpu_time_step(double time_step_s) {
    return static_cast<double>(static_cast<float>(time_step_s));
}

} // namespace runtime::cuda_resident
