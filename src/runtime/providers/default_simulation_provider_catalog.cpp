#include "runtime/providers/default_simulation_provider_catalog.h"
#if defined(EF_RUNTIME_COMPOSITION_TESTING)
#include "runtime/providers/internal/default_simulation_provider_catalog_test_access.h"
#endif

#include "components/physics/instruments.h"
#include "core/engine/simulation_kernel.h"
#include "core/engine/simulation_kernel_engagement_event_store.h"
#include "core/engine/simulation_kernel_services.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/engagement_event_store.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/unit_factory.h"
#include "core/interfaces/weapon_release_damage_bridge.h"
#include "core/interfaces/weapon_release_service.h"
#include "models/core/default_unit_factory.h"
#include "runtime/composition/composition_json.h"
#include "runtime/composition/composition_runtime.h"
#include "runtime/composition/provider_catalog.h"
#include "runtime/contracts/composition/default_compatibility_manifest.v1.generated.h"
#include "runtime/contracts/backend_profile_contracts.h"
#include "runtime/contracts/simulation_composition_contract.h"
#include "runtime/contracts/world_batch_backend_provider_contract.h"

#include <flecs.h>

#include <exception>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <typeinfo>
#include <utility>
#include <vector>

namespace runtime::providers {
namespace {

namespace composition = runtime::composition;
namespace contracts = runtime::composition_contracts;

constexpr std::string_view kBuiltinPluginId = "builtin.core_runtime";
constexpr std::string_view kEnvironmentProviderId = "builtin.environment.default";
constexpr std::string_view kUnitFactoryProviderId = "builtin.unit_factory.default";
constexpr std::string_view kEffectsProviderId = "builtin.effects.default";
constexpr std::string_view kSensorProviderId = "builtin.sensor.default";
constexpr std::string_view kAcousticProviderId = "builtin.acoustic.default";
constexpr std::string_view kControlProviderId = "builtin.control.default";
constexpr std::string_view kGuidanceProviderId = "builtin.guidance.default";
constexpr std::string_view kEventStoreProviderId = "builtin.engagement_event_store";
constexpr std::string_view kDamageBridgeProviderId = "builtin.weapon_release.damage_bridge";
constexpr std::string_view kWeaponReleaseProviderId = "builtin.weapon_release.service";

composition::CompositionRuntimeError provider_error(std::string_view provider_id,
                                                    std::string detail) {
    return {
        std::string(composition::kErrorProviderConstructionFailed),
        std::string(provider_id),
        std::move(detail),
    };
}

contracts::CompositionPluginDescriptor builtin_plugin_metadata() {
    contracts::CompositionPluginDescriptor plugin;
    plugin.plugin_id = std::string(kBuiltinPluginId);
    plugin.implementation_id = "echelon_forge.native_builtin";
    plugin.plugin_version = "1.0.0";
    plugin.composition_contract_range = ">=1.0.0 <2.0.0";
    plugin.host_support = {"native"};
    plugin.determinism_class = "truth_affecting_deterministic";
    plugin.artifact.kind = "repository_builtin";
    plugin.artifact.identity = "echelon-forge-source-tree";
    plugin.canonical_configuration_json = "{}";
    return plugin;
}

composition::ProviderFactoryMetadata builtin_factory_metadata(std::string_view provider_id,
                                                              contracts::CompositionScope scope) {
    composition::ProviderFactoryMetadata metadata;
    metadata.provider_id = std::string(provider_id);
    metadata.plugin_id = std::string(kBuiltinPluginId);
    metadata.implementation_version = "1.0.0";
    metadata.scope = scope;
    metadata.canonical_configuration_json = "{}";
    metadata.plugin = builtin_plugin_metadata();
    return metadata;
}

class LambdaProviderFactory final : public composition::IProviderFactory {
  public:
    using Construction = std::function<composition::ProviderInstanceResult(
        composition::ProviderConstructionContext &)>;

