#include "runtime_host_candidate.h"

#include <doctest/doctest.h>

#include <atomic>
#include <barrier>
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace {

namespace host = runtime::host;
using echelon_forge::runtime_contracts::v1::RuntimeEntityRef;
using echelon_forge::runtime_contracts::v1::RuntimeEpisodeRef;
using echelon_forge::runtime_contracts::v1::RuntimeHostIdentity;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;
using echelon_forge::runtime_contracts::v1::RuntimeResultRef;
using echelon_forge::runtime_contracts::v1::RuntimeWorldRef;

constexpr const char *kHash =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
constexpr const char *kHash2 =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

RuntimeIdentity128 logical_host_id(std::uint64_t low = 2) {
    return {.high = 1, .low = low};
}

host::RuntimePlanBinding plan(std::string id = "plan.v1", std::string hash = kHash) {
    return {.plan_id = std::move(id), .plan_sha256 = std::move(hash)};
}

RuntimeEpisodeRef episode(const RuntimeIncarnationRef &slot, std::uint64_t generation = 1) {
    return {
        .world = {
            .incarnation = slot,
            .world_slot = 0,
            .world_generation = 1,
        },
        .episode_id = {.high = 4, .low = 5},
        .episode_generation = generation,
    };
}

std::shared_ptr<host::RuntimeStateTransferOwnerRegistry>
make_transfer_owner_registry();

class FakeControl final : public host::RuntimeInstanceControl {
  public:
    class NativeControl final : public host::RuntimeNativeEpisodeControl {
      public:
        explicit NativeControl(RuntimeIdentity128 resource) : resource_(resource) {}
        [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
            return resource_;
        }
        [[nodiscard]] host::RuntimeNativeEpisodeMutation
        apply(const host::RuntimeNativeEpisodeCommand &) noexcept override {
            return {.applied = true,
                    .terminal = terminal_,
                    .snapshot_id = {.high = 91, .low = 92},
                    .snapshot_sha256 = kHash};
        }
        void set_terminal(bool terminal) noexcept { terminal_ = terminal; }

      private:
        RuntimeIdentity128 resource_;
        bool terminal_ = true;
    };

    explicit FakeControl(bool release_result = true,
                         std::optional<RuntimeIdentity128> resource_identity = std::nullopt)
        : release_result_(release_result),
          resource_identity_(resource_identity.value_or(
              RuntimeIdentity128{.high = 9, .low = next_identity.fetch_add(1)})),
          native_episode_control_(
              std::make_shared<NativeControl>(resource_identity_)),
          owner_registry_(make_transfer_owner_registry()) {}

    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
        return resource_identity_;
    }

    [[nodiscard]] std::shared_ptr<host::RuntimeNativeEpisodeControl>
    native_episode_control() const noexcept override {
        return native_episode_control_;
    }

    [[nodiscard]] std::shared_ptr<host::RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept override {
        return owner_registry_;
    }

    [[nodiscard]] bool request_cooperative_cancel() noexcept override {
        ++cancel_calls;
        return cancel_acknowledged;
    }

    [[nodiscard]] bool release_resources() noexcept override {
        ++release_calls;
        released = release_result_;
        return release_result_;
    }

    [[nodiscard]] bool resources_released() const noexcept override { return released; }

    void allow_release() noexcept { release_result_ = true; }
    void set_native_terminal(bool terminal) noexcept {
        native_episode_control_->set_terminal(terminal);
    }

    int cancel_calls = 0;
    int release_calls = 0;
    bool released = false;
    bool cancel_acknowledged = true;

  private:
    inline static std::atomic<std::uint64_t> next_identity{1};
    bool release_result_ = true;
    RuntimeIdentity128 resource_identity_;
    std::shared_ptr<NativeControl> native_episode_control_;
    std::shared_ptr<host::RuntimeStateTransferOwnerRegistry> owner_registry_;
};

class OneShotCasLoss final : public host::RuntimeHostCasFaultInjector {
  public:
    explicit OneShotCasLoss(host::RuntimeSlotCasOperation operation) : operation_(operation) {}

    [[nodiscard]] bool force_loss(host::RuntimeSlotCasOperation operation) noexcept override {
        if (!consumed_ && operation == operation_) {
            consumed_ = true;
            return true;
        }
        return false;
    }

  private:
    host::RuntimeSlotCasOperation operation_;
    bool consumed_ = false;
};

class ReentrantCasLoss final : public host::RuntimeHostCasFaultInjector {
  public:
    host::RuntimeHostCandidate *runtime = nullptr;
    host::RuntimeSlotCasOperation operation = host::RuntimeSlotCasOperation::InitialPublish;
    bool observed = false;

    [[nodiscard]] bool force_loss(host::RuntimeSlotCasOperation current) noexcept override {
        if (current != operation) {
            return false;
        }
        if (runtime != nullptr) {
            (void)runtime->snapshot();
        }
        observed = true;
        return true;
    }
};

std::shared_ptr<FakeControl> make_control(bool release_result = true) {
    return std::make_shared<FakeControl>(release_result);
}

host::RuntimeCandidateValidationProof validation() {
    return {
        .static_plan_validated = true,
        .resources_ready = true,
        .shadow_probe_passed = true,
        .unreachable_from_production = true,
        .production_authorized = false,
    };
}

host::RuntimeInitialCommitProof initial_proof() {
    return {
        .lifecycle_evidence_sha256 = kHash,
        .dark_evidence_sealed = true,
        .production_authorized = false,
    };
}

class NoopImportTransaction final : public host::RuntimeStateOwnerImportTransaction {
  public:
    void commit() noexcept override {}
    void abort() noexcept override {}
};

