#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <cuda_profiler_api.h>
#include <cuda_runtime_api.h>
#include <nlohmann/json.hpp>

#include "runtime/contracts/cuda_resident_resource_evidence_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_device_consumer.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

#ifndef EF_CR2_RESOURCE_BUILD_CONFIG
#define EF_CR2_RESOURCE_BUILD_CONFIG "unknown"
#endif

namespace {

namespace evidence = runtime::cuda_resident::resource_evidence;
namespace replay = runtime::cuda_resident::replay;
using Json = nlohmann::json;
using runtime::cuda_resident::CudaBarrierKernelResources;
using runtime::cuda_resident::CudaResidentBackend;
using runtime::cuda_resident::CudaResidentDeviceConsumer;
using runtime::cuda_resident::replay::CudaResidentReplayHarness;
using runtime::cuda_resident::testing::CudaWorldStoreTestAccess;

struct Args {
    std::string output_path;
};

void require_cuda(cudaError_t status, std::string_view operation) {
    if (status != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(status));
    }
}

class ProfilerRange final {
  public:
    ProfilerRange() {
        require_cuda(cudaProfilerStart(), "cudaProfilerStart");
        active_ = true;
    }

    ~ProfilerRange() {
        if (active_) (void)cudaProfilerStop();
    }

    ProfilerRange(const ProfilerRange &) = delete;
    ProfilerRange &operator=(const ProfilerRange &) = delete;

    void stop() {
        require_cuda(cudaProfilerStop(), "cudaProfilerStop");
        active_ = false;
    }

  private:
    bool active_ = false;
};

Args parse_args(int argc, char **argv) {
    Args args{};
    for (int index = 1; index < argc; ++index) {
        const std::string_view flag(argv[index]);
        if (flag == "--output" && index + 1 < argc) {
            args.output_path = argv[++index];
        } else if (flag == "--help" || flag == "-h") {
            std::cout << "Usage: CUDA resident resource probe [--output PATH]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("usage: CUDA resident resource probe [--output PATH]");
        }
    }
    return args;
}

