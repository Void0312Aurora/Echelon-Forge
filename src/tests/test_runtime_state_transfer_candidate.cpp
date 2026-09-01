#include "runtime_state_transfer_candidate.h"
#include "runtime_host_candidate.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <memory>
#include <ostream>
#include <string>
#include <utility>
#include <vector>

namespace {

namespace host = runtime::host;
using echelon_forge::runtime_contracts::v1::RuntimeEpisodeRef;
using echelon_forge::runtime_contracts::v1::RuntimeHostIdentity;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;

constexpr const char *kHash =
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
constexpr const char *kHash2 =
    "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

std::vector<std::uint8_t> fixture_owner_state_payload(
    host::RuntimeStateCategory category, std::uint32_t generation) {
    const std::string bytes = std::string("fixture-owner-state:") +
                              std::string(host::runtime_state_category_name(category)) +
                              ":v" + std::to_string(generation);
    return {bytes.begin(), bytes.end()};
}

RuntimeIncarnationRef slot(std::uint64_t host_low = 100,
                           std::uint64_t incarnation = 1) {
    return {.host = RuntimeHostIdentity{
                .host_id = {.high = 1, .low = host_low},
                .boot_id = {.high = 2, .low = host_low},
            },
            .incarnation_epoch = incarnation};
}

RuntimeEpisodeRef episode(const RuntimeIncarnationRef &source,
                          std::uint64_t generation = 1,
                          std::uint64_t episode_low = 200) {
    return {.world = {.incarnation = source,
                      .world_slot = 0,
                      .world_generation = 1},
            .episode_id = {.high = 3, .low = episode_low},
            .episode_generation = generation};
}

class ScriptedEpisodeControl final : public host::RuntimeNativeEpisodeControl {
  public:
    host::RuntimeNativeEpisodeMutation mutation;
    int calls = 0;

    explicit ScriptedEpisodeControl(RuntimeIdentity128 resource = {}) : resource_(resource) {}

    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
        return resource_;
    }

    [[nodiscard]] host::RuntimeNativeEpisodeMutation
    apply(const host::RuntimeNativeEpisodeCommand &) noexcept override {
        ++calls;
        return mutation;
    }

  private:
    RuntimeIdentity128 resource_;
};

struct ValidationFixture {
    std::unique_ptr<host::RuntimeHostCandidate> host;
    std::unique_ptr<host::RuntimeEpisodeCoordinatorCandidate> coordinator;
    std::shared_ptr<class FixtureOwnerRegistry> target_owner_registry;
    host::RuntimeStateTransferValidationRequest request;
};

class FixtureInstanceControl final : public host::RuntimeInstanceControl {
  public:
    FixtureInstanceControl(
        RuntimeIdentity128 resource,
        std::shared_ptr<host::RuntimeStateTransferOwnerRegistry> owner_registry)
        : resource_(resource),
          native_episode_control_(std::make_shared<ScriptedEpisodeControl>(resource)),
          owner_registry_(std::move(owner_registry)) {
        native_episode_control_->mutation = {.applied = true,
                                             .terminal = true,
                                             .snapshot_id = {.high = 12, .low = 13},
                                             .snapshot_sha256 = kHash};
    }
    [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
        return resource_;
    }
    [[nodiscard]] std::shared_ptr<host::RuntimeNativeEpisodeControl>
    native_episode_control() const noexcept override {
        return native_episode_control_;
    }
    [[nodiscard]] std::shared_ptr<host::RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept override {
        return owner_registry_;
    }
    [[nodiscard]] bool begin_state_transfer() noexcept override { return true; }
    void end_state_transfer() noexcept override {}
    [[nodiscard]] bool request_cooperative_cancel() noexcept override { return true; }
    [[nodiscard]] bool release_resources() noexcept override {
        released_ = true;
        return true;
    }
    [[nodiscard]] bool resources_released() const noexcept override { return released_; }

  private:
    RuntimeIdentity128 resource_;
    std::shared_ptr<ScriptedEpisodeControl> native_episode_control_;
    std::shared_ptr<host::RuntimeStateTransferOwnerRegistry> owner_registry_;
    bool released_ = false;
};

class NoopImportTransaction final : public host::RuntimeStateOwnerImportTransaction {
  public:
    explicit NoopImportTransaction(std::shared_ptr<std::atomic<int>> abort_count)
        : abort_count_(std::move(abort_count)) {}
    void commit() noexcept override {}
    void abort() noexcept override {
        if (abort_count_ != nullptr) {
            ++*abort_count_;
        }
    }

  private:
    std::shared_ptr<std::atomic<int>> abort_count_;
};

class DurableStatusImportTransaction final
    : public host::RuntimeStateOwnerImportTransaction {
  public:
    [[nodiscard]] host::RuntimeStateOwnerImportTransactionStatus
    commit_with_deadline(std::uint64_t now_tick,
                         std::uint64_t deadline_tick) noexcept override {
        if (phase_.phase != host::RuntimeStateOwnerImportTransactionPhase::Prepared) {
            phase_.error = host::RuntimeStateTransferError::ImportTransactionStateInvalid;
            return phase_;
        }
        if (deadline_tick != 0 && now_tick >= deadline_tick) {
            phase_ = {.phase = host::RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                       .error = host::RuntimeStateTransferError::ImportTransactionDeadlineExceeded,
                       .journal_sequence = 7,
                       .durable = true};
            return phase_;
        }
        phase_ = {.phase = host::RuntimeStateOwnerImportTransactionPhase::Committed,
                   .error = host::RuntimeStateTransferError::None,
                   .journal_sequence = 8,
                   .durable = true};
        return phase_;
    }

    [[nodiscard]] host::RuntimeStateOwnerImportTransactionStatus
    abort_with_deadline(std::uint64_t now_tick,
                        std::uint64_t deadline_tick) noexcept override {
        if (deadline_tick != 0 && now_tick >= deadline_tick) {
            phase_ = {.phase = host::RuntimeStateOwnerImportTransactionPhase::Ambiguous,
                       .error = host::RuntimeStateTransferError::ImportTransactionDeadlineExceeded,
                       .journal_sequence = 9,
                       .durable = true};
            return phase_;
        }
        phase_ = {.phase = host::RuntimeStateOwnerImportTransactionPhase::Aborted,
                   .error = host::RuntimeStateTransferError::None,
                   .journal_sequence = 10,
                   .durable = true};
        return phase_;
    }

    [[nodiscard]] host::RuntimeStateOwnerImportTransactionStatus
    recover_with_deadline(std::uint64_t, std::uint64_t) noexcept override {
        if (phase_.phase == host::RuntimeStateOwnerImportTransactionPhase::Ambiguous) {
            phase_ = {.phase = host::RuntimeStateOwnerImportTransactionPhase::Aborted,
                       .error = host::RuntimeStateTransferError::None,
                       .journal_sequence = 11,
                       .durable = true};
        }
        return phase_;
    }

    [[nodiscard]] host::RuntimeStateOwnerImportTransactionStatus
    status() const noexcept override {
        return phase_;
    }

  private:
    host::RuntimeStateOwnerImportTransactionStatus phase_{};
};

