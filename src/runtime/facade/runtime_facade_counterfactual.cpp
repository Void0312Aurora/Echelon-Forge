#include "runtime/facade/runtime_facade_internal.h"

#include "components/basic/common.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"

#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using namespace runtime_facade_internal;

BatchWorldSetupRequest single_world_counterfactual_setup(BatchWorldSetupRequest setup,
                                                         std::uint32_t seed) {
    if (seed != 0U) {
        setup.seeds = {seed};
    } else if (setup.seeds.empty()) {
        setup.seeds = {0U};
    } else {
        setup.seeds = {setup.seeds.front()};
    }
    for (auto &assignment : setup.terrain_assignments) {
        assignment.world_index = 0;
    }
    for (auto &assignment : setup.wind_assignments) {
        assignment.world_index = 0;
    }
    for (auto &zone : setup.zones) {
        zone.world_index = 0;
    }
    for (auto &spawn : setup.spawn_requests) {
        spawn.world_index = 0;
    }
    for (auto &spawn : setup.typed_platform_spawn_requests) {
        spawn.world_index = 0;
    }
    if (setup.time_steps.size() > 1U) {
        setup.time_steps = {setup.time_steps.front()};
    }
    return setup;
}

std::uint64_t counterfactual_spawned_entity_id(const BatchWorldSetupResult &setup_result,
                                               const WorldEntityRef &requested_ref) {
    if (requested_ref.entity_id != 0U) {
        return requested_ref.entity_id;
    }
    if (!setup_result.entity_ids.empty()) {
        return setup_result.entity_ids.front();
    }
    return 0U;
}

RuntimeCounterfactualSnapshot
counterfactual_snapshot_from_runtime(const WorldBatchRuntime &runtime, const WorldEntityRef &ref,
                                     const RuntimeFidelityAdmission &fidelity_admission,
                                     const std::string &cadence_reason,
                                     std::vector<std::string> evidence_refs) {
    if (!valid_runtime_world_index(runtime, ref.world_index)) {
        throw std::out_of_range(std::string(kRuntimeCounterfactualInvalidWorld));
    }

    WorldEntityKinematics kinematics{};
    if (!runtime.try_get_entity_kinematics(ref, &kinematics)) {
        throw std::runtime_error(std::string(kRuntimeCounterfactualInvalidEntity));
    }

    evidence_refs.push_back("RuntimeFacade.snapshot_counterfactual_entity");
    evidence_refs.push_back("RuntimeFacade.admit_fidelity_request");
    if (!fidelity_admission.selected_stage_node_id.empty()) {
        evidence_refs.push_back("selected_stage_node_id=" +
                                fidelity_admission.selected_stage_node_id);
    }
    if (!cadence_reason.empty()) {
        evidence_refs.push_back("cadence_reason=" + cadence_reason);
    }

    return RuntimeCounterfactualSnapshot{
        .world_index = ref.world_index,
        .entity_id = ref.entity_id,
        .x = kinematics.x,
        .y = kinematics.y,
        .z = kinematics.z,
        .vx = kinematics.vx,
        .vy = kinematics.vy,
        .vz = kinematics.vz,
        .heading = kinematics.heading,
        .pitch = kinematics.pitch,
        .roll = kinematics.roll,
        .snapshot_version = kRuntimeCounterfactualSelectedSliceSnapshotVersion,
        .barrier_id = std::string(kRuntimeCounterfactualSelectedSliceBarrierId),
        .fidelity_profile_id = fidelity_admission.backend_profile_id,
        .provider_family = fidelity_admission.selected_provider_family,
        .selected_stage_node_id = fidelity_admission.selected_stage_node_id,
        .cadence_reason = cadence_reason,
        .evidence_refs = std::move(evidence_refs),
    };
}

runtime::counterfactual::ReplayEnvelope
replay_envelope_from_experiment_request(const RuntimeExperimentRequest &request) {
    using namespace runtime::counterfactual;

    const auto &branch_request = request.branch_request;
    return ReplayEnvelope{
        .replay_envelope_id = branch_request.replay_envelope_id,
        .run_id = request.experiment_run_id.empty() ? "run:counterfactual_experiment"
                                                    : request.experiment_run_id,
        .episode_id =
            request.setup_ref.empty() ? "episode:counterfactual_experiment" : request.setup_ref,
        .has_deterministic_seed = true,
        .deterministic_seed = branch_request.deterministic_seed,
        .has_source_time = true,
        .source_time_s = 0.0,
        .snapshot_ref =
            ReplaySnapshotRef{
                .snapshot_version_ref = request.setup_ref.empty()
                                            ? "snapshot:counterfactual_experiment"
                                            : request.setup_ref,
            },
        .barrier_ref =
            ReplayBarrierRef{
                .barrier_id = branch_request.restore_barrier_id,
                .barrier_sequence = 1,
                .barrier_detail = branch_request.cadence_reason.empty()
                                      ? "maintained_facade_export"
                                      : branch_request.cadence_reason,
            },
        .event_order_ref =
            ReplayEventOrderRef{
                .sort_key = std::string(kDeterministicReplayEventOrderSortKey),
                .event_id = branch_request.branch_point_id,
                .producer_node_id = "observation_export.v1",
            },
        .facade_provenance_ref =
            ReplayFacadeProvenanceRef{
                .packet_ref = "observation_packet:" + branch_request.replay_envelope_id,
            },
        .snapshot_restore_supported = true,
        .restore_support_boundary =
            std::string(kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly),
    };
}

