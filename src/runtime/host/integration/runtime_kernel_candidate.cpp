#include "runtime_kernel_candidate.h"

#include "simulation_kernel_state_owner_adapters.h"
#include "components/basic/common.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <atomic>
#include <filesystem>
#include <limits>
#include <mutex>
#include <stdexcept>
#include <unordered_map>
#include <utility>

#include <nlohmann/json.hpp>

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

std::string valid_digest(char value) {
    return std::string(64, value);
}

std::string hex_encode_bytes(const std::vector<std::uint8_t> &bytes) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string output;
    output.reserve(bytes.size() * 2U);
    for (const auto byte : bytes) {
        output.push_back(digits[byte >> 4U]);
        output.push_back(digits[byte & 0x0fU]);
    }
    return output;
}

class FileJournal final : public RuntimeStateTransferJournal {
  public:
    explicit FileJournal(std::string path) : journal_(std::move(path)) {}

    RuntimeStateTransferJournalAppendResult
    append_and_sync(std::string_view transaction_id, RuntimeStateOwnerImportTransactionPhase phase,
                    std::string_view payload_sha256, std::string_view pre_mutation_sha256,
                    const std::vector<std::uint8_t> &pre_mutation_payload) noexcept override {
        return journal_.append_and_sync(transaction_id, phase, payload_sha256, pre_mutation_sha256,
                                        pre_mutation_payload);
    }

    RuntimeStateTransferJournalReadResult
    latest(std::string_view transaction_id) noexcept override {
        return journal_.latest(transaction_id);
    }

  private:
    RuntimeStateTransferFileJournal journal_;
};

} // namespace

class RuntimeKernelCandidate::Control final : public RuntimeInstanceControl {
  public:
    Control(RuntimeIdentity128 resource, std::shared_ptr<SimulationKernel> kernel,
            std::uint32_t reset_seed)
        : resource_(resource), kernel_(kernel),
          native_(std::make_shared<Native>(resource, kernel, reset_seed)) {}

    class Native final : public RuntimeNativeEpisodeControl {
      public:
        Native(RuntimeIdentity128 resource, std::shared_ptr<SimulationKernel> kernel,
               std::uint32_t reset_seed)
            : resource_(resource), kernel_(kernel), reset_seed_(reset_seed) {}

        RuntimeIdentity128 resource_identity() const noexcept override { return resource_; }

        RuntimeNativeEpisodeMutation
        apply(const RuntimeNativeEpisodeCommand &command) noexcept override {
            if (kernel_ == nullptr) {
                return {};
            }
            try {
                if (command.intent.kind == RuntimeEpisodeIntentKind::Action) {
                    kernel_->step();
                } else if (command.intent.kind == RuntimeEpisodeIntentKind::Reset) {
                    kernel_->reset(reset_seed_);
                } else {
                    return {};
                }
            } catch (...) {
                return {};
            }
            const bool terminal =
                command.intent.kind == RuntimeEpisodeIntentKind::Action &&
                terminal_receipt_for_test_.exchange(false, std::memory_order_acq_rel);
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
        std::uint32_t reset_seed_ = 0U;
        std::atomic_bool terminal_receipt_for_test_{false};
        std::atomic<std::uint64_t> next_snapshot_sequence_{1};
    };

    RuntimeIdentity128 resource_identity() const noexcept override { return resource_; }
    std::shared_ptr<RuntimeNativeEpisodeControl> native_episode_control() const noexcept override {
        return native_;
    }
    std::shared_ptr<RuntimeStateTransferOwnerRegistry>
    state_transfer_owner_registry() const noexcept override {
        return registry_;
    }
    bool begin_state_transfer() noexcept override {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        if (released_ || transfer_active_) return false;
        transfer_active_ = true;
        return true;
    }
    void end_state_transfer() noexcept override {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        transfer_active_ = false;
    }
    bool transfer_active() const noexcept {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return transfer_active_;
    }
    bool request_cooperative_cancel() noexcept override {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        cancellation_acknowledged_ = true;
        return true;
    }
    bool release_resources() noexcept override {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        released_ = true;
        return true;
    }
    bool resources_released() const noexcept override {
        std::lock_guard<std::mutex> lock(lifecycle_mutex_);
        return released_;
    }

    void bind_registry(std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry) {
        registry_ = std::move(registry);
    }

    void arm_terminal_receipt_for_test() noexcept { native_->arm_terminal_receipt_for_test(); }

