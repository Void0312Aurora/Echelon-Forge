#pragma once

#include "core/engine/world_batch_runtime.h"
#include "runtime/facade/runtime_facade.h"

#include "runtime/contracts/stage_node_manifest_registry.h"
#include "runtime/facade/internal/world_batch_backend.h"
#include "runtime/facade/internal/world_batch_backend_provider.h"
#include "runtime/facade/internal/world_batch_compatibility_port.h"

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

struct RuntimeFacadeHostContext {
    std::string host_mode = "native_cpp";
    std::string binding_version = "native.v1";
};

struct RuntimeFacadeIdentity {
    runtime::backend_provider::WorldBatchBackendProviderIdentity backend_identity;
    RuntimeFacadeHostContext host_context;
    // Backend/world generations may restart after a world is destroyed. This
    // facade-owned incarnation makes shrink/regrow evidence identities ABA-safe.
    std::uint64_t composition_incarnation = 1;
};

namespace runtime_facade_internal {

using runtime::scheduler::find_stage_node_manifest;

inline std::vector<WorldEntityRef>
world_refs_from_engagement_refs(const std::vector<EngagementEntityRef> &refs) {
    std::vector<WorldEntityRef> out;
    out.reserve(refs.size());
    for (const auto &ref : refs) {
        out.push_back(WorldEntityRef{
            .world_index = ref.world_index,
            .entity_id = ref.entity_id,
        });
    }
    return out;
}

inline bool valid_runtime_world_index(const IWorldBatchBackend &runtime,
                                      std::uint64_t world_index) {
    return world_index < runtime.configuration().world_count;
}

inline const IWorldBatchCompatibilityPort &
require_compatibility_port(const IWorldBatchBackend &runtime) {
    const IWorldBatchCompatibilityPort *port = runtime.compatibility_port();
    if (port == nullptr) {
        throw std::logic_error("selected backend does not expose the legacy compatibility port");
    }
    return *port;
}

inline constexpr std::string_view kObservationExportNodeId = "observation_export.v1";
inline constexpr std::string_view kLaunchNodeId = "fire_control_launch.v1";
inline constexpr std::string_view kEffectsDamageNodeId = "effects_damage.v1";
inline constexpr std::string_view kExportBarrierId = "export";
inline constexpr std::string_view kExportBarrierDetail = "maintained_facade_export";
inline constexpr std::uint64_t kExportBarrierSequence = 1;
inline constexpr std::string_view kObservationPacketIdPrefix = "obs:";
inline constexpr std::string_view kEngagementPacketIdPrefix = "eng:";
inline constexpr std::string_view kDiagnosticsPacketIdPrefix = "diag:";
inline constexpr std::string_view kMaintainedBaselineBackendProfileId = "cpu_exact.reference";
inline constexpr std::string_view kMaintainedBaselineParityBudgetRef =
    "parity_budget.cpu_exact.reference.v1";
inline constexpr std::string_view kMaintainedBaselineProfileStatus = "maintained_exact_baseline";
inline constexpr std::string_view kDeviceObservationViewCandidateProfileId =
    "gpu_helpers.diagnostics_only";
inline constexpr std::string_view kDeviceObservationViewRejectionReason =
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile";
inline constexpr std::string_view kExactGpuBackendCandidateProfileId =
    "gpu_exact.unmaintained_candidate";
inline constexpr std::string_view kExactGpuBackendRejectionReason =
    "gpu_exact.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kResidentStateCandidateProfileId =
    "resident_state.unmaintained_candidate";
inline constexpr std::string_view kResidentStateCandidateParityBudgetRef =
    "parity_budget.resident_state.unmaintained_candidate.v1";
inline constexpr std::string_view kResidentStateRejectionReason =
    "resident_state.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kShadowCompareCandidateProfileId =
    "shadow_compare.unmaintained_candidate";
inline constexpr std::string_view kShadowCompareCandidateParityBudgetRef =
    "parity_budget.shadow_compare.unmaintained_candidate.v1";
inline constexpr std::string_view kShadowCompareRejectionReason =
    "shadow_compare.unmaintained_candidate_is_not_maintained";
inline constexpr std::string_view kMultiFidelityRejectionReason =
    "multi_fidelity_profiles_require_a_maintained_registry_revision_and_acceptance_gate";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyNone = "none";
inline constexpr std::string_view kRuntimeFidelityProviderFamilyReferenceCpu = "reference_cpu";

inline bool runtime_string_blank(const std::string &value) {
    return value.empty() || std::all_of(value.begin(), value.end(),
                                        [](unsigned char c) { return std::isspace(c) != 0; });
}

inline void append_runtime_evidence_ref(std::vector<std::string> &evidence_refs,
                                        const std::string &ref) {
    if (runtime_string_blank(ref)) {
        return;
    }
    if (std::find(evidence_refs.begin(), evidence_refs.end(), ref) != evidence_refs.end()) {
        return;
    }
    evidence_refs.push_back(ref);
}

} // namespace runtime_facade_internal
