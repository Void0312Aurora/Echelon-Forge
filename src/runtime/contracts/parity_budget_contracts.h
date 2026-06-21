#pragma once

#include <algorithm>
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::parity {

inline constexpr std::string_view kParityBudgetCpuExactReferenceV1 =
    "parity_budget.cpu_exact.reference.v1";
inline constexpr std::string_view kParityBudgetGpuHelpersDiagnosticsOnlyV1 =
    "parity_budget.gpu_helpers.diagnostics_only.v1";
inline constexpr std::string_view kParityBudgetGpuExactUnmaintainedCandidateV1 =
    "parity_budget.gpu_exact.unmaintained_candidate.v1";
inline constexpr std::string_view kParityBudgetResidentStateUnmaintainedCandidateV1 =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kParityBudgetShadowCompareUnmaintainedCandidateV1 =
    "parity_budget.shadow_compare.unmaintained_candidate.v1";

inline constexpr std::string_view kParityBudgetProfileClassReference = "reference";
inline constexpr std::string_view kParityBudgetProfileClassAcceleratedExact =
    "accelerated_exact";
inline constexpr std::string_view kParityBudgetProfileClassResidentState =
    "resident_state";
inline constexpr std::string_view kParityBudgetProfileClassDiagnosticsOnly =
    "diagnostics_only";
inline constexpr std::string_view kParityBudgetProfileClassApproximate = "approximate";

inline constexpr std::string_view kParityBudgetRejectionMissingBudgetRef =
    "missing_parity_budget_ref";
inline constexpr std::string_view kParityBudgetRejectionUnknownBudgetRef =
    "unknown_parity_budget_ref";
inline constexpr std::string_view kParityBudgetRejectionProfileClassIncompatible =
    "parity_budget_profile_class_incompatible";
inline constexpr std::string_view kParityBudgetRejectionAcceptanceGateMissing =
    "parity_budget_acceptance_gate_missing";
inline constexpr std::string_view kParityBudgetRejectionCandidateNotMaintained =
    "parity_budget_candidate_is_not_accepted_for_maintained_use";
inline constexpr std::string_view kParityBudgetRejectionDiagnosticsOnlyNotMaintained =
    "parity_budget_diagnostics_only_is_not_accepted_for_maintained_use";
inline constexpr std::string_view kParityBudgetRejectionMetadataIncomplete =
    "parity_budget_metadata_incomplete";

struct ParityBudgetScope {
    std::string maintained_status;
    std::vector<std::string> clock_domains;
    std::vector<std::string> state_shards;
    std::vector<std::string> output_families;
    std::vector<std::string> diagnostics_only_surfaces;
};

struct ParityBudgetComparisonDomain {
    std::string mode;
    std::vector<std::string> identity_fields;
    std::vector<std::string> envelope_fields;
    std::vector<std::string> structured_fields;
    std::vector<std::string> tolerance_requirements;
    std::string payload_policy;
    std::string prose_policy;
    std::string normalization;
    std::string allowed_drift;
};

struct ParityBudgetMismatchPolicy {
    std::string maintained_profile_result;
    std::string candidate_result;
    std::string diagnostics_result;
    bool quarantine_required = false;
};

struct ParityBudgetRecord {
    std::string budget_id;
    int budget_version = 0;
    std::string backend_profile_id;
    std::string profile_class;
    std::string comparison_reference;
    ParityBudgetScope budget_scope;
    ParityBudgetComparisonDomain event_order;
    ParityBudgetComparisonDomain snapshot_versions;
    ParityBudgetComparisonDomain numeric_state;
    ParityBudgetComparisonDomain observation_export;
    ParityBudgetComparisonDomain diagnostics_trace;
    std::vector<std::string> sync_barriers;
    std::vector<std::string> diagnostics_requirements;
    ParityBudgetMismatchPolicy mismatch_policy;
    std::string acceptance_gate;
    std::string change_reason;
};

struct ParityBudgetValidationResult {
    bool valid = true;
    bool accepted_for_maintained_use = false;
    std::string rejection_reason;
    std::vector<std::string> errors;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }

    void reject(std::string reason) {
        valid = false;
        accepted_for_maintained_use = false;
        rejection_reason = std::move(reason);
    }
};

