from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FLECS_INCLUDE = REPO_ROOT / "build" / "_deps" / "flecs-src"
FLECS_STATIC_LIB = REPO_ROOT / "build" / "_deps" / "flecs-build" / "libflecs_static.a"


def _repo_text(*parts: str) -> str:
  return (REPO_ROOT / Path(*parts)).read_text(encoding="utf-8")


def _method_body(source: str, signature: str) -> str:
  start = source.index(signature)
  body_start = source.index("{", start)
  depth = 0
  for index in range(body_start, len(source)):
    char = source[index]
    if char == "{":
      depth += 1
    elif char == "}":
      depth -= 1
      if depth == 0:
        return source[body_start:index + 1]
  raise AssertionError(f"could not find method body for {signature}")


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
  binary = "/tmp/runtime_facade_window_loop_injection_test_bin"
  command = [
    "g++",
    "-std=c++20",
    "-I",
    str(REPO_ROOT / "src"),
  ]
  if FLECS_INCLUDE.is_dir():
    command.extend(["-I", str(FLECS_INCLUDE)])
  command.extend([
    "-x",
    "c++",
    "-",
    "-x",
    "none",
    "-o",
    binary,
  ])
  if FLECS_STATIC_LIB.is_file():
    command.append(str(FLECS_STATIC_LIB))
  compile_result = subprocess.run(
    command,
    input=source,
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )
  assert compile_result.returncode == 0, compile_result.stderr
  return subprocess.run(
    [binary],
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )


def test_runtime_facade_exposes_wp10_window_loop_api() -> None:
  header = _repo_text("src", "runtime", "facade", "runtime_facade.h")
  source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

  assert '#include "runtime/facade/runtime_window_coordinator.h"' in source
  assert "RuntimeWindowResult run_wp10_window(const RuntimeWindowRequest& request);" in header

  body = _method_body(
    source,
    "RuntimeWindowResult RuntimeFacade::run_wp10_window",
  )
  assert "return execute_runtime_window(" in body
  assert "set_pilot_actions_batch(assignments)" in body
  assert "set_mission_commands_maintained_batch(assignments)" in body
  assert "set_mission_commands_batch(assignments)" not in body
  assert "step_batch()" in body
  assert "export_observation_packet(observation_request)" in body
  assert "export_engagement_event_packet(engagement_request)" in body
  assert "export_diagnostics_traces(engagement_request)" in body
  assert ".runtime(" not in body


