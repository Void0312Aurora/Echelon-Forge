#include "runtime/contracts/cuda_resident_learner_consumption_contract.h"
#include "runtime/contracts/cuda_resident_matrix_contract.h"
#include "runtime/contracts/cuda_resident_selected_slice_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"
#include "tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if defined(EF_CR2_MATRIX_CPU_PROBE) && defined(EF_CR2_MATRIX_CUDA_PROBE)
#error "CR2 matrix probe must select exactly one lane"
#elif defined(EF_CR2_MATRIX_CUDA_PROBE)
#include <cuda_runtime_api.h>
#elif defined(EF_CR2_MATRIX_CPU_PROBE)
#include <spdlog/spdlog.h>
#else
#error "CR2 matrix probe lane is not configured"
#endif

#ifndef EF_CR2_MATRIX_BUILD_CONFIG
#define EF_CR2_MATRIX_BUILD_CONFIG "unknown"
#endif

namespace {

namespace matrix = runtime::cuda_resident::matrix;
namespace probe = runtime::cuda_resident::matrix::probe;
namespace replay = runtime::cuda_resident::replay;
using Clock = std::chrono::steady_clock;
using Json = nlohmann::json;

struct Args {
    std::vector<std::size_t> world_counts{matrix::kWorldCounts.begin(), matrix::kWorldCounts.end()};
    matrix::Protocol protocol = matrix::kProductionProtocol;
    std::string database_path = "examples/config/database";
    std::string output_path;
    // CP-6 opt-in: appends the learner-equivalent consumer mode. Off by
    // default so unflagged reports keep the frozen CR2-6a mode shape.
    bool learner_consumer_mode = false;
};

double elapsed_ms(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double, std::milli>(end - start).count();
}

std::size_t parse_positive_size(const char *value, const char *label) {
    if (value == nullptr || *value == '\0') {
        throw std::invalid_argument(std::string(label) + " requires a positive integer");
    }
    char *end = nullptr;
    const unsigned long long parsed = std::strtoull(value, &end, 10);
    if (end == value || *end != '\0' || parsed == 0 ||
        parsed > std::numeric_limits<std::size_t>::max()) {
        throw std::invalid_argument(std::string(label) + " requires a positive integer");
    }
    return static_cast<std::size_t>(parsed);
}

std::vector<std::size_t> parse_world_counts(std::string_view value) {
    std::vector<std::size_t> counts;
    std::size_t begin = 0;
    while (begin <= value.size()) {
        const std::size_t comma = value.find(',', begin);
        const std::string token(value.substr(
            begin, comma == std::string_view::npos ? value.size() - begin : comma - begin));
        counts.push_back(parse_positive_size(token.c_str(), "--worlds"));
        if (comma == std::string_view::npos) break;
        begin = comma + 1;
    }
    if (!std::is_sorted(counts.begin(), counts.end()) ||
        std::adjacent_find(counts.begin(), counts.end()) != counts.end()) {
        throw std::invalid_argument("--worlds must be unique and ascending");
    }
    for (const std::size_t count : counts) {
        if (std::find(matrix::kWorldCounts.begin(), matrix::kWorldCounts.end(), count) ==
            matrix::kWorldCounts.end()) {
            throw std::invalid_argument("--worlds contains a count outside the frozen matrix");
        }
    }
    return counts;
}

Args args_from_command_line(int argc, char **argv) {
    Args args{};
    for (int index = 1; index < argc; ++index) {
        const std::string flag(argv[index]);
        const auto require_value = [&](const char *label) -> const char * {
            if (index + 1 >= argc) throw std::invalid_argument(std::string(label) + " needs value");
            return argv[++index];
        };
        if (flag == "--worlds") {
            args.world_counts = parse_world_counts(require_value("--worlds"));
        } else if (flag == "--cold-samples") {
            args.protocol.cold_samples =
                parse_positive_size(require_value(flag.c_str()), flag.c_str());
        } else if (flag == "--warmup") {
            args.protocol.warmup_windows =
                parse_positive_size(require_value(flag.c_str()), flag.c_str());
        } else if (flag == "--measured") {
            args.protocol.measured_windows =
                parse_positive_size(require_value(flag.c_str()), flag.c_str());
        } else if (flag == "--rollout-samples") {
            args.protocol.rollout_samples =
                parse_positive_size(require_value(flag.c_str()), flag.c_str());
        } else if (flag == "--rollout-windows") {
            args.protocol.rollout_windows =
                parse_positive_size(require_value(flag.c_str()), flag.c_str());
        } else if (flag == "--database") {
            args.database_path = require_value("--database");
        } else if (flag == "--output") {
            args.output_path = require_value("--output");
        } else if (flag == "--learner-consumer") {
            args.learner_consumer_mode = true;
        } else if (flag == "--smoke") {
            args.world_counts = {1, 4};
            args.protocol = {
                .cold_samples = 1,
                .warmup_windows = 1,
                .measured_windows = 2,
                .rollout_samples = 1,
                .rollout_windows = 2,
            };
        } else {
            throw std::invalid_argument("unknown CR2 matrix probe flag: " + flag);
        }
    }
    return args;
}

bool is_production_protocol(const Args &args) {
    const auto &expected = matrix::kProductionProtocol;
    return args.world_counts ==
               std::vector<std::size_t>(matrix::kWorldCounts.begin(), matrix::kWorldCounts.end()) &&
           args.protocol.cold_samples == expected.cold_samples &&
           args.protocol.warmup_windows == expected.warmup_windows &&
           args.protocol.measured_windows == expected.measured_windows &&
           args.protocol.rollout_samples == expected.rollout_samples &&
           args.protocol.rollout_windows == expected.rollout_windows;
}

replay::ReplayTrace make_trace(std::size_t world_count) {
    replay::ReplayTrace trace{
        .run_id = "cr2.production_matrix.fixed_air",
    };
    trace.seeds.reserve(world_count);
    trace.spawns.reserve(world_count);
    trace.time_steps.reserve(world_count);
    replay::ReplayActionWindow actions{.request_id = "cr2.matrix.window"};
    actions.actions.reserve(world_count);
    for (std::size_t world = 0; world < world_count; ++world) {
        trace.seeds.push_back(static_cast<std::uint32_t>(1009 + world * 17));
        trace.time_steps.push_back(0.001 + static_cast<double>(world % 3) * 0.0001);
        trace.spawns.push_back({
            .world_index = world,
            .type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName),
            .entity_name = "CR2Matrix" + std::to_string(world),
            .is_agent = true,
            .x = 1000.0 + static_cast<double>(world % 32) * 25.0,
            .y = static_cast<double>(world / 32) * 20.0,
            .z = 1500.0 + static_cast<double>(world % 7),
            .heading = 90.0,
            .vx = 200.0 + static_cast<double>(world % 5),
        });
        PilotAction action{};
        action.stick_pitch = static_cast<double>(static_cast<int>(world % 5) - 2) * 0.01;
        action.stick_roll = static_cast<double>(static_cast<int>(world % 7) - 3) * 0.01;
        action.rudder = static_cast<double>(static_cast<int>(world % 3) - 1) * 0.01;
        action.throttle = 0.65 + static_cast<double>(world % 3) * 0.01;
        action.active = true;
        actions.actions.push_back(action);
    }
    trace.windows.push_back(std::move(actions));
    return trace;
}

