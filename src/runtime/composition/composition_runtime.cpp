#include "runtime/composition/composition_runtime.h"

#include <algorithm>
#include <array>
#include <exception>
#include <functional>
#include <limits>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <tuple>
#include <type_traits>
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
    return contracts::is_valid_scope(provider_scope) && contracts::is_valid_scope(rebuilt_scope) &&
           scope_index(provider_scope) >= scope_index(rebuilt_scope);
}

[[nodiscard]] CompositionRuntimeError exception_error(std::string_view code, std::string subject,
                                                      const std::exception &exception) {
    return {std::string(code), std::move(subject), exception.what()};
}

[[nodiscard]] CompositionRuntimeError unknown_exception_error(std::string_view code,
                                                              std::string subject) {
    return {std::string(code), std::move(subject), "unknown exception"};
}

void sort_strings(std::vector<std::string> &values) {
    std::sort(values.begin(), values.end(), Utf8Less{});
}

[[nodiscard]] contracts::CompositionPluginDescriptor
canonical_plugin(contracts::CompositionPluginDescriptor value) {
    sort_strings(value.host_support);
    sort_strings(value.required_capabilities);
    sort_strings(value.conflicts);
    return value;
}

[[nodiscard]] bool
factory_metadata_matches(const ProviderFactoryMetadata &metadata,
                         const contracts::CompositionProviderDescriptor &descriptor,
                         const contracts::CompositionPluginDescriptor &plugin) {
    return metadata.provider_id == descriptor.provider_id &&
           metadata.plugin_id == descriptor.plugin_id &&
           metadata.implementation_version == descriptor.implementation_version &&
           metadata.scope == descriptor.scope &&
           metadata.canonical_configuration_json == descriptor.canonical_configuration_json &&
           canonical_plugin(metadata.plugin) == canonical_plugin(plugin);
}

[[nodiscard]] contracts::CompositionProviderDescriptor
canonical_provider(contracts::CompositionProviderDescriptor value) {
    sort_strings(value.offered_services);
    sort_strings(value.required_services);
    sort_strings(value.required_capabilities);
    sort_strings(value.conflicts);
    sort_strings(value.after_provider_ids);
    return value;
}

[[nodiscard]] std::vector<contracts::CompositionComponentContribution>
canonical_components(std::vector<contracts::CompositionComponentContribution> values) {
    std::sort(values.begin(), values.end(), [](const auto &left, const auto &right) {
        return Utf8Less{}(left.component_id, right.component_id);
    });
    return values;
}

[[nodiscard]] contracts::CompositionSystemContribution
canonical_system(contracts::CompositionSystemContribution value) {
    sort_strings(value.required_services);
    sort_strings(value.required_components);
    sort_strings(value.provided_components);
    sort_strings(value.semantic_stage_ids);
    sort_strings(value.executable_node_ids);
    sort_strings(value.read_state_shards);
    sort_strings(value.write_state_shards);
    sort_strings(value.required_barriers);
    sort_strings(value.required_capabilities);
    sort_strings(value.conflicts);
    sort_strings(value.after);
    sort_strings(value.before);
    return value;
}

[[nodiscard]] std::vector<contracts::CompositionSystemContribution>
canonical_systems(std::vector<contracts::CompositionSystemContribution> values) {
    for (auto &value : values) {
        value = canonical_system(std::move(value));
    }
    std::sort(values.begin(), values.end(), [](const auto &left, const auto &right) {
        return Utf8Less{}(left.contribution_id, right.contribution_id);
    });
    return values;
}

[[nodiscard]] std::vector<contracts::CompositionServiceBinding>
canonical_bindings(std::vector<contracts::CompositionServiceBinding> values) {
    std::sort(values.begin(), values.end(), [](const auto &left, const auto &right) {
        return std::tie(left.consumer_kind, left.consumer_id, left.service_key, left.provider_id) <
               std::tie(right.consumer_kind, right.consumer_id, right.service_key,
                        right.provider_id);
    });
    return values;
}

[[nodiscard]] std::vector<contracts::CompositionScopePolicy>
canonical_scope_policies(std::vector<contracts::CompositionScopePolicy> values) {
    std::sort(values.begin(), values.end(), [](const auto &left, const auto &right) {
        return scope_index(left.scope) < scope_index(right.scope);
    });
    return values;
}

[[nodiscard]] contracts::CompositionReconfigurationPolicy
canonical_reconfiguration(contracts::CompositionReconfigurationPolicy value) {
    sort_strings(value.allowed_barriers);
    return value;
}

[[nodiscard]] contracts::CompositionBackendRequest
canonical_backend(contracts::CompositionBackendRequest value) {
    sort_strings(value.required_capabilities);
    return value;
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
    try {
        impl_->effects.push_back(std::move(effect));
    } catch (...) {
        if (effect) {
            effect->rollback();
        }
        throw;
    }
}

struct CompositionRuntime::Impl {
    struct ProviderRecord {
        using ServiceTypeMap = std::map<std::string, const std::type_info *, Utf8Less>;

        std::shared_ptr<IProviderFactory> factory;
        ServiceTypeMap service_types;
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

        [[nodiscard]] bool supports_replacement_handover() const noexcept {
            return std::all_of(effects.begin(), effects.end(), [](const auto &effect) {
                return effect && effect->supports_replacement_handover();
            });
        }

