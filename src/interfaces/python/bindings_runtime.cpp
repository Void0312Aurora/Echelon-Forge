#include "interfaces/python/binding_utils.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
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

    nb::class_<EngagementEntityRef>(m, "EngagementEntityRef")
        .def(nb::init<>())
        .def_rw("world_index", &EngagementEntityRef::world_index)
        .def_rw("entity_id", &EngagementEntityRef::entity_id);

    nb::class_<TrackPacket>(m, "TrackPacket")
        .def(nb::init<>())
        .def_rw("track_id", &TrackPacket::track_id)
        .def_rw("correlated_entity", &TrackPacket::correlated_entity)
        .def_rw("has_correlated_entity", &TrackPacket::has_correlated_entity)
        .def_rw("correlation_policy", &TrackPacket::correlation_policy)
        .def_rw("source", &TrackPacket::source)
        .def_rw("classification", &TrackPacket::classification)
        .def_rw("status", &TrackPacket::status)
        .def_rw("quality", &TrackPacket::quality)
        .def_rw("confidence", &TrackPacket::confidence)
        .def_rw("usable", &TrackPacket::usable)
        .def_rw("iff", &TrackPacket::iff)
        .def_rw("source_time_s", &TrackPacket::source_time_s)
        .def_rw("update_age_s", &TrackPacket::update_age_s)
        .def_rw("snapshot_version", &TrackPacket::snapshot_version);

    nb::class_<LaunchRequest>(m, "LaunchRequest")
        .def(nb::init<>())
        .def_rw("request_id", &LaunchRequest::request_id)
        .def_rw("shooter", &LaunchRequest::shooter)
        .def_rw("target_entity", &LaunchRequest::target_entity)
        .def_rw("has_target_entity", &LaunchRequest::has_target_entity)
        .def_rw("target_track_id", &LaunchRequest::target_track_id)
        .def_rw("has_target_track", &LaunchRequest::has_target_track)
        .def_rw("station_id", &LaunchRequest::station_id)
        .def_rw("mount_id", &LaunchRequest::mount_id)
        .def_rw("requested_munition_family", &LaunchRequest::requested_munition_family)
        .def_rw("authority", &LaunchRequest::authority)
        .def_rw("requested_time_s", &LaunchRequest::requested_time_s)
        .def_rw("merge_policy", &LaunchRequest::merge_policy);

    nb::class_<LaunchEvent>(m, "LaunchEvent")
        .def(nb::init<>())
        .def_rw("event_id", &LaunchEvent::event_id)
        .def_rw("request_id", &LaunchEvent::request_id)
        .def_rw("accepted", &LaunchEvent::accepted)
        .def_rw("rejection_reason", &LaunchEvent::rejection_reason)
        .def_rw("selected_launcher", &LaunchEvent::selected_launcher)
        .def_rw("selected_munition", &LaunchEvent::selected_munition)
        .def_rw("ammo_delta", &LaunchEvent::ammo_delta)
        .def_rw("cooldown_delta_s", &LaunchEvent::cooldown_delta_s)
        .def_rw("spawned_munition", &LaunchEvent::spawned_munition)
        .def_rw("has_spawned_munition", &LaunchEvent::has_spawned_munition)
        .def_rw("event_time_s", &LaunchEvent::event_time_s);

    nb::class_<MunitionLifecyclePacket>(m, "MunitionLifecyclePacket")
        .def(nb::init<>())
        .def_rw("packet_id", &MunitionLifecyclePacket::packet_id)
        .def_rw("munition", &MunitionLifecyclePacket::munition)
        .def_rw("attacker", &MunitionLifecyclePacket::attacker)
        .def_rw("target_entity", &MunitionLifecyclePacket::target_entity)
        .def_rw("has_target_entity", &MunitionLifecyclePacket::has_target_entity)
        .def_rw("target_track_id", &MunitionLifecyclePacket::target_track_id)
        .def_rw("has_target_track", &MunitionLifecyclePacket::has_target_track)
        .def_rw("launch_event_id", &MunitionLifecyclePacket::launch_event_id)
        .def_rw("active", &MunitionLifecyclePacket::active)
        .def_rw("seeker_mode", &MunitionLifecyclePacket::seeker_mode)
        .def_rw("guidance_cadence_s", &MunitionLifecyclePacket::guidance_cadence_s)
        .def_rw("track_memory_state", &MunitionLifecyclePacket::track_memory_state)
        .def_rw("fuel_remaining_fraction", &MunitionLifecyclePacket::fuel_remaining_fraction)
        .def_rw("burnout", &MunitionLifecyclePacket::burnout)
        .def_rw("max_flight_time_s", &MunitionLifecyclePacket::max_flight_time_s)
        .def_rw("fuze_state", &MunitionLifecyclePacket::fuze_state)
        .def_rw("source_time_s", &MunitionLifecyclePacket::source_time_s);

    nb::class_<EffectsEvent>(m, "EffectsEvent")
        .def(nb::init<>())
        .def_rw("event_id", &EffectsEvent::event_id)
        .def_rw("munition", &EffectsEvent::munition)
        .def_rw("target", &EffectsEvent::target)
        .def_rw("trigger_type", &EffectsEvent::trigger_type)
        .def_rw("outcome_state", &EffectsEvent::outcome_state)
        .def_rw("detonation_time_s", &EffectsEvent::detonation_time_s)
        .def_rw("nearest_approach_time_s", &EffectsEvent::nearest_approach_time_s)
        .def_rw("quality", &EffectsEvent::quality)
        .def_rw("confidence", &EffectsEvent::confidence)
        .def_rw("effect_family", &EffectsEvent::effect_family);

    nb::class_<DamageReport>(m, "DamageReport")
        .def(nb::init<>())
        .def_rw("report_id", &DamageReport::report_id)
        .def_rw("target", &DamageReport::target)
        .def_rw("source_event_id", &DamageReport::source_event_id)
        .def_rw("hp_delta", &DamageReport::hp_delta)
        .def_rw("system_health_delta", &DamageReport::system_health_delta)
        .def_rw("platform_damage_state_delta", &DamageReport::platform_damage_state_delta)
        .def_rw("mission_kill", &DamageReport::mission_kill)
        .def_rw("mobility_kill", &DamageReport::mobility_kill)
        .def_rw("sensor_kill", &DamageReport::sensor_kill)
        .def_rw("survivability_kill", &DamageReport::survivability_kill)
        .def_rw("loss_state_from", &DamageReport::loss_state_from)
        .def_rw("loss_state_to", &DamageReport::loss_state_to)
        .def_rw("destroyed", &DamageReport::destroyed)
        .def_rw("report_time_s", &DamageReport::report_time_s);

    nb::class_<DiagnosticsTrace>(m, "DiagnosticsTrace")
        .def(nb::init<>())
        .def_rw("trace_id", &DiagnosticsTrace::trace_id)
        .def_rw("parent_trace_id", &DiagnosticsTrace::parent_trace_id)
        .def_rw("chain_id", &DiagnosticsTrace::chain_id)
        .def_rw("track_id", &DiagnosticsTrace::track_id)
        .def_rw("launch_request_id", &DiagnosticsTrace::launch_request_id)
        .def_rw("launch_event_id", &DiagnosticsTrace::launch_event_id)
        .def_rw("munition", &DiagnosticsTrace::munition)
        .def_rw("effects_event_id", &DiagnosticsTrace::effects_event_id)
        .def_rw("damage_report_id", &DiagnosticsTrace::damage_report_id)
        .def_rw("observation_packet_version", &DiagnosticsTrace::observation_packet_version);

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

    nb::class_<EngagementBatchRequest>(m, "EngagementBatchRequest")
        .def(nb::init<>())
        .def_rw("refs", &EngagementBatchRequest::refs)
        .def_rw("trace_ids", &EngagementBatchRequest::trace_ids)
        .def_rw("include_track_packets", &EngagementBatchRequest::include_track_packets)
        .def_rw("include_launch_requests", &EngagementBatchRequest::include_launch_requests)
        .def_rw("include_launch_events", &EngagementBatchRequest::include_launch_events)
        .def_rw(
            "include_munition_lifecycle_packets",
            &EngagementBatchRequest::include_munition_lifecycle_packets
        )
        .def_rw("include_effects_events", &EngagementBatchRequest::include_effects_events)
        .def_rw("include_damage_reports", &EngagementBatchRequest::include_damage_reports)
        .def_rw("include_diagnostics_traces", &EngagementBatchRequest::include_diagnostics_traces);

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

    nb::class_<EngagementEventPacket>(m, "EngagementEventPacket")
        .def(nb::init<>())
        .def_rw("refs", &EngagementEventPacket::refs)
        .def_rw("trace_ids", &EngagementEventPacket::trace_ids)
        .def_rw("track_packets", &EngagementEventPacket::track_packets)
        .def_rw("launch_requests", &EngagementEventPacket::launch_requests)
        .def_rw("launch_events", &EngagementEventPacket::launch_events)
        .def_rw(
            "munition_lifecycle_packets",
            &EngagementEventPacket::munition_lifecycle_packets
        )
        .def_rw("effects_events", &EngagementEventPacket::effects_events)
        .def_rw("damage_reports", &EngagementEventPacket::damage_reports)
        .def_rw("diagnostics_traces", &EngagementEventPacket::diagnostics_traces);

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
        .def_rw("vz", &WorldSpawnRequest::vz)
        .def_rw("ammo_override_enabled", &WorldSpawnRequest::ammo_override_enabled)
        .def_rw("missiles_remaining", &WorldSpawnRequest::missiles_remaining)
        .def_rw("max_missiles", &WorldSpawnRequest::max_missiles)
        .def_rw("weapon_cooldown_override_enabled", &WorldSpawnRequest::weapon_cooldown_override_enabled)
        .def_rw("weapon_cooldown_s", &WorldSpawnRequest::weapon_cooldown_s)
        .def_rw("weapon_last_fire_time", &WorldSpawnRequest::weapon_last_fire_time);

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
        )
        .def(
            "export_engagement_event_packet",
            &RuntimeFacade::export_engagement_event_packet,
            nb::arg("request")
        );
}
