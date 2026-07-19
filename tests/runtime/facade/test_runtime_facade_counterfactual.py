from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports
from python.runtime_bootstrap import resolve_repo_path


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
  return Path(resolve_repo_path(*parts)).read_text(encoding="utf-8")


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


class RuntimeFacadeCounterfactualTests(unittest.TestCase):
  def test_runtime_facade_counterfactual_restore_rejects_unsupported_claims(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    branch_result = facade.run_counterfactual_branch(_build_counterfactual_branch_request())
    self.assertTrue(bool(branch_result.admitted))

    def build_request() -> ef_py.RuntimeCounterfactualRestoreRequest:
      request = ef_py.RuntimeCounterfactualRestoreRequest()
      request.snapshot = branch_result.parent_snapshot
      request.expected_worldline_id = branch_result.parent_snapshot.worldline_id
      request.target_worldline_id = branch_result.branch_snapshot.worldline_id
      request.target_deterministic_seed = int(branch_result.branch_snapshot.deterministic_seed)
      request.target_entity_ref = _entity_ref(
        int(branch_result.branch_snapshot.world_index),
        int(branch_result.branch_snapshot.entity_id),
      )
      request.restore_barrier_id = branch_result.parent_snapshot.barrier_id
      request.evidence_refs = ["test:restore"]
      return request

    raw = build_request()
    raw.allow_raw_authoritative_state_mutation = True
    self.assertEqual(
      facade.restore_counterfactual_snapshot(raw).rejection_reason,
      "counterfactual_restore_raw_authoritative_state_mutation_forbidden",
    )

    full_clone = build_request()
    full_clone.request_full_clone = True
    self.assertEqual(
      facade.restore_counterfactual_snapshot(full_clone).rejection_reason,
      "counterfactual_restore_full_clone_not_supported",
    )

    resident = build_request()
    resident.request_resident_state_restore = True
    self.assertEqual(
      facade.restore_counterfactual_snapshot(resident).rejection_reason,
      "counterfactual_restore_resident_state_not_supported",
    )

    exact_gpu = build_request()
    exact_gpu.request_exact_gpu_restore = True
    self.assertEqual(
      facade.restore_counterfactual_snapshot(exact_gpu).rejection_reason,
      "counterfactual_restore_exact_gpu_not_supported",
    )

  def test_runtime_facade_counterfactual_restore_rejects_unregistered_or_mismatched_worldline(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    branch_result = facade.run_counterfactual_branch(_build_counterfactual_branch_request())
    self.assertTrue(bool(branch_result.admitted))

    request = ef_py.RuntimeCounterfactualRestoreRequest()
    request.snapshot = branch_result.parent_snapshot
    request.expected_worldline_id = "worldline:wrong"
    request.target_worldline_id = branch_result.branch_snapshot.worldline_id
    request.target_entity_ref = _entity_ref(
      int(branch_result.branch_snapshot.world_index),
      int(branch_result.branch_snapshot.entity_id),
    )
    request.restore_barrier_id = branch_result.parent_snapshot.barrier_id
    mismatch = facade.restore_counterfactual_snapshot(request)
    self.assertFalse(bool(mismatch.restored))
    self.assertEqual(mismatch.rejection_reason, "counterfactual_worldline_id_mismatch")

    request = ef_py.RuntimeCounterfactualRestoreRequest()
    request.snapshot = branch_result.parent_snapshot
    request.snapshot.worldline_id = "worldline:not-registered"
    request.expected_worldline_id = "worldline:not-registered"
    request.target_worldline_id = "worldline:not-registered"
    request.target_entity_ref = _entity_ref(
      int(branch_result.branch_snapshot.world_index),
      int(branch_result.branch_snapshot.entity_id),
    )
    request.restore_barrier_id = branch_result.parent_snapshot.barrier_id
    unregistered = facade.restore_counterfactual_snapshot(request)
    self.assertFalse(bool(unregistered.restored))
    self.assertEqual(
      unregistered.rejection_reason,
      "counterfactual_worldline_id_not_registered",
    )

  def test_runtime_facade_counterfactual_restore_can_seed_branch_worldline_from_parent_snapshot(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    branch_result = facade.run_counterfactual_branch(_build_counterfactual_branch_request())
    self.assertTrue(bool(branch_result.admitted))

    setup_result = facade.apply_world_setup(_build_single_aircraft_setup(seed=456))
    self.assertEqual(len(setup_result.entity_ids), 1)

    request = ef_py.RuntimeCounterfactualRestoreRequest()
    request.snapshot = branch_result.parent_snapshot
    request.expected_worldline_id = branch_result.parent_snapshot.worldline_id
    request.target_worldline_id = "worldline:wp17f:branch:restored"
    request.target_deterministic_seed = 456
    request.target_entity_ref = _entity_ref(
      0,
      int(setup_result.entity_ids[0]),
    )
    request.restore_barrier_id = branch_result.parent_snapshot.barrier_id
    request.evidence_refs = ["test:branch-restore"]

    restored = facade.restore_counterfactual_snapshot(request)

    self.assertTrue(bool(restored.restored))
    self.assertEqual(restored.rejection_reason, "")
    self.assertEqual(
      restored.restored_snapshot.worldline_id,
      "worldline:wp17f:branch:restored",
    )
    self.assertEqual(
      restored.restored_snapshot.parent_worldline_id,
      branch_result.parent_snapshot.worldline_id,
    )
    self.assertEqual(int(restored.restored_snapshot.deterministic_seed), 456)
    self.assertEqual(
      int(restored.restored_snapshot.entity_id),
      int(setup_result.entity_ids[0]),
    )

  def test_runtime_facade_counterfactual_experiment_collects_evidence_without_truth_promotion(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = ef_py.RuntimeExperimentRequest()
    request.branch_request = _build_counterfactual_branch_request()
    request.experiment_run_id = "experiment_run:counterfactual:e"
    request.comparison_id = "comparison:counterfactual:e"
    request.setup_ref = "scenario:baseline:counterfactual:e"
    request.generation_ref = "scenario-gen:runtime:counterfactual:e"
    request.generated_input_ref = "scenario-gen:req:counterfactual:e"
    request.generated_input_baseline_scenario_ref = "scenario:baseline:counterfactual:e"
    request.capability_refs = ["capability_bundle:runtime_facade.counterfactual"]
    request.generated_input_evidence_refs = ["evidence:generation:counterfactual:e"]
    request.evidence_refs = ["evidence:experiment:counterfactual:e"]

    parent_step = ef_py.RuntimeExperimentStepRequest()
    parent_step.state = _build_route_state(1)
    parent_step.request = _build_route_request(1)
    parent_step.observation_ref = "profile_obs:parent:counterfactual:e"
    parent_step.profile_ref = "profile:parent:counterfactual:e"
    parent_step.claim_scope = "comparative"
    parent_step.evidence_refs = ["evidence:parent-step:counterfactual:e"]
    branch_step = ef_py.RuntimeExperimentStepRequest()
    branch_step.state = _build_route_state(1)
    branch_step.request = _build_route_request(1)
    branch_step.observation_ref = "profile_obs:branch:counterfactual:e"
    branch_step.profile_ref = "profile:branch:counterfactual:e"
    branch_step.claim_scope = "comparative"
    branch_step.evidence_refs = ["evidence:branch-step:counterfactual:e"]
    request.parent_step_requests = [parent_step]
    request.branch_step_requests = [branch_step]
    request.trace_ids = [9001]

    result = facade.run_counterfactual_experiment(request)

    self.assertTrue(bool(result.admitted), result.rejection_reason)
    self.assertEqual(result.rejection_reason, "")
    self.assertTrue(bool(result.branch_result.admitted))
    self.assertTrue(bool(result.ancestry.evidence_bridge_valid))
    self.assertFalse(bool(result.ancestry.evidence_bridge_fail_closed))
    self.assertEqual(result.ancestry.replay_envelope_ref, "replay:wp17f:0001")
    self.assertEqual(result.ancestry.branch_point_ref, "branch_point:wp17f:0001")
    self.assertEqual(result.ancestry.generated_input_ref, "scenario-gen:req:counterfactual:e")
    self.assertEqual(result.ancestry.backend_profile_ref, "cpu_exact.reference")
    self.assertEqual(result.ancestry.fidelity_profile_ref, "exact_evaluation")
    self.assertIn(
      "capability_bundle:runtime_facade.counterfactual",
      list(result.ancestry.capability_refs),
    )
    self.assertIn(
      "profile_obs:parent:counterfactual:e",
      list(result.ancestry.profile_observation_refs),
    )
    self.assertIn(
      "profile_obs:branch:counterfactual:e",
      list(result.ancestry.profile_observation_refs),
    )
    self.assertTrue(list(result.parent_step_result.rewards))
    self.assertTrue(list(result.branch_step_result.rewards))
    self.assertTrue(list(result.parent_observation_packet.agent_observations))
    self.assertTrue(list(result.branch_observation_packet.agent_observations))
    parent_observation = result.parent_observation_packet.agent_observations[0]
    branch_observation = result.branch_observation_packet.agent_observations[0]
    self.assertAlmostEqual(
      float(branch_observation.x) - float(parent_observation.x),
      25.0,
      places=6,
    )
    self.assertAlmostEqual(
      float(branch_observation.vy) - float(parent_observation.vy),
      5.0,
      places=6,
    )
    self.assertAlmostEqual(
      float(branch_observation.heading) - float(parent_observation.heading),
      15.0,
      places=6,
    )
    self.assertIn(
      "claim_boundary=non_truth_claim_observation_only",
      list(result.ancestry.evidence_refs),
    )
    self.assertIn(
      "promotion_state=not_promoted",
      list(result.ancestry.evidence_refs),
    )

  def test_runtime_facade_counterfactual_experiment_rejects_truth_and_support_promotion(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    truth_claim = ef_py.RuntimeExperimentRequest()
    truth_claim.branch_request = _build_counterfactual_branch_request()
    truth_claim.truth_claim = True

    truth_result = facade.run_counterfactual_experiment(truth_claim)

    self.assertFalse(bool(truth_result.admitted))
    self.assertEqual(
      truth_result.rejection_reason,
      "counterfactual_experiment_truth_claim_forbidden",
    )

    promoted = ef_py.RuntimeExperimentRequest()
    promoted.branch_request = _build_counterfactual_branch_request()
    promoted.promoted_to_support = True

    promoted_result = facade.run_counterfactual_experiment(promoted)

    self.assertFalse(bool(promoted_result.admitted))
    self.assertEqual(
      promoted_result.rejection_reason,
      "counterfactual_experiment_support_promotion_forbidden",
    )

  def test_runtime_facade_counterfactual_branch_rejects_unmaintained_fidelity(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    request = _build_counterfactual_branch_request()
    request.fidelity_request.provider_family = "resident_state"

    result = facade.run_counterfactual_branch(request)

    self.assertFalse(bool(result.admitted))
    self.assertEqual(result.rejection_reason, "counterfactual_fidelity_request_not_admitted")
    self.assertFalse(bool(result.fidelity_admission.admitted))
    self.assertEqual(
      result.fidelity_admission.rejection_reason,
      "resident_state_fidelity_requires_maintained_backend_profile",
    )

  def test_runtime_facade_exports_typed_observation_packet(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    facade.load_database(resolve_repo_path("examples", "config", "database"))

    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [123]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = 0
    spawn.side = ef_py.Side.Blue
    spawn.type_name = "Aircraft"
    spawn.entity_name = "Lead"
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

    setup_result = facade.apply_world_setup(setup_request)
    self.assertEqual(len(setup_result.entity_ids), 1)

    ref = _entity_ref(0, int(setup_result.entity_ids[0]))
    obs_request = ef_py.ObservationBatchRequest()
    obs_request.refs = [ref]
    obs_request.include_agent_observations = True
    obs_request.include_instrument_states = True
    packet = facade.export_observation_packet(obs_request)

    self.assertEqual(len(packet.refs), 1)
    self.assertEqual(len(packet.agent_observations), 1)
    self.assertEqual(len(packet.instrument_states), 1)
    self.assertEqual(int(packet.agent_observations[0].id), int(setup_result.entity_ids[0]))

  def test_runtime_facade_tasking_packet_preserves_mission_command_n4_target_provenance(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))

    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [127]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = 0
    spawn.side = ef_py.Side.Blue
    spawn.type_name = "F-16C_Block50"
    spawn.entity_name = "ScreenLead"
    spawn.is_agent = True
    spawn.x = -1400.0
    spawn.y = 0.0
    spawn.z = 1200.0
    spawn.heading = 90.0
    spawn.vy = 180.0
    setup_request.terrain_assignments = [terrain]
    setup_request.spawn_requests = [spawn]
    setup_request.time_steps = [0.05]

    setup_result = facade.apply_world_setup(setup_request)
    ref = _entity_ref(0, int(setup_result.entity_ids[0]))
    assignment = ef_py.WorldMissionCommandMaintainedAssignment()
    assignment.world_index = 0
    assignment.entity_id = int(setup_result.entity_ids[0])
    assignment.mission_command.shared_core.command_code = 32
    assignment.mission_command.shared_core.assigned_target_id = 7001
    assignment.mission_command.shared_core.threat_state = 5
    assignment.mission_command.shared_core.assigned_target_track_id = 88001
    assignment.mission_command.shared_core.assigned_target_source_id = 99002
    assignment.mission_command.shared_core.assigned_target_snapshot_time_s = 223.5
    assignment.mission_command.shared_core.authorization_to_fire = True
    assignment.mission_command.shared_core.active = True
    facade.set_mission_commands_maintained_batch([assignment])

    tasking_request = ef_py.TaskingBatchRequest()
    tasking_request.refs = [ref]
    tasking_request.include_mission_command_contracts = True
    packet = facade.export_tasking_packet(tasking_request)

    self.assertEqual(len(packet.mission_command_contracts), 1)
    self.assertEqual(
      int(packet.mission_command_contracts[0].shared_core.assigned_target_id),
      7001,
    )
    self.assertEqual(int(packet.mission_command_contracts[0].shared_core.threat_state), 5)
    self.assertEqual(
      int(packet.mission_command_contracts[0].shared_core.assigned_target_track_id),
      88001,
    )
    self.assertEqual(
      int(packet.mission_command_contracts[0].shared_core.assigned_target_source_id),
      99002,
    )
    self.assertAlmostEqual(
      float(packet.mission_command_contracts[0].shared_core.assigned_target_snapshot_time_s),
      223.5,
      places=6,
    )
    self.assertEqual(packet.provenance.source_label, "facade_tasking_packet")
    self.assertEqual(packet.provenance.maintained_status, "adapter_projection")

  def test_runtime_facade_apply_world_setup_defaults_missing_terrain_assignment_to_flat(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))

    default_request = ef_py.BatchWorldSetupRequest()
    default_request.seeds = [123]
    default_spawn = ef_py.WorldSpawnRequest()
    default_spawn.world_index = 0
    default_spawn.side = ef_py.Side.Blue
    default_spawn.type_name = "Aircraft"
    default_spawn.entity_name = "FlatLead"
    default_spawn.is_agent = True
    default_spawn.x = 25000.0
    default_spawn.y = 25000.0
    default_spawn.z = 1200.0
    default_spawn.heading = 90.0
    default_spawn.vy = 180.0
    default_request.spawn_requests = [default_spawn]
    default_request.time_steps = [0.05]

    default_result = facade.apply_world_setup(default_request)
    facade.step_batch()
    default_inst = facade.get_instrument_states_batch([_entity_ref(0, int(default_result.entity_ids[0]))])[0]

    terrain_request = ef_py.BatchWorldSetupRequest()
    terrain_request.seeds = [124]
    legacy_terrain = ef_py.WorldTerrainAssignment()
    legacy_terrain.world_index = 0
    legacy_terrain.terrain_type = "legacy"
    terrain_spawn = ef_py.WorldSpawnRequest()
    terrain_spawn.world_index = 0
    terrain_spawn.side = ef_py.Side.Blue
    terrain_spawn.type_name = "Aircraft"
    terrain_spawn.entity_name = "TerrainLead"
    terrain_spawn.is_agent = True
    terrain_spawn.x = 25000.0
    terrain_spawn.y = 25000.0
    terrain_spawn.z = 1200.0
    terrain_spawn.heading = 90.0
    terrain_spawn.vy = 180.0
    terrain_request.terrain_assignments = [legacy_terrain]
    terrain_request.spawn_requests = [terrain_spawn]
    terrain_request.time_steps = [0.05]

    terrain_result = facade.apply_world_setup(terrain_request)
    facade.step_batch()
    terrain_inst = facade.get_instrument_states_batch([_entity_ref(0, int(terrain_result.entity_ids[0]))])[0]

    self.assertAlmostEqual(float(default_inst.alt_radar), 1200.0, delta=1.0)
    self.assertLess(float(terrain_inst.alt_radar), 1200.0 - 100.0)

  def test_runtime_facade_apply_world_setup_rejects_unknown_terrain_type(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))

    request = ef_py.BatchWorldSetupRequest()
    request.seeds = [125]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "desert"
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = 0
    spawn.side = ef_py.Side.Blue
    spawn.type_name = "Aircraft"
    spawn.entity_name = "BadTerrainLead"
    spawn.is_agent = True
    request.terrain_assignments = [terrain]
    request.spawn_requests = [spawn]
    request.time_steps = [0.05]

    with self.assertRaisesRegex(Exception, "Unknown terrain_type"):
      facade.apply_world_setup(request)

  def test_runtime_facade_typed_platform_setup_materializes_through_type_name_projection_bridge(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(
      facade.load_database(resolve_repo_path("examples", "config", "database"))
    )

    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [123]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    baseline_spawn = ef_py.WorldSpawnRequest()
    baseline_spawn.world_index = 0
    baseline_spawn.side = ef_py.Side.Blue
    baseline_spawn.type_name = "Aircraft"
    baseline_spawn.entity_name = "BaselineLead"
    baseline_spawn.is_agent = True
    baseline_spawn.x = -1400.0
    baseline_spawn.y = 0.0
    baseline_spawn.z = 1200.0
    baseline_spawn.heading = 90.0
    baseline_spawn.vy = 180.0
    setup_request.terrain_assignments = [terrain]
    setup_request.wind_assignments = [wind]
    setup_request.spawn_requests = [baseline_spawn]
    setup_request.typed_platform_spawn_requests = [
      _make_typed_platform_spawn_request()
    ]
    setup_request.time_steps = [0.05]

    setup_result = facade.apply_world_setup(setup_request)

    self.assertEqual(len(setup_result.entity_ids), 1)
    self.assertEqual(len(setup_result.typed_platform_spawn_results), 1)

    typed_result = setup_result.typed_platform_spawn_results[0]
    self.assertEqual(int(typed_result.request_index), 0)
    self.assertEqual(int(typed_result.world_index), 0)
    self.assertGreater(int(typed_result.entity_id), 0)
    self.assertTrue(bool(typed_result.admitted))
    self.assertTrue(bool(typed_result.materialized))
    self.assertFalse(bool(typed_result.fail_closed))
    self.assertEqual(typed_result.request_id, "typed-spawn:lead")
    self.assertEqual(typed_result.source_type_name, "Aircraft")
    self.assertEqual(typed_result.plan_id, "plan:typed-spawn:lead")
    self.assertEqual(typed_result.capability_bundle_id, "bundle:Aircraft")
    self.assertEqual(
      typed_result.setup_surface,
      "mixed_typed_setup_type_name_projection_bridge",
    )
    self.assertEqual(typed_result.rejection_reason, "")
    self.assertEqual(list(typed_result.errors), [])
    self.assertIn(
      "BatchWorldSetupRequest.typed_platform_spawn_requests",
      list(typed_result.evidence_refs),
    )
    self.assertIn("plan:typed-spawn:lead:evidence", list(typed_result.evidence_refs))
    self.assertIn(
      "RuntimeFacade.apply_world_setup.type_name_projection_typed_platform_spawn_bridge",
      list(typed_result.evidence_refs),
    )
    self.assertIn(
      "RuntimeFacade.apply_world_setup.type_name_projection_materialization",
      list(typed_result.evidence_refs),
    )
    self.assertNotEqual(int(typed_result.entity_id), int(setup_result.entity_ids[0]))

    observations = _public_observations_for_entity_range(
      facade,
      0,
      int(setup_result.entity_ids[0]),
      int(setup_result.entity_ids[0]) + 4,
    )
    self.assertTrue(
      _has_public_observation_at(
        observations,
        x=-1400.0,
        y=0.0,
        z=1200.0,
      )
    )
    self.assertTrue(
      _has_public_observation_at(
        observations,
        x=-1450.0,
        y=25.0,
        z=1200.0,
      )
    )

  def test_runtime_facade_typed_platform_setup_fail_closed_does_not_spawn_on_validation_or_world_guard(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(
      facade.load_database(resolve_repo_path("examples", "config", "database"))
    )

    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [123]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    setup_request.terrain_assignments = [terrain]
    setup_request.wind_assignments = [wind]

    invalid_request = _make_typed_platform_spawn_request(
      request_id="typed-spawn:invalid",
      entity_name="InvalidTypedLead",
    )
    invalid_request.request_id = ""

    out_of_range_request = _make_typed_platform_spawn_request(
      world_index=7,
      request_id="typed-spawn:oob",
      entity_name="OutOfRangeTypedLead",
    )

    setup_request.typed_platform_spawn_requests = [
      invalid_request,
      out_of_range_request,
    ]
    setup_request.time_steps = [0.05]

    setup_result = facade.apply_world_setup(setup_request)

    self.assertEqual(len(setup_result.entity_ids), 0)
    self.assertEqual(len(setup_result.typed_platform_spawn_results), 2)

    validation_failure = setup_result.typed_platform_spawn_results[0]
    self.assertEqual(int(validation_failure.request_index), 0)
    self.assertEqual(int(validation_failure.world_index), 0)
    self.assertEqual(int(validation_failure.entity_id), 0)
    self.assertFalse(bool(validation_failure.admitted))
    self.assertFalse(bool(validation_failure.materialized))
    self.assertTrue(bool(validation_failure.fail_closed))
    self.assertEqual(validation_failure.request_id, "")
    self.assertEqual(validation_failure.source_type_name, "Aircraft")
    self.assertEqual(validation_failure.plan_id, "plan:typed-spawn:invalid")
    self.assertEqual(validation_failure.capability_bundle_id, "bundle:Aircraft")
    self.assertEqual(
      validation_failure.rejection_reason,
      "typed_platform_spawn_request_id_required",
    )
    self.assertIn("request_id is required", list(validation_failure.errors))
    self.assertIn(
      "BatchWorldSetupRequest.typed_platform_spawn_requests",
      list(validation_failure.evidence_refs),
    )

    world_guard_failure = setup_result.typed_platform_spawn_results[1]
    self.assertEqual(int(world_guard_failure.request_index), 1)
    self.assertEqual(int(world_guard_failure.world_index), 7)
    self.assertEqual(int(world_guard_failure.entity_id), 0)
    self.assertFalse(bool(world_guard_failure.admitted))
    self.assertFalse(bool(world_guard_failure.materialized))
    self.assertTrue(bool(world_guard_failure.fail_closed))
    self.assertEqual(world_guard_failure.request_id, "typed-spawn:oob")
    self.assertEqual(world_guard_failure.source_type_name, "Aircraft")
    self.assertEqual(world_guard_failure.plan_id, "plan:typed-spawn:oob")
    self.assertEqual(world_guard_failure.capability_bundle_id, "bundle:Aircraft")
    self.assertEqual(
      world_guard_failure.rejection_reason,
      "typed_platform_spawn_world_index_out_of_range",
    )
    self.assertIn(
      "typed platform spawn world_index is outside the configured runtime batch",
      list(world_guard_failure.errors),
    )
    self.assertIn(
      "BatchWorldSetupRequest.typed_platform_spawn_requests",
      list(world_guard_failure.evidence_refs),
    )

    observations = _public_observations_for_entity_range(facade, 0, 1, 8)
    self.assertFalse(
      _has_public_observation_at(
        observations,
        x=-1450.0,
        y=25.0,
        z=1200.0,
      )
    )

  def test_runtime_facade_maintained_typed_setup_request_materializes_without_type_name_projection_rematerialization(self) -> None:
    facade = ef_py.RuntimeFacade(1)
    self.assertTrue(
      facade.load_database(resolve_repo_path("examples", "config", "database"))
    )

    setup_request = ef_py.BatchWorldSetupRequest()
    setup_request.seeds = [123]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    setup_request.terrain_assignments = [terrain]
    setup_request.wind_assignments = [wind]
    setup_request.typed_platform_spawn_requests = [
      _make_maintained_typed_platform_spawn_request()
    ]
    setup_request.time_steps = [0.05]

    setup_result = facade.apply_world_setup(setup_request)

    self.assertEqual(len(setup_result.entity_ids), 0)
    self.assertEqual(len(setup_result.typed_platform_spawn_results), 1)

    typed_result = setup_result.typed_platform_spawn_results[0]
    self.assertEqual(int(typed_result.request_index), 0)
    self.assertEqual(int(typed_result.world_index), 0)
    self.assertGreater(int(typed_result.entity_id), 0)
    self.assertTrue(bool(typed_result.admitted))
    self.assertTrue(bool(typed_result.materialized))
    self.assertFalse(bool(typed_result.fail_closed))
    self.assertEqual(
      str(typed_result.setup_surface),
      "maintained_typed_setup",
    )
    self.assertEqual(str(typed_result.rejection_reason), "")
    self.assertEqual(list(typed_result.errors), [])
    self.assertIn(
      "RuntimeFacade.apply_world_setup.maintained_typed_setup",
      list(typed_result.evidence_refs),
    )
    self.assertIn(
      "RuntimeFacade.apply_world_setup.maintained_typed_materialized",
      list(typed_result.evidence_refs),
    )
    self.assertNotIn(
      "RuntimeFacade.apply_world_setup.type_name_projection_materialization",
      list(typed_result.evidence_refs),
    )
    self.assertNotIn(
      "RuntimeFacade.apply_world_setup.type_name_projection_typed_platform_spawn_bridge",
      list(typed_result.evidence_refs),
    )

    observations = _public_observations_for_entity_range(
      facade,
      0,
      int(typed_result.entity_id),
      int(typed_result.entity_id) + 4,
    )
    self.assertTrue(
      _has_public_observation_at(
        observations,
        x=-1450.0,
        y=25.0,
        z=1200.0,
      )
    )

  def test_runtime_facade_step_execution_batch_returns_results_and_observations(self) -> None:
    entity_id = 77
    facade = ef_py.RuntimeFacade(1)

    ref = _entity_ref(0, entity_id)
    state = _build_route_state(entity_id)
    facade.prime_execution_episode_batch([ref], [state])

    exported_states = facade.export_execution_episode_states([ref])
    self.assertEqual(len(exported_states), 1)
    self.assertEqual(int(exported_states[0].agent_id), entity_id)

    batch_request = ef_py.ExecutionBatchStepRequest()
    batch_request.step_requests = [_build_route_request(entity_id)]
    batch_request.include_agent_observations = False

    result = facade.step_execution_batch(batch_request)
    post_step_exported_state = facade.export_execution_episode_states([ref])[0]

    self.assertEqual(len(result.step_results), 1)
    self.assertEqual(len(result.execution_episode_states), 1)
    self.assertEqual(len(result.rewards), 1)
    self.assertEqual(len(result.terminated), 1)
    self.assertEqual(len(result.truncated), 1)
    self.assertEqual(len(result.status_vectors), 1)
    self.assertEqual(len(result.termination_reasons), 1)
    self.assertEqual(len(result.reward_breakdown_jsons), 1)
    self.assertEqual(len(result.step_infos), 1)
    self.assertEqual(len(result.step_info_valid_flags), 1)
    self.assertEqual(len(result.controller_state_changed_flags), 1)
    self.assertEqual(len(result.observation_packet.refs), 1)
    self.assertEqual(len(result.observation_packet.agent_observations), 0)

    step_result = result.step_results[0]
    execution_episode_state = result.execution_episode_states[0]
    self.assertTrue(bool(step_result.valid))
    self.assertTrue(bool(step_result.structural_state_changed))
    self.assertAlmostEqual(float(result.rewards[0]), float(step_result.reward_total), places=6)
    self.assertEqual(bool(result.terminated[0]), bool(step_result.terminated))
    self.assertEqual(bool(result.truncated[0]), bool(step_result.truncated))
    self.assertEqual(
      [float(value) for value in result.status_vectors[0]],
      [
        float(step_result.status0),
        float(step_result.status1),
        float(step_result.status2),
        float(step_result.status3),
      ],
    )
    self.assertEqual(
      str(result.termination_reasons[0]),
      str(step_result.controller_state.last_termination_reason),
    )
    self.assertEqual(
      str(result.reward_breakdown_jsons[0]),
      str(step_result.controller_state.last_reward_breakdown_json),
    )
    self.assertEqual(bool(result.step_info_valid_flags[0]), bool(step_result.step_info_valid))
    self.assertEqual(
      float(result.step_infos[0].gear_stress),
      float(step_result.step_info.gear_stress),
    )
    self.assertEqual(
      bool(result.controller_state_changed_flags[0]),
      bool(step_result.structural_state_changed),
    )
    self.assertTrue(
      bool(ef_py.execution_episode_states_equivalent(execution_episode_state, post_step_exported_state))
    )
    self.assertEqual(int(execution_episode_state.mission_command.command_code), 2)
    self.assertEqual(str(execution_episode_state.mission_phase_name), "post_route")
    self.assertEqual(int(step_result.controller_state.mission_command.command_code), 2)
    self.assertEqual(str(step_result.controller_state.mission_phase_name), "post_route")

  def test_runtime_facade_step_execution_products_batch_advances_runtime_state(self) -> None:
    entity_id = 91
    facade = ef_py.RuntimeFacade(1)

    ref = _entity_ref(0, entity_id)
    state = _build_route_state(entity_id)
    facade.prime_execution_episode_batch([ref], [state])

    products = facade.step_execution_products_batch([_build_route_request(entity_id)])
    exported_states = facade.export_execution_episode_states([ref])

    self.assertEqual(len(products), 1)
    self.assertEqual(len(exported_states), 1)
    self.assertTrue(bool(products[0].valid))
    self.assertGreater(float(products[0].compiled_reward_total), 0.0)
    self.assertFalse(bool(products[0].terminated))
    self.assertEqual(str(exported_states[0].mission_phase_name), "post_route")
    self.assertEqual(int(exported_states[0].mission_command.command_code), 2)
    self.assertEqual(int(exported_states[0].step_count), 1)
    self.assertEqual(len(list(exported_states[0].route_waypoints)), 0)

  def test_runtime_facade_supports_batch_world_setup_via_packaged_scenario_runtime(self) -> None:
    scenario = {
      "scenario_name": "runtime_facade_batch_setup",
      "environment": {
        "time_step": 0.05,
        "terrain_type": "legacy",
        "wind": {
          "speed_mps": 4.0,
          "dir_from_deg": 180.0,
          "shear_mps_per_km": 0.0,
        },
        "zones": [
          {
            "name": "Runway_A",
            "x": 0.0,
            "y": 0.0,
            "width": 60.0,
            "length": 2500.0,
            "heading": 90.0,
            "surface": "Concrete",
          }
        ],
      },
      "mission_command": {
        "command_code": 2,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
      },
      "entities": [
        {
          "name": "Lead",
          "type": "Aircraft",
          "side": "Blue",
          "is_agent": True,
          "pos": [-1400.0, 0.0, 1200.0],
          "vel": [0.0, 180.0, 0.0],
          "heading": 90.0,
        },
        {
          "name": "Wing",
          "type": "Aircraft",
          "side": "Blue",
          "is_agent": False,
          "pos": [-1550.0, -120.0, 1200.0],
          "vel": [0.0, 180.0, 0.0],
          "heading": 90.0,
        },
      ],
    }
    compiled = ScenarioCompiler.compile_data(scenario)
    facade = ef_py.RuntimeFacade(2)
    self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))

    worlds = load_compiled_scenario_for_setup_target(
      facade,
      compiled,
      seeds=[11, 17],
      apply_buffer=BatchWorldApplyBuffer(2),
    )

    self.assertEqual(len(worlds), 2)
    self.assertIsNotNone(worlds[0].agent_id)
    self.assertIsNotNone(worlds[1].agent_id)
    self.assertIn("Lead", worlds[0].entities)
    self.assertIn("Wing", worlds[1].entities)

    refs = [_entity_ref(0, int(worlds[0].agent_id)), _entity_ref(1, int(worlds[1].agent_id))]
    obs_request = ef_py.ObservationBatchRequest()
    obs_request.refs = refs
    obs_request.include_agent_observations = True
    packet = facade.export_observation_packet(obs_request)
    obs0 = packet.agent_observations[0]
    obs1 = packet.agent_observations[1]
    self.assertEqual(int(obs0.id), int(worlds[0].agent_id))
    self.assertEqual(int(obs1.id), int(worlds[1].agent_id))



if __name__ == "__main__":
  unittest.main()