class TransferOwnerRegistry final : public host::RuntimeStateTransferOwnerRegistry {
  public:
    [[nodiscard]] host::RuntimeStateOwnerExport export_source(
        const host::RuntimeStateTransferProfile &profile,
        const RuntimeIncarnationRef &source_slot,
        const host::RuntimeEpisodeCoordinatorSnapshot &barrier_snapshot) noexcept override {
        host::RuntimeStateOwnerExport exported;
        exported.source_slot = source_slot;
        exported.census = {.profile_id = profile.profile_id,
                            .profile_generation = profile.profile_generation,
                            .source_slot = source_slot,
                            .source_plan_sha256 = profile.source_plan_sha256,
                            .target_plan_sha256 = profile.target_plan_sha256};
        try {
            for (const auto &policy : profile.rows) {
                host::RuntimeStateCensusEntry entry{
                    .category = policy.category,
                    .disposition = policy.disposition,
                    .owner_id = policy.owner_id,
                    .schema_id = policy.schema_id,
                    .schema_generation = 1,
                    .step_sequence = barrier_snapshot.step_sequence,
                    .barrier_sequence = barrier_snapshot.barrier_sequence,
                };
                if (policy.disposition == host::RuntimeStateDisposition::Transfer) {
                    entry.state_content_sha256 = kHash;
                    entry.canonical_payload = host::runtime_state_canonical_payload(entry);
                    entry.canonical_payload_sha256 =
                        host::runtime_state_payload_sha256(entry.canonical_payload);
                    entry.semantic_evidence_sha256 = kHash;
                } else if (policy.disposition == host::RuntimeStateDisposition::Rederive ||
                           policy.disposition == host::RuntimeStateDisposition::Drain) {
                    entry.semantic_evidence_sha256 = kHash;
                }
                host::RuntimeStateOwnerArtifact artifact{
                    .category = entry.category,
                    .schema_id = entry.schema_id,
                    .schema_generation = entry.schema_generation,
                    .payload = entry.canonical_payload.empty()
                                   ? host::runtime_state_canonical_payload(entry)
                                   : entry.canonical_payload,
                };
                artifact.payload_sha256 = host::runtime_state_payload_sha256(artifact.payload);
                exported.artifacts.push_back(std::move(artifact));
                exported.census.entries.push_back(std::move(entry));
            }
        } catch (...) {
            exported.status = {.error = host::RuntimeStateTransferError::SemanticEvidenceMissing,
                               .detail = "fixture source export allocation failed"};
        }
        return exported;
    }

    [[nodiscard]] host::RuntimeStateOwnerImportReceipt import_and_observe(
        const host::RuntimeStateTransferProfile &,
        const host::RuntimeStateOwnerExport &source_export,
        const RuntimeIdentity128 &candidate_resource_identity) noexcept override {
        host::RuntimeStateOwnerImportReceipt receipt;
        receipt.candidate_resource_identity = candidate_resource_identity;
        try {
            for (const auto &entry : source_export.census.entries) {
                const auto artifact = std::find_if(
                    source_export.artifacts.begin(), source_export.artifacts.end(),
                    [&](const auto &candidate) {
                        return candidate.category == entry.category;
                    });
                if (artifact == source_export.artifacts.end()) {
                    receipt.status = {
                        .error = host::RuntimeStateTransferError::MissingCategory,
                        .detail = "fixture import has no source artifact"};
                    return receipt;
                }
                receipt.observations.push_back({
                    .category = entry.category,
                    .owner_id = entry.owner_id,
                    .schema_id = entry.schema_id,
                    .schema_generation = entry.schema_generation,
                    .source_entry_sha256 =
                        host::runtime_state_census_entry_sha256(entry),
                    .candidate_entry_sha256 =
                        host::runtime_state_census_entry_sha256(entry),
                    .source_artifact_payload_sha256 = artifact->payload_sha256,
                    .candidate_artifact_payload_sha256 = artifact->payload_sha256,
                    .semantic_replay_sha256 = entry.semantic_evidence_sha256,
                    .candidate_resource_identity = candidate_resource_identity,
                    .item_count = entry.item_count,
                    .settled_item_count = entry.settled_item_count,
                    .source_schema_generation = entry.schema_generation,
                    .exact_schema_decoded = true,
                });
                auto &observation = receipt.observations.back();
                auto normalized = entry;
                normalized.schema_generation =
                    host::kRuntimeStateTransferContractGeneration;
                if (entry.schema_generation !=
                    host::kRuntimeStateTransferContractGeneration) {
                    normalized.canonical_payload =
                        host::runtime_state_canonical_payload(normalized);
                    normalized.canonical_payload_sha256 =
                        host::runtime_state_payload_sha256(normalized.canonical_payload);
                }
                observation.schema_generation =
                    host::kRuntimeStateTransferContractGeneration;
                observation.candidate_entry_sha256 =
                    host::runtime_state_census_entry_sha256(normalized);
            }
            receipt.transaction = std::make_shared<NoopImportTransaction>();
            return receipt;
        } catch (...) {
            receipt.status = {.error = host::RuntimeStateTransferError::SemanticEvidenceMissing,
                              .detail = "fixture owner allocation failed"};
            return receipt;
        }
    }
};

std::shared_ptr<host::RuntimeStateTransferOwnerRegistry>
make_transfer_owner_registry() {
    return std::make_shared<TransferOwnerRegistry>();
}

