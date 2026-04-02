#include "gpu/gpu_flight_shaping_runtime.h"

#include <stdexcept>

namespace gpu::detail {

#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
std::vector<float> compute_flight_shaping_experiment_batch_cuda(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
);
bool compute_flight_shaping_experiment_batch_cuda_device_resident(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
);
FlightShapingExperimentStats last_flight_shaping_cuda_stats();
const void* last_flight_shaping_output_device_ptr_cuda();
std::size_t last_flight_shaping_output_float_count_cuda();
#endif

}  // namespace gpu::detail

namespace {

void pack_products(const FlightShapingRuntimeProducts& src, float* dst) {
    dst[0] = src.valid ? 1.0f : 0.0f;
    dst[1] = static_cast<float>(src.altitude_progress);
    dst[2] = static_cast<float>(src.low_alt_descent_penalty);
    dst[3] = static_cast<float>(src.speed_progress);
    dst[4] = static_cast<float>(src.speed_regress);
    dst[5] = static_cast<float>(src.stationary_penalty);
    dst[6] = static_cast<float>(src.liftoff_bonus);
    dst[7] = src.next_liftoff_awarded ? 1.0f : 0.0f;
    dst[8] = static_cast<float>(src.rotation_reward);
    dst[9] = static_cast<float>(src.rotation_overpitch_penalty);
    dst[10] = static_cast<float>(src.gear_up_bonus);
    dst[11] = src.next_gear_bonus_awarded ? 1.0f : 0.0f;
    dst[12] = static_cast<float>(src.roll_stability);
    dst[13] = static_cast<float>(src.heading_error_penalty);
    dst[14] = static_cast<float>(src.heading_hold_bonus);
    dst[15] = static_cast<float>(src.altitude_error_penalty);
    dst[16] = static_cast<float>(src.altitude_hold_bonus);
    dst[17] = static_cast<float>(src.speed_error_penalty);
    dst[18] = static_cast<float>(src.speed_hold_bonus);
    dst[19] = static_cast<float>(src.roll_abs_penalty);
    dst[20] = static_cast<float>(src.pitch_abs_penalty);
    dst[21] = static_cast<float>(src.yaw_rate_abs_penalty);
    dst[22] = static_cast<float>(src.beta_abs_penalty);
    dst[23] = static_cast<float>(src.g_deviation_penalty);
    dst[24] = static_cast<float>(src.speed_reward);
    dst[25] = static_cast<float>(src.runway_centerline_m_penalty);
    dst[26] = static_cast<float>(src.runway_centerline_penalty);
    dst[27] = static_cast<float>(src.runway_centerline_barrier);
    dst[28] = static_cast<float>(src.departure_centerline_m_penalty);
    dst[29] = static_cast<float>(src.departure_centerline_reward);
    dst[30] = static_cast<float>(src.departure_track_error_penalty);
    dst[31] = static_cast<float>(src.departure_track_reward);
    dst[32] = static_cast<float>(src.alignment_reward);
}

}  // namespace

namespace gpu {

FlightShapingExperimentStats last_flight_shaping_stats() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_flight_shaping_cuda_stats();
#else
    return FlightShapingExperimentStats{};
#endif
}

const void* last_flight_shaping_output_device_ptr() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_flight_shaping_output_device_ptr_cuda();
#else
    return nullptr;
#endif
}

std::size_t last_flight_shaping_output_float_count() {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::last_flight_shaping_output_float_count_cuda();
#else
    return 0;
#endif
}

std::vector<float> compute_flight_shaping_reference_cpu_batch(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
) {
    if (inputs_batch.empty()) {
        return {};
    }
    std::vector<float> out(inputs_batch.size() * static_cast<std::size_t>(kFlightShapingOutputCount), 0.0f);
    for (std::size_t idx = 0; idx < inputs_batch.size(); ++idx) {
        const auto products = compute_flight_shaping_terms(inputs_batch[idx]);
        pack_products(products, out.data() + static_cast<std::ptrdiff_t>(idx * static_cast<std::size_t>(kFlightShapingOutputCount)));
    }
    return out;
}

std::vector<float> compute_flight_shaping_experiment_batch(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    auto out = detail::compute_flight_shaping_experiment_batch_cuda(inputs_batch);
    if (!out.empty()) {
        return out;
    }
#endif
    return compute_flight_shaping_reference_cpu_batch(inputs_batch);
}

bool compute_flight_shaping_experiment_batch_device_resident(
    const std::vector<FlightShapingRuntimeInputs>& inputs_batch
) {
#if defined(EF_ENABLE_CUDA_EXPERIMENTS)
    return detail::compute_flight_shaping_experiment_batch_cuda_device_resident(inputs_batch);
#else
    (void)inputs_batch;
    return false;
#endif
}

}  // namespace gpu
