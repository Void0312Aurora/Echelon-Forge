#pragma once

#include "runtime/facade/runtime_facade.h"

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/stage_node_manifest_registry.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <vector>

namespace runtime_facade_internal {

using runtime::scheduler::find_stage_node_manifest;

inline std::vector<WorldEntityRef>
refs_from_step_requests(const std::vector<WorldExecutionEpisodeStepRequest> &requests) {
    std::vector<WorldEntityRef> refs;
    refs.reserve(requests.size());
    for (const auto &request : requests) {
        refs.push_back(WorldEntityRef{
            .world_index = request.world_index,
            .entity_id = request.entity_id,
        });
    }
    return refs;
}

inline std::vector<WorldEntityRef>
world_refs_from_engagement_refs(const std::vector<EngagementEntityRef> &refs) {
    std::vector<WorldEntityRef> out;
    out.reserve(refs.size());
    for (const auto &ref : refs) {
        out.push_back(WorldEntityRef{
            .world_index = ref.world_index,
            .entity_id = ref.entity_id,
        });
    }
    return out;
}

inline bool valid_runtime_world_index(const WorldBatchRuntime &runtime, std::uint64_t world_index) {
    return world_index < runtime.world_count();
}

inline constexpr std::string_view kObservationExportNodeId = "observation_export.v1";
inline constexpr std::string_view kLaunchNodeId = "fire_control_launch.v1";
inline constexpr std::string_view kEffectsDamageNodeId = "effects_damage.v1";
inline constexpr std::string_view kExportBarrierId = "export";
inline constexpr std::string_view kExportBarrierDetail = "maintained_facade_export";
inline constexpr std::uint64_t kExportBarrierSequence = 1;
inline constexpr std::string_view kObservationPacketIdPrefix = "obs:";
inline constexpr std::string_view kEngagementPacketIdPrefix = "eng:";
inline constexpr std::string_view kDiagnosticsPacketIdPrefix = "diag:";
inline constexpr std::string_view kMaintainedBaselineBackendProfileId = "cpu_exact.reference";
inline constexpr std::string_view kMaintainedBaselineParityBudgetRef =
    "parity_budget.cpu_exact.reference.v1";
inline constexpr std::string_view kMaintainedBaselineProfileStatus = "maintained_exact_baseline";
inline constexpr std::string_view kDeviceObservationViewCandidateProfileId =
    "gpu_helpers.diagnostics_only";
inline constexpr std::string_view kDeviceObservationViewRejectionReason =
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile";
inline constexpr std::string_view kExactGpuBackendCandidateProfileId =
    "gpu_exact.unmaintained_candidate";
inline constexpr std::string_view kExactGpuBackendRejectionReason =
    "gpu_exact.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kResidentStateCandidateProfileId =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kResidentStateCandidateParityBudgetRef =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kResidentStateRejectionReason =
    "resident_state.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kShadowCompareCandidateProfileId =
    "shadow_compare.unmaintained_candidate";
inline constexpr std::string_view kShadowCompareCandidateParityBudgetRef =
    "parity_budget.shadow_compare.unmaintained_candidate.v1";
inline constexpr std::string_view kShadowCompareRejectionReason =
    "shadow_compare.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kMultiFidelityRejectionReason =
    "multi_fidelity_profiles_require_a_maintained_registry_revision_and_acceptance_gate";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyNone = "none";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyReferenceCpu = "reference_cpu";
inline constexpr std::string_view kRuntimeCounterfactualSelectedSliceBarrierId =
    "counterfactual_selected_slice";
inline constexpr std::uint64_t kRuntimeCounterfactualSelectedSliceSnapshotVersion = 1;
inline constexpr std::string_view kRuntimeCounterfactualRawMutationRejection =
    "counterfactual_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kRuntimeCounterfactualRestoreRawMutationRejection =
    "counterfactual_restore_raw_authoritative_state_mutation_forbidden";
inline constexpr std::string_view kRuntimeCounterfactualMissingReplayEnvelope =
    "counterfactual_replay_envelope_id_required";
inline constexpr std::string_view kRuntimeCounterfactualMissingBranchPoint =
    "counterfactual_branch_point_id_required";
inline constexpr std::string_view kRuntimeCounterfactualUnsupportedFidelity =
    "counterfactual_fidelity_request_not_admitted";
inline constexpr std::string_view kRuntimeCounterfactualInvalidWorld =
    "counterfactual_world_index_out_of_range";
inline constexpr std::string_view kRuntimeCounterfactualInvalidEntity =
    "counterfactual_entity_missing_transform_or_velocity";
inline constexpr std::string_view kRuntimeCounterfactualSetupMissingEntity =
    "counterfactual_baseline_setup_entity_missing";
inline constexpr std::string_view kRuntimeCounterfactualMissingWorldlineId =
    "counterfactual_worldline_id_required";
inline constexpr std::string_view kRuntimeCounterfactualInvalidWorldlineId =
    "counterfactual_worldline_id_not_registered";
inline constexpr std::string_view kRuntimeCounterfactualWorldlineMismatch =
    "counterfactual_worldline_id_mismatch";
inline constexpr std::string_view kRuntimeCounterfactualRestoreBarrierMismatch =
    "counterfactual_restore_barrier_id_mismatch";
inline constexpr std::string_view kRuntimeCounterfactualRestoreResidentStateRejection =
    "counterfactual_restore_resident_state_not_supported";
inline constexpr std::string_view kRuntimeCounterfactualRestoreExactGpuRejection =
    "counterfactual_restore_exact_gpu_not_supported";
inline constexpr std::string_view kRuntimeCounterfactualRestoreFullCloneRejection =
    "counterfactual_restore_full_clone_not_supported";
inline constexpr std::string_view kRuntimeCounterfactualRestoreBoundaryRejection =
    "counterfactual_restore_boundary_not_supported";
inline constexpr std::string_view kRuntimeCounterfactualRestoreEvidenceLabel =
    "RuntimeFacade.restore_counterfactual_snapshot";
inline constexpr std::string_view kRuntimeCounterfactualRegisterEvidenceLabel =
    "RuntimeFacade.register_counterfactual_worldline_snapshot";
inline constexpr std::string_view kRuntimeExperimentEvidenceLabel =
    "RuntimeFacade.run_counterfactual_experiment";
inline constexpr std::string_view kRuntimeExperimentTruthClaimRejection =
    "counterfactual_experiment_truth_claim_forbidden";
inline constexpr std::string_view kRuntimeExperimentSupportPromotionRejection =
    "counterfactual_experiment_support_promotion_forbidden";
inline constexpr std::string_view kRuntimeExperimentBranchRejected =
    "counterfactual_experiment_branch_rejected";
// T10 slice 5: fail-closed rejection reasons of the maintained-run
// replay-envelope producer (RuntimeFacade::build_maintained_replay_envelope).
inline constexpr std::string_view kMaintainedReplayEnvelopeRunIdRequired =
    "maintained_replay_envelope_run_id_required";
inline constexpr std::string_view kMaintainedReplayEnvelopeEpisodeIdRequired =
    "maintained_replay_envelope_episode_id_required";
inline constexpr std::string_view kMaintainedReplayEnvelopeMissingObservationProvenance =
    "maintained_replay_envelope_observation_packet_provenance_missing";
inline constexpr std::string_view kMaintainedReplayEnvelopeMissingTraceIds =
    "maintained_replay_envelope_engagement_trace_ids_missing";
inline constexpr std::string_view kMaintainedReplayEnvelopeTraceIdsNotRunMinted =
    "maintained_replay_envelope_trace_ids_not_minted_by_this_run";
inline constexpr std::string_view kMaintainedReplayEnvelopeMissingWindowCommitBarrier =
    "maintained_replay_envelope_window_commit_barrier_missing";
inline constexpr std::string_view kMaintainedReplayEnvelopeMissingProducerNode =
    "maintained_replay_envelope_engagement_producer_node_missing";
inline constexpr std::string_view kMaintainedReplayEnvelopeSourceTimeNotFinite =
    "maintained_replay_envelope_source_time_not_finite";
inline constexpr std::string_view kMaintainedReplayEnvelopeRunSnapshotNotRunMinted =
    "maintained_replay_envelope_run_snapshot_version_not_minted_by_this_run";
inline constexpr std::string_view kMaintainedReplayEnvelopeProducerEvidenceLabel =
    "RuntimeFacade.build_maintained_replay_envelope";
// T10 slice 5 / VA-2: infix joining the observation packet's per-export
// provenance string to the run-global monotone snapshot version, used only on
// the opt-in run-global qualification path (default off keeps the packet string
// byte-identical).
inline constexpr std::string_view kMaintainedReplayEnvelopeRunSnapshotInfix = ":run_snapshot:";
// T10 slice 6A (this iteration): fail-closed rejection reasons and evidence
// vocabulary of the maintained engagement-packet ancestry producer
// (RuntimeFacade::build_maintained_packet_ancestry). The producer reuses the
// slice-5 envelope gates verbatim (their kMaintainedReplayEnvelope* reasons
// propagate unchanged), so only the ancestry-specific gates are named here.
inline constexpr std::string_view kMaintainedPacketAncestryParentNotRunMinted =
    "maintained_packet_ancestry_parent_trace_id_not_minted_by_this_run";
inline constexpr std::string_view kMaintainedPacketAncestryParentNotBeforeWindow =
    "maintained_packet_ancestry_parent_trace_id_not_before_window_traces";
inline constexpr std::string_view kMaintainedPacketAncestryMissingDiagnosticsTraces =
    "maintained_packet_ancestry_window_diagnostics_traces_missing";
inline constexpr std::string_view kMaintainedPacketAncestryNoRunMintedTraces =
    "maintained_packet_ancestry_no_window_trace_carries_a_run_minted_tag";
inline constexpr std::string_view kMaintainedPacketAncestryProducerEvidenceLabel =
    "RuntimeFacade.build_maintained_packet_ancestry";
// Typed-ref lineage vocabulary (VA-5): evidence kinds carried on the ancestry
// result's ScenarioGenerationEvidenceMetadataRef entries. The replay-envelope
// entry reuses the contract-owned kScenarioGenerationEvidenceKindReplayEnvelope;
// these two name the trace-id edges the ancestry adds.
inline constexpr std::string_view kMaintainedPacketAncestryEvidenceKindAnchorTrace = "anchor_trace";
inline constexpr std::string_view kMaintainedPacketAncestryEvidenceKindParentTrace = "parent_trace";
// "ancestry:maintained:*" id namespace; disjoint from "replay:maintained:*"
// (slice 5), "replay:facade:*" (restore boundary), and caller-authored spaces.
inline constexpr std::string_view kMaintainedPacketAncestryIdPrefix = "ancestry:maintained:";
// T10 slice 7 (this iteration): fail-closed rejection reasons and evidence
// vocabulary of the maintained worldline/counterfactual comparison producer
// (RuntimeFacade::build_maintained_worldline_comparison). The producer reuses
// the slice-5 envelope gates and slice-6A ancestry gates per side; their
// underlying reasons are carried in the result's `errors` behind these
// side-naming wrappers (two windows make verbatim propagation ambiguous).
inline constexpr std::string_view kMaintainedWorldlineComparisonBaselineEnvelopeRejected =
    "maintained_worldline_comparison_baseline_envelope_rejected";
inline constexpr std::string_view kMaintainedWorldlineComparisonCandidateEnvelopeRejected =
    "maintained_worldline_comparison_candidate_envelope_rejected";
inline constexpr std::string_view kMaintainedWorldlineComparisonBaselineAncestryRejected =
    "maintained_worldline_comparison_baseline_ancestry_rejected";
inline constexpr std::string_view kMaintainedWorldlineComparisonCandidateAncestryRejected =
    "maintained_worldline_comparison_candidate_ancestry_rejected";
inline constexpr std::string_view kMaintainedWorldlineComparisonAnchorsNotDistinct =
    "maintained_worldline_comparison_windows_share_the_anchor_trace";
inline constexpr std::string_view kMaintainedWorldlineComparisonProducerEvidenceLabel =
    "RuntimeFacade.build_maintained_worldline_comparison";
// Typed-ref lineage vocabulary (VA-5): the envelope entries reuse the
// contract-owned kScenarioGenerationEvidenceKindReplayEnvelope and the anchor
// entries reuse kMaintainedPacketAncestryEvidenceKindAnchorTrace; this one
// names the slice-6A ancestry ids the comparison consumes.
inline constexpr std::string_view kMaintainedWorldlineComparisonEvidenceKindPacketAncestry =
    "packet_ancestry";
// "comparison:maintained:*" and "worldline:maintained:*" id namespaces;
// disjoint from the raw-facade "counterfactual:selected_slice*" comparison
// ids, the registered "worldline:runtime:*"/"worldline:baseline"/
// "worldline:branch" spaces, "replay:maintained:*", "ancestry:maintained:*",
// and caller-authored spaces. Verified unused at this baseline.
inline constexpr std::string_view kMaintainedWorldlineComparisonIdPrefix =
    "comparison:maintained:";
inline constexpr std::string_view kMaintainedWorldlineComparisonWorldlineIdPrefix =
    "worldline:maintained:";

inline bool runtime_string_blank(const std::string &value) {
    return value.empty() || std::all_of(value.begin(), value.end(),
                                        [](unsigned char c) { return std::isspace(c) != 0; });
}

inline void append_runtime_evidence_ref(std::vector<std::string> &evidence_refs,
                                        const std::string &ref) {
    if (runtime_string_blank(ref)) {
        return;
    }
    if (std::find(evidence_refs.begin(), evidence_refs.end(), ref) != evidence_refs.end()) {
        return;
    }
    evidence_refs.push_back(ref);
}

} // namespace runtime_facade_internal

struct RuntimeFacade::CounterfactualWorldlineRegistry {
    std::map<std::string, RuntimeCounterfactualSnapshot> snapshots;
};
