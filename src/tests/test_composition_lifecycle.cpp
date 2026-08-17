#include <ostream>

#include "runtime/composition/composition_json.h"
#include "runtime/composition/composition_identity.h"
#include "runtime/composition/composition_runtime.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <fstream>
#include <functional>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <typeinfo>
#include <utility>
#include <vector>

namespace {

namespace composition = runtime::composition;
namespace contracts = runtime::composition_contracts;

struct Trace {
    std::vector<std::string> entries;

    void push(std::string entry) { entries.push_back(std::move(entry)); }

    [[nodiscard]] std::vector<std::string> matching(std::string_view prefix) const {
        std::vector<std::string> result;
        for (const auto &entry : entries) {
            if (entry.starts_with(prefix)) {
                result.push_back(entry);
            }
        }
        return result;
    }
};

class TraceEffect final : public composition::ILifecycleEffect {
  public:
    TraceEffect(Trace &trace, std::string provider_id, bool fail_commit, bool handover_safe = true,
                std::function<void()> dispose_callback = {})
        : trace_(trace), provider_id_(std::move(provider_id)), fail_commit_(fail_commit),
          handover_safe_(handover_safe), dispose_callback_(std::move(dispose_callback)) {}

    ~TraceEffect() override { trace_.push("effect.destroy:" + provider_id_); }

    composition::CompositionStatus commit() override {
        trace_.push("effect.commit:" + provider_id_);
        if (fail_commit_) {
            return composition::CompositionStatus::failure({
                std::string(composition::kErrorLifecycleEffectCommitFailed),
                provider_id_,
                "injected commit failure",
            });
        }
        committed_ = true;
        return composition::CompositionStatus::success();
    }

    void rollback() noexcept override {
        if (!terminal_) {
            trace_.push("effect.rollback:" + provider_id_);
            terminal_ = true;
        }
    }

    void dispose() noexcept override {
        if (!terminal_) {
            trace_.push("effect.dispose:" + provider_id_);
            terminal_ = true;
            if (dispose_callback_) {
                dispose_callback_();
            }
        }
    }

    [[nodiscard]] bool supports_replacement_handover() const noexcept override {
        return handover_safe_;
    }

  private:
    Trace &trace_;
    std::string provider_id_;
    bool fail_commit_ = false;
    bool handover_safe_ = true;
    bool committed_ = false;
    bool terminal_ = false;
    std::function<void()> dispose_callback_;
};

class IntProviderInstance final : public composition::IProviderInstance {
  public:
    IntProviderInstance(Trace &trace, std::string provider_id, std::string service_key, int value)
        : trace_(trace), provider_id_(std::move(provider_id)), service_key_(std::move(service_key)),
          value_(value) {}

    ~IntProviderInstance() override { trace_.push("instance.destroy:" + provider_id_); }

    void *query_service(std::string_view service_key,
                        const std::type_info &requested_type) noexcept override {
        return service_key == service_key_ && requested_type == typeid(int) ? &value_ : nullptr;
    }

  private:
    Trace &trace_;
    std::string provider_id_;
    std::string service_key_;
    int value_ = 0;
};

class IntProviderFactory final : public composition::IProviderFactory {
  public:
    IntProviderFactory(Trace &trace, std::string provider_id, std::string offered_service,
                       contracts::CompositionScope scope, int base_value,
                       std::vector<std::string> required_services = {},
                       std::string implementation_version = "1.0.0",
                       std::string canonical_configuration_json = "{}", bool handover_safe = true)
        : trace_(trace), provider_id_(std::move(provider_id)),
          offered_service_(std::move(offered_service)), scope_(scope), base_value_(base_value),
          implementation_version_(std::move(implementation_version)),
          canonical_configuration_json_(std::move(canonical_configuration_json)),
          required_services_(std::move(required_services)), handover_safe_(handover_safe) {}

    composition::ProviderFactoryMetadata metadata() const override {
        return {provider_id_, "builtin.core", implementation_version_, scope_,
                canonical_configuration_json_};
    }

    const std::type_info *service_type(std::string_view service_key) const noexcept override {
        if (service_key != offered_service_) {
            return nullptr;
        }
        return report_double_service_ ? &typeid(double) : &typeid(int);
    }

    composition::ProviderInstanceResult
    construct(composition::ProviderConstructionContext &context) override {
        ++construction_count_;
        trace_.push("construct:" + provider_id_);
        const bool fail_effect_commit = fail_effect_commit_next_;
        fail_effect_commit_next_ = false;
        auto dispose_callback = std::move(dispose_callback_next_);
        context.adopt_effect(std::make_unique<TraceEffect>(
            trace_, provider_id_, fail_effect_commit, handover_safe_, std::move(dispose_callback)));
        if (fail_next_) {
            fail_next_ = false;
            return composition::ProviderInstanceResult::failure({
                std::string(composition::kErrorProviderConstructionFailed),
                provider_id_,
                "injected construction failure",
            });
        }

        if (ignore_lookup_error_next_) {
            ignore_lookup_error_next_ = false;
            static_cast<void>(context.service<int>(contracts::kServiceCompositionEvidenceSink));
        }

        int value = base_value_ + construction_count_;
        for (const auto &service_key : required_services_) {
            const auto dependency = context.service<int>(service_key);
            if (const int *pointer = dependency.try_get()) {
                value += *pointer;
            } else {
                return composition::ProviderInstanceResult::failure({
                    std::string(composition::kErrorServiceUnavailable),
                    provider_id_,
                    service_key,
                });
            }
        }
        return composition::ProviderInstanceResult::success(
            std::make_unique<IntProviderInstance>(trace_, provider_id_, offered_service_, value));
    }