    LambdaProviderFactory(composition::ProviderFactoryMetadata metadata,
                          std::map<std::string, const std::type_info *, std::less<>> service_types,
                          Construction construction)
        : metadata_(std::move(metadata)), service_types_(std::move(service_types)),
          construction_(std::move(construction)) {}

    [[nodiscard]] composition::ProviderFactoryMetadata metadata() const override {
        return metadata_;
    }

    [[nodiscard]] const std::type_info *
    service_type(std::string_view service_key) const noexcept override {
        const auto iterator = service_types_.find(service_key);
        return iterator == service_types_.end() ? nullptr : iterator->second;
    }

    [[nodiscard]] composition::ProviderInstanceResult
    construct(composition::ProviderConstructionContext &context) override {
        return construction_(context);
    }

  private:
    const composition::ProviderFactoryMetadata metadata_;
    const std::map<std::string, const std::type_info *, std::less<>> service_types_;
    const Construction construction_;
};

template <typename Service>
class SingleServiceInstance final : public composition::IProviderInstance {
  public:
    SingleServiceInstance(std::string service_key, std::unique_ptr<Service> service)
        : service_key_(std::move(service_key)), service_(std::move(service)) {}

    [[nodiscard]] void *query_service(std::string_view service_key,
                                      const std::type_info &requested_type) noexcept override {
        if (service_key != service_key_ || requested_type != typeid(Service)) {
            return nullptr;
        }
        return service_.get();
    }

  private:
    std::string service_key_;
    std::unique_ptr<Service> service_;
};

template <typename Service>
composition::ProviderInstanceResult single_service_instance(std::string_view service_key,
                                                            std::unique_ptr<Service> service) {
    if (!service) {
        return composition::ProviderInstanceResult::failure(
            provider_error({}, "provider created a null service"));
    }
    std::unique_ptr<composition::IProviderInstance> instance =
        std::make_unique<SingleServiceInstance<Service>>(std::string(service_key),
                                                         std::move(service));
    return composition::ProviderInstanceResult::success(std::move(instance));
}

class EngagementEventStoreInstance final : public composition::IProviderInstance {
  public:
    explicit EngagementEventStoreInstance(std::unique_ptr<IEngagementEventStore> store)
        : store_(std::move(store)) {}

    [[nodiscard]] void *query_service(std::string_view service_key,
                                      const std::type_info &requested_type) noexcept override {
        if (service_key == contracts::kServiceEngagementEventRecorder &&
            requested_type == typeid(IEngagementEventRecorder)) {
            return static_cast<IEngagementEventRecorder *>(store_.get());
        }
        if (service_key == contracts::kServiceEngagementEventStore &&
            requested_type == typeid(IEngagementEventStore)) {
            return store_.get();
        }
        return nullptr;
    }

  private:
    std::unique_ptr<IEngagementEventStore> store_;
};

struct DefaultWorldBatchBackendSelection {
    std::string provider_id =
        std::string(runtime::world_batch_backend_contracts::kDefaultProviderId);
    std::string implementation_version =
        std::string(runtime::world_batch_backend_contracts::kDefaultImplementationVersion);
    std::string profile_id =
        std::string(runtime::backend_profiles::kBackendProfileIdCpuExactReference);
    std::vector<std::string> admitted_capabilities = {
        std::string(runtime::world_batch_backend_contracts::kCpuExactCapabilityId)};
};

class SimulationKernelWeaponReleaseDamageBridge final : public IWeaponReleaseDamageBridge {
  public:
    explicit SimulationKernelWeaponReleaseDamageBridge(SimulationKernel &kernel)
        : kernel_(kernel) {}

    bool apply_proximity_hit(std::uint64_t attacker_id, std::uint64_t target_id, double damage,
                             double fuse_distance) override {
        return kernel_.debug_apply_proximity_hit(attacker_id, target_id, damage, fuse_distance);
    }

  private:
    SimulationKernel &kernel_;
};

template <typename Ref, typename Service>
class SingletonServiceEffect final : public composition::ILifecycleEffect {
  public:
    SingletonServiceEffect(flecs::world &world, Service *Ref::*member, Service *service,
                           bool fail_commit = false)
        : world_(world), member_(member), service_(service), fail_commit_(fail_commit) {
        if (const Ref *current = world_.get<Ref>()) {
            previous_ = current->*member_;
        }
    }

    [[nodiscard]] composition::CompositionStatus commit() override {
        if (fail_commit_) {
            return composition::CompositionStatus::failure({
                std::string(composition::kErrorLifecycleEffectCommitFailed),
                {},
                "injected default-provider publication failure",
            });
        }
        try {
            Ref next{};
            next.*member_ = service_;
            world_.set<Ref>(next);
            committed_ = true;
            return composition::CompositionStatus::success();
        } catch (const std::exception &exception) {
            return composition::CompositionStatus::failure({
                std::string(composition::kErrorLifecycleEffectCommitFailed),
                {},
                exception.what(),
            });
        } catch (...) {
            return composition::CompositionStatus::failure({
                std::string(composition::kErrorLifecycleEffectCommitFailed),
                {},
                "Flecs singleton publication failed",
            });
        }
    }

    void rollback() noexcept override {
        if (!committed_ || current_service() != service_) {
            return;
        }
        publish(previous_);
        committed_ = false;
    }

    void dispose() noexcept override {
        if (current_service() == service_) {
            publish(nullptr);
        }
        committed_ = false;
    }

    [[nodiscard]] bool supports_replacement_handover() const noexcept override { return true; }

  private:
    [[nodiscard]] Service *current_service() const noexcept {
        try {
            const Ref *current = world_.get<Ref>();
            return current ? current->*member_ : nullptr;
        } catch (...) {
            return nullptr;
        }
    }

    void publish(Service *service) noexcept {
        try {
            Ref next{};
            next.*member_ = service;
            world_.set<Ref>(next);
        } catch (...) {
        }
    }

