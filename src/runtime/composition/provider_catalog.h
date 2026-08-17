#pragma once

#include "runtime/composition/composition_error.h"
#include "runtime/contracts/simulation_composition_contract.h"

#include <atomic>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <typeinfo>
#include <utility>
#include <vector>

namespace runtime::composition {

namespace detail {

struct ServiceHandleControl {
    std::atomic<bool> active{false};
    std::uint64_t generation = 0;
    composition_contracts::CompositionScope scope = composition_contracts::CompositionScope::world;
    std::string provider_id;
};

struct UntypedServiceHandle {
    std::weak_ptr<ServiceHandleControl> control;
    void *service = nullptr;
    const std::type_info *type = nullptr;
};

} // namespace detail

template <typename T> class ServiceHandle {
  public:
    ServiceHandle() = default;

    [[nodiscard]] T *try_get() const noexcept {
        const auto control = control_.lock();
        if (!control || !control->active.load(std::memory_order_acquire) || service_ == nullptr ||
            type_ == nullptr || *type_ != typeid(T)) {
            return nullptr;
        }
        return static_cast<T *>(service_);
    }

    [[nodiscard]] bool valid() const noexcept { return try_get() != nullptr; }

    [[nodiscard]] explicit operator bool() const noexcept { return valid(); }

    [[nodiscard]] std::uint64_t generation() const noexcept {
        const auto control = control_.lock();
        return control ? control->generation : 0;
    }

    [[nodiscard]] composition_contracts::CompositionScope scope() const noexcept {
        const auto control = control_.lock();
        return control ? control->scope : composition_contracts::CompositionScope::world;
    }

    [[nodiscard]] std::string provider_id() const {
        const auto control = control_.lock();
        return control ? control->provider_id : std::string{};
    }

  private:
    friend class ProviderConstructionContext;
    friend class CompositionRuntime;

    explicit ServiceHandle(detail::UntypedServiceHandle handle)
        : control_(std::move(handle.control)), service_(handle.service), type_(handle.type) {}

    std::weak_ptr<detail::ServiceHandleControl> control_;
    void *service_ = nullptr;
    const std::type_info *type_ = nullptr;
};

class ILifecycleEffect {
  public:
    virtual ~ILifecycleEffect() = default;

    // commit() publishes the staged effect. rollback() must reverse either a
    // staged or committed effect and must be idempotent. dispose() performs the
    // normal committed teardown path. Both terminal methods are noexcept so a
    // lifecycle transaction can always finish unwinding.
    [[nodiscard]] virtual CompositionStatus commit() = 0;
    virtual void rollback() noexcept = 0;
    virtual void dispose() noexcept = 0;

    // Replacement rebuild commits the new generation before retiring the old
    // generation. Returning true is a contract that commit/rollback/dispose
    // operate on an effect-owned token or generation, so disposing the retired
    // effect cannot erase the replacement publication.
    [[nodiscard]] virtual bool supports_replacement_handover() const noexcept { return false; }
};

class IProviderInstance {
  public:
    virtual ~IProviderInstance() = default;

    [[nodiscard]] virtual void *query_service(std::string_view service_key,
                                              const std::type_info &requested_type) noexcept = 0;
};

class ProviderConstructionContext {
  public:
    // The context object, descriptor reference, and raw pointer obtained from
    // ServiceHandle<T>::try_get() are valid only synchronously during
    // IProviderFactory::construct(). A provider instance may retain the
    // ServiceHandle value itself; its generation control makes try_get()
    // fail closed after the supplying provider is retired.
    ProviderConstructionContext(const ProviderConstructionContext &) = delete;
    ProviderConstructionContext &operator=(const ProviderConstructionContext &) = delete;

    [[nodiscard]] const composition_contracts::CompositionProviderDescriptor &
    descriptor() const noexcept;

    template <typename T>
    [[nodiscard]] ServiceHandle<T> service(std::string_view service_key) const {
        return ServiceHandle<T>(lookup_service(service_key, typeid(T)));
    }

    void adopt_effect(std::unique_ptr<ILifecycleEffect> effect);

  private:
    struct Impl;
    friend class CompositionRuntime;
    friend class CompositionKernel;

    explicit ProviderConstructionContext(Impl *impl) noexcept : impl_(impl) {}

    [[nodiscard]] detail::UntypedServiceHandle
    lookup_service(std::string_view service_key, const std::type_info &requested_type) const;

    Impl *impl_ = nullptr;
};

using ProviderInstanceResult = CompositionResult<std::unique_ptr<IProviderInstance>>;

struct ProviderFactoryMetadata {
    std::string provider_id;
    std::string plugin_id;
    std::string implementation_version;
    composition_contracts::CompositionScope scope = composition_contracts::CompositionScope::world;
    std::string canonical_configuration_json;
    // Exact plugin identity implemented by this factory. Provider-only metadata
    // is insufficient because replacement evidence also claims plugin version,
    // artifact, host, determinism, capability, and plugin configuration fields.
    composition_contracts::CompositionPluginDescriptor plugin;
};

class IProviderFactory {
  public:
    virtual ~IProviderFactory() = default;

    [[nodiscard]] virtual ProviderFactoryMetadata metadata() const = 0;
    [[nodiscard]] virtual const std::type_info *
    service_type(std::string_view service_key) const noexcept = 0;
    [[nodiscard]] virtual ProviderInstanceResult
    construct(ProviderConstructionContext &context) = 0;
};

class ProviderCatalog {
  public:
    ProviderCatalog();
    ~ProviderCatalog();

    ProviderCatalog(const ProviderCatalog &) = delete;
    ProviderCatalog &operator=(const ProviderCatalog &) = delete;
    ProviderCatalog(ProviderCatalog &&) noexcept;
    ProviderCatalog &operator=(ProviderCatalog &&) noexcept;

    [[nodiscard]] CompositionStatus register_factory(std::shared_ptr<IProviderFactory> factory);
    [[nodiscard]] CompositionStatus freeze();

    [[nodiscard]] bool frozen() const noexcept;
    [[nodiscard]] std::shared_ptr<IProviderFactory>
    find(std::string_view provider_id) const noexcept;
    [[nodiscard]] const ProviderFactoryMetadata *
    metadata(std::string_view provider_id) const noexcept;
    [[nodiscard]] const std::type_info *service_type(std::string_view provider_id,
                                                     std::string_view service_key) const noexcept;
    [[nodiscard]] std::vector<std::string> provider_ids() const;

  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace runtime::composition
