#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "components/systems/comm.h"
#include "core/interfaces/observation.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/contracts/runtime_dto_contracts.h"
#include "runtime/contracts/runtime_composition_evidence_contract.h"
#include "runtime/contracts/world_batch_contracts.h"

class SimulationKernel;
class FlecsCpuBackend;
struct ObservationBatchPacket;

struct RuntimeCapabilities {
#define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_capabilities.inc"
};

struct RuntimeBatchConfig {
#define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_batch_config.inc"
};

// Native-owned failure state for the active backend generation.  This is a
// diagnostic snapshot: it does not claim rollback or per-world commit truth.
struct RuntimeBatchFailureStatus {
    bool healthy = true;
    std::uint64_t generation = 0;
    bool requires_host_recreate = false;
    std::string failure_reason;
};

using RuntimeCompositionEvidence =
    runtime::composition_evidence_contracts::RuntimeCompositionEvidence;
using RuntimeCompositionEvidenceResult =
    runtime::composition_evidence_contracts::RuntimeCompositionEvidenceResult;
using RuntimeCompositionEvidenceComparison =
    runtime::composition_evidence_contracts::EvidenceComparisonResult;

// Explicit backend-selection preflight. This is deliberately separate from
// RuntimeBatchConfig so the maintained two-field CPU default keeps its bytes
// and behavior. Admission does not mutate or replace the active backend.
struct RuntimeBackendRequest {
    std::string backend_profile_id;
    std::string capability_manifest_id;
    std::string parity_budget_ref;
    std::vector<std::string> requested_feature_ids;
    bool allow_unmaintained_candidate = false;
};

struct RuntimeBackendAdmission {
    bool admitted = false;
    bool maintained_selection = false;
    bool experimental_selection = false;
    std::string backend_profile_id;
    std::string capability_manifest_id;
    std::string parity_budget_ref;
    std::vector<std::string> admitted_feature_ids;
    std::string rejection_reason;
    std::vector<std::string> errors;
};

struct RuntimeFidelityRequest {
#define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_fidelity_request.inc"
};

struct RuntimeFidelityAdmission {
#define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_fidelity_admission.inc"
};

// Native identity facts are detached observations of the maintained engine
// owner.  The facade never derives these values from observation packet
// versions, entity references, or Python-side mirrors.
struct RuntimeNativeSnapshotFacts {
    std::uint64_t step = 0;
    std::string state_digest;
    std::uint64_t event_cursor = 0;
    std::string rng_digest;
    bool terminated = false;

    [[nodiscard]] bool well_formed() const noexcept;
    bool operator==(const RuntimeNativeSnapshotFacts &) const = default;
};

// Opaque, native-owned sibling branch.  The child owns an independent
// SimulationKernel restored from the parent's complete native state bundle.
// No Python state or raw parent handle crosses this boundary.
class RuntimeFacadeNativeBranch {
  public:
    RuntimeFacadeNativeBranch(const RuntimeFacadeNativeBranch &) = delete;
    RuntimeFacadeNativeBranch &operator=(const RuntimeFacadeNativeBranch &) = delete;
    RuntimeFacadeNativeBranch(RuntimeFacadeNativeBranch &&) noexcept;
    RuntimeFacadeNativeBranch &operator=(RuntimeFacadeNativeBranch &&) noexcept;
    ~RuntimeFacadeNativeBranch();

    [[nodiscard]] bool valid() const noexcept;
    [[nodiscard]] RuntimeNativeSnapshotFacts snapshot_facts() const;
    [[nodiscard]] bool step_pilot_actions(const std::vector<WorldPilotActionAssignment> &actions);
    [[nodiscard]] ObservationBatchPacket
    read_observation_packet(const std::vector<WorldEntityRef> &refs) const;
    [[nodiscard]] std::unique_ptr<RuntimeFacadeNativeBranch> checkpoint() const;
    [[nodiscard]] std::unique_ptr<RuntimeFacadeNativeBranch>
    fork_native_branch(std::string intervention_digest, std::uint64_t horizon) const;

  private:
    struct State;
    explicit RuntimeFacadeNativeBranch(std::shared_ptr<State> state) noexcept;
    std::shared_ptr<State> state_;
    friend class FlecsCpuBackend;
    friend std::unique_ptr<RuntimeFacadeNativeBranch>
    make_runtime_facade_native_branch(SimulationKernel &, std::uint64_t, std::string,
                                      std::uint64_t);
};

struct BatchResetRequest {
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/batch_reset_request.inc"
};

struct BatchWorldSetupRequest {
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/batch_world_setup_request.inc"
};

struct BatchWorldSetupResult {
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/batch_world_setup_result.inc"
};

struct RuntimeWorldLayoutRequest {
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_world_layout_request.inc"
};

struct RuntimeWorldLayoutResult {
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime/runtime_world_layout_result.inc"
};

struct ObservationBatchRequest {
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/observation_batch_request.inc"
};

struct TaskingBatchRequest {
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/tasking_batch_request.inc"
};

struct EngagementBatchRequest {
#define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/engagement_batch_request.inc"
};

struct DeviceResidentOutputDescriptor {
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/runtime/resident_device_output_descriptor.inc"
};

struct ObservationBatchPacket {
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/observation_batch_packet.inc"
};

struct EngagementEventPacket {
#define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/engagement_event_packet.inc"
};

struct TaskingBatchPacket {
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch/tasking_batch_packet.inc"
};

struct RuntimeWindowActionRequest {
    struct CadenceControl {
#define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name, default_value)                         \
    type name = default_value;
#include "runtime/facade/detail/window/runtime_window_cadence_control.inc"
    };

    ActionIntentPacket action_intent{};
    std::string source_layer = "facade";
    std::string input_snapshot_version;
    struct ClockDomainMetadata {
        std::string source_clock_domain = "outer_window";
        std::string relation = "nested";
        std::string clock_merge_policy;
        double source_time_s = 0.0;
        bool has_source_time = false;
        std::string source_snapshot_version;
        std::string target_window_id;
        std::vector<std::string> barrier_order;
        bool diagnostics_only = false;
        std::string diagnostics_reason;
    } clock_domain_metadata{};
    CadenceControl cadence_control{};
};

struct RuntimeWindowInputRecord {
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_input_record.inc"
};

struct RuntimeWindowSchedulingContext {
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/window/runtime_window_scheduling_context.inc"
};

struct RuntimeWindowBarrierRecord {
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_barrier_record.inc"
};

struct RuntimeWindowVisibilityRecord {
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value)                       \
    type name = default_value;
#include "runtime/facade/detail/window/runtime_window_visibility_record.inc"
};

struct RuntimeWindowNodeExecutionRecord {
#define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type, name, default_value)                   \
    type name = default_value;
#include "runtime/facade/detail/window/runtime_window_node_execution_record.inc"
};

struct RuntimeWindowCadence {
#define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_cadence.inc"
};

struct RuntimeWindowCadenceConfig {
#define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_cadence_config.inc"
};

struct RuntimeWindowCadenceTraceRecord {
#define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type, name, default_value)                    \
    type name = default_value;
#include "runtime/facade/detail/window/runtime_window_cadence_trace_record.inc"
};

struct RuntimeWindowRequest {
#define EF_RUNTIME_WINDOW_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_request.inc"
};

struct RuntimeWindowResult {
#define EF_RUNTIME_WINDOW_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/window/runtime_window_result.inc"
};
