#pragma once

#include <cstddef>
#include <string_view>

#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

namespace runtime::cuda_resident::learner_consumption {

// CP-6 closes gate G-C with a learner-EQUIVALENT consumer measured at the
// CR2-3 lease: it reads every element of the lease value tensor, applies the
// pinned per-field normalization below, and writes a device-resident policy
// input buffer. "Learner equivalent" is scoped to the resident fixture
// surface (the fixed-air fifteen-field observation contract); it is a
// representative pre-inference transform, not equivalence with any production
// forward pass, and the production dictionary-observation stack stays outside
// this gate's coverage.
inline constexpr std::string_view kLearnerConsumerSurfaceV1 =
    "cuda_resident.device_consumer_learner_equivalent.v1";

// Matrix mode identity for the measured learner-consumer lane. Deliberately
// NOT added to the frozen CR2-6a mode table (kModes): the matrix evidence
// validators are still single-generation pinned, and extending the frozen
// scope is the CP-8 re-matrix kickoff's lane. The probe exposes the mode
// behind an explicit flag instead, so default reports keep the frozen shape.
inline constexpr std::string_view kLearnerConsumerModeIdNoExport = "no_export_learner_consumer";

// One feature per packed observation field. The packing kernel already
// produces the world-major [world_count, feature_count] float layout, so the
// policy input buffer shares the lease payload's layout family.
inline constexpr std::size_t kLearnerConsumptionFeatureCount = 15;

// Per-field affine normalization: policy_input = (value - offset) * scale.
// The constants are representative magnitudes for the fixed-air fixture's
// observation fields, owned by this contract alone; any Python or diagnostic
// reader derives them from here (the kernel receives them by value from this
// table). Field identities and order are the projection contract's packed
// observation order, asserted below.
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

// Closing a measurement gate grants nothing else.
inline constexpr bool kMaintainedClaimAllowed = false;
inline constexpr bool kPublicSupportEnabled = false;
inline constexpr bool kPromotionAllowed = false;
inline constexpr bool kTuningAuthorized = false;

} // namespace runtime::cuda_resident::learner_consumption
