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
    "51a09dc082a48cbed8f311512d48ee245b5b69512bfa63bfe38d8343f84c8ba9";
inline constexpr std::string_view kResolvedManifestSha256 =
    "791847a129734e9ab632a8eff9a3a141d13bda9bba76093440dc9269a63d3796";
inline constexpr std::string_view kCatalogLockSha256 =
    "ec36d4f134e003e852a87f0dc2edb8095bbd798855d88b099e0174d45efa7f94";
inline constexpr std::string_view kProfileProjectionSha256 =
    "1339376f0d0de6bfb2541f72ac2a8250669357db1b4eba610227fa66bf4cc945";
inline constexpr std::string_view kResolverContractVersion =
    "echelon_forge.simulation_composition_resolver.v1";
inline constexpr std::string_view kExecutableGraphSha256 =
    "be615e16a2634a17d7dce3595cbcb54331324e3709f0147e05fe0a144222b0ef";
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
