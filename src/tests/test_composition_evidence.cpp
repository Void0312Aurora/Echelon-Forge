#include <doctest/doctest.h>

#include "runtime/contracts/composition/runtime_composition_evidence.v1.generated.h"
#include "runtime/contracts/runtime_composition_evidence_contract.h"
#include "runtime/facade/runtime_facade.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <psapi.h>
#pragma comment(lib, "psapi.lib")
#elif defined(__linux__)
#if defined(__GLIBC__)
#include <malloc.h>
#endif
#elif defined(__APPLE__)
#include <mach/mach.h>
#include <sys/resource.h>
#endif

namespace {

namespace evidence = runtime::composition_evidence_contracts;
namespace generated = runtime::composition_evidence_contracts::generated;
using Json = nlohmann::json;
using SteadyClock = std::chrono::steady_clock;

constexpr std::size_t kParitySemanticWorldCount = 2;
constexpr std::size_t kParitySemanticSteps = 3;
constexpr std::size_t kParityMeasurementWorldCount = 32;
constexpr std::size_t kParityWarmupSteps = 3;
constexpr std::size_t kParityMeasurementSteps = 20;
constexpr std::size_t kParityResetIterations = 5;
constexpr std::uint32_t kParitySeedBase = 42;
constexpr double kParityTimeStepS = 0.05;

Json read_fixture(std::string_view name) {
    const std::filesystem::path path = std::filesystem::path(EF_SOURCE_ROOT) / "tests" /
                                       "architecture" / "composition" / "fixtures" / name;
    std::ifstream stream(path);
    REQUIRE_MESSAGE(stream.good(), "failed to open evidence fixture: ", path.string());
    return Json::parse(stream);
}

bool has_mismatch(const RuntimeCompositionEvidenceComparison &comparison,
                  std::string_view expected) {
    return std::find(comparison.mismatches.begin(), comparison.mismatches.end(), expected) !=
           comparison.mismatches.end();
}

double elapsed_ms(const SteadyClock::time_point start) {
    return std::chrono::duration<double, std::milli>(SteadyClock::now() - start).count();
}

void trim_process_allocator() {
#if defined(__GLIBC__)
    // Normalize retained free glibc arenas out of the live-memory sample. The
    // trim is measurement-only and deliberately excluded from teardown timing.
    malloc_trim(0);
#endif
}

std::uint64_t current_rss_bytes() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS_EX counters{};
    counters.cb = sizeof(counters);
    if (GetProcessMemoryInfo(GetCurrentProcess(),
                             reinterpret_cast<PROCESS_MEMORY_COUNTERS *>(&counters),
                             sizeof(counters)) == 0) {
        return 0;
    }
    return static_cast<std::uint64_t>(counters.WorkingSetSize);
#elif defined(__linux__)
    std::ifstream stream("/proc/self/status");
    std::string label;
    while (stream >> label) {
        if (label == "VmRSS:") {
            std::uint64_t kibibytes = 0;
            stream >> kibibytes;
            return stream.fail() ? 0 : kibibytes * 1024U;
        }
        stream.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    }
    return 0;
#elif defined(__APPLE__)
    mach_task_basic_info info{};
    mach_msg_type_number_t count = MACH_TASK_BASIC_INFO_COUNT;
    return task_info(mach_task_self(), MACH_TASK_BASIC_INFO, reinterpret_cast<task_info_t>(&info),
                     &count) == KERN_SUCCESS
               ? static_cast<std::uint64_t>(info.resident_size)
               : 0;
#else
    return 0;
#endif
}

std::uint64_t peak_rss_bytes() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS_EX counters{};
    counters.cb = sizeof(counters);
    if (GetProcessMemoryInfo(GetCurrentProcess(),
                             reinterpret_cast<PROCESS_MEMORY_COUNTERS *>(&counters),
                             sizeof(counters)) == 0) {
        return 0;
    }
    return static_cast<std::uint64_t>(counters.PeakWorkingSetSize);
#elif defined(__linux__)
    std::ifstream stream("/proc/self/status");
    std::string label;
    while (stream >> label) {
        if (label == "VmHWM:") {
            std::uint64_t kibibytes = 0;
            stream >> kibibytes;
            return stream.fail() ? 0 : kibibytes * 1024U;
        }
        stream.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    }
    return 0;
#elif defined(__APPLE__)
    rusage usage{};
    return getrusage(RUSAGE_SELF, &usage) == 0 ? static_cast<std::uint64_t>(usage.ru_maxrss) : 0;
#else
    return 0;
#endif
}