[[maybe_unused]] runtime::counterfactual::BranchPoint
branch_point_from_experiment_request(const RuntimeExperimentRequest &request) {
    const auto envelope = replay_envelope_from_experiment_request(request);
    return runtime::counterfactual::BranchPoint{
        .branch_point_id = request.branch_request.branch_point_id,
        .replay_envelope_id = request.branch_request.replay_envelope_id,
        .snapshot_version_ref = envelope.snapshot_ref.snapshot_version_ref,
        .barrier_id = request.branch_request.restore_barrier_id,
        .event_order_ref = request.branch_request.branch_point_id,
        .facade_packet_ref = envelope.facade_provenance_ref.packet_ref,
    };
}

std::vector<std::string>
runtime_experiment_capability_refs(const RuntimeExperimentRequest &request) {
    if (!request.capability_refs.empty()) {
        return request.capability_refs;
    }
    return {"capability_bundle:runtime_facade.counterfactual"};
}

std::vector<std::string>
runtime_experiment_generated_input_evidence_refs(const RuntimeExperimentRequest &request) {
    std::vector<std::string> refs = request.generated_input_evidence_refs;
    if (refs.empty()) {
        refs.push_back(request.generation_ref.empty() ? "generated_input:runtime_facade.counterfactual"
                                                      : request.generation_ref);
    }
    return refs;
}

runtime::counterfactual::ScenarioGenerationArtifactMetadata
scenario_generation_metadata_from_experiment_request(
    const RuntimeExperimentRequest &request, const std::vector<std::string> &capability_refs) {
    using namespace runtime::counterfactual;

    ScenarioGenerationArtifactMetadata metadata{};
    metadata.authoritative_state_mutation_allowed = false;
    metadata.request.request_id =
        request.generated_input_ref.empty()
            ? (request.generation_ref.empty() ? "scenario-gen:runtime_facade.counterfactual"
                                              : request.generation_ref)
            : request.generated_input_ref;
    metadata.request.request_version = "1";
    metadata.request.contract_version =
        std::string(kScenarioGenerationContractVersionRequestV1);
    metadata.request.generation_kind = request.generated_input_kind.empty()
                                           ? std::string(kScenarioGenerationKindScenarioVariation)
                                           : request.generated_input_kind;
    metadata.request.source = request.generated_input_source.empty()
                                  ? std::string(kScenarioGenerationSourceCounterfactualBranch)
                                  : request.generated_input_source;
    metadata.request.generator_version = request.generated_input_generator_version.empty()
                                             ? "RuntimeFacade.run_counterfactual_experiment.counterfactual"
                                             : request.generated_input_generator_version;
    metadata.request.has_deterministic_seed = true;
    metadata.request.deterministic_seed = request.branch_request.deterministic_seed;
    metadata.request.baseline_scenario_ref =
        request.generated_input_baseline_scenario_ref.empty()
            ? (request.setup_ref.empty() ? "scenario:runtime_facade.counterfactual" : request.setup_ref)
            : request.generated_input_baseline_scenario_ref;
    metadata.request.replay_envelope_ref = request.branch_request.replay_envelope_id;
    metadata.request.branch_point_ref = request.branch_request.branch_point_id;
    metadata.request.capability_refs = capability_refs;

    metadata.request.evidence_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
        .ref_id = metadata.request.baseline_scenario_ref,
        .evidence_kind = std::string(kScenarioGenerationEvidenceKindBaselineScenario),
        .provenance_label = "baseline",
    });
    metadata.request.evidence_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
        .ref_id = request.branch_request.replay_envelope_id,
        .evidence_kind = std::string(kScenarioGenerationEvidenceKindReplayEnvelope),
        .provenance_label = "replay",
    });
    metadata.request.evidence_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
        .ref_id = request.branch_request.branch_point_id,
        .evidence_kind = std::string(kScenarioGenerationEvidenceKindBranchPoint),
        .provenance_label = "branch",
    });
    for (const auto &evidence_ref : runtime_experiment_generated_input_evidence_refs(request)) {
        metadata.request.evidence_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
            .ref_id = evidence_ref,
            .evidence_kind = std::string(kScenarioGenerationEvidenceKindReviewNote),
            .provenance_label = "runtime",
        });
    }
    return metadata;
}

