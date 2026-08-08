#pragma once

#include <algorithm>
#include <cctype>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::backend_profiles {

inline constexpr std::string_view kBackendProfileIdCpuExactReference =
    "cpu_exact.reference";
inline constexpr std::string_view kBackendProfileIdGpuHelpersDiagnosticsOnly =
    "gpu_helpers.diagnostics_only";
inline constexpr std::string_view kBackendProfileIdGpuExactUnmaintainedCandidate =
    "gpu_exact.unmaintained_candidate";
inline constexpr std::string_view kBackendProfileIdResidentStateUnmaintainedCandidate =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kBackendProfileIdShadowCompareUnmaintainedCandidate =
    "shadow_compare.unmaintained_candidate";

inline constexpr std::string_view kBackendProfileClassReference = "reference";
inline constexpr std::string_view kBackendProfileClassAcceleratedExact =
    "accelerated_exact";
inline constexpr std::string_view kBackendProfileClassResidentState = "resident_state";
inline constexpr std::string_view kBackendProfileClassApproximate = "approximate";
inline constexpr std::string_view kBackendProfileClassDiagnosticsOnly =
    "diagnostics_only";

inline constexpr std::string_view kBackendProfileMaintainedStatusMaintainedExactBaseline =
    "maintained_exact_baseline";
inline constexpr std::string_view kBackendProfileMaintainedStatusDiagnosticsOnly =
    "diagnostics_only";
inline constexpr std::string_view kBackendProfileMaintainedStatusUnmaintainedCandidate =
    "unmaintained_candidate";

inline constexpr std::string_view kBackendProfileSyncPolicyHostOwned = "host-owned";
inline constexpr std::string_view kBackendProfileSyncPolicyBackendOwned = "backend-owned";
inline constexpr std::string_view kBackendProfileSyncPolicyPartialSync = "partial-sync";
inline constexpr std::string_view kBackendProfileSyncPolicyObservationOnly =
    "observation-only";
inline constexpr std::string_view kBackendProfileSyncPolicyExportOnly = "export-only";
inline constexpr std::string_view kBackendProfileSyncPolicyUndeclaredBlocked =
    "undeclared_blocked";

inline constexpr std::string_view
    kBackendProfileRejectionReasonProfileIdNotFound = "backend_profile_id_not_found";

inline constexpr std::string_view
    kBackendProfileRejectionReasonMaintainedBaselineExactGpu =
        "backend_profile_maintained_exact_baseline_cannot_authorize_exact_gpu_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonDiagnosticsOnlyExactGpu =
        "backend_profile_diagnostics_only_cannot_authorize_exact_gpu_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonUnmaintainedCandidateExactGpu =
        "backend_profile_unmaintained_candidate_cannot_authorize_exact_gpu_support";

inline constexpr std::string_view
    kBackendProfileRejectionReasonMaintainedBaselineResidentState =
        "backend_profile_maintained_exact_baseline_cannot_authorize_resident_state_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonDiagnosticsOnlyResidentState =
        "backend_profile_diagnostics_only_cannot_authorize_resident_state_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonUnmaintainedCandidateResidentState =
        "backend_profile_unmaintained_candidate_cannot_authorize_resident_state_support";

inline constexpr std::string_view
    kBackendProfileRejectionReasonMaintainedBaselineShadowCompare =
        "backend_profile_maintained_exact_baseline_cannot_authorize_shadow_compare_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonDiagnosticsOnlyShadowCompare =
        "backend_profile_diagnostics_only_cannot_authorize_shadow_compare_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonUnmaintainedCandidateShadowCompare =
        "backend_profile_unmaintained_candidate_cannot_authorize_shadow_compare_support";

inline constexpr std::string_view
    kBackendProfileRejectionReasonMaintainedBaselineDeviceObservationView =
        "backend_profile_maintained_exact_baseline_cannot_authorize_device_observation_view_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonDiagnosticsOnlyDeviceObservationView =
        "backend_profile_diagnostics_only_cannot_authorize_device_observation_view_support";