    flecs::world &world_;
    Service *Ref::*member_ = nullptr;
    Service *service_ = nullptr;
    Service *previous_ = nullptr;
    bool fail_commit_ = false;
    bool committed_ = false;
};

template <typename Ref, typename Service>
void adopt_singleton_effect(composition::ProviderConstructionContext &context, flecs::world &world,
                            Service *Ref::*member, Service *service, bool fail_commit = false) {
    context.adopt_effect(std::make_unique<SingletonServiceEffect<Ref, Service>>(
        world, member, service, fail_commit));
}

template <typename Dependency>
bool require_service(composition::ProviderConstructionContext &context,
                     std::string_view service_key) {
    return context.service<Dependency>(service_key).valid();
}

std::shared_ptr<composition::IProviderFactory>
make_factory(std::string_view provider_id, contracts::CompositionScope scope,
             std::map<std::string, const std::type_info *, std::less<>> service_types,
             LambdaProviderFactory::Construction construction) {
    return std::make_shared<LambdaProviderFactory>(builtin_factory_metadata(provider_id, scope),
                                                   std::move(service_types),
                                                   std::move(construction));
}

composition::CompositionStatus
register_default_factories(composition::ProviderCatalog &catalog, SimulationKernel &kernel,
                           flecs::world &world, MissileTuning &missile_tuning, std::mt19937 &rng,
                           std::string_view fail_effect_provider = {}) {
    const auto register_factory = [&](std::shared_ptr<composition::IProviderFactory> factory) {
        return catalog.register_factory(std::move(factory));
    };

    auto status = register_factory(make_factory(
        runtime::world_batch_backend_contracts::kDefaultProviderId,
        contracts::CompositionScope::backend,
        {{std::string(contracts::kServiceWorldBatchBackend),
          &typeid(DefaultWorldBatchBackendSelection)}},
        [](composition::ProviderConstructionContext &) {
            return single_service_instance(contracts::kServiceWorldBatchBackend,
                                           std::make_unique<DefaultWorldBatchBackendSelection>());
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kEffectsProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceEffectsModel), &typeid(IEffectsModel)}},
        [&world, fail_effect_provider](composition::ProviderConstructionContext &context) {
            auto service = make_default_effects_model();
            IEffectsModel *pointer = service.get();
            adopt_singleton_effect(context, world, &EffectsModelRef::model, pointer,
                                   fail_effect_provider == kEffectsProviderId);
            return single_service_instance(contracts::kServiceEffectsModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kEventStoreProviderId, contracts::CompositionScope::world,
        {
            {std::string(contracts::kServiceEngagementEventRecorder),
             &typeid(IEngagementEventRecorder)},
            {std::string(contracts::kServiceEngagementEventStore), &typeid(IEngagementEventStore)},
        },
        [&world](composition::ProviderConstructionContext &context) {
            std::unique_ptr<IEngagementEventStore> store =
                std::make_unique<SimulationKernelEngagementEventStore>(world);
            auto *recorder = static_cast<IEngagementEventRecorder *>(store.get());
            adopt_singleton_effect(context, world, &EngagementEventRecorderRef::recorder, recorder);
            std::unique_ptr<composition::IProviderInstance> instance =
                std::make_unique<EngagementEventStoreInstance>(std::move(store));
            return composition::ProviderInstanceResult::success(std::move(instance));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kEnvironmentProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceEnvironmentModel), &typeid(IEnvironmentModel)}},
        [&world](composition::ProviderConstructionContext &context) {
            auto service = make_default_environment_model();
            IEnvironmentModel *pointer = service.get();
            adopt_singleton_effect(context, world, &EnvironmentModelRef::model, pointer);
            return single_service_instance(contracts::kServiceEnvironmentModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kAcousticProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceAcousticModel), &typeid(IAcousticModel)}},
        [&world](composition::ProviderConstructionContext &context) {
            if (!require_service<IEnvironmentModel>(context, contracts::kServiceEnvironmentModel)) {
                return composition::ProviderInstanceResult::failure(
                    provider_error(kAcousticProviderId, "environment dependency is unavailable"));
            }
            auto service = make_default_acoustic_model();
            IAcousticModel *pointer = service.get();
            adopt_singleton_effect(context, world, &AcousticModelRef::model, pointer);
            return single_service_instance(contracts::kServiceAcousticModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kControlProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceControlModel), &typeid(IControlModel)}},
        [&world](composition::ProviderConstructionContext &context) {
            if (!require_service<IEnvironmentModel>(context, contracts::kServiceEnvironmentModel)) {
                return composition::ProviderInstanceResult::failure(
                    provider_error(kControlProviderId, "environment dependency is unavailable"));
            }
            auto service = make_default_control_model();
            IControlModel *pointer = service.get();
            adopt_singleton_effect(context, world, &ControlModelRef::model, pointer);
            return single_service_instance(contracts::kServiceControlModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kGuidanceProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceGuidanceModel), &typeid(IGuidanceModel)}},
        [&world](composition::ProviderConstructionContext &context) {
            if (!require_service<IEnvironmentModel>(context, contracts::kServiceEnvironmentModel) ||
                !require_service<IEngagementEventRecorder>(
                    context, contracts::kServiceEngagementEventRecorder)) {
                return composition::ProviderInstanceResult::failure(
                    provider_error(kGuidanceProviderId, "guidance dependency is unavailable"));
            }
            auto service = make_default_guidance_model();
            IGuidanceModel *pointer = service.get();
            adopt_singleton_effect(context, world, &GuidanceModelRef::model, pointer);
            return single_service_instance(contracts::kServiceGuidanceModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kSensorProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceSensorModel), &typeid(ISensorModel)}},
        [&world](composition::ProviderConstructionContext &context) {
            if (!require_service<IEnvironmentModel>(context, contracts::kServiceEnvironmentModel)) {
                return composition::ProviderInstanceResult::failure(
                    provider_error(kSensorProviderId, "environment dependency is unavailable"));
            }
            auto service = make_default_sensor_model();
            ISensorModel *pointer = service.get();
            adopt_singleton_effect(context, world, &SensorModelRef::model, pointer);
            return single_service_instance(contracts::kServiceSensorModel, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kUnitFactoryProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceUnitFactory), &typeid(IUnitFactory)}},
        [](composition::ProviderConstructionContext &) {
            std::unique_ptr<IUnitFactory> service = std::make_unique<DefaultUnitFactory>();
            return single_service_instance(contracts::kServiceUnitFactory, std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kDamageBridgeProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceWeaponReleaseDamageBridge),
          &typeid(IWeaponReleaseDamageBridge)}},
        [&kernel](composition::ProviderConstructionContext &context) {
            if (!require_service<IEffectsModel>(context, contracts::kServiceEffectsModel)) {
                return composition::ProviderInstanceResult::failure(
                    provider_error(kDamageBridgeProviderId, "effects dependency is unavailable"));
            }
            std::unique_ptr<IWeaponReleaseDamageBridge> service =
                std::make_unique<SimulationKernelWeaponReleaseDamageBridge>(kernel);
            return single_service_instance(contracts::kServiceWeaponReleaseDamageBridge,
                                           std::move(service));
        }));
    if (!status) return status;

    status = register_factory(make_factory(
        kWeaponReleaseProviderId, contracts::CompositionScope::world,
        {{std::string(contracts::kServiceWeaponRelease), &typeid(IWeaponReleaseService)}},
        [&world, &missile_tuning, &rng,
         fail_effect_provider](composition::ProviderConstructionContext &context) {
            auto unit_factory = context.service<IUnitFactory>(contracts::kServiceUnitFactory);
            auto event_store =
                context.service<IEngagementEventStore>(contracts::kServiceEngagementEventStore);
            auto damage_bridge = context.service<IWeaponReleaseDamageBridge>(
                contracts::kServiceWeaponReleaseDamageBridge);
            if (!unit_factory || !event_store || !damage_bridge) {
                return composition::ProviderInstanceResult::failure(provider_error(
                    kWeaponReleaseProviderId, "weapon-release dependency is unavailable"));
            }
            auto service = make_simulation_kernel_weapon_release_service(
                world, *unit_factory.try_get(), missile_tuning, rng, *event_store.try_get(),
                *event_store.try_get(), *damage_bridge.try_get());
            IWeaponReleaseService *pointer = service.get();
            adopt_singleton_effect(context, world, &WeaponReleaseServiceRef::service, pointer,
                                   fail_effect_provider == kWeaponReleaseProviderId);
            return single_service_instance(contracts::kServiceWeaponRelease, std::move(service));
        }));
    if (!status) return status;

    return catalog.freeze();
}

} // namespace

