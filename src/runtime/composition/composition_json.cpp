#include "runtime/composition/composition_json.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <initializer_list>
#include <limits>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace runtime::composition {
namespace {

namespace contracts = composition_contracts;
using Json = nlohmann::json;

class ParseContext {
  public:
    [[nodiscard]] bool failed() const noexcept { return error_.has_value(); }

    [[nodiscard]] CompositionRuntimeError take_error() { return std::move(error_.value()); }

    void fail(std::string_view code, std::string path, std::string detail) {
        if (!error_.has_value()) {
            error_ = CompositionRuntimeError{
                std::string(code),
                std::move(path),
                std::move(detail),
            };
        }
    }

    [[nodiscard]] bool exact_object(const Json &value, std::string_view path,
                                    std::initializer_list<std::string_view> fields) {
        if (!value.is_object()) {
            fail(contracts::kErrorInvalidJsonType, std::string(path), "expected object");
            return false;
        }
        std::set<std::string> expected;
        for (const auto field : fields) {
            expected.emplace(field);
        }
        for (const auto &[field, _] : value.items()) {
            if (!expected.contains(field)) {
                fail(contracts::kErrorUnexpectedField, std::string(path) + "." + field,
                     "field is not allowed");
                return false;
            }
        }
        for (const auto &field : expected) {
            if (!value.contains(field)) {
                fail(contracts::kErrorMissingField, std::string(path) + "." + field,
                     "field is required");
                return false;
            }
        }
        return true;
    }

    [[nodiscard]] std::string string_field(const Json &object, std::string_view field,
                                           std::string_view path) {
        const auto &value = object.at(std::string(field));
        if (!value.is_string()) {
            fail(contracts::kErrorInvalidJsonType, std::string(path) + "." + std::string(field),
                 "expected string");
            return {};
        }
        return value.get<std::string>();
    }

    [[nodiscard]] bool bool_field(const Json &object, std::string_view field,
                                  std::string_view path) {
        const auto &value = object.at(std::string(field));
        if (!value.is_boolean()) {
            fail(contracts::kErrorInvalidJsonType, std::string(path) + "." + std::string(field),
                 "expected boolean");
            return false;
        }
        return value.get<bool>();
    }

    [[nodiscard]] std::vector<std::string> string_array(const Json &value, std::string_view path) {
        std::vector<std::string> result;
        if (!value.is_array()) {
            fail(contracts::kErrorInvalidJsonType, std::string(path), "expected array");
            return result;
        }
        result.reserve(value.size());
        for (std::size_t index = 0; index < value.size(); ++index) {
            if (!value[index].is_string()) {
                fail(contracts::kErrorInvalidJsonType,
                     std::string(path) + "[" + std::to_string(index) + "]", "expected string");
                return {};
            }
            result.push_back(value[index].get<std::string>());
        }
        return result;
    }

    [[nodiscard]] bool validate_canonical_numbers(const Json &value, std::string_view path) {
        if (value.is_number_float()) {
            fail(contracts::kErrorNoncanonicalNumber, std::string(path),
                 "floating-point numbers are forbidden");
            return false;
        }
        if (value.is_number_unsigned() &&
            value.get<std::uint64_t>() >
                static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
            fail(contracts::kErrorNoncanonicalNumber, std::string(path),
                 "integer exceeds signed int64");
            return false;
        }
        if (value.is_array()) {
            for (std::size_t index = 0; index < value.size(); ++index) {
                if (!validate_canonical_numbers(value[index], std::string(path) + "[" +
                                                                  std::to_string(index) + "]")) {
                    return false;
                }
            }
        } else if (value.is_object()) {
            for (const auto &[field, nested] : value.items()) {
                if (!validate_canonical_numbers(nested, std::string(path) + "." + field)) {
                    return false;
                }
            }
        }
        return true;
    }