    void fail_next_construction() noexcept { fail_next_ = true; }

    void fail_next_effect_commit() noexcept { fail_effect_commit_next_ = true; }

    void ignore_lookup_error_next() noexcept { ignore_lookup_error_next_ = true; }

    void set_dispose_callback(std::function<void()> callback) {
        dispose_callback_next_ = std::move(callback);
    }

    void mutate_identity_version(std::string version) {
        implementation_version_ = std::move(version);
    }

    void mutate_service_type() noexcept { report_double_service_ = true; }

  private:
    Trace &trace_;
    std::string provider_id_;
    std::string offered_service_;
    contracts::CompositionScope scope_ = contracts::CompositionScope::world;
    std::string implementation_version_ = "1.0.0";
    std::string canonical_configuration_json_ = "{}";
    int base_value_ = 0;
    std::vector<std::string> required_services_;
    int construction_count_ = 0;
    bool fail_next_ = false;
    bool fail_effect_commit_next_ = false;
    bool ignore_lookup_error_next_ = false;
    bool handover_safe_ = true;
    bool report_double_service_ = false;
    std::function<void()> dispose_callback_next_;
};

class MetadataOnlyFactory final : public composition::IProviderFactory {
  public:
    explicit MetadataOnlyFactory(contracts::CompositionProviderDescriptor descriptor)
        : metadata_{descriptor.provider_id, descriptor.plugin_id, descriptor.implementation_version,
                    descriptor.scope, descriptor.canonical_configuration_json},
          offered_services_(descriptor.offered_services.begin(),
                            descriptor.offered_services.end()) {}

    composition::ProviderFactoryMetadata metadata() const override { return metadata_; }

    const std::type_info *service_type(std::string_view service_key) const noexcept override {
        return offered_services_.contains(service_key) ? &typeid(int) : nullptr;
    }

    composition::ProviderInstanceResult
    construct(composition::ProviderConstructionContext &) override {
        return composition::ProviderInstanceResult::failure({
            std::string(composition::kErrorProviderConstructionFailed),
            metadata_.provider_id,
            "metadata-only factory must not be realized",
        });
    }