struct DefaultSimulationComposition::Impl {
    explicit Impl(composition::CompositionRuntime runtime_value)
        : runtime(std::move(runtime_value)) {}

    [[nodiscard]] bool refresh_handles() {
        std::lock_guard lock(lifecycle_mutex);
        environment_model = runtime.root_service<IEnvironmentModel>(
            kEnvironmentProviderId, contracts::kServiceEnvironmentModel);
        unit_factory = runtime.root_service<IUnitFactory>(kUnitFactoryProviderId,
                                                          contracts::kServiceUnitFactory);
        effects_model = runtime.root_service<IEffectsModel>(kEffectsProviderId,
                                                            contracts::kServiceEffectsModel);
        sensor_model =
            runtime.root_service<ISensorModel>(kSensorProviderId, contracts::kServiceSensorModel);
        acoustic_model = runtime.root_service<IAcousticModel>(kAcousticProviderId,
                                                              contracts::kServiceAcousticModel);
        control_model = runtime.root_service<IControlModel>(kControlProviderId,
                                                            contracts::kServiceControlModel);
        guidance_model = runtime.root_service<IGuidanceModel>(kGuidanceProviderId,
                                                              contracts::kServiceGuidanceModel);
        engagement_event_store = runtime.root_service<IEngagementEventStore>(
            kEventStoreProviderId, contracts::kServiceEngagementEventStore);
        weapon_release_service = runtime.root_service<IWeaponReleaseService>(
            kWeaponReleaseProviderId, contracts::kServiceWeaponRelease);
        return environment_model && unit_factory && effects_model && sensor_model &&
               acoustic_model && control_model && guidance_model && engagement_event_store &&
               weapon_release_service;
    }

