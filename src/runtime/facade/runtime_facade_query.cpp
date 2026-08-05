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

// T8 information-state architecture, fourth slice / I60. Additive, read-only
// declaration export for the TL13 maintained observation seam; see
// runtime_facade.h for the additive / zero-wiring / single-source rationale.
// This is a pure constant producer: it reads and mutates no facade instance
// state, so it perturbs no serialized output and is safe on a zero-world facade.
ObservationViewSpec RuntimeFacade::describe_maintained_observation_view() const {
    // The structural facts below mirror the Python single source of truth verbatim
    // and are gated against it by tests/architecture/information_state (G4 export
    // parity):
    //   * view_id / owner  -> gym_envs/observation_view.py (registered in
    //     MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS, python/architecture/information_layer.py)
    //   * produced/consumed layers + semantic stage -> that owner's
    //     INFORMATION_LAYER_PRODUCED / INFORMATION_LAYER_CONSUMED / SEMANTIC_STAGE
    // Every string is drawn from the G4 six-layer / P0-P10 whitelist (design doc
    // §3/§6). schema_version keeps the DTO default (single source: the .inc).
    // required_fields / optional_fields are left empty on purpose: the detailed
    // observation field catalogue stays Python-owned so there is no dual-source
    // field list to drift.
    ObservationViewSpec spec{};
    spec.view_id = "gym_envs.observation_view";
    spec.information_layer_produced = {"Agent Observation"};
    spec.information_layer_consumed = {"World Truth", "Track State", "Shared Tactical Picture"};
    spec.semantic_stage = {"P10 ObservationExport"};
    return spec;
}