std::string parity_platform_id() {
#if defined(_WIN32)
    return "windows";
#elif defined(__linux__)
    return "linux";
#elif defined(__APPLE__)
    return "macos";
#else
    return "unknown";
#endif
}

std::string parity_compiler_id() {
#if defined(_MSC_VER)
    return "msvc." + std::to_string(_MSC_VER);
#elif defined(__clang__)
    return "clang." + std::to_string(__clang_major__) + "." + std::to_string(__clang_minor__);
#elif defined(__GNUC__)
    return "gcc." + std::to_string(__GNUC__) + "." + std::to_string(__GNUC_MINOR__);
#else
    return "unknown";
#endif
}

std::string parity_build_mode() {
#if defined(NDEBUG)
    return "release";
#else
    return "debug";
#endif
}

BatchWorldSetupRequest parity_setup_request(std::size_t world_count) {
    BatchWorldSetupRequest request{};
    request.seeds.reserve(world_count);
    request.time_steps.reserve(world_count);
    request.spawn_requests.reserve(world_count);
    for (std::size_t world = 0; world < world_count; ++world) {
        request.seeds.push_back(kParitySeedBase + static_cast<std::uint32_t>(world));
        request.time_steps.push_back(kParityTimeStepS);
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.side = Side::Blue;
        spawn.type_name = "Aircraft";
        spawn.entity_name = "HostBatchParity" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0;
        spawn.heading = 90.0;
        request.spawn_requests.push_back(std::move(spawn));
    }
    return request;
}

Json parity_observation_json(const AgentObservation &observation) {
    return {
        {"sim_time", observation.sim_time},
        {"entity_id", observation.id},
        {"x", observation.x},
        {"y", observation.y},
        {"z", observation.z},
        {"vx", observation.vx},
        {"vy", observation.vy},
        {"vz", observation.vz},
        {"heading", observation.heading},
        {"pitch", observation.pitch},
        {"roll", observation.roll},
        {"speed", observation.speed},
        {"health", observation.health},
    };
}

Json parity_observations_json(const std::vector<AgentObservation> &observations) {
    Json result = Json::array();
    for (const AgentObservation &observation : observations) {
        result.push_back(parity_observation_json(observation));
    }
    return result;
}

Json parity_state_without_entity_ids(const std::vector<AgentObservation> &observations) {
    Json result = parity_observations_json(observations);
    for (Json &row : result) {
        row.erase("entity_id");
    }
    return result;
}

bool parity_reset_cleared_entities(const std::vector<AgentObservation> &observations) {
    return std::all_of(observations.begin(), observations.end(), [](const AgentObservation &value) {
        return value.sim_time == 0.0 && value.x == 0.0 && value.y == 0.0 && value.z == 0.0 &&
               value.vx == 0.0 && value.vy == 0.0 && value.vz == 0.0 && value.speed == 0.0 &&
               value.health == 0.0;
    });
}

Json parity_composition_json(const RuntimeCompositionEvidence &value) {
    return {
        {"runtime_request_sha256", value.runtime_request_sha256},
        {"catalog_lock_sha256", value.catalog_lock_sha256},
        {"profile_projection_sha256", value.profile_projection_sha256},
        {"requested_manifest_sha256", value.requested_manifest_sha256},
        {"resolved_manifest_sha256", value.resolved_manifest_sha256},
        {"executable_graph_sha256", value.executable_graph_sha256},
        {"evidence_sha256", value.evidence_sha256},
        {"backend_provider_id", value.backend.provider_id},
        {"backend_implementation_version", value.backend.implementation_version},
        {"backend_profile_id", value.backend.backend_profile_id},
        {"provider_count", value.provider_versions.size()},
        {"world_count", value.world_instances.size()},
        {"host_mode", value.host_mode},
        {"binding_version", value.binding_version},
    };
}

std::vector<WorldPilotActionAssignment>
parity_pilot_actions(const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> assignments;
    assignments.reserve(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        PilotAction action{};
        action.stick_pitch = 0.2;
        action.stick_roll = -0.1;
        action.rudder = 0.05;
        action.throttle = 0.75;
        action.gear_handle = 0.0F;
        action.active = true;
        assignments.push_back(WorldPilotActionAssignment{
            .world_index = world,
            .entity_id = entity_ids[world],
            .action = action,
        });
    }
    return assignments;
}

Json parity_pilot_actions_json(const std::vector<WorldPilotActionAssignment> &assignments) {
    Json result = Json::array();
    for (const WorldPilotActionAssignment &assignment : assignments) {
        result.push_back({
            {"world_index", assignment.world_index},
            {"entity_id", assignment.entity_id},
            {"stick_pitch", assignment.action.stick_pitch},
            {"stick_roll", assignment.action.stick_roll},
            {"rudder", assignment.action.rudder},
            {"throttle", assignment.action.throttle},
            {"gear_handle", assignment.action.gear_handle},
            {"active", assignment.action.active},
        });
    }
    return result;
}

Json parity_window_trace(const RuntimeWindowResult &window) {
    Json barriers = Json::array();
    for (const RuntimeWindowBarrierRecord &barrier : window.barrier_trace) {
        barriers.push_back({
            {"sequence", barrier.sequence},
            {"barrier_id", barrier.barrier_id},
            {"node_id", barrier.node_id},
        });
    }
    Json nodes = Json::array();
    for (const RuntimeWindowNodeExecutionRecord &node : window.executed_nodes) {
        nodes.push_back({
            {"node_id", node.node_id},
            {"execution_state", node.execution_state},
            {"decision_reason", node.decision_reason},
            {"trigger_source", node.trigger_source},
            {"decision_barrier_id", node.decision_barrier_id},
            {"source_snapshot_version", node.source_snapshot_version},
            {"target_window_id", node.target_window_id},
            {"visible_input_count", node.visible_input_count},
        });
    }
    return {
        {"barriers", barriers},
        {"executed_nodes", nodes},
        {"engagement",
         {
             {"snapshot_version", window.engagement_packet.snapshot_version},
             {"barrier_id", window.engagement_packet.barrier_id},
             {"barrier_sequence", window.engagement_packet.barrier_sequence},
             {"source_time_s", window.engagement_packet.source_time_s},
             {"producer_node_id", window.engagement_packet.producer_node_id},
             {"trace_ids", window.engagement_packet.trace_ids},
             {"launch_event_count", window.engagement_packet.launch_events.size()},
             {"effects_event_count", window.engagement_packet.effects_events.size()},
             {"diagnostics_trace_count", window.engagement_packet.diagnostics_traces.size()},
         }},
    };
}

Json run_native_semantic_parity_workload() {
    RuntimeBatchConfig config{};
    config.world_count = kParitySemanticWorldCount;
    config.worker_threads = 1;
    RuntimeFacade facade(config);
    const BatchWorldSetupResult setup =
        facade.apply_world_setup(parity_setup_request(kParitySemanticWorldCount));
    if (setup.entity_ids.size() != kParitySemanticWorldCount) {
        throw std::runtime_error("P7-A semantic setup returned an unexpected entity count");
    }
    std::vector<WorldEntityRef> refs;
    refs.reserve(kParitySemanticWorldCount);
    for (std::size_t world = 0; world < kParitySemanticWorldCount; ++world) {
        refs.push_back(WorldEntityRef{
            .world_index = world,
            .entity_id = setup.entity_ids[world],
        });
    }
    const Json initial = parity_observations_json(facade.get_agent_observations_batch(refs));
    const std::vector<WorldPilotActionAssignment> actions = parity_pilot_actions(setup.entity_ids);
    facade.set_pilot_actions_batch(actions);
    for (std::size_t step = 0; step < kParitySemanticSteps; ++step) {
        facade.step_batch();
    }
    const Json final = parity_observations_json(facade.get_agent_observations_batch(refs));
    const RuntimeCompositionEvidenceResult composition = facade.export_composition_evidence();
    if (!composition.available) {
        throw std::runtime_error("P7-A semantic workload has no composition evidence");
    }
    RuntimeWindowRequest window_request{};
    window_request.window_id = "window:host-batch-parity";
    window_request.source_time_s = 5.0;
    window_request.engagement_request.trace_ids = {1};
    const RuntimeWindowResult window = facade.run_window(window_request);
    const auto comparison = facade.compare_composition_evidence(composition.evidence);
    if (!comparison.compatible || !comparison.mismatches.empty()) {
        throw std::runtime_error("P7-A semantic composition comparison was not admitted");
    }
    const std::string composition_ref =
        "composition_evidence_sha256=" + composition.evidence.evidence_sha256;
    return {
        {"composition", parity_composition_json(composition.evidence)},
        {"action_inputs", parity_pilot_actions_json(actions)},
        {"initial_observations", initial},
        {"final_observations", final},
        {"window_trace", parity_window_trace(window)},
        {"composition_comparison",
         {
             {"compatible", comparison.compatible},
             {"mismatches", comparison.mismatches},
             {"evidence_ref", composition_ref},
         }},
    };
}

