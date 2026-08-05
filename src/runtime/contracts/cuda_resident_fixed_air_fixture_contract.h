#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace runtime::cuda_resident {

// Baseline-locked identity contract for the RB4 minimal fixture. The CPU
// reference and resident backend are tested independently against this value;
// production CUDA code never calls into Flecs to discover or translate ids.
inline constexpr std::uint64_t kFixedAirFixtureEntityBaseId = 581;
inline constexpr std::string_view kFixedAirFixtureTypeName = "Aircraft";
inline constexpr std::string_view kFixedAirFixtureRequestId = "rb4.fixed_air_fixture.v1";
inline constexpr std::string_view kCudaResidentSnapshotSchemaV1 =
    "cuda_resident.fixed_air_snapshot.v1";
inline constexpr std::string_view kCudaResidentSnapshotProvenance =
    "cuda_resident.rb4.explicit_device_reconstruction";

[[nodiscard]] constexpr std::uint64_t
fixed_air_fixture_entity_id(std::uint32_t generation) noexcept {
    return kFixedAirFixtureEntityBaseId | (static_cast<std::uint64_t>(generation) << 32U);
}

enum class CudaResidentBarrierCode : std::uint8_t {
    none = 0,
    input_injection = 1,
    stage_publish = 2,
    window_commit = 3,
};

enum class CudaResidentShard : std::size_t {
    identity = 0,
    pilot_flight_controls,
    clock,
    snapshot,
    kinematics,
    dynamics,
    episode,
    instrument,
    observation,
    reward,
    termination,
    events,
    export_envelope,
    count,
};

inline constexpr std::size_t kCudaResidentShardCount =
    static_cast<std::size_t>(CudaResidentShard::count);

inline constexpr std::array<std::string_view, kCudaResidentShardCount> kCudaResidentShardIds = {
    "identity",        "pilot_flight_controls",
    "clock",           "snapshot",
    "kinematics",      "dynamics",
    "episode",         "instrument",
    "observation",     "reward",
    "termination",     "events",
    "export_envelope",
};

[[nodiscard]] constexpr std::string_view
cuda_resident_barrier_id(CudaResidentBarrierCode barrier) noexcept {
    switch (barrier) {
    case CudaResidentBarrierCode::input_injection:
        return "input_injection";
    case CudaResidentBarrierCode::stage_publish:
        return "stage_publish";
    case CudaResidentBarrierCode::window_commit:
        return "window_commit";
    case CudaResidentBarrierCode::none:
        return "none";
    }
    return "unknown";
}

} // namespace runtime::cuda_resident
