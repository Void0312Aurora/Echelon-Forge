#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace runtime::projection_contracts {

inline constexpr std::string_view kRuntimeCompositionRequestSchemaVersion =
    "echelon_forge.runtime_composition_request.v1";
inline constexpr std::string_view kAdmittedCatalogLockSchemaVersion =
    "echelon_forge.admitted_catalog_lock.v1";
inline constexpr std::string_view kAdmittedCatalogLockContractVersion =
    "echelon_forge.admitted_catalog_lock_contract.v1";
inline constexpr std::string_view kOwnerAuthorityRegistrySchemaVersion =
    "echelon_forge.owner_authority_registry.v1";
inline constexpr std::string_view kOwnerAuthorityRegistryId =
    "echelon_forge.runtime_composition_owners";
inline constexpr std::string_view kCanonicalizationId = "echelon_forge.sorted_utf8_json.v1";
inline constexpr std::string_view kHashAlgorithm = "sha256";

inline constexpr std::string_view kCategoryModel = "model";
inline constexpr std::string_view kCategorySystem = "system";
inline constexpr std::string_view kCategoryBackend = "backend";
inline constexpr std::string_view kCategoryDomain = "domain";
inline constexpr std::string_view kCategoryEvidence = "evidence";
inline constexpr std::string_view kCategorySecurity = "security";

struct ProjectionContractVersions {
    std::string composition;
    std::string runtime;
    std::string content;
    std::string stage;
    bool operator==(const ProjectionContractVersions &) const = default;
};

struct RuntimeCompositionIntent {
    std::string simulation_id;
    std::string policy_id;
    std::string evaluation_id;
    bool operator==(const RuntimeCompositionIntent &) const = default;
};

struct RuntimeCompositionProfileConstraint {
    std::string profile_id;
    std::string profile_version;
    bool operator==(const RuntimeCompositionProfileConstraint &) const = default;
};

struct RuntimeCompositionRequest {
    std::string schema_version;
    std::string request_id;
    std::string request_version;
    ProjectionContractVersions contract_versions;
    RuntimeCompositionIntent intent;
    RuntimeCompositionProfileConstraint requested_profile;
    std::vector<std::string> required_capabilities;
    std::vector<std::string> required_policies;
    // Canonical JSON bytes for the schema's recursive ``configuration`` value.
    // The producer-neutral value contract is intentionally represented as
    // bytes here so native callers cannot smuggle a platform-specific type.
    std::string configuration;
    bool operator==(const RuntimeCompositionRequest &) const = default;
};

struct CatalogLockProvenance {
    std::string artifact_kind;
    std::string artifact_identity;
    std::optional<std::string> artifact_sha256;
    bool operator==(const CatalogLockProvenance &) const = default;
};

struct AdmittedCatalogEntry {
    std::string category;
    std::string owner_id;
    std::string descriptor_id;
    std::string implementation_id;
    std::string implementation_version;
    std::vector<std::string> capabilities;
    CatalogLockProvenance provenance;
    std::string trust_decision;
    bool operator==(const AdmittedCatalogEntry &) const = default;
};

struct CatalogLockCategoryAuthority {
    std::string category;
    std::string owner_id;
    bool operator==(const CatalogLockCategoryAuthority &) const = default;
};

struct AdmittedCatalogLock {
    std::string schema_version;
    std::string contract_version;
    std::string lock_id;
    std::string lock_version;
    std::string request_schema_version;
    std::string request_sha256;
    std::string authority_registry_sha256;
    std::vector<CatalogLockCategoryAuthority> category_authorities;
    std::vector<AdmittedCatalogEntry> entries;
    std::string canonicalization;
    std::string hash_algorithm;
    std::string canonical_json;
    std::string lock_sha256;
    bool operator==(const AdmittedCatalogLock &) const = default;
};

struct ProjectionValidationIssue {
    std::string code;
    std::string path;
    std::string detail;
};

struct ProjectionValidationResult {
    bool valid = false;
    std::vector<ProjectionValidationIssue> issues;
};

// Shared native identity primitive for versioned canonical JSON artifacts.
// Callers must pass the exact canonical UTF-8 bytes defined by the contract.
[[nodiscard]] std::string canonical_sha256_hex(std::string_view canonical_bytes);

// Native revalidation boundary for the producer-neutral P2-C0 projection.
// The function is deliberately JSON-facing: it verifies the exact canonical
// bytes and identity fields before any P1-B lowering or provider construction.
[[nodiscard]] ProjectionValidationResult
validate_runtime_composition_projection_json(std::string_view request_json,
                                             std::string_view lock_json,
                                             std::string_view authority_registry_json);

} // namespace runtime::projection_contracts
