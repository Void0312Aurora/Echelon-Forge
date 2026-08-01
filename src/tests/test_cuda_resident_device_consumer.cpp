#include <doctest/doctest.h>

#include <cstdint>
#include <memory>
#include <ostream>
#include <string>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_device_consumer_contract.h"
#include "runtime/contracts/cuda_resident_phase_d_fixture_contract.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"
#include "runtime/facade/internal/cuda_resident/cuda_resident_device_consumer.h"

namespace {

using runtime::cuda_resident::CudaResidentBackend;
using runtime::cuda_resident::device_consumer::FailureCode;

std::vector<WorldSpawnRequest> make_spawns() {
    std::vector<WorldSpawnRequest> spawns;
    for (std::size_t world = 0; world < 2; ++world) {
        WorldSpawnRequest spawn{};
        spawn.world_index = world;
        spawn.type_name = std::string(runtime::cuda_resident::kFixedAirFixtureTypeName);
        spawn.entity_name = "CR2DeviceConsumer" + std::to_string(world);
        spawn.is_agent = true;
        spawn.x = 1000.0 + static_cast<double>(world) * 100.0;
        spawn.z = 1500.0;
        spawn.vx = 200.0 + static_cast<double>(world);
        spawn.heading = 90.0;
        spawns.push_back(std::move(spawn));
    }
    return spawns;
}

std::vector<WorldPilotActionAssignment>
make_actions(const std::vector<std::uint64_t> &entity_ids) {
    std::vector<WorldPilotActionAssignment> actions(entity_ids.size());
    for (std::size_t world = 0; world < entity_ids.size(); ++world) {
        actions[world].world_index = world;
        actions[world].entity_id = entity_ids[world];
        actions[world].action.active = true;
        actions[world].action.stick_pitch = 0.10 + 0.05 * static_cast<double>(world);
        actions[world].action.stick_roll = -0.20 + 0.05 * static_cast<double>(world);
        actions[world].action.rudder = 0.03;
        actions[world].action.throttle = 0.65;
    }
    return actions;
}

struct Fixture {
    std::vector<std::uint32_t> seeds = {101, 202};
    std::vector<double> time_steps = {0.05, 0.125};
    std::vector<WorldSpawnRequest> spawns = make_spawns();
    std::vector<std::uint64_t> entity_ids;
    std::vector<WorldPilotActionAssignment> actions;
};

Fixture setup_backend(CudaResidentBackend &backend) {
    Fixture fixture;
    const auto setup = backend.setup({
        .kind = runtime::backend::SetupKind::Batch,
        .seeds = fixture.seeds,
        .spawn_requests = fixture.spawns,
        .time_steps = fixture.time_steps,
    });
    fixture.entity_ids = setup.entity_ids;
    fixture.actions = make_actions(fixture.entity_ids);
    return fixture;
}

void advance_one_window(CudaResidentBackend &backend, const Fixture &fixture) {
    backend.inject({.pilot_actions = fixture.actions});
    backend.advance({.kind = runtime::backend::AdvanceKind::WorldBatch});
}

} // namespace

TEST_CASE("CR2-3 device-consumer contract is private, explicit, and fail-closed") {
    using namespace runtime::cuda_resident;
    using namespace runtime::cuda_resident::device_consumer;

    CHECK(kCudaResidentDeviceLeaseSchemaV1 == "cuda_resident.device_observation_lease.v1");
    CHECK(kCudaResidentDeviceConsumerSurfaceV1 == "cuda_resident.device_consumer_smoke.v1");
    CHECK(kCudaResidentDeviceLeaseOwnership == "owned_d2d_snapshot_copy");
    CHECK(kCudaResidentDeviceLeaseStream == "legacy_default_stream");
    CHECK_FALSE(kDeviceConsumerMeasuredPathIncludesHostValidationReadback);
    CHECK(kDeviceConsumerDiagnosticReadbackIsOutsideMeasuredPath);
    CHECK(kSubmissionMaySynchronizeForDeviceAllocation);
    CHECK(kInFlightReleaseMaySynchronize);
    CHECK(failure_code_id(FailureCode::lease_event_record_failed) ==
          "lease_event_record_failed");
    CHECK(failure_code_id(FailureCode::wait_required) == "wait_required");

    CudaResidentDeviceConsumer consumer;
    const auto invalid_submit = consumer.submit(
        {}, {.request_id = "invalid", .expected_epoch = {.allocation_generation = 1,
                                                           .reset_generation = 1,
                                                           .committed_window = 1,
                                                           .source_snapshot = 3}});
    CHECK(invalid_submit.failure == FailureCode::invalid_lease);
    CHECK(consumer.await({}).failure == FailureCode::invalid_receipt);
    CHECK(consumer.materialize_for_diagnostics({}).failure == FailureCode::invalid_receipt);
    float value = 0.0F;
    int fake_event = 0;
    ConsumerReceipt missing_ids{
        .lifetime = std::make_shared<int>(1),
        .completion_state = std::make_shared<int>(1),
        .first_values = &value,
        .ready_event = &fake_event,
        .device_ordinal = 0,
        .world_count = 1,
        .source_epoch = {.allocation_generation = 1,
                         .reset_generation = 1,
                         .committed_window = 1,
                         .source_snapshot = 3},
    };
    CHECK_FALSE(missing_ids.valid());
    CHECK(consumer.await(missing_ids).failure == FailureCode::invalid_receipt);

    if (!CudaWorldStore::compiled_with_cuda()) {
        CudaResidentBackend backend;
        const auto unavailable = backend.acquire_device_observation_lease("cuda-off");
        CHECK(unavailable.failure == FailureCode::cuda_unavailable);
    }
}

