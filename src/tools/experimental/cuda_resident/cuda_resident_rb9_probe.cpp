#include "runtime/contracts/cuda_resident_performance_contract.h"
#include "runtime/contracts/cuda_resident_replay_contract.h"
#include "runtime/contracts/cuda_resident_device_consumer_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"
#include "tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.h"

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

#if defined(EF_RB9_CPU_PROBE) && defined(EF_RB9_CUDA_PROBE)
#error "RB9 probe must select exactly one lane"
#elif defined(EF_RB9_CUDA_PROBE)
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#include <cuda_runtime_api.h>
#elif !defined(EF_RB9_CPU_PROBE)
#error "RB9 probe lane is not configured"
#endif

#ifndef EF_RB9_BUILD_CONFIG
#define EF_RB9_BUILD_CONFIG "unknown"
#endif

namespace {

using Clock = std::chrono::steady_clock;
using Json = nlohmann::json;
using runtime::cuda_resident::performance::probe::Mode;
using runtime::cuda_resident::performance::probe::ProbeSession;
using runtime::cuda_resident::performance::probe::WindowTiming;
using runtime::cuda_resident::replay::CudaResidentReplayHarness;
using runtime::cuda_resident::replay::ReplayActionWindow;
using runtime::cuda_resident::replay::ReplayTrace;

struct Args {
    std::vector<std::size_t> world_counts = {1, 4, 16, 64, 256};
    std::size_t cold_samples = 50;
    std::size_t warmup_windows = 32;
    std::size_t measured_windows = 200;
    std::size_t rollout_samples = 30;
    std::size_t rollout_windows = 128;
    std::string database_path = "examples/config/database";
    std::string output_path;
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
        const std::string token(value.substr(begin, comma == std::string_view::npos
                                                        ? value.size() - begin
                                                        : comma - begin));
        counts.push_back(parse_positive_size(token.c_str(), "--worlds"));
        if (comma == std::string_view::npos) break;
        begin = comma + 1;
    }
    if (counts.empty()) throw std::invalid_argument("--worlds must not be empty");
    if (!std::is_sorted(counts.begin(), counts.end()) ||
        std::adjacent_find(counts.begin(), counts.end()) != counts.end()) {
        throw std::invalid_argument("--worlds must be unique and ascending");
    }
    return counts;
}

Args parse_args(int argc, char **argv) {
    Args args{};
    for (int index = 1; index < argc; ++index) {
        const std::string flag = argv[index];
        const auto require_value = [&](const char *label) -> const char * {
            if (index + 1 >= argc) {
                throw std::invalid_argument(std::string("missing value for ") + label);
            }
            return argv[++index];
        };
        if (flag == "--worlds") {
            args.world_counts = parse_world_counts(require_value("--worlds"));
        } else if (flag == "--cold-samples") {
            args.cold_samples = parse_positive_size(require_value("--cold-samples"), flag.c_str());
        } else if (flag == "--warmup") {
            args.warmup_windows = parse_positive_size(require_value("--warmup"), flag.c_str());
        } else if (flag == "--samples") {
            args.measured_windows = parse_positive_size(require_value("--samples"), flag.c_str());
        } else if (flag == "--rollouts") {
            args.rollout_samples = parse_positive_size(require_value("--rollouts"), flag.c_str());
        } else if (flag == "--rollout-windows") {
            args.rollout_windows =
                parse_positive_size(require_value("--rollout-windows"), flag.c_str());
        } else if (flag == "--database") {
            args.database_path = require_value("--database");
        } else if (flag == "--output") {
            args.output_path = require_value("--output");
        } else if (flag == "--smoke") {
            args.cold_samples = 1;
            args.warmup_windows = 1;
            args.measured_windows = 3;
            args.rollout_samples = 1;
            args.rollout_windows = 2;
        } else if (flag == "--help" || flag == "-h") {
            std::cout
                << "Usage: RB9 probe [options]\n"
                << "  --worlds 1,4,16,64,256\n"
                << "  --cold-samples N       reset/setup first-window samples (default 50)\n"
                << "  --warmup N             warmup windows (default 32)\n"
                << "  --samples N            measured warm windows (default 200)\n"
                << "  --rollouts N           independent rollout samples (default 30)\n"
                << "  --rollout-windows N    windows per rollout (default 128)\n"
                << "  --database PATH        CPU database path\n"
                << "  --output PATH          JSON output (stdout when omitted)\n"
                << "  --smoke                minimal validation protocol\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown flag: " + flag);
        }
    }
    return args;
}

