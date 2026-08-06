#include <cstddef>
#include <exception>
#include <iostream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "runtime/contracts/cuda_resident_parity_release_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.h"

#if defined(EF_CR2_FULL_WINDOW_CPU_PROBE) && defined(EF_CR2_FULL_WINDOW_CUDA_PROBE)
#error "CR2 full-window probe must select exactly one lane"
#elif defined(EF_CR2_FULL_WINDOW_CPU_PROBE)
#include "runtime/facade/internal/flecs_cpu_backend.h"
#include <spdlog/spdlog.h>
#elif defined(EF_CR2_FULL_WINDOW_CUDA_PROBE)
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#else
#error "CR2 full-window probe lane is not configured"
#endif

namespace {

namespace full_window = runtime::cuda_resident::full_window;
namespace parity_release = runtime::cuda_resident::parity_release;
namespace replay = runtime::cuda_resident::replay;
using full_window::Operation;

inline constexpr std::string_view kProbeSchema = "cuda_resident.full_window_probe.v1";

struct Args {
    std::string database_path = "examples/config/database";
    bool parity_release = false;
};

replay::ReplayTrace make_trace() {
    replay::ReplayTrace trace{
        .run_id = "cr2.full_window.fixed_air",
        .seeds = {101, 202},
        .time_steps = {0.01, 0.02},
    };
    for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "CR2FullWindow" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        trace.spawns.push_back(std::move(spawn));
    }
    for (std::size_t window = 0; window < 2; ++window) {
        replay::ReplayActionWindow actions{
            .request_id = "cr2.window." + std::to_string(window),
        };
        for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
            PilotAction action{};
            action.stick_pitch = 0.01 * static_cast<double>(window + world + 1);
            action.stick_roll = -0.01 * static_cast<double>(world + 1);
            action.rudder = 0.005 * static_cast<double>(window + 1);
            action.throttle = 0.65 + 0.01 * static_cast<double>(world);
            action.active = true;
            actions.actions.push_back(action);
        }
        trace.windows.push_back(std::move(actions));
    }
    return trace;
}

Args args_from_command_line(int argc, char **argv) {
    Args args{};
    for (int index = 1; index < argc; ++index) {
        const std::string_view argument(argv[index]);
        if (argument == "--database" && index + 1 < argc) {
            args.database_path = argv[++index];
        } else if (argument == "--parity-release") {
            args.parity_release = true;
        } else {
            throw std::invalid_argument(
                "usage: full-window probe [--database <path>] [--parity-release]");
        }
    }
    return args;
}

void verify_common_sequence(const full_window::RunResult &result, std::size_t window_count) {
    const std::vector<Operation> per_window{
        Operation::input_injection,
        Operation::evaluation,
        Operation::advance,
        Operation::export_state,
    };
    if (!result.completed || result.operations.size() != 1 + per_window.size() * window_count ||
        result.operations.front().operation != Operation::setup) {
        throw std::runtime_error(
            "full-window probe did not complete the common operation sequence");
    }
    for (std::size_t window = 0; window < window_count; ++window) {
        for (std::size_t operation = 0; operation < per_window.size(); ++operation) {
            const auto &record = result.operations[1 + window * per_window.size() + operation];
            if (!record.succeeded || record.window_index != window ||
                record.operation != per_window[operation]) {
                throw std::runtime_error("full-window probe operation order diverged");
            }
        }
    }
}

nlohmann::json operations_json(const full_window::RunResult &result) {
    nlohmann::json operations = nlohmann::json::array();
    for (const auto &record : result.operations) {
        operations.push_back({
            {"window_index", record.window_index},
            {"request_id", record.request_id},
            {"operation", full_window::operation_name(record.operation)},
            {"succeeded", record.succeeded},
            {"barrier_id", record.barrier_id},
        });
    }
    return operations;
}

nlohmann::json failure_json(const full_window::RunResult &result) {
    if (!result.failure.has_value()) {
        return nullptr;
    }
    return {
        {"code", full_window::failure_code_name(result.failure->code)},
        {"operation", full_window::operation_name(result.failure->operation)},
        {"window_index", result.failure->window_index},
        {"last_completed_barrier", result.failure->last_completed_barrier},
        {"detail", result.failure->detail},
    };
}

nlohmann::json released_world_json(const AgentObservation &observation,
                                   const InstrumentState &instrument, std::size_t world_slot) {
    return {
        {"world_slot", world_slot},
        {"released",
         {{"agent_observations",
           {{"sim_time", observation.sim_time},
            {"x", observation.x},
            {"y", observation.y},
            {"z", observation.z},
            {"vx", observation.vx},
            {"vy", observation.vy},
            {"vz", observation.vz},
            {"heading", observation.heading},
            {"roll", observation.roll},
            {"speed", observation.speed},
            {"gear_state", observation.gear_state}}},
          {"instrument_states", {{"throttle_pos", instrument.throttle_pos}}}}},
        {"diagnostic_identity", {{"agent_observations", {{"id", observation.id}}}}},
    };
}

nlohmann::json released_frames_json(const full_window::RunResult &result) {
    nlohmann::json frames = nlohmann::json::array();
    for (const auto &frame : result.export_frames) {
        if (frame.agent_observations.size() != frame.instrument_states.size()) {
            throw std::runtime_error("full-window release frame cardinality diverged");
        }
        nlohmann::json worlds = nlohmann::json::array();
        for (std::size_t world = 0; world < frame.agent_observations.size(); ++world) {
            worlds.push_back(released_world_json(frame.agent_observations[world],
                                                 frame.instrument_states[world], world));
        }
        frames.push_back({
            {"window_index", frame.window_index},
            {"request_id", frame.request_id},
            {"source_barrier", frame.source_barrier},
            {"capture_barrier", frame.capture_barrier},
            {"worlds", std::move(worlds)},
        });
    }
    return frames;
}

nlohmann::json parity_contract_json() {
    nlohmann::json released = nlohmann::json::array();
    nlohmann::json identity = nlohmann::json::array();
    nlohmann::json excluded = nlohmann::json::array();
    nlohmann::json barriers = nlohmann::json::array();
    nlohmann::json lane_evidence = nlohmann::json::array();
    nlohmann::json diagnostic_metadata = nlohmann::json::array();
    for (const auto &field : parity_release::kReleasedNumericFields) {
        released.push_back({
            {"path", field.path},
            {"absolute_tolerance", field.absolute_tolerance},
            {"relative_tolerance", field.relative_tolerance},
            {"comparator", field.comparator},
            {"finite_required", field.finite_required},
            {"normalize_signed_zero", field.normalize_signed_zero},
        });
    }
    for (const auto &field : parity_release::kIdentityDiagnosticFields) {
        identity.push_back({{"path", field.path}, {"disposition", field.disposition}});
    }
    for (const auto &field : parity_release::kExcludedFields) {
        excluded.push_back({{"path", field.path}, {"reason", field.reason}});
    }
    for (const auto &barrier : parity_release::kBarrierRules) {
        barriers.push_back({
            {"barrier", barrier.barrier},
            {"disposition", barrier.disposition},
            {"reason", barrier.reason},
        });
    }
    for (const auto field : parity_release::kOuterLaneEvidenceFields) {
        lane_evidence.push_back(field);
    }
    for (const auto field : parity_release::kDiagnosticOnlyMetadataFields) {
        diagnostic_metadata.push_back(field);
    }
    return {
        {"schema_version", parity_release::kSchemaV1},
        {"policy_id", parity_release::kPolicyId},
        {"source_budget_ref", parity_release::kSourceBudgetRef},
        {"trace_profile_id", parity_release::kTraceProfileId},
        {"trace_signature_sha256", parity_release::kTraceSignatureSha256},
        {"payload_barrier", parity_release::kPayloadBarrier},
        {"payload_capture_path", parity_release::kPayloadCapturePath},
        {"canonical_world_key", parity_release::kCanonicalWorldKey},
        {"identity_policy", parity_release::kIdentityPolicy},
        {"reset_policy", parity_release::kResetPolicy},
        {"released_numeric_fields", std::move(released)},
        {"identity_diagnostic_fields", std::move(identity)},
        {"excluded_fields", std::move(excluded)},
        {"declared_barriers", std::move(barriers)},
        {"outer_lane_evidence_fields", std::move(lane_evidence)},
        {"diagnostic_only_metadata_fields", std::move(diagnostic_metadata)},
        {"raw_field_count", parity_release::kRawObservationFields.size() +
                                parity_release::kRawInstrumentFields.size()},
        {"partition_complete", parity_release::partition_is_complete()},
        {"candidate_promotion_blocked", parity_release::kCandidatePromotionBlocked},
        {"maintained_claim_allowed", parity_release::kMaintainedClaimAllowed},
        {"public_support_enabled", parity_release::kPublicSupportEnabled},
        {"measured_consumer_path_unchanged", parity_release::kMeasuredConsumerPathUnchanged},
    };
}