    composition::CompositionRuntime runtime;
    mutable std::recursive_mutex lifecycle_mutex;
    composition::ServiceHandle<IEnvironmentModel> environment_model;
    composition::ServiceHandle<IUnitFactory> unit_factory;
    composition::ServiceHandle<IEffectsModel> effects_model;
    composition::ServiceHandle<ISensorModel> sensor_model;
    composition::ServiceHandle<IAcousticModel> acoustic_model;
    composition::ServiceHandle<IControlModel> control_model;
    composition::ServiceHandle<IGuidanceModel> guidance_model;
    composition::ServiceHandle<IEngagementEventStore> engagement_event_store;
    composition::ServiceHandle<IWeaponReleaseService> weapon_release_service;
};

DefaultSimulationComposition::DefaultSimulationComposition(std::unique_ptr<Impl> impl) noexcept
    : impl_(std::move(impl)) {}

DefaultSimulationComposition::~DefaultSimulationComposition() {
    stop();
}

IEnvironmentModel *DefaultSimulationComposition::environment_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->environment_model.try_get();
}

IUnitFactory *DefaultSimulationComposition::unit_factory() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->unit_factory.try_get();
}

IEffectsModel *DefaultSimulationComposition::effects_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->effects_model.try_get();
}

ISensorModel *DefaultSimulationComposition::sensor_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->sensor_model.try_get();
}

IAcousticModel *DefaultSimulationComposition::acoustic_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->acoustic_model.try_get();
}

IControlModel *DefaultSimulationComposition::control_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->control_model.try_get();
}

IGuidanceModel *DefaultSimulationComposition::guidance_model() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->guidance_model.try_get();
}

IEngagementEventStore *DefaultSimulationComposition::engagement_event_store() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->engagement_event_store.try_get();
}

IWeaponReleaseService *DefaultSimulationComposition::weapon_release_service() const noexcept {
    if (!impl_) return nullptr;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->weapon_release_service.try_get();
}

std::string DefaultSimulationComposition::requested_manifest_sha256() const {
    if (!impl_) return {};
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->runtime.requested_manifest_sha256();
}

std::string DefaultSimulationComposition::resolved_manifest_sha256() const {
    if (!impl_) return {};
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->runtime.resolved_manifest_sha256();
}

std::uint64_t DefaultSimulationComposition::world_generation() const noexcept {
    if (!impl_) return 0;
    std::lock_guard lock(impl_->lifecycle_mutex);
    return impl_->runtime.scope_generation(contracts::CompositionScope::world);
}

std::array<std::uint64_t, 5> DefaultSimulationComposition::scope_generations() const noexcept {
    if (!impl_) return {};
    std::lock_guard lock(impl_->lifecycle_mutex);
    return {
        impl_->runtime.scope_generation(contracts::CompositionScope::application),
        impl_->runtime.scope_generation(contracts::CompositionScope::backend),
        impl_->runtime.scope_generation(contracts::CompositionScope::batch),
        impl_->runtime.scope_generation(contracts::CompositionScope::world),
        impl_->runtime.scope_generation(contracts::CompositionScope::episode),
    };
}

