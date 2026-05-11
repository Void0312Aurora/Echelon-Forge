#include "runtime/facade/runtime_facade.h"

#include "core/engine/world_batch_runtime.h"

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
    return RuntimeCapabilities{};
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