def test_runtime_window_coordinator_classifies_requests_and_records_visibility() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include <string>
    #include <vector>
    #include "runtime/facade/runtime_window_coordinator.h"

    namespace {

    RuntimeWindowActionRequest make_request(
      std::uint64_t world_id,
      std::uint64_t entity_id,
      std::string source_id,
      std::string source_layer,
      std::string snapshot_version,
      double effective_time_s,
      double valid_until_s,
      std::string merge_policy,
      bool with_pilot_action
    ) {
      RuntimeWindowActionRequest request{};
      request.source_layer = std::move(source_layer);
      request.input_snapshot_version = std::move(snapshot_version);
      request.action_intent.source_id = std::move(source_id);
      request.action_intent.effective_time_s = effective_time_s;
      request.action_intent.valid_until_s = valid_until_s;
      request.action_intent.target.world_index = world_id;
      request.action_intent.target.entity_id = entity_id;
      request.action_intent.action_family = "direct_control";
      request.action_intent.merge_policy = std::move(merge_policy);
      request.action_intent.has_pilot_action = with_pilot_action;
      if (with_pilot_action) {
        request.action_intent.pilot_action.throttle = 0.75;
      }
      return request;
    }

    } // namespace

    int main() {
      RuntimeWindowRequest request{};
      request.window_id = "window:test:7";
      request.world_id = 7;
      request.source_time_s = 10.0;
      request.cadence_config.window_duration_s = 0.1;
      request.cadence_config.domains = {
        RuntimeWindowCadence{
          .domain = "policy",
          .tick_count = 1,
          .interval_s = 0.1,
          .merge_policy = "nested_slot",
          .barrier_id = "input_injection",
        },
        RuntimeWindowCadence{
          .domain = "control",
          .tick_count = 2,
          .interval_s = 0.05,
          .merge_policy = "hold_last",
          .barrier_id = "input_injection",
        },
        RuntimeWindowCadence{
          .domain = "physics",
          .tick_count = 6,
          .interval_s = 1.0 / 60.0,
          .merge_policy = "enqueue_event",
          .barrier_id = "window_commit",
        },
        RuntimeWindowCadence{
          .domain = "export",
          .tick_count = 1,
          .interval_s = 0.1,
          .merge_policy = "nested_slot",
          .barrier_id = "export",
        },
      };
      auto accepted = make_request(
        7,
        101,
        "policy:accepted",
        "policy",
        "obs:10",
        10.0,
        10.5,
        "last_write_wins",
        true
      );
      accepted.cadence_control.enabled = true;
      accepted.cadence_control.hold_policy.hold_mode = "hold_last";
      accepted.cadence_control.hold_policy.validity_duration_s = 0.1;
      accepted.cadence_control.has_expiry_time = true;
      accepted.cadence_control.expiry_time_s = 10.04;
      request.action_requests.push_back(accepted);
      request.action_requests.push_back(make_request(
        7,
        102,
        "policy:future",
        "policy",
        "obs:10",
        12.0,
        12.5,
        "last_write_wins",
        true
      ));
      request.action_requests.push_back(make_request(
        7,
        103,
        "policy:expired",
        "policy",
        "obs:10",
        8.0,
        9.5,
        "last_write_wins",
        true
      ));
      request.action_requests.push_back(make_request(
        7,
        104,
        "policy:invalid",
        "",
        "",
        10.0,
        10.5,
        "append_only",
        true
      ));

      std::vector<std::string> callback_order;
      bool mission_apply_called = false;
      bool observation_request_ok = false;
      bool engagement_request_ok = false;
      bool diagnostics_request_ok = false;
      RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
          .apply_pilot_actions =
            [&callback_order](const std::vector<WorldPilotActionAssignment>& assignments) {
              if (assignments.size() != 1 ||
                assignments[0].world_index != 7 ||
                assignments[0].entity_id != 101) {
                callback_order.push_back("pilot_apply_bad");
                return;
              }
              callback_order.push_back("pilot_apply");
          },
        .apply_mission_commands =
            [&mission_apply_called](const std::vector<WorldMissionCommandMaintainedAssignment>&) {
              mission_apply_called = true;
            },
          .step_window = [&callback_order]() {
            callback_order.push_back("step");
          },
          .export_observation_packet =
            [&callback_order, &observation_request_ok](const ObservationBatchRequest& observation_request) {
              observation_request_ok =
                observation_request.refs.size() == 1 &&
                observation_request.refs[0].world_index == 7 &&
                observation_request.refs[0].entity_id == 101;
              callback_order.push_back("observation_export");
              ObservationBatchPacket packet{};
              packet.snapshot_version = 11;
              packet.barrier_id = "export";
              packet.source_time_s = 10.0;
              packet.provenance.information_state_layer = "AgentObservation";
              packet.provenance.source_label = "facade_observation_packet";
              packet.provenance.maintained_status = "maintained";
              packet.provenance.observation_packet_ids = {"obs:11"};
              packet.provenance.source_observation_versions = {"global:11"};
              packet.refs = observation_request.refs;
              return packet;
            },
          .export_engagement_event_packet =
            [&callback_order, &engagement_request_ok](const EngagementBatchRequest& engagement_request) {
              engagement_request_ok =
                engagement_request.refs.size() == 1 &&
                engagement_request.refs[0].world_index == 7 &&
                engagement_request.refs[0].entity_id == 101 &&
                engagement_request.trace_ids.size() == 1 &&
                engagement_request.trace_ids[0] == 1;
              callback_order.push_back("engagement_export");
              EngagementEventPacket packet{};
              packet.snapshot_version = 11;
              packet.barrier_id = "export";
              packet.barrier_sequence = 4;
              packet.barrier_detail = "maintained_facade_export";
              packet.source_time_s = 10.0;
              packet.producer_node_id = "p10.observation_export.v1";
              packet.packet_provenance.information_state_layer = "TrackState";
              packet.packet_provenance.source_label = "track_state_packet";
              packet.packet_provenance.maintained_status = "maintained";
              packet.packet_provenance.observation_packet_ids = {"eng:11"};
              packet.packet_provenance.source_observation_versions = {"track:11"};
              packet.diagnostics_provenance.information_state_layer = "DecisionBelief";
              packet.diagnostics_provenance.source_label = "world_truth_diagnostics";
              packet.diagnostics_provenance.maintained_status = "diagnostics_only";
              packet.diagnostics_provenance.observation_packet_ids = {"diag:11"};
              packet.diagnostics_provenance.source_observation_versions = {"diag:11"};
              packet.diagnostics_provenance.diagnostics_reason =
                "diagnostics_trace_surface_not_maintained_decision_path";
              packet.refs = engagement_request.refs;
              packet.trace_ids = engagement_request.trace_ids;
              packet.launch_events.push_back(LaunchEvent{
                .event_id = 701,
                .accepted = true,
                .event_time_s = 10.0,
                .producer_node_id = "p7.fire_control_launch.v1",
              });
              packet.effects_events.push_back(EffectsEvent{
                .event_id = 702,
                .detonation_time_s = 10.0,
                .producer_node_id = "p9.effects_damage.v1",
              });
              packet.damage_reports.push_back(DamageReport{
                .report_id = 703,
                .source_event_id = 702,
                .report_time_s = 10.0,
                .producer_node_id = "p9.effects_damage.v1",
              });
              packet.diagnostics_traces.push_back(DiagnosticsTrace{
                .trace_id = 77,
                .launch_event_id = 701,
                .source_snapshot_version = 11,
                .barrier_id = "export",
                .barrier_detail = "maintained_facade_export",
                .source_time_s = 10.0,
                .source_node_id = "p7.fire_control_launch.v1",
                .export_node_id = "p10.observation_export.v1",
              });
              return packet;
            },
          .export_diagnostics_traces =
            [&callback_order, &diagnostics_request_ok](const EngagementBatchRequest& engagement_request) {
              diagnostics_request_ok =
                engagement_request.refs.size() == 1 &&
                engagement_request.trace_ids.size() == 1;
              callback_order.push_back("diagnostics_export");
              return std::vector<DiagnosticsTrace>{
                DiagnosticsTrace{
                  .trace_id = 77,
                  .observation_packet_version = 11,
                },
              };
            },
        }
      );

      if (mission_apply_called) {
        std::cerr << "mission apply should not run\n";
        return 1;
      }
      if (result.context.window_id != "window:test:7" ||
        result.context.world_id != 7 ||
        result.context.source_time_s != 10.0) {
        std::cerr << "window context drifted\n";
        return 1;
      }
      if (result.context.accepted_inputs.size() != 1 ||
        result.context.deferred_inputs.size() != 1 ||
        result.context.expired_inputs.size() != 1 ||
        result.context.rejected_inputs.size() != 1) {
        std::cerr << "request classification drifted\n";
        return 1;
      }
      if (result.injected_inputs.size() != 1 ||
        result.injected_inputs[0].request.action_intent.source_id != "policy:accepted") {
        std::cerr << "accepted input was not injected\n";
        return 1;
      }
      if (result.cadence_config.window_duration_s != 0.1 ||
        result.cadence_config.domains.size() != 4 ||
        result.cadence_trace.size() != 10) {
        std::cerr << "cadence config/trace drifted\n";
        return 1;
      }
      if (result.visibility_trace.size() < 2 ||
        result.visibility_trace[0].visible_input_count != 0 ||
        result.visibility_trace[1].barrier_id != "input_injection" ||
        result.visibility_trace[1].visible_input_count != 1) {
        std::cerr << "input visibility drifted\n";
        return 1;
      }
      if (result.barrier_trace.size() < 3 ||
        result.barrier_trace.front().barrier_id != "input_injection" ||
        result.barrier_trace[result.barrier_trace.size() - 2].barrier_id != "window_commit" ||
        result.barrier_trace.back().barrier_id != "export") {
        std::cerr << "barrier sequence drifted\n";
        return 1;
      }
      for (std::size_t index = 1; index + 2 < result.barrier_trace.size(); ++index) {
        if (result.barrier_trace[index].barrier_id != "stage_publish") {
          std::cerr << "unexpected barrier between input_injection and window_commit\n";
          return 1;
        }
      }

      const auto p7 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p7.fire_control_launch.v1";
        }
      );
      const auto p9 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p9.effects_damage.v1";
        }
      );
      const auto p10 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p10.observation_export.v1";
        }
      );
      if (p7 == result.executed_nodes.end() ||
        p9 == result.executed_nodes.end() ||
        p10 == result.executed_nodes.end()) {
        std::cerr << "maintained registry node ids were not consumed\n";
        return 1;
      }
      if (p7->visible_input_count != 1 ||
        p9->visible_input_count != 0 ||
        p10->visible_input_count != 0) {
        std::cerr << "manifest read visibility drifted\n";
        return 1;
      }
      std::size_t policy_ticks = 0;
      std::size_t control_ticks = 0;
      std::size_t physics_ticks = 0;
      std::size_t export_ticks = 0;
      bool saw_control_trigger = false;
      bool saw_control_expired = false;
      for (const auto& trace : result.cadence_trace) {
        if (trace.domain == "policy") {
          ++policy_ticks;
        } else if (trace.domain == "control") {
          ++control_ticks;
          saw_control_trigger =
            saw_control_trigger || trace.decision == "triggered";
          saw_control_expired =
            saw_control_expired || trace.decision == "expired";
        } else if (trace.domain == "physics") {
          ++physics_ticks;
        } else if (trace.domain == "export") {
          ++export_ticks;
        }
      }
      if (policy_ticks != 1 || control_ticks != 2 ||
        physics_ticks != 6 || export_ticks != 1 ||
        !saw_control_trigger || !saw_control_expired) {
        std::cerr << "cadence trace counts or expiry evidence drifted\n";
        return 1;
      }
      if (p7->execution_state != "executed" ||
        p7->trigger_source != "input_injection:policy:accepted" ||
        p7->decision_barrier_id != "input_injection" ||
        p7->clock_merge_policy != "hold_last" ||
        p7->source_snapshot_version != "obs:10" ||
        p7->target_window_id != "window:test:7" ||
        p7->barrier_order.size() != 1 ||
        p7->barrier_order[0] != "input_injection") {
        std::cerr << "fire-control execution evidence drifted\n";
        return 1;
      }
      if (p9->execution_state != "executed" ||
        p9->trigger_source != "p7.fire_control_launch.v1:fire_control_and_launch" ||
        p9->decision_barrier_id != "window_commit" ||
        p9->clock_merge_policy != "enqueue_event" ||
        p9->barrier_order.size() != 2 ||
        p9->barrier_order[0] != "input_injection" ||
        p9->barrier_order[1] != "window_commit") {
        std::cerr << "effects/damage execution evidence drifted\n";
        return 1;
      }
      if (p10->execution_state != "executed" ||
        p10->trigger_source != "export:maintained_facade_export" ||
        p10->decision_barrier_id != "export" ||
        p10->clock_merge_policy != "nested_slot" ||
        p10->source_snapshot_version != "observation_packet:11" ||
        p10->barrier_order.size() != 2 ||
        p10->barrier_order[0] != "window_commit" ||
        p10->barrier_order[1] != "export") {
        std::cerr << "observation/export execution evidence drifted\n";
        return 1;
      }

      const std::vector<std::string> expected_order = {
        "pilot_apply",
        "step",
        "observation_export",
        "engagement_export",
        "diagnostics_export",
      };
      if (callback_order != expected_order) {
        std::cerr << "callback order drifted\n";
        return 1;
      }
      if (!observation_request_ok || !engagement_request_ok || !diagnostics_request_ok) {
        std::cerr << "derived export requests drifted\n";
        return 1;
      }
      if (result.observation_packet.barrier_id != "export" ||
        result.observation_packet.snapshot_version != 11 ||
        result.observation_packet.provenance.information_state_layer != "AgentObservation" ||
        result.observation_packet.provenance.source_label != "facade_observation_packet" ||
        result.observation_packet.provenance.maintained_status != "maintained" ||
        result.engagement_packet.refs.size() != 1 ||
        result.engagement_packet.snapshot_version != 11 ||
        result.engagement_packet.barrier_id != "export" ||
        result.engagement_packet.barrier_detail != "maintained_facade_export" ||
        result.engagement_packet.producer_node_id != "p10.observation_export.v1" ||
        result.engagement_packet.packet_provenance.information_state_layer != "TrackState" ||
        result.engagement_packet.packet_provenance.source_label != "track_state_packet" ||
        result.engagement_packet.packet_provenance.maintained_status != "maintained" ||
        result.engagement_packet.diagnostics_provenance.information_state_layer != "DecisionBelief" ||
        result.engagement_packet.diagnostics_provenance.source_label != "world_truth_diagnostics" ||
        result.engagement_packet.diagnostics_provenance.maintained_status != "diagnostics_only" ||
        result.engagement_packet.launch_events.size() != 1 ||
        result.engagement_packet.launch_events[0].producer_node_id != "p7.fire_control_launch.v1" ||
        result.engagement_packet.effects_events.size() != 1 ||
        result.engagement_packet.effects_events[0].producer_node_id != "p9.effects_damage.v1" ||
        result.engagement_packet.damage_reports.size() != 1 ||
        result.engagement_packet.damage_reports[0].producer_node_id != "p9.effects_damage.v1" ||
        result.engagement_packet.diagnostics_traces.size() != 1 ||
        result.engagement_packet.diagnostics_traces[0].source_node_id != "p7.fire_control_launch.v1" ||
        result.engagement_packet.diagnostics_traces[0].export_node_id != "p10.observation_export.v1" ||
        result.diagnostics_traces.size() != 1 ||
        result.context.current_barrier_id != "export") {
        std::cerr << "export products drifted\n";
        return 1;
      }
      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_runtime_window_coordinator_skips_and_rejects_nodes_with_clock_domain_evidence() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include <string>
    #include <vector>
    #include "runtime/facade/runtime_window_coordinator.h"

    int main() {
      RuntimeWindowRequest request{};
      request.window_id = "window:test:skip";
      request.world_id = 11;
      request.source_time_s = 5.0;
      request.export_observation = false;
      request.export_engagement = false;
      request.export_diagnostics = false;

      std::vector<std::string> callback_order;
      RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
          .step_window = [&callback_order]() {
            callback_order.push_back("step");
          },
        }
      );

      if (callback_order.size() != 1 || callback_order[0] != "step") {
        std::cerr << "window stepping should still occur once\n";
        return 1;
      }
      const auto p7 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p7.fire_control_launch.v1";
        }
      );
      const auto p9 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p9.effects_damage.v1";
        }
      );
      const auto p10 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p10.observation_export.v1";
        }
      );
      if (p7 == result.executed_nodes.end() ||
        p9 == result.executed_nodes.end() ||
        p10 == result.executed_nodes.end()) {
        std::cerr << "maintained nodes missing from evidence\n";
        return 1;
      }
      if (p7->execution_state != "skipped" ||
        p7->trigger_source != "input_injection:none" ||
        p7->decision_barrier_id != "input_injection") {
        std::cerr << "fire-control skip evidence drifted\n";
        return 1;
      }
      if (p9->execution_state != "skipped" ||
        p9->trigger_source != "window_commit:none" ||
        p9->decision_barrier_id != "window_commit") {
        std::cerr << "effects/damage skip evidence drifted\n";
        return 1;
      }
      if (p10->execution_state != "skipped" ||
        p10->trigger_source != "export:none" ||
        p10->decision_barrier_id != "export") {
        std::cerr << "export skip evidence drifted\n";
        return 1;
      }
      if (!result.observation_packet.refs.empty() ||
        !result.engagement_packet.refs.empty() ||
        !result.diagnostics_traces.empty()) {
        std::cerr << "skipped export should not leak packets\n";
        return 1;
      }
      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_runtime_window_coordinator_rejects_independent_domain_without_deterministic_merge_metadata() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include "runtime/facade/runtime_window_coordinator.h"

    int main() {
      RuntimeWindowRequest request{};
      request.window_id = "window:test:independent";
      request.world_id = 19;
      request.source_time_s = 7.0;
      request.export_observation = false;
      request.export_engagement = false;
      request.export_diagnostics = false;

      RuntimeWindowActionRequest action{};
      action.source_layer = "sensor";
      action.input_snapshot_version = "obs:7";
      action.action_intent.source_id = "sensor:independent";
      action.action_intent.effective_time_s = 7.0;
      action.action_intent.valid_until_s = 7.5;
      action.action_intent.target.world_index = 19;
      action.action_intent.target.entity_id = 301;
      action.action_intent.action_family = "direct_control";
      action.action_intent.merge_policy = "last_write_wins";
      action.action_intent.has_pilot_action = true;
      action.action_intent.pilot_action.throttle = 0.9;
      action.clock_domain_metadata.source_clock_domain = "sensor.scan_slot";
      action.clock_domain_metadata.relation = "independent";
      action.clock_domain_metadata.has_source_time = true;
      action.clock_domain_metadata.source_time_s = 7.0;
      request.action_requests.push_back(action);

      bool pilot_apply_called = false;
      RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
          .apply_pilot_actions =
            [&pilot_apply_called](const std::vector<WorldPilotActionAssignment>&) {
              pilot_apply_called = true;
            },
        }
      );

      if (pilot_apply_called) {
        std::cerr << "independent domain without merge metadata should fail closed\n";
        return 1;
      }
      if (!result.context.accepted_inputs.empty() ||
        result.context.rejected_inputs.size() != 1 ||
        !result.context.deferred_inputs.empty()) {
        std::cerr << "independent domain input classification drifted\n";
        return 1;
      }
      if (result.context.rejected_inputs[0].reason.find("clock_merge_policy") ==
        std::string::npos) {
        std::cerr << "missing merge metadata rejection reason\n";
        return 1;
      }
      const auto p7 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p7.fire_control_launch.v1";
        }
      );
      const auto p9 = std::find_if(
        result.executed_nodes.begin(),
        result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p9.effects_damage.v1";
        }
      );
      if (p7 == result.executed_nodes.end() || p9 == result.executed_nodes.end()) {
        std::cerr << "missing maintained node evidence\n";
        return 1;
      }
      if (p7->execution_state != "rejected" ||
        p7->clock_merge_policy != "reject_on_ambiguous_order" ||
        p7->trigger_source != "input_injection_rejected:sensor:independent") {
        std::cerr << "upstream rejection evidence drifted\n";
        return 1;
      }
      if (p9->execution_state != "rejected" ||
        p9->trigger_source != "p7.fire_control_launch.v1:rejected_upstream_trigger") {
        std::cerr << "downstream rejection evidence drifted\n";
        return 1;
      }
      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_runtime_window_coordinator_rejects_same_window_conflicts_to_avoid_hidden_order() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <vector>
    #include "runtime/facade/runtime_window_coordinator.h"

    int main() {
      RuntimeWindowRequest request{};
      request.world_id = 3;
      request.source_time_s = 4.0;
      request.action_requests.resize(2);
      for (std::size_t index = 0; index < request.action_requests.size(); ++index) {
        auto& action = request.action_requests[index];
        action.source_layer = "policy";
        action.input_snapshot_version = "obs:4";
        action.action_intent.source_id = "policy:" + std::to_string(index);
        action.action_intent.effective_time_s = 4.0;
        action.action_intent.valid_until_s = 4.2;
        action.action_intent.target.world_index = 3;
        action.action_intent.target.entity_id = 90;
        action.action_intent.action_family = "direct_control";
        action.action_intent.merge_policy = "last_write_wins";
        action.action_intent.has_pilot_action = true;
        action.action_intent.pilot_action.throttle = 0.5 + static_cast<double>(index);
      }

      bool apply_called = false;
      RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
          .apply_pilot_actions =
            [&apply_called](const std::vector<WorldPilotActionAssignment>&) {
              apply_called = true;
            },
        }
      );

      if (apply_called) {
        std::cerr << "conflicting same-window requests should fail closed\n";
        return 1;
      }
      if (!result.context.accepted_inputs.empty() ||
        result.context.rejected_inputs.size() != 2 ||
        !result.injected_inputs.empty()) {
        std::cerr << "same-window conflicts were not rejected\n";
        return 1;
      }
      if (result.visibility_trace.size() < 2 ||
        result.visibility_trace[1].visible_input_count != 0) {
        std::cerr << "conflicting requests leaked into injection visibility\n";
        return 1;
      }
      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_runtime_window_coordinator_records_hold_last_and_interpolate_evidence_without_claiming_maintained_interpolation() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include "runtime/facade/runtime_window_coordinator.h"

    RuntimeWindowActionRequest make_request(
      const std::string& source_id,
      const std::string& hold_mode,
      double expiry_time_s
    ) {
      RuntimeWindowActionRequest action{};
      action.source_layer = "policy";
      action.input_snapshot_version = "obs:20";
      action.action_intent.source_id = source_id;
      action.action_intent.effective_time_s = 20.0;
      action.action_intent.valid_until_s = 20.2;
      action.action_intent.target.world_index = 20;
      action.action_intent.target.entity_id = 401;
      action.action_intent.action_family = "direct_control";
      action.action_intent.merge_policy = "last_write_wins";
      action.action_intent.has_pilot_action = true;
      action.action_intent.pilot_action.throttle = 0.65;
      action.cadence_control.enabled = true;
      action.cadence_control.hold_policy.hold_mode = hold_mode;
      action.cadence_control.hold_policy.validity_duration_s = 0.1;
      action.cadence_control.has_expiry_time = true;
      action.cadence_control.expiry_time_s = expiry_time_s;
      return action;
    }

    int main() {
      RuntimeWindowRequest hold_request{};
      hold_request.window_id = "window:test:hold";
      hold_request.world_id = 20;
      hold_request.source_time_s = 20.0;
      hold_request.export_observation = false;
      hold_request.export_engagement = false;
      hold_request.export_diagnostics = false;
      hold_request.action_requests.push_back(
        make_request("policy:hold", "hold_last", 20.2)
      );

      RuntimeWindowResult hold_result = execute_runtime_window(
        hold_request,
        RuntimeWindowCoordinatorCallbacks{}
      );

      bool saw_hold = false;
      for (const auto& trace : hold_result.cadence_trace) {
        if (trace.domain == "control" && trace.decision == "held" && trace.held) {
          saw_hold = true;
        }
      }
      if (!saw_hold) {
        std::cerr << "missing hold_last cadence evidence\n";
        return 1;
      }

      RuntimeWindowRequest interpolate_request{};
      interpolate_request.window_id = "window:test:interpolate";
      interpolate_request.world_id = 20;
      interpolate_request.source_time_s = 20.0;
      interpolate_request.export_observation = false;
      interpolate_request.export_engagement = false;
      interpolate_request.export_diagnostics = false;
      interpolate_request.action_requests.push_back(
        make_request("policy:interpolate", "interpolate", 20.2)
      );

      RuntimeWindowResult interpolate_result = execute_runtime_window(
        interpolate_request,
        RuntimeWindowCoordinatorCallbacks{}
      );

      bool saw_interpolation = false;
      for (const auto& trace : interpolate_result.cadence_trace) {
        if (trace.domain == "control" &&
          trace.decision == "interpolated" &&
          trace.diagnostics_only) {
          saw_interpolation = true;
        }
      }
      if (!saw_interpolation) {
        std::cerr << "missing interpolation diagnostics evidence\n";
        return 1;
      }
      const auto p7 = std::find_if(
        interpolate_result.executed_nodes.begin(),
        interpolate_result.executed_nodes.end(),
        [](const RuntimeWindowNodeExecutionRecord& record) {
          return record.node_id == "p7.fire_control_launch.v1";
        }
      );
      if (p7 == interpolate_result.executed_nodes.end() ||
        p7->execution_state != "executed") {
        std::cerr << "interpolation should not replace maintained first control tick\n";
        return 1;
      }
      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout
