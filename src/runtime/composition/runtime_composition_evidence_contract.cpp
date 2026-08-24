#include "runtime/contracts/runtime_composition_evidence_contract.h"

#include "runtime/contracts/runtime_composition_projection_contract.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cctype>
#include <limits>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>

namespace runtime::composition_evidence_contracts {
namespace {

using Json = nlohmann::json;

constexpr std::array<std::string_view, 5> kScopeNames = {"application", "backend", "batch", "world",
                                                         "episode"};

void add_issue(EvidenceValidationResult &result, std::string code, std::string path,
               std::string detail) {
    result.issues.push_back({std::move(code), std::move(path), std::move(detail)});
}

bool is_sha256(std::string_view value) noexcept {
    return value.size() == 64 && std::all_of(value.begin(), value.end(), [](unsigned char ch) {
               return std::isdigit(ch) != 0 || (ch >= 'a' && ch <= 'f');
           });
}

bool is_ascii(std::string_view value) noexcept {
    return std::all_of(value.begin(), value.end(), [](unsigned char ch) { return ch <= 0x7fU; });
}

bool valid_scope(std::string_view scope) noexcept {
    return std::find(kScopeNames.begin(), kScopeNames.end(), scope) != kScopeNames.end();
}

RuntimeCompositionEvidence normalized(RuntimeCompositionEvidence evidence) {
    std::sort(evidence.provider_versions.begin(), evidence.provider_versions.end(),
              [](const auto &left, const auto &right) {
                  return std::tie(left.provider_id, left.implementation_version) <
                         std::tie(right.provider_id, right.implementation_version);
              });
    std::sort(evidence.backend.admitted_capabilities.begin(),
              evidence.backend.admitted_capabilities.end());
    for (auto &world : evidence.world_instances) {
        std::sort(world.scope_generations.begin(), world.scope_generations.end(),
                  [](const auto &left, const auto &right) {
                      return std::tie(left.scope, left.instance_id, left.generation) <
                             std::tie(right.scope, right.instance_id, right.generation);
                  });
    }
    std::sort(
        evidence.world_instances.begin(), evidence.world_instances.end(),
        [](const auto &left, const auto &right) { return left.world_index < right.world_index; });
    return evidence;
}

Json payload_json(const RuntimeCompositionEvidence &evidence) {
    Json provider_versions = Json::array();
    for (const auto &provider : evidence.provider_versions) {
        provider_versions.push_back({
            {"implementation_version", provider.implementation_version},
            {"provider_id", provider.provider_id},
        });
    }

    Json world_instances = Json::array();
    for (const auto &world : evidence.world_instances) {
        Json scope_generations = Json::array();
        for (const auto &scope : world.scope_generations) {
            scope_generations.push_back({
                {"generation", scope.generation},
                {"instance_id", scope.instance_id},
                {"scope", scope.scope},
            });
        }
        world_instances.push_back({
            {"scope_generations", std::move(scope_generations)},
            {"world_index", world.world_index},
        });
    }

    return {
        {"backend",
         {
             {"admitted_capabilities", evidence.backend.admitted_capabilities},
             {"backend_profile_id", evidence.backend.backend_profile_id},
             {"implementation_version", evidence.backend.implementation_version},
             {"provider_id", evidence.backend.provider_id},
         }},
        {"binding_version", evidence.binding_version},
        {"canonicalization", evidence.canonicalization},
        {"catalog_lock_sha256", evidence.catalog_lock_sha256},
        {"composition_id", evidence.composition_id},
        {"evidence_contract_version", evidence.evidence_contract_version},
        {"executable_graph_sha256", evidence.executable_graph_sha256},
        {"hash_algorithm", evidence.hash_algorithm},
        {"host_mode", evidence.host_mode},
        {"profile_projection_sha256", evidence.profile_projection_sha256},
        {"provider_versions", std::move(provider_versions)},
        {"requested_manifest_sha256", evidence.requested_manifest_sha256},
        {"requested_profile_id", evidence.requested_profile_id},
        {"requested_profile_version", evidence.requested_profile_version},
        {"resolved_manifest_sha256", evidence.resolved_manifest_sha256},
        {"resolver_contract_version", evidence.resolver_contract_version},
        {"runtime_request_sha256", evidence.runtime_request_sha256},
        {"schema_version", evidence.schema_version},
        {"stage_contract_version", evidence.stage_contract_version},
        {"world_instances", std::move(world_instances)},
    };
}

void compare_field(EvidenceComparisonResult &result, bool equal, std::string_view path) {
    if (!equal) {
        result.mismatches.emplace_back(path);
    }
}

} // namespace

RuntimeCompositionEvidence seal_runtime_composition_evidence(RuntimeCompositionEvidence evidence) {
    evidence.schema_version = std::string(kSchemaVersion);
    evidence.evidence_contract_version = std::string(kContractVersion);
    evidence.canonicalization = std::string(kCanonicalization);
    evidence.hash_algorithm = std::string(kHashAlgorithm);
    evidence.canonical_json.clear();
    evidence.evidence_sha256.clear();
    evidence = normalized(std::move(evidence));
    evidence.canonical_json = payload_json(evidence).dump();
    evidence.evidence_sha256 =
        runtime::projection_contracts::canonical_sha256_hex(evidence.canonical_json);
    return evidence;
}

EvidenceValidationResult
validate_runtime_composition_evidence(const RuntimeCompositionEvidence &evidence) {
    EvidenceValidationResult result;
    bool payload_strings_ascii = true;
    for (const auto &[path, value] : std::array<std::pair<std::string_view, std::string_view>, 5>{
             {{"$.schema_version", evidence.schema_version},
              {"$.evidence_contract_version", evidence.evidence_contract_version},
              {"$.canonicalization", evidence.canonicalization},
              {"$.hash_algorithm", evidence.hash_algorithm},
              {"$.evidence_sha256", evidence.evidence_sha256}}}) {
        if (!is_ascii(value)) {
            add_issue(result, "evidence.non_ascii_string", std::string(path),
                      "v1 evidence strings must be ASCII");
            payload_strings_ascii = false;
        }
    }
    if (evidence.schema_version != kSchemaVersion) {
        add_issue(result, "evidence.unsupported_schema", "$.schema_version",
                  "runtime composition evidence schema is not admitted");
    }
    if (evidence.evidence_contract_version != kContractVersion) {
        add_issue(result, "evidence.unsupported_contract", "$.evidence_contract_version",
                  "runtime composition evidence contract is not admitted");
    }
    if (evidence.canonicalization != kCanonicalization ||
        evidence.hash_algorithm != kHashAlgorithm) {
        add_issue(result, "evidence.invalid_identity_policy", "$.canonicalization",
                  "canonicalization and hash algorithm must match the maintained contract");
    }

    for (const auto &[path, value] : std::array<std::pair<std::string_view, std::string_view>, 6>{
             {{"$.runtime_request_sha256", evidence.runtime_request_sha256},
              {"$.requested_manifest_sha256", evidence.requested_manifest_sha256},
              {"$.resolved_manifest_sha256", evidence.resolved_manifest_sha256},
              {"$.catalog_lock_sha256", evidence.catalog_lock_sha256},
              {"$.profile_projection_sha256", evidence.profile_projection_sha256},
              {"$.executable_graph_sha256", evidence.executable_graph_sha256}}}) {
        if (!is_ascii(value)) {
            add_issue(result, "evidence.non_ascii_string", std::string(path),
                      "v1 evidence strings must be ASCII");
            payload_strings_ascii = false;
        }
        if (!is_sha256(value)) {
            add_issue(result, "evidence.invalid_sha256", std::string(path),
                      "expected lowercase SHA-256");
        }
    }
    if (evidence.composition_id.empty() || evidence.requested_profile_id.empty() ||
        evidence.requested_profile_version.empty() || evidence.resolver_contract_version.empty() ||
        evidence.stage_contract_version.empty() || evidence.host_mode.empty() ||
        evidence.binding_version.empty()) {
        add_issue(result, "evidence.missing_identity", "$",
                  "resolver, stage, host, and binding identities are required");
    }
    for (const auto &[path, value] : std::array<std::pair<std::string_view, std::string_view>, 8>{{
             {"$.composition_id", evidence.composition_id},
             {"$.requested_profile_id", evidence.requested_profile_id},
             {"$.requested_profile_version", evidence.requested_profile_version},
             {"$.resolver_contract_version", evidence.resolver_contract_version},
             {"$.stage_contract_version", evidence.stage_contract_version},
             {"$.host_mode", evidence.host_mode},
             {"$.binding_version", evidence.binding_version},
             {"$.canonical_json", evidence.canonical_json},
         }}) {
        if (!is_ascii(value)) {
            add_issue(result, "evidence.non_ascii_string", std::string(path),
                      "v1 evidence strings must be ASCII");
            payload_strings_ascii = false;
        }
    }

    std::set<std::string> provider_ids;
    for (std::size_t index = 0; index < evidence.provider_versions.size(); ++index) {
        const auto &provider = evidence.provider_versions[index];
        if (provider.provider_id.empty() || provider.implementation_version.empty()) {
            add_issue(result, "evidence.invalid_provider", "$.provider_versions",
                      "provider identity and implementation version are required");
        }
        if (!is_ascii(provider.provider_id) || !is_ascii(provider.implementation_version)) {
            add_issue(result, "evidence.non_ascii_string", "$.provider_versions",
                      "v1 provider identities must be ASCII");
            payload_strings_ascii = false;
        }
        if (!provider_ids.insert(provider.provider_id).second) {
            add_issue(result, "evidence.duplicate_provider", "$.provider_versions",
                      provider.provider_id);
        }
    }
    if (provider_ids.empty()) {
        add_issue(result, "evidence.missing_provider", "$.provider_versions",
                  "at least one realized provider version is required");
    }
    const auto backend_provider = std::find_if(
        evidence.provider_versions.begin(), evidence.provider_versions.end(),
        [&](const auto &provider) { return provider.provider_id == evidence.backend.provider_id; });
    const bool backend_complete =
        !evidence.backend.provider_id.empty() && !evidence.backend.implementation_version.empty() &&
        !evidence.backend.backend_profile_id.empty() &&
        !evidence.backend.admitted_capabilities.empty() &&
        std::none_of(evidence.backend.admitted_capabilities.begin(),
                     evidence.backend.admitted_capabilities.end(),
                     [](const std::string &capability) { return capability.empty(); });
    if (!backend_complete) {
        add_issue(result, "evidence.invalid_backend", "$.backend",
                  "complete backend identity and admitted capabilities are required");
    }
    const bool backend_ascii =
        is_ascii(evidence.backend.provider_id) &&
        is_ascii(evidence.backend.implementation_version) &&
        is_ascii(evidence.backend.backend_profile_id) &&
        std::all_of(evidence.backend.admitted_capabilities.begin(),
                    evidence.backend.admitted_capabilities.end(),
                    [](const std::string &capability) { return is_ascii(capability); });
    if (!backend_ascii) {
        add_issue(result, "evidence.non_ascii_string", "$.backend",
                  "v1 backend identities and capabilities must be ASCII");
        payload_strings_ascii = false;
    }
    if (backend_complete && backend_ascii &&
        (backend_provider == evidence.provider_versions.end() ||
         backend_provider->implementation_version != evidence.backend.implementation_version)) {
        add_issue(result, "evidence.backend_provider_mismatch", "$.backend",
                  "backend identity must match the realized provider-version set");
    }
    if (std::adjacent_find(evidence.backend.admitted_capabilities.begin(),
                           evidence.backend.admitted_capabilities.end()) !=
        evidence.backend.admitted_capabilities.end()) {
        add_issue(result, "evidence.duplicate_capability", "$.backend.admitted_capabilities",
                  "backend capabilities must be unique");
    }

    if (evidence.world_instances.empty()) {
        add_issue(result, "evidence.empty_world_instances", "$.world_instances",
                  "at least one realized world is required");
    }

    std::set<std::uint64_t> world_indices;
    for (std::size_t world_position = 0; world_position < evidence.world_instances.size();
         ++world_position) {
        const auto &world = evidence.world_instances[world_position];
        if (world.world_index >
            static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
            add_issue(result, "evidence.integer_out_of_range", "$.world_instances",
                      "world indices must fit the signed 64-bit canonical JSON domain");
        }
        if (!world_indices.insert(world.world_index).second) {
            add_issue(result, "evidence.duplicate_world", "$.world_instances",
                      "world indices must be unique");
        }
        if (world.world_index != world_position) {
            add_issue(result, "evidence.noncontiguous_world", "$.world_instances",
                      "world indices must be the contiguous canonical range [0, world_count)");
        }
        std::set<std::string> scope_names;
        std::set<std::string> instance_ids;
        for (const auto &scope : world.scope_generations) {
            if (scope.generation >
                static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max())) {
                add_issue(result, "evidence.integer_out_of_range", "$.world_instances",
                          "scope generations must fit the signed 64-bit canonical JSON domain");
            }
            if (!valid_scope(scope.scope) || scope.instance_id.empty() || scope.generation == 0) {
                add_issue(result, "evidence.invalid_scope_generation", "$.world_instances",
                          "scope, instance identity, and positive generation are required");
            }
            if (!is_ascii(scope.scope) || !is_ascii(scope.instance_id)) {
                add_issue(result, "evidence.non_ascii_string", "$.world_instances",
                          "v1 scope identities must be ASCII");
                payload_strings_ascii = false;
            }
            if (!scope_names.insert(scope.scope).second ||
                !instance_ids.insert(scope.instance_id).second) {
                add_issue(result, "evidence.duplicate_scope_generation", "$.world_instances",
                          scope.scope + ":" + scope.instance_id);
            }
        }
        const bool has_every_scope =
            scope_names.size() == kScopeNames.size() &&
            std::all_of(kScopeNames.begin(), kScopeNames.end(), [&](std::string_view name) {
                return scope_names.contains(std::string(name));
            });
        if (!has_every_scope) {
            add_issue(result, "evidence.incomplete_scope_generations", "$.world_instances",
                      "every realized world must expose all five composition scopes");
        }
    }

