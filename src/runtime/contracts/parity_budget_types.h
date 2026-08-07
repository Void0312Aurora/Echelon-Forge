#pragma once

#include <algorithm>
#include <cctype>
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
inline constexpr std::string_view kParityBudgetProfileClassAcceleratedExact = "accelerated_exact";
inline constexpr std::string_view kParityBudgetProfileClassResidentState = "resident_state";
inline constexpr std::string_view kParityBudgetProfileClassDiagnosticsOnly = "diagnostics_only";
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
inline constexpr std::string_view kParityComparatorExact = "exact";
inline constexpr std::string_view kParityComparatorAbsoluteOrRelative = "absolute_or_relative";

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

enum class ParityBudgetSurfaceStatus {
    current_dto,
    future_frozen_contract,
};

enum class ParityBudgetValueKind {
    boolean,
    signed_integer,
    unsigned_integer,
    float32,
    float64,
    string,
    structured,
};

struct ParityBudgetSelectedField {
    std::string field_path;
    std::string surface_owner;
    ParityBudgetSurfaceStatus surface_status = ParityBudgetSurfaceStatus::current_dto;
    ParityBudgetValueKind value_kind = ParityBudgetValueKind::structured;
    std::string shard;

    bool operator==(const ParityBudgetSelectedField &) const = default;
};

struct ParityBudgetSelectedFieldFamily {
    std::string field_family;
    std::vector<ParityBudgetSelectedField> selected_fields;
    std::string comparator;
    double absolute_tolerance = 0.0;
    double relative_tolerance = 0.0;
    std::vector<std::string> comparison_barriers;

    bool operator==(const ParityBudgetSelectedFieldFamily &) const = default;
};

struct ParityBudgetBarrierRule {
    std::string barrier_id;
    std::string candidate_rule;
    std::vector<std::string> visible_shards;
    bool enabled = true;
    bool comparison_eligible = false;
    bool host_truth_available = false;

    bool operator==(const ParityBudgetBarrierRule &) const = default;
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
    std::vector<ParityBudgetSelectedFieldFamily> selected_slice_fields;
    std::vector<ParityBudgetBarrierRule> barrier_rules;
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
    return std::all_of(value.begin(), value.end(),
                       [](unsigned char c) { return std::isspace(c) != 0; });
}

inline bool contains_value(const std::vector<std::string> &items, std::string_view expected) {
    return std::find(items.begin(), items.end(), expected) != items.end();
}

inline bool profile_class_compatible_with_parity_budget(std::string_view profile_class,
                                                        std::string_view budget_profile_class) {
    if (profile_class == budget_profile_class) {
        return true;
    }

    return false;
}

inline bool parity_budget_has_required_comparison_metadata(const ParityBudgetRecord &record) {
    return !is_blank(record.event_order.mode) && !record.event_order.identity_fields.empty() &&
           !is_blank(record.snapshot_versions.mode) &&
           !record.snapshot_versions.identity_fields.empty() &&
           !is_blank(record.observation_export.mode) &&
           !record.observation_export.envelope_fields.empty() &&
           !is_blank(record.observation_export.payload_policy) &&
           !is_blank(record.diagnostics_trace.mode) &&
           !record.diagnostics_trace.structured_fields.empty() &&
           !is_blank(record.diagnostics_trace.prose_policy) && !record.sync_barriers.empty() &&
           !is_blank(record.mismatch_policy.maintained_profile_result) &&
           !is_blank(record.mismatch_policy.diagnostics_result);
}

inline bool parity_budget_has_acceptance_gate(const ParityBudgetRecord &record) {
    return !is_blank(record.acceptance_gate);
}

inline ParityBudgetSelectedField current_selected_field(std::string field_path,
                                                        std::string surface_owner,
                                                        ParityBudgetValueKind value_kind,
                                                        std::string shard) {
    return ParityBudgetSelectedField{
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = ParityBudgetSurfaceStatus::current_dto,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

inline ParityBudgetSelectedField future_selected_field(std::string field_path,
                                                       std::string surface_owner,
                                                       ParityBudgetValueKind value_kind,
                                                       std::string shard) {
    return ParityBudgetSelectedField{
        .field_path = std::move(field_path),
        .surface_owner = std::move(surface_owner),
        .surface_status = ParityBudgetSurfaceStatus::future_frozen_contract,
        .value_kind = value_kind,
        .shard = std::move(shard),
    };
}

} // namespace runtime::parity
