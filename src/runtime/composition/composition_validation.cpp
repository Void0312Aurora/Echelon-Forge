#include "runtime/composition/composition_runtime.h"

#include "runtime/composition/composition_identity.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cctype>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace runtime::composition {
namespace {

namespace contracts = composition_contracts;

struct Utf8Less {
    [[nodiscard]] bool operator()(std::string_view lhs, std::string_view rhs) const noexcept {
        return std::lexicographical_compare(
            lhs.begin(), lhs.end(), rhs.begin(), rhs.end(), [](char left, char right) {
                return static_cast<unsigned char>(left) < static_cast<unsigned char>(right);
            });
    }
};

constexpr std::array<std::string_view, 13> kKnownServiceKeys = {
    contracts::kServiceEnvironmentModel,
    contracts::kServiceUnitFactory,
    contracts::kServiceEffectsModel,
    contracts::kServiceSensorModel,
    contracts::kServiceAcousticModel,
    contracts::kServiceControlModel,
    contracts::kServiceGuidanceModel,
    contracts::kServiceEngagementEventRecorder,
    contracts::kServiceEngagementEventStore,
    contracts::kServiceWeaponReleaseDamageBridge,
    contracts::kServiceWeaponRelease,
    contracts::kServiceWorldBatchBackend,
    contracts::kServiceCompositionEvidenceSink,
};

struct TopologicalOrder {
    std::vector<std::string> order;
    std::vector<std::string> cycle;
};

[[nodiscard]] bool is_identifier(std::string_view value) noexcept {
    if (value.empty() || value.size() > 128 || value.front() < 'a' || value.front() > 'z') {
        return false;
    }
    bool after_separator = false;
    for (std::size_t index = 1; index < value.size(); ++index) {
        const char character = value[index];
        const bool alpha_numeric =
            (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9');
        const bool separator = character == '.' || character == '_' || character == '-';
        if ((!alpha_numeric && !separator) || (separator && after_separator)) {
            return false;
        }
        after_separator = separator;
    }
    return !after_separator;
}

[[nodiscard]] bool is_version(std::string_view value) noexcept {
    std::size_t index = 0;
    for (int field = 0; field < 3; ++field) {
        const std::size_t start = index;
        while (index < value.size() && value[index] >= '0' && value[index] <= '9') {
            ++index;
        }
        if (index == start) {
            return false;
        }
        if (field < 2) {
            if (index >= value.size() || value[index] != '.') {
                return false;
            }
            ++index;
        }
    }
    if (index == value.size()) {
        return true;
    }
    if (value[index] != '-' && value[index] != '+') {
        return false;
    }
    ++index;
    if (index == value.size()) {
        return false;
    }
    for (; index < value.size(); ++index) {
        const unsigned char character = static_cast<unsigned char>(value[index]);
        if (!std::isalnum(character) && value[index] != '.' && value[index] != '-') {
            return false;
        }
    }
    return true;
}

[[nodiscard]] bool is_sha256(std::string_view value) noexcept {
    return value.size() == 64 && std::all_of(value.begin(), value.end(), [](char character) {
               return (character >= '0' && character <= '9') ||
                      (character >= 'a' && character <= 'f');
           });
}

[[nodiscard]] bool is_known_service(std::string_view service_key) noexcept {
    return std::find(kKnownServiceKeys.begin(), kKnownServiceKeys.end(), service_key) !=
           kKnownServiceKeys.end();
}

[[nodiscard]] bool validate_configuration_numbers(contracts::CompositionValidationResult &result,
                                                  const nlohmann::json &value,
                                                  std::string_view path, std::string_view subject) {
    if (value.is_number_float() ||
        (value.is_number_unsigned() &&
         value.get<std::uint64_t>() >
             static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()))) {
        result.add_issue(std::string(contracts::kErrorNoncanonicalNumber), std::string(path),
                         std::string(subject));
        return false;
    }
    if (value.is_array()) {
        for (const auto &nested : value) {
            if (!validate_configuration_numbers(result, nested, path, subject)) {
                return false;
            }
        }
    } else if (value.is_object()) {
        for (const auto &[_, nested] : value.items()) {
            if (!validate_configuration_numbers(result, nested, path, subject)) {
                return false;
            }
        }
    }
    return true;
}

void validate_canonical_configuration(contracts::CompositionValidationResult &result,
                                      std::string_view encoded, std::string_view path,
                                      std::string_view subject) {
    if (encoded.empty()) {
        result.add_issue(std::string(contracts::kErrorInvalidJsonType), std::string(path),
                         std::string(subject) + ": canonical JSON is required");
        return;
    }
    try {
        const auto parsed = nlohmann::json::parse(encoded.begin(), encoded.end());
        if (!validate_configuration_numbers(result, parsed, path, subject)) {
            return;
        }
        if (parsed.dump() != encoded) {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType), std::string(path),
                             std::string(subject) +
                                 ": expected compact JSON with UTF-8 byte-sorted object keys");
        }
    } catch (const nlohmann::json::parse_error &error) {
        result.add_issue(std::string(contracts::kErrorInvalidJsonType), std::string(path),
                         std::string(subject) + ": " + error.what());
    }
}

