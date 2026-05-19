#include "runtime/facade/runtime_facade.h"

#include "core/engine/world_batch_runtime.h"

#include <algorithm>

namespace {

std::vector<WorldEntityRef> refs_from_step_requests(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) {
    std::vector<WorldEntityRef> refs;
    refs.reserve(requests.size());
    for (const auto& request : requests) {
        refs.push_back(WorldEntityRef{
            .world_index = request.world_index,
            .entity_id = request.entity_id,
        });
    }
    return refs;
}

std::vector<WorldEntityRef> world_refs_from_engagement_refs(
    const std::vector<EngagementEntityRef>& refs
) {
    std::vector<WorldEntityRef> out;
    out.reserve(refs.size());
    for (const auto& ref : refs) {
        out.push_back(WorldEntityRef{
            .world_index = ref.world_index,
            .entity_id = ref.entity_id,
        });
    }
    return out;
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

TrackPacket track_packet_from_observation_contact(
    const EngagementEntityRef& observer,
    const TrackData& contact,
    double source_time_s,
    std::uint64_t snapshot_version
) {
    return TrackPacket{
        .track_id = contact.id,
        .correlated_entity = EngagementEntityRef{
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

DiagnosticsTrace diagnostics_trace_from_track_packet(
    std::uint64_t trace_id,
    const TrackPacket& track,
    std::uint64_t observation_packet_version
) {
    return DiagnosticsTrace{
        .trace_id = trace_id,
        .parent_trace_id = 0,
        .chain_id = trace_id,
        .track_id = track.track_id,
        .observation_packet_version = observation_packet_version,
    };
}

bool contains_world_index(const std::vector<std::uint64_t>& world_indices, std::uint64_t world_index) {
    return std::find(world_indices.begin(), world_indices.end(), world_index) != world_indices.end();
}

void assign_world_index(EngagementEntityRef& ref, std::uint64_t world_index) {
    if (ref.entity_id != 0) {
        ref.world_index = world_index;
    }
}

RecentEngagementEvents with_world_index(
    RecentEngagementEvents recent,
    std::uint64_t world_index
) {
    for (auto& event : recent.launch_events) {
        assign_world_index(event.spawned_munition, world_index);
    }
    for (auto& event : recent.effects_events) {
        assign_world_index(event.munition, world_index);
        assign_world_index(event.target, world_index);
    }
    for (auto& report : recent.damage_reports) {
        assign_world_index(report.target, world_index);
    }
    for (auto& trace : recent.diagnostics_traces) {
        assign_world_index(trace.munition, world_index);
    }
    return recent;
}

void append_recent_engagement_events(
    EngagementEventPacket& packet,
    const RecentEngagementEvents& recent,
    const EngagementBatchRequest& request
) {
    if (request.include_launch_events) {
        packet.launch_events.insert(
            packet.launch_events.end(),
            recent.launch_events.begin(),
            recent.launch_events.end()
        );
    }
    if (request.include_effects_events) {
        packet.effects_events.insert(
            packet.effects_events.end(),
            recent.effects_events.begin(),
            recent.effects_events.end()
        );
    }
    if (request.include_damage_reports) {
        packet.damage_reports.insert(
            packet.damage_reports.end(),
            recent.damage_reports.begin(),
            recent.damage_reports.end()
        );
    }
    if (request.include_diagnostics_traces) {
        packet.diagnostics_traces.insert(
            packet.diagnostics_traces.end(),
            recent.diagnostics_traces.begin(),
            recent.diagnostics_traces.end()
        );
    }
}

ObservationBatchRequest observation_request_from_step_request(
    const ExecutionBatchStepRequest& request
) {
    return ObservationBatchRequest{
        .refs = refs_from_step_requests(request.step_requests),
        .include_agent_observations = request.include_agent_observations,
        .include_instrument_states = request.include_instrument_states,
        .include_mission_commands = request.include_mission_commands,
        .include_task_orders = request.include_task_orders,
        .include_leader_intents = request.include_leader_intents,
        .include_pilot_reports = request.include_pilot_reports,
    };
}

}  // namespace

RuntimeFacade::RuntimeFacade(std::size_t world_count)
    : runtime_(std::make_unique<WorldBatchRuntime>(world_count)) {}

RuntimeFacade::RuntimeFacade(const RuntimeBatchConfig& config)
    : runtime_(std::make_unique<WorldBatchRuntime>(config.world_count)) {
    configure_batch(config);
}

RuntimeFacade::RuntimeFacade(RuntimeFacade&&) noexcept = default;

RuntimeFacade& RuntimeFacade::operator=(RuntimeFacade&&) noexcept = default;

RuntimeFacade::~RuntimeFacade() = default;

void RuntimeFacade::configure_batch(const RuntimeBatchConfig& config) {
    runtime_->resize(config.world_count);
    runtime_->set_worker_threads(config.worker_threads);
}

RuntimeBatchConfig RuntimeFacade::batch_config() const noexcept {
    return RuntimeBatchConfig{
        .world_count = runtime_->world_count(),
        .worker_threads = runtime_->worker_threads(),
    };
}

RuntimeCapabilities RuntimeFacade::capabilities() const noexcept {
    return RuntimeCapabilities{
        .supports_batch_runtime = runtime_ != nullptr,
        .supports_compiled_episode_controller = true,
        .supports_compiled_execution_step = true,
        .supports_gpu_visual = false,
        .supports_gpu_observation = false,
        .supports_gpu_flight_shaping = false,
        .supports_device_observation_view = false,
        .supports_resident_state = false,
        .supports_exact_gpu_backend = false,
        .supports_shadow_compare = false,
    };
}

std::size_t RuntimeFacade::world_count() const noexcept {
    return runtime_->world_count();
}

void RuntimeFacade::resize(std::size_t world_count) {
    runtime_->resize(world_count);
}

void RuntimeFacade::set_worker_threads(std::size_t worker_threads) noexcept {
    runtime_->set_worker_threads(worker_threads);
}

std::size_t RuntimeFacade::worker_threads() const noexcept {
    return runtime_->worker_threads();
}

std::size_t RuntimeFacade::effective_worker_threads() const noexcept {
    return runtime_->effective_worker_threads();
}

WorldBatchRuntime& RuntimeFacade::runtime() noexcept {
    return *runtime_;
}

const WorldBatchRuntime& RuntimeFacade::runtime() const noexcept {
    return *runtime_;
}

bool RuntimeFacade::load_database(const std::string& path) {
    return runtime_->load_database(path);
}

bool RuntimeFacade::load_unit_definitions(const std::string& path, std::string* error) {
    return runtime_->load_unit_definitions(path, error);
}

void RuntimeFacade::reset_batch(const BatchResetRequest& request) {
    runtime_->reset_batch(request.seeds);
}

std::vector<uint64_t> RuntimeFacade::apply_world_setup_batch(
    const std::vector<uint32_t>& seeds,
    const std::vector<WorldTerrainAssignment>& terrain_assignments,
    const std::vector<WorldWindAssignment>& wind_assignments,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<WorldSpawnRequest>& requests,
    const std::vector<double>& time_steps
) {
    return runtime_->apply_world_setup_batch(
        seeds,
        terrain_assignments,
        wind_assignments,
        zones,
        requests,
        time_steps
    );
}

BatchWorldSetupResult RuntimeFacade::apply_world_setup(const BatchWorldSetupRequest& request) {
    BatchWorldSetupResult result{};
    result.entity_ids = runtime_->apply_world_setup_batch(
        request.seeds,
        request.terrain_assignments,
        request.wind_assignments,
        request.zones,
        request.spawn_requests,
        request.time_steps
    );
    return result;
}

void RuntimeFacade::set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments) {
    runtime_->set_pilot_actions_batch(assignments);
}

void RuntimeFacade::set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment>& assignments) {
    runtime_->set_mission_commands_batch(assignments);
}

void RuntimeFacade::set_task_orders_batch(const std::vector<WorldTaskOrderAssignment>& assignments) {
    runtime_->set_task_orders_batch(assignments);
}

void RuntimeFacade::set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment>& assignments) {
    runtime_->set_leader_intents_batch(assignments);
}

void RuntimeFacade::set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment>& assignments) {
    runtime_->set_pilot_reports_batch(assignments);
}