  private:
    RuntimeIdentity128 resource_;
    std::shared_ptr<SimulationKernel> kernel_;
    std::shared_ptr<Native> native_;
    std::shared_ptr<RuntimeStateTransferOwnerRegistry> registry_;
    mutable std::mutex lifecycle_mutex_;
    bool cancellation_acknowledged_ = false;
    bool released_ = false;
    bool transfer_active_ = false;
};

RuntimeKernelCandidate::RuntimeKernelCandidate(RuntimeKernelCandidateConfig config)
    : config_(std::move(config)), kernel_(nullptr),
      host_(RuntimeHostConfig{.host_id = config_.host_id, .mode = config_.mode}) {
    if (!config_.host_id.well_formed()) {
        throw std::invalid_argument("candidate host_id must be non-zero");
    }
    if (config_.run_recorder_store == nullptr && !config_.run_ledger_path.empty()) {
        if (config_.run_audit_identity.empty())
            throw std::invalid_argument("P5-B production ledger requires an audit identity");
        owned_run_store_ = std::make_unique<RuntimeFileArtifactLedgerStore>(
            config_.run_ledger_path,
            RuntimeArtifactLedgerAccessContext{RuntimeArtifactLedgerRole::RuntimeHost,
                                               config_.run_audit_identity});
        config_.run_recorder_store = owned_run_store_.get();
    }
    const bool recorder_configured = config_.run_recorder_store != nullptr;
    const bool recorder_identity_present = !config_.run_id.empty() ||
                                           !config_.run_writer_id.empty() ||
                                           !config_.run_header_json.empty();
    if (recorder_configured != recorder_identity_present ||
        (recorder_configured && (config_.run_id.empty() || config_.run_writer_id.empty() ||
                                 config_.run_header_json.empty()))) {
        throw std::invalid_argument(
            "P5-B recorder configuration requires store, run, writer, and header together");
    }
    if (recorder_configured && config_.run_receipt_template_json.empty()) {
        throw std::invalid_argument(
            "P5-B recorder configuration requires a run-specific terminal receipt template");
    }
    if (recorder_configured) {
        if (config_.run_execution_sources.resolved_execution_plan_path.empty() ||
            config_.run_execution_sources.request_path.empty() ||
            config_.run_execution_sources.package_path.empty() ||
            config_.run_execution_sources.wheel_path.empty()) {
            throw std::invalid_argument("P5-B recorder configuration requires owner-controlled "
                                        "execution provenance sources");
        }
        std::string header_detail;
        if (!validate_runtime_run_header_json(config_.run_id, config_.run_header_json,
                                              header_detail)) {
            throw std::invalid_argument("P5-B recorder configuration requires a complete run "
                                        "admission binding: " +
                                        header_detail);
        }
        const auto header = nlohmann::json::parse(config_.run_header_json);
        std::string observed_bindings_json;
        std::string verified_request_json;
        if (!collect_runtime_execution_bindings_json(
                config_.run_execution_sources, header.at("receipt_bindings").dump(),
                observed_bindings_json, header_detail, &verified_request_json) ||
            observed_bindings_json != header.at("receipt_bindings").dump()) {
            throw std::invalid_argument("P5-B execution provenance differs from admitted header: " +
                                        header_detail);
        }
        const auto verified_request = nlohmann::json::parse(verified_request_json);
        const auto &configuration = verified_request.at("configuration");
        admitted_seed_ = configuration.at("seed").get<std::uint32_t>();
        admitted_time_step_ns_ = configuration.at("time_step_ns").get<std::uint64_t>();
        std::string execution_plan_json;
        if (!load_runtime_execution_plan_json(config_.run_execution_sources,
                                              header.at("receipt_bindings").dump(),
                                              execution_plan_json, header_detail)) {
            throw std::invalid_argument("P5-B admitted execution plan cannot be loaded: " +
                                        header_detail);
        }
        const auto &admitted_plan = header.at("receipt_bindings").at("plan_binding");
        const RuntimePlanBinding header_plan = {
            .plan_id = admitted_plan.at("plan_id").get<std::string>(),
            .plan_sha256 = admitted_plan.at("plan_sha256").get<std::string>(),
        };
        if (config_.plan.plan_id.empty() && config_.plan.plan_sha256.empty()) {
            config_.plan = header_plan;
        } else if (config_.plan != header_plan) {
            throw std::invalid_argument("P5-B recorder plan differs from the admitted run binding");
        }
        if (!config_.resolved_manifest_json.empty() &&
            config_.resolved_manifest_json != execution_plan_json) {
            throw std::invalid_argument(
                "P5-B caller-selected runtime input differs from the admitted execution plan");
        }
        config_.resolved_manifest_json = std::move(execution_plan_json);
        admitted_execution_plan_sha256_ = admitted_plan.at("plan_sha256").get<std::string>();
        const auto admitted_plan_document = nlohmann::json::parse(config_.resolved_manifest_json);
        admitted_resolved_manifest_sha256_ = admitted_plan_document.at("input_bindings")
                                                 .at("resolved_manifest_sha256")
                                                 .get<std::string>();
        run_recorder_ = std::make_unique<RuntimeRunRecorder>(*config_.run_recorder_store,
                                                             config_.run_id, config_.run_writer_id);
        const auto admission = run_recorder_->admit(config_.run_header_json);
        if (!admission) {
            throw std::invalid_argument(
                "P5-B durable admission failed before kernel construction: " + admission.detail);
        }
    }
    try {
        kernel_ = config_.resolved_manifest_json.empty()
                      ? std::make_shared<SimulationKernel>()
                      : std::make_shared<SimulationKernel>(config_.resolved_manifest_json);
        if (admitted_seed_.has_value() && admitted_time_step_ns_.has_value()) {
            const auto configuration = nlohmann::json{
                {"event", "runtime_configuration"},
                {"phase", "intent"},
                {"seed", *admitted_seed_},
                {"time_step_ns",
                 *admitted_time_step_ns_}}.dump();
            if (!run_recorder_->append(run_recorder_->next_sequence(), configuration)) {
                throw std::runtime_error(
                    "P5-B runtime configuration intent could not be made durable");
            }
            kernel_->reset(*admitted_seed_);
            kernel_->set_time_step(static_cast<double>(*admitted_time_step_ns_) / 1'000'000'000.0);
            const auto applied = nlohmann::json{
                {"event", "runtime_configuration"},
                {"phase", "outcome"},
                {"seed", *admitted_seed_},
                {"time_step_ns", *admitted_time_step_ns_},
                {"applied", true}}.dump();
            if (!run_recorder_->append(run_recorder_->next_sequence(), applied)) {
                throw std::runtime_error(
                    "P5-B runtime configuration outcome could not be made durable");
            }
        }
        const RuntimeIdentity128 resource = mint_candidate_resource();
        control_ = std::make_shared<Control>(resource, kernel_, admitted_seed_.value_or(0U));
        std::string journal_path = config_.journal_path;
        owns_journal_path_ = journal_path.empty();
        if (journal_path.empty()) {
            journal_path =
                (std::filesystem::temp_directory_path() /
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
            .sample_tick = [deadline_tick =
                                config_.lifecycle_deadline_tick] { return deadline_tick; },
            .rederive_python_caches = [] { return true; },
            .snapshot_python_caches = [] { return std::vector<std::uint8_t>{0}; },
            .rollback_python_caches =
                [](const std::vector<std::uint8_t> &before) { return before.size() == 1; },
            .recover_python_caches =
                [](const std::vector<std::uint8_t> &) {
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
        if (run_recorder_ != nullptr) {
            const auto lifecycle = run_recorder_->note_lifecycle("construction");
            if (!lifecycle)
                throw std::runtime_error("P5-B construction lifecycle evidence failed: " +
                                         lifecycle.detail);
        }
    } catch (const std::exception &error) {
        if (run_recorder_ != nullptr && run_recorder_->terminalizable()) {
            try {
                const auto arguments =
                    nlohmann::json{{"error", error.what()}, {"phase", "candidate_construction"}};
                (void)record_mutation("construction_failed", arguments.dump());
                (void)finalize_observed(config_.run_receipt_template_json, "failed", error.what());
            } catch (...) {
            }
        }
        throw;
    }
}

RuntimeKernelCandidate::~RuntimeKernelCandidate() {
    bool shutdown_completed = stopped_;
    try {
        if (!stopped_) {
            shutdown_completed = static_cast<bool>(shutdown(0, 0).status);
        }
        if (run_recorder_ != nullptr && run_recorder_->terminalizable()) {
            const auto arguments = nlohmann::json{{"phase", "candidate_destructor"}};
            (void)record_mutation("destructor_incomplete", arguments.dump());
            shutdown_completed = static_cast<bool>(finalize_observed(
                config_.run_receipt_template_json, "incomplete", "destructor cleanup"));
        }
    } catch (...) {
        shutdown_completed = false;
    }
    registry_.reset();
    control_.reset();
    kernel_.reset();
    journal_.reset();
    if (shutdown_completed &&
        (run_recorder_ == nullptr ||
         run_recorder_->state() == RuntimeRunRecorderState::Finalized) &&
        owns_journal_path_ && !journal_path_.empty()) {
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
        (!admitted_execution_plan_sha256_.empty() &&
         config_.plan.plan_sha256 != admitted_execution_plan_sha256_) ||
        (!admitted_resolved_manifest_sha256_.empty() &&
         admitted_resolved_manifest_sha256_ != sealed_composition_.resolved_manifest_sha256) ||
        (admitted_execution_plan_sha256_.empty() &&
         config_.plan.plan_sha256 != sealed_composition_.resolved_manifest_sha256)) {
        return {.error = RuntimeHostError::InvalidArgument,
                .detail = "candidate is not bound to its admitted execution plan and sealed "
                          "resolved composition"};
    }
    const auto owner = host_.issue_owner_handle(
        control_, {
                      .transaction_kind = RuntimeHostTransactionKind::Initial,
                      .plan = config_.plan,
                      .world_slot_count = 1,
                  });
    if (!owner.valid()) {
        return {.error = RuntimeHostError::InvalidArgument,
                .detail = "P4-C candidate owner handle was not issued"};
    }
    const auto begun = host_.begin_candidate(
        {
            .transaction_kind = RuntimeHostTransactionKind::Initial,
            .plan = config_.plan,
            .lifecycle_deadline_tick = config_.lifecycle_deadline_tick,
            .world_slot_count = 1,
        },
        owner);
    if (!begun.status) {
        return begun.status;
    }
    const auto validated =
        host_.validate_candidate(begun.handle, {.static_plan_validated = true,
                                                .resources_ready = true,
                                                .shadow_probe_passed = true,
                                                .unreachable_from_production = true,
                                                .production_authorized = false});
    if (!validated) {
        return validated;
    }
    if (run_recorder_ != nullptr) {
        const auto lifecycle = run_recorder_->note_lifecycle("validation");
        if (!lifecycle) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B validation lifecycle evidence failed: " + lifecycle.detail};
        }
    }
    const auto published =
        host_.commit_initial(begun.handle, {.lifecycle_evidence_sha256 = valid_digest('b'),
                                            .dark_evidence_sealed = true,
                                            .production_authorized = false});
    if (!published.status) {
        return published.status;
    }
    incarnation_ = published.published_slot;
    if (run_recorder_ != nullptr) {
        const auto episode_ref = current_episode();
        if (!episode_ref.well_formed()) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B runtime identity lacks an active episode"};
        }
        const auto bound = run_recorder_->bind_runtime_identity(
            "boot-" + std::to_string(incarnation_.host.boot_id.high) + "-" +
                std::to_string(incarnation_.host.boot_id.low),
            std::to_string(incarnation_.incarnation_epoch),
            "world-" + std::to_string(episode_ref.world.world_slot),
            std::to_string(episode_ref.world.world_generation),
            "episode-" + std::to_string(episode_ref.episode_id.high) + "-" +
                std::to_string(episode_ref.episode_id.low),
            std::to_string(episode_ref.episode_generation), "request-" + config_.run_id);
        if (!bound) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B runtime identity binding failed: " + bound.detail};
        }
        const auto publication = run_recorder_->note_lifecycle("publication");
        if (!publication) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B publication lifecycle evidence failed: " + publication.detail};
        }
        const auto episode = run_recorder_->note_lifecycle("episode");
        if (!episode) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B episode lifecycle evidence failed: " + episode.detail};
        }
    }
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
    if (run_recorder_ != nullptr && run_recorder_->state() == RuntimeRunRecorderState::New) {
        const RuntimeRunRecorderStatus admission = run_recorder_->admit(config_.run_header_json);
        if (!admission) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = "P5-B durable run admission failed: " + admission.detail};
        }
    }
    if (run_recorder_ != nullptr && !run_recorder_->admitted()) {
        return {.error = RuntimeHostError::InvalidArgument,
                .detail = "P5-B recorder is not durably admitted"};
    }
    const auto initialized = initialize_candidate();
    if (!initialized && run_recorder_ != nullptr && run_recorder_->admitted()) {
        const auto rejection_arguments =
            nlohmann::json{{"error", initialized.detail}, {"phase", "candidate_initialization"}};
        if (!record_mutation("start_rejected", rejection_arguments.dump())) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail = initialized.detail + "; durable rejection evidence append failed"};
        }
        const auto finalized =
            finalize_observed(config_.run_receipt_template_json, "rejected", initialized.detail);
        if (!finalized) {
            return {.error = RuntimeHostError::InvalidArgument,
                    .detail =
                        initialized.detail + "; terminal receipt failed: " + finalized.detail};
        }
    }
    return initialized;
}

