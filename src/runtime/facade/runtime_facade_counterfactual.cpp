#include "runtime/facade/runtime_facade_internal.h"

#include "components/basic/common.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/facade/runtime_window_coordinator.h"

#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
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
    for (auto &assignment : setup.sun_assignments) {
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
counterfactual_snapshot_from_runtime(const IWorldBatchBackend &runtime, const WorldEntityRef &ref,
                                     const RuntimeFidelityAdmission &fidelity_admission,
                                     const std::string &cadence_reason,
                                     std::vector<std::string> evidence_refs) {
    if (!valid_runtime_world_index(runtime, ref.world_index)) {
        throw std::out_of_range(std::string(kRuntimeCounterfactualInvalidWorld));
    }

    const ::runtime::backend::ExportResult exported =
        runtime.export_state(::runtime::backend::ExportRequest{
            .kinematics_ref = &ref,
            .include_kinematics = true,
        });
    if (exported.kinematics.empty() || !exported.kinematics.front().found) {
        throw std::runtime_error(std::string(kRuntimeCounterfactualInvalidEntity));
    }
    const ::runtime::backend::EntityKinematics &kinematics = exported.kinematics.front().state;

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
        refs.push_back(request.generation_ref.empty()
                           ? "generated_input:runtime_facade.counterfactual"
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
    metadata.request.contract_version = std::string(kScenarioGenerationContractVersionRequestV1);
    metadata.request.generation_kind = request.generated_input_kind.empty()
                                           ? std::string(kScenarioGenerationKindScenarioVariation)
                                           : request.generated_input_kind;
    metadata.request.source = request.generated_input_source.empty()
                                  ? std::string(kScenarioGenerationSourceCounterfactualBranch)
                                  : request.generated_input_source;
    metadata.request.generator_version =
        request.generated_input_generator_version.empty()
            ? "RuntimeFacade.run_counterfactual_experiment.counterfactual"
            : request.generated_input_generator_version;
    metadata.request.has_deterministic_seed = true;
    metadata.request.deterministic_seed = request.branch_request.deterministic_seed;
    metadata.request.baseline_scenario_ref =
        request.generated_input_baseline_scenario_ref.empty()
            ? (request.setup_ref.empty() ? "scenario:runtime_facade.counterfactual"
                                         : request.setup_ref)
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
    const runtime::backend::ExportResult exported =
        runtime_->export_state(runtime::backend::ExportRequest{
            .kinematics_ref = &ref,
            .include_kinematics = true,
        });
    if (exported.kinematics.empty() || !exported.kinematics.front().found) {
        return false;
    }
    runtime::backend::EntityKinematics state = exported.kinematics.front().state;

    state.x += request.mutation_dx;
    state.y += request.mutation_dy;
    state.z += request.mutation_dz;
    state.heading = Math::normalize_heading_deg(state.heading + request.mutation_dheading);
    state.vx += request.mutation_dvx;
    state.vy += request.mutation_dvy;
    state.vz += request.mutation_dvz;
    const runtime::backend::InputResult input_result =
        runtime_->inject(runtime::backend::InputBatch{
            .kinematics_write =
                runtime::backend::EntityKinematicsWrite{
                    .ref = ref,
                    .state = state,
                },
        });
    return input_result.kinematics_write_result.value_or(false);
}

bool RuntimeFacade::restore_counterfactual_entity(const WorldEntityRef &target_ref,
                                                  const RuntimeCounterfactualSnapshot &snapshot) {
    runtime::backend::EntityKinematics state{};
    state.x = snapshot.x;
    state.y = snapshot.y;
    state.z = snapshot.z;
    state.heading = Math::normalize_heading_deg(snapshot.heading);
    state.pitch = snapshot.pitch;
    state.roll = snapshot.roll;
    state.vx = snapshot.vx;
    state.vy = snapshot.vy;
    state.vz = snapshot.vz;
    const runtime::backend::InputResult input_result =
        runtime_->inject(runtime::backend::InputBatch{
            .kinematics_write =
                runtime::backend::EntityKinematicsWrite{
                    .ref = target_ref,
                    .state = state,
                },
        });
    return input_result.kinematics_write_result.value_or(false);
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

    const std::uint32_t seed =
        request.branch_request.deterministic_seed == 0U
            ? 0U
            : static_cast<std::uint32_t>(request.branch_request.deterministic_seed & 0xffffffffULL);
    const BatchWorldSetupRequest setup =
        single_world_counterfactual_setup(request.branch_request.baseline_setup, seed);

    RuntimeFacade parent(1);
    RuntimeFacade branch(1);
    const BatchWorldSetupResult parent_setup = parent.apply_world_setup(setup);
    const BatchWorldSetupResult branch_setup = branch.apply_world_setup(setup);
    const WorldEntityRef parent_ref{
        .world_index = 0,
        .entity_id =
            counterfactual_spawned_entity_id(parent_setup, request.branch_request.entity_ref),
    };
    const WorldEntityRef branch_ref{
        .world_index = 0,
        .entity_id =
            counterfactual_spawned_entity_id(branch_setup, request.branch_request.entity_ref),
    };
    if (parent_ref.entity_id == 0U || branch_ref.entity_id == 0U) {
        result.rejection_reason = std::string(kRuntimeCounterfactualSetupMissingEntity);
        return result;
    }
    if (!parent.restore_counterfactual_entity(parent_ref, result.branch_result.parent_snapshot) ||
        !branch.restore_counterfactual_entity(branch_ref, result.branch_result.branch_snapshot)) {
        result.rejection_reason = std::string(kRuntimeCounterfactualInvalidEntity);
        return result;
    }

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
                        .world_index = parent_ref.world_index,
                        .entity_id = parent_ref.entity_id,
                    },
                },
        };
        const ObservationBatchRequest branch_obs_request{
            .refs =
                {
                    WorldEntityRef{
                        .world_index = branch_ref.world_index,
                        .entity_id = branch_ref.entity_id,
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
                .world_index = parent_ref.world_index,
                .entity_id = parent_ref.entity_id,
            },
        };
        parent_trace_request.trace_ids = request.trace_ids;
        EngagementBatchRequest branch_trace_request{};
        branch_trace_request.refs = {
            EngagementEntityRef{
                .world_index = branch_ref.world_index,
                .entity_id = branch_ref.entity_id,
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

// T10 evidence spine, slice 5: maintained-run replay-envelope producer.
//
// Assembles a ReplayEnvelope from the REAL products of one maintained window
// (the RuntimeWindowResult the caller got back from run_window) rather than
// from request/snapshot fields the way the two synthetic assemblies above do
// (replay_envelope_from_experiment_request,
// runtime_counterfactual_restore_boundary_for_snapshot -- both unchanged).
// Field sources, the "replay:maintained:*" id namespace, the I59 opt-in truth
// linkage (window trace ids must have been minted by THIS facade's VA-8
// allocator), and the honest restore_unsupported claim are documented on the
// declaration in runtime_facade.h. Read-only: the method only peeks the
// allocator cursor (mints nothing), so it is idempotent and perturbs no
// existing serialized value.
runtime::counterfactual::MaintainedReplayEnvelopeResult
RuntimeFacade::build_maintained_replay_envelope(const RuntimeWindowResult &window_result,
                                                const std::string &run_id,
                                                const std::string &episode_id,
                                                std::uint64_t deterministic_seed,
                                                std::uint64_t run_snapshot_version) const {
    using namespace runtime::counterfactual;

    MaintainedReplayEnvelopeResult result{};

    // Provenance gate 0: only a RuntimeWindowResult returned by this facade's
    // run_window seam may enter the maintained evidence producers.  The
    // identity is opaque and is not a bound DTO field, so a hand-built result
    // cannot pass by copying a locally allocated numeric trace id; a result
    // returned by another facade is rejected even when both allocators are at
    // the same cursor (the common overlapping-id case).
    if (window_result.identity_token_.identity_ == nullptr) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowIdentityMissing);
        return result;
    }
    if (!runtime_window_result_belongs_to_this_facade(window_result)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowIdentityForeign);
        return result;
    }
    if (!runtime_window_result_evidence_matches_identity(window_result)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowEvidenceMismatch);
        return result;
    }

    // P5-A: replay admission consumes the immutable composition snapshot
    // sealed at window commit and compares it with the facade's currently
    // realized composition.  Resizing/reconfiguration, provider/profile/host
    // substitution, scope-generation drift, or a zero-world commit therefore
    // fails closed with named mismatch paths instead of silently replaying
    // under a different runtime identity.
    const RuntimeCompositionEvidenceComparison composition_comparison =
        runtime_window_composition_evidence_comparison(window_result);
    if (!composition_comparison.compatible) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeCompositionEvidenceMismatch);
        result.errors = composition_comparison.mismatches;
        return result;
    }

    // From this point on, assemble only from the immutable evidence sealed by
    // run_window. The public RuntimeWindowResult remains copyable for DTO
    // compatibility, but a copied token cannot authenticate substituted fields.
    const RuntimeWindowEvidenceSnapshot &sealed = window_result.identity_token_.identity_->evidence;

    if (runtime_string_blank(run_id)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeRunIdRequired);
        return result;
    }
    if (runtime_string_blank(episode_id)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeEpisodeIdRequired);
        return result;
    }

    // Real export provenance: the observation packet must carry the
    // run-produced id/version embedding strings ("obs:{n}" / "global:{n}",
    // apply_observation_packet_provenance). A default-constructed packet (no
    // export in this window) fails closed here.
    const InformationStateSource &observation_provenance = sealed.observation_provenance;
    if (observation_provenance.observation_packet_ids.empty() ||
        observation_provenance.source_observation_versions.empty() ||
        runtime_string_blank(observation_provenance.observation_packet_ids.front()) ||
        runtime_string_blank(observation_provenance.source_observation_versions.front())) {
        result.rejection_reason =
            std::string(kMaintainedReplayEnvelopeMissingObservationProvenance);
        return result;
    }

    // Real event tags: the engagement packet's trace_ids anchor the envelope's
    // event-order ref and the envelope id.
    const std::vector<std::uint64_t> &trace_ids = sealed.engagement_trace_ids;
    if (trace_ids.empty()) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeMissingTraceIds);
        return result;
    }

    // I59 opt-in truth linkage: every window trace id must have been minted by
    // THIS facade's VA-8 allocator (allocator sequences start at 1, so a
    // minted id is always in [1, peek_next_trace_id())). The default
    // maintained path's placeholder trace_ids = [1] against an untouched
    // allocator (peek == 1) fails exactly here, which is what makes this
    // producer meaningful only on the use_facade_evidence_producers=True
    // adapter path (or an equivalent allocator-stamping caller).
    const std::uint64_t next_unminted_trace_id = peek_next_trace_id();
    const bool all_trace_ids_run_minted =
        std::all_of(trace_ids.begin(), trace_ids.end(), [&](std::uint64_t trace_id) {
            return trace_id >= 1U && trace_id < next_unminted_trace_id;
        });
    if (!all_trace_ids_run_minted ||
        !runtime_window_trace_ids_recorded_by_this_window(window_result)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeTraceIdsNotRunMinted);
        return result;
    }

    // Real window barrier: the last "window_commit" record of the window's
    // own barrier trace (sequence + id are the run's actual barrier values).
    const RuntimeWindowBarrierRecord *window_commit_record = nullptr;
    for (const auto &record : sealed.barrier_trace) {
        if (record.barrier_id == kRuntimeWindowBarrierWindowCommit) {
            window_commit_record = &record;
        }
    }
    if (window_commit_record == nullptr) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeMissingWindowCommitBarrier);
        return result;
    }

    // Real producer node: the engagement packet's manifest-stamped export node
    // (apply_export_packet_metadata); blank means the run produced no export
    // provenance for the event order, so fail closed instead of inventing one.
    if (runtime_string_blank(sealed.engagement_producer_node_id)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeMissingProducerNode);
        return result;
    }

    if (!replay_contract_has_finite_time(sealed.source_time_s)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeSourceTimeNotFinite);
        return result;
    }

    // VA-2 snapshot identity. Default (run_snapshot_version == 0): the packet's
    // own per-export provenance string, byte-identical to the pre-slice value.
    // Opt-in: qualify it with the run-global monotone version, which must have
    // been minted by THIS facade's VA-2 allocator -- so an arbitrary caller
    // number cannot become the envelope's snapshot identity.
    std::string snapshot_version_ref = observation_provenance.source_observation_versions.front();
    if (run_snapshot_version != 0) {
        if (run_snapshot_version >= peek_next_run_snapshot_version() ||
            !runtime_window_snapshot_recorded_by_this_window(window_result, run_snapshot_version)) {
            result.rejection_reason = std::string(kMaintainedReplayEnvelopeRunSnapshotNotRunMinted);
            return result;
        }
        snapshot_version_ref += std::string(kMaintainedReplayEnvelopeRunSnapshotInfix) +
                                std::to_string(run_snapshot_version);
    }

    const std::uint64_t anchor_trace_id = trace_ids.back();
    ReplayEnvelope envelope{
        // "replay:maintained:*" namespace -- disjoint from the snapshot-derived
        // "replay:facade:*" restore-boundary space and from caller-authored
        // spaces (see the declaration comment in runtime_facade.h).
        .replay_envelope_id =
            "replay:maintained:" + run_id + ":trace:" + std::to_string(anchor_trace_id),
        .run_id = run_id,
        .episode_id = episode_id,
        .has_deterministic_seed = true,
        .deterministic_seed = deterministic_seed,
        .has_source_time = true,
        .source_time_s = sealed.source_time_s,
        .snapshot_ref =
            ReplaySnapshotRef{
                // The run-produced "global:{snapshot_version}" string carried
                // on the real observation packet, optionally qualified with the
                // run-global monotone VA-2 version (see the declaration).
                .snapshot_version_ref = snapshot_version_ref,
            },
        .barrier_ref =
            ReplayBarrierRef{
                .barrier_id = window_commit_record->barrier_id,
                .barrier_sequence = window_commit_record->sequence,
                .barrier_detail = sealed.engagement_barrier_detail,
            },
        .event_order_ref =
            ReplayEventOrderRef{
                .sort_key = std::string(kDeterministicReplayEventOrderSortKey),
                // "event:trace:{id}" embeds the run-minted VA-8 trace id tail
                // (textual uint64-into-string embedding per the T10 glossary).
                .event_id = "event:trace:" + std::to_string(anchor_trace_id),
                .producer_node_id = sealed.engagement_producer_node_id,
            },
        .facade_provenance_ref =
            ReplayFacadeProvenanceRef{
                // The run-produced "obs:{snapshot_version}" packet id string.
                .packet_ref = observation_provenance.observation_packet_ids.front(),
                .packet_kind = "ObservationBatchPacket",
                // The real packet's own provenance struct (WP11 label plus the
                // run-produced id/version lists), not a fresh synthetic label.
                .information_state_source = observation_provenance,
            },
        // Honest restore claim: the maintained window registers no
        // counterfactual worldline snapshot, so restore support stays
        // unclaimed behind the fail-closed boundary.
        .snapshot_restore_supported = false,
        .restore_support_boundary = std::string(kReplayRestoreSupportBoundaryUnsupported),
    };

    const ReplayContractValidationResult validation = validate_replay_envelope(envelope);
    if (!validation.valid) {
        result.rejection_reason = validation.rejection_reason;
        result.errors = validation.errors;
        return result;
    }

    result.admitted = true;
    result.envelope = std::move(envelope);
    result.evidence_refs.push_back(std::string(kMaintainedReplayEnvelopeProducerEvidenceLabel));
    const std::vector<std::string> ordered_refs =
        ordered_replay_envelope_evidence_refs(result.envelope);
    result.evidence_refs.insert(result.evidence_refs.end(), ordered_refs.begin(),
                                ordered_refs.end());
    result.evidence_refs.push_back(
        "composition_evidence_sha256=" +
        window_result.identity_token_.identity_->composition_evidence.evidence.evidence_sha256);
    return result;
}

