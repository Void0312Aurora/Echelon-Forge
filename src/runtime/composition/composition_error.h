#pragma once

#include <optional>
#include <string>
#include <string_view>
#include <utility>

namespace runtime::composition {

inline constexpr std::string_view kErrorCatalogFrozen = "runtime.composition.catalog_frozen";
inline constexpr std::string_view kErrorCatalogNotFrozen = "runtime.composition.catalog_not_frozen";
inline constexpr std::string_view kErrorDuplicateFactory = "runtime.composition.duplicate_factory";
inline constexpr std::string_view kErrorInvalidFactory = "runtime.composition.invalid_factory";
inline constexpr std::string_view kErrorFactoryNotFound = "runtime.composition.factory_not_found";
inline constexpr std::string_view kErrorFactoryServiceTypeMissing =
    "runtime.composition.factory_service_type_missing";
inline constexpr std::string_view kErrorResolvedOrderMismatch =
    "runtime.composition.resolved_order_mismatch";
inline constexpr std::string_view kErrorProviderConstructionFailed =
    "runtime.composition.provider_construction_failed";
inline constexpr std::string_view kErrorLifecycleEffectCommitFailed =
    "runtime.composition.lifecycle_effect_commit_failed";
inline constexpr std::string_view kErrorServiceUnavailable =
    "runtime.composition.service_unavailable";
inline constexpr std::string_view kErrorServiceTypeMismatch =
    "runtime.composition.service_type_mismatch";
inline constexpr std::string_view kErrorRuntimeNotFrozen = "runtime.composition.runtime_not_frozen";
inline constexpr std::string_view kErrorRuntimeShutdown = "runtime.composition.runtime_shutdown";
inline constexpr std::string_view kErrorRebuildBarrierRejected =
    "runtime.composition.rebuild_barrier_rejected";

struct CompositionRuntimeError {
    std::string code;
    std::string subject;
    std::string detail;
};

class CompositionStatus {
  public:
    [[nodiscard]] static CompositionStatus success() { return CompositionStatus{}; }

    [[nodiscard]] static CompositionStatus failure(CompositionRuntimeError error) {
        CompositionStatus status;
        status.error_ = std::move(error);
        return status;
    }

    [[nodiscard]] bool ok() const noexcept { return !error_.has_value(); }

    [[nodiscard]] explicit operator bool() const noexcept { return ok(); }

    [[nodiscard]] const CompositionRuntimeError &error() const { return error_.value(); }

  private:
    std::optional<CompositionRuntimeError> error_;
};

template <typename T> class CompositionResult {
  public:
    [[nodiscard]] static CompositionResult success(T value) {
        CompositionResult result;
        result.value_.emplace(std::move(value));
        return result;
    }

    [[nodiscard]] static CompositionResult failure(CompositionRuntimeError error) {
        CompositionResult result;
        result.error_ = std::move(error);
        return result;
    }

    [[nodiscard]] bool ok() const noexcept { return value_.has_value(); }

    [[nodiscard]] explicit operator bool() const noexcept { return ok(); }

    [[nodiscard]] T &value() & { return value_.value(); }

    [[nodiscard]] const T &value() const & { return value_.value(); }

    [[nodiscard]] T &&value() && { return std::move(value_.value()); }

    [[nodiscard]] const CompositionRuntimeError &error() const { return error_.value(); }

  private:
    std::optional<T> value_;
    std::optional<CompositionRuntimeError> error_;
};

} // namespace runtime::composition
