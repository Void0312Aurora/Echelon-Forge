// Window-throughput probe for the CUDA-resident fixed-air backend.
//
// Drives the backend-neutral SPI (configure -> setup -> {inject, advance}*)
// at a chosen world count so the resident kernels can be timed by wall clock
// and profiled by Nsight Compute at sizes the parity tests never reach. It
// prints one JSON object per world count; it never compares against the CPU
// reference (the replay/full-window tests own parity).
//
// Usage: ef_cuda_resident_window_probe [--worlds 1,64,4096] [--warmup N]
//        [--windows N] [--resetup-every N] [--export] [--fixture-sticks]
//        [--digest]
//
// --digest prints an FNV-1a hash over the bit patterns of every resident
// numeric field after the run, so a kernel change can be proven bit-identical
// (run with --warmup 0 --windows <= --resetup-every for a deterministic trace).
#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <exception>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "runtime/contracts/cuda_resident_fixed_air_fixture_contract.h"
#include "runtime/contracts/cuda_resident_flight_dynamics_fixture_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

namespace {

using runtime::cuda_resident::CudaBarrierKernelResources;
using runtime::cuda_resident::CudaResidentBackend;
using runtime::cuda_resident::CudaWorldStore;
using Access = runtime::cuda_resident::testing::CudaWorldStoreTestAccess;

struct Args {
    std::vector<std::size_t> worlds = {1, 16, 256, 4096, 65536};
    int warmup = 32;
    int windows = 200;
    // Re-run setup (outside the timed region) after this many windows. The
    // fixture is validated for one window; a dt=0.125 world held at neutral
    // sticks goes non-finite between windows 17 and 31 (measured on HEI), so
    // 16 keeps every timed window inside the admitted envelope.
    int resetup_every = 16;
    bool export_state = false;
    bool fixture_sticks = false;
    bool digest = false;
};

std::size_t parse_size(const std::string &value, const char *name, bool allow_zero = false) {
    char *end = nullptr;
    const unsigned long long parsed = std::strtoull(value.c_str(), &end, 10);
    if (end == value.c_str() || *end != '\0' || (parsed == 0 && !allow_zero)) {
        throw std::invalid_argument(std::string("invalid integer for ") + name);
    }
    return static_cast<std::size_t>(parsed);
}

Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        auto next = [&]() -> std::string {
            if (i + 1 >= argc) throw std::invalid_argument("missing value for " + flag);
            return argv[++i];
        };
        if (flag == "--worlds") {
            args.worlds.clear();
            std::stringstream list(next());
            std::string item;
            while (std::getline(list, item, ','))
                args.worlds.push_back(parse_size(item, "--worlds"));
        } else if (flag == "--warmup") {
            args.warmup = static_cast<int>(parse_size(next(), "--warmup", true));
        } else if (flag == "--windows") {
            args.windows = static_cast<int>(parse_size(next(), "--windows"));
        } else if (flag == "--resetup-every") {
            args.resetup_every = static_cast<int>(parse_size(next(), "--resetup-every"));
        } else if (flag == "--export") {
            args.export_state = true;
        } else if (flag == "--fixture-sticks") {
            args.fixture_sticks = true;
        } else if (flag == "--digest") {
            args.digest = true;
        } else {
            throw std::invalid_argument("unknown flag " + flag);
        }
    }
    return args;
}

// Every world replicates one of the two RB8 replay-trace worlds (world % 2):
// the same spawn, time step and throttle the parity tests validate, so the
// probe stays inside the admitted fixed-air envelope at any world count.
std::vector<WorldSpawnRequest> make_spawns(std::size_t worlds) {
    std::vector<WorldSpawnRequest> spawns(worlds);
    for (std::size_t world = 0; world < worlds; ++world) {
        const double lane = static_cast<double>(world % 2);
        WorldSpawnRequest &spawn = spawns[world];
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "ResidentProbe" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + lane * 100.0;
        spawn.y = -50.0 * lane;
        spawn.z = 1500.0 + lane * 10.0;
        spawn.heading = 90.0 - lane * 5.0;
        spawn.pitch = 2.0;
        spawn.roll = -3.0;
        spawn.vx = 200.0 + lane;
        spawn.vy = 2.0 * lane;
        spawn.vz = -1.0;
    }
    return spawns;
}

