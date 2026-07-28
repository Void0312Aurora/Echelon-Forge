#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"
#include "core/mission/episode/execution_episode_controller.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/contracts/runtime_dto_contracts.h"
#include "runtime/contracts/world_batch_contracts.h"

// These types are intentionally incomplete at the public DTO boundary.  The
// runtime facade attaches an opaque, non-bindable identity to results returned
// by RuntimeFacade::run_window. Maintained evidence producers use it to reject
// synthetic/foreign results and to verify that every consumed public evidence
// field still matches the immutable snapshot sealed for that exact window.
struct RuntimeFacadeIdentity;
struct RuntimeWindowIdentity;

// Public storage keeps RuntimeWindowResult an aggregate (existing designated
// initialization is a source-compatibility contract), while the incomplete
// pointee and private payload keep the token opaque. RuntimeFacade is the only
// producer that can attach or inspect a non-empty token; Python bindings omit
// this holder entirely.
class RuntimeWindowIdentityToken {
  public:
    RuntimeWindowIdentityToken() = default;
    RuntimeWindowIdentityToken(const RuntimeWindowIdentityToken &) = default;
    RuntimeWindowIdentityToken(RuntimeWindowIdentityToken &&) noexcept = default;
    RuntimeWindowIdentityToken &operator=(const RuntimeWindowIdentityToken &) = default;
    RuntimeWindowIdentityToken &operator=(RuntimeWindowIdentityToken &&) noexcept = default;

  private:
    friend class RuntimeFacade;
    std::shared_ptr<const RuntimeWindowIdentity> identity_;
};

struct RuntimeCapabilities {
#define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_capabilities.inc"
};

struct RuntimeBatchConfig {
#define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_batch_config.inc"
};

struct RuntimeFidelityRequest {
#define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_fidelity_request.inc"
};

struct RuntimeFidelityAdmission {
#define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_fidelity_admission.inc"
};

struct RuntimeCounterfactualSnapshot {
#define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name, default_value)                        \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_snapshot.inc"
};

struct RuntimeWorldlineComparison {
#define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_worldline_comparison.inc"
};

struct BatchResetRequest {
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_reset_request.inc"
};

struct BatchWorldSetupRequest {
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_world_setup_request.inc"
};

struct BatchWorldSetupResult {
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_world_setup_result.inc"
};

struct RuntimeWorldLayoutRequest {
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_world_layout_request.inc"
};

struct RuntimeWorldLayoutResult {
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_world_layout_result.inc"
};

struct RuntimeCounterfactualBranchRequest {
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type, name, default_value)                  \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_branch_request.inc"
};

struct RuntimeCounterfactualRestoreRequest {
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type, name, default_value)                 \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_restore_request.inc"
};

struct RuntimeCounterfactualRestoreResult {
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type, name, default_value)                  \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_restore_result.inc"
};

struct RuntimeCounterfactualBranchResult {
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type, name, default_value)                   \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_branch_result.inc"
};

struct RuntimeExperimentStepRequest {
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value)                        \
    type name = default_value;
#include "runtime/facade/detail/runtime_experiment_step_request.inc"
};

struct RuntimeExperimentRequest {
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_request.inc"
};

struct ObservationBatchRequest {
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/observation_batch_request.inc"
};

struct TaskingBatchRequest {
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/tasking_batch_request.inc"
};

struct EngagementBatchRequest {
#define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/engagement_batch_request.inc"
};

struct ExecutionBatchStepRequest {
#define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/execution_batch_step_request.inc"
};

struct DeviceResidentOutputDescriptor {
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/resident_device_output_descriptor.inc"
};

struct ObservationBatchPacket {
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/observation_batch_packet.inc"
};

struct EngagementEventPacket {
#define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/engagement_event_packet.inc"
};

struct TaskingBatchPacket {
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/tasking_batch_packet.inc"
};

struct ExecutionBatchStepResult {
    std::vector<ExecutionEpisodeControllerStepResult> step_results;
    std::vector<ExecutionEpisodeState> execution_episode_states;
    std::vector<double> rewards;
    std::vector<bool> terminated;
    std::vector<bool> truncated;
    std::vector<std::array<double, 4>> status_vectors;
    std::vector<std::string> termination_reasons;
    std::vector<TerminationSpec> termination_specs;
    std::vector<std::string> reward_breakdown_jsons;
    std::vector<RewardReport> reward_reports;
    std::vector<StepInfoProducts> step_infos;
    std::vector<bool> step_info_valid_flags;
    std::vector<bool> controller_state_changed_flags;
    ObservationBatchPacket observation_packet;
    TaskingBatchPacket tasking_packet;
};

struct RuntimeExperimentAncestry {
#define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_ancestry.inc"
};

struct RuntimeExperimentResult {
#define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_result.inc"
};