  private:
    std::optional<CompositionRuntimeError> error_;
};

[[nodiscard]] std::optional<contracts::CompositionScope>
parse_scope(ParseContext &context, const Json &value, std::string_view path) {
    if (!value.is_string()) {
        context.fail(contracts::kErrorInvalidJsonType, std::string(path), "expected scope string");
        return std::nullopt;
    }
    const auto scope = value.get<std::string>();
    if (scope == contracts::kScopeApplication) {
        return contracts::CompositionScope::application;
    }
    if (scope == contracts::kScopeBackend) {
        return contracts::CompositionScope::backend;
    }
    if (scope == contracts::kScopeBatch) {
        return contracts::CompositionScope::batch;
    }
    if (scope == contracts::kScopeWorld) {
        return contracts::CompositionScope::world;
    }
    if (scope == contracts::kScopeEpisode) {
        return contracts::CompositionScope::episode;
    }
    context.fail(contracts::kErrorInvalidScopePolicy, std::string(path), scope);
    return std::nullopt;
}

[[nodiscard]] contracts::CompositionArtifactRef
parse_artifact(ParseContext &context, const Json &value, std::string_view path) {
    contracts::CompositionArtifactRef result;
    if (!context.exact_object(value, path, {"kind", "identity", "sha256"})) {
        return result;
    }
    result.kind = context.string_field(value, "kind", path);
    result.identity = context.string_field(value, "identity", path);
    const auto &digest = value.at("sha256");
    if (digest.is_null()) {
        result.sha256 = std::nullopt;
    } else if (digest.is_string()) {
        result.sha256 = digest.get<std::string>();
    } else {
        context.fail(contracts::kErrorInvalidJsonType, std::string(path) + ".sha256",
                     "expected string or null");
    }
    return result;
}

[[nodiscard]] contracts::CompositionPluginDescriptor
parse_plugin(ParseContext &context, const Json &value, std::string_view path) {
    contracts::CompositionPluginDescriptor result;
    if (!context.exact_object(value, path,
                              {
                                  "plugin_id",
                                  "implementation_id",
                                  "plugin_version",
                                  "composition_contract_range",
                                  "host_support",
                                  "determinism_class",
                                  "artifact",
                                  "required_capabilities",
                                  "conflicts",
                                  "configuration",
                              })) {
        return result;
    }
    result.plugin_id = context.string_field(value, "plugin_id", path);
    result.implementation_id = context.string_field(value, "implementation_id", path);
    result.plugin_version = context.string_field(value, "plugin_version", path);
    result.composition_contract_range =
        context.string_field(value, "composition_contract_range", path);
    result.host_support =
        context.string_array(value.at("host_support"), std::string(path) + ".host_support");
    result.determinism_class = context.string_field(value, "determinism_class", path);
    result.artifact =
        parse_artifact(context, value.at("artifact"), std::string(path) + ".artifact");
    result.required_capabilities = context.string_array(
        value.at("required_capabilities"), std::string(path) + ".required_capabilities");
    result.conflicts =
        context.string_array(value.at("conflicts"), std::string(path) + ".conflicts");
    const auto &configuration = value.at("configuration");
    if (context.validate_canonical_numbers(configuration, std::string(path) + ".configuration")) {
        result.canonical_configuration_json = configuration.dump();
    }
    return result;
}

[[nodiscard]] contracts::CompositionProviderDescriptor
parse_provider(ParseContext &context, const Json &value, std::string_view path) {
    contracts::CompositionProviderDescriptor result;
    if (!context.exact_object(value, path,
                              {
                                  "provider_id",
                                  "plugin_id",
                                  "implementation_version",
                                  "scope",
                                  "cardinality",
                                  "offered_services",
                                  "required_services",
                                  "required_capabilities",
                                  "conflicts",
                                  "after_provider_ids",
                                  "restart_policy",
                                  "teardown_policy",
                                  "configuration",
                              })) {
        return result;
    }
    result.provider_id = context.string_field(value, "provider_id", path);
    result.plugin_id = context.string_field(value, "plugin_id", path);
    result.implementation_version = context.string_field(value, "implementation_version", path);
    const auto scope = parse_scope(context, value.at("scope"), std::string(path) + ".scope");
    if (scope.has_value()) {
        result.scope = *scope;
    }
    result.cardinality = context.string_field(value, "cardinality", path);
    result.offered_services =
        context.string_array(value.at("offered_services"), std::string(path) + ".offered_services");
    result.required_services = context.string_array(value.at("required_services"),
                                                    std::string(path) + ".required_services");
    result.required_capabilities = context.string_array(
        value.at("required_capabilities"), std::string(path) + ".required_capabilities");
    result.conflicts =
        context.string_array(value.at("conflicts"), std::string(path) + ".conflicts");
    result.after_provider_ids = context.string_array(value.at("after_provider_ids"),
                                                     std::string(path) + ".after_provider_ids");
    result.restart_policy = context.string_field(value, "restart_policy", path);
    result.teardown_policy = context.string_field(value, "teardown_policy", path);
    const auto &configuration = value.at("configuration");
    if (context.validate_canonical_numbers(configuration, std::string(path) + ".configuration")) {
        result.canonical_configuration_json = configuration.dump();
    }
    return result;
}

[[nodiscard]] contracts::CompositionSystemContribution
parse_system(ParseContext &context, const Json &value, std::string_view path) {
    contracts::CompositionSystemContribution result;
    if (!context.exact_object(value, path,
                              {
                                  "contribution_id",
                                  "plugin_id",
                                  "registration_factory_id",
                                  "domain",
                                  "required_services",
                                  "required_components",
                                  "provided_components",
                                  "semantic_stage_ids",
                                  "executable_node_ids",
                                  "read_state_shards",
                                  "write_state_shards",
                                  "required_barriers",
                                  "required_capabilities",
                                  "conflicts",
                                  "after",
                                  "before",
                              })) {
        return result;
    }
    result.contribution_id = context.string_field(value, "contribution_id", path);
    result.plugin_id = context.string_field(value, "plugin_id", path);
    result.registration_factory_id = context.string_field(value, "registration_factory_id", path);
    result.domain = context.string_field(value, "domain", path);
    const auto parse_array = [&](std::string_view field) {
        return context.string_array(value.at(std::string(field)),
                                    std::string(path) + "." + std::string(field));
    };
    result.required_services = parse_array("required_services");
    result.required_components = parse_array("required_components");
    result.provided_components = parse_array("provided_components");
    result.semantic_stage_ids = parse_array("semantic_stage_ids");
    result.executable_node_ids = parse_array("executable_node_ids");
    result.read_state_shards = parse_array("read_state_shards");
    result.write_state_shards = parse_array("write_state_shards");
    result.required_barriers = parse_array("required_barriers");
    result.required_capabilities = parse_array("required_capabilities");
    result.conflicts = parse_array("conflicts");
    result.after = parse_array("after");
    result.before = parse_array("before");
    return result;
}

[[nodiscard]] ManifestParseResult parse_manifest_value(ParseContext &context, const Json &root,
                                                       std::string base_path) {
    contracts::SimulationCompositionManifest manifest;
    if (!context.exact_object(root, base_path,
                              {
                                  "schema_version",
                                  "composition_id",
                                  "contract_versions",
                                  "requested_profile",
                                  "plugins",
                                  "providers",
                                  "service_bindings",
                                  "component_contributions",
                                  "system_contributions",
                                  "backend_request",
                                  "scope_policies",
                                  "reconfiguration_policy",
                                  "evidence_policy",
                                  "compatibility_claims",
                              })) {
        return ManifestParseResult::failure(context.take_error());
    }
    manifest.schema_version = context.string_field(root, "schema_version", base_path);
    manifest.composition_id = context.string_field(root, "composition_id", base_path);

    const auto &versions = root.at("contract_versions");
    const std::string versions_path = base_path + ".contract_versions";
    if (context.exact_object(versions, versions_path,
                             {"composition", "runtime", "content", "stage"})) {
        manifest.contract_versions = {
            context.string_field(versions, "composition", versions_path),
            context.string_field(versions, "runtime", versions_path),
            context.string_field(versions, "content", versions_path),
            context.string_field(versions, "stage", versions_path),
        };
    }

    const auto &profile = root.at("requested_profile");
    const std::string profile_path = base_path + ".requested_profile";
    if (context.exact_object(profile, profile_path, {"profile_id", "profile_version"})) {
        manifest.requested_profile = {
            context.string_field(profile, "profile_id", profile_path),
            context.string_field(profile, "profile_version", profile_path),
        };
    }

    const auto parse_object_array = [&](std::string_view field, auto &&parser, auto &target) {
        const auto &values = root.at(std::string(field));
        const std::string field_path = base_path + "." + std::string(field);
        if (!values.is_array()) {
            context.fail(contracts::kErrorInvalidJsonType, field_path, "expected array");
            return;
        }
        target.reserve(values.size());
        for (std::size_t index = 0; index < values.size() && !context.failed(); ++index) {
            target.push_back(
                parser(context, values[index], field_path + "[" + std::to_string(index) + "]"));
        }
    };
    parse_object_array("plugins", parse_plugin, manifest.plugins);
    parse_object_array("providers", parse_provider, manifest.providers);

    const auto &bindings = root.at("service_bindings");
    const std::string bindings_path = base_path + ".service_bindings";
    if (!bindings.is_array()) {
        context.fail(contracts::kErrorInvalidJsonType, bindings_path, "expected array");
    } else {
        for (std::size_t index = 0; index < bindings.size() && !context.failed(); ++index) {
            const auto path = bindings_path + "[" + std::to_string(index) + "]";
            const auto &value = bindings[index];
            if (!context.exact_object(
                    value, path, {"consumer_kind", "consumer_id", "service_key", "provider_id"})) {
                break;
            }
            manifest.service_bindings.push_back({
                context.string_field(value, "consumer_kind", path),
                context.string_field(value, "consumer_id", path),
                context.string_field(value, "service_key", path),
                context.string_field(value, "provider_id", path),
            });
        }
    }

    const auto &components = root.at("component_contributions");
    const std::string components_path = base_path + ".component_contributions";
    if (!components.is_array()) {
        context.fail(contracts::kErrorInvalidJsonType, components_path, "expected array");
    } else {
        for (std::size_t index = 0; index < components.size() && !context.failed(); ++index) {
            const auto path = components_path + "[" + std::to_string(index) + "]";
            const auto &value = components[index];
            if (!context.exact_object(value, path,
                                      {"component_id", "plugin_id", "registration_id"})) {
                break;
            }
            manifest.component_contributions.push_back({
                context.string_field(value, "component_id", path),
                context.string_field(value, "plugin_id", path),
                context.string_field(value, "registration_id", path),
            });
        }
    }
    parse_object_array("system_contributions", parse_system, manifest.system_contributions);

    const auto &backend = root.at("backend_request");
    const std::string backend_path = base_path + ".backend_request";
    if (context.exact_object(backend, backend_path,
                             {"backend_profile_id", "provider_id", "required_capabilities"})) {
        manifest.backend_request = {
            context.string_field(backend, "backend_profile_id", backend_path),
            context.string_field(backend, "provider_id", backend_path),
            context.string_array(backend.at("required_capabilities"),
                                 backend_path + ".required_capabilities"),
        };
    }

    const auto &scopes = root.at("scope_policies");
    const std::string scopes_path = base_path + ".scope_policies";
    if (!scopes.is_array()) {
        context.fail(contracts::kErrorInvalidJsonType, scopes_path, "expected array");
    } else {
        for (std::size_t index = 0; index < scopes.size() && !context.failed(); ++index) {
            const auto path = scopes_path + "[" + std::to_string(index) + "]";
            const auto &value = scopes[index];
            if (!context.exact_object(
                    value, path, {"scope", "parent_scope", "cardinality", "rebuild_trigger"})) {
                break;
            }
            const auto scope = parse_scope(context, value.at("scope"), path + ".scope");
            std::optional<contracts::CompositionScope> parent;
            if (value.at("parent_scope").is_null()) {
                parent = std::nullopt;
            } else {
                parent = parse_scope(context, value.at("parent_scope"), path + ".parent_scope");
            }
            if (scope.has_value()) {
                manifest.scope_policies.push_back({
                    *scope,
                    parent,
                    context.string_field(value, "cardinality", path),
                    context.string_field(value, "rebuild_trigger", path),
                });
            }
        }
    }

    const auto &reconfiguration = root.at("reconfiguration_policy");
    const std::string reconfiguration_path = base_path + ".reconfiguration_policy";
    if (context.exact_object(
            reconfiguration, reconfiguration_path,
            {"truth_affecting_change", "active_episode_change", "allowed_barriers"})) {
        manifest.reconfiguration_policy = {
            context.string_field(reconfiguration, "truth_affecting_change", reconfiguration_path),
            context.string_field(reconfiguration, "active_episode_change", reconfiguration_path),
            context.string_array(reconfiguration.at("allowed_barriers"),
                                 reconfiguration_path + ".allowed_barriers"),
        };
    }

    const auto &evidence = root.at("evidence_policy");
    const std::string evidence_path = base_path + ".evidence_policy";
    if (context.exact_object(evidence, evidence_path,
                             {
                                 "canonicalization",
                                 "hash_algorithm",
                                 "include_provider_versions",
                                 "include_graph_hash",
                                 "include_scope_generations",
                             })) {
        manifest.evidence_policy = {
            context.string_field(evidence, "canonicalization", evidence_path),
            context.string_field(evidence, "hash_algorithm", evidence_path),
            context.bool_field(evidence, "include_provider_versions", evidence_path),
            context.bool_field(evidence, "include_graph_hash", evidence_path),
            context.bool_field(evidence, "include_scope_generations", evidence_path),
        };
    }
    manifest.compatibility_claims =
        context.string_array(root.at("compatibility_claims"), base_path + ".compatibility_claims");

    if (context.failed()) {
        return ManifestParseResult::failure(context.take_error());
    }
    return ManifestParseResult::success(std::move(manifest));
}

[[nodiscard]] CompositionResult<Json> parse_json(std::string_view json_text) {
    try {
        return CompositionResult<Json>::success(Json::parse(json_text.begin(), json_text.end()));
    } catch (const Json::parse_error &error) {
        return CompositionResult<Json>::failure({
            std::string(contracts::kErrorInvalidJsonType),
            "$",
            error.what(),
        });
    }
}

} // namespace