replay::ReplayTrace make_trace() {
    replay::ReplayTrace trace{
        .run_id = "cr2.resource.steady_full_window_body.sm86",
    };
    trace.seeds.reserve(evidence::kWorldCount);
    trace.spawns.reserve(evidence::kWorldCount);
    trace.time_steps.reserve(evidence::kWorldCount);
    replay::ReplayActionWindow actions{.request_id = "cr2.resource.window.0"};
    actions.actions.reserve(evidence::kWorldCount);

    for (std::size_t world = 0; world < evidence::kWorldCount; ++world) {
        trace.seeds.push_back(static_cast<std::uint32_t>(1009 + world * 17));
        trace.time_steps.push_back(0.001 + static_cast<double>(world % 3) * 0.0001);
        trace.spawns.push_back({
            .world_index = world,
            .type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName),
            .entity_name = "CR2Resource" + std::to_string(world),
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

std::vector<WorldPilotActionAssignment>
make_assignments(const replay::ReplayTrace &trace, const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> assignments;
    assignments.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        assignments.push_back({
            .world_index = world,
            .entity_id = entity_ids[world],
            .action = trace.windows.front().actions[world],
        });
    }
    return assignments;
}

std::vector<WorldEntityRef> make_refs(const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldEntityRef> refs;
    refs.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        refs.push_back({.world_index = world, .entity_id = entity_ids[world]});
    }
    return refs;
}

Json resource_json(std::string_view kernel_id, const CudaBarrierKernelResources &resources) {
    return {
        {"kernel_id", kernel_id},
        {"registers_per_thread", resources.registers_per_thread},
        {"local_bytes_per_thread", resources.local_bytes_per_thread},
        {"static_shared_bytes", resources.static_shared_bytes},
        {"threads_per_block", resources.threads_per_block},
        {"active_blocks_per_multiprocessor", resources.active_blocks_per_multiprocessor},
        {"active_warps_per_multiprocessor", resources.active_warps_per_multiprocessor},
        {"theoretical_occupancy", resources.theoretical_occupancy},
    };
}

Json query_kernel_resources() {
    return Json::array({
        resource_json("apply_barrier", CudaWorldStoreTestAccess::barrier_kernel_resources()),
        resource_json("phase_a_controls", CudaWorldStoreTestAccess::phase_a_kernel_resources()),
        resource_json("phase_b_forces",
                      CudaWorldStoreTestAccess::phase_b_forces_kernel_resources()),
        resource_json("phase_b_aerodynamics",
                      CudaWorldStoreTestAccess::phase_b_aerodynamics_kernel_resources()),
        resource_json("phase_b_integrate",
                      CudaWorldStoreTestAccess::phase_b_integrate_kernel_resources()),
        resource_json("phase_d_instruments",
                      CudaWorldStoreTestAccess::phase_d_instruments_kernel_resources()),
        resource_json("phase_d_configuration",
                      CudaWorldStoreTestAccess::phase_d_configuration_kernel_resources()),
        resource_json("phase_d_projection",
                      CudaWorldStoreTestAccess::phase_d_projection_kernel_resources()),
        resource_json("phase_d_pack", CudaWorldStoreTestAccess::phase_d_pack_kernel_resources()),
        resource_json("phase_d_consumer",
                      CudaWorldStoreTestAccess::phase_d_consumer_kernel_resources()),
    });
}

Json cuda_environment() {
    int device = 0;
    int driver_version = 0;
    int runtime_version = 0;
    cudaDeviceProp properties{};
    require_cuda(cudaGetDevice(&device), "cudaGetDevice");
    require_cuda(cudaGetDeviceProperties(&properties, device), "cudaGetDeviceProperties");
    require_cuda(cudaDriverGetVersion(&driver_version), "cudaDriverGetVersion");
    require_cuda(cudaRuntimeGetVersion(&runtime_version), "cudaRuntimeGetVersion");
    return {
        {"device_ordinal", device},
        {"device_name", properties.name},
        {"compute_capability",
         std::to_string(properties.major) + "." + std::to_string(properties.minor)},
        {"driver_version", driver_version},
        {"runtime_version", runtime_version},
    };
}

std::string fnv1a64(std::string_view value) {
    std::uint64_t digest = 14695981039346656037ULL;
    for (const unsigned char byte : value) {
        digest ^= byte;
        digest *= 1099511628211ULL;
    }
    std::ostringstream output;
    output << std::hex << std::setfill('0') << std::setw(16) << digest;
    return output.str();
}

Json run_probe() {
    const replay::ReplayTrace trace = make_trace();
    const std::string trace_signature = CudaResidentReplayHarness::trace_signature(trace);
    const std::string trace_digest = fnv1a64(trace_signature);
    if (trace_signature.size() != evidence::kTraceSignatureBytes ||
        trace_digest != evidence::kTraceSignatureDigest) {
        throw std::runtime_error("resource probe trace contract drifted");
    }
    CudaResidentBackend backend;
    CudaResidentDeviceConsumer consumer;
    backend.configure({.world_count = evidence::kWorldCount});
    const auto setup = backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = trace.seeds,
        .spawn_requests = trace.spawns,
        .time_steps = trace.time_steps,
    });
    if (setup.entity_ids.size() != evidence::kWorldCount) {
        throw std::runtime_error("resource probe setup cardinality mismatch");
    }

    const auto assignments = make_assignments(trace, setup.entity_ids);
    const auto refs = make_refs(setup.entity_ids);
    const Json resources = query_kernel_resources();
    const Json environment = cuda_environment();

    runtime::backend::ExportResult exported;
    runtime::cuda_resident::device_consumer::AcquireResult acquired;
    runtime::cuda_resident::device_consumer::SubmitResult submitted;
    {
        ProfilerRange capture;
        backend.inject({.pilot_actions = assignments});
        const auto evaluated = backend.evaluate({});
        if (!evaluated.execution_episode_products.empty()) {
            throw std::runtime_error("resource probe evaluation must remain empty");
        }
        backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
        exported = backend.export_state({
            .refs = refs,
            .include_agent_observations = true,
            .include_instrument_states = true,
        });
        acquired = backend.acquire_device_observation_lease("cr2.resource.lease");
        if (!acquired.success()) {
            throw std::runtime_error("resource probe lease acquisition failed: " + acquired.detail);
        }
        submitted = consumer.submit(acquired.lease, {.request_id = "cr2.resource.consumer",
                                                     .expected_epoch = acquired.lease.epoch});
        if (!submitted.success()) {
            throw std::runtime_error("resource probe consumer submit failed: " + submitted.detail);
        }
        const auto waited = consumer.await(submitted.receipt);
        if (!waited.success()) {
            throw std::runtime_error("resource probe consumer wait failed: " + waited.detail);
        }
        capture.stop();
    }

    if (exported.agent_observations.size() != evidence::kWorldCount ||
        exported.instrument_states.size() != evidence::kWorldCount ||
        submitted.receipt.world_count != evidence::kWorldCount) {
        throw std::runtime_error("resource probe captured payload cardinality mismatch");
    }
    const auto diagnostics = backend.diagnostics();
    return {
        {"schema_version", evidence::kProbeSchemaV1},
        {"profile_id", evidence::kProfileId},
        {"build_config", EF_CR2_RESOURCE_BUILD_CONFIG},
        {"cuda_architecture", evidence::kCudaArchitecture},
        {"trace_signature_algorithm", evidence::kTraceSignatureAlgorithm},
        {"trace_signature_digest", trace_digest},
        {"trace_signature_bytes", trace_signature.size()},
        {"world_count", evidence::kWorldCount},
        {"window_count", 1},
        {"threads_per_block", evidence::kThreadsPerBlock},
        {"blocks", evidence::kBlocks},
        {"backend_id", diagnostics.backend_id},
        {"cuda_environment", environment},
        {"runtime_kernel_resources", resources},
        {"capture",
         {
             {"range", evidence::kCaptureRange},
             {"setup_outside", evidence::kSetupOutsideCapture},
             {"resource_queries_outside", true},
             {"public_export_inside", evidence::kPublicExportInsideCapture},
             {"device_consumer_inside", evidence::kDeviceConsumerInsideCapture},
             {"diagnostic_materialization_inside",
              evidence::kDiagnosticMaterializationInsideCapture},
             {"operation_sequence",
              Json::array({"inject", "evaluate_empty", "advance_world_batch", "public_export",
                           "acquire_device_lease", "consumer_submit", "consumer_event_await"})},
         }},
        {"result",
         {
             {"agent_observation_count", exported.agent_observations.size()},
             {"instrument_state_count", exported.instrument_states.size()},
             {"consumer_world_count", submitted.receipt.world_count},
             {"consumer_await_completed", true},
             {"diagnostic_materialization_called", false},
         }},
        {"maintained_claim_allowed", evidence::kMaintainedClaimAllowed},
        {"public_support_enabled", evidence::kPublicSupportEnabled},
        {"promotion_allowed", evidence::kPromotionAllowed},
        {"tuning_authorized", evidence::kTuningAuthorized},
    };
}

void write_report(const Json &report, const std::string &output_path) {
    if (output_path.empty()) {
        std::cout << report.dump(2) << '\n';
        return;
    }
    std::ofstream output(output_path, std::ios::binary | std::ios::trunc);
    if (!output) throw std::runtime_error("failed to open resource probe output");
    output << report.dump(2) << '\n';
    if (!output) throw std::runtime_error("failed to write resource probe output");
}

} // namespace

int main(int argc, char **argv) {
    try {
        const Args args = parse_args(argc, argv);
        write_report(run_probe(), args.output_path);
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "CUDA resident resource probe failed: " << error.what() << '\n';
        return 1;
    }
}
