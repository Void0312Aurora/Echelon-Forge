#pragma once

#include <string>
#include <vector>

#include "runtime/contracts/parity_budget_selected_slice.h"

namespace runtime::parity {

inline ParityBudgetRecord make_cpu_exact_reference_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetCpuExactReferenceV1),
        .budget_version = 1,
        .backend_profile_id = "cpu_exact.reference",
        .profile_class = std::string(kParityBudgetProfileClassReference),
        .comparison_reference = "self",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "maintained_exact_baseline",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"scheduler", "physics", "track", "observation", "engagement"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces = {"human_readable_diagnostics_prose"},
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact",
                .tolerance_requirements = {},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_envelope",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_structured_ancestry",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "fail",
                .candidate_result = "not_applicable",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate = "maintained_cpu_reference_existing_baseline",
        .change_reason = "initial maintained exact reference budget",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_gpu_helpers_diagnostics_only_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetGpuHelpersDiagnosticsOnlyV1),
        .budget_version = 1,
        .backend_profile_id = "gpu_helpers.diagnostics_only",
        .profile_class = std::string(kParityBudgetProfileClassDiagnosticsOnly),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "diagnostics_only_not_truth",
                .clock_domains = {"declared_by_helper_export"},
                .state_shards = {},
                .output_families = {"helper_metrics", "helper_trace", "probe_export"},
                .diagnostics_only_surfaces = {"all_exported_surfaces"},
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_if_replayed_against_reference",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_if_snapshot_link_is_reported",
                .identity_fields =
                    {
                        "source_snapshot_version",
                        "barrier_id",
                        "barrier_sequence",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "diagnostics_only",
                .tolerance_requirements =
                    {
                        "field_family_comparator_threshold_if_promoted",
                    },
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_present",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_present",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "export_barrier_id",
                "helper_name",
                "helper_build_or_feature_flag",
                "diagnostics_label",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_applicable",
                .candidate_result = "not_applicable",
                .diagnostics_result = "report_only",
                .quarantine_required = false,
            },
        .acceptance_gate = "not_eligible_for_maintained_truth_without_reclassification",
        .change_reason = "initial diagnostics-only placeholder for GPU helper exports",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_gpu_exact_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetGpuExactUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "gpu_exact.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassAcceleratedExact),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"scheduler", "physics", "track", "observation", "engagement"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces =
                    {
                        "accelerator_kernel_notes",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_promotion",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_promotion",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_accelerated_exact",
                .tolerance_requirements = {},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_promotion",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_required_for_promotion",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "accelerator_backend_id",
                "accelerator_build_or_feature_flag",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_accepted",
                .candidate_result = "fail_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate = "future_accelerated_exact_promotion_review_with_replay_evidence",
        .change_reason = "initial unmaintained candidate budget; no exact GPU acceptance claimed",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

inline ParityBudgetRecord make_resident_state_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetResidentStateUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "resident_state.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassResidentState),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"physics.fixed_tick", "sensor.scan_slot"},
                .state_shards = {"observation", "physics_or_track_if_declared_by_future_profile"},
                .output_families =
                    {
                        "observation_packet",
                        "committed_snapshot",
                        "diagnostics_trace",
                    },
                .diagnostics_only_surfaces =
                    {
                        "unsynced_backend_local_state",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_at_declared_barriers",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_required_for_host_visible_exports",
                .identity_fields =
                    {
                        "world_id",
                        "global_version",
                        "barrier_id",
                        "barrier_sequence",
                        "shard_versions",
                        "lineage",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "exact_by_default_with_explicit_future_tolerance_only",
                .tolerance_requirements = {"field_family", "comparator", "threshold"},
                .allowed_drift = "none",
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_host_visible_exports",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_host_visible_exports",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "resulting_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = resident_candidate_sync_barrier_contract(),
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "resulting_snapshot_version",
                "sync_barrier_id",
                "host_state_owner",
                "backend_state_owner",
                "sync_policy",
                "resident_state_scope",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_accepted",
                .candidate_result = "fail_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = true,
            },
        .acceptance_gate =
            "future_resident_state_promotion_review_with_ownership_sync_and_replay_evidence",
        .change_reason = "initial unmaintained resident-state candidate budget; host/backend split "
                         "not yet accepted as maintained",
        .selected_slice_fields = resident_candidate_selected_slice_field_contract(),
        .barrier_rules = resident_candidate_barrier_contract(),
    };
}

inline ParityBudgetRecord make_shadow_compare_unmaintained_candidate_budget() {
    return ParityBudgetRecord{
        .budget_id = std::string(kParityBudgetShadowCompareUnmaintainedCandidateV1),
        .budget_version = 1,
        .backend_profile_id = "shadow_compare.unmaintained_candidate",
        .profile_class = std::string(kParityBudgetProfileClassDiagnosticsOnly),
        .comparison_reference = "cpu_exact.reference",
        .budget_scope =
            ParityBudgetScope{
                .maintained_status = "unmaintained_candidate",
                .clock_domains = {"reference_clock_only"},
                .state_shards = {},
                .output_families = {"shadow_report", "mismatch_report", "diagnostics_trace"},
                .diagnostics_only_surfaces =
                    {
                        "shadow_report",
                        "mismatch_report",
                        "human_readable_diagnostics_prose",
                    },
            },
        .event_order =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_for_reference_stream",
                .identity_fields = {"timestamp", "priority", "event_id", "event_family_membership"},
                .allowed_drift = "none",
            },
        .snapshot_versions =
            ParityBudgetComparisonDomain{
                .mode = "exact_identity_for_reference_links",
                .identity_fields =
                    {
                        "source_snapshot_version",
                        "barrier_id",
                        "barrier_sequence",
                    },
                .normalization = "exported_snapshot_version",
                .allowed_drift = "none",
            },
        .numeric_state =
            ParityBudgetComparisonDomain{
                .mode = "diagnostics_only_until_promoted",
                .tolerance_requirements = {"field_family", "comparator", "threshold"},
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_exported",
                .envelope_fields =
                    {
                        "schema_version",
                        "field_set",
                        "visibility_label",
                        "provenance",
                        "source_snapshot_version",
                    },
                .payload_policy = "inherit_numeric_state",
            },
        .diagnostics_trace =
            ParityBudgetComparisonDomain{
                .mode = "exact_for_shadow_report_ancestry",
                .structured_fields =
                    {
                        "source_request_id",
                        "event_id",
                        "source_snapshot_version",
                        "mismatch_code",
                    },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"reference_export", "shadow_report_export"},
        .diagnostics_requirements =
            {
                "backend_profile_id",
                "budget_id",
                "budget_version",
                "comparison_reference",
                "source_snapshot_version",
                "shadow_run_id",
                "compared_profile_id",
                "sync_barrier_id",
                "mismatch_domain",
                "mismatch_code",
                "mismatch_summary",
            },
        .mismatch_policy =
            ParityBudgetMismatchPolicy{
                .maintained_profile_result = "not_applicable",
                .candidate_result = "report_only_and_remain_unmaintained",
                .diagnostics_result = "report_only",
                .quarantine_required = false,
            },
        .acceptance_gate = "future_shadow_compare_review_before_any_maintained_claim",
        .change_reason = "initial unmaintained shadow-compare placeholder; no shadow capability "
                         "acceptance claimed",
        .selected_slice_fields = {},
        .barrier_rules = {},
    };
}

} // namespace runtime::parity
