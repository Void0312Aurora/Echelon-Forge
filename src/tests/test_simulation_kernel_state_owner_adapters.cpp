#include "runtime/host/integration/simulation_kernel_state_owner_adapters.h"
#include "runtime/host/runtime_host_candidate.h"

#include "components/command/common/comm_message.h"
#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/systems/track_management.h"
#include "core/engine/simulation_kernel.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs/addons/meta.h>
#include <nlohmann/json.hpp>

#include <array>
#include <algorithm>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <memory>
#include <random>
#include <sstream>
#include <string>
#include <system_error>
#include <set>

namespace {

namespace host = runtime::host;
namespace integration = runtime::host::integration;
using echelon_forge::runtime_contracts::v1::RuntimeHostIdentity;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;

RuntimeIncarnationRef integration_slot() {
    return {.host = RuntimeHostIdentity{
                .host_id = {.high = 400, .low = 401},
                .boot_id = {.high = 402, .low = 403}},
            .incarnation_epoch = 1};
}

host::RuntimeEpisodeCoordinatorSnapshot integration_barrier() {
    return {
        .episode = {
            .world = {
                .incarnation = integration_slot(),
                .world_slot = 0,
                .world_generation = 5,
            },
            .episode_id = {.high = 410, .low = 411},
            .episode_generation = 7,
        },
        .phase = host::RuntimeEpisodePhase::ReplacementBarrier,
        .step_sequence = 11,
        .barrier_sequence = 13,
        .snapshot_id = {.high = 412, .low = 413},
        .snapshot_sha256 = std::string(64, 'a'),
    };
}

host::RuntimeStateOwnerExportContext integration_export_context(
    const host::RuntimeEpisodeCoordinatorSnapshot &barrier,
    std::size_t source_read_only_result_leases = 0) {
    return {
        .barrier_snapshot = barrier,
        .source_read_only_result_leases = source_read_only_result_leases,
        .cooperative_cancellation_acknowledged = true,
    };
}

std::pair<std::uint64_t, std::mt19937> decode_rng_for_test(
    const std::string &encoded) {
    std::istringstream input(encoded);
    std::string header;
    std::uint64_t draw_position = 0;
    std::mt19937 engine;
    REQUIRE(std::getline(input, header));
    REQUIRE(header == "rng.v2");
    REQUIRE(static_cast<bool>(input >> draw_position));
    REQUIRE(static_cast<bool>(input >> engine));
    return {draw_position, engine};
}

class KernelReplacementEpisodeControl final
    : public host::RuntimeNativeEpisodeControl {
  public:
    explicit KernelReplacementEpisodeControl(RuntimeIdentity128 resource)
        : resource_(resource) {}

    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
        return resource_;
    }

    [[nodiscard]] host::RuntimeNativeEpisodeMutation
    apply(const host::RuntimeNativeEpisodeCommand &) noexcept override {
        return {.applied = true,
                .terminal = true,
                .snapshot_id = {.high = 430, .low = 431},
                .snapshot_sha256 = std::string(64, 'b')};
    }

  private:
    RuntimeIdentity128 resource_;
};

class KernelReplacementControl final : public host::RuntimeInstanceControl {
  public:
    KernelReplacementControl(
        RuntimeIdentity128 resource,
        std::shared_ptr<host::RuntimeStateTransferOwnerRegistry> registry)
        : resource_(resource),
          episode_control_(
              std::make_shared<KernelReplacementEpisodeControl>(resource)),
          registry_(std::move(registry)) {}

    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
        return resource_;
    }

    [[nodiscard]] std::shared_ptr<host::RuntimeNativeEpisodeControl>
    native_episode_control() const noexcept override {
        return episode_control_;
    }

    [[nodiscard]] std::shared_ptr<host::RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept override {
        return registry_;
    }

    [[nodiscard]] bool begin_state_transfer() noexcept override { return true; }
    void end_state_transfer() noexcept override {}

    [[nodiscard]] bool request_cooperative_cancel() noexcept override {
        cancellation_acknowledged_ = true;
        return true;
    }

    [[nodiscard]] bool release_resources() noexcept override {
        released_ = true;
        return true;
    }

    [[nodiscard]] bool resources_released() const noexcept override {
        return released_;
    }

    [[nodiscard]] bool cancellation_acknowledged() const noexcept {
        return cancellation_acknowledged_;
    }

  private:
    RuntimeIdentity128 resource_;
    std::shared_ptr<KernelReplacementEpisodeControl> episode_control_;
    std::shared_ptr<host::RuntimeStateTransferOwnerRegistry> registry_;
    bool cancellation_acknowledged_ = false;
    bool released_ = false;
};

} // namespace