host::RuntimeTransferCommitProof transfer_proof(host::RuntimeHostCandidate &runtime,
                                                 const host::RuntimeCandidateHandle &handle,
                                                 const RuntimeIncarnationRef &source,
                                                 std::uint64_t deadline = 10,
                                                 std::string source_plan = kHash) {
    const auto episode_admission = runtime.issue_shadow_episode(0);
    host::RuntimeEpisodeBarrierAdmission barrier;
    host::RuntimeReplacementQuiescenceResult quiescence;
    if (episode_admission.status) {
        const RuntimeEpisodeRef current_episode = episode_admission.capability.episode();
        const auto terminal = runtime.submit_shadow_episode(
            episode_admission.capability,
            {.kind = host::RuntimeEpisodeIntentKind::Action,
             .expected_episode = current_episode,
             .expected_step_sequence = 0,
             .idempotency_key = {.high = 83, .low = 84},
             .payload_sha256 = kHash});
        REQUIRE_MESSAGE(terminal.status, terminal.status.detail);
    }
    quiescence = runtime.quiesce_replacement_source(handle);
    if (!quiescence.status) {
        return {};
    }
    barrier = runtime.open_shadow_replacement_barrier(0);
    REQUIRE(barrier.status);
    const auto barrier_snapshot = barrier.capability.snapshot();
    const std::uint64_t host_fence = quiescence.capability.mutation_fence_sequence();

    const std::vector<std::pair<host::RuntimeStateCategory,
                                host::RuntimeStateDisposition>> rules = {
        {host::RuntimeStateCategory::CompositionProviderSystemGraph,
         host::RuntimeStateDisposition::Rederive},
        {host::RuntimeStateCategory::EcsComponentTruth,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::RngState,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::ClockCadence,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::DelayedEventsQueues,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::CommandsLinksPendingIntent,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::EpisodeRewardTermination,
         host::RuntimeStateDisposition::Transfer},
        {host::RuntimeStateCategory::PythonLoaderControllerCaches,
         host::RuntimeStateDisposition::Rederive},
        {host::RuntimeStateCategory::BackendDeviceAllocationsLeases,
         host::RuntimeStateDisposition::Rederive},
        {host::RuntimeStateCategory::InFlightRequestsResults,
         host::RuntimeStateDisposition::Drain},
        {host::RuntimeStateCategory::ExternalSideEffects,
         host::RuntimeStateDisposition::NotApplicable},
        {host::RuntimeStateCategory::DiagnosticsTelemetry,
         host::RuntimeStateDisposition::Rederive},
    };
    host::RuntimeStateTransferProfile profile{
        .profile_id = "host-test-profile",
        .profile_generation = 1,
        .source_plan_sha256 = std::move(source_plan),
        .target_plan_sha256 = kHash2,
    };
    host::RuntimeStateCensus census{
        .profile_id = profile.profile_id,
        .profile_generation = profile.profile_generation,
        .source_slot = source,
        .source_plan_sha256 = profile.source_plan_sha256,
        .target_plan_sha256 = profile.target_plan_sha256,
    };
    for (const auto &[category, disposition] : rules) {
        const std::string owner(host::runtime_state_owner_id(category));
        const std::string schema(host::runtime_state_schema_id(category));
        const bool truth = category == host::RuntimeStateCategory::EcsComponentTruth ||
                           category == host::RuntimeStateCategory::RngState ||
                           category == host::RuntimeStateCategory::ClockCadence ||
                           category == host::RuntimeStateCategory::DelayedEventsQueues ||
                           category == host::RuntimeStateCategory::CommandsLinksPendingIntent ||
                           category == host::RuntimeStateCategory::EpisodeRewardTermination;
        profile.rows.push_back({.category = category,
                                .disposition = disposition,
                                .owner_id = owner,
                                .schema_id = schema,
                                .minimum_schema_generation = 1,
                                .maximum_schema_generation = 1,
                                .truth_affecting = truth});
        host::RuntimeStateCensusEntry entry{
            .category = category,
            .disposition = disposition,
            .owner_id = owner,
            .schema_id = schema,
            .schema_generation = 1,
            .step_sequence = barrier_snapshot.step_sequence,
            .barrier_sequence = barrier_snapshot.barrier_sequence,
        };
        if (disposition == host::RuntimeStateDisposition::Transfer) {
            entry.state_content_sha256 = kHash;
            entry.canonical_payload = host::runtime_state_canonical_payload(entry);
            entry.canonical_payload_sha256 =
                host::runtime_state_payload_sha256(entry.canonical_payload);
            entry.semantic_evidence_sha256 = kHash;
        } else if (disposition == host::RuntimeStateDisposition::Rederive ||
                   disposition == host::RuntimeStateDisposition::Drain) {
            entry.semantic_evidence_sha256 = kHash;
        }
        census.entries.push_back(std::move(entry));
    }
    auto validated = host::RuntimeStateTransferValidator::validate({
        .profile = std::move(profile),
        .census = std::move(census),
        .evidence = {.source_final_mutation_fence_sequence = host_fence,
                    },
        .host_quiescence = std::move(quiescence.capability),
        .episode_barrier = std::move(barrier.capability),
    });
    if (!validated.status) {
        return {};
    }
    return {.validated_transfer = std::move(validated.transfer),
            .production_authorized = false,
            .drain_deadline_tick = deadline};
}

host::RuntimeRecoveryCommitProof recovery_proof(const RuntimeIncarnationRef &source,
                                                std::uint64_t deadline = 10) {
    return {
        .source_faulted_slot = source,
        .checkpoint_id = "checkpoint.v1",
        .checkpoint_sha256 = kHash2,
        .checkpoint_admitted = true,
        .source_truth_exported = false,
        .candidate_import_probe_passed = true,
        .production_authorized = false,
        .drain_deadline_tick = deadline,
    };
}

RuntimeIncarnationRef publish_initial(host::RuntimeHostCandidate &runtime,
                                      const std::shared_ptr<FakeControl> &control) {
    const auto begun = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .expected_slot = std::nullopt,
        .plan = plan(),
        .control = control,
        .lifecycle_deadline_tick = 20,
        .world_slot_count = 1,
    });
    REQUIRE(begun.status);
    REQUIRE(runtime.validate_candidate(begun.handle, validation()));
    const auto published = runtime.commit_initial(begun.handle, initial_proof());
    REQUIRE(published.status);
    return published.published_slot;
}

host::RuntimeShadowEpisodeAdmission try_admit_episode(
    host::RuntimeHostCandidate &runtime, const RuntimeIncarnationRef &slot,
    std::uint64_t generation = 0) {
    (void)generation;
    const auto current = runtime.snapshot().active;
    if (!current.has_value() || current->incarnation != slot) {
        return {.status = {.error = host::RuntimeHostError::StaleReference,
                           .detail = "episode slot is not current"},
                .capability = {}};
    }
    return runtime.issue_shadow_episode(0);
}

host::RuntimeShadowEpisodeCapability admit_episode(
    host::RuntimeHostCandidate &runtime, const RuntimeIncarnationRef &slot,
    std::uint64_t generation = 0) {
    auto admitted = try_admit_episode(runtime, slot, generation);
    REQUIRE(admitted.status);
    REQUIRE(admitted.capability.valid());
    return admitted.capability;
}

host::RuntimeLeaseAdmission acquire(host::RuntimeHostCandidate &runtime,
                                    const RuntimeIncarnationRef &slot,
                                    host::RuntimeLeaseKind kind) {
    return runtime.acquire_lease(admit_episode(runtime, slot), kind);
}

} // namespace

