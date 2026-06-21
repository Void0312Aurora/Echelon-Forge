from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter # noqa: E402
from python.scenario_compiler import ScenarioCompiler # noqa: E402
from python.scenario.runtime import BatchWorldApplyBuffer # noqa: E402
from python.scenario.runtime import active_roster_world_entity_refs # noqa: E402
from python.scenario.runtime import find_active_roster_member # noqa: E402
from python.scenario.runtime import load_compiled_scenario_for_setup_target # noqa: E402
from python.scenario.runtime import resolve_active_controllable_roster # noqa: E402


_RUNTIME_CAPABILITY_EXPECTATIONS = {
  "supports_batch_runtime": True,
  "supports_compiled_episode_controller": True,
  "supports_compiled_execution_step": True,
  "supports_gpu_visual": False,
  "supports_gpu_observation": False,
  "supports_gpu_flight_shaping": False,
  "supports_device_observation_view": False,
  "supports_resident_state": False,
  "supports_exact_gpu_backend": False,
  "supports_shadow_compare": False,
}

_RUNTIME_CAPABILITY_METADATA_EXPECTATIONS = {
  "maintained_baseline_backend_profile_id": "cpu_exact.reference",
  "maintained_baseline_parity_budget_ref": "parity_budget.cpu_exact.reference.v1",
  "maintained_baseline_profile_status": "maintained_exact_baseline",
  "device_observation_view_candidate_profile_id": "gpu_helpers.diagnostics_only",
  "device_observation_view_rejection_reason": (
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile"
  ),
  "exact_gpu_backend_candidate_profile_id": "gpu_exact.unmaintained_candidate",
  "exact_gpu_backend_rejection_reason": "gpu_exact.unmaintained_candidate_is_not_maintained",
  "resident_state_candidate_profile_id": "resident_state.unmaintained_candidate",
  "resident_state_candidate_parity_budget_ref": (
    "parity_budget.resident_state.unmaintained_candidate.v1"
  ),
  "resident_state_rejection_reason": (
    "resident_state.unmaintained_candidate_is_not_maintained"
  ),
  "shadow_compare_candidate_profile_id": "shadow_compare.unmaintained_candidate",
  "shadow_compare_candidate_parity_budget_ref": (
    "parity_budget.shadow_compare.unmaintained_candidate.v1"
  ),
  "shadow_compare_rejection_reason": (
    "shadow_compare.unmaintained_candidate_is_not_maintained"
  ),
  "multi_fidelity_rejection_reason": (
    "multi_fidelity_profiles_require_a_maintained_registry_revision_and_acceptance_gate"
  ),
}

_RUNTIME_FIDELITY_PROVIDER_FAMILY_EXPECTATIONS = {
  "none": "none",
  "reference_cpu": "reference_cpu",
}

_RUNTIME_FACADE_SOURCE_PARTS = (
  ("src", "runtime", "facade", "runtime_facade_world_setup.cpp"),
  ("src", "runtime", "facade", "runtime_facade_counterfactual.cpp"),
  ("src", "runtime", "facade", "runtime_facade_config.cpp"),
  ("src", "runtime", "facade", "runtime_facade_query.cpp"),
  ("src", "runtime", "facade", "runtime_facade_command_api.cpp"),
  ("src", "runtime", "facade", "runtime_facade_execution.cpp"),
  ("src", "runtime", "facade", "runtime_facade_packet.cpp"),
  ("src", "runtime", "facade", "runtime_facade.cpp"),
  ("src", "runtime", "facade", "runtime_facade_internal.h"),
)


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
  ref = ef_py.WorldEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _public_observations_for_entity_range(
  facade: ef_py.RuntimeFacade,
  world_index: int,
  start_entity_id: int,
  end_entity_id: int,
) -> list[ef_py.AgentObservation]:
  refs = [
    _entity_ref(world_index, entity_id)
    for entity_id in range(int(start_entity_id), int(end_entity_id))
  ]
  return list(facade.get_agent_observations_batch(refs))


def _has_public_observation_at(
  observations: list[ef_py.AgentObservation],
  *,
  x: float,
  y: float,
  z: float,
) -> bool:
  return any(
    abs(float(observation.x) - x) < 1e-6
    and abs(float(observation.y) - y) < 1e-6
    and abs(float(observation.z) - z) < 1e-6
    for observation in observations
  )


