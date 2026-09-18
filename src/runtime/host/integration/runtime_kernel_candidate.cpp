#include "runtime_kernel_candidate.h"

#include "simulation_kernel_state_owner_adapters.h"
#include "components/basic/common.h"

#include <atomic>
#include <filesystem>
#include <limits>
#include <stdexcept>
#include <unordered_map>
#include <utility>

namespace runtime::host::integration {

namespace {

using echelon_forge::runtime_contracts::v1::RuntimeEntityRef;
using echelon_forge::runtime_contracts::v1::RuntimeEpisodeRef;
using echelon_forge::runtime_contracts::v1::RuntimeIdentity128;
using echelon_forge::runtime_contracts::v1::RuntimeIncarnationRef;
using echelon_forge::runtime_contracts::v1::RuntimeWorldRef;

std::atomic<std::uint64_t> next_resource_sequence{1};

RuntimeIdentity128 mint_candidate_resource() noexcept {
    return {.high = 0x4546432D50344300ULL,
            .low = next_resource_sequence.fetch_add(1, std::memory_order_relaxed)};
}

std::string valid_digest(char value) { return std::string(64, value); }

class FileJournal final : public RuntimeStateTransferJournal {
  public:
    explicit FileJournal(std::string path) : journal_(std::move(path)) {}

    RuntimeStateTransferJournalAppendResult append_and_sync(
        std::string_view transaction_id, RuntimeStateOwnerImportTransactionPhase phase,
        std::string_view payload_sha256, std::string_view pre_mutation_sha256,
        const std::vector<std::uint8_t> &pre_mutation_payload) noexcept override {
        return journal_.append_and_sync(transaction_id, phase, payload_sha256,
                                        pre_mutation_sha256, pre_mutation_payload);
    }

    RuntimeStateTransferJournalReadResult latest(std::string_view transaction_id) noexcept override {
        return journal_.latest(transaction_id);
    }

  private:
    RuntimeStateTransferFileJournal journal_;
};

} // namespace

class RuntimeKernelCandidate::Control final : public RuntimeInstanceControl {
  public:
    Control(RuntimeIdentity128 resource, std::shared_ptr<SimulationKernel> kernel)
        : resource_(resource), kernel_(kernel), native_(std::make_shared<Native>(resource, kernel)) {}

    class Native final : public RuntimeNativeEpisodeControl {
      public:
        Native(RuntimeIdentity128 resource, std::shared_ptr<SimulationKernel> kernel)
            : resource_(resource), kernel_(kernel) {}

        RuntimeIdentity128 resource_identity() const noexcept override { return resource_; }

        RuntimeNativeEpisodeMutation apply(
            const RuntimeNativeEpisodeCommand &command) noexcept override {
            if (kernel_ == nullptr) {
                return {};
            }
            try {
                if (command.intent.kind == RuntimeEpisodeIntentKind::Action) {
                    kernel_->step();
                } else if (command.intent.kind == RuntimeEpisodeIntentKind::Reset) {
                    kernel_->reset(0);
                } else {
                    return {};
                }
            } catch (...) {
                return {};
            }
            const bool terminal = command.intent.kind == RuntimeEpisodeIntentKind::Action &&
                                  terminal_receipt_for_test_.exchange(false,
                                                                      std::memory_order_acq_rel);
            std::string snapshot_sha256;
            try {
                const std::string serialized =
                    SimulationKernelStateOwnerBridge::serialize_world(*kernel_);
                const std::vector<std::uint8_t> bytes(serialized.begin(), serialized.end());
                snapshot_sha256 = runtime_state_payload_sha256(bytes);
            } catch (...) {
                return {};
            }
            return {.applied = true,
                    .terminal = terminal,
                    .snapshot_id = {.high = resource_.high,
                                    .low = next_snapshot_sequence_.fetch_add(
                                        1, std::memory_order_relaxed)},
                    .snapshot_sha256 = snapshot_sha256};
        }

        void arm_terminal_receipt_for_test() noexcept {
            terminal_receipt_for_test_.store(true, std::memory_order_release);
        }

