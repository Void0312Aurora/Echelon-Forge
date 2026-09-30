#include "runtime_kernel_candidate_facade.h"

namespace runtime::host::integration {

RuntimeWorldRef RuntimeKernelCandidateFacadeAdapter::world_ref() const noexcept {
    return candidate_ == nullptr ? RuntimeWorldRef{} : candidate_->world_ref();
}

RuntimeCandidateCompositionSnapshot
RuntimeKernelCandidateFacadeAdapter::composition_snapshot() const {
    return candidate_ == nullptr ? RuntimeCandidateCompositionSnapshot{}
                                 : candidate_->composition_snapshot();
}

bool RuntimeKernelCandidateFacadeAdapter::composition_immutable() const noexcept {
    return candidate_ != nullptr && candidate_->composition_immutable();
}

std::vector<RuntimeEntityRef> RuntimeKernelCandidateFacadeAdapter::apply_spawn_batch(
    const std::vector<WorldSpawnRequest> &requests) {
    std::vector<RuntimeEntityRef> entities;
    if (candidate_ == nullptr) {
        return entities;
    }
    entities.reserve(requests.size());
    for (const auto &request : requests) {
        const auto entity = candidate_->spawn_unit(world_ref(), request);
        if (!entity.has_value()) {
            // Candidate-only contract: return the successfully spawned prefix.
            // This preserves the per-request result shape of WorldBatchRuntime;
            // callers must not infer atomicity from an empty/full vector.
            return entities;
        }
        entities.push_back(*entity);
    }
    return entities;
}

bool RuntimeKernelCandidateFacadeAdapter::step_batch(std::size_t world_count) {
    if (candidate_ == nullptr || world_count != 1) {
        return false;
    }
    return candidate_->step(world_ref());
}

bool RuntimeKernelCandidateFacadeAdapter::set_time_step(double dt) {
    return candidate_ != nullptr && candidate_->set_time_step(world_ref(), dt);
}

bool RuntimeKernelCandidateFacadeAdapter::try_get_entity_kinematics(const RuntimeEntityRef &entity,
                                                                    WorldEntityKinematics *state) {
    return candidate_ != nullptr && candidate_->try_get_entity_kinematics(entity, state);
}

bool RuntimeKernelCandidateFacadeAdapter::try_set_entity_kinematics(
    const RuntimeEntityRef &entity, const WorldEntityKinematics &state) {
    return candidate_ != nullptr && candidate_->try_set_entity_kinematics(entity, state);
}

} // namespace runtime::host::integration
