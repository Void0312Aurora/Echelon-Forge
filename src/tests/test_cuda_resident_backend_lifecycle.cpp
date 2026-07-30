#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <vector>

static_assert(!std::is_copy_constructible_v<runtime::cuda_resident::CudaWorldStore>);
static_assert(!std::is_move_constructible_v<runtime::cuda_resident::CudaWorldStore>);
static_assert(!std::is_copy_constructible_v<runtime::cuda_resident::CudaResidentBackend>);
static_assert(!std::is_move_constructible_v<runtime::cuda_resident::CudaResidentBackend>);

namespace {

void check_device_metadata(const runtime::cuda_resident::CudaWorldStore &store,
                           const std::vector<std::uint32_t> &expected_seeds,
                           std::uint64_t expected_generation) {
    const runtime::cuda_resident::CudaWorldStoreLifecycleSnapshot snapshot =
        runtime::cuda_resident::testing::CudaWorldStoreTestAccess::readback(store);
    CHECK(snapshot.seeds == expected_seeds);
    CHECK(snapshot.reset_generations.size() == expected_seeds.size());
    CHECK(std::all_of(snapshot.reset_generations.begin(), snapshot.reset_generations.end(),
                      [expected_generation](std::uint64_t generation) {
                          return generation == expected_generation;
                      }));
}

} // namespace

TEST_CASE("RB3 CUDA world store lifecycle is instance owned and fail closed") {
    using namespace runtime::cuda_resident;
    using testing::CudaWorldStoreTestAccess;

    CudaWorldStore first;
    CudaWorldStore second;
    CHECK(first.diagnostics().state == CudaWorldStoreState::unconfigured);
    CHECK(second.diagnostics().state == CudaWorldStoreState::unconfigured);
    CHECK(first.diagnostics().allocation_generation == 0);
    CHECK(second.diagnostics().allocation_generation == 0);

    const bool first_configured = first.configure(4);
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK_FALSE(first_configured);
        CHECK(first.diagnostics().state == CudaWorldStoreState::unavailable);
        CHECK(first.diagnostics().world_capacity == 0);
        CHECK(first.diagnostics().device_bytes == 0);
        CHECK(first.diagnostics().allocation_generation == 0);
        CHECK_FALSE(first.diagnostics().last_error.empty());
        CHECK(second.diagnostics().state == CudaWorldStoreState::unconfigured);
        CHECK_FALSE(first.reset({1, 2, 3, 4}));
    } else if (first_configured) {
        CHECK(first.diagnostics().state == CudaWorldStoreState::ready);
        CHECK(first.diagnostics().world_capacity == 4);
        CHECK(first.diagnostics().device_bytes > 4 * 2 * 16);
        CHECK(first.diagnostics().allocation_generation == 1);

        const std::vector<std::uint32_t> first_seeds = {1, 2, 3, 4};
        CHECK(first.reset(first_seeds));
        CHECK(first.diagnostics().reset_generation == 1);
        check_device_metadata(first, first_seeds, 1);

        CHECK_FALSE(first.reset({1, 2}));
        CHECK(first.diagnostics().reset_generation == 1);
        check_device_metadata(first, first_seeds, 1);

        CudaWorldStoreTestAccess::fail_next_reset_copy(first);
        CHECK_FALSE(first.reset({5, 6, 7, 8}));
        CHECK(first.diagnostics().reset_generation == 1);
        check_device_metadata(first, first_seeds, 1);

        CHECK(first.configure(6));
        CHECK(first.diagnostics().world_capacity == 6);
        CHECK(first.diagnostics().allocation_generation == 2);
        CHECK(first.reset({}));
        CHECK(first.diagnostics().reset_generation == 2);
        const std::vector<std::uint32_t> six_zero_seeds(6, 0);
        check_device_metadata(first, six_zero_seeds, 2);

        CudaWorldStoreTestAccess::fail_next_allocation(first);
        CHECK_FALSE(first.configure(8));
        CHECK(first.diagnostics().world_capacity == 6);
        CHECK(first.diagnostics().allocation_generation == 2);
        CHECK(first.reset({21, 22, 23, 24, 25, 26}));
        const std::vector<std::uint32_t> post_allocation_failure = {21, 22, 23, 24, 25, 26};
        check_device_metadata(first, post_allocation_failure, 3);

        CudaWorldStoreTestAccess::fail_next_release(first);
        CHECK_FALSE(first.configure(8));
        CHECK(first.diagnostics().world_capacity == 6);
        CHECK(first.diagnostics().allocation_generation == 2);
        CHECK(first.reset({31, 32, 33, 34, 35, 36}));
        const std::vector<std::uint32_t> post_release_failure = {31, 32, 33, 34, 35, 36};
        check_device_metadata(first, post_release_failure, 4);

        CHECK_FALSE(first.configure(std::numeric_limits<std::size_t>::max()));
        CHECK(first.diagnostics().world_capacity == 6);
        CHECK(first.diagnostics().allocation_generation == 2);
        CHECK_FALSE(first.diagnostics().last_error.empty());
        check_device_metadata(first, post_release_failure, 4);

        CudaWorldStoreTestAccess::set_allocation_generation(
            first, std::numeric_limits<std::uint64_t>::max());
        CHECK_FALSE(first.configure(7));
        CHECK(first.diagnostics().world_capacity == 6);
        CHECK(first.diagnostics().allocation_generation ==
              std::numeric_limits<std::uint64_t>::max());
        check_device_metadata(first, post_release_failure, 4);

        CudaWorldStoreTestAccess::set_reset_generation(first,
                                                       std::numeric_limits<std::uint64_t>::max());
        CHECK_FALSE(first.reset({41, 42, 43, 44, 45, 46}));
        CHECK(first.diagnostics().reset_generation == std::numeric_limits<std::uint64_t>::max());
        check_device_metadata(first, post_release_failure, 4);

        CHECK(second.configure(2));
        CHECK(second.diagnostics().allocation_generation == 1);
        CHECK(second.reset({91, 92}));
        check_device_metadata(second, {91, 92}, 1);
        CHECK(first.diagnostics().world_capacity == 6);

        CudaWorldStoreTestAccess::fail_next_release(first);
        CHECK_FALSE(first.teardown());
        CHECK(first.diagnostics().state == CudaWorldStoreState::ready);
        CHECK(first.diagnostics().world_capacity == 6);
        check_device_metadata(first, post_release_failure, 4);
    } else {
        CHECK(first.diagnostics().state == CudaWorldStoreState::unavailable);
        CHECK_FALSE(first.diagnostics().runtime_available);
        CHECK_FALSE(first.diagnostics().last_error.empty());
    }

    CHECK(first.teardown());
    CHECK(first.teardown());
    CHECK(first.diagnostics().state == CudaWorldStoreState::unconfigured);
    CHECK(first.diagnostics().world_capacity == 0);
    CHECK(first.diagnostics().device_bytes == 0);
    CHECK(second.teardown());
}

