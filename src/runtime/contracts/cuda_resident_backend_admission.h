#pragma once

#include <algorithm>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/parity_budget_contracts.h"

namespace runtime::cuda_resident {

inline constexpr std::string_view kCapabilityManifestIdBoundedAirExecutionV1 =
    "cuda_resident.air_execution.fixed_step.v1";

inline constexpr std::string_view kFeatureCanonicalWorldSetup =
    "canonical_world_setup.fixed_air_fixture";
inline constexpr std::string_view kFeaturePilotFlightControls = "pilot_action.flight_controls";
inline constexpr std::string_view kFeatureAirframeDynamics = "airframe_dynamics.six_dof";
inline constexpr std::string_view kFeatureInstruments = "instruments.air_execution";
inline constexpr std::string_view kFeatureAgentObservation = "observation.agent_air_execution";
inline constexpr std::string_view kFeatureReward = "reward.execution_episode";
inline constexpr std::string_view kFeatureTermination = "termination.execution_episode";
inline constexpr std::string_view kFeatureHostSnapshotExport = "export.host_snapshot";
inline constexpr std::string_view kFeatureDeviceObservationExport =
    "export.device_observation_view";

inline constexpr std::string_view kBackendAdmissionRejectionMissingProfile =
    "backend_request_missing_profile_id";
inline constexpr std::string_view kBackendAdmissionRejectionUnknownProfile =
    "backend_request_unknown_profile_id";
inline constexpr std::string_view kBackendAdmissionRejectionUnsupportedProfile =
    "backend_request_profile_not_selectable";
inline constexpr std::string_view kBackendAdmissionRejectionMissingManifest =
    "backend_request_missing_capability_manifest";
inline constexpr std::string_view kBackendAdmissionRejectionUnknownManifest =
    "backend_request_unknown_capability_manifest";
inline constexpr std::string_view kBackendAdmissionRejectionManifestProfileMismatch =
    "backend_request_manifest_profile_mismatch";
inline constexpr std::string_view kBackendAdmissionRejectionManifestInvalid =
    "backend_request_capability_manifest_invalid";
inline constexpr std::string_view kBackendAdmissionRejectionRequiredFeatureMissing =
    "backend_request_required_manifest_feature_missing";
inline constexpr std::string_view kBackendAdmissionRejectionUnsupportedFeature =
    "backend_request_feature_not_supported_by_manifest";
inline constexpr std::string_view kBackendAdmissionRejectionParityBudget =
    "backend_request_parity_budget_invalid_or_mismatched";
inline constexpr std::string_view kBackendAdmissionRejectionCandidateOptInRequired =
    "backend_request_unmaintained_candidate_opt_in_required";
inline constexpr std::string_view kBackendAdmissionRejectionExperimentalBackendNotCompiled =
    "backend_request_experimental_backend_not_compiled";
inline constexpr std::string_view kBackendAdmissionRejectionManifestNotCompiled =
    "backend_request_manifest_not_supported_by_compiled_backend";
inline constexpr std::string_view kBackendAdmissionRejectionCpuManifestForbidden =
    "backend_request_cpu_reference_does_not_accept_candidate_manifest";

struct CapabilityManifest {
    std::string manifest_id;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    std::string fixture_scope;
    bool fixed_step_only = true;
    bool dynamic_entity_families = false;
    bool implicit_cpu_fallback = false;
    std::vector<std::string> required_feature_ids;
    std::vector<std::string> supported_feature_ids;
    std::vector<std::string> forbidden_feature_ids;

    bool operator==(const CapabilityManifest &) const = default;
};

struct CapabilityManifestValidationResult {
    bool valid = true;
    std::vector<std::string> errors;

