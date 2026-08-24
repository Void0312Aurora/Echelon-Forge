#include "core/engine/simulation_kernel.h"
#include "runtime/contracts/composition/default_compatibility_manifest.v1.generated.h"
#include "runtime/facade/internal/world_batch_backend_provider.h"
#include "runtime/facade/runtime_facade.h"

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

namespace provider = runtime::backend_provider;
using json = nlohmann::json;

json load_fixture(std::string_view filename) {
    const std::filesystem::path path = std::filesystem::path(EF_SOURCE_ROOT) / "tests" /
                                       "architecture" / "composition" / "fixtures" / filename;
    std::ifstream stream(path);
    REQUIRE_MESSAGE(stream.good(), "cannot open backend provider fixture: " << path.string());
    return json::parse(stream);
}

provider::WorldBatchBackendProviderRequest request_from_json(const json &value) {
    return {
        .schema_version = value.at("schema_version").get<std::string>(),
        .backend_profile_id = value.at("backend_profile_id").get<std::string>(),
        .provider_id = value.at("provider_id").get<std::string>(),
        .provider_implementation_version =
            value.at("provider_implementation_version").get<std::string>(),
        .required_capabilities = value.at("required_capabilities").get<std::vector<std::string>>(),
    };
}

} // namespace

TEST_CASE("default kernel construction is an explicit generated-manifest alias") {
    namespace generated = runtime::composition_contracts::generated;

    SimulationKernel kernel;
    CHECK(kernel.requested_composition_sha256() == generated::kDefaultCompatibilityRequestedSha256);
    CHECK(kernel.resolved_composition_sha256() == generated::kDefaultCompatibilityResolvedSha256);
    CHECK_THROWS_AS(
        [] {
            SimulationKernel rejected(std::string{});
            (void)rejected;
        }(),
        std::runtime_error);
}

TEST_CASE("default resolved composition selects the maintained backend provider") {
    const provider::WorldBatchBackendProviderRequest fixture =
        request_from_json(load_fixture("default_backend_provider_request.v1.json"));
    CHECK(fixture == provider::default_world_batch_backend_provider_request());

    auto materialized =
        provider::default_world_batch_backend_provider_catalog().materialize(fixture, 3);
    REQUIRE(materialized);
    CHECK(materialized.identity.provider_id == provider::kBuiltinFlecsCpuProviderId);
    CHECK(materialized.identity.implementation_version == "1.0.0");
    CHECK(materialized.identity.backend_profile_id == "cpu_exact.reference");
    CHECK(materialized.identity.admitted_capabilities ==
          std::vector<std::string>{std::string(provider::kCpuExactCapabilityId)});
    CHECK(materialized.backend->configuration().world_count == 3);
    // Keep the returned diagnostics object alive while doctest decomposes the
    // member comparison.  P5-A made diagnostics carry per-world vectors, so a
    // member reference into a temporary diagnostics value is no longer a safe
    // assertion operand on MSVC.
    const runtime::backend::Diagnostics diagnostics = materialized.backend->diagnostics();
    CHECK(diagnostics.backend_id == "flecs_cpu_reference");
}

TEST_CASE("runtime facade constructs through the admitted provider without semantic drift") {
    RuntimeFacade by_count(2);
    CHECK(by_count.world_count() == 2);

    RuntimeFacade by_config(RuntimeBatchConfig{.world_count = 4, .worker_threads = 2});
    CHECK(by_config.world_count() == 4);
    CHECK(by_config.worker_threads() == 2);
}

TEST_CASE("negative backend capability fixtures fail closed before materialization") {
    const json matrix = load_fixture("invalid_backend_provider_request_matrix.v1.json");
    REQUIRE(matrix.at("schema_version") ==
            "echelon_forge.invalid_backend_provider_request_matrix.v1");
    for (const json &entry : matrix.at("cases")) {
        CAPTURE(entry.at("case_id").get<std::string>());
        auto materialized = provider::default_world_batch_backend_provider_catalog().materialize(
            request_from_json(entry.at("request")), 1);
        CHECK_FALSE(materialized);
        CHECK(materialized.backend == nullptr);
        CHECK(materialized.error.code == entry.at("expected_error").get<std::string>());
    }
}

TEST_CASE("capability rejection happens before a provider factory is invoked") {
    std::size_t factory_invocations = 0;
    provider::WorldBatchBackendProviderCatalog catalog({
        provider::WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(provider::kBuiltinFlecsCpuProviderId),
            .implementation_version = "1.0.0",
            .backend_profile_id = "cpu_exact.reference",
            .offered_service = std::string(provider::kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(provider::kCpuExactCapabilityId)},
            .factory =
                [&](std::size_t) {
                    ++factory_invocations;
                    return std::unique_ptr<IWorldBatchBackend>{};
                },
        },
    });
    provider::WorldBatchBackendProviderRequest request =
        provider::default_world_batch_backend_provider_request();
    request.required_capabilities.clear();

    const auto rejected = catalog.materialize(request, 1);
    CHECK_FALSE(rejected);
    CHECK(rejected.error.code == provider::kErrorCapabilityRequired);
    CHECK(factory_invocations == 0);
}