TEST_CASE("RB4 backend shell keeps unsupported semantics fail closed") {
    using namespace runtime::cuda_resident;

    CudaResidentBackend backend;
    CHECK(backend.diagnostics().backend_id == std::string(kCudaResidentRb7BackendId));
    CHECK(backend.configuration().world_count == 0);
    CHECK(backend.configuration().worker_threads == 1);
    CHECK(backend.configuration().effective_worker_threads == 1);
    CHECK(backend.compatibility_port() == nullptr);

    runtime::backend::ConfigureRequest configure_request{
        .world_count = 3,
        .worker_threads = 7,
    };
    if (!CudaWorldStore::compiled_with_cuda()) {
        CHECK_THROWS_AS(backend.configure(configure_request), std::runtime_error);
        CHECK(backend.configuration().world_count == 0);
        CHECK(backend.configuration().worker_threads == 7);
    } else {
        try {
            backend.configure(configure_request);
            CHECK(backend.configuration().world_count == 3);
            const std::vector<std::uint32_t> seeds = {11, 12, 13};
            backend.reset(runtime::backend::ResetRequest{.seeds = seeds});
            CHECK(backend.store_diagnostics().reset_generation == 1);
        } catch (const std::runtime_error &) {
            CHECK_FALSE(backend.store_diagnostics().runtime_available);
        }
    }

    CHECK_THROWS_AS(backend.load_content({}), std::logic_error);
    CHECK_THROWS_AS(backend.setup({.kind = runtime::backend::SetupKind::Layout}), std::logic_error);
    runtime::backend::InputBatch unsupported_input{};
    unsupported_input.kinematics_write = runtime::backend::EntityKinematicsWrite{};
    CHECK_THROWS_AS(backend.inject(unsupported_input), std::logic_error);
    CHECK_THROWS_AS(backend.evaluate({}), std::logic_error);
    CHECK_THROWS_AS(backend.advance({.kind = runtime::backend::AdvanceKind::StepExecutionProducts}),
                    std::logic_error);
    CHECK_NOTHROW(backend.export_state({}));
    CHECK_THROWS_AS(backend.export_state({.include_recent_engagement_events = true}),
                    std::logic_error);
}
