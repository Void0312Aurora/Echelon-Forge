#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_facade(nb::module_ &m) {
    // Maintained runtime facade surface for frontend-facing batch use cases.
    nb::class_<RuntimeFacade>(m, "RuntimeFacade")
        .def(nb::init<size_t>(), nb::arg("world_count") = 0)
        .def(nb::init<const RuntimeBatchConfig &>(), nb::arg("config"))
        .def("batch_config", &RuntimeFacade::batch_config)
        .def("capabilities", &RuntimeFacade::capabilities)
        .def("admit_backend_request", &RuntimeFacade::admit_backend_request, nb::arg("request"))
        .def("admit_fidelity_request", &RuntimeFacade::admit_fidelity_request, nb::arg("request"))
        .def("world_count", &RuntimeFacade::world_count)
        .def("resize", &RuntimeFacade::resize, nb::arg("world_count"))
        .def("set_worker_threads", &RuntimeFacade::set_worker_threads, nb::arg("worker_threads"))
        .def("worker_threads", &RuntimeFacade::worker_threads)
        .def("effective_worker_threads", &RuntimeFacade::effective_worker_threads)
        .def("load_database", &RuntimeFacade::load_database, nb::arg("path"))
        .def(
            "load_unit_definitions",
            [](RuntimeFacade &self, const std::string &path) {
                std::string error;
                bool ok = self.load_unit_definitions(path, &error);
                if (!ok && !error.empty()) {
                    spdlog::warn("RuntimeFacade failed to load unit definitions: {}", error);
                }
                return ok;
            },
            nb::arg("path"))
        .def("reset_batch", [](RuntimeFacade &self) { self.reset_batch(BatchResetRequest{}); })
        .def("reset_batch", &RuntimeFacade::reset_batch, nb::arg("request"))
        .def("step_batch", &RuntimeFacade::step_batch)
        .def("apply_world_setup_batch", &RuntimeFacade::apply_world_setup_batch, nb::arg("seeds"),
             nb::arg("terrain_assignments"), nb::arg("wind_assignments"), nb::arg("zones"),
             nb::arg("requests"), nb::arg("time_steps") = std::vector<double>{},
             nb::arg("sun_assignments") = std::vector<WorldSunAssignment>{})
        .def("apply_world_setup", &RuntimeFacade::apply_world_setup, nb::arg("request"))
        .def("apply_world_layout", &RuntimeFacade::apply_world_layout, nb::arg("request"))
        .def("world_time_step", &RuntimeFacade::world_time_step, nb::arg("world_index"))
        .def("get_sensor_candidate_ids_batch", &RuntimeFacade::get_sensor_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("get_visual_candidate_ids_batch", &RuntimeFacade::get_visual_candidate_ids_batch,
             nb::arg("refs"), nb::arg("range_m") = 25000.0, nb::arg("use_gpu") = false)
        .def("get_comm_candidate_ids_batch", &RuntimeFacade::get_comm_candidate_ids_batch,
             nb::arg("refs"), nb::arg("use_gpu") = false)
        .def("set_pilot_actions_batch", &RuntimeFacade::set_pilot_actions_batch,
             nb::arg("assignments"))
        .def("apply_launch_requests_batch", &RuntimeFacade::apply_launch_requests_batch,
             nb::arg("requests"))
        .def("set_mission_commands_maintained_batch",
             &RuntimeFacade::set_mission_commands_maintained_batch, nb::arg("assignments"))
        .def("set_task_orders_maintained_batch", &RuntimeFacade::set_task_orders_maintained_batch,
             nb::arg("assignments"))
        .def("set_leader_intents_maintained_batch",
             &RuntimeFacade::set_leader_intents_maintained_batch, nb::arg("assignments"))
        .def("set_pilot_reports_maintained_batch",
             &RuntimeFacade::set_pilot_reports_maintained_batch, nb::arg("assignments"))
        .def("get_agent_observations_batch", &RuntimeFacade::get_agent_observations_batch,
             nb::arg("refs"))
        .def("get_instrument_states_batch", &RuntimeFacade::get_instrument_states_batch,
             nb::arg("refs"))
        .def("get_mission_commands_maintained_batch",
             &RuntimeFacade::get_mission_commands_maintained_batch, nb::arg("refs"))
        .def("get_task_orders_maintained_batch", &RuntimeFacade::get_task_orders_maintained_batch,
             nb::arg("refs"))
        .def("get_leader_intents_maintained_batch",
             &RuntimeFacade::get_leader_intents_maintained_batch, nb::arg("refs"))
        .def("get_pilot_reports_maintained_batch",
             &RuntimeFacade::get_pilot_reports_maintained_batch, nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade &self, const std::vector<WorldEntityRef> &refs) {
                return self.export_observation_packet(refs);
            },
            nb::arg("refs"))
        .def(
            "export_observation_packet",
            [](const RuntimeFacade &self, const ObservationBatchRequest &request) {
                return self.export_observation_packet(request);
            },
            nb::arg("request"))
        .def("export_tasking_packet", &RuntimeFacade::export_tasking_packet, nb::arg("request"))
        .def("export_engagement_event_packet", &RuntimeFacade::export_engagement_event_packet,
             nb::arg("request"))
        .def("export_diagnostics_traces", &RuntimeFacade::export_diagnostics_traces,
             nb::arg("request"))
        .def("run_window", &RuntimeFacade::run_window, nb::arg("request"));
}
