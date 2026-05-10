#include "interfaces/python/binding_utils.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime(nb::module_& m) {
    nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")
        .def(nb::init<>())
        .def_rw("supports_batch_runtime", &RuntimeCapabilities::supports_batch_runtime)
        .def_rw(
            "supports_compiled_episode_controller",
            &RuntimeCapabilities::supports_compiled_episode_controller
        )
        .def_rw(
            "supports_compiled_execution_step",
            &RuntimeCapabilities::supports_compiled_execution_step
        )
        .def_rw("supports_gpu_visual", &RuntimeCapabilities::supports_gpu_visual)
        .def_rw("supports_gpu_observation", &RuntimeCapabilities::supports_gpu_observation)
        .def_rw("supports_gpu_flight_shaping", &RuntimeCapabilities::supports_gpu_flight_shaping)
        .def_rw("supports_device_observation_view", &RuntimeCapabilities::supports_device_observation_view)
        .def_rw("supports_resident_state", &RuntimeCapabilities::supports_resident_state)
        .def_rw("supports_exact_gpu_backend", &RuntimeCapabilities::supports_exact_gpu_backend)
        .def_rw("supports_shadow_compare", &RuntimeCapabilities::supports_shadow_compare);

    nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")
        .def(nb::init<>())
        .def_rw("world_count", &RuntimeBatchConfig::world_count)
        .def_rw("worker_threads", &RuntimeBatchConfig::worker_threads);

    nb::class_<BatchResetRequest>(m, "BatchResetRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchResetRequest::seeds);

    nb::class_<BatchWorldSetupRequest>(m, "BatchWorldSetupRequest")
        .def(nb::init<>())
        .def_rw("seeds", &BatchWorldSetupRequest::seeds)
        .def_rw("terrain_assignments", &BatchWorldSetupRequest::terrain_assignments)
        .def_rw("wind_assignments", &BatchWorldSetupRequest::wind_assignments)
        .def_rw("zones", &BatchWorldSetupRequest::zones)
        .def_rw("spawn_requests", &BatchWorldSetupRequest::spawn_requests)
        .def_rw("time_steps", &BatchWorldSetupRequest::time_steps);

    nb::class_<BatchWorldSetupResult>(m, "BatchWorldSetupResult")
        .def(nb::init<>())
        .def_rw("entity_ids", &BatchWorldSetupResult::entity_ids);

    nb::class_<ObservationBatchRequest>(m, "ObservationBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &ObservationBatchRequest::refs)
        .def_rw("include_agent_observations", &ObservationBatchRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ObservationBatchRequest::include_instrument_states)
        .def_rw("include_mission_commands", &ObservationBatchRequest::include_mission_commands)
        .def_rw("include_task_orders", &ObservationBatchRequest::include_task_orders)
        .def_rw("include_leader_intents", &ObservationBatchRequest::include_leader_intents)
        .def_rw("include_pilot_reports", &ObservationBatchRequest::include_pilot_reports);

    nb::class_<ExecutionBatchStepRequest>(m, "ExecutionBatchStepRequest")
        .def(nb::init<>())
        .def_rw("step_requests", &ExecutionBatchStepRequest::step_requests)
        .def_rw("include_agent_observations", &ExecutionBatchStepRequest::include_agent_observations)
        .def_rw("include_instrument_states", &ExecutionBatchStepRequest::include_instrument_states)
        .def_rw("include_mission_commands", &ExecutionBatchStepRequest::include_mission_commands)
        .def_rw("include_task_orders", &ExecutionBatchStepRequest::include_task_orders)
        .def_rw("include_leader_intents", &ExecutionBatchStepRequest::include_leader_intents)
        .def_rw("include_pilot_reports", &ExecutionBatchStepRequest::include_pilot_reports);

    nb::class_<ObservationBatchPacket>(m, "ObservationBatchPacket")
        .def(nb::init<>())
        .def_rw("refs", &ObservationBatchPacket::refs)
        .def_rw("agent_observations", &ObservationBatchPacket::agent_observations)
        .def_rw("instrument_states", &ObservationBatchPacket::instrument_states)
        .def_rw("mission_commands", &ObservationBatchPacket::mission_commands)
        .def_rw("task_orders", &ObservationBatchPacket::task_orders)
        .def_rw("leader_intents", &ObservationBatchPacket::leader_intents)
        .def_rw("pilot_reports", &ObservationBatchPacket::pilot_reports);

    nb::class_<ExecutionBatchStepResult>(m, "ExecutionBatchStepResult")
        .def(nb::init<>())
        .def_rw("step_results", &ExecutionBatchStepResult::step_results)
        .def_rw("rewards", &ExecutionBatchStepResult::rewards)
        .def_rw("terminated", &ExecutionBatchStepResult::terminated)
        .def_rw("truncated", &ExecutionBatchStepResult::truncated)
        .def_rw("status_vectors", &ExecutionBatchStepResult::status_vectors)
        .def_rw("termination_reasons", &ExecutionBatchStepResult::termination_reasons)
        .def_rw("reward_breakdown_jsons", &ExecutionBatchStepResult::reward_breakdown_jsons)
        .def_rw("step_infos", &ExecutionBatchStepResult::step_infos)
        .def_rw("step_info_valid_flags", &ExecutionBatchStepResult::step_info_valid_flags)
        .def_rw(
            "controller_state_changed_flags",
            &ExecutionBatchStepResult::controller_state_changed_flags
        )
        .def_rw("observation_packet", &ExecutionBatchStepResult::observation_packet);

    nb::class_<WorldEntityRef>(m, "WorldEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &WorldEntityRef::world_index)
        .def_rw("entity_id", &WorldEntityRef::entity_id);

    nb::class_<WorldTerrainAssignment>(m, "WorldTerrainAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTerrainAssignment::world_index)
        .def_rw("terrain_type", &WorldTerrainAssignment::terrain_type);

    nb::class_<WorldWindAssignment>(m, "WorldWindAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldWindAssignment::world_index)
        .def_rw("speed_mps", &WorldWindAssignment::speed_mps)
        .def_rw("dir_from_deg", &WorldWindAssignment::dir_from_deg)
        .def_rw("shear_mps_per_km", &WorldWindAssignment::shear_mps_per_km);

    nb::class_<WorldZoneDefinition>(m, "WorldZoneDefinition")
        .def(nb::init<>())
        .def_rw("world_index", &WorldZoneDefinition::world_index)
        .def_rw("name", &WorldZoneDefinition::name)
        .def_rw("x", &WorldZoneDefinition::x)
        .def_rw("y", &WorldZoneDefinition::y)
        .def_rw("width", &WorldZoneDefinition::width)
        .def_rw("length", &WorldZoneDefinition::length)
        .def_rw("heading", &WorldZoneDefinition::heading)
        .def_rw("surface_type", &WorldZoneDefinition::surface_type);

    nb::class_<WorldSpawnRequest>(m, "WorldSpawnRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSpawnRequest::world_index)
        .def_rw("side", &WorldSpawnRequest::side)
        .def_rw("type_name", &WorldSpawnRequest::type_name)
        .def_rw("entity_name", &WorldSpawnRequest::entity_name)
        .def_rw("is_agent", &WorldSpawnRequest::is_agent)
        .def_rw("x", &WorldSpawnRequest::x)
        .def_rw("y", &WorldSpawnRequest::y)
        .def_rw("z", &WorldSpawnRequest::z)
        .def_rw("heading", &WorldSpawnRequest::heading)
        .def_rw("pitch", &WorldSpawnRequest::pitch)
        .def_rw("roll", &WorldSpawnRequest::roll)
        .def_rw("vx", &WorldSpawnRequest::vx)
        .def_rw("vy", &WorldSpawnRequest::vy)
        .def_rw("vz", &WorldSpawnRequest::vz);

    nb::class_<WorldPilotActionAssignment>(m, "WorldPilotActionAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotActionAssignment::world_index)
        .def_rw("entity_id", &WorldPilotActionAssignment::entity_id)
        .def_rw("action", &WorldPilotActionAssignment::action);

    nb::class_<WorldMissionCommandAssignment>(m, "WorldMissionCommandAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMissionCommandAssignment::world_index)
        .def_rw("entity_id", &WorldMissionCommandAssignment::entity_id)
        .def_rw("command", &WorldMissionCommandAssignment::command);

    nb::class_<WorldTaskOrderAssignment>(m, "WorldTaskOrderAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldTaskOrderAssignment::world_index)
        .def_rw("entity_id", &WorldTaskOrderAssignment::entity_id)
        .def_rw("order", &WorldTaskOrderAssignment::order);

    nb::class_<WorldLeaderIntentAssignment>(m, "WorldLeaderIntentAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldLeaderIntentAssignment::world_index)
        .def_rw("entity_id", &WorldLeaderIntentAssignment::entity_id)
        .def_rw("intent", &WorldLeaderIntentAssignment::intent);

    nb::class_<WorldPilotReportAssignment>(m, "WorldPilotReportAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldPilotReportAssignment::world_index)
        .def_rw("entity_id", &WorldPilotReportAssignment::entity_id)
        .def_rw("report", &WorldPilotReportAssignment::report);

    nb::class_<WorldExecutionEpisodeStepRequest>(m, "WorldExecutionEpisodeStepRequest")
        .def(nb::init<>())
        .def_rw("world_index", &WorldExecutionEpisodeStepRequest::world_index)
        .def_rw("entity_id", &WorldExecutionEpisodeStepRequest::entity_id)
        .def_rw("config", &WorldExecutionEpisodeStepRequest::config)
        .def_rw("env_state", &WorldExecutionEpisodeStepRequest::env_state);

    nb::class_<WorldBatchRuntime>(m, "WorldBatchRuntime")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def("world_count", &WorldBatchRuntime::world_count)
        .def("resize", &WorldBatchRuntime::resize, nb::arg("world_count"))
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("world", nb::overload_cast<size_t>(&WorldBatchRuntime::world), nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch, nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](WorldBatchRuntime& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("set_terrain_types_batch", &WorldBatchRuntime::set_terrain_types_batch, nb::arg("assignments"))
        .def("set_winds_batch", &WorldBatchRuntime::set_winds_batch, nb::arg("assignments"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch, nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("add_zones_batch", &WorldBatchRuntime::add_zones_batch, nb::arg("zones"))
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def(
            "apply_world_setup_batch",
            &WorldBatchRuntime::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &WorldBatchRuntime::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &WorldBatchRuntime::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &WorldBatchRuntime::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &WorldBatchRuntime::set_pilot_reports_batch, nb::arg("assignments"))
        .def("clear_execution_episode_controller_batch", &WorldBatchRuntime::clear_execution_episode_controller_batch)
        .def(
            "prime_execution_episode_controller_batch",
            &WorldBatchRuntime::prime_execution_episode_controller_batch,
            nb::arg("refs"),
            nb::arg("states")
        )
        .def(
            "execution_episode_controller_ready",
            &WorldBatchRuntime::execution_episode_controller_ready,
            nb::arg("world_index")
        )
        .def(
            "export_execution_episode_states_batch",
            &WorldBatchRuntime::export_execution_episode_states_batch,
            nb::arg("refs")
        )
        .def(
            "evaluate_execution_episode_batch",
            &WorldBatchRuntime::evaluate_execution_episode_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_episode_batch",
            &WorldBatchRuntime::step_execution_episode_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_episode_results_batch",
            &WorldBatchRuntime::step_execution_episode_results_batch,
            nb::arg("requests")
        )
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &WorldBatchRuntime::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch, nb::arg("refs"))
        .def(
            "get_sensor_candidate_ids_batch",
            &WorldBatchRuntime::get_sensor_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        )
        .def(
            "get_visual_candidate_ids_batch",
            &WorldBatchRuntime::get_visual_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("range_m") = 25000.0,
            nb::arg("use_gpu") = false
        )
        .def(
            "get_comm_candidate_ids_batch",
            &WorldBatchRuntime::get_comm_candidate_ids_batch,
            nb::arg("refs"),
            nb::arg("use_gpu") = false
        );

    // Maintained runtime facade surface for frontend-facing batch use cases.
    nb::class_<RuntimeFacade>(m, "RuntimeFacade")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def(nb::init<const RuntimeBatchConfig&>(), nb::arg("config"))
        .def("configure_batch", &RuntimeFacade::configure_batch, nb::arg("config"))
        .def("batch_config", &RuntimeFacade::batch_config)
        .def("capabilities", &RuntimeFacade::capabilities)
        .def("world_count", &RuntimeFacade::world_count)
        .def("resize", &RuntimeFacade::resize, nb::arg("world_count"))
        .def("set_worker_threads", &RuntimeFacade::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &RuntimeFacade::worker_threads)
        .def("effective_worker_threads", &RuntimeFacade::effective_worker_threads)
        .def("runtime", nb::overload_cast<>(&RuntimeFacade::runtime), nb::rv_policy::reference_internal)
        .def("load_database", &RuntimeFacade::load_database, nb::arg("path"))
        .def("load_unit_definitions", [](RuntimeFacade& self, const std::string& path) {
            std::string error;
            bool ok = self.load_unit_definitions(path, &error);
            if (!ok && !error.empty()) {
                spdlog::warn("RuntimeFacade failed to load unit definitions: {}", error);
            }
            return ok;
        }, nb::arg("path"))
        .def("reset_batch", &RuntimeFacade::reset_batch, nb::arg("request") = BatchResetRequest{})
        .def("step_batch", &RuntimeFacade::step_batch)
        .def(
            "apply_world_setup_batch",
            &RuntimeFacade::apply_world_setup_batch,
            nb::arg("seeds"),
            nb::arg("terrain_assignments"),
            nb::arg("wind_assignments"),
            nb::arg("zones"),
            nb::arg("requests"),
            nb::arg("time_steps") = std::vector<double>{}
        )
        .def("apply_world_setup", &RuntimeFacade::apply_world_setup, nb::arg("request"))
        .def("set_pilot_actions_batch", &RuntimeFacade::set_pilot_actions_batch, nb::arg("assignments"))
        .def("set_mission_commands_batch", &RuntimeFacade::set_mission_commands_batch, nb::arg("assignments"))
        .def("set_task_orders_batch", &RuntimeFacade::set_task_orders_batch, nb::arg("assignments"))
        .def("set_leader_intents_batch", &RuntimeFacade::set_leader_intents_batch, nb::arg("assignments"))
        .def("set_pilot_reports_batch", &RuntimeFacade::set_pilot_reports_batch, nb::arg("assignments"))
        .def("clear_execution_episode_batch", &RuntimeFacade::clear_execution_episode_batch)
        .def(
            "prime_execution_episode_batch",
            &RuntimeFacade::prime_execution_episode_batch,
            nb::arg("refs"),
            nb::arg("states")
        )
        .def("execution_episode_ready", &RuntimeFacade::execution_episode_ready, nb::arg("world_index"))
        .def(
            "export_execution_episode_states",
            &RuntimeFacade::export_execution_episode_states,
            nb::arg("refs")
        )
        .def(
            "evaluate_execution_batch",
            &RuntimeFacade::evaluate_execution_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_products_batch",
            &RuntimeFacade::step_execution_products_batch,
            nb::arg("requests")
        )
        .def(
            "step_execution_batch",
            &RuntimeFacade::step_execution_batch,
            nb::arg("request")
        )
        .def("get_agent_observations_batch", &RuntimeFacade::get_agent_observations_batch, nb::arg("refs"))
        .def("get_instrument_states_batch", &RuntimeFacade::get_instrument_states_batch, nb::arg("refs"))
        .def("get_mission_commands_batch", &RuntimeFacade::get_mission_commands_batch, nb::arg("refs"))
        .def("get_task_orders_batch", &RuntimeFacade::get_task_orders_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &RuntimeFacade::get_leader_intents_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &RuntimeFacade::get_pilot_reports_batch, nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade& self, const std::vector<WorldEntityRef>& refs) {
                return self.export_observation_packet(refs);
            },
            nb::arg("refs")
        )
        .def(
            "export_observation_packet",
            [](const RuntimeFacade& self, const ObservationBatchRequest& request) {
                return self.export_observation_packet(request);
            },
            nb::arg("request")
        );
}