ReplayTrace make_trace(std::size_t world_count) {
    ReplayTrace trace{
        .run_id = "rb9.production_shaped.fixed_air",
        .seeds = {},
        .spawns = {},
        .time_steps = {},
        .windows = {},
    };
    trace.seeds.reserve(world_count);
    trace.spawns.reserve(world_count);
    trace.time_steps.reserve(world_count);
    ReplayActionWindow actions{
        .actions = {},
        .request_id = "rb9.window",
    };
    actions.actions.reserve(world_count);
    for (std::size_t world = 0; world < world_count; ++world) {
        trace.seeds.push_back(static_cast<std::uint32_t>(1009 + world * 17));
        trace.time_steps.push_back(0.001 + static_cast<double>(world % 3) * 0.0001);
        trace.spawns.push_back({
            .world_index = world,
            .type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName),
            .entity_name = "RB9Perf" + std::to_string(world),
            .is_agent = true,
            .x = 1000.0 + static_cast<double>(world % 32) * 25.0,
            .y = static_cast<double>(world / 32) * 20.0,
            .z = 1500.0 + static_cast<double>(world % 7),
            .heading = 90.0,
            .pitch = 0.0,
            .roll = 0.0,
            .vx = 200.0 + static_cast<double>(world % 5),
            .vy = 0.0,
            .vz = 0.0,
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


Json statistics_json(const std::vector<double> &samples) {
    if (samples.empty()) return nullptr;
    std::vector<double> sorted = samples;
    std::sort(sorted.begin(), sorted.end());
    const auto nearest_rank = [&](double percentile) {
        const double rank = std::ceil(percentile * static_cast<double>(sorted.size()));
        const std::size_t index = static_cast<std::size_t>(std::max(1.0, rank)) - 1;
        return sorted[std::min(index, sorted.size() - 1)];
    };
    const double total = std::accumulate(sorted.begin(), sorted.end(), 0.0);
    return {
        {"sample_count", sorted.size()},
        {"p50_ms", nearest_rank(0.50)},
        {"p95_ms", nearest_rank(0.95)},
        {"min_ms", sorted.front()},
        {"max_ms", sorted.back()},
        {"mean_ms", total / static_cast<double>(sorted.size())},
        {"raw_ms", sorted},
    };
}

#if defined(EF_RB9_CUDA_PROBE)
Json ledger_json(const runtime::cuda_resident::performance::WindowTransferLedger &ledger) {
    return {
        {"source", "static_operation_ledger_validated_against_cuda_world_store_split.v1"},
        {"h2d_copy_count", ledger.h2d_copy_count},
        {"h2d_bytes", ledger.h2d_bytes},
        {"d2h_copy_count", ledger.d2h_copy_count},
        {"d2h_bytes", ledger.d2h_bytes},
        {"d2d_copy_count", ledger.d2d_copy_count},
        {"d2d_bytes", ledger.d2d_bytes},
        {"kernel_launch_count", ledger.kernel_launch_count},
        {"synchronization_count", ledger.synchronization_count},
        {"device_observation_pack_bytes", ledger.device_observation_pack_bytes},
        {"device_observation_consumer_bytes", ledger.device_observation_consumer_bytes},
        {"device_observation_view_bytes", ledger.device_observation_view_bytes},
        {"device_consumer_measured_path_d2h_copy_count",
         ledger.device_consumer_measured_path_d2h_copy_count},
        {"device_consumer_diagnostic_d2h_copy_count",
         ledger.device_consumer_diagnostic_d2h_copy_count},
        {"device_consumer_event_wait_count", ledger.device_consumer_event_wait_count},
        {"host_snapshot_includes_full_state_d2h",
         ledger.host_snapshot_includes_full_state_d2h},
        {"device_consumer_includes_host_validation_d2h",
         ledger.device_consumer_includes_host_validation_d2h},
        {"device_consumer_allocation_may_synchronize",
         ledger.device_consumer_allocation_may_synchronize},
        {"device_consumer_release_outside_measured_path",
         ledger.device_consumer_release_outside_measured_path},
    };
}
#endif

Json run_row(const Args &args, std::size_t world_count, const Mode &mode) {
    const ReplayTrace trace = make_trace(world_count);
    Json row = {
        {"world_count", world_count},
        {"mode_id", mode.id},
        {"host_snapshot", mode.host_snapshot},
        {"device_consumer", mode.device_consumer},
        {"trace_signature", CudaResidentReplayHarness::trace_signature(trace)},
        {"master_trace_prefix_world_count", 256},
        {"available", true},
        {"unavailable_reason", ""},
        {"learner_equivalent", false},
        {"device_consumer_validation_boundary",
         mode.device_consumer ? "deferred_after_sample_timer" : "not_applicable"},
        {"parity_status", "rb8_selected_slice_quarantined"},
        {"promotion_eligible", false},
    };

#if defined(EF_RB9_CPU_PROBE)
    if (mode.device_consumer) {
        row["available"] = false;
        row["unavailable_reason"] = "cpu_reference_has_no_device_observation_consumer";
        row["latency"] = nullptr;
        row["device_memory"] = {
            {"availability", "not_applicable"},
            {"resident_bytes", nullptr},
            {"peak_candidate_requested_bytes", nullptr},
        };
        row["operation_ledger"] = {
            {"source", "not_applicable_cpu_reference"},
            {"h2d_copy_count", nullptr},
            {"d2h_copy_count", nullptr},
            {"d2d_copy_count", nullptr},
            {"kernel_launch_count", nullptr},
            {"synchronization_count", nullptr},
        };
        return row;
    }
#endif

    std::vector<double> setup_samples;
    std::vector<double> cold_total_samples;
    std::vector<double> cold_window_samples;
    ProbeSession cold_session(trace, args.database_path);
    for (std::size_t sample = 0; sample < args.cold_samples; ++sample) {
        const auto total_begin = Clock::now();
        cold_session.reset_fixture();
        setup_samples.push_back(cold_session.setup_ms());
        const WindowTiming timing = cold_session.run_window(mode);
        cold_window_samples.push_back(timing.end_to_end_ms);
        cold_total_samples.push_back(elapsed_ms(total_begin, Clock::now()));
        cold_session.validate_pending_device_consumers();
    }

    ProbeSession warmed(trace, args.database_path);
#if defined(EF_RB9_CUDA_PROBE)
    const std::size_t device_bytes = warmed.device_bytes();
    const std::size_t state_slot_bytes = warmed.state_slot_bytes();
#endif
    for (std::size_t window = 0; window < args.warmup_windows; ++window) {
        (void)warmed.run_window(mode);
        warmed.validate_pending_device_consumers();
    }
    std::vector<double> end_to_end_samples;
    std::vector<double> advance_samples;
    std::vector<double> collection_samples;
    end_to_end_samples.reserve(args.measured_windows);
    advance_samples.reserve(args.measured_windows);
    collection_samples.reserve(args.measured_windows);
    for (std::size_t window = 0; window < args.measured_windows; ++window) {
        const WindowTiming timing = warmed.run_window(mode);
        end_to_end_samples.push_back(timing.end_to_end_ms);
        advance_samples.push_back(timing.advance_ms);
        collection_samples.push_back(timing.collection_ms);
        warmed.validate_pending_device_consumers();
    }

    std::vector<double> rollout_samples;
    rollout_samples.reserve(args.rollout_samples);
    ProbeSession rollout_session(trace, args.database_path);
    for (std::size_t rollout = 0; rollout < args.rollout_samples; ++rollout) {
        rollout_session.reset_fixture();
        const auto begin = Clock::now();
        for (std::size_t window = 0; window < args.rollout_windows; ++window) {
            (void)rollout_session.run_window(mode);
        }
        rollout_samples.push_back(elapsed_ms(begin, Clock::now()));
        rollout_session.validate_pending_device_consumers();
    }

    ProbeSession deterministic(trace, args.database_path);
    deterministic.reset_fixture();
    (void)deterministic.run_window(mode);
    deterministic.validate_pending_device_consumers();
    const std::string first_digest = deterministic.state_digest();
    deterministic.reset_fixture();
    (void)deterministic.run_window(mode);
    deterministic.validate_pending_device_consumers();
    const std::string second_digest = deterministic.state_digest();

    row["latency"] = {
        {"setup", statistics_json(setup_samples)},
        {"cold_reset_setup_plus_first_window", statistics_json(cold_total_samples)},
        {"cold_first_window", statistics_json(cold_window_samples)},
        {"warmed_end_to_end", statistics_json(end_to_end_samples)},
        {"warmed_advance", statistics_json(advance_samples)},
        {"warmed_collection", statistics_json(collection_samples)},
        {"rollout_total", statistics_json(rollout_samples)},
        {"rollout_windows", args.rollout_windows},
    };
    row["determinism"] = {
        {"checked", true},
        {"matched", first_digest == second_digest},
        {"first_digest", first_digest},
        {"second_digest", second_digest},
        {"scope", "identity_inclusive_reset_diagnostic"},
        {"identity_inclusive", true},
        {"mismatch_reason", first_digest == second_digest
                                 ? "none"
                                 : "reset_allocates_fresh_entity_ids"},
    };

#if defined(EF_RB9_CUDA_PROBE)
    const auto ledger = runtime::cuda_resident::performance::modeled_window_ledger(
        world_count, state_slot_bytes, mode.host_snapshot, mode.device_consumer);
    row["operation_ledger"] = ledger_json(ledger);
    row["device_memory"] = {
        {"availability", "candidate_owned_requested_bytes"},
        {"resident_bytes", device_bytes},
        {"state_slot_bytes", state_slot_bytes},
        {"peak_candidate_requested_bytes",
         device_bytes +
             (mode.device_consumer ? args.rollout_windows : std::size_t{1}) *
                 (ledger.device_observation_view_bytes +
                  ledger.device_observation_consumer_bytes)},
        {"deferred_device_consumer_receipts",
         mode.device_consumer ? args.rollout_windows : std::size_t{0}},
    };
#else
    row["operation_ledger"] = {
        {"source", "not_applicable_cpu_reference"},
        {"h2d_copy_count", nullptr},
        {"d2h_copy_count", nullptr},
        {"d2d_copy_count", nullptr},
        {"kernel_launch_count", nullptr},
        {"synchronization_count", nullptr},
    };
    row["device_memory"] = {
        {"availability", "not_applicable"},
        {"resident_bytes", nullptr},
        {"peak_candidate_requested_bytes", nullptr},
    };
#endif
    return row;
}

#if defined(EF_RB9_CUDA_PROBE)

Json kernel_resource_json(std::string_view kernel_id,
                          const runtime::cuda_resident::CudaBarrierKernelResources &resources) {
    return {
        {"kernel_id", kernel_id},
        {"registers_per_thread", resources.registers_per_thread},
        {"local_bytes_per_thread", resources.local_bytes_per_thread},
        {"static_shared_bytes", resources.static_shared_bytes},
        {"threads_per_block", resources.threads_per_block},
        {"active_blocks_per_multiprocessor", resources.active_blocks_per_multiprocessor},
        {"active_warps_per_multiprocessor", resources.active_warps_per_multiprocessor},
        {"theoretical_occupancy", resources.theoretical_occupancy},
        {"spill_loads", nullptr},
        {"spill_stores", nullptr},
        {"spill_availability", "release_ptxas_log_required"},
    };
}

Json cuda_kernel_resources() {
    using runtime::cuda_resident::testing::CudaWorldStoreTestAccess;
    return Json::array({
        kernel_resource_json("apply_barrier",
                             CudaWorldStoreTestAccess::barrier_kernel_resources()),
        kernel_resource_json("phase_a_controls",
                             CudaWorldStoreTestAccess::phase_a_kernel_resources()),
        kernel_resource_json("phase_b_forces",
                             CudaWorldStoreTestAccess::phase_b_forces_kernel_resources()),
        kernel_resource_json("phase_b_aerodynamics",
                             CudaWorldStoreTestAccess::phase_b_aerodynamics_kernel_resources()),
        kernel_resource_json("phase_b_integrate",
                             CudaWorldStoreTestAccess::phase_b_integrate_kernel_resources()),
        kernel_resource_json("phase_d_instruments",
                             CudaWorldStoreTestAccess::phase_d_instruments_kernel_resources()),
        kernel_resource_json("phase_d_configuration",
                             CudaWorldStoreTestAccess::phase_d_configuration_kernel_resources()),
        kernel_resource_json("phase_d_projection",
                             CudaWorldStoreTestAccess::phase_d_projection_kernel_resources()),
        kernel_resource_json("phase_d_pack",
                             CudaWorldStoreTestAccess::phase_d_pack_kernel_resources()),
        kernel_resource_json("phase_d_consumer",
                             CudaWorldStoreTestAccess::phase_d_consumer_kernel_resources()),
    });
}

Json cuda_environment() {
    int device = 0;
    cudaDeviceProp properties{};
    int driver_version = 0;
    int runtime_version = 0;
    if (cudaGetDevice(&device) != cudaSuccess ||
        cudaGetDeviceProperties(&properties, device) != cudaSuccess ||
        cudaDriverGetVersion(&driver_version) != cudaSuccess ||
        cudaRuntimeGetVersion(&runtime_version) != cudaSuccess) {
        throw std::runtime_error("RB9 CUDA environment query failed");
    }
    return {
        {"device_name", properties.name},
        {"compute_capability", std::to_string(properties.major) + "." +
                                   std::to_string(properties.minor)},
        {"total_global_memory_bytes", properties.totalGlobalMem},
        {"driver_version", driver_version},
        {"runtime_version", runtime_version},
    };
}

#endif

Json run_probe(const Args &args) {
    const std::vector<Mode> modes = {
        {.host_snapshot = false, .device_consumer = false, .id = "no_export_no_device"},
        {.host_snapshot = true, .device_consumer = false, .id = "host_export_no_device"},
        {.host_snapshot = false, .device_consumer = true, .id = "no_export_device_consumer"},
        {.host_snapshot = true, .device_consumer = true, .id = "host_export_device_consumer"},
    };

#if defined(EF_RB9_CPU_PROBE)
    const std::string lane = "flecs_cpu_reference";
    const std::string invocation_surface = "backend_spi_world_batch";
    constexpr bool learner_facing_device_lease_available = false;
#else
    const std::string lane = "cuda_resident";
    const std::string invocation_surface =
        std::string(runtime::cuda_resident::performance::kCudaResidentPerformanceInvocationSurface);
    constexpr bool learner_facing_device_lease_available = true;
#endif

    Json report = {
        {"schema_version",
         runtime::cuda_resident::performance::kCudaResidentPerformanceSchemaV1},
        {"harness_id", runtime::cuda_resident::performance::kCudaResidentPerformanceHarnessId},
        {"profile_id", runtime::cuda_resident::performance::kCudaResidentPerformanceProfileId},
        {"parity_budget_ref",
         runtime::cuda_resident::performance::kCudaResidentPerformanceBudgetRef},
        {"lane", lane},
        {"invocation_surface", invocation_surface},
        {"trace_signature_algorithm", "rb8_canonical_trace_v1"},
        {"build_config", EF_RB9_BUILD_CONFIG},
        {"full_facade_available", false},
        {"complete_rollout_collection_available", true},
        {"learner_consumption_available", false},
        {"learner_facing_device_lease_available", learner_facing_device_lease_available},
        {"device_consumer_contract_id",
         learner_facing_device_lease_available
             ? Json(std::string(runtime::cuda_resident::device_consumer::
                                   kCudaResidentDeviceConsumerSurfaceV1))
             : Json(nullptr)},
        {"maintained_claim", false},
        {"promotion_allowed", false},
        {"required_metrics_complete", false},
        {"break_even_eligible", false},
        {"world_counts", args.world_counts},
        {"master_trace_signature",
         CudaResidentReplayHarness::trace_signature(make_trace(256))},
        {"protocol",
         {
             {"cold_samples", args.cold_samples},
             {"warmup_windows", args.warmup_windows},
             {"measured_windows", args.measured_windows},
             {"rollout_samples", args.rollout_samples},
             {"rollout_windows", args.rollout_windows},
             {"percentile_method", "nearest_rank"},
             {"latency_clock", "steady_clock"},
             {"cold_semantics", "same_backend_reset_setup_then_first_window"},
             {"fresh_process_cold_available", false},
         }},
        {"hold_reasons",
         Json::array({"cuda_candidate_not_on_full_runtime_facade_window",
                      "learner_consumption_unavailable",
                      "achieved_gpu_counters_unavailable:ERR_NVGPUCTRPERM",
                      "identity_inclusive_reset_determinism_is_diagnostic"})},
        {"rows", Json::array()},
    };

#if defined(EF_RB9_CUDA_PROBE)
    report["cuda_environment"] = cuda_environment();
    report["kernel_resources"] = cuda_kernel_resources();
    report["achieved_hardware_counters"] = {
        {"availability", "unavailable"},
        {"reason",
         runtime::cuda_resident::performance::kCudaResidentPerformanceUnavailableCountersReason},
        {"achieved_occupancy", nullptr},
        {"branch_divergence", nullptr},
        {"global_memory_traffic", nullptr},
        {"local_memory_traffic", nullptr},
        {"shared_memory_traffic", nullptr},
    };
#else
    report["cuda_environment"] = nullptr;
    report["cpu_worker_threads_request"] = 0;
    report["cpu_worker_threads_semantics"] = "auto";
    report["kernel_resources"] = Json::array();
    report["achieved_hardware_counters"] = {
        {"availability", "not_applicable"},
        {"reason", "cpu_reference_lane"},
        {"achieved_occupancy", nullptr},
        {"branch_divergence", nullptr},
        {"global_memory_traffic", nullptr},
        {"local_memory_traffic", nullptr},
        {"shared_memory_traffic", nullptr},
    };
#endif

    for (const std::size_t world_count : args.world_counts) {
        for (const Mode &mode : modes) {
            report["rows"].push_back(run_row(args, world_count, mode));
        }
    }
    return report;
}

} // namespace

int main(int argc, char **argv) {
    try {
        const Args args = parse_args(argc, argv);
        const Json report = run_probe(args);
        const std::string output = report.dump(2) + "\n";
        if (args.output_path.empty()) {
            std::cout << output;
        } else {
            std::ofstream stream(args.output_path, std::ios::binary | std::ios::trunc);
            if (!stream) throw std::runtime_error("could not open RB9 output path");
            stream << output;
            if (!stream) throw std::runtime_error("could not write RB9 output path");
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "RB9 probe failed: " << error.what() << '\n';
        return 1;
    }
}