TEST_SUITE("simulation_kernel_state_owner_adapters") {

TEST_CASE("real SimulationKernel owner registry exports and imports all twelve rows") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(123);
    target.reset(456);
    source.step();
    const auto target_python_applied = std::make_shared<std::atomic<bool>>(false);

    const auto journal_path = std::filesystem::temp_directory_path() /
                              "echelon_forge_p4b_simulation_owner_test.wal";
    const auto target_journal_path = std::filesystem::temp_directory_path() /
                                     "echelon_forge_p4b_simulation_owner_target_test.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);
    auto journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
        journal_path.string());
    auto registry = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = journal,
        .transaction_namespace = "source-kernel",
    });
    REQUIRE(registry != nullptr);
    auto target_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &target,
            .journal = std::make_shared<
                host::RuntimeStateTransferFileJournal>(
                target_journal_path.string()),
            .transaction_namespace = "target-kernel",
            .rederive_python_caches = [target_python_applied] {
                target_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [target_python_applied] {
                return std::vector<std::uint8_t>{
                    target_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [target_python_applied](const auto &before) {
                if (before.size() != 1) return false;
                target_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [target_python_applied](const auto &) {
                return target_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
            });
    REQUIRE(target_registry != nullptr);

    const std::string plan_sha256 = source.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-owner.v2", 1, plan_sha256, plan_sha256);
    const host::RuntimeEpisodeCoordinatorSnapshot barrier = integration_barrier();
    const auto exported = registry->export_source(
        profile, integration_slot(),
        {.barrier_snapshot = barrier,
         .source_read_only_result_leases = 3,
         .cooperative_cancellation_acknowledged = true});
    REQUIRE(exported.status);
    CHECK(exported.artifacts.size() == host::kRuntimeStateCategoryCount);
    CHECK(exported.census.entries.size() == host::kRuntimeStateCategoryCount);
    const auto in_flight = std::find_if(
        exported.census.entries.begin(), exported.census.entries.end(),
        [](const auto &entry) {
            return entry.category ==
                   host::RuntimeStateCategory::InFlightRequestsResults;
        });
    REQUIRE(in_flight != exported.census.entries.end());
    CHECK(in_flight->item_count == 3);
    CHECK(in_flight->settled_item_count == 3);
    auto imported = target_registry->import_and_observe(
        profile, exported, {.high = 420, .low = 421});
    INFO(imported.status.detail);
    REQUIRE(imported.status);
    REQUIRE(imported.observations.size() == host::kRuntimeStateCategoryCount);
    REQUIRE(imported.transaction != nullptr);
    const auto committed = imported.transaction->commit_with_deadline(20, 100);
    CHECK(committed.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);
    imported.transaction.reset();
    target_registry.reset();
    target_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &target,
            .journal = std::make_shared<
                host::RuntimeStateTransferFileJournal>(
                target_journal_path.string()),
            .transaction_namespace = "target-kernel",
            .rederive_python_caches = [target_python_applied] {
                target_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [target_python_applied] {
                return std::vector<std::uint8_t>{
                    target_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [target_python_applied](const auto &before) {
                if (before.size() != 1) return false;
                target_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [target_python_applied](const auto &) {
                return target_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
        });
    REQUIRE(target_registry != nullptr);
    auto reopened = target_registry->import_and_observe(
        profile, exported, {.high = 420, .low = 421});
    REQUIRE(reopened.status);
    REQUIRE(reopened.transaction != nullptr);
    const auto recovered = reopened.transaction->recover_with_deadline(21, 100);
    CHECK(recovered.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(recovered.durable);
    reopened.transaction.reset();
    target_registry.reset();
    std::filesystem::remove(journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);
}

TEST_CASE("Python cache owner durably recovers failed rederive and compensates commit") {
    SimulationKernel kernel;
    kernel.reset(903);
    const auto journal_path = std::filesystem::temp_directory_path() /
                              "echelon_forge_p4b_python_owner_recovery.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    const auto applied = std::make_shared<std::atomic<bool>>(false);
    const auto fail_rederive = std::make_shared<std::atomic<bool>>(true);
    auto registry = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &kernel,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string()),
        .transaction_namespace = "python-owner-recovery",
        .rederive_python_caches = [applied, fail_rederive] {
            if (fail_rederive->load()) {
                return false;
            }
            applied->store(true);
            return true;
        },
        .snapshot_python_caches = [applied] {
            return std::vector<std::uint8_t>{applied->load() ? 1U : 0U};
        },
        .rollback_python_caches = [applied](const auto &before) {
            if (before.size() != 1) return false;
            applied->store(before.front() != 0);
            return true;
        },
        .recover_python_caches = [applied](const auto &) {
            return applied->load()
                       ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                       : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
        },
    });
    REQUIRE(registry != nullptr);
    const auto adapter = std::dynamic_pointer_cast<
        host::RuntimeStateOwnerAdapterRegistry>(registry);
    REQUIRE(adapter != nullptr);
    const auto *owner = adapter->registration(
        host::RuntimeStateCategory::PythonLoaderControllerCaches);
    REQUIRE(owner != nullptr);
    const auto barrier = integration_barrier();
    const auto plan_sha256 = kernel.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-python-owner.v2", 1, plan_sha256, plan_sha256);
    const auto exported = owner->export_state(
        profile, integration_slot(), integration_export_context(barrier));
    const RuntimeIdentity128 failed_candidate{.high = 460, .low = 461};
    auto failed = owner->import_state(
        profile, integration_slot(), exported.census_entry, exported.artifact,
        exported.artifact, failed_candidate);
    REQUIRE(failed.transaction != nullptr);
    CHECK(failed.transaction->commit_with_deadline(20, 100).phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Ambiguous);
    const auto failed_recovery = failed.transaction->recover_with_deadline(21, 100);
    REQUIRE(failed_recovery.phase ==
            host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    CHECK_FALSE(applied->load());

    fail_rederive->store(false);
    const RuntimeIdentity128 committed_candidate{.high = 462, .low = 463};
    auto committed = owner->import_state(
        profile, integration_slot(), exported.census_entry, exported.artifact,
        exported.artifact, committed_candidate);
    REQUIRE(committed.transaction != nullptr);
    REQUIRE(committed.transaction->commit_with_deadline(22, 100).phase ==
            host::RuntimeStateOwnerImportTransactionPhase::Committed);
    REQUIRE(applied->load());
    REQUIRE(committed.transaction->rollback_committed());
    CHECK_FALSE(applied->load());
    CHECK(committed.transaction->status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("host replacement commits all twelve real SimulationKernel owner rows") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(901);
    target.reset(902);
    const auto source_unit = source.spawn_unit(
        Side::Blue, "Aircraft", 100.0, 200.0, 3000.0, 45.0, 0.0, 0.0,
        150.0, 0.0, 0.0);
    REQUIRE(source_unit.is_valid());
    MissionCommand command{};
    command.active = true;
    command.command_code = 73;
    command.cmd_heading_deg = 123.0;
    source.set_command_link(source_unit.id(), 1.5, 0.0);
    source.set_mission_command(source_unit.id(), command);
    {
        auto lease = source.acquire_world_lease();
        auto entity = lease.world().entity(source_unit.id());
        entity.set<Score>({.total_reward = 17.25,
                           .missiles_fired = 2,
                           .hits_landed = 1,
                           .kills_confirmed = 1});
        entity.set<Health>({.current_hp = 63.0,
                            .max_hp = 100.0,
                            .mission_kill = true,
                            .mobility_kill = false,
                            .sensor_kill = true});
    }
    source.step();

    const auto source_python_applied = std::make_shared<std::atomic<bool>>(false);
    const auto target_python_applied = std::make_shared<std::atomic<bool>>(false);

    const auto source_journal_path = std::filesystem::temp_directory_path() /
                                     "echelon_forge_p4b_host_source.wal";
    const auto target_journal_path = std::filesystem::temp_directory_path() /
                                     "echelon_forge_p4b_host_target.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);
    auto source_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &source,
            .journal = std::make_shared<
                host::RuntimeStateTransferFileJournal>(
                source_journal_path.string()),
            .transaction_namespace = "host-source",
            .bound_resource_identity = {.high = 452, .low = 453},
            .sample_tick = [] { return std::uint64_t{0}; },
            .rederive_python_caches = [source_python_applied] {
                source_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [source_python_applied] {
                return std::vector<std::uint8_t>{
                    source_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [source_python_applied](const auto &before) {
                if (before.size() != 1) return false;
                source_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [source_python_applied](const auto &) {
                return source_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
        });
    auto target_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &target,
            .journal = std::make_shared<
                host::RuntimeStateTransferFileJournal>(
                target_journal_path.string()),
            .transaction_namespace = "host-target",
            .bound_resource_identity = {.high = 454, .low = 455},
            .sample_tick = [] { return std::uint64_t{0}; },
            .rederive_python_caches = [target_python_applied] {
                target_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [target_python_applied] {
                return std::vector<std::uint8_t>{
                    target_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [target_python_applied](const auto &before) {
                if (before.size() != 1) return false;
                target_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [target_python_applied](const auto &) {
                return target_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
        });
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);

    const std::string plan_sha256 = source.resolved_composition_sha256();
    REQUIRE(plan_sha256 == target.resolved_composition_sha256());
    auto runtime = std::make_unique<host::RuntimeHostCandidate>(
        host::RuntimeHostConfig{
            .host_id = {.high = 450, .low = 451},
            .mode = host::RuntimeHostMode::Dark,
        });
    auto source_control = std::make_shared<KernelReplacementControl>(
        RuntimeIdentity128{.high = 452, .low = 453}, source_registry);
    const host::RuntimePlanBinding source_plan{
        .plan_id = "p4b-real-source",
        .plan_sha256 = plan_sha256,
    };
    auto source_owner_handle = runtime->issue_owner_handle(
        source_control,
        {.transaction_kind = host::RuntimeHostTransactionKind::Initial,
         .plan = source_plan,
         .world_slot_count = 1});
    REQUIRE(source_owner_handle.valid());
    const auto initial = runtime->begin_candidate(
        {.transaction_kind = host::RuntimeHostTransactionKind::Initial,
         .plan = source_plan,
         .lifecycle_deadline_tick = 200,
         .world_slot_count = 1},
        source_owner_handle);
    REQUIRE(initial.status);
    REQUIRE(runtime->validate_candidate(
        initial.handle,
        {.static_plan_validated = true,
         .resources_ready = true,
         .shadow_probe_passed = true,
         .unreachable_from_production = true}));
    const auto initial_publication = runtime->commit_initial(
        initial.handle,
        {.lifecycle_evidence_sha256 = std::string(64, 'c'),
         .dark_evidence_sealed = true});
    REQUIRE(initial_publication.status);
    const auto source_slot = initial_publication.published_slot;

    auto target_control = std::make_shared<KernelReplacementControl>(
        RuntimeIdentity128{.high = 454, .low = 455}, target_registry);
    const host::RuntimePlanBinding target_plan{
        .plan_id = "p4b-real-target",
        .plan_sha256 = plan_sha256,
    };
    auto target_owner_handle = runtime->issue_owner_handle(
        target_control,
        {.transaction_kind = host::RuntimeHostTransactionKind::Replacement,
         .expected_slot = source_slot,
         .plan = target_plan,
         .world_slot_count = 1});
    REQUIRE(target_owner_handle.valid());
    const auto candidate = runtime->begin_candidate(
        {.transaction_kind = host::RuntimeHostTransactionKind::Replacement,
         .expected_slot = source_slot,
         .plan = target_plan,
         .lifecycle_deadline_tick = 200,
         .world_slot_count = 1},
        target_owner_handle);
    REQUIRE(candidate.status);
    REQUIRE(runtime->validate_candidate(
        candidate.handle,
        {.static_plan_validated = true,
         .resources_ready = true,
         .shadow_probe_passed = true,
         .unreachable_from_production = true}));

    const auto episode_admission = runtime->issue_shadow_episode(0);
    REQUIRE(episode_admission.status);
    auto late_result = runtime->acquire_lease(
        episode_admission.capability, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(late_result.status);
    const auto terminal = runtime->submit_shadow_episode(
        episode_admission.capability,
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = episode_admission.capability.episode(),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 456, .low = 457},
         .payload_sha256 = std::string(64, 'd')});
    REQUIRE(terminal.status);
    REQUIRE(terminal.receipt.terminal);

    auto quiescence = runtime->quiesce_replacement_source(candidate.handle);
    REQUIRE(quiescence.status);
    REQUIRE(source_control->cancellation_acknowledged());
    auto barrier = runtime->open_shadow_replacement_barrier(
        terminal.receipt.episode_after,
        terminal.receipt.resulting_step_sequence);
    REQUIRE(barrier.status);
    const auto barrier_snapshot = barrier.capability.snapshot();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "p4b-real-host-replacement.v2", 1, plan_sha256, plan_sha256);
    const auto source_export = source_registry->export_source(
        profile, source_slot,
        {.barrier_snapshot = barrier_snapshot,
         .source_read_only_result_leases = 1,
         .cooperative_cancellation_acknowledged = true});
    REQUIRE(source_export.status);
    auto validated = host::RuntimeStateTransferValidator::validate({
        .profile = profile,
        .census = source_export.census,
        .evidence = {
            .source_final_mutation_fence_sequence =
                quiescence.capability.mutation_fence_sequence(),
        },
        .host_quiescence = std::move(quiescence.capability),
        .episode_barrier = std::move(barrier.capability),
    });
    REQUIRE(validated.status);
    REQUIRE(validated.transfer.valid());
    REQUIRE(runtime->prepare_replacement(
        candidate.handle,
        {.validated_transfer = std::move(validated.transfer),
         .drain_deadline_tick = 180}));
    const auto publication =
        runtime->commit_prepared_candidate(candidate.handle, 20);
    REQUIRE(publication.status);
    CHECK(publication.published_slot.incarnation_epoch ==
          source_slot.incarnation_epoch + 1);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          integration::SimulationKernelStateOwnerBridge::serialize_world(source));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_rng(target) ==
          integration::SimulationKernelStateOwnerBridge::serialize_rng(source));

    REQUIRE(runtime->validate_result(
        late_result.lease,
        {.request = late_result.request_ref}));
    late_result.lease.settle();
    REQUIRE(runtime->poll(30));
    CHECK_FALSE(runtime->snapshot().draining.has_value());
    REQUIRE(runtime->snapshot().active.has_value());
    CHECK(runtime->snapshot().active->incarnation == publication.published_slot);

    const auto shutdown = runtime->begin_shutdown(40, 160);
    REQUIRE(shutdown.status);
    runtime.reset();
    source_control.reset();
    target_control.reset();
    source_registry.reset();
    target_registry.reset();
    std::filesystem::remove(source_journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);
}

TEST_CASE("failed real SimulationKernel replacement compensates owners and restores the active epoch") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(931);
    target.reset(932);
    const auto source_unit = source.spawn_unit(
        Side::Blue, "Aircraft", 100.0, 200.0, 3000.0, 45.0, 0.0, 0.0,
        150.0, 0.0, 0.0);
    REQUIRE(source_unit.is_valid());
    source.set_command_link(source_unit.id(), 2.5, 0.0);
    source.step();

    const std::string target_world_before =
        integration::SimulationKernelStateOwnerBridge::serialize_world(target);
    const std::string target_rng_before =
        integration::SimulationKernelStateOwnerBridge::serialize_rng(target);
    const auto target_python_applied = std::make_shared<std::atomic<bool>>(false);
    const auto target_tick_calls = std::make_shared<std::atomic<std::uint64_t>>(0);
    const auto target_rollback_calls = std::make_shared<std::atomic<std::uint64_t>>(0);

    const auto source_journal_path = std::filesystem::temp_directory_path() /
                                     "echelon_forge_p4c_rollback_source.wal";
    const auto target_journal_path = std::filesystem::temp_directory_path() /
                                     "echelon_forge_p4c_rollback_target.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);

    const auto source_python_applied = std::make_shared<std::atomic<bool>>(false);
    auto source_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &source,
            .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
                source_journal_path.string()),
            .transaction_namespace = "p4c-rollback-source",
            .bound_resource_identity = {.high = 932, .low = 933},
            .sample_tick = [] { return std::uint64_t{0}; },
            .rederive_python_caches = [source_python_applied] {
                source_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [source_python_applied] {
                return std::vector<std::uint8_t>{
                    source_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [source_python_applied](const auto &before) {
                if (before.size() != 1) {
                    return false;
                }
                source_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [source_python_applied](const auto &) {
                return source_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
        });

    // Each real owner transaction samples this clock before and after its
    // native apply.  Trigger the deadline on the post-apply sample of the
    // final row so every earlier row has a durable commit that must be
    // compensated, while no synthetic owner is involved.
    auto target_registry =
        integration::SimulationKernelStateOwnerBridge::create_registry({
            .kernel = &target,
            .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
                target_journal_path.string()),
            .transaction_namespace = "p4c-rollback-target",
            .bound_resource_identity = {.high = 934, .low = 935},
            .sample_tick = [target_tick_calls] {
                const std::uint64_t call =
                    target_tick_calls->fetch_add(1, std::memory_order_relaxed) + 1;
                return call >= 24 ? std::uint64_t{180} : std::uint64_t{0};
            },
            .rederive_python_caches = [target_python_applied] {
                target_python_applied->store(true);
                return true;
            },
            .snapshot_python_caches = [target_python_applied] {
                return std::vector<std::uint8_t>{
                    target_python_applied->load() ? 1U : 0U};
            },
            .rollback_python_caches = [target_python_applied, target_rollback_calls](
                                           const auto &before) {
                if (before.size() != 1) {
                    return false;
                }
                target_rollback_calls->fetch_add(1, std::memory_order_relaxed);
                target_python_applied->store(before.front() != 0);
                return true;
            },
            .recover_python_caches = [target_python_applied](const auto &) {
                return target_python_applied->load()
                           ? host::RuntimeStateOwnerImportTransactionPhase::Committed
                           : host::RuntimeStateOwnerImportTransactionPhase::Aborted;
            },
        });
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);
    const std::string plan_sha256 = source.resolved_composition_sha256();
    REQUIRE(plan_sha256 == target.resolved_composition_sha256());

    const std::size_t orphaned_before = host::RuntimeHostCandidate::orphaned_host_count();
    auto runtime = std::make_unique<host::RuntimeHostCandidate>(host::RuntimeHostConfig{
        .host_id = {.high = 930, .low = 931},
        .mode = host::RuntimeHostMode::Dark,
    });
    auto source_control = std::make_shared<KernelReplacementControl>(
        RuntimeIdentity128{.high = 932, .low = 933}, source_registry);
    const host::RuntimePlanBinding source_plan{
        .plan_id = "p4c-rollback-source",
        .plan_sha256 = plan_sha256,
    };
    auto source_owner_handle = runtime->issue_owner_handle(
        source_control,
        {.transaction_kind = host::RuntimeHostTransactionKind::Initial,
         .plan = source_plan,
         .world_slot_count = 1});
    REQUIRE(source_owner_handle.valid());
    const auto initial = runtime->begin_candidate(
        {.transaction_kind = host::RuntimeHostTransactionKind::Initial,
         .plan = source_plan,
         .lifecycle_deadline_tick = 200,
         .world_slot_count = 1},
        source_owner_handle);
    REQUIRE(initial.status);
    REQUIRE(runtime->validate_candidate(
        initial.handle,
        {.static_plan_validated = true,
         .resources_ready = true,
         .shadow_probe_passed = true,
         .unreachable_from_production = true}));
    REQUIRE(runtime->commit_initial(
                 initial.handle,
                 {.lifecycle_evidence_sha256 = std::string(64, 'c'),
                  .dark_evidence_sealed = true})
                .status);
    const auto source_slot = runtime->snapshot().active->incarnation;

    auto target_control = std::make_shared<KernelReplacementControl>(
        RuntimeIdentity128{.high = 934, .low = 935}, target_registry);
    const host::RuntimePlanBinding target_plan{
        .plan_id = "p4c-rollback-target",
        .plan_sha256 = plan_sha256,
    };
    auto target_owner_handle = runtime->issue_owner_handle(
        target_control,
        {.transaction_kind = host::RuntimeHostTransactionKind::Replacement,
         .expected_slot = source_slot,
         .plan = target_plan,
         .world_slot_count = 1});
    REQUIRE(target_owner_handle.valid());
    const auto candidate = runtime->begin_candidate(
        {.transaction_kind = host::RuntimeHostTransactionKind::Replacement,
         .expected_slot = source_slot,
         .plan = target_plan,
         .lifecycle_deadline_tick = 200,
         .world_slot_count = 1},
        target_owner_handle);
    REQUIRE(candidate.status);
    REQUIRE(runtime->validate_candidate(
        candidate.handle,
        {.static_plan_validated = true,
         .resources_ready = true,
         .shadow_probe_passed = true,
         .unreachable_from_production = true}));

    const auto episode_admission = runtime->issue_shadow_episode(0);
    REQUIRE(episode_admission.status);
    auto old_result = runtime->acquire_lease(
        episode_admission.capability, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(old_result.status);
    const auto terminal = runtime->submit_shadow_episode(
        episode_admission.capability,
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = episode_admission.capability.episode(),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 936, .low = 937},
         .payload_sha256 = std::string(64, 'd')});
    REQUIRE(terminal.status);
    REQUIRE(terminal.receipt.terminal);
    auto quiescence = runtime->quiesce_replacement_source(candidate.handle);
    REQUIRE(quiescence.status);
    auto barrier = runtime->open_shadow_replacement_barrier(
        terminal.receipt.episode_after, terminal.receipt.resulting_step_sequence);
    REQUIRE(barrier.status);
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "p4c-real-rollback.v2", 1, plan_sha256, plan_sha256);
    const auto source_export = source_registry->export_source(
        profile, source_slot,
        {.barrier_snapshot = barrier.capability.snapshot(),
         .source_read_only_result_leases = 1,
         .cooperative_cancellation_acknowledged = true});
    REQUIRE(source_export.status);
    auto validated = host::RuntimeStateTransferValidator::validate({
        .profile = profile,
        .census = source_export.census,
        .evidence = {
            .source_final_mutation_fence_sequence =
                quiescence.capability.mutation_fence_sequence(),
        },
        .host_quiescence = std::move(quiescence.capability),
        .episode_barrier = std::move(barrier.capability),
    });
    REQUIRE(validated.status);
    REQUIRE(validated.transfer.valid());
    REQUIRE(runtime->prepare_replacement(
        candidate.handle,
        {.validated_transfer = std::move(validated.transfer),
         .drain_deadline_tick = 180}));

    const auto publication = runtime->commit_prepared_candidate(candidate.handle, 20);
    CHECK(publication.status.error == host::RuntimeHostError::InvalidCommitProof);
    REQUIRE(runtime->snapshot().active.has_value());
    CHECK(runtime->snapshot().active->incarnation == source_slot);
    CHECK(runtime->snapshot().active->admission_open);
    CHECK_FALSE(runtime->snapshot().candidate.has_value());
    CHECK_FALSE(runtime->snapshot().draining.has_value());
    CHECK(runtime->snapshot().quarantined.empty());

    // The target actually imported native truth before the final deadline
    // crossed; compensation must restore the exact target pre-image.
    CHECK(target_tick_calls->load(std::memory_order_relaxed) >= 24);
    CHECK(target_rollback_calls->load(std::memory_order_relaxed) > 0);
    CHECK_FALSE(target_python_applied->load(std::memory_order_relaxed));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_world_before);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_rng(target) ==
          target_rng_before);

    std::ifstream target_wal(target_journal_path, std::ios::binary);
    const std::string wal_bytes((std::istreambuf_iterator<char>(target_wal)),
                                std::istreambuf_iterator<char>());
    std::size_t aborted_records = 0;
    for (std::size_t offset = wal_bytes.find("\taborted\t");
         offset != std::string::npos;
         offset = wal_bytes.find("\taborted\t", offset + 1)) {
        ++aborted_records;
    }
    CHECK(aborted_records >= 12);

    // The source result lease and source epoch remain valid after the failed
    // replacement, while no candidate epoch escaped the host authority table.
    REQUIRE(runtime->validate_result(old_result.lease,
                                     {.request = old_result.request_ref}));
    const auto restored_episode = runtime->issue_shadow_episode(0);
    REQUIRE(restored_episode.status);
    CHECK(restored_episode.capability.episode().world.incarnation == source_slot);
    REQUIRE(runtime->release_shadow_episode(restored_episode.capability));
    old_result.lease.settle();

    const auto shutdown = runtime->begin_shutdown(40, 200);
    REQUIRE(shutdown.status);
    runtime.reset();
    source_control.reset();
    target_control.reset();
    source_registry.reset();
    target_registry.reset();
    CHECK(host::RuntimeHostCandidate::orphaned_host_count() <= orphaned_before);
    std::filesystem::remove(source_journal_path, remove_error);
    std::filesystem::remove(target_journal_path, remove_error);
}

TEST_CASE("real SimulationKernel ECS truth round trips and rolls back") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(123);
    target.reset(456);
    const auto source_lead = source.spawn_unit(
        Side::Blue, "Aircraft", 100.0, 200.0, 3000.0, 45.0, 0.0, 0.0,
        150.0, 0.0, 0.0);
    const auto source_target = source.spawn_unit(
        Side::Red, "Aircraft", 5100.0, 200.0, 3000.0, 225.0, 0.0, 0.0,
        -150.0, 0.0, 0.0);
    REQUIRE(source_lead.is_valid());
    REQUIRE(source_target.is_valid());
    Detection detection{};
    detection.target_id = source_target.id();
    detection.range = 5000.0;
    detection.local_sensor_hit = true;
    source.set_contact_list(source_lead.id(), {detection});
    {
        auto lease = source.acquire_world_lease();
        SystemTrack track{};
        track.track_id = 6101;
        track.entity_id = source_target.id();
        lease.world().entity(source_lead.id()).set<SystemTrack>(track);
    }
    MissionCommand command{};
    command.active = true;
    command.assigned_target_id = source_target.id();
    command.assigned_target_track_id = 88001;
    command.engagement_authority_holder_id = source_lead.id();
    source.set_command_link(source_lead.id(), 0.0, 0.0);
    source.set_mission_command(source_lead.id(), command);
    TaskOrder task_order{};
    task_order.active = true;
    task_order.issuer_id = source_lead.id();
    task_order.assignee_id = source_target.id();
    task_order.lead_aircraft_id = source_target.id();
    source.set_task_order(source_lead.id(), task_order);
    LeaderIntent intent{};
    intent.active = true;
    intent.tactical_unit_id = source_lead.id();
    intent.assigned_target_id = source_target.id();
    intent.assigned_target_track_id = 88002;
    source.set_leader_intent(source_lead.id(), intent);
    PilotReport report{};
    report.active = true;
    report.sender_id = source_lead.id();
    report.entity_ref = source_target.id();
    report.element_id = source_lead.id();
    source.set_pilot_report(source_lead.id(), report);
    {
        auto lease = source.acquire_world_lease();
        auto status_message = make_action_command();
        status_message.send_msg = true;
        status_message.msg_type = static_cast<int>(CommMsgType::STATUS_FUEL);
        status_message.msg_arg = 99;
        lease.world().entity(source_lead.id()).set<ActionCommand>(status_message);
        auto target_message = make_action_command();
        target_message.send_msg = true;
        target_message.msg_type = static_cast<int>(CommMsgType::ReportContact);
        target_message.msg_arg = source_lead.id();
        lease.world().entity(source_target.id()).set<ActionCommand>(target_message);
    }

    // Consume target-local ids so a correct transfer cannot accidentally pass
    // by retaining source Flecs ids.
    {
        auto lease = target.acquire_world_lease();
        REQUIRE(lease.world().entity().is_valid());
        REQUIRE(lease.world().entity().is_valid());
        REQUIRE(lease.world().entity().is_valid());
    }

    const auto journal_path = std::filesystem::temp_directory_path() /
                              "echelon_forge_p4b_simulation_owner_reject_test.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    auto registry = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string()),
        .transaction_namespace = "source-reject",
    });
    REQUIRE(registry != nullptr);
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-reject.v2", 1, source.resolved_composition_sha256(),
        source.resolved_composition_sha256());
    const std::string source_world =
        integration::SimulationKernelStateOwnerBridge::serialize_world(source);
    const std::string target_before =
        integration::SimulationKernelStateOwnerBridge::serialize_world(target);
    const std::vector<std::uint8_t> source_bytes(source_world.begin(),
                                                 source_world.end());
    const std::vector<std::uint8_t> target_before_bytes(target_before.begin(),
                                                        target_before.end());
    auto unknown_document = nlohmann::json::parse(source_world);
    unknown_document["unknown_truth"] = true;
    const auto unknown_json = unknown_document.dump();
    const std::vector<std::uint8_t> unknown_payload(unknown_json.begin(),
                                                    unknown_json.end());
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, unknown_payload));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    const std::vector<std::uint8_t> malformed_payload{'{', 'n', 'o', 't',
                                                       '-', 'j', 's', 'o', 'n'};
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, malformed_payload));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, source_bytes));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          source_world);
    std::uint64_t target_lead_id = 0;
    std::uint64_t target_target_id = 0;
    {
        auto lease = target.acquire_world_lease();
        const auto target_lead = lease.world().lookup(
            ("p4b-simobject-" + std::to_string(source_lead.id())).c_str());
        const auto target_target = lease.world().lookup(
            ("p4b-simobject-" + std::to_string(source_target.id())).c_str());
        REQUIRE(target_lead.is_valid());
        REQUIRE(target_target.is_valid());
        target_lead_id = target_lead.id();
        target_target_id = target_target.id();
        const auto *restored_track = target_lead.get<SystemTrack>();
        REQUIRE(restored_track != nullptr);
        CHECK(restored_track->track_id == 6101);
        CHECK(restored_track->entity_id == target_target.id());
    }
    CHECK(target_lead_id != source_lead.id());
    CHECK(target_target_id != source_target.id());
    const auto restored_detections = target.get_detections(target_lead_id);
    REQUIRE(restored_detections.size() == 1);
    CHECK(restored_detections.front().target_id == target_target_id);
    const auto restored_command = target.get_mission_command(target_lead_id);
    CHECK(restored_command.assigned_target_id == target_target_id);
    CHECK(restored_command.assigned_target_track_id == 88001);
    CHECK(restored_command.engagement_authority_holder_id == target_lead_id);
    const auto restored_order = target.get_task_order(target_lead_id);
    CHECK(restored_order.issuer_id == target_lead_id);
    CHECK(restored_order.assignee_id == target_target_id);
    CHECK(restored_order.lead_aircraft_id == target_target_id);
    const auto restored_intent = target.get_leader_intent(target_lead_id);
    CHECK(restored_intent.tactical_unit_id == target_lead_id);
    CHECK(restored_intent.assigned_target_id == target_target_id);
    CHECK(restored_intent.assigned_target_track_id == 88002);
    {
        auto lease = target.acquire_world_lease();
        const auto *status_message = lease.world().entity(target_lead_id).get<ActionCommand>();
        REQUIRE(status_message != nullptr);
        CHECK(status_message->msg_arg == 99);
        const auto *target_message = lease.world().entity(target_target_id).get<ActionCommand>();
        REQUIRE(target_message != nullptr);
        CHECK(target_message->msg_arg == target_lead_id);
    }
    const auto restored_report = target.get_pilot_report(target_lead_id);
    CHECK(restored_report.sender_id == target_lead_id);
    CHECK(restored_report.entity_ref == target_target_id);
    CHECK(restored_report.element_id == target_lead_id);
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, target_before_bytes));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("real ECS owner imports N-1 through its durable transaction") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(123);
    target.reset(456);
    REQUIRE(source.spawn_unit(Side::Blue, "Aircraft", 100.0, 200.0,
                              3000.0, 45.0, 0.0, 0.0,
                              150.0, 0.0, 0.0).is_valid());
    REQUIRE(target.spawn_unit(Side::Red, "Aircraft", -100.0, -200.0,
                              5000.0, 180.0, 0.0, 0.0,
                              220.0, 0.0, 0.0).is_valid());

    const auto source_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_ecs_source_owner.wal";
    const auto target_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_ecs_target_owner.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
    auto source_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            source_path.string()),
        .transaction_namespace = "ecs-source",
    });
    auto target_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            target_path.string()),
        .transaction_namespace = "ecs-target",
    });
    auto source_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            source_registry_base);
    auto target_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            target_registry_base);
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);
    const auto *source_owner = source_registry->registration(
        host::RuntimeStateCategory::EcsComponentTruth);
    const auto *target_owner = target_registry->registration(
        host::RuntimeStateCategory::EcsComponentTruth);
    REQUIRE(source_owner != nullptr);
    REQUIRE(target_owner != nullptr);

    const auto barrier = integration_barrier();
    const std::string plan_sha256 = source.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-ecs-n-minus-one.v2", 1, plan_sha256, plan_sha256);
    auto exported = source_owner->export_state(
        profile, integration_slot(), integration_export_context(barrier));
    auto previous_entry = exported.census_entry;
    previous_entry.schema_generation = host::kRuntimeStateTransferPreviousGeneration;
    previous_entry.canonical_payload =
        host::runtime_state_canonical_payload(previous_entry);
    previous_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(previous_entry.canonical_payload);
    auto previous_artifact = exported.artifact;
    previous_artifact.schema_generation =
        host::kRuntimeStateTransferPreviousGeneration;
    const auto migrated = source_owner->migrate_previous(previous_artifact);
    REQUIRE(migrated.payload == previous_artifact.payload);

    const std::string target_before =
        integration::SimulationKernelStateOwnerBridge::serialize_world(target);
    auto aborted = target_owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        {.high = 416, .low = 417});
    REQUIRE(aborted.transaction != nullptr);
    const auto aborted_status = aborted.transaction->abort_with_deadline(20, 100);
    CHECK(aborted_status.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    CHECK(aborted_status.durable);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);

    const RuntimeIdentity128 candidate_identity{.high = 418, .low = 419};
    auto imported = target_owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        candidate_identity);
    REQUIRE(imported.transaction != nullptr);
    CHECK(imported.transaction->status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Prepared);
    const auto committed = imported.transaction->commit_with_deadline(20, 100);
    CHECK(committed.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          integration::SimulationKernelStateOwnerBridge::serialize_world(source));

    auto reopened = target_owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        candidate_identity);
    REQUIRE(reopened.transaction != nullptr);
    CHECK(reopened.transaction->status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(reopened.transaction->status().durable);

    aborted.transaction.reset();
    imported.transaction.reset();
    reopened.transaction.reset();
    source_registry_base.reset();
    target_registry_base.reset();
    source_registry.reset();
    target_registry.reset();
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
}