struct RuntimeWindowActionRequest {
    struct CadenceControl {
#define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name, default_value)                         \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_control.inc"
    };

    ActionIntentPacket action_intent{};
    std::string source_layer = "facade";
    std::string input_snapshot_version;
    struct ClockDomainMetadata {
        std::string source_clock_domain = "outer_window";
        std::string relation = "nested";
        std::string clock_merge_policy;
        double source_time_s = 0.0;
        bool has_source_time = false;
        std::string source_snapshot_version;
        std::string target_window_id;
        std::vector<std::string> barrier_order;
        bool diagnostics_only = false;
        std::string diagnostics_reason;
    } clock_domain_metadata{};
    CadenceControl cadence_control{};
};

struct RuntimeWindowInputRecord {
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_input_record.inc"
};

struct RuntimeWindowSchedulingContext {
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_scheduling_context.inc"
};

struct RuntimeWindowBarrierRecord {
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_barrier_record.inc"
};

struct RuntimeWindowVisibilityRecord {
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value)                       \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_visibility_record.inc"
};

struct RuntimeWindowNodeExecutionRecord {
#define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type, name, default_value)                   \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_node_execution_record.inc"
};

struct RuntimeWindowCadence {
#define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence.inc"
};

struct RuntimeWindowCadenceConfig {
#define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_config.inc"
};

struct RuntimeWindowCadenceTraceRecord {
#define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type, name, default_value)                    \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_trace_record.inc"
};

struct RuntimeWindowRequest {
#define EF_RUNTIME_WINDOW_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_request.inc"
};

struct RuntimeWindowResult {
#define EF_RUNTIME_WINDOW_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_result.inc"
    // Trailing additive storage: existing field order and offsets stay fixed,
    // and the result remains an aggregate for designated initialization.
    RuntimeWindowIdentityToken identity_token_{};
};

// --- T10 evidence spine, slice 6A (this iteration) -------------------------
//
// Additive result DTOs of the maintained engagement-packet ancestry producer
// (RuntimeFacade::build_maintained_packet_ancestry). Hand-written next to the
// window DTOs they reference, following the slice-5 precedent
// (MaintainedReplayEnvelopeResult in counterfactual_replay_contract_types.h);
// appended at the end of this header, so no existing member order moves.
//
// The ancestry carries parent-linked COPIES of a real window's exported
// DiagnosticsTrace family (census slice-6 gap: parent_trace_id is hardcoded 0
// on the facade export path) -- the window products themselves are never
// mutated, so every default-path serialized value stays byte-identical.
// Lineage refs use the shared typed-ref vocabulary
// (ScenarioGenerationEvidenceMetadataRef: ref_id / evidence_kind /
// provenance_label, the VA-5/VA-6 field names the lineage schema modules pin).
struct MaintainedEngagementPacketAncestry {
    // "ancestry:maintained:{run_id}:trace:{anchor_trace_id}" -- reserved
    // namespace, disjoint from "replay:maintained:*" and "replay:facade:*".
    std::string packet_ancestry_id;
    std::string run_id;
    std::string episode_id;
    // The window's own run-minted VA-8 anchor (engagement packet trace_ids
    // tail, same anchor the slice-5 envelope id embeds).
    std::uint64_t anchor_trace_id = 0;
    // The PREVIOUS window's run-minted anchor; 0 = root window (no parent),
    // which is exactly the pre-slice default value of parent_trace_id.
    std::uint64_t parent_trace_id = 0;
    // The admitted maintained replay envelope of the SAME window
    // ("replay:maintained:{run_id}:trace:{anchor}"), validated by
    // validate_replay_envelope before this ancestry can be admitted.
    std::string replay_envelope_ref;
    // "event:trace:{parent_trace_id}" (the slice-5 event-order embedding) or
    // empty at the root.
    std::string parent_event_order_ref;
    // Typed lineage refs (VA-5 vocabulary): replay envelope + anchor trace
    // (+ parent trace when linked).
    std::vector<runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef> lineage_refs;
    // Parent-linked copies of the window's exported diagnostics traces.
    // Copies whose trace_id is one of the packet's run-minted tags carry
    // parent_trace_id = the ancestry parent; copies from the kernel
    // engagement-event id space are left untouched (the census's disjoint-id
    // warning: a VA-8 parent must not be grafted onto a kernel-space trace).
    std::vector<DiagnosticsTrace> ancestral_traces;
};

// Fail-closed result: `admitted` is only true when the slice-5 envelope gates
// (including validate_replay_envelope) passed AND the ancestry-specific parent
// gates passed. On rejection the ancestry stays default-constructed, so a
// rejected result cannot leak half-real lineage.
struct MaintainedPacketAncestryResult {
    bool admitted = false;
    MaintainedEngagementPacketAncestry ancestry{};
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;
};