std::string trace_digest(const replay::ReplayTrace &trace) {
    const std::string canonical = replay::CudaResidentReplayHarness::trace_signature(trace);
    const std::uint64_t digest = matrix::fnv1a64(canonical);
    constexpr char digits[] = "0123456789abcdef";
    std::string output(16, '0');
    for (std::size_t index = 0; index < output.size(); ++index) {
        const std::size_t shift = (output.size() - index - 1) * 4;
        output[index] = digits[(digest >> shift) & 0x0fU];
    }
    return output;
}

Json statistics_json(const std::vector<double> &samples) {
    if (samples.empty()) return nullptr;
    std::vector<double> sorted = samples;
    std::sort(sorted.begin(), sorted.end());
    const auto nearest_rank = [&](double percentile) {
        const double rank = std::ceil(percentile * static_cast<double>(sorted.size()));
        const std::size_t index = static_cast<std::size_t>(std::max(1.0, rank)) - 1;
        return sorted[std::min(index, sorted.size() - 1)];
    };
    const double total = std::accumulate(samples.begin(), samples.end(), 0.0);
    return {
        {"sample_count", samples.size()},
        {"p50_ms", nearest_rank(0.50)},
        {"p95_ms", nearest_rank(0.95)},
        {"min_ms", sorted.front()},
        {"max_ms", sorted.back()},
        {"mean_ms", total / static_cast<double>(samples.size())},
        {"raw_ms", samples},
    };
}

