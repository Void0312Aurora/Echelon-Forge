#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace runtime::composition_contracts {

inline constexpr std::string_view kManifestSchemaVersion =
    "echelon_forge.simulation_composition_manifest.v1";
inline constexpr std::string_view kResolvedManifestSchemaVersion =
    "echelon_forge.resolved_simulation_composition.v1";
inline constexpr std::string_view kCompositionContractVersion = "1.0.0";
inline constexpr std::string_view kResolverContractVersion =
    "echelon_forge.simulation_composition_resolver.v1";
inline constexpr std::string_view kCanonicalizationId =
    "echelon_forge.sorted_utf8_json.v1";
inline constexpr std::string_view kCanonicalHashAlgorithm = "sha256";

inline constexpr std::string_view kScopeApplication = "application";
inline constexpr std::string_view kScopeBackend = "backend";
inline constexpr std::string_view kScopeBatch = "batch";
inline constexpr std::string_view kScopeWorld = "world";
inline constexpr std::string_view kScopeEpisode = "episode";

inline constexpr std::string_view kServiceEnvironmentModel =
    "simulation.environment.model";
inline constexpr std::string_view kServiceUnitFactory = "simulation.unit_factory";
inline constexpr std::string_view kServiceEffectsModel = "simulation.effects.model";
inline constexpr std::string_view kServiceSensorModel = "simulation.sensor.model";
inline constexpr std::string_view kServiceAcousticModel = "simulation.acoustic.model";
inline constexpr std::string_view kServiceControlModel = "simulation.control.model";
inline constexpr std::string_view kServiceGuidanceModel = "simulation.guidance.model";
inline constexpr std::string_view kServiceEngagementEventRecorder =
    "runtime.engagement_event_recorder";
inline constexpr std::string_view kServiceWeaponReleaseDamageBridge =
    "runtime.weapon_release.damage_bridge";
inline constexpr std::string_view kServiceWeaponRelease =
    "runtime.weapon_release.service";
inline constexpr std::string_view kServiceWorldBatchBackend =
    "runtime.world_batch_backend";
inline constexpr std::string_view kServiceCompositionEvidenceSink =
    "runtime.composition_evidence_sink";

inline constexpr std::string_view kErrorInvalidJsonType =
    "composition.invalid_json_type";
inline constexpr std::string_view kErrorUnsupportedSchemaVersion =
    "composition.unsupported_schema_version";
inline constexpr std::string_view kErrorMissingField = "composition.missing_field";
inline constexpr std::string_view kErrorUnexpectedField = "composition.unexpected_field";
inline constexpr std::string_view kErrorInvalidIdentifier =
    "composition.invalid_identifier";
inline constexpr std::string_view kErrorInvalidVersion = "composition.invalid_version";
inline constexpr std::string_view kErrorDuplicateId = "composition.duplicate_id";
inline constexpr std::string_view kErrorDuplicateValue = "composition.duplicate_value";
inline constexpr std::string_view kErrorUnknownPlugin = "composition.unknown_plugin";
inline constexpr std::string_view kErrorUnknownProvider = "composition.unknown_provider";
inline constexpr std::string_view kErrorUnknownConsumer = "composition.unknown_consumer";
inline constexpr std::string_view kErrorUnknownService = "composition.unknown_service";
inline constexpr std::string_view kErrorServiceNotOffered =
    "composition.service_not_offered";
inline constexpr std::string_view kErrorMissingServiceBinding =
    "composition.missing_service_binding";
inline constexpr std::string_view kErrorAmbiguousServiceBinding =
    "composition.ambiguous_service_binding";
inline constexpr std::string_view kErrorScopeCaptureViolation =
    "composition.scope_capture_violation";
inline constexpr std::string_view kErrorProviderConflict =
    "composition.provider_conflict";
inline constexpr std::string_view kErrorProviderDependencyCycle =
    "composition.provider_dependency_cycle";
inline constexpr std::string_view kErrorUnknownComponent =
    "composition.unknown_component";
inline constexpr std::string_view kErrorUnknownSystemDependency =
    "composition.unknown_system_dependency";
inline constexpr std::string_view kErrorSystemConflict = "composition.system_conflict";
inline constexpr std::string_view kErrorSystemDependencyCycle =
    "composition.system_dependency_cycle";
inline constexpr std::string_view kErrorBackendProviderMismatch =
    "composition.backend_provider_mismatch";
inline constexpr std::string_view kErrorInvalidScopePolicy =
    "composition.invalid_scope_policy";
inline constexpr std::string_view kErrorInvalidReconfigurationPolicy =
    "composition.invalid_reconfiguration_policy";
inline constexpr std::string_view kErrorInvalidEvidencePolicy =
    "composition.invalid_evidence_policy";
inline constexpr std::string_view kErrorNoncanonicalNumber =
    "composition.noncanonical_number";

enum class CompositionScope : std::uint8_t {
    application = 0,
    backend = 1,
    batch = 2,
    world = 3,
    episode = 4,
};

