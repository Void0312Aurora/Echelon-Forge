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
    "796721f17c1a995dbb26cc23a950287c96b0511d950aedbe71169d4b5d5aa4cc";
inline constexpr std::string_view kResolvedManifestSha256 =
    "50afe7755149225662774531be5eaf39794ebb246e6ccdcc42040fde9720bf56";
inline constexpr std::string_view kCatalogLockSha256 =
    "ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94";
inline constexpr std::string_view kProfileProjectionSha256 =
    "f9e73c2add32ed0739615b58e8e3cc2ef58a82a81746a055ebe3fc6b37458329";
inline constexpr std::string_view kResolverContractVersion =
    "echelon_forge.simulation_composition_resolver.v1";
inline constexpr std::string_view kExecutableGraphSha256 =
    "aa31bfeba7661e9eb0909d06f6f360f79b6bedf9d6948a0a6c639c8eb70de202";
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