void RuntimeFacade::step_batch() {
    runtime_->step_batch();
}

void RuntimeFacade::clear_execution_episode_batch() noexcept {
    runtime_->clear_execution_episode_controller_batch();
}

void RuntimeFacade::prime_execution_episode_batch(
    const std::vector<WorldEntityRef>& refs,
    const std::vector<ExecutionEpisodeState>& states
) {
    runtime_->prime_execution_episode_controller_batch(refs, states);
}

bool RuntimeFacade::execution_episode_ready(std::size_t world_index) const noexcept {
    return runtime_->execution_episode_controller_ready(world_index);
}

std::vector<ExecutionEpisodeState> RuntimeFacade::export_execution_episode_states(
    const std::vector<WorldEntityRef>& refs
) const {
    return runtime_->export_execution_episode_states_batch(refs);
}

std::vector<ExecutionEpisodeRuntimeProducts> RuntimeFacade::evaluate_execution_batch(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) const {
    return runtime_->evaluate_execution_episode_batch(requests);
}

std::vector<ExecutionEpisodeRuntimeProducts> RuntimeFacade::step_execution_products_batch(
    const std::vector<WorldExecutionEpisodeStepRequest>& requests
) {
    return runtime_->step_execution_episode_batch(requests);
}

ExecutionBatchStepResult RuntimeFacade::step_execution_batch(const ExecutionBatchStepRequest& request) {
    ExecutionBatchStepResult result{};
    result.step_results = runtime_->step_execution_episode_results_batch(request.step_requests);
    result.rewards.reserve(result.step_results.size());
    result.terminated.reserve(result.step_results.size());
    result.truncated.reserve(result.step_results.size());
    result.status_vectors.reserve(result.step_results.size());
    result.termination_reasons.reserve(result.step_results.size());
    result.reward_breakdown_jsons.reserve(result.step_results.size());
    result.step_infos.reserve(result.step_results.size());
    result.step_info_valid_flags.reserve(result.step_results.size());
    result.controller_state_changed_flags.reserve(result.step_results.size());
    for (const auto& step_result : result.step_results) {
        result.rewards.push_back(step_result.reward_total);
        result.terminated.push_back(step_result.terminated);
        result.truncated.push_back(step_result.truncated);
        result.status_vectors.push_back(std::array<double, 4>{
            step_result.status0,
            step_result.status1,
            step_result.status2,
            step_result.status3,
        });
        result.termination_reasons.push_back(step_result.controller_state.last_termination_reason);
        result.reward_breakdown_jsons.push_back(step_result.controller_state.last_reward_breakdown_json);
        result.step_infos.push_back(step_result.step_info);
        result.step_info_valid_flags.push_back(step_result.step_info_valid);
        result.controller_state_changed_flags.push_back(step_result.structural_state_changed);
    }
    result.observation_packet = build_observation_packet(observation_request_from_step_request(request));
    return result;
}