TEST_SUITE("runtime_host_candidate") {

TEST_CASE("initial publication is dark-only and admits identity-bound leases") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const auto control = make_control();
    const RuntimeIncarnationRef first = publish_initial(runtime, control);

    const auto snapshot = runtime.snapshot();
    REQUIRE(snapshot.active.has_value());
    CHECK(snapshot.state == host::RuntimeHostState::Active);
    CHECK(snapshot.active->incarnation == first);
    CHECK(snapshot.active->incarnation.incarnation_epoch == 1);
    CHECK_FALSE(snapshot.production_authorized);

    const auto admitted = acquire(runtime, first, host::RuntimeLeaseKind::TruthMutating);
    REQUIRE(admitted.status);
    REQUIRE(admitted.lease.valid());
    CHECK(admitted.request_ref.request_sequence == 1);
    const RuntimeResultRef result{.request = admitted.request_ref};
    CHECK(runtime.validate_result(admitted.lease, result));
    CHECK(runtime.validate_result(admitted.lease, result).error ==
          host::RuntimeHostError::DuplicateResult);
    CHECK_FALSE(runtime.validate_result(admitted.lease, RuntimeResultRef{}));

    const auto bad_begin = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = plan(),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    CHECK_FALSE(bad_begin.status);
    CHECK(bad_begin.status.error == host::RuntimeHostError::HostStateMismatch);
}

TEST_CASE("host admission is fenced by the live native coordinator step") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(71),
                                        .mode = host::RuntimeHostMode::Shadow});
    const auto active_control = make_control();
    active_control->set_native_terminal(false);
    const RuntimeIncarnationRef active = publish_initial(runtime, active_control);
    auto admitted = runtime.issue_shadow_episode(0);
    REQUIRE(admitted.status);
    auto first = runtime.acquire_lease(admitted.capability,
                                       host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(first.status);
    first.lease.settle();

    REQUIRE(runtime.submit_shadow_episode(
        admitted.capability,
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = admitted.capability.episode(),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 705, .low = 706},
         .payload_sha256 = kHash}).status);
    CHECK(runtime.acquire_lease(admitted.capability,
                                host::RuntimeLeaseKind::ReadOnlyResult)
              .status.error == host::RuntimeHostError::StaleReference);
}

TEST_CASE("host episode submission requires the admitted shadow capability") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(75),
                                        .mode = host::RuntimeHostMode::Shadow});
    publish_initial(runtime, make_control());
    const auto admitted = runtime.issue_shadow_episode(0);
    REQUIRE(admitted.status);
    const auto forged = runtime.submit_shadow_episode(
        host::RuntimeShadowEpisodeCapability{},
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = admitted.capability.episode(),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 750, .low = 751},
         .payload_sha256 = kHash});
    CHECK(forged.status.error == host::RuntimeStateTransferError::StaleIntent);
}

TEST_CASE("host rejects a coordinator capability that is not slot-owned") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(73),
                                        .mode = host::RuntimeHostMode::Shadow});
    const RuntimeIncarnationRef active = publish_initial(runtime, make_control());
    RuntimeEpisodeRef forged = episode(active);
    forged.world.world_generation = 2;
    auto external = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = forged,
        .initial_snapshot_id = {.high = 730, .low = 731},
        .initial_snapshot_sha256 = kHash2,
    });
    REQUIRE(external.status);
    auto native = external.coordinator->issue_episode_capability();
    REQUIRE(native.status);
    CHECK(runtime.admit_shadow_episode(std::move(native.capability)).status.error ==
          host::RuntimeHostError::StaleReference);
}

TEST_CASE("host cannot open a replacement barrier before host quiescence") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(74),
                                        .mode = host::RuntimeHostMode::Shadow});
    const RuntimeIncarnationRef active = publish_initial(runtime, make_control());
    const auto episode_admission = runtime.issue_shadow_episode(0);
    REQUIRE(episode_admission.status);
    CHECK(runtime.open_shadow_replacement_barrier(
              episode_admission.capability.episode(), 0)
              .status.error == host::RuntimeStateTransferError::StaleIntent);
    CHECK(runtime.snapshot().active->state == host::RuntimeSlotState::Active);
    CHECK(runtime.snapshot().active->incarnation == active);
}

TEST_CASE("host rejects a validated transfer whose source plan does not match the active slot") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(72),
                                        .mode = host::RuntimeHostMode::Shadow});
    const RuntimeIncarnationRef active = publish_initial(runtime, make_control());
    const auto candidate = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = active,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(candidate.status);
    REQUIRE(runtime.validate_candidate(candidate.handle, validation()));
    CHECK(runtime.prepare_replacement(candidate.handle,
                                      transfer_proof(runtime, candidate.handle, active, 10, kHash2))
              .error == host::RuntimeHostError::InvalidCommitProof);
    // A rejected transfer must roll the source back to an active, retryable
    // state; a failed validation may not strand the host in Quiescing.
    CHECK(runtime.snapshot().active->admission_open);
    CHECK(runtime.abort_candidate(candidate.handle));
}

TEST_CASE("lease settlement and terminal-result admission share one mutex linearization") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef slot = publish_initial(runtime, make_control());

    for (int iteration = 0; iteration < 64; ++iteration) {
        auto admitted = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
        REQUIRE(admitted.status);
        const RuntimeResultRef result{.request = admitted.request_ref};
        host::RuntimeHostStatus validation_status;
        std::barrier start(3);
        std::thread validator([&] {
            start.arrive_and_wait();
            validation_status = runtime.validate_result(admitted.lease, result);
        });
        std::thread settler([&] {
            start.arrive_and_wait();
            admitted.lease.settle();
        });
        start.arrive_and_wait();
        validator.join();
        settler.join();

        CHECK((validation_status.error == host::RuntimeHostError::None ||
               validation_status.error == host::RuntimeHostError::StaleReference));
        CHECK_FALSE(admitted.lease.valid());
        CHECK(runtime.validate_result(admitted.lease, result).error ==
              host::RuntimeHostError::StaleReference);
    }
    REQUIRE(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().active->read_only_result_leases == 0);
}

