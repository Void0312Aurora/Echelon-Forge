#include "runtime_host_candidate.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <limits>
#include <mutex>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <utility>

namespace runtime::host {

constexpr std::uint64_t kFirstIncarnationEpoch = 1;
constexpr std::size_t kMaxAdmittedShadowEpisodes = 4096;
constexpr std::uint64_t kMaxWorldSlots = 64;

RuntimeHostStatus success() {
    return {};
}

RuntimeHostStatus failure(RuntimeHostError error, std::string detail) {
    return {.error = error, .detail = std::move(detail)};
}

bool is_lower_hex_sha256(const std::string &value) {
    if (value.size() != 64) {
        return false;
    }
    return std::all_of(value.begin(), value.end(), [](unsigned char character) {
        return (character >= '0' && character <= '9') || (character >= 'a' && character <= 'f');
    });
}

bool same_slot(const RuntimeIncarnationRef &lhs, const RuntimeIncarnationRef &rhs) {
    return lhs.well_formed() && rhs.well_formed() && lhs == rhs;
}

bool same_host(const RuntimeHostIdentity &lhs, const RuntimeHostIdentity &rhs) {
    return lhs.well_formed() && rhs.well_formed() && lhs == rhs;
}

bool increment_nonzero(std::uint64_t &value) {
    if (value == std::numeric_limits<std::uint64_t>::max()) {
        return false;
    }
    ++value;
    return value != 0;
}

RuntimeIdentity128 mint_identity_nonce() {
    static std::atomic<std::uint64_t> fallback_sequence{1};
    RuntimeIdentity128 output;
    try {
        std::random_device random;
        auto next64 = [&random]() {
            std::uint64_t value = 0;
            for (int index = 0; index < 4; ++index) {
                value = (value << 16U) ^ static_cast<std::uint64_t>(random());
            }
            return value;
        };
        output = {.high = next64(), .low = next64()};
    } catch (...) {
        output = {};
    }
    const std::uint64_t fallback = fallback_sequence.fetch_add(1, std::memory_order_relaxed);
    output.low ^= fallback == 0 ? 1 : fallback;
    if (!output.well_formed()) {
        output.low = fallback == 0 ? 1 : fallback;
    }
    return output;
}

bool supported_transaction_kind(RuntimeHostTransactionKind kind) noexcept {
    switch (kind) {
    case RuntimeHostTransactionKind::Initial:
    case RuntimeHostTransactionKind::Replacement:
    case RuntimeHostTransactionKind::CheckpointRecovery:
        return true;
    }
    return false;
}

bool supported_lease_kind(RuntimeLeaseKind kind) noexcept {
    switch (kind) {
    case RuntimeLeaseKind::TruthMutating:
    case RuntimeLeaseKind::ReadOnlyResult:
        return true;
    }
    return false;
}

RuntimeRequestRef invalid_request_ref() {
    return {};
}

struct RuntimeHostSlot;

struct RuntimeAdmittedShadowEpisode {
    RuntimeEpisodeRef episode;
    RuntimeNativeEpisodeCapability native_episode;
};

struct RuntimeWorldAuthorityRecord {
    std::uint64_t world_generation = 0;
    RuntimeIdentity128 coordinator_nonce;
};

struct RuntimeHostSharedState {
    explicit RuntimeHostSharedState(RuntimeHostConfig config_value)
        : config(std::move(config_value)),
          identity{.host_id = config.host_id, .boot_id = mint_identity_nonce()},
          host_instance_nonce(mint_identity_nonce()) {}

    mutable std::mutex mutex;
    RuntimeHostConfig config;
    RuntimeHostIdentity identity;
    RuntimeIdentity128 host_instance_nonce;
    RuntimeHostState host_state = RuntimeHostState::Absent;
    bool production_authorized = false;

    // Lifecycle decisions are serialized by mutex. The active pointer is an
    // atomic shared_ptr so every publication path has a real CAS linearization
    // point and cannot regress to a plain pointer swap.
    std::atomic<std::shared_ptr<RuntimeHostSlot>> active;
    std::shared_ptr<RuntimeHostSlot> candidate;
    std::shared_ptr<RuntimeHostSlot> draining;
    std::vector<std::shared_ptr<RuntimeHostSlot>> quarantined;
    std::shared_ptr<RuntimeHostSlot> shutdown_pending;
    std::mutex pending_rollback_mutex;
    std::shared_ptr<RuntimeHostSlot> pending_rollback_active;
    std::shared_ptr<RuntimeHostSlot> pending_rollback_candidate;

    std::uint64_t last_lifecycle_ticket = 0;
    std::uint64_t last_candidate_sequence = 0;
    std::uint64_t last_request_sequence = 0;
    std::uint64_t last_episode_capability_sequence = 0;
    std::uint64_t last_publication_ticket = 0;
    std::uint64_t last_transfer_fence_sequence = 0;
    std::uint64_t shutdown_ticket = 0;
    std::uint64_t shutdown_deadline_tick = 0;
    std::uint64_t retired_incarnation_high_watermark = 0;
    std::unordered_map<std::uint64_t, RuntimeAdmittedShadowEpisode> admitted_shadow_episodes;
    std::unordered_map<std::uint64_t, RuntimeWorldAuthorityRecord> world_authority;
    std::unordered_map<std::uint64_t, std::shared_ptr<RuntimeEpisodeCoordinatorCandidate>>
        world_coordinators;
    // Saved source routing used only while a failed replacement is retained
    // for durable owner-outcome recovery.
    std::unordered_map<std::uint64_t, RuntimeWorldAuthorityRecord> rollback_world_authority;
    std::unordered_map<std::uint64_t, std::shared_ptr<RuntimeEpisodeCoordinatorCandidate>>
        rollback_world_coordinators;
    std::atomic<std::size_t> state_transfers_in_flight{0};
    std::size_t native_episode_submissions_in_flight = 0;
    bool orphan_handoff_recorded = false;
};

struct RuntimeOwnerHandleToken {
    std::weak_ptr<RuntimeHostSharedState> issuer;
    RuntimeHostIdentity host;
    RuntimeIdentity128 host_instance_nonce;
    RuntimeIdentity128 resource_identity;
    std::shared_ptr<RuntimeInstanceControl> control;
    RuntimeIdentity128 authenticator;
    bool binding_present = false;
    RuntimeOwnerAdmissionBinding binding;
    std::atomic<bool> consumed{false};
};

struct RuntimeHostSlot {
    std::uint64_t candidate_sequence = 0;
    RuntimeHostTransactionKind transaction_kind = RuntimeHostTransactionKind::Initial;
    RuntimePlanBinding plan;
    std::shared_ptr<RuntimeInstanceControl> control;
    std::shared_ptr<RuntimeNativeEpisodeControl> native_episode_control;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> owner_registry;
    RuntimeIdentity128 resource_identity;
    RuntimeIncarnationRef incarnation;
    RuntimeSlotState state = RuntimeSlotState::Constructing;
    bool admission_open = false;
    bool result_publication_open = false;
    std::size_t truth_mutating_leases = 0;
    std::size_t read_only_result_leases = 0;
    std::uint64_t final_transfer_fence_sequence = 0;
    std::uint64_t lifecycle_deadline_tick = 0;
    std::uint64_t drain_deadline_tick = 0;
    std::uint64_t world_slot_count = 0;
    std::string opaque_transfer_sha256;
    RuntimeValidatedStateTransfer validated_transfer;
    // For a replacement publication that fails after the active-pointer CAS,
    // retain the source slot so an explicit owner-transaction recovery can
    // restore the pre-publication authority without guessing.
    std::shared_ptr<RuntimeHostSlot> rollback_target;
    bool owner_publication_recovery_pending = false;
    bool resources_released = false;
    bool cancellation_in_progress = false;
    bool cancellation_acknowledged = false;
    std::atomic<bool> quiescence_capability_live{false};
};

using RuntimeCoordinatorMap =
    std::unordered_map<std::uint64_t, std::shared_ptr<RuntimeEpisodeCoordinatorCandidate>>;

std::optional<RuntimeCoordinatorMap> build_world_coordinators(
    const RuntimeHostSlot &slot,
    const std::optional<RuntimeEpisodeCoordinatorSnapshot> &transferred = std::nullopt) noexcept {
    try {
        RuntimeCoordinatorMap built;
        for (std::uint64_t world_slot = 0; world_slot < slot.world_slot_count; ++world_slot) {
            RuntimeEpisodeRef initial_episode{
                .world = {.incarnation = slot.incarnation,
                          .world_slot = world_slot,
                          .world_generation = 1},
                .episode_id = {.high = 0x4550462D434F4F52ULL, .low = world_slot + 1},
                .episode_generation = 1};
            std::uint64_t initial_step_sequence = 0;
            std::uint64_t initial_barrier_sequence = 0;
            RuntimeEpisodePhase initial_phase = RuntimeEpisodePhase::Running;
            RuntimeIdentity128 initial_snapshot_id{.high = 0x4550462D534E4150ULL,
                                                   .low = world_slot + 1};
            std::string initial_snapshot_sha256 =
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
            if (transferred.has_value() && transferred->episode.world.world_slot == world_slot) {
                initial_episode = transferred->episode;
                initial_episode.world.incarnation = slot.incarnation;
                initial_step_sequence = transferred->step_sequence;
                initial_barrier_sequence = transferred->barrier_sequence;
                // The source barrier proves a terminal episode, but its
                // ReplacementBarrier phase belongs to the source-side capability
                // and cannot be reconstructed on the fresh target coordinator.
                // Preserve the terminal boundary and require an explicit reset
                // before target actions are admitted.
                initial_phase = transferred->phase == RuntimeEpisodePhase::ReplacementBarrier
                                    ? RuntimeEpisodePhase::Terminal
                                    : transferred->phase;
                initial_snapshot_id = transferred->snapshot_id;
                initial_snapshot_sha256 = transferred->snapshot_sha256;
            }
            auto created = RuntimeEpisodeCoordinatorCandidate::create({
                .initial_episode = initial_episode,
                .initial_phase = initial_phase,
                .initial_snapshot_id = initial_snapshot_id,
                .initial_snapshot_sha256 = initial_snapshot_sha256,
                .initial_step_sequence = initial_step_sequence,
                .initial_barrier_sequence = initial_barrier_sequence,
            });
            if (!created.status || created.coordinator == nullptr) {
                return std::nullopt;
            }
            built.emplace(world_slot, std::shared_ptr<RuntimeEpisodeCoordinatorCandidate>(
                                          std::move(created.coordinator)));
        }
        return built;
    } catch (...) {
        // The host must never publish a slot whose native authority map is
        // only partially constructed.  The local map owns every coordinator
        // created before the failure and releases their world reservations.
        return std::nullopt;
    }
}

using RuntimeAuthorityMap = std::unordered_map<std::uint64_t, RuntimeWorldAuthorityRecord>;

std::optional<RuntimeAuthorityMap> build_world_authority(
    const RuntimeHostSlot &slot,
    const std::optional<RuntimeEpisodeCoordinatorSnapshot> &transferred = std::nullopt) noexcept {
    try {
        RuntimeAuthorityMap built;
        for (std::uint64_t world_slot = 0; world_slot < slot.world_slot_count; ++world_slot) {
            const std::uint64_t world_generation =
                transferred.has_value() && transferred->episode.world.world_slot == world_slot
                    ? transferred->episode.world.world_generation
                    : 1;
            built.emplace(world_slot,
                          RuntimeWorldAuthorityRecord{.world_generation = world_generation});
        }
        return built;
    } catch (...) {
        return std::nullopt;
    }
}

struct RuntimeLeaseToken {
    RuntimeLeaseToken(std::shared_ptr<RuntimeHostSharedState> state_value,
                      std::shared_ptr<RuntimeHostSlot> slot_value, RuntimeRequestRef request_value,
                      RuntimeLeaseKind kind_value)
        : state(std::move(state_value)), slot(std::move(slot_value)),
          request(std::move(request_value)), lease_kind(kind_value) {}

    ~RuntimeLeaseToken();

