#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace runtime::composition_evidence_contracts {

inline constexpr std::string_view kSchemaVersion = "echelon_forge.runtime_composition_evidence.v1";
inline constexpr std::string_view kContractVersion = "1.0.0";
inline constexpr std::string_view kCanonicalization = "echelon_forge.sorted_utf8_json.v1";
inline constexpr std::string_view kHashAlgorithm = "sha256";

struct ProviderVersionEvidence {
    std::string provider_id;
    std::string implementation_version;
    bool operator==(const ProviderVersionEvidence &) const = default;
};

struct BackendEvidence {
    std::string provider_id;
    std::string implementation_version;
    std::string backend_profile_id;
    std::vector<std::string> admitted_capabilities;
    bool operator==(const BackendEvidence &) const = default;
};

struct ScopeGenerationEvidence {
    std::string scope;
    std::string instance_id;
    std::uint64_t generation = 0;
    bool operator==(const ScopeGenerationEvidence &) const = default;
};

struct WorldInstanceEvidence {
    std::uint64_t world_index = 0;
    std::vector<ScopeGenerationEvidence> scope_generations;
    bool operator==(const WorldInstanceEvidence &) const = default;
};

struct RuntimeCompositionEvidence {
    std::string schema_version;
    std::string evidence_contract_version;
    std::string composition_id;
    std::string requested_profile_id;
    std::string requested_profile_version;
    std::string runtime_request_sha256;
    std::string requested_manifest_sha256;
    std::string resolved_manifest_sha256;
    std::string catalog_lock_sha256;
    std::string profile_projection_sha256;
    std::string resolver_contract_version;
    std::vector<ProviderVersionEvidence> provider_versions;
    BackendEvidence backend;
    std::string executable_graph_sha256;
    std::string stage_contract_version;
    std::string host_mode;
    std::string binding_version;
    std::vector<WorldInstanceEvidence> world_instances;
    std::string canonicalization;
    std::string hash_algorithm;
    std::string canonical_json;
    std::string evidence_sha256;
    bool operator==(const RuntimeCompositionEvidence &) const = default;
};

struct RuntimeCompositionEvidenceResult {
    bool available = false;
    RuntimeCompositionEvidence evidence;
    std::string error_code;
    std::string error_detail;
};

struct EvidenceValidationIssue {
    std::string code;
    std::string path;
    std::string detail;
};

struct EvidenceValidationResult {
    bool valid = false;
    std::vector<EvidenceValidationIssue> issues;
};

struct EvidenceComparisonResult {
    bool compatible = false;
    std::vector<std::string> mismatches;
};

// Normalizes order-sensitive set-like fields, writes canonical_json, and seals
// the evidence identity. Runtime scope-generation rows remain explicit inputs.
[[nodiscard]] RuntimeCompositionEvidence
seal_runtime_composition_evidence(RuntimeCompositionEvidence evidence);

[[nodiscard]] EvidenceValidationResult
validate_runtime_composition_evidence(const RuntimeCompositionEvidence &evidence);

// Strict comparison for maintained replay/comparison admission. This bounded
// P5-A contract has no migration fallback: any unexplained identity difference
// is returned as a named mismatch and compatibility is false.
[[nodiscard]] EvidenceComparisonResult
compare_runtime_composition_evidence(const RuntimeCompositionEvidence &expected,
                                     const RuntimeCompositionEvidence &actual);

} // namespace runtime::composition_evidence_contracts