TEST_CASE("replacement closes admission, fences truth leases, and retires a tombstoned slot") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const auto old_control = make_control();
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, old_control);
    auto truth = acquire(runtime, old_slot, host::RuntimeLeaseKind::TruthMutating);
    auto read = acquire(runtime, old_slot, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(truth.status);
    REQUIRE(read.status);

    const auto begun = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(begun.status);
    REQUIRE(runtime.validate_candidate(begun.handle, validation()));
    CHECK(runtime.prepare_replacement(begun.handle,
                                      transfer_proof(runtime, begun.handle, old_slot)).error ==
          host::RuntimeHostError::InvalidCommitProof);
    CHECK(old_control->cancel_calls == 1);
    CHECK_FALSE(try_admit_episode(runtime, old_slot).status);

    truth.lease = {};
    REQUIRE(runtime.prepare_replacement(
        begun.handle, transfer_proof(runtime, begun.handle, old_slot)));
    const auto published = runtime.commit_prepared_candidate(begun.handle);
    REQUIRE(published.status);
    CHECK(published.published_slot.incarnation_epoch == 2);
    REQUIRE(runtime.validate_result(read.lease, RuntimeResultRef{.request = read.request_ref}));
    CHECK_FALSE(runtime.validate_result(read.lease, RuntimeResultRef{.request = truth.request_ref}));

    read.lease = {};
    REQUIRE(runtime.poll(10));
    const auto after = runtime.snapshot();
    CHECK_FALSE(after.draining.has_value());
    REQUIRE(after.active.has_value());
    CHECK(after.retired_incarnation_high_watermark == old_slot.incarnation_epoch);
    CHECK(old_control->release_calls == 1);
    CHECK_FALSE(try_admit_episode(runtime, old_slot).status);
}

TEST_CASE("replacement abort reopens the same active epoch, while recovery rejects faulted truth export") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Shadow});
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());

    const auto replacement_control = make_control();
    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = replacement_control,
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
    CHECK(runtime.prepare_replacement(
        replacement.handle, transfer_proof(runtime, replacement.handle, old_slot)));
    REQUIRE(runtime.abort_candidate(replacement.handle));
    REQUIRE(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().active->incarnation == old_slot);
    CHECK(runtime.snapshot().active->admission_open);
    CHECK(replacement_control->release_calls == 1);

    REQUIRE(runtime.mark_active_faulted(old_slot, 20));
    const auto recovery = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::CheckpointRecovery,
        .expected_slot = old_slot,
        .plan = plan("plan.recovery", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(recovery.status);
    REQUIRE(runtime.validate_candidate(recovery.handle, validation()));
    auto invalid = recovery_proof(old_slot);
    invalid.source_truth_exported = true;
    CHECK(runtime.prepare_checkpoint_recovery(recovery.handle, invalid).error ==
          host::RuntimeHostError::InvalidCommitProof);
    CHECK(runtime.abort_candidate(recovery.handle));
    CHECK(runtime.snapshot().state == host::RuntimeHostState::Faulted);
    CHECK(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().active->state == host::RuntimeSlotState::ActiveFaulted);

    const auto retry = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::CheckpointRecovery,
        .expected_slot = old_slot,
        .plan = plan("plan.recovery.retry", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(retry.status);
    REQUIRE(runtime.validate_candidate(retry.handle, validation()));
    REQUIRE(runtime.prepare_checkpoint_recovery(retry.handle, recovery_proof(old_slot)));
    const auto recovered = runtime.commit_prepared_candidate(retry.handle);
    REQUIRE(recovered.status);
    CHECK(recovered.published_slot.incarnation_epoch == 2);
    CHECK_FALSE(runtime.validate_result(
        acquire(runtime, recovered.published_slot, host::RuntimeLeaseKind::ReadOnlyResult)
            .lease,
        RuntimeResultRef{}));
}

TEST_CASE("drain timeout quarantines leased resources and later retry unfreezes replacement") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const auto old_control = make_control();
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, old_control);
    auto read = acquire(runtime, old_slot, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(read.status);

    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
    REQUIRE(runtime.prepare_replacement(
        replacement.handle, transfer_proof(runtime, replacement.handle, old_slot, 3)));
    REQUIRE(runtime.commit_prepared_candidate(replacement.handle).status);
    CHECK(runtime.poll(2));
    CHECK(runtime.poll(3).error == host::RuntimeHostError::QuarantineUnresolved);
    CHECK(runtime.snapshot().quarantined.size() == 1);
    CHECK(runtime.begin_candidate({
              .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
              .expected_slot = runtime.snapshot().active->incarnation,
              .plan = plan("plan.v3", kHash),
              .control = make_control(),
              .lifecycle_deadline_tick = 20,
          })
              .status.error == host::RuntimeHostError::QuarantineBackpressure);

    read.lease = {};
    REQUIRE(runtime.retry_quarantined_reclamation());
    CHECK(runtime.snapshot().quarantined.empty());
    CHECK(old_control->release_calls == 1);
}

TEST_CASE("shutdown is terminal, idempotent, and never publishes a candidate") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef slot = publish_initial(runtime, make_control());
    auto read = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(read.status);

    const auto first = runtime.begin_shutdown(0, 4);
    CHECK(first.shutdown_ticket != 0);
    CHECK(first.state == host::RuntimeHostState::ShuttingDown);
    const auto repeated = runtime.begin_shutdown(1, 99);
    CHECK(repeated.shutdown_ticket == first.shutdown_ticket);
    CHECK(repeated.state == host::RuntimeHostState::ShuttingDown);
    CHECK(runtime.snapshot().active == std::nullopt);
    CHECK(runtime.begin_candidate({
              .transaction_kind = host::RuntimeHostTransactionKind::Initial,
              .plan = plan(),
              .control = make_control(),
              .lifecycle_deadline_tick = 20,
          })
              .status.error == host::RuntimeHostError::HostTerminal);

    CHECK(runtime.poll(4).error == host::RuntimeHostError::QuarantineUnresolved);
    read.lease = {};
    const auto final = runtime.snapshot();
    CHECK(final.state == host::RuntimeHostState::Stopped);
    CHECK(runtime.begin_shutdown(5, 5).state == host::RuntimeHostState::Stopped);
}

TEST_CASE("shutdown lease release does not use the deadline as an early clock sample") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef slot = publish_initial(runtime, make_control());
    auto first = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
    auto second = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(first.status);
    REQUIRE(second.status);

    REQUIRE(runtime.begin_shutdown(0, 10).state == host::RuntimeHostState::ShuttingDown);
    first.lease = {};
    const auto after_first = runtime.snapshot();
    CHECK(after_first.state == host::RuntimeHostState::ShuttingDown);
    CHECK(after_first.draining.has_value());
    CHECK(after_first.quarantined.empty());

    second.lease = {};
    CHECK(runtime.snapshot().state == host::RuntimeHostState::Stopped);
}