ManifestParseResult parse_simulation_composition_manifest_json(std::string_view json_text) {
    auto parsed = parse_json(json_text);
    if (!parsed) {
        return ManifestParseResult::failure(parsed.error());
    }
    ParseContext context;
    return parse_manifest_value(context, parsed.value(), "$");
}

ResolvedCompositionParseResult parse_resolved_composition_json(std::string_view json_text) {
    auto parsed = parse_json(json_text);
    if (!parsed) {
        return ResolvedCompositionParseResult::failure(parsed.error());
    }
    const auto &root = parsed.value();
    ParseContext context;
    if (!context.exact_object(root, "$",
                              {
                                  "schema_version",
                                  "resolver_contract_version",
                                  "requested_manifest_sha256",
                                  "resolved_manifest_sha256",
                                  "provider_construction_order",
                                  "system_registration_order",
                                  "manifest",
                              })) {
        return ResolvedCompositionParseResult::failure(context.take_error());
    }

    contracts::ResolvedSimulationComposition resolved;
    resolved.schema_version = context.string_field(root, "schema_version", "$");
    resolved.resolver_contract_version =
        context.string_field(root, "resolver_contract_version", "$");
    resolved.requested_manifest_sha256 =
        context.string_field(root, "requested_manifest_sha256", "$");
    resolved.resolved_manifest_sha256 = context.string_field(root, "resolved_manifest_sha256", "$");
    resolved.provider_construction_order = context.string_array(
        root.at("provider_construction_order"), "$.provider_construction_order");
    resolved.system_registration_order =
        context.string_array(root.at("system_registration_order"), "$.system_registration_order");
    auto manifest = parse_manifest_value(context, root.at("manifest"), "$.manifest");
    if (!manifest) {
        return ResolvedCompositionParseResult::failure(manifest.error());
    }
    resolved.manifest = std::move(manifest).value();
    if (context.failed()) {
        return ResolvedCompositionParseResult::failure(context.take_error());
    }
    return ResolvedCompositionParseResult::success(std::move(resolved));
}

} // namespace runtime::composition