  private:
    composition::ProviderFactoryMetadata metadata_;
    std::set<std::string, std::less<>> offered_services_;
};

std::string read_text_file(const std::string &path) {
    std::ifstream stream(path, std::ios::binary);
    REQUIRE(stream.good());
    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

contracts::CompositionProviderDescriptor provider(std::string provider_id,
                                                  contracts::CompositionScope scope,
                                                  std::string offered_service,
                                                  std::vector<std::string> required_services = {}) {
    contracts::CompositionProviderDescriptor result;
    result.provider_id = std::move(provider_id);
    result.plugin_id = "builtin.core";
    result.implementation_version = "1.0.0";
    result.scope = scope;
    result.cardinality = "one_per_scope";
    result.offered_services = {std::move(offered_service)};
    result.required_services = std::move(required_services);
    result.restart_policy = "rebuild_scope_generation";
    result.teardown_policy = "reverse_dependency_order";
    result.canonical_configuration_json = "{}";
    return result;
}

void refresh_identity(contracts::ResolvedSimulationComposition &resolved) {
    const auto identity = composition::compute_composition_identity(resolved);
    if (!identity) {
        throw std::runtime_error(identity.error().detail);
    }
    resolved.requested_manifest_sha256 = identity.value().requested_manifest_sha256;
    resolved.resolved_manifest_sha256 = identity.value().resolved_manifest_sha256;
}

contracts::ResolvedSimulationComposition make_resolved() {
    contracts::ResolvedSimulationComposition resolved;
    resolved.schema_version = std::string(contracts::kResolvedManifestSchemaVersion);
    resolved.resolver_contract_version = std::string(contracts::kResolverContractVersion);
    resolved.provider_construction_order = {
        "provider.application",
        "provider.backend",
        "provider.world",
        "provider.episode",
    };
    resolved.system_registration_order = {"system.test"};

    auto &manifest = resolved.manifest;
    manifest.schema_version = std::string(contracts::kManifestSchemaVersion);
    manifest.composition_id = "test.lifecycle";
    manifest.contract_versions = {"1.0.0", "1.0.0", "1.0.0", "1.0.0"};
    manifest.requested_profile = {"test.profile", "1.0.0"};
    manifest.plugins.push_back({
        "builtin.core",
        "builtin.core",
        "1.0.0",
        ">=1.0.0 <2.0.0",
        {"native"},
        "truth_affecting_deterministic",
        {"repository_builtin", "test", std::nullopt},
        {},
        {},
        "{}",
    });
    manifest.providers = {
        provider("provider.application", contracts::CompositionScope::application,
                 std::string(contracts::kServiceEnvironmentModel)),
        provider("provider.backend", contracts::CompositionScope::backend,
                 std::string(contracts::kServiceWorldBatchBackend)),
        provider("provider.world", contracts::CompositionScope::world,
                 std::string(contracts::kServiceEffectsModel),
                 {std::string(contracts::kServiceEnvironmentModel)}),
        provider("provider.episode", contracts::CompositionScope::episode,
                 std::string(contracts::kServiceSensorModel),
                 {std::string(contracts::kServiceEffectsModel)}),
    };
    manifest.service_bindings = {
        {
            "provider",
            "provider.world",
            std::string(contracts::kServiceEnvironmentModel),
            "provider.application",
        },
        {
            "provider",
            "provider.episode",
            std::string(contracts::kServiceEffectsModel),
            "provider.world",
        },
        {
            "system",
            "system.test",
            std::string(contracts::kServiceSensorModel),
            "provider.episode",
        },
    };
    manifest.component_contributions = {{"TestComponent", "builtin.core", "component.test"}};
    contracts::CompositionSystemContribution system;
    system.contribution_id = "system.test";
    system.plugin_id = "builtin.core";
    system.registration_factory_id = "system.register_test";
    system.domain = "common";
    system.required_services = {std::string(contracts::kServiceSensorModel)};
    system.required_components = {"TestComponent"};
    manifest.system_contributions = {std::move(system)};
    manifest.backend_request = {
        "cpu.test",
        "provider.backend",
        {},
    };
    manifest.scope_policies = {
        {
            contracts::CompositionScope::application,
            std::nullopt,
            "singleton",
            "host_reconfiguration_or_shutdown",
        },
        {
            contracts::CompositionScope::backend,
            contracts::CompositionScope::application,
            "singleton",
            "backend_switch_or_failure",
        },
        {
            contracts::CompositionScope::batch,
            contracts::CompositionScope::backend,
            "one_per_parent",
            "batch_resize_or_reconfiguration",
        },
        {
            contracts::CompositionScope::world,
            contracts::CompositionScope::batch,
            "one_per_parent",
            "world_replacement_or_composition_change",
        },
        {
            contracts::CompositionScope::episode,
            contracts::CompositionScope::world,
            "one_per_parent",
            "reset_or_episode_completion",
        },
    };
    manifest.reconfiguration_policy = {
        "rebuild_scope_generation",
        "forbidden",
        {"episode_end", "pre_run", "world_rebuild"},
    };
    manifest.evidence_policy = {
        std::string(contracts::kCanonicalizationId),
        std::string(contracts::kCanonicalHashAlgorithm),
        true,
        true,
        true,
    };
    manifest.compatibility_claims = {"test.lifecycle"};
    refresh_identity(resolved);
    return resolved;
}

struct CatalogBundle {
    explicit CatalogBundle(Trace &trace, std::string world_version = "1.0.0",
                           std::string world_configuration = "{}", int world_base = 20,
                           bool world_handover_safe = true) {
        factories.emplace(
            "provider.application",
            std::make_shared<IntProviderFactory>(trace, "provider.application",
                                                 std::string(contracts::kServiceEnvironmentModel),
                                                 contracts::CompositionScope::application, 10));
        factories.emplace("provider.backend", std::make_shared<IntProviderFactory>(
                                                  trace, "provider.backend",
                                                  std::string(contracts::kServiceWorldBatchBackend),
                                                  contracts::CompositionScope::backend, 100));
        factories.emplace("provider.world",
                          std::make_shared<IntProviderFactory>(
                              trace, "provider.world", std::string(contracts::kServiceEffectsModel),
                              contracts::CompositionScope::world, world_base,
                              std::vector<std::string>{
                                  std::string(contracts::kServiceEnvironmentModel),
                              },
                              std::move(world_version), std::move(world_configuration),
                              world_handover_safe));
        factories.emplace("provider.episode", std::make_shared<IntProviderFactory>(
                                                  trace, "provider.episode",
                                                  std::string(contracts::kServiceSensorModel),
                                                  contracts::CompositionScope::episode, 30,
                                                  std::vector<std::string>{
                                                      std::string(contracts::kServiceEffectsModel),
                                                  }));
        for (const auto &[_, factory] : factories) {
            REQUIRE(catalog.register_factory(factory).ok());
        }
        REQUIRE(catalog.freeze().ok());
    }

    [[nodiscard]] std::shared_ptr<IntProviderFactory> factory(std::string_view provider_id) {
        return factories.at(std::string(provider_id));
    }

    composition::ProviderCatalog catalog;
    std::map<std::string, std::shared_ptr<IntProviderFactory>> factories;
};

composition::CompositionRuntime realize(contracts::ResolvedSimulationComposition resolved,
                                        const composition::ProviderCatalog &catalog) {
    auto result = composition::CompositionKernel::realize(std::move(resolved), catalog);
    REQUIRE(result.ok());
    return std::move(result).value();
}

} // namespace

TEST_SUITE("composition_lifecycle") {

    TEST_CASE("native JSON ingestion reproduces the frozen P1-B resolved fixture") {
        const std::string requested_fixture_path = std::string(EF_SOURCE_ROOT) +
                                                   "/tests/architecture/composition/fixtures/"
                                                   "default_compatibility_manifest.requested.json";
        const std::string requested_fixture = read_text_file(requested_fixture_path);
        const auto requested =
            composition::parse_simulation_composition_manifest_json(requested_fixture);
        REQUIRE(requested.ok());
        CHECK(requested.value().providers.size() == 11);
        CHECK(requested.value().component_contributions.size() == 82);
        CHECK(requested.value().system_contributions.size() == 34);

        std::string requested_with_extra_field = requested_fixture;
        const std::string schema_version = "\"schema_version\":";
        const auto schema_version_position = requested_with_extra_field.find(schema_version);
        REQUIRE(schema_version_position != std::string::npos);
        requested_with_extra_field.insert(schema_version_position, "\"unexpected\": true, ");
        const auto rejected_requested =
            composition::parse_simulation_composition_manifest_json(requested_with_extra_field);
        CHECK_FALSE(rejected_requested.ok());
        CHECK(rejected_requested.error().code == contracts::kErrorUnexpectedField);
        CHECK(rejected_requested.error().subject == "$.unexpected");

        const std::string fixture_path = std::string(EF_SOURCE_ROOT) +
                                         "/tests/architecture/composition/fixtures/"
                                         "default_compatibility_manifest.resolved.json";
        const std::string fixture = read_text_file(fixture_path);
        auto parsed = composition::parse_resolved_composition_json(fixture);
        REQUIRE(parsed.ok());
        auto resolved = std::move(parsed).value();
        CHECK(resolved.manifest.providers.size() == 11);
        CHECK(resolved.manifest.component_contributions.size() == 82);
        CHECK(resolved.manifest.system_contributions.size() == 34);
        CHECK(resolved.provider_construction_order.size() == 11);
        CHECK(resolved.system_registration_order.size() == 34);

        composition::ProviderCatalog catalog;
        for (const auto &provider_descriptor : resolved.manifest.providers) {
            REQUIRE(
                catalog.register_factory(std::make_shared<MetadataOnlyFactory>(provider_descriptor))
                    .ok());
        }
        REQUIRE(catalog.freeze().ok());
        const auto validation = composition::validate_resolved_composition(resolved, catalog);
        CHECK(validation.valid);

        std::string floating = fixture;
        const std::string configuration = "\"configuration\": {}";
        const auto configuration_position = floating.find(configuration);
        REQUIRE(configuration_position != std::string::npos);
        floating.replace(configuration_position, configuration.size(),
                         "\"configuration\": {\"forbidden_float\": 1.5}");
        const auto rejected = composition::parse_resolved_composition_json(floating);
        CHECK_FALSE(rejected.ok());
        CHECK(rejected.error().code == contracts::kErrorNoncanonicalNumber);
    }

    TEST_CASE("provider catalog freezes deterministically and rejects duplicate mutation") {
        Trace trace;
        composition::ProviderCatalog catalog;
        auto factory = std::make_shared<IntProviderFactory>(
            trace, "provider.application", std::string(contracts::kServiceEnvironmentModel),
            contracts::CompositionScope::application, 10);
        CHECK(catalog.register_factory(factory).ok());
        const auto duplicate = catalog.register_factory(factory);
        CHECK_FALSE(duplicate.ok());
        CHECK(duplicate.error().code == composition::kErrorDuplicateFactory);
        CHECK(catalog.freeze().ok());
        CHECK(catalog.frozen());
        const auto frozen = catalog.register_factory(std::move(factory));
        CHECK_FALSE(frozen.ok());
        CHECK(frozen.error().code == composition::kErrorCatalogFrozen);
        CHECK(catalog.provider_ids() == std::vector<std::string>{"provider.application"});
    }

    TEST_CASE("native validation rejects catalog and resolved-order mismatch before construction") {
        Trace trace;
        CatalogBundle bundle(trace);
        auto resolved = make_resolved();
        CHECK(composition::validate_resolved_composition(resolved, bundle.catalog).valid);

        std::swap(resolved.provider_construction_order[0], resolved.provider_construction_order[1]);
        const auto validation =
            composition::validate_resolved_composition(resolved, bundle.catalog);
        CHECK_FALSE(validation.valid);
        CHECK(
            std::any_of(validation.issues.begin(), validation.issues.end(), [](const auto &issue) {
                return issue.code == composition::kErrorResolvedOrderMismatch;
            }));
        const auto realized =
            composition::CompositionKernel::realize(std::move(resolved), bundle.catalog);
        CHECK_FALSE(realized.ok());
        CHECK(trace.matching("construct:").empty());
    }

    TEST_CASE("typed manifests cannot bypass canonical configuration validation") {
        Trace trace;
        CatalogBundle bundle(trace);

        auto unsorted = make_resolved();
        unsorted.manifest.plugins.front().canonical_configuration_json = "{\"z\":0,\"a\":1}";
        const auto unsorted_validation =
            composition::validate_resolved_composition(unsorted, bundle.catalog);
        CHECK_FALSE(unsorted_validation.valid);
        CHECK(std::any_of(unsorted_validation.issues.begin(), unsorted_validation.issues.end(),
                          [](const auto &issue) {
                              return issue.code == contracts::kErrorInvalidJsonType &&
                                     issue.path == "$.manifest.plugins.configuration";
                          }));

        auto floating = make_resolved();
        floating.manifest.providers.front().canonical_configuration_json = "{\"value\":1.5}";
        const auto floating_validation =
            composition::validate_resolved_composition(floating, bundle.catalog);
        CHECK_FALSE(floating_validation.valid);
        CHECK(std::any_of(floating_validation.issues.begin(), floating_validation.issues.end(),
                          [](const auto &issue) {
                              return issue.code == contracts::kErrorNoncanonicalNumber &&
                                     issue.path == "$.manifest.providers.configuration";
                          }));

        auto invalid_schema_values = make_resolved();
        invalid_schema_values.manifest.plugins.front().host_support = {"browser"};
        invalid_schema_values.manifest.plugins.front().artifact.sha256 = "short";
        invalid_schema_values.manifest.providers.front().teardown_policy = "unordered";
        invalid_schema_values.manifest.system_contributions.front().domain = "space";
        const auto schema_validation =
            composition::validate_resolved_composition(invalid_schema_values, bundle.catalog);
        CHECK_FALSE(schema_validation.valid);
        const auto has_path = [&](std::string_view path) {
            return std::any_of(schema_validation.issues.begin(), schema_validation.issues.end(),
                               [&](const auto &issue) { return issue.path == path; });
        };
        CHECK(has_path("$.manifest.plugins.host_support"));
        CHECK(has_path("$.manifest.plugins.artifact.sha256"));
        CHECK(has_path("$.manifest.providers.teardown_policy"));
        CHECK(has_path("$.manifest.system_contributions.domain"));
    }

    TEST_CASE("realization freezes typed services and disposes in reverse dependency order") {
        Trace trace;
        CatalogBundle bundle(trace);
        auto runtime = realize(make_resolved(), bundle.catalog);

        CHECK(runtime.frozen());
        CHECK(runtime.provider_count() == 4);
        CHECK(runtime.scope_generation(contracts::CompositionScope::application) == 1);
        const auto sensor =
            runtime.service_for<int>("system", "system.test", contracts::kServiceSensorModel);
        REQUIRE(sensor.valid());
        CHECK(sensor.provider_id() == "provider.episode");
        CHECK(sensor.scope() == contracts::CompositionScope::episode);
        CHECK(sensor.generation() == 1);
        CHECK_FALSE(
            runtime.service_for<double>("system", "system.test", contracts::kServiceSensorModel)
                .valid());
        CHECK(trace.matching("construct:") == std::vector<std::string>{
                                                  "construct:provider.application",
                                                  "construct:provider.backend",
                                                  "construct:provider.world",
                                                  "construct:provider.episode",
                                              });
        CHECK(trace.matching("effect.commit:") == std::vector<std::string>{
                                                      "effect.commit:provider.application",
                                                      "effect.commit:provider.backend",
                                                      "effect.commit:provider.world",
                                                      "effect.commit:provider.episode",
                                                  });

        const auto before_stop = trace.entries.size();
        runtime.stop();
        CHECK(runtime.shutdown());
        CHECK_FALSE(sensor.valid());
        const std::vector<std::string> teardown_entries(
            trace.entries.begin() +
                static_cast<std::vector<std::string>::difference_type>(before_stop),
            trace.entries.end());
        CHECK(teardown_entries == std::vector<std::string>{
                                      "effect.dispose:provider.episode",
                                      "effect.destroy:provider.episode",
                                      "instance.destroy:provider.episode",
                                      "effect.dispose:provider.world",
                                      "effect.destroy:provider.world",
                                      "instance.destroy:provider.world",
                                      "effect.dispose:provider.backend",
                                      "effect.destroy:provider.backend",
                                      "instance.destroy:provider.backend",
                                      "effect.dispose:provider.application",
                                      "effect.destroy:provider.application",
                                      "instance.destroy:provider.application",
                                  });
        CHECK(trace.matching("instance.destroy:") == std::vector<std::string>{
                                                         "instance.destroy:provider.episode",
                                                         "instance.destroy:provider.world",
                                                         "instance.destroy:provider.backend",
                                                         "instance.destroy:provider.application",
                                                     });
        CHECK(trace.matching("effect.dispose:") == std::vector<std::string>{
                                                       "effect.dispose:provider.episode",
                                                       "effect.dispose:provider.world",
                                                       "effect.dispose:provider.backend",
                                                       "effect.dispose:provider.application",
                                                   });
    }

    TEST_CASE("construction and effect failures roll back all staged providers") {
        SUBCASE("provider construction failure") {
            Trace trace;
            CatalogBundle bundle(trace);
            bundle.factory("provider.episode")->fail_next_construction();
            auto result = composition::CompositionKernel::realize(make_resolved(), bundle.catalog);
            CHECK_FALSE(result.ok());
            CHECK(result.error().code == composition::kErrorProviderConstructionFailed);
            CHECK(trace.matching("effect.rollback:") == std::vector<std::string>{
                                                            "effect.rollback:provider.episode",
                                                            "effect.rollback:provider.world",
                                                            "effect.rollback:provider.backend",
                                                            "effect.rollback:provider.application",
                                                        });
            CHECK(trace.matching("effect.dispose:").empty());
        }

        SUBCASE("effect commit failure") {
            Trace trace;
            CatalogBundle bundle(trace);
            bundle.factory("provider.world")->fail_next_effect_commit();
            auto result = composition::CompositionKernel::realize(make_resolved(), bundle.catalog);
            CHECK_FALSE(result.ok());
            CHECK(result.error().code == composition::kErrorLifecycleEffectCommitFailed);
            CHECK(trace.matching("effect.rollback:") == std::vector<std::string>{
                                                            "effect.rollback:provider.episode",
                                                            "effect.rollback:provider.world",
                                                            "effect.rollback:provider.backend",
                                                            "effect.rollback:provider.application",
                                                        });
            CHECK(trace.matching("effect.dispose:").empty());
        }
    }

    TEST_CASE("scope rebuild is failure atomic and invalidates only replaced generations") {
        Trace trace;
        CatalogBundle bundle(trace);
        auto runtime = realize(make_resolved(), bundle.catalog);
        const auto application = runtime.service_for<int>("provider", "provider.world",
                                                          contracts::kServiceEnvironmentModel);
        const auto world = runtime.service_for<int>("provider", "provider.episode",
                                                    contracts::kServiceEffectsModel);
        const auto episode =
            runtime.service_for<int>("system", "system.test", contracts::kServiceSensorModel);
        REQUIRE(application.valid());
        REQUIRE(world.valid());
        REQUIRE(episode.valid());

        const auto rejected = runtime.rebuild_scope(contracts::CompositionScope::world, "mid_step");
        CHECK_FALSE(rejected.ok());
        CHECK(rejected.error().code == composition::kErrorRebuildBarrierRejected);

        bundle.factory("provider.episode")->fail_next_construction();
        const auto failed =
            runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild");
        CHECK_FALSE(failed.ok());
        CHECK(application.valid());
        CHECK(world.valid());
        CHECK(episode.valid());
        CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 1);
        CHECK(runtime.scope_generation(contracts::CompositionScope::episode) == 1);

        REQUIRE(runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild").ok());
        CHECK(application.valid());
        CHECK_FALSE(world.valid());
        CHECK_FALSE(episode.valid());
        CHECK(runtime.scope_generation(contracts::CompositionScope::batch) == 1);
        CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 2);
        CHECK(runtime.scope_generation(contracts::CompositionScope::episode) == 2);
        const auto rebuilt_world = runtime.service_for<int>("provider", "provider.episode",
                                                            contracts::kServiceEffectsModel);
        const auto rebuilt_episode =
            runtime.service_for<int>("system", "system.test", contracts::kServiceSensorModel);
        CHECK(rebuilt_world.valid());
        CHECK(rebuilt_episode.valid());
        CHECK(rebuilt_world.generation() == 2);
        CHECK(rebuilt_episode.generation() == 2);

        REQUIRE(runtime.rebuild_scope(contracts::CompositionScope::episode, "episode_end").ok());
        CHECK(rebuilt_world.valid());
        CHECK_FALSE(rebuilt_episode.valid());
        CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 2);
        CHECK(runtime.scope_generation(contracts::CompositionScope::episode) == 3);
    }

    TEST_CASE("scope rebuild fails closed for providers requiring process restart") {
        Trace trace;
        CatalogBundle bundle(trace);
        auto resolved = make_resolved();
        auto world_descriptor = std::find_if(
            resolved.manifest.providers.begin(), resolved.manifest.providers.end(),
            [](const auto &descriptor) { return descriptor.provider_id == "provider.world"; });
        REQUIRE(world_descriptor != resolved.manifest.providers.end());
        world_descriptor->restart_policy = "process_restart";
        refresh_identity(resolved);
        auto runtime = realize(std::move(resolved), bundle.catalog);
        const auto world = runtime.service_for<int>("provider", "provider.episode",
                                                    contracts::kServiceEffectsModel);
        REQUIRE(world.valid());

        const auto rejected =
            runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild");
        CHECK_FALSE(rejected.ok());
        CHECK(rejected.error().code == composition::kErrorRebuildBarrierRejected);
        CHECK(rejected.error().subject == "provider.world");
        CHECK(world.valid());
        CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 1);
    }

    TEST_CASE("typed validation rejects stale identity invalid scopes and explicit self cycles") {
        Trace trace;
        CatalogBundle bundle(trace);

        SUBCASE("stale hash") {
            auto resolved = make_resolved();
            resolved.manifest.composition_id = "test.lifecycle.tampered";
            const auto validation =
                composition::validate_resolved_composition(resolved, bundle.catalog);
            CHECK_FALSE(validation.valid);
            CHECK(std::any_of(validation.issues.begin(), validation.issues.end(),
                              [](const auto &issue) {
                                  return issue.code == composition::kErrorManifestHashMismatch;
                              }));
        }

        SUBCASE("invalid typed scope") {
            auto resolved = make_resolved();
            resolved.manifest.providers.front().scope =
                static_cast<contracts::CompositionScope>(255);
            const auto validation =
                composition::validate_resolved_composition(resolved, bundle.catalog);
            CHECK_FALSE(validation.valid);
            CHECK(std::any_of(validation.issues.begin(), validation.issues.end(),
                              [](const auto &issue) {
                                  return issue.code == contracts::kErrorInvalidScopePolicy;
                              }));

            auto runtime = realize(make_resolved(), bundle.catalog);
            const auto invalid_scope = static_cast<contracts::CompositionScope>(255);
            CHECK(runtime.scope_generation(invalid_scope) == 0);
            const auto rejected = runtime.rebuild_scope(invalid_scope, "world_rebuild");
            CHECK_FALSE(rejected.ok());
            CHECK(rejected.error().code == contracts::kErrorInvalidScopePolicy);
        }

        SUBCASE("provider self dependency") {
            auto resolved = make_resolved();
            resolved.manifest.providers.front().after_provider_ids = {"provider.application"};
            refresh_identity(resolved);
            const auto validation =
                composition::validate_resolved_composition(resolved, bundle.catalog);
            CHECK_FALSE(validation.valid);
            CHECK(std::any_of(validation.issues.begin(), validation.issues.end(),
                              [](const auto &issue) {
                                  return issue.code == contracts::kErrorProviderDependencyCycle;
                              }));
        }

        SUBCASE("system self dependency") {
            auto resolved = make_resolved();
            resolved.manifest.system_contributions.front().after = {"system.test"};
            refresh_identity(resolved);
            const auto validation =
                composition::validate_resolved_composition(resolved, bundle.catalog);
            CHECK_FALSE(validation.valid);
            CHECK(std::any_of(validation.issues.begin(), validation.issues.end(),
                              [](const auto &issue) {
                                  return issue.code == contracts::kErrorSystemDependencyCycle;
                              }));
        }
    }

    TEST_CASE("failed provider cleanup destroys effects before instances") {
        Trace trace;
        CatalogBundle bundle(trace);
        bundle.factory("provider.application")->ignore_lookup_error_next();

        const auto result =
            composition::CompositionKernel::realize(make_resolved(), bundle.catalog);
        CHECK_FALSE(result.ok());
        CHECK(result.error().code == composition::kErrorServiceUnavailable);
        const auto rollback = std::find(trace.entries.begin(), trace.entries.end(),
                                        "effect.rollback:provider.application");
        const auto effect_destroy = std::find(trace.entries.begin(), trace.entries.end(),
                                              "effect.destroy:provider.application");
        const auto instance_destroy = std::find(trace.entries.begin(), trace.entries.end(),
                                                "instance.destroy:provider.application");
        REQUIRE(rollback != trace.entries.end());
        REQUIRE(effect_destroy != trace.entries.end());
        REQUIRE(instance_destroy != trace.entries.end());
        CHECK(rollback < effect_destroy);
        CHECK(effect_destroy < instance_destroy);
    }

    TEST_CASE("lifecycle callbacks cannot reenter stop or rebuild") {
        Trace trace;
        CatalogBundle bundle(trace);
        composition::CompositionRuntime *runtime_pointer = nullptr;
        bool callback_called = false;
        std::string nested_error;
        bundle.factory("provider.episode")->set_dispose_callback([&] {
            callback_called = true;
            runtime_pointer->stop();
            const auto nested =
                runtime_pointer->rebuild_scope(contracts::CompositionScope::world, "world_rebuild");
            nested_error = nested.ok() ? "unexpected_success" : nested.error().code;
        });

        auto runtime = realize(make_resolved(), bundle.catalog);
        runtime_pointer = &runtime;
        runtime.stop();
        CHECK(callback_called);
        CHECK(runtime.shutdown());
        CHECK(nested_error == composition::kErrorRuntimeShutdown);
        CHECK(trace.matching("effect.dispose:provider.episode").size() == 1);
        runtime.stop();
        CHECK(trace.matching("effect.dispose:provider.episode").size() == 1);
    }

    TEST_CASE("catalog snapshots identity and detects metadata mutation") {
        Trace trace;
        CatalogBundle bundle(trace);
        auto resolved = make_resolved();

        CatalogBundle mismatched(trace, "2.0.0");
        const auto validation =
            composition::validate_resolved_composition(resolved, mismatched.catalog);
        CHECK_FALSE(validation.valid);
        CHECK(
            std::any_of(validation.issues.begin(), validation.issues.end(), [](const auto &issue) {
                return issue.code == composition::kErrorFactoryMetadataMismatch;
            }));

        bundle.factory("provider.world")->mutate_identity_version("2.0.0");
        const auto result =
            composition::CompositionKernel::realize(std::move(resolved), bundle.catalog);
        CHECK_FALSE(result.ok());
        CHECK(result.error().code == composition::kErrorFactoryMetadataMismatch);

        Trace rebuild_trace;
        CatalogBundle rebuild_bundle(rebuild_trace);
        auto rebuild_runtime = realize(make_resolved(), rebuild_bundle.catalog);
        rebuild_bundle.factory("provider.application")->mutate_identity_version("2.0.0");
        const auto rebuild_result =
            rebuild_runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild");
        CHECK_FALSE(rebuild_result.ok());
        CHECK(rebuild_result.error().code == composition::kErrorFactoryMetadataMismatch);
        CHECK(rebuild_runtime.scope_generation(contracts::CompositionScope::world) == 1);

        Trace type_trace;
        CatalogBundle type_bundle(type_trace);
        type_bundle.factory("provider.world")->mutate_service_type();
        const auto type_result =
            composition::CompositionKernel::realize(make_resolved(), type_bundle.catalog);
        CHECK_FALSE(type_result.ok());
        CHECK(type_result.error().code == composition::kErrorServiceTypeMismatch);
    }

    TEST_CASE("replacement rebuild updates identity atomically and enforces handover") {
        SUBCASE("successful replacement") {
            Trace trace;
            CatalogBundle current_bundle(trace);
            auto current = make_resolved();
            auto runtime = realize(current, current_bundle.catalog);
            const auto old_world = runtime.service_for<int>("provider", "provider.episode",
                                                            contracts::kServiceEffectsModel);
            REQUIRE(old_world.valid());

            auto replacement = make_resolved();
            auto world = std::find_if(
                replacement.manifest.providers.begin(), replacement.manifest.providers.end(),
                [](const auto &descriptor) { return descriptor.provider_id == "provider.world"; });
            REQUIRE(world != replacement.manifest.providers.end());
            world->implementation_version = "2.0.0";
            world->canonical_configuration_json = "{\"gain\":2}";
            replacement.manifest.composition_id = "test.lifecycle.replacement";
            refresh_identity(replacement);
            const auto expected_requested = replacement.requested_manifest_sha256;
            const auto expected_resolved = replacement.resolved_manifest_sha256;
            CatalogBundle replacement_bundle(trace, "2.0.0", "{\"gain\":2}", 200);

            const auto status =
                runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild",
                                      std::move(replacement), replacement_bundle.catalog);
            REQUIRE(status.ok());
            CHECK_FALSE(old_world.valid());
            CHECK(runtime.requested_manifest_sha256() == expected_requested);
            CHECK(runtime.resolved_manifest_sha256() == expected_resolved);
            CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 2);
            const auto new_world = runtime.service_for<int>("provider", "provider.episode",
                                                            contracts::kServiceEffectsModel);
            REQUIRE(new_world.valid());
            CHECK(*new_world.try_get() > 200);
        }

        SUBCASE("failed replacement preserves old identity and generation") {
            Trace trace;
            CatalogBundle current_bundle(trace);
            auto current = make_resolved();
            auto runtime = realize(current, current_bundle.catalog);
            const std::string old_hash(runtime.resolved_manifest_sha256());
            const auto old_world = runtime.service_for<int>("provider", "provider.episode",
                                                            contracts::kServiceEffectsModel);
            REQUIRE(old_world.valid());

            CatalogBundle replacement_bundle(trace);
            replacement_bundle.factory("provider.episode")->fail_next_construction();
            const auto failed =
                runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild",
                                      make_resolved(), replacement_bundle.catalog);
            CHECK_FALSE(failed.ok());
            CHECK(old_world.valid());
            CHECK(runtime.resolved_manifest_sha256() == old_hash);
            CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 1);
        }

        SUBCASE("unsafe effect handover is rejected before commit") {
            Trace trace;
            CatalogBundle current_bundle(trace);
            auto runtime = realize(make_resolved(), current_bundle.catalog);
            const auto old_world = runtime.service_for<int>("provider", "provider.episode",
                                                            contracts::kServiceEffectsModel);
            REQUIRE(old_world.valid());

            CatalogBundle unsafe_bundle(trace, "1.0.0", "{}", 20, false);
            const auto rejected =
                runtime.rebuild_scope(contracts::CompositionScope::world, "world_rebuild",
                                      make_resolved(), unsafe_bundle.catalog);
            CHECK_FALSE(rejected.ok());
            CHECK(rejected.error().code == composition::kErrorLifecycleHandoverUnsupported);
            CHECK(old_world.valid());
            CHECK(runtime.scope_generation(contracts::CompositionScope::world) == 1);
        }
    }

} // TEST_SUITE("composition_lifecycle")