std::vector<AgentObservation> RuntimeFacade::get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_agent_observations_batch(refs);
}

std::vector<InstrumentState> RuntimeFacade::get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_instrument_states_batch(refs);
}

std::vector<MissionCommand> RuntimeFacade::get_mission_commands_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_mission_commands_batch(refs);
}

std::vector<TaskOrder> RuntimeFacade::get_task_orders_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_task_orders_batch(refs);
}

std::vector<LeaderIntent> RuntimeFacade::get_leader_intents_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_leader_intents_batch(refs);
}

std::vector<PilotReport> RuntimeFacade::get_pilot_reports_batch(const std::vector<WorldEntityRef>& refs) const {
    return runtime_->get_pilot_reports_batch(refs);
}

ObservationBatchPacket RuntimeFacade::export_observation_packet(const std::vector<WorldEntityRef>& refs) const {
    return build_observation_packet(ObservationBatchRequest{
        .refs = refs,
        .include_agent_observations = true,
        .include_instrument_states = true,
        .include_mission_commands = true,
        .include_task_orders = true,
        .include_leader_intents = true,
        .include_pilot_reports = true,
    });
}

ObservationBatchPacket RuntimeFacade::export_observation_packet(const ObservationBatchRequest& request) const {
    return build_observation_packet(request);
}