runtime::counterfactual::CounterfactualAdmissionResult
counterfactual_admission_from_experiment_request(const RuntimeExperimentRequest &request,
                                                 const std::vector<std::string> &capability_refs) {
    runtime::counterfactual::CounterfactualAdmissionResult admission{};
    admission.admitted = true;
    admission.snapshot_restore_supported = true;
    admission.request_id = request.branch_request.branch_point_id.empty()
                               ? request.experiment_run_id
                               : request.branch_request.branch_point_id;
    admission.baseline_worldline_id = request.branch_request.parent_worldline_id;
    admission.child_worldline_id = request.branch_request.branch_worldline_id;
    admission.replay_envelope_id = request.branch_request.replay_envelope_id;
    admission.branch_point_id = request.branch_request.branch_point_id;
    admission.intervention_kind =
        std::string(runtime::counterfactual::kCounterfactualInterventionKindObservationWithhold);
    admission.source = std::string(runtime::counterfactual::kCounterfactualSourceExperimentPlan);
    admission.authority_ref = "RuntimeFacade.run_counterfactual_experiment";
    admission.provenance_ref =
        request.setup_ref.empty() ? request.experiment_run_id : request.setup_ref;
    admission.backend_profile_ref = request.branch_request.fidelity_request.backend_profile_id;
    admission.fidelity_profile_ref = request.branch_request.fidelity_request.request_label;
    admission.capability_refs = capability_refs;
    admission.admission_state =
        std::string(runtime::counterfactual::kCounterfactualAdmissionStateAdmitted);
    admission.worldline_support_state =
        std::string(runtime::counterfactual::kWorldlineBranchSupportStateAdmitted);
    admission.restore_support_boundary =
        std::string(runtime::counterfactual::kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly);
    admission.evidence_refs = request.evidence_refs;
    return admission;
}

std::vector<runtime::counterfactual::ExperimentProfileObservationRef>
profile_observation_refs_from_experiment_request(
    const RuntimeExperimentRequest &request,
    const RuntimeCounterfactualBranchResult &branch_result) {
    using namespace runtime::counterfactual;

    std::vector<ExperimentProfileObservationRef> refs;
    const auto add_ref = [&](const RuntimeExperimentStepRequest &step_request,
                             std::string fallback_ref, std::string fallback_profile) {
        ExperimentProfileObservationRef ref{};
        ref.observation_ref = step_request.observation_ref.empty() ? std::move(fallback_ref)
                                                                   : step_request.observation_ref;
        ref.profile_ref = step_request.profile_ref.empty() ? std::move(fallback_profile)
                                                           : step_request.profile_ref;
        ref.status = std::string(kExperimentProfileObservationStatusObserved);
        ref.claim_scope = step_request.claim_scope.empty()
                              ? std::string(kExperimentProfileClaimScopeDescriptive)
                              : step_request.claim_scope;
        ref.truth_claim = request.truth_claim;
        ref.promoted_to_support = request.promoted_to_support;
        ref.evidence_refs = step_request.evidence_refs;
        if (ref.evidence_refs.empty()) {
            ref.evidence_refs = branch_result.comparison.evidence_refs;
        }
        if (ref.evidence_refs.empty()) {
            ref.evidence_refs = {"RuntimeFacade.run_counterfactual_experiment"};
        }
        refs.push_back(std::move(ref));
    };

    for (std::size_t index = 0; index < request.parent_step_requests.size(); ++index) {
        add_ref(request.parent_step_requests[index], "profile_obs:parent:" + std::to_string(index),
                "profile:parent");
    }
    for (std::size_t index = 0; index < request.branch_step_requests.size(); ++index) {
        add_ref(request.branch_step_requests[index], "profile_obs:branch:" + std::to_string(index),
                "profile:branch");
    }
    if (refs.empty()) {
        ExperimentProfileObservationRef ref{};
        ref.observation_ref = "profile_obs:" + branch_result.comparison.comparison_id;
        ref.profile_ref = "profile:counterfactual_selected_slice";
        ref.status = std::string(kExperimentProfileObservationStatusObserved);
        ref.claim_scope = std::string(kExperimentProfileClaimScopeComparative);
        ref.truth_claim = request.truth_claim;
        ref.promoted_to_support = request.promoted_to_support;
        ref.evidence_refs = branch_result.comparison.evidence_refs;
        if (ref.evidence_refs.empty()) {
            ref.evidence_refs = {"RuntimeFacade.run_counterfactual_experiment"};
        }
        refs.push_back(std::move(ref));
    }
    return refs;
}