class CountingAbortImportTransaction final
    : public host::RuntimeStateOwnerImportTransaction {
  public:
    explicit CountingAbortImportTransaction(std::shared_ptr<std::atomic<int>> count)
        : count_(std::move(count)) {}

    [[nodiscard]] host::RuntimeStateOwnerImportTransactionStatus
    abort_with_deadline(std::uint64_t, std::uint64_t) noexcept override {
        ++*count_;
        return {.phase = host::RuntimeStateOwnerImportTransactionPhase::Aborted,
                .error = host::RuntimeStateTransferError::None,
                .journal_sequence = 12,
                .durable = true};
    }

  private:
    std::shared_ptr<std::atomic<int>> count_;
};

class FixtureOwnerRegistry final : public host::RuntimeStateTransferOwnerRegistry {
  public:
    explicit FixtureOwnerRegistry(bool tamper = false, bool export_allowed = true,
                                  bool tamper_artifact = false,
                                  RuntimeIdentity128 resource_identity = {})
        : tamper_(tamper), export_allowed_(export_allowed),
          tamper_artifact_(tamper_artifact),
          abort_count_(std::make_shared<std::atomic<int>>(0)),
          resource_identity_(resource_identity) {}

    [[nodiscard]] RuntimeIdentity128 bound_resource_identity() const noexcept override {
        return resource_identity_;
    }
    [[nodiscard]] const void *owner_binding_token() const noexcept override {
        return this;
    }

    [[nodiscard]] host::RuntimeStateOwnerExport export_source(
        const host::RuntimeStateTransferProfile &profile,
        const RuntimeIncarnationRef &source_slot,
        const host::RuntimeStateOwnerExportContext &context) noexcept override {
        const auto &barrier_snapshot = context.barrier_snapshot;
        host::RuntimeStateOwnerExport exported;
        exported.source_slot = source_slot;
        if (!export_allowed_) {
            exported.status = {.error = host::RuntimeStateTransferError::SemanticEvidenceMissing,
                               .detail = "target registry must never export source truth"};
            return exported;
        }
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
                    .sequence_high_watermark = 17,
                    .rng_draw_position = 18,
                    .simulation_tick = 19,
                    .step_sequence = barrier_snapshot.step_sequence,
                    .barrier_sequence = barrier_snapshot.barrier_sequence,
                };
                if (policy.disposition == host::RuntimeStateDisposition::Transfer) {
                    const auto owner_payload = fixture_owner_state_payload(
                        entry.category, entry.schema_generation);
                    entry.state_content_sha256 =
                        host::runtime_state_payload_sha256(owner_payload);
                    entry.canonical_payload = host::runtime_state_canonical_payload(entry);
                    entry.canonical_payload_sha256 =
                        host::runtime_state_payload_sha256(entry.canonical_payload);
                    entry.semantic_evidence_sha256 = kHash;
                } else if (policy.disposition == host::RuntimeStateDisposition::Rederive ||
                           policy.disposition == host::RuntimeStateDisposition::Drain) {
                    entry.semantic_evidence_sha256 = kHash2;
                }
                host::RuntimeStateOwnerArtifact artifact{
                    .category = entry.category,
                    .schema_id = entry.schema_id,
                    .schema_generation = entry.schema_generation,
                    .payload = policy.disposition == host::RuntimeStateDisposition::Transfer
                                   ? fixture_owner_state_payload(entry.category,
                                                                 entry.schema_generation)
                                   : std::vector<std::uint8_t>{},
                };
                artifact.payload_sha256 = host::runtime_state_payload_sha256(artifact.payload);
                exported.artifacts.push_back(std::move(artifact));
                if (tamper_artifact_ && exported.artifacts.size() == 1) {
                    exported.artifacts.back().payload.push_back(0xffU);
                }
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
                receipt.observations.push_back({
                    .category = entry.category,
                    .owner_id = entry.owner_id,
                    .schema_id = entry.schema_id,
                    .schema_generation = entry.schema_generation,
                    .source_entry_sha256 =
                        host::runtime_state_census_entry_sha256(entry),
                    .candidate_entry_sha256 =
                        host::runtime_state_census_entry_sha256(entry),
                    .source_artifact_payload_sha256 = [&] {
                        const auto artifact = std::find_if(
                            source_export.artifacts.begin(), source_export.artifacts.end(),
                            [&](const auto &candidate) {
                                return candidate.category == entry.category;
                            });
                        return artifact == source_export.artifacts.end()
                                   ? std::string{}
                                   : artifact->payload_sha256;
                    }(),
                    .candidate_artifact_payload_sha256 = [&] {
                        const auto artifact = std::find_if(
                            source_export.artifacts.begin(), source_export.artifacts.end(),
                            [&](const auto &candidate) {
                                return candidate.category == entry.category;
                            });
                        return artifact == source_export.artifacts.end()
                                   ? std::string{}
                                   : artifact->payload_sha256;
                    }(),
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
                if (tamper_ && receipt.observations.size() == 1) {
                    receipt.observations.back().candidate_entry_sha256.assign(64, '0');
                }
            }
            receipt.transaction = std::make_shared<NoopImportTransaction>(abort_count_);
            return receipt;
        } catch (...) {
            receipt.status = {.error = host::RuntimeStateTransferError::SemanticEvidenceMissing,
                              .detail = "fixture owner allocation failed"};
            return receipt;
        }
  }

  private:
    bool tamper_ = false;
    bool export_allowed_ = true;
    bool tamper_artifact_ = false;
    std::shared_ptr<std::atomic<int>> abort_count_;
    RuntimeIdentity128 resource_identity_;

  public:
    [[nodiscard]] int abort_count() const noexcept {
        return abort_count_ == nullptr ? 0 : abort_count_->load();
    }
};

host::RuntimePlanBinding fixture_plan(const char *id, const char *hash) {
    return {.plan_id = id, .plan_sha256 = hash};
}