      private:
        RuntimeIdentity128 resource_;
        std::shared_ptr<SimulationKernel> kernel_;
        std::atomic_bool terminal_receipt_for_test_{false};
        std::atomic<std::uint64_t> next_snapshot_sequence_{1};
    };

    RuntimeIdentity128 resource_identity() const noexcept override { return resource_; }
    std::shared_ptr<RuntimeNativeEpisodeControl>
    native_episode_control() const noexcept override { return native_; }
    std::shared_ptr<RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept override { return registry_; }
    bool begin_state_transfer() noexcept override {
        bool expected = false;
        return !released_ &&
               transfer_active_.compare_exchange_strong(expected, true,
                                                        std::memory_order_acq_rel);
    }
    void end_state_transfer() noexcept override {
        transfer_active_.store(false, std::memory_order_release);
    }
    bool transfer_active() const noexcept {
        return transfer_active_.load(std::memory_order_acquire);
    }
    bool request_cooperative_cancel() noexcept override {
        cancellation_acknowledged_ = true;
        return true;
    }
    bool release_resources() noexcept override {
        released_ = true;
        return true;
    }
    bool resources_released() const noexcept override { return released_; }

    void bind_registry(std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry) {
        registry_ = std::move(registry);
    }

    void arm_terminal_receipt_for_test() noexcept {
        native_->arm_terminal_receipt_for_test();
    }