Json run_native_batch_measurement() {
    trim_process_allocator();
    const std::uint64_t rss_before = current_rss_bytes();
    const std::uint64_t peak_rss_before = peak_rss_bytes();
    RuntimeBatchConfig config{};
    config.world_count = kParityMeasurementWorldCount;
    config.worker_threads = 1;
    const SteadyClock::time_point construct_start = SteadyClock::now();
    auto facade = std::make_unique<RuntimeFacade>(config);
    const double cold_construct_ms = elapsed_ms(construct_start);
    const std::uint64_t rss_after_construct = current_rss_bytes();

    const BatchWorldSetupRequest setup_request = parity_setup_request(kParityMeasurementWorldCount);
    const SteadyClock::time_point setup_start = SteadyClock::now();
    BatchWorldSetupResult setup = facade->apply_world_setup(setup_request);
    const double setup_ms = elapsed_ms(setup_start);
    if (setup.entity_ids.size() != kParityMeasurementWorldCount) {
        throw std::runtime_error("P7-A batch setup returned an unexpected entity count");
    }
    const std::uint64_t rss_after_setup = current_rss_bytes();

    for (std::size_t step = 0; step < kParityWarmupSteps; ++step) {
        facade->step_batch();
    }
    const SteadyClock::time_point step_start = SteadyClock::now();
    for (std::size_t step = 0; step < kParityMeasurementSteps; ++step) {
        facade->step_batch();
    }
    const double step_total_ms = elapsed_ms(step_start);
    const std::uint64_t rss_after_steps = current_rss_bytes();

    const auto refs_for_setup = [&setup]() {
        std::vector<WorldEntityRef> refs;
        refs.reserve(kParityMeasurementWorldCount);
        for (std::size_t world = 0; world < kParityMeasurementWorldCount; ++world) {
            refs.push_back(WorldEntityRef{
                .world_index = world,
                .entity_id = setup.entity_ids[world],
            });
        }
        return refs;
    };
    std::vector<WorldEntityRef> reset_refs = refs_for_setup();
    const Json representative_reset_state =
        parity_state_without_entity_ids(facade->get_agent_observations_batch(reset_refs));
    double reset_total_ms = 0.0;
    for (std::size_t iteration = 0; iteration < kParityResetIterations; ++iteration) {
        if (iteration != 0) {
            setup = facade->apply_world_setup(setup_request);
            if (setup.entity_ids.size() != kParityMeasurementWorldCount) {
                throw std::runtime_error(
                    "P7-A repeated reset setup returned an unexpected entity count");
            }
            reset_refs = refs_for_setup();
            for (std::size_t step = 0; step < kParityWarmupSteps + kParityMeasurementSteps;
                 ++step) {
                facade->step_batch();
            }
            if (parity_state_without_entity_ids(facade->get_agent_observations_batch(reset_refs)) !=
                representative_reset_state) {
                throw std::runtime_error(
                    "P7-A repeated reset did not receive the representative workload");
            }
        }
        const SteadyClock::time_point reset_start = SteadyClock::now();
        facade->reset_batch();
        reset_total_ms += elapsed_ms(reset_start);
        if (!parity_reset_cleared_entities(facade->get_agent_observations_batch(reset_refs))) {
            throw std::runtime_error("P7-A reset did not clear the representative workload");
        }
    }
    const std::uint64_t rss_after_resets = current_rss_bytes();

    const SteadyClock::time_point teardown_start = SteadyClock::now();
    facade.reset();
    const double teardown_ms = elapsed_ms(teardown_start);
    trim_process_allocator();
    const std::uint64_t rss_after_teardown = current_rss_bytes();
    if (rss_before == 0 || rss_after_construct == 0 || rss_after_setup == 0 ||
        rss_after_steps == 0 || rss_after_resets == 0 || rss_after_teardown == 0) {
        throw std::runtime_error("P7-A native RSS measurement is unavailable");
    }
    const SteadyClock::time_point warm_construct_start = SteadyClock::now();
    auto warm_facade = std::make_unique<RuntimeFacade>(config);
    const double warm_construct_ms = elapsed_ms(warm_construct_start);
    warm_facade.reset();
    const std::uint64_t peak_rss_after = peak_rss_bytes();
    if (peak_rss_before == 0 || peak_rss_after == 0 || peak_rss_after < peak_rss_before) {
        throw std::runtime_error("P7-A native peak RSS measurement is unavailable");
    }
    const std::uint64_t sampled_peak_rss = std::max(
        {rss_before, rss_after_construct, rss_after_setup, rss_after_steps, rss_after_resets});
    const std::uint64_t sampled_peak_delta =
        sampled_peak_rss >= rss_before ? sampled_peak_rss - rss_before : 0;
    const std::uint64_t teardown_residual =
        rss_after_teardown >= rss_before ? rss_after_teardown - rss_before : 0;
    const std::uint64_t peak_rss_delta = peak_rss_after - peak_rss_before;

    return {
        {"cold_construct_ms", cold_construct_ms},
        {"warm_construct_ms", warm_construct_ms},
        {"setup_ms", setup_ms},
        {"step_ms_per_batch", step_total_ms / static_cast<double>(kParityMeasurementSteps)},
        {"step_ms_per_world", step_total_ms / static_cast<double>(kParityMeasurementSteps *
                                                                  kParityMeasurementWorldCount)},
        {"reset_ms_per_batch", reset_total_ms / static_cast<double>(kParityResetIterations)},
        {"reset_ms_per_world", reset_total_ms / static_cast<double>(kParityResetIterations *
                                                                    kParityMeasurementWorldCount)},
        {"teardown_ms", teardown_ms},
        {"rss_before_bytes", rss_before},
        {"rss_after_construct_bytes", rss_after_construct},
        {"rss_after_setup_bytes", rss_after_setup},
        {"rss_after_steps_bytes", rss_after_steps},
        {"rss_after_resets_bytes", rss_after_resets},
        {"rss_after_teardown_bytes", rss_after_teardown},
        {"sampled_peak_rss_bytes", sampled_peak_rss},
        {"sampled_peak_delta_bytes", sampled_peak_delta},
        {"sampled_peak_delta_bytes_per_world",
         static_cast<double>(sampled_peak_delta) /
             static_cast<double>(kParityMeasurementWorldCount)},
        {"peak_rss_before_bytes", peak_rss_before},
        {"peak_rss_after_bytes", peak_rss_after},
        {"peak_rss_delta_bytes", peak_rss_delta},
        {"peak_rss_delta_bytes_per_world",
         static_cast<double>(peak_rss_delta) / static_cast<double>(kParityMeasurementWorldCount)},
        {"teardown_residual_bytes", teardown_residual},
        {"teardown_residual_bytes_per_world",
         static_cast<double>(teardown_residual) /
             static_cast<double>(kParityMeasurementWorldCount)},
    };
}

} // namespace

TEST_CASE("P5-A default facade evidence exactly matches the generated owner fixture") {
    RuntimeFacade facade(1);
    const RuntimeCompositionEvidenceResult result = facade.export_composition_evidence();
    INFO(result.error_code, ": ", result.error_detail);
    REQUIRE(result.available);
    CHECK(result.error_code.empty());

    const RuntimeCompositionEvidence &actual = result.evidence;
    const Json fixture = read_fixture("default_runtime_composition_evidence.v1.json");
    CHECK(actual.evidence_sha256 == fixture.at("evidence_sha256").get<std::string>());
    CHECK(actual.canonical_json == fixture.at("canonical_json").get<std::string>());
    CHECK(actual.composition_id == generated::kCompositionId);
    CHECK(actual.requested_profile_id == generated::kRequestedProfileId);
    CHECK(actual.requested_profile_version == generated::kRequestedProfileVersion);
    CHECK(actual.runtime_request_sha256 == generated::kRuntimeRequestSha256);
    CHECK(actual.requested_manifest_sha256 == generated::kRequestedManifestSha256);
    CHECK(actual.resolved_manifest_sha256 == generated::kResolvedManifestSha256);
    CHECK(actual.catalog_lock_sha256 == generated::kCatalogLockSha256);
    CHECK(actual.profile_projection_sha256 == generated::kProfileProjectionSha256);
    CHECK(actual.executable_graph_sha256 == generated::kExecutableGraphSha256);
    CHECK(actual.provider_versions.size() == 11);
    CHECK(actual.backend.provider_id == generated::kBackendProviderId);
    CHECK(actual.backend.implementation_version == generated::kBackendImplementationVersion);
    CHECK(actual.backend.backend_profile_id == generated::kBackendProfileId);
    REQUIRE(actual.world_instances.size() == 1);
    CHECK(actual.world_instances.front().world_index == 0);
    CHECK(actual.world_instances.front().scope_generations.size() == 5);
    CHECK(std::all_of(actual.world_instances.front().scope_generations.begin(),
                      actual.world_instances.front().scope_generations.end(),
                      [](const auto &scope) { return scope.generation == 1; }));
    CHECK(evidence::validate_runtime_composition_evidence(actual).valid);
}

TEST_CASE("P5-A zero-world facade refuses to claim realized composition evidence") {
    RuntimeFacade facade(0);
    const RuntimeCompositionEvidenceResult result = facade.export_composition_evidence();
    CHECK_FALSE(result.available);
    CHECK(result.error_code == "composition_evidence.no_realized_worlds");
}

TEST_CASE("P5-A exports every world and rejects strict composition mismatches") {
    RuntimeFacade facade(2);
    const RuntimeCompositionEvidenceResult result = facade.export_composition_evidence();
    REQUIRE(result.available);
    const RuntimeCompositionEvidence &actual = result.evidence;
    REQUIRE(actual.world_instances.size() == 2);
    CHECK(actual.world_instances[0].world_index == 0);
    CHECK(actual.world_instances[1].world_index == 1);
    CHECK(facade.compare_composition_evidence(actual).compatible);

    RuntimeCompositionEvidence candidate = actual;
    candidate.catalog_lock_sha256 = std::string(64, '0');
    candidate = evidence::seal_runtime_composition_evidence(std::move(candidate));
    auto comparison = facade.compare_composition_evidence(candidate);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.catalog_lock_sha256"));

    candidate = actual;
    candidate.provider_versions.front().implementation_version = "9.9.9";
    candidate = evidence::seal_runtime_composition_evidence(std::move(candidate));
    comparison = facade.compare_composition_evidence(candidate);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.provider_versions"));

    candidate = actual;
    candidate.backend.backend_profile_id = "gpu.candidate";
    candidate = evidence::seal_runtime_composition_evidence(std::move(candidate));
    comparison = facade.compare_composition_evidence(candidate);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.backend"));

    candidate = actual;
    candidate.executable_graph_sha256 = std::string(64, '1');
    candidate = evidence::seal_runtime_composition_evidence(std::move(candidate));
    comparison = facade.compare_composition_evidence(candidate);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.executable_graph_sha256"));

    candidate = actual;
    candidate.world_instances[1].scope_generations[0].generation += 1;
    candidate = evidence::seal_runtime_composition_evidence(std::move(candidate));
    comparison = facade.compare_composition_evidence(candidate);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.world_instances"));
}

TEST_CASE("P5-A host identity is explicit rather than inferred from process state") {
    RuntimeFacade facade(1);
    const RuntimeCompositionEvidenceResult result = facade.export_composition_evidence();
    REQUIRE(result.available);
    CHECK(result.evidence.host_mode == "native_cpp");
    CHECK(result.evidence.binding_version == "native.v1");
    CHECK(evidence::validate_runtime_composition_evidence(result.evidence).valid);

    RuntimeCompositionEvidence non_ascii = result.evidence;
    non_ascii.host_mode = "native_\xc3\xa9";
    non_ascii = evidence::seal_runtime_composition_evidence(std::move(non_ascii));
    const auto validation = evidence::validate_runtime_composition_evidence(non_ascii);
    CHECK_FALSE(validation.valid);
    CHECK(std::any_of(validation.issues.begin(), validation.issues.end(),
                      [](const auto &issue) { return issue.code == "evidence.non_ascii_string"; }));
}

