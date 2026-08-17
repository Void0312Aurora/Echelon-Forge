#include "runtime/composition/composition_runtime.h"

#include <algorithm>
#include <array>
#include <exception>
#include <functional>
#include <limits>
#include <map>
#include <optional>
#include <string>
#include <tuple>
#include <utility>

namespace runtime::composition {
namespace {

namespace contracts = composition_contracts;

struct Utf8Less {
    using is_transparent = void;

    [[nodiscard]] bool operator()(std::string_view lhs, std::string_view rhs) const noexcept {
        return std::lexicographical_compare(
            lhs.begin(), lhs.end(), rhs.begin(), rhs.end(), [](char left, char right) {
                return static_cast<unsigned char>(left) < static_cast<unsigned char>(right);
            });
    }
};

using BindingKey = std::tuple<std::string, std::string, std::string>;

[[nodiscard]] constexpr std::size_t scope_index(contracts::CompositionScope scope) noexcept {
    return static_cast<std::size_t>(scope);
}

[[nodiscard]] bool scope_is_affected(contracts::CompositionScope provider_scope,
                                     contracts::CompositionScope rebuilt_scope) noexcept {
    return scope_index(provider_scope) >= scope_index(rebuilt_scope);
}

[[nodiscard]] CompositionRuntimeError exception_error(std::string_view code, std::string subject,
                                                      const std::exception &exception) {
    return {std::string(code), std::move(subject), exception.what()};
}

[[nodiscard]] CompositionRuntimeError unknown_exception_error(std::string_view code,
                                                              std::string subject) {
    return {std::string(code), std::move(subject), "unknown exception"};
}

} // namespace

struct ProviderConstructionContext::Impl {
    const contracts::CompositionProviderDescriptor *descriptor = nullptr;
    std::function<detail::UntypedServiceHandle(std::string_view, const std::type_info &)> lookup;
    std::vector<std::unique_ptr<ILifecycleEffect>> effects;
    mutable std::optional<CompositionRuntimeError> error;
};

const composition_contracts::CompositionProviderDescriptor &
ProviderConstructionContext::descriptor() const noexcept {
    return *impl_->descriptor;
}

detail::UntypedServiceHandle
ProviderConstructionContext::lookup_service(std::string_view service_key,
                                            const std::type_info &requested_type) const {
    if (impl_ == nullptr || !impl_->lookup) {
        return {};
    }
    return impl_->lookup(service_key, requested_type);
}

void ProviderConstructionContext::adopt_effect(std::unique_ptr<ILifecycleEffect> effect) {
    if (impl_ == nullptr) {
        return;
    }
    if (!effect) {
        impl_->error = CompositionRuntimeError{
            std::string(kErrorProviderConstructionFailed),
            impl_->descriptor ? impl_->descriptor->provider_id : std::string{},
            "lifecycle effect must not be null",
        };
        return;
    }
    impl_->effects.push_back(std::move(effect));
}

struct CompositionRuntime::Impl {
    struct ProviderRecord {
        const contracts::CompositionProviderDescriptor *descriptor = nullptr;
        std::shared_ptr<IProviderFactory> factory;
        std::unique_ptr<IProviderInstance> instance;
        std::vector<std::unique_ptr<ILifecycleEffect>> effects;
        std::shared_ptr<detail::ServiceHandleControl> handle_control;

        void release(bool rollback) noexcept {
            if (handle_control) {
                handle_control->active.store(false, std::memory_order_release);
            }
            for (auto iterator = effects.rbegin(); iterator != effects.rend(); ++iterator) {
                if (rollback) {
                    (*iterator)->rollback();
                } else {
                    (*iterator)->dispose();
                }
            }
            effects.clear();
            instance.reset();
        }

        [[nodiscard]] detail::UntypedServiceHandle
        service(std::string_view service_key, const std::type_info &requested_type) const noexcept {
            if (!instance || !factory || !handle_control ||
                !handle_control->active.load(std::memory_order_acquire)) {
                return {};
            }
            const std::type_info *declared_type = factory->service_type(service_key);
            if (declared_type == nullptr || *declared_type != requested_type) {
                return {};
            }
            void *service_pointer = instance->query_service(service_key, requested_type);
            if (service_pointer == nullptr) {
                return {};
            }
            return {handle_control, service_pointer, declared_type};
        }
    };

    using RecordMap = std::map<std::string, std::unique_ptr<ProviderRecord>, Utf8Less>;

    contracts::ResolvedSimulationComposition resolved;
    std::map<std::string, const contracts::CompositionProviderDescriptor *, Utf8Less> descriptors;
    std::map<std::string, std::shared_ptr<IProviderFactory>, Utf8Less> factories;
    std::map<BindingKey, std::string> bindings;
    RecordMap records;
    std::array<std::uint64_t, 5> generations{1, 1, 1, 1, 1};
    bool frozen = false;
    bool stopped = false;

