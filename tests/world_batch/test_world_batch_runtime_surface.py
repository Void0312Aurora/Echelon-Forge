from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import textwrap
import unittest
import uuid
from pathlib import Path

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter # noqa: E402
from python.rl.tasking.leader_tasking import infer_route_ref_id # noqa: E402
from python.scenario_compiler import ScenarioCompiler # noqa: E402
from python.scenario_compiler import ( # noqa: E402
  DEFAULT_TERRAIN_TYPE,
  TERRAIN_TYPE_SOURCE_COMPATIBILITY,
  TERRAIN_TYPE_SOURCE_DEFAULT,
  _clone_runtime_mission_command,
)
from python.scenario.runtime import ( # noqa: E402
  BatchWorldApplyBuffer,
  build_compiled_world_layout,
  load_compiled_scenario_for_setup_target,
  prepare_scenario_world_layout,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _compile_and_run_cpp_source(source: str) -> subprocess.CompletedProcess[str]:
  binary = Path(tempfile.gettempdir()) / f"wp24_k_world_batch_runtime_{uuid.uuid4().hex}"
  compile_result = subprocess.run(
    [
      "g++",
      "-std=c++20",
      "-I",
      str(REPO_ROOT / "src"),
      "-x",
      "c++",
      "-",
      "-o",
      str(binary),
    ],
    input=source,
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )
  if compile_result.returncode != 0:
    return compile_result
  result = subprocess.run(
    [str(binary)],
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )
  try:
    binary.unlink(missing_ok=True)
  except OSError:
    pass
  return result


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
  ref = ef_py.WorldEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _mission_assignment(world_index: int, entity_id: int, command) -> object:
  assignment = ef_py.WorldMissionCommandMaintainedAssignment()
  assignment.world_index = int(world_index)
  assignment.entity_id = int(entity_id)
  assignment.mission_command = ef_py.mission_command_maintained_batch_contract(command)
  return assignment


def _leader_intent_assignment(world_index: int, entity_id: int, intent) -> object:
  assignment = ef_py.WorldLeaderIntentMaintainedAssignment()
  assignment.world_index = int(world_index)
  assignment.entity_id = int(entity_id)
  assignment.leader_intent = ef_py.leader_intent_maintained_batch_contract(intent)
  return assignment


def _pilot_report_assignment(world_index: int, entity_id: int, report) -> object:
  assignment = ef_py.WorldPilotReportMaintainedAssignment()
  assignment.world_index = int(world_index)
  assignment.entity_id = int(entity_id)
  assignment.pilot_report = ef_py.pilot_report_maintained_batch_contract(report)
  return assignment


def _make_detection(target_id: int, *, range_m: float = 8000.0) -> ef_py.Detection:
  detection = ef_py.Detection()
  detection.target_id = int(target_id)
  detection.range = float(range_m)
  detection.bearing = 0.0
  detection.elevation = 0.0
  detection.closing_speed = 350.0
  detection.signal_strength = 1.0
  detection.detection_prob_used = 1.0
  detection.sensor_type = int(ef_py.SensorType.Radar)
  detection.local_sensor_hit = True
  detection.timestamp = 0.0
  return detection


def _spawn_request(
  *,
  world_index: int,
  type_name: str,
  entity_name: str,
  x: float,
  y: float,
  z: float = 1200.0,
  heading: float = 90.0,
  vy: float = 180.0,
  missiles_remaining: int = 2,
  max_missiles: int = 6,
  weapon_cooldown_s: float = 10.0,
  weapon_last_fire_time: float = 0.0,
) -> ef_py.WorldSpawnRequest:
  request = ef_py.WorldSpawnRequest()
  request.world_index = int(world_index)
  request.side = ef_py.Side.Blue
  request.type_name = type_name
  request.entity_name = entity_name
  request.is_agent = True
  request.x = float(x)
  request.y = float(y)
  request.z = float(z)
  request.heading = float(heading)
  request.vy = float(vy)
  request.ammo_override_enabled = True
  request.missiles_remaining = int(missiles_remaining)
  request.max_missiles = int(max_missiles)
  request.weapon_cooldown_override_enabled = True
  request.weapon_cooldown_s = float(weapon_cooldown_s)
  request.weapon_last_fire_time = float(weapon_last_fire_time)
  return request


def _assert_gpu_helper_capabilities_remain_fail_closed(testcase: unittest.TestCase) -> None:
  capabilities = ef_py.RuntimeFacade(1).capabilities()
  for field in (
    "supports_gpu_visual",
    "supports_gpu_observation",
    "supports_gpu_flight_shaping",
    "supports_device_observation_view",
    "supports_resident_state",
    "supports_exact_gpu_backend",
    "supports_shadow_compare",
  ):
    testcase.assertFalse(
      bool(getattr(capabilities, field)),
      msg=f"{field} must remain false after helper-backed candidate queries",
    )
  testcase.assertEqual(
    str(capabilities.device_observation_view_candidate_profile_id),
    "gpu_helpers.diagnostics_only",
  )
  testcase.assertEqual(
    str(capabilities.device_observation_view_rejection_reason),
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile",
  )


def _inline_batch_scenario() -> dict:
  return {
    "scenario_name": "phase4_batch_runtime_inline",
    "environment": {
      "time_step": 0.05,
      "terrain_type": "legacy",
      "wind": {
        "speed_mps": 6.0,
        "dir_from_deg": 210.0,
        "shear_mps_per_km": 0.5,
      },
      "randomization": {
        "world_yaw_range": [-20.0, 20.0],
        "world_yaw_origin": [0.0, 0.0],
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
        "randomization": {
          "along_body_m_range": [-100.0, 100.0],
          "cross_body_m_range": [-50.0, 50.0],
          "heading_offset_deg_range": [-5.0, 5.0],
        },
      },
      {
        "name": "Wing",
        "type": "Aircraft",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1550.0, -120.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 90.0,
      },
    ],
    "cooperative_roster": {
      "team_id": 7001,
      "element_id": 7001,
      "policy_route": "shared_execution",
      "members": [
        {
          "entity": "Lead",
          "role_code": 21,
          "formation_role_id": "ElementLead",
          "relative_slot_code": 11,
        },
        {
          "entity": "Wing",
          "role_code": 22,
          "formation_role_id": "Wingman",
          "relative_slot_code": 12,
          "reference_entity": "Lead",
        },
      ],
    },
  }


def _inline_route_scenario() -> dict:
  scenario = _inline_batch_scenario()
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "waypoints": [
      {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0},
      {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0},
    ],
  }
  return scenario


def _inline_route_template_scenario() -> dict:
  scenario = _inline_batch_scenario()
  scenario["environment"]["randomization"] = {
    "world_yaw_range": [20.0, 20.0],
    "world_yaw_origin": [0.0, 0.0],
    "rotate_mission_heading_with_world": True,
  }
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "randomization": {
      "waypoint_templates": [
        [
          {"x": 500.0, "y": 0.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 700.0},
          {"x": 2000.0, "y": 1000.0, "altitude_m": 1200.0, "speed_mps": 180.0, "radius_m": 700.0},
        ]
      ]
    },
  }
  return scenario


def _inline_route_generator_scenario() -> dict:
  scenario = _inline_batch_scenario()
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "randomization": {
      "route_generator": {
        "enabled": True,
        "waypoint_count_range": [3, 3],
        "first_leg_length_m_range": [4000.0, 4000.0],
        "subsequent_leg_length_m_range": [5000.0, 5000.0],
        "waypoint_radius_m_range": [700.0, 700.0],
        "speed_mps_range": [180.0, 180.0],
        "altitude_m_range": [1200.0, 1200.0],
        "turn_angle_deg_range": [20.0, 20.0],
        "min_turn_abs_deg": 5.0,
        "max_turn_abs_deg": 30.0,
      }
    },
  }
  return scenario


