#include "runtime/facade/internal/world_batch_backend_provider.h"

#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/composition/default_compatibility_manifest.v1.generated.h"
#include "runtime/facade/internal/flecs_cpu_backend.h"

#include <algorithm>
#include <exception>
#include <utility>

namespace runtime::backend_provider {
namespace {

namespace profiles = runtime::backend_profiles;

WorldBatchBackendProviderMaterialization failure(std::string_view code, std::string subject,
                                                 std::string detail) {
    return {
        .backend = nullptr,
        .identity = {},
        .error = {std::string(code), std::move(subject), std::move(detail)},
    };
}

bool contains(const std::vector<std::string> &values, std::string_view expected) {
    return std::find(values.begin(), values.end(), expected) != values.end();
}

WorldBatchBackendProviderRequest load_default_request() {
    std::vector<std::string> capabilities;
    capabilities.reserve(
        runtime::composition_contracts::generated::kDefaultBackendRequiredCapabilities.size());
    for (const std::string_view capability :
         runtime::composition_contracts::generated::kDefaultBackendRequiredCapabilities) {
        capabilities.emplace_back(capability);
    }

    return {
        .schema_version = std::string(kBackendProviderRequestSchemaVersion),
        .backend_profile_id =
            std::string(runtime::composition_contracts::generated::kDefaultBackendProfileId),
        .provider_id =
            std::string(runtime::composition_contracts::generated::kDefaultBackendProviderId),
        .provider_implementation_version = std::string(
            runtime::composition_contracts::generated::kDefaultBackendImplementationVersion),
        .required_capabilities = std::move(capabilities),
    };
}

} // namespace

WorldBatchBackendProviderCatalog::WorldBatchBackendProviderCatalog(
    std::vector<WorldBatchBackendProviderDescriptor> descriptors)
    : descriptors_(std::move(descriptors)) {}

WorldBatchBackendProviderMaterialization
WorldBatchBackendProviderCatalog::materialize(const WorldBatchBackendProviderRequest &request,
                                              std::size_t world_count) const {
    if (request.schema_version != kBackendProviderRequestSchemaVersion) {
        return failure(kErrorInvalidRequestSchema, request.schema_version,
                       "backend provider request schema version is not admitted");
    }

    const profiles::BackendProfileContract *profile =
        profiles::find_backend_profile_contract(request.backend_profile_id);
    if (profile == nullptr) {
        return failure(kErrorProfileNotFound, request.backend_profile_id,
                       "backend profile is absent from the native owner registry");
    }
    const profiles::BackendProfileValidationResult profile_validation =
        profiles::validate_backend_profile_contract(*profile);
    if (!profile_validation.valid) {
        return failure(kErrorProviderContractInvalid, request.backend_profile_id,
                       "backend profile registry entry failed native validation");
    }
    if (!profiles::is_maintained_backend_profile(*profile) ||
        !profile->projection_eligibility.maintained_cpu_exact_baseline) {
        return failure(kErrorProfileNotMaintained, request.backend_profile_id,
                       "diagnostics-only and unmaintained candidate profiles cannot construct "
                       "the maintained facade backend");
    }

    const auto provider =
        std::find_if(descriptors_.begin(), descriptors_.end(), [&](const auto &descriptor) {
            return descriptor.provider_id == request.provider_id;
        });
    if (provider == descriptors_.end()) {
        return failure(kErrorProviderNotFound, request.provider_id,
                       "backend provider is absent from the native provider catalog");
    }
    if (std::count_if(descriptors_.begin(), descriptors_.end(), [&](const auto &descriptor) {
            return descriptor.provider_id == request.provider_id;
        }) != 1) {
        return failure(kErrorProviderContractInvalid, request.provider_id,
                       "native backend provider identity must be unique");
    }
    if (provider->implementation_version.empty() ||
        provider->offered_service != kWorldBatchBackendServiceId || !provider->factory) {
        return failure(kErrorProviderContractInvalid, provider->provider_id,
                       "backend provider descriptor is incomplete or does not offer the semantic "
                       "backend service");
    }
    std::vector<std::string> seen_provider_capabilities;
    seen_provider_capabilities.reserve(provider->admitted_capabilities.size());
    for (const std::string &capability : provider->admitted_capabilities) {
        if (capability.empty() || contains(seen_provider_capabilities, capability)) {
            return failure(kErrorProviderContractInvalid, provider->provider_id,
                           "backend provider descriptor must admit unique non-empty "
                           "capabilities");
        }
        seen_provider_capabilities.push_back(capability);
    }
    if (provider->backend_profile_id != request.backend_profile_id) {
        return failure(kErrorProviderProfileMismatch, request.provider_id,
                       "backend provider does not own the requested profile");
    }
    if (provider->implementation_version != request.provider_implementation_version) {
        return failure(kErrorProviderVersionMismatch, request.provider_id,
                       "backend provider implementation version does not match the resolved "
                       "manifest request");
    }
    if (request.required_capabilities.empty()) {
        return failure(kErrorCapabilityRequired, request.provider_id,
                       "backend provider request must name its required capabilities");
    }

    std::vector<std::string> seen_capabilities;
    seen_capabilities.reserve(request.required_capabilities.size());
    for (const std::string &capability : request.required_capabilities) {
        if (capability.empty()) {
            return failure(kErrorCapabilityRequired, request.provider_id,
                           "backend provider capability identifiers must be non-empty");
        }
        if (contains(seen_capabilities, capability)) {
            return failure(kErrorCapabilityDuplicate, capability,
                           "backend provider capability identifiers must be unique");
        }
        seen_capabilities.push_back(capability);
        if (!contains(provider->admitted_capabilities, capability)) {
            return failure(kErrorCapabilityNotAdmitted, capability,
                           "backend provider does not admit the requested capability");
        }
    }
    for (const std::string &capability : provider->admitted_capabilities) {
        if (!contains(request.required_capabilities, capability)) {
            return failure(kErrorCapabilityMissing, capability,
                           "backend provider request omitted a capability required by the native "
                           "provider descriptor");
        }
    }

    try {
        std::unique_ptr<IWorldBatchBackend> backend = provider->factory(world_count);
        if (backend == nullptr) {
            return failure(kErrorConstructionFailed, provider->provider_id,
                           "backend provider factory returned no backend");
        }
        return {
            .backend = std::move(backend),
            .identity =
                {
                    .provider_id = provider->provider_id,
                    .implementation_version = provider->implementation_version,
                    .backend_profile_id = provider->backend_profile_id,
                    .admitted_capabilities = provider->admitted_capabilities,
                },
            .error = {},
        };
    } catch (const std::exception &error) {
        return failure(kErrorConstructionFailed, provider->provider_id, error.what());
    } catch (...) {
        return failure(kErrorConstructionFailed, provider->provider_id,
                       "backend provider factory raised a non-standard exception");
    }
}

const WorldBatchBackendProviderCatalog &default_world_batch_backend_provider_catalog() {
    static const WorldBatchBackendProviderCatalog catalog({
        WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(kBuiltinFlecsCpuProviderId),
            .implementation_version =
                std::string(runtime::world_batch_backend_contracts::kDefaultImplementationVersion),
            .backend_profile_id = std::string(profiles::kBackendProfileIdCpuExactReference),
            .offered_service = std::string(kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(kCpuExactCapabilityId)},
            .factory =
                [](std::size_t world_count) {
                    return std::make_unique<FlecsCpuBackend>(world_count);
                },
        },
    });
    return catalog;
}

const WorldBatchBackendProviderRequest &default_world_batch_backend_provider_request() {
    static const WorldBatchBackendProviderRequest request = load_default_request();
    return request;
}

WorldBatchBackendProviderMaterialization
materialize_default_world_batch_backend(std::size_t world_count) {
    return default_world_batch_backend_provider_catalog().materialize(
        default_world_batch_backend_provider_request(), world_count);
}

} // namespace runtime::backend_provider
