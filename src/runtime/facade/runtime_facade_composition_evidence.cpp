#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"

#include <algorithm>
#include <array>
#include <string>
#include <string_view>
#include <utility>

namespace {

namespace evidence = runtime::composition_evidence_contracts;
namespace generated = runtime::composition_evidence_contracts::generated;

RuntimeCompositionEvidenceResult unavailable(std::string code, std::string detail) {
    return {
        .available = false,
        .evidence = {},
        .error_code = std::move(code),
        .error_detail = std::move(detail),
    };
}

constexpr std::array<std::string_view, 5> kScopeNames = {"application", "backend", "batch", "world",
                                                         "episode"};

} // namespace

RuntimeCompositionEvidenceResult RuntimeFacade::export_composition_evidence() const {
    if (runtime_ == nullptr || identity_ == nullptr) {
        return unavailable("composition_evidence.runtime_unavailable",
                           "facade runtime identity is not available");
    }

    const runtime::backend::Diagnostics diagnostics = runtime_->diagnostics();
    if (diagnostics.world_compositions.empty()) {
        return unavailable("composition_evidence.no_realized_worlds",
                           "zero-world facade has no realized composition evidence");
    }
    if (diagnostics.world_compositions.size() != diagnostics.world_count) {
        return unavailable("composition_evidence.world_count_mismatch",
                           "backend diagnostics omitted a realized world");
    }
    const auto &backend_identity = identity_->backend_identity;
    const bool backend_capabilities_match =
        backend_identity.admitted_capabilities.size() == generated::kBackendCapabilities.size() &&
        std::equal(backend_identity.admitted_capabilities.begin(),
                   backend_identity.admitted_capabilities.end(),
                   generated::kBackendCapabilities.begin(), generated::kBackendCapabilities.end());
    if (backend_identity.provider_id != generated::kBackendProviderId ||
        backend_identity.implementation_version != generated::kBackendImplementationVersion ||
        backend_identity.backend_profile_id != generated::kBackendProfileId ||
        !backend_capabilities_match) {
        return unavailable(
            "composition_evidence.backend_identity_mismatch",
            "materialized backend identity does not match the generated owner anchor: " +
                backend_identity.provider_id + "@" + backend_identity.implementation_version + "/" +
                backend_identity.backend_profile_id +
                "/capabilities=" + std::to_string(backend_identity.admitted_capabilities.size()));
    }

    RuntimeCompositionEvidence value;
    value.composition_id = std::string(generated::kCompositionId);
    value.requested_profile_id = std::string(generated::kRequestedProfileId);
    value.requested_profile_version = std::string(generated::kRequestedProfileVersion);
    value.runtime_request_sha256 = std::string(generated::kRuntimeRequestSha256);
    value.requested_manifest_sha256 = std::string(generated::kRequestedManifestSha256);
    value.resolved_manifest_sha256 = std::string(generated::kResolvedManifestSha256);
    value.catalog_lock_sha256 = std::string(generated::kCatalogLockSha256);
    value.profile_projection_sha256 = std::string(generated::kProfileProjectionSha256);
    value.resolver_contract_version = std::string(generated::kResolverContractVersion);
    for (const auto &provider : generated::kProviderVersions) {
        value.provider_versions.push_back({
            .provider_id = std::string(provider.provider_id),
            .implementation_version = std::string(provider.implementation_version),
        });
    }
    value.backend = {
        .provider_id = backend_identity.provider_id,
        .implementation_version = backend_identity.implementation_version,
        .backend_profile_id = backend_identity.backend_profile_id,
        .admitted_capabilities = backend_identity.admitted_capabilities,
    };
    value.executable_graph_sha256 = std::string(generated::kExecutableGraphSha256);
    value.stage_contract_version = std::string(generated::kStageContractVersion);
    value.host_mode = identity_->host_context.host_mode;
    value.binding_version = identity_->host_context.binding_version;

    for (const auto &world : diagnostics.world_compositions) {
        if (world.requested_manifest_sha256 != value.requested_manifest_sha256 ||
            world.resolved_manifest_sha256 != value.resolved_manifest_sha256 ||
            world.executable_graph_sha256 != value.executable_graph_sha256) {
            return unavailable("composition_evidence.runtime_identity_mismatch",
                               "realized world identity does not match the generated owner anchor");
        }
        evidence::WorldInstanceEvidence world_evidence;
        world_evidence.world_index = world.world_index;
        for (std::size_t index = 0; index < kScopeNames.size(); ++index) {
            const std::string instance_prefix =
                "composition:" + std::to_string(identity_->composition_incarnation) +
                "/world:" + std::to_string(world.world_index);
            world_evidence.scope_generations.push_back({
                .scope = std::string(kScopeNames[index]),
                .instance_id = instance_prefix + "/" + std::string(kScopeNames[index]),
                .generation = world.scope_generations[index],
            });
        }
        value.world_instances.push_back(std::move(world_evidence));
    }

    value = evidence::seal_runtime_composition_evidence(std::move(value));
    const auto validation = evidence::validate_runtime_composition_evidence(value);
    if (!validation.valid) {
        const std::string detail =
            validation.issues.empty()
                ? "runtime evidence failed validation"
                : validation.issues.front().code + "@" + validation.issues.front().path;
        return unavailable("composition_evidence.invalid_runtime_evidence", detail);
    }
    return {
        .available = true,
        .evidence = std::move(value),
        .error_code = {},
        .error_detail = {},
    };
}

RuntimeCompositionEvidenceComparison
RuntimeFacade::compare_composition_evidence(const RuntimeCompositionEvidence &expected) const {
    const RuntimeCompositionEvidenceResult actual = export_composition_evidence();
    if (!actual.available) {
        return {
            .compatible = false,
            .mismatches = {"actual:" + actual.error_code},
        };
    }
    return evidence::compare_runtime_composition_evidence(expected, actual.evidence);
}
