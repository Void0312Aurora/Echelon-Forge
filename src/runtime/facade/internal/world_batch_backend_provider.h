#pragma once

#include "runtime/facade/internal/world_batch_backend.h"
#include "runtime/contracts/world_batch_backend_provider_contract.h"

#include <cstddef>
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace runtime::backend_provider {

inline constexpr std::string_view kBackendProviderRequestSchemaVersion =
    runtime::world_batch_backend_contracts::kRequestSchemaVersion;
inline constexpr std::string_view kWorldBatchBackendServiceId =
    runtime::world_batch_backend_contracts::kSemanticServiceId;
inline constexpr std::string_view kBuiltinFlecsCpuProviderId =
    runtime::world_batch_backend_contracts::kDefaultProviderId;
inline constexpr std::string_view kCpuExactCapabilityId =
    runtime::world_batch_backend_contracts::kCpuExactCapabilityId;

inline constexpr std::string_view kErrorInvalidRequestSchema =
    "backend_provider.invalid_request_schema";
inline constexpr std::string_view kErrorProfileNotFound = "backend_provider.profile_not_found";
inline constexpr std::string_view kErrorProfileNotMaintained =
    "backend_provider.profile_not_maintained";
inline constexpr std::string_view kErrorProviderNotFound = "backend_provider.provider_not_found";
inline constexpr std::string_view kErrorProviderProfileMismatch =
    "backend_provider.provider_profile_mismatch";
inline constexpr std::string_view kErrorProviderVersionMismatch =
    "backend_provider.provider_version_mismatch";
inline constexpr std::string_view kErrorCapabilityRequired = "backend_provider.capability_required";
inline constexpr std::string_view kErrorCapabilityDuplicate =
    "backend_provider.capability_duplicate";
inline constexpr std::string_view kErrorCapabilityNotAdmitted =
    "backend_provider.capability_not_admitted";
inline constexpr std::string_view kErrorCapabilityMissing = "backend_provider.capability_missing";
inline constexpr std::string_view kErrorProviderContractInvalid =
    "backend_provider.provider_contract_invalid";
inline constexpr std::string_view kErrorConstructionFailed = "backend_provider.construction_failed";

struct WorldBatchBackendProviderRequest {
    std::string schema_version;
    std::string backend_profile_id;
    std::string provider_id;
    std::string provider_implementation_version;
    std::vector<std::string> required_capabilities;
    bool operator==(const WorldBatchBackendProviderRequest &) const = default;
};

struct WorldBatchBackendProviderError {
    std::string code;
    std::string subject;
    std::string detail;
};

struct WorldBatchBackendProviderIdentity {
    std::string provider_id;
    std::string implementation_version;
    std::string backend_profile_id;
    std::vector<std::string> admitted_capabilities;
};

struct WorldBatchBackendProviderMaterialization {
    std::unique_ptr<IWorldBatchBackend> backend;
    WorldBatchBackendProviderIdentity identity;
    WorldBatchBackendProviderError error;

    [[nodiscard]] explicit operator bool() const noexcept { return backend != nullptr; }
};

struct WorldBatchBackendProviderDescriptor {
    using Factory = std::function<std::unique_ptr<IWorldBatchBackend>(std::size_t)>;

    std::string provider_id;
    std::string implementation_version;
    std::string backend_profile_id;
    std::string offered_service;
    std::vector<std::string> admitted_capabilities;
    Factory factory;
};

class WorldBatchBackendProviderCatalog {
  public:
    explicit WorldBatchBackendProviderCatalog(
        std::vector<WorldBatchBackendProviderDescriptor> descriptors);

    [[nodiscard]] WorldBatchBackendProviderMaterialization
    materialize(const WorldBatchBackendProviderRequest &request, std::size_t world_count) const;

  private:
    std::vector<WorldBatchBackendProviderDescriptor> descriptors_;
};

[[nodiscard]] const WorldBatchBackendProviderCatalog &
default_world_batch_backend_provider_catalog();

// The maintained default request is read from the generated resolved native
// composition. Any drift in profile, provider scope, or offered semantic
// service fails before a concrete backend factory is consulted.
[[nodiscard]] const WorldBatchBackendProviderRequest &
default_world_batch_backend_provider_request();

[[nodiscard]] WorldBatchBackendProviderMaterialization
materialize_default_world_batch_backend(std::size_t world_count);

} // namespace runtime::backend_provider