        [[nodiscard]] detail::UntypedServiceHandle
        service(std::string_view service_key, const std::type_info &requested_type) const noexcept {
            if (!instance || !factory || !handle_control ||
                !handle_control->active.load(std::memory_order_acquire)) {
                return {};
            }
            const auto declared = service_types.find(service_key);
            if (declared == service_types.end() || declared->second == nullptr ||
                *declared->second != requested_type) {
                return {};
            }
            void *service_pointer = instance->query_service(service_key, requested_type);
            if (service_pointer == nullptr) {
                return {};
            }
            return {handle_control, service_pointer, declared->second};
        }
    };

    using DescriptorIndexMap = std::map<std::string, std::size_t, Utf8Less>;
    using PluginMap = std::map<std::string, contracts::CompositionPluginDescriptor, Utf8Less>;
    using FactoryMap = std::map<std::string, std::shared_ptr<IProviderFactory>, Utf8Less>;
    using BindingMap = std::map<BindingKey, std::string>;
    using ServiceTypeKey = std::pair<std::string, std::string>;
    using ServiceTypeMap = std::map<ServiceTypeKey, const std::type_info *>;
    using RecordMap = std::map<std::string, std::unique_ptr<ProviderRecord>, Utf8Less>;

    struct PreparedPlan {
        contracts::ResolvedSimulationComposition resolved;
        DescriptorIndexMap descriptors;
        PluginMap plugins;
        FactoryMap factories;
        BindingMap bindings;
        ServiceTypeMap service_types;
    };

    enum class LifecycleState {
        constructing,
        frozen,
        rebuilding,
        stopping,
        stopped,
    };

    std::unique_ptr<PreparedPlan> plan;
    RecordMap records;
    std::array<std::uint64_t, 5> generations{1, 1, 1, 1, 1};
    mutable std::recursive_mutex lifecycle_mutex;
    LifecycleState state = LifecycleState::constructing;

    ~Impl() { stop(); }

    [[nodiscard]] static PreparedPlan
    prepare_plan(contracts::ResolvedSimulationComposition resolved,
                 const ProviderCatalog &catalog) {
        PreparedPlan prepared;
        prepared.resolved = std::move(resolved);
        for (const auto &plugin : prepared.resolved.manifest.plugins) {
            prepared.plugins.emplace(plugin.plugin_id, plugin);
        }
        for (std::size_t index = 0; index < prepared.resolved.manifest.providers.size(); ++index) {
            const auto &provider = prepared.resolved.manifest.providers[index];
            prepared.descriptors.emplace(provider.provider_id, index);
            prepared.factories.emplace(provider.provider_id, catalog.find(provider.provider_id));
            for (const auto &service_key : provider.offered_services) {
                prepared.service_types.emplace(
                    ServiceTypeKey{provider.provider_id, service_key},
                    catalog.service_type(provider.provider_id, service_key));
            }
        }
        for (const auto &binding : prepared.resolved.manifest.service_bindings) {
            prepared.bindings.emplace(
                BindingKey{binding.consumer_kind, binding.consumer_id, binding.service_key},
                binding.provider_id);
        }
        return prepared;
    }

    [[nodiscard]] static const contracts::CompositionProviderDescriptor *
    descriptor_for(const PreparedPlan &prepared, std::string_view provider_id) noexcept {
        const auto iterator = prepared.descriptors.find(provider_id);
        if (iterator == prepared.descriptors.end() ||
            iterator->second >= prepared.resolved.manifest.providers.size()) {
            return nullptr;
        }
        return &prepared.resolved.manifest.providers[iterator->second];
    }

    [[nodiscard]] static const contracts::CompositionPluginDescriptor *
    plugin_for(const PreparedPlan &prepared, std::string_view plugin_id) noexcept {
        const auto iterator = prepared.plugins.find(plugin_id);
        return iterator == prepared.plugins.end() ? nullptr : &iterator->second;
    }

    [[nodiscard]] static const std::type_info *
    service_type_for(const PreparedPlan &prepared, std::string_view provider_id,
                     std::string_view service_key) noexcept {
        const auto iterator = std::find_if(
            prepared.service_types.begin(), prepared.service_types.end(), [&](const auto &entry) {
                return entry.first.first == provider_id && entry.first.second == service_key;
            });
        return iterator == prepared.service_types.end() ? nullptr : iterator->second;
    }