class WorldBatchRuntimeTests(unittest.TestCase):
  def test_world_batch_runtime_worker_thread_controls(self) -> None:
    batch = ef_py.WorldBatchRuntime(3)
    self.assertEqual(int(batch.worker_threads()), 1)
    self.assertGreaterEqual(int(batch.effective_worker_threads()), 1)
    self.assertLessEqual(int(batch.effective_worker_threads()), 3)

    batch.set_worker_threads(1)
    self.assertEqual(int(batch.worker_threads()), 1)
    self.assertEqual(int(batch.effective_worker_threads()), 1)

    batch.set_worker_threads(8)
    self.assertEqual(int(batch.worker_threads()), 8)
    self.assertEqual(int(batch.effective_worker_threads()), 3)

  def test_world_batch_runtime_step_execution_episode_results_batch_transitions_state(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)

    ref = _entity_ref(0, 77)
    state = ef_py.ExecutionEpisodeState()
    state.agent_id = 77
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
        "route_ref_id": 77,
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
    batch.prime_execution_episode_controller_batch([ref], [state])

    request = ef_py.WorldExecutionEpisodeStepRequest()
    request.world_index = 0
    request.entity_id = 77
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

    results = batch.step_execution_episode_results_batch([request])

    self.assertEqual(len(results), 1)
    result = results[0]
    self.assertTrue(bool(result.valid))
    self.assertTrue(bool(result.structural_state_changed))
    self.assertEqual(int(result.controller_state.mission_command.command_code), 2)
    self.assertEqual(str(result.controller_state.mission_phase_name), "post_route")
    self.assertEqual(len(list(result.controller_state.route_waypoints)), 0)
    self.assertAlmostEqual(
      float(json.loads(str(result.controller_state.last_reward_breakdown_json))["phase_transition_bonus"]),
      123.0,
      places=6,
    )

  def test_world_batch_runtime_steps_and_reads_observations(self) -> None:
    batch = ef_py.WorldBatchRuntime(2)
    self.assertEqual(int(batch.world_count()), 2)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.set_time_step(0.05)
    batch.reset_batch([7, 11])

    eid0 = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      -1400.0,
      0.0,
      2.1,
      90.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
    )
    eid1 = batch.world_raw_quarantine(1).spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      -2400.0,
      100.0,
      2.1,
      90.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
    )

    batch.step_batch()
    refs = [_entity_ref(0, eid0), _entity_ref(1, eid1)]
    obs = batch.get_agent_observations_batch(refs)
    inst = batch.get_instrument_states_batch(refs)

    self.assertEqual(len(obs), 2)
    self.assertEqual(len(inst), 2)
    self.assertEqual(int(obs[0].id), int(eid0))
    self.assertEqual(int(obs[1].id), int(eid1))
    self.assertGreaterEqual(float(obs[0].sim_time), 0.05)
    self.assertGreaterEqual(float(obs[1].sim_time), 0.05)
    self.assertNotEqual(float(obs[0].x), float(obs[1].x))

  def test_world_batch_runtime_controls_multiple_entities_within_same_world(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.set_time_step(0.05)
    batch.reset_batch([13])

    lead = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      -1400.0,
      0.0,
      1200.0,
      90.0,
      0.0,
      0.0,
      0.0,
      180.0,
      0.0,
    )
    wing = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      -1550.0,
      -120.0,
      1200.0,
      90.0,
      0.0,
      0.0,
      0.0,
      180.0,
      0.0,
    )
    refs = [_entity_ref(0, int(lead)), _entity_ref(0, int(wing))]
    initial_inst = batch.get_instrument_states_batch(refs)

    act0 = ef_py.PilotAction()
    act0.stick_roll = -0.35
    act0.throttle = 1.0
    act0.active = True
    act1 = ef_py.PilotAction()
    act1.stick_roll = 0.40
    act1.throttle = 0.25
    act1.active = True

    assign0 = ef_py.WorldPilotActionAssignment()
    assign0.world_index = 0
    assign0.entity_id = int(lead)
    assign0.action = act0
    assign1 = ef_py.WorldPilotActionAssignment()
    assign1.world_index = 0
    assign1.entity_id = int(wing)
    assign1.action = act1
    batch.set_pilot_actions_batch([assign0, assign1])

    for _ in range(3):
      batch.step_batch()

    obs = batch.get_agent_observations_batch(refs)
    inst = batch.get_instrument_states_batch(refs)

    self.assertEqual(len(obs), 2)
    self.assertEqual(len(inst), 2)
    self.assertGreater(float(obs[0].sim_time), 0.0)
    self.assertGreater(float(obs[1].sim_time), 0.0)
    self.assertNotAlmostEqual(float(inst[0].throttle_pos), float(initial_inst[0].throttle_pos), places=4)
    self.assertNotAlmostEqual(float(inst[1].throttle_pos), float(initial_inst[1].throttle_pos), places=4)
    self.assertAlmostEqual(float(inst[0].throttle_pos), 1.0, places=6)
    self.assertAlmostEqual(float(inst[1].throttle_pos), 0.25, places=6)
    self.assertGreater(float(inst[0].throttle_pos), float(inst[1].throttle_pos))

  def test_world_batch_runtime_applies_launch_request_as_single_shot_without_pilot_action(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    world = batch.world_raw_quarantine(0)
    world.set_time_step(0.05)
    shooter = int(
      world.spawn_unit(
        ef_py.Side.Red,
        "F-16C_Block50",
        0.0,
        0.0,
        1200.0,
        0.0,
        0.0,
        0.0,
        0.0,
        220.0,
        0.0,
      )
    )
    target = int(
      world.spawn_unit(
        ef_py.Side.Blue,
        "F-16C_Block50",
        0.0,
        8000.0,
        1200.0,
        180.0,
        0.0,
        0.0,
        0.0,
        -220.0,
        0.0,
      )
    )
    world.set_unit_ammo(shooter, 4, 4)
    world.set_weapon_cooldown(shooter, 0.0, -1.0)
    world.set_contact_list(shooter, [_make_detection(target)])

    request = ef_py.LaunchRequest()
    request.request_id = 77
    request.shooter.world_index = 0
    request.shooter.entity_id = shooter
    request.target_entity.world_index = 0
    request.target_entity.entity_id = target
    request.has_target_entity = True
    request.authority = "unit_test"
    request.requested_munition_family = "missile"

    events = batch.apply_launch_requests_batch([request])

    self.assertEqual(len(events), 1)
    self.assertTrue(bool(events[0].accepted))
    self.assertEqual(int(events[0].request_id), 77)
    self.assertTrue(bool(events[0].has_spawned_munition))
    self.assertEqual(
      int(batch.get_agent_observations_batch([_entity_ref(0, shooter)])[0].missiles_remaining),
      3,
    )

    for _ in range(3):
      batch.step_batch()

    self.assertEqual(
      int(batch.get_agent_observations_batch([_entity_ref(0, shooter)])[0].missiles_remaining),
      3,
    )

  def test_world_batch_runtime_applies_world_setup_batch(self) -> None:
    batch = ef_py.WorldBatchRuntime(2)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

    terrain0 = ef_py.WorldTerrainAssignment()
    terrain0.world_index = 0
    terrain0.terrain_type = "flat"
    terrain1 = ef_py.WorldTerrainAssignment()
    terrain1.world_index = 1
    terrain1.terrain_type = "legacy"

    wind0 = ef_py.WorldWindAssignment()
    wind0.world_index = 0
    wind0.speed_mps = 5.0
    wind0.dir_from_deg = 180.0
    wind0.shear_mps_per_km = 0.0
    wind1 = ef_py.WorldWindAssignment()
    wind1.world_index = 1
    wind1.speed_mps = 7.0
    wind1.dir_from_deg = 220.0
    wind1.shear_mps_per_km = 1.0

    zone0 = ef_py.WorldZoneDefinition()
    zone0.world_index = 0
    zone0.name = "Runway_A"
    zone0.x = 0.0
    zone0.y = 0.0
    zone0.width = 60.0
    zone0.length = 2000.0
    zone0.heading = 90.0
    zone0.surface_type = 0
    zone1 = ef_py.WorldZoneDefinition()
    zone1.world_index = 1
    zone1.name = "Runway_B"
    zone1.x = 100.0
    zone1.y = 50.0
    zone1.width = 70.0
    zone1.length = 2100.0
    zone1.heading = 45.0
    zone1.surface_type = 1

    spawn0 = ef_py.WorldSpawnRequest()
    spawn0.world_index = 0
    spawn0.side = ef_py.Side.Blue
    spawn0.type_name = "Aircraft"
    spawn0.entity_name = "Lead0"
    spawn0.is_agent = True
    spawn0.x = -1400.0
    spawn0.y = 0.0
    spawn0.z = 2.1
    spawn0.heading = 90.0
    spawn1 = ef_py.WorldSpawnRequest()
    spawn1.world_index = 1
    spawn1.side = ef_py.Side.Blue
    spawn1.type_name = "Aircraft"
    spawn1.entity_name = "Lead1"
    spawn1.is_agent = True
    spawn1.x = -2400.0
    spawn1.y = 100.0
    spawn1.z = 2.1
    spawn1.heading = 45.0

    entity_ids = batch.apply_world_setup_batch(
      [7, 11],
      [terrain0, terrain1],
      [wind0, wind1],
      [zone0, zone1],
      [spawn0, spawn1],
      [0.05, 0.08],
    )

    self.assertEqual(len(entity_ids), 2)
    refs = [_entity_ref(0, int(entity_ids[0])), _entity_ref(1, int(entity_ids[1]))]
    obs = batch.get_agent_observations_batch(refs)
    self.assertEqual(int(obs[0].id), int(entity_ids[0]))
    self.assertEqual(int(obs[1].id), int(entity_ids[1]))
    self.assertAlmostEqual(float(batch.world_raw_quarantine(0).get_time_step()), 0.05, places=6)
    self.assertAlmostEqual(float(batch.world_raw_quarantine(1).get_time_step()), 0.08, places=6)
    self.assertNotEqual(float(obs[0].x), float(obs[1].x))

  def test_spawn_units_batch_preserves_type_name_and_spawn_overrides(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([23])

    spawn = _spawn_request(
      world_index=0,
      type_name="F-16C_Block50",
      entity_name="SpawnBatchLead",
      x=-1200.0,
      y=50.0,
      missiles_remaining=2,
      max_missiles=8,
      weapon_cooldown_s=10.0,
      weapon_last_fire_time=0.0,
    )

    entity_ids = batch.spawn_units_batch([spawn])

    self.assertEqual(len(entity_ids), 1)
    self.assertGreater(int(entity_ids[0]), 0)
    obs = batch.world_raw_quarantine(0).get_agent_observation(int(entity_ids[0]))
    self.assertEqual(int(obs.id), int(entity_ids[0]))
    self.assertEqual(int(getattr(obs, "missiles_remaining", -1)), 2)
    self.assertFalse(bool(getattr(obs, "can_fire", True)))

  def test_apply_world_setup_batch_preserves_type_name_and_spawn_overrides(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "legacy"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    spawn = _spawn_request(
      world_index=0,
      type_name="Aircraft",
      entity_name="SetupBatchLead",
      x=-1400.0,
      y=0.0,
      missiles_remaining=1,
      max_missiles=4,
      weapon_cooldown_s=5.0,
      weapon_last_fire_time=0.0,
    )

    entity_ids = batch.apply_world_setup_batch(
      [29],
      [terrain],
      [wind],
      [],
      [spawn],
      [0.05],
    )

    self.assertEqual(len(entity_ids), 1)
    self.assertGreater(int(entity_ids[0]), 0)
    self.assertAlmostEqual(float(batch.world_raw_quarantine(0).get_time_step()), 0.05, places=6)
    obs = batch.get_agent_observations_batch([_entity_ref(0, int(entity_ids[0]))])[0]
    self.assertEqual(int(obs.id), int(entity_ids[0]))
    self.assertEqual(int(getattr(obs, "missiles_remaining", -1)), 1)
    self.assertFalse(bool(getattr(obs, "can_fire", True)))

  def test_apply_world_setup_batch_rejects_unknown_terrain_type(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "desert"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    spawn = _spawn_request(
      world_index=0,
      type_name="Aircraft",
      entity_name="BadTerrainLead",
      x=-1400.0,
      y=0.0,
    )

    with self.assertRaisesRegex(Exception, "Unknown terrain_type"):
      batch.apply_world_setup_batch([31], [terrain], [wind], [], [spawn], [0.05])

  def test_apply_world_setup_batch_defaults_missing_terrain_assignment_to_flat(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

    legacy_spawn = _spawn_request(
      world_index=0,
      type_name="Aircraft",
      entity_name="LegacyTerrainLead",
      x=25000.0,
      y=25000.0,
      z=1200.0,
    )
    legacy_ids = batch.apply_world_setup_batch(
      [31],
      [],
      [],
      [],
      [legacy_spawn],
      [0.05],
    )
    batch.step_batch()
    legacy_inst = batch.get_instrument_states_batch([_entity_ref(0, int(legacy_ids[0]))])[0]

    explicit_legacy = ef_py.WorldTerrainAssignment()
    explicit_legacy.world_index = 0
    explicit_legacy.terrain_type = "legacy"
    compat_spawn = _spawn_request(
      world_index=0,
      type_name="Aircraft",
      entity_name="CompatTerrainLead",
      x=25000.0,
      y=25000.0,
      z=1200.0,
    )
    compat_ids = batch.apply_world_setup_batch(
      [32],
      [explicit_legacy],
      [],
      [],
      [compat_spawn],
      [0.05],
    )
    batch.step_batch()
    compat_inst = batch.get_instrument_states_batch([_entity_ref(0, int(compat_ids[0]))])[0]

    self.assertAlmostEqual(float(legacy_inst.alt_radar), 1200.0, places=2)
    self.assertLess(float(compat_inst.alt_radar), 1200.0 - 100.0)

  def test_world_batch_runtime_command_chain_roundtrip(self) -> None:
    batch = ef_py.WorldBatchRuntime(2)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([3, 5])

    eid0 = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Blue, "Aircraft", -1400.0, 0.0, 2.1, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    eid1 = batch.world_raw_quarantine(1).spawn_unit(ef_py.Side.Blue, "Aircraft", -1400.0, 0.0, 2.1, 90.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    batch.world_raw_quarantine(0).set_command_link(eid0, 0.0, 0.0)
    batch.world_raw_quarantine(1).set_command_link(eid1, 0.0, 0.0)
    refs = [_entity_ref(0, eid0), _entity_ref(1, eid1)]

    cmd0 = ef_py.MissionCommand()
    cmd0.command_code = 2
    cmd0.cmd_heading_deg = 45.0
    cmd0.cmd_altitude_m = 1200.0
    cmd0.cmd_speed_mps = 180.0
    cmd0.active = True

    cmd1 = ef_py.MissionCommand()
    cmd1.command_code = 4
    cmd1.cmd_heading_deg = 90.0
    cmd1.cmd_altitude_m = 600.0
    cmd1.cmd_speed_mps = 95.0
    cmd1.active = True

    batch.set_mission_commands_maintained_batch(
      [
        _mission_assignment(0, int(eid0), cmd0),
        _mission_assignment(1, int(eid1), cmd1),
      ]
    )

    intent0 = ef_py.LeaderIntent()
    intent0.phase_id = ef_py.LeaderPhase.Departure
    intent0.element_phase_id = 11
    intent0.service_profile = ef_py.ServiceProfile.AirForce
    intent0.task_family = ef_py.TaskFamily.Patrol
    intent0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    intent0.tactical_unit_id = 7001
    intent0.task_group_id = 8001
    intent0.role_code = 21
    intent0.warfare_role_code = int(ef_py.NavalWarfareRole.ScreenCommander)
    intent0.coordination_mode = ef_py.CoordinationMode.Follow
    intent0.relative_slot_code = 11
    intent0.recovery_site_id = 91
    intent0.officer_in_tactical_command = 8101
    intent0.command_code = 2
    intent0.cmd_heading_deg = 45.0
    intent0.formation_mode_id = ef_py.FormationMode.Joining
    intent0.join_required_flag = True
    intent0.wingman_command_mode = ef_py.WingmanCommandMode.HoldSlot
    intent0.active = True
    intent1 = ef_py.LeaderIntent()
    intent1.phase_id = ef_py.LeaderPhase.ApproachArmed
    intent1.element_phase_id = 23
    intent1.service_profile = ef_py.ServiceProfile.AirForce
    intent1.task_family = ef_py.TaskFamily.Recover
    intent1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    intent1.tactical_unit_id = 7001
    intent1.task_group_id = 8001
    intent1.role_code = 22
    intent1.warfare_role_code = int(ef_py.NavalWarfareRole.AirDefenseCommander)
    intent1.coordination_mode = ef_py.CoordinationMode.Recover
    intent1.relative_slot_code = 12
    intent1.recovery_site_id = 91
    intent1.officer_in_tactical_command = 8102
    intent1.command_code = 4
    intent1.cmd_heading_deg = 90.0
    intent1.formation_mode_id = ef_py.FormationMode.Recover
    intent1.rejoin_required_flag = True
    intent1.wingman_command_mode = ef_py.WingmanCommandMode.Rejoin
    intent1.active = True
    batch.set_leader_intents_maintained_batch(
      [
        _leader_intent_assignment(0, int(eid0), intent0),
        _leader_intent_assignment(1, int(eid1), intent1),
      ]
    )

    order0 = ef_py.TaskOrder()
    order0.task_type = ef_py.TaskType.CAP
    order0.task_id = 101
    order0.service_profile = ef_py.ServiceProfile.AirForce
    order0.task_family = ef_py.TaskFamily.Patrol
    order0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    order0.command_relationship = ef_py.CommandRelationship.TACON
    order0.authority_scope = ef_py.AuthorityScope.Tactical
    order0.parent_node_id = 5001
    order0.task_group_id = 8001
    order0.supported_node_id = 9001
    order0.supporting_node_id = 9002
    order0.role_code = 21
    order0.warfare_role_code = int(ef_py.NavalWarfareRole.ScreenCommander)
    order0.coordination_mode = ef_py.CoordinationMode.Attached
    order0.relative_slot_code = 11
    order0.assignee_kind = ef_py.AssigneeKind.Element
    order0.recovery_site_id = 91
    order0.officer_in_tactical_command = 8101
    order0.element_id = 7001
    order0.lead_aircraft_id = int(eid0)
    order0.naval_station_type = ef_py.NavalStationType.Screen
    order0.formation_template_id = 91
    order0.formation_role_id = ef_py.FormationRole.ElementLead
    order0.active = True
    order1 = ef_py.TaskOrder()
    order1.task_type = ef_py.TaskType.RTB
    order1.task_id = 202
    order1.service_profile = ef_py.ServiceProfile.AirForce
    order1.task_family = ef_py.TaskFamily.Recover
    order1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    order1.command_relationship = ef_py.CommandRelationship.TACON
    order1.authority_scope = ef_py.AuthorityScope.Tactical
    order1.parent_node_id = 5001
    order1.task_group_id = 8001
    order1.role_code = 22
    order1.warfare_role_code = int(ef_py.NavalWarfareRole.AirDefenseCommander)
    order1.coordination_mode = ef_py.CoordinationMode.Follow
    order1.relative_slot_code = 12
    order1.assignee_kind = ef_py.AssigneeKind.Element
    order1.recovery_site_id = 91
    order1.officer_in_tactical_command = 8102
    order1.element_id = 7001
    order1.lead_aircraft_id = int(eid0)
    order1.naval_station_type = ef_py.NavalStationType.Support
    order1.formation_template_id = 91
    order1.formation_role_id = ef_py.FormationRole.Wingman
    order1.wingman_slot_id = ef_py.WingmanSlot.Right
    order1.active = True
    order_assign0 = ef_py.WorldTaskOrderMaintainedAssignment()
    order_assign0.world_index = 0
    order_assign0.entity_id = int(eid0)
    order_assign0.task_order = ef_py.task_order_maintained_batch_contract(order0)
    order_assign1 = ef_py.WorldTaskOrderMaintainedAssignment()
    order_assign1.world_index = 1
    order_assign1.entity_id = int(eid1)
    order_assign1.task_order = ef_py.task_order_maintained_batch_contract(order1)
    batch.set_task_orders_maintained_batch([order_assign0, order_assign1])

    report0 = ef_py.PilotReport()
    report0.report_type = ef_py.CommMsgType.REP_WILCO
    report0.service_profile = ef_py.ServiceProfile.AirForce
    report0.task_family = ef_py.TaskFamily.Patrol
    report0.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    report0.tactical_unit_id = 7001
    report0.task_group_id = 8001
    report0.role_code = 21
    report0.warfare_role_code = int(ef_py.NavalWarfareRole.ScreenCommander)
    report0.coordination_mode = ef_py.CoordinationMode.Attached
    report0.officer_in_tactical_command = 8101
    report0.element_id = 7001
    report0.phase_id = int(ef_py.LeaderPhase.Departure)
    report0.formation_role_id = int(ef_py.FormationRole.ElementLead)
    report0.separation_m = 126.0
    report0.active = True
    report1 = ef_py.PilotReport()
    report1.report_type = ef_py.CommMsgType.REP_JOINED
    report1.service_profile = ef_py.ServiceProfile.AirForce
    report1.task_family = ef_py.TaskFamily.Recover
    report1.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    report1.tactical_unit_id = 7001
    report1.task_group_id = 8001
    report1.role_code = 22
    report1.warfare_role_code = int(ef_py.NavalWarfareRole.AirDefenseCommander)
    report1.coordination_mode = ef_py.CoordinationMode.Recover
    report1.officer_in_tactical_command = 8102
    report1.element_id = 7001
    report1.phase_id = int(ef_py.LeaderPhase.ApproachArmed)
    report1.formation_role_id = int(ef_py.FormationRole.Wingman)
    report1.formation_error_m = 18.0
    report1.active = True
    batch.set_pilot_reports_maintained_batch(
      [
        _pilot_report_assignment(0, int(eid0), report0),
        _pilot_report_assignment(1, int(eid1), report1),
      ]
    )

    got_cmds = batch.get_mission_commands_maintained_batch(refs)
    got_orders = batch.get_task_orders_maintained_batch(refs)
    got_intents = batch.get_leader_intents_maintained_batch(refs)
    got_reports = batch.get_pilot_reports_maintained_batch(refs)

    self.assertEqual(int(got_cmds[0].shared_core.command_code), 2)
    self.assertEqual(int(got_cmds[1].shared_core.command_code), 4)
    self.assertAlmostEqual(float(got_cmds[0].shared_core.cmd_heading_deg), 45.0, places=6)
    self.assertAlmostEqual(float(got_cmds[1].shared_core.cmd_speed_mps), 95.0, places=6)
    got_order0_identity = ef_py.task_order_maintained_air_tasking_identity(got_orders[0])
    got_order0_formation = ef_py.task_order_maintained_air_formation(got_orders[0])
    got_order0_stationing = ef_py.task_order_maintained_naval_stationing(got_orders[0])
    got_order1_formation = ef_py.task_order_maintained_air_formation(got_orders[1])
    got_order1_stationing = ef_py.task_order_maintained_naval_stationing(got_orders[1])
    self.assertEqual(got_order0_identity.task_type, ef_py.TaskType.CAP)
    self.assertEqual(ef_py.task_order_maintained_air_tasking_identity(got_orders[1]).task_type, ef_py.TaskType.RTB)
    self.assertEqual(int(got_orders[0].shared_core.task_id), 101)
    self.assertEqual(int(got_orders[1].shared_core.task_id), 202)
    self.assertEqual(got_orders[0].shared_core.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(got_orders[0].shared_core.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(got_orders[0].shared_core.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(got_orders[0].shared_core.command_relationship, ef_py.CommandRelationship.TACON)
    self.assertEqual(got_orders[0].shared_core.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(int(got_orders[0].shared_core.task_group_id), 8001)
    self.assertEqual(int(got_orders[0].shared_core.role_code), 21)
    self.assertEqual(
      int(got_orders[0].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.ScreenCommander),
    )
    self.assertEqual(got_orders[0].shared_core.coordination_mode, ef_py.CoordinationMode.Attached)
    self.assertEqual(int(got_orders[0].shared_core.relative_slot_code), 11)
    self.assertEqual(int(got_orders[0].shared_core.recovery_site_id), 91)
    self.assertEqual(int(got_orders[0].naval_command_authority.officer_in_tactical_command), 8101)
    self.assertEqual(got_orders[0].shared_core.assignee_kind, ef_py.AssigneeKind.Element)
    self.assertEqual(int(got_order0_identity.element_id), 7001)
    self.assertEqual(got_order0_stationing.naval_station_type, ef_py.NavalStationType.Screen)
    self.assertEqual(got_order0_formation.formation_role_id, ef_py.FormationRole.ElementLead)
    self.assertEqual(
      int(got_orders[1].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.AirDefenseCommander),
    )
    self.assertEqual(int(got_orders[1].naval_command_authority.officer_in_tactical_command), 8102)
    self.assertEqual(got_order1_stationing.naval_station_type, ef_py.NavalStationType.Support)
    self.assertEqual(got_order1_formation.formation_role_id, ef_py.FormationRole.Wingman)
    self.assertEqual(got_order1_formation.wingman_slot_id, ef_py.WingmanSlot.Right)
    self.assertEqual(got_intents[0].phase_id, ef_py.LeaderPhase.Departure)
    self.assertEqual(got_intents[1].phase_id, ef_py.LeaderPhase.ApproachArmed)
    self.assertEqual(got_intents[0].shared_core.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(got_intents[0].shared_core.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(got_intents[0].shared_core.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(int(got_intents[0].shared_core.tactical_unit_id), 7001)
    self.assertEqual(int(got_intents[0].shared_core.task_group_id), 8001)
    self.assertEqual(int(got_intents[0].shared_core.role_code), 21)
    self.assertEqual(
      int(got_intents[0].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.ScreenCommander),
    )
    self.assertEqual(got_intents[0].shared_core.coordination_mode, ef_py.CoordinationMode.Follow)
    self.assertEqual(int(got_intents[0].shared_core.relative_slot_code), 11)
    self.assertEqual(int(got_intents[0].shared_core.recovery_site_id), 91)
    self.assertEqual(int(got_intents[0].naval_command_authority.officer_in_tactical_command), 8101)
    self.assertEqual(int(got_intents[0].element_phase_id), 11)
    self.assertEqual(got_intents[0].formation_mode_id, ef_py.FormationMode.Joining)
    self.assertTrue(bool(got_intents[0].join_required_flag))
    self.assertEqual(
      int(got_intents[1].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.AirDefenseCommander),
    )
    self.assertEqual(int(got_intents[1].naval_command_authority.officer_in_tactical_command), 8102)
    self.assertEqual(got_intents[1].formation_mode_id, ef_py.FormationMode.Recover)
    self.assertTrue(bool(got_intents[1].rejoin_required_flag))
    self.assertEqual(got_reports[0].shared_core.report_type, ef_py.CommMsgType.REP_WILCO)
    self.assertEqual(got_reports[1].shared_core.report_type, ef_py.CommMsgType.REP_JOINED)
    self.assertEqual(got_reports[0].shared_core.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(got_reports[0].shared_core.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(got_reports[0].shared_core.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(int(got_reports[0].shared_core.tactical_unit_id), 7001)
    self.assertEqual(int(got_reports[0].shared_core.task_group_id), 8001)
    self.assertEqual(int(got_reports[0].shared_core.role_code), 21)
    self.assertEqual(
      int(got_reports[0].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.ScreenCommander),
    )
    self.assertEqual(got_reports[0].shared_core.coordination_mode, ef_py.CoordinationMode.Attached)
    self.assertEqual(int(got_reports[0].naval_command_authority.officer_in_tactical_command), 8101)
    self.assertEqual(int(got_reports[0].air.element_id), 7001)
    self.assertEqual(
      int(got_reports[1].naval_command_authority.warfare_role_code),
      int(ef_py.NavalWarfareRole.AirDefenseCommander),
    )
    self.assertEqual(int(got_reports[1].naval_command_authority.officer_in_tactical_command), 8102)
    self.assertEqual(int(got_reports[1].air.formation_role_id), int(ef_py.FormationRole.Wingman))
    self.assertAlmostEqual(float(got_reports[1].air.formation_error_m), 18.0, places=6)

  def test_world_batch_runtime_command_chain_maintained_contract_support_declared(self) -> None:
    header = (REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.h").read_text(encoding="utf-8")
    impl = (REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp").read_text(encoding="utf-8")

    for token in (
      "void set_mission_commands_maintained_batch(",
      "std::vector<MissionCommandMaintainedBatchContract>",
      "get_mission_commands_maintained_batch(",
      "void set_leader_intents_maintained_batch(",
      "std::vector<LeaderIntentMaintainedBatchContract>",
      "get_leader_intents_maintained_batch(",
      "void set_pilot_reports_maintained_batch(",
      "std::vector<PilotReportMaintainedBatchContract>",
      "get_pilot_reports_maintained_batch(",
    ):
      self.assertIn(token, header)

    for token in (
      "mission_command_compatibility_shell_from_maintained_batch_contract(",
      "leader_intent_compatibility_shell_from_maintained_batch_contract(",
      "pilot_report_compatibility_shell_from_maintained_batch_contract(",
      "mission_command_maintained_batch_contract(",
      "leader_intent_maintained_batch_contract(",
      "pilot_report_maintained_batch_contract(",
    ):
      self.assertIn(token, impl)

  def test_world_batch_command_chain_maintained_contracts_compile_and_preserve_slices(self) -> None:
    source = textwrap.dedent(
      r"""
      #include <type_traits>
      #include "runtime/contracts/world_batch_contracts.h"

      int main() {
        static_assert(MissionCommandMaintainedBatchContract::kMaintainedBatchTruth);
        static_assert(LeaderIntentMaintainedBatchContract::kMaintainedBatchTruth);
        static_assert(PilotReportMaintainedBatchContract::kMaintainedBatchTruth);
        static_assert(WorldMissionCommandMaintainedAssignment::kMaintainedBatchTruth);
        static_assert(WorldLeaderIntentMaintainedAssignment::kMaintainedBatchTruth);
        static_assert(WorldPilotReportMaintainedAssignment::kMaintainedBatchTruth);

        static_assert(WorldMissionCommandAssignment::kCompatibilityTransportShell);
        static_assert(WorldLeaderIntentAssignment::kCompatibilityTransportShell);
        static_assert(WorldPilotReportAssignment::kCompatibilityTransportShell);

        static_assert(std::is_same_v<
          decltype(world_mission_command_maintained_batch_contract(
            std::declval<WorldMissionCommandMaintainedAssignment&>())),
          MissionCommandMaintainedBatchContract&>);
        static_assert(std::is_same_v<
          decltype(world_leader_intent_maintained_batch_contract(
            std::declval<WorldLeaderIntentMaintainedAssignment&>())),
          LeaderIntentMaintainedBatchContract&>);
        static_assert(std::is_same_v<
          decltype(world_pilot_report_maintained_batch_contract(
            std::declval<WorldPilotReportMaintainedAssignment&>())),
          PilotReportMaintainedBatchContract&>);

        MissionCommand command{};
        command.command_code = 31;
        command.cmd_heading_deg = 45.0;
        command.cmd_altitude_m = 1200.0;
        command.cmd_speed_mps = 180.0;
        command.route_ref_id = 7101;
        command.authorization_to_fire = true;
        command.active = true;
        command.recovery_base_id = 81;
        command.recovery_runway_id = 82;
        command.recovery_approach_type = RecoveryApproachType::ILS;
        command.takeoff_procedure_id = TakeoffProcedureType::Interval;
        command.takeoff_clearance_id = TakeoffClearanceState::ClearedForTakeoff;
        command.takeoff_interval_s = 12.5;
        command.runway_slot_id = RunwaySlotPosition::Right;
        command.formation_id = 17;
        command.form_offset_x = 180.0;
        command.form_offset_y = -90.0;
        command.form_offset_z = 30.0;
        command.reference_entity_id = 9101;
        command.station_radius_m = 16000.0;
        command.station_bearing_deg = 75.0;
        command.embarked_helo_entity_id = 9201;
        command.launch_helo = true;
        command.recover_helo = false;
        command.relay_oth_targeting = true;

        const auto command_contract =
          mission_command_maintained_batch_contract(command);
        const auto command_shell =
          mission_command_compatibility_shell_from_maintained_batch_contract(
            command_contract);

        LeaderIntent intent{};
        intent.command_code = 4;
        intent.cmd_heading_deg = 90.0;
        intent.cmd_altitude_m = 600.0;
        intent.cmd_speed_mps = 95.0;
        intent.task_group_id = 8001;
        intent.role_code = 22;
        intent.active = true;
        intent.recovery_base_id = 91;
        intent.recovery_runway_id = 92;
        intent.recovery_approach_type = RecoveryApproachType::Overhead;
        intent.takeoff_procedure_id = TakeoffProcedureType::SingleShip;
        intent.takeoff_clearance_id = TakeoffClearanceState::LineUpAndWait;
        intent.takeoff_interval_s = 13.5;
        intent.runway_slot_id = RunwaySlotPosition::Left;
        intent.formation_id = 34;
        intent.form_offset_x = 4.25;
        intent.form_offset_y = 5.5;
        intent.form_offset_z = 6.75;
        intent.warfare_role_code = 35;
        intent.officer_in_tactical_command = 36;

        const auto intent_contract =
          leader_intent_maintained_batch_contract(intent);
        const auto intent_shell =
          leader_intent_compatibility_shell_from_maintained_batch_contract(
            intent_contract);

        PilotReport report{};
        report.report_type = CommMsgType::REP_WILCO;
        report.sender_id = 101;
        report.task_id = 202;
        report.role_code = 21;
        report.active = true;
        report.element_id = 7001;
        report.phase_id = 8;
        report.formation_role_id = 3;
        report.separation_m = 126.0;
        report.warfare_role_code = 41;
        report.officer_in_tactical_command = 42;

        const auto report_contract =
          pilot_report_maintained_batch_contract(report);
        const auto report_shell =
          pilot_report_compatibility_shell_from_maintained_batch_contract(
            report_contract);

        return !(
          command_shell.command_code == command.command_code &&
          command_shell.cmd_heading_deg == command.cmd_heading_deg &&
          command_shell.route_ref_id == command.route_ref_id &&
          command_shell.recovery_base_id == command.recovery_base_id &&
          command_shell.takeoff_interval_s == command.takeoff_interval_s &&
          command_shell.formation_id == command.formation_id &&
          command_shell.reference_entity_id == command.reference_entity_id &&
          command_shell.embarked_helo_entity_id == command.embarked_helo_entity_id &&
          command_shell.launch_helo == command.launch_helo &&
          intent_shell.command_code == intent.command_code &&
          intent_shell.task_group_id == intent.task_group_id &&
          intent_shell.recovery_base_id == intent.recovery_base_id &&
          intent_shell.takeoff_interval_s == intent.takeoff_interval_s &&
          intent_shell.formation_id == intent.formation_id &&
          intent_shell.warfare_role_code == intent.warfare_role_code &&
          report_shell.report_type == report.report_type &&
          report_shell.sender_id == report.sender_id &&
          report_shell.element_id == report.element_id &&
          report_shell.separation_m == report.separation_m &&
          report_shell.warfare_role_code == report.warfare_role_code);
      }
      """
    )

    result = _compile_and_run_cpp_source(source)

    self.assertEqual(result.returncode, 0, result.stderr)

  def test_world_batch_runtime_task_order_maintained_batch_roundtrip(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([19])

    entity_id = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      -1200.0,
      50.0,
      1300.0,
      90.0,
      0.0,
      0.0,
      0.0,
      180.0,
      0.0,
    )
    ref = _entity_ref(0, int(entity_id))

    assignment = ef_py.WorldTaskOrderMaintainedAssignment()
    assignment.world_index = 0
    assignment.entity_id = int(entity_id)
    assignment.task_order.shared_core.task_id = 333
    assignment.task_order.shared_core.service_profile = ef_py.ServiceProfile.AirForce
    assignment.task_order.shared_core.task_family = ef_py.TaskFamily.Recover
    assignment.task_order.shared_core.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit
    assignment.task_order.shared_core.priority = 7
    assignment.task_order.shared_core.issuer_id = 7000
    assignment.task_order.shared_core.assignee_id = int(entity_id)
    assignment.task_order.shared_core.command_relationship = ef_py.CommandRelationship.TACON
    assignment.task_order.shared_core.authority_scope = ef_py.AuthorityScope.Tactical
    assignment.task_order.shared_core.parent_node_id = 7100
    assignment.task_order.shared_core.task_group_id = 7200
    assignment.task_order.shared_core.supported_node_id = 7300
    assignment.task_order.shared_core.supporting_node_id = 7400
    assignment.task_order.shared_core.role_code = 21
    assignment.task_order.shared_core.coordination_mode = ef_py.CoordinationMode.Attached
    assignment.task_order.shared_core.relative_slot_code = 11
    assignment.task_order.shared_core.assignee_kind = ef_py.AssigneeKind.Element
    assignment.task_order.shared_core.recovery_site_id = 81
    assignment.task_order.shared_core.active = True
    assignment.task_order.shared_core.issue_time_s = 42.5
    air_identity = ef_py.task_order_maintained_air_tasking_identity(
      assignment.task_order
    )
    air_identity.task_type = ef_py.TaskType.CAPMission
    air_identity.element_id = 7001
    air_identity.package_id = 7002
    air_identity.lead_aircraft_id = int(entity_id)
    air_stationing = ef_py.task_order_maintained_air_stationing(
      assignment.task_order
    )
    air_stationing.anchor_x_m = 1400.0
    air_stationing.anchor_y_m = -250.0
    air_stationing.anchor_z_m = 6100.0
    air_stationing.station_type = ef_py.StationType.Racetrack
    air_stationing.station_radius_m = 18000.0
    air_stationing.station_leg_length_m = 31000.0
    air_stationing.station_heading_deg = 270.0
    air_stationing.altitude_block_min_m = 5600.0
    air_stationing.altitude_block_max_m = 6600.0
    air_stationing.target_altitude_m = 6100.0
    air_stationing.speed_min_mps = 170.0
    air_stationing.speed_max_mps = 230.0
    air_stationing.target_speed_mps = 205.0
    air_stationing.entry_condition_code = 3
    air_stationing.exit_condition_code = 4
    air_stationing.on_station_time_s = 900.0
    air_stationing.fuel_bingo_override_kg = 1200.0
    assignment.task_order.air_recovery.recovery_base_id = 81
    assignment.task_order.air_recovery.recovery_runway_id = 82
    assignment.task_order.air_recovery.recovery_approach_type = ef_py.RecoveryApproachType.ILS
    assignment.task_order.air_takeoff.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
    assignment.task_order.air_takeoff.takeoff_clearance_id = ef_py.TakeoffClearanceState.ClearedForTakeoff
    assignment.task_order.air_takeoff.takeoff_interval_s = 14.0
    assignment.task_order.air_takeoff.runway_slot_id = ef_py.RunwaySlotPosition.Right
    air_formation = ef_py.task_order_maintained_air_formation(
      assignment.task_order
    )
    air_formation.formation_template_id = 91
    air_formation.formation_contract_id = 92
    air_formation.formation_role_id = ef_py.FormationRole.Wingman
    air_formation.wingman_slot_id = ef_py.WingmanSlot.Left
    air_formation.join_policy_id = 5
    air_formation.rejoin_policy_id = 6
    air_formation.mutual_support_mode = 7
    air_formation.support_sector_id = 501
    assignment.task_order.naval_command_authority.warfare_role_code = 12
    assignment.task_order.naval_command_authority.officer_in_tactical_command = 9012
    ef_py.task_order_maintained_naval_stationing(
      assignment.task_order
    ).naval_station_type = ef_py.NavalStationType.Screen

    batch.set_task_orders_maintained_batch([assignment])

    maintained = batch.get_task_orders_maintained_batch([ref])

    self.assertEqual(len(maintained), 1)
    self.assertEqual(int(maintained[0].shared_core.task_id), 333)
    self.assertEqual(maintained[0].shared_core.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(maintained[0].shared_core.task_family, ef_py.TaskFamily.Recover)
    self.assertEqual(maintained[0].shared_core.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(int(maintained[0].shared_core.priority), 7)
    self.assertEqual(int(maintained[0].shared_core.issuer_id), 7000)
    self.assertEqual(int(maintained[0].shared_core.assignee_id), int(entity_id))
    self.assertEqual(maintained[0].shared_core.command_relationship, ef_py.CommandRelationship.TACON)
    self.assertEqual(maintained[0].shared_core.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(int(maintained[0].shared_core.parent_node_id), 7100)
    self.assertEqual(int(maintained[0].shared_core.task_group_id), 7200)
    self.assertEqual(int(maintained[0].shared_core.supported_node_id), 7300)
    self.assertEqual(int(maintained[0].shared_core.supporting_node_id), 7400)
    self.assertEqual(int(maintained[0].shared_core.role_code), 21)
    self.assertEqual(maintained[0].shared_core.coordination_mode, ef_py.CoordinationMode.Attached)
    self.assertEqual(int(maintained[0].shared_core.relative_slot_code), 11)
    self.assertEqual(maintained[0].shared_core.assignee_kind, ef_py.AssigneeKind.Element)
    self.assertEqual(int(maintained[0].shared_core.recovery_site_id), 81)
    self.assertTrue(bool(maintained[0].shared_core.active))
    self.assertAlmostEqual(float(maintained[0].shared_core.issue_time_s), 42.5, places=6)
    maintained_identity = ef_py.task_order_maintained_air_tasking_identity(
      maintained[0]
    )
    maintained_stationing = ef_py.task_order_maintained_air_stationing(
      maintained[0]
    )
    maintained_formation = ef_py.task_order_maintained_air_formation(
      maintained[0]
    )
    maintained_naval_stationing = ef_py.task_order_maintained_naval_stationing(
      maintained[0]
    )
    self.assertEqual(maintained_identity.task_type, ef_py.TaskType.CAPMission)
    self.assertEqual(int(maintained_identity.element_id), 7001)
    self.assertEqual(int(maintained_identity.package_id), 7002)
    self.assertEqual(int(maintained_identity.lead_aircraft_id), int(entity_id))
    self.assertAlmostEqual(float(maintained_stationing.anchor_x_m), 1400.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.anchor_y_m), -250.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.anchor_z_m), 6100.0, places=6)
    self.assertEqual(maintained_stationing.station_type, ef_py.StationType.Racetrack)
    self.assertAlmostEqual(float(maintained_stationing.station_radius_m), 18000.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.station_leg_length_m), 31000.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.station_heading_deg), 270.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.altitude_block_min_m), 5600.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.altitude_block_max_m), 6600.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.target_altitude_m), 6100.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.speed_min_mps), 170.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.speed_max_mps), 230.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.target_speed_mps), 205.0, places=6)
    self.assertEqual(int(maintained_stationing.entry_condition_code), 3)
    self.assertEqual(int(maintained_stationing.exit_condition_code), 4)
    self.assertAlmostEqual(float(maintained_stationing.on_station_time_s), 900.0, places=6)
    self.assertAlmostEqual(float(maintained_stationing.fuel_bingo_override_kg), 1200.0, places=6)
    self.assertEqual(int(maintained[0].air_recovery.recovery_base_id), 81)
    self.assertEqual(int(maintained[0].air_recovery.recovery_runway_id), 82)
    self.assertEqual(
      maintained[0].air_recovery.recovery_approach_type,
      ef_py.RecoveryApproachType.ILS,
    )
    self.assertEqual(
      maintained[0].air_takeoff.takeoff_procedure_id,
      ef_py.TakeoffProcedureType.Interval,
    )
    self.assertEqual(
      maintained[0].air_takeoff.takeoff_clearance_id,
      ef_py.TakeoffClearanceState.ClearedForTakeoff,
    )
    self.assertAlmostEqual(float(maintained[0].air_takeoff.takeoff_interval_s), 14.0, places=6)
    self.assertEqual(
      maintained[0].air_takeoff.runway_slot_id,
      ef_py.RunwaySlotPosition.Right,
    )
    self.assertEqual(int(maintained_formation.formation_template_id), 91)
    self.assertEqual(int(maintained_formation.formation_contract_id), 92)
    self.assertEqual(
      maintained_formation.formation_role_id,
      ef_py.FormationRole.Wingman,
    )
    self.assertEqual(maintained_formation.wingman_slot_id, ef_py.WingmanSlot.Left)
    self.assertEqual(int(maintained_formation.join_policy_id), 5)
    self.assertEqual(int(maintained_formation.rejoin_policy_id), 6)
    self.assertEqual(int(maintained_formation.mutual_support_mode), 7)
    self.assertEqual(int(maintained_formation.support_sector_id), 501)
    self.assertEqual(int(maintained[0].naval_command_authority.warfare_role_code), 12)
    self.assertEqual(
      int(maintained[0].naval_command_authority.officer_in_tactical_command),
      9012,
    )
    self.assertEqual(
      maintained_naval_stationing.naval_station_type,
      ef_py.NavalStationType.Screen,
    )

  def test_world_batch_runtime_mission_command_maintained_batch_roundtrip_preserves_n4_target_provenance(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([33])

    ship = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      -1400.0,
      0.0,
      0.0,
      90.0,
      0.0,
      0.0,
      0.0,
      10.29,
      0.0,
    )
    batch.world_raw_quarantine(0).set_command_link(int(ship), 0.0, 0.0)
    ref = _entity_ref(0, int(ship))

    assignment = ef_py.WorldMissionCommandMaintainedAssignment()
    assignment.world_index = 0
    assignment.entity_id = int(ship)
    assignment.mission_command.shared_core.command_code = 32
    assignment.mission_command.shared_core.cmd_heading_deg = 45.0
    assignment.mission_command.shared_core.cmd_altitude_m = 0.0
    assignment.mission_command.shared_core.cmd_speed_mps = 12.0
    assignment.mission_command.shared_core.assigned_target_id = 7001
    assignment.mission_command.shared_core.threat_state = 4
    assignment.mission_command.shared_core.assigned_target_track_id = 88001
    assignment.mission_command.shared_core.assigned_target_source_id = 99002
    assignment.mission_command.shared_core.assigned_target_snapshot_time_s = 123.75
    assignment.mission_command.shared_core.authorization_to_fire = True
    assignment.mission_command.shared_core.active = True

    batch.set_mission_commands_maintained_batch([assignment])

    maintained = batch.get_mission_commands_maintained_batch([ref])

    self.assertEqual(len(maintained), 1)
    self.assertEqual(int(maintained[0].shared_core.assigned_target_id), 7001)
    self.assertEqual(int(maintained[0].shared_core.threat_state), 4)
    self.assertEqual(int(maintained[0].shared_core.assigned_target_track_id), 88001)
    self.assertEqual(int(maintained[0].shared_core.assigned_target_source_id), 99002)
    self.assertAlmostEqual(
      float(maintained[0].shared_core.assigned_target_snapshot_time_s),
      123.75,
      places=6,
    )

  def test_world_batch_runtime_mission_command_roundtrip_preserves_formation_offsets(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([29])

    lead = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Blue, "Aircraft", -1400.0, 0.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)
    wing = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Blue, "Aircraft", -1550.0, -120.0, 1200.0, 90.0, 0.0, 0.0, 0.0, 180.0, 0.0)
    batch.world_raw_quarantine(0).set_command_link(int(lead), 0.0, 0.0)
    batch.world_raw_quarantine(0).set_command_link(int(wing), 0.0, 0.0)
    refs = [_entity_ref(0, int(lead)), _entity_ref(0, int(wing))]

    cmd0 = ef_py.MissionCommand()
    cmd0.command_code = 2
    cmd0.cmd_heading_deg = 45.0
    cmd0.cmd_altitude_m = 1200.0
    cmd0.cmd_speed_mps = 180.0
    cmd0.formation_id = 17
    cmd0.form_offset_x = 0.0
    cmd0.form_offset_y = 0.0
    cmd0.form_offset_z = 0.0
    cmd0.active = True

    cmd1 = ef_py.MissionCommand()
    cmd1.command_code = 2
    cmd1.cmd_heading_deg = 45.0
    cmd1.cmd_altitude_m = 1200.0
    cmd1.cmd_speed_mps = 180.0
    cmd1.formation_id = 17
    cmd1.form_offset_x = 180.0
    cmd1.form_offset_y = -90.0
    cmd1.form_offset_z = 30.0
    cmd1.active = True

    batch.set_mission_commands_maintained_batch(
      [
        _mission_assignment(0, int(lead), cmd0),
        _mission_assignment(0, int(wing), cmd1),
      ]
    )

    got = batch.get_mission_commands_maintained_batch(refs)

    self.assertEqual(len(got), 2)
    self.assertEqual(int(got[0].air_formation.formation_id), 17)
    self.assertEqual(int(got[1].air_formation.formation_id), 17)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_x), 0.0, places=6)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_y), 0.0, places=6)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_z), 0.0, places=6)
    self.assertAlmostEqual(float(got[1].air_formation.form_offset_x), 180.0, places=6)
    self.assertAlmostEqual(float(got[1].air_formation.form_offset_y), -90.0, places=6)
    self.assertAlmostEqual(float(got[1].air_formation.form_offset_z), 30.0, places=6)

  def test_world_batch_runtime_mission_command_roundtrip_preserves_naval_extension_fields(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([31])

    ship = batch.world_raw_quarantine(0).spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      -1400.0,
      0.0,
      0.0,
      90.0,
      0.0,
      0.0,
      0.0,
      10.29,
      0.0,
    )
    batch.world_raw_quarantine(0).set_command_link(int(ship), 0.0, 0.0)
    refs = [_entity_ref(0, int(ship))]

    cmd = ef_py.MissionCommand()
    cmd.command_code = 32
    cmd.cmd_heading_deg = 45.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 12.0
    cmd.reference_entity_id = 5201
    cmd.station_radius_m = 16000.0
    cmd.station_bearing_deg = 75.0
    cmd.recovery_base_id = 9201
    cmd.recovery_runway_id = 14
    cmd.recovery_approach_type = ef_py.RecoveryApproachType.ILS
    cmd.formation_id = 73
    cmd.form_offset_x = 240.0
    cmd.form_offset_y = -110.0
    cmd.form_offset_z = 18.0
    cmd.embarked_helo_entity_id = 9301
    cmd.launch_helo = True
    cmd.recover_helo = False
    cmd.relay_oth_targeting = True
    cmd.active = True

    batch.set_mission_commands_maintained_batch([_mission_assignment(0, int(ship), cmd)])

    got = batch.get_mission_commands_maintained_batch(refs)

    self.assertEqual(len(got), 1)
    self.assertEqual(int(got[0].naval_stationing.reference_entity_id), 5201)
    self.assertAlmostEqual(float(got[0].naval_stationing.station_radius_m), 16000.0, places=6)
    self.assertAlmostEqual(float(got[0].naval_stationing.station_bearing_deg), 75.0, places=6)
    self.assertEqual(int(got[0].air_recovery.recovery_base_id), 9201)
    self.assertEqual(int(got[0].air_recovery.recovery_runway_id), 14)
    self.assertEqual(got[0].air_recovery.recovery_approach_type, ef_py.RecoveryApproachType.ILS)
    self.assertEqual(int(got[0].air_formation.formation_id), 73)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_x), 240.0, places=6)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_y), -110.0, places=6)
    self.assertAlmostEqual(float(got[0].air_formation.form_offset_z), 18.0, places=6)
    self.assertEqual(int(got[0].naval_embarked_helo.embarked_helo_entity_id), 9301)
    self.assertTrue(bool(got[0].naval_embarked_helo.launch_helo))
    self.assertFalse(bool(got[0].naval_embarked_helo.recover_helo))
    self.assertTrue(bool(got[0].naval_embarked_helo.relay_oth_targeting))




if __name__ == "__main__":
  unittest.main()