TEST_CASE("CR2-3 lease survives backend reset and supports repeat submit and await") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }

    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    const Fixture fixture = setup_backend(backend);
    CHECK(backend.acquire_device_observation_lease("before-commit").failure ==
          FailureCode::no_committed_window);
    advance_one_window(backend, fixture);

    auto acquired = backend.acquire_device_observation_lease("window-1");
    REQUIRE(acquired.success());
    const auto &lease = acquired.lease;
    CHECK(lease.observations.shape == std::vector<std::uint64_t>{2, 15});
    CHECK(lease.observations.strides == std::vector<std::uint64_t>{15, 1});
    CHECK(lease.observations.stride_units == "elements");
    CHECK(lease.observations.dtype == "float32");
    CHECK(lease.ids_tensor.shape == std::vector<std::uint64_t>{2});
    CHECK(lease.ids_tensor.dtype == "uint64");
    CHECK(lease.epoch.allocation_generation == 1);
    CHECK(lease.epoch.reset_generation == 1);
    CHECK(lease.epoch.committed_window == 1);
    CHECK(lease.epoch.source_snapshot == 3);
    CHECK(lease.producer_stream == 0);

    CudaResidentDeviceConsumer consumer;
    auto submitted = consumer.submit(
        lease, {.request_id = "consume-1", .expected_epoch = lease.epoch});
    REQUIRE(submitted.success());
    CHECK(consumer.materialize_for_diagnostics(submitted.receipt).failure ==
          FailureCode::wait_required);
    CHECK(consumer.await(submitted.receipt).success());
    CHECK(consumer.await(submitted.receipt).success());
    const auto diagnostic = consumer.materialize_for_diagnostics(submitted.receipt);
    REQUIRE(diagnostic.success());
    REQUIRE(diagnostic.materialized.first_values.size() == 2);
    CHECK(diagnostic.materialized.first_values[0] == doctest::Approx(0.05F));
    CHECK(diagnostic.materialized.first_values[1] == doctest::Approx(0.125F));
    CHECK(diagnostic.materialized.ids == fixture.entity_ids);
    CHECK(consumer.materialize_for_diagnostics(submitted.receipt).success());

    const auto repeated = consumer.submit(
        lease, {.request_id = "consume-repeat", .expected_epoch = lease.epoch});
    REQUIRE(repeated.success());
    CHECK(consumer.await(repeated.receipt).success());

    const auto retained_lease = lease;
    backend.reset({.seeds = fixture.seeds});
    acquired = {};
    submitted = {};
    CHECK(backend.acquire_device_observation_lease("after-reset").failure ==
          FailureCode::no_committed_window);
    const auto retained_submit = consumer.submit(
        retained_lease,
        {.request_id = "consume-after-reset", .expected_epoch = retained_lease.epoch});
    REQUIRE(retained_submit.success());
    CHECK(consumer.await(retained_submit.receipt).success());
    const auto retained_diagnostic =
        consumer.materialize_for_diagnostics(retained_submit.receipt);
    REQUIRE(retained_diagnostic.success());
    CHECK(retained_diagnostic.materialized.ids == fixture.entity_ids);

    device_consumer::ObservationLease detached_lease;
    std::vector<std::uint64_t> detached_ids;
    {
        auto producer = std::make_unique<CudaResidentBackend>();
        producer->configure({.world_count = 2});
        const Fixture detached_fixture = setup_backend(*producer);
        advance_one_window(*producer, detached_fixture);
        auto detached = producer->acquire_device_observation_lease("before-destroy");
        REQUIRE(detached.success());
        detached_lease = detached.lease;
        detached_ids = detached_fixture.entity_ids;
    }
    device_consumer::ConsumerReceipt detached_receipt;
    {
        CudaResidentDeviceConsumer submitter;
        auto detached_submit = submitter.submit(
            detached_lease,
            {.request_id = "detached-consumer", .expected_epoch = detached_lease.epoch});
        REQUIRE(detached_submit.success());
        detached_receipt = detached_submit.receipt;
    }
    CudaResidentDeviceConsumer finisher;
    CHECK(finisher.await(detached_receipt).success());
    const auto detached_diagnostic =
        finisher.materialize_for_diagnostics(detached_receipt);
    REQUIRE(detached_diagnostic.success());
    CHECK(detached_diagnostic.materialized.ids == detached_ids);
}