TEST_CASE("P5-A validation rejects duplicate providers and incomplete world scopes") {
    RuntimeFacade facade(1);
    const RuntimeCompositionEvidenceResult result = facade.export_composition_evidence();
    REQUIRE(result.available);

    RuntimeCompositionEvidence duplicate = result.evidence;
    duplicate.provider_versions.push_back(duplicate.provider_versions.front());
    duplicate = evidence::seal_runtime_composition_evidence(std::move(duplicate));
    CHECK_FALSE(evidence::validate_runtime_composition_evidence(duplicate).valid);

    RuntimeCompositionEvidence incomplete = result.evidence;
    incomplete.world_instances.front().scope_generations.pop_back();
    incomplete = evidence::seal_runtime_composition_evidence(std::move(incomplete));
    const auto validation = evidence::validate_runtime_composition_evidence(incomplete);
    CHECK_FALSE(validation.valid);
    CHECK(std::any_of(validation.issues.begin(), validation.issues.end(), [](const auto &issue) {
        return issue.code == "evidence.incomplete_scope_generations";
    }));

    RuntimeCompositionEvidence repeated_scope = result.evidence;
    repeated_scope.world_instances.front().scope_generations[1].scope =
        repeated_scope.world_instances.front().scope_generations[0].scope;
    repeated_scope = evidence::seal_runtime_composition_evidence(std::move(repeated_scope));
    const auto repeated_scope_validation =
        evidence::validate_runtime_composition_evidence(repeated_scope);
    CHECK_FALSE(repeated_scope_validation.valid);
    CHECK(std::any_of(repeated_scope_validation.issues.begin(),
                      repeated_scope_validation.issues.end(), [](const auto &issue) {
                          return issue.code == "evidence.duplicate_scope_generation" ||
                                 issue.code == "evidence.incomplete_scope_generations";
                      }));

    RuntimeCompositionEvidence noncontiguous_world = result.evidence;
    noncontiguous_world.world_instances.front().world_index = 1;
    noncontiguous_world =
        evidence::seal_runtime_composition_evidence(std::move(noncontiguous_world));
    const auto noncontiguous_validation =
        evidence::validate_runtime_composition_evidence(noncontiguous_world);
    CHECK_FALSE(noncontiguous_validation.valid);
    CHECK(std::any_of(
        noncontiguous_validation.issues.begin(), noncontiguous_validation.issues.end(),
        [](const auto &issue) { return issue.code == "evidence.noncontiguous_world"; }));

    RuntimeCompositionEvidence empty_worlds = result.evidence;
    empty_worlds.world_instances.clear();
    empty_worlds = evidence::seal_runtime_composition_evidence(std::move(empty_worlds));
    const auto empty_worlds_validation =
        evidence::validate_runtime_composition_evidence(empty_worlds);
    CHECK_FALSE(empty_worlds_validation.valid);
    CHECK(std::any_of(
        empty_worlds_validation.issues.begin(), empty_worlds_validation.issues.end(),
        [](const auto &issue) { return issue.code == "evidence.empty_world_instances"; }));

    RuntimeCompositionEvidence invalid_utf8 = result.evidence;
    invalid_utf8.world_instances.front().scope_generations.front().instance_id =
        std::string("scope:") + static_cast<char>(0xff);
    evidence::EvidenceValidationResult invalid_utf8_validation;
    CHECK_NOTHROW(invalid_utf8_validation =
                      evidence::validate_runtime_composition_evidence(invalid_utf8));
    CHECK_FALSE(invalid_utf8_validation.valid);
    CHECK(std::any_of(invalid_utf8_validation.issues.begin(), invalid_utf8_validation.issues.end(),
                      [](const auto &issue) { return issue.code == "evidence.non_ascii_string"; }));

    RuntimeCompositionEvidence oversized_generation = result.evidence;
    oversized_generation.world_instances.front().scope_generations.front().generation =
        static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) + 1U;
    const auto oversized_generation_validation =
        evidence::validate_runtime_composition_evidence(oversized_generation);
    CHECK_FALSE(oversized_generation_validation.valid);
    CHECK(std::any_of(oversized_generation_validation.issues.begin(),
                      oversized_generation_validation.issues.end(), [](const auto &issue) {
                          return issue.code == "evidence.integer_out_of_range";
                      }));

    RuntimeCompositionEvidence incomplete_invalid_utf8_backend = result.evidence;
    incomplete_invalid_utf8_backend.backend.provider_id.clear();
    incomplete_invalid_utf8_backend.backend.backend_profile_id =
        std::string("backend:") + static_cast<char>(0xff);
    evidence::EvidenceValidationResult incomplete_backend_validation;
    CHECK_NOTHROW(incomplete_backend_validation = evidence::validate_runtime_composition_evidence(
                      incomplete_invalid_utf8_backend));
    CHECK_FALSE(incomplete_backend_validation.valid);
    CHECK(std::any_of(incomplete_backend_validation.issues.begin(),
                      incomplete_backend_validation.issues.end(),
                      [](const auto &issue) { return issue.code == "evidence.invalid_backend"; }));
    CHECK(std::any_of(incomplete_backend_validation.issues.begin(),
                      incomplete_backend_validation.issues.end(),
                      [](const auto &issue) { return issue.code == "evidence.non_ascii_string"; }));

    RuntimeCompositionEvidence invalid_utf8_schema = result.evidence;
    invalid_utf8_schema.schema_version = std::string("schema:") + static_cast<char>(0xff);
    evidence::EvidenceValidationResult invalid_utf8_schema_validation;
    CHECK_NOTHROW(invalid_utf8_schema_validation =
                      evidence::validate_runtime_composition_evidence(invalid_utf8_schema));
    CHECK_FALSE(invalid_utf8_schema_validation.valid);
    CHECK(std::any_of(invalid_utf8_schema_validation.issues.begin(),
                      invalid_utf8_schema_validation.issues.end(),
                      [](const auto &issue) { return issue.code == "evidence.non_ascii_string"; }));
}

