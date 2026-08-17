#include "runtime/composition/composition_identity.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace runtime::composition {
namespace {

namespace contracts = composition_contracts;
using Json = nlohmann::json;

struct Utf8Less {
    [[nodiscard]] bool operator()(std::string_view lhs, std::string_view rhs) const noexcept {
        return std::lexicographical_compare(
            lhs.begin(), lhs.end(), rhs.begin(), rhs.end(), [](char left, char right) {
                return static_cast<unsigned char>(left) < static_cast<unsigned char>(right);
            });
    }
};

template <typename Range> [[nodiscard]] Json sorted_strings(const Range &values) {
    std::vector<std::string> sorted(values.begin(), values.end());
    std::sort(sorted.begin(), sorted.end(), Utf8Less{});
    return sorted;
}

[[nodiscard]] CompositionResult<Json> parse_configuration(std::string_view encoded,
                                                          std::string subject) {
    try {
        return CompositionResult<Json>::success(Json::parse(encoded.begin(), encoded.end()));
    } catch (const Json::parse_error &error) {
        return CompositionResult<Json>::failure({
            std::string(contracts::kErrorInvalidJsonType),
            std::move(subject),
            error.what(),
        });
    }
}

[[nodiscard]] CompositionResult<Json>
manifest_json(const contracts::SimulationCompositionManifest &manifest) {
    Json plugins = Json::array();
    std::vector<const contracts::CompositionPluginDescriptor *> plugin_rows;
    plugin_rows.reserve(manifest.plugins.size());
    for (const auto &plugin : manifest.plugins) {
        plugin_rows.push_back(&plugin);
    }
    std::sort(plugin_rows.begin(), plugin_rows.end(), [](const auto *left, const auto *right) {
        return Utf8Less{}(left->plugin_id, right->plugin_id);
    });
    for (const auto *plugin : plugin_rows) {
        auto configuration =
            parse_configuration(plugin->canonical_configuration_json, plugin->plugin_id);
        if (!configuration) {
            return CompositionResult<Json>::failure(configuration.error());
        }
        Json artifact = {
            {"identity", plugin->artifact.identity},
            {"kind", plugin->artifact.kind},
            {"sha256", plugin->artifact.sha256.has_value() ? Json(*plugin->artifact.sha256)
                                                            : Json(nullptr)},
        };
        plugins.push_back({
            {"artifact", std::move(artifact)},
            {"composition_contract_range", plugin->composition_contract_range},
            {"configuration", std::move(configuration).value()},
            {"conflicts", sorted_strings(plugin->conflicts)},
            {"determinism_class", plugin->determinism_class},
            {"host_support", sorted_strings(plugin->host_support)},
            {"implementation_id", plugin->implementation_id},
            {"plugin_id", plugin->plugin_id},
            {"plugin_version", plugin->plugin_version},
            {"required_capabilities", sorted_strings(plugin->required_capabilities)},
        });
    }

    Json providers = Json::array();
    std::vector<const contracts::CompositionProviderDescriptor *> provider_rows;
    provider_rows.reserve(manifest.providers.size());
    for (const auto &provider : manifest.providers) {
        provider_rows.push_back(&provider);
    }
    std::sort(provider_rows.begin(), provider_rows.end(), [](const auto *left, const auto *right) {
        return Utf8Less{}(left->provider_id, right->provider_id);
    });
    for (const auto *provider : provider_rows) {
        if (!contracts::is_valid_scope(provider->scope)) {
            return CompositionResult<Json>::failure({
                std::string(contracts::kErrorInvalidScopePolicy),
                provider->provider_id,
                "provider scope is outside the v1 scope domain",
            });
        }
        auto configuration =
            parse_configuration(provider->canonical_configuration_json, provider->provider_id);
        if (!configuration) {
            return CompositionResult<Json>::failure(configuration.error());
        }
        providers.push_back({
            {"after_provider_ids", sorted_strings(provider->after_provider_ids)},
            {"cardinality", provider->cardinality},
            {"configuration", std::move(configuration).value()},
            {"conflicts", sorted_strings(provider->conflicts)},
            {"implementation_version", provider->implementation_version},
            {"offered_services", sorted_strings(provider->offered_services)},
            {"plugin_id", provider->plugin_id},
            {"provider_id", provider->provider_id},
            {"required_capabilities", sorted_strings(provider->required_capabilities)},
            {"required_services", sorted_strings(provider->required_services)},
            {"restart_policy", provider->restart_policy},
            {"scope", contracts::to_string(provider->scope)},
            {"teardown_policy", provider->teardown_policy},
        });
    }

    Json bindings = Json::array();
    std::vector<const contracts::CompositionServiceBinding *> binding_rows;
    binding_rows.reserve(manifest.service_bindings.size());
    for (const auto &binding : manifest.service_bindings) {
        binding_rows.push_back(&binding);
    }
    std::sort(binding_rows.begin(), binding_rows.end(), [](const auto *left, const auto *right) {
        return std::tie(left->consumer_kind, left->consumer_id, left->service_key,
                        left->provider_id) <
               std::tie(right->consumer_kind, right->consumer_id, right->service_key,
                        right->provider_id);
    });
    for (const auto *binding : binding_rows) {
        bindings.push_back({
            {"consumer_id", binding->consumer_id},
            {"consumer_kind", binding->consumer_kind},
            {"provider_id", binding->provider_id},
            {"service_key", binding->service_key},
        });
    }

    Json components = Json::array();
    std::vector<const contracts::CompositionComponentContribution *> component_rows;
    component_rows.reserve(manifest.component_contributions.size());
    for (const auto &component : manifest.component_contributions) {
        component_rows.push_back(&component);
    }
    std::sort(component_rows.begin(), component_rows.end(), [](const auto *left, const auto *right) {
        return Utf8Less{}(left->component_id, right->component_id);
    });
    for (const auto *component : component_rows) {
        components.push_back({
            {"component_id", component->component_id},
            {"plugin_id", component->plugin_id},
            {"registration_id", component->registration_id},
        });
    }

    Json systems = Json::array();
    std::vector<const contracts::CompositionSystemContribution *> system_rows;
    system_rows.reserve(manifest.system_contributions.size());
    for (const auto &system : manifest.system_contributions) {
        system_rows.push_back(&system);
    }
    std::sort(system_rows.begin(), system_rows.end(), [](const auto *left, const auto *right) {
        return Utf8Less{}(left->contribution_id, right->contribution_id);
    });
    for (const auto *system : system_rows) {
        systems.push_back({
            {"after", sorted_strings(system->after)},
            {"before", sorted_strings(system->before)},
            {"conflicts", sorted_strings(system->conflicts)},
            {"contribution_id", system->contribution_id},
            {"domain", system->domain},
            {"executable_node_ids", sorted_strings(system->executable_node_ids)},
            {"plugin_id", system->plugin_id},
            {"provided_components", sorted_strings(system->provided_components)},
            {"read_state_shards", sorted_strings(system->read_state_shards)},
            {"registration_factory_id", system->registration_factory_id},
            {"required_barriers", sorted_strings(system->required_barriers)},
            {"required_capabilities", sorted_strings(system->required_capabilities)},
            {"required_components", sorted_strings(system->required_components)},
            {"required_services", sorted_strings(system->required_services)},
            {"semantic_stage_ids", sorted_strings(system->semantic_stage_ids)},
            {"write_state_shards", sorted_strings(system->write_state_shards)},
        });
    }

    Json scopes = Json::array();
    std::vector<const contracts::CompositionScopePolicy *> scope_rows;
    scope_rows.reserve(manifest.scope_policies.size());
    for (const auto &scope : manifest.scope_policies) {
        scope_rows.push_back(&scope);
    }
    std::sort(scope_rows.begin(), scope_rows.end(), [](const auto *left, const auto *right) {
        return static_cast<std::uint8_t>(left->scope) <
               static_cast<std::uint8_t>(right->scope);
    });
    for (const auto *scope : scope_rows) {
        if (!contracts::is_valid_scope(scope->scope) ||
            (scope->parent_scope.has_value() &&
             !contracts::is_valid_scope(*scope->parent_scope))) {
            return CompositionResult<Json>::failure({
                std::string(contracts::kErrorInvalidScopePolicy),
                "$.manifest.scope_policies",
                "scope policy contains an invalid typed scope",
            });
        }
        scopes.push_back({
            {"cardinality", scope->cardinality},
            {"parent_scope", scope->parent_scope.has_value()
                                 ? Json(contracts::to_string(*scope->parent_scope))
                                 : Json(nullptr)},
            {"rebuild_trigger", scope->rebuild_trigger},
            {"scope", contracts::to_string(scope->scope)},
        });
    }

    Json result = {
        {"backend_request",
         {
             {"backend_profile_id", manifest.backend_request.backend_profile_id},
             {"provider_id", manifest.backend_request.provider_id},
             {"required_capabilities",
              sorted_strings(manifest.backend_request.required_capabilities)},
         }},
        {"compatibility_claims", sorted_strings(manifest.compatibility_claims)},
        {"component_contributions", std::move(components)},
        {"composition_id", manifest.composition_id},
        {"contract_versions",
         {
             {"composition", manifest.contract_versions.composition},
             {"content", manifest.contract_versions.content},
             {"runtime", manifest.contract_versions.runtime},
             {"stage", manifest.contract_versions.stage},
         }},
        {"evidence_policy",
         {
             {"canonicalization", manifest.evidence_policy.canonicalization},
             {"hash_algorithm", manifest.evidence_policy.hash_algorithm},
             {"include_graph_hash", manifest.evidence_policy.include_graph_hash},
             {"include_provider_versions", manifest.evidence_policy.include_provider_versions},
             {"include_scope_generations", manifest.evidence_policy.include_scope_generations},
         }},
        {"plugins", std::move(plugins)},
        {"providers", std::move(providers)},
        {"reconfiguration_policy",
         {
             {"active_episode_change",
              manifest.reconfiguration_policy.active_episode_change},
             {"allowed_barriers",
              sorted_strings(manifest.reconfiguration_policy.allowed_barriers)},
             {"truth_affecting_change",
              manifest.reconfiguration_policy.truth_affecting_change},
         }},
        {"requested_profile",
         {
             {"profile_id", manifest.requested_profile.profile_id},
             {"profile_version", manifest.requested_profile.profile_version},
         }},
        {"schema_version", manifest.schema_version},
        {"scope_policies", std::move(scopes)},
        {"service_bindings", std::move(bindings)},
        {"system_contributions", std::move(systems)},
    };
    return CompositionResult<Json>::success(std::move(result));
}

[[nodiscard]] constexpr std::uint32_t choose(std::uint32_t x, std::uint32_t y,
                                             std::uint32_t z) noexcept {
    return (x & y) ^ (~x & z);
}

[[nodiscard]] constexpr std::uint32_t majority(std::uint32_t x, std::uint32_t y,
                                               std::uint32_t z) noexcept {
    return (x & y) ^ (x & z) ^ (y & z);
}

[[nodiscard]] std::string sha256_hex(std::string_view input) {
    constexpr std::array<std::uint32_t, 64> constants = {
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U,
        0x923f82a4U, 0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U,
        0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U,
        0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
        0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU,
        0x5b9cca4fU, 0x682e6ff3U, 0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
    };
    std::array<std::uint32_t, 8> state = {
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
    };

    std::vector<std::uint8_t> bytes(input.begin(), input.end());
    const std::uint64_t bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
    bytes.push_back(0x80U);
    while ((bytes.size() % 64U) != 56U) {
        bytes.push_back(0U);
    }
    for (int shift = 56; shift >= 0; shift -= 8) {
        bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
    }

    for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
        std::array<std::uint32_t, 64> words{};
        for (std::size_t index = 0; index < 16U; ++index) {
            const std::size_t base = offset + index * 4U;
            words[index] = (static_cast<std::uint32_t>(bytes[base]) << 24U) |
                           (static_cast<std::uint32_t>(bytes[base + 1U]) << 16U) |
                           (static_cast<std::uint32_t>(bytes[base + 2U]) << 8U) |
                           static_cast<std::uint32_t>(bytes[base + 3U]);
        }
        for (std::size_t index = 16U; index < words.size(); ++index) {
            const std::uint32_t sigma0 = std::rotr(words[index - 15U], 7) ^
                                         std::rotr(words[index - 15U], 18) ^
                                         (words[index - 15U] >> 3U);
            const std::uint32_t sigma1 = std::rotr(words[index - 2U], 17) ^
                                         std::rotr(words[index - 2U], 19) ^
                                         (words[index - 2U] >> 10U);
            words[index] = words[index - 16U] + sigma0 + words[index - 7U] + sigma1;
        }

        std::uint32_t a = state[0];
        std::uint32_t b = state[1];
        std::uint32_t c = state[2];
        std::uint32_t d = state[3];
        std::uint32_t e = state[4];
        std::uint32_t f = state[5];
        std::uint32_t g = state[6];
        std::uint32_t h = state[7];
        for (std::size_t index = 0; index < words.size(); ++index) {
            const std::uint32_t sum1 = std::rotr(e, 6) ^ std::rotr(e, 11) ^ std::rotr(e, 25);
            const std::uint32_t temp1 =
                h + sum1 + choose(e, f, g) + constants[index] + words[index];
            const std::uint32_t sum0 = std::rotr(a, 2) ^ std::rotr(a, 13) ^ std::rotr(a, 22);
            const std::uint32_t temp2 = sum0 + majority(a, b, c);
            h = g;
            g = f;
            f = e;
            e = d + temp1;
            d = c;
            c = b;
            b = a;
            a = temp1 + temp2;
        }
        state[0] += a;
        state[1] += b;
        state[2] += c;
        state[3] += d;
        state[4] += e;
        state[5] += f;
        state[6] += g;
        state[7] += h;
    }

    std::ostringstream stream;
    stream << std::hex << std::setfill('0');
    for (const auto word : state) {
        stream << std::setw(8) << word;
    }
    return stream.str();
}

} // namespace

CompositionIdentityResult compute_composition_identity(
    const composition_contracts::ResolvedSimulationComposition &resolved) {
    auto manifest = manifest_json(resolved.manifest);
    if (!manifest) {
        return CompositionIdentityResult::failure(manifest.error());
    }
    const std::string requested_hash = sha256_hex(manifest.value().dump());
    Json resolved_payload = {
        {"manifest", manifest.value()},
        {"provider_construction_order", resolved.provider_construction_order},
        {"requested_manifest_sha256", requested_hash},
        {"resolver_contract_version", resolved.resolver_contract_version},
        {"schema_version", resolved.schema_version},
        {"system_registration_order", resolved.system_registration_order},
    };
    return CompositionIdentityResult::success(
        {requested_hash, sha256_hex(resolved_payload.dump())});
}

} // namespace runtime::composition
