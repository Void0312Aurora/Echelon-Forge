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
    "5627bc9e8968f02b48f83d6107e8ed72830e8a589b8fc6b96d3bd451b183b242";
inline constexpr std::string_view kResolvedManifestSha256 =
    "5556901f96740ca4b2a85ebf2d15d6e6a9e1eff3e4b7407148923b0373a4fe73";
inline constexpr std::string_view kCatalogLockSha256 =
    "ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94";
inline constexpr std::string_view kProfileProjectionSha256 =
    "808b04004b5e9725931d3ee7694103de63b37a2eacb3ed8f394cd5d3909434dd";
inline constexpr std::string_view kResolverContractVersion =
    "echelon_forge.simulation_composition_resolver.v1";
inline constexpr std::string_view kExecutableGraphSha256 =
    "ad00da86583a6da290eb4db550f520c323fe76e10778760ecf07affcd048cad6";
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
