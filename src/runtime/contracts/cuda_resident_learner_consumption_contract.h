#pragma once

#include <cstddef>
#include <string_view>

#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

namespace runtime::cuda_resident::learner_consumption {

// The explicitly selected CUDA-resident backend exposes a learner-equivalent
// consumer at the device-observation lease boundary. It reads every element of
// the fixed-air fifteen-field observation tensor, applies the per-field
// normalization below, and writes a device-resident policy-input buffer.
// "Learner equivalent" is deliberately limited to this pre-inference
// transform; it does not claim equivalence with a production forward pass.
inline constexpr std::string_view kLearnerConsumerSurfaceV1 =
    "cuda_resident.device_consumer_learner_equivalent.v1";

// One feature per packed observation field. The packing kernel already
// produces the world-major [world_count, feature_count] float layout, so the
// policy input buffer shares the lease payload's layout family.
inline constexpr std::size_t kLearnerConsumptionFeatureCount = 15;

// Per-field affine normalization: policy_input = (value - offset) * scale.
// The kernel receives the constants by value from this table. Field identities
// and order match the projection contract's packed observation order.
struct LearnerFieldNormalization {
    std::string_view field_id;
    float offset;
    float scale;
};

inline constexpr LearnerFieldNormalization kLearnerNormalization[kLearnerConsumptionFeatureCount] =
    {
        {"sim_time", 0.0F, 0.01F}, // episode seconds, ~100 s scale
        {"x", 0.0F, 0.0001F},      // fixture airspace ~10 km
        {"y", 0.0F, 0.0001F},
        {"z", 1500.0F, 0.0001F},     // centered on the fixture target altitude
        {"vx", 0.0F, 1.0F / 350.0F}, // envelope speed scale
        {"vy", 0.0F, 1.0F / 350.0F},
        {"vz", 0.0F, 1.0F / 350.0F},
        {"heading", 180.0F, 1.0F / 360.0F},
        {"pitch", 0.0F, 1.0F / 90.0F},
        {"roll", 0.0F, 1.0F / 90.0F},
        {"speed", 200.0F, 1.0F / 350.0F}, // centered on cruise speed
        {"health", 0.0F, 0.01F},          // fixture health is percent-scaled
        {"gear_state", 0.0F, 1.0F},
        {"throttle", 0.0F, 1.0F},
        {"total_reward", 0.0F, 0.1F},
};

inline constexpr bool learner_normalization_is_well_formed() {
    for (std::size_t field = 0; field < kLearnerConsumptionFeatureCount; ++field) {
        const auto &entry = kLearnerNormalization[field];
        if (entry.field_id != kObservationProjectionObservationFieldNames[field]) {
            return false;
        }
        if (entry.scale == 0.0F) return false;
        if (!(entry.scale == entry.scale) || !(entry.offset == entry.offset)) {
            return false; // NaN guard without <cmath> in a contract header.
        }
    }
    return true;
}

static_assert(kLearnerConsumptionFeatureCount == kObservationProjectionObservationValueCount,
              "the learner-equivalent consumer covers the packed fifteen-field observation");
static_assert(learner_normalization_is_well_formed(),
              "field identities follow the projection contract order with non-zero finite scales");

} // namespace runtime::cuda_resident::learner_consumption