    ~Impl() { stop(); }

    void stop() noexcept {
        if (stopped) {
            return;
        }
        release_records(records, resolved.provider_construction_order, false);
        records.clear();
        frozen = false;
        stopped = true;
    }

    static void release_records(RecordMap &target, const std::vector<std::string> &provider_order,
                                bool rollback) noexcept {
        for (auto iterator = provider_order.rbegin(); iterator != provider_order.rend();
             ++iterator) {
            const auto record = target.find(*iterator);
            if (record != target.end() && record->second) {
                record->second->release(rollback);
            }
        }
    }

    [[nodiscard]] const ProviderRecord *find_record(const RecordMap &candidates,
                                                    std::string_view provider_id) const noexcept {
        const auto candidate = candidates.find(provider_id);
        if (candidate != candidates.end() && candidate->second) {
            return candidate->second.get();
        }
        const auto committed = records.find(provider_id);
        return committed == records.end() ? nullptr : committed->second.get();
    }

    [[nodiscard]] detail::UntypedServiceHandle
    lookup_bound_service(const RecordMap &candidates, std::string_view consumer_kind,
                         std::string_view consumer_id, std::string_view service_key,
                         const std::type_info &requested_type,
                         std::optional<CompositionRuntimeError> *error) const {
        const auto binding = bindings.find(
            {std::string(consumer_kind), std::string(consumer_id), std::string(service_key)});
        if (binding == bindings.end()) {
            if (error != nullptr) {
                *error = CompositionRuntimeError{
                    std::string(kErrorServiceUnavailable),
                    std::string(consumer_id),
                    "no explicit binding for " + std::string(service_key),
                };
            }
            return {};
        }
        const ProviderRecord *provider = find_record(candidates, binding->second);
        if (provider == nullptr || provider->factory == nullptr) {
            if (error != nullptr) {
                *error = CompositionRuntimeError{
                    std::string(kErrorServiceUnavailable),
                    binding->second,
                    std::string(service_key),
                };
            }
            return {};
        }
        const std::type_info *declared_type = provider->factory->service_type(service_key);
        if (declared_type == nullptr || *declared_type != requested_type) {
            if (error != nullptr) {
                *error = CompositionRuntimeError{
                    std::string(kErrorServiceTypeMismatch),
                    binding->second,
                    std::string(service_key),
                };
            }
            return {};
        }
        auto handle = provider->service(service_key, requested_type);
        if (handle.service == nullptr && error != nullptr) {
            *error = CompositionRuntimeError{
                std::string(kErrorServiceUnavailable),
                binding->second,
                std::string(service_key),
            };
        }
        return handle;
    }