[[nodiscard]] constexpr std::string_view to_string(CompositionScope scope) noexcept {
    switch (scope) {
        case CompositionScope::application:
            return kScopeApplication;
        case CompositionScope::backend:
            return kScopeBackend;
        case CompositionScope::batch:
            return kScopeBatch;
        case CompositionScope::world:
            return kScopeWorld;
        case CompositionScope::episode:
            return kScopeEpisode;
    }
    return {};
}

[[nodiscard]] constexpr bool can_supply_scope(
    CompositionScope provider_scope,
    CompositionScope consumer_scope
) noexcept {
    return static_cast<std::uint8_t>(provider_scope) <=
        static_cast<std::uint8_t>(consumer_scope);
}

struct CompositionContractVersions {
    std::string composition;
    std::string runtime;
    std::string content;
    std::string stage;
};

struct RequestedCompositionProfile {
    std::string profile_id;
    std::string profile_version;
};

struct CompositionArtifactRef {
    std::string kind;
    std::string identity;
    std::optional<std::string> sha256;
};

struct CompositionPluginDescriptor {
    std::string plugin_id;
    std::string implementation_id;
    std::string plugin_version;
    std::string composition_contract_range;
    std::vector<std::string> host_support;
    std::string determinism_class;
    CompositionArtifactRef artifact;
    std::vector<std::string> required_capabilities;
    std::vector<std::string> conflicts;
    // Canonical JSON object encoded with kCanonicalizationId. This keeps the
    // stable contract independent of a particular JSON library.
    std::string canonical_configuration_json;
};

struct CompositionProviderDescriptor {
    std::string provider_id;
    std::string plugin_id;
    std::string implementation_version;
    CompositionScope scope = CompositionScope::world;
    std::string cardinality;
    std::vector<std::string> offered_services;
    std::vector<std::string> required_services;
    std::vector<std::string> required_capabilities;
    std::vector<std::string> conflicts;
    std::vector<std::string> after_provider_ids;
    std::string restart_policy;
    std::string teardown_policy;
    std::string canonical_configuration_json;
};

struct CompositionServiceBinding {
    std::string consumer_kind;
    std::string consumer_id;
    std::string service_key;
    std::string provider_id;
};

struct CompositionComponentContribution {
    std::string component_id;
    std::string plugin_id;
    std::string registration_id;
};

struct CompositionSystemContribution {
    std::string contribution_id;
    std::string plugin_id;
    std::string registration_factory_id;
    std::string domain;
    std::vector<std::string> required_services;
    std::vector<std::string> required_components;
    std::vector<std::string> provided_components;
    std::vector<std::string> semantic_stage_ids;
    std::vector<std::string> executable_node_ids;
    std::vector<std::string> read_state_shards;
    std::vector<std::string> write_state_shards;
    std::vector<std::string> required_barriers;
    std::vector<std::string> required_capabilities;
    std::vector<std::string> conflicts;
    std::vector<std::string> after;
    std::vector<std::string> before;
};

struct CompositionBackendRequest {
    std::string backend_profile_id;
    std::string provider_id;
    std::vector<std::string> required_capabilities;
};

struct CompositionScopePolicy {
    CompositionScope scope = CompositionScope::world;
    std::optional<CompositionScope> parent_scope;
    std::string cardinality;
    std::string rebuild_trigger;
};

struct CompositionReconfigurationPolicy {
    std::string truth_affecting_change;
    std::string active_episode_change;
    std::vector<std::string> allowed_barriers;
};

struct CompositionEvidencePolicy {
    std::string canonicalization;
    std::string hash_algorithm;
    bool include_provider_versions = true;
    bool include_graph_hash = true;
    bool include_scope_generations = true;
};

struct SimulationCompositionManifest {
    std::string schema_version;
    std::string composition_id;
    CompositionContractVersions contract_versions;
    RequestedCompositionProfile requested_profile;
    std::vector<CompositionPluginDescriptor> plugins;
    std::vector<CompositionProviderDescriptor> providers;
    std::vector<CompositionServiceBinding> service_bindings;
    std::vector<CompositionComponentContribution> component_contributions;
    std::vector<CompositionSystemContribution> system_contributions;
    CompositionBackendRequest backend_request;
    std::vector<CompositionScopePolicy> scope_policies;
    CompositionReconfigurationPolicy reconfiguration_policy;
    CompositionEvidencePolicy evidence_policy;
    std::vector<std::string> compatibility_claims;
};

struct CompositionValidationIssue {
    std::string code;
    std::string path;
    std::string detail;
};

struct CompositionValidationResult {
    bool valid = true;
    std::vector<CompositionValidationIssue> issues;

    void add_issue(std::string code, std::string path, std::string detail) {
        valid = false;
        issues.push_back(
            {std::move(code), std::move(path), std::move(detail)}
        );
    }
};

struct ResolvedSimulationComposition {
    std::string schema_version;
    std::string resolver_contract_version;
    std::string requested_manifest_sha256;
    std::string resolved_manifest_sha256;
    std::vector<std::string> provider_construction_order;
    std::vector<std::string> system_registration_order;
    SimulationCompositionManifest manifest;
};

} // namespace runtime::composition_contracts