    std::shared_ptr<RuntimeHostSharedState> state;
    std::shared_ptr<RuntimeHostSlot> slot;
    RuntimeRequestRef request;
    RuntimeLeaseKind lease_kind = RuntimeLeaseKind::ReadOnlyResult;
    std::atomic<bool> active{true};
    std::atomic<bool> result_accepted{false};
};

struct HostOrphanRegistry {
    std::mutex mutex;
    std::vector<std::shared_ptr<RuntimeHostSharedState>> hosts;
};

struct ResourceIdentityRegistry {
    std::mutex mutex;
    std::vector<RuntimeIdentity128> identities;
};

HostOrphanRegistry &orphan_registry() {
    static HostOrphanRegistry *registry = new HostOrphanRegistry();
    return *registry;
}

ResourceIdentityRegistry &resource_identity_registry() {
    static ResourceIdentityRegistry *registry = new ResourceIdentityRegistry();
    return *registry;
}

bool reserve_resource_identity(const RuntimeIdentity128 &identity) {
    if (!identity.well_formed()) {
        return false;
    }
    ResourceIdentityRegistry &registry = resource_identity_registry();
    std::lock_guard<std::mutex> lock(registry.mutex);
    if (std::find(registry.identities.begin(), registry.identities.end(), identity) !=
        registry.identities.end()) {
        return false;
    }
    registry.identities.push_back(identity);
    return true;
}

void release_resource_identity(const RuntimeIdentity128 &identity) noexcept {
    try {
        ResourceIdentityRegistry &registry = resource_identity_registry();
        std::lock_guard<std::mutex> lock(registry.mutex);
        const auto position =
            std::find(registry.identities.begin(), registry.identities.end(), identity);
        if (position != registry.identities.end()) {
            registry.identities.erase(position);
        }
    } catch (...) {
        // A retained identity fails closed against accidental aliasing.
    }
}

void retain_orphan_state(const std::shared_ptr<RuntimeHostSharedState> &state) noexcept {
    if (state == nullptr) {
        return;
    }
    try {
        HostOrphanRegistry &registry = orphan_registry();
        std::scoped_lock lock(registry.mutex, state->mutex);
        const bool owns_resources = state->active.load(std::memory_order_acquire) != nullptr ||
                                    state->candidate != nullptr || state->draining != nullptr ||
                                    state->shutdown_pending != nullptr ||
                                    !state->quarantined.empty();
        if (!state->orphan_handoff_recorded && owns_resources) {
            state->orphan_handoff_recorded = true;
            registry.hosts.push_back(state);
        }
    } catch (...) {
        // Silent destruction would violate the resource-ownership contract.
        std::terminate();
    }
}

bool invoke_cas_fault_injector(const std::shared_ptr<RuntimeHostSharedState> &state,
                               RuntimeSlotCasOperation operation) noexcept {
    const std::shared_ptr<RuntimeHostCasFaultInjector> injector =
        state == nullptr ? nullptr : state->config.cas_fault_injector;
    return injector != nullptr && injector->force_loss(operation);
}

RuntimeSlotSnapshot snapshot_slot(const RuntimeHostSlot &slot) {
    return {
        .candidate_sequence = slot.candidate_sequence,
        .state = slot.state,
        .plan = slot.plan,
        .incarnation = slot.incarnation,
        .admission_open = slot.admission_open,
        .result_publication_open = slot.result_publication_open,
        .truth_mutating_leases = slot.truth_mutating_leases,
        .read_only_result_leases = slot.read_only_result_leases,
        .final_transfer_fence_sequence = slot.final_transfer_fence_sequence,
        .drain_deadline_tick = slot.drain_deadline_tick,
        .resources_released = slot.resources_released,
    };
}

bool no_leases(const RuntimeHostSlot &slot) {
    return slot.truth_mutating_leases == 0 && slot.read_only_result_leases == 0;
}

bool no_truth_leases(const RuntimeHostSlot &slot) {
    return slot.truth_mutating_leases == 0;
}

bool resource_identity_in_use(const RuntimeHostSharedState &state,
                              const RuntimeIdentity128 &identity) {
    if (!identity.well_formed()) {
        return true;
    }
    const auto matches = [&identity](const std::shared_ptr<RuntimeHostSlot> &slot) {
        return slot != nullptr && slot->resource_identity == identity &&
               slot->state != RuntimeSlotState::Retired;
    };
    if (matches(state.active.load(std::memory_order_acquire)) || matches(state.candidate) ||
        matches(state.draining) || matches(state.shutdown_pending)) {
        return true;
    }
    return std::any_of(state.quarantined.begin(), state.quarantined.end(), matches);
}

RuntimeHostStatus validate_candidate_handle(const RuntimeHostSharedState &state,
                                            const RuntimeCandidateHandle &handle) {
    if (!handle.well_formed()) {
        return failure(RuntimeHostError::InvalidArgument, "candidate handle is not well formed");
    }
    if (!supported_transaction_kind(handle.transaction_kind)) {
        return failure(RuntimeHostError::InvalidArgument,
                       "candidate handle has an unsupported transaction kind");
    }
    if (state.candidate == nullptr) {
        return failure(RuntimeHostError::CandidateNotFound, "host has no candidate");
    }
    if (!same_host(handle.host, state.identity) ||
        handle.host_instance_nonce != state.host_instance_nonce ||
        state.last_lifecycle_ticket != handle.lifecycle_ticket ||
        state.candidate->candidate_sequence != handle.candidate_sequence ||
        state.candidate->transaction_kind != handle.transaction_kind) {
        return failure(RuntimeHostError::CandidateNotFound,
                       "candidate handle does not identify the current lifecycle ticket");
    }
    return success();
}

RuntimeHostStatus validate_expected_slot(const RuntimeHostSharedState &state,
                                         const RuntimeIncarnationRef &expected,
                                         const RuntimeHostSlot &active) {
    if (!same_host(expected.host, state.identity) || !same_slot(expected, active.incarnation)) {
        return failure(RuntimeHostError::StaleExpectedSlot,
                       "expected slot does not match the current host incarnation");
    }
    return success();
}

void append_tombstone(RuntimeHostSharedState &state, const RuntimeHostSlot &slot) {
    if (!slot.incarnation.well_formed()) {
        return;
    }
    state.retired_incarnation_high_watermark =
        std::max(state.retired_incarnation_high_watermark, slot.incarnation.incarnation_epoch);
    for (auto iterator = state.admitted_shadow_episodes.begin();
         iterator != state.admitted_shadow_episodes.end();) {
        if (same_slot(iterator->second.episode.world.incarnation, slot.incarnation)) {
            iterator = state.admitted_shadow_episodes.erase(iterator);
        } else {
            ++iterator;
        }
    }
}

bool is_quarantined(const RuntimeHostSharedState &state,
                    const std::shared_ptr<RuntimeHostSlot> &slot) {
    return std::find(state.quarantined.begin(), state.quarantined.end(), slot) !=
           state.quarantined.end();
}

void retain_quarantine(RuntimeHostSharedState &state,
                       const std::shared_ptr<RuntimeHostSlot> &slot) {
    if (slot == nullptr || is_quarantined(state, slot)) {
        return;
    }
    state.quarantined.push_back(slot);
    if (state.quarantined.size() > 1) {
        state.host_state = RuntimeHostState::FailStopped;
    }
}

// The callback is invoked outside the host mutex. A slot in Reclaiming is not
// admitted by any operation, so another thread can safely observe the
// transitional state while resource release is in progress.
bool reclaim_slot(RuntimeHostSharedState &state, std::unique_lock<std::mutex> &lock,
                  const std::shared_ptr<RuntimeHostSlot> &slot) {
    if (slot == nullptr || !no_leases(*slot) ||
        state.state_transfers_in_flight.load(std::memory_order_acquire) != 0 ||
        state.native_episode_submissions_in_flight != 0 ||
        slot->state == RuntimeSlotState::Retired || slot->state == RuntimeSlotState::Reclaiming) {
        return false;
    }
    slot->state = RuntimeSlotState::Reclaiming;
    std::shared_ptr<RuntimeInstanceControl> control = slot->control;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> owner_registry = slot->owner_registry;
    slot->owner_registry.reset();
    lock.unlock();
    bool released = false;
    try {
        released =
            control != nullptr && control->release_resources() && control->resources_released();
    } catch (...) {
        released = false;
    }
    lock.lock();
    slot->resources_released = released;
    if (released) {
        slot->control.reset();
        // Keep Reclaiming visible while the final callback-capable owner is
        // destroyed outside the host mutex.
        lock.unlock();
        control.reset();
        owner_registry.reset();
        lock.lock();
        slot->state = RuntimeSlotState::Retired;
        append_tombstone(state, *slot);
        release_resource_identity(slot->resource_identity);
        return true;
    }
    slot->state = RuntimeSlotState::Quarantined;
    return false;
}

void clear_slot_reference(RuntimeHostSharedState &state,
                          const std::shared_ptr<RuntimeHostSlot> &slot) {
    if (state.candidate == slot) {
        state.candidate.reset();
    }
    if (state.draining == slot) {
        state.draining.reset();
    }
    const auto quarantine = std::find(state.quarantined.begin(), state.quarantined.end(), slot);
    if (quarantine != state.quarantined.end()) {
        state.quarantined.erase(quarantine);
    }
    if (state.shutdown_pending == slot) {
        state.shutdown_pending.reset();
    }
}

void apply_pending_quiescence_rollback(RuntimeHostSharedState &state) {
    std::shared_ptr<RuntimeHostSlot> active;
    std::shared_ptr<RuntimeHostSlot> candidate;
    {
        std::lock_guard<std::mutex> pending_lock(state.pending_rollback_mutex);
        active = std::move(state.pending_rollback_active);
        candidate = std::move(state.pending_rollback_candidate);
    }
    if (active == nullptr || candidate == nullptr) {
        return;
    }
    const bool same_attempt = state.host_state == RuntimeHostState::Active &&
                              state.active.load(std::memory_order_acquire) == active &&
                              state.candidate == candidate &&
                              active->state == RuntimeSlotState::Quiescing;
    if (!same_attempt) {
        return;
    }
    if (active->quiescence_capability_live.load(std::memory_order_acquire) ||
        active->truth_mutating_leases != 0 ||
        state.state_transfers_in_flight.load(std::memory_order_acquire) != 0 ||
        state.native_episode_submissions_in_flight != 0) {
        std::lock_guard<std::mutex> pending_lock(state.pending_rollback_mutex);
        state.pending_rollback_active = active;
        state.pending_rollback_candidate = candidate;
        return;
    }
    active->state = RuntimeSlotState::Active;
    active->admission_open = true;
    active->result_publication_open = true;
    active->final_transfer_fence_sequence = 0;
}

RuntimeHostStatus cancel_slot(RuntimeHostSharedState &state, std::unique_lock<std::mutex> &lock,
                              const std::shared_ptr<RuntimeHostSlot> &slot);

void abandon_transfer_outside_host_mutex(std::unique_lock<std::mutex> &lock,
                                         const std::shared_ptr<RuntimeHostSlot> &candidate) {
    if (candidate == nullptr) {
        return;
    }
    RuntimeValidatedStateTransfer transfer = std::move(candidate->validated_transfer);
    lock.unlock();
    transfer.abandon();
    lock.lock();
}

RuntimeHostStatus fail_candidate(RuntimeHostSharedState &state, std::unique_lock<std::mutex> &lock,
                                 const RuntimeHostStatus &reason) {
    std::shared_ptr<RuntimeHostSlot> candidate = state.candidate;
    if (candidate == nullptr) {
        return reason;
    }
    candidate->admission_open = false;
    candidate->result_publication_open = false;
    candidate->state = RuntimeSlotState::CandidateFailed;
    abandon_transfer_outside_host_mutex(lock, candidate);
    const RuntimeHostStatus cancellation = cancel_slot(state, lock, candidate);
    if (!cancellation) {
        return reason ? cancellation : reason;
    }
    const bool reclaimed = reclaim_slot(state, lock, candidate);
    if (reclaimed) {
        clear_slot_reference(state, candidate);
        lock.unlock();
        candidate.reset();
        lock.lock();
        return reason;
    }
    if (candidate->state == RuntimeSlotState::Quarantined) {
        retain_quarantine(state, candidate);
        state.candidate.reset();
        lock.unlock();
        candidate.reset();
        lock.lock();
        return failure(state.host_state == RuntimeHostState::FailStopped
                           ? RuntimeHostError::QuarantineUnresolved
                           : RuntimeHostError::ResourceReleaseFailed,
                       "candidate resource release failed; resource remains retained");
    }
    return reason;
}

RuntimeHostStatus cancel_slot(RuntimeHostSharedState &state, std::unique_lock<std::mutex> &lock,
                              const std::shared_ptr<RuntimeHostSlot> &slot) {
    (void)state;
    if (slot == nullptr || slot->control == nullptr || slot->cancellation_acknowledged) {
        return success();
    }
    if (slot->cancellation_in_progress) {
        return failure(RuntimeHostError::CancellationPending,
                       "cooperative cancellation is already in progress");
    }
    slot->cancellation_in_progress = true;
    const std::shared_ptr<RuntimeInstanceControl> control = slot->control;
    lock.unlock();
    bool acknowledged = false;
    try {
        acknowledged = control->request_cooperative_cancel();
    } catch (...) {
        acknowledged = false;
    }
    lock.lock();
    slot->cancellation_in_progress = false;
    slot->cancellation_acknowledged = acknowledged;
    return acknowledged ? success()
                        : failure(RuntimeHostError::CancellationPending,
                                  "cooperative cancellation was not acknowledged");
}

RuntimeHostStatus move_to_quarantine(RuntimeHostSharedState &state,
                                     const std::shared_ptr<RuntimeHostSlot> &slot) {
    slot->admission_open = false;
    slot->result_publication_open = false;
    slot->state = RuntimeSlotState::Quarantined;
    retain_quarantine(state, slot);
    return failure(RuntimeHostError::QuarantineUnresolved,
                   state.host_state == RuntimeHostState::FailStopped
                       ? "quarantine budget exhausted; all slots remain retained"
                       : "drain deadline expired; slot is quarantined");
}

RuntimeHostStatus compare_exchange_active(RuntimeHostSharedState &state,
                                          std::shared_ptr<RuntimeHostSlot> &expected,
                                          std::shared_ptr<RuntimeHostSlot> desired,
                                          bool injected_loss) {
    if (state.last_publication_ticket == std::numeric_limits<std::uint64_t>::max()) {
        return failure(RuntimeHostError::TicketExhausted, "publication ticket sequence exhausted");
    }
    if (injected_loss) {
        return failure(RuntimeHostError::PublicationRaceLost,
                       "publication compare-and-swap loss was injected");
    }
    if (!state.active.compare_exchange_strong(
            expected, std::move(desired), std::memory_order_acq_rel, std::memory_order_acquire)) {
        return failure(RuntimeHostError::PublicationRaceLost,
                       "active-slot compare-and-swap lost its expected value");
    }
    ++state.last_publication_ticket;
    return success();
}

RuntimeHostStatus settle_candidate_at_deadline(RuntimeHostSharedState &state,
                                               std::unique_lock<std::mutex> &lock,
                                               const RuntimeHostStatus &reason) {
    std::shared_ptr<RuntimeHostSlot> candidate = state.candidate;
    if (candidate == nullptr) {
        return reason;
    }
    candidate->admission_open = false;
    candidate->result_publication_open = false;
    candidate->state = RuntimeSlotState::CandidateFailed;
    abandon_transfer_outside_host_mutex(lock, candidate);
    const RuntimeHostStatus cancellation = cancel_slot(state, lock, candidate);
    if (!cancellation) {
        candidate->state = RuntimeSlotState::Quarantined;
        retain_quarantine(state, candidate);
        state.candidate.reset();
        lock.unlock();
        candidate.reset();
        lock.lock();
        return reason;
    }
    if (reclaim_slot(state, lock, candidate)) {
        clear_slot_reference(state, candidate);
        lock.unlock();
        candidate.reset();
        lock.lock();
    } else if (candidate->state == RuntimeSlotState::Quarantined) {
        retain_quarantine(state, candidate);
        state.candidate.reset();
        lock.unlock();
        candidate.reset();
        lock.lock();
    }
    return reason;
}

RuntimeHostStatus progress_candidate_deadline(RuntimeHostSharedState &state,
                                              std::unique_lock<std::mutex> &lock,
                                              std::uint64_t now_tick, bool injected_loss) {
    if (state.candidate == nullptr || state.candidate->lifecycle_deadline_tick == 0 ||
        now_tick < state.candidate->lifecycle_deadline_tick) {
        return success();
    }
    if (state.native_episode_submissions_in_flight != 0 ||
        state.state_transfers_in_flight.load(std::memory_order_acquire) != 0) {
        return failure(
            RuntimeHostError::CandidateBusy,
            "candidate deadline cannot retire a slot with native or state-transfer work in flight");
    }
    const std::shared_ptr<RuntimeHostSlot> old = state.active.load(std::memory_order_acquire);
    if (old != nullptr && old->state == RuntimeSlotState::Publishing) {
        return failure(RuntimeHostError::CandidateBusy,
                       "candidate deadline cannot interrupt target import publication");
    }
    const RuntimeHostStatus timeout =
        failure(RuntimeHostError::LifecycleDeadlineExpired,
                "candidate lifecycle deadline expired before publication");
    if (old == nullptr) {
        return settle_candidate_at_deadline(state, lock, timeout);
    }
    const bool quiescing = old->state == RuntimeSlotState::Quiescing ||
                           old->state == RuntimeSlotState::RecoveryQuiesced;
    if (!quiescing || no_truth_leases(*old)) {
        if (old->state == RuntimeSlotState::Quiescing) {
            old->state = RuntimeSlotState::Active;
            old->admission_open = true;
            old->result_publication_open = true;
            old->quiescence_capability_live.store(false, std::memory_order_release);
            state.host_state = RuntimeHostState::Active;
        } else if (old->state == RuntimeSlotState::RecoveryQuiesced) {
            old->state = RuntimeSlotState::ActiveFaulted;
            old->admission_open = false;
            old->result_publication_open = false;
            state.host_state = RuntimeHostState::Faulted;
        }
        return settle_candidate_at_deadline(state, lock, timeout);
    }

    std::shared_ptr<RuntimeHostSlot> expected = old;
    const RuntimeHostStatus unpublished =
        compare_exchange_active(state, expected, {}, injected_loss);
    if (!unpublished) {
        return unpublished;
    }
    old->admission_open = false;
    old->result_publication_open = false;
    old->state = RuntimeSlotState::Quarantined;
    retain_quarantine(state, old);

    const RuntimeHostStatus terminal_timeout =
        failure(RuntimeHostError::QuarantineUnresolved,
                "quiesce deadline expired with a live truth lease; host is fail-stopped");
    state.host_state = RuntimeHostState::FailStopped;
    (void)settle_candidate_at_deadline(state, lock, terminal_timeout);
    return terminal_timeout;
}

RuntimeHostStatus progress_fault_deadline(RuntimeHostSharedState &state,
                                          std::unique_lock<std::mutex> &lock,
                                          std::uint64_t now_tick, bool injected_loss) {
    if (state.host_state != RuntimeHostState::Faulted) {
        return success();
    }
    const std::shared_ptr<RuntimeHostSlot> faulted = state.active.load(std::memory_order_acquire);
    if (faulted == nullptr || faulted->state != RuntimeSlotState::ActiveFaulted ||
        now_tick < faulted->drain_deadline_tick) {
        return success();
    }
    if (state.native_episode_submissions_in_flight != 0) {
        return failure(RuntimeHostError::ShutdownPending,
                       "fault deadline is waiting for native episode submissions to settle");
    }
    state.host_state = RuntimeHostState::FailStopped;
    const RuntimeHostStatus terminal =
        failure(RuntimeHostError::HostTerminal, "fault deadline expired; host is fail-stopped");
    if (state.candidate != nullptr) {
        (void)settle_candidate_at_deadline(state, lock, terminal);
    }
    const RuntimeHostStatus cancellation = cancel_slot(state, lock, faulted);
    (void)cancellation;
    std::shared_ptr<RuntimeHostSlot> expected = faulted;
    const RuntimeHostStatus unpublished =
        compare_exchange_active(state, expected, {}, injected_loss);
    if (!unpublished) {
        state.host_state = RuntimeHostState::Faulted;
        return unpublished;
    }
    faulted->admission_open = false;
    faulted->result_publication_open = false;
    if (no_leases(*faulted) && reclaim_slot(state, lock, faulted)) {
        clear_slot_reference(state, faulted);
    } else {
        faulted->state = RuntimeSlotState::Quarantined;
        retain_quarantine(state, faulted);
    }
    return terminal;
}

RuntimeHostStatus progress_shutdown(RuntimeHostSharedState &state,
                                    std::unique_lock<std::mutex> &lock, std::uint64_t now_tick) {
    if (state.host_state != RuntimeHostState::ShuttingDown) {
        return success();
    }

    // begin_shutdown may have closed admission while a native callback was
    // still running.  Keep the active slot pinned until that callback has
    // returned; only then perform the CAS unpublish and reclamation steps.
    if (const std::shared_ptr<RuntimeHostSlot> active =
            state.active.load(std::memory_order_acquire);
        active != nullptr && active->state == RuntimeSlotState::ShuttingDown) {
        if (state.native_episode_submissions_in_flight != 0 ||
            state.state_transfers_in_flight.load(std::memory_order_acquire) != 0) {
            return failure(
                RuntimeHostError::ShutdownPending,
                "shutdown is waiting for native episode or state-transfer work to settle");
        }
        std::shared_ptr<RuntimeHostSlot> expected = active;
        const RuntimeHostStatus unpublished = compare_exchange_active(state, expected, {}, false);
        if (!unpublished) {
            return unpublished;
        }
        const RuntimeHostStatus cancellation = cancel_slot(state, lock, active);
        if (!cancellation) {
            state.shutdown_pending = active;
            return cancellation;
        }
        active->drain_deadline_tick = state.shutdown_deadline_tick;
        if (no_leases(*active)) {
            if (reclaim_slot(state, lock, active)) {
                clear_slot_reference(state, active);
            } else if (active->state == RuntimeSlotState::Quarantined) {
                retain_quarantine(state, active);
            }
        } else {
            active->state = RuntimeSlotState::Draining;
            state.draining = active;
        }
    }
    if (const std::shared_ptr<RuntimeHostSlot> active =
            state.active.load(std::memory_order_acquire);
        active != nullptr && active->state == RuntimeSlotState::Publishing) {
        return failure(RuntimeHostError::ShutdownPending,
                       "shutdown is waiting for target import publication to finish");
    }

    if (state.candidate != nullptr) {
        const std::shared_ptr<RuntimeHostSlot> candidate = state.candidate;
        if (candidate->state == RuntimeSlotState::Reclaiming) {
            return failure(RuntimeHostError::ShutdownPending,
                           "candidate reclamation is already in progress");
        }
        candidate->admission_open = false;
        candidate->result_publication_open = false;
        abandon_transfer_outside_host_mutex(lock, candidate);
        candidate->state = RuntimeSlotState::CandidateFailed;
        const RuntimeHostStatus cancellation = cancel_slot(state, lock, candidate);
        if (!cancellation) {
            if (now_tick < state.shutdown_deadline_tick) {
                return cancellation;
            }
            candidate->state = RuntimeSlotState::Quarantined;
            retain_quarantine(state, candidate);
            state.candidate.reset();
        } else {
            if (reclaim_slot(state, lock, candidate)) {
                clear_slot_reference(state, candidate);
            } else if (candidate->state == RuntimeSlotState::Quarantined) {
                retain_quarantine(state, candidate);
                state.candidate.reset();
            }
        }
    }

    if (state.draining != nullptr) {
        const std::shared_ptr<RuntimeHostSlot> draining = state.draining;
        if (no_leases(*draining)) {
            if (reclaim_slot(state, lock, draining)) {
                clear_slot_reference(state, draining);
            } else if (draining->state == RuntimeSlotState::Quarantined) {
                retain_quarantine(state, draining);
                state.draining.reset();
            }
        } else if (now_tick >= draining->drain_deadline_tick) {
            state.draining.reset();
            return move_to_quarantine(state, draining);
        }
    }

    if (state.shutdown_pending != nullptr && state.draining == nullptr) {
        const std::shared_ptr<RuntimeHostSlot> pending = state.shutdown_pending;
        const RuntimeHostStatus cancellation = cancel_slot(state, lock, pending);
        if (!cancellation) {
            if (now_tick < state.shutdown_deadline_tick) {
                return cancellation;
            }
            pending->state = RuntimeSlotState::Quarantined;
            retain_quarantine(state, pending);
            state.shutdown_pending.reset();
        } else {
            state.shutdown_pending.reset();
            pending->state = RuntimeSlotState::Draining;
            pending->drain_deadline_tick = state.shutdown_deadline_tick;
            state.draining = pending;
            if (no_leases(*pending)) {
                if (reclaim_slot(state, lock, pending)) {
                    clear_slot_reference(state, pending);
                } else if (pending->state == RuntimeSlotState::Quarantined) {
                    retain_quarantine(state, pending);
                    state.draining.reset();
                }
            }
        }
    }

    if (state.draining == nullptr && state.shutdown_pending == nullptr &&
        state.quarantined.empty() && state.active.load(std::memory_order_acquire) == nullptr &&
        state.candidate == nullptr) {
        state.host_state = RuntimeHostState::Stopped;
        return success();
    }
    if (state.host_state == RuntimeHostState::FailStopped) {
        return failure(RuntimeHostError::QuarantineUnresolved,
                       "shutdown retained more resources than the quarantine budget");
    }
    return failure(RuntimeHostError::ShutdownPending, "shutdown is waiting for slot settlement");
}

void release_lease_token(RuntimeLeaseToken &token) noexcept {
    const std::shared_ptr<RuntimeHostSharedState> state = token.state;
    if (state == nullptr || token.slot == nullptr) {
        return;
    }
    try {
        std::unique_lock<std::mutex> lock(state->mutex);
        bool expected_active = true;
        if (!token.active.compare_exchange_strong(expected_active, false, std::memory_order_acq_rel,
                                                  std::memory_order_acquire)) {
            return;
        }
        if (token.lease_kind == RuntimeLeaseKind::TruthMutating) {
            if (token.slot->truth_mutating_leases > 0) {
                --token.slot->truth_mutating_leases;
            }
        } else if (token.slot->read_only_result_leases > 0) {
            --token.slot->read_only_result_leases;
        }

        if (state->draining == token.slot && no_leases(*token.slot)) {
            if (reclaim_slot(*state, lock, token.slot)) {
                clear_slot_reference(*state, token.slot);
            } else if (token.slot->state == RuntimeSlotState::Quarantined) {
                retain_quarantine(*state, token.slot);
                state->draining.reset();
            }
        }
        if (is_quarantined(*state, token.slot) && no_leases(*token.slot) &&
            token.slot->state != RuntimeSlotState::Reclaiming) {
            if (reclaim_slot(*state, lock, token.slot)) {
                clear_slot_reference(*state, token.slot);
            }
        }
        if (state->host_state == RuntimeHostState::ShuttingDown &&
            (state->draining == nullptr || no_leases(*state->draining))) {
            // A lease destructor has no trusted clock sample. It may settle a
            // fully-drained slot, but must not treat the configured deadline as
            // "now" and quarantine other still-live leases prematurely.
            (void)progress_shutdown(*state, lock, 0);
        }
    } catch (...) {
        // A lease destructor cannot throw. The slot remains quarantined or
        // draining and the next explicit poll/retry reports the failure.
    }
}

RuntimeLeaseToken::~RuntimeLeaseToken() {
    release_lease_token(*this);
}

bool RuntimePlanBinding::well_formed() const noexcept {
    return !plan_id.empty() && is_lower_hex_sha256(plan_sha256);
}

RuntimeInstanceLease::RuntimeInstanceLease(std::shared_ptr<RuntimeLeaseToken> token) noexcept
    : token_(std::move(token)) {}

RuntimeInstanceLease::RuntimeInstanceLease(RuntimeInstanceLease &&other) noexcept
    : token_(std::move(other.token_)) {}

RuntimeInstanceLease &RuntimeInstanceLease::operator=(RuntimeInstanceLease &&other) noexcept {
    if (this != &other) {
        token_ = std::move(other.token_);
    }
    return *this;
}

RuntimeInstanceLease::~RuntimeInstanceLease() = default;

bool RuntimeInstanceLease::valid() const noexcept {
    return token_ != nullptr && token_->active.load(std::memory_order_acquire);
}

RuntimeLeaseKind RuntimeInstanceLease::kind() const noexcept {
    return token_ == nullptr ? RuntimeLeaseKind::ReadOnlyResult : token_->lease_kind;
}

RuntimeRequestRef RuntimeInstanceLease::request_ref() const noexcept {
    return token_ == nullptr ? invalid_request_ref() : token_->request;
}

void RuntimeInstanceLease::settle() noexcept {
    if (token_ != nullptr) {
        release_lease_token(*token_);
    }
}

bool RuntimeShadowEpisodeCapability::valid() const noexcept {
    return host_.well_formed() && host_instance_nonce_.well_formed() &&
           resource_identity_.well_formed() && episode_.well_formed() && capability_sequence_ != 0;
}

RuntimeEpisodeRef RuntimeShadowEpisodeCapability::episode() const noexcept {
    return episode_;
}

RuntimeIdentity128 RuntimeShadowEpisodeCapability::resource_identity() const noexcept {
    return resource_identity_;
}

RuntimeHostCandidate::RuntimeHostCandidate(RuntimeHostConfig config)
    : state_(std::make_shared<RuntimeHostSharedState>(std::move(config))) {
    if (!state_->config.host_id.well_formed() || !state_->identity.well_formed()) {
        throw std::invalid_argument("runtime host ID must be non-zero");
    }
    if (state_->config.mode != RuntimeHostMode::Dark &&
        state_->config.mode != RuntimeHostMode::Shadow) {
        throw std::invalid_argument("runtime host mode is unsupported");
    }
}

RuntimeHostCandidate::RuntimeHostCandidate(RuntimeHostCandidate &&other) noexcept
    : state_(std::move(other.state_)) {}

RuntimeHostCandidate &RuntimeHostCandidate::operator=(RuntimeHostCandidate &&other) noexcept {
    if (this != &other) {
        if (state_ != nullptr) {
            const std::shared_ptr<RuntimeHostSharedState> displaced = state_;
            try {
                (void)begin_shutdown(0, 0);
            } catch (...) {
                // Move assignment must not throw. Any unsettled resources are
                // retained by outstanding leases through the old shared state.
            }
            retain_orphan_state(displaced);
        }
        state_ = std::move(other.state_);
    }
    return *this;
}

RuntimeHostCandidate::~RuntimeHostCandidate() {
    if (state_ == nullptr) {
        return;
    }
    const std::shared_ptr<RuntimeHostSharedState> retiring = state_;
    try {
        (void)begin_shutdown(0, 0);
    } catch (...) {
        // Destruction must not throw. Live leases keep the shared state and
        // resource controls alive until their own explicit settlement.
    }
    retain_orphan_state(retiring);
}

bool RuntimeOwnerHandle::valid() const noexcept {
    return token_ != nullptr && token_->host.well_formed() &&
           token_->host_instance_nonce.well_formed() && token_->resource_identity.well_formed() &&
           token_->control != nullptr && token_->authenticator.well_formed() &&
           !token_->consumed.load(std::memory_order_acquire) && !token_->issuer.expired();
}

RuntimeIdentity128 RuntimeOwnerHandle::resource_identity() const noexcept {
    return token_ == nullptr ? RuntimeIdentity128{} : token_->resource_identity;
}

RuntimeOwnerHandle
RuntimeHostCandidate::issue_owner_handle(const std::shared_ptr<RuntimeInstanceControl> &control) {
    const std::shared_ptr<RuntimeHostSharedState> state = state_;
    if (state == nullptr || control == nullptr) {
        return {};
    }
    RuntimeIdentity128 resource_identity;
    try {
        resource_identity = control->resource_identity();
    } catch (...) {
        return {};
    }
    if (!resource_identity.well_formed()) {
        return {};
    }
    std::lock_guard<std::mutex> lock(state->mutex);
    if (state_ != state || state->host_state == RuntimeHostState::ShuttingDown ||
        state->host_state == RuntimeHostState::Stopped ||
        state->host_state == RuntimeHostState::FailStopped ||
        resource_identity_in_use(*state, resource_identity)) {
        return {};
    }
    try {
        auto token = std::make_shared<RuntimeOwnerHandleToken>();
        token->issuer = state;
        token->host = state->identity;
        token->host_instance_nonce = state->host_instance_nonce;
        token->resource_identity = resource_identity;
        token->control = control;
        token->authenticator = mint_identity_nonce();
        return RuntimeOwnerHandle(std::move(token));
    } catch (...) {
        return {};
    }
}

RuntimeOwnerHandle
RuntimeHostCandidate::issue_owner_handle(const std::shared_ptr<RuntimeInstanceControl> &control,
                                         const RuntimeOwnerAdmissionBinding &binding) {
    if (!binding.plan.well_formed() || binding.world_slot_count > kMaxWorldSlots ||
        (binding.expected_slot.has_value() && !binding.expected_slot->well_formed())) {
        return {};
    }
    RuntimeOwnerHandle handle = issue_owner_handle(control);
    if (!handle.valid()) {
        return {};
    }
    handle.token_->binding = binding;
    handle.token_->binding_present = true;
    return handle;
}

RuntimeCandidateBeginResult
RuntimeHostCandidate::begin_candidate(const RuntimeCandidateRequest &request,
                                      const RuntimeOwnerHandle &owner_handle) {
    const std::shared_ptr<RuntimeHostSharedState> state = state_;
    const std::shared_ptr<RuntimeOwnerHandleToken> token = owner_handle.token_;
    if (state == nullptr || token == nullptr || token->issuer.lock() != state ||
        token->host != state->identity ||
        token->host_instance_nonce != state->host_instance_nonce || token->control == nullptr ||
        token->consumed.load(std::memory_order_acquire)) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "owner handle is stale, forged, or already consumed"),
                .handle = {}};
    }
    if (token->control->resource_identity() != token->resource_identity) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "owner handle resource identity drifted"),
                .handle = {}};
    }
    if (token->binding_present && (token->binding.transaction_kind != request.transaction_kind ||
                                   token->binding.expected_slot != request.expected_slot ||
                                   token->binding.plan != request.plan ||
                                   (token->binding.world_slot_count != 0 &&
                                    token->binding.world_slot_count != request.world_slot_count))) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "owner handle admission binding does not match request"),
                .handle = {}};
    }
    if (token->consumed.exchange(true, std::memory_order_acq_rel)) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "owner handle is stale, forged, or already consumed"),
                .handle = {}};
    }
    RuntimeCandidateRequest bound_request = request;
    bound_request.control = token->control;
    const RuntimeCandidateBeginResult result = begin_candidate(bound_request);
    if (!result.status) {
        token->consumed.store(false, std::memory_order_release);
    }
    return result;
}

RuntimeCandidateBeginResult
RuntimeHostCandidate::begin_candidate(const RuntimeCandidateRequest &request) {
    const std::shared_ptr<RuntimeHostSharedState> state = state_;
    if (state == nullptr) {
        return {.status = failure(RuntimeHostError::HostTerminal, "host state is unavailable"),
                .handle = {}};
    }
    if (!request.plan.well_formed() || request.control == nullptr) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "candidate plan or control is not well formed"),
                .handle = {}};
    }
    const RuntimeIdentity128 resource_identity = request.control->resource_identity();
    if (!resource_identity.well_formed()) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "candidate resource identity is invalid"),
                .handle = {}};
    }

    std::unique_lock<std::mutex> lock(state->mutex);
    if (state_ != state) {
        return {.status = failure(RuntimeHostError::HostTerminal,
                                  "host object changed while reading candidate identity"),
                .handle = {}};
    }
    if (state->host_state == RuntimeHostState::ShuttingDown ||
        state->host_state == RuntimeHostState::Stopped ||
        state->host_state == RuntimeHostState::FailStopped) {
        return {.status = failure(RuntimeHostError::HostTerminal,
                                  "host cannot begin a candidate after shutdown"),
                .handle = {}};
    }
    if (!supported_transaction_kind(request.transaction_kind)) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "candidate request has an unsupported transaction kind"),
                .handle = {}};
    }
    if (request.lifecycle_deadline_tick == 0) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "every candidate transaction requires a lifecycle deadline"),
                .handle = {}};
    }
    if (request.world_slot_count > kMaxWorldSlots) {
        return {.status =
                    failure(RuntimeHostError::InvalidArgument,
                            "candidate world-slot cardinality exceeds the bounded host contract"),
                .handle = {}};
    }
    if (request.expected_slot.has_value() &&
        (!request.expected_slot->well_formed() ||
         !same_host(request.expected_slot->host, state->identity))) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "expected slot has the wrong host identity"),
                .handle = {}};
    }
    if (state->candidate != nullptr) {
        return {.status = failure(RuntimeHostError::CandidateBusy,
                                  "host already has an unpublished candidate"),
                .handle = {}};
    }
    if (!state->quarantined.empty()) {
        return {.status = failure(RuntimeHostError::QuarantineBackpressure,
                                  "unresolved quarantine freezes replacement"),
                .handle = {}};
    }
    if (state->draining != nullptr) {
        return {.status =
                    failure(RuntimeHostError::DrainBackpressure, "a prior slot is still draining"),
                .handle = {}};
    }
    if (resource_identity_in_use(*state, resource_identity)) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "candidate resource identity is invalid or already owned"),
                .handle = {}};
    }

    const std::shared_ptr<RuntimeHostSlot> active = state->active.load(std::memory_order_acquire);
    if (request.transaction_kind == RuntimeHostTransactionKind::Initial) {
        if (request.expected_slot.has_value() || state->host_state != RuntimeHostState::Absent ||
            active != nullptr) {
            return {.status = failure(RuntimeHostError::HostStateMismatch,
                                      "initial candidate requires an absent host"),
                    .handle = {}};
        }
    } else if (active == nullptr || !request.expected_slot.has_value() ||
               !same_slot(*request.expected_slot, active->incarnation)) {
        return {.status = failure(RuntimeHostError::StaleExpectedSlot,
                                  "candidate expected slot is not the current slot"),
                .handle = {}};
    } else if (request.transaction_kind == RuntimeHostTransactionKind::Replacement &&
               (state->host_state != RuntimeHostState::Active ||
                active->state != RuntimeSlotState::Active)) {
        return {.status = failure(RuntimeHostError::HostStateMismatch,
                                  "replacement requires an active slot"),
                .handle = {}};
    } else if (request.transaction_kind == RuntimeHostTransactionKind::CheckpointRecovery &&
               (state->host_state != RuntimeHostState::Faulted ||
                active->state != RuntimeSlotState::ActiveFaulted)) {
        return {.status = failure(RuntimeHostError::HostStateMismatch,
                                  "checkpoint recovery requires an active faulted slot"),
                .handle = {}};
    }

    // Resource-owner hooks are caller code.  Acquire the typed registry only
    // outside the host mutex, then revalidate the lifecycle predicates before
    // publishing the candidate so a reentrant or blocking hook cannot deadlock
    // the lifecycle state machine or bind a registry to a stale slot.
    lock.unlock();
    std::shared_ptr<RuntimeNativeEpisodeControl> native_episode_control;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> owner_registry;
    try {
        native_episode_control = request.control->native_episode_control();
        owner_registry = request.control->state_transfer_owner_registry();
    } catch (...) {
        return {.status = failure(RuntimeHostError::InvalidArgument,
                                  "candidate owner registry acquisition failed"),
                .handle = {}};
    }
    lock.lock();
    if (state_ != state) {
        lock.unlock();
        owner_registry.reset();
        return {.status = failure(RuntimeHostError::HostTerminal,
                                  "host object changed while acquiring the owner registry"),
                .handle = {}};
    }
    auto reject_after_registry = [&](RuntimeHostStatus reason) -> RuntimeCandidateBeginResult {
        lock.unlock();
        owner_registry.reset();
        return {.status = std::move(reason), .handle = {}};
    };
    if (native_episode_control == nullptr ||
        native_episode_control->resource_identity() != resource_identity ||
        owner_registry == nullptr) {
        return reject_after_registry(
            failure(RuntimeHostError::InvalidArgument,
                    "candidate control returned no host-bound native/owner adapter"));
    }
    const RuntimeIdentity128 bound_owner_resource = owner_registry->bound_resource_identity();
    if (!bound_owner_resource.well_formed() || bound_owner_resource != resource_identity ||
        owner_registry->owner_binding_token() == nullptr) {
        return reject_after_registry(
            failure(RuntimeHostError::InvalidArgument,
                    "candidate owner registry has no exact resource/owner binding"));
    }
    if (state->host_state == RuntimeHostState::ShuttingDown ||
        state->host_state == RuntimeHostState::Stopped ||
        state->host_state == RuntimeHostState::FailStopped || state->candidate != nullptr ||
        !state->quarantined.empty() || state->draining != nullptr ||
        resource_identity_in_use(*state, resource_identity)) {
        return reject_after_registry(
            failure(RuntimeHostError::CandidateBusy,
                    "host lifecycle changed while acquiring the owner registry"));
    }
    const std::shared_ptr<RuntimeHostSlot> current_active =
        state->active.load(std::memory_order_acquire);
    if (request.transaction_kind == RuntimeHostTransactionKind::Initial) {
        if (request.expected_slot.has_value() || state->host_state != RuntimeHostState::Absent ||
            current_active != nullptr) {
            return reject_after_registry(
                failure(RuntimeHostError::HostStateMismatch,
                        "initial candidate became stale while acquiring the owner registry"));
        }
    } else if (current_active == nullptr || !request.expected_slot.has_value() ||
               !same_slot(*request.expected_slot, current_active->incarnation)) {
        return reject_after_registry(
            failure(RuntimeHostError::StaleExpectedSlot,
                    "candidate expected slot changed while acquiring the owner registry"));
    } else if ((request.transaction_kind == RuntimeHostTransactionKind::Replacement ||
                request.transaction_kind == RuntimeHostTransactionKind::CheckpointRecovery) &&
               request.world_slot_count != 0 &&
               request.world_slot_count != current_active->world_slot_count) {
        return reject_after_registry(
            failure(RuntimeHostError::InvalidArgument,
                    "candidate world-slot cardinality cannot drop active authority slots"));
    } else if (request.transaction_kind == RuntimeHostTransactionKind::Replacement &&
               (state->host_state != RuntimeHostState::Active ||
                current_active->state != RuntimeSlotState::Active)) {
        return reject_after_registry(
            failure(RuntimeHostError::HostStateMismatch,
                    "replacement source changed while acquiring the owner registry"));
    } else if (request.transaction_kind == RuntimeHostTransactionKind::CheckpointRecovery &&
               (state->host_state != RuntimeHostState::Faulted ||
                current_active->state != RuntimeSlotState::ActiveFaulted)) {
        return reject_after_registry(
            failure(RuntimeHostError::HostStateMismatch,
                    "recovery source changed while acquiring the owner registry"));
    }

    if (!increment_nonzero(state->last_lifecycle_ticket) ||
        !increment_nonzero(state->last_candidate_sequence)) {
        return reject_after_registry(
            failure(RuntimeHostError::TicketExhausted, "lifecycle or candidate ticket exhausted"));
    }
    std::shared_ptr<RuntimeHostSlot> candidate;
    try {
        candidate = std::make_shared<RuntimeHostSlot>();
    } catch (...) {
        return reject_after_registry(
            failure(RuntimeHostError::InvalidArgument, "candidate slot allocation failed"));
    }
    candidate->candidate_sequence = state->last_candidate_sequence;
    candidate->transaction_kind = request.transaction_kind;
    candidate->plan = request.plan;
    candidate->control = request.control;
    candidate->native_episode_control = std::move(native_episode_control);
    candidate->owner_registry = std::move(owner_registry);
    candidate->resource_identity = resource_identity;
    candidate->lifecycle_deadline_tick = request.lifecycle_deadline_tick;
    candidate->world_slot_count = request.world_slot_count;
    if (candidate->world_slot_count == 0 && current_active != nullptr) {
        candidate->world_slot_count = current_active->world_slot_count;
    }
    candidate->state = RuntimeSlotState::Constructing;
    if (!reserve_resource_identity(resource_identity)) {
        const RuntimeHostStatus reason =
            failure(RuntimeHostError::InvalidArgument,
                    "candidate resource identity is owned by another host");
        lock.unlock();
        candidate.reset();
        return {.status = reason, .handle = {}};
    }
    state->candidate = std::move(candidate);
    return {.status = success(),
            .handle = {.host = state->identity,
                       .host_instance_nonce = state->host_instance_nonce,
                       .lifecycle_ticket = state->last_lifecycle_ticket,
                       .candidate_sequence = state->last_candidate_sequence,
                       .transaction_kind = request.transaction_kind}};
}