TEST_CASE("shutdown deadline retains a slot whose cancellation is not acknowledged") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const auto control = make_control();
    control->cancel_acknowledged = false;
    (void)publish_initial(runtime, control);
    CHECK(runtime.begin_shutdown(0, 3).status.error ==
          host::RuntimeHostError::CancellationPending);
    CHECK(runtime.poll(2).error == host::RuntimeHostError::CancellationPending);
    CHECK(runtime.poll(3).error == host::RuntimeHostError::ShutdownPending);
    CHECK(runtime.snapshot().quarantined.size() == 1);
    REQUIRE(runtime.retry_quarantined_reclamation());
    CHECK(runtime.snapshot().state == host::RuntimeHostState::Stopped);
}

TEST_CASE("restart boot identity rejects references from the previous process") {
    host::RuntimeHostCandidate first_runtime(
        {.host_id = logical_host_id(2), .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef old_slot = publish_initial(first_runtime, make_control());
    const auto old_episode = admit_episode(first_runtime, old_slot);

    host::RuntimeHostCandidate restarted(
        {.host_id = logical_host_id(2), .mode = host::RuntimeHostMode::Dark});
    CHECK_FALSE(restarted.acquire_lease(old_episode, host::RuntimeLeaseKind::ReadOnlyResult).status);
    CHECK(restarted.snapshot().identity.boot_id != old_slot.host.boot_id);
}

TEST_CASE("unsupported enum values fail closed and move assignment settles the replaced host") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(), .mode = host::RuntimeHostMode::Dark});
    const auto invalid_begin = runtime.begin_candidate({
        .transaction_kind = static_cast<host::RuntimeHostTransactionKind>(255),
        .plan = plan(),
        .control = make_control(),
    });
    CHECK(invalid_begin.status.error == host::RuntimeHostError::InvalidArgument);

    const auto old_target_control = make_control();
    const RuntimeIncarnationRef source_slot = publish_initial(runtime, old_target_control);
    const auto invalid_lease = runtime.acquire_lease(
        admit_episode(runtime, source_slot), static_cast<host::RuntimeLeaseKind>(255));
    CHECK(invalid_lease.status.error == host::RuntimeHostError::InvalidArgument);

    const auto incoming_control = make_control();
    host::RuntimeHostCandidate replaced({.host_id = logical_host_id(9), .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef incoming_slot = publish_initial(replaced, incoming_control);
    runtime = std::move(replaced);
    CHECK(old_target_control->release_calls == 1);
    CHECK(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().active->incarnation == incoming_slot);
}

TEST_CASE("all active-slot mutations share one ticketed CAS failure path") {
    SUBCASE("initial publication loss leaves the host absent and retryable") {
        const auto injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::InitialPublish);
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                            .mode = host::RuntimeHostMode::Dark,
                                            .cas_fault_injector = injector});
        const auto begun = runtime.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::Initial,
            .plan = plan(),
            .control = make_control(),
            .lifecycle_deadline_tick = 20,
        });
        REQUIRE(begun.status);
        REQUIRE(runtime.validate_candidate(begun.handle, validation()));
        CHECK(runtime.commit_initial(begun.handle, initial_proof()).status.error ==
              host::RuntimeHostError::PublicationRaceLost);
        CHECK(runtime.snapshot().state == host::RuntimeHostState::Absent);
        CHECK(runtime.snapshot().last_publication_ticket == 0);
        CHECK(publish_initial(runtime, make_control()).incarnation_epoch == 1);
    }

    SUBCASE("replacement loss reopens the old incarnation") {
        const auto injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::ReplacementPublish);
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                            .mode = host::RuntimeHostMode::Dark,
                                            .cas_fault_injector = injector});
        const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
        const auto begun = runtime.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
            .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
        });
        REQUIRE(begun.status);
        REQUIRE(runtime.validate_candidate(begun.handle, validation()));
        REQUIRE(runtime.prepare_replacement(
            begun.handle, transfer_proof(runtime, begun.handle, old_slot)));
        CHECK(runtime.commit_prepared_candidate(begun.handle).status.error ==
              host::RuntimeHostError::PublicationRaceLost);
        REQUIRE(runtime.snapshot().active.has_value());
        CHECK(runtime.snapshot().active->incarnation == old_slot);
        CHECK(runtime.snapshot().active->admission_open);
        CHECK(runtime.snapshot().last_publication_ticket == 1);
    }

    SUBCASE("recovery loss preserves the faulted source and shutdown loss is retryable") {
        const auto recovery_injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::RecoveryPublish);
        host::RuntimeHostCandidate recovery_host({.host_id = logical_host_id(),
                                                  .mode = host::RuntimeHostMode::Dark,
                                                  .cas_fault_injector = recovery_injector});
        const RuntimeIncarnationRef faulted = publish_initial(recovery_host, make_control());
        REQUIRE(recovery_host.mark_active_faulted(faulted, 20));
        const auto recovery = recovery_host.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::CheckpointRecovery,
            .expected_slot = faulted,
            .plan = plan("plan.recovery", kHash2),
            .control = make_control(),
            .lifecycle_deadline_tick = 20,
        });
        REQUIRE(recovery.status);
        REQUIRE(recovery_host.validate_candidate(recovery.handle, validation()));
        REQUIRE(recovery_host.prepare_checkpoint_recovery(
            recovery.handle, recovery_proof(faulted)));
        CHECK(recovery_host.commit_prepared_candidate(recovery.handle).status.error ==
              host::RuntimeHostError::PublicationRaceLost);
        CHECK(recovery_host.snapshot().state == host::RuntimeHostState::Faulted);
        REQUIRE(recovery_host.snapshot().active.has_value());
        CHECK(recovery_host.snapshot().active->state == host::RuntimeSlotState::ActiveFaulted);

        const auto shutdown_injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::ShutdownUnpublish);
        host::RuntimeHostCandidate shutdown_host({.host_id = logical_host_id(8),
                                                  .mode = host::RuntimeHostMode::Dark,
                                                  .cas_fault_injector = shutdown_injector});
        (void)publish_initial(shutdown_host, make_control());
        CHECK(shutdown_host.begin_shutdown(0, 1).status.error ==
              host::RuntimeHostError::PublicationRaceLost);
        CHECK(shutdown_host.snapshot().state == host::RuntimeHostState::Active);
        CHECK(shutdown_host.snapshot().active.has_value());
        CHECK(shutdown_host.begin_shutdown(0, 1).state == host::RuntimeHostState::Stopped);
        CHECK(shutdown_host.snapshot().last_publication_ticket == 2);
    }
}