TEST_CASE("ECS owner covers every generic platform family") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(51);
    target.reset(52);
    REQUIRE(source.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, 3000.0,
                              0.0, 0.0, 0.0, 150.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Blue, "Ship", 1000.0, 0.0, 0.0,
                              0.0, 0.0, 0.0, 10.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Blue, "Submarine", 2000.0, 0.0, -50.0,
                              0.0, 0.0, 0.0, 5.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Red, "Missile", 3000.0, 0.0, 3000.0,
                              180.0, 0.0, 0.0, -600.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Neutral, "Facility", 4000.0, 0.0, 0.0,
                              0.0, 0.0, 0.0, 0.0, 0.0, 0.0).is_valid());
    const auto source_world =
        integration::SimulationKernelStateOwnerBridge::serialize_world(source);
    const std::vector<std::uint8_t> payload(source_world.begin(), source_world.end());
    auto unknown_codec_document = nlohmann::json::parse(source_world);
    bool missile_codec_found = false;
    for (auto &result : unknown_codec_document.at("results")) {
        auto &components = result.at("components");
        if (components.contains("Missile")) {
            components.at("Missile")["unknown_truth"] = true;
            missile_codec_found = true;
            break;
        }
    }
    REQUIRE(missile_codec_found);
    const auto unknown_codec_json = unknown_codec_document.dump();
    const std::vector<std::uint8_t> unknown_codec_payload(
        unknown_codec_json.begin(), unknown_codec_json.end());
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, unknown_codec_payload));
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_world(target,
                                                                          payload));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          source_world);
}