TEST_CASE("P5-A shrink and regrow cannot reproduce an old composition incarnation") {
    RuntimeFacade facade(1);
    const RuntimeCompositionEvidenceResult before = facade.export_composition_evidence();
    REQUIRE(before.available);

    facade.resize(0);
    facade.resize(1);

    const RuntimeCompositionEvidenceResult after = facade.export_composition_evidence();
    REQUIRE(after.available);
    CHECK(after.evidence.evidence_sha256 != before.evidence.evidence_sha256);
    CHECK(after.evidence.world_instances.front().scope_generations.front().instance_id !=
          before.evidence.world_instances.front().scope_generations.front().instance_id);
    const auto comparison = facade.compare_composition_evidence(before.evidence);
    CHECK_FALSE(comparison.compatible);
    CHECK(has_mismatch(comparison, "$.world_instances"));

    RuntimeFacade configured(1);
    const RuntimeCompositionEvidenceResult configured_before =
        configured.export_composition_evidence();
    REQUIRE(configured_before.available);

    configured.configure_batch(RuntimeBatchConfig{.world_count = 0, .worker_threads = 0});
    configured.configure_batch(RuntimeBatchConfig{.world_count = 1, .worker_threads = 0});

    const RuntimeCompositionEvidenceResult configured_after =
        configured.export_composition_evidence();
    REQUIRE(configured_after.available);
    CHECK(configured_after.evidence.evidence_sha256 != configured_before.evidence.evidence_sha256);
    CHECK_FALSE(configured.compare_composition_evidence(configured_before.evidence).compatible);
}

TEST_CASE("P7-A default CPU-exact native host and batch parity probe") {
    const Json metrics = run_native_batch_measurement();
    const Json first = run_native_semantic_parity_workload();
    const Json second = run_native_semantic_parity_workload();
    REQUIRE(first == second);

    const Json &composition = first.at("composition");
    CHECK(composition.at("runtime_request_sha256").get<std::string>() ==
          std::string(generated::kRuntimeRequestSha256));
    CHECK(composition.at("catalog_lock_sha256").get<std::string>() ==
          std::string(generated::kCatalogLockSha256));
    CHECK(composition.at("profile_projection_sha256").get<std::string>() ==
          std::string(generated::kProfileProjectionSha256));
    CHECK(composition.at("requested_manifest_sha256").get<std::string>() ==
          std::string(generated::kRequestedManifestSha256));
    CHECK(composition.at("resolved_manifest_sha256").get<std::string>() ==
          std::string(generated::kResolvedManifestSha256));
    CHECK(composition.at("executable_graph_sha256").get<std::string>() ==
          std::string(generated::kExecutableGraphSha256));
    CHECK(composition.at("backend_provider_id").get<std::string>() ==
          std::string(generated::kBackendProviderId));
    CHECK(composition.at("backend_implementation_version").get<std::string>() ==
          std::string(generated::kBackendImplementationVersion));
    CHECK(composition.at("backend_profile_id").get<std::string>() ==
          std::string(generated::kBackendProfileId));
    CHECK(composition.at("provider_count").get<std::size_t>() == 11);
    CHECK(composition.at("world_count").get<std::size_t>() == kParitySemanticWorldCount);

    const Json report = {
        {"schema_version", "echelon_forge.runtime_host_batch_native_probe.v1"},
        {"host_id", "native_cpp_direct"},
        {"runtime_owner",
         {
             {"execution_owner", "native_cpp"},
             {"backend_provider_id", std::string(generated::kBackendProviderId)},
             {"node_host_status", "conditional_held_p6b_not_admitted"},
         }},
        {"environment",
         {
             {"platform", parity_platform_id()},
             {"compiler", parity_compiler_id()},
             {"build_mode", parity_build_mode()},
             {"logical_cpu_count", std::max(1U, std::thread::hardware_concurrency())},
         }},
        {"workload",
         {
             {"semantic_world_count", kParitySemanticWorldCount},
             {"semantic_steps", kParitySemanticSteps},
             {"measurement_world_count", kParityMeasurementWorldCount},
             {"warmup_steps", kParityWarmupSteps},
             {"measurement_steps", kParityMeasurementSteps},
             {"reset_iterations", kParityResetIterations},
             {"worker_threads", 1},
             {"seed_base", kParitySeedBase},
             {"time_step_s", kParityTimeStepS},
         }},
        {"semantic", first},
        {"metrics", metrics},
    };

    if (const char *output = std::getenv("EF_P7_PARITY_REPORT");
        output != nullptr && output[0] != '\0') {
        const std::filesystem::path report_path(output);
        if (!report_path.parent_path().empty()) {
            std::filesystem::create_directories(report_path.parent_path());
        }
        std::ofstream stream(report_path, std::ios::binary | std::ios::trunc);
        REQUIRE_MESSAGE(stream.good(), "failed to open P7-A native report: ", report_path.string());
        stream << report.dump(2) << '\n';
        stream.flush();
        REQUIRE_MESSAGE(stream.good(),
                        "failed to write P7-A native report: ", report_path.string());
    }
}
