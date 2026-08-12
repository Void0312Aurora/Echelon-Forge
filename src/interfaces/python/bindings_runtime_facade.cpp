#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
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
        .def("configure_batch", &RuntimeFacade::configure_batch, nb::arg("config"))
        .def("batch_config", &RuntimeFacade::batch_config)
        .def("capabilities", &RuntimeFacade::capabilities)
        .def("admit_backend_request", &RuntimeFacade::admit_backend_request, nb::arg("request"))
        .def("admit_fidelity_request", &RuntimeFacade::admit_fidelity_request, nb::arg("request"))
        .def("snapshot_counterfactual_entity", &RuntimeFacade::snapshot_counterfactual_entity,
             nb::arg("ref"), nb::arg("fidelity_admission"), nb::arg("cadence_reason"),
             nb::arg("evidence_refs"))
        .def("restore_counterfactual_snapshot", &RuntimeFacade::restore_counterfactual_snapshot,
             nb::arg("request"))
        .def("run_counterfactual_branch", &RuntimeFacade::run_counterfactual_branch,
             nb::arg("request"))
        .def("run_counterfactual_experiment", &RuntimeFacade::run_counterfactual_experiment,
             nb::arg("request"))
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
        .def("clear_execution_episode_batch", &RuntimeFacade::clear_execution_episode_batch)
        .def("prime_execution_episode_batch", &RuntimeFacade::prime_execution_episode_batch,
             nb::arg("refs"), nb::arg("states"))
        .def("execution_episode_ready", &RuntimeFacade::execution_episode_ready,
             nb::arg("world_index"))
        .def("export_execution_episode_states", &RuntimeFacade::export_execution_episode_states,
             nb::arg("refs"))
        .def("evaluate_execution_batch", &RuntimeFacade::evaluate_execution_batch,
             nb::arg("requests"))
        .def("step_execution_products_batch", &RuntimeFacade::step_execution_products_batch,
             nb::arg("requests"))
        .def("step_execution_batch", &RuntimeFacade::step_execution_batch, nb::arg("request"))
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
        .def("run_window", &RuntimeFacade::run_window, nb::arg("request"))
        // Additive run-global snapshot-version and trace-id producers. They are
        // not wired into any existing export path without explicit opt-in.
        .def("allocate_run_snapshot_version", &RuntimeFacade::allocate_run_snapshot_version)
        .def("peek_next_run_snapshot_version", &RuntimeFacade::peek_next_run_snapshot_version)
        .def("allocate_trace_id", &RuntimeFacade::allocate_trace_id)
        .def("peek_next_trace_id", &RuntimeFacade::peek_next_trace_id)
        // Additive read-only declaration export of the maintained observation
        // view.
        // Not wired into any existing export path; gated against the Python
        // registry by the export-parity architecture test.
        .def("describe_maintained_observation_view",
             &RuntimeFacade::describe_maintained_observation_view)
        // Additive read-only maintained-run replay-envelope producer. Not wired
        // into any existing path; only meaningful against window evidence
        // stamped by the facade-evidence opt-in
        // (use_facade_evidence_producers=True) adapter path. See the
        // declaration comment in runtime_facade.h for the field sources, the
        // "replay:maintained:*" id namespace, and the opt-in
        // `run_snapshot_version` qualification (default 0 = off, keeping
        // the packet's per-export provenance string byte-identical).
        .def("build_maintained_replay_envelope", &RuntimeFacade::build_maintained_replay_envelope,
             nb::arg("window_result"), nb::arg("run_id"), nb::arg("episode_id"),
             nb::arg("deterministic_seed"), nb::arg("run_snapshot_version") = 0)
        // Additive read-only maintained engagement-packet ancestry producer. It
        // is not wired into any existing path and is only meaningful against
        // window evidence stamped by the facade-evidence opt-in
        // (use_facade_evidence_producers=True) adapter path.
        // See the declaration comment in runtime_facade.h for the gate order,
        // the "ancestry:maintained:*" id namespace, and the root semantics of
        // parent_trace_id = 0 (default = no parent linkage, keeping every
        // trace copy's parent_trace_id at the existing default 0).
        .def("build_maintained_packet_ancestry", &RuntimeFacade::build_maintained_packet_ancestry,
             nb::arg("window_result"), nb::arg("run_id"), nb::arg("episode_id"),
             nb::arg("deterministic_seed"), nb::arg("parent_trace_id") = 0)
        // Additive read-only maintained worldline/counterfactual comparison
        // producer. It is not wired into any existing path and is only
        // meaningful against window evidence
        // stamped by the facade-evidence opt-in (use_facade_evidence_producers=True)
        // adapter path. See the declaration comment in runtime_facade.h for
        // the gate order, the "comparison:maintained:*" /
        // "worldline:maintained:*" id namespaces, and the no-truth-promotion
        // red line (evidence ids only, never copies of truth state).
        .def("build_maintained_worldline_comparison",
             &RuntimeFacade::build_maintained_worldline_comparison,
             nb::arg("baseline_window_result"), nb::arg("candidate_window_result"),
             nb::arg("run_id"), nb::arg("episode_id"), nb::arg("baseline_deterministic_seed"),
             nb::arg("candidate_deterministic_seed"), nb::arg("baseline_parent_trace_id") = 0,
             nb::arg("candidate_parent_trace_id") = 0);
}