TEST_CASE("ECS owner covers maintained database platform definitions") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(61);
    target.reset(62);
    REQUIRE(source.load_database("examples/config/database"));
    REQUIRE(target.load_database("examples/config/database"));
    const auto source_aircraft = source.spawn_unit(
        Side::Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0,
        250.0, 0.0, 0.0);
    REQUIRE(source_aircraft.is_valid());
    ecs_entity_t source_munition = 0;
    {
        auto lease = source.acquire_world_lease();
        lease.world().entity(source_aircraft.id()).children([&](flecs::entity child) {
            const auto *candidate = child.get<Munition>();
            if (candidate != nullptr && candidate->station_id == 1 &&
                source_munition == 0) {
                source_munition = child.id();
            }
        });
        REQUIRE(source_munition != 0);
        REQUIRE(lease.world().entity(source_munition).has<SimObject>());
        auto *munition = lease.world().entity(source_munition).get_mut<Munition>();
        REQUIRE(munition != nullptr);
        munition->is_fired = true;
        lease.world().entity(source_munition).modified<Munition>();
        CHECK(lease.world().entity(source_munition).get<Munition>()->is_fired);
    }
    const auto source_destroyer = source.spawn_unit(
        Side::Blue, "DDG-51_Flight_I_ASW_Helo_MVP",
        10000.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        12.0, 0.0, 0.0);
    REQUIRE(source_destroyer.is_valid());
    const auto source_helo = source.debug_get_embarked_helo(source_destroyer.id());
    REQUIRE(source_helo != 0);
    {
        auto lease = source.acquire_world_lease();
        REQUIRE(lease.world().entity(source_helo).has<SimObject>());
        lease.world().entity(source_helo).set<Health>({37.0, 100.0});
    }
    REQUIRE(source.spawn_unit(Side::Blue, "Kilo_Class_MVP", 20000.0, 0.0,
                              -100.0, 0.0, 0.0, 0.0,
                              8.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Red, "Ground_Platoon_MVP", 30000.0, 0.0,
                              0.0, 0.0, 0.0, 0.0,
                              5.0, 0.0, 0.0).is_valid());
    REQUIRE(source.spawn_unit(Side::Neutral, "Generic_Airbase", 40000.0, 0.0,
                              0.0, 0.0, 0.0, 0.0,
                              0.0, 0.0, 0.0).is_valid());

    const auto source_world =
        integration::SimulationKernelStateOwnerBridge::serialize_world(source);
    const auto source_document = nlohmann::json::parse(source_world);
    bool source_munition_fired = false;
    for (const auto &result : source_document.at("results")) {
        if (result.at("components").contains("Munition") &&
            result.at("components").at("Munition").at("station_id").get<int>() == 1) {
            source_munition_fired = result.at("components")
                                        .at("Munition")
                                        .at("is_fired")
                                        .get<bool>();
            break;
        }
    }
    REQUIRE(source_munition_fired);
    const auto target_before =
        integration::SimulationKernelStateOwnerBridge::serialize_world(target);
    auto missing_sim_object_tag = nlohmann::json::parse(source_world);
    missing_sim_object_tag.at("results").front().erase("tags");
    const auto missing_sim_object_tag_json = missing_sim_object_tag.dump();
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, std::vector<std::uint8_t>(missing_sim_object_tag_json.begin(),
                                          missing_sim_object_tag_json.end())));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    auto missing_child_of = nlohmann::json::parse(source_world);
    missing_child_of.erase("child_of");
    const auto missing_child_of_json = missing_child_of.dump();
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, std::vector<std::uint8_t>(missing_child_of_json.begin(),
                                          missing_child_of_json.end())));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    auto duplicate_parent = nlohmann::json::parse(source_world);
    REQUIRE_FALSE(duplicate_parent.at("child_of").empty());
    duplicate_parent["child_of"].push_back(duplicate_parent.at("child_of").front());
    const auto duplicate_parent_json = duplicate_parent.dump();
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, std::vector<std::uint8_t>(duplicate_parent_json.begin(),
                                          duplicate_parent_json.end())));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);

    auto cyclic_parent = nlohmann::json::parse(source_world);
    const auto first_relation = cyclic_parent.at("child_of").front();
    cyclic_parent["child_of"].push_back(
        {{"child", first_relation.at("parent")},
         {"parent", first_relation.at("child")}});
    const auto cyclic_parent_json = cyclic_parent.dump();
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, std::vector<std::uint8_t>(cyclic_parent_json.begin(),
                                          cyclic_parent_json.end())));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);

    auto hidden_pair = nlohmann::json::parse(source_world);
    hidden_pair.at("results").front()["pairs"] = {"(Unsupported,Pair)"};
    const auto hidden_pair_json = hidden_pair.dump();
    CHECK_FALSE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, std::vector<std::uint8_t>(hidden_pair_json.begin(),
                                          hidden_pair_json.end())));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          target_before);
    const std::vector<std::uint8_t> payload(source_world.begin(), source_world.end());
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_world(target,
                                                                          payload));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_world(target) ==
          source_world);
    {
        auto lease = target.acquire_world_lease();
        flecs::entity target_munition;
        lease.world().query<Munition>().each(
            [&](flecs::entity child, Munition &munition) {
                if (!target_munition.is_valid() && child.has<SimObject>() &&
                    munition.station_id == 1) {
                    target_munition = child;
                }
            });
        REQUIRE(target_munition.is_valid());
        const auto *restored_munition = target_munition.get<Munition>();
        REQUIRE(restored_munition != nullptr);
        CHECK(restored_munition->station_id == 1);
        CHECK(restored_munition->is_fired);
        const auto target_destroyer = lease.world().lookup(
            ("p4b-simobject-" + std::to_string(source_destroyer.id())).c_str());
        REQUIRE(target_destroyer.is_valid());
        const auto target_helo = target.debug_get_embarked_helo(target_destroyer.id());
        REQUIRE(target_helo != 0);
        CHECK(lease.world().entity(target_helo).is_alive());
        const auto *target_helo_health =
            lease.world().entity(target_helo).get<Health>();
        REQUIRE(target_helo_health != nullptr);
        CHECK(target_helo_health->current_hp == doctest::Approx(37.0));
        CHECK(ecs_get_target(lease.world().c_ptr(), target_helo, EcsChildOf, 0) ==
              target_destroyer.id());
    }

    // Destroyed is distinct from stowed: transfer must not resurrect a child
    // merely because both states carry a target-local id of zero.
    {
        auto lease = source.acquire_world_lease();
        lease.world().entity(source_helo).destruct();
    }
    source.step();
    CHECK(source.debug_get_embarked_helo(source_destroyer.id()) == 0);
    const auto empty_bay_world =
        integration::SimulationKernelStateOwnerBridge::serialize_world(source);
    const std::vector<std::uint8_t> empty_bay_payload(
        empty_bay_world.begin(), empty_bay_world.end());
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_world(
        target, empty_bay_payload));
    {
        auto lease = target.acquire_world_lease();
        const auto target_destroyer = lease.world().lookup(
            ("p4b-simobject-" + std::to_string(source_destroyer.id())).c_str());
        REQUIRE(target_destroyer.is_valid());
        CHECK(target.debug_get_embarked_helo(target_destroyer.id()) == 0);
    }
}

