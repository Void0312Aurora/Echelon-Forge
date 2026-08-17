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
    [[nodiscard]] std::string_view requested_manifest_sha256() const noexcept;
    [[nodiscard]] std::string_view resolved_manifest_sha256() const noexcept;

    template <typename T>
    [[nodiscard]] ServiceHandle<T> service_for(std::string_view consumer_kind,
                                               std::string_view consumer_id,
                                               std::string_view service_key) const {
        return ServiceHandle<T>(
            lookup_service_for(consumer_kind, consumer_id, service_key, typeid(T)));
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

    explicit CompositionRuntime(std::unique_ptr<Impl> impl) noexcept;

    [[nodiscard]] detail::UntypedServiceHandle
    lookup_service_for(std::string_view consumer_kind, std::string_view consumer_id,
                       std::string_view service_key, const std::type_info &requested_type) const;

    std::unique_ptr<Impl> impl_;
};

using CompositionRuntimeResult = CompositionResult<CompositionRuntime>;

class CompositionKernel {
  public:
    [[nodiscard]] static CompositionRuntimeResult
    realize(composition_contracts::ResolvedSimulationComposition resolved,
            const ProviderCatalog &catalog);
};

} // namespace runtime::composition