def _build_route_state(entity_id: int) -> ef_py.ExecutionEpisodeState:
  state = ef_py.ExecutionEpisodeState()
  state.agent_id = int(entity_id)
  state.has_mission_command = True
  state.mission_command.command_code = 3
  state.mission_command.cmd_heading_deg = 90.0
  state.mission_command.cmd_altitude_m = 1200.0
  state.mission_command.cmd_speed_mps = 180.0
  state.mission_command.active = True
  state.has_mission_command_json = True
  state.mission_command_json = json.dumps(
    {
      "command_code": 3,
      "route_ref_id": int(entity_id),
      "target_altitude": 1200.0,
      "target_heading": 90.0,
      "target_speed": 180.0,
      "waypoint_mode": "flyby",
      "waypoints": [
        {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
      ],
    },
    ensure_ascii=True,
    sort_keys=True,
  )
  route_waypoint = ef_py.SpatialRouteWaypoint()
  route_waypoint.x_m = -1350.0
  route_waypoint.y_m = 0.0
  route_waypoint.z_m = 1200.0
  route_waypoint.radius_m = 1200.0
  route_waypoint.altitude_m = 1200.0
  route_waypoint.speed_mps = 180.0
  route_waypoint.waypoint_mode = "flyby"
  state.route_waypoints = [route_waypoint]
  state.has_post_waypoint_transition_json = True
  state.post_waypoint_transition_json = json.dumps(
    {
      "command_code": 2,
      "phase_name": "post_route",
      "target_altitude": 900.0,
      "target_heading": 45.0,
      "target_speed": 160.0,
      "transition_reward": 123.0,
    },
    ensure_ascii=True,
    sort_keys=True,
  )
  return state


def _build_route_request(entity_id: int) -> ef_py.WorldExecutionEpisodeStepRequest:
  request = ef_py.WorldExecutionEpisodeStepRequest()
  request.world_index = 0
  request.entity_id = int(entity_id)
  request.config = ef_py.StepEvaluationBatchConfig()
  request.env_state.steps = 1
  request.env_state.truth_x = -1400.0
  request.env_state.truth_y = 0.0
  request.env_state.truth_z = 1200.0
  request.env_state.truth_speed = 180.0
  request.env_state.has_safety = True
  request.env_state.safety.finite_state_valid = True
  request.env_state.safety.health = 100.0
  request.env_state.safety.survival_reward = 0.02
  request.env_state.has_waypoint = True
  request.env_state.waypoint.valid = True
  request.env_state.waypoint.waypoint_index = 0
  request.env_state.waypoint.waypoint_count = 1
  request.env_state.waypoint.dist_m = 50.0
  request.env_state.waypoint.waypoint_radius_m = 1200.0
  request.env_state.waypoint.has_prev_dist = True
  request.env_state.waypoint.prev_dist_m = 120.0
  request.env_state.waypoint.progress_weight = 0.1
  request.env_state.waypoint.distance_weight = -0.001
  request.env_state.waypoint.reached_bonus = 20.0
  return request


def _build_single_aircraft_setup(seed: int = 123) -> ef_py.BatchWorldSetupRequest:
  setup_request = ef_py.BatchWorldSetupRequest()
  setup_request.seeds = [int(seed)]
  terrain = _default_world_terrain_assignment()
  wind = ef_py.WorldWindAssignment()
  wind.world_index = 0
  spawn = ef_py.WorldSpawnRequest()
  spawn.world_index = 0
  spawn.side = ef_py.Side.Blue
  spawn.type_name = "Aircraft"
  spawn.entity_name = "CounterfactualLead"
  spawn.is_agent = True
  spawn.x = -1400.0
  spawn.y = 0.0
  spawn.z = 1200.0
  spawn.heading = 90.0
  spawn.vy = 180.0
  setup_request.terrain_assignments = [terrain]
  setup_request.wind_assignments = [wind]
  setup_request.spawn_requests = [spawn]
  setup_request.time_steps = [0.05]
  return setup_request


def _default_world_terrain_assignment() -> ef_py.WorldTerrainAssignment:
  terrain = ef_py.WorldTerrainAssignment()
  terrain.world_index = 0
  return terrain


def _build_reference_fidelity_request() -> ef_py.RuntimeFidelityRequest:
  request = ef_py.RuntimeFidelityRequest()
  request.request_label = "exact_evaluation"
  request.backend_profile_id = "cpu_exact.reference"
  request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
  request.provider_family = "reference_cpu"
  request.model_family_scope = ["P0-P10 semantic lifecycle", "counterfactual_selected_slice"]
  request.validation_gate = "WP17-F selected counterfactual runtime slice"
  request.facade_evidence_refs = [
    "RuntimeFacade.admit_fidelity_request",
    "RuntimeFacade.run_counterfactual_branch",
  ]
  return request


def _make_typed_platform_spawn_request(
  *,
  world_index: int = 0,
  request_id: str = "typed-spawn:lead",
  source_type_name: str = "Aircraft",
  entity_name: str = "TypedLead",
) -> ef_py.TypedPlatformSpawnRequest:
  request = ef_py.TypedPlatformSpawnRequest()
  request.world_index = int(world_index)
  request.side = ef_py.Side.Blue
  request.request_id = request_id
  request.source_type_name = source_type_name
  request.entity_name = entity_name
  request.is_agent = True
  request.x = -1450.0
  request.y = 25.0
  request.z = 1200.0
  request.heading = 90.0
  request.vy = 180.0

  mobility = ef_py.PlatformCapability()
  mobility.capability_id = f"mobility:{source_type_name}"
  mobility.family = "mobility"
  mobility.capability_type = "fixed_wing_flight"
  mobility.implementation_ref = "DefaultUnitFactory"
  mobility.evidence_refs = [f"capability:{source_type_name}:mobility"]

  bundle = ef_py.CapabilityBundle()
  bundle.bundle_id = f"bundle:{source_type_name}"
  bundle.source_type_name = source_type_name
  bundle.capabilities = [mobility]
  bundle.template_evidence_ref = f"template:{source_type_name}"
  bundle.evidence_refs = [
    f"bundle:{source_type_name}:evidence",
    f"shared:{source_type_name}:evidence",
  ]
  bundle.type_name_projection_preserved = True
  request.capability_bundle = bundle

  plan = ef_py.ResolvedPlatformSpawnPlan()
  plan.plan_id = f"plan:{request_id}"
  plan.source_request_kind = "typed_platform_request"
  plan.source_type_name = source_type_name
  plan.capability_bundle_id = bundle.bundle_id
  plan.resolved_platform_definition_ref = f"definition:{source_type_name}"
  plan.materialization_strategy = "resolved_spawn_plan_bridge"
  plan.template_evidence_ref = bundle.template_evidence_ref
  plan.resolution_evidence_ref = f"resolution:{request_id}"
  plan.materialization_evidence_ref = f"materialization:{request_id}"
  plan.evidence_refs = [
    f"plan:{request_id}:evidence",
    f"shared:{source_type_name}:evidence",
  ]
  plan.resolved_capabilities = [mobility]
  plan.type_name_projection_preserved = True
  plan.admitted = True
  request.resolved_spawn_plan = plan
  request.facade_evidence_refs = [
    "BatchWorldSetupRequest.typed_platform_spawn_requests",
    f"facade:{request_id}",
  ]
  request.type_name_projection_preserved = True
  return request


def _make_maintained_typed_platform_spawn_request(
  *,
  world_index: int = 0,
  request_id: str = "typed-spawn:maintained",
  source_type_name: str = "Aircraft",
  entity_name: str = "MaintainedTypedLead",
) -> ef_py.TypedPlatformSpawnRequest:
  request = _make_typed_platform_spawn_request(
    world_index=world_index,
    request_id=request_id,
    source_type_name=source_type_name,
    entity_name=entity_name,
  )
  request.type_name_projection_preserved = False
  request.capability_bundle.type_name_projection_preserved = False
  request.resolved_spawn_plan.type_name_projection_preserved = False
  return request


def _build_counterfactual_branch_request() -> ef_py.RuntimeCounterfactualBranchRequest:
  request = ef_py.RuntimeCounterfactualBranchRequest()
  request.baseline_setup = _build_single_aircraft_setup()
  request.entity_ref = _entity_ref(0, 0)
  request.fidelity_request = _build_reference_fidelity_request()
  request.deterministic_seed = 123
  request.replay_envelope_id = "replay:wp17f:0001"
  request.branch_point_id = "branch_point:wp17f:0001"
  request.parent_worldline_id = "worldline:wp17f:baseline"
  request.branch_worldline_id = "worldline:wp17f:branch"
  request.restore_barrier_id = "counterfactual_selected_slice"
  request.mutation_dx = 25.0
  request.mutation_dvy = 5.0
  request.mutation_dheading = 15.0
  request.evidence_refs = ["cadence:wp17c:selected_slice"]
  return request


def _repo_text(*parts: str) -> str:
  if parts == ("src", "runtime", "facade", "runtime_facade.cpp"):
    return "\n".join(
      Path(resolve_repo_path(*source_parts)).read_text(encoding="utf-8")
      for source_parts in _RUNTIME_FACADE_SOURCE_PARTS
    )
  return Path(resolve_repo_path(*parts)).read_text(encoding="utf-8")


def _signature_match(source: str, signature: str) -> re.Match[str]:
  pattern = r"\s+".join(re.escape(part) for part in signature.split())
  match = re.search(pattern, source)
  if match is None:
    raise AssertionError(f"could not locate signature {signature}")
  return match


def _method_body(source: str, signature: str) -> str:
  start = _signature_match(source, signature).start()
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


class RuntimeFacadeCoreTests(unittest.TestCase):
  def test_world_terrain_assignment_defaults_to_non_legacy_mainline(self) -> None:
    terrain = _default_world_terrain_assignment()

    self.assertEqual(int(terrain.world_index), 0)
    self.assertEqual(str(terrain.terrain_type), "flat")

  def test_runtime_facade_fidelity_admission_admits_reference_baseline(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = ef_py.RuntimeFidelityRequest()
    request.request_label = "exact_evaluation"
    request.backend_profile_id = "cpu_exact.reference"
    request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
    request.provider_family = "reference_cpu"
    request.model_family_scope = [
      "P0-P10 semantic lifecycle",
      "observation_packet",
      "diagnostics_trace",
    ]
    request.validation_gate = (
      "WP17-D facade-owned exact-evaluation baseline admission"
    )
    request.facade_evidence_refs = [
      "RuntimeFacade.capabilities",
      "RuntimeFacade.admit_fidelity_request",
    ]

    admission = facade.admit_fidelity_request(request)

    self.assertTrue(bool(admission.admitted))
    self.assertTrue(bool(admission.baseline_exact_evaluation))
    self.assertEqual(admission.requested_provider_family, "reference_cpu")
    self.assertEqual(admission.selected_provider_family, "reference_cpu")
    self.assertEqual(admission.selected_stage_node_id, "observation_export.v1")
    self.assertEqual(admission.rejection_reason, "")
    self.assertIn("RuntimeFacade.capabilities", list(admission.evidence_refs))

  def test_runtime_facade_fidelity_admission_rejects_unmaintained_provider_families(self) -> None:
    facade = ef_py.RuntimeFacade(1)

    for provider_family, rejection in (
      ("gpu", "exact_gpu_fidelity_requires_maintained_backend_profile"),
      ("accelerated_exact", "exact_gpu_fidelity_requires_maintained_backend_profile"),
      ("resident_state", "resident_state_fidelity_requires_maintained_backend_profile"),
      ("shadow", "shadow_fidelity_requires_maintained_backend_profile"),
    ):
      request = ef_py.RuntimeFidelityRequest()
      request.request_label = "exact_evaluation"
      request.backend_profile_id = "cpu_exact.reference"
      request.parity_budget_ref = "parity_budget.cpu_exact.reference.v1"
      request.provider_family = provider_family
      request.model_family_scope = ["P0-P10 semantic lifecycle"]
      request.validation_gate = "WP17-D unsupported-provider fail-closed"
      request.facade_evidence_refs = ["RuntimeFacade.admit_fidelity_request"]

      admission = facade.admit_fidelity_request(request)

      self.assertFalse(bool(admission.admitted), msg=provider_family)
      self.assertEqual(admission.requested_provider_family, provider_family)
      self.assertEqual(admission.selected_provider_family, "none")
      self.assertEqual(admission.selected_stage_node_id, "")
      self.assertEqual(admission.rejection_reason, rejection)

  def test_runtime_facade_declares_engagement_packet_shell_types(self) -> None:
    header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")

    self.assertIn('#include "runtime/contracts/engagement_contracts.h"', header)
    self.assertIn("struct EngagementBatchRequest", header)
    self.assertIn("struct EngagementEventPacket", header)

    request_block = re.search(
      r"struct EngagementBatchRequest \{(?P<body>.*?)\};",
      header,
      flags=re.S,
    )
    self.assertIsNotNone(request_block)
    request_body = request_block.group("body")
    self.assertIn("std::vector<EngagementEntityRef> refs", request_body)
    self.assertIn("std::vector<std::uint64_t> trace_ids", request_body)
    for flag in [
      "include_track_packets",
      "include_launch_requests",
      "include_launch_events",
      "include_munition_lifecycle_packets",
      "include_effects_events",
      "include_damage_reports",
      "include_diagnostics_traces",
    ]:
      self.assertIn(flag, request_body)

    packet_block = re.search(
      r"struct EngagementEventPacket \{(?P<body>.*?)\};",
      header,
      flags=re.S,
    )
    self.assertIsNotNone(packet_block)
    packet_body = packet_block.group("body")
    for field in [
      "std::uint64_t snapshot_version",
      "std::string barrier_id",
      "std::uint64_t barrier_sequence",
      "std::string barrier_detail",
      "double source_time_s",
      "std::string producer_node_id",
      "InformationStateSource packet_provenance",
      "InformationStateSource diagnostics_provenance",
      "std::vector<EngagementEntityRef> refs",
      "std::vector<std::uint64_t> trace_ids",
      "std::vector<TrackPacket> track_packets",
      "std::vector<LaunchRequest> launch_requests",
      "std::vector<LaunchEvent> launch_events",
      "std::vector<MunitionLifecyclePacket> munition_lifecycle_packets",
      "std::vector<EffectsEvent> effects_events",
      "std::vector<DamageReport> damage_reports",
      "std::vector<PlatformConsequenceEvent> platform_consequence_events",
      "std::vector<DiagnosticsTrace> diagnostics_traces",
    ]:
      self.assertIn(field, packet_body)

    observation_block = re.search(
      r"struct ObservationBatchPacket \{(?P<body>.*?)\};",
      header,
      flags=re.S,
    )
    self.assertIsNotNone(observation_block)
    observation_body = observation_block.group("body")
    self.assertIn("InformationStateSource provenance", observation_body)

  def test_runtime_facade_exports_read_only_engagement_snapshot_without_weapon_escape(self) -> None:
    facade_header = _repo_text("src", "runtime", "facade", "runtime_facade.h")
    facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

    self.assertIn(
      "EngagementEventPacket export_engagement_event_packet("
      "const EngagementBatchRequest& request) const;",
      facade_header,
    )
    self.assertIn(
      "std::vector<DiagnosticsTrace> export_diagnostics_traces("
      "const EngagementBatchRequest& request) const;",
      facade_header,
    )

    body = _method_body(
      facade_source,
      "EngagementEventPacket RuntimeFacade::export_engagement_event_packet",
    )
    self.assertIn("EngagementEventPacket packet{}", body)
    self.assertIn("packet.refs = request.refs", body)
    self.assertIn("packet.trace_ids = request.trace_ids", body)
    self.assertIn("stable_sort_engagement_packet(&packet)", body)
    self.assertIn(
      "stable_sort_lethality_header_events(&packet->nearest_approach_events)",
      facade_source,
    )
    self.assertIn(
      "stable_sort_lethality_header_events(&packet->fuze_evaluation_events)",
      facade_source,
    )
    self.assertIn(
      "stable_sort_lethality_header_events(&packet->structural_breakup_events)",
      facade_source,
    )
    self.assertIn(
      "stable_sort_lethality_header_events(&packet->lifecycle_transition_events)",
      facade_source,
    )
    self.assertIn("stable_sort_platform_consequence_events(&packet->platform_consequence_events)", facade_source)
    self.assertIn("packet.nearest_approach_events.insert", facade_source)
    self.assertIn("packet.fuze_evaluation_events.insert", facade_source)
    self.assertIn("packet.warhead_mechanism_events.insert", facade_source)
    self.assertIn("packet.spatial_coverage_events.insert", facade_source)
    self.assertIn("packet.component_load_events.insert", facade_source)
    self.assertIn("packet.component_damage_events.insert", facade_source)
    self.assertIn("packet.structural_breakup_events.insert", facade_source)
    self.assertIn("packet.lifecycle_transition_events.insert", facade_source)
    self.assertIn("packet.platform_consequence_events.insert", facade_source)
    self.assertIn("assign_world_index(event.header, world_index)", facade_source)
    self.assertIn("apply_export_packet_metadata(", body)
    self.assertIn("finalize_recent_event_metadata(&packet)", body)
    self.assertIn("finalize_diagnostics_ancestry(&packet)", body)
    self.assertTrue(
      "get_agent_observations_batch" in body or "build_observation_packet" in body,
      "engagement export should read live AgentObservation contacts via the facade/runtime observation path",
    )
    self.assertIn("include_track_packets", body)
    self.assertIn("include_diagnostics_traces", body)
    self.assertIn("packet.track_packets.push_back", body)
    self.assertIn("packet.diagnostics_traces.push_back", body)
    self.assertIn("return packet", body)
    self.assertNotIn(".runtime(", body)
    self.assertNotIn("fire_missile", body)
    self.assertNotIn("fire_naval_weapon", body)
    for field in [
      "launch_requests",
      "launch_events",
      "munition_lifecycle_packets",
      "effects_events",
      "damage_reports",
    ]:
      self.assertNotIn(f"packet.{field}.push_back", body)
      self.assertNotIn(f"packet.{field} =", body)

  def test_runtime_facade_exports_dedicated_diagnostics_trace_surface(self) -> None:
    facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

    body = _method_body(
      facade_source,
      "std::vector<DiagnosticsTrace> RuntimeFacade::export_diagnostics_traces",
    )
    self.assertIn("std::vector<DiagnosticsTrace> traces", body)
    self.assertIn("append_recent_diagnostics_traces", body)
    self.assertIn("request.include_track_packets || request.include_diagnostics_traces", body)
    self.assertIn("runtime_->get_agent_observations_batch", body)
    self.assertIn("diagnostics_trace_from_track_packet", body)
    self.assertIn("stable_sort_diagnostics_traces(&traces)", body)
    self.assertNotIn("EngagementEventPacket packet{}", body)
    self.assertNotIn("fire_missile", body)
    self.assertNotIn("fire_naval_weapon", body)

  def test_resolve_active_controllable_roster_returns_active_members(self) -> None:
    scenario = {
      "scenario_name": "roster_resolution",
      "environment": {
        "time_step": 0.05,
        "terrain_type": "legacy",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        "zones": [],
      },
      "mission_command": {
        "command_code": 2,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
      },
      "entities": [
        {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True, "pos": [-1400.0, 0.0, 1200.0], "vel": [0.0, 180.0, 0.0], "heading": 90.0},
        {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True, "pos": [-1550.0, -120.0, 1200.0], "vel": [0.0, 180.0, 0.0], "heading": 90.0},
      ],
      "cooperative_roster": {
        "team_id": 7001,
        "members": [
          {
            "entity": "Lead",
            "role_code": 21,
            "formation_role_id": "ElementLead",
            "relative_slot_code": 11,
            "policy_route": "shared_execution",
          },
          {
            "entity": "Wing",
            "role_code": 22,
            "formation_role_id": "Wingman",
            "relative_slot_code": 12,
            "reference_entity": "Lead",
            "policy_route": "shared_execution",
          },
        ],
      },
    }

    compiled = ScenarioCompiler.compile_data(scenario)
    adapter = RuntimeFacadeAdapter(1)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))
    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[123])

    self.assertEqual(len(worlds), 1)
    roster = worlds[0].active_roster
    self.assertEqual(len(roster), 2)
    self.assertEqual({member.entity_name for member in roster}, {"Lead", "Wing"})
    self.assertEqual(int(roster[0].team_id), 7001)
    self.assertEqual(int(roster[0].role_code), 21)
    self.assertEqual(int(roster[1].reference_entity_id), int(worlds[0].entities["Lead"]))

  def test_resolve_active_controllable_roster_falls_back_to_agent_entities(self) -> None:
    scenario = {
      "scenario_name": "roster_fallback",
      "entities": [
        {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True},
        {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True},
        {"name": "Observer", "type": "Aircraft", "side": "Blue", "is_agent": False},
      ],
    }
    entities = {"Lead": 101, "Wing": 102, "Observer": 103}

    roster = resolve_active_controllable_roster(scenario, entities, world_index=7)

    self.assertEqual(len(roster), 2)
    self.assertEqual([int(member.world_index) for member in roster], [7, 7])
    self.assertEqual({member.entity_name for member in roster}, {"Lead", "Wing"})
    self.assertTrue(all(bool(member.is_agent) for member in roster))

  def test_active_roster_helpers_find_members_and_build_refs(self) -> None:
    scenario = {
      "scenario_name": "roster_helpers",
      "entities": [
        {"name": "Lead", "type": "Aircraft", "side": "Blue", "is_agent": True},
        {"name": "Wing", "type": "Aircraft", "side": "Blue", "is_agent": True},
      ],
      "cooperative_roster": {
        "team_id": 8001,
        "members": [
          {"entity": "Lead", "role_code": 21, "formation_role_id": "ElementLead"},
          {"entity": "Wing", "role_code": 22, "formation_role_id": "Wingman", "reference_entity": "Lead"},
        ],
      },
    }
    entities = {"Lead": 201, "Wing": 202}
    roster = resolve_active_controllable_roster(scenario, entities, world_index=3)

    wing = find_active_roster_member(roster, entity_name="Wing")
    self.assertIsNotNone(wing)
    self.assertEqual(int(wing.entity_id), 202)
    self.assertEqual(int(wing.reference_entity_id), 201)

    lead = find_active_roster_member(roster, role_code=21)
    self.assertIsNotNone(lead)
    self.assertEqual(str(lead.formation_role_id), "ElementLead")

    refs = active_roster_world_entity_refs(roster)
    self.assertEqual(len(refs), 2)
    self.assertEqual([int(ref.world_index) for ref in refs], [3, 3])
    self.assertEqual([int(ref.entity_id) for ref in refs], [201, 202])

  def test_runtime_facade_exposes_capabilities_and_batch_config(self) -> None:
    config = ef_py.RuntimeBatchConfig()
    config.world_count = 3
    config.worker_threads = 2

    facade = ef_py.RuntimeFacade(config)
    capabilities = facade.capabilities()
    returned = facade.batch_config()

    self.assertEqual(int(facade.world_count()), 3)
    self.assertEqual(int(returned.world_count), 3)
    self.assertEqual(int(returned.worker_threads), 2)
    for field, expected in _RUNTIME_CAPABILITY_EXPECTATIONS.items():
      self.assertTrue(hasattr(capabilities, field), msg=f"missing RuntimeCapabilities.{field}")
      self.assertIs(
        bool(getattr(capabilities, field)),
        expected,
        msg=f"unexpected RuntimeCapabilities.{field}",
      )

    for field, expected in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS.items():
      self.assertTrue(hasattr(capabilities, field), msg=f"missing RuntimeCapabilities.{field}")
      self.assertEqual(
        getattr(capabilities, field),
        expected,
        msg=f"unexpected RuntimeCapabilities.{field}",
      )

    self.assertFalse(bool(capabilities.supports_resident_state))
    self.assertFalse(bool(capabilities.supports_exact_gpu_backend))
    self.assertFalse(bool(capabilities.supports_shadow_compare))

  def test_runtime_facade_fidelity_surface_declares_provider_selection_metadata(self) -> None:
    header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")
    facade_header = _repo_text("src", "runtime", "facade", "runtime_facade.h")
    binding_source = _repo_text("src", "interfaces", "python", "bindings_runtime.cpp")
    facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

    for token in (
      "struct RuntimeFidelityRequest",
      "std::string provider_family = \"none\"",
      "struct RuntimeFidelityAdmission",
      "std::string requested_provider_family = \"none\"",
      "std::string selected_provider_family = \"none\"",
      "std::string selected_stage_node_id",
    ):
      self.assertIn(token, header)

    self.assertIn("RuntimeFidelityAdmission admit_fidelity_request(", facade_header)
    self.assertIn('"RuntimeFidelityRequest"', binding_source)
    self.assertIn('"RuntimeFidelityAdmission"', binding_source)
    self.assertIn('"admit_fidelity_request"', binding_source)

    for provider_family in _RUNTIME_FIDELITY_PROVIDER_FAMILY_EXPECTATIONS.values():
      self.assertIn(provider_family, facade_source)
    self.assertIn("observation_export.v1", facade_source)

  def test_runtime_capability_surface_declares_stable_backend_metadata_fields(self) -> None:
    header = _repo_text("src", "runtime", "facade", "runtime_facade_types.h")
    binding_source = _repo_text("src", "interfaces", "python", "bindings_runtime.cpp")
    facade_source = _repo_text("src", "runtime", "facade", "runtime_facade.cpp")

    for field in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS:
      self.assertIn(field, header)
      self.assertIn(f'"{field}"', binding_source)

    for value in _RUNTIME_CAPABILITY_METADATA_EXPECTATIONS.values():
      self.assertIn(value, facade_source)

  def test_runtime_facade_counterfactual_branch_reports_selected_slice_delta(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = _build_counterfactual_branch_request()

    result = facade.run_counterfactual_branch(request)

    self.assertTrue(bool(result.admitted))
    self.assertEqual(result.rejection_reason, "")
    self.assertTrue(bool(result.fidelity_admission.admitted))
    self.assertEqual(result.fidelity_admission.selected_provider_family, "reference_cpu")
    self.assertEqual(result.fidelity_admission.selected_stage_node_id, "observation_export.v1")
    self.assertEqual(result.parent_snapshot.worldline_id, request.parent_worldline_id)
    self.assertEqual(result.parent_snapshot.parent_worldline_id, request.parent_worldline_id)
    self.assertEqual(result.parent_snapshot.deterministic_seed, request.deterministic_seed)
    self.assertEqual(result.branch_snapshot.worldline_id, request.branch_worldline_id)
    self.assertEqual(result.branch_snapshot.parent_worldline_id, request.parent_worldline_id)
    self.assertEqual(result.parent_snapshot.barrier_id, "counterfactual_selected_slice")
    self.assertEqual(result.branch_snapshot.barrier_id, "counterfactual_selected_slice")
    self.assertEqual(result.parent_snapshot.cadence_reason, request.cadence_reason)
    self.assertEqual(result.branch_snapshot.provider_family, "reference_cpu")
    self.assertTrue(bool(result.comparison.comparable))
    self.assertEqual(result.comparison.parent_worldline_id, request.parent_worldline_id)
    self.assertEqual(result.comparison.branch_worldline_id, request.branch_worldline_id)
    self.assertAlmostEqual(float(result.comparison.dx), 25.0, places=6)
    self.assertAlmostEqual(float(result.comparison.dvy), 5.0, places=6)
    self.assertAlmostEqual(float(result.comparison.dheading), 15.0, places=6)
    self.assertTrue(bool(result.restore_result.restored))
    self.assertEqual(result.restore_result.rejection_reason, "")
    self.assertEqual(
      result.restore_result.restored_snapshot.worldline_id,
      request.branch_worldline_id,
    )
    self.assertEqual(
      result.restore_result.restored_snapshot.parent_worldline_id,
      request.parent_worldline_id,
    )
    self.assertEqual(
      int(result.restore_result.restored_snapshot.entity_id),
      int(result.branch_snapshot.entity_id),
    )
    self.assertIn("RuntimeFacade.run_counterfactual_branch", list(result.evidence_refs))
    self.assertIn("branch_point_id=branch_point:wp17f:0001", list(result.comparison.evidence_refs))

  def test_runtime_facade_counterfactual_branch_rejects_raw_authoritative_mutation(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = _build_counterfactual_branch_request()
    request.allow_raw_authoritative_state_mutation = True

    result = facade.run_counterfactual_branch(request)

    self.assertFalse(bool(result.admitted))
    self.assertEqual(
      result.rejection_reason,
      "counterfactual_raw_authoritative_state_mutation_forbidden",
    )

  def test_runtime_facade_counterfactual_snapshot_rejects_missing_entity(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    admission = facade.admit_fidelity_request(_build_reference_fidelity_request())

    with self.assertRaisesRegex(RuntimeError, "counterfactual_entity_missing_transform_or_velocity"):
      facade.snapshot_counterfactual_entity(
        _entity_ref(0, 999999),
        admission,
        "test:missing-entity",
        ["test:counterfactual-snapshot"],
      )



if __name__ == "__main__":
  unittest.main()