    [[nodiscard]] CompositionStatus
    build_candidates(const std::vector<std::string> &provider_ids,
                     const std::array<std::uint64_t, 5> &candidate_generations,
                     RecordMap &candidates) {
        for (const auto &provider_id : provider_ids) {
            const auto descriptor_iterator = descriptors.find(provider_id);
            const auto factory_iterator = factories.find(provider_id);
            if (descriptor_iterator == descriptors.end() || factory_iterator == factories.end()) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({std::string(kErrorFactoryNotFound), provider_id,
                                                   "validated factory is absent"});
            }
            const auto *descriptor = descriptor_iterator->second;
            auto factory = factory_iterator->second;

            ProviderConstructionContext::Impl context_impl;
            context_impl.descriptor = descriptor;
            context_impl.lookup = [&](std::string_view service_key, const std::type_info &type) {
                return lookup_bound_service(candidates, "provider", descriptor->provider_id,
                                            service_key, type, &context_impl.error);
            };
            ProviderConstructionContext context(&context_impl);

            ProviderInstanceResult construction = ProviderInstanceResult::failure({
                std::string(kErrorProviderConstructionFailed),
                provider_id,
                "factory did not return a result",
            });
            try {
                construction = factory->construct(context);
            } catch (const std::exception &exception) {
                for (auto iterator = context_impl.effects.rbegin();
                     iterator != context_impl.effects.rend(); ++iterator) {
                    (*iterator)->rollback();
                }
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorProviderConstructionFailed, provider_id, exception));
            } catch (...) {
                for (auto iterator = context_impl.effects.rbegin();
                     iterator != context_impl.effects.rend(); ++iterator) {
                    (*iterator)->rollback();
                }
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorProviderConstructionFailed, provider_id));
            }

            if (!construction || context_impl.error.has_value()) {
                for (auto iterator = context_impl.effects.rbegin();
                     iterator != context_impl.effects.rend(); ++iterator) {
                    (*iterator)->rollback();
                }
                if (construction) {
                    std::move(construction).value().reset();
                }
                release_records(candidates, provider_ids, true);
                if (context_impl.error.has_value()) {
                    return CompositionStatus::failure(std::move(*context_impl.error));
                }
                auto error = construction.error();
                if (error.code.empty()) {
                    error.code = std::string(kErrorProviderConstructionFailed);
                }
                if (error.subject.empty()) {
                    error.subject = provider_id;
                }
                return CompositionStatus::failure(std::move(error));
            }

            auto instance = std::move(construction).value();
            if (!instance) {
                for (auto iterator = context_impl.effects.rbegin();
                     iterator != context_impl.effects.rend(); ++iterator) {
                    (*iterator)->rollback();
                }
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({
                    std::string(kErrorProviderConstructionFailed),
                    provider_id,
                    "factory returned a null provider instance",
                });
            }

            for (const auto &service_key : descriptor->offered_services) {
                const std::type_info *service_type = factory->service_type(service_key);
                if (service_type == nullptr ||
                    instance->query_service(service_key, *service_type) == nullptr) {
                    for (auto iterator = context_impl.effects.rbegin();
                         iterator != context_impl.effects.rend(); ++iterator) {
                        (*iterator)->rollback();
                    }
                    instance.reset();
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorServiceUnavailable),
                        provider_id,
                        service_key,
                    });
                }
            }

            auto control = std::make_shared<detail::ServiceHandleControl>();
            control->generation = candidate_generations[scope_index(descriptor->scope)];
            control->scope = descriptor->scope;
            control->provider_id = provider_id;
            control->active.store(true, std::memory_order_release);

            auto record = std::make_unique<ProviderRecord>();
            record->descriptor = descriptor;
            record->factory = std::move(factory);
            record->instance = std::move(instance);
            record->effects = std::move(context_impl.effects);
            record->handle_control = std::move(control);
            candidates.emplace(provider_id, std::move(record));
        }
        return CompositionStatus::success();
    }

    [[nodiscard]] CompositionStatus
    commit_candidates(RecordMap &candidates, const std::vector<std::string> &provider_ids) {
        for (const auto &provider_id : provider_ids) {
            const auto record = candidates.find(provider_id);
            if (record == candidates.end() || !record->second) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({
                    std::string(kErrorProviderConstructionFailed),
                    provider_id,
                    "candidate provider record is absent",
                });
            }
            for (auto &effect : record->second->effects) {
                CompositionStatus status = CompositionStatus::failure({
                    std::string(kErrorLifecycleEffectCommitFailed),
                    provider_id,
                    "effect did not return a status",
                });
                try {
                    status = effect->commit();
                } catch (const std::exception &exception) {
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure(
                        exception_error(kErrorLifecycleEffectCommitFailed, provider_id, exception));
                } catch (...) {
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure(
                        unknown_exception_error(kErrorLifecycleEffectCommitFailed, provider_id));
                }
                if (!status) {
                    auto error = status.error();
                    if (error.code.empty()) {
                        error.code = std::string(kErrorLifecycleEffectCommitFailed);
                    }
                    if (error.subject.empty()) {
                        error.subject = provider_id;
                    }
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure(std::move(error));
                }
            }
        }
        return CompositionStatus::success();
    }
};

CompositionRuntime::~CompositionRuntime() = default;

CompositionRuntime::CompositionRuntime(std::unique_ptr<Impl> impl) noexcept
    : impl_(std::move(impl)) {}

CompositionRuntime::CompositionRuntime(CompositionRuntime &&) noexcept = default;

CompositionRuntime &CompositionRuntime::operator=(CompositionRuntime &&) noexcept = default;

bool CompositionRuntime::frozen() const noexcept {
    return impl_ != nullptr && impl_->frozen && !impl_->stopped;
}

bool CompositionRuntime::shutdown() const noexcept {
    return impl_ == nullptr || impl_->stopped;
}

std::size_t CompositionRuntime::provider_count() const noexcept {
    return impl_ == nullptr ? 0 : impl_->records.size();
}

std::uint64_t
CompositionRuntime::scope_generation(composition_contracts::CompositionScope scope) const noexcept {
    return impl_ == nullptr ? 0 : impl_->generations[scope_index(scope)];
}

detail::UntypedServiceHandle
CompositionRuntime::lookup_service_for(std::string_view consumer_kind, std::string_view consumer_id,
                                       std::string_view service_key,
                                       const std::type_info &requested_type) const {
    if (!frozen()) {
        return {};
    }
    const Impl::RecordMap no_candidates;
    return impl_->lookup_bound_service(no_candidates, consumer_kind, consumer_id, service_key,
                                       requested_type, nullptr);
}

CompositionStatus CompositionRuntime::rebuild_scope(composition_contracts::CompositionScope scope,
                                                    std::string_view barrier) {
    if (impl_ == nullptr || impl_->stopped) {
        return CompositionStatus::failure(
            {std::string(kErrorRuntimeShutdown), {}, "composition runtime is stopped"});
    }
    if (!impl_->frozen) {
        return CompositionStatus::failure(
            {std::string(kErrorRuntimeNotFrozen), {}, "composition runtime is not frozen"});
    }
    const auto &allowed = impl_->resolved.manifest.reconfiguration_policy.allowed_barriers;
    if (std::find(allowed.begin(), allowed.end(), barrier) == allowed.end()) {
        return CompositionStatus::failure({
            std::string(kErrorRebuildBarrierRejected),
            std::string(contracts::to_string(scope)),
            std::string(barrier),
        });
    }

    auto candidate_generations = impl_->generations;
    for (std::size_t index = scope_index(scope); index < candidate_generations.size(); ++index) {
        if (candidate_generations[index] == std::numeric_limits<std::uint64_t>::max()) {
            return CompositionStatus::failure({
                std::string(kErrorProviderConstructionFailed),
                std::string(contracts::to_string(scope)),
                "scope generation exhausted",
            });
        }
        ++candidate_generations[index];
    }

    std::vector<std::string> affected;
    for (const auto &provider_id : impl_->resolved.provider_construction_order) {
        const auto descriptor = impl_->descriptors.find(provider_id);
        if (descriptor != impl_->descriptors.end() &&
            scope_is_affected(descriptor->second->scope, scope)) {
            if (descriptor->second->restart_policy != "rebuild_scope_generation") {
                return CompositionStatus::failure({
                    std::string(kErrorRebuildBarrierRejected),
                    provider_id,
                    "provider restart policy requires " + descriptor->second->restart_policy,
                });
            }
            affected.push_back(provider_id);
        }
    }

    CompositionRuntime::Impl::RecordMap candidates;
    auto build_status = impl_->build_candidates(affected, candidate_generations, candidates);
    if (!build_status) {
        return build_status;
    }
    auto commit_status = impl_->commit_candidates(candidates, affected);
    if (!commit_status) {
        return commit_status;
    }

    Impl::RecordMap retired;
    for (const auto &provider_id : affected) {
        auto current = impl_->records.find(provider_id);
        if (current != impl_->records.end()) {
            retired.emplace(provider_id, std::move(current->second));
        }
        auto candidate = candidates.find(provider_id);
        if (candidate != candidates.end()) {
            impl_->records[provider_id] = std::move(candidate->second);
        }
    }
    impl_->generations = candidate_generations;
    Impl::release_records(retired, affected, false);
    return CompositionStatus::success();
}

void CompositionRuntime::stop() noexcept {
    if (impl_ != nullptr) {
        impl_->stop();
    }
}

CompositionRuntimeResult
CompositionKernel::realize(composition_contracts::ResolvedSimulationComposition resolved,
                           const ProviderCatalog &catalog) {
    const auto validation = validate_resolved_composition(resolved, catalog);
    if (!validation.valid) {
        const auto &issue = validation.issues.front();
        return CompositionRuntimeResult::failure({issue.code, issue.path, issue.detail});
    }

    auto impl = std::make_unique<CompositionRuntime::Impl>();
    impl->resolved = std::move(resolved);
    for (const auto &provider : impl->resolved.manifest.providers) {
        impl->descriptors.emplace(provider.provider_id, &provider);
        impl->factories.emplace(provider.provider_id, catalog.find(provider.provider_id));
    }
    for (const auto &binding : impl->resolved.manifest.service_bindings) {
        impl->bindings.emplace(
            BindingKey{binding.consumer_kind, binding.consumer_id, binding.service_key},
            binding.provider_id);
    }

    CompositionRuntime::Impl::RecordMap candidates;
    auto build_status = impl->build_candidates(impl->resolved.provider_construction_order,
                                               impl->generations, candidates);
    if (!build_status) {
        return CompositionRuntimeResult::failure(build_status.error());
    }
    auto commit_status =
        impl->commit_candidates(candidates, impl->resolved.provider_construction_order);
    if (!commit_status) {
        return CompositionRuntimeResult::failure(commit_status.error());
    }

    impl->records = std::move(candidates);
    impl->frozen = true;
    impl->stopped = false;
    return CompositionRuntimeResult::success(CompositionRuntime(std::move(impl)));
}

} // namespace runtime::composition