inline constexpr std::string_view
    kBackendProfileRejectionReasonUnmaintainedCandidateDeviceObservationView =
        "backend_profile_unmaintained_candidate_cannot_authorize_device_observation_view_support";

enum class BackendProfileCapabilityClaim {
    exact_gpu_backend,
    resident_state,
    shadow_compare,
    device_observation_view,
};

struct BackendProfileProjectionEligibility {
    bool maintained_cpu_exact_baseline = false;
    bool exact_gpu_supported = false;
    bool resident_state_supported = false;
    bool shadow_supported = false;
    bool device_observation_view_supported = false;
    bool diagnostics_allowed = false;
};

struct BackendProfileSourceProvenance {
    std::string path;
    std::string section;
    std::string row_label;
    std::string accepted_by;
};

struct BackendProfileContract {
    std::string backend_profile_id;
    std::string profile_class;
    std::string comparison_reference;
    std::string host_state_owner;
    std::string backend_state_owner;
    std::string sync_policy;
    std::string state_scope;
    std::string parity_budget_ref;
    std::string observability_scope;
    std::string compatibility_rule;
    std::string deprecation_rule;
    std::string validation_gate;
    std::string maintained_status;
    BackendProfileProjectionEligibility projection_eligibility;
    BackendProfileSourceProvenance source_doc_provenance;
};

struct BackendProfileValidationResult {
    bool valid = true;
    std::vector<std::string> errors;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }
};

struct BackendProfileCapabilityGateResult {
    bool allowed = false;
    std::string backend_profile_id;
    std::string rejection_reason;
};

