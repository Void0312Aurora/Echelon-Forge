#include "tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.h"

#include <bit>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <vector>

#if defined(EF_RB9_CPU_PROBE) && defined(EF_RB9_CUDA_PROBE)
#error "RB9 probe must select exactly one lane"
#elif defined(EF_RB9_CPU_PROBE)
#include "runtime/facade/internal/flecs_cpu_backend.h"
#elif defined(EF_RB9_CUDA_PROBE)
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#else
#error "RB9 probe lane is not configured"
#endif

namespace runtime::cuda_resident::performance::probe {

namespace {

using Clock = std::chrono::steady_clock;
using replay::ReplayTrace;

double elapsed_ms(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double, std::milli>(end - start).count();
}

std::vector<WorldPilotActionAssignment>
make_assignments(const ReplayTrace &trace, const std::vector<std::uint64_t> &entity_ids) {
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

void digest_mix(std::uint64_t &digest, std::uint64_t value) {
    for (unsigned int shift = 0; shift < 64; shift += 8) {
        digest ^= (value >> shift) & 0xffU;
        digest *= 1099511628211ULL;
    }
}

void digest_mix(std::uint64_t &digest, double value) {
    digest_mix(digest, std::bit_cast<std::uint64_t>(value));
}

std::string digest_hex(std::uint64_t value) {
    std::ostringstream stream;
    stream << std::hex << std::setfill('0') << std::setw(16) << value;
    return stream.str();
}

} // namespace

#if defined(EF_RB9_CPU_PROBE)

struct ProbeSession::Impl {
    Impl(const replay::ReplayTrace &trace, const std::string &database_path)
        : trace(trace), backend(trace.seeds.size()) {
        const auto setup_start = Clock::now();
        backend.configure({.worker_threads = 0});
        const auto content = backend.load_content({
            .kind = runtime::backend::ContentKind::Database,
            .path = &database_path,
        });
        if (!content.loaded) throw std::runtime_error("RB9 CPU database load failed");
        setup_fixture();
        setup_duration_ms = elapsed_ms(setup_start, Clock::now());
    }

    void setup_fixture() {
        const auto setup = backend.setup({
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = trace.seeds,
            .spawn_requests = trace.spawns,
            .time_steps = trace.time_steps,
        });
        if (setup.entity_ids.size() != trace.seeds.size()) {
            throw std::runtime_error("RB9 CPU setup cardinality mismatch");
        }
        assignments = make_assignments(trace, setup.entity_ids);
        refs = make_refs(setup.entity_ids);
    }

    ReplayTrace trace;
    FlecsCpuBackend backend;
    std::vector<WorldPilotActionAssignment> assignments;
    std::vector<WorldEntityRef> refs;
    double setup_duration_ms = 0.0;
};

#else

struct ProbeSession::Impl {
    Impl(const replay::ReplayTrace &trace, const std::string &)
        : trace(trace) {
        const auto setup_start = Clock::now();
        backend.configure({.world_count = trace.seeds.size()});
        setup_fixture();
        setup_duration_ms = elapsed_ms(setup_start, Clock::now());
    }

    void setup_fixture() {
        const auto setup = backend.setup({
            .kind = runtime::backend::SetupKind::Batch,
            .seeds = trace.seeds,
            .spawn_requests = trace.spawns,
            .time_steps = trace.time_steps,
        });
        if (setup.entity_ids.size() != trace.seeds.size()) {
            throw std::runtime_error("RB9 CUDA setup cardinality mismatch");
        }
        assignments = make_assignments(trace, setup.entity_ids);
    }