RuntimeWorldlineComparison
compare_counterfactual_snapshots(const RuntimeCounterfactualSnapshot &parent,
                                 const RuntimeCounterfactualSnapshot &branch,
                                 const RuntimeCounterfactualBranchRequest &request) {
    RuntimeWorldlineComparison comparison{};
    comparison.comparable = parent.entity_id != 0U && parent.entity_id == branch.entity_id &&
                            parent.world_index == branch.world_index;
    comparison.comparison_id = request.branch_point_id.empty()
                                   ? "counterfactual:selected_slice"
                                   : "counterfactual:selected_slice:" + request.branch_point_id;
    comparison.parent_worldline_id = parent.worldline_id;
    comparison.branch_worldline_id = branch.worldline_id;
    comparison.barrier_id = std::string(kRuntimeCounterfactualSelectedSliceBarrierId);
    comparison.dx = branch.x - parent.x;
    comparison.dy = branch.y - parent.y;
    comparison.dz = branch.z - parent.z;
    comparison.dvx = branch.vx - parent.vx;
    comparison.dvy = branch.vy - parent.vy;
    comparison.dvz = branch.vz - parent.vz;
    comparison.dheading = branch.heading - parent.heading;
    comparison.evidence_refs = {
        "RuntimeFacade.run_counterfactual_branch",
        "RuntimeFacade.compare_counterfactual_snapshots",
        "replay_envelope_id=" + request.replay_envelope_id,
        "branch_point_id=" + request.branch_point_id,
        "restore_barrier_id=" + request.restore_barrier_id,
        "parent_worldline_id=" + parent.worldline_id,
        "branch_worldline_id=" + branch.worldline_id,
        "deterministic_seed=" + std::to_string(request.deterministic_seed),
    };
    return comparison;
}

std::string runtime_counterfactual_restore_boundary_for_snapshot(
    const RuntimeCounterfactualSnapshot &snapshot) {
    using namespace runtime::counterfactual;

    const ReplayEnvelope envelope{
        .replay_envelope_id = snapshot.worldline_id.empty()
                                  ? "replay:facade:anonymous"
                                  : "replay:facade:" + snapshot.worldline_id,
        .run_id = snapshot.worldline_id.empty() ? "run:facade" : snapshot.worldline_id,
        .episode_id = snapshot.barrier_id.empty() ? "episode:facade" : snapshot.barrier_id,
        .has_deterministic_seed = true,
        .deterministic_seed = snapshot.deterministic_seed,
        .has_source_time = true,
        .source_time_s = 0.0,
        .snapshot_ref =
            ReplaySnapshotRef{
                .snapshot_version_ref = "snapshot:" + std::to_string(snapshot.snapshot_version),
            },
        .barrier_ref =
            ReplayBarrierRef{
                .barrier_id = snapshot.barrier_id,
                .barrier_sequence = snapshot.snapshot_version,
                .barrier_detail = snapshot.cadence_reason.empty() ? "maintained_facade_export"
                                                                  : snapshot.cadence_reason,
            },
        .event_order_ref =
            ReplayEventOrderRef{
                .sort_key = std::string(kDeterministicReplayEventOrderSortKey),
                .event_id = snapshot.worldline_id.empty() ? "event:facade"
                                                          : "event:" + snapshot.worldline_id,
                .producer_node_id = snapshot.selected_stage_node_id.empty()
                                        ? "observation_export.v1"
                                        : snapshot.selected_stage_node_id,
            },
        .facade_provenance_ref =
            ReplayFacadeProvenanceRef{
                .packet_ref =
                    snapshot.worldline_id.empty() ? "obs:facade" : "obs:" + snapshot.worldline_id,
            },
        .snapshot_restore_supported = true,
        .restore_support_boundary =
            std::string(kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly),
    };
    const ReplayRestoreSupportResult support =
        validate_replay_envelope_for_snapshot_restore(envelope);
    return support.supported ? std::string() : support.rejection_reason;
}

} // namespace

bool RuntimeFacade::counterfactual_world_index_valid(std::uint64_t world_index) const noexcept {
    return valid_runtime_world_index(*runtime_, world_index);
}

bool RuntimeFacade::apply_counterfactual_delta(const WorldEntityRef &ref,
                                               const RuntimeCounterfactualBranchRequest &request) {
    WorldEntityKinematics state{};
    if (!runtime_->try_get_entity_kinematics(ref, &state)) {
        return false;
    }

    state.x += request.mutation_dx;
    state.y += request.mutation_dy;
    state.z += request.mutation_dz;
    state.heading = Math::normalize_heading_deg(state.heading + request.mutation_dheading);
    state.vx += request.mutation_dvx;
    state.vy += request.mutation_dvy;
    state.vz += request.mutation_dvz;
    return runtime_->try_set_entity_kinematics(ref, state);
}