std::vector<WorldPilotActionAssignment> make_actions(const std::vector<std::uint64_t> &ids,
                                                     bool fixture_sticks) {
    std::vector<WorldPilotActionAssignment> assignments(ids.size());
    for (std::size_t world = 0; world < ids.size(); ++world) {
        const auto &input = runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs
            [world % runtime::cuda_resident::kCudaResidentFlightDynamicsFirstInputs.size()];
        PilotAction action{};
        // Sticks stay inside the control-preparation manual deadband so the
        // fixture autopilot holds attitude; held fixture stick deflection
        // leaves the fixed-air envelope within ~64 windows even at dt=0.05.
        action.stick_pitch = fixture_sticks ? input.stick_pitch : 0.0;
        action.stick_roll = fixture_sticks ? input.stick_roll : 0.0;
        action.rudder = fixture_sticks ? input.rudder : 0.0;
        action.throttle = input.throttle;
        action.flaps = 0.1F;
        action.active = true;
        assignments[world] = {.world_index = world, .entity_id = ids[world], .action = action};
    }
    return assignments;
}

void print_resources(const char *name, const CudaBarrierKernelResources &r, bool comma) {
    std::cout << "    \"" << name << "\": {\"registers_per_thread\": " << r.registers_per_thread
              << ", \"threads_per_block\": " << r.threads_per_block
              << ", \"active_blocks_per_sm\": " << r.active_blocks_per_multiprocessor
              << ", \"theoretical_occupancy\": " << r.theoretical_occupancy << "}"
              << (comma ? ",\n" : "\n");
}

// FNV-1a over the bit patterns of every resident numeric field. The hashed
// structs are all-8-byte members (no padding), which the static_asserts pin.
class StateDigest {
  public:
    template <typename T> void bytes(const T &value) {
        const auto *data = reinterpret_cast<const unsigned char *>(&value);
        for (std::size_t i = 0; i < sizeof(T); ++i) {
            hash_ = (hash_ ^ data[i]) * 1099511628211ULL;
        }
    }
    void flag(bool value) { bytes(static_cast<std::uint8_t>(value)); }
    [[nodiscard]] std::uint64_t value() const noexcept { return hash_; }

  private:
    std::uint64_t hash_ = 14695981039346656037ULL;
};

std::uint64_t digest_state(const runtime::cuda_resident::CudaWorldStoreStateSnapshot &state) {
    using namespace runtime::cuda_resident;
    static_assert(sizeof(CudaWorldKinematicsState) == 9 * sizeof(double));
    static_assert(sizeof(CudaWorldDynamicsState) == 20 * sizeof(double));
    static_assert(sizeof(CudaWorldInstrumentState) == 23 * sizeof(double));
    static_assert(sizeof(CudaWorldObservationState) == 16 * sizeof(double));
    static_assert(sizeof(CudaWorldRewardState) == 4 * sizeof(double));
    StateDigest digest;
    for (const CudaWorldResidentState &world : state.worlds) {
        const CudaWorldObservationProjectionState &projection = world.observation_projection;
        digest.bytes(world.kinematics);
        digest.bytes(world.dynamics);
        digest.bytes(projection.instrument);
        digest.bytes(projection.observation);
        digest.bytes(projection.reward);
        digest.flag(projection.termination.terminated);
        digest.flag(projection.termination.truncated);
        digest.bytes(projection.termination.reason_code);
        digest.bytes(projection.termination.snapshot_version);
        digest.flag(projection.events_empty);
        digest.bytes(world.prepared_controls.stick_roll_filt);
        digest.bytes(world.prepared_controls.stick_pitch_filt);
        digest.bytes(world.prepared_controls.stick_yaw_filt);
        digest.bytes(world.prepared_controls.stick_yaw_cmd);
        digest.flag(world.prepared_controls.valid);
        digest.flag(world.prepared_controls.manual_takeover);
        digest.bytes(world.prepared_controls.control_version);
        digest.bytes(world.clock_tick);
        digest.bytes(world.simulation_time_s);
        digest.bytes(world.global_version);
        digest.bytes(world.barrier_sequence);
        digest.bytes(world.barrier);
        digest.bytes(world.shard_versions);
    }
    return digest.value();
}

double percentile(std::vector<double> values, double q) {
    std::sort(values.begin(), values.end());
    const std::size_t rank = static_cast<std::size_t>(q * static_cast<double>(values.size() - 1));
    return values[rank];
}