TEST_CASE("every registered component has transfer or explicit rederive policy") {
    SimulationKernel kernel;
    kernel.reset(71);
    const std::set<std::string_view> dedicated_codecs{
        "Missile", "HitboxConfig", "AircraftVulnerabilityProfile",
        "SystemHealth", "ComponentDamageState"};
    const std::set<std::string_view> target_rederived_services{
        "EffectsModelRef", "EngagementEventRecorderRef", "SensorModelRef",
        "AcousticModelRef", "ControlModelRef", "GuidanceModelRef",
        "EnvironmentModelRef", "WeaponReleaseServiceRef"};
    std::vector<std::string> missing;
    auto lease = kernel.acquire_world_lease();
    for (const auto &row : runtime::systems::default_component_contributions()) {
        const ecs_entity_t component_id = ecs_lookup(
            lease.world().c_ptr(), std::string(row.component_id).c_str());
        REQUIRE(component_id != 0);
        const bool reflected = ecs_has(lease.world().c_ptr(), component_id, EcsType);
        if (!reflected && !dedicated_codecs.contains(row.component_id) &&
            !target_rederived_services.contains(row.component_id)) {
            missing.emplace_back(row.component_id);
        }
    }
    std::ostringstream detail;
    for (const auto &name : missing) {
        detail << ' ' << name;
    }
    INFO("registered transfer codec coverage missing:" << detail.str());
    CHECK(missing.empty());
}