// T10 evidence spine, slice 6A (this iteration): maintained engagement-packet
// ancestry producer. Contract, gate order, and the root/parent semantics are
// documented on the declaration in runtime_facade.h; the fail-closed reason
// strings live in runtime_facade_internal.h (kMaintainedPacketAncestry*).
// Read-only like the slice-5 producer: it peeks the VA-8 cursor (via the
// internal envelope build and the parent admission check) and mints nothing,
// so calling it is idempotent and perturbs no existing serialized value.
MaintainedPacketAncestryResult RuntimeFacade::build_maintained_packet_ancestry(
    const RuntimeWindowResult &window_result, const std::string &run_id,
    const std::string &episode_id, std::uint64_t deterministic_seed,
    std::uint64_t parent_trace_id) const {
    using runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef;

    MaintainedPacketAncestryResult result{};

    // Keep the window/facade association explicit at this producer boundary as
    // well as in the replay-envelope producer below.  This prevents a future
    // refactor from accidentally bypassing the identity gate while retaining
    // the same fail-closed reasons for synthetic and foreign windows.
    if (window_result.identity_token_.identity_ == nullptr) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowIdentityMissing);
        return result;
    }
    if (!runtime_window_result_belongs_to_this_facade(window_result)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowIdentityForeign);
        return result;
    }
    if (!runtime_window_result_evidence_matches_identity(window_result)) {
        result.rejection_reason = std::string(kMaintainedReplayEnvelopeWindowEvidenceMismatch);
        return result;
    }

    // Gate 1: the same window must assemble an ADMITTED maintained replay
    // envelope. This reuses all nine slice-5 real-evidence gates (run/episode
    // id, real export provenance, VA-8 trace-id admission -- the gate that
    // fail-closes foreign-facade and default-placeholder evidence -- window
    // barrier, producer node, finite time) plus validate_replay_envelope, and
    // binds the ancestry to a validator-accepted envelope id. Default VA-2
    // qualification (run_snapshot_version = 0) keeps the envelope's snapshot
    // ref byte-identical to the slice-5 default.
    const runtime::counterfactual::MaintainedReplayEnvelopeResult envelope_result =
        build_maintained_replay_envelope(window_result, run_id, episode_id, deterministic_seed);
    if (!envelope_result.admitted) {
        result.rejection_reason = envelope_result.rejection_reason;
        result.errors = envelope_result.errors;
        return result;
    }

    // Non-empty and all run-minted: gate 1 admitted them.
    const RuntimeWindowEvidenceSnapshot &sealed = window_result.identity_token_.identity_->evidence;
    const std::vector<std::uint64_t> &window_trace_tags = sealed.engagement_trace_ids;
    const std::uint64_t anchor_trace_id = window_trace_tags.back();

    // Gates 2 + 3: parent linkage must come from THIS facade's VA-8 allocator,
    // point strictly backwards (below every window tag), and name an anchor
    // recorded by an earlier genuine window. Keep the numeric chronology gate
    // before the registry gate so a self/forward parent retains its dedicated
    // rejection reason even though it cannot be an earlier recorded anchor.
    if (parent_trace_id != 0U) {
        if (parent_trace_id >= peek_next_trace_id()) {
            result.rejection_reason = std::string(kMaintainedPacketAncestryParentNotRunMinted);
            return result;
        }
        const std::uint64_t window_min_trace_tag =
            *std::min_element(window_trace_tags.begin(), window_trace_tags.end());
        if (parent_trace_id >= window_min_trace_tag) {
            result.rejection_reason = std::string(kMaintainedPacketAncestryParentNotBeforeWindow);
            return result;
        }
        if (!runtime_window_parent_trace_recorded_before_this_window(window_result,
                                                                     parent_trace_id)) {
            result.rejection_reason = std::string(kMaintainedPacketAncestryParentNotRunMinted);
            return result;
        }
    }

    // Gate 4: the packet family must actually carry exported traces, and at
    // least one must be tagged with a run-minted packet tag. Kernel-space
    // trace ids are value-indistinguishable from VA-8 ids (census VA-8), so
    // membership in the admitted tag set is the discriminator.
    const std::vector<DiagnosticsTrace> &window_traces = sealed.diagnostics_traces;
    if (window_traces.empty()) {
        result.rejection_reason = std::string(kMaintainedPacketAncestryMissingDiagnosticsTraces);
        return result;
    }
    const auto is_run_minted_tag = [&window_trace_tags](std::uint64_t trace_id) {
        return std::find(window_trace_tags.begin(), window_trace_tags.end(), trace_id) !=
               window_trace_tags.end();
    };
    std::uint64_t linked_trace_count = 0;
    for (const auto &trace : window_traces) {
        if (is_run_minted_tag(trace.trace_id)) {
            ++linked_trace_count;
        }
    }
    if (linked_trace_count == 0U) {
        result.rejection_reason = std::string(kMaintainedPacketAncestryNoRunMintedTraces);
        return result;
    }

    // Populate: parent-linked COPIES only. The window product is const and
    // never mutated; copies whose trace_id is a run-minted packet tag carry
    // the ancestry parent, kernel-space copies stay untouched, and at the
    // root (parent_trace_id == 0) every copy keeps the pre-slice default 0.
    MaintainedEngagementPacketAncestry ancestry{};
    ancestry.packet_ancestry_id = std::string(kMaintainedPacketAncestryIdPrefix) + run_id +
                                  ":trace:" + std::to_string(anchor_trace_id);
    ancestry.run_id = run_id;
    ancestry.episode_id = episode_id;
    ancestry.anchor_trace_id = anchor_trace_id;
    ancestry.parent_trace_id = parent_trace_id;
    ancestry.replay_envelope_ref = envelope_result.envelope.replay_envelope_id;
    ancestry.parent_event_order_ref =
        parent_trace_id == 0U ? std::string() : "event:trace:" + std::to_string(parent_trace_id);
    ancestry.ancestral_traces = window_traces;
    if (parent_trace_id != 0U) {
        for (auto &trace : ancestry.ancestral_traces) {
            if (is_run_minted_tag(trace.trace_id)) {
                trace.parent_trace_id = parent_trace_id;
            }
        }
    }

    // Typed lineage refs (VA-5 vocabulary: ref_id / evidence_kind /
    // provenance_label): the validated envelope, this window's anchor, and the
    // parent edge when linked. Deterministic order.
    ancestry.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
        .ref_id = ancestry.replay_envelope_ref,
        .evidence_kind =
            std::string(runtime::counterfactual::kScenarioGenerationEvidenceKindReplayEnvelope),
        .provenance_label = "replay",
    });
    ancestry.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
        .ref_id = "event:trace:" + std::to_string(anchor_trace_id),
        .evidence_kind = std::string(kMaintainedPacketAncestryEvidenceKindAnchorTrace),
        .provenance_label = "anchor",
    });
    if (parent_trace_id != 0U) {
        ancestry.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
            .ref_id = ancestry.parent_event_order_ref,
            .evidence_kind = std::string(kMaintainedPacketAncestryEvidenceKindParentTrace),
            .provenance_label = "parent",
        });
    }

    result.admitted = true;
    result.ancestry = std::move(ancestry);
    result.evidence_refs.push_back(std::string(kMaintainedPacketAncestryProducerEvidenceLabel));
    result.evidence_refs.push_back("packet_ancestry_id=" + result.ancestry.packet_ancestry_id);
    result.evidence_refs.push_back("replay_envelope_ref=" + result.ancestry.replay_envelope_ref);
    result.evidence_refs.push_back("anchor_trace_id=" + std::to_string(anchor_trace_id));
    if (parent_trace_id != 0U) {
        result.evidence_refs.push_back("parent_trace_id=" + std::to_string(parent_trace_id));
    }
    result.evidence_refs.push_back("linked_trace_count=" + std::to_string(linked_trace_count));
    return result;
}