void run_case(std::size_t worlds, const Args &args) {
    CudaResidentBackend backend;
    backend.configure({.world_count = worlds});
    std::vector<std::uint32_t> seeds(worlds);
    std::vector<double> time_steps(worlds);
    for (std::size_t world = 0; world < worlds; ++world) {
        seeds[world] = static_cast<std::uint32_t>(101 + world);
        time_steps[world] = runtime::cuda_resident::kCudaResidentFlightDynamicsFixtureTimeSteps
            [world % runtime::cuda_resident::kCudaResidentFlightDynamicsFixtureTimeSteps.size()];
    }
    const std::vector<WorldSpawnRequest> spawns = make_spawns(worlds);
    auto run_setup = [&]() {
        return backend.setup({
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = seeds,
            .spawn_requests = spawns,
            .time_steps = time_steps,
        });
    };
    const auto setup = run_setup();
    std::vector<WorldPilotActionAssignment> actions =
        make_actions(setup.entity_ids, args.fixture_sticks);
    std::vector<WorldEntityRef> refs(worlds);
    for (std::size_t world = 0; world < worlds; ++world) {
        refs[world] = {.world_index = world, .entity_id = setup.entity_ids[world]};
    }

    int since_setup = 0;
    auto window = [&]() {
        ++since_setup;
        backend.inject({.pilot_actions = actions});
        backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
        if (args.export_state) {
            (void)backend.export_state({.refs = refs,
                                        .include_agent_observations = true,
                                        .include_instrument_states = true});
        }
    };
    auto maybe_resetup = [&]() {
        if (since_setup < args.resetup_every) return;
        const auto again = run_setup();
        actions = make_actions(again.entity_ids, args.fixture_sticks);
        for (std::size_t world = 0; world < worlds; ++world) {
            refs[world].entity_id = again.entity_ids[world];
        }
        since_setup = 0;
    };
    for (int i = 0; i < args.warmup; ++i) {
        maybe_resetup();
        window();
    }

    std::vector<double> samples_us;
    samples_us.reserve(static_cast<std::size_t>(args.windows));
    for (int i = 0; i < args.windows; ++i) {
        maybe_resetup();
        const auto start = std::chrono::steady_clock::now();
        window();
        const auto stop = std::chrono::steady_clock::now();
        samples_us.push_back(std::chrono::duration<double, std::micro>(stop - start).count());
    }
    const double p50 = percentile(samples_us, 0.50);
    std::cout << "  {\"worlds\": " << worlds << ", \"windows\": " << args.windows
              << ", \"export\": " << (args.export_state ? "true" : "false")
              << ", \"window_us_p10\": " << percentile(samples_us, 0.10)
              << ", \"window_us_p50\": " << p50
              << ", \"window_us_p90\": " << percentile(samples_us, 0.90)
              << ", \"world_steps_per_s_p50\": " << static_cast<double>(worlds) * 1.0e6 / p50
              << ", \"state_slot_bytes\": " << backend.store_diagnostics().state_slot_bytes;
    if (args.digest) {
        auto &store =
            runtime::cuda_resident::testing::CudaResidentBackendTestAccess::world_store(backend);
        std::cout << ", \"state_digest\": \"" << std::hex << digest_state(Access::read_state(store))
                  << std::dec << "\"";
    }
    std::cout << "}";
}

} // namespace

int main(int argc, char **argv) {
    try {
        const Args args = parse_args(argc, argv);
        if (!CudaWorldStore::compiled_with_cuda()) {
            std::cerr << "built without EF_ENABLE_CUDA_RESIDENT_BACKEND\n";
            return 2;
        }
        std::cout << "{\n  \"schema\": \"cuda_resident.window_probe.v1\",\n  \"kernels\": {\n";
        print_resources("apply_barrier_kernel", Access::barrier_kernel_resources(), true);
        print_resources("control_preparation_kernel",
                        Access::control_preparation_kernel_resources(), true);
        print_resources("window_commit_body_kernel", Access::window_commit_body_kernel_resources(),
                        false);
        std::cout << "  },\n  \"cases\": [\n";
        for (std::size_t i = 0; i < args.worlds.size(); ++i) {
            run_case(args.worlds[i], args);
            std::cout << (i + 1 < args.worlds.size() ? ",\n" : "\n");
        }
        std::cout << "  ]\n}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "cuda_resident_window_probe: " << error.what() << "\n";
        return 1;
    }
}