TEST_CASE("CAS fault injection is reentrant because it runs outside the host mutex") {
    const auto injector = std::make_shared<ReentrantCasLoss>();
    injector->operation = host::RuntimeSlotCasOperation::ReplacementPublish;
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark,
                                        .cas_fault_injector = injector});
    injector->runtime = &runtime;
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
        REQUIRE(runtime.prepare_replacement(
            replacement.handle, transfer_proof(runtime, replacement.handle, old_slot)));
    CHECK(runtime.commit_prepared_candidate(replacement.handle).status.error ==
          host::RuntimeHostError::PublicationRaceLost);
    CHECK(injector->observed);
}

TEST_CASE("timeout CAS losses preserve state and retry with a monotonic ticket") {
    SUBCASE("quiesce timeout CAS loss retries without dropping either slot") {
        const auto injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::QuiesceTimeoutUnpublish);
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                            .mode = host::RuntimeHostMode::Dark,
                                            .cas_fault_injector = injector});
        const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
        auto truth = acquire(runtime, old_slot, host::RuntimeLeaseKind::TruthMutating);
        const auto replacement = runtime.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
            .expected_slot = old_slot,
            .plan = plan("plan.v2", kHash2),
            .control = make_control(),
            .lifecycle_deadline_tick = 3,
        });
        REQUIRE(replacement.status);
        REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
        CHECK(runtime.prepare_replacement(
                  replacement.handle,
                  transfer_proof(runtime, replacement.handle, old_slot))
                  .error ==
              host::RuntimeHostError::InvalidCommitProof);
        CHECK(runtime.poll(3).error == host::RuntimeHostError::PublicationRaceLost);
        CHECK(runtime.snapshot().last_publication_ticket == 1);
        CHECK(runtime.snapshot().active.has_value());
        CHECK(runtime.snapshot().candidate.has_value());
        CHECK(runtime.snapshot().quarantined.empty());
        CHECK(runtime.poll(3).error == host::RuntimeHostError::QuarantineUnresolved);
        CHECK(runtime.snapshot().last_publication_ticket == 2);
        truth.lease.settle();
        CHECK(runtime.retry_quarantined_reclamation());
    }

    SUBCASE("fault timeout CAS loss preserves the faulted source until retry") {
        const auto injector = std::make_shared<OneShotCasLoss>(
            host::RuntimeSlotCasOperation::FaultTimeoutUnpublish);
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(31),
                                            .mode = host::RuntimeHostMode::Dark,
                                            .cas_fault_injector = injector});
        const RuntimeIncarnationRef slot = publish_initial(runtime, make_control());
        auto read = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
        REQUIRE(runtime.mark_active_faulted(slot, 3));
        CHECK(runtime.poll(3).error == host::RuntimeHostError::PublicationRaceLost);
        CHECK(runtime.snapshot().state == host::RuntimeHostState::Faulted);
        CHECK(runtime.snapshot().last_publication_ticket == 1);
        REQUIRE(runtime.snapshot().active.has_value());
        CHECK(runtime.snapshot().active->incarnation == slot);
        CHECK(runtime.poll(3).error == host::RuntimeHostError::HostTerminal);
        CHECK(runtime.snapshot().last_publication_ticket == 2);
        read.lease.settle();
        CHECK(runtime.retry_quarantined_reclamation());
    }
}

TEST_CASE("quiesce deadline fail-stops instead of waiting forever for a truth lease") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
    auto truth = acquire(runtime, old_slot, host::RuntimeLeaseKind::TruthMutating);
    REQUIRE(truth.status);
    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 5,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
    CHECK(runtime.prepare_replacement(
              replacement.handle, transfer_proof(runtime, replacement.handle, old_slot))
              .error ==
          host::RuntimeHostError::InvalidCommitProof);
    CHECK(runtime.poll(4));
    CHECK(runtime.poll(5).error == host::RuntimeHostError::QuarantineUnresolved);
    CHECK(runtime.snapshot().state == host::RuntimeHostState::FailStopped);
    CHECK_FALSE(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().quarantined.size() == 1);
    truth.lease = {};
    CHECK(runtime.retry_quarantined_reclamation());
    CHECK(runtime.snapshot().state == host::RuntimeHostState::FailStopped);
    CHECK(runtime.snapshot().quarantined.empty());
}

TEST_CASE("candidate deadline aborts an idle replacement and reopens the old slot") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = make_control(),
        .lifecycle_deadline_tick = 3,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
    CHECK(runtime.poll(3).error == host::RuntimeHostError::LifecycleDeadlineExpired);
    CHECK_FALSE(runtime.snapshot().candidate.has_value());
    REQUIRE(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().active->incarnation == old_slot);
    CHECK(runtime.snapshot().active->admission_open);
}

TEST_CASE("initial candidate cannot remain constructed past its lifecycle deadline") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const auto candidate = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = plan(),
        .control = make_control(),
        .lifecycle_deadline_tick = 2,
    });
    REQUIRE(candidate.status);
    CHECK(runtime.poll(2).error == host::RuntimeHostError::LifecycleDeadlineExpired);
    CHECK(runtime.snapshot().state == host::RuntimeHostState::Absent);
    CHECK_FALSE(runtime.snapshot().candidate.has_value());
}