[[nodiscard]] inline bool is_blank(std::string_view value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

[[nodiscard]] inline bool contains_value(
    const std::vector<std::string>& items,
    std::string_view expected
) {
    return std::find(items.begin(), items.end(), expected) != items.end();
}

[[nodiscard]] inline bool is_known_backend_profile_class(std::string_view value) {
    return value == kBackendProfileClassReference ||
        value == kBackendProfileClassAcceleratedExact ||
        value == kBackendProfileClassResidentState ||
        value == kBackendProfileClassApproximate ||
        value == kBackendProfileClassDiagnosticsOnly;
}

[[nodiscard]] inline bool is_known_backend_profile_maintained_status(
    std::string_view value
) {
    return value == kBackendProfileMaintainedStatusMaintainedExactBaseline ||
        value == kBackendProfileMaintainedStatusDiagnosticsOnly ||
        value == kBackendProfileMaintainedStatusUnmaintainedCandidate;
}

[[nodiscard]] inline bool is_known_backend_profile_sync_policy(std::string_view value) {
    return value == kBackendProfileSyncPolicyHostOwned ||
        value == kBackendProfileSyncPolicyBackendOwned ||
        value == kBackendProfileSyncPolicyPartialSync ||
        value == kBackendProfileSyncPolicyObservationOnly ||
        value == kBackendProfileSyncPolicyExportOnly ||
        value == kBackendProfileSyncPolicyUndeclaredBlocked;
}

[[nodiscard]] inline bool is_maintained_backend_profile(
    const BackendProfileContract& profile
) {
    return profile.maintained_status ==
        kBackendProfileMaintainedStatusMaintainedExactBaseline;
}

[[nodiscard]] inline bool backend_profile_authorizes_capability_claim(
    const BackendProfileContract& profile,
    BackendProfileCapabilityClaim claim
) {
    switch (claim) {
        case BackendProfileCapabilityClaim::exact_gpu_backend:
            return profile.projection_eligibility.exact_gpu_supported;
        case BackendProfileCapabilityClaim::resident_state:
            return profile.projection_eligibility.resident_state_supported;
        case BackendProfileCapabilityClaim::shadow_compare:
            return profile.projection_eligibility.shadow_supported;
        case BackendProfileCapabilityClaim::device_observation_view:
            return profile.projection_eligibility.device_observation_view_supported;
    }
    return false;
}

[[nodiscard]] inline std::string_view rejection_reason_for_backend_profile_capability(
    const BackendProfileContract& profile,
    BackendProfileCapabilityClaim claim
) {
    const std::string_view maintained_status = profile.maintained_status;
    switch (claim) {
        case BackendProfileCapabilityClaim::exact_gpu_backend:
            if (maintained_status ==
                kBackendProfileMaintainedStatusMaintainedExactBaseline) {
                return kBackendProfileRejectionReasonMaintainedBaselineExactGpu;
            }
            if (maintained_status == kBackendProfileMaintainedStatusDiagnosticsOnly) {
                return kBackendProfileRejectionReasonDiagnosticsOnlyExactGpu;
            }
            return kBackendProfileRejectionReasonUnmaintainedCandidateExactGpu;
        case BackendProfileCapabilityClaim::resident_state:
            if (maintained_status ==
                kBackendProfileMaintainedStatusMaintainedExactBaseline) {
                return kBackendProfileRejectionReasonMaintainedBaselineResidentState;
            }
            if (maintained_status == kBackendProfileMaintainedStatusDiagnosticsOnly) {
                return kBackendProfileRejectionReasonDiagnosticsOnlyResidentState;
            }
            return kBackendProfileRejectionReasonUnmaintainedCandidateResidentState;
        case BackendProfileCapabilityClaim::shadow_compare:
            if (maintained_status ==
                kBackendProfileMaintainedStatusMaintainedExactBaseline) {
                return kBackendProfileRejectionReasonMaintainedBaselineShadowCompare;
            }
            if (maintained_status == kBackendProfileMaintainedStatusDiagnosticsOnly) {
                return kBackendProfileRejectionReasonDiagnosticsOnlyShadowCompare;
            }
            return kBackendProfileRejectionReasonUnmaintainedCandidateShadowCompare;
        case BackendProfileCapabilityClaim::device_observation_view:
            if (maintained_status ==
                kBackendProfileMaintainedStatusMaintainedExactBaseline) {
                return kBackendProfileRejectionReasonMaintainedBaselineDeviceObservationView;
            }
            if (maintained_status == kBackendProfileMaintainedStatusDiagnosticsOnly) {
                return kBackendProfileRejectionReasonDiagnosticsOnlyDeviceObservationView;
            }
            return kBackendProfileRejectionReasonUnmaintainedCandidateDeviceObservationView;
    }
    return kBackendProfileRejectionReasonProfileIdNotFound;
}

[[nodiscard]] inline BackendProfileValidationResult validate_backend_profile_contract(
    const BackendProfileContract& profile
) {
    BackendProfileValidationResult result{};

    if (is_blank(profile.backend_profile_id)) {
        result.add_error("backend_profile_id is required");
    }
    if (!is_known_backend_profile_class(profile.profile_class)) {
        result.add_error("profile_class must be a supported backend profile class");
    }
    if (is_blank(profile.comparison_reference)) {
        result.add_error("comparison_reference is required");
    }
    if (is_blank(profile.host_state_owner)) {
        result.add_error("host_state_owner is required");
    }
    if (is_blank(profile.backend_state_owner)) {
        result.add_error("backend_state_owner is required");
    }
    if (!is_known_backend_profile_sync_policy(profile.sync_policy)) {
        result.add_error("sync_policy must be a supported backend profile sync policy");
    }
    if (is_blank(profile.state_scope)) {
        result.add_error("state_scope is required");
    }
    if (is_blank(profile.parity_budget_ref)) {
        result.add_error("parity_budget_ref is required");
    }
    if (is_blank(profile.observability_scope)) {
        result.add_error("observability_scope is required");
    }
    if (is_blank(profile.compatibility_rule)) {
        result.add_error("compatibility_rule is required");
    }
    if (is_blank(profile.deprecation_rule)) {
        result.add_error("deprecation_rule is required");
    }
    if (is_blank(profile.validation_gate)) {
        result.add_error("validation_gate is required");
    }
    if (!is_known_backend_profile_maintained_status(profile.maintained_status)) {
        result.add_error("maintained_status must be a supported backend profile lifecycle");
    }
    if (is_blank(profile.source_doc_provenance.path)) {
        result.add_error("source_doc_provenance.path is required");
    }
    if (is_blank(profile.source_doc_provenance.section)) {
        result.add_error("source_doc_provenance.section is required");
    }
    if (is_blank(profile.source_doc_provenance.row_label)) {
        result.add_error("source_doc_provenance.row_label is required");
    }
    if (is_blank(profile.source_doc_provenance.accepted_by)) {
        result.add_error("source_doc_provenance.accepted_by is required");
    }

    if (profile.projection_eligibility.maintained_cpu_exact_baseline &&
        profile.backend_profile_id != kBackendProfileIdCpuExactReference) {
        result.add_error(
            "maintained_cpu_exact_baseline may only be true for cpu_exact.reference"
        );
    }
    if (profile.projection_eligibility.maintained_cpu_exact_baseline &&
        profile.maintained_status !=
            kBackendProfileMaintainedStatusMaintainedExactBaseline) {
        result.add_error(
            "maintained_cpu_exact_baseline requires maintained_exact_baseline status"
        );
    }
    if (profile.projection_eligibility.maintained_cpu_exact_baseline &&
        profile.profile_class != kBackendProfileClassReference) {
        result.add_error(
            "maintained_cpu_exact_baseline requires the reference profile class"
        );
    }
    if (!is_maintained_backend_profile(profile) &&
        (profile.projection_eligibility.exact_gpu_supported ||
         profile.projection_eligibility.resident_state_supported ||
         profile.projection_eligibility.shadow_supported ||
         profile.projection_eligibility.device_observation_view_supported)) {
        result.add_error(
            "non-maintained profiles must not authorize exact_gpu/resident_state/shadow/device_observation_view support"
        );
    }

    return result;
}

[[nodiscard]] inline BackendProfileValidationResult
validate_maintained_backend_profile_contract(const BackendProfileContract& profile) {
    BackendProfileValidationResult result = validate_backend_profile_contract(profile);
    if (!is_maintained_backend_profile(profile)) {
        result.add_error(
            "maintained backend profile validation requires maintained_exact_baseline status"
        );
    }
    if (!profile.projection_eligibility.maintained_cpu_exact_baseline) {
        result.add_error(
            "maintained backend profile must declare maintained_cpu_exact_baseline"
        );
    }
    return result;
}

[[nodiscard]] inline BackendProfileValidationResult validate_backend_profile_registry(
    const std::vector<BackendProfileContract>& registry
) {
    BackendProfileValidationResult result{};
    std::vector<std::string> seen_ids;
    seen_ids.reserve(registry.size());

    for (const auto& profile : registry) {
        if (contains_value(seen_ids, profile.backend_profile_id)) {
            result.add_error("duplicate backend_profile_id: " + profile.backend_profile_id);
            continue;
        }

        seen_ids.push_back(profile.backend_profile_id);
        const BackendProfileValidationResult profile_result =
            validate_backend_profile_contract(profile);
        for (const auto& error : profile_result.errors) {
            result.add_error(profile.backend_profile_id + ": " + error);
        }
    }

    if (registry.empty()) {
        result.add_error("backend profile registry seed must not be empty");
    }

    return result;
}

[[nodiscard]] inline const std::vector<BackendProfileContract>&
backend_profile_registry_seed() {
    static const std::vector<BackendProfileContract> registry = {
        BackendProfileContract{
            .backend_profile_id = std::string(kBackendProfileIdCpuExactReference),
            .profile_class = std::string(kBackendProfileClassReference),
            .comparison_reference = "self",
            .host_state_owner =
                "Host owns committed scheduler state, world state, observation envelopes, and diagnostics ancestry.",
            .backend_state_owner = "None for maintained truth.",
            .sync_policy = std::string(kBackendProfileSyncPolicyHostOwned),
            .state_scope =
                "Maintained CPU exact execution, event order, snapshots, observations, and diagnostics ancestry exposed through facade contracts.",
            .parity_budget_ref = "parity_budget.cpu_exact.reference.v1",
            .observability_scope =
                "Maintained facade outputs and structured diagnostics ancestry; diagnostics prose remains diagnostics-only.",
            .compatibility_rule =
                "Default fallback and comparison anchor for other profiles; no accelerated, resident-state, shadow, or device-observation support is implied.",
            .deprecation_rule =
                "Deprecate only through a replacement reference profile that preserves scheduler event order, snapshot identity, and validation obligations.",
            .validation_gate =
                "WP6-A registry review plus WP6-B reference budget acceptance; no GPU/resident/shadow promotion implied.",
            .maintained_status =
                std::string(kBackendProfileMaintainedStatusMaintainedExactBaseline),
            .projection_eligibility =
                BackendProfileProjectionEligibility{
                    .maintained_cpu_exact_baseline = true,
                    .exact_gpu_supported = false,
                    .resident_state_supported = false,
                    .shadow_supported = false,
                    .device_observation_view_supported = false,
                    .diagnostics_allowed = true,
                },
            .source_doc_provenance =
                BackendProfileSourceProvenance{
                    .path =
                        "docs/task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md",
                    .section = "3. Initial Registry",
                    .row_label = std::string(kBackendProfileIdCpuExactReference),
                    .accepted_by =
                        "docs/task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md",
                },
        },
        BackendProfileContract{
            .backend_profile_id =
                std::string(kBackendProfileIdGpuHelpersDiagnosticsOnly),
            .profile_class = std::string(kBackendProfileClassDiagnosticsOnly),
            .comparison_reference = std::string(kBackendProfileIdCpuExactReference),
            .host_state_owner = "Host remains owner of all maintained truth.",
            .backend_state_owner =
                "GPU/helper-local diagnostics buffers or probes only when labeled diagnostics-only.",
            .sync_policy = std::string(kBackendProfileSyncPolicyExportOnly),
            .state_scope =
                "GPU availability checks, helper traces, probe outputs, or debug artifacts that do not affect committed state.",
            .parity_budget_ref = "parity_budget.gpu_helpers.diagnostics_only.v1",
            .observability_scope =
                "Diagnostics traces, probe summaries, build/runtime availability facts; never maintained state.",
            .compatibility_rule =
                "Probeable deployment facts may be reported, but exact GPU, resident-state, shadow, and device-observation-view support stay false.",
            .deprecation_rule =
                "Remove or narrow if a helper starts influencing committed state; promote only through a separate maintained profile.",
            .validation_gate =
                "Diagnostics labeling review; tests may assert report-only behavior but cannot accept it as maintained parity.",
            .maintained_status =
                std::string(kBackendProfileMaintainedStatusDiagnosticsOnly),
            .projection_eligibility =
                BackendProfileProjectionEligibility{
                    .maintained_cpu_exact_baseline = false,
                    .exact_gpu_supported = false,
                    .resident_state_supported = false,
                    .shadow_supported = false,
                    .device_observation_view_supported = false,
                    .diagnostics_allowed = true,
                },
            .source_doc_provenance =
                BackendProfileSourceProvenance{
                    .path =
                        "docs/task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md",
                    .section = "3. Initial Registry",
                    .row_label =
                        std::string(kBackendProfileIdGpuHelpersDiagnosticsOnly),
                    .accepted_by =
                        "docs/task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md",
                },
        },
        BackendProfileContract{
            .backend_profile_id =
                std::string(kBackendProfileIdGpuExactUnmaintainedCandidate),
            .profile_class = std::string(kBackendProfileClassAcceleratedExact),
            .comparison_reference = std::string(kBackendProfileIdCpuExactReference),
            .host_state_owner =
                "Host ownership of committed state is assumed until a maintained profile states otherwise.",
            .backend_state_owner =
                "No backend-owned maintained state declared; GPU execution internals are not authoritative.",
            .sync_policy = std::string(kBackendProfileSyncPolicyUndeclaredBlocked),
            .state_scope =
                "Placeholder for a possible exact GPU world-step or accelerated exact path; no maintained exact GPU support is claimed.",
            .parity_budget_ref =
                "parity_budget.gpu_exact.unmaintained_candidate.v1",
            .observability_scope =
                "Candidate diagnostics only, such as mismatch evidence or performance notes, when explicitly labeled.",
            .compatibility_rule =
                "Deployment facts may explain GPU helper availability, but maintained exact GPU support must remain false.",
            .deprecation_rule =
                "Delete if no exact promotion plan remains; replace only after ownership, sync, parity, and validation gates pass.",
            .validation_gate =
                "Blocked until exact event order, snapshot identity, ownership split, sync barriers, parity budget, and replay/validation gates are accepted.",
            .maintained_status =
                std::string(kBackendProfileMaintainedStatusUnmaintainedCandidate),
            .projection_eligibility =
                BackendProfileProjectionEligibility{
                    .maintained_cpu_exact_baseline = false,
                    .exact_gpu_supported = false,
                    .resident_state_supported = false,
                    .shadow_supported = false,
                    .device_observation_view_supported = false,
                    .diagnostics_allowed = true,
                },
            .source_doc_provenance =
                BackendProfileSourceProvenance{
                    .path =
                        "docs/task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md",
                    .section = "3. Initial Registry",
                    .row_label =
                        std::string(
                            kBackendProfileIdGpuExactUnmaintainedCandidate
                        ),
                    .accepted_by =
                        "docs/task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md",
                },
        },
        BackendProfileContract{
            .backend_profile_id = std::string(
                kBackendProfileIdResidentStateUnmaintainedCandidate
            ),
            .profile_class = std::string(kBackendProfileClassResidentState),
            .comparison_reference = std::string(kBackendProfileIdCpuExactReference),
            .host_state_owner =
                "Host remains owner of maintained committed state until a profile declares host-visible reconstruction or export rules.",
            .backend_state_owner =
                "Candidate backend-resident operational shards are not maintained truth.",
            .sync_policy = std::string(kBackendProfileSyncPolicyUndeclaredBlocked),
            .state_scope =
                "Placeholder for backend-resident observation, physics, or operational state; no maintained resident-state support is claimed.",
            .parity_budget_ref =
                "parity_budget.resident_state.unmaintained_candidate.v1",
            .observability_scope =
                "Candidate diagnostics only; unsynced backend-local state must stay outside maintained parity.",
            .compatibility_rule =
                "Probeable backend presence does not imply resident-state ownership or device-observation-view support.",
            .deprecation_rule =
                "Remove or split if the resident scope cannot be reconstructed, exported, or synchronized under resident-state boundary rules.",
            .validation_gate =
                "Blocked until ownership split, sync cadence/trigger, barriers, host-visible reconstruction/export, parity budget, and validation gates are accepted.",
            .maintained_status =
                std::string(kBackendProfileMaintainedStatusUnmaintainedCandidate),
            .projection_eligibility =
                BackendProfileProjectionEligibility{
                    .maintained_cpu_exact_baseline = false,
                    .exact_gpu_supported = false,
                    .resident_state_supported = false,
                    .shadow_supported = false,
                    .device_observation_view_supported = false,
                    .diagnostics_allowed = true,
                },
            .source_doc_provenance =
                BackendProfileSourceProvenance{
                    .path =
                        "docs/task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md",
                    .section = "3. Initial Registry",
                    .row_label = std::string(
                        kBackendProfileIdResidentStateUnmaintainedCandidate
                    ),
                    .accepted_by =
                        "docs/task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md",
                },
        },
        BackendProfileContract{
            .backend_profile_id = std::string(
                kBackendProfileIdShadowCompareUnmaintainedCandidate
            ),
            .profile_class = std::string(kBackendProfileClassDiagnosticsOnly),
            .comparison_reference = std::string(kBackendProfileIdCpuExactReference),
            .host_state_owner = "Host reference path owns committed state.",
            .backend_state_owner =
                "Shadow helper outputs are diagnostics-only and cannot own committed state.",
            .sync_policy = std::string(kBackendProfileSyncPolicyExportOnly),
            .state_scope =
                "Placeholder for shadow comparison reports or offline A/B evidence; no maintained shadow support is claimed.",
            .parity_budget_ref =
                "parity_budget.shadow_compare.unmaintained_candidate.v1",
            .observability_scope =
                "Comparison reports, mismatch summaries, and replay evidence labeled diagnostics-only.",
            .compatibility_rule =
                "Shadow output cannot affect committed state, fallback control flow, or maintained support.",
            .deprecation_rule =
                "Remove if reports are not used; promote only by defining shadow scope, non-interference, diagnostics separation, and validation evidence.",
            .validation_gate =
                "Blocked until shadow scope, non-interference rule, diagnostics separation, parity budget if maintained, and validation review are accepted.",
            .maintained_status =
                std::string(kBackendProfileMaintainedStatusUnmaintainedCandidate),
            .projection_eligibility =
                BackendProfileProjectionEligibility{
                    .maintained_cpu_exact_baseline = false,
                    .exact_gpu_supported = false,
                    .resident_state_supported = false,
                    .shadow_supported = false,
                    .device_observation_view_supported = false,
                    .diagnostics_allowed = true,
                },
            .source_doc_provenance =
                BackendProfileSourceProvenance{
                    .path =
                        "docs/task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md",
                    .section = "3. Initial Registry",
                    .row_label = std::string(
                        kBackendProfileIdShadowCompareUnmaintainedCandidate
                    ),
                    .accepted_by =
                        "docs/task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md",
                },
        },
    };
    return registry;
}

[[nodiscard]] inline const BackendProfileContract* find_backend_profile_contract(
    std::string_view backend_profile_id
) {
    const auto& registry = backend_profile_registry_seed();
    const auto it = std::find_if(
        registry.begin(),
        registry.end(),
        [backend_profile_id](const BackendProfileContract& profile) {
            return profile.backend_profile_id == backend_profile_id;
        }
    );
    if (it == registry.end()) {
        return nullptr;
    }
    return &(*it);
}

[[nodiscard]] inline std::vector<const BackendProfileContract*>
enumerate_maintained_backend_profile_contracts() {
    std::vector<const BackendProfileContract*> profiles;
    for (const auto& profile : backend_profile_registry_seed()) {
        if (is_maintained_backend_profile(profile)) {
            profiles.push_back(&profile);
        }
    }
    return profiles;
}

[[nodiscard]] inline std::optional<BackendProfileValidationResult>
validate_backend_profile_registry_seed() {
    const BackendProfileValidationResult result =
        validate_backend_profile_registry(backend_profile_registry_seed());
    if (result.valid) {
        return std::nullopt;
    }
    return result;
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_capability(
    const BackendProfileContract& profile,
    BackendProfileCapabilityClaim claim
) {
    BackendProfileCapabilityGateResult result{};
    result.backend_profile_id = profile.backend_profile_id;
    result.allowed = backend_profile_authorizes_capability_claim(profile, claim);
    if (!result.allowed) {
        result.rejection_reason = std::string(
            rejection_reason_for_backend_profile_capability(profile, claim)
        );
    }
    return result;
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_capability(
    std::string_view backend_profile_id,
    BackendProfileCapabilityClaim claim
) {
    const BackendProfileContract* profile =
        find_backend_profile_contract(backend_profile_id);
    if (profile == nullptr) {
        BackendProfileCapabilityGateResult result{};
        result.backend_profile_id = std::string(backend_profile_id);
        result.allowed = false;
        result.rejection_reason =
            std::string(kBackendProfileRejectionReasonProfileIdNotFound);
        return result;
    }
    return validate_backend_profile_for_capability(*profile, claim);
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_exact_gpu_support(std::string_view backend_profile_id) {
    return validate_backend_profile_for_capability(
        backend_profile_id,
        BackendProfileCapabilityClaim::exact_gpu_backend
    );
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_resident_state_support(
    std::string_view backend_profile_id
) {
    return validate_backend_profile_for_capability(
        backend_profile_id,
        BackendProfileCapabilityClaim::resident_state
    );
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_shadow_compare_support(
    std::string_view backend_profile_id
) {
    return validate_backend_profile_for_capability(
        backend_profile_id,
        BackendProfileCapabilityClaim::shadow_compare
    );
}

[[nodiscard]] inline BackendProfileCapabilityGateResult
validate_backend_profile_for_device_observation_view_support(
    std::string_view backend_profile_id
) {
    return validate_backend_profile_for_capability(
        backend_profile_id,
        BackendProfileCapabilityClaim::device_observation_view
    );
}

}  // namespace runtime::backend_profiles
