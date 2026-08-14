#include "runtime/facade/runtime_facade_internal.h"

#include <cstdint>
#include <vector>

std::vector<std::vector<std::uint64_t>>
RuntimeFacade::get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                              bool use_gpu) const {
    return runtime_facade_internal::require_compatibility_port(*runtime_)
        .get_sensor_candidate_ids_batch(refs, use_gpu);
}

std::vector<std::vector<std::uint64_t>>
RuntimeFacade::get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                              double range_m, bool use_gpu) const {
    return runtime_facade_internal::require_compatibility_port(*runtime_)
        .get_visual_candidate_ids_batch(refs, range_m, use_gpu);
}

std::vector<std::vector<std::uint64_t>>
RuntimeFacade::get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                            bool use_gpu) const {
    return runtime_facade_internal::require_compatibility_port(*runtime_)
        .get_comm_candidate_ids_batch(refs, use_gpu);
}

std::vector<WorldBatchVisualBindingCompatibilityScene>
RuntimeFacade::collect_visual_binding_compatibility_scenes_batch(
    const std::vector<WorldEntityRef> &refs, int downsample, bool use_gpu) const {
    const auto visual_candidate_ids = get_visual_candidate_ids_batch(refs, 25000.0, use_gpu);
    return collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        refs, visual_candidate_ids, downsample);
}

std::vector<WorldBatchVisualBindingCompatibilityScene>
RuntimeFacade::collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
    const std::vector<WorldEntityRef> &refs,
    const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch, int downsample) const {
    return runtime_facade_internal::require_compatibility_port(*runtime_)
        .collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(refs, downsample,
                                                                              candidate_ids_batch);
}

std::vector<AgentObservation>
RuntimeFacade::get_agent_observations_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_agent_observations = true,
        })
        .agent_observations;
}

std::vector<InstrumentState>
RuntimeFacade::get_instrument_states_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_instrument_states = true,
        })
        .instrument_states;
}