Json unavailable_row(std::size_t world_count, const probe::Mode &mode,
                     const std::string &trace_signature) {
    return {
        {"world_count", world_count},
        {"mode_id", mode.id},
        {"host_export", mode.host_export},
        {"device_consumer", mode.device_consumer},
        {"trace_signature", trace_signature},
        {"available", false},
        {"unavailable_reason", "cpu_reference_has_no_device_observation_consumer"},
        {"effective_worker_threads", nullptr},
        {"latency", nullptr},
        {"reset_determinism", nullptr},
        {"consumer_diagnostics", nullptr},
        {"device_memory", nullptr},
        {"promotion_eligible", false},
    };
}

Json run_row(const Args &args, std::size_t world_count, const probe::Mode &mode) {
    const replay::ReplayTrace trace = make_trace(world_count);
    const std::string trace_signature = trace_digest(trace);
#if defined(EF_CR2_MATRIX_CPU_PROBE)
    if (mode.device_consumer) return unavailable_row(world_count, mode, trace_signature);
#endif

    std::vector<double> setup_samples;
    std::vector<double> cold_total_samples;
    std::vector<double> cold_window_samples;
    std::string reset_digest;
    std::size_t receipt_count = 0;
    std::size_t materialized_count = 0;
    probe::ProbeSession cold(trace, args.database_path);
    for (std::size_t sample = 0; sample < args.protocol.cold_samples; ++sample) {
        const auto total_begin = Clock::now();
        cold.reset_fixture();
        setup_samples.push_back(cold.setup_ms());
        const probe::WindowTiming timing = cold.run_window(mode);
        cold_window_samples.push_back(timing.end_to_end_ms);
        cold_total_samples.push_back(elapsed_ms(total_begin, Clock::now()));
        const auto drained = cold.drain_device_consumers(sample == 0);
        receipt_count += drained.receipt_count;
        materialized_count += drained.materialized_count;
        const std::string digest = cold.released_state_digest();
        if (reset_digest.empty()) reset_digest = digest;
        if (digest != reset_digest) {
            throw std::runtime_error("CR2 matrix selected payload reset digest drifted");
        }
    }

    probe::ProbeSession warmed(trace, args.database_path);
    const std::size_t effective_worker_threads = warmed.effective_worker_threads();
    const std::size_t device_bytes = warmed.device_bytes();
    const std::size_t state_slot_bytes = warmed.state_slot_bytes();
    for (std::size_t window = 0; window < args.protocol.warmup_windows; ++window) {
        (void)warmed.run_window(mode);
        const auto drained = warmed.drain_device_consumers(false);
        receipt_count += drained.receipt_count;
    }
    std::vector<double> end_to_end_samples;
    std::vector<double> compute_samples;
    std::vector<double> collection_samples;
    for (std::size_t window = 0; window < args.protocol.measured_windows; ++window) {
        const probe::WindowTiming timing = warmed.run_window(mode);
        end_to_end_samples.push_back(timing.end_to_end_ms);
        compute_samples.push_back(timing.input_evaluate_advance_ms);
        collection_samples.push_back(timing.collection_ms);
        const auto drained = warmed.drain_device_consumers(false);
        receipt_count += drained.receipt_count;
    }

    std::vector<double> rollout_samples;
    std::size_t max_deferred_receipts = 0;
    probe::ProbeSession rollout(trace, args.database_path);
    for (std::size_t sample = 0; sample < args.protocol.rollout_samples; ++sample) {
        rollout.reset_fixture();
        const auto begin = Clock::now();
        for (std::size_t window = 0; window < args.protocol.rollout_windows; ++window) {
            (void)rollout.run_window(mode);
        }
        rollout_samples.push_back(elapsed_ms(begin, Clock::now()));
        const auto drained = rollout.drain_device_consumers(false);
        receipt_count += drained.receipt_count;
        max_deferred_receipts = std::max(max_deferred_receipts, drained.receipt_count);
    }

    return {
        {"world_count", world_count},
        {"mode_id", mode.id},
        {"host_export", mode.host_export},
        {"device_consumer", mode.device_consumer},
        {"trace_signature", trace_signature},
        {"available", true},
        {"unavailable_reason", ""},
        {"effective_worker_threads", effective_worker_threads},
        {"latency",
         {{"setup", statistics_json(setup_samples)},
          {"cold_reset_setup_plus_first_window", statistics_json(cold_total_samples)},
          {"cold_first_window", statistics_json(cold_window_samples)},
          {"warmed_end_to_end", statistics_json(end_to_end_samples)},
          {"warmed_input_evaluate_advance", statistics_json(compute_samples)},
          {"warmed_collection", statistics_json(collection_samples)},
          {"rollout_total", statistics_json(rollout_samples)},
          {"rollout_windows", args.protocol.rollout_windows}}},
        {"reset_determinism",
         {{"checked", true},
          {"matched", true},
          {"digest", reset_digest},
          {"scope", "released_selected_payload_identity_excluded"},
          {"identity_excluded", true},
          {"correctness_export_outside_timer", true}}},
        {"consumer_diagnostics",
         {{"receipt_count", receipt_count},
          {"materialized_count", materialized_count},
          {"validation_outside_timer", true},
          {"release_outside_timer", true},
          {"max_deferred_rollout_receipts", max_deferred_receipts}}},
        {"device_memory",
         {{"availability", device_bytes > 0 ? "candidate_owned_requested_bytes" : "not_applicable"},
          {"resident_bytes", device_bytes > 0 ? Json(device_bytes) : Json(nullptr)},
          {"state_slot_bytes", state_slot_bytes > 0 ? Json(state_slot_bytes) : Json(nullptr)}}},
        {"promotion_eligible", false},
    };
}

