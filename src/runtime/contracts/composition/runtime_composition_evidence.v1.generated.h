#pragma once

#include <array>
#include <string_view>

namespace runtime::composition_evidence_contracts::generated {

struct ProviderVersion {
    std::string_view provider_id;
    std::string_view implementation_version;
};

inline constexpr std::string_view kRuntimeRequestSha256 =
    "5c2954d6d04c77fe803130db14d7e5b56391dcf51e482c73ac8cd96877698d6f";
inline constexpr std::string_view kCompositionId = "builtin.default_compatibility";
inline constexpr std::string_view kRequestedProfileId = "builtin.default_compatibility";
inline constexpr std::string_view kRequestedProfileVersion = "1.0.0";
inline constexpr std::string_view kRequestedManifestSha256 =
    "f53d527676ee9b0c58e82adb5038f5baec6231005e6423773f5a5acf22ce82d2";
inline constexpr std::string_view kResolvedManifestSha256 =
    "696a70f3667b934e80d5525e7204a21b8c8e4ce4b6c67bfe54aac98f058e9728";
inline constexpr std::string_view kCatalogLockSha256 =
    "ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94";
inline constexpr std::string_view kProfileProjectionSha256 =
    "a18710e47cdb5d40f8502f066bc15c54b1edbd522050820024a60cc8422d8741";
inline constexpr std::string_view kResolverContractVersion =
    "echelon_forge.simulation_composition_resolver.v1";
inline constexpr std::string_view kExecutableGraphSha256 =
    "6c35e313f5a67ce7d6e76824a2652fc90319b0d8788723cb90ff5270297e3399";
inline constexpr std::string_view kStageContractVersion = "1.0.0";
inline constexpr std::string_view kHostMode = "native_cpp";
inline constexpr std::string_view kBindingVersion = "native.v1";
inline constexpr std::string_view kBackendProviderId = "builtin.backend.flecs_cpu";
inline constexpr std::string_view kBackendImplementationVersion = "1.0.0";
inline constexpr std::string_view kBackendProfileId = "cpu_exact.reference";

inline constexpr std::array<ProviderVersion, 11> kProviderVersions = {{
    {"builtin.acoustic.default", "1.0.0"},
    {"builtin.backend.flecs_cpu", "1.0.0"},
    {"builtin.control.default", "1.0.0"},
    {"builtin.effects.default", "1.0.0"},
    {"builtin.engagement_event_store", "1.0.0"},
    {"builtin.environment.default", "1.0.0"},
    {"builtin.guidance.default", "1.0.0"},
    {"builtin.sensor.default", "1.0.0"},
    {"builtin.unit_factory.default", "1.0.0"},
    {"builtin.weapon_release.damage_bridge", "1.0.0"},
    {"builtin.weapon_release.service", "1.0.0"},
}};

inline constexpr std::array<std::string_view, 1> kBackendCapabilities = {{
    "runtime.cpu_exact",
}};

} // namespace runtime::composition_evidence_contracts::generated
