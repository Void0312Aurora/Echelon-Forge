#include "tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.h"

#include "runtime/contracts/cuda_resident_matrix_contract.h"

#include <bit>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <vector>

#if defined(EF_CR2_MATRIX_CPU_PROBE) && defined(EF_CR2_MATRIX_CUDA_PROBE)
#error "CR2 matrix session must select exactly one lane"
#elif defined(EF_CR2_MATRIX_CPU_PROBE)
#include "runtime/facade/internal/flecs_cpu_backend.h"
#elif defined(EF_CR2_MATRIX_CUDA_PROBE)
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_device_consumer.h"
#else
#error "CR2 matrix session lane is not configured"
#endif

namespace runtime::cuda_resident::matrix::probe {

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
        digest *= runtime::cuda_resident::matrix::kFnv1a64Prime;
    }
}

void digest_mix(std::uint64_t &digest, double value) {
    const double canonical = value == 0.0 ? 0.0 : value;
    digest_mix(digest, std::bit_cast<std::uint64_t>(canonical));
}

std::string digest_hex(std::uint64_t value) {
    std::ostringstream stream;
    stream << std::hex << std::setfill('0') << std::setw(16) << value;
    return stream.str();
}

} // namespace

struct ProbeSession::Impl {
    Impl(const ReplayTrace &trace, const std::string &database_path) : trace(trace) {
        const auto setup_start = Clock::now();
#if defined(EF_CR2_MATRIX_CPU_PROBE)
        backend.configure({
            .world_count = trace.seeds.size(),
            .worker_threads = runtime::cuda_resident::matrix::kCpuHostWorkerRequest,
        });
        const auto content = backend.load_content({
            .kind = runtime::backend::ContentKind::Database,
            .path = &database_path,
        });
        if (!content.loaded) throw std::runtime_error("CR2 matrix CPU database load failed");
#else
        (void)database_path;
        backend.configure({
            .world_count = trace.seeds.size(),
            .worker_threads = runtime::cuda_resident::matrix::kCudaHostWorkerRequest,
        });
#endif
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
            throw std::runtime_error("CR2 matrix setup cardinality mismatch");
        }
        assignments = make_assignments(trace, setup.entity_ids);
        refs = make_refs(setup.entity_ids);
    }

    ReplayTrace trace;
#if defined(EF_CR2_MATRIX_CPU_PROBE)
    FlecsCpuBackend backend;
#else
    runtime::cuda_resident::CudaResidentBackend backend;
    runtime::cuda_resident::CudaResidentDeviceConsumer device_consumer;
    std::vector<runtime::cuda_resident::device_consumer::ConsumerReceipt> pending_receipts;
#endif
    std::vector<WorldPilotActionAssignment> assignments;
    std::vector<WorldEntityRef> refs;
    double setup_duration_ms = 0.0;
};

ProbeSession::ProbeSession(const ReplayTrace &trace, const std::string &database_path)
    : impl_(std::make_unique<Impl>(trace, database_path)) {}

ProbeSession::~ProbeSession() = default;

void ProbeSession::reset_fixture() {
#if defined(EF_CR2_MATRIX_CUDA_PROBE)
    if (!impl_->pending_receipts.empty()) {
        throw std::logic_error("CR2 matrix reset requires pending consumer release");
    }
#endif
    const auto setup_start = Clock::now();
    impl_->backend.reset({.seeds = impl_->trace.seeds});
    impl_->setup_fixture();
    impl_->setup_duration_ms = elapsed_ms(setup_start, Clock::now());
}