    void add_error(std::string error) {
        valid = false;
        errors.push_back(std::move(error));
    }
};

struct BackendRequest {
    std::string backend_profile_id;
    std::string capability_manifest_id;
    std::string parity_budget_ref;
    std::vector<std::string> requested_feature_ids;
    bool allow_unmaintained_candidate = false;
};

// Supplied by trusted build/factory code, never by the request. RB2's facade
// intentionally reports no compiled experimental backend; RB3 may open that
// availability only after its lifecycle shell exists.
struct BackendAvailability {
    bool compiled_experimental_backend = false;
    std::vector<std::string> supported_manifest_ids;
};

struct BackendAdmissionResult {
    bool admitted = false;
    bool maintained_selection = false;
    bool experimental_selection = false;
    std::string backend_profile_id;
    std::string capability_manifest_id;
    std::string parity_budget_ref;
    std::vector<std::string> admitted_feature_ids;
    std::string rejection_reason;
    std::vector<std::string> errors;

    void reject(std::string reason, std::string error) {
        admitted = false;
        maintained_selection = false;
        experimental_selection = false;
        rejection_reason = std::move(reason);
        errors.push_back(std::move(error));
    }
};

[[nodiscard]] inline bool contains(const std::vector<std::string> &values,
                                   std::string_view expected) {
    return std::find(values.begin(), values.end(), expected) != values.end();
}

[[nodiscard]] inline const std::vector<std::string> &
bounded_air_execution_required_feature_contract() {
    static const std::vector<std::string> features = {
        std::string(kFeatureCanonicalWorldSetup),
        std::string(kFeaturePilotFlightControls),
        std::string(kFeatureAirframeDynamics),
        std::string(kFeatureInstruments),
        std::string(kFeatureAgentObservation),
        std::string(kFeatureReward),
        std::string(kFeatureTermination),
        std::string(kFeatureHostSnapshotExport),
        std::string(kFeatureDeviceObservationExport),
    };
    return features;
}

[[nodiscard]] inline const std::vector<std::string> &
bounded_air_execution_supported_feature_contract() {
    return bounded_air_execution_required_feature_contract();
}

[[nodiscard]] inline const std::vector<std::string> &
bounded_air_execution_forbidden_feature_contract() {
    static const std::vector<std::string> features = {
        "pilot_action.sensor_controls",
        "pilot_action.weapon_controls",
        "dynamic_entity_families",
        "spatial_interaction",
        "sensors",
        "communications",
        "electronic_warfare",
        "weapons_and_effects",
        "damage",
        "logistics",
        "naval",
        "ground",
    };
    return features;
}

[[nodiscard]] inline const CapabilityManifest &bounded_air_execution_manifest() {
    static const CapabilityManifest manifest{
        .manifest_id = std::string(kCapabilityManifestIdBoundedAirExecutionV1),
        .backend_profile_id =
            std::string(backend_profiles::kBackendProfileIdResidentStateUnmaintainedCandidate),
        .parity_budget_ref = std::string(parity::kParityBudgetResidentStateUnmaintainedCandidateV1),
        .fixture_scope =
            "fixed-step bounded air execution: setup, flight controls, airframe dynamics, "
            "instruments, observation, reward, termination, and declared export barriers",
        .fixed_step_only = true,
        .dynamic_entity_families = false,
        .implicit_cpu_fallback = false,
        .required_feature_ids = bounded_air_execution_required_feature_contract(),
        .supported_feature_ids = bounded_air_execution_supported_feature_contract(),
        .forbidden_feature_ids = bounded_air_execution_forbidden_feature_contract(),
    };
    return manifest;
}

[[nodiscard]] inline const std::vector<CapabilityManifest> &capability_manifest_registry() {
    static const std::vector<CapabilityManifest> registry = {bounded_air_execution_manifest()};
    return registry;
}

[[nodiscard]] inline const CapabilityManifest *
find_capability_manifest(std::string_view manifest_id) {
    const auto &registry = capability_manifest_registry();
    const auto it =
        std::find_if(registry.begin(), registry.end(),
                     [manifest_id](const auto &entry) { return entry.manifest_id == manifest_id; });
    return it == registry.end() ? nullptr : &(*it);
}

[[nodiscard]] inline CapabilityManifestValidationResult
validate_capability_manifest(const CapabilityManifest &manifest) {
    CapabilityManifestValidationResult result{};
    if (manifest.manifest_id.empty()) {
        result.add_error("manifest_id is required");
    }
    if (manifest.backend_profile_id.empty()) {
        result.add_error("backend_profile_id is required");
    }
    if (manifest.parity_budget_ref.empty()) {
        result.add_error("parity_budget_ref is required");
    }
    if (manifest.fixture_scope.empty()) {
        result.add_error("fixture_scope is required");
    }
    if (!manifest.fixed_step_only) {
        result.add_error("the CUDA-resident candidate manifest must remain fixed-step only");
    }
    if (manifest.dynamic_entity_families) {
        result.add_error(
            "the CUDA-resident candidate manifest must reject dynamic entity families");
    }
    if (manifest.implicit_cpu_fallback) {
        result.add_error("the CUDA-resident candidate manifest must forbid implicit CPU fallback");
    }
    if (manifest.required_feature_ids.empty() || manifest.supported_feature_ids.empty()) {
        result.add_error("required and supported feature sets are required");
    }
    for (const auto &feature_id : manifest.required_feature_ids) {
        if (!contains(manifest.supported_feature_ids, feature_id)) {
            result.add_error("required feature is not supported: " + feature_id);
        }
    }
    for (const auto &feature_id : manifest.forbidden_feature_ids) {
        if (contains(manifest.supported_feature_ids, feature_id)) {
            result.add_error("feature is both supported and forbidden: " + feature_id);
        }
    }
    if (manifest.manifest_id == kCapabilityManifestIdBoundedAirExecutionV1 &&
        manifest != bounded_air_execution_manifest()) {
        result.add_error(
            "the bounded-air manifest must exactly match its canonical identity and feature sets");
    }
    return result;
}

[[nodiscard]] inline BackendRequest make_cpu_reference_backend_request() {
    return BackendRequest{
        .backend_profile_id = std::string(backend_profiles::kBackendProfileIdCpuExactReference),
        .capability_manifest_id = {},
        .parity_budget_ref = std::string(parity::kParityBudgetCpuExactReferenceV1),
        .requested_feature_ids = {},
        .allow_unmaintained_candidate = false,
    };
}

[[nodiscard]] inline BackendRequest make_bounded_air_execution_candidate_request() {
    const CapabilityManifest &manifest = bounded_air_execution_manifest();
    return BackendRequest{
        .backend_profile_id = manifest.backend_profile_id,
        .capability_manifest_id = manifest.manifest_id,
        .parity_budget_ref = manifest.parity_budget_ref,
        .requested_feature_ids = manifest.required_feature_ids,
        .allow_unmaintained_candidate = true,
    };
}

[[nodiscard]] inline BackendAdmissionResult
admit_backend_request(const BackendRequest &request, const BackendAvailability &availability) {
    BackendAdmissionResult result{};
    result.backend_profile_id = request.backend_profile_id;
    result.capability_manifest_id = request.capability_manifest_id;
    result.parity_budget_ref = request.parity_budget_ref;

    if (request.backend_profile_id.empty()) {
        result.reject(std::string(kBackendAdmissionRejectionMissingProfile),
                      "backend_profile_id is required");
        return result;
    }

    const backend_profiles::BackendProfileContract *profile =
        backend_profiles::find_backend_profile_contract(request.backend_profile_id);
    if (profile == nullptr) {
        result.reject(std::string(kBackendAdmissionRejectionUnknownProfile),
                      "backend_profile_id was not found in the registry");
        return result;
    }

    const parity::ParityBudgetValidationResult budget_result =
        parity::validate_profile_owned_parity_budget(
            request.backend_profile_id, profile->profile_class, request.parity_budget_ref);
    if (!budget_result.valid || profile->parity_budget_ref != request.parity_budget_ref) {
        result.reject(std::string(kBackendAdmissionRejectionParityBudget),
                      "profile-owned parity budget is missing, invalid, or mismatched");
        result.errors.insert(result.errors.end(), budget_result.errors.begin(),
                             budget_result.errors.end());
        return result;
    }

    if (request.backend_profile_id == backend_profiles::kBackendProfileIdCpuExactReference) {
        if (!request.capability_manifest_id.empty() || !request.requested_feature_ids.empty() ||
            request.allow_unmaintained_candidate) {
            result.reject(std::string(kBackendAdmissionRejectionCpuManifestForbidden),
                          "CPU reference selection must not carry candidate manifest fields");
            return result;
        }
        if (!budget_result.accepted_for_maintained_use) {
            result.reject(std::string(kBackendAdmissionRejectionParityBudget),
                          "CPU reference budget is not accepted for maintained use");
            return result;
        }
        result.admitted = true;
        result.maintained_selection = true;
        return result;
    }

    if (request.backend_profile_id !=
        backend_profiles::kBackendProfileIdResidentStateUnmaintainedCandidate) {
        result.reject(std::string(kBackendAdmissionRejectionUnsupportedProfile),
                      "backend admission selects only the CPU reference or bounded "
                      "CUDA-resident candidate");
        return result;
    }
    if (!request.allow_unmaintained_candidate) {
        result.reject(std::string(kBackendAdmissionRejectionCandidateOptInRequired),
                      "unmaintained candidate selection requires explicit opt-in");
        return result;
    }
    if (request.capability_manifest_id.empty()) {
        result.reject(std::string(kBackendAdmissionRejectionMissingManifest),
                      "candidate selection requires capability_manifest_id");
        return result;
    }

    const CapabilityManifest *manifest = find_capability_manifest(request.capability_manifest_id);
    if (manifest == nullptr) {
        result.reject(std::string(kBackendAdmissionRejectionUnknownManifest),
                      "capability_manifest_id was not found in the candidate registry");
        return result;
    }
    if (manifest->backend_profile_id != request.backend_profile_id ||
        manifest->parity_budget_ref != request.parity_budget_ref) {
        result.reject(std::string(kBackendAdmissionRejectionManifestProfileMismatch),
                      "manifest profile or parity-budget ownership does not match the request");
        return result;
    }
    const CapabilityManifestValidationResult manifest_result =
        validate_capability_manifest(*manifest);
    if (!manifest_result.valid) {
        result.reject(std::string(kBackendAdmissionRejectionManifestInvalid),
                      "capability manifest failed contract validation");
        result.errors.insert(result.errors.end(), manifest_result.errors.begin(),
                             manifest_result.errors.end());
        return result;
    }
    for (const auto &required_feature_id : manifest->required_feature_ids) {
        if (!contains(request.requested_feature_ids, required_feature_id)) {
            result.reject(std::string(kBackendAdmissionRejectionRequiredFeatureMissing),
                          "request omitted required feature: " + required_feature_id);
            return result;
        }
    }
    for (const auto &feature_id : request.requested_feature_ids) {
        if (!contains(manifest->supported_feature_ids, feature_id)) {
            result.reject(std::string(kBackendAdmissionRejectionUnsupportedFeature),
                          "request contains unsupported feature: " + feature_id);
            return result;
        }
    }
    if (!availability.compiled_experimental_backend) {
        result.reject(std::string(kBackendAdmissionRejectionExperimentalBackendNotCompiled),
                      "no compiled experimental CUDA-resident backend is available");
        return result;
    }
    if (!contains(availability.supported_manifest_ids, manifest->manifest_id)) {
        result.reject(std::string(kBackendAdmissionRejectionManifestNotCompiled),
                      "compiled experimental backend does not advertise this manifest");
        return result;
    }

    result.admitted = true;
    result.experimental_selection = true;
    result.admitted_feature_ids = request.requested_feature_ids;
    return result;
}

} // namespace runtime::cuda_resident
