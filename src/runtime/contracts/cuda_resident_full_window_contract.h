#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "runtime/contracts/cuda_resident_replay_contract.h"

struct AgentObservation;
struct InstrumentState;

namespace runtime::cuda_resident::full_window {

inline constexpr std::string_view kSurfaceId = "cuda_resident.full_window_spi.v1";
inline constexpr std::string_view kInputBarrier = "input_injection";
inline constexpr std::string_view kWindowBarrier = "window_commit";
inline constexpr std::string_view kExportBarrier = "export";

enum class Operation : std::uint8_t {
    setup,
    input_injection,
    evaluation,
    advance,
    export_state,
};

enum class FailureCode : std::uint8_t {
    invalid_trace,
    setup_failed,
    input_failed,
    evaluation_failed,
    unexpected_evaluation_output,
    advance_failed,
    export_failed,
    export_cardinality_mismatch,
    export_identity_mismatch,
    session_poisoned,
};

struct OperationRecord {
    std::size_t window_index = 0;
    std::string request_id;
    Operation operation = Operation::setup;
    bool succeeded = false;
    std::string barrier_id;
};

struct FailureRecord {
    FailureCode code = FailureCode::invalid_trace;
    Operation operation = Operation::setup;
    std::size_t window_index = 0;
    std::string last_completed_barrier;
    std::string detail;
};

struct ExportFrame {
    std::size_t window_index = 0;
    std::string request_id;
    std::string source_barrier;
    std::string capture_barrier;
    std::vector<AgentObservation> agent_observations;
    std::vector<InstrumentState> instrument_states;
};

struct RunResult {
    std::string surface_id = std::string(kSurfaceId);
    replay::ReplayLaneKind lane = replay::ReplayLaneKind::cpu_reference;
    std::string backend_id;
    std::string trace_signature;
    bool completed = false;
    std::vector<OperationRecord> operations;
    std::vector<ExportFrame> export_frames;
    std::optional<FailureRecord> failure;
};

[[nodiscard]] inline std::string_view operation_name(Operation operation) noexcept {
    switch (operation) {
    case Operation::setup:
        return "setup";
    case Operation::input_injection:
        return "input_injection";
    case Operation::evaluation:
        return "evaluation";
    case Operation::advance:
        return "advance";
    case Operation::export_state:
        return "export";
    }
    return "unknown";
}

[[nodiscard]] inline std::string_view failure_code_name(FailureCode code) noexcept {
    switch (code) {
    case FailureCode::invalid_trace:
        return "invalid_trace";
    case FailureCode::setup_failed:
        return "setup_failed";
    case FailureCode::input_failed:
        return "input_failed";
    case FailureCode::evaluation_failed:
        return "evaluation_failed";
    case FailureCode::unexpected_evaluation_output:
        return "unexpected_evaluation_output";
    case FailureCode::advance_failed:
        return "advance_failed";
    case FailureCode::export_failed:
        return "export_failed";
    case FailureCode::export_cardinality_mismatch:
        return "export_cardinality_mismatch";
    case FailureCode::export_identity_mismatch:
        return "export_identity_mismatch";
    case FailureCode::session_poisoned:
        return "session_poisoned";
    }
    return "unknown";
}

} // namespace runtime::cuda_resident::full_window