TEST_CASE("CR2-3 lease and consumer failures are stable and retryable") {
    using namespace runtime::cuda_resident;
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK(true);
        return;
    }

    CudaResidentBackend backend;
    backend.configure({.world_count = 2});
    const Fixture fixture = setup_backend(backend);
    advance_one_window(backend, fixture);
    auto &store = testing::CudaResidentBackendTestAccess::world_store(backend);

    testing::CudaWorldStoreTestAccess::fail_next_device_lease_allocation(store);
    CHECK(backend.acquire_device_observation_lease("lease-allocation").failure ==
          FailureCode::lease_allocation_failed);
    testing::CudaWorldStoreTestAccess::fail_next_device_lease_event_record(store);
    CHECK(backend.acquire_device_observation_lease("lease-event").failure ==
          FailureCode::lease_event_record_failed);
    const auto acquired = backend.acquire_device_observation_lease("lease-ok");
    REQUIRE(acquired.success());

    CudaResidentDeviceConsumer consumer;
    auto mismatched_epoch = acquired.lease.epoch;
    ++mismatched_epoch.committed_window;
    CHECK(consumer.submit(acquired.lease,
                          {.request_id = "stale", .expected_epoch = mismatched_epoch})
              .failure == FailureCode::stale_epoch);
    auto bad_layout = acquired.lease;
    bad_layout.observations.strides[0] = 1;
    CHECK(consumer.submit(bad_layout,
                          {.request_id = "layout", .expected_epoch = bad_layout.epoch})
              .failure == FailureCode::incompatible_layout);
    auto bad_stream = acquired.lease;
    bad_stream.producer_stream = 7;
    CHECK(consumer.submit(bad_stream,
                          {.request_id = "stream", .expected_epoch = bad_stream.epoch})
              .failure == FailureCode::stream_mismatch);
    auto bad_device = acquired.lease;
    ++bad_device.device_ordinal;
    CHECK(consumer.submit(bad_device,
                          {.request_id = "device", .expected_epoch = bad_device.epoch})
              .failure == FailureCode::device_mismatch);

    testing::CudaResidentDeviceConsumerTestAccess::fail_next_allocation(consumer);
    CHECK(consumer.submit(acquired.lease,
                          {.request_id = "allocation", .expected_epoch = acquired.lease.epoch})
              .failure == FailureCode::consumer_allocation_failed);
    testing::CudaResidentDeviceConsumerTestAccess::fail_next_launch(consumer);
    CHECK(consumer.submit(acquired.lease,
                          {.request_id = "launch", .expected_epoch = acquired.lease.epoch})
              .failure == FailureCode::consumer_launch_failed);
    testing::CudaResidentDeviceConsumerTestAccess::fail_next_event_record(consumer);
    CHECK(consumer.submit(acquired.lease,
                          {.request_id = "event", .expected_epoch = acquired.lease.epoch})
              .failure == FailureCode::consumer_event_record_failed);

    const auto submitted = consumer.submit(
        acquired.lease,
        {.request_id = "retryable", .expected_epoch = acquired.lease.epoch});
    REQUIRE(submitted.success());
    testing::CudaResidentDeviceConsumerTestAccess::fail_next_wait(consumer);
    CHECK(consumer.await(submitted.receipt).failure == FailureCode::wait_failed);
    CHECK(consumer.await(submitted.receipt).success());
    testing::CudaResidentDeviceConsumerTestAccess::fail_next_materialize(consumer);
    CHECK(consumer.materialize_for_diagnostics(submitted.receipt).failure ==
          FailureCode::diagnostic_failed);
    CHECK(consumer.materialize_for_diagnostics(submitted.receipt).success());
}