    if (!payload_strings_ascii) {
        result.valid = false;
        return result;
    }

    RuntimeCompositionEvidence canonical = normalized(evidence);
    if (canonical.provider_versions != evidence.provider_versions ||
        canonical.backend.admitted_capabilities != evidence.backend.admitted_capabilities ||
        canonical.world_instances != evidence.world_instances) {
        add_issue(result, "evidence.noncanonical_order", "$",
                  "set-like evidence fields must use canonical order");
    }
    canonical.canonical_json.clear();
    canonical.evidence_sha256.clear();
    const std::string expected_json = payload_json(canonical).dump();
    if (evidence.canonical_json != expected_json) {
        add_issue(result, "evidence.canonical_bytes_mismatch", "$.canonical_json",
                  "canonical bytes do not match the evidence payload");
    }
    if (!is_sha256(evidence.evidence_sha256) ||
        evidence.evidence_sha256 !=
            runtime::projection_contracts::canonical_sha256_hex(expected_json)) {
        add_issue(result, "evidence.identity_mismatch", "$.evidence_sha256",
                  "evidence identity does not match canonical bytes");
    }

    result.valid = result.issues.empty();
    return result;
}

EvidenceComparisonResult
compare_runtime_composition_evidence(const RuntimeCompositionEvidence &expected,
                                     const RuntimeCompositionEvidence &actual) {
    EvidenceComparisonResult result;
    const auto expected_validation = validate_runtime_composition_evidence(expected);
    const auto actual_validation = validate_runtime_composition_evidence(actual);
    for (const auto &issue : expected_validation.issues) {
        result.mismatches.push_back("expected:" + issue.code + "@" + issue.path);
    }
    for (const auto &issue : actual_validation.issues) {
        result.mismatches.push_back("actual:" + issue.code + "@" + issue.path);
    }
    if (!expected_validation.valid || !actual_validation.valid) {
        return result;
    }

    compare_field(result, expected.runtime_request_sha256 == actual.runtime_request_sha256,
                  "$.runtime_request_sha256");
    compare_field(result, expected.composition_id == actual.composition_id, "$.composition_id");
    compare_field(result, expected.requested_profile_id == actual.requested_profile_id,
                  "$.requested_profile_id");
    compare_field(result, expected.requested_profile_version == actual.requested_profile_version,
                  "$.requested_profile_version");
    compare_field(result, expected.requested_manifest_sha256 == actual.requested_manifest_sha256,
                  "$.requested_manifest_sha256");
    compare_field(result, expected.resolved_manifest_sha256 == actual.resolved_manifest_sha256,
                  "$.resolved_manifest_sha256");
    compare_field(result, expected.catalog_lock_sha256 == actual.catalog_lock_sha256,
                  "$.catalog_lock_sha256");
    compare_field(result, expected.profile_projection_sha256 == actual.profile_projection_sha256,
                  "$.profile_projection_sha256");
    compare_field(result, expected.resolver_contract_version == actual.resolver_contract_version,
                  "$.resolver_contract_version");
    compare_field(result, expected.provider_versions == actual.provider_versions,
                  "$.provider_versions");
    compare_field(result, expected.backend == actual.backend, "$.backend");
    compare_field(result, expected.executable_graph_sha256 == actual.executable_graph_sha256,
                  "$.executable_graph_sha256");
    compare_field(result, expected.stage_contract_version == actual.stage_contract_version,
                  "$.stage_contract_version");
    compare_field(result, expected.host_mode == actual.host_mode, "$.host_mode");
    compare_field(result, expected.binding_version == actual.binding_version, "$.binding_version");
    compare_field(result, expected.world_instances == actual.world_instances, "$.world_instances");
    result.compatible = result.mismatches.empty();
    return result;
}

} // namespace runtime::composition_evidence_contracts