host::RuntimeCandidateValidationProof fixture_validation() {
    return {.static_plan_validated = true,
            .resources_ready = true,
            .shadow_probe_passed = true,
            .unreachable_from_production = true};
}

std::vector<std::pair<host::RuntimeStateCategory, host::RuntimeStateDisposition>>
standard_rules() {
    return {
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
}

ValidationFixture make_validation_fixture(std::uint64_t host_low, bool tamper = false,
                                          bool source_artifact_tamper = false) {
    const auto source_owner_registry =
        std::make_shared<FixtureOwnerRegistry>(
            false, true, source_artifact_tamper,
            RuntimeIdentity128{.high = 92, .low = host_low});
    // The target adapter is intentionally forbidden from exporting. This
    // proves the validator uses the active source registry for source truth
    // and the candidate registry only for import/replay observation.
    const auto target_owner_registry = std::make_shared<FixtureOwnerRegistry>(
        tamper, false, false,
        RuntimeIdentity128{.high = 93, .low = host_low});
    auto runtime = std::make_unique<host::RuntimeHostCandidate>(host::RuntimeHostConfig{
        .host_id = {.high = 91, .low = host_low},
        .mode = host::RuntimeHostMode::Dark,
    });
    const auto initial = runtime->begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Initial,
        .plan = fixture_plan("source-plan", kHash),
        .control = std::make_shared<FixtureInstanceControl>(
            RuntimeIdentity128{.high = 92, .low = host_low}, source_owner_registry),
        .lifecycle_deadline_tick = 100,
    });
    REQUIRE(initial.status);
    REQUIRE(runtime->validate_candidate(initial.handle, fixture_validation()));
    const auto published = runtime->commit_initial(
        initial.handle,
        {.lifecycle_evidence_sha256 = kHash, .dark_evidence_sealed = true});
    REQUIRE(published.status);
    const RuntimeIncarnationRef source = published.published_slot;
    const auto candidate = runtime->begin_candidate({
        .transaction_kind = host::RuntimeHostTransactionKind::Replacement,
        .expected_slot = source,
        .plan = fixture_plan("target-plan", kHash2),
        .control = std::make_shared<FixtureInstanceControl>(
            RuntimeIdentity128{.high = 93, .low = host_low}, target_owner_registry),
        .lifecycle_deadline_tick = 100,
    });
    REQUIRE(candidate.status);
    REQUIRE(runtime->validate_candidate(candidate.handle, fixture_validation()));
    const auto episode_admission = runtime->issue_shadow_episode(0);
    REQUIRE(episode_admission.status);
    const RuntimeEpisodeRef current_episode = episode_admission.capability.episode();
    const auto transition = runtime->submit_shadow_episode(
        episode_admission.capability,
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = current_episode,
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 14, .low = 15},
         .payload_sha256 = kHash});
    REQUIRE(transition.status);
    auto quiescence = runtime->quiesce_replacement_source(candidate.handle);
    REQUIRE(quiescence.status);
    auto barrier = runtime->open_shadow_replacement_barrier(
        transition.receipt.episode_after,
        transition.receipt.resulting_step_sequence);
    REQUIRE(barrier.status);
    const auto barrier_snapshot = barrier.capability.snapshot();
    const std::uint64_t host_fence = quiescence.capability.mutation_fence_sequence();

    host::RuntimeStateTransferProfile profile{
        .profile_id = "cpu-exact-shadow.v1",
        .profile_generation = 1,
        .source_plan_sha256 = kHash,
        .target_plan_sha256 = kHash2,
    };
    host::RuntimeStateCensus census{
        .profile_id = profile.profile_id,
        .profile_generation = profile.profile_generation,
        .source_slot = source,
        .source_plan_sha256 = profile.source_plan_sha256,
        .target_plan_sha256 = profile.target_plan_sha256,
    };
    for (const auto &[category, disposition] : standard_rules()) {
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
            .item_count = 0,
            .settled_item_count = 0,
            .sequence_high_watermark = 17,
            .rng_draw_position = 18,
            .simulation_tick = 19,
            .step_sequence = barrier_snapshot.step_sequence,
            .barrier_sequence = barrier_snapshot.barrier_sequence,
        };
        if (disposition == host::RuntimeStateDisposition::Transfer) {
            const auto owner_payload =
                fixture_owner_state_payload(category, entry.schema_generation);
            entry.state_content_sha256 =
                host::runtime_state_payload_sha256(owner_payload);
            entry.canonical_payload = host::runtime_state_canonical_payload(entry);
            entry.canonical_payload_sha256 =
                host::runtime_state_payload_sha256(entry.canonical_payload);
            entry.semantic_evidence_sha256 = kHash;
        } else if (disposition == host::RuntimeStateDisposition::Rederive ||
                   disposition == host::RuntimeStateDisposition::Drain) {
            entry.semantic_evidence_sha256 = kHash2;
        }
        census.entries.push_back(std::move(entry));
    }
    return {.host = std::move(runtime),
            .coordinator = {},
            .target_owner_registry = target_owner_registry,
            .request = {.profile = std::move(profile),
                        .census = std::move(census),
                        .evidence = {
                            .source_final_mutation_fence_sequence = host_fence,
                        },
                        .host_quiescence = std::move(quiescence.capability),
                        .episode_barrier = std::move(barrier.capability)}};
}

host::RuntimeStateCensusEntry &entry_for(
    host::RuntimeStateTransferValidationRequest &request,
    host::RuntimeStateCategory category) {
    const auto position = std::find_if(
        request.census.entries.begin(), request.census.entries.end(),
        [category](const auto &entry) { return entry.category == category; });
    REQUIRE(position != request.census.entries.end());
    return *position;
}

host::RuntimeStateCensusRowPolicy &policy_for(
    host::RuntimeStateTransferValidationRequest &request,
    host::RuntimeStateCategory category) {
    const auto position = std::find_if(
        request.profile.rows.begin(), request.profile.rows.end(),
        [category](const auto &row) { return row.category == category; });
    REQUIRE(position != request.profile.rows.end());
    return *position;
}

} // namespace