composition::CompositionStatus
DefaultSimulationComposition::rebuild_world(std::string_view barrier) {
    if (!impl_) {
        return composition::CompositionStatus::failure({
            std::string(composition::kErrorRuntimeShutdown),
            std::string(contracts::kScopeWorld),
            "default simulation composition is stopped",
        });
    }
    std::lock_guard lock(impl_->lifecycle_mutex);
    auto status = impl_->runtime.rebuild_scope(contracts::CompositionScope::world, barrier);
    if (!status) {
        return status;
    }
    if (!impl_->refresh_handles()) {
        impl_->runtime.stop();
        return composition::CompositionStatus::failure({
            std::string(composition::kErrorServiceUnavailable),
            std::string(contracts::kScopeWorld),
            "rebuilt default composition did not expose every required root service",
        });
    }
    return composition::CompositionStatus::success();
}

void DefaultSimulationComposition::stop() noexcept {
    if (impl_) {
        std::lock_guard lock(impl_->lifecycle_mutex);
        impl_->runtime.stop();
    }
}

DefaultSimulationCompositionResult build_default_simulation_composition_impl(
    SimulationKernel &kernel, flecs::world &world, MissileTuning &missile_tuning, std::mt19937 &rng,
    std::string_view resolved_manifest_json, std::string_view fail_effect_provider) {
    composition::ProviderCatalog catalog;
    auto catalog_status = register_default_factories(catalog, kernel, world, missile_tuning, rng,
                                                     fail_effect_provider);
    if (!catalog_status) {
        return DefaultSimulationCompositionResult::failure(catalog_status.error());
    }

    const std::string resolved_json(resolved_manifest_json);
    auto parsed = composition::parse_resolved_composition_json(resolved_json);
    if (!parsed) {
        return DefaultSimulationCompositionResult::failure(parsed.error());
    }
    auto realized = composition::CompositionKernel::realize(std::move(parsed).value(), catalog);
    if (!realized) {
        return DefaultSimulationCompositionResult::failure(realized.error());
    }

    auto impl = std::make_unique<DefaultSimulationComposition::Impl>(std::move(realized).value());
    if (!impl->refresh_handles()) {
        impl->runtime.stop();
        return DefaultSimulationCompositionResult::failure({
            std::string(composition::kErrorServiceUnavailable),
            "builtin.default_compatibility",
            "realized default composition did not expose every required root service",
        });
    }
    return DefaultSimulationCompositionResult::success(
        std::unique_ptr<DefaultSimulationComposition>(
            new DefaultSimulationComposition(std::move(impl))));
}

DefaultSimulationCompositionResult
build_default_simulation_composition(SimulationKernel &kernel, flecs::world &world,
                                     MissileTuning &missile_tuning, std::mt19937 &rng,
                                     std::string_view resolved_manifest_json) {
    return build_default_simulation_composition_impl(kernel, world, missile_tuning, rng,
                                                     resolved_manifest_json, {});
}

std::string default_compatibility_resolved_manifest_json() {
    std::string resolved_json;
    for (const auto chunk : contracts::generated::kDefaultCompatibilityResolvedJsonChunks) {
        resolved_json.append(chunk);
    }
    return resolved_json;
}

#if defined(EF_RUNTIME_COMPOSITION_TESTING)
DefaultSimulationCompositionResult
build_default_simulation_composition_for_testing(SimulationKernel &kernel, flecs::world &world,
                                                 MissileTuning &missile_tuning, std::mt19937 &rng) {
    constexpr std::string_view fail_effect_provider = kWeaponReleaseProviderId;
    const std::string resolved_json = default_compatibility_resolved_manifest_json();
    return build_default_simulation_composition_impl(kernel, world, missile_tuning, rng,
                                                     resolved_json, fail_effect_provider);
}
#endif

} // namespace runtime::providers