TEST_CASE("candidate deadline quarantines cancellation-unacknowledged resources") {
    SUBCASE("an initial candidate cannot remain orphaned") {
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                            .mode = host::RuntimeHostMode::Dark});
        const auto control = make_control();
        control->cancel_acknowledged = false;
        const auto candidate = runtime.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::Initial,
            .plan = plan(),
            .control = control,
            .lifecycle_deadline_tick = 2,
        });
        REQUIRE(candidate.status);
        CHECK(runtime.poll(2).error == host::RuntimeHostError::LifecycleDeadlineExpired);
        CHECK_FALSE(runtime.snapshot().candidate.has_value());
        CHECK(runtime.snapshot().quarantined.size() == 1);
        REQUIRE(runtime.retry_quarantined_reclamation());
        CHECK(runtime.snapshot().quarantined.empty());
    }

    SUBCASE("a live old truth lease and unacknowledged candidate retain both owners") {
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(19),
                                            .mode = host::RuntimeHostMode::Dark});
        const RuntimeIncarnationRef old_slot = publish_initial(runtime, make_control());
        auto truth = acquire(runtime, old_slot, host::RuntimeLeaseKind::TruthMutating);
        const auto candidate_control = make_control();
        candidate_control->cancel_acknowledged = false;
        const auto candidate = runtime.begin_candidate({
            .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
            .expected_slot = old_slot,
            .plan = plan("plan.v2", kHash2),
            .control = candidate_control,
            .lifecycle_deadline_tick = 2,
        });
        REQUIRE(candidate.status);
        REQUIRE(runtime.validate_candidate(candidate.handle, validation()));
    CHECK(runtime.prepare_replacement(
              candidate.handle, transfer_proof(runtime, candidate.handle, old_slot))
              .error ==
              host::RuntimeHostError::InvalidCommitProof);
        CHECK(runtime.poll(2).error == host::RuntimeHostError::QuarantineUnresolved);
        CHECK_FALSE(runtime.snapshot().candidate.has_value());
        CHECK(runtime.snapshot().quarantined.size() == 2);
        truth.lease.settle();
        CHECK(runtime.retry_quarantined_reclamation().error ==
              host::RuntimeHostError::HostTerminal);
        CHECK(runtime.snapshot().quarantined.empty());
    }
}

TEST_CASE("faulted active slot has a terminal deadline and retained-resource path") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef slot = publish_initial(runtime, make_control());
    auto read = acquire(runtime, slot, host::RuntimeLeaseKind::ReadOnlyResult);
    REQUIRE(runtime.mark_active_faulted(slot, 3));
    CHECK(runtime.poll(2));
    CHECK(runtime.poll(3).error == host::RuntimeHostError::HostTerminal);
    CHECK(runtime.snapshot().state == host::RuntimeHostState::FailStopped);
    CHECK_FALSE(runtime.snapshot().active.has_value());
    CHECK(runtime.snapshot().quarantined.size() == 1);
    read.lease = {};
    CHECK(runtime.retry_quarantined_reclamation());
    CHECK(runtime.snapshot().quarantined.empty());
}

TEST_CASE("a second quarantine fail-stops without losing either resource owner") {
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const auto old_control = make_control();
    const RuntimeIncarnationRef old_slot = publish_initial(runtime, old_control);
    auto read = acquire(runtime, old_slot, host::RuntimeLeaseKind::ReadOnlyResult);
    const auto new_control = make_control(false);
    const auto replacement = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = old_slot,
        .plan = plan("plan.v2", kHash2),
        .control = new_control,
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(replacement.status);
    REQUIRE(runtime.validate_candidate(replacement.handle, validation()));
    REQUIRE(runtime.prepare_replacement(
        replacement.handle, transfer_proof(runtime, replacement.handle, old_slot, 2)));
    REQUIRE(runtime.commit_prepared_candidate(replacement.handle).status);
    CHECK(runtime.poll(2).error == host::RuntimeHostError::QuarantineUnresolved);
    CHECK(runtime.snapshot().quarantined.size() == 1);

    CHECK(runtime.begin_shutdown(3, 3).state == host::RuntimeHostState::FailStopped);
    CHECK(runtime.snapshot().quarantined.size() == 2);
    read.lease = {};
    new_control->allow_release();
    CHECK(runtime.retry_quarantined_reclamation().error == host::RuntimeHostError::HostTerminal);
    CHECK(runtime.snapshot().quarantined.empty());
    CHECK(old_control->release_calls == 1);
    CHECK(new_control->release_calls >= 2);
}

TEST_CASE("resource identities cannot be aliased across active and candidate slots") {
    const RuntimeIdentity128 shared_resource{.high = 77, .low = 88};
    host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                        .mode = host::RuntimeHostMode::Dark});
    const RuntimeIncarnationRef active =
        publish_initial(runtime, std::make_shared<FakeControl>(true, shared_resource));
    const auto aliased = runtime.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = active,
        .plan = plan("plan.v2", kHash2),
        .control = std::make_shared<FakeControl>(true, shared_resource),
        .lifecycle_deadline_tick = 20,
    });
    CHECK(aliased.status.error == host::RuntimeHostError::InvalidArgument);

    host::RuntimeHostCandidate other_host({.host_id = logical_host_id(99),
                                           .mode = host::RuntimeHostMode::Dark});
    const auto cross_host_alias = other_host.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = plan(),
        .control = std::make_shared<FakeControl>(true, shared_resource),
        .lifecycle_deadline_tick = 20,
    });
    CHECK(cross_host_alias.status.error == host::RuntimeHostError::InvalidArgument);
}

TEST_CASE("candidate handles are bound to one host object even with the same logical host ID") {
    host::RuntimeHostCandidate first({.host_id = logical_host_id(),
                                      .mode = host::RuntimeHostMode::Dark});
    host::RuntimeHostCandidate second({.host_id = logical_host_id(),
                                       .mode = host::RuntimeHostMode::Dark});
    const auto first_candidate = first.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = plan(),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    const auto second_candidate = second.begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = plan(),
        .control = make_control(),
        .lifecycle_deadline_tick = 20,
    });
    REQUIRE(first_candidate.status);
    REQUIRE(second_candidate.status);
    CHECK(second.validate_candidate(first_candidate.handle, validation()).error ==
          host::RuntimeHostError::CandidateNotFound);
    CHECK(first_candidate.handle.host.boot_id != second_candidate.handle.host.boot_id);
}

TEST_CASE("destruction hands unreleased resources to an observable retry registry") {
    const std::size_t baseline = host::RuntimeHostCandidate::orphaned_host_count();
    const auto control = make_control(false);
    {
        host::RuntimeHostCandidate runtime({.host_id = logical_host_id(),
                                            .mode = host::RuntimeHostMode::Dark});
        (void)publish_initial(runtime, control);
    }
    CHECK(host::RuntimeHostCandidate::orphaned_host_count() == baseline + 1);
    control->allow_release();
    CHECK(host::RuntimeHostCandidate::retry_orphaned_reclamation());
    CHECK(host::RuntimeHostCandidate::orphaned_host_count() == baseline);
}

} // TEST_SUITE("runtime_host_candidate")