bool RuntimeFacade::restore_counterfactual_entity(const WorldEntityRef &target_ref,
                                                  const RuntimeCounterfactualSnapshot &snapshot) {
    WorldEntityKinematics state{};
    state.x = snapshot.x;
    state.y = snapshot.y;
    state.z = snapshot.z;
    state.heading = Math::normalize_heading_deg(snapshot.heading);
    state.pitch = snapshot.pitch;
    state.roll = snapshot.roll;
    state.vx = snapshot.vx;
    state.vy = snapshot.vy;
    state.vz = snapshot.vz;
    return runtime_->try_set_entity_kinematics(target_ref, state);
}

void RuntimeFacade::register_counterfactual_worldline_snapshot(
    const RuntimeCounterfactualSnapshot &snapshot) {
    if (counterfactual_worldlines_ == nullptr || runtime_string_blank(snapshot.worldline_id)) {
        return;
    }
    counterfactual_worldlines_->snapshots[snapshot.worldline_id] = snapshot;
}

RuntimeCounterfactualSnapshot RuntimeFacade::snapshot_counterfactual_entity(
    const WorldEntityRef &ref, const RuntimeFidelityAdmission &fidelity_admission,
    const std::string &cadence_reason, const std::vector<std::string> &evidence_refs) {
    RuntimeCounterfactualSnapshot snapshot = counterfactual_snapshot_from_runtime(
        *runtime_, ref, fidelity_admission, cadence_reason, evidence_refs);
    if (runtime_string_blank(snapshot.worldline_id)) {
        snapshot.worldline_id = "worldline:runtime:" + std::to_string(snapshot.world_index) + ":" +
                                std::to_string(snapshot.entity_id);
    }
    if (snapshot.parent_worldline_id.empty()) {
        snapshot.parent_worldline_id = snapshot.worldline_id;
    }
    if (snapshot.deterministic_seed == 0U) {
        snapshot.deterministic_seed = snapshot.entity_id;
    }
    if (snapshot.evidence_refs.empty() ||
        std::find(snapshot.evidence_refs.begin(), snapshot.evidence_refs.end(),
                  std::string(kRuntimeCounterfactualRegisterEvidenceLabel)) ==
            snapshot.evidence_refs.end()) {
        snapshot.evidence_refs.push_back(std::string(kRuntimeCounterfactualRegisterEvidenceLabel));
    }
    register_counterfactual_worldline_snapshot(snapshot);
    return snapshot;
}

RuntimeCounterfactualRestoreResult
RuntimeFacade::restore_counterfactual_snapshot(const RuntimeCounterfactualRestoreRequest &request) {
    RuntimeCounterfactualRestoreResult result{};
    result.evidence_refs = request.evidence_refs;
    append_runtime_evidence_ref(result.evidence_refs,
                                std::string(kRuntimeCounterfactualRestoreEvidenceLabel));
    append_runtime_evidence_ref(result.evidence_refs,
                                "restore_barrier_id=" + request.restore_barrier_id);

    if (request.allow_raw_authoritative_state_mutation) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRestoreRawMutationRejection);
        return result;
    }
    if (request.request_full_clone) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRestoreFullCloneRejection);
        return result;
    }
    if (request.request_resident_state_restore) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRestoreResidentStateRejection);
        return result;
    }
    if (request.request_exact_gpu_restore) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRestoreExactGpuRejection);
        return result;
    }

    const RuntimeCounterfactualSnapshot &snapshot = request.snapshot;
    if (runtime_string_blank(snapshot.worldline_id)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualMissingWorldlineId);
        return result;
    }

    const std::string boundary_rejection =
        runtime_counterfactual_restore_boundary_for_snapshot(snapshot);
    if (!boundary_rejection.empty()) {
        result.rejection_reason = boundary_rejection;
        return result;
    }

    if (request.restore_barrier_id != snapshot.barrier_id) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRestoreBarrierMismatch);
        return result;
    }

    if (!runtime_string_blank(request.expected_worldline_id) &&
        request.expected_worldline_id != snapshot.worldline_id) {
        result.rejection_reason = std::string(kRuntimeCounterfactualWorldlineMismatch);
        return result;
    }
    if (counterfactual_worldlines_ == nullptr) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidWorldlineId);
        return result;
    }
    const auto registry_it = counterfactual_worldlines_->snapshots.find(snapshot.worldline_id);
    if (registry_it == counterfactual_worldlines_->snapshots.end()) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidWorldlineId);
        return result;
    }

    WorldEntityRef target_ref = request.target_entity_ref;
    if (target_ref.entity_id == 0U) {
        target_ref = WorldEntityRef{
            .world_index = registry_it->second.world_index,
            .entity_id = registry_it->second.entity_id,
        };
    }

    std::string restore_rejection;
    if (!counterfactual_world_index_valid(target_ref.world_index)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidWorld);
        return result;
    }
    if (!restore_counterfactual_entity(target_ref, registry_it->second)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidEntity);
        return result;
    }

    result.restored = true;
    result.restored_snapshot = registry_it->second;
    result.restored_snapshot.worldline_id = runtime_string_blank(request.target_worldline_id)
                                                ? registry_it->second.worldline_id
                                                : request.target_worldline_id;
    result.restored_snapshot.parent_worldline_id = registry_it->second.worldline_id;
    if (request.target_deterministic_seed != 0U) {
        result.restored_snapshot.deterministic_seed = request.target_deterministic_seed;
    }
    result.restored_snapshot.world_index = target_ref.world_index;
    result.restored_snapshot.entity_id = target_ref.entity_id;
    append_runtime_evidence_ref(result.restored_snapshot.evidence_refs,
                                std::string(kRuntimeCounterfactualRestoreEvidenceLabel));
    append_runtime_evidence_ref(result.restored_snapshot.evidence_refs,
                                "restore_barrier_id=" + request.restore_barrier_id);
    append_runtime_evidence_ref(result.restored_snapshot.evidence_refs,
                                "source_worldline_id=" + registry_it->second.worldline_id);
    append_runtime_evidence_ref(result.restored_snapshot.evidence_refs,
                                "target_worldline_id=" + result.restored_snapshot.worldline_id);
    register_counterfactual_worldline_snapshot(result.restored_snapshot);
    return result;
}