TEST_CASE("real SimulationKernel RNG and clock codecs round trip and roll back") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(17);
    target.reset(29);
    source.step();
    const std::string target_rng_before =
        integration::SimulationKernelStateOwnerBridge::serialize_rng(target);
    const std::string target_clock_before =
        integration::SimulationKernelStateOwnerBridge::serialize_clock(target, 0, 3);
    const auto source_rng = integration::SimulationKernelStateOwnerBridge::serialize_rng(source);
    const auto source_clock =
        integration::SimulationKernelStateOwnerBridge::serialize_clock(source, 1, 3);
    const std::vector<std::uint8_t> source_rng_bytes(source_rng.begin(), source_rng.end());
    const std::vector<std::uint8_t> source_clock_bytes(source_clock.begin(),
                                                       source_clock.end());
    const std::vector<std::uint8_t> target_rng_before_bytes(
        target_rng_before.begin(), target_rng_before.end());
    const std::vector<std::uint8_t> target_clock_before_bytes(
        target_clock_before.begin(), target_clock_before.end());
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_rng(
        target, source_rng_bytes));
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_clock(
        target, source_clock_bytes));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_rng(target) == source_rng);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_clock(target, 1, 3) ==
          source_clock);

    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_rng(
        target, target_rng_before_bytes));
    REQUIRE(integration::SimulationKernelStateOwnerBridge::restore_clock(
        target, target_clock_before_bytes));
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_rng(target) ==
          target_rng_before);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_clock(target, 0, 3) ==
          target_clock_before);
}

TEST_CASE("real RNG owner imports N-1 through the durable adapter journal") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(17);
    target.reset(29);
    const auto shooter = source.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0,
                                           1000.0, 0.0, 0.0, 0.0,
                                           150.0, 0.0, 0.0);
    const auto victim = source.spawn_unit(Side::Red, "Aircraft", 12000.0, 0.0,
                                          1000.0, 180.0, 0.0, 0.0,
                                          -200.0, 0.0, 0.0);
    REQUIRE(shooter.is_valid());
    REQUIRE(victim.is_valid());
    source.set_unit_ammo(shooter.id(), 1, 1);
    source.set_weapon_cooldown(shooter.id(), 0.0, -1.0);
    Detection track{};
    track.target_id = victim.id();
    track.range = 12000.0;
    track.bearing = 0.0;
    track.elevation = 0.0;
    track.closing_speed = 350.0;
    track.signal_strength = 1.0;
    track.local_sensor_hit = true;
    source.set_contact_list(shooter.id(), {track});
    REQUIRE(source.fire_missile(shooter.id(), victim.id()).is_valid());

    const auto source_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_rng_source_owner.wal";
    const auto target_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_rng_target_owner.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
    auto source_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            source_path.string()),
        .transaction_namespace = "rng-source",
    });
    auto target_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            target_path.string()),
        .transaction_namespace = "rng-target",
    });
    auto source_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            source_registry_base);
    auto target_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            target_registry_base);
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);
    const auto *source_owner =
        source_registry->registration(host::RuntimeStateCategory::RngState);
    const auto *target_owner =
        target_registry->registration(host::RuntimeStateCategory::RngState);
    REQUIRE(source_owner != nullptr);
    REQUIRE(target_owner != nullptr);

    const auto barrier = integration_barrier();
    const std::string plan_sha256 = source.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-rng-n-minus-one.v2", 1, plan_sha256, plan_sha256);
    auto exported = source_owner->export_state(
        profile, integration_slot(), integration_export_context(barrier));
    auto previous_entry = exported.census_entry;
    previous_entry.schema_generation = host::kRuntimeStateTransferPreviousGeneration;
    previous_entry.canonical_payload =
        host::runtime_state_canonical_payload(previous_entry);
    previous_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(previous_entry.canonical_payload);
    auto previous_artifact = exported.artifact;
    previous_artifact.schema_generation =
        host::kRuntimeStateTransferPreviousGeneration;
    const auto migrated = source_owner->migrate_previous(previous_artifact);
    CHECK(migrated.schema_generation ==
          host::kRuntimeStateTransferContractGeneration);
    CHECK(migrated.payload == previous_artifact.payload);

    const RuntimeIdentity128 candidate_identity{.high = 420, .low = 421};
    auto imported = target_owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        candidate_identity);
    REQUIRE(imported.transaction != nullptr);
    const auto prepared = imported.transaction->status();
    CHECK(prepared.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Prepared);
    CHECK(prepared.durable);
    const auto committed = imported.transaction->commit_with_deadline(20, 100);
    CHECK(committed.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);

    const std::string source_rng =
        integration::SimulationKernelStateOwnerBridge::serialize_rng(source);
    const std::string target_rng =
        integration::SimulationKernelStateOwnerBridge::serialize_rng(target);
    CHECK(target_rng == source_rng);
    auto [source_position, source_engine] = decode_rng_for_test(source_rng);
    auto [target_position, target_engine] = decode_rng_for_test(target_rng);
    CHECK(source_position == 2);
    CHECK(target_position == source_position);
    for (int index = 0; index < 16; ++index) {
        CHECK(target_engine() == source_engine());
    }

    auto reopened = target_owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        candidate_identity);
    REQUIRE(reopened.transaction != nullptr);
    CHECK(reopened.transaction->status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(reopened.transaction->status().durable);
    imported.transaction.reset();
    reopened.transaction.reset();
    source_registry_base.reset();
    target_registry_base.reset();
    source_registry.reset();
    target_registry.reset();
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
}

