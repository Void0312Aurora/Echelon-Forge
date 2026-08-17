#include "runtime/composition/provider_catalog.h"

#include <algorithm>
#include <array>
#include <exception>
#include <map>

namespace runtime::composition {

namespace {

namespace contracts = composition_contracts;

constexpr std::array<std::string_view, 12> kKnownServiceKeys = {
    contracts::kServiceEnvironmentModel,
    contracts::kServiceUnitFactory,
    contracts::kServiceEffectsModel,
    contracts::kServiceSensorModel,
    contracts::kServiceAcousticModel,
    contracts::kServiceControlModel,
    contracts::kServiceGuidanceModel,
    contracts::kServiceEngagementEventRecorder,
    contracts::kServiceWeaponReleaseDamageBridge,
    contracts::kServiceWeaponRelease,
    contracts::kServiceWorldBatchBackend,
    contracts::kServiceCompositionEvidenceSink,
};

} // namespace

struct ProviderCatalog::Impl {
    struct Entry {
        ProviderFactoryMetadata metadata;
        std::shared_ptr<IProviderFactory> factory;
        std::map<std::string, const std::type_info *, std::less<>> service_types;
    };

    bool frozen = false;
    std::map<std::string, Entry, std::less<>> factories;
};

ProviderCatalog::ProviderCatalog() : impl_(std::make_unique<Impl>()) {}

ProviderCatalog::~ProviderCatalog() = default;

ProviderCatalog::ProviderCatalog(ProviderCatalog &&) noexcept = default;

ProviderCatalog &ProviderCatalog::operator=(ProviderCatalog &&) noexcept = default;

CompositionStatus ProviderCatalog::register_factory(std::shared_ptr<IProviderFactory> factory) {
    if (impl_->frozen) {
        return CompositionStatus::failure(
            {std::string(kErrorCatalogFrozen), {}, "provider catalog is frozen"});
    }
    if (!factory) {
        return CompositionStatus::failure(
            {std::string(kErrorInvalidFactory), {}, "factory and provider_id are required"});
    }

    ProviderFactoryMetadata metadata;
    try {
        metadata = factory->metadata();
    } catch (const std::exception &exception) {
        return CompositionStatus::failure(
            {std::string(kErrorInvalidFactory), {}, exception.what()});
    } catch (...) {
        return CompositionStatus::failure(
            {std::string(kErrorInvalidFactory), {}, "factory metadata threw an unknown exception"});
    }
    if (metadata.provider_id.empty() || metadata.plugin_id.empty() ||
        metadata.implementation_version.empty() ||
        !composition_contracts::is_valid_scope(metadata.scope) ||
        metadata.canonical_configuration_json.empty() ||
        metadata.plugin.plugin_id != metadata.plugin_id ||
        metadata.plugin.implementation_id.empty() || metadata.plugin.plugin_version.empty() ||
        metadata.plugin.composition_contract_range.empty() ||
        metadata.plugin.host_support.empty() || metadata.plugin.artifact.kind.empty() ||
        metadata.plugin.artifact.identity.empty() ||
        metadata.plugin.canonical_configuration_json.empty()) {
        return CompositionStatus::failure({
            std::string(kErrorInvalidFactory),
            metadata.provider_id,
            "factory identity metadata is incomplete or invalid",
        });
    }

    std::string provider_id = metadata.provider_id;
    Impl::Entry entry;
    entry.metadata = std::move(metadata);
    entry.factory = std::move(factory);
    for (const auto service_key : kKnownServiceKeys) {
        if (const auto *service_type = entry.factory->service_type(service_key)) {
            entry.service_types.emplace(std::string(service_key), service_type);
        }
    }
    const auto [_, inserted] = impl_->factories.emplace(provider_id, std::move(entry));
    if (!inserted) {
        return CompositionStatus::failure({
            std::string(kErrorDuplicateFactory),
            std::move(provider_id),
            "provider factory is already registered",
        });
    }
    return CompositionStatus::success();
}

CompositionStatus ProviderCatalog::freeze() {
    impl_->frozen = true;
    return CompositionStatus::success();
}

bool ProviderCatalog::frozen() const noexcept {
    return impl_->frozen;
}

std::shared_ptr<IProviderFactory>
ProviderCatalog::find(std::string_view provider_id) const noexcept {
    const auto iterator = impl_->factories.find(provider_id);
    return iterator == impl_->factories.end() ? nullptr : iterator->second.factory;
}

const ProviderFactoryMetadata *
ProviderCatalog::metadata(std::string_view provider_id) const noexcept {
    const auto iterator = impl_->factories.find(provider_id);
    return iterator == impl_->factories.end() ? nullptr : &iterator->second.metadata;
}

const std::type_info *ProviderCatalog::service_type(std::string_view provider_id,
                                                    std::string_view service_key) const noexcept {
    const auto provider = impl_->factories.find(provider_id);
    if (provider == impl_->factories.end()) {
        return nullptr;
    }
    const auto service = provider->second.service_types.find(service_key);
    return service == provider->second.service_types.end() ? nullptr : service->second;
}

std::vector<std::string> ProviderCatalog::provider_ids() const {
    std::vector<std::string> result;
    result.reserve(impl_->factories.size());
    for (const auto &[provider_id, _] : impl_->factories) {
        result.push_back(provider_id);
    }
    return result;
}

} // namespace runtime::composition