TEST_SUITE("runtime_state_transfer_candidate") {

TEST_CASE("payload digest uses SHA-256 and category names are stable") {
    const std::vector<std::uint8_t> abc{'a', 'b', 'c'};
    CHECK(host::runtime_state_payload_sha256(abc) ==
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    CHECK(host::runtime_state_category_name(
              host::RuntimeStateCategory::InFlightRequestsResults) ==
          "in-flight-requests-results");
    CHECK(host::runtime_state_disposition_name(host::RuntimeStateDisposition::Rederive) ==
          "rederive");
}

TEST_CASE("native receipt bytes match the Python shadow mirror vector") {
    const RuntimeIncarnationRef source{
        .host = {.host_id = {.high = 1, .low = 2},
                 .boot_id = {.high = 3, .low = 4}},
        .incarnation_epoch = 1,
    };
    const RuntimeEpisodeRef value{
        .world = {.incarnation = source, .world_slot = 0, .world_generation = 1},
        .episode_id = {.high = 5, .low = 7},
        .episode_generation = 1,
    };
    const host::RuntimeEpisodeTransitionReceipt receipt{
        .kind = host::RuntimeEpisodeIntentKind::Action,
        .idempotency_key = {.high = 8, .low = 9},
        .episode_before = value,
        .episode_after = value,
        .previous_step_sequence = 0,
        .resulting_step_sequence = 1,
        .resulting_phase = host::RuntimeEpisodePhase::Running,
        .terminal = false,
        .reset_applied = false,
        .snapshot_id = {.high = 11, .low = 12},
        .snapshot_sha256 = kHash2,
        .barrier_sequence = 0,
    };
    const std::string bytes = host::canonical_episode_transition_receipt_bytes(receipt);
    const std::vector<std::uint8_t> payload(bytes.begin(), bytes.end());
    CHECK(host::runtime_state_payload_sha256(payload) ==
          "280f80bf64d46f9b2746f5d450dc8456e8fff4a1fe6180dd5c3e8b6a608370fe");
}

TEST_CASE("native intent bytes match the cross-language authority vector") {
    const RuntimeIncarnationRef source{
        .host = {.host_id = {.high = 1, .low = 2},
                 .boot_id = {.high = 3, .low = 4}},
        .incarnation_epoch = 1,
    };
    const RuntimeEpisodeRef value{
        .world = {.incarnation = source, .world_slot = 0, .world_generation = 1},
        .episode_id = {.high = 5, .low = 7},
        .episode_generation = 1,
    };
    const host::RuntimeEpisodeTransitionIntent intent{
        .protocol_generation = 1,
        .kind = host::RuntimeEpisodeIntentKind::Action,
        .expected_episode = value,
        .expected_step_sequence = 0,
        .idempotency_key = {.high = 8, .low = 9},
        .payload_sha256 = kHash,
        .production_authorized = false,
    };
    const std::string bytes = host::canonical_episode_transition_intent_bytes(intent);
    const std::vector<std::uint8_t> payload(bytes.begin(), bytes.end());
    CHECK(host::runtime_state_payload_sha256(payload) ==
          "7a9b047d12c941acf2153bb69d4bb20b0fba6feec9f9b2b92d845df503ab1c71");
}

TEST_CASE("native coordinator owns phase sequence reset and idempotent receipts") {
    const auto source = slot();
    auto created = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = episode(source),
        .initial_snapshot_id = {.high = 20, .low = 21},
        .initial_snapshot_sha256 = kHash,
    });
    REQUIRE(created.status);

    auto duplicate = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = episode(source),
        .initial_snapshot_id = {.high = 22, .low = 23},
        .initial_snapshot_sha256 = kHash,
    });
    CHECK(duplicate.status.error == host::RuntimeStateTransferError::DuplicateCoordinator);

    auto native_capability = created.coordinator->issue_episode_capability();
    REQUIRE(native_capability.status);
    CHECK(native_capability.capability.valid());

    ScriptedEpisodeControl action;
    action.mutation = {.applied = true,
                       .terminal = true,
                       .snapshot_id = {.high = 24, .low = 25},
                       .snapshot_sha256 = kHash2};
    const host::RuntimeEpisodeTransitionIntent intent{
        .kind = host::RuntimeEpisodeIntentKind::Action,
        .expected_episode = episode(source),
        .expected_step_sequence = 0,
        .idempotency_key = {.high = 26, .low = 27},
        .payload_sha256 = kHash,
    };
    const auto terminal = created.coordinator->submit(intent, action);
    REQUIRE(terminal.status);
    CHECK(terminal.receipt.well_formed());
    CHECK(terminal.receipt.resulting_step_sequence == 1);
    CHECK(terminal.receipt.resulting_phase == host::RuntimeEpisodePhase::Terminal);
    CHECK(action.calls == 1);
    CHECK_FALSE(native_capability.capability.valid());

    const auto replay = created.coordinator->submit(intent, action);
    REQUIRE(replay.status);
    CHECK(replay.replayed);
    CHECK(replay.receipt == terminal.receipt);
    CHECK(action.calls == 1);
    auto conflicting_intent = intent;
    conflicting_intent.payload_sha256 = kHash2;
    CHECK(created.coordinator->submit(conflicting_intent, action).status.error ==
          host::RuntimeStateTransferError::IdempotencyConflict);

    auto barrier = created.coordinator->open_replacement_barrier(
        terminal.receipt.episode_after, terminal.receipt.resulting_step_sequence);
    REQUIRE(barrier.status);
    CHECK(barrier.capability.valid());
    REQUIRE(created.coordinator->abort_replacement_barrier(
        std::move(barrier.capability)));
    CHECK(created.coordinator->snapshot().phase == host::RuntimeEpisodePhase::Terminal);

    ScriptedEpisodeControl reset;
    reset.mutation = {
        .applied = true,
        .terminal = false,
        .snapshot_id = {.high = 28, .low = 29},
        .snapshot_sha256 = kHash,
    };
    const auto reset_result = created.coordinator->submit(
        {.kind = host::RuntimeEpisodeIntentKind::Reset,
         .expected_episode = terminal.receipt.episode_after,
         .expected_step_sequence = terminal.receipt.resulting_step_sequence,
         .idempotency_key = {.high = 30, .low = 31},
         .payload_sha256 = kHash2},
        reset);
    REQUIRE(reset_result.status);
    CHECK(reset_result.receipt.reset_applied);
    CHECK(reset_result.receipt.episode_after.episode_generation == 2);
    CHECK(reset_result.receipt.episode_after.world.world_generation == 2);
    CHECK(reset_result.receipt.resulting_step_sequence == 0);
    CHECK(created.coordinator->snapshot().phase == host::RuntimeEpisodePhase::Running);

    REQUIRE(created.coordinator->acknowledge_receipt(terminal.receipt));
    CHECK(created.coordinator->submit(intent, action).status.error ==
          host::RuntimeStateTransferError::ReceiptResyncRequired);
}

TEST_CASE("applied native protocol violation fail-stops instead of fabricating continuity") {
    const auto source = slot(109);
    auto created = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = episode(source),
        .initial_snapshot_id = {.high = 40, .low = 41},
        .initial_snapshot_sha256 = kHash,
    });
    REQUIRE(created.status);
    ScriptedEpisodeControl invalid;
    invalid.mutation = {.applied = true,
                        .terminal = false,
                        .snapshot_id = {},
                        .snapshot_sha256 = "invalid"};
    CHECK(created.coordinator->submit(
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = episode(source),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 42, .low = 43},
         .payload_sha256 = kHash},
        invalid).status.error == host::RuntimeStateTransferError::NativeMutationFailed);
    CHECK(created.coordinator->snapshot().phase == host::RuntimeEpisodePhase::FailStopped);
    CHECK(created.coordinator->issue_episode_capability().status.error ==
          host::RuntimeStateTransferError::AdmissionClosed);
}

TEST_CASE("native mutation callback runs outside the coordinator mutex") {
    const auto source = slot(111);
    auto created = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = episode(source),
        .initial_snapshot_id = {.high = 50, .low = 51},
        .initial_snapshot_sha256 = kHash,
    });
    REQUIRE(created.status);
    class ReentrantControl final : public host::RuntimeNativeEpisodeControl {
      public:
        host::RuntimeEpisodeCoordinatorCandidate *coordinator = nullptr;
        bool observed = false;

        [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
            return {};
        }

        [[nodiscard]] host::RuntimeNativeEpisodeMutation
        apply(const host::RuntimeNativeEpisodeCommand &) noexcept override {
            if (coordinator != nullptr) {
                observed = coordinator->snapshot().phase == host::RuntimeEpisodePhase::Running;
            }
            return {.applied = true,
                    .terminal = false,
                    .snapshot_id = {.high = 52, .low = 53},
                    .snapshot_sha256 = kHash2};
        }
    } control;
    control.coordinator = created.coordinator.get();
    REQUIRE(created.coordinator->submit(
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = episode(source),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 54, .low = 55},
         .payload_sha256 = kHash},
        control).status);
    CHECK(control.observed);
}

TEST_CASE("native mutation callback cannot admit a capability at the old step") {
    const auto source = slot(112);
    auto created = host::RuntimeEpisodeCoordinatorCandidate::create({
        .initial_episode = episode(source),
        .initial_snapshot_id = {.high = 56, .low = 57},
        .initial_snapshot_sha256 = kHash,
    });
    REQUIRE(created.status);
    class ReentrantControl final : public host::RuntimeNativeEpisodeControl {
      public:
        host::RuntimeEpisodeCoordinatorCandidate *coordinator = nullptr;
        host::RuntimeStateTransferError error = host::RuntimeStateTransferError::None;
        [[nodiscard]] RuntimeIdentity128 resource_identity() const noexcept override {
            return {};
        }
        [[nodiscard]] host::RuntimeNativeEpisodeMutation
        apply(const host::RuntimeNativeEpisodeCommand &) noexcept override {
            if (coordinator != nullptr) {
                error = coordinator->issue_episode_capability().status.error;
            }
            return {.applied = true,
                    .terminal = false,
                    .snapshot_id = {.high = 58, .low = 59},
                    .snapshot_sha256 = kHash2};
        }
    } control;
    control.coordinator = created.coordinator.get();
    REQUIRE(created.coordinator->submit(
        {.kind = host::RuntimeEpisodeIntentKind::Action,
         .expected_episode = episode(source),
         .expected_step_sequence = 0,
         .idempotency_key = {.high = 60, .low = 61},
         .payload_sha256 = kHash},
        control).status);
    CHECK(control.error == host::RuntimeStateTransferError::AdmissionClosed);
}

TEST_CASE("complete state census validates and binds every category to one barrier") {
    auto fixture = make_validation_fixture(101);
    const auto source = fixture.request.census.source_slot;
    auto validated = host::RuntimeStateTransferValidator::validate(
        std::move(fixture.request));
    REQUIRE(validated.status);
    CHECK(validated.transfer.valid());
    CHECK(validated.transfer.source_slot() == source);
    CHECK(validated.transfer.target_plan_sha256() == kHash2);
    CHECK(validated.transfer.state_bundle_sha256().size() == 64);
    CHECK(validated.transfer.transfer_fence_sequence() != 0);
    validated.transfer.abandon();
    CHECK(fixture.target_owner_registry->abort_count() == 1);
    CHECK(fixture.host->snapshot().active.has_value());
}

TEST_CASE("state census rejects omission duplication unknown truth and payload tampering") {
    SUBCASE("missing category") {
        auto fixture = make_validation_fixture(102);
        fixture.request.census.entries.pop_back();
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::MissingCategory);
    }
    SUBCASE("duplicate category") {
        auto fixture = make_validation_fixture(103);
        fixture.request.census.entries.back() = fixture.request.census.entries.front();
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::DuplicateCategory);
    }
    SUBCASE("unknown ECS truth field") {
        auto fixture = make_validation_fixture(104);
        entry_for(fixture.request, host::RuntimeStateCategory::EcsComponentTruth)
            .contains_unknown_truth_fields = true;
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::UnknownTruthField);
    }
    SUBCASE("payload digest mismatch") {
        auto fixture = make_validation_fixture(105);
        entry_for(fixture.request, host::RuntimeStateCategory::RngState)
            .canonical_payload.push_back(0xffU);
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::PayloadDigestMismatch);
    }
    SUBCASE("caller cannot rename a native state owner or schema") {
        auto fixture = make_validation_fixture(110);
        policy_for(fixture.request, host::RuntimeStateCategory::EcsComponentTruth)
            .owner_id = "caller-owned-ecs";
        entry_for(fixture.request, host::RuntimeStateCategory::EcsComponentTruth)
            .owner_id = "caller-owned-ecs";
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::InvalidCensusProfile);
    }
    SUBCASE("owner import inequality rejects a forged candidate observation") {
        auto fixture = make_validation_fixture(113, true);
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::SemanticEvidenceMissing);
    }
    SUBCASE("source artifact digest mismatch is rejected before target import") {
        auto fixture = make_validation_fixture(114, false, true);
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::PayloadDigestMismatch);
        CHECK(fixture.target_owner_registry->abort_count() == 0);
    }
}

TEST_CASE("resource in-flight and side-effect rows fail closed") {
    SUBCASE("raw backend handle transfer") {
        auto fixture = make_validation_fixture(106);
        auto &policy = policy_for(
            fixture.request, host::RuntimeStateCategory::BackendDeviceAllocationsLeases);
        auto &entry = entry_for(
            fixture.request, host::RuntimeStateCategory::BackendDeviceAllocationsLeases);
        policy.disposition = host::RuntimeStateDisposition::Transfer;
        entry.disposition = host::RuntimeStateDisposition::Transfer;
        entry.state_content_sha256 = kHash;
        entry.canonical_payload = host::runtime_state_canonical_payload(entry);
        entry.canonical_payload_sha256 =
            host::runtime_state_payload_sha256(entry.canonical_payload);
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::RawHandleTransferForbidden);
    }
    SUBCASE("unsettled in-flight work") {
        auto fixture = make_validation_fixture(107);
        auto &entry = entry_for(
            fixture.request, host::RuntimeStateCategory::InFlightRequestsResults);
        entry.item_count = 2;
        entry.settled_item_count = 1;
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::UnsettledWork);
    }
    SUBCASE("profile rejects unresolved external side effects") {
        auto fixture = make_validation_fixture(108);
        policy_for(fixture.request, host::RuntimeStateCategory::ExternalSideEffects)
            .disposition = host::RuntimeStateDisposition::Reject;
        entry_for(fixture.request, host::RuntimeStateCategory::ExternalSideEffects)
            .disposition = host::RuntimeStateDisposition::Reject;
        CHECK(host::RuntimeStateTransferValidator::validate(std::move(fixture.request))
                  .status.error == host::RuntimeStateTransferError::ReplacementRejected);
    }
}

TEST_CASE("owner import transactions expose bounded durable lifecycle status") {
    auto abort_count = std::make_shared<std::atomic<int>>(0);
    NoopImportTransaction legacy(abort_count);
    CHECK(legacy.status().phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Prepared);
    CHECK_FALSE(legacy.status().durable);

    const auto legacy_commit_timeout = legacy.commit_with_deadline(10, 10);
    CHECK(legacy_commit_timeout.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Prepared);
    CHECK(legacy_commit_timeout.error ==
          host::RuntimeStateTransferError::ImportTransactionDeadlineExceeded);

    const auto legacy_abort_timeout = legacy.abort_with_deadline(10, 10);
    CHECK(legacy_abort_timeout.phase ==
          host::RuntimeStateOwnerImportTransactionPhase::Ambiguous);
    CHECK(legacy_abort_timeout.error ==
          host::RuntimeStateTransferError::ImportTransactionDeadlineExceeded);

    DurableStatusImportTransaction durable;
    const auto committed = durable.commit_with_deadline(10, 20);
    REQUIRE(committed);
    CHECK(committed.phase == host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);
    CHECK(committed.journal_sequence != 0);

    DurableStatusImportTransaction interrupted;
    const auto ambiguous = interrupted.abort_with_deadline(20, 20);
    CHECK(ambiguous.phase == host::RuntimeStateOwnerImportTransactionPhase::Ambiguous);
    CHECK(ambiguous.error ==
          host::RuntimeStateTransferError::ImportTransactionDeadlineExceeded);
    const auto recovered = interrupted.recover_with_deadline(21, 30);
    REQUIRE(recovered);
    CHECK(recovered.phase == host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    CHECK(recovered.durable);
    CHECK(recovered.journal_sequence != ambiguous.journal_sequence);
}

TEST_CASE("decoder and replay matrix covers every state category and one generation window") {
    const auto &matrix = host::runtime_state_decoder_replay_matrix();
    REQUIRE(matrix.size() == host::kRuntimeStateCategoryCount);
    for (std::size_t index = 0; index < matrix.size(); ++index) {
        const auto &rule = matrix[index];
        CHECK(static_cast<std::size_t>(rule.category) == index);
        CHECK(rule.owner_id == host::runtime_state_owner_id(rule.category));
        CHECK(rule.schema_id == host::runtime_state_schema_id(rule.category));
        CHECK(rule.current_schema_generation ==
              host::kRuntimeStateTransferContractGeneration);
        CHECK(rule.previous_schema_generation ==
              host::kRuntimeStateTransferPreviousGeneration);
        CHECK(rule.migration_sha256.size() == 64);
        CHECK(rule.rollback_required);
        CHECK(host::runtime_state_decoder_replay_rule(rule.category) == &rule);
    }
}

TEST_CASE("canonical profile factory binds all rows to the decoder matrix") {
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "profile:canonical", 7, kHash, kHash2);
    REQUIRE(profile.profile_id == "profile:canonical");
    REQUIRE(profile.profile_generation == 7);
    REQUIRE(profile.source_plan_sha256 == kHash);
    REQUIRE(profile.target_plan_sha256 == kHash2);
    REQUIRE(profile.rows.size() == host::kRuntimeStateCategoryCount);
    for (std::size_t index = 0; index < profile.rows.size(); ++index) {
        const auto &row = profile.rows[index];
        const auto &rule = host::runtime_state_decoder_replay_matrix()[index];
        CHECK(row.category == rule.category);
        CHECK(row.disposition == rule.disposition);
        CHECK(row.owner_id == rule.owner_id);
        CHECK(row.schema_id == rule.schema_id);
        CHECK(row.minimum_schema_generation == rule.previous_schema_generation);
        CHECK(row.maximum_schema_generation == rule.current_schema_generation);
    }
}