    static void rollback_effects(std::vector<std::unique_ptr<ILifecycleEffect>> &effects) noexcept {
        for (auto iterator = effects.rbegin(); iterator != effects.rend(); ++iterator) {
            (*iterator)->rollback();
        }
        effects.clear();
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

    struct CandidateRollbackGuard {
        RecordMap &records;
        const std::vector<std::string> &provider_order;
        bool active = true;

        ~CandidateRollbackGuard() {
            if (active) {
                release_records(records, provider_order, true);
            }
        }

        void dismiss() noexcept { active = false; }
    };

    struct PendingProviderRollbackGuard {
        std::vector<std::unique_ptr<ILifecycleEffect>> &effects;
        std::unique_ptr<IProviderInstance> &instance;
        bool active = true;

        ~PendingProviderRollbackGuard() {
            if (active) {
                rollback_effects(effects);
                instance.reset();
            }
        }

        void dismiss() noexcept { active = false; }
    };

    void stop() noexcept {
        std::lock_guard lock(lifecycle_mutex);
        if (state == LifecycleState::stopping || state == LifecycleState::stopped ||
            state == LifecycleState::rebuilding) {
            return;
        }
        state = LifecycleState::stopping;
        RecordMap retiring;
        retiring.swap(records);
        if (plan) {
            release_records(retiring, plan->resolved.provider_construction_order, false);
        }
        retiring.clear();
        state = LifecycleState::stopped;
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
    lookup_bound_service(const PreparedPlan &prepared, const RecordMap &candidates,
                         std::string_view consumer_kind, std::string_view consumer_id,
                         std::string_view service_key, const std::type_info &requested_type,
                         std::optional<CompositionRuntimeError> *error) const {
        const auto binding = prepared.bindings.find(
            {std::string(consumer_kind), std::string(consumer_id), std::string(service_key)});
        if (binding == prepared.bindings.end()) {
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
        const auto declared = provider->service_types.find(service_key);
        if (declared == provider->service_types.end() || declared->second == nullptr ||
            *declared->second != requested_type) {
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
    build_candidates(const PreparedPlan &prepared, const std::vector<std::string> &provider_ids,
                     const std::array<std::uint64_t, 5> &candidate_generations,
                     RecordMap &candidates) {
        CandidateRollbackGuard candidate_guard{candidates, provider_ids};
        for (const auto &provider_id : provider_ids) {
            const auto *descriptor = descriptor_for(prepared, provider_id);
            const auto factory_iterator = prepared.factories.find(provider_id);
            if (descriptor == nullptr || factory_iterator == prepared.factories.end() ||
                !factory_iterator->second) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({std::string(kErrorFactoryNotFound), provider_id,
                                                   "validated factory is absent"});
            }
            if (!contracts::is_valid_scope(descriptor->scope)) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({
                    std::string(contracts::kErrorInvalidScopePolicy),
                    provider_id,
                    "provider scope is outside the v1 scope domain",
                });
            }

            typename RecordMap::iterator slot;
            try {
                const auto [iterator, inserted] = candidates.try_emplace(provider_id, nullptr);
                if (!inserted) {
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorProviderConstructionFailed),
                        provider_id,
                        "candidate provider slot already exists",
                    });
                }
                slot = iterator;
            } catch (const std::exception &exception) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorProviderConstructionFailed, provider_id, exception));
            } catch (...) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorProviderConstructionFailed, provider_id));
            }

            auto factory = factory_iterator->second;
            try {
                const auto *plugin = plugin_for(prepared, descriptor->plugin_id);
                if (plugin == nullptr ||
                    !factory_metadata_matches(factory->metadata(), *descriptor, *plugin)) {
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorFactoryMetadataMismatch),
                        provider_id,
                        "factory identity changed after catalog freeze",
                    });
                }
            } catch (const std::exception &exception) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorFactoryMetadataMismatch, provider_id, exception));
            } catch (...) {
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorFactoryMetadataMismatch, provider_id));
            }

            ProviderConstructionContext::Impl context_impl;
            context_impl.descriptor = descriptor;
            context_impl.lookup = [&](std::string_view service_key, const std::type_info &type) {
                return lookup_bound_service(prepared, candidates, "provider",
                                            descriptor->provider_id, service_key, type,
                                            &context_impl.error);
            };
            ProviderConstructionContext context(&context_impl);
            std::unique_ptr<IProviderInstance> instance;
            PendingProviderRollbackGuard pending_guard{context_impl.effects, instance};

            ProviderInstanceResult construction = ProviderInstanceResult::failure({
                std::string(kErrorProviderConstructionFailed),
                provider_id,
                "factory did not return a result",
            });
            try {
                construction = factory->construct(context);
            } catch (const std::exception &exception) {
                rollback_effects(context_impl.effects);
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorProviderConstructionFailed, provider_id, exception));
            } catch (...) {
                rollback_effects(context_impl.effects);
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorProviderConstructionFailed, provider_id));
            }

            if (!construction || context_impl.error.has_value()) {
                if (construction) {
                    instance = std::move(construction).value();
                }
                rollback_effects(context_impl.effects);
                instance.reset();
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

            instance = std::move(construction).value();
            if (!instance) {
                rollback_effects(context_impl.effects);
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure({
                    std::string(kErrorProviderConstructionFailed),
                    provider_id,
                    "factory returned a null provider instance",
                });
            }

            try {
                const auto *plugin = plugin_for(prepared, descriptor->plugin_id);
                if (plugin == nullptr ||
                    !factory_metadata_matches(factory->metadata(), *descriptor, *plugin)) {
                    rollback_effects(context_impl.effects);
                    instance.reset();
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorFactoryMetadataMismatch),
                        provider_id,
                        "factory identity changed during construction",
                    });
                }
            } catch (const std::exception &exception) {
                rollback_effects(context_impl.effects);
                instance.reset();
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorFactoryMetadataMismatch, provider_id, exception));
            } catch (...) {
                rollback_effects(context_impl.effects);
                instance.reset();
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorFactoryMetadataMismatch, provider_id));
            }

            for (const auto &service_key : descriptor->offered_services) {
                const auto *frozen_type = service_type_for(prepared, provider_id, service_key);
                const std::type_info *live_type = factory->service_type(service_key);
                if (frozen_type == nullptr || live_type == nullptr || *live_type != *frozen_type) {
                    rollback_effects(context_impl.effects);
                    instance.reset();
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorServiceTypeMismatch),
                        provider_id,
                        service_key,
                    });
                }
                if (instance->query_service(service_key, *frozen_type) == nullptr) {
                    rollback_effects(context_impl.effects);
                    instance.reset();
                    release_records(candidates, provider_ids, true);
                    return CompositionStatus::failure({
                        std::string(kErrorServiceUnavailable),
                        provider_id,
                        service_key,
                    });
                }
            }

            std::unique_ptr<ProviderRecord> record;
            try {
                auto control = std::make_shared<detail::ServiceHandleControl>();
                control->generation = candidate_generations[scope_index(descriptor->scope)];
                control->scope = descriptor->scope;
                control->provider_id = provider_id;
                control->active.store(true, std::memory_order_release);

                record = std::make_unique<ProviderRecord>();
                record->factory = std::move(factory);
                for (const auto &service_key : descriptor->offered_services) {
                    record->service_types.emplace(
                        service_key, service_type_for(prepared, provider_id, service_key));
                }
                record->instance = std::move(instance);
                record->effects = std::move(context_impl.effects);
                record->handle_control = std::move(control);
                slot->second = std::move(record);
                pending_guard.dismiss();
            } catch (const std::exception &exception) {
                if (record) {
                    record->release(true);
                }
                rollback_effects(context_impl.effects);
                instance.reset();
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    exception_error(kErrorProviderConstructionFailed, provider_id, exception));
            } catch (...) {
                if (record) {
                    record->release(true);
                }
                rollback_effects(context_impl.effects);
                instance.reset();
                release_records(candidates, provider_ids, true);
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorProviderConstructionFailed, provider_id));
            }
        }
        candidate_guard.dismiss();
        return CompositionStatus::success();
    }

    [[nodiscard]] CompositionStatus
    validate_factory_identity_after_commit(const PreparedPlan &prepared,
                                           const RecordMap &candidates) const {
        for (const auto &provider_id : prepared.resolved.provider_construction_order) {
            const auto *descriptor = descriptor_for(prepared, provider_id);
            const auto *plugin =
                descriptor == nullptr ? nullptr : plugin_for(prepared, descriptor->plugin_id);
            const auto prepared_factory = prepared.factories.find(provider_id);
            const auto *live_record = find_record(candidates, provider_id);
            if (descriptor == nullptr || plugin == nullptr ||
                prepared_factory == prepared.factories.end() || !prepared_factory->second ||
                live_record == nullptr || !live_record->factory) {
                return CompositionStatus::failure({
                    std::string(kErrorProviderConstructionFailed),
                    provider_id,
                    "active or prepared provider identity record is absent",
                });
            }

            try {
                if (!factory_metadata_matches(prepared_factory->second->metadata(), *descriptor,
                                              *plugin) ||
                    !factory_metadata_matches(live_record->factory->metadata(), *descriptor,
                                              *plugin)) {
                    return CompositionStatus::failure({
                        std::string(kErrorFactoryMetadataMismatch),
                        provider_id,
                        "active or prepared factory identity changed while lifecycle effects "
                        "committed",
                    });
                }
            } catch (const std::exception &exception) {
                return CompositionStatus::failure(
                    exception_error(kErrorFactoryMetadataMismatch, provider_id, exception));
            } catch (...) {
                return CompositionStatus::failure(
                    unknown_exception_error(kErrorFactoryMetadataMismatch, provider_id));
            }

            for (const auto &service_key : descriptor->offered_services) {
                const auto *frozen_type = service_type_for(prepared, provider_id, service_key);
                const auto *prepared_type = prepared_factory->second->service_type(service_key);
                const auto *live_type = live_record->factory->service_type(service_key);
                if (frozen_type == nullptr || prepared_type == nullptr || live_type == nullptr ||
                    *prepared_type != *frozen_type || *live_type != *frozen_type) {
                    return CompositionStatus::failure({
                        std::string(kErrorServiceTypeMismatch),
                        provider_id,
                        "active or prepared service type changed while lifecycle effects "
                        "committed: " +
                            service_key,
                    });
                }
            }
        }
        return CompositionStatus::success();
    }

    [[nodiscard]] CompositionStatus
    commit_candidates(const PreparedPlan &prepared, RecordMap &candidates,
                      const std::vector<std::string> &provider_ids) {
        CandidateRollbackGuard candidate_guard{candidates, provider_ids};
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
        auto identity_status = validate_factory_identity_after_commit(prepared, candidates);
        if (!identity_status) {
            release_records(candidates, provider_ids, true);
            return identity_status;
        }
        candidate_guard.dismiss();
        return CompositionStatus::success();
    }

    [[nodiscard]] CompositionStatus
    validate_replacement_boundary(contracts::CompositionScope scope,
                                  const PreparedPlan &replacement) const {
        const auto &current_manifest = plan->resolved.manifest;
        const auto &next_manifest = replacement.resolved.manifest;
        if (canonical_components(current_manifest.component_contributions) !=
                canonical_components(next_manifest.component_contributions) ||
            canonical_systems(current_manifest.system_contributions) !=
                canonical_systems(next_manifest.system_contributions) ||
            plan->resolved.system_registration_order !=
                replacement.resolved.system_registration_order) {
            return CompositionStatus::failure({
                std::string(kErrorReplacementBoundaryViolation),
                std::string(contracts::to_string(scope)),
                "provider replacement cannot mutate component or system contributions",
            });
        }
        if (canonical_scope_policies(current_manifest.scope_policies) !=
                canonical_scope_policies(next_manifest.scope_policies) ||
            canonical_reconfiguration(current_manifest.reconfiguration_policy) !=
                canonical_reconfiguration(next_manifest.reconfiguration_policy) ||
            current_manifest.evidence_policy != next_manifest.evidence_policy ||
            canonical_bindings(current_manifest.service_bindings) !=
                canonical_bindings(next_manifest.service_bindings)) {
            return CompositionStatus::failure({
                std::string(kErrorReplacementBoundaryViolation),
                std::string(contracts::to_string(scope)),
                "scope, reconfiguration, and evidence policies are immutable during rebuild",
            });
        }
        if (scope_index(scope) > scope_index(contracts::CompositionScope::backend) &&
            canonical_backend(current_manifest.backend_request) !=
                canonical_backend(next_manifest.backend_request)) {
            return CompositionStatus::failure({
                std::string(kErrorReplacementBoundaryViolation),
                std::string(contracts::to_string(scope)),
                "backend selection can change only at application/backend rebuild scope",
            });
        }

        const auto factory_identity_matches =
            [](const PreparedPlan &prepared,
               const contracts::CompositionProviderDescriptor &descriptor) {
                const auto factory = prepared.factories.find(descriptor.provider_id);
                const auto *plugin = plugin_for(prepared, descriptor.plugin_id);
                if (factory == prepared.factories.end() || !factory->second || plugin == nullptr) {
                    return false;
                }
                try {
                    return factory_metadata_matches(factory->second->metadata(), descriptor,
                                                    *plugin);
                } catch (...) {
                    return false;
                }
            };
        std::set<std::string, Utf8Less> affected_plugin_ids;
        std::set<std::string, Utf8Less> immutable_contribution_plugin_ids;
        for (const auto &component : current_manifest.component_contributions) {
            immutable_contribution_plugin_ids.emplace(component.plugin_id);
        }
        for (const auto &system : current_manifest.system_contributions) {
            immutable_contribution_plugin_ids.emplace(system.plugin_id);
        }
        for (const auto &[provider_id, index] : plan->descriptors) {
            const auto &descriptor = current_manifest.providers[index];
            if (!factory_identity_matches(*plan, descriptor)) {
                return CompositionStatus::failure(
                    {std::string(kErrorFactoryMetadataMismatch), provider_id,
                     "current factory identity changed after catalog freeze"});
            }
            if (scope_is_affected(descriptor.scope, scope)) {
                affected_plugin_ids.emplace(descriptor.plugin_id);
                continue;
            }
            const auto current_plugin = std::find_if(
                current_manifest.plugins.begin(), current_manifest.plugins.end(),
                [&](const auto &plugin) { return plugin.plugin_id == descriptor.plugin_id; });
            const auto replacement_plugin = std::find_if(
                next_manifest.plugins.begin(), next_manifest.plugins.end(),
                [&](const auto &plugin) { return plugin.plugin_id == descriptor.plugin_id; });
            if (current_plugin == current_manifest.plugins.end() ||
                replacement_plugin == next_manifest.plugins.end() ||
                canonical_plugin(*current_plugin) != canonical_plugin(*replacement_plugin)) {
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    provider_id,
                    "plugin identity used by an unaffected provider changed",
                });
            }
        }

        for (const auto &[provider_id, index] : plan->descriptors) {
            const auto &descriptor = current_manifest.providers[index];
            if (scope_is_affected(descriptor.scope, scope)) {
                continue;
            }
            const auto *replacement_descriptor = descriptor_for(replacement, provider_id);
            if (replacement_descriptor == nullptr ||
                canonical_provider(*replacement_descriptor) != canonical_provider(descriptor)) {
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    provider_id,
                    "provider outside the rebuilt scope changed",
                });
            }
        }
        for (const auto &[provider_id, index] : replacement.descriptors) {
            const auto &descriptor = next_manifest.providers[index];
            if (!factory_identity_matches(replacement, descriptor)) {
                return CompositionStatus::failure(
                    {std::string(kErrorFactoryMetadataMismatch), provider_id,
                     "replacement factory identity changed after catalog freeze"});
            }
            if (scope_is_affected(descriptor.scope, scope)) {
                affected_plugin_ids.emplace(descriptor.plugin_id);
                continue;
            }
            const auto *current_descriptor = descriptor_for(*plan, provider_id);
            if (current_descriptor == nullptr ||
                canonical_provider(*current_descriptor) != canonical_provider(descriptor)) {
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    provider_id,
                    "replacement added or moved a provider outside the rebuilt scope",
                });
            }
        }

        for (const auto &plugin : current_manifest.plugins) {
            if (affected_plugin_ids.contains(plugin.plugin_id) &&
                !immutable_contribution_plugin_ids.contains(plugin.plugin_id)) {
                continue;
            }
            const auto replacement_plugin = std::find_if(
                next_manifest.plugins.begin(), next_manifest.plugins.end(),
                [&](const auto &candidate) { return candidate.plugin_id == plugin.plugin_id; });
            if (replacement_plugin == next_manifest.plugins.end() ||
                canonical_plugin(*replacement_plugin) != canonical_plugin(plugin)) {
                return CompositionStatus::failure(
                    {std::string(kErrorReplacementBoundaryViolation), plugin.plugin_id,
                     "plugin identity outside the rebuilt scope changed"});
            }
        }
        for (const auto &plugin : next_manifest.plugins) {
            if (affected_plugin_ids.contains(plugin.plugin_id) &&
                !immutable_contribution_plugin_ids.contains(plugin.plugin_id)) {
                continue;
            }
            const auto current_plugin = std::find_if(
                current_manifest.plugins.begin(), current_manifest.plugins.end(),
                [&](const auto &candidate) { return candidate.plugin_id == plugin.plugin_id; });
            if (current_plugin == current_manifest.plugins.end()) {
                return CompositionStatus::failure(
                    {std::string(kErrorReplacementBoundaryViolation), plugin.plugin_id,
                     "replacement added a plugin outside the rebuilt scope"});
            }
        }

        for (const auto &[service_key, current_type] : plan->service_types) {
            const auto replacement_type = replacement.service_types.find(service_key);
            if (replacement_type == replacement.service_types.end() ||
                replacement_type->second == nullptr || current_type == nullptr ||
                *replacement_type->second != *current_type) {
                return CompositionStatus::failure({std::string(kErrorReplacementBoundaryViolation),
                                                   service_key.first + ":" + service_key.second,
                                                   "service type changed across replacement"});
            }
        }
        for (const auto &[service_key, replacement_type] : replacement.service_types) {
            const auto current_type = plan->service_types.find(service_key);
            if (current_type == plan->service_types.end() || current_type->second == nullptr ||
                replacement_type == nullptr || *current_type->second != *replacement_type) {
                return CompositionStatus::failure(
                    {std::string(kErrorReplacementBoundaryViolation),
                     service_key.first + ":" + service_key.second,
                     "replacement introduced or changed a service type"});
            }
        }

        for (const auto &binding : current_manifest.service_bindings) {
            if (binding.consumer_kind != "provider") {
                continue;
            }
            const auto *consumer = descriptor_for(*plan, binding.consumer_id);
            if (consumer == nullptr || scope_is_affected(consumer->scope, scope)) {
                continue;
            }
            if (std::find(next_manifest.service_bindings.begin(),
                          next_manifest.service_bindings.end(),
                          binding) == next_manifest.service_bindings.end()) {
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    binding.consumer_id,
                    "binding retained by an unaffected provider changed",
                });
            }
        }
        for (const auto &binding : next_manifest.service_bindings) {
            if (binding.consumer_kind != "provider") {
                continue;
            }
            const auto *consumer = descriptor_for(replacement, binding.consumer_id);
            if (consumer == nullptr || scope_is_affected(consumer->scope, scope)) {
                continue;
            }
            if (std::find(current_manifest.service_bindings.begin(),
                          current_manifest.service_bindings.end(),
                          binding) == current_manifest.service_bindings.end()) {
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    binding.consumer_id,
                    "replacement introduced a binding for an unaffected provider",
                });
            }
        }
        return CompositionStatus::success();
    }

    [[nodiscard]] CompositionStatus rebuild(contracts::CompositionScope scope,
                                            std::string_view barrier,
                                            std::unique_ptr<PreparedPlan> replacement) {
        std::lock_guard lock(lifecycle_mutex);
        if (state == LifecycleState::stopped || state == LifecycleState::stopping) {
            return CompositionStatus::failure(
                {std::string(kErrorRuntimeShutdown), {}, "composition runtime is stopped"});
        }
        if (state == LifecycleState::rebuilding) {
            return CompositionStatus::failure({
                std::string(kErrorLifecycleOperationInProgress),
                std::string(contracts::to_string(scope)),
                "a lifecycle rebuild is already in progress",
            });
        }
        if (state != LifecycleState::frozen) {
            return CompositionStatus::failure(
                {std::string(kErrorRuntimeNotFrozen), {}, "composition runtime is not frozen"});
        }
        if (!contracts::is_valid_scope(scope)) {
            return CompositionStatus::failure({
                std::string(contracts::kErrorInvalidScopePolicy),
                "$.scope",
                "scope is outside the v1 scope domain",
            });
        }
        const auto &current_allowed =
            plan->resolved.manifest.reconfiguration_policy.allowed_barriers;
        const auto &replacement_allowed =
            replacement->resolved.manifest.reconfiguration_policy.allowed_barriers;
        if (std::find(current_allowed.begin(), current_allowed.end(), barrier) ==
                current_allowed.end() ||
            std::find(replacement_allowed.begin(), replacement_allowed.end(), barrier) ==
                replacement_allowed.end()) {
            return CompositionStatus::failure({
                std::string(kErrorRebuildBarrierRejected),
                std::string(contracts::to_string(scope)),
                std::string(barrier),
            });
        }
        auto boundary_status = validate_replacement_boundary(scope, *replacement);
        if (!boundary_status) {
            return boundary_status;
        }

        state = LifecycleState::rebuilding;
        struct StateRestore {
            Impl &owner;
            ~StateRestore() {
                if (owner.state == LifecycleState::rebuilding) {
                    owner.state = LifecycleState::frozen;
                }
            }
        } state_restore{*this};

        auto candidate_generations = generations;
        for (std::size_t index = scope_index(scope); index < candidate_generations.size();
             ++index) {
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
        for (const auto &provider_id : replacement->resolved.provider_construction_order) {
            const auto *descriptor = descriptor_for(*replacement, provider_id);
            if (descriptor != nullptr && scope_is_affected(descriptor->scope, scope)) {
                if (descriptor->restart_policy != "rebuild_scope_generation") {
                    return CompositionStatus::failure({
                        std::string(kErrorRebuildBarrierRejected),
                        provider_id,
                        "provider restart policy requires " + descriptor->restart_policy,
                    });
                }
                affected.push_back(provider_id);
            }
        }

        RecordMap next_records;
        try {
            for (const auto &provider_id : replacement->resolved.provider_construction_order) {
                next_records.try_emplace(provider_id, nullptr);
            }
        } catch (const std::exception &exception) {
            return CompositionStatus::failure(
                exception_error(kErrorProviderConstructionFailed,
                                std::string(contracts::to_string(scope)), exception));
        } catch (...) {
            return CompositionStatus::failure(unknown_exception_error(
                kErrorProviderConstructionFailed, std::string(contracts::to_string(scope))));
        }

        RecordMap candidates;
        auto build_status =
            build_candidates(*replacement, affected, candidate_generations, candidates);
        if (!build_status) {
            return build_status;
        }

        bool has_retired_effects = false;
        bool has_candidate_effects = false;
        bool handover_safe = true;
        for (const auto &[provider_id, record] : records) {
            const auto *descriptor = descriptor_for(*plan, provider_id);
            if (record && descriptor != nullptr && scope_is_affected(descriptor->scope, scope) &&
                !record->effects.empty()) {
                has_retired_effects = true;
                handover_safe = handover_safe && record->supports_replacement_handover();
            }
        }
        for (const auto &[_, record] : candidates) {
            if (record && !record->effects.empty()) {
                has_candidate_effects = true;
                handover_safe = handover_safe && record->supports_replacement_handover();
            }
        }
        if (has_retired_effects && has_candidate_effects && !handover_safe) {
            release_records(candidates, affected, true);
            return CompositionStatus::failure({
                std::string(kErrorLifecycleHandoverUnsupported),
                std::string(contracts::to_string(scope)),
                "replacement effects must be generation/token aware",
            });
        }

        for (const auto &provider_id : replacement->resolved.provider_construction_order) {
            const auto *descriptor = descriptor_for(*replacement, provider_id);
            if (descriptor != nullptr && !scope_is_affected(descriptor->scope, scope) &&
                !records.contains(provider_id)) {
                release_records(candidates, affected, true);
                return CompositionStatus::failure({
                    std::string(kErrorReplacementBoundaryViolation),
                    provider_id,
                    "unaffected provider record is absent",
                });
            }
        }

        auto commit_status = commit_candidates(*replacement, candidates, affected);
        if (!commit_status) {
            return commit_status;
        }

        for (const auto &provider_id : replacement->resolved.provider_construction_order) {
            auto candidate = candidates.find(provider_id);
            if (candidate != candidates.end() && candidate->second) {
                next_records.find(provider_id)->second = std::move(candidate->second);
                continue;
            }
            auto current = records.find(provider_id);
            if (current != records.end()) {
                next_records.find(provider_id)->second = std::move(current->second);
            }
        }

        records.swap(next_records);
        plan.swap(replacement);
        generations = candidate_generations;
        release_records(next_records, replacement->resolved.provider_construction_order, false);
        state = LifecycleState::frozen;
        return CompositionStatus::success();
    }
};