RuntimeHostStatus
RuntimeHostCandidate::validate_candidate(const RuntimeCandidateHandle &handle,
                                         const RuntimeCandidateValidationProof &proof) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return status;
    }
    RuntimeHostSlot &candidate = *state_->candidate;
    if (candidate.state != RuntimeSlotState::Constructing &&
        candidate.state != RuntimeSlotState::Validating) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "candidate validation must start from constructing");
    }
    candidate.state = RuntimeSlotState::Validating;
    const bool mode_probe_ok =
        state_->config.mode == RuntimeHostMode::Dark || proof.shadow_probe_passed;
    if (!proof.static_plan_validated || !proof.resources_ready || !mode_probe_ok ||
        !proof.unreachable_from_production || proof.production_authorized) {
        return fail_candidate(
            *state_, lock,
            failure(RuntimeHostError::InvalidCommitProof,
                    "candidate validation proof is incomplete or authorizes production"));
    }
    candidate.state = RuntimeSlotState::Ready;
    return success();
}

RuntimePublicationResult
RuntimeHostCandidate::commit_initial(const RuntimeCandidateHandle &handle,
                                     const RuntimeInitialCommitProof &proof) {
    const bool injected_loss =
        invoke_cas_fault_injector(state_, RuntimeSlotCasOperation::InitialPublish);
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return {.status = status, .published_slot = {}};
    }
    RuntimeHostSlot &candidate = *state_->candidate;
    if (candidate.state != RuntimeSlotState::Ready ||
        candidate.transaction_kind != RuntimeHostTransactionKind::Initial) {
        return {.status = failure(RuntimeHostError::InvalidCandidateState,
                                  "initial commit requires a validated initial candidate"),
                .published_slot = {}};
    }
    if (!is_lower_hex_sha256(proof.lifecycle_evidence_sha256) || !proof.dark_evidence_sealed ||
        proof.production_authorized) {
        return {.status = failure(RuntimeHostError::InvalidCommitProof,
                                  "initial commit requires sealed dark evidence"),
                .published_slot = {}};
    }
    candidate.incarnation = {.host = state_->identity, .incarnation_epoch = kFirstIncarnationEpoch};
    auto coordinators = build_world_coordinators(candidate);
    auto authority = build_world_authority(candidate);
    if (!coordinators.has_value() || !authority.has_value()) {
        return {.status = fail_candidate(
                    *state_, lock,
                    failure(RuntimeHostError::InvalidCommitProof,
                            "candidate native world authority could not be constructed")),
                .published_slot = {}};
    }
    candidate.state = RuntimeSlotState::InitialCommitReady;
    candidate.state = RuntimeSlotState::Publishing;
    candidate.admission_open = true;
    candidate.result_publication_open = true;
    std::shared_ptr<RuntimeHostSlot> expected;
    const RuntimeHostStatus publication =
        compare_exchange_active(*state_, expected, state_->candidate, injected_loss);
    if (!publication) {
        const RuntimeHostStatus failure_status = publication;
        return {.status = fail_candidate(*state_, lock, failure_status), .published_slot = {}};
    }
    state_->candidate->state = RuntimeSlotState::Active;
    state_->world_authority.swap(*authority);
    state_->world_coordinators.swap(*coordinators);
    const RuntimeIncarnationRef published = state_->candidate->incarnation;
    state_->candidate.reset();
    state_->host_state = RuntimeHostState::Active;
    return {.status = success(),
            .published_slot = published,
            .publication_ticket = state_->last_publication_ticket};
}

RuntimeHostStatus RuntimeHostCandidate::prepare_replacement(const RuntimeCandidateHandle &handle,
                                                            RuntimeTransferCommitProof &&proof) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return status;
    }
    if (state_->candidate->transaction_kind != RuntimeHostTransactionKind::Replacement) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "candidate is not a replacement transaction");
    }
    if (!proof.validated_transfer.valid() || proof.production_authorized) {
        return failure(RuntimeHostError::InvalidCommitProof,
                       "replacement requires a validated non-production P4-B state transfer");
    }
    if (proof.drain_deadline_tick == 0) {
        return failure(RuntimeHostError::InvalidArgument,
                       "replacement transfer requires a non-zero drain deadline");
    }
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (active == nullptr ||
        !same_slot(proof.validated_transfer.source_slot(), active->incarnation)) {
        return failure(RuntimeHostError::StaleExpectedSlot,
                       "replacement proof source is not the active slot");
    }
    if (active->state != RuntimeSlotState::Quiescing || !active->cancellation_acknowledged ||
        !no_truth_leases(*active) || active->final_transfer_fence_sequence == 0) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "replacement source lacks the final host quiescence fence");
    }
    if (state_->candidate->state == RuntimeSlotState::TransferCommitReady) {
        return success();
    }
    if (state_->candidate->state != RuntimeSlotState::Ready) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "replacement candidate is not ready or quiescing");
    }
    const RuntimeStateTransferStatus prepared = proof.validated_transfer.prepare_for_host(
        active->incarnation, active->plan.plan_sha256, state_->candidate->plan.plan_sha256,
        state_->candidate->resource_identity, handle.lifecycle_ticket, handle.candidate_sequence,
        active->final_transfer_fence_sequence);
    if (!prepared) {
        return failure(RuntimeHostError::InvalidCommitProof, prepared.detail);
    }
    state_->candidate->opaque_transfer_sha256 =
        std::string(proof.validated_transfer.state_bundle_sha256());
    state_->candidate->final_transfer_fence_sequence =
        proof.validated_transfer.transfer_fence_sequence();
    state_->candidate->validated_transfer = std::move(proof.validated_transfer);
    state_->candidate->drain_deadline_tick = proof.drain_deadline_tick;
    state_->candidate->state = RuntimeSlotState::TransferCommitReady;
    return success();
}

RuntimeReplacementQuiescenceResult
RuntimeHostCandidate::quiesce_replacement_source(const RuntimeCandidateHandle &handle) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    apply_pending_quiescence_rollback(*state_);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return {.status = status, .capability = {}};
    }
    const std::shared_ptr<RuntimeHostSlot> candidate = state_->candidate;
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (candidate->transaction_kind != RuntimeHostTransactionKind::Replacement ||
        candidate->state != RuntimeSlotState::Ready || active == nullptr) {
        return {.status =
                    failure(RuntimeHostError::InvalidCandidateState,
                            "replacement quiescence requires a ready candidate and active source"),
                .capability = {}};
    }
    if (state_->native_episode_submissions_in_flight != 0) {
        return {.status = failure(RuntimeHostError::CandidateBusy,
                                  "native episode submissions must settle before host quiescence"),
                .capability = {}};
    }
    if (candidate->world_slot_count != 1) {
        return {.status = failure(RuntimeHostError::InvalidCommitProof,
                                  "P4-B transfer requires one host-owned world barrier; "
                                  "multi-world transfer remains unqualified"),
                .capability = {}};
    }
    const auto coordinator = state_->world_coordinators.find(0);
    if (coordinator == state_->world_coordinators.end() ||
        coordinator->second->snapshot().phase != RuntimeEpisodePhase::Terminal) {
        return {.status =
                    failure(RuntimeHostError::InvalidCandidateState,
                            "replacement source episode must be terminal before host quiescence"),
                .capability = {}};
    }
    auto restore_source_after_failed_quiescence = [&]() noexcept {
        if (state_->host_state == RuntimeHostState::Active &&
            state_->active.load(std::memory_order_acquire) == active &&
            state_->candidate == candidate && active->state == RuntimeSlotState::Quiescing &&
            !active->quiescence_capability_live.load(std::memory_order_acquire) &&
            active->truth_mutating_leases == 0) {
            active->state = RuntimeSlotState::Active;
            active->admission_open = true;
            active->result_publication_open = true;
            active->final_transfer_fence_sequence = 0;
        }
    };
    if (active->state == RuntimeSlotState::Active) {
        active->admission_open = false;
        active->state = RuntimeSlotState::Quiescing;
    } else if (active->state == RuntimeSlotState::Quiescing) {
        if (active->quiescence_capability_live.load(std::memory_order_acquire)) {
            return {.status = failure(RuntimeHostError::CandidateBusy,
                                      "replacement source already has a live quiescence attempt"),
                    .capability = {}};
        }
    } else if (active->state != RuntimeSlotState::Quiescing) {
        return {.status = failure(RuntimeHostError::InvalidCandidateState,
                                  "replacement source is not active or quiescing"),
                .capability = {}};
    }
    if (!active->cancellation_acknowledged) {
        status = cancel_slot(*state_, lock, active);
        const RuntimeHostStatus transaction_status = validate_candidate_handle(*state_, handle);
        const std::shared_ptr<RuntimeHostSlot> current_active =
            state_->active.load(std::memory_order_acquire);
        if (!transaction_status || state_->candidate != candidate || current_active != active ||
            active->state != RuntimeSlotState::Quiescing) {
            return {.status = transaction_status
                                  ? failure(RuntimeHostError::InvalidCandidateState,
                                            "replacement transaction changed during cancellation")
                                  : transaction_status,
                    .capability = {}};
        }
        if (!status) {
            return {.status = status, .capability = {}};
        }
    }
    if (!active->cancellation_acknowledged) {
        return {.status = failure(RuntimeHostError::CancellationPending,
                                  "replacement source cancellation is not acknowledged"),
                .capability = {}};
    }
    if (active->owner_registry == nullptr || candidate->owner_registry == nullptr) {
        restore_source_after_failed_quiescence();
        return {.status = failure(RuntimeHostError::InvalidCommitProof,
                                  "replacement source or candidate has no typed owner registry"),
                .capability = {}};
    }
    if (!no_truth_leases(*active)) {
        restore_source_after_failed_quiescence();
        return {.status = failure(RuntimeHostError::TruthLeasesOutstanding,
                                  "truth-mutating leases must settle before state export"),
                .capability = {}};
    }
    if (active->final_transfer_fence_sequence == 0) {
        if (!increment_nonzero(state_->last_transfer_fence_sequence)) {
            restore_source_after_failed_quiescence();
            return {.status = failure(RuntimeHostError::TicketExhausted,
                                      "host mutation fence sequence exhausted"),
                    .capability = {}};
        }
        active->final_transfer_fence_sequence = state_->last_transfer_fence_sequence;
    }
    try {
        auto capability = RuntimeHostQuiescenceCapability::mint_for_host(
            active->incarnation, active->plan.plan_sha256, candidate->plan.plan_sha256,
            active->resource_identity, candidate->resource_identity, active->owner_registry,
            candidate->owner_registry, state_->host_instance_nonce,
            [weak_state = std::weak_ptr<RuntimeHostSharedState>(state_), active,
             candidate]() noexcept {
                const auto state = weak_state.lock();
                if (state == nullptr) {
                    return false;
                }
                std::lock_guard<std::mutex> lock(state->mutex);
                return state->host_state == RuntimeHostState::Active &&
                       state->active.load(std::memory_order_acquire) == active &&
                       state->candidate == candidate &&
                       active->state == RuntimeSlotState::Quiescing && !active->admission_open &&
                       active->cancellation_acknowledged &&
                       active->final_transfer_fence_sequence != 0 &&
                       active->truth_mutating_leases == 0 &&
                       state->native_episode_submissions_in_flight == 0;
            },
            [weak_state = std::weak_ptr<RuntimeHostSharedState>(state_), active,
             candidate]() noexcept {
                const auto state = weak_state.lock();
                if (state == nullptr) {
                    return;
                }
                active->quiescence_capability_live.store(false, std::memory_order_release);
                std::unique_lock<std::mutex> lock(state->mutex, std::try_to_lock);
                // Host abort/CAS-failure paths restore the source
                // explicitly while already holding this mutex.  Do
                // not deadlock if the transfer destructor is running
                // from one of those paths.
                if (!lock.owns_lock()) {
                    std::lock_guard<std::mutex> pending_lock(state->pending_rollback_mutex);
                    state->pending_rollback_active = active;
                    state->pending_rollback_candidate = candidate;
                    return;
                }
                if (state->host_state == RuntimeHostState::Active &&
                    state->active.load(std::memory_order_acquire) == active &&
                    state->candidate == candidate && active->state == RuntimeSlotState::Quiescing &&
                    !active->admission_open && active->truth_mutating_leases == 0 &&
                    state->state_transfers_in_flight.load(std::memory_order_acquire) == 0 &&
                    state->native_episode_submissions_in_flight == 0) {
                    active->state = RuntimeSlotState::Active;
                    active->admission_open = true;
                    active->result_publication_open = true;
                    active->final_transfer_fence_sequence = 0;
                } else if (state->host_state == RuntimeHostState::Active &&
                           state->active.load(std::memory_order_acquire) == active &&
                           state->candidate == candidate &&
                           active->state == RuntimeSlotState::Quiescing) {
                    // A transfer or native callback may still own the
                    // quiescence reservation. Keep rollback durable
                    // until its matching end callback drains.
                    std::lock_guard<std::mutex> pending_lock(state->pending_rollback_mutex);
                    state->pending_rollback_active = active;
                    state->pending_rollback_candidate = candidate;
                }
            },
            [weak_state = std::weak_ptr<RuntimeHostSharedState>(state_), candidate]() noexcept {
                const auto state = weak_state.lock();
                if (state == nullptr) {
                    return false;
                }
                {
                    std::lock_guard<std::mutex> lock(state->mutex);
                    const auto active = state->active.load(std::memory_order_acquire);
                    if (state->host_state != RuntimeHostState::Active || active == nullptr ||
                        active->state != RuntimeSlotState::Quiescing || active->admission_open ||
                        state->candidate != candidate || active->truth_mutating_leases != 0 ||
                        state->native_episode_submissions_in_flight != 0) {
                        return false;
                    }
                    auto count = state->state_transfers_in_flight.load(std::memory_order_acquire);
                    while (count != std::numeric_limits<std::size_t>::max() &&
                           !state->state_transfers_in_flight.compare_exchange_weak(
                               count, count + 1, std::memory_order_acq_rel,
                               std::memory_order_acquire)) {
                    }
                    if (count == std::numeric_limits<std::size_t>::max()) {
                        return false;
                    }
                }
                bool fenced = false;
                try {
                    fenced =
                        candidate->control != nullptr && candidate->control->begin_state_transfer();
                } catch (...) {
                    fenced = false;
                }
                if (!fenced) {
                    auto count = state->state_transfers_in_flight.load(std::memory_order_acquire);
                    while (count != 0 && !state->state_transfers_in_flight.compare_exchange_weak(
                                             count, count - 1, std::memory_order_acq_rel,
                                             std::memory_order_acquire)) {
                    }
                }
                return fenced;
            },
            [weak_state = std::weak_ptr<RuntimeHostSharedState>(state_), active,
             candidate]() noexcept {
                const auto state = weak_state.lock();
                if (state == nullptr) {
                    return false;
                }
                std::lock_guard<std::mutex> lock(state->mutex);
                return state->host_state == RuntimeHostState::Active &&
                       state->active.load(std::memory_order_acquire) == active &&
                       state->candidate == candidate &&
                       active->state == RuntimeSlotState::Quiescing &&
                       state->state_transfers_in_flight.load(std::memory_order_acquire) != 0;
            },
            [weak_state = std::weak_ptr<RuntimeHostSharedState>(state_), active,
             candidate]() noexcept {
                const auto state = weak_state.lock();
                if (state == nullptr) {
                    return;
                }
                try {
                    if (candidate->control != nullptr) {
                        candidate->control->end_state_transfer();
                    }
                } catch (...) {
                }
                active->quiescence_capability_live.store(false, std::memory_order_release);
                std::size_t count =
                    state->state_transfers_in_flight.load(std::memory_order_acquire);
                while (count != 0 && !state->state_transfers_in_flight.compare_exchange_weak(
                                         count, count - 1, std::memory_order_acq_rel,
                                         std::memory_order_acquire)) {
                }
                // The transfer destructor may have queued source
                // rollback while this reservation was still counted.
                // Revisit that queue immediately after the matching
                // end callback so failed preparation does not strand
                // the active slot in Quiescing.
                std::unique_lock<std::mutex> rollback_lock(state->mutex, std::try_to_lock);
                if (rollback_lock.owns_lock()) {
                    apply_pending_quiescence_rollback(*state);
                }
            },
            handle.lifecycle_ticket, handle.candidate_sequence,
            active->final_transfer_fence_sequence, active->read_only_result_leases,
            active->cancellation_acknowledged);
        active->quiescence_capability_live.store(true, std::memory_order_release);
        return {.status = success(), .capability = std::move(capability)};
    } catch (...) {
        restore_source_after_failed_quiescence();
        return {.status = failure(RuntimeHostError::InvalidCommitProof,
                                  "host quiescence capability allocation failed"),
                .capability = {}};
    }
}

RuntimeHostStatus
RuntimeHostCandidate::prepare_checkpoint_recovery(const RuntimeCandidateHandle &handle,
                                                  const RuntimeRecoveryCommitProof &proof) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return status;
    }
    if (state_->candidate->transaction_kind != RuntimeHostTransactionKind::CheckpointRecovery) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "candidate is not a checkpoint-recovery transaction");
    }
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (active == nullptr || !same_slot(proof.source_faulted_slot, active->incarnation)) {
        return failure(RuntimeHostError::StaleExpectedSlot,
                       "recovery proof source is not the active faulted slot");
    }
    if (active->state != RuntimeSlotState::ActiveFaulted &&
        active->state != RuntimeSlotState::RecoveryQuiesced) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "recovery source is not faulted or recovery-quiesced");
    }
    if (proof.checkpoint_id.empty() || !is_lower_hex_sha256(proof.checkpoint_sha256) ||
        !proof.checkpoint_admitted || proof.source_truth_exported ||
        !proof.candidate_import_probe_passed || proof.production_authorized) {
        return failure(RuntimeHostError::InvalidCommitProof,
                       "recovery requires an admitted checkpoint and no faulted-truth export");
    }
    const std::shared_ptr<RuntimeHostSlot> candidate = state_->candidate;
    if (candidate->state == RuntimeSlotState::Ready &&
        active->state == RuntimeSlotState::ActiveFaulted) {
        active->admission_open = false;
        active->state = RuntimeSlotState::RecoveryQuiesced;
        const RuntimeHostStatus cancellation = cancel_slot(*state_, lock, active);
        const RuntimeHostStatus transaction_status = validate_candidate_handle(*state_, handle);
        const std::shared_ptr<RuntimeHostSlot> current_active =
            state_->active.load(std::memory_order_acquire);
        if (!transaction_status || state_->candidate != candidate || current_active != active ||
            active->state != RuntimeSlotState::RecoveryQuiesced) {
            return transaction_status ? failure(RuntimeHostError::InvalidCandidateState,
                                                "recovery transaction changed during cancellation")
                                      : transaction_status;
        }
        if (!cancellation) {
            return cancellation;
        }
    } else if (candidate->state != RuntimeSlotState::Ready &&
               candidate->state != RuntimeSlotState::RecoveryCommitReady) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "recovery candidate is not ready or recovery-quiesced");
    }
    if (!active->cancellation_acknowledged) {
        const RuntimeHostStatus cancellation = cancel_slot(*state_, lock, active);
        const RuntimeHostStatus transaction_status = validate_candidate_handle(*state_, handle);
        const std::shared_ptr<RuntimeHostSlot> current_active =
            state_->active.load(std::memory_order_acquire);
        if (!transaction_status || state_->candidate != candidate || current_active != active ||
            active->state != RuntimeSlotState::RecoveryQuiesced) {
            return transaction_status ? failure(RuntimeHostError::InvalidCandidateState,
                                                "recovery transaction changed during cancellation")
                                      : transaction_status;
        }
        if (!cancellation) {
            return cancellation;
        }
    }
    if (!no_truth_leases(*active)) {
        return failure(RuntimeHostError::TruthLeasesOutstanding,
                       "faulted truth-mutating leases must settle before recovery");
    }
    candidate->opaque_transfer_sha256 = proof.checkpoint_sha256;
    candidate->drain_deadline_tick = proof.drain_deadline_tick;
    candidate->state = RuntimeSlotState::RecoveryCommitReady;
    return success();
}

RuntimePublicationResult
RuntimeHostCandidate::commit_prepared_candidate(const RuntimeCandidateHandle &handle,
                                                std::uint64_t now_tick) {
    const RuntimeSlotCasOperation operation =
        handle.transaction_kind == RuntimeHostTransactionKind::Replacement
            ? RuntimeSlotCasOperation::ReplacementPublish
            : RuntimeSlotCasOperation::RecoveryPublish;
    const bool injected_loss = invoke_cas_fault_injector(state_, operation);
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return {.status = status, .published_slot = {}};
    }
    const std::shared_ptr<RuntimeHostSlot> candidate = state_->candidate;
    const std::shared_ptr<RuntimeHostSlot> old = state_->active.load(std::memory_order_acquire);
    const bool replacement = candidate->transaction_kind == RuntimeHostTransactionKind::Replacement;
    const RuntimeSlotState expected_candidate_state =
        replacement ? RuntimeSlotState::TransferCommitReady : RuntimeSlotState::RecoveryCommitReady;
    const RuntimeSlotState expected_old_state =
        replacement ? RuntimeSlotState::Quiescing : RuntimeSlotState::RecoveryQuiesced;
    if (candidate->state != expected_candidate_state || old == nullptr ||
        old->state != expected_old_state || !no_truth_leases(*old)) {
        return {.status = failure(RuntimeHostError::InvalidCandidateState,
                                  "prepared publication state is incomplete"),
                .published_slot = {}};
    }
    if (candidate->drain_deadline_tick != 0 && now_tick >= candidate->drain_deadline_tick) {
        return {.status = failure(RuntimeHostError::LifecycleDeadlineExpired,
                                  "prepared publication deadline has expired"),
                .published_slot = {}};
    }
    if (old->incarnation.incarnation_epoch == std::numeric_limits<std::uint64_t>::max()) {
        return {.status =
                    failure(RuntimeHostError::EpochExhausted, "host incarnation epoch exhausted"),
                .published_slot = {}};
    }
    candidate->incarnation = {
        .host = state_->identity,
        .incarnation_epoch = old->incarnation.incarnation_epoch + 1,
    };
    const std::optional<RuntimeEpisodeCoordinatorSnapshot> transferred_snapshot =
        replacement ? std::optional<RuntimeEpisodeCoordinatorSnapshot>(
                          candidate->validated_transfer.source_barrier_snapshot())
                    : std::nullopt;
    auto coordinators = build_world_coordinators(*candidate, transferred_snapshot);
    auto authority = build_world_authority(*candidate, transferred_snapshot);
    if (!coordinators.has_value() || !authority.has_value()) {
        candidate->state = RuntimeSlotState::CandidateFailed;
        abandon_transfer_outside_host_mutex(lock, candidate);
        old->state = RuntimeSlotState::Active;
        old->admission_open = true;
        old->result_publication_open = true;
        old->final_transfer_fence_sequence = 0;
        state_->host_state = RuntimeHostState::Active;
        const RuntimeHostStatus build_failure =
            failure(RuntimeHostError::InvalidCommitProof,
                    "candidate native world authority could not be constructed");
        return {.status = fail_candidate(*state_, lock, build_failure), .published_slot = {}};
    }
    candidate->state = RuntimeSlotState::Publishing;
    candidate->rollback_target = old;
    candidate->admission_open = true;
    candidate->result_publication_open = true;
    std::shared_ptr<RuntimeHostSlot> expected = old;
    const RuntimeHostStatus publication =
        compare_exchange_active(*state_, expected, candidate, injected_loss);
    if (!publication) {
        candidate->state = RuntimeSlotState::CandidateFailed;
        abandon_transfer_outside_host_mutex(lock, candidate);
        if (replacement) {
            old->state = RuntimeSlotState::Active;
            old->admission_open = true;
            old->result_publication_open = true;
            old->final_transfer_fence_sequence = 0;
            old->quiescence_capability_live.store(false, std::memory_order_release);
            state_->host_state = RuntimeHostState::Active;
        } else {
            old->state = RuntimeSlotState::ActiveFaulted;
            old->admission_open = false;
            old->result_publication_open = false;
            state_->host_state = RuntimeHostState::Faulted;
        }
        const RuntimeHostStatus failure_status = publication;
        return {.status = fail_candidate(*state_, lock, failure_status), .published_slot = {}};
    }

    // Keep an exact copy of the pre-publication authority so an owner
    // transaction that later resolves Aborted can roll back the pointer CAS
    // and the host routing tables as one operation.
    const auto previous_authority = state_->world_authority;
    const auto previous_coordinators = state_->world_coordinators;
    state_->world_authority.swap(*authority);
    state_->world_coordinators.swap(*coordinators);
    if (replacement) {
        // Keep the newly published pointer in Publishing while the owner
        // transaction commits outside the host mutex.  Lifecycle callers are
        // rejected for this state, so no shutdown/fault path can reclaim the
        // target while its provisional import is being made durable.
        candidate->state = RuntimeSlotState::Publishing;
        lock.unlock();
        RuntimeStateTransferStatus committed =
            candidate->validated_transfer.commit_for_host(now_tick, candidate->drain_deadline_tick);
        lock.lock();
        if (!committed) {
            // The owner transaction may have crossed the process boundary
            // while commit_for_host was returning an ambiguous status.  Ask
            // the durable owner to classify that outcome before quarantining
            // anything.  This is the only safe way to distinguish an
            // already-committed target from an abortable provisional import.
            lock.unlock();
            const RuntimeStateTransferStatus recovered =
                candidate->validated_transfer.recover_for_host(now_tick,
                                                               candidate->drain_deadline_tick);
            lock.lock();
            if (recovered && candidate->validated_transfer.committed() &&
                state_->active.load(std::memory_order_acquire) == candidate &&
                state_->host_state == RuntimeHostState::Active) {
                committed = RuntimeStateTransferStatus{};
            } else if (candidate->validated_transfer.aborted()) {
                std::shared_ptr<RuntimeHostSlot> expected_candidate = candidate;
                const RuntimeHostStatus unpublished =
                    compare_exchange_active(*state_, expected_candidate, old, false);
                if (unpublished) {
                    state_->world_authority = previous_authority;
                    state_->world_coordinators = previous_coordinators;
                    candidate->state = RuntimeSlotState::CandidateFailed;
                    candidate->admission_open = false;
                    candidate->result_publication_open = false;
                    old->state = RuntimeSlotState::Active;
                    old->admission_open = true;
                    old->result_publication_open = true;
                    old->final_transfer_fence_sequence = 0;
                    old->quiescence_capability_live.store(false, std::memory_order_release);
                    state_->host_state = RuntimeHostState::Active;
                    const RuntimeHostStatus import_failure =
                        failure(RuntimeHostError::InvalidCommitProof,
                                committed.detail.empty() ? "owner import recovered as aborted"
                                                         : committed.detail);
                    lock.unlock();
                    candidate->validated_transfer.release_host_transfer_fence();
                    lock.lock();
                    return {.status = fail_candidate(*state_, lock, import_failure),
                            .published_slot = {}};
                }
            }
            if (!committed) {
                // Recovery could not prove either outcome.  Unpublish the
                // candidate, restore the old authority, and retain both slots
                // with an explicit rollback link for retry_quarantined_reclamation().
                std::shared_ptr<RuntimeHostSlot> expected_candidate = candidate;
                const RuntimeHostStatus unpublished =
                    compare_exchange_active(*state_, expected_candidate, {}, false);
                if (unpublished) {
                    state_->rollback_world_authority = previous_authority;
                    state_->rollback_world_coordinators = previous_coordinators;
                    candidate->state = RuntimeSlotState::Quarantined;
                    candidate->owner_publication_recovery_pending = true;
                    candidate->admission_open = false;
                    candidate->result_publication_open = false;
                    retain_quarantine(*state_, candidate);
                    state_->candidate.reset();
                    old->state = RuntimeSlotState::Quarantined;
                    old->admission_open = false;
                    old->result_publication_open = false;
                    retain_quarantine(*state_, old);
                } else {
                    // A second CAS race is itself fail-closed: the candidate
                    // is no longer eligible for admission, but it remains
                    // retained so a later explicit recovery/reclamation pass
                    // cannot lose the owner transaction.
                    candidate->state = RuntimeSlotState::Quarantined;
                    candidate->owner_publication_recovery_pending = true;
                    candidate->admission_open = false;
                    candidate->result_publication_open = false;
                    retain_quarantine(*state_, candidate);
                    state_->candidate.reset();
                }
                state_->host_state = RuntimeHostState::FailStopped;
                return {.status =
                            failure(RuntimeHostError::QuarantineUnresolved,
                                    recovered.detail.empty() ? committed.detail : recovered.detail),
                        .published_slot = {}};
            }
        }
        if (state_->active.load(std::memory_order_acquire) != candidate ||
            state_->host_state != RuntimeHostState::Active) {
            state_->host_state = RuntimeHostState::FailStopped;
            return {.status = failure(RuntimeHostError::QuarantineUnresolved,
                                      "host authority changed during target import commit"),
                    .published_slot = {}};
        }
    }
    candidate->state = RuntimeSlotState::Active;
    old->state = RuntimeSlotState::Draining;
    old->admission_open = false;
    old->result_publication_open = replacement;
    old->drain_deadline_tick = candidate->drain_deadline_tick;
    state_->draining = old;
    state_->candidate.reset();
    state_->host_state = RuntimeHostState::Active;
    const auto publication_ticket = state_->last_publication_ticket;
    // Owner commit keeps the target fence live until routing, slot state and
    // the source draining transition are all finalized. Never call owner
    // control code while holding the host mutex.
    lock.unlock();
    candidate->validated_transfer.release_host_transfer_fence();
    return {.status = success(),
            .published_slot = candidate->incarnation,
            .publication_ticket = publication_ticket};
}

RuntimeHostStatus RuntimeHostCandidate::abort_candidate(const RuntimeCandidateHandle &handle) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    RuntimeHostStatus status = validate_candidate_handle(*state_, handle);
    if (!status) {
        return status;
    }
    std::shared_ptr<RuntimeHostSlot> candidate = state_->candidate;
    if (candidate->state == RuntimeSlotState::Publishing) {
        return failure(RuntimeHostError::CandidateBusy,
                       "candidate target import publication is already in progress");
    }
    if (state_->state_transfers_in_flight.load(std::memory_order_acquire) != 0 &&
        !candidate->validated_transfer.valid()) {
        return failure(RuntimeHostError::CandidateBusy,
                       "candidate owner state transfer is still in flight");
    }
    candidate->state = RuntimeSlotState::CandidateFailed;
    abandon_transfer_outside_host_mutex(lock, candidate);
    if (candidate->state == RuntimeSlotState::Reclaiming) {
        return failure(RuntimeHostError::InvalidCandidateState,
                       "candidate resource reclamation is already in progress");
    }
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    const bool replacement = candidate->transaction_kind == RuntimeHostTransactionKind::Replacement;
    const bool recovery =
        candidate->transaction_kind == RuntimeHostTransactionKind::CheckpointRecovery;
    candidate->admission_open = false;
    candidate->result_publication_open = false;
    if (replacement && active != nullptr &&
        (active->state == RuntimeSlotState::Quiescing ||
         active->state == RuntimeSlotState::TransferCommitReady)) {
        active->state = RuntimeSlotState::Active;
        active->admission_open = true;
        active->result_publication_open = true;
        active->final_transfer_fence_sequence = 0;
        active->quiescence_capability_live.store(false, std::memory_order_release);
    }
    if (recovery && active != nullptr && active->state == RuntimeSlotState::RecoveryQuiesced) {
        // Aborting recovery must leave the faulted source retryable. It must
        // never silently turn a failed recovery attempt into a terminal host.
        active->state = RuntimeSlotState::ActiveFaulted;
        active->admission_open = false;
        active->result_publication_open = false;
    }
    const RuntimeHostStatus reason = success();
    const RuntimeHostStatus result = fail_candidate(*state_, lock, reason);
    // Do not release the last candidate owner under the host mutex.  The
    // owner registry/control may have callback-capable destruction paths.
    lock.unlock();
    candidate.reset();
    lock.lock();
    return result;
}

RuntimeHostStatus
RuntimeHostCandidate::mark_active_faulted(const RuntimeIncarnationRef &expected_slot,
                                          std::uint64_t fault_deadline_tick) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (state_->host_state != RuntimeHostState::Active || active == nullptr ||
        active->state != RuntimeSlotState::Active) {
        return failure(RuntimeHostError::HostStateMismatch,
                       "only an active slot can enter active_faulted");
    }
    RuntimeHostStatus status = validate_expected_slot(*state_, expected_slot, *active);
    if (!status) {
        return status;
    }
    if (state_->native_episode_submissions_in_flight != 0 ||
        state_->state_transfers_in_flight.load(std::memory_order_acquire) != 0) {
        return failure(RuntimeHostError::CandidateBusy,
                       "fault transition cannot race native episode or state-transfer work");
    }
    if (fault_deadline_tick == 0) {
        return failure(RuntimeHostError::InvalidArgument,
                       "fault transition requires a terminal deadline");
    }
    active->admission_open = false;
    active->result_publication_open = false;
    active->state = RuntimeSlotState::ActiveFaulted;
    active->drain_deadline_tick = fault_deadline_tick;
    state_->host_state = RuntimeHostState::Faulted;
    return cancel_slot(*state_, lock, active);
}

RuntimeShadowEpisodeAdmission
RuntimeHostCandidate::admit_shadow_episode(RuntimeNativeEpisodeCapability &&native_episode) {
    const RuntimeEpisodeRef episode = native_episode.episode();
    std::unique_lock<std::mutex> lock(state_->mutex);
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (state_->host_state != RuntimeHostState::Active || active == nullptr ||
        active->state != RuntimeSlotState::Active || !active->admission_open) {
        return {.status = failure(RuntimeHostError::AdmissionClosed,
                                  "host has no active shadow episode boundary"),
                .capability = {}};
    }
    if (!episode.well_formed() || !same_slot(episode.world.incarnation, active->incarnation)) {
        return {.status = failure(RuntimeHostError::StaleReference,
                                  "episode is stale or belongs to another slot"),
                .capability = {}};
    }
    const auto authority = state_->world_authority.find(episode.world.world_slot);
    const auto coordinator = state_->world_coordinators.find(episode.world.world_slot);
    if (authority == state_->world_authority.end() ||
        coordinator == state_->world_coordinators.end() || episode.world.world_generation == 0 ||
        authority->second.world_generation != episode.world.world_generation ||
        native_episode.coordinator_nonce() != coordinator->second->coordinator_nonce()) {
        return {.status = failure(RuntimeHostError::StaleReference,
                                  "episode world is not in the active slot authority table"),
                .capability = {}};
    }
    const RuntimeIncarnationRef expected_source = active->incarnation;
    lock.unlock();
    const RuntimeStateTransferStatus native_status =
        native_episode.consume_for_host(expected_source);
    lock.lock();
    const std::shared_ptr<RuntimeHostSlot> current = state_->active.load(std::memory_order_acquire);
    if (!native_status || current != active || state_->host_state != RuntimeHostState::Active ||
        active->state != RuntimeSlotState::Active || !active->admission_open) {
        return {.status = failure(RuntimeHostError::StaleReference,
                                  native_status ? "host changed while admitting native episode"
                                                : native_status.detail),
                .capability = {}};
    }
    auto authority_after = state_->world_authority.find(episode.world.world_slot);
    if (authority_after == state_->world_authority.end()) {
        return {.status = failure(RuntimeHostError::StaleReference,
                                  "world authority was retired during admission"),
                .capability = {}};
    }
    // A concurrent reset may have advanced the same authority while the host
    // mutex was released for native capability consumption.  Authority is a
    // monotonic high-water mark: an older admission can never regress it.
    if (episode.world.world_generation >= authority_after->second.world_generation) {
        authority_after->second.world_generation = episode.world.world_generation;
        authority_after->second.coordinator_nonce = native_episode.coordinator_nonce();
    }
    if (state_->admitted_shadow_episodes.size() >= kMaxAdmittedShadowEpisodes) {
        return {.status = failure(RuntimeHostError::AdmissionClosed,
                                  "P4-A shadow episode capability budget is exhausted"),
                .capability = {}};
    }
    if (!increment_nonzero(state_->last_episode_capability_sequence)) {
        return {.status = failure(RuntimeHostError::TicketExhausted,
                                  "episode capability sequence exhausted"),
                .capability = {}};
    }
    const std::uint64_t sequence = state_->last_episode_capability_sequence;
    state_->admitted_shadow_episodes.emplace(
        sequence, RuntimeAdmittedShadowEpisode{.episode = episode,
                                               .native_episode = std::move(native_episode)});
    RuntimeShadowEpisodeCapability capability;
    capability.host_ = state_->identity;
    capability.host_instance_nonce_ = state_->host_instance_nonce;
    capability.resource_identity_ = active->resource_identity;
    capability.episode_ = episode;
    capability.capability_sequence_ = sequence;
    return {.status = success(), .capability = capability};
}

RuntimeShadowEpisodeAdmission RuntimeHostCandidate::issue_shadow_episode(std::uint64_t world_slot) {
    std::shared_ptr<RuntimeEpisodeCoordinatorCandidate> coordinator;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        const auto active = state_->active.load(std::memory_order_acquire);
        if (state_->host_state != RuntimeHostState::Active || active == nullptr ||
            active->state != RuntimeSlotState::Active || !active->admission_open) {
            return {.status = failure(RuntimeHostError::AdmissionClosed,
                                      "host has no active shadow episode boundary"),
                    .capability = {}};
        }
        const auto iterator = state_->world_coordinators.find(world_slot);
        if (iterator == state_->world_coordinators.end()) {
            return {.status = failure(RuntimeHostError::StaleReference,
                                      "world slot is not owned by the active slot"),
                    .capability = {}};
        }
        coordinator = iterator->second;
    }
    auto native = coordinator->issue_episode_capability();
    if (!native.status) {
        return {.status = failure(RuntimeHostError::StaleReference, native.status.detail),
                .capability = {}};
    }
    return admit_shadow_episode(std::move(native.capability));
}

RuntimeHostStatus
RuntimeHostCandidate::release_shadow_episode(const RuntimeShadowEpisodeCapability &capability) {
    std::lock_guard<std::mutex> lock(state_->mutex);
    if (!capability.valid() || !same_host(capability.host_, state_->identity) ||
        capability.host_instance_nonce_ != state_->host_instance_nonce) {
        return failure(RuntimeHostError::StaleReference,
                       "shadow episode capability is stale or belongs to another host");
    }
    const auto iterator = state_->admitted_shadow_episodes.find(capability.capability_sequence_);
    if (iterator == state_->admitted_shadow_episodes.end() ||
        iterator->second.episode != capability.episode_) {
        return failure(RuntimeHostError::StaleReference,
                       "shadow episode capability was already released");
    }
    state_->admitted_shadow_episodes.erase(iterator);
    return success();
}

RuntimeEpisodeTransitionResult RuntimeHostCandidate::submit_shadow_episode(
    const RuntimeShadowEpisodeCapability &episode_capability,
    const RuntimeEpisodeTransitionIntent &intent) {
    const std::shared_ptr<RuntimeHostSharedState> state = state_;
    if (state == nullptr) {
        return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                           .detail = "host state is unavailable"}};
    }
    std::shared_ptr<RuntimeEpisodeCoordinatorCandidate> coordinator;
    std::shared_ptr<RuntimeNativeEpisodeControl> native_episode_control;
    {
        std::lock_guard<std::mutex> lock(state->mutex);
        const auto active = state->active.load(std::memory_order_acquire);
        if (active == nullptr || state->host_state != RuntimeHostState::Active ||
            !active->admission_open || !episode_capability.valid() ||
            !same_host(episode_capability.host_, state->identity) ||
            episode_capability.host_instance_nonce_ != state->host_instance_nonce ||
            intent.expected_episode != episode_capability.episode_) {
            return {
                .status = {.error = RuntimeStateTransferError::StaleIntent,
                           .detail =
                               "episode submission is not bound to an admitted host capability"}};
        }
        const auto admitted =
            state->admitted_shadow_episodes.find(episode_capability.capability_sequence_);
        if (admitted == state->admitted_shadow_episodes.end() ||
            admitted->second.episode != episode_capability.episode_) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "episode capability is not admitted by this host"}};
        }
        if (active == nullptr || state->host_state != RuntimeHostState::Active ||
            !active->admission_open || !intent.expected_episode.well_formed() ||
            !same_slot(intent.expected_episode.world.incarnation, active->incarnation)) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "episode intent is not bound to the active host slot"}};
        }
        const auto iterator =
            state->world_coordinators.find(intent.expected_episode.world.world_slot);
        if (iterator == state->world_coordinators.end()) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "episode world slot has no host-owned coordinator"}};
        }
        coordinator = iterator->second;
        native_episode_control = active->native_episode_control;
        if (native_episode_control == nullptr) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "active slot has no host-bound native episode control"}};
        }
        ++state->native_episode_submissions_in_flight;
    }
    RuntimeEpisodeTransitionResult result;
    try {
        result = coordinator->submit(intent, *native_episode_control);
    } catch (...) {
        result.status = {.error = RuntimeStateTransferError::NativeMutationFailed,
                         .detail = "native episode submission raised unexpectedly"};
    }
    if (!result.status) {
        std::lock_guard<std::mutex> lock(state->mutex);
        --state->native_episode_submissions_in_flight;
        return result;
    }
    std::lock_guard<std::mutex> lock(state->mutex);
    --state->native_episode_submissions_in_flight;
    const auto active = state->active.load(std::memory_order_acquire);
    const auto authority =
        state->world_authority.find(result.receipt.episode_after.world.world_slot);
    const auto current_coordinator =
        state->world_coordinators.find(result.receipt.episode_after.world.world_slot);
    if (active == nullptr || active->state != RuntimeSlotState::Active ||
        state->host_state != RuntimeHostState::Active ||
        current_coordinator == state->world_coordinators.end() ||
        authority == state->world_authority.end() ||
        !same_slot(result.receipt.episode_after.world.incarnation, active->incarnation) ||
        current_coordinator->second != coordinator || !result.receipt.episode_after.well_formed()) {
        return {.status = {.error = RuntimeStateTransferError::ConcurrentMutation,
                           .detail = "host authority changed while recording the native receipt"},
                .receipt = result.receipt,
                .replayed = result.replayed};
    }
    if (result.receipt.episode_after.world.world_generation >= authority->second.world_generation) {
        authority->second.world_generation = result.receipt.episode_after.world.world_generation;
        authority->second.coordinator_nonce = coordinator->coordinator_nonce();
    }
    return result;
}

RuntimeEpisodeBarrierAdmission
RuntimeHostCandidate::open_shadow_replacement_barrier(const RuntimeEpisodeRef &expected_episode,
                                                      std::uint64_t expected_step_sequence) {
    std::shared_ptr<RuntimeEpisodeCoordinatorCandidate> coordinator;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        const auto active = state_->active.load(std::memory_order_acquire);
        if (active == nullptr || state_->host_state != RuntimeHostState::Active ||
            active->state != RuntimeSlotState::Quiescing || active->admission_open ||
            !active->cancellation_acknowledged || active->final_transfer_fence_sequence == 0 ||
            !no_truth_leases(*active) || !expected_episode.well_formed() ||
            !same_slot(expected_episode.world.incarnation, active->incarnation)) {
            return {
                .status = {.error = RuntimeStateTransferError::StaleIntent,
                           .detail = "replacement barrier requires a host-quiesced active slot"}};
        }
        const auto iterator = state_->world_coordinators.find(expected_episode.world.world_slot);
        if (iterator == state_->world_coordinators.end()) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "episode world slot has no host-owned coordinator"}};
        }
        coordinator = iterator->second;
    }
    auto barrier = coordinator->open_replacement_barrier(expected_episode, expected_step_sequence);
    if (!barrier.status) {
        return barrier;
    }
    const RuntimeStateTransferStatus binding = barrier.capability.bind_for_host(
        state_->host_instance_nonce, expected_episode.world.world_slot);
    if (!binding) {
        (void)coordinator->abort_replacement_barrier(std::move(barrier.capability));
        return {.status = binding, .capability = {}};
    }
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        const auto active = state_->active.load(std::memory_order_acquire);
        const auto current = state_->world_coordinators.find(expected_episode.world.world_slot);
        if (active == nullptr || state_->host_state != RuntimeHostState::Active ||
            active->state != RuntimeSlotState::Quiescing || active->admission_open ||
            !active->cancellation_acknowledged || active->final_transfer_fence_sequence == 0 ||
            !no_truth_leases(*active) || current == state_->world_coordinators.end() ||
            current->second != coordinator) {
            (void)coordinator->abort_replacement_barrier(std::move(barrier.capability));
            return {
                .status = {.error = RuntimeStateTransferError::StaleIntent,
                           .detail = "host authority changed while opening the episode barrier"},
                .capability = {}};
        }
    }
    return barrier;
}

RuntimeEpisodeBarrierAdmission
RuntimeHostCandidate::open_shadow_replacement_barrier(std::uint64_t world_slot) {
    std::shared_ptr<RuntimeEpisodeCoordinatorCandidate> coordinator;
    RuntimeEpisodeCoordinatorSnapshot current;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        const auto active = state_->active.load(std::memory_order_acquire);
        if (active == nullptr || state_->host_state != RuntimeHostState::Active ||
            active->state != RuntimeSlotState::Quiescing || active->admission_open ||
            !active->cancellation_acknowledged || active->final_transfer_fence_sequence == 0 ||
            !no_truth_leases(*active)) {
            return {.status = {.error = RuntimeStateTransferError::BarrierRequired,
                               .detail =
                                   "host must quiesce the active slot before opening its barrier"}};
        }
        const auto iterator = state_->world_coordinators.find(world_slot);
        if (iterator == state_->world_coordinators.end()) {
            return {.status = {.error = RuntimeStateTransferError::StaleIntent,
                               .detail = "episode world slot has no host-owned coordinator"}};
        }
        coordinator = iterator->second;
        current = coordinator->snapshot();
    }
    auto barrier = coordinator->open_replacement_barrier(current.episode, current.step_sequence);
    if (!barrier.status) {
        return barrier;
    }
    const RuntimeStateTransferStatus binding =
        barrier.capability.bind_for_host(state_->host_instance_nonce, world_slot);
    if (!binding) {
        (void)coordinator->abort_replacement_barrier(std::move(barrier.capability));
        return {.status = binding, .capability = {}};
    }
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        const auto active = state_->active.load(std::memory_order_acquire);
        const auto current_coordinator = state_->world_coordinators.find(world_slot);
        if (active == nullptr || state_->host_state != RuntimeHostState::Active ||
            active->state != RuntimeSlotState::Quiescing || active->admission_open ||
            !active->cancellation_acknowledged || !no_truth_leases(*active) ||
            current_coordinator == state_->world_coordinators.end() ||
            current_coordinator->second != coordinator) {
            (void)coordinator->abort_replacement_barrier(std::move(barrier.capability));
            return {
                .status = {.error = RuntimeStateTransferError::StaleIntent,
                           .detail = "host authority changed while opening the episode barrier"},
                .capability = {}};
        }
    }
    return barrier;
}

RuntimeLeaseAdmission
RuntimeHostCandidate::acquire_lease(const RuntimeShadowEpisodeCapability &episode,
                                    RuntimeLeaseKind kind) {
    std::unique_lock<std::mutex> lock(state_->mutex);
    if (!supported_lease_kind(kind)) {
        return {.status = failure(RuntimeHostError::InvalidArgument, "lease kind is unsupported"),
                .lease = {},
                .request_ref = {}};
    }
    const std::shared_ptr<RuntimeHostSlot> active = state_->active.load(std::memory_order_acquire);
    if (state_->host_state != RuntimeHostState::Active || active == nullptr ||
        active->state != RuntimeSlotState::Active) {
        return {.status =
                    failure(RuntimeHostError::AdmissionClosed, "host has no active admitting slot"),
                .lease = {},
                .request_ref = {}};
    }
    if (!active->admission_open) {
        return {.status =
                    failure(RuntimeHostError::AdmissionClosed, "active slot admission is closed"),
                .lease = {},
                .request_ref = {}};
    }
    const auto admitted = state_->admitted_shadow_episodes.find(episode.capability_sequence_);
    if (!episode.valid() || !same_host(episode.host_, state_->identity) ||
        episode.host_instance_nonce_ != state_->host_instance_nonce ||
        admitted == state_->admitted_shadow_episodes.end() ||
        admitted->second.episode != episode.episode_ ||
        !same_slot(episode.episode_.world.incarnation, active->incarnation)) {
        return {.status =
                    failure(RuntimeHostError::StaleReference,
                            "episode capability is stale, forged, or belongs to another host"),
                .lease = {},
                .request_ref = {}};
    }
    const RuntimeStateTransferStatus native_status =
        admitted->second.native_episode.validate_for_host(active->incarnation);
    if (!native_status) {
        state_->admitted_shadow_episodes.erase(admitted);
        return {.status = failure(RuntimeHostError::StaleReference, native_status.detail),
                .lease = {},
                .request_ref = {}};
    }
    if (kind == RuntimeLeaseKind::TruthMutating) {
        if (active->truth_mutating_leases == std::numeric_limits<std::size_t>::max()) {
            return {.status = failure(RuntimeHostError::LeaseCountExhausted,
                                      "truth-mutating lease count exhausted"),
                    .lease = {},
                    .request_ref = {}};
        }
    } else {
        if (active->read_only_result_leases == std::numeric_limits<std::size_t>::max()) {
            return {.status = failure(RuntimeHostError::LeaseCountExhausted,
                                      "read-only lease count exhausted"),
                    .lease = {},
                    .request_ref = {}};
        }
        const auto coordinator = state_->world_coordinators.find(episode.episode_.world.world_slot);
        if (coordinator == state_->world_coordinators.end() || coordinator->second == nullptr) {
            return {.status = failure(RuntimeHostError::StaleReference,
                                      "episode world slot has no host-owned coordinator"),
                    .lease = {},
                    .request_ref = {}};
        }
        const RuntimeEpisodeCoordinatorSnapshot episode_snapshot = coordinator->second->snapshot();
        if (kind == RuntimeLeaseKind::TruthMutating &&
            episode_snapshot.phase == RuntimeEpisodePhase::Terminal) {
            return {.status = failure(
                        RuntimeHostError::AdmissionClosed,
                        "truth-mutating lease is closed at terminal episode; use reset intent"),
                    .lease = {},
                    .request_ref = {}};
        }
        if (!increment_nonzero(state_->last_request_sequence)) {
            return {.status = failure(RuntimeHostError::RequestSequenceExhausted,
                                      "request sequence exhausted"),
                    .lease = {},
                    .request_ref = {}};
        }
        RuntimeRequestRef request_ref = {.episode = episode.episode_,
                                         .request_sequence = state_->last_request_sequence};
        if (kind == RuntimeLeaseKind::TruthMutating) {
            ++active->truth_mutating_leases;
        } else {
            ++active->read_only_result_leases;
        }
        auto token = std::make_shared<RuntimeLeaseToken>(state_, active, request_ref, kind);
        return {.status = success(),
                .lease = RuntimeInstanceLease(std::move(token)),
                .request_ref = request_ref};
    }

    RuntimeHostStatus RuntimeHostCandidate::validate_result(const RuntimeInstanceLease &lease,
                                                            const RuntimeResultRef &result) const {
        if (!result.well_formed() || result.request != lease.request_ref()) {
            return failure(RuntimeHostError::ResultMismatch,
                           "result identity does not match the admitted lease");
        }
        const std::shared_ptr<RuntimeLeaseToken> token = lease.token_;
        std::unique_lock<std::mutex> lock(state_->mutex);
        if (token == nullptr || token->state != state_ || token->slot == nullptr) {
            return failure(RuntimeHostError::StaleReference, "lease belongs to another host");
        }
        if (!token->active.load(std::memory_order_acquire)) {
            return failure(RuntimeHostError::StaleReference,
                           "lease was settled before terminal-result admission");
        }
        if (token->slot->state == RuntimeSlotState::Active &&
            token->slot->result_publication_open) {
            bool expected = false;
            return token->result_accepted.compare_exchange_strong(expected, true)
                       ? success()
                       : failure(RuntimeHostError::DuplicateResult,
                                 "terminal result was already accepted for this request");
        }
        if (token->slot->state == RuntimeSlotState::Draining &&
            token->lease_kind == RuntimeLeaseKind::ReadOnlyResult &&
            token->slot->result_publication_open) {
            bool expected = false;
            return token->result_accepted.compare_exchange_strong(expected, true)
                       ? success()
                       : failure(RuntimeHostError::DuplicateResult,
                                 "terminal result was already accepted for this request");
        }
        return failure(RuntimeHostError::StaleReference,
                       "slot no longer permits result publication for this lease");
    }

    RuntimeShutdownResult RuntimeHostCandidate::begin_shutdown(std::uint64_t now_tick,
                                                               std::uint64_t deadline_tick) {
        const bool injected_loss =
            invoke_cas_fault_injector(state_, RuntimeSlotCasOperation::ShutdownUnpublish);
        std::unique_lock<std::mutex> lock(state_->mutex);
        if (state_->host_state == RuntimeHostState::Stopped) {
            return {.status = success(),
                    .shutdown_ticket = state_->shutdown_ticket,
                    .state = RuntimeHostState::Stopped,
                    .publication_ticket = state_->last_publication_ticket};
        }
        if (state_->host_state == RuntimeHostState::FailStopped) {
            return {.status = failure(RuntimeHostError::QuarantineUnresolved,
                                      "host is fail-stopped with unresolved resources"),
                    .shutdown_ticket = state_->shutdown_ticket,
                    .state = RuntimeHostState::FailStopped,
                    .publication_ticket = state_->last_publication_ticket};
        }
        if (state_->host_state == RuntimeHostState::ShuttingDown) {
            RuntimeHostStatus status = progress_shutdown(*state_, lock, now_tick);
            return {.status = status,
                    .shutdown_ticket = state_->shutdown_ticket,
                    .state = state_->host_state,
                    .publication_ticket = state_->last_publication_ticket};
        }
        if (!increment_nonzero(state_->last_lifecycle_ticket)) {
            state_->host_state = RuntimeHostState::FailStopped;
            return {.status =
                        failure(RuntimeHostError::TicketExhausted, "shutdown ticket exhausted"),
                    .shutdown_ticket = 0,
                    .state = state_->host_state,
                    .publication_ticket = state_->last_publication_ticket};
        }
        state_->shutdown_ticket = state_->last_lifecycle_ticket;
        state_->shutdown_deadline_tick = std::max(now_tick, deadline_tick);
        const std::shared_ptr<RuntimeHostSlot> active =
            state_->active.load(std::memory_order_acquire);
        if (active != nullptr && active->state == RuntimeSlotState::Publishing) {
            return {.status =
                        failure(RuntimeHostError::ShutdownPending,
                                "shutdown is waiting for target import publication to finish"),
                    .shutdown_ticket = state_->shutdown_ticket,
                    .state = state_->host_state,
                    .publication_ticket = state_->last_publication_ticket};
        }
        if (state_->native_episode_submissions_in_flight != 0 ||
            state_->state_transfers_in_flight.load(std::memory_order_acquire) != 0) {
            return {
                .status = failure(
                    RuntimeHostError::ShutdownPending,
                    "shutdown is waiting for native episode or state-transfer callbacks to settle"),
                .shutdown_ticket = state_->shutdown_ticket,
                .state = state_->host_state,
                .publication_ticket = state_->last_publication_ticket};
        }
        state_->host_state = RuntimeHostState::ShuttingDown;

        if (active != nullptr) {
            const RuntimeSlotState prior_active_state = active->state;
            const bool prior_admission_open = active->admission_open;
            const bool prior_result_publication_open = active->result_publication_open;
            active->admission_open = false;
            active->result_publication_open = false;
            active->state = RuntimeSlotState::ShuttingDown;
            std::shared_ptr<RuntimeHostSlot> expected = active;
            const RuntimeHostStatus unpublished =
                compare_exchange_active(*state_, expected, {}, injected_loss);
            if (!unpublished) {
                active->state = prior_active_state;
                active->admission_open = prior_admission_open;
                active->result_publication_open = prior_result_publication_open;
                state_->host_state = active->state == RuntimeSlotState::ActiveFaulted
                                         ? RuntimeHostState::Faulted
                                         : RuntimeHostState::Active;
                return {.status = unpublished,
                        .shutdown_ticket = state_->shutdown_ticket,
                        .state = state_->host_state,
                        .publication_ticket = state_->last_publication_ticket};
            }
            const RuntimeHostStatus cancellation = cancel_slot(*state_, lock, active);
            if (!cancellation) {
                state_->shutdown_pending = active;
                return {.status = cancellation,
                        .shutdown_ticket = state_->shutdown_ticket,
                        .state = state_->host_state,
                        .publication_ticket = state_->last_publication_ticket};
            }
            state_->shutdown_pending = active;
        }
        RuntimeHostStatus status = progress_shutdown(*state_, lock, now_tick);
        return {.status = status,
                .shutdown_ticket = state_->shutdown_ticket,
                .state = state_->host_state,
                .publication_ticket = state_->last_publication_ticket};
    }

    RuntimeHostStatus RuntimeHostCandidate::poll(std::uint64_t now_tick) {
        std::unique_lock<std::mutex> lock(state_->mutex);
        const std::shared_ptr<RuntimeHostSlot> active_before_probe =
            state_->active.load(std::memory_order_acquire);
        const bool candidate_timeout_cas_expected =
            state_->candidate != nullptr && active_before_probe != nullptr &&
            state_->candidate->lifecycle_deadline_tick != 0 &&
            now_tick >= state_->candidate->lifecycle_deadline_tick &&
            !no_truth_leases(*active_before_probe) &&
            (active_before_probe->state == RuntimeSlotState::Quiescing ||
             active_before_probe->state == RuntimeSlotState::RecoveryQuiesced);
        const bool fault_timeout_cas_expected =
            state_->host_state == RuntimeHostState::Faulted && active_before_probe != nullptr &&
            active_before_probe->state == RuntimeSlotState::ActiveFaulted &&
            now_tick >= active_before_probe->drain_deadline_tick;
        lock.unlock();
        const bool injected_quiesce_loss =
            candidate_timeout_cas_expected &&
            invoke_cas_fault_injector(state_, RuntimeSlotCasOperation::QuiesceTimeoutUnpublish);
        const bool injected_fault_loss =
            fault_timeout_cas_expected &&
            invoke_cas_fault_injector(state_, RuntimeSlotCasOperation::FaultTimeoutUnpublish);
        lock.lock();
        apply_pending_quiescence_rollback(*state_);
        const RuntimeHostStatus candidate_deadline =
            progress_candidate_deadline(*state_, lock, now_tick, injected_quiesce_loss);
        if (!candidate_deadline) {
            return candidate_deadline;
        }
        const RuntimeHostStatus fault_deadline =
            progress_fault_deadline(*state_, lock, now_tick, injected_fault_loss);
        if (!fault_deadline) {
            return fault_deadline;
        }
        if (state_->host_state == RuntimeHostState::Stopped ||
            state_->host_state == RuntimeHostState::FailStopped) {
            return state_->host_state == RuntimeHostState::Stopped
                       ? success()
                       : failure(RuntimeHostError::QuarantineUnresolved,
                                 "host is fail-stopped with unresolved resources");
        }
        if (state_->draining != nullptr) {
            const std::shared_ptr<RuntimeHostSlot> draining = state_->draining;
            if (no_leases(*draining)) {
                if (reclaim_slot(*state_, lock, draining)) {
                    clear_slot_reference(*state_, draining);
                } else if (draining->state == RuntimeSlotState::Quarantined) {
                    state_->draining.reset();
                    retain_quarantine(*state_, draining);
                }
            } else if (now_tick >= draining->drain_deadline_tick) {
                state_->draining.reset();
                return move_to_quarantine(*state_, draining);
            }
        }
        if (state_->host_state == RuntimeHostState::ShuttingDown) {
            return progress_shutdown(*state_, lock, now_tick);
        }
        return success();
    }

    RuntimeHostStatus RuntimeHostCandidate::retry_quarantined_reclamation() {
        std::unique_lock<std::mutex> lock(state_->mutex);
        if (state_->quarantined.empty()) {
            return success();
        }
        bool unresolved = false;
        const auto retained = state_->quarantined;

        // First resolve any replacement publication whose owner transaction was
        // left ambiguous.  The source slot is intentionally kept quarantined
        // until this classification completes, so reclamation cannot destroy the
        // rollback target before the durable transaction is settled.
        for (const std::shared_ptr<RuntimeHostSlot> &quarantined : retained) {
            if (quarantined == nullptr || quarantined->rollback_target == nullptr ||
                !quarantined->owner_publication_recovery_pending ||
                quarantined->state != RuntimeSlotState::Quarantined ||
                (!quarantined->validated_transfer.ambiguous() &&
                 !quarantined->validated_transfer.committed() &&
                 !quarantined->validated_transfer.aborted())) {
                continue;
            }
            const std::shared_ptr<RuntimeHostSlot> rollback_target = quarantined->rollback_target;
            lock.unlock();
            const RuntimeStateTransferStatus recovered =
                quarantined->validated_transfer.recover_for_host(0,
                                                                 quarantined->drain_deadline_tick);
            lock.lock();
            if (!recovered) {
                unresolved = true;
                continue;
            }
            if (quarantined->validated_transfer.committed()) {
                std::shared_ptr<RuntimeHostSlot> expected;
                const RuntimeHostStatus published =
                    compare_exchange_active(*state_, expected, quarantined, false);
                if (!published) {
                    unresolved = true;
                    continue;
                }
                quarantined->state = RuntimeSlotState::Active;
                quarantined->owner_publication_recovery_pending = false;
                quarantined->admission_open = true;
                quarantined->result_publication_open = true;
                rollback_target->state = RuntimeSlotState::Draining;
                rollback_target->admission_open = false;
                rollback_target->result_publication_open = true;
                rollback_target->drain_deadline_tick = quarantined->drain_deadline_tick;
                state_->draining = rollback_target;
                state_->rollback_world_authority.clear();
                state_->rollback_world_coordinators.clear();
                state_->host_state = RuntimeHostState::Active;
                state_->quarantined.erase(std::remove(state_->quarantined.begin(),
                                                      state_->quarantined.end(), quarantined),
                                          state_->quarantined.end());
                lock.unlock();
                quarantined->validated_transfer.release_host_transfer_fence();
                lock.lock();
                continue;
            }
            if (quarantined->validated_transfer.aborted()) {
                std::shared_ptr<RuntimeHostSlot> expected;
                const RuntimeHostStatus published =
                    compare_exchange_active(*state_, expected, rollback_target, false);
                if (!published) {
                    unresolved = true;
                    continue;
                }
                if (!state_->rollback_world_authority.empty() ||
                    !state_->rollback_world_coordinators.empty()) {
                    state_->world_authority = std::move(state_->rollback_world_authority);
                    state_->world_coordinators = std::move(state_->rollback_world_coordinators);
                }
                rollback_target->state = RuntimeSlotState::Active;
                rollback_target->admission_open = true;
                rollback_target->result_publication_open = true;
                rollback_target->final_transfer_fence_sequence = 0;
                rollback_target->quiescence_capability_live.store(false, std::memory_order_release);
                state_->host_state = RuntimeHostState::Active;
                quarantined->state = RuntimeSlotState::CandidateFailed;
                quarantined->owner_publication_recovery_pending = false;
                quarantined->admission_open = false;
                quarantined->result_publication_open = false;
                state_->quarantined.erase(std::remove(state_->quarantined.begin(),
                                                      state_->quarantined.end(), quarantined),
                                          state_->quarantined.end());
                state_->quarantined.erase(std::remove(state_->quarantined.begin(),
                                                      state_->quarantined.end(), rollback_target),
                                          state_->quarantined.end());
                lock.unlock();
                quarantined->validated_transfer.release_host_transfer_fence();
                lock.lock();
                if (!reclaim_slot(*state_, lock, quarantined)) {
                    unresolved = true;
                }
            }
        }

        for (const std::shared_ptr<RuntimeHostSlot> &quarantined : retained) {
            if (quarantined == nullptr || quarantined->state != RuntimeSlotState::Quarantined) {
                continue;
            }
            const bool waits_for_replacement =
                std::any_of(retained.begin(), retained.end(), [&](const auto &candidate) {
                    return candidate != nullptr &&
                           candidate->state == RuntimeSlotState::Quarantined &&
                           candidate->owner_publication_recovery_pending &&
                           candidate->rollback_target == quarantined;
                });
            if (waits_for_replacement) {
                unresolved = true;
                continue;
            }
            if (!no_leases(*quarantined)) {
                unresolved = true;
                continue;
            }
            if (!reclaim_slot(*state_, lock, quarantined)) {
                unresolved = true;
                continue;
            }
            clear_slot_reference(*state_, quarantined);
        }
        if (unresolved) {
            return failure(RuntimeHostError::QuarantineUnresolved,
                           "one or more quarantined resources remain retained");
        }
        if (state_->host_state == RuntimeHostState::ShuttingDown) {
            return progress_shutdown(*state_, lock, state_->shutdown_deadline_tick);
        }
        return state_->host_state == RuntimeHostState::FailStopped
                   ? failure(RuntimeHostError::HostTerminal,
                             "resources were released but fail-stopped host remains terminal")
                   : success();
    }

    RuntimeHostSnapshot RuntimeHostCandidate::snapshot() const {
        std::unique_lock<std::mutex> lock(state_->mutex);
        const std::shared_ptr<RuntimeHostSlot> active =
            state_->active.load(std::memory_order_acquire);
        std::vector<RuntimeSlotSnapshot> quarantined;
        quarantined.reserve(state_->quarantined.size());
        for (const std::shared_ptr<RuntimeHostSlot> &slot : state_->quarantined) {
            quarantined.push_back(snapshot_slot(*slot));
        }
        RuntimeHostSnapshot output{
            .identity = state_->identity,
            .mode = state_->config.mode,
            .state = state_->host_state,
            .host_instance_nonce = state_->host_instance_nonce,
            .production_authorized = state_->production_authorized,
            .last_lifecycle_ticket = state_->last_lifecycle_ticket,
            .last_request_sequence = state_->last_request_sequence,
            .shutdown_ticket = state_->shutdown_ticket,
            .last_publication_ticket = state_->last_publication_ticket,
            .active = active == nullptr
                          ? std::nullopt
                          : std::optional<RuntimeSlotSnapshot>(snapshot_slot(*active)),
            .candidate = state_->candidate == nullptr ? std::nullopt
                                                      : std::optional<RuntimeSlotSnapshot>(
                                                            snapshot_slot(*state_->candidate)),
            .draining = state_->draining == nullptr
                            ? std::nullopt
                            : std::optional<RuntimeSlotSnapshot>(snapshot_slot(*state_->draining)),
            .quarantined = std::move(quarantined),
            .shutdown_pending =
                state_->shutdown_pending == nullptr
                    ? std::nullopt
                    : std::optional<RuntimeSlotSnapshot>(snapshot_slot(*state_->shutdown_pending)),
            .retired_incarnation_high_watermark = state_->retired_incarnation_high_watermark,
        };
        return output;
    }

    std::size_t RuntimeHostCandidate::orphaned_host_count() noexcept {
        try {
            HostOrphanRegistry &registry = orphan_registry();
            std::lock_guard<std::mutex> lock(registry.mutex);
            return registry.hosts.size();
        } catch (...) {
            return 0;
        }
    }

    RuntimeHostStatus RuntimeHostCandidate::retry_orphaned_reclamation() {
        std::vector<std::shared_ptr<RuntimeHostSharedState>> states;
        {
            HostOrphanRegistry &registry = orphan_registry();
            std::lock_guard<std::mutex> lock(registry.mutex);
            states = registry.hosts;
        }

        bool unresolved = false;
        for (const std::shared_ptr<RuntimeHostSharedState> &state : states) {
            std::unique_lock<std::mutex> lock(state->mutex);
            const auto quarantined = state->quarantined;
            for (const std::shared_ptr<RuntimeHostSlot> &slot : quarantined) {
                if (!no_leases(*slot) || !reclaim_slot(*state, lock, slot)) {
                    unresolved = true;
                    continue;
                }
                clear_slot_reference(*state, slot);
            }
            if (state->host_state == RuntimeHostState::ShuttingDown) {
                const RuntimeHostStatus status = progress_shutdown(*state, lock, 0);
                if (!status && status.error != RuntimeHostError::ShutdownPending) {
                    unresolved = true;
                }
            }
        }

        {
            HostOrphanRegistry &registry = orphan_registry();
            std::lock_guard<std::mutex> orphan_lock(registry.mutex);
            std::erase_if(registry.hosts, [](const auto &state) {
                std::lock_guard<std::mutex> state_lock(state->mutex);
                const bool no_owned_slots =
                    state->active.load(std::memory_order_acquire) == nullptr &&
                    state->candidate == nullptr && state->draining == nullptr &&
                    state->shutdown_pending == nullptr && state->quarantined.empty();
                if (no_owned_slots) {
                    state->orphan_handoff_recorded = false;
                }
                return no_owned_slots;
            });
            unresolved = unresolved || !registry.hosts.empty();
        }
        return unresolved ? failure(RuntimeHostError::QuarantineUnresolved,
                                    "one or more orphaned host resources remain retained")
                          : success();
    }

} // namespace runtime::host