TEST_CASE("fixed twelve-owner adapter registry executes current and N-1 generations") {
    bool emit_previous_generation = false;
    bool corrupt_last_import = false;
    const auto cleanup_abort_count = std::make_shared<std::atomic<int>>(0);
    std::array<host::RuntimeStateOwnerAdapterRegistration,
                host::kRuntimeStateCategoryCount>
        registrations{};
    for (std::size_t index = 0; index < registrations.size(); ++index) {
        const auto category = static_cast<host::RuntimeStateCategory>(index);
        registrations[index].category = category;
        registrations[index].owner_id = std::string(host::runtime_state_owner_id(category));
        registrations[index].schema_id = std::string(host::runtime_state_schema_id(category));
        registrations[index].migration_sha256 = std::string(
            host::runtime_state_decoder_replay_matrix()[index].migration_sha256);
        registrations[index].export_state = [category, &emit_previous_generation](
                                                const host::RuntimeStateTransferProfile &profile,
                                                const RuntimeIncarnationRef &,
                                                const host::RuntimeStateOwnerExportContext &context) {
            const auto &snapshot = context.barrier_snapshot;
            const auto row = std::find_if(
                profile.rows.begin(), profile.rows.end(),
                [category](const auto &candidate) { return candidate.category == category; });
            REQUIRE(row != profile.rows.end());
            host::RuntimeStateCensusEntry entry{
                .category = category,
                .disposition = row->disposition,
                .owner_id = row->owner_id,
                .schema_id = row->schema_id,
                .schema_generation = emit_previous_generation
                                         ? host::kRuntimeStateTransferPreviousGeneration
                                         : host::kRuntimeStateTransferContractGeneration,
                .sequence_high_watermark = 17,
                .rng_draw_position = 18,
                .simulation_tick = 19,
                .step_sequence = snapshot.step_sequence,
                .barrier_sequence = snapshot.barrier_sequence,
            };
            if (row->disposition == host::RuntimeStateDisposition::Transfer) {
                const auto owner_payload = fixture_owner_state_payload(
                    category, entry.schema_generation);
                entry.state_content_sha256 =
                    host::runtime_state_payload_sha256(owner_payload);
                entry.canonical_payload = host::runtime_state_canonical_payload(entry);
                entry.canonical_payload_sha256 =
                    host::runtime_state_payload_sha256(entry.canonical_payload);
                entry.semantic_evidence_sha256 = kHash;
            } else if (row->disposition == host::RuntimeStateDisposition::Rederive ||
                       row->disposition == host::RuntimeStateDisposition::Drain) {
                entry.semantic_evidence_sha256 = kHash2;
            }
            host::RuntimeStateOwnerArtifact artifact{
                .category = category,
                .schema_id = entry.schema_id,
                .schema_generation = entry.schema_generation,
                .payload = row->disposition == host::RuntimeStateDisposition::Transfer
                               ? fixture_owner_state_payload(category,
                                                             entry.schema_generation)
                               : std::vector<std::uint8_t>{},
            };
            artifact.payload_sha256 = host::runtime_state_payload_sha256(artifact.payload);
            return host::RuntimeStateOwnerAdapterExport{
                .census_entry = std::move(entry), .artifact = std::move(artifact)};
        };
        registrations[index].migrate_previous = [](const auto &source) {
            auto migrated = source;
            migrated.schema_generation = host::kRuntimeStateTransferContractGeneration;
            migrated.payload.push_back(0x02U);
            migrated.payload_sha256 =
                host::runtime_state_payload_sha256(migrated.payload);
            return migrated;
        };
    registrations[index].import_state = [category, &corrupt_last_import,
                                              cleanup_abort_count](
                                                const host::RuntimeStateTransferProfile &,
                                                const RuntimeIncarnationRef &,
                                                const host::RuntimeStateCensusEntry &entry,
                                                const host::RuntimeStateOwnerArtifact &source_artifact,
                                                const host::RuntimeStateOwnerArtifact &admitted_artifact,
                                                const RuntimeIdentity128 &candidate_identity) {
            host::RuntimeStateOwnerObservation observation{
                .category = category,
                .owner_id = entry.owner_id,
                .schema_id = entry.schema_id,
                .schema_generation = admitted_artifact.schema_generation,
                .source_entry_sha256 = host::runtime_state_census_entry_sha256(entry),
                .candidate_entry_sha256 = [&] {
                    auto normalized = entry;
                    normalized.schema_generation =
                        host::kRuntimeStateTransferContractGeneration;
                    if (entry.schema_generation !=
                        host::kRuntimeStateTransferContractGeneration) {
                        normalized.canonical_payload =
                            host::runtime_state_canonical_payload(normalized);
                        normalized.canonical_payload_sha256 =
                            host::runtime_state_payload_sha256(
                                normalized.canonical_payload);
                    }
                    return host::runtime_state_census_entry_sha256(normalized);
                }(),
                .source_artifact_payload_sha256 = source_artifact.payload_sha256,
                .candidate_artifact_payload_sha256 = admitted_artifact.payload_sha256,
                .semantic_replay_sha256 = entry.semantic_evidence_sha256,
                .candidate_resource_identity = candidate_identity,
                .item_count = entry.item_count,
                .settled_item_count = entry.settled_item_count,
                .source_schema_generation = entry.schema_generation,
                .exact_schema_decoded = true,
            };
            if (corrupt_last_import &&
                category == host::RuntimeStateCategory::DiagnosticsTelemetry) {
                observation.owner_id = "invalid-owner";
            }
            return host::RuntimeStateOwnerAdapterImport{
                .observation = std::move(observation),
                .transaction = corrupt_last_import
                                   ? std::static_pointer_cast<
                                         host::RuntimeStateOwnerImportTransaction>(
                                         std::make_shared<CountingAbortImportTransaction>(
                                             cleanup_abort_count))
                                   : std::static_pointer_cast<
                                         host::RuntimeStateOwnerImportTransaction>(
                                         std::make_shared<DurableStatusImportTransaction>()),
            };
        };
    }

    const auto registry = std::make_shared<host::RuntimeStateOwnerAdapterRegistry>(
        std::move(registrations));
    REQUIRE(registry->registration_status());
    const auto profile = host::runtime_state_transfer_profile_from_decoder_matrix(
        "profile:adapter-registry", 1, kHash, kHash2);
    const auto exported = registry->export_source(profile, slot(130), {});
    REQUIRE(exported.status);
    REQUIRE(exported.census.entries.size() == host::kRuntimeStateCategoryCount);
    REQUIRE(exported.artifacts.size() == host::kRuntimeStateCategoryCount);

    const auto imported = registry->import_and_observe(
        profile, exported, RuntimeIdentity128{.high = 131, .low = 132});
    REQUIRE(imported.status);
    REQUIRE(imported.observations.size() == host::kRuntimeStateCategoryCount);
    REQUIRE(imported.transaction != nullptr);
    const auto committed = imported.transaction->commit_with_deadline(1, 100);
    REQUIRE(committed);
    CHECK(committed.phase == host::RuntimeStateOwnerImportTransactionPhase::Committed);
    CHECK(committed.durable);
    CHECK(committed.journal_sequence != 0);

    emit_previous_generation = true;
    const auto previous_export = registry->export_source(profile, slot(133), {});
    REQUIRE(previous_export.status);
    const auto previous_import = registry->import_and_observe(
        profile, previous_export, RuntimeIdentity128{.high = 134, .low = 135});
    REQUIRE(previous_import.status);
    REQUIRE(previous_import.observations.size() == host::kRuntimeStateCategoryCount);
    for (const auto &observation : previous_import.observations) {
        CHECK(observation.source_schema_generation ==
              host::kRuntimeStateTransferPreviousGeneration);
        CHECK(observation.schema_generation ==
              host::kRuntimeStateTransferContractGeneration);
        CHECK(observation.source_artifact_payload_sha256 !=
              observation.candidate_artifact_payload_sha256);
    }
    REQUIRE(previous_import.transaction->abort_with_deadline(2, 100));

    corrupt_last_import = true;
    const auto rejected_import = registry->import_and_observe(
        profile, previous_export, RuntimeIdentity128{.high = 136, .low = 137});
    CHECK_FALSE(rejected_import.status);
    CHECK(rejected_import.transaction == nullptr);
    CHECK(rejected_import.observations.empty());
    CHECK(cleanup_abort_count->load() ==
          static_cast<int>(host::kRuntimeStateCategoryCount));
}

