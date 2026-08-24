#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/facade/internal/world_batch_backend_provider.h"

#include <algorithm>
#include <bit>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

bool exact_double_equal(double lhs, double rhs) noexcept {
    return std::bit_cast<std::uint64_t>(lhs) == std::bit_cast<std::uint64_t>(rhs);
}

bool information_state_source_equal(const InformationStateSource &lhs,
                                    const InformationStateSource &rhs) noexcept {
    return lhs.information_state_layer == rhs.information_state_layer &&
           lhs.source_label == rhs.source_label && lhs.maintained_status == rhs.maintained_status &&
           lhs.observation_packet_ids == rhs.observation_packet_ids &&
           lhs.source_observation_versions == rhs.source_observation_versions &&
           lhs.diagnostics_reason == rhs.diagnostics_reason;
}

bool barrier_record_equal(const RuntimeWindowBarrierRecord &lhs,
                          const RuntimeWindowBarrierRecord &rhs) noexcept {
    return lhs.sequence == rhs.sequence && lhs.barrier_id == rhs.barrier_id &&
           lhs.node_id == rhs.node_id;
}

bool diagnostics_trace_equal(const DiagnosticsTrace &lhs, const DiagnosticsTrace &rhs) noexcept {
    return lhs.trace_id == rhs.trace_id && lhs.parent_trace_id == rhs.parent_trace_id &&
           lhs.chain_id == rhs.chain_id && lhs.track_id == rhs.track_id &&
           lhs.launch_request_id == rhs.launch_request_id &&
           lhs.launch_event_id == rhs.launch_event_id &&
           lhs.munition.world_index == rhs.munition.world_index &&
           lhs.munition.entity_id == rhs.munition.entity_id &&
           lhs.effects_event_id == rhs.effects_event_id &&
           lhs.damage_report_id == rhs.damage_report_id &&
           lhs.observation_packet_version == rhs.observation_packet_version &&
           lhs.source_snapshot_version == rhs.source_snapshot_version &&
           lhs.barrier_id == rhs.barrier_id && lhs.barrier_detail == rhs.barrier_detail &&
           exact_double_equal(lhs.source_time_s, rhs.source_time_s) &&
           lhs.source_node_id == rhs.source_node_id && lhs.export_node_id == rhs.export_node_id;
}

template <typename T, typename Equal>
bool vector_equal_by(const std::vector<T> &lhs, const std::vector<T> &rhs, Equal equal) noexcept {
    return lhs.size() == rhs.size() &&
           std::equal(lhs.begin(), lhs.end(), rhs.begin(), std::move(equal));
}

bool execution_source_snapshot_versions_equal(
    const std::vector<RuntimeWindowNodeExecutionRecord> &executed_nodes,
    const std::vector<std::string> &sealed_versions) noexcept {
    if (executed_nodes.size() != sealed_versions.size()) {
        return false;
    }
    for (std::size_t index = 0; index < executed_nodes.size(); ++index) {
        if (executed_nodes[index].source_snapshot_version != sealed_versions[index]) {
            return false;
        }
    }
    return true;
}

} // namespace

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : counterfactual_worldlines_(std::make_unique<CounterfactualWorldlineRegistry>()),
      identity_(std::make_shared<RuntimeFacadeIdentity>()) {
    runtime::backend_provider::WorldBatchBackendProviderMaterialization materialized =
        runtime::backend_provider::materialize_default_world_batch_backend(world_count);
    if (!materialized) {
        throw std::runtime_error(materialized.error.code + "@" + materialized.error.subject + ": " +
                                 materialized.error.detail);
    }
    identity_->backend_identity = std::move(materialized.identity);
    runtime_ = std::move(materialized.backend);
}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig &config) : RuntimeFacade(config.world_count) {
    configure_batch(config);
}

// I54-R: the move operations are user-defined (not defaulted) because the
// uint64 evidence cursors would otherwise be *copied* on move, letting a
// moved-from facade silently mint ids that duplicate (or, via move
// assignment, rewind) the destination's run. Each operation transfers every
// member of RuntimeFacade -- runtime_, counterfactual_worldlines_, identity_,
// next_run_snapshot_version_, next_trace_id_ -- and leaves the source's
// cursors at kInvalidatedEvidenceCursor so the producer methods fail fast.
// The tripwire below fires if the member set changes without this file
// being revisited.
static_assert(sizeof(RuntimeFacade) == 2 * sizeof(std::unique_ptr<IWorldBatchBackend>) +
                                           sizeof(std::shared_ptr<RuntimeFacadeIdentity>) +
                                           3 * sizeof(std::uint64_t),
              "RuntimeFacade member set changed: update the user-defined move constructor and "
              "move assignment in runtime_facade.cpp to transfer every member");

RuntimeFacade::RuntimeFacade(RuntimeFacade &&other) noexcept
    : runtime_(std::move(other.runtime_)),
      counterfactual_worldlines_(std::move(other.counterfactual_worldlines_)),
      identity_(std::move(other.identity_)),
      next_run_snapshot_version_(
          std::exchange(other.next_run_snapshot_version_, kInvalidatedEvidenceCursor)),
      next_trace_id_(std::exchange(other.next_trace_id_, kInvalidatedEvidenceCursor)),
      next_window_identity_(
          std::exchange(other.next_window_identity_, kInvalidatedEvidenceCursor)) {}

RuntimeFacade &RuntimeFacade::operator=(RuntimeFacade &&other) noexcept {
    if (this != &other) {
        runtime_ = std::move(other.runtime_);
        counterfactual_worldlines_ = std::move(other.counterfactual_worldlines_);
        identity_ = std::move(other.identity_);
        next_run_snapshot_version_ =
            std::exchange(other.next_run_snapshot_version_, kInvalidatedEvidenceCursor);
        next_trace_id_ = std::exchange(other.next_trace_id_, kInvalidatedEvidenceCursor);
        next_window_identity_ =
            std::exchange(other.next_window_identity_, kInvalidatedEvidenceCursor);
    }
    return *this;
}

RuntimeFacade::~RuntimeFacade() = default;

bool RuntimeFacade::runtime_window_result_belongs_to_this_facade(
    const RuntimeWindowResult &window_result) const noexcept {
    if (identity_ == nullptr || window_result.identity_token_.identity_ == nullptr) {
        return false;
    }
    const std::shared_ptr<const RuntimeWindowIdentity> &window_identity_token =
        window_result.identity_token_.identity_;
    const RuntimeWindowIdentity &window_identity = *window_identity_token;
    const std::shared_ptr<const RuntimeFacadeIdentity> facade_identity =
        window_identity.facade_identity.lock();
    if (facade_identity == nullptr || facade_identity.get() != identity_.get() ||
        window_identity.window_sequence == 0) {
        return false;
    }
    const auto it = identity_->recorded_window_sequences.find(window_identity.window_sequence);
    if (it == identity_->recorded_window_sequences.end()) {
        return false;
    }
    const std::shared_ptr<const RuntimeWindowIdentity> recorded = it->second.lock();
    return recorded != nullptr && recorded.get() == window_identity_token.get();
}

bool RuntimeFacade::runtime_window_result_evidence_matches_identity(
    const RuntimeWindowResult &window_result) const noexcept {
    if (!runtime_window_result_belongs_to_this_facade(window_result)) {
        return false;
    }
    const RuntimeWindowEvidenceSnapshot &sealed = window_result.identity_token_.identity_->evidence;
    return exact_double_equal(window_result.context.source_time_s, sealed.source_time_s) &&
           information_state_source_equal(window_result.observation_packet.provenance,
                                          sealed.observation_provenance) &&
           window_result.engagement_packet.trace_ids == sealed.engagement_trace_ids &&
           window_result.engagement_packet.producer_node_id == sealed.engagement_producer_node_id &&
           window_result.engagement_packet.barrier_detail == sealed.engagement_barrier_detail &&
           vector_equal_by(window_result.barrier_trace, sealed.barrier_trace,
                           barrier_record_equal) &&
           vector_equal_by(window_result.diagnostics_traces, sealed.diagnostics_traces,
                           diagnostics_trace_equal) &&
           execution_source_snapshot_versions_equal(window_result.executed_nodes,
                                                    sealed.execution_source_snapshot_versions);
}

RuntimeCompositionEvidenceComparison RuntimeFacade::runtime_window_composition_evidence_comparison(
    const RuntimeWindowResult &window_result) const {
    if (!runtime_window_result_belongs_to_this_facade(window_result)) {
        return {
            .compatible = false,
            .mismatches = {"window:composition_evidence_identity_unavailable"},
        };
    }

    const RuntimeCompositionEvidenceResult &sealed =
        window_result.identity_token_.identity_->composition_evidence;
    if (!sealed.available) {
        const std::string code = sealed.error_code.empty()
                                     ? "composition_evidence.commit_snapshot_unavailable"
                                     : sealed.error_code;
        return {
            .compatible = false,
            .mismatches = {"sealed:" + code},
        };
    }
    return compare_composition_evidence(sealed.evidence);
}

bool RuntimeFacade::runtime_window_trace_ids_recorded_by_this_window(
    const RuntimeWindowResult &window_result) const noexcept {
    if (!runtime_window_result_belongs_to_this_facade(window_result)) {
        return false;
    }
    const RuntimeWindowIdentity &window_identity = *window_result.identity_token_.identity_;
    const std::uint64_t sequence = window_identity.window_sequence;
    return std::all_of(
        window_identity.evidence.engagement_trace_ids.begin(),
        window_identity.evidence.engagement_trace_ids.end(), [&](std::uint64_t trace_id) {
            const auto it = identity_->recorded_trace_window_sequences.find(trace_id);
            if (it == identity_->recorded_trace_window_sequences.end()) {
                return false;
            }
            const std::shared_ptr<const RuntimeWindowIdentity> recorded = it->second.lock();
            return recorded != nullptr &&
                   recorded.get() == window_result.identity_token_.identity_.get() &&
                   recorded->window_sequence == sequence;
        });
}

bool RuntimeFacade::runtime_window_snapshot_recorded_by_this_window(
    const RuntimeWindowResult &window_result, std::uint64_t run_snapshot_version) const noexcept {
    if (!runtime_window_result_belongs_to_this_facade(window_result) || run_snapshot_version == 0) {
        return false;
    }
    const auto it = identity_->recorded_snapshot_window_sequences.find(run_snapshot_version);
    if (it == identity_->recorded_snapshot_window_sequences.end()) {
        return false;
    }
    const std::shared_ptr<const RuntimeWindowIdentity> recorded = it->second.lock();
    return recorded != nullptr && recorded.get() == window_result.identity_token_.identity_.get();
}

bool RuntimeFacade::runtime_window_parent_trace_recorded_before_this_window(
    const RuntimeWindowResult &window_result, std::uint64_t parent_trace_id) const noexcept {
    if (!runtime_window_result_belongs_to_this_facade(window_result) || parent_trace_id == 0) {
        return false;
    }
    const auto it = identity_->recorded_anchor_window_sequences.find(parent_trace_id);
    if (it == identity_->recorded_anchor_window_sequences.end()) {
        return false;
    }
    const std::shared_ptr<const RuntimeWindowIdentity> recorded = it->second.lock();
    if (recorded == nullptr) {
        return false;
    }
    const std::shared_ptr<const RuntimeFacadeIdentity> recorded_facade_identity =
        recorded->facade_identity.lock();
    return recorded_facade_identity != nullptr &&
           recorded_facade_identity.get() == identity_.get() &&
           recorded->window_sequence < window_result.identity_token_.identity_->window_sequence;
}