TEST_CASE("clock owner imports N-1 and rejects trailing or stale barrier metadata") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(17);
    target.reset(29);
    source.step();
    const auto journal_path = std::filesystem::temp_directory_path() /
                              "echelon_forge_p4b_clock_owner_reject.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    auto registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string()),
        .transaction_namespace = "clock-target",
    });
    auto registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(registry_base);
    REQUIRE(registry != nullptr);
    const auto *owner =
        registry->registration(host::RuntimeStateCategory::ClockCadence);
    REQUIRE(owner != nullptr);
    const auto barrier = integration_barrier();
    const std::string plan_sha256 = source.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-clock-reject.v2", 1, plan_sha256, plan_sha256);
    auto artifact = host::RuntimeStateOwnerArtifact{
        .category = host::RuntimeStateCategory::ClockCadence,
        .schema_id = std::string(host::runtime_state_schema_id(
            host::RuntimeStateCategory::ClockCadence)),
        .schema_generation = host::kRuntimeStateTransferContractGeneration,
        .payload = {},
    };
    const std::string encoded =
        integration::SimulationKernelStateOwnerBridge::serialize_clock(
            source, barrier.step_sequence, barrier.barrier_sequence);
    artifact.payload.assign(encoded.begin(), encoded.end());
    artifact.payload_sha256 = host::runtime_state_payload_sha256(artifact.payload);
    auto entry = host::RuntimeStateCensusEntry{
        .category = host::RuntimeStateCategory::ClockCadence,
        .disposition = host::RuntimeStateDisposition::Transfer,
        .owner_id = std::string(host::runtime_state_owner_id(
            host::RuntimeStateCategory::ClockCadence)),
        .schema_id = artifact.schema_id,
        .schema_generation = host::kRuntimeStateTransferContractGeneration,
        .state_content_sha256 = artifact.payload_sha256,
        .step_sequence = barrier.step_sequence,
        .barrier_sequence = barrier.barrier_sequence,
    };
    entry.canonical_payload = host::runtime_state_canonical_payload(entry);
    entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(entry.canonical_payload);

    auto trailing = artifact;
    trailing.payload.push_back('x');
    trailing.payload_sha256 = host::runtime_state_payload_sha256(trailing.payload);
    CHECK_THROWS_AS(
        (void)owner->import_state(profile, integration_slot(), entry, trailing, trailing,
                                  {.high = 430, .low = 431}),
        std::runtime_error);
    auto stale_entry = entry;
    ++stale_entry.barrier_sequence;
    stale_entry.canonical_payload = host::runtime_state_canonical_payload(stale_entry);
    stale_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(stale_entry.canonical_payload);
    CHECK_THROWS_AS(
        (void)owner->import_state(profile, integration_slot(), stale_entry, artifact, artifact,
                                  {.high = 432, .low = 433}),
        std::runtime_error);

    auto previous_entry = entry;
    previous_entry.schema_generation = host::kRuntimeStateTransferPreviousGeneration;
    previous_entry.canonical_payload =
        host::runtime_state_canonical_payload(previous_entry);
    previous_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(previous_entry.canonical_payload);
    auto previous_artifact = artifact;
    previous_artifact.schema_generation =
        host::kRuntimeStateTransferPreviousGeneration;
    const auto migrated = owner->migrate_previous(previous_artifact);
    auto imported = owner->import_state(
        profile, integration_slot(), previous_entry, previous_artifact, migrated,
        {.high = 434, .low = 435});
    REQUIRE(imported.transaction != nullptr);
    const auto committed = imported.transaction->commit_with_deadline(20, 100);
    CHECK(committed.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);
    CHECK(integration::SimulationKernelStateOwnerBridge::serialize_clock(
              target, barrier.step_sequence, barrier.barrier_sequence) == encoded);
    imported.transaction.reset();
    registry_base.reset();
    registry.reset();
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("episode owner binds the exact host replacement barrier to its WAL") {
    SimulationKernel target;
    target.reset(29);
    const auto journal_path = std::filesystem::temp_directory_path() /
                              "echelon_forge_p4b_episode_owner.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    auto registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string()),
        .transaction_namespace = "episode-target",
    });
    auto registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(registry_base);
    REQUIRE(registry != nullptr);
    const auto *owner = registry->registration(
        host::RuntimeStateCategory::EpisodeRewardTermination);
    REQUIRE(owner != nullptr);
    const auto barrier = integration_barrier();
    const std::string plan_sha256 = target.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-episode-owner.v2", 1, plan_sha256, plan_sha256);
    auto exported = owner->export_state(
        profile, integration_slot(), integration_export_context(barrier));
    const std::string episode_payload(exported.artifact.payload.begin(),
                                      exported.artifact.payload.end());
    CHECK(episode_payload.find("\"owner_schema\":\"episode-owner.v3\"") !=
          std::string::npos);
    CHECK(episode_payload.find("\"episode_barrier\"") != std::string::npos);
    CHECK(exported.census_entry.step_sequence == barrier.step_sequence);
    CHECK(exported.census_entry.barrier_sequence == barrier.barrier_sequence);
    auto foreign_barrier = barrier;
    ++foreign_barrier.episode.world.incarnation.incarnation_epoch;
    CHECK_THROWS_AS(
        (void)owner->export_state(
            profile, integration_slot(), integration_export_context(foreign_barrier)),
        std::runtime_error);

    const RuntimeIdentity128 candidate_identity{.high = 440, .low = 441};
    auto previous_entry = exported.census_entry;
    previous_entry.schema_generation = host::kRuntimeStateTransferPreviousGeneration;
    previous_entry.canonical_payload =
        host::runtime_state_canonical_payload(previous_entry);
    previous_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(previous_entry.canonical_payload);
    auto previous_artifact = exported.artifact;
    previous_artifact.schema_generation =
        host::kRuntimeStateTransferPreviousGeneration;
    const auto migrated = owner->migrate_previous(previous_artifact);
    auto imported = owner->import_state(profile, integration_slot(), previous_entry,
                                        previous_artifact, migrated,
                                        candidate_identity);
    REQUIRE(imported.transaction != nullptr);
    CHECK(imported.transaction->status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Prepared);
    const auto committed = imported.transaction->commit_with_deadline(20, 100);
    CHECK(committed.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);

    auto stale_entry = exported.census_entry;
    ++stale_entry.step_sequence;
    stale_entry.canonical_payload = host::runtime_state_canonical_payload(stale_entry);
    stale_entry.canonical_payload_sha256 =
        host::runtime_state_payload_sha256(stale_entry.canonical_payload);
    CHECK_THROWS_AS(
        (void)owner->import_state(profile, integration_slot(), stale_entry, previous_artifact,
                                  migrated,
                                  {.high = 442, .low = 443}),
        std::runtime_error);
    auto trailing = exported.artifact;
    trailing.payload.push_back('x');
    trailing.payload_sha256 = host::runtime_state_payload_sha256(trailing.payload);
    CHECK_THROWS_AS(
        (void)owner->import_state(profile, integration_slot(), exported.census_entry, trailing,
                                  trailing, {.high = 444, .low = 445}),
        std::runtime_error);
    imported.transaction.reset();
    registry_base.reset();
    registry.reset();
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("delayed and command owners import N-1 through separate WAL rows") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(81);
    target.reset(82);
    const auto source_unit = source.spawn_unit(
        Side::Blue, "Aircraft", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0,
        180.0, 0.0, 0.0);
    REQUIRE(source_unit.is_valid());
    source.set_command_link(source_unit.id(), 2.0, 0.0);
    MissionCommand pending{};
    pending.active = true;
    pending.command_code = 91;
    pending.cmd_heading_deg = 137.0;
    source.set_mission_command(source_unit.id(), pending);

    const auto source_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_subset_source.wal";
    const auto target_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_subset_target.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
    auto source_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            source_path.string()),
        .transaction_namespace = "subset-source",
    });
    auto target_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            target_path.string()),
        .transaction_namespace = "subset-target",
    });
    auto source_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            source_registry_base);
    auto target_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            target_registry_base);
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);
    const auto barrier = integration_barrier();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-subset-n-minus-one.v2", 1,
        source.resolved_composition_sha256(),
        target.resolved_composition_sha256());

    const auto import_category = [&](host::RuntimeStateCategory category,
                                     RuntimeIdentity128 identity) {
        const auto *source_owner = source_registry->registration(category);
        const auto *target_owner = target_registry->registration(category);
        REQUIRE(source_owner != nullptr);
        REQUIRE(target_owner != nullptr);
        auto exported = source_owner->export_state(
            profile, integration_slot(), integration_export_context(barrier));
        if (category == host::RuntimeStateCategory::DelayedEventsQueues) {
            const auto collision_document = nlohmann::json::parse(
                std::string(exported.artifact.payload.begin(),
                            exported.artifact.payload.end()));
            REQUIRE_FALSE(collision_document.at("results").empty());
            const auto collision_name = collision_document.at("results")
                                            .front()
                                            .at("name")
                                            .get<std::string>();
            flecs::entity collision_entity;
            {
                auto lease = target.acquire_world_lease();
                collision_entity = lease.world().lookup(collision_name.c_str());
                REQUIRE(collision_entity.is_valid());
                collision_entity.remove<SimObject>();
                CHECK_FALSE(collision_entity.has<SimObject>());
            }
            auto collision_import = target_owner->import_state(
                profile, integration_slot(), exported.census_entry,
                exported.artifact, exported.artifact, {.high = 459, .low = 461});
            REQUIRE(collision_import.transaction != nullptr);
            const auto collision_status =
                collision_import.transaction->commit_with_deadline(20, 100);
            CHECK(collision_status.phase ==
                  host::RuntimeStateOwnerImportTransactionPhase::Ambiguous);
            {
                auto lease = target.acquire_world_lease();
                const auto retained = lease.world().lookup(collision_name.c_str());
                REQUIRE(retained.is_valid());
                CHECK_FALSE(retained.has<SimObject>());
                retained.add<SimObject>();
            }
        }
        if (category == host::RuntimeStateCategory::DelayedEventsQueues) {
            auto unknown_document = nlohmann::json::parse(
                std::string(exported.artifact.payload.begin(),
                            exported.artifact.payload.end()));
            unknown_document["unknown_truth"] = true;
            const auto unknown_json = unknown_document.dump();
            auto unknown_artifact = exported.artifact;
            unknown_artifact.payload.assign(unknown_json.begin(),
                                            unknown_json.end());
            unknown_artifact.payload_sha256 =
                host::runtime_state_payload_sha256(unknown_artifact.payload);
            CHECK_THROWS_AS(
                (void)target_owner->import_state(
                    profile, integration_slot(), exported.census_entry, unknown_artifact,
                    unknown_artifact, {.high = 459, .low = 460}),
                std::runtime_error);
        }
        auto previous_entry = exported.census_entry;
        previous_entry.schema_generation =
            host::kRuntimeStateTransferPreviousGeneration;
        previous_entry.canonical_payload =
            host::runtime_state_canonical_payload(previous_entry);
        previous_entry.canonical_payload_sha256 =
            host::runtime_state_payload_sha256(previous_entry.canonical_payload);
        auto previous_artifact = exported.artifact;
        previous_artifact.schema_generation =
            host::kRuntimeStateTransferPreviousGeneration;
        const auto migrated = source_owner->migrate_previous(previous_artifact);
        auto imported = target_owner->import_state(
            profile, integration_slot(), previous_entry, previous_artifact, migrated,
            identity);
        REQUIRE(imported.transaction != nullptr);
        const auto committed = imported.transaction->commit_with_deadline(20, 100);
        CHECK(committed.phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Committed);
        CHECK(committed.durable);
        const auto target_export = target_owner->export_state(
            profile, integration_slot(), integration_export_context(barrier));
        CHECK(target_export.artifact.payload == exported.artifact.payload);
        imported.transaction.reset();
    };

    import_category(host::RuntimeStateCategory::EcsComponentTruth,
                    {.high = 460, .low = 461});
    import_category(host::RuntimeStateCategory::DelayedEventsQueues,
                    {.high = 462, .low = 463});
    import_category(host::RuntimeStateCategory::CommandsLinksPendingIntent,
                    {.high = 464, .low = 465});

    const auto target_name =
        "p4b-simobject-" + std::to_string(source_unit.id());
    std::uint64_t target_unit_id = 0;
    {
        auto lease = target.acquire_world_lease();
        const auto entity = lease.world().lookup(target_name.c_str());
        REQUIRE(entity.is_valid());
        target_unit_id = entity.id();
        const auto *pending_state = entity.get<PendingMissionCommand>();
        REQUIRE(pending_state != nullptr);
        CHECK(pending_state->active);
        CHECK(pending_state->command.command_code == 91);
        CHECK(pending_state->command.cmd_heading_deg == 137.0);
    }
    const auto restored_link = [&] {
        auto lease = target.acquire_world_lease();
        const auto *link = lease.world().entity(target_unit_id).get<CommandLink>();
        REQUIRE(link != nullptr);
        return *link;
    }();
    CHECK(restored_link.latency_s == 2.0);
    CHECK(restored_link.drop_prob == 0.0);

    source_registry_base.reset();
    target_registry_base.reset();
    source_registry.reset();
    target_registry.reset();
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
}