template <typename Range>
void validate_unique_strings(contracts::CompositionValidationResult &result, const Range &values,
                             std::string_view path) {
    std::set<std::string, Utf8Less> seen;
    for (const auto &value : values) {
        if (value.empty()) {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType), std::string(path),
                             "array entries must not be empty");
        }
        if (!seen.emplace(value).second) {
            result.add_issue(std::string(contracts::kErrorDuplicateValue), std::string(path),
                             value);
        }
    }
}

template <typename Range>
void validate_nonempty_array(contracts::CompositionValidationResult &result, const Range &values,
                             std::string_view path) {
    if (values.empty()) {
        result.add_issue(std::string(contracts::kErrorInvalidJsonType), std::string(path),
                         "array must not be empty");
    }
}

[[nodiscard]] contracts::CompositionPluginDescriptor
canonical_plugin(contracts::CompositionPluginDescriptor value) {
    const auto sort_values = [](auto &values) {
        std::sort(values.begin(), values.end(), Utf8Less{});
    };
    sort_values(value.host_support);
    sort_values(value.required_capabilities);
    sort_values(value.conflicts);
    return value;
}

[[nodiscard]] TopologicalOrder
stable_topological_order(const std::set<std::string, Utf8Less> &nodes,
                         const std::set<std::pair<std::string, std::string>> &edges) {
    std::map<std::string, std::set<std::string, Utf8Less>, Utf8Less> successors;
    std::map<std::string, std::size_t, Utf8Less> indegree;
    for (const auto &node : nodes) {
        successors.emplace(node, std::set<std::string, Utf8Less>{});
        indegree.emplace(node, 0);
    }
    for (const auto &[source, target] : edges) {
        if (!nodes.contains(source) || !nodes.contains(target)) {
            continue;
        }
        if (successors[source].emplace(target).second) {
            ++indegree[target];
        }
    }

    std::set<std::string, Utf8Less> ready;
    for (const auto &[node, degree] : indegree) {
        if (degree == 0) {
            ready.emplace(node);
        }
    }

    TopologicalOrder result;
    while (!ready.empty()) {
        auto iterator = ready.begin();
        std::string node = *iterator;
        ready.erase(iterator);
        result.order.push_back(node);
        for (const auto &successor : successors[node]) {
            auto &degree = indegree[successor];
            --degree;
            if (degree == 0) {
                ready.emplace(successor);
            }
        }
    }
    for (const auto &[node, degree] : indegree) {
        if (degree > 0) {
            result.cycle.push_back(node);
        }
    }
    return result;
}

[[nodiscard]] std::optional<contracts::CompositionScope>
expected_parent(contracts::CompositionScope scope) noexcept {
    switch (scope) {
    case contracts::CompositionScope::application:
        return std::nullopt;
    case contracts::CompositionScope::backend:
        return contracts::CompositionScope::application;
    case contracts::CompositionScope::batch:
        return contracts::CompositionScope::backend;
    case contracts::CompositionScope::world:
        return contracts::CompositionScope::batch;
    case contracts::CompositionScope::episode:
        return contracts::CompositionScope::world;
    }
    return std::nullopt;
}

[[nodiscard]] std::string_view expected_cardinality(contracts::CompositionScope scope) noexcept {
    return scope == contracts::CompositionScope::application ||
                   scope == contracts::CompositionScope::backend
               ? "singleton"
               : "one_per_parent";
}

