#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_engine(nb::module_ &m) {
    nb::class_<runtime::scheduler::StageNodeManifest> stage_node_manifest_class(
        m, "StageNodeManifest");
    stage_node_manifest_class.def(nb::init<>())
        .def_rw("node_id", &runtime::scheduler::StageNodeManifest::node_id)
        .def_rw("semantic_stage", &runtime::scheduler::StageNodeManifest::semantic_stage)
        .def_rw("owner_module", &runtime::scheduler::StageNodeManifest::owner_module)
        .def_rw("input_packets", &runtime::scheduler::StageNodeManifest::input_packets)
        .def_rw("output_packets", &runtime::scheduler::StageNodeManifest::output_packets)
        .def_rw("read_state_shards", &runtime::scheduler::StageNodeManifest::read_state_shards)
        .def_rw("write_state_shards", &runtime::scheduler::StageNodeManifest::write_state_shards)
        .def_rw("read_snapshot_policy", &runtime::scheduler::StageNodeManifest::read_snapshot_policy)
        .def_rw("write_commit_policy", &runtime::scheduler::StageNodeManifest::write_commit_policy)
        .def_rw("clock_domain", &runtime::scheduler::StageNodeManifest::clock_domain)
        .def_rw("latency_policy", &runtime::scheduler::StageNodeManifest::latency_policy)
        .def_rw("sync_policy", &runtime::scheduler::StageNodeManifest::sync_policy)
        .def_rw("allowed_same_window_edges",
                &runtime::scheduler::StageNodeManifest::allowed_same_window_edges)
        .def_rw("required_barriers", &runtime::scheduler::StageNodeManifest::required_barriers)
        .def_rw("event_families_emitted",
                &runtime::scheduler::StageNodeManifest::event_families_emitted)
        .def_rw("diagnostic_trace_obligations",
                &runtime::scheduler::StageNodeManifest::diagnostic_trace_obligations)
        .def_rw("facade_visibility", &runtime::scheduler::StageNodeManifest::facade_visibility)
        .def_rw("adapter_projection_allowed",
                &runtime::scheduler::StageNodeManifest::adapter_projection_allowed);

    nb::class_<WorldBatchRuntime>(m, "WorldBatchRuntime")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def("world_count", &WorldBatchRuntime::world_count)
        .def("resize", &WorldBatchRuntime::resize, nb::arg("world_count"))
        .def("set_worker_threads", &WorldBatchRuntime::set_worker_threads,
             nb::arg("worker_threads"))
        .def("worker_threads", &WorldBatchRuntime::worker_threads)
        .def("effective_worker_threads", &WorldBatchRuntime::effective_worker_threads)
        .def("batch_healthy", &WorldBatchRuntime::batch_healthy)
        .def("batch_failure_reason", &WorldBatchRuntime::batch_failure_reason)
        .def("batch_generation", &WorldBatchRuntime::batch_generation)
        .def("resolve_factory_platform_spawn_plan",
             &WorldBatchRuntime::resolve_factory_platform_spawn_plan,
             nb::arg("world_index"), nb::arg("type_name"))
        .def("maintained_stage_node_manifests",
             &WorldBatchRuntime::maintained_stage_node_manifests)
        .def("world_raw_quarantine",
             nb::overload_cast<size_t>(&WorldBatchRuntime::world_raw_quarantine),
             nb::rv_policy::reference_internal, nb::arg("index"))
        .def("reset_batch", &WorldBatchRuntime::reset_batch,
             nb::arg("seeds") = std::vector<uint32_t>{})
        .def("step_batch", &WorldBatchRuntime::step_batch)
        .def("step_worlds", &WorldBatchRuntime::step_worlds, nb::arg("world_indices"))
        .def("load_database", &WorldBatchRuntime::load_database, nb::arg("path"))
        .def(
            "load_unit_definitions",
            [](WorldBatchRuntime &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok && !error.empty()) {
                    spdlog::warn("WorldBatchRuntime failed to load unit definitions: {}", error);
                }
                return ok;
            },
            nb::arg("path"))
        .def("set_time_step", &WorldBatchRuntime::set_time_step, nb::arg("dt"))
        .def("clear_zones_batch", &WorldBatchRuntime::clear_zones_batch,
             nb::arg("world_indices") = std::vector<uint64_t>{})
        .def("spawn_units_batch", &WorldBatchRuntime::spawn_units_batch, nb::arg("requests"))
        .def("apply_world_setup_batch", &WorldBatchRuntime::apply_world_setup_batch,
             nb::arg("seeds"), nb::arg("terrain_assignments"), nb::arg("wind_assignments"),
             nb::arg("zones"), nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{},
             nb::arg("sun_assignments") = std::vector<WorldSunAssignment>{},
             nb::arg("geodetic_anchor_assignments") = std::vector<WorldGeodeticAnchorAssignment>{},
             nb::arg("maritime_assignments") = std::vector<WorldMaritimeAssignment>{})
        .def("apply_world_layout", &WorldBatchRuntime::apply_world_layout, nb::arg("world_index"),
             nb::arg("seed"), nb::arg("terrain_type"), nb::arg("wind_speed_mps"),
             nb::arg("wind_dir_from_deg"), nb::arg("wind_shear_mps_per_km"),
             nb::arg("maritime_configured"), nb::arg("sea_state"), nb::arg("wave_heading_deg"),
             nb::arg("wave_period_s"), nb::arg("zones"), nb::arg("requests"),
             nb::arg("time_steps") = std::vector<double>{}, nb::arg("sun_azimuth_deg") = 0.0,
             nb::arg("sun_elevation_deg") = 45.0,
             nb::arg("geodetic_anchor") = WorldGeodeticAnchorAssignment{})
        .def("world_time_step", &WorldBatchRuntime::world_time_step, nb::arg("world_index"))
        .def("set_pilot_actions_batch", &WorldBatchRuntime::set_pilot_actions_batch,
             nb::arg("assignments"))
        .def("apply_launch_requests_batch", &WorldBatchRuntime::apply_launch_requests_batch,
             nb::arg("requests"))
        .def("set_mission_commands_maintained_batch",
             &WorldBatchRuntime::set_mission_commands_maintained_batch, nb::arg("assignments"))
        .def("set_task_orders_maintained_batch",
             &WorldBatchRuntime::set_task_orders_maintained_batch, nb::arg("assignments"))
        .def("set_leader_intents_maintained_batch",
             &WorldBatchRuntime::set_leader_intents_maintained_batch, nb::arg("assignments"))
        .def("set_pilot_reports_maintained_batch",
             &WorldBatchRuntime::set_pilot_reports_maintained_batch, nb::arg("assignments"))
        .def("get_agent_observations_batch", &WorldBatchRuntime::get_agent_observations_batch,
             nb::arg("refs"))
        .def("get_instrument_states_batch", &WorldBatchRuntime::get_instrument_states_batch,
             nb::arg("refs"))
        .def("get_mission_commands_batch", &WorldBatchRuntime::get_mission_commands_batch,
             nb::arg("refs"))
        .def("get_mission_commands_maintained_batch",
             &WorldBatchRuntime::get_mission_commands_maintained_batch, nb::arg("refs"))
        .def("get_task_orders_maintained_batch",
             &WorldBatchRuntime::get_task_orders_maintained_batch, nb::arg("refs"))
        .def("get_leader_intents_batch", &WorldBatchRuntime::get_leader_intents_batch,
             nb::arg("refs"))
        .def("get_leader_intents_maintained_batch",
             &WorldBatchRuntime::get_leader_intents_maintained_batch, nb::arg("refs"))
        .def("get_pilot_reports_batch", &WorldBatchRuntime::get_pilot_reports_batch,
             nb::arg("refs"))
        .def("get_pilot_reports_maintained_batch",
             &WorldBatchRuntime::get_pilot_reports_maintained_batch, nb::arg("refs"))
        .def("get_sensor_candidate_ids_batch", &WorldBatchRuntime::get_sensor_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("get_visual_candidate_ids_batch", &WorldBatchRuntime::get_visual_candidate_ids_batch,
             nb::arg("refs"), nb::arg("range_m") = 25000.0, nb::arg("use_gpu") = false)
        .def("get_comm_candidate_ids_batch", &WorldBatchRuntime::get_comm_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false);
}