TEST_CASE("composition and explicit policy owners import N-1 durably") {
    SimulationKernel source;
    SimulationKernel target;
    source.reset(17);
    target.reset(29);
    const auto source_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_policy_source_owner.wal";
    const auto target_path = std::filesystem::temp_directory_path() /
                             "echelon_forge_p4b_policy_target_owner.wal";
    std::error_code remove_error;
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
    auto source_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &source,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            source_path.string()),
        .transaction_namespace = "policy-source",
    });
    auto target_registry_base = integration::SimulationKernelStateOwnerBridge::create_registry({
        .kernel = &target,
        .journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            target_path.string()),
        .transaction_namespace = "policy-target",
    });
    auto source_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            source_registry_base);
    auto target_registry =
        std::dynamic_pointer_cast<host::RuntimeStateOwnerAdapterRegistry>(
            target_registry_base);
    REQUIRE(source_registry != nullptr);
    REQUIRE(target_registry != nullptr);
    const auto barrier = integration_barrier();
    const std::string plan_sha256 = source.resolved_composition_sha256();
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "simulation-kernel-policy-owners.v2", 1, plan_sha256, plan_sha256);

    const std::array categories{
        host::RuntimeStateCategory::CompositionProviderSystemGraph,
        host::RuntimeStateCategory::PythonLoaderControllerCaches,
        host::RuntimeStateCategory::BackendDeviceAllocationsLeases,
        host::RuntimeStateCategory::InFlightRequestsResults,
        host::RuntimeStateCategory::ExternalSideEffects,
        host::RuntimeStateCategory::DiagnosticsTelemetry,
    };
    std::uint64_t candidate_low = 451;
    for (const auto category : categories) {
        const auto *source_owner = source_registry->registration(category);
        const auto *target_owner = target_registry->registration(category);
        REQUIRE(source_owner != nullptr);
        REQUIRE(target_owner != nullptr);
        auto exported = source_owner->export_state(
            profile, integration_slot(), integration_export_context(barrier));
        const std::string encoded(exported.artifact.payload.begin(),
                                  exported.artifact.payload.end());
        if (category ==
            host::RuntimeStateCategory::CompositionProviderSystemGraph) {
            CHECK(encoded.starts_with("composition.v2\n"));
            CHECK(encoded.find(plan_sha256) != std::string::npos);
        } else if (category ==
                   host::RuntimeStateCategory::PythonLoaderControllerCaches) {
            CHECK(encoded.starts_with("python-mirror-rederive.v2\n"));
            CHECK(encoded.find("cache_transfer=forbidden") != std::string::npos);
        } else if (category ==
                   host::RuntimeStateCategory::BackendDeviceAllocationsLeases) {
            CHECK(encoded.starts_with("backend-resource-rederive.v2\n"));
            CHECK(encoded.find("backend_profile_id=cpu_exact.reference") !=
                  std::string::npos);
            CHECK(encoded.find("raw_handle_transfer=forbidden") !=
                  std::string::npos);
        } else if (category ==
                   host::RuntimeStateCategory::InFlightRequestsResults) {
            CHECK(encoded.starts_with("in-flight-drain.v2\n"));
            CHECK(encoded.find("truth_mutating_remaining=0") !=
                  std::string::npos);
            CHECK(encoded.find("cancellation_acknowledged=1") !=
                  std::string::npos);
        } else if (category == host::RuntimeStateCategory::ExternalSideEffects) {
            CHECK(encoded.find("disposition=not-applicable") != std::string::npos);
            CHECK(encoded.find("external_receipt_count=0") != std::string::npos);
        } else {
            CHECK(encoded.find("disposition=rederive") != std::string::npos);
            CHECK(encoded.find("continuity=reset-at-target") != std::string::npos);
        }

        auto previous_entry = exported.census_entry;
        previous_entry.schema_generation =
            host::kRuntimeStateTransferPreviousGeneration;
        previous_entry.canonical_payload =
            host::runtime_state_canonical_payload(previous_entry);
        previous_entry.canonical_payload_sha256 =
            host::runtime_state_payload_sha256(previous_entry.canonical_payload);
        auto previous_artifact = exported.artifact;
        previous_artifact.schema_generation =
            host::kRuntimeStateTransferPreviousGeneration;
        const auto migrated = source_owner->migrate_previous(previous_artifact);
        auto imported = target_owner->import_state(
            profile, integration_slot(), previous_entry, previous_artifact, migrated,
            {.high = 450, .low = candidate_low++});
        REQUIRE(imported.transaction != nullptr);
        const auto committed = imported.transaction->commit_with_deadline(20, 100);
        CHECK(committed.phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Committed);
        CHECK(committed.durable);
        imported.transaction.reset();

        if (category ==
            host::RuntimeStateCategory::CompositionProviderSystemGraph) {
            const auto mismatched_profile =
                host::runtime_state_transfer_profile_from_decoder_matrix(
                    "simulation-kernel-policy-mismatch.v2", 1,
                    plan_sha256, std::string(64, 'b'));
            CHECK_THROWS_AS(
                (void)target_owner->import_state(
                    mismatched_profile, integration_slot(), previous_entry, previous_artifact,
                    migrated, {.high = 450, .low = candidate_low++}),
                std::runtime_error);
        } else if (category == host::RuntimeStateCategory::ExternalSideEffects) {
            auto trailing = migrated;
            trailing.payload.push_back('x');
            trailing.payload_sha256 =
                host::runtime_state_payload_sha256(trailing.payload);
            CHECK_THROWS_AS(
                (void)target_owner->import_state(
                    profile, integration_slot(), previous_entry, previous_artifact, trailing,
                    {.high = 450, .low = candidate_low++}),
                std::runtime_error);
        } else {
            auto stale_entry = previous_entry;
            ++stale_entry.barrier_sequence;
            stale_entry.canonical_payload =
                host::runtime_state_canonical_payload(stale_entry);
            stale_entry.canonical_payload_sha256 =
                host::runtime_state_payload_sha256(stale_entry.canonical_payload);
            CHECK_THROWS_AS(
                (void)target_owner->import_state(
                    profile, integration_slot(), stale_entry, previous_artifact, migrated,
                    {.high = 450, .low = candidate_low++}),
                std::runtime_error);
        }
    }
    source_registry_base.reset();
    target_registry_base.reset();
    source_registry.reset();
    target_registry.reset();
    std::filesystem::remove(source_path, remove_error);
    std::filesystem::remove(target_path, remove_error);
}

} // TEST_SUITE