[[nodiscard]] std::string_view
expected_rebuild_trigger(contracts::CompositionScope scope) noexcept {
    switch (scope) {
    case contracts::CompositionScope::application:
        return "host_reconfiguration_or_shutdown";
    case contracts::CompositionScope::backend:
        return "backend_switch_or_failure";
    case contracts::CompositionScope::batch:
        return "batch_resize_or_reconfiguration";
    case contracts::CompositionScope::world:
        return "world_replacement_or_composition_change";
    case contracts::CompositionScope::episode:
        return "reset_or_episode_completion";
    }
    return {};
}

void sort_and_deduplicate(contracts::CompositionValidationResult &result) {
    auto &issues = result.issues;
    std::sort(issues.begin(), issues.end(), [](const auto &left, const auto &right) {
        return std::tie(left.code, left.path, left.detail) <
               std::tie(right.code, right.path, right.detail);
    });
    issues.erase(std::unique(issues.begin(), issues.end(),
                             [](const auto &left, const auto &right) {
                                 return left.code == right.code && left.path == right.path &&
                                        left.detail == right.detail;
                             }),
                 issues.end());
    result.valid = issues.empty();
}

} // namespace

composition_contracts::CompositionValidationResult
validate_resolved_composition(const composition_contracts::ResolvedSimulationComposition &resolved,
                              const ProviderCatalog &catalog) {
    namespace contracts = composition_contracts;
    contracts::CompositionValidationResult result;
    const auto &manifest = resolved.manifest;

    if (resolved.schema_version != contracts::kResolvedManifestSchemaVersion) {
        result.add_issue(std::string(contracts::kErrorUnsupportedSchemaVersion), "$.schema_version",
                         std::string(contracts::kResolvedManifestSchemaVersion));
    }
    if (resolved.resolver_contract_version != contracts::kResolverContractVersion) {
        result.add_issue(std::string(contracts::kErrorUnsupportedSchemaVersion),
                         "$.resolver_contract_version",
                         std::string(contracts::kResolverContractVersion));
    }
    if (!is_sha256(resolved.requested_manifest_sha256)) {
        result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                         "$.requested_manifest_sha256", "expected lowercase SHA-256");
    }
    if (!is_sha256(resolved.resolved_manifest_sha256)) {
        result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                         "$.resolved_manifest_sha256", "expected lowercase SHA-256");
    }
    if (manifest.schema_version != contracts::kManifestSchemaVersion) {
        result.add_issue(std::string(contracts::kErrorUnsupportedSchemaVersion),
                         "$.manifest.schema_version",
                         std::string(contracts::kManifestSchemaVersion));
    }
    if (manifest.contract_versions.composition != contracts::kCompositionContractVersion) {
        result.add_issue(std::string(contracts::kErrorUnsupportedSchemaVersion),
                         "$.manifest.contract_versions.composition",
                         std::string(contracts::kCompositionContractVersion));
    }
    if (!is_identifier(manifest.composition_id)) {
        result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                         "$.manifest.composition_id", manifest.composition_id);
    }
    for (const auto *version : {
             &manifest.contract_versions.composition,
             &manifest.contract_versions.runtime,
             &manifest.contract_versions.content,
             &manifest.contract_versions.stage,
             &manifest.requested_profile.profile_version,
         }) {
        if (!is_version(*version)) {
            result.add_issue(std::string(contracts::kErrorInvalidVersion),
                             "$.manifest.contract_versions", *version);
        }
    }
    if (!is_identifier(manifest.requested_profile.profile_id)) {
        result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                         "$.manifest.requested_profile.profile_id",
                         manifest.requested_profile.profile_id);
    }
    if (!catalog.frozen()) {
        result.add_issue(std::string(kErrorCatalogNotFrozen), "$.catalog",
                         "provider catalog must be frozen before validation");
    }
    validate_nonempty_array(result, manifest.plugins, "$.manifest.plugins");
    validate_nonempty_array(result, manifest.providers, "$.manifest.providers");

    std::set<std::string, Utf8Less> plugin_ids;
    std::map<std::string, const contracts::CompositionPluginDescriptor *, Utf8Less> plugins;
    for (const auto &plugin : manifest.plugins) {
        if (!is_identifier(plugin.plugin_id) || !is_identifier(plugin.implementation_id)) {
            result.add_issue(std::string(contracts::kErrorInvalidIdentifier), "$.manifest.plugins",
                             plugin.plugin_id);
        }
        if (!is_version(plugin.plugin_version)) {
            result.add_issue(std::string(contracts::kErrorInvalidVersion), "$.manifest.plugins",
                             plugin.plugin_version);
        }
        if (!plugin_ids.emplace(plugin.plugin_id).second) {
            result.add_issue(std::string(contracts::kErrorDuplicateId), "$.manifest.plugins",
                             plugin.plugin_id);
        } else {
            plugins.emplace(plugin.plugin_id, &plugin);
        }
        validate_unique_strings(result, plugin.host_support, "$.manifest.plugins.host_support");
        validate_nonempty_array(result, plugin.host_support, "$.manifest.plugins.host_support");
        for (const auto &host : plugin.host_support) {
            if (host != "native" && host != "cordis") {
                result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                                 "$.manifest.plugins.host_support", host);
            }
        }
        validate_unique_strings(result, plugin.required_capabilities,
                                "$.manifest.plugins.required_capabilities");
        validate_unique_strings(result, plugin.conflicts, "$.manifest.plugins.conflicts");
        if (plugin.composition_contract_range.empty()) {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.plugins.composition_contract_range", plugin.plugin_id);
        }
        if (plugin.determinism_class != "truth_affecting_deterministic" &&
            plugin.determinism_class != "diagnostics_only") {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.plugins.determinism_class", plugin.determinism_class);
        }
        if (plugin.artifact.kind != "repository_builtin" &&
            plugin.artifact.kind != "native_package" && plugin.artifact.kind != "cordis_package") {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.plugins.artifact.kind", plugin.artifact.kind);
        }
        if (plugin.artifact.identity.empty()) {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.plugins.artifact.identity", plugin.plugin_id);
        }
        if (plugin.artifact.sha256.has_value() && !is_sha256(*plugin.artifact.sha256)) {
            result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                             "$.manifest.plugins.artifact.sha256", plugin.plugin_id);
        }
        validate_canonical_configuration(result, plugin.canonical_configuration_json,
                                         "$.manifest.plugins.configuration", plugin.plugin_id);
    }

    std::map<std::string, const contracts::CompositionProviderDescriptor *, Utf8Less> providers;
    std::map<std::string, const std::type_info *, Utf8Less> service_types;
    std::set<std::string, Utf8Less> provider_ids;
    std::set<std::pair<std::string, std::string>> provider_edges;
    for (const auto &provider : manifest.providers) {
        if (!is_identifier(provider.provider_id) || !is_identifier(provider.plugin_id)) {
            result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                             "$.manifest.providers", provider.provider_id);
        }
        if (!is_version(provider.implementation_version)) {
            result.add_issue(std::string(contracts::kErrorInvalidVersion),
                             "$.manifest.providers.implementation_version",
                             provider.implementation_version);
        }
        if (!provider_ids.emplace(provider.provider_id).second) {
            result.add_issue(std::string(contracts::kErrorDuplicateId), "$.manifest.providers",
                             provider.provider_id);
        } else {
            providers.emplace(provider.provider_id, &provider);
        }
        if (!plugin_ids.contains(provider.plugin_id)) {
            result.add_issue(std::string(contracts::kErrorUnknownPlugin),
                             "$.manifest.providers.plugin_id", provider.plugin_id);
        }
        if (!contracts::is_valid_scope(provider.scope)) {
            result.add_issue(std::string(contracts::kErrorInvalidScopePolicy),
                             "$.manifest.providers.scope", provider.provider_id);
        }
        if (provider.cardinality != "one_per_scope") {
            result.add_issue(std::string(contracts::kErrorInvalidScopePolicy),
                             "$.manifest.providers.cardinality", provider.provider_id);
        }
        validate_unique_strings(result, provider.offered_services,
                                "$.manifest.providers.offered_services");
        validate_unique_strings(result, provider.required_services,
                                "$.manifest.providers.required_services");
        validate_unique_strings(result, provider.required_capabilities,
                                "$.manifest.providers.required_capabilities");
        validate_unique_strings(result, provider.after_provider_ids,
                                "$.manifest.providers.after_provider_ids");
        validate_unique_strings(result, provider.conflicts, "$.manifest.providers.conflicts");
        validate_nonempty_array(result, provider.offered_services,
                                "$.manifest.providers.offered_services");
        if (provider.restart_policy != "rebuild_scope_generation" &&
            provider.restart_policy != "process_restart" &&
            provider.restart_policy != "diagnostics_restart") {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.providers.restart_policy", provider.provider_id);
        }
        if (provider.teardown_policy != "reverse_dependency_order") {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.providers.teardown_policy", provider.provider_id);
        }
        for (const auto &service_key : provider.offered_services) {
            if (!is_known_service(service_key)) {
                result.add_issue(std::string(contracts::kErrorUnknownService),
                                 "$.manifest.providers.offered_services", service_key);
            }
        }
        for (const auto &service_key : provider.required_services) {
            if (!is_known_service(service_key)) {
                result.add_issue(std::string(contracts::kErrorUnknownService),
                                 "$.manifest.providers.required_services", service_key);
            }
        }
        const auto factory = catalog.find(provider.provider_id);
        const auto *factory_metadata = catalog.metadata(provider.provider_id);
        if (!factory) {
            result.add_issue(std::string(kErrorFactoryNotFound), "$.catalog", provider.provider_id);
        } else if (factory_metadata == nullptr ||
                   factory_metadata->provider_id != provider.provider_id ||
                   factory_metadata->plugin_id != provider.plugin_id ||
                   factory_metadata->implementation_version != provider.implementation_version ||
                   factory_metadata->scope != provider.scope ||
                   factory_metadata->canonical_configuration_json !=
                       provider.canonical_configuration_json ||
                   !plugins.contains(provider.plugin_id) ||
                   canonical_plugin(factory_metadata->plugin) !=
                       canonical_plugin(*plugins.at(provider.plugin_id))) {
            result.add_issue(std::string(kErrorFactoryMetadataMismatch), "$.catalog",
                             provider.provider_id);
        } else {
            for (const auto &service_key : provider.offered_services) {
                const auto *service_type = catalog.service_type(provider.provider_id, service_key);
                if (service_type == nullptr) {
                    result.add_issue(std::string(kErrorFactoryServiceTypeMissing), "$.catalog",
                                     provider.provider_id + ":" + service_key);
                    continue;
                }
                const auto [iterator, inserted] = service_types.emplace(service_key, service_type);
                if (!inserted && *iterator->second != *service_type) {
                    result.add_issue(std::string(kErrorServiceTypeMismatch), "$.catalog",
                                     service_key);
                }
            }
        }
        validate_canonical_configuration(result, provider.canonical_configuration_json,
                                         "$.manifest.providers.configuration",
                                         provider.provider_id);
    }

    std::set<std::string, Utf8Less> component_ids;
    for (const auto &component : manifest.component_contributions) {
        if (component.component_id.empty() || !is_identifier(component.registration_id)) {
            result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                             "$.manifest.component_contributions", component.component_id);
        }
        if (!plugin_ids.contains(component.plugin_id)) {
            result.add_issue(std::string(contracts::kErrorUnknownPlugin),
                             "$.manifest.component_contributions.plugin_id", component.plugin_id);
        }
        if (!component_ids.emplace(component.component_id).second) {
            result.add_issue(std::string(contracts::kErrorDuplicateId),
                             "$.manifest.component_contributions", component.component_id);
        }
    }

    std::map<std::string, const contracts::CompositionSystemContribution *, Utf8Less> systems;
    std::set<std::string, Utf8Less> system_ids;
    std::set<std::pair<std::string, std::string>> system_edges;
    for (const auto &system : manifest.system_contributions) {
        if (!is_identifier(system.contribution_id) ||
            !is_identifier(system.registration_factory_id)) {
            result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                             "$.manifest.system_contributions", system.contribution_id);
        }
        if (!system_ids.emplace(system.contribution_id).second) {
            result.add_issue(std::string(contracts::kErrorDuplicateId),
                             "$.manifest.system_contributions", system.contribution_id);
        } else {
            systems.emplace(system.contribution_id, &system);
        }
        if (!plugin_ids.contains(system.plugin_id)) {
            result.add_issue(std::string(contracts::kErrorUnknownPlugin),
                             "$.manifest.system_contributions.plugin_id", system.plugin_id);
        }
        validate_unique_strings(result, system.required_services,
                                "$.manifest.system_contributions.required_services");
        validate_unique_strings(result, system.required_components,
                                "$.manifest.system_contributions.required_components");
        validate_unique_strings(result, system.provided_components,
                                "$.manifest.system_contributions.provided_components");
        validate_unique_strings(result, system.semantic_stage_ids,
                                "$.manifest.system_contributions.semantic_stage_ids");
        validate_unique_strings(result, system.executable_node_ids,
                                "$.manifest.system_contributions.executable_node_ids");
        validate_unique_strings(result, system.read_state_shards,
                                "$.manifest.system_contributions.read_state_shards");
        validate_unique_strings(result, system.write_state_shards,
                                "$.manifest.system_contributions.write_state_shards");
        validate_unique_strings(result, system.required_barriers,
                                "$.manifest.system_contributions.required_barriers");
        validate_unique_strings(result, system.required_capabilities,
                                "$.manifest.system_contributions.required_capabilities");
        validate_unique_strings(result, system.after, "$.manifest.system_contributions.after");
        validate_unique_strings(result, system.before, "$.manifest.system_contributions.before");
        validate_unique_strings(result, system.conflicts,
                                "$.manifest.system_contributions.conflicts");
        if (system.domain != "common" && system.domain != "air" && system.domain != "naval" &&
            system.domain != "ground" && system.domain != "cross_domain" &&
            system.domain != "diagnostics") {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.system_contributions.domain", system.domain);
        }
        for (const auto &service_key : system.required_services) {
            if (!is_known_service(service_key)) {
                result.add_issue(std::string(contracts::kErrorUnknownService),
                                 "$.manifest.system_contributions.required_services", service_key);
            }
        }
        for (const auto &component_id : system.required_components) {
            if (!component_ids.contains(component_id)) {
                result.add_issue(std::string(contracts::kErrorUnknownComponent),
                                 "$.manifest.system_contributions.required_components",
                                 component_id);
            }
        }
    }

    using BindingKey = std::tuple<std::string, std::string, std::string>;
    std::map<BindingKey, std::vector<const contracts::CompositionServiceBinding *>> bindings;
    for (const auto &binding : manifest.service_bindings) {
        const auto provider_iterator = providers.find(binding.provider_id);
        if (provider_iterator == providers.end()) {
            result.add_issue(std::string(contracts::kErrorUnknownProvider),
                             "$.manifest.service_bindings.provider_id", binding.provider_id);
        }
        if (!is_known_service(binding.service_key)) {
            result.add_issue(std::string(contracts::kErrorUnknownService),
                             "$.manifest.service_bindings.service_key", binding.service_key);
        }
        if (binding.consumer_kind == "provider") {
            const auto consumer_iterator = providers.find(binding.consumer_id);
            if (consumer_iterator == providers.end()) {
                result.add_issue(std::string(contracts::kErrorUnknownConsumer),
                                 "$.manifest.service_bindings.consumer_id", binding.consumer_id);
            } else if (std::find(consumer_iterator->second->required_services.begin(),
                                 consumer_iterator->second->required_services.end(),
                                 binding.service_key) ==
                       consumer_iterator->second->required_services.end()) {
                result.add_issue(std::string(contracts::kErrorUnknownService),
                                 "$.manifest.service_bindings.service_key",
                                 "provider consumer does not require service");
            }
            if (provider_iterator != providers.end() && consumer_iterator != providers.end()) {
                const auto *supplier = provider_iterator->second;
                const auto *consumer = consumer_iterator->second;
                if (!contracts::can_supply_scope(supplier->scope, consumer->scope)) {
                    result.add_issue(std::string(contracts::kErrorScopeCaptureViolation),
                                     "$.manifest.service_bindings",
                                     binding.provider_id + "->" + binding.consumer_id);
                }
                provider_edges.emplace(binding.provider_id, binding.consumer_id);
            }
        } else if (binding.consumer_kind == "system") {
            const auto consumer_iterator = systems.find(binding.consumer_id);
            if (consumer_iterator == systems.end()) {
                result.add_issue(std::string(contracts::kErrorUnknownConsumer),
                                 "$.manifest.service_bindings.consumer_id", binding.consumer_id);
            } else if (std::find(consumer_iterator->second->required_services.begin(),
                                 consumer_iterator->second->required_services.end(),
                                 binding.service_key) ==
                       consumer_iterator->second->required_services.end()) {
                result.add_issue(std::string(contracts::kErrorUnknownService),
                                 "$.manifest.service_bindings.service_key",
                                 "system consumer does not require service");
            }
        } else {
            result.add_issue(std::string(contracts::kErrorInvalidJsonType),
                             "$.manifest.service_bindings.consumer_kind", binding.consumer_kind);
        }
        if (provider_iterator != providers.end() &&
            std::find(provider_iterator->second->offered_services.begin(),
                      provider_iterator->second->offered_services.end(),
                      binding.service_key) == provider_iterator->second->offered_services.end()) {
            result.add_issue(std::string(contracts::kErrorServiceNotOffered),
                             "$.manifest.service_bindings.provider_id",
                             binding.provider_id + ":" + binding.service_key);
        }
        bindings[{binding.consumer_kind, binding.consumer_id, binding.service_key}].push_back(
            &binding);
    }

    for (const auto &[provider_id, provider] : providers) {
        for (const auto &service_key : provider->required_services) {
            const auto iterator = bindings.find({"provider", provider_id, service_key});
            const std::size_t count = iterator == bindings.end() ? 0 : iterator->second.size();
            if (count == 0) {
                result.add_issue(std::string(contracts::kErrorMissingServiceBinding),
                                 "$.manifest.providers.required_services",
                                 provider_id + ":" + service_key);
            } else if (count > 1) {
                result.add_issue(std::string(contracts::kErrorAmbiguousServiceBinding),
                                 "$.manifest.providers.required_services",
                                 provider_id + ":" + service_key);
            }
        }
        for (const auto &dependency : provider->after_provider_ids) {
            if (!providers.contains(dependency)) {
                result.add_issue(std::string(contracts::kErrorUnknownProvider),
                                 "$.manifest.providers.after_provider_ids", dependency);
            } else {
                provider_edges.emplace(dependency, provider_id);
            }
        }
        for (const auto &conflict : provider->conflicts) {
            if (providers.contains(conflict)) {
                result.add_issue(std::string(contracts::kErrorProviderConflict),
                                 "$.manifest.providers.conflicts", provider_id + ":" + conflict);
            }
        }
    }
    for (const auto &[system_id, system] : systems) {
        for (const auto &service_key : system->required_services) {
            const auto iterator = bindings.find({"system", system_id, service_key});
            const std::size_t count = iterator == bindings.end() ? 0 : iterator->second.size();
            if (count == 0) {
                result.add_issue(std::string(contracts::kErrorMissingServiceBinding),
                                 "$.manifest.system_contributions.required_services",
                                 system_id + ":" + service_key);
            } else if (count > 1) {
                result.add_issue(std::string(contracts::kErrorAmbiguousServiceBinding),
                                 "$.manifest.system_contributions.required_services",
                                 system_id + ":" + service_key);
            }
        }
        for (const auto &dependency : system->after) {
            if (!systems.contains(dependency)) {
                result.add_issue(std::string(contracts::kErrorUnknownSystemDependency),
                                 "$.manifest.system_contributions.after", dependency);
            } else {
                system_edges.emplace(dependency, system_id);
            }
        }
        for (const auto &successor : system->before) {
            if (!systems.contains(successor)) {
                result.add_issue(std::string(contracts::kErrorUnknownSystemDependency),
                                 "$.manifest.system_contributions.before", successor);
            } else {
                system_edges.emplace(system_id, successor);
            }
        }
        for (const auto &conflict : system->conflicts) {
            if (systems.contains(conflict)) {
                result.add_issue(std::string(contracts::kErrorSystemConflict),
                                 "$.manifest.system_contributions.conflicts",
                                 system_id + ":" + conflict);
            }
        }
    }

    const auto provider_order = stable_topological_order(provider_ids, provider_edges);
    if (!provider_order.cycle.empty()) {
        result.add_issue(std::string(contracts::kErrorProviderDependencyCycle),
                         "$.manifest.providers", provider_order.cycle.front());
    } else if (provider_order.order != resolved.provider_construction_order) {
        result.add_issue(std::string(kErrorResolvedOrderMismatch), "$.provider_construction_order",
                         "resolved provider order is not the stable native order");
    }

    const auto system_order = stable_topological_order(system_ids, system_edges);
    if (!system_order.cycle.empty()) {
        result.add_issue(std::string(contracts::kErrorSystemDependencyCycle),
                         "$.manifest.system_contributions", system_order.cycle.front());
    } else if (system_order.order != resolved.system_registration_order) {
        result.add_issue(std::string(kErrorResolvedOrderMismatch), "$.system_registration_order",
                         "resolved system order is not the stable native order");
    }

    const auto backend = providers.find(manifest.backend_request.provider_id);
    if (!is_identifier(manifest.backend_request.backend_profile_id)) {
        result.add_issue(std::string(contracts::kErrorInvalidIdentifier),
                         "$.manifest.backend_request.backend_profile_id",
                         manifest.backend_request.backend_profile_id);
    }
    validate_unique_strings(result, manifest.backend_request.required_capabilities,
                            "$.manifest.backend_request.required_capabilities");
    if (backend == providers.end() ||
        std::find(backend->second->offered_services.begin(),
                  backend->second->offered_services.end(), contracts::kServiceWorldBatchBackend) ==
            backend->second->offered_services.end()) {
        result.add_issue(std::string(contracts::kErrorBackendProviderMismatch),
                         "$.manifest.backend_request.provider_id",
                         manifest.backend_request.provider_id);
    }

    std::set<contracts::CompositionScope> scope_rows;
    for (const auto &policy : manifest.scope_policies) {
        const bool valid_scope = contracts::is_valid_scope(policy.scope);
        const bool valid_parent =
            !policy.parent_scope.has_value() || contracts::is_valid_scope(*policy.parent_scope);
        if (!valid_scope || !valid_parent || !scope_rows.emplace(policy.scope).second ||
            policy.parent_scope != expected_parent(policy.scope) ||
            policy.cardinality != expected_cardinality(policy.scope) ||
            policy.rebuild_trigger != expected_rebuild_trigger(policy.scope)) {
            result.add_issue(std::string(contracts::kErrorInvalidScopePolicy),
                             "$.manifest.scope_policies",
                             std::string(contracts::to_string(policy.scope)));
        }
    }
    if (scope_rows.size() != 5) {
        result.add_issue(std::string(contracts::kErrorInvalidScopePolicy),
                         "$.manifest.scope_policies", "exact five-scope hierarchy is required");
    }

    const auto &reconfiguration = manifest.reconfiguration_policy;
    if (reconfiguration.truth_affecting_change != "rebuild_scope_generation" ||
        reconfiguration.active_episode_change != "forbidden") {
        result.add_issue(std::string(contracts::kErrorInvalidReconfigurationPolicy),
                         "$.manifest.reconfiguration_policy",
                         "truth-affecting active mutation is forbidden");
    }
    validate_unique_strings(result, reconfiguration.allowed_barriers,
                            "$.manifest.reconfiguration_policy.allowed_barriers");
    validate_nonempty_array(result, reconfiguration.allowed_barriers,
                            "$.manifest.reconfiguration_policy.allowed_barriers");

    const auto &evidence = manifest.evidence_policy;
    if (evidence.canonicalization != contracts::kCanonicalizationId ||
        evidence.hash_algorithm != contracts::kCanonicalHashAlgorithm ||
        !evidence.include_provider_versions || !evidence.include_graph_hash ||
        !evidence.include_scope_generations) {
        result.add_issue(std::string(contracts::kErrorInvalidEvidencePolicy),
                         "$.manifest.evidence_policy", "v1 evidence identity fields are mandatory");
    }
    validate_unique_strings(result, manifest.compatibility_claims,
                            "$.manifest.compatibility_claims");

    if (is_sha256(resolved.requested_manifest_sha256) &&
        is_sha256(resolved.resolved_manifest_sha256)) {
        const auto identity = compute_composition_identity(resolved);
        if (!identity) {
            result.add_issue(identity.error().code, identity.error().subject,
                             identity.error().detail);
        } else {
            if (identity.value().requested_manifest_sha256 != resolved.requested_manifest_sha256) {
                result.add_issue(std::string(kErrorManifestHashMismatch),
                                 "$.requested_manifest_sha256",
                                 identity.value().requested_manifest_sha256);
            }
            if (identity.value().resolved_manifest_sha256 != resolved.resolved_manifest_sha256) {
                result.add_issue(std::string(kErrorManifestHashMismatch),
                                 "$.resolved_manifest_sha256",
                                 identity.value().resolved_manifest_sha256);
            }
        }
    }

    sort_and_deduplicate(result);
    return result;
}

} // namespace runtime::composition