bool RuntimeKernelCandidate::record_mutation(std::string_view operation,
                                             std::string_view arguments_json) {
    if (run_recorder_ == nullptr) return true;
    if (!run_recorder_->admitted() || operation.empty()) return false;
    try {
        const auto arguments = nlohmann::json::parse(arguments_json.begin(), arguments_json.end());
        const auto payload = nlohmann::json{
            {"arguments", arguments},
            {"operation", operation},
            {"phase", "intent"}}.dump();
        return static_cast<bool>(run_recorder_->append(run_recorder_->next_sequence(), payload));
    } catch (const nlohmann::json::exception &) {
        return false;
    }
}

bool RuntimeKernelCandidate::record_outcome(std::string_view operation, bool success,
                                            std::string_view result_json) {
    if (run_recorder_ == nullptr) return true;
    if (!run_recorder_->admitted() || operation.empty()) return false;
    try {
        const auto result = nlohmann::json::parse(result_json.begin(), result_json.end());
        const auto payload = nlohmann::json{
            {"operation", operation},
            {"phase", "outcome"},
            {"result", result},
            {"success", success}}.dump();
        return static_cast<bool>(run_recorder_->append(run_recorder_->next_sequence(), payload));
    } catch (const nlohmann::json::exception &) {
        return false;
    }
}

void RuntimeKernelCandidate::terminalize_evidence_failure(std::string_view reason) noexcept {
    if (run_recorder_ == nullptr || !run_recorder_->terminalizable()) return;
    try {
        (void)finalize_observed(config_.run_receipt_template_json, "failed", reason);
    } catch (...) {
    }
}

RuntimeRunRecorderStatus
RuntimeKernelCandidate::finalize_observed(std::string_view receipt_template_json,
                                          std::string_view terminal_state,
                                          std::string_view terminal_reason) {
    if (run_recorder_ == nullptr)
        return {false, "recorder.absent", "candidate has no configured P5-B recorder"};
    const auto admitted_bindings = run_recorder_->admission_bindings_json();
    if (!admitted_bindings.empty()) {
        std::string observed_bindings;
        std::string detail;
        if (!collect_runtime_execution_bindings_json(
                config_.run_execution_sources, admitted_bindings, observed_bindings, detail) ||
            observed_bindings != admitted_bindings) {
            terminal_state = "failed";
            terminal_reason = "execution provenance changed after admission";
        }
    }
    return run_recorder_->finalize_observed(receipt_template_json, terminal_state, terminal_reason);
}

void RuntimeKernelCandidate::arm_terminal_receipt_for_test() noexcept {
    if (control_ != nullptr) {
        control_->arm_terminal_receipt_for_test();
    }
}

RuntimeShutdownResult RuntimeKernelCandidate::shutdown(std::uint64_t now_tick,
                                                       std::uint64_t deadline_tick) {
    if (stopped_) {
        if (run_recorder_ != nullptr && run_recorder_->terminalizable()) {
            const auto finalized =
                run_recorder_->state() == RuntimeRunRecorderState::Rejected
                    ? finalize_observed(config_.run_receipt_template_json, "failed",
                                        "durable evidence append failed")
                : started_ ? finalize_run(config_.run_receipt_template_json)
                           : finalize_observed(config_.run_receipt_template_json, "cancelled",
                                               "candidate closed before start");
            if (!finalized) {
                return {.status = {.error = RuntimeHostError::InvalidArgument,
                                   .detail = "P5-B terminal receipt failed: " + finalized.detail},
                        .state = RuntimeHostState::Stopped};
            }
        }
        return {.status = {}, .state = RuntimeHostState::Stopped};
    }
    // Evidence loss fail-stops further truth mutation, but it must never hold
    // resources alive.  A rejected recorder is reconciled later as
    // crashed/incomplete; shutdown still follows the host's terminal path.
    bool evidence_failed =
        run_recorder_ != nullptr && run_recorder_->state() == RuntimeRunRecorderState::Rejected;
    if (run_recorder_ != nullptr && run_recorder_->admitted() &&
        !run_recorder_->note_lifecycle("drain"))
        evidence_failed = true;
    if (run_recorder_ != nullptr && run_recorder_->admitted() && !record_mutation("shutdown"))
        evidence_failed = true;
    const auto result = host_.begin_shutdown(now_tick, deadline_tick);
    if (result.status && kernel_ != nullptr) {
        terminal_state_bytes_ = observed_state_bytes();
        terminal_state_sha256_ =
            terminal_state_bytes_.has_value()
                ? std::optional<std::string>(runtime_state_payload_sha256(*terminal_state_bytes_))
                : std::nullopt;
        kernel_->shutdown();
        stopped_ = true;
        if (run_recorder_ != nullptr && run_recorder_->admitted() &&
            !record_outcome(
                "shutdown", true,
                nlohmann::json{{"state_sha256", terminal_state_sha256_.value_or("")}}.dump()))
            evidence_failed = true;
        if (run_recorder_ != nullptr && run_recorder_->admitted() &&
            !run_recorder_->note_lifecycle("shutdown"))
            evidence_failed = true;
        registry_.reset();
        control_.reset();
        kernel_.reset();
        journal_.reset();
        if (run_recorder_ != nullptr && run_recorder_->admitted() &&
            !run_recorder_->note_lifecycle("reclamation"))
            evidence_failed = true;
        if (run_recorder_ != nullptr && run_recorder_->terminalizable()) {
            const auto finalized =
                evidence_failed || run_recorder_->state() == RuntimeRunRecorderState::Rejected
                    ? finalize_observed(config_.run_receipt_template_json, "failed",
                                        "durable evidence append failed")
                : started_ ? finalize_run(config_.run_receipt_template_json)
                           : finalize_observed(config_.run_receipt_template_json, "cancelled",
                                               "candidate closed before start");
            if (!finalized) {
                return {.status = {.error = RuntimeHostError::InvalidArgument,
                                   .detail = "P5-B terminal receipt failed: " + finalized.detail},
                        .state = RuntimeHostState::Stopped};
            }
        }
    } else if (run_recorder_ != nullptr && run_recorder_->admitted()) {
        (void)record_outcome("shutdown", false,
                             nlohmann::json{{"detail", result.status.detail}}.dump());
    }
    return result;
}

RuntimeRunRecorderStatus RuntimeKernelCandidate::finalize_run(std::string_view receipt_json) {
    if (run_recorder_ == nullptr) {
        return {false, "recorder.absent", "candidate has no configured P5-B recorder"};
    }
    if (!stopped_) {
        return {false, "recorder.lifecycle",
                "candidate must be stopped before receipt finalization"};
    }
    const auto state_sha256 =
        terminal_state_sha256_.has_value() ? terminal_state_sha256_ : observed_state_sha256();
    if (!state_sha256.has_value())
        return {false, "recorder.result", "candidate state could not be observed for finalization"};
    const auto state_bytes =
        terminal_state_bytes_.has_value() ? terminal_state_bytes_ : observed_state_bytes();
    if (!state_bytes.has_value())
        return {false, "recorder.result", "candidate state bytes could not be observed"};
    const std::string state_payload(reinterpret_cast<const char *>(state_bytes->data()),
                                    state_bytes->size());
    std::string artifact_digest;
    std::string retrieval_location;
    const auto artifact_status = run_recorder_->put_artifact(
        "runtime-state", state_payload, "application/vnd.echelon-forge.runtime-state.v1+octets",
        "run-retained", artifact_digest, retrieval_location);
    if (!artifact_status) return artifact_status;
    const auto result_status = run_recorder_->record_native_result(*state_sha256, *state_sha256);
    if (!result_status) return result_status;
    return finalize_observed(receipt_json, "completed", "completed");
}

RuntimeRunRecorderStatus
RuntimeKernelCandidate::persist_checkpoint(std::string_view checkpoint_json,
                                           std::string_view validation_json) {
    if (run_recorder_ == nullptr)
        return {false, "recorder.absent", "candidate has no configured P5-B recorder"};
    if (control_ == nullptr || !control_->begin_state_transfer())
        return {false, "recorder.checkpoint", "candidate state-transfer barrier is busy"};
    struct StateTransferGuard final {
        std::shared_ptr<Control> control;
        ~StateTransferGuard() {
            if (control != nullptr) control->end_state_transfer();
        }
    } state_transfer_guard{control_};
    (void)validation_json;
    const auto state_bytes = observed_state_bytes();
    if (!state_bytes.has_value())
        return {false, "recorder.checkpoint", "candidate state could not be observed"};
    const auto state_sha256 = runtime_state_payload_sha256(*state_bytes);
    try {
        auto checkpoint = nlohmann::json::parse(checkpoint_json.begin(), checkpoint_json.end());
        auto &payload = checkpoint.at("payload");
        payload["run_id"] = config_.run_id;
        payload["writer_generation"] = std::to_string(run_recorder_->fence_generation());
        payload["plan_sha256"] = config_.plan.plan_sha256;
        payload["host_boot_id"] = "boot-" + std::to_string(incarnation_.host.boot_id.high) + "-" +
                                  std::to_string(incarnation_.host.boot_id.low);
        payload["incarnation_epoch"] = std::to_string(incarnation_.incarnation_epoch);
        payload["aggregate_state_sha256"] = state_sha256;
        const auto episode = current_episode();
        if (!episode.well_formed())
            return {false, "recorder.checkpoint", "candidate lacks an active episode scope"};
        payload["world_fragments"] = nlohmann::json::array({nlohmann::json{
            {"episode_ids",
             nlohmann::json::array({"episode-" + std::to_string(episode.episode_id.high) + "-" +
                                    std::to_string(episode.episode_id.low)})},
            {"fragment_sequence", "0"},
            {"state_sha256", state_sha256},
            {"world_id", "world-" + std::to_string(episode.world.world_slot)}}});
        const auto admitted_bindings_json = run_recorder_->admission_bindings_json();
        if (admitted_bindings_json.empty())
            return {false, "recorder.checkpoint", "checkpoint lacks an admitted execution binding"};
        const auto admitted_bindings = nlohmann::json::parse(admitted_bindings_json);
        payload["release_id"] = admitted_bindings.at("release_binding").at("release_id");
        payload["decision_id"] = admitted_bindings.at("release_binding").at("rollout_decision_id");
        payload["target_reader_generation_min"] = admitted_bindings.at("reader_generation_min");
        payload["target_reader_generation_max"] = admitted_bindings.at("reader_generation_max");
        const auto canonical_payload =
            runtime::authority_contracts::canonical_authority_json(payload.dump());
        if (!canonical_payload.has_value())
            return {false, "recorder.checkpoint", "checkpoint payload is not canonicalizable"};
        checkpoint["payload_sha256"] = runtime::authority_contracts::authority_digest_sha256_hex(
            "runtime.state-checkpoint", "application/vnd.echelon-forge.state-checkpoint.v1+json",
            *canonical_payload);
        const auto canonical_checkpoint =
            runtime::authority_contracts::canonical_authority_json(checkpoint.dump());
        if (!canonical_checkpoint.has_value())
            return {false, "recorder.checkpoint", "checkpoint envelope is not canonicalizable"};
        const auto replay_sha256 =
            runtime::authority_contracts::checkpoint_replay_aggregate_sha256(payload.dump());
        if (!replay_sha256.has_value())
            return {false, "recorder.checkpoint", "checkpoint replay material is incomplete"};
        const auto validation = nlohmann::json{
            {"accepted", true},
            {"aggregate_replay_sha256", *replay_sha256},
            {"checkpoint_id", payload.at("checkpoint_id")},
            {"state_payload_hex", hex_encode_bytes(*state_bytes)},
            {"state_sha256", state_sha256},
            {"validator_id", "native-runtime-state"},
        };
        const auto canonical_validation =
            runtime::authority_contracts::canonical_authority_json(validation.dump());
        if (!canonical_validation.has_value())
            return {false, "recorder.checkpoint", "checkpoint validation is not canonicalizable"};
        return run_recorder_->persist_checkpoint(*canonical_checkpoint, *canonical_validation);
    } catch (const nlohmann::json::exception &error) {
        return {false, "recorder.checkpoint", error.what()};
    }
}

std::optional<std::string> RuntimeKernelCandidate::observed_state_sha256() const {
    const auto bytes = observed_state_bytes();
    return bytes.has_value() ? std::optional<std::string>(runtime_state_payload_sha256(*bytes))
                             : std::nullopt;
}

std::optional<std::vector<std::uint8_t>> RuntimeKernelCandidate::observed_state_bytes() const {
    if (kernel_ == nullptr) return std::nullopt;
    try {
        const auto serialized = SimulationKernelStateOwnerBridge::serialize_world(*kernel_);
        return std::vector<std::uint8_t>(serialized.begin(), serialized.end());
    } catch (...) {
        return std::nullopt;
    }
}

RuntimeHostSnapshot RuntimeKernelCandidate::host_snapshot() const {
    return host_.snapshot();
}

RuntimeIncarnationRef RuntimeKernelCandidate::incarnation() const noexcept {
    return incarnation_;
}

RuntimeWorldRef RuntimeKernelCandidate::world_ref() const noexcept {
    return {.incarnation = incarnation_, .world_slot = 0, .world_generation = world_generation_};
}

RuntimeEpisodeRef RuntimeKernelCandidate::episode_ref() noexcept {
    return current_episode();
}

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
           world.well_formed() && world == world_ref() && host_.snapshot().active.has_value() &&
           host_.snapshot().active->incarnation == incarnation_;
}

std::optional<RuntimeEntityRef> RuntimeKernelCandidate::entity_ref(std::uint64_t entity_id) const {
    if (entity_id == 0 || !validate_world(world_ref())) {
        return std::nullopt;
    }
    return RuntimeEntityRef{
        .world = world_ref(), .entity_id = entity_id, .entity_generation = next_entity_generation_};
}

bool RuntimeKernelCandidate::validate_entity(const RuntimeEntityRef &entity) const noexcept {
    return validate_world(entity.world) && entity.entity_id != 0 &&
           entity.entity_generation == next_entity_generation_;
}

std::optional<RuntimeEntityRef>
RuntimeKernelCandidate::spawn_unit(const RuntimeWorldRef &world, const WorldSpawnRequest &request) {
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
    const auto spawn_arguments = nlohmann::json{{"world_index", request.world_index},
                                                {"side", request.side},
                                                {"type_name", request.type_name},
                                                {"x", request.x},
                                                {"y", request.y},
                                                {"z", request.z},
                                                {"heading", request.heading},
                                                {"pitch", request.pitch},
                                                {"roll", request.roll},
                                                {"vx", request.vx},
                                                {"vy", request.vy},
                                                {"vz", request.vz}};
    if (!record_mutation("spawn_unit", spawn_arguments.dump())) {
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return std::nullopt;
    }
    try {
        const auto entity = kernel_->spawn_unit(
            request.side, request.type_name, request.x, request.y, request.z, request.heading,
            request.pitch, request.roll, request.vx, request.vy, request.vz);
        if (!entity.is_valid()) {
            const bool outcome_recorded = record_outcome(
                "spawn_unit", false, R"({"reason":"kernel returned invalid entity"})");
            if (!outcome_recorded)
                terminalize_evidence_failure("durable spawn failure outcome append failed");
            lease_admission.lease.settle();
            (void)host_.release_shadow_episode(episode_admission.capability);
            return std::nullopt;
        }
        const auto result = entity_ref(entity.id());
        const bool outcome_recorded = record_outcome(
            "spawn_unit", result.has_value(), nlohmann::json{{"entity_id", entity.id()}}.dump());
        if (!outcome_recorded)
            terminalize_evidence_failure("durable spawn outcome append failed after mutation");
        if (outcome_recorded && result.has_value()) {
            const auto observed =
                run_recorder_ == nullptr
                    ? RuntimeRunRecorderStatus{true, {}, {}}
                    : run_recorder_->observe_entity("entity-" + std::to_string(entity.id()),
                                                    std::to_string(result->entity_generation));
            if (!observed) {
                terminalize_evidence_failure("durable entity observation append failed");
                lease_admission.lease.settle();
                (void)host_.release_shadow_episode(episode_admission.capability);
                return std::nullopt;
            }
        }
        lease_admission.lease.settle();
        (void)host_.release_shadow_episode(episode_admission.capability);
        return outcome_recorded ? result : std::nullopt;
    } catch (...) {
        const bool outcome_recorded =
            record_outcome("spawn_unit", false, R"({"reason":"kernel exception"})");
        if (!outcome_recorded)
            terminalize_evidence_failure("durable spawn exception outcome append failed");
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
        !expected_episode.well_formed() || expected_episode.world != world_ref() ||
        !idempotency_key.well_formed() || payload_sha256.size() != 64) {
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
    const std::string_view operation =
        kind == RuntimeEpisodeIntentKind::Action ? "episode_action" : "episode_reset";
    const auto episode_arguments =
        nlohmann::json{{"world_host_high", expected_episode.world.incarnation.host.host_id.high},
                       {"world_host_low", expected_episode.world.incarnation.host.host_id.low},
                       {"world_slot", expected_episode.world.world_slot},
                       {"world_generation", expected_episode.world.world_generation},
                       {"episode_generation", expected_episode.episode_generation},
                       {"idempotency_high", idempotency_key.high},
                       {"idempotency_low", idempotency_key.low},
                       {"payload_sha256", payload_sha256},
                       {"expected_step_sequence", episode_step_sequence_}};
    if (!record_mutation(operation, episode_arguments.dump())) {
        (void)host_.release_shadow_episode(admission.capability);
        return false;
    }
    const auto transition = host_.submit_shadow_episode(
        admission.capability, {.kind = kind,
                               .expected_episode = expected_episode,
                               .expected_step_sequence = episode_step_sequence_,
                               .idempotency_key = idempotency_key,
                               .payload_sha256 = std::move(payload_sha256),
                               .production_authorized = false});
    auto outcome = nlohmann::json{{"detail", transition.status.detail}};
    if (transition.status) {
        outcome["resulting_step_sequence"] = transition.receipt.resulting_step_sequence;
        outcome["reset_applied"] = transition.receipt.reset_applied;
        outcome["terminal"] = transition.receipt.terminal;
        outcome["world_generation"] = transition.receipt.episode_after.world.world_generation;
        outcome["episode_generation"] = transition.receipt.episode_after.episode_generation;
    }
    const bool outcome_recorded =
        record_outcome(operation, static_cast<bool>(transition.status), outcome.dump());
    if (receipt != nullptr && transition.status && outcome_recorded) {
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
    if (!outcome_recorded)
        terminalize_evidence_failure("durable episode outcome append failed after transition");
    return static_cast<bool>(transition.status) && outcome_recorded;
}

bool RuntimeKernelCandidate::step(const RuntimeWorldRef &world) {
    if (!validate_world(world)) {
        return false;
    }
    const auto episode = current_episode();
    if (next_action_idempotency_sequence_ == std::numeric_limits<std::uint64_t>::max()) {
        return false;
    }
    const std::uint64_t idempotency_sequence = next_action_idempotency_sequence_;
    RuntimeEpisodeTransitionReceipt receipt{};
    const bool accepted = submit_episode(
        episode, RuntimeEpisodeIntentKind::Action,
        {.high = 0x4550432D53544550ULL, .low = idempotency_sequence}, valid_digest('c'), &receipt);
    if (accepted) ++next_action_idempotency_sequence_;
    return accepted;
}

bool RuntimeKernelCandidate::set_time_step(const RuntimeWorldRef &world, double dt) {
    if (!validate_world(world) || kernel_ == nullptr) {
        return false;
    }
    if (!record_mutation("set_time_step", nlohmann::json{{"dt", dt}}.dump())) return false;
    try {
        kernel_->set_time_step(dt);
        const bool outcome_recorded =
            record_outcome("set_time_step", true, nlohmann::json{{"dt", dt}}.dump());
        if (!outcome_recorded)
            terminalize_evidence_failure("durable time-step outcome append failed after mutation");
        return outcome_recorded;
    } catch (...) {
        const bool outcome_recorded =
            record_outcome("set_time_step", false, R"({"reason":"kernel exception"})");
        if (!outcome_recorded)
            terminalize_evidence_failure("durable time-step failure outcome append failed");
        return false;
    }
}

bool RuntimeKernelCandidate::try_get_entity_kinematics(const RuntimeEntityRef &entity,
                                                       WorldEntityKinematics *state) {
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

bool RuntimeKernelCandidate::try_set_entity_kinematics(const RuntimeEntityRef &entity,
                                                       const WorldEntityKinematics &state) {
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
    const auto kinematics_arguments =
        nlohmann::json{{"entity_id", entity.entity_id},
                       {"entity_generation", entity.entity_generation},
                       {"x", state.x},
                       {"y", state.y},
                       {"z", state.z},
                       {"vx", state.vx},
                       {"vy", state.vy},
                       {"vz", state.vz},
                       {"heading", state.heading},
                       {"pitch", state.pitch},
                       {"roll", state.roll}};
    if (!record_mutation("set_entity_kinematics", kinematics_arguments.dump())) {
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
    const bool outcome_recorded = record_outcome(
        "set_entity_kinematics", true,
        nlohmann::json{
            {"entity_id", entity.entity_id},
            {"state_sha256", runtime::authority_contracts::sha256_hex(kinematics_arguments.dump())}}
            .dump());
    if (!outcome_recorded)
        terminalize_evidence_failure("durable kinematics outcome append failed after mutation");
    lease_admission.lease.settle();
    (void)host_.release_shadow_episode(episode_admission.capability);
    return outcome_recorded;
}

} // namespace runtime::host::integration