TEST_CASE("provider profile mismatch fails before a provider factory is invoked") {
    std::size_t factory_invocations = 0;
    provider::WorldBatchBackendProviderCatalog catalog({
        provider::WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(provider::kBuiltinFlecsCpuProviderId),
            .implementation_version = "1.0.0",
            .backend_profile_id = "gpu_helpers.diagnostics_only",
            .offered_service = std::string(provider::kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(provider::kCpuExactCapabilityId)},
            .factory =
                [&](std::size_t) {
                    ++factory_invocations;
                    return std::unique_ptr<IWorldBatchBackend>{};
                },
        },
    });

    const auto rejected =
        catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
    CHECK_FALSE(rejected);
    CHECK(rejected.error.code == provider::kErrorProviderProfileMismatch);
    CHECK(factory_invocations == 0);
}

TEST_CASE("provider implementation version mismatch fails before factory invocation") {
    std::size_t factory_invocations = 0;
    provider::WorldBatchBackendProviderCatalog catalog({
        provider::WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(provider::kBuiltinFlecsCpuProviderId),
            .implementation_version = "2.0.0",
            .backend_profile_id = "cpu_exact.reference",
            .offered_service = std::string(provider::kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(provider::kCpuExactCapabilityId)},
            .factory =
                [&](std::size_t) {
                    ++factory_invocations;
                    return std::unique_ptr<IWorldBatchBackend>{};
                },
        },
    });

    const auto rejected =
        catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
    CHECK_FALSE(rejected);
    CHECK(rejected.error.code == provider::kErrorProviderVersionMismatch);
    CHECK(factory_invocations == 0);
}

TEST_CASE("invalid provider catalog metadata fails before a provider factory is invoked") {
    std::size_t factory_invocations = 0;
    const auto descriptor = [&]() {
        return provider::WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(provider::kBuiltinFlecsCpuProviderId),
            .implementation_version = "1.0.0",
            .backend_profile_id = "cpu_exact.reference",
            .offered_service = std::string(provider::kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(provider::kCpuExactCapabilityId)},
            .factory =
                [&](std::size_t) {
                    ++factory_invocations;
                    return std::unique_ptr<IWorldBatchBackend>{};
                },
        };
    };

    SUBCASE("provider identity is duplicated") {
        provider::WorldBatchBackendProviderCatalog catalog({descriptor(), descriptor()});
        const auto rejected =
            catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
        CHECK_FALSE(rejected);
        CHECK(rejected.error.code == provider::kErrorProviderContractInvalid);
        CHECK(factory_invocations == 0);
    }

    SUBCASE("provider capability is duplicated") {
        auto invalid_descriptor = descriptor();
        invalid_descriptor.admitted_capabilities.push_back(
            std::string(provider::kCpuExactCapabilityId));
        provider::WorldBatchBackendProviderCatalog catalog({std::move(invalid_descriptor)});
        const auto rejected =
            catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
        CHECK_FALSE(rejected);
        CHECK(rejected.error.code == provider::kErrorProviderContractInvalid);
        CHECK(factory_invocations == 0);
    }
}

TEST_CASE("provider construction failures stay inside the materialization boundary") {
    const auto descriptor = [](provider::WorldBatchBackendProviderDescriptor::Factory factory) {
        return provider::WorldBatchBackendProviderDescriptor{
            .provider_id = std::string(provider::kBuiltinFlecsCpuProviderId),
            .implementation_version = "1.0.0",
            .backend_profile_id = "cpu_exact.reference",
            .offered_service = std::string(provider::kWorldBatchBackendServiceId),
            .admitted_capabilities = {std::string(provider::kCpuExactCapabilityId)},
            .factory = std::move(factory),
        };
    };

    SUBCASE("null backend") {
        provider::WorldBatchBackendProviderCatalog catalog(
            {descriptor([](std::size_t) { return std::unique_ptr<IWorldBatchBackend>{}; })});
        const auto rejected =
            catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
        CHECK_FALSE(rejected);
        CHECK(rejected.error.code == provider::kErrorConstructionFailed);
        CHECK(rejected.error.detail == "backend provider factory returned no backend");
    }

    SUBCASE("standard exception") {
        provider::WorldBatchBackendProviderCatalog catalog({descriptor([](std::size_t) {
            throw std::runtime_error("injected provider failure");
            return std::unique_ptr<IWorldBatchBackend>{};
        })});
        const auto rejected =
            catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
        CHECK_FALSE(rejected);
        CHECK(rejected.error.code == provider::kErrorConstructionFailed);
        CHECK(rejected.error.detail == "injected provider failure");
    }

    SUBCASE("non-standard exception") {
        provider::WorldBatchBackendProviderCatalog catalog({descriptor([](std::size_t) {
            throw 7;
            return std::unique_ptr<IWorldBatchBackend>{};
        })});
        const auto rejected =
            catalog.materialize(provider::default_world_batch_backend_provider_request(), 1);
        CHECK_FALSE(rejected);
        CHECK(rejected.error.code == provider::kErrorConstructionFailed);
        CHECK(rejected.error.detail == "backend provider factory raised a non-standard exception");
    }
}
