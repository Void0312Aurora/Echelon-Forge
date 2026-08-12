#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_counterfactual(nb::module_ &m) {
    // Additive read surface for the replay contract types plus the fail-closed
    // validator, allowing the maintained Python run to validate the envelope
    // assembled from its own window products
    // (RuntimeFacade::build_maintained_replay_envelope). Nothing on an
    // existing path constructs or consumes these bindings.
    nb::class_<runtime::counterfactual::ReplaySnapshotRef>(m, "ReplaySnapshotRef")
        .def(nb::init<>())
        .def_rw("snapshot_version_ref",
                &runtime::counterfactual::ReplaySnapshotRef::snapshot_version_ref);

    nb::class_<runtime::counterfactual::ReplayBarrierRef>(m, "ReplayBarrierRef")
        .def(nb::init<>())
        .def_rw("barrier_id", &runtime::counterfactual::ReplayBarrierRef::barrier_id)
        .def_rw("barrier_sequence", &runtime::counterfactual::ReplayBarrierRef::barrier_sequence)
        .def_rw("barrier_detail", &runtime::counterfactual::ReplayBarrierRef::barrier_detail);

    nb::class_<runtime::counterfactual::ReplayEventOrderRef>(m, "ReplayEventOrderRef")
        .def(nb::init<>())
        .def_rw("sort_key", &runtime::counterfactual::ReplayEventOrderRef::sort_key)
        .def_rw("event_id", &runtime::counterfactual::ReplayEventOrderRef::event_id)
        .def_rw("producer_node_id",
                &runtime::counterfactual::ReplayEventOrderRef::producer_node_id);

    nb::class_<runtime::counterfactual::ReplayFacadeProvenanceRef>(m, "ReplayFacadeProvenanceRef")
        .def(nb::init<>())
        .def_rw("packet_ref", &runtime::counterfactual::ReplayFacadeProvenanceRef::packet_ref)
        .def_rw("packet_kind", &runtime::counterfactual::ReplayFacadeProvenanceRef::packet_kind)
        .def_rw("information_state_source",
                &runtime::counterfactual::ReplayFacadeProvenanceRef::information_state_source);

    nb::class_<runtime::counterfactual::ReplayEnvelope>(m, "ReplayEnvelope")
        .def(nb::init<>())
        .def_rw("replay_envelope_id", &runtime::counterfactual::ReplayEnvelope::replay_envelope_id)
        .def_rw("run_id", &runtime::counterfactual::ReplayEnvelope::run_id)
        .def_rw("episode_id", &runtime::counterfactual::ReplayEnvelope::episode_id)
        .def_rw("has_deterministic_seed",
                &runtime::counterfactual::ReplayEnvelope::has_deterministic_seed)
        .def_rw("deterministic_seed", &runtime::counterfactual::ReplayEnvelope::deterministic_seed)
        .def_rw("has_source_time", &runtime::counterfactual::ReplayEnvelope::has_source_time)
        .def_rw("source_time_s", &runtime::counterfactual::ReplayEnvelope::source_time_s)
        .def_rw("snapshot_ref", &runtime::counterfactual::ReplayEnvelope::snapshot_ref)
        .def_rw("barrier_ref", &runtime::counterfactual::ReplayEnvelope::barrier_ref)
        .def_rw("event_order_ref", &runtime::counterfactual::ReplayEnvelope::event_order_ref)
        .def_rw("facade_provenance_ref",
                &runtime::counterfactual::ReplayEnvelope::facade_provenance_ref)
        .def_rw("snapshot_restore_supported",
                &runtime::counterfactual::ReplayEnvelope::snapshot_restore_supported)
        .def_rw("restore_support_boundary",
                &runtime::counterfactual::ReplayEnvelope::restore_support_boundary);

    nb::class_<runtime::counterfactual::ReplayContractValidationResult>(
        m, "ReplayContractValidationResult")
        .def(nb::init<>())
        .def_rw("valid", &runtime::counterfactual::ReplayContractValidationResult::valid)
        .def_rw("errors", &runtime::counterfactual::ReplayContractValidationResult::errors)
        .def_rw("rejection_reason",
                &runtime::counterfactual::ReplayContractValidationResult::rejection_reason);

    nb::class_<runtime::counterfactual::MaintainedReplayEnvelopeResult>(
        m, "MaintainedReplayEnvelopeResult")
        .def(nb::init<>())
        .def_rw("admitted", &runtime::counterfactual::MaintainedReplayEnvelopeResult::admitted)
        .def_rw("envelope", &runtime::counterfactual::MaintainedReplayEnvelopeResult::envelope)
        .def_rw("rejection_reason",
                &runtime::counterfactual::MaintainedReplayEnvelopeResult::rejection_reason)
        .def_rw("errors", &runtime::counterfactual::MaintainedReplayEnvelopeResult::errors)
        .def_rw("evidence_refs",
                &runtime::counterfactual::MaintainedReplayEnvelopeResult::evidence_refs);

    m.def("validate_replay_envelope", &runtime::counterfactual::validate_replay_envelope,
          nb::arg("envelope"));

    // Additive read surface for the maintained engagement-packet ancestry
    // producer.
    // (RuntimeFacade::build_maintained_packet_ancestry). Nothing on an existing
    // path constructs or consumes these bindings. The typed lineage ref reuses
    // the shared typed-lineage vocabulary (ref_id / evidence_kind /
    // provenance_label) already owned by the C++ contract type.
    nb::class_<runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef>(
        m, "ScenarioGenerationEvidenceMetadataRef")
        .def(nb::init<>())
        .def_rw("ref_id", &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::ref_id)
        .def_rw("evidence_kind",
                &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::evidence_kind)
        .def_rw("provenance_label",
                &runtime::counterfactual::ScenarioGenerationEvidenceMetadataRef::provenance_label);

    nb::class_<MaintainedEngagementPacketAncestry>(m, "MaintainedEngagementPacketAncestry")
        .def(nb::init<>())
        .def_rw("packet_ancestry_id", &MaintainedEngagementPacketAncestry::packet_ancestry_id)
        .def_rw("run_id", &MaintainedEngagementPacketAncestry::run_id)
        .def_rw("episode_id", &MaintainedEngagementPacketAncestry::episode_id)
        .def_rw("anchor_trace_id", &MaintainedEngagementPacketAncestry::anchor_trace_id)
        .def_rw("parent_trace_id", &MaintainedEngagementPacketAncestry::parent_trace_id)
        .def_rw("replay_envelope_ref", &MaintainedEngagementPacketAncestry::replay_envelope_ref)
        .def_rw("parent_event_order_ref",
                &MaintainedEngagementPacketAncestry::parent_event_order_ref)
        .def_rw("lineage_refs", &MaintainedEngagementPacketAncestry::lineage_refs)
        .def_rw("ancestral_traces", &MaintainedEngagementPacketAncestry::ancestral_traces);

    nb::class_<MaintainedPacketAncestryResult>(m, "MaintainedPacketAncestryResult")
        .def(nb::init<>())
        .def_rw("admitted", &MaintainedPacketAncestryResult::admitted)
        .def_rw("ancestry", &MaintainedPacketAncestryResult::ancestry)
        .def_rw("rejection_reason", &MaintainedPacketAncestryResult::rejection_reason)
        .def_rw("errors", &MaintainedPacketAncestryResult::errors)
        .def_rw("evidence_refs", &MaintainedPacketAncestryResult::evidence_refs);

    // Additive read surface for the maintained worldline/counterfactual
    // comparison producer
    // (RuntimeFacade::build_maintained_worldline_comparison). Nothing on an
    // existing path constructs or consumes these bindings. The DTO carries
    // evidence ids only (no truth-state copies -- the no-truth-promotion red
    // line documented on the C++ type in runtime_facade_types.h).
    nb::class_<MaintainedWorldlineComparison>(m, "MaintainedWorldlineComparison")
        .def(nb::init<>())
        .def_rw("comparison_id", &MaintainedWorldlineComparison::comparison_id)
        .def_rw("run_id", &MaintainedWorldlineComparison::run_id)
        .def_rw("episode_id", &MaintainedWorldlineComparison::episode_id)
        .def_rw("baseline_worldline_id", &MaintainedWorldlineComparison::baseline_worldline_id)
        .def_rw("candidate_worldline_id", &MaintainedWorldlineComparison::candidate_worldline_id)
        .def_rw("baseline_anchor_trace_id",
                &MaintainedWorldlineComparison::baseline_anchor_trace_id)
        .def_rw("candidate_anchor_trace_id",
                &MaintainedWorldlineComparison::candidate_anchor_trace_id)
        .def_rw("baseline_replay_envelope_ref",
                &MaintainedWorldlineComparison::baseline_replay_envelope_ref)
        .def_rw("candidate_replay_envelope_ref",
                &MaintainedWorldlineComparison::candidate_replay_envelope_ref)
        .def_rw("baseline_packet_ancestry_ref",
                &MaintainedWorldlineComparison::baseline_packet_ancestry_ref)
        .def_rw("candidate_packet_ancestry_ref",
                &MaintainedWorldlineComparison::candidate_packet_ancestry_ref)
        .def_rw("baseline_event_order_ref",
                &MaintainedWorldlineComparison::baseline_event_order_ref)
        .def_rw("candidate_event_order_ref",
                &MaintainedWorldlineComparison::candidate_event_order_ref)
        .def_rw("baseline_snapshot_version_ref",
                &MaintainedWorldlineComparison::baseline_snapshot_version_ref)
        .def_rw("candidate_snapshot_version_ref",
                &MaintainedWorldlineComparison::candidate_snapshot_version_ref)
        .def_rw("baseline_deterministic_seed",
                &MaintainedWorldlineComparison::baseline_deterministic_seed)
        .def_rw("candidate_deterministic_seed",
                &MaintainedWorldlineComparison::candidate_deterministic_seed)
        .def_rw("deterministic_seed_matched",
                &MaintainedWorldlineComparison::deterministic_seed_matched)
        .def_rw("claim_scope", &MaintainedWorldlineComparison::claim_scope)
        .def_rw("truth_claim", &MaintainedWorldlineComparison::truth_claim)
        .def_rw("promoted_to_support", &MaintainedWorldlineComparison::promoted_to_support)
        .def_rw("lineage_refs", &MaintainedWorldlineComparison::lineage_refs);

    nb::class_<MaintainedWorldlineComparisonResult>(m, "MaintainedWorldlineComparisonResult")
        .def(nb::init<>())
        .def_rw("admitted", &MaintainedWorldlineComparisonResult::admitted)
        .def_rw("comparison", &MaintainedWorldlineComparisonResult::comparison)
        .def_rw("rejection_reason", &MaintainedWorldlineComparisonResult::rejection_reason)
        .def_rw("errors", &MaintainedWorldlineComparisonResult::errors)
        .def_rw("evidence_refs", &MaintainedWorldlineComparisonResult::evidence_refs);
}