#if defined(EF_CR2_MATRIX_CUDA_PROBE)
Json cuda_environment() {
    int device = 0;
    cudaDeviceProp properties{};
    int driver_version = 0;
    int runtime_version = 0;
    if (cudaGetDevice(&device) != cudaSuccess ||
        cudaGetDeviceProperties(&properties, device) != cudaSuccess ||
        cudaDriverGetVersion(&driver_version) != cudaSuccess ||
        cudaRuntimeGetVersion(&runtime_version) != cudaSuccess) {
        throw std::runtime_error("CR2 matrix CUDA environment query failed");
    }
    return {
        {"device_ordinal", device},
        {"device_name", properties.name},
        {"compute_capability",
         std::to_string(properties.major) + "." + std::to_string(properties.minor)},
        {"total_global_memory_bytes", properties.totalGlobalMem},
        {"driver_version", driver_version},
        {"runtime_version", runtime_version},
    };
}
#endif

Json run_probe(const Args &args) {
    std::vector<probe::Mode> modes = {
        {.host_export = false, .device_consumer = false, .id = "no_export_no_device"},
        {.host_export = true, .device_consumer = false, .id = "host_export_no_device"},
        {.host_export = false, .device_consumer = true, .id = "no_export_device_consumer"},
        {.host_export = true, .device_consumer = true, .id = "host_export_device_consumer"},
    };
    if (args.learner_consumer_mode) {
        modes.push_back(
            {.host_export = false,
             .device_consumer = true,
             .learner_consumer = true,
             .id = std::string(
                 runtime::cuda_resident::learner_consumption::kLearnerConsumerModeIdNoExport)});
    }
#if defined(EF_CR2_MATRIX_CPU_PROBE)
    const std::string lane = "flecs_cpu_reference";
    const Json environment = nullptr;
    const Json lane_configuration = {
        {"host_worker_request", matrix::kCpuHostWorkerRequest},
        {"host_worker_policy", matrix::kCpuHostWorkerPolicy},
        {"device_parallelism", "not_applicable"},
    };
#else
    const std::string lane = "cuda_resident";
    const Json environment = cuda_environment();
    const Json lane_configuration = {
        {"host_worker_request", matrix::kCudaHostWorkerRequest},
        {"host_worker_policy", matrix::kCudaHostWorkerPolicy},
        {"device_parallelism", std::string("world_grid_") +
                                   std::to_string(matrix::kCudaThreadsPerBlock) +
                                   "_threads_per_block"},
    };
#endif
    Json rows = Json::array();
    for (const std::size_t world_count : args.world_counts) {
        for (const auto &mode : modes)
            rows.push_back(run_row(args, world_count, mode));
    }
    Json mode_rows = Json::array();
    for (const auto &mode : matrix::kModes) {
        mode_rows.push_back({
            {"mode_id", mode.id},
            {"host_export", mode.host_export},
            {"device_consumer", mode.device_consumer},
            {"cpu_available", mode.cpu_available},
        });
    }
    if (args.learner_consumer_mode) {
        mode_rows.push_back({
            {"mode_id", runtime::cuda_resident::learner_consumption::kLearnerConsumerModeIdNoExport},
            {"host_export", false},
            {"device_consumer", true},
            {"learner_consumer", true},
            {"cpu_available", false},
        });
    }
    return {
        {"schema_version", matrix::kProbeSchema},
        {"profile_id", matrix::kProfileId},
        {"lane", lane},
        {"backend_id",
         rows.empty() ? "" : probe::ProbeSession(make_trace(1), args.database_path).backend_id()},
        {"build_config", EF_CR2_MATRIX_BUILD_CONFIG},
        {"production_protocol", is_production_protocol(args)},
        {"invocation_surface", matrix::kInvocationSurface},
        {"full_window_surface_ref", matrix::kFullWindowSurfaceRef},
        {"operation_sequence", Json::array({"inject", "evaluate_empty", "advance_world_batch",
                                            "optional_public_export", "optional_device_consumer"})},
        {"selected_payload_schema_ref", matrix::kSelectedPayloadSchemaRef},
        {"selected_payload_policy_ref", matrix::kSelectedPayloadPolicyRef},
        {"selected_payload_policy_trace_profile_ref",
         matrix::kSelectedPayloadPolicyTraceProfileRef},
        {"selected_payload_reference_scope", matrix::kSelectedPayloadReferenceScope},
        {"selected_payload_matrix_profile_released", matrix::kSelectedPayloadMatrixProfileReleased},
        {"trace_signature_algorithm", matrix::kTraceSignatureAlgorithm},
        {"master_trace_world_count", 256},
        {"master_trace_signature", trace_digest(make_trace(256))},
        {"world_counts", args.world_counts},
        {"modes", std::move(mode_rows)},
        {"protocol",
         {{"cold_samples", args.protocol.cold_samples},
          {"warmup_windows", args.protocol.warmup_windows},
          {"measured_windows", args.protocol.measured_windows},
          {"rollout_samples", args.protocol.rollout_samples},
          {"rollout_windows", args.protocol.rollout_windows},
          {"percentile_method", "nearest_rank"},
          {"latency_clock", "steady_clock"},
          {"cold_semantics", "same_backend_reset_setup_then_first_window"},
          {"fresh_process_cold_available", false}}},
        {"lane_configuration", lane_configuration},
        {"cuda_environment", environment},
        {"rows", std::move(rows)},
        {"gates",
         {{"cr2_4b_selected_payload_parity_required", true},
          {"cr2_5_achieved_counter_gate_complete", false},
          {"matrix_evidence_complete", false},
          {"maintained_claim_allowed", false},
          {"public_support_enabled", false},
          {"promotion_allowed", false},
          {"tuning_authorized", false}}},
    };
}

} // namespace

int main(int argc, char **argv) {
    try {
#if defined(EF_CR2_MATRIX_CPU_PROBE)
        spdlog::set_level(spdlog::level::warn);
#endif
        const Args args = args_from_command_line(argc, argv);
        const Json report = run_probe(args);
        if (args.output_path.empty()) {
            std::cout << report.dump(2) << '\n';
        } else {
            std::ofstream output(args.output_path, std::ios::binary | std::ios::trunc);
            if (!output) throw std::runtime_error("CR2 matrix output path could not be opened");
            output << report.dump(2) << '\n';
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "CR2 matrix probe failed: " << error.what() << '\n';
        return 2;
    }
}
