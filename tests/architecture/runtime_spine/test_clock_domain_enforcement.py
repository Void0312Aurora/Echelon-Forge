from __future__ import annotations

import textwrap

import pytest

from tests.architecture.helpers import (
  REPO_ROOT,
  compile_cpp_snippet,
  dependency_include_path,
  dependency_link_args,
)


def _optional_dependency_include(dependency: str):
  """Resolve a CMake dependency's include dir, or None when it is absent.

  `dependency_include_path` raises `AssertionError` at import time, which
  aborts collection for the whole module. Returning None instead lets the
  module collect so the dependency-free checks still run and the
  dependency-bound ones report SKIPPED rather than a collection error.
  """
  try:
    return dependency_include_path(dependency)
  except AssertionError:
    return None


FLECS_INCLUDE = _optional_dependency_include("flecs")
FLECS_LINK_ARGS = dependency_link_args("flecs")

# Governs the local-environment red recorded in the T6 residual ledger
# (docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md, section 5
# "flecs static-lib link-signature reds"): CPU build snapshots that ship
# only `_deps/flecs-build` without `_deps/flecs-src` cannot supply flecs
# headers. Conditional on actual dependency presence, mirroring the
# section 8.7 build-gpu-absent precedent -- on a build tree with the flecs
# source present these checks run unchanged.
requires_flecs = pytest.mark.skipif(
  FLECS_INCLUDE is None,
  reason=(
    "missing CMake dependency 'flecs' include directory in the configured "
    "CMO_BUILD_DIR (no _deps/flecs-src); see T6 residual ledger section 5"
  ),
)


def _compile_and_run(source: str):
  return compile_cpp_snippet(
    source,
    include_paths=(FLECS_INCLUDE,),
    link_args=FLECS_LINK_ARGS,
    binary_prefix="runtime_spine_clock_domain_enforcement",
  )


@requires_flecs
def test_wp16_runtime_window_coordinator_records_strict_selected_slice_clock_domain_gate() -> None:
  source = textwrap.dedent(
    r"""
    #include <algorithm>
    #include <iostream>
    #include <vector>
    #include "runtime/facade/runtime_window_coordinator.h"
    #include "runtime/contracts/stage_node_manifest_registry.h"

    int main() {
      using namespace runtime::scheduler;
      RuntimeWindowRequest request{};
      request.window_id = "window:wp16:trigger";
      request.world_id = 2;
      request.source_time_s = 3.0;

      RuntimeWindowActionRequest action{};
      action.source_layer = "policy";
      action.input_snapshot_version = "obs:3";
      action.action_intent.source_id = "policy:triggered";
      action.action_intent.effective_time_s = 3.0;
      action.action_intent.valid_until_s = 3.5;
      action.action_intent.target.world_index = 2;
      action.action_intent.target.entity_id = 42;
      action.action_intent.action_family = "direct_control";
      action.action_intent.merge_policy = "last_write_wins";
      action.action_intent.has_pilot_action = true;
      action.action_intent.pilot_action.throttle = 0.6;
      action.clock_domain_metadata.source_clock_domain = "policy.control_slot";
      action.clock_domain_metadata.clock_merge_policy = "nested_slot";
      action.clock_domain_metadata.has_source_time = true;
      action.clock_domain_metadata.source_time_s = 3.0;
      action.clock_domain_metadata.source_snapshot_version = "obs:3";
      action.cadence_control.enabled = true;
      action.cadence_control.hold_policy.hold_mode = "hold_last";
      action.cadence_control.hold_policy.validity_duration_s = 0.1;
      action.cadence_control.has_expiry_time = true;
      action.cadence_control.expiry_time_s = 3.1;
      request.action_requests.push_back(action);

      RuntimeWindowResult result = execute_runtime_window(
        request,
        RuntimeWindowCoordinatorCallbacks{
          .step_window = []() {},
          .export_observation_packet =
            [](const ObservationBatchRequest&) {
              ObservationBatchPacket packet{};
              packet.snapshot_version = 4;
              return packet;
            },
          .export_engagement_event_packet =
            [](const EngagementBatchRequest&) {
              EngagementEventPacket packet{};
              packet.snapshot_version = 4;
              return packet;
            },
          .export_diagnostics_traces =
            [](const EngagementBatchRequest&) {
              return std::vector<DiagnosticsTrace>{};
            },
        }
      );

      if (kClockDomainAdvisoryOnly != true) {
        std::cerr << "global advisory flag should stay unchanged\n";
        return 1;
      }
      const auto selected =
        enumerate_selected_slice_strict_clock_domain_manifests();
      if (selected.size() != 3) {
        std::cerr << "selected-slice strict helper drifted\n";
        return 1;
      }
      if (result.cadence_config.window_duration_s != 0.1 ||
        result.cadence_config.domains.size() != 4) {
        std::cerr << "selected-slice cadence config drifted\n";
        return 1;
      }
      if (result.cadence_trace.size() != 10) {
        std::cerr << "selected-slice cadence trace should expose 1/2/6/1 ticks\n";
        return 1;
      }

      if (result.executed_nodes.size() != 3) {
        std::cerr << "selected maintained slice should produce exactly three node records\n";
        return 1;
      }
      for (const auto& expected : {
           std::string("fire_control_launch.v1"),
           std::string("effects_damage.v1"),
           std::string("observation_export.v1"),
         }) {
        const auto it = std::find_if(
          result.executed_nodes.begin(),
          result.executed_nodes.end(),
          [&expected](const RuntimeWindowNodeExecutionRecord& record) {
            return record.node_id == expected;
          }
        );
        if (it == result.executed_nodes.end()) {
          std::cerr << "missing selected-slice node evidence: " << expected << "\n";
          return 1;
        }
        if (it->execution_state != "executed") {
          std::cerr << "selected-slice node did not execute: " << expected << "\n";
          return 1;
        }
      }
      std::size_t policy_ticks = 0;
      std::size_t control_ticks = 0;
      std::size_t physics_ticks = 0;
      std::size_t export_ticks = 0;
      bool saw_hold = false;
      for (const auto& record : result.cadence_trace) {
        if (record.domain == "policy") {
          ++policy_ticks;
        } else if (record.domain == "control") {
          ++control_ticks;
          saw_hold = saw_hold || record.held;
        } else if (record.domain == "physics") {
          ++physics_ticks;
        } else if (record.domain == "export") {
          ++export_ticks;
        }
      }
      if (policy_ticks != 1 || control_ticks != 2 ||
        physics_ticks != 6 || export_ticks != 1 || !saw_hold) {
        std::cerr << "cadence trace counts/hold evidence drifted\n";
        return 1;
      }

      const auto* compatibility =
        find_stage_node_manifest("launch_request_adapter_projection.v1");
      const auto* diagnostics =
        find_stage_node_manifest("observation_trace_diagnostics.v1");
      if (compatibility == nullptr || diagnostics == nullptr) {
        std::cerr << "missing excluded sibling manifests\n";
        return 1;
      }
      if (is_maintained_scheduler_truth(*compatibility) ||
        is_maintained_scheduler_truth(*diagnostics)) {
        std::cerr << "excluded siblings drifted into maintained truth\n";
        return 1;
      }
      for (const auto& record : result.executed_nodes) {
        if (record.node_id == compatibility->node_id ||
          record.node_id == diagnostics->node_id) {
          std::cerr << "excluded sibling leaked into selected-slice execution evidence\n";
          return 1;
        }
      }

      return 0;
    }
    """
  )
  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout
