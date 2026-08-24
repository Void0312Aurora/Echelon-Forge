#include "runtime/facade/runtime_facade_internal.h"

#include "runtime/facade/runtime_window_coordinator.h"

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace {

using namespace runtime_facade_internal;

constexpr std::string_view kRunSnapshotVersionPrefix = "snapshot:";

std::optional<std::uint64_t> parse_run_snapshot_version(std::string_view value) noexcept {
    if (!value.starts_with(kRunSnapshotVersionPrefix)) {
        return std::nullopt;
    }
    value.remove_prefix(kRunSnapshotVersionPrefix.size());
    if (value.empty()) {
        return std::nullopt;
    }
    std::uint64_t parsed = 0;
    const auto [end, error] = std::from_chars(value.data(), value.data() + value.size(), parsed);
    if (error != std::errc{} || end != value.data() + value.size() || parsed == 0) {
        return std::nullopt;
    }
    return parsed;
}

RuntimeWindowEvidenceSnapshot sealed_window_evidence(const RuntimeWindowResult &result) {
    RuntimeWindowEvidenceSnapshot sealed{};
    sealed.source_time_s = result.context.source_time_s;
    sealed.observation_provenance = result.observation_packet.provenance;
    sealed.engagement_trace_ids = result.engagement_packet.trace_ids;
    sealed.engagement_producer_node_id = result.engagement_packet.producer_node_id;
    sealed.engagement_barrier_detail = result.engagement_packet.barrier_detail;
    sealed.barrier_trace = result.barrier_trace;
    sealed.diagnostics_traces = result.diagnostics_traces;
    sealed.execution_source_snapshot_versions.reserve(result.executed_nodes.size());
    for (const auto &record : result.executed_nodes) {
        sealed.execution_source_snapshot_versions.push_back(record.source_snapshot_version);
    }
    return sealed;
}

std::string track_source_name(int source) {
    switch (source) {
    case 1:
        return "radar";
    case 2:
        return "rwr_esm";
    case 3:
        return "data_link";
    case 4:
        return "fused";
    case 5:
        return "sonar";
    case 0:
    default:
        return "none";
    }
}

std::string track_classification_name(int classification) {
    switch (classification) {
    case 1:
        return "friendly";
    case 2:
        return "hostile";
    case 3:
        return "neutral";
    case 0:
    default:
        return "unknown";
    }
}

std::string track_status_name(int status) {
    switch (status) {
    case 1:
        return "confirmed";
    case 2:
        return "coasted";
    case 0:
    default:
        return "tentative";
    }
}

int launch_event_priority(const LaunchEvent &) {
    return 10;
}

int effects_event_priority(const EffectsEvent &) {
    return 20;
}

int damage_report_priority(const DamageReport &) {
    return 30;
}

int diagnostics_trace_priority(const DiagnosticsTrace &) {
    return 40;
}

template <typename Event>
const std::string &ensure_manifest_node_id(Event &event, std::string Event::*field,
                                           std::string_view fallback_node_id) {
    auto &node_id = event.*field;
    if (node_id.empty() && find_stage_node_manifest(fallback_node_id) != nullptr) {
        node_id = std::string(fallback_node_id);
    }
    return node_id;
}

void stable_sort_track_packets(std::vector<TrackPacket> *tracks) {
    if (tracks == nullptr) {
        return;
    }
    std::stable_sort(tracks->begin(), tracks->end(),
                     [](const TrackPacket &lhs, const TrackPacket &rhs) {
                         if (lhs.source_time_s != rhs.source_time_s) {
                             return lhs.source_time_s < rhs.source_time_s;
                         }
                         if (lhs.update_age_s != rhs.update_age_s) {
                             return lhs.update_age_s < rhs.update_age_s;
                         }
                         return lhs.track_id < rhs.track_id;
                     });
}

void stable_sort_launch_events(std::vector<LaunchEvent> *events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(events->begin(), events->end(),
                     [](const LaunchEvent &lhs, const LaunchEvent &rhs) {
                         if (lhs.event_time_s != rhs.event_time_s) {
                             return lhs.event_time_s < rhs.event_time_s;
                         }
                         if (launch_event_priority(lhs) != launch_event_priority(rhs)) {
                             return launch_event_priority(lhs) < launch_event_priority(rhs);
                         }
                         return lhs.event_id < rhs.event_id;
                     });
}

void stable_sort_effects_events(std::vector<EffectsEvent> *events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(events->begin(), events->end(),
                     [](const EffectsEvent &lhs, const EffectsEvent &rhs) {
                         if (lhs.detonation_time_s != rhs.detonation_time_s) {
                             return lhs.detonation_time_s < rhs.detonation_time_s;
                         }
                         if (effects_event_priority(lhs) != effects_event_priority(rhs)) {
                             return effects_event_priority(lhs) < effects_event_priority(rhs);
                         }
                         return lhs.event_id < rhs.event_id;
                     });
}

void stable_sort_damage_reports(std::vector<DamageReport> *reports) {
    if (reports == nullptr) {
        return;
    }
    std::stable_sort(reports->begin(), reports->end(),
                     [](const DamageReport &lhs, const DamageReport &rhs) {
                         if (lhs.report_time_s != rhs.report_time_s) {
                             return lhs.report_time_s < rhs.report_time_s;
                         }
                         if (damage_report_priority(lhs) != damage_report_priority(rhs)) {
                             return damage_report_priority(lhs) < damage_report_priority(rhs);
                         }
                         return lhs.report_id < rhs.report_id;
                     });
}

void stable_sort_platform_consequence_events(std::vector<PlatformConsequenceEvent> *events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(events->begin(), events->end(),
                     [](const PlatformConsequenceEvent &lhs, const PlatformConsequenceEvent &rhs) {
                         if (lhs.header.source_time_s != rhs.header.source_time_s) {
                             return lhs.header.source_time_s < rhs.header.source_time_s;
                         }
                         return lhs.header.event_id < rhs.header.event_id;
                     });
}

template <typename EventT> void stable_sort_lethality_header_events(std::vector<EventT> *events) {
    if (events == nullptr) {
        return;
    }
    std::stable_sort(events->begin(), events->end(), [](const EventT &lhs, const EventT &rhs) {
        if (lhs.header.source_time_s != rhs.header.source_time_s) {
            return lhs.header.source_time_s < rhs.header.source_time_s;
        }
        return lhs.header.event_id < rhs.header.event_id;
    });
}

void stable_sort_diagnostics_traces(std::vector<DiagnosticsTrace> *traces) {
    if (traces == nullptr) {
        return;
    }
    std::stable_sort(traces->begin(), traces->end(),
                     [](const DiagnosticsTrace &lhs, const DiagnosticsTrace &rhs) {
                         if (lhs.source_time_s != rhs.source_time_s) {
                             return lhs.source_time_s < rhs.source_time_s;
                         }
                         if (diagnostics_trace_priority(lhs) != diagnostics_trace_priority(rhs)) {
                             return diagnostics_trace_priority(lhs) <
                                    diagnostics_trace_priority(rhs);
                         }
                         return lhs.trace_id < rhs.trace_id;
                     });
}

void apply_export_packet_metadata(EngagementEventPacket *packet, std::uint64_t snapshot_version,
                                  double source_time_s) {
    if (packet == nullptr) {
        return;
    }
    packet->snapshot_version = snapshot_version;
    packet->barrier_id = std::string(kExportBarrierId);
    packet->barrier_sequence = kExportBarrierSequence;
    packet->barrier_detail = std::string(kExportBarrierDetail);
    packet->source_time_s = source_time_s;
    if (find_stage_node_manifest(kObservationExportNodeId) != nullptr) {
        packet->producer_node_id = std::string(kObservationExportNodeId);
    }
    packet->packet_provenance.observation_packet_ids = {std::string(kEngagementPacketIdPrefix) +
                                                        std::to_string(snapshot_version)};
    packet->packet_provenance.source_observation_versions = {"track:" +
                                                             std::to_string(snapshot_version)};
    packet->diagnostics_provenance.observation_packet_ids = {
        std::string(kDiagnosticsPacketIdPrefix) + std::to_string(snapshot_version)};
    packet->diagnostics_provenance.source_observation_versions = {"diag:" +
                                                                  std::to_string(snapshot_version)};
    packet->diagnostics_provenance.diagnostics_reason =
        "diagnostics_trace_surface_not_maintained_decision_path";
}

void apply_export_trace_metadata(DiagnosticsTrace *trace, std::uint64_t snapshot_version,
                                 double source_time_s, std::string_view source_node_id) {
    if (trace == nullptr) {
        return;
    }
    trace->source_snapshot_version = snapshot_version;
    trace->barrier_id = std::string(kExportBarrierId);
    trace->barrier_detail = std::string(kExportBarrierDetail);
    trace->source_time_s = source_time_s;
    if (find_stage_node_manifest(source_node_id) != nullptr) {
        trace->source_node_id = std::string(source_node_id);
    }
    if (find_stage_node_manifest(kObservationExportNodeId) != nullptr) {
        trace->export_node_id = std::string(kObservationExportNodeId);
    }
}

void finalize_recent_event_metadata(EngagementEventPacket *packet) {
    if (packet == nullptr) {
        return;
    }
    for (auto &event : packet->launch_events) {
        ensure_manifest_node_id(event, &LaunchEvent::producer_node_id, kLaunchNodeId);
    }
    for (auto &event : packet->effects_events) {
        ensure_manifest_node_id(event, &EffectsEvent::producer_node_id, kEffectsDamageNodeId);
    }
    for (auto &report : packet->damage_reports) {
        ensure_manifest_node_id(report, &DamageReport::producer_node_id, kEffectsDamageNodeId);
    }
    for (auto &event : packet->platform_consequence_events) {
        if (event.header.producer_node_id.empty() &&
            find_stage_node_manifest(kEffectsDamageNodeId) != nullptr) {
            event.header.producer_node_id = std::string(kEffectsDamageNodeId);
        }
    }
}

void finalize_diagnostics_ancestry(EngagementEventPacket *packet) {
    if (packet == nullptr) {
        return;
    }
    for (auto &trace : packet->diagnostics_traces) {
        if (trace.launch_event_id != 0) {
            const auto match =
                std::find_if(packet->launch_events.begin(), packet->launch_events.end(),
                             [&trace](const LaunchEvent &event) {
                                 return event.event_id == trace.launch_event_id;
                             });
            if (match != packet->launch_events.end()) {
                apply_export_trace_metadata(
                    &trace, packet->snapshot_version, match->event_time_s,
                    match->producer_node_id.empty() ? kLaunchNodeId : match->producer_node_id);
                continue;
            }
        }
        if (trace.effects_event_id != 0) {
            const auto match =
                std::find_if(packet->effects_events.begin(), packet->effects_events.end(),
                             [&trace](const EffectsEvent &event) {
                                 return event.event_id == trace.effects_event_id;
                             });
            if (match != packet->effects_events.end()) {
                apply_export_trace_metadata(
                    &trace, packet->snapshot_version, match->detonation_time_s,
                    match->producer_node_id.empty() ? kEffectsDamageNodeId
                                                    : match->producer_node_id);
                continue;
            }
        }
        if (trace.damage_report_id != 0) {
            const auto match =
                std::find_if(packet->damage_reports.begin(), packet->damage_reports.end(),
                             [&trace](const DamageReport &report) {
                                 return report.report_id == trace.damage_report_id;
                             });
            if (match != packet->damage_reports.end()) {
                apply_export_trace_metadata(&trace, packet->snapshot_version, match->report_time_s,
                                            match->producer_node_id.empty()
                                                ? kEffectsDamageNodeId
                                                : match->producer_node_id);
                continue;
            }
        }
        apply_export_trace_metadata(
            &trace,
            trace.source_snapshot_version != 0 ? trace.source_snapshot_version
                                               : packet->snapshot_version,
            trace.source_time_s,
            trace.source_node_id.empty() ? kObservationExportNodeId : trace.source_node_id);
    }
}

void apply_observation_packet_provenance(ObservationBatchPacket *packet) {
    if (packet == nullptr) {
        return;
    }
    packet->provenance.information_state_layer =
        std::string(kPolicyInformationStateAgentObservation);
    packet->provenance.source_label = std::string(kPolicySourceLabelFacadeObservationPacket);
    packet->provenance.maintained_status = std::string(kPolicyMaintainedStatusMaintained);
    packet->provenance.observation_packet_ids = {std::string(kObservationPacketIdPrefix) +
                                                 std::to_string(packet->snapshot_version)};
    packet->provenance.source_observation_versions = {"global:" +
                                                      std::to_string(packet->snapshot_version)};
    packet->provenance.diagnostics_reason.clear();
}

void apply_tasking_packet_provenance(TaskingBatchPacket *packet) {
    if (packet == nullptr) {
        return;
    }
    packet->provenance.information_state_layer = std::string(kPolicyInformationStateDecisionBelief);
    packet->provenance.source_label = "facade_tasking_packet";
    packet->provenance.maintained_status = std::string(kPolicyMaintainedStatusAdapterProjection);
    packet->provenance.observation_packet_ids = {"tasking:" +
                                                 std::to_string(packet->snapshot_version)};
    packet->provenance.source_observation_versions = {"tasking:" +
                                                      std::to_string(packet->snapshot_version)};
    packet->provenance.diagnostics_reason =
        "command_tasking_read_export_split_from_observation_packet";
}

TrackPacket track_packet_from_observation_contact(const EngagementEntityRef &observer,
                                                  const TrackData &contact, double source_time_s,
                                                  std::uint64_t snapshot_version) {
    return TrackPacket{
        .track_id = contact.id,
        .correlated_entity =
            EngagementEntityRef{
                .world_index = observer.world_index,
                .entity_id = contact.id,
            },
        .has_correlated_entity = contact.id != 0,
        .correlation_policy = contact.id != 0 ? "entity_id" : "unresolved",
        .source = track_source_name(contact.source),
        .classification = track_classification_name(contact.classification),
        .status = track_status_name(contact.status),
        .quality = contact.quality,
        .confidence = contact.confidence,
        .usable = contact.usability > 0,
        .iff = contact.iff_known ? "known" : "unknown",
        .source_time_s = source_time_s,
        .update_age_s = contact.time_since_update,
        .snapshot_version = snapshot_version,
    };
}

DiagnosticsTrace diagnostics_trace_from_track_packet(std::uint64_t trace_id,
                                                     const TrackPacket &track,
                                                     std::uint64_t observation_packet_version) {
    return DiagnosticsTrace{
        .trace_id = trace_id,
        .parent_trace_id = 0,
        .chain_id = trace_id,
        .track_id = track.track_id,
        .observation_packet_version = observation_packet_version,
        .source_snapshot_version = track.snapshot_version,
        .barrier_id = std::string(kExportBarrierId),
        .barrier_detail = std::string(kExportBarrierDetail),
        .source_time_s = track.source_time_s,
        .source_node_id = std::string(kObservationExportNodeId),
        .export_node_id = std::string(kObservationExportNodeId),
    };
}

bool contains_world_index(const std::vector<std::uint64_t> &world_indices,
                          std::uint64_t world_index) {
    return std::find(world_indices.begin(), world_indices.end(), world_index) !=
           world_indices.end();
}

// Shared dedupe-and-accumulate walk behind both export_diagnostics_traces
// and export_engagement_event_packet below.
template <typename AccumulateFn>
void for_each_distinct_export_world_index(const IWorldBatchBackend &runtime,
                                          const std::vector<EngagementEntityRef> &refs,
                                          AccumulateFn &&accumulate) {
    std::vector<std::uint64_t> exported_world_indices;
    for (const auto &ref : refs) {
        if (!valid_runtime_world_index(runtime, ref.world_index)) {
            continue;
        }
        if (contains_world_index(exported_world_indices, ref.world_index)) {
            continue;
        }
        exported_world_indices.push_back(ref.world_index);
        accumulate(ref.world_index);
    }
}

// Shared valid-ref filter behind both export_diagnostics_traces and
// export_engagement_event_packet below.
std::vector<EngagementEntityRef>
filter_valid_world_refs(const IWorldBatchBackend &runtime,
                        const std::vector<EngagementEntityRef> &refs) {
    std::vector<EngagementEntityRef> valid_refs;
    valid_refs.reserve(refs.size());
    for (const auto &ref : refs) {
        if (valid_runtime_world_index(runtime, ref.world_index)) {
            valid_refs.push_back(ref);
        }
    }
    return valid_refs;
}

void assign_world_index(EngagementEntityRef &ref, std::uint64_t world_index) {
    if (ref.entity_id != 0) {
        ref.world_index = world_index;
    }
}

void assign_world_index(LethalityChainHeader &header, std::uint64_t world_index) {
    assign_world_index(header.munition, world_index);
    assign_world_index(header.shooter, world_index);
    assign_world_index(header.target, world_index);
}

RecentEngagementEvents with_world_index(RecentEngagementEvents recent, std::uint64_t world_index) {
    for (auto &event : recent.launch_events) {
        assign_world_index(event.spawned_munition, world_index);
    }
    for (auto &event : recent.effects_events) {
        assign_world_index(event.munition, world_index);
        assign_world_index(event.target, world_index);
    }
    for (auto &event : recent.nearest_approach_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.fuze_evaluation_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.warhead_mechanism_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.spatial_coverage_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.component_load_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.component_damage_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &report : recent.damage_reports) {
        assign_world_index(report.target, world_index);
    }
    for (auto &event : recent.platform_consequence_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.structural_breakup_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &event : recent.lifecycle_transition_events) {
        assign_world_index(event.header, world_index);
        assign_world_index(event.wreck_entity, world_index);
    }
    for (auto &event : recent.training_projection_events) {
        assign_world_index(event.header, world_index);
    }
    for (auto &trace : recent.diagnostics_traces) {
        assign_world_index(trace.munition, world_index);
    }
    return recent;
}

void append_recent_diagnostics_traces(std::vector<DiagnosticsTrace> &traces,
                                      const RecentEngagementEvents &recent) {
    for (const auto &trace : recent.diagnostics_traces) {
        DiagnosticsTrace copy = trace;
        std::uint64_t snapshot_version = copy.observation_packet_version;
        double source_time_s = copy.source_time_s;
        if (copy.launch_event_id != 0) {
            const auto match =
                std::find_if(recent.launch_events.begin(), recent.launch_events.end(),
                             [&copy](const LaunchEvent &event) {
                                 return event.event_id == copy.launch_event_id;
                             });
            if (match != recent.launch_events.end()) {
                source_time_s = match->event_time_s;
            }
            apply_export_trace_metadata(&copy, snapshot_version, source_time_s, kLaunchNodeId);
        } else if (copy.effects_event_id != 0 || copy.damage_report_id != 0) {
            const auto effects_match =
                std::find_if(recent.effects_events.begin(), recent.effects_events.end(),
                             [&copy](const EffectsEvent &event) {
                                 return event.event_id == copy.effects_event_id;
                             });
            const auto damage_match =
                std::find_if(recent.damage_reports.begin(), recent.damage_reports.end(),
                             [&copy](const DamageReport &report) {
                                 return report.report_id == copy.damage_report_id;
                             });
            if (effects_match != recent.effects_events.end()) {
                source_time_s = effects_match->detonation_time_s;
            } else if (damage_match != recent.damage_reports.end()) {
                source_time_s = damage_match->report_time_s;
            }
            apply_export_trace_metadata(&copy, snapshot_version, source_time_s,
                                        kEffectsDamageNodeId);
        } else {
            if (source_time_s == 0.0 && snapshot_version != 0) {
                source_time_s = static_cast<double>(snapshot_version - 1);
            }
            apply_export_trace_metadata(&copy, snapshot_version, source_time_s,
                                        kObservationExportNodeId);
        }
        traces.push_back(std::move(copy));
    }
}

void append_recent_engagement_events(EngagementEventPacket &packet,
                                     const RecentEngagementEvents &recent,
                                     const EngagementBatchRequest &request) {
    if (request.include_launch_events) {
        packet.launch_events.insert(packet.launch_events.end(), recent.launch_events.begin(),
                                    recent.launch_events.end());
    }
    if (request.include_effects_events) {
        packet.effects_events.insert(packet.effects_events.end(), recent.effects_events.begin(),
                                     recent.effects_events.end());
        packet.nearest_approach_events.insert(packet.nearest_approach_events.end(),
                                              recent.nearest_approach_events.begin(),
                                              recent.nearest_approach_events.end());
        packet.fuze_evaluation_events.insert(packet.fuze_evaluation_events.end(),
                                             recent.fuze_evaluation_events.begin(),
                                             recent.fuze_evaluation_events.end());
        packet.warhead_mechanism_events.insert(packet.warhead_mechanism_events.end(),
                                               recent.warhead_mechanism_events.begin(),
                                               recent.warhead_mechanism_events.end());
        packet.spatial_coverage_events.insert(packet.spatial_coverage_events.end(),
                                              recent.spatial_coverage_events.begin(),
                                              recent.spatial_coverage_events.end());
        packet.component_load_events.insert(packet.component_load_events.end(),
                                            recent.component_load_events.begin(),
                                            recent.component_load_events.end());
        packet.component_damage_events.insert(packet.component_damage_events.end(),
                                              recent.component_damage_events.begin(),
                                              recent.component_damage_events.end());
        packet.structural_breakup_events.insert(packet.structural_breakup_events.end(),
                                                recent.structural_breakup_events.begin(),
                                                recent.structural_breakup_events.end());
        packet.lifecycle_transition_events.insert(packet.lifecycle_transition_events.end(),
                                                  recent.lifecycle_transition_events.begin(),
                                                  recent.lifecycle_transition_events.end());
    }
    if (request.include_damage_reports) {
        packet.damage_reports.insert(packet.damage_reports.end(), recent.damage_reports.begin(),
                                     recent.damage_reports.end());
        packet.platform_consequence_events.insert(packet.platform_consequence_events.end(),
                                                  recent.platform_consequence_events.begin(),
                                                  recent.platform_consequence_events.end());
    }
    if (request.include_diagnostics_traces) {
        append_recent_diagnostics_traces(packet.diagnostics_traces, recent);
    }
}

std::uint64_t next_snapshot_version(std::size_t index) {
    return static_cast<std::uint64_t>(index + 1);
}

double resolve_observation_source_time(const std::vector<AgentObservation> &observations,
                                       std::size_t fallback_count) {
    if (observations.empty()) {
        return fallback_count == 0 ? 0.0 : static_cast<double>(fallback_count - 1);
    }

    double latest = 0.0;
    for (const auto &observation : observations) {
        latest = std::max(latest, observation.sim_time);
    }
    return latest;
}

double resolve_engagement_source_time(const EngagementEventPacket &packet) {
    double latest = 0.0;
    for (const auto &track : packet.track_packets) {
        latest = std::max(latest, track.source_time_s);
    }
    for (const auto &event : packet.launch_events) {
        latest = std::max(latest, event.event_time_s);
    }
    for (const auto &event : packet.effects_events) {
        latest = std::max(latest, event.detonation_time_s);
    }
    for (const auto &event : packet.nearest_approach_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.fuze_evaluation_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.warhead_mechanism_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.spatial_coverage_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.component_load_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.component_damage_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.structural_breakup_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &event : packet.lifecycle_transition_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &report : packet.damage_reports) {
        latest = std::max(latest, report.report_time_s);
    }
    for (const auto &event : packet.platform_consequence_events) {
        latest = std::max(latest, event.header.source_time_s);
    }
    for (const auto &trace : packet.diagnostics_traces) {
        latest = std::max(latest, trace.source_time_s);
    }
    if (latest == 0.0 && !packet.refs.empty()) {
        return static_cast<double>(packet.refs.size() - 1);
    }
    return latest;
}

std::uint64_t resolve_engagement_snapshot_version(const EngagementEventPacket &packet) {
    std::uint64_t latest = 0;
    for (const auto &track : packet.track_packets) {
        latest = std::max(latest, track.snapshot_version);
    }
    for (const auto &trace : packet.diagnostics_traces) {
        latest = std::max(latest, trace.observation_packet_version);
        latest = std::max(latest, trace.source_snapshot_version);
    }
    if (latest == 0 && !packet.refs.empty()) {
        return next_snapshot_version(packet.refs.size() - 1);
    }
    return latest;
}

void stable_sort_engagement_packet(EngagementEventPacket *packet) {
    if (packet == nullptr) {
        return;
    }
    stable_sort_track_packets(&packet->track_packets);
    stable_sort_launch_events(&packet->launch_events);
    stable_sort_effects_events(&packet->effects_events);
    stable_sort_lethality_header_events(&packet->nearest_approach_events);
    stable_sort_lethality_header_events(&packet->fuze_evaluation_events);
    stable_sort_lethality_header_events(&packet->warhead_mechanism_events);
    stable_sort_lethality_header_events(&packet->spatial_coverage_events);
    stable_sort_lethality_header_events(&packet->component_load_events);
    stable_sort_lethality_header_events(&packet->component_damage_events);
    stable_sort_lethality_header_events(&packet->structural_breakup_events);
    stable_sort_lethality_header_events(&packet->lifecycle_transition_events);
    stable_sort_damage_reports(&packet->damage_reports);
    stable_sort_platform_consequence_events(&packet->platform_consequence_events);
    stable_sort_diagnostics_traces(&packet->diagnostics_traces);
}

} // namespace

RecentEngagementEvents
RuntimeFacade::export_recent_engagement_events_for_world(std::size_t world_index) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .world_index = world_index,
            .include_recent_engagement_events = true,
        })
        .recent_engagement_events;
}

ObservationBatchPacket
RuntimeFacade::export_observation_packet(const std::vector<WorldEntityRef> &refs) const {
    return build_observation_packet(ObservationBatchRequest{
        .refs = refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
    });
}

ObservationBatchPacket
RuntimeFacade::export_observation_packet(const ObservationBatchRequest &request) const {
    return build_observation_packet(request);
}

TaskingBatchPacket RuntimeFacade::export_tasking_packet(const TaskingBatchRequest &request) const {
    return build_tasking_packet(request);
}

std::vector<DiagnosticsTrace>
RuntimeFacade::export_diagnostics_traces(const EngagementBatchRequest &request) const {
    std::vector<DiagnosticsTrace> traces;

    for_each_distinct_export_world_index(*runtime_, request.refs, [&](std::uint64_t world_index) {
        append_recent_diagnostics_traces(
            traces, with_world_index(export_recent_engagement_events_for_world(
                                         static_cast<std::size_t>(world_index)),
                                     world_index));
    });

    const bool needs_observations =
        request.include_track_packets || request.include_diagnostics_traces;
    if (!needs_observations || request.refs.empty() || request.trace_ids.empty()) {
        return traces;
    }

    const std::vector<EngagementEntityRef> valid_refs =
        filter_valid_world_refs(*runtime_, request.refs);
    if (valid_refs.empty()) {
        return traces;
    }

    const std::vector<WorldEntityRef> observation_refs =
        world_refs_from_engagement_refs(valid_refs);
    const auto observations = runtime_
                                  ->export_state(runtime::backend::ExportRequest{
                                      .refs = observation_refs,
                                      .include_agent_observations = true,
                                  })
                                  .agent_observations;

    std::uint64_t next_snapshot_version = 1;
    for (std::size_t ref_index = 0; ref_index < valid_refs.size(); ++ref_index) {
        const auto &ref = valid_refs[ref_index];
        const auto &observation = observations[ref_index];
        const std::uint64_t snapshot_version = next_snapshot_version++;
        for (const auto &contact : observation.contacts) {
            const auto trace_id = request.trace_ids[traces.size() % request.trace_ids.size()];
            traces.push_back(diagnostics_trace_from_track_packet(
                trace_id,
                track_packet_from_observation_contact(ref, contact, observation.sim_time,
                                                      snapshot_version),
                snapshot_version));
        }
    }
    stable_sort_diagnostics_traces(&traces);
    return traces;
}

RuntimeWindowResult RuntimeFacade::run_window(const RuntimeWindowRequest &request) {
    if (identity_ != nullptr) {
        identity_->prune_expired_window_identity_registries();
    }

    RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
            .apply_pilot_actions =
                [this](const std::vector<WorldPilotActionAssignment> &assignments) {
                    set_pilot_actions_batch(assignments);
                },
            .apply_mission_commands =
                [this](const std::vector<WorldMissionCommandMaintainedAssignment> &assignments) {
                    set_mission_commands_maintained_batch(assignments);
                },
            .step_window = [this]() { step_batch(); },
            .export_observation_packet =
                [this](const ObservationBatchRequest &observation_request) {
                    return export_observation_packet(observation_request);
                },
            .export_engagement_event_packet =
                [this](const EngagementBatchRequest &engagement_request) {
                    return export_engagement_event_packet(engagement_request);
                },
            .export_diagnostics_traces =
                [this](const EngagementBatchRequest &engagement_request) {
                    return export_diagnostics_traces(engagement_request);
                },
        });

    // The identity is intentionally attached only at the public facade seam,
    // after the coordinator has produced the result.  Synthetic results made
    // through the binding have no identity, and a result from another facade
    // carries a different shared identity object even when its numeric trace
    // ids overlap this run.
    if (identity_ == nullptr || next_window_identity_ == kInvalidatedEvidenceCursor) {
        return result;
    }
    const std::uint64_t window_sequence = next_window_identity_++;
    RuntimeWindowEvidenceSnapshot sealed = sealed_window_evidence(result);
    RuntimeCompositionEvidenceResult composition_evidence = export_composition_evidence();
    const std::shared_ptr<const RuntimeWindowIdentity> window_identity =
        std::make_shared<RuntimeWindowIdentity>(RuntimeWindowIdentity{
            .facade_identity = identity_,
            .window_sequence = window_sequence,
            .evidence = std::move(sealed),
            .composition_evidence = std::move(composition_evidence),
        });
    identity_->recorded_window_sequences.try_emplace(window_sequence, window_identity);

    for (const std::uint64_t trace_id : window_identity->evidence.engagement_trace_ids) {
        if (trace_id >= 1U && trace_id < next_trace_id_) {
            identity_->recorded_trace_window_sequences.try_emplace(trace_id, window_identity);
        }
    }
    if (!window_identity->evidence.engagement_trace_ids.empty()) {
        const std::uint64_t anchor_trace_id = window_identity->evidence.engagement_trace_ids.back();
        const auto trace_it = identity_->recorded_trace_window_sequences.find(anchor_trace_id);
        const std::shared_ptr<const RuntimeWindowIdentity> recorded_trace =
            trace_it == identity_->recorded_trace_window_sequences.end() ? nullptr
                                                                         : trace_it->second.lock();
        if (recorded_trace != nullptr && recorded_trace.get() == window_identity.get()) {
            identity_->recorded_anchor_window_sequences.try_emplace(anchor_trace_id,
                                                                    window_identity);
        }
    }

    for (const std::string &source_version :
         window_identity->evidence.execution_source_snapshot_versions) {
        const std::optional<std::uint64_t> parsed = parse_run_snapshot_version(source_version);
        if (parsed.has_value() && *parsed < next_run_snapshot_version_) {
            identity_->recorded_snapshot_window_sequences.try_emplace(*parsed, window_identity);
        }
    }

    identity_->retain_recent_window_identity(window_identity);
    result.identity_token_.identity_ = window_identity;
    return result;
}

EngagementEventPacket
RuntimeFacade::export_engagement_event_packet(const EngagementBatchRequest &request) const {
    EngagementEventPacket packet{};
    packet.refs = request.refs;
    packet.trace_ids = request.trace_ids;
    packet.barrier_id = std::string(kExportBarrierId);
    packet.barrier_sequence = kExportBarrierSequence;
    packet.barrier_detail = std::string(kExportBarrierDetail);

    for_each_distinct_export_world_index(*runtime_, request.refs, [&](std::uint64_t world_index) {
        append_recent_engagement_events(packet,
                                        with_world_index(export_recent_engagement_events_for_world(
                                                             static_cast<std::size_t>(world_index)),
                                                         world_index),
                                        request);
    });

    const bool needs_observations =
        request.include_track_packets || request.include_diagnostics_traces;
    if (!needs_observations || request.refs.empty()) {
        finalize_recent_event_metadata(&packet);
        stable_sort_engagement_packet(&packet);
        apply_export_packet_metadata(&packet, resolve_engagement_snapshot_version(packet),
                                     resolve_engagement_source_time(packet));
        finalize_diagnostics_ancestry(&packet);
        stable_sort_diagnostics_traces(&packet.diagnostics_traces);
        return packet;
    }

    const std::vector<EngagementEntityRef> valid_refs =
        filter_valid_world_refs(*runtime_, request.refs);
    if (valid_refs.empty()) {
        apply_export_packet_metadata(&packet, resolve_engagement_snapshot_version(packet),
                                     resolve_engagement_source_time(packet));
        return packet;
    }

    const std::vector<WorldEntityRef> observation_refs =
        world_refs_from_engagement_refs(valid_refs);
    const auto observations = runtime_
                                  ->export_state(runtime::backend::ExportRequest{
                                      .refs = observation_refs,
                                      .include_agent_observations = true,
                                  })
                                  .agent_observations;

    std::size_t observation_trace_index = packet.diagnostics_traces.size();
    std::uint64_t next_snapshot_version = 1;
    for (std::size_t ref_index = 0; ref_index < valid_refs.size(); ++ref_index) {
        const auto &ref = valid_refs[ref_index];
        const auto &observation = observations[ref_index];
        const std::uint64_t snapshot_version = next_snapshot_version++;
        for (const auto &contact : observation.contacts) {
            if (request.include_track_packets) {
                packet.track_packets.push_back(track_packet_from_observation_contact(
                    ref, contact, observation.sim_time, snapshot_version));
            }
            if (request.include_diagnostics_traces && !request.trace_ids.empty()) {
                const auto trace_id =
                    request.trace_ids[observation_trace_index % request.trace_ids.size()];
                packet.diagnostics_traces.push_back(diagnostics_trace_from_track_packet(
                    trace_id,
                    track_packet_from_observation_contact(ref, contact, observation.sim_time,
                                                          snapshot_version),
                    snapshot_version));
                ++observation_trace_index;
            }
        }
    }
    stable_sort_engagement_packet(&packet);
    apply_export_packet_metadata(&packet, resolve_engagement_snapshot_version(packet),
                                 resolve_engagement_source_time(packet));
    finalize_recent_event_metadata(&packet);
    finalize_diagnostics_ancestry(&packet);
    stable_sort_diagnostics_traces(&packet.diagnostics_traces);
    return packet;
}

ObservationBatchPacket
RuntimeFacade::build_observation_packet(const ObservationBatchRequest &request) const {
    ObservationBatchPacket packet{};
    packet.refs = request.refs;
    packet.barrier_id = "export";

    if (request.refs.empty()) {
        apply_observation_packet_provenance(&packet);
        return packet;
    }

    runtime::backend::ExportRequest export_request{
        .refs = request.refs,
        .include_agent_observations = request.include_agent_observations,
        .include_instrument_states = request.include_instrument_states,
    };
    runtime::backend::ExportResult exported = runtime_->export_state(export_request);
    packet.agent_observations = std::move(exported.agent_observations);
    packet.instrument_states = std::move(exported.instrument_states);
    packet.snapshot_version = next_snapshot_version(packet.refs.size() - 1);
    packet.source_time_s =
        resolve_observation_source_time(packet.agent_observations, packet.refs.size());
    apply_observation_packet_provenance(&packet);
    return packet;
}

TaskingBatchPacket RuntimeFacade::build_tasking_packet(const TaskingBatchRequest &request) const {
    TaskingBatchPacket packet{};
    packet.refs = request.refs;
    packet.barrier_id = "tasking_export";

    if (request.refs.empty()) {
        apply_tasking_packet_provenance(&packet);
        return packet;
    }

    runtime::backend::ExportResult exported =
        runtime_->export_state(runtime::backend::ExportRequest{
            .refs = request.refs,
            .include_mission_commands = request.include_mission_command_contracts,
            .include_task_orders = request.include_task_order_contracts,
            .include_leader_intents = request.include_leader_intent_contracts,
            .include_pilot_reports = request.include_pilot_report_contracts,
        });
    packet.mission_command_contracts = std::move(exported.mission_commands);
    packet.task_order_contracts = std::move(exported.task_orders);
    packet.leader_intent_contracts = std::move(exported.leader_intents);
    packet.pilot_report_contracts = std::move(exported.pilot_reports);
    packet.snapshot_version = next_snapshot_version(packet.refs.size() - 1);
    packet.source_time_s = packet.refs.empty() ? 0.0 : static_cast<double>(packet.refs.size() - 1);
    apply_tasking_packet_provenance(&packet);
    return packet;
}