// --- T10 evidence spine, slice 7 (this iteration) ---------------------------
//
// Additive result DTOs of the maintained worldline/counterfactual comparison
// producer (RuntimeFacade::build_maintained_worldline_comparison). Hand-written
// next to the slice-6A ancestry DTOs they consume, following the slice-5/6A
// precedent; appended at the end of this header, so no existing member order
// moves (member order is ABI for every DTO above).
//
// NO TRUTH PROMOTION -- the slice red line. Unlike the raw counterfactual
// surface's RuntimeWorldlineComparison (which carries kinematic truth deltas
// dx/dy/dz/dvx/dvy/dvz/dheading), this DTO carries evidence REFERENCES only:
// ids minted by the slice-5/6A producers of THIS facade (replay envelope ids,
// packet ancestry ids, VA-8 anchor trace ids, event-order refs, snapshot
// version refs) plus the caller-owned run identity and seeds. No field copies
// truth state, so an admitted comparison can never promote a counterfactual
// worldline's state into support -- there is nothing state-shaped to promote.
// truth_claim / promoted_to_support are structurally always false (the
// producer takes no flag that could set them) and claim_scope is always the
// contract-owned "comparative" (kExperimentProfileClaimScopeComparative),
// mirroring the WP17 experiment surface's descriptive-claims discipline.
struct MaintainedWorldlineComparison {
    // "comparison:maintained:{run_id}:trace:{baseline_anchor}:vs:{candidate_anchor}"
    // -- reserved namespace, disjoint from the raw-facade
    // "counterfactual:selected_slice*" comparison ids and from
    // "replay:maintained:*" / "ancestry:maintained:*".
    std::string comparison_id;
    std::string run_id;
    std::string episode_id;
    // Maintained worldline identity, minted by THIS producer as
    // "worldline:maintained:{run_id}:trace:{anchor}": a worldline here is the
    // evidence chain named by its window's run-minted VA-8 anchor, not a
    // registered counterfactual snapshot (no worldline registry entry is
    // created or read; the counterfactual restore path stays untouched).
    std::string baseline_worldline_id;
    std::string candidate_worldline_id;
    // The two windows' run-minted VA-8 anchors (engagement packet trace_ids
    // tails), admitted by the slice-5 gates; distinct by the comparison gate.
    std::uint64_t baseline_anchor_trace_id = 0;
    std::uint64_t candidate_anchor_trace_id = 0;
    // Deterministic replay refs: each side's admitted maintained replay
    // envelope ("replay:maintained:{run_id}:trace:{anchor}", I69 producer,
    // validated by validate_replay_envelope which requires the deterministic
    // seed and the deterministic event-order sort key).
    std::string baseline_replay_envelope_ref;
    std::string candidate_replay_envelope_ref;
    // Each side's admitted maintained packet ancestry
    // ("ancestry:maintained:{run_id}:trace:{anchor}", I79 producer).
    std::string baseline_packet_ancestry_ref;
    std::string candidate_packet_ancestry_ref;
    // "event:trace:{anchor}" -- the envelopes' deterministic event-order ids.
    std::string baseline_event_order_ref;
    std::string candidate_event_order_ref;
    // The envelopes' snapshot identities (the packets' run-produced
    // "global:{n}" provenance strings; slice-5 default VA-2 qualification off).
    std::string baseline_snapshot_version_ref;
    std::string candidate_snapshot_version_ref;
    // Caller-owned run identity seeds of the two worldlines (the run
    // orchestrator owns them, exactly as on the envelope producer), echoed so
    // a consumer can pick the same-seed replay pair without re-deriving.
    std::uint64_t baseline_deterministic_seed = 0;
    std::uint64_t candidate_deterministic_seed = 0;
    bool deterministic_seed_matched = false;
    // Always "comparative" / false / false -- see the no-truth-promotion block
    // comment above.
    std::string claim_scope;
    bool truth_claim = false;
    bool promoted_to_support = false;
    // Typed lineage refs (VA-5 vocabulary: ref_id / evidence_kind /
    // provenance_label): envelope + ancestry + anchor per side, labels
    // "baseline" / "candidate". Deterministic order.
    std::vector<runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef> lineage_refs;
};

// Fail-closed result: `admitted` is only true when BOTH windows' slice-5
// envelope gates and slice-6A ancestry gates passed (their rejections are
// wrapped in side-naming reasons, underlying detail in `errors`) AND the
// comparison-specific distinct-anchor gate passed. On rejection the comparison
// stays default-constructed, so a rejected result cannot leak a half-real
// evidence join.
struct MaintainedWorldlineComparisonResult {
    bool admitted = false;
    MaintainedWorldlineComparison comparison{};
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;
};