  private:
    RuntimeIdentity128 resource_;
    std::shared_ptr<SimulationKernel> kernel_;
    std::shared_ptr<Native> native_;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry_;
    bool cancellation_acknowledged_ = false;
    bool released_ = false;
    std::atomic_bool transfer_active_{false};
};

RuntimeKernelCandidate::RuntimeKernelCandidate(RuntimeKernelCandidateConfig config)
    : config_(std::move(config)),
      kernel_(config_.resolved_manifest_json.empty()
                  ? std::make_shared<SimulationKernel>()
                  : std::make_shared<SimulationKernel>(config_.resolved_manifest_json)),
      host_(RuntimeHostConfig{.host_id = config_.host_id, .mode = config_.mode}) {
    if (!config_.host_id.well_formed()) {
        throw std::invalid_argument("candidate host_id must be non-zero");
    }
    const RuntimeIdentity128 resource = mint_candidate_resource();
    control_ = std::make_shared<Control>(resource, kernel_);
    std::string journal_path = config_.journal_path;
    owns_journal_path_ = journal_path.empty();
    if (journal_path.empty()) {
        journal_path = (std::filesystem::temp_directory_path() /
                        ("echelon_forge_p4c_candidate_" + std::to_string(resource.low) + ".wal"))
                           .string();
    }
    journal_path_ = journal_path;
    journal_ = std::make_shared<FileJournal>(journal_path);
    registry_ = SimulationKernelStateOwnerBridge::create_registry({
        .kernel = kernel_.get(),
        .journal = journal_,
        .transaction_namespace = "p4c-kernel-candidate-" + std::to_string(resource.low),
        .bound_resource_identity = resource,
        .sample_tick = [deadline_tick = config_.lifecycle_deadline_tick] {
            return deadline_tick;
        },
        .rederive_python_caches = [] { return true; },
        .snapshot_python_caches = [] { return std::vector<std::uint8_t>{0}; },
        .rollback_python_caches = [](const std::vector<std::uint8_t> &before) {
            return before.size() == 1;
        },
        .recover_python_caches = [](const std::vector<std::uint8_t> &) {
            return RuntimeStateOwnerImportTransactionPhase::Committed;
        },
    });
    if (registry_ == nullptr) {
        throw std::runtime_error("P4-C kernel owner registry construction failed");
    }
    control_->bind_registry(registry_);

    sealed_composition_ = composition_snapshot();
    if (config_.plan.plan_id.empty() && config_.plan.plan_sha256.empty()) {
        config_.plan = {.plan_id = "p4c.kernel-candidate.v1",
                        .plan_sha256 = sealed_composition_.resolved_manifest_sha256};
    }
}

RuntimeKernelCandidate::~RuntimeKernelCandidate() {
    bool shutdown_completed = stopped_;
    if (!stopped_) {
        shutdown_completed = static_cast<bool>(shutdown(0, 0).status);
    }
    registry_.reset();
    control_.reset();
    kernel_.reset();
    journal_.reset();
    if (shutdown_completed && owns_journal_path_ && !journal_path_.empty()) {
        std::error_code error;
        (void)std::filesystem::remove(journal_path_, error);
    }
}

RuntimeCandidateCompositionSnapshot RuntimeKernelCandidate::composition_snapshot() const {
    if (kernel_ == nullptr) {
        return {};
    }
    return {.requested_manifest_sha256 = kernel_->requested_composition_sha256(),
            .resolved_manifest_sha256 = kernel_->resolved_composition_sha256(),
            .executable_graph_sha256 = kernel_->executable_composition_graph_sha256(),
            .scope_generations = kernel_->composition_scope_generations()};
}

bool RuntimeKernelCandidate::composition_immutable() const noexcept {
    try {
        return composition_snapshot() == sealed_composition_;
    } catch (...) {
        return false;
    }
}

RuntimeHostStatus RuntimeKernelCandidate::initialize_candidate() {
    if (!config_.plan.well_formed() ||
        config_.plan.plan_sha256 != sealed_composition_.resolved_manifest_sha256) {
        return {.error = RuntimeHostError::InvalidArgument,
                .detail = "P4-C candidate plan is not bound to the sealed resolved composition"};
    }
    const auto owner = host_.issue_owner_handle(control_, {
        .transaction_kind = RuntimeHostTransactionKind::Initial,
        .plan = config_.plan,
        .world_slot_count = 1,
    });
    if (!owner.valid()) {
        return {.error = RuntimeHostError::InvalidArgument,
                .detail = "P4-C candidate owner handle was not issued"};
    }
    const auto begun = host_.begin_candidate({
        .transaction_kind = RuntimeHostTransactionKind::Initial,
        .plan = config_.plan,
        .lifecycle_deadline_tick = config_.lifecycle_deadline_tick,
        .world_slot_count = 1,
    }, owner);
    if (!begun.status) {
        return begun.status;
    }
    const auto validated = host_.validate_candidate(
        begun.handle,
        {.static_plan_validated = true,
         .resources_ready = true,
         .shadow_probe_passed = true,
         .unreachable_from_production = true,
         .production_authorized = false});
    if (!validated) {
        return validated;
    }
    const auto published = host_.commit_initial(
        begun.handle,
        {.lifecycle_evidence_sha256 = valid_digest('b'),
         .dark_evidence_sealed = true,
         .production_authorized = false});
    if (!published.status) {
        return published.status;
    }
    incarnation_ = published.published_slot;
    started_ = true;
    return {};
}

RuntimeHostStatus RuntimeKernelCandidate::start() {
    if (started_) {
        return {};
    }
    if (stopped_) {
        return {.error = RuntimeHostError::HostTerminal,
                .detail = "P4-C candidate was already stopped"};
    }
    return initialize_candidate();
}

void RuntimeKernelCandidate::arm_terminal_receipt_for_test() noexcept {
    if (control_ != nullptr) {
        control_->arm_terminal_receipt_for_test();
    }
}

RuntimeShutdownResult RuntimeKernelCandidate::shutdown(std::uint64_t now_tick,
                                                       std::uint64_t deadline_tick) {
    if (stopped_) {
        return {.status = {}, .state = RuntimeHostState::Stopped};
    }
    const auto result = host_.begin_shutdown(now_tick, deadline_tick);
    if (result.status && kernel_ != nullptr) {
        kernel_->shutdown();
        stopped_ = true;
    }
    return result;
}

RuntimeHostSnapshot RuntimeKernelCandidate::host_snapshot() const { return host_.snapshot(); }

RuntimeIncarnationRef RuntimeKernelCandidate::incarnation() const noexcept { return incarnation_; }

RuntimeWorldRef RuntimeKernelCandidate::world_ref() const noexcept {
    return {.incarnation = incarnation_, .world_slot = 0, .world_generation = world_generation_};
}

RuntimeEpisodeRef RuntimeKernelCandidate::episode_ref() noexcept { return current_episode(); }

RuntimeEpisodeRef RuntimeKernelCandidate::current_episode() noexcept {
    const auto admission = host_.issue_shadow_episode(0);
    if (!admission.status) {
        return {};
    }
    const RuntimeEpisodeRef episode = admission.capability.episode();
    (void)host_.release_shadow_episode(admission.capability);
    return episode;
}

bool RuntimeKernelCandidate::validate_world(const RuntimeWorldRef &world) const noexcept {
    return started_ && !stopped_ && control_ != nullptr && !control_->transfer_active() &&
           world.well_formed() && world == world_ref() &&
           host_.snapshot().active.has_value() &&
           host_.snapshot().active->incarnation == incarnation_;
}

std::optional<RuntimeEntityRef> RuntimeKernelCandidate::entity_ref(std::uint64_t entity_id) const {
    if (entity_id == 0 || !validate_world(world_ref())) {
        return std::nullopt;
    }
    return RuntimeEntityRef{.world = world_ref(), .entity_id = entity_id,
                            .entity_generation = next_entity_generation_};
}

bool RuntimeKernelCandidate::validate_entity(const RuntimeEntityRef &entity) const noexcept {
    return validate_world(entity.world) && entity.entity_id != 0 &&
           entity.entity_generation == next_entity_generation_;
}

std::optional<RuntimeEntityRef> RuntimeKernelCandidate::spawn_unit(
    const RuntimeWorldRef &world, const WorldSpawnRequest &request) {
    if (!validate_world(world) || request.world_index != 0 || kernel_ == nullptr ||
        request.type_name.empty()) {
        return std::nullopt;
    }
    const auto episode_admission = host_.issue_shadow_episode(0);
    if (!episode_admission.status) {
        return std::nullopt;
    }
    auto lease_admission =
        host_.acquire_lease(episode_admission.capability, RuntimeLeaseKind::TruthMutating);
    if (!lease_admission.status) {
        (void)host_.release_shadow_episode(episode_admission.capability);
        return std::nullopt;
    }
    try {
        const auto entity = kernel_->spawn_unit(request.side, request.type_name, request.x,
                                                request.y, request.z, request.heading,
                                                request.pitch, request.roll, request.vx, request.vy,
                                                request.vz);
        if (!entity.is_valid()) {
            lease_admission.lease.settle();
            (void)host_.release_shadow_episode(episode_admission.capability);
            return std::nullopt;
        }
        const auto result = entity_ref(entity.id());
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return result;
    } catch (...) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return std::nullopt;
    }
}

bool RuntimeKernelCandidate::submit_episode(const RuntimeEpisodeRef &expected_episode,
                                            RuntimeEpisodeIntentKind kind,
                                            RuntimeIdentity128 idempotency_key,
                                            std::string payload_sha256,
                                            RuntimeEpisodeTransitionReceipt *receipt) {
    if (!started_ || stopped_ || control_ == nullptr || control_->transfer_active() ||
        !expected_episode.well_formed() ||
        expected_episode.world != world_ref() || !idempotency_key.well_formed() ||
        payload_sha256.size() != 64) {
        return false;
    }
    const auto admission = host_.issue_shadow_episode(0);
    if (!admission.status) {
        return false;
    }
    if (admission.capability.episode() != expected_episode) {
        (void)host_.release_shadow_episode(admission.capability);
        return false;
    }
    const auto transition = host_.submit_shadow_episode(
        admission.capability,
        {.kind = kind,
         .expected_episode = expected_episode,
         .expected_step_sequence = episode_step_sequence_,
         .idempotency_key = idempotency_key,
         .payload_sha256 = std::move(payload_sha256),
         .production_authorized = false});
    if (receipt != nullptr && transition.status) {
        *receipt = transition.receipt;
    }
    (void)host_.release_shadow_episode(admission.capability);
    if (transition.status) {
        episode_step_sequence_ = transition.receipt.resulting_step_sequence;
        if (transition.receipt.reset_applied) {
            world_generation_ = transition.receipt.episode_after.world.world_generation;
            ++next_entity_generation_;
            episode_step_sequence_ = 0;
        }
    }
    return static_cast<bool>(transition.status);
}

bool RuntimeKernelCandidate::step(const RuntimeWorldRef &world) {
    if (!validate_world(world)) {
        return false;
    }
    const auto episode = current_episode();
    if (next_action_idempotency_sequence_ == std::numeric_limits<std::uint64_t>::max()) {
        return false;
    }
    const std::uint64_t idempotency_sequence = next_action_idempotency_sequence_++;
    RuntimeEpisodeTransitionReceipt receipt{};
    return submit_episode(episode, RuntimeEpisodeIntentKind::Action,
                          {.high = 0x4550432D53544550ULL, .low = idempotency_sequence},
                          valid_digest('c'),
                          &receipt);
}

bool RuntimeKernelCandidate::set_time_step(const RuntimeWorldRef &world, double dt) {
    if (!validate_world(world) || kernel_ == nullptr) {
        return false;
    }
    try {
        kernel_->set_time_step(dt);
        return true;
    } catch (...) {
        return false;
    }
}

bool RuntimeKernelCandidate::try_get_entity_kinematics(
    const RuntimeEntityRef &entity, WorldEntityKinematics *state) {
    if (!validate_entity(entity) || state == nullptr || kernel_ == nullptr) {
        return false;
    }
    const auto episode_admission = host_.issue_shadow_episode(0);
    if (!episode_admission.status) {
        return false;
    }
    auto lease_admission =
        host_.acquire_lease(episode_admission.capability, RuntimeLeaseKind::ReadOnlyResult);
    if (!lease_admission.status) {
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    auto lease = kernel_->acquire_world_lease();
    const auto target = lease.world().entity(entity.entity_id);
    if (!target.is_valid()) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    const Transform *transform = target.get<Transform>();
    const Velocity *velocity = target.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    state->x = transform->x;
    state->y = transform->y;
    state->z = transform->z;
    state->vx = velocity->vx;
    state->vy = velocity->vy;
    state->vz = velocity->vz;
    state->heading = transform->heading;
    state->pitch = transform->pitch;
    state->roll = transform->roll;
    lease_admission.lease.settle();
    (void)host_.release_shadow_episode(episode_admission.capability);
    return true;
}

bool RuntimeKernelCandidate::try_set_entity_kinematics(
    const RuntimeEntityRef &entity, const WorldEntityKinematics &state) {
    if (!validate_entity(entity) || kernel_ == nullptr) {
        return false;
    }
    const auto episode_admission = host_.issue_shadow_episode(0);
    if (!episode_admission.status) {
        return false;
    }
    auto lease_admission =
        host_.acquire_lease(episode_admission.capability, RuntimeLeaseKind::TruthMutating);
    if (!lease_admission.status) {
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    auto lease = kernel_->acquire_world_lease();
    const auto target = lease.world().entity(entity.entity_id);
    if (!target.is_valid()) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    const Transform *transform = target.get<Transform>();
    const Velocity *velocity = target.get<Velocity>();
    if (transform == nullptr || velocity == nullptr) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return false;
    }
    target.set<Transform>(Transform{.x = state.x,
                                    .y = state.y,
                                    .z = state.z,
                                    .heading = state.heading,
                                    .pitch = state.pitch,
                                    .roll = state.roll});
    target.set<Velocity>(Velocity{.vx = state.vx, .vy = state.vy, .vz = state.vz});
    lease_admission.lease.settle();
    (void)host_.release_shadow_episode(episode_admission.capability);
    return true;
}

} // namespace runtime::host::integration
