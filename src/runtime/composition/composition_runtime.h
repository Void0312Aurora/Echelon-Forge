#pragma once

#include "runtime/composition/provider_catalog.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <typeinfo>

namespace runtime::composition {

[[nodiscard]] composition_contracts::CompositionValidationResult
validate_resolved_composition(const composition_contracts::ResolvedSimulationComposition &resolved,
                              const ProviderCatalog &catalog);

class CompositionRuntime {
  public:
    CompositionRuntime() = delete;
    ~CompositionRuntime();

    CompositionRuntime(const CompositionRuntime &) = delete;
    CompositionRuntime &operator=(const CompositionRuntime &) = delete;
    CompositionRuntime(CompositionRuntime &&) noexcept;
    CompositionRuntime &operator=(CompositionRuntime &&) noexcept = delete;

    [[nodiscard]] bool frozen() const noexcept;
    [[nodiscard]] bool shutdown() const noexcept;
    [[nodiscard]] std::size_t provider_count() const noexcept;
    [[nodiscard]] std::uint64_t
    scope_generation(composition_contracts::CompositionScope scope) const noexcept;
    [[nodiscard]] std::string requested_manifest_sha256() const;
    [[nodiscard]] std::string resolved_manifest_sha256() const;

    template <typename T>
    [[nodiscard]] ServiceHandle<T> service_for(std::string_view consumer_kind,
                                               std::string_view consumer_id,
                                               std::string_view service_key) const {
        return ServiceHandle<T>(
            lookup_service_for(consumer_kind, consumer_id, service_key, typeid(T)));
    }

    // Composition roots may acquire an admitted provider's explicitly offered
    // service without inventing a second binding consumer. This is restricted
    // to the provider/service pair already present in the frozen manifest.
    template <typename T>
    [[nodiscard]] ServiceHandle<T> root_service(std::string_view provider_id,
                                                std::string_view service_key) const {
        return ServiceHandle<T>(lookup_root_service(provider_id, service_key, typeid(T)));
    }

    [[nodiscard]] CompositionStatus rebuild_scope(composition_contracts::CompositionScope scope,
                                                  std::string_view barrier);
    [[nodiscard]] CompositionStatus
    rebuild_scope(composition_contracts::CompositionScope scope, std::string_view barrier,
                  composition_contracts::ResolvedSimulationComposition replacement,
                  const ProviderCatalog &catalog);
    void stop() noexcept;

  private:
    struct Impl;
    friend class CompositionKernel;

    explicit CompositionRuntime(std::shared_ptr<Impl> impl) noexcept;

    [[nodiscard]] detail::UntypedServiceHandle
    lookup_service_for(std::string_view consumer_kind, std::string_view consumer_id,
                       std::string_view service_key, const std::type_info &requested_type) const;

    [[nodiscard]] detail::UntypedServiceHandle
    lookup_root_service(std::string_view provider_id, std::string_view service_key,
                        const std::type_info &requested_type) const;

    // Public operations retain a local shared reference before entering Impl.
    // This keeps an in-flight lifecycle transaction alive if a callback moves
    // and destroys the public wrapper reentrantly.
    std::shared_ptr<Impl> impl_;
};

using CompositionRuntimeResult = CompositionResult<CompositionRuntime>;

class CompositionKernel {
  public:
    [[nodiscard]] static CompositionRuntimeResult
    realize(composition_contracts::ResolvedSimulationComposition resolved,
            const ProviderCatalog &catalog);
};

} // namespace runtime::composition