EngagementEventPacket RuntimeFacade::export_engagement_event_packet(
    const EngagementBatchRequest& request
) const {
    EngagementEventPacket packet{};
    packet.refs = request.refs;
    packet.trace_ids = request.trace_ids;

    std::vector<std::uint64_t> exported_world_indices;
    for (const auto& ref : request.refs) {
        if (contains_world_index(exported_world_indices, ref.world_index)) {
            continue;
        }
        exported_world_indices.push_back(ref.world_index);
        append_recent_engagement_events(
            packet,
            with_world_index(
                runtime_->world(static_cast<std::size_t>(ref.world_index)).export_recent_engagement_events(),
                ref.world_index
            ),
            request
        );
    }

    const bool needs_observations =
        request.include_track_packets || request.include_diagnostics_traces;
    if (!needs_observations || request.refs.empty()) {
        return packet;
    }

    const auto observations = runtime_->get_agent_observations_batch(
        world_refs_from_engagement_refs(request.refs)
    );

    std::uint64_t next_snapshot_version = 1;
    for (std::size_t ref_index = 0; ref_index < request.refs.size(); ++ref_index) {
        const auto& ref = request.refs[ref_index];
        const auto& observation = observations[ref_index];
        const std::uint64_t snapshot_version = next_snapshot_version++;
        for (const auto& contact : observation.contacts) {
            if (request.include_track_packets) {
                packet.track_packets.push_back(track_packet_from_observation_contact(
                    ref,
                    contact,
                    observation.sim_time,
                    snapshot_version
                ));
            }
            if (request.include_diagnostics_traces && !request.trace_ids.empty()) {
                const auto trace_id = request.trace_ids[
                    packet.diagnostics_traces.size() % request.trace_ids.size()
                ];
                packet.diagnostics_traces.push_back(diagnostics_trace_from_track_packet(
                    trace_id,
                    track_packet_from_observation_contact(
                        ref,
                        contact,
                        observation.sim_time,
                        snapshot_version
                    ),
                    snapshot_version
                ));
            }
        }
    }
    return packet;
}

ObservationBatchPacket RuntimeFacade::build_observation_packet(
    const ObservationBatchRequest& request
) const {
    ObservationBatchPacket packet{};
    packet.refs = request.refs;

    if (request.refs.empty()) {
        return packet;
    }

    if (request.include_agent_observations) {
        packet.agent_observations = runtime_->get_agent_observations_batch(request.refs);
    }
    if (request.include_instrument_states) {
        packet.instrument_states = runtime_->get_instrument_states_batch(request.refs);
    }
    if (request.include_mission_commands) {
        packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);
    }
    if (request.include_task_orders) {
        packet.task_orders = runtime_->get_task_orders_batch(request.refs);
    }
    if (request.include_leader_intents) {
        packet.leader_intents = runtime_->get_leader_intents_batch(request.refs);
    }
    if (request.include_pilot_reports) {
        packet.pilot_reports = runtime_->get_pilot_reports_batch(request.refs);
    }
    return packet;
}