RuntimeCounterfactualBranchResult
RuntimeFacade::run_counterfactual_branch(const RuntimeCounterfactualBranchRequest &request) {
    RuntimeCounterfactualBranchResult result{};
    result.evidence_refs = request.evidence_refs;
    result.evidence_refs.push_back("RuntimeFacade.run_counterfactual_branch");

    if (request.allow_raw_authoritative_state_mutation) {
        result.rejection_reason = std::string(kRuntimeCounterfactualRawMutationRejection);
        return result;
    }
    if (runtime_string_blank(request.replay_envelope_id)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualMissingReplayEnvelope);
        return result;
    }
    if (runtime_string_blank(request.branch_point_id)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualMissingBranchPoint);
        return result;
    }

    result.fidelity_admission = admit_fidelity_request(request.fidelity_request);
    if (!result.fidelity_admission.admitted) {
        result.rejection_reason = std::string(kRuntimeCounterfactualUnsupportedFidelity);
        if (!result.fidelity_admission.rejection_reason.empty()) {
            result.evidence_refs.push_back("fidelity_rejection=" +
                                           result.fidelity_admission.rejection_reason);
        }
        return result;
    }

    const std::uint32_t seed =
        request.deterministic_seed == 0U
            ? 0U
            : static_cast<std::uint32_t>(request.deterministic_seed & 0xffffffffULL);
    BatchWorldSetupRequest setup = single_world_counterfactual_setup(request.baseline_setup, seed);

    RuntimeFacade parent(1);
    RuntimeFacade branch(1);
    const BatchWorldSetupResult parent_setup = parent.apply_world_setup(setup);
    const BatchWorldSetupResult branch_setup = branch.apply_world_setup(setup);

    WorldEntityRef parent_ref{
        .world_index = 0,
        .entity_id = counterfactual_spawned_entity_id(parent_setup, request.entity_ref),
    };
    WorldEntityRef branch_ref{
        .world_index = 0,
        .entity_id = counterfactual_spawned_entity_id(branch_setup, request.entity_ref),
    };
    if (parent_ref.entity_id == 0U || branch_ref.entity_id == 0U) {
        result.rejection_reason = std::string(kRuntimeCounterfactualSetupMissingEntity);
        return result;
    }

    std::vector<std::string> snapshot_evidence = result.evidence_refs;
    snapshot_evidence.push_back("replay_envelope_id=" + request.replay_envelope_id);
    snapshot_evidence.push_back("branch_point_id=" + request.branch_point_id);
    if (!request.parent_worldline_id.empty()) {
        snapshot_evidence.push_back("parent_worldline_id=" + request.parent_worldline_id);
    }
    if (!request.branch_worldline_id.empty()) {
        snapshot_evidence.push_back("branch_worldline_id=" + request.branch_worldline_id);
    }

    result.parent_snapshot = parent.snapshot_counterfactual_entity(
        parent_ref, result.fidelity_admission, request.cadence_reason, snapshot_evidence);
    result.parent_snapshot.worldline_id = runtime_string_blank(request.parent_worldline_id)
                                              ? "worldline:baseline"
                                              : request.parent_worldline_id;
    result.parent_snapshot.parent_worldline_id = result.parent_snapshot.worldline_id;
    result.parent_snapshot.deterministic_seed = request.deterministic_seed;
    parent.register_counterfactual_worldline_snapshot(result.parent_snapshot);
    branch.register_counterfactual_worldline_snapshot(result.parent_snapshot);

    RuntimeCounterfactualRestoreRequest restore_request{};
    restore_request.snapshot = result.parent_snapshot;
    restore_request.expected_worldline_id = result.parent_snapshot.worldline_id;
    restore_request.target_worldline_id = runtime_string_blank(request.branch_worldline_id)
                                              ? "worldline:branch"
                                              : request.branch_worldline_id;
    restore_request.target_deterministic_seed = request.deterministic_seed;
    restore_request.target_entity_ref = branch_ref;
    restore_request.restore_barrier_id = request.restore_barrier_id;
    restore_request.evidence_refs = result.evidence_refs;
    result.restore_result = branch.restore_counterfactual_snapshot(restore_request);
    if (!result.restore_result.restored) {
        result.rejection_reason = result.restore_result.rejection_reason;
        return result;
    }

    if (!branch.counterfactual_world_index_valid(branch_ref.world_index)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidWorld);
        return result;
    }
    if (!branch.apply_counterfactual_delta(branch_ref, request)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidEntity);
        return result;
    }

    result.branch_snapshot = branch.snapshot_counterfactual_entity(
        branch_ref, result.fidelity_admission, request.cadence_reason, snapshot_evidence);
    result.branch_snapshot.worldline_id = result.restore_result.restored_snapshot.worldline_id;
    result.branch_snapshot.parent_worldline_id =
        result.restore_result.restored_snapshot.parent_worldline_id;
    result.branch_snapshot.deterministic_seed =
        result.restore_result.restored_snapshot.deterministic_seed;
    branch.register_counterfactual_worldline_snapshot(result.branch_snapshot);
    result.comparison =
        compare_counterfactual_snapshots(result.parent_snapshot, result.branch_snapshot, request);
    result.admitted = result.comparison.comparable;
    if (!result.admitted) {
        result.rejection_reason = "counterfactual_worldline_comparison_not_comparable";
    }
    result.evidence_refs.insert(result.evidence_refs.end(),
                                result.restore_result.evidence_refs.begin(),
                                result.restore_result.evidence_refs.end());
    result.evidence_refs.insert(result.evidence_refs.end(), result.comparison.evidence_refs.begin(),
                                result.comparison.evidence_refs.end());
    register_counterfactual_worldline_snapshot(result.parent_snapshot);
    register_counterfactual_worldline_snapshot(result.branch_snapshot);
    return result;
}