TEST_CASE("file WAL persists terminal owner transaction across journal reopen") {
    const auto journal_path =
        std::filesystem::temp_directory_path() /
        "echelon_forge_p4b_owner_transaction_test.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    const std::string transaction_id = kHash;
    int commit_calls = 0;
    int abort_calls = 0;
    auto callbacks = host::RuntimeStateOwnerImportRecoveryCallbacks{
        .commit = [&] {
            ++commit_calls;
            return true;
        },
        .abort = [&] {
            ++abort_calls;
            return true;
        },
        .recover = [] {
            return host::RuntimeStateOwnerImportTransactionPhase::Aborted;
        },
        .verify = [] { return true; },
    };
    {
        auto journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        host::RuntimeDurableOwnerImportTransaction transaction(
            transaction_id, kHash2, journal, callbacks);
        const auto prepared = transaction.status();
        REQUIRE(prepared.phase ==
                host::RuntimeStateOwnerImportTransactionPhase::Prepared);
        REQUIRE(prepared.durable);
        REQUIRE(prepared.journal_sequence == 1);
        const auto committed = transaction.commit_with_deadline(1, 20);
        REQUIRE(committed);
        CHECK(committed.phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Committed);
        CHECK(committed.durable);
        CHECK(committed.journal_sequence == 3);
        CHECK(commit_calls == 1);
        CHECK(abort_calls == 0);
    }
    {
        auto reopened = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        host::RuntimeDurableOwnerImportTransaction recovered(
            transaction_id, kHash2, reopened, callbacks);
        const auto status = recovered.status();
        REQUIRE(status.phase ==
                host::RuntimeStateOwnerImportTransactionPhase::Committed);
        REQUIRE(status.durable);
        CHECK(status.journal_sequence == 3);
        CHECK(recovered.commit_with_deadline(2, 20).phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Committed);
        CHECK(commit_calls == 1);
    }
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("file WAL reconciles interrupted commit and rejects complete corruption") {
    const auto journal_path =
        std::filesystem::temp_directory_path() /
        "echelon_forge_p4b_owner_recovery_test.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    const std::string transaction_id = kHash;
    {
        auto journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        REQUIRE(journal->append_and_sync(
            transaction_id, host::RuntimeStateOwnerImportTransactionPhase::Prepared,
            kHash2).status);
        REQUIRE(journal->append_and_sync(
            transaction_id, host::RuntimeStateOwnerImportTransactionPhase::Committing,
            kHash2).status);
    }
    {
        auto reopened = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        host::RuntimeDurableOwnerImportTransaction interrupted(
            transaction_id, kHash2, reopened,
            {.commit = [] { return false; },
             .abort = [] { return true; },
             .recover = [] {
                 return host::RuntimeStateOwnerImportTransactionPhase::Aborted;
             }});
        CHECK(interrupted.status().phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Committing);
        const auto reconciled = interrupted.recover_with_deadline(3, 20);
        REQUIRE(reconciled);
        CHECK(reconciled.phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Aborted);
        CHECK(reconciled.journal_sequence == 3);
        CHECK(reconciled.durable);
    }
    {
        std::ofstream torn(journal_path, std::ios::binary | std::ios::app);
        torn << "torn-tail-without-newline";
    }
    {
        auto reopened = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        REQUIRE(reopened->latest(transaction_id).status);
        host::RuntimeDurableOwnerImportTransaction after_torn_tail(
            kHash2, kHash, reopened,
            {.commit = [] { return true; },
             .abort = [] { return true; },
             .recover = [] {
                 return host::RuntimeStateOwnerImportTransactionPhase::Aborted;
             }});
        REQUIRE(after_torn_tail.status().phase ==
                host::RuntimeStateOwnerImportTransactionPhase::Prepared);
        REQUIRE(after_torn_tail.abort_with_deadline(4, 20).phase ==
                host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    }
    {
        std::ofstream corrupt(journal_path, std::ios::binary | std::ios::app);
        corrupt << "complete-corrupt-frame\n";
    }
    {
        host::RuntimeStateTransferFileJournal corrupt(journal_path.string());
        CHECK(corrupt.latest(transaction_id).status.error ==
              host::RuntimeStateTransferError::ImportJournalCorrupt);
    }
    std::filesystem::remove(journal_path, remove_error);
}

TEST_CASE("file WAL reopens a compensated terminal abort") {
    const auto journal_path =
        std::filesystem::temp_directory_path() /
        "echelon_forge_p4b_owner_compensated_abort_test.wal";
    std::error_code remove_error;
    std::filesystem::remove(journal_path, remove_error);
    const std::string transaction_id = kHash;
    auto callbacks = host::RuntimeStateOwnerImportRecoveryCallbacks{
        .commit = [] { return true; },
        .abort = [] { return true; },
        .recover = [] {
            return host::RuntimeStateOwnerImportTransactionPhase::Aborted;
        },
        .compensate = [] { return true; },
        // Reopen must not trust the terminal marker without owner evidence;
        // recovery below reaffirms the compensated target state.
        .verify = [] { return false; },
    };
    {
        auto journal = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        host::RuntimeDurableOwnerImportTransaction transaction(
            transaction_id, kHash2, journal, callbacks);
        REQUIRE(transaction.commit_with_deadline(1, 20).phase ==
                host::RuntimeStateOwnerImportTransactionPhase::Committed);
        REQUIRE(transaction.rollback_committed());
        CHECK(transaction.status().phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Aborted);
    }
    {
        auto reopened = std::make_shared<host::RuntimeStateTransferFileJournal>(
            journal_path.string());
        host::RuntimeDurableOwnerImportTransaction recovered(
            transaction_id, kHash2, reopened, callbacks);
        CHECK(recovered.status().phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Ambiguous);
        const auto reconciled = recovered.recover_with_deadline(3, 20);
        REQUIRE(reconciled);
        CHECK(reconciled.phase ==
              host::RuntimeStateOwnerImportTransactionPhase::Aborted);
        CHECK(reconciled.durable);
    }
    std::filesystem::remove(journal_path, remove_error);
}

} // TEST_SUITE