    ReplayTrace trace;
    runtime::cuda_resident::CudaResidentBackend backend;
    std::vector<WorldPilotActionAssignment> assignments;
    double setup_duration_ms = 0.0;
};

#endif

ProbeSession::ProbeSession(const replay::ReplayTrace &trace, const std::string &database_path)
    : impl_(std::make_unique<Impl>(trace, database_path)) {}

ProbeSession::~ProbeSession() = default;

void ProbeSession::reset_fixture() {
    const auto setup_start = Clock::now();
    impl_->backend.reset({.seeds = impl_->trace.seeds});
    impl_->setup_fixture();
    impl_->setup_duration_ms = elapsed_ms(setup_start, Clock::now());
}

WindowTiming ProbeSession::run_window(const Mode &mode) {
#if defined(EF_RB9_CPU_PROBE)
    if (mode.device_consumer) {
        throw std::logic_error("CPU reference has no device observation consumer");
    }
#endif
    const auto begin = Clock::now();
#if defined(EF_RB9_CPU_PROBE)
    impl_->backend.inject({.pilot_actions = impl_->assignments});
    impl_->backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    const auto advanced = Clock::now();
    if (mode.host_snapshot) {
        const auto output = impl_->backend.export_state({
            .refs = impl_->refs,
            .include_agent_observations = true,
            .include_instrument_states = true,
        });
        if (output.agent_observations.size() != impl_->refs.size() ||
            output.instrument_states.size() != impl_->refs.size()) {
            throw std::runtime_error("RB9 CPU host collection cardinality mismatch");
        }
    }
#else
    impl_->backend.inject({.pilot_actions = impl_->assignments});
    impl_->backend.publish_stage();
    impl_->backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    const auto advanced = Clock::now();
    if (mode.host_snapshot) {
        const auto snapshot = impl_->backend.export_snapshot("rb9.host_snapshot");
        if (snapshot.worlds.size() != impl_->trace.seeds.size()) {
            throw std::runtime_error("RB9 CUDA host collection cardinality mismatch");
        }
    }
    if (mode.device_consumer) {
        const auto view = impl_->backend.export_device_observation_view("rb9.device_consumer");
        std::vector<float> values;
        std::vector<std::uint64_t> ids;
        if (!runtime::cuda_resident::testing::CudaWorldStoreTestAccess::
                consume_device_observation_view(view, &values, &ids) ||
            values.size() != impl_->trace.seeds.size() || ids.size() != impl_->trace.seeds.size()) {
            throw std::runtime_error("RB9 CUDA device consumer failed");
        }
    }
#endif
    const auto collected = Clock::now();
    return {
        .end_to_end_ms = elapsed_ms(begin, collected),
        .advance_ms = elapsed_ms(begin, advanced),
        .collection_ms = elapsed_ms(advanced, collected),
    };
}

std::string ProbeSession::state_digest() const {
    std::uint64_t digest = 1469598103934665603ULL;
#if defined(EF_RB9_CPU_PROBE)
    const auto output = impl_->backend.export_state({
        .refs = impl_->refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
    });
    for (const auto &observation : output.agent_observations) {
        digest_mix(digest, observation.id);
        digest_mix(digest, observation.sim_time);
        digest_mix(digest, observation.x);
        digest_mix(digest, observation.y);
        digest_mix(digest, observation.z);
        digest_mix(digest, observation.total_reward);
    }
#else
    const auto snapshot = impl_->backend.export_snapshot("rb9.determinism");
    for (const auto &world : snapshot.worlds) {
        digest_mix(digest, world.entity_ref.entity_id);
        digest_mix(digest, world.clock.simulation_time_s);
        digest_mix(digest, world.kinematics.x);
        digest_mix(digest, world.kinematics.y);
        digest_mix(digest, world.kinematics.z);
        digest_mix(digest, world.phase_d.reward.total_reward);
    }
#endif
    return digest_hex(digest);
}

double ProbeSession::setup_ms() const noexcept { return impl_->setup_duration_ms; }

std::size_t ProbeSession::device_bytes() const noexcept {
#if defined(EF_RB9_CPU_PROBE)
    return 0;
#else
    return impl_->backend.store_diagnostics().device_bytes;
#endif
}

std::size_t ProbeSession::state_slot_bytes() const noexcept {
#if defined(EF_RB9_CPU_PROBE)
    return 0;
#else
    return impl_->backend.store_diagnostics().state_slot_bytes;
#endif
}

} // namespace runtime::cuda_resident::performance::probe