WindowTiming ProbeSession::run_window(const Mode &mode) {
#if defined(EF_CR2_MATRIX_CPU_PROBE)
    if (mode.device_consumer) {
        throw std::logic_error("CPU reference has no device observation consumer");
    }
#endif
    const auto begin = Clock::now();
    impl_->backend.inject({.pilot_actions = impl_->assignments});
    const auto evaluation = impl_->backend.evaluate({});
    if (!evaluation.execution_episode_products.empty()) {
        throw std::runtime_error("CR2 matrix empty evaluation produced output");
    }
    impl_->backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
    const auto advanced = Clock::now();
    if (mode.host_export) {
        const auto output = impl_->backend.export_state({
            .refs = impl_->refs,
            .include_agent_observations = true,
            .include_instrument_states = true,
        });
        if (output.agent_observations.size() != impl_->refs.size() ||
            output.instrument_states.size() != impl_->refs.size()) {
            throw std::runtime_error("CR2 matrix public export cardinality mismatch");
        }
        for (std::size_t world = 0; world < impl_->refs.size(); ++world) {
            if (output.agent_observations[world].id != impl_->refs[world].entity_id) {
                throw std::runtime_error("CR2 matrix public export identity mismatch");
            }
        }
    }
#if defined(EF_CR2_MATRIX_CUDA_PROBE)
    if (mode.device_consumer) {
        const auto acquired =
            impl_->backend.acquire_device_observation_lease("cr2.matrix.device_consumer");
        if (!acquired.success()) {
            throw std::runtime_error("CR2 matrix device lease acquisition failed");
        }
        const auto submitted = impl_->device_consumer.submit(
            acquired.lease,
            {.request_id = "cr2.matrix.device_consumer", .expected_epoch = acquired.lease.epoch});
        if (!submitted.success()) {
            throw std::runtime_error("CR2 matrix device consumer submission failed");
        }
        const auto waited = impl_->device_consumer.await(submitted.receipt);
        if (!waited.success()) {
            throw std::runtime_error("CR2 matrix device consumer wait failed");
        }
        impl_->pending_receipts.push_back(submitted.receipt);
    }
#endif
    const auto collected = Clock::now();
    return {
        .end_to_end_ms = elapsed_ms(begin, collected),
        .input_evaluate_advance_ms = elapsed_ms(begin, advanced),
        .collection_ms = elapsed_ms(advanced, collected),
    };
}

DrainResult ProbeSession::drain_device_consumers(bool materialize_first) {
#if defined(EF_CR2_MATRIX_CUDA_PROBE)
    auto pending = std::move(impl_->pending_receipts);
    impl_->pending_receipts.clear();
    std::size_t materialized = 0;
    if (materialize_first && !pending.empty()) {
        const auto diagnostic = impl_->device_consumer.materialize_for_diagnostics(pending.front());
        if (!diagnostic.success() ||
            diagnostic.materialized.first_values.size() != impl_->trace.seeds.size() ||
            diagnostic.materialized.ids.size() != impl_->trace.seeds.size()) {
            throw std::runtime_error("CR2 matrix device consumer diagnostic failed");
        }
        materialized = 1;
    }
    return {.receipt_count = pending.size(), .materialized_count = materialized};
#else
    (void)materialize_first;
    return {};
#endif
}

std::string ProbeSession::released_state_digest() const {
    const auto output = impl_->backend.export_state({
        .refs = impl_->refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
    });
    if (output.agent_observations.size() != impl_->refs.size() ||
        output.instrument_states.size() != impl_->refs.size()) {
        throw std::runtime_error("CR2 matrix digest export cardinality mismatch");
    }
    std::uint64_t digest = runtime::cuda_resident::matrix::kFnv1a64OffsetBasis;
    for (std::size_t world = 0; world < impl_->refs.size(); ++world) {
        const auto &observation = output.agent_observations[world];
        const auto &instrument = output.instrument_states[world];
        if (observation.id != impl_->refs[world].entity_id) {
            throw std::runtime_error("CR2 matrix digest export identity mismatch");
        }
        digest_mix(digest, static_cast<std::uint64_t>(world));
        digest_mix(digest, observation.sim_time);
        digest_mix(digest, observation.x);
        digest_mix(digest, observation.y);
        digest_mix(digest, observation.z);
        digest_mix(digest, observation.vx);
        digest_mix(digest, observation.vy);
        digest_mix(digest, observation.vz);
        digest_mix(digest, observation.heading);
        digest_mix(digest, observation.roll);
        digest_mix(digest, observation.speed);
        digest_mix(digest, observation.gear_state);
        digest_mix(digest, instrument.throttle_pos);
    }
    return digest_hex(digest);
}

double ProbeSession::setup_ms() const noexcept {
    return impl_->setup_duration_ms;
}

std::size_t ProbeSession::device_bytes() const noexcept {
#if defined(EF_CR2_MATRIX_CUDA_PROBE)
    return impl_->backend.store_diagnostics().device_bytes;
#else
    return 0;
#endif
}

std::size_t ProbeSession::state_slot_bytes() const noexcept {
#if defined(EF_CR2_MATRIX_CUDA_PROBE)
    return impl_->backend.store_diagnostics().state_slot_bytes;
#else
    return 0;
#endif
}

std::size_t ProbeSession::effective_worker_threads() const noexcept {
    return impl_->backend.configuration().effective_worker_threads;
}

std::string ProbeSession::backend_id() const {
    return impl_->backend.diagnostics().backend_id;
}

} // namespace runtime::cuda_resident::matrix::probe
