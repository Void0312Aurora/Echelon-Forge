#include "runtime/composition/provider_catalog.h"

#include <algorithm>
#include <map>

namespace runtime::composition {

struct ProviderCatalog::Impl {
    bool frozen = false;
    std::map<std::string, std::shared_ptr<IProviderFactory>, std::less<>> factories;
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
    if (!factory || factory->provider_id().empty()) {
        return CompositionStatus::failure(
            {std::string(kErrorInvalidFactory), {}, "factory and provider_id are required"});
    }

    std::string provider_id(factory->provider_id());
    const auto [_, inserted] = impl_->factories.emplace(provider_id, std::move(factory));
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
    return iterator == impl_->factories.end() ? nullptr : iterator->second;
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