// T10 evidence spine, slice 7 (this iteration): maintained worldline /
// counterfactual comparison producer. Contract, gate order, the worldline
// semantics, and the no-truth-promotion red line are documented on the
// declaration in runtime_facade.h; the fail-closed reason strings live in
// runtime_facade_internal.h (kMaintainedWorldlineComparison*). Read-only like
// the slice-5/6A producers it consumes: every inner call only peeks the
// allocator cursors and mints nothing, no counterfactual worldline snapshot
// is registered, so calling it is idempotent and perturbs no existing
// serialized value. (Each side's ancestry build re-runs that side's envelope
// build internally; both are deterministic over the same const inputs, so the
// ancestry's replay_envelope_ref equals the directly built envelope id by
// construction.)
MaintainedWorldlineComparisonResult RuntimeFacade::build_maintained_worldline_comparison(
    const RuntimeWindowResult &baseline_window_result,
    const RuntimeWindowResult &candidate_window_result, const std::string &run_id,
    const std::string &episode_id, std::uint64_t baseline_deterministic_seed,
    std::uint64_t candidate_deterministic_seed, std::uint64_t baseline_parent_trace_id,
    std::uint64_t candidate_parent_trace_id) const {
    using runtime::counterfactual::MaintainedReplayEnvelopeResult;
    using runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef;

    MaintainedWorldlineComparisonResult result{};

    // Side-naming rejection wrapper: the comparison-level reason names the
    // failed side/surface; the underlying slice-5/6A reason (and its errors)
    // go to result.errors so nothing is lost and nothing half-real leaks.
    const auto reject_side = [&result](std::string_view comparison_reason,
                                       const std::string &inner_reason,
                                       const std::vector<std::string> &inner_errors) {
        result.rejection_reason = std::string(comparison_reason);
        if (!inner_reason.empty()) {
            result.errors.push_back(inner_reason);
        }
        result.errors.insert(result.errors.end(), inner_errors.begin(), inner_errors.end());
    };

    // Gates 1 + 2: both windows admit a maintained replay envelope in strict
    // baseline-then-candidate order.  The replay producer owns the opaque
    // window/facade identity gate as well as the remaining slice-5
    // real-evidence gates, so this comparison cannot bypass provenance while
    // preserving side-specific error attribution.
    const MaintainedReplayEnvelopeResult baseline_envelope = build_maintained_replay_envelope(
        baseline_window_result, run_id, episode_id, baseline_deterministic_seed);
    if (!baseline_envelope.admitted) {
        reject_side(kMaintainedWorldlineComparisonBaselineEnvelopeRejected,
                    baseline_envelope.rejection_reason, baseline_envelope.errors);
        return result;
    }
    const MaintainedReplayEnvelopeResult candidate_envelope = build_maintained_replay_envelope(
        candidate_window_result, run_id, episode_id, candidate_deterministic_seed);
    if (!candidate_envelope.admitted) {
        reject_side(kMaintainedWorldlineComparisonCandidateEnvelopeRejected,
                    candidate_envelope.rejection_reason, candidate_envelope.errors);
        return result;
    }

    // Gates 3 + 4: both windows admit a maintained packet ancestry (slice-6A
    // parent gates guard each side's lineage contribution).
    const MaintainedPacketAncestryResult baseline_ancestry =
        build_maintained_packet_ancestry(baseline_window_result, run_id, episode_id,
                                         baseline_deterministic_seed, baseline_parent_trace_id);
    if (!baseline_ancestry.admitted) {
        reject_side(kMaintainedWorldlineComparisonBaselineAncestryRejected,
                    baseline_ancestry.rejection_reason, baseline_ancestry.errors);
        return result;
    }
    const MaintainedPacketAncestryResult candidate_ancestry =
        build_maintained_packet_ancestry(candidate_window_result, run_id, episode_id,
                                         candidate_deterministic_seed, candidate_parent_trace_id);
    if (!candidate_ancestry.admitted) {
        reject_side(kMaintainedWorldlineComparisonCandidateAncestryRejected,
                    candidate_ancestry.rejection_reason, candidate_ancestry.errors);
        return result;
    }

    // Gate 5: distinct anchors -- a window joined against itself is not a
    // worldline comparison, and identical anchors would collapse the two
    // worldline ids into one.
    const std::uint64_t baseline_anchor = baseline_ancestry.ancestry.anchor_trace_id;
    const std::uint64_t candidate_anchor = candidate_ancestry.ancestry.anchor_trace_id;
    if (baseline_anchor == candidate_anchor) {
        result.rejection_reason = std::string(kMaintainedWorldlineComparisonAnchorsNotDistinct);
        return result;
    }

    // Populate: evidence ids only (no truth-state copy anywhere below).
    MaintainedWorldlineComparison comparison{};
    comparison.comparison_id = std::string(kMaintainedWorldlineComparisonIdPrefix) + run_id +
                               ":trace:" + std::to_string(baseline_anchor) +
                               ":vs:" + std::to_string(candidate_anchor);
    comparison.run_id = run_id;
    comparison.episode_id = episode_id;
    comparison.baseline_worldline_id =
        std::string(kMaintainedWorldlineComparisonWorldlineIdPrefix) + run_id +
        ":trace:" + std::to_string(baseline_anchor);
    comparison.candidate_worldline_id =
        std::string(kMaintainedWorldlineComparisonWorldlineIdPrefix) + run_id +
        ":trace:" + std::to_string(candidate_anchor);
    comparison.baseline_anchor_trace_id = baseline_anchor;
    comparison.candidate_anchor_trace_id = candidate_anchor;
    comparison.baseline_replay_envelope_ref = baseline_envelope.envelope.replay_envelope_id;
    comparison.candidate_replay_envelope_ref = candidate_envelope.envelope.replay_envelope_id;
    comparison.baseline_packet_ancestry_ref = baseline_ancestry.ancestry.packet_ancestry_id;
    comparison.candidate_packet_ancestry_ref = candidate_ancestry.ancestry.packet_ancestry_id;
    comparison.baseline_event_order_ref = baseline_envelope.envelope.event_order_ref.event_id;
    comparison.candidate_event_order_ref = candidate_envelope.envelope.event_order_ref.event_id;
    comparison.baseline_snapshot_version_ref =
        baseline_envelope.envelope.snapshot_ref.snapshot_version_ref;
    comparison.candidate_snapshot_version_ref =
        candidate_envelope.envelope.snapshot_ref.snapshot_version_ref;
    comparison.baseline_deterministic_seed = baseline_deterministic_seed;
    comparison.candidate_deterministic_seed = candidate_deterministic_seed;
    comparison.deterministic_seed_matched =
        baseline_deterministic_seed == candidate_deterministic_seed;
    comparison.claim_scope =
        std::string(runtime::counterfactual::kExperimentProfileClaimScopeComparative);
    comparison.truth_claim = false;
    comparison.promoted_to_support = false;

    // Typed lineage refs (VA-5 vocabulary): envelope + ancestry + anchor per
    // side. Deterministic order, baseline first.
    const auto push_side_lineage = [&comparison](const std::string &envelope_ref,
                                                 const std::string &ancestry_ref,
                                                 const std::string &event_order_ref,
                                                 const char *side_label) {
        comparison.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
            .ref_id = envelope_ref,
            .evidence_kind =
                std::string(runtime::counterfactual::kScenarioGenerationEvidenceKindReplayEnvelope),
            .provenance_label = side_label,
        });
        comparison.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
            .ref_id = ancestry_ref,
            .evidence_kind = std::string(kMaintainedWorldlineComparisonEvidenceKindPacketAncestry),
            .provenance_label = side_label,
        });
        comparison.lineage_refs.push_back(ScenarioGenerationEvidenceMetadataRef{
            .ref_id = event_order_ref,
            .evidence_kind = std::string(kMaintainedPacketAncestryEvidenceKindAnchorTrace),
            .provenance_label = side_label,
        });
    };
    push_side_lineage(comparison.baseline_replay_envelope_ref,
                      comparison.baseline_packet_ancestry_ref, comparison.baseline_event_order_ref,
                      "baseline");
    push_side_lineage(comparison.candidate_replay_envelope_ref,
                      comparison.candidate_packet_ancestry_ref,
                      comparison.candidate_event_order_ref, "candidate");

    result.admitted = true;
    result.comparison = std::move(comparison);
    result.evidence_refs.push_back(
        std::string(kMaintainedWorldlineComparisonProducerEvidenceLabel));
    result.evidence_refs.push_back("comparison_id=" + result.comparison.comparison_id);
    result.evidence_refs.push_back("baseline_replay_envelope_ref=" +
                                   result.comparison.baseline_replay_envelope_ref);
    result.evidence_refs.push_back("candidate_replay_envelope_ref=" +
                                   result.comparison.candidate_replay_envelope_ref);
    result.evidence_refs.push_back("baseline_packet_ancestry_ref=" +
                                   result.comparison.baseline_packet_ancestry_ref);
    result.evidence_refs.push_back("candidate_packet_ancestry_ref=" +
                                   result.comparison.candidate_packet_ancestry_ref);
    result.evidence_refs.push_back(
        std::string("deterministic_seed_matched=") +
        (result.comparison.deterministic_seed_matched ? "true" : "false"));
    return result;
}