nlohmann::json released_session_json(const full_window::RunResult &result,
                                     std::size_t session_index, std::string_view session_label) {
    return {
        {"session_index", session_index},
        {"session_label", session_label},
        {"lane", replay::replay_lane_name(result.lane)},
        {"backend_id", result.backend_id},
        {"trace_signature", result.trace_signature},
        {"completed", result.completed},
        {"failure", failure_json(result)},
        {"operations", operations_json(result)},
        {"frames", released_frames_json(result)},
    };
}

nlohmann::json to_json(const full_window::RunResult &result,
                       const full_window::RunResult *reset_result) {
    nlohmann::json output{
        {"schema_version", kProbeSchema},
        {"surface_id", result.surface_id},
        {"lane", replay::replay_lane_name(result.lane)},
        {"backend_id", result.backend_id},
        {"trace_signature", result.trace_signature},
        {"completed", result.completed},
        {"operations", operations_json(result)},
    };
    if (reset_result != nullptr) {
        nlohmann::json parity = parity_contract_json();
        parity["sessions"] = nlohmann::json::array({
            released_session_json(result, 0, "first"),
            released_session_json(*reset_result, 1, "same_backend_reset"),
        });
        output["parity_release"] = std::move(parity);
    }
    output["failure"] = failure_json(result);
    return output;
}

} // namespace

int main(int argc, char **argv) {
    try {
        const Args args = args_from_command_line(argc, argv);
        const replay::ReplayTrace trace = make_trace();
#if defined(EF_CR2_FULL_WINDOW_CPU_PROBE)
        spdlog::set_level(spdlog::level::warn);
        auto backend = std::make_unique<FlecsCpuBackend>();
        backend->configure({.world_count = trace.seeds.size(), .worker_threads = 0});
        const auto content = backend->load_content({
            .kind = runtime::backend::ContentKind::Database,
            .path = &args.database_path,
        });
        if (!content.loaded) {
            throw std::runtime_error("CR2 CPU database load failed before runner entry");
        }
        const replay::ReplayLaneKind lane = replay::ReplayLaneKind::cpu_reference;
#else
        (void)args.database_path;
        if (!runtime::cuda_resident::CudaWorldStore::compiled_with_cuda()) {
            throw std::runtime_error("CR2 CUDA full-window probe was built without CUDA");
        }
        auto backend = std::make_unique<runtime::cuda_resident::CudaResidentBackend>();
        backend->configure({.world_count = trace.seeds.size()});
        const replay::ReplayLaneKind lane = replay::ReplayLaneKind::cuda_resident;
#endif
        full_window::Runner runner(*backend, {.lane = lane});
        const full_window::RunResult result = runner.run(trace);
        verify_common_sequence(result, trace.windows.size());
        std::optional<full_window::RunResult> reset_result;
        if (args.parity_release) {
            full_window::Runner reset_runner(*backend, {.lane = lane});
            reset_result = reset_runner.run(trace);
            verify_common_sequence(*reset_result, trace.windows.size());
        }
        std::cout << to_json(result, reset_result ? &*reset_result : nullptr).dump(2) << '\n';
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "CR2 full-window probe failed: " << error.what() << '\n';
        return 2;
    }
}