RuntimeExperimentResult
RuntimeFacade::run_counterfactual_experiment(const RuntimeExperimentRequest &request) {
    RuntimeExperimentResult result{};
    result.evidence_refs = request.evidence_refs;
    append_runtime_evidence_ref(result.evidence_refs, std::string(kRuntimeExperimentEvidenceLabel));

    if (request.truth_claim) {
        result.rejection_reason = std::string(kRuntimeExperimentTruthClaimRejection);
        return result;
    }
    if (request.promoted_to_support) {
        result.rejection_reason = std::string(kRuntimeExperimentSupportPromotionRejection);
        return result;
    }

    result.branch_result = run_counterfactual_branch(request.branch_request);
    if (!result.branch_result.admitted) {
        result.rejection_reason = result.branch_result.rejection_reason.empty()
                                      ? std::string(kRuntimeExperimentBranchRejected)
                                      : result.branch_result.rejection_reason;
        return result;
    }

    RuntimeFacade parent(1);
    RuntimeFacade branch(1);
    parent.apply_world_setup(request.branch_request.baseline_setup);
    branch.apply_world_setup(request.branch_request.baseline_setup);

    if (!request.parent_step_requests.empty()) {
        parent.clear_execution_episode_batch();
        std::vector<WorldEntityRef> refs;
        std::vector<ExecutionEpisodeState> states;
        refs.reserve(request.parent_step_requests.size());
        states.reserve(request.parent_step_requests.size());
        ExecutionBatchStepRequest step_request{};
        for (const auto &item : request.parent_step_requests) {
            refs.push_back(WorldEntityRef{
                .world_index = item.request.world_index,
                .entity_id = item.request.entity_id,
            });
            states.push_back(item.state);
            step_request.step_requests.push_back(item.request);
        }
        parent.prime_execution_episode_batch(refs, states);
        result.parent_step_result = parent.step_execution_batch(step_request);
    }

    if (!request.branch_step_requests.empty()) {
        branch.clear_execution_episode_batch();
        std::vector<WorldEntityRef> refs;
        std::vector<ExecutionEpisodeState> states;
        refs.reserve(request.branch_step_requests.size());
        states.reserve(request.branch_step_requests.size());
        ExecutionBatchStepRequest step_request{};
        for (const auto &item : request.branch_step_requests) {
            refs.push_back(WorldEntityRef{
                .world_index = item.request.world_index,
                .entity_id = item.request.entity_id,
            });
            states.push_back(item.state);
            step_request.step_requests.push_back(item.request);
        }
        branch.prime_execution_episode_batch(refs, states);
        result.branch_step_result = branch.step_execution_batch(step_request);
    }

    if (request.include_observations) {
        const ObservationBatchRequest parent_obs_request{
            .refs =
                {
                    WorldEntityRef{
                        .world_index = result.branch_result.parent_snapshot.world_index,
                        .entity_id = result.branch_result.parent_snapshot.entity_id,
                    },
                },
        };
        const ObservationBatchRequest branch_obs_request{
            .refs =
                {
                    WorldEntityRef{
                        .world_index = result.branch_result.branch_snapshot.world_index,
                        .entity_id = result.branch_result.branch_snapshot.entity_id,
                    },
                },
        };
        result.parent_observation_packet = parent.export_observation_packet(parent_obs_request);
        result.branch_observation_packet = branch.export_observation_packet(branch_obs_request);
    }

    if (request.include_diagnostics_traces && !request.trace_ids.empty()) {
        EngagementBatchRequest parent_trace_request{};
        parent_trace_request.refs = {
            EngagementEntityRef{
                .world_index = result.branch_result.parent_snapshot.world_index,
                .entity_id = result.branch_result.parent_snapshot.entity_id,
            },
        };
        parent_trace_request.trace_ids = request.trace_ids;
        EngagementBatchRequest branch_trace_request{};
        branch_trace_request.refs = {
            EngagementEntityRef{
                .world_index = result.branch_result.branch_snapshot.world_index,
                .entity_id = result.branch_result.branch_snapshot.entity_id,
            },
        };
        branch_trace_request.trace_ids = request.trace_ids;
        result.parent_diagnostics_traces = parent.export_diagnostics_traces(parent_trace_request);
        result.branch_diagnostics_traces = branch.export_diagnostics_traces(branch_trace_request);
    }

    const std::vector<std::string> capability_refs = runtime_experiment_capability_refs(request);
    const auto replay_envelope = replay_envelope_from_experiment_request(request);
    const auto generated_input =
        scenario_generation_metadata_from_experiment_request(request, capability_refs);
    const auto admission =
        counterfactual_admission_from_experiment_request(request, capability_refs);
    const auto profile_refs =
        profile_observation_refs_from_experiment_request(request, result.branch_result);
    std::vector<std::string> bridge_evidence = result.evidence_refs;
    bridge_evidence.insert(bridge_evidence.end(), result.branch_result.evidence_refs.begin(),
                           result.branch_result.evidence_refs.end());
    if (!request.setup_ref.empty()) {
        append_runtime_evidence_ref(bridge_evidence, "setup_ref=" + request.setup_ref);
    }
    if (!request.generation_ref.empty()) {
        append_runtime_evidence_ref(bridge_evidence, "generation_ref=" + request.generation_ref);
    }

    const auto record = runtime::counterfactual::make_experiment_evidence_bridge_record(
        admission, replay_envelope, generated_input,
        request.experiment_run_id.empty() ? "experiment_run:runtime_facade.counterfactual"
                                          : request.experiment_run_id,
        request.comparison_id.empty() ? result.branch_result.comparison.comparison_id
                                      : request.comparison_id,
        profile_refs, bridge_evidence);
    const auto validation = runtime::counterfactual::validate_experiment_evidence_bridge_record(
        record, admission, replay_envelope, generated_input);

    result.ancestry.evidence_bridge_valid = validation.valid;
    result.ancestry.evidence_bridge_fail_closed = validation.fail_closed;
    result.ancestry.evidence_bridge_rejection_reason = validation.rejection_reason;
    result.ancestry.evidence_bridge_errors = validation.errors;
    result.ancestry.counterfactual_request_ref = admission.request_id;
    result.ancestry.counterfactual_admission_ref = admission.request_id;
    result.ancestry.setup_ref = request.setup_ref;
    result.ancestry.generation_ref = request.generation_ref;
    result.ancestry.replay_envelope_ref = admission.replay_envelope_id;
    result.ancestry.branch_point_ref = admission.branch_point_id;
    result.ancestry.generated_input_ref = generated_input.request.request_id;
    result.ancestry.backend_profile_ref = admission.backend_profile_ref;
    result.ancestry.fidelity_profile_ref = admission.fidelity_profile_ref;
    result.ancestry.capability_refs = admission.capability_refs;
    result.ancestry.evidence_refs =
        runtime::counterfactual::ordered_experiment_bridge_evidence_refs(record);
    for (const auto &profile_ref : profile_refs) {
        result.ancestry.profile_observation_refs.push_back(profile_ref.observation_ref);
    }

    if (!validation.valid) {
        result.rejection_reason = validation.rejection_reason;
        return result;
    }

    result.admitted = true;
    result.evidence_refs.insert(result.evidence_refs.end(), result.ancestry.evidence_refs.begin(),
                                result.ancestry.evidence_refs.end());
    return result;
}