inline bool is_blank(std::string_view value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

inline bool contains_value(
    const std::vector<std::string>& items,
    std::string_view expected
) {
    return std::find(items.begin(), items.end(), expected) != items.end();
}

inline bool profile_class_compatible_with_parity_budget(
    std::string_view profile_class,
    std::string_view budget_profile_class
) {
    if (profile_class == budget_profile_class) {
        return true;
    }

    return false;
}

inline bool parity_budget_has_required_comparison_metadata(const ParityBudgetRecord& record) {
    return !is_blank(record.event_order.mode) &&
        !record.event_order.identity_fields.empty() &&
        !is_blank(record.snapshot_versions.mode) &&
        !record.snapshot_versions.identity_fields.empty() &&
        !is_blank(record.observation_export.mode) &&
        !record.observation_export.envelope_fields.empty() &&
        !is_blank(record.observation_export.payload_policy) &&
        !is_blank(record.diagnostics_trace.mode) &&
        !record.diagnostics_trace.structured_fields.empty() &&
        !is_blank(record.diagnostics_trace.prose_policy) &&
        !record.sync_barriers.empty() &&
        !is_blank(record.mismatch_policy.maintained_profile_result) &&
        !is_blank(record.mismatch_policy.diagnostics_result);
}

inline bool parity_budget_has_acceptance_gate(const ParityBudgetRecord& record) {
    return !is_blank(record.acceptance_gate);
}

inline bool parity_budget_is_maintained_baseline(const ParityBudgetRecord& record) {
    return record.budget_id == kParityBudgetCpuExactReferenceV1 &&
        record.backend_profile_id == "cpu_exact.reference" &&
        record.profile_class == kParityBudgetProfileClassReference &&
        record.budget_scope.maintained_status == "maintained_exact_baseline";
}

inline ParityBudgetValidationResult validate_parity_budget_record_contract(
    const ParityBudgetRecord& record
) {
    ParityBudgetValidationResult result{};

    if (is_blank(record.budget_id)) {
        result.add_error("budget_id is required");
    }
    if (record.budget_version <= 0) {
        result.add_error("budget_version must be positive");
    }
    if (is_blank(record.backend_profile_id)) {
        result.add_error("backend_profile_id is required");
    }
    if (is_blank(record.profile_class)) {
        result.add_error("profile_class is required");
    }
    if (is_blank(record.comparison_reference)) {
        result.add_error("comparison_reference is required");
    }
    if (record.budget_scope.clock_domains.empty()) {
        result.add_error("budget_scope.clock_domains is required");
    }
    if (record.budget_scope.output_families.empty()) {
        result.add_error("budget_scope.output_families is required");
    }
    if (!parity_budget_has_required_comparison_metadata(record)) {
        result.add_error(
            "comparison domains must define event_order, snapshot_versions, "
            "observation_export, diagnostics_trace, sync_barriers, and mismatch_policy"
        );
    }
    if (record.diagnostics_requirements.empty()) {
        result.add_error("diagnostics_requirements is required");
    }
    if (!parity_budget_has_acceptance_gate(record)) {
        result.reject(std::string(kParityBudgetRejectionAcceptanceGateMissing));
        result.add_error("acceptance_gate is required");
        return result;
    }

    if (!result.valid) {
        result.rejection_reason = std::string(kParityBudgetRejectionMetadataIncomplete);
        return result;
    }

    result.accepted_for_maintained_use = parity_budget_is_maintained_baseline(record);
    if (!result.accepted_for_maintained_use) {
        if (record.profile_class == kParityBudgetProfileClassDiagnosticsOnly) {
            result.rejection_reason =
                std::string(kParityBudgetRejectionDiagnosticsOnlyNotMaintained);
        } else {
            result.rejection_reason =
                std::string(kParityBudgetRejectionCandidateNotMaintained);
        }
    }
    return result;
}

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
                .output_families = {
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
                .identity_fields = {
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
                .envelope_fields = {
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
                .structured_fields = {
                    "source_request_id",
                    "event_id",
                    "source_snapshot_version",
                    "resulting_snapshot_version",
                    "mismatch_code",
                },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements = {
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
                .identity_fields = {
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
                .tolerance_requirements = {
                    "field_family_comparator_threshold_if_promoted",
                },
            },
        .observation_export =
            ParityBudgetComparisonDomain{
                .mode = "exact_if_present",
                .envelope_fields = {
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
                .structured_fields = {
                    "source_request_id",
                    "event_id",
                    "source_snapshot_version",
                    "mismatch_code",
                },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"export"},
        .diagnostics_requirements = {
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
                .output_families = {
                    "observation_packet",
                    "committed_snapshot",
                    "diagnostics_trace",
                },
                .diagnostics_only_surfaces = {
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
                .identity_fields = {
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
                .envelope_fields = {
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
                .structured_fields = {
                    "source_request_id",
                    "event_id",
                    "source_snapshot_version",
                    "resulting_snapshot_version",
                    "mismatch_code",
                },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"input_injection", "tick_commit", "window_commit", "export"},
        .diagnostics_requirements = {
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
        .acceptance_gate =
            "future_accelerated_exact_promotion_review_with_replay_evidence",
        .change_reason =
            "initial unmaintained candidate budget; no exact GPU acceptance claimed",
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
                .output_families = {
                    "observation_packet",
                    "committed_snapshot",
                    "diagnostics_trace",
                },
                .diagnostics_only_surfaces = {
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
                .identity_fields = {
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
                .envelope_fields = {
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
                .structured_fields = {
                    "source_request_id",
                    "event_id",
                    "source_snapshot_version",
                    "resulting_snapshot_version",
                    "mismatch_code",
                },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {
            "input_injection",
            "partial_sync_commit",
            "window_commit",
            "export",
        },
        .diagnostics_requirements = {
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
        .change_reason =
            "initial unmaintained resident-state candidate budget; host/backend split not yet accepted as maintained",
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
                .diagnostics_only_surfaces = {
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
                .identity_fields = {
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
                .envelope_fields = {
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
                .structured_fields = {
                    "source_request_id",
                    "event_id",
                    "source_snapshot_version",
                    "mismatch_code",
                },
                .prose_policy = "diagnostics_only",
            },
        .sync_barriers = {"reference_export", "shadow_report_export"},
        .diagnostics_requirements = {
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
        .change_reason =
            "initial unmaintained shadow-compare placeholder; no shadow capability acceptance claimed",
    };
}

inline const std::vector<ParityBudgetRecord>& parity_budget_registry_seed() {
    static const std::vector<ParityBudgetRecord> registry = {
        make_cpu_exact_reference_budget(),
        make_gpu_helpers_diagnostics_only_budget(),
        make_gpu_exact_unmaintained_candidate_budget(),
        make_resident_state_unmaintained_candidate_budget(),
        make_shadow_compare_unmaintained_candidate_budget(),
    };
    return registry;
}

inline const ParityBudgetRecord* find_parity_budget_record(std::string_view budget_id) {
    const auto& registry = parity_budget_registry_seed();
    const auto it = std::find_if(
        registry.begin(),
        registry.end(),
        [budget_id](const ParityBudgetRecord& record) {
            return record.budget_id == budget_id;
        }
    );
    return it == registry.end() ? nullptr : &(*it);
}

inline ParityBudgetValidationResult validate_profile_owned_parity_budget(
    std::string_view backend_profile_id,
    std::string_view profile_class,
    std::string_view budget_ref
) {
    ParityBudgetValidationResult result{};

    if (is_blank(budget_ref)) {
        result.reject(std::string(kParityBudgetRejectionMissingBudgetRef));
        result.add_error("budget_ref is required");
        return result;
    }

    const ParityBudgetRecord* record = find_parity_budget_record(budget_ref);
    if (record == nullptr) {
        result.reject(std::string(kParityBudgetRejectionUnknownBudgetRef));
        result.add_error("budget_ref was not found in the registry seed");
        return result;
    }

    result = validate_parity_budget_record_contract(*record);
    if (!result.valid) {
        return result;
    }

    if (!is_blank(backend_profile_id) && record->backend_profile_id != backend_profile_id) {
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("backend_profile_id does not own the referenced budget");
        return result;
    }

    if (!profile_class_compatible_with_parity_budget(profile_class, record->profile_class)) {
        result.reject(std::string(kParityBudgetRejectionProfileClassIncompatible));
        result.add_error("profile_class is not compatible with the referenced budget");
        return result;
    }

    return result;
}

inline std::optional<ParityBudgetValidationResult> validate_parity_budget_registry_seed() {
    const auto& registry = parity_budget_registry_seed();
    if (registry.empty()) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error("registry seed must not be empty");
        return result;
    }

    std::vector<std::string> seen_budget_ids;
    seen_budget_ids.reserve(registry.size());
    std::vector<std::string> maintained_budget_ids;

    for (const auto& record : registry) {
        if (contains_value(seen_budget_ids, record.budget_id)) {
            ParityBudgetValidationResult result{};
            result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
            result.add_error("duplicate budget_id: " + record.budget_id);
            return result;
        }
        seen_budget_ids.push_back(record.budget_id);

        const ParityBudgetValidationResult record_result =
            validate_parity_budget_record_contract(record);
        if (!record_result.valid) {
            return record_result;
        }

        if (record_result.accepted_for_maintained_use) {
            maintained_budget_ids.push_back(record.budget_id);
        }
    }

    if (maintained_budget_ids.size() != 1 ||
        maintained_budget_ids.front() != kParityBudgetCpuExactReferenceV1) {
        ParityBudgetValidationResult result{};
        result.reject(std::string(kParityBudgetRejectionMetadataIncomplete));
        result.add_error(
            "registry seed must keep only parity_budget.cpu_exact.reference.v1 as maintained"
        );
        return result;
    }

    return std::nullopt;
}

}  // namespace runtime::parity