CompositionRuntime::~CompositionRuntime() {
    // Clear wrapper ownership before invoking callbacks. A dispose callback may
    // inspect or move the public wrapper; it must observe an inert wrapper
    // rather than reenter the shared_ptr member currently being destroyed.
    auto impl = std::move(impl_);
    if (impl != nullptr) {
        impl->stop();
    }
}

CompositionRuntime::CompositionRuntime(std::shared_ptr<Impl> impl) noexcept
    : impl_(std::move(impl)) {}

CompositionRuntime::CompositionRuntime(CompositionRuntime &&) noexcept = default;

bool CompositionRuntime::frozen() const noexcept {
    const auto impl = impl_;
    if (impl == nullptr) {
        return false;
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->state == Impl::LifecycleState::frozen;
}

bool CompositionRuntime::shutdown() const noexcept {
    const auto impl = impl_;
    if (impl == nullptr) {
        return true;
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->state == Impl::LifecycleState::stopped;
}

std::size_t CompositionRuntime::provider_count() const noexcept {
    const auto impl = impl_;
    if (impl == nullptr) {
        return 0;
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->records.size();
}

std::uint64_t
CompositionRuntime::scope_generation(composition_contracts::CompositionScope scope) const noexcept {
    const auto impl = impl_;
    if (impl == nullptr || !contracts::is_valid_scope(scope)) {
        return 0;
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->generations[scope_index(scope)];
}

std::string CompositionRuntime::requested_manifest_sha256() const {
    const auto impl = impl_;
    if (impl == nullptr) {
        return {};
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->plan == nullptr ? std::string{} : impl->plan->resolved.requested_manifest_sha256;
}

std::string CompositionRuntime::resolved_manifest_sha256() const {
    const auto impl = impl_;
    if (impl == nullptr) {
        return {};
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    return impl->plan == nullptr ? std::string{} : impl->plan->resolved.resolved_manifest_sha256;
}

detail::UntypedServiceHandle
CompositionRuntime::lookup_service_for(std::string_view consumer_kind, std::string_view consumer_id,
                                       std::string_view service_key,
                                       const std::type_info &requested_type) const {
    const auto impl = impl_;
    if (impl == nullptr) {
        return {};
    }
    std::lock_guard lock(impl->lifecycle_mutex);
    if (impl->state != Impl::LifecycleState::frozen || impl->plan == nullptr) {
        return {};
    }
    const Impl::RecordMap no_candidates;
    return impl->lookup_bound_service(*impl->plan, no_candidates, consumer_kind, consumer_id,
                                      service_key, requested_type, nullptr);
}

CompositionStatus CompositionRuntime::rebuild_scope(composition_contracts::CompositionScope scope,
                                                    std::string_view barrier) {
    const auto impl = impl_;
    if (impl == nullptr) {
        return CompositionStatus::failure(
            {std::string(kErrorRuntimeShutdown), {}, "composition runtime is stopped"});
    }
    try {
        std::lock_guard lock(impl->lifecycle_mutex);
        if (impl->plan == nullptr) {
            return CompositionStatus::failure(
                {std::string(kErrorRuntimeShutdown), {}, "composition runtime is stopped"});
        }
        return impl->rebuild(scope, barrier, std::make_unique<Impl::PreparedPlan>(*impl->plan));
    } catch (const std::exception &exception) {
        return CompositionStatus::failure(exception_error(
            kErrorProviderConstructionFailed, std::string(contracts::to_string(scope)), exception));
    } catch (...) {
        return CompositionStatus::failure(unknown_exception_error(
            kErrorProviderConstructionFailed, std::string(contracts::to_string(scope))));
    }
}

CompositionStatus
CompositionRuntime::rebuild_scope(composition_contracts::CompositionScope scope,
                                  std::string_view barrier,
                                  composition_contracts::ResolvedSimulationComposition replacement,
                                  const ProviderCatalog &catalog) {
    const auto impl = impl_;
    if (impl == nullptr) {
        return CompositionStatus::failure(
            {std::string(kErrorRuntimeShutdown), {}, "composition runtime is stopped"});
    }
    const auto validation = validate_resolved_composition(replacement, catalog);
    if (!validation.valid) {
        const auto &issue = validation.issues.front();
        return CompositionStatus::failure({issue.code, issue.path, issue.detail});
    }
    try {
        return impl->rebuild(scope, barrier,
                             std::make_unique<Impl::PreparedPlan>(
                                 Impl::prepare_plan(std::move(replacement), catalog)));
    } catch (const std::exception &exception) {
        return CompositionStatus::failure(exception_error(
            kErrorProviderConstructionFailed, std::string(contracts::to_string(scope)), exception));
    } catch (...) {
        return CompositionStatus::failure(unknown_exception_error(
            kErrorProviderConstructionFailed, std::string(contracts::to_string(scope))));
    }
}

void CompositionRuntime::stop() noexcept {
    const auto impl = impl_;
    if (impl != nullptr) {
        impl->stop();
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

    auto impl = std::make_shared<CompositionRuntime::Impl>();
    try {
        impl->plan = std::make_unique<CompositionRuntime::Impl::PreparedPlan>(
            CompositionRuntime::Impl::prepare_plan(std::move(resolved), catalog));
    } catch (const std::exception &exception) {
        return CompositionRuntimeResult::failure(
            exception_error(kErrorProviderConstructionFailed, "prepare_plan", exception));
    } catch (...) {
        return CompositionRuntimeResult::failure(
            unknown_exception_error(kErrorProviderConstructionFailed, "prepare_plan"));
    }

    CompositionRuntime::Impl::RecordMap candidates;
    try {
        auto build_status =
            impl->build_candidates(*impl->plan, impl->plan->resolved.provider_construction_order,
                                   impl->generations, candidates);
        if (!build_status) {
            return CompositionRuntimeResult::failure(build_status.error());
        }
        auto commit_status = impl->commit_candidates(
            *impl->plan, candidates, impl->plan->resolved.provider_construction_order);
        if (!commit_status) {
            return CompositionRuntimeResult::failure(commit_status.error());
        }
    } catch (const std::exception &exception) {
        CompositionRuntime::Impl::release_records(
            candidates, impl->plan->resolved.provider_construction_order, true);
        return CompositionRuntimeResult::failure(
            exception_error(kErrorProviderConstructionFailed, "realize", exception));
    } catch (...) {
        CompositionRuntime::Impl::release_records(
            candidates, impl->plan->resolved.provider_construction_order, true);
        return CompositionRuntimeResult::failure(
            unknown_exception_error(kErrorProviderConstructionFailed, "realize"));
    }

    impl->records = std::move(candidates);
    impl->state = CompositionRuntime::Impl::LifecycleState::frozen;
    return CompositionRuntimeResult::success(CompositionRuntime(std::move(impl)));
}

} // namespace runtime::composition
