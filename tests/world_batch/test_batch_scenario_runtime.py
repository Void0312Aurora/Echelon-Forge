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


class BatchScenarioRuntimeTests(unittest.TestCase):
  def test_load_compiled_scenario_batch_reuses_apply_buffer(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())
    adapter = RuntimeFacadeAdapter(2)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))
    apply_buffer = BatchWorldApplyBuffer(2)

    worlds_a = load_compiled_scenario_for_setup_target(
      adapter,
      compiled,
      seeds=[11, 17],
      apply_buffer=apply_buffer,
    )
    worlds_b = load_compiled_scenario_for_setup_target(
      adapter,
      compiled,
      seeds=[21, 27],
      apply_buffer=apply_buffer,
    )

    self.assertEqual(len(worlds_a), 2)
    self.assertEqual(len(worlds_b), 2)
    self.assertEqual(len(apply_buffer.terrain_assignments), 2)
    self.assertEqual(len(apply_buffer.wind_assignments), 2)
    self.assertEqual(len(apply_buffer.zone_defs), 2)
    self.assertEqual(len(apply_buffer.spawn_requests), 4)
    self.assertNotEqual(float(worlds_a[0].layout.world_yaw_deg), float(worlds_b[0].layout.world_yaw_deg))
    self.assertIsNotNone(worlds_b[0].agent_id)
    self.assertEqual(len(worlds_b[0].active_roster), 2)
    self.assertEqual(len(worlds_b[1].active_roster), 2)
    self.assertEqual([int(member.world_index) for member in worlds_b[0].active_roster], [0, 0])
    self.assertEqual([int(member.world_index) for member in worlds_b[1].active_roster], [1, 1])
    obs = adapter.get_agent_observation(0, int(worlds_b[0].agent_id))
    self.assertEqual(int(obs.id), int(worlds_b[0].agent_id))

  def test_load_compiled_scenario_batch_spawns_worlds(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())
    batch = ef_py.WorldBatchRuntime(2)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))

    with self.assertRaisesRegex(RuntimeError, "maintained facade setup target"):
      load_compiled_scenario_for_setup_target(batch, compiled, seeds=[11, 17])

    adapter = RuntimeFacadeAdapter(2)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))
    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[11, 17])
    self.assertEqual(len(worlds), 2)
    self.assertIsNotNone(worlds[0].agent_id)
    self.assertIsNotNone(worlds[1].agent_id)
    self.assertIn("Lead", worlds[0].entities)
    self.assertIn("Wing", worlds[1].entities)
    self.assertNotEqual(float(worlds[0].layout.world_yaw_deg), float(worlds[1].layout.world_yaw_deg))

    refs = []
    for world_index, applied in enumerate(worlds):
      ref = ef_py.WorldEntityRef()
      ref.world_index = int(world_index)
      ref.entity_id = int(applied.agent_id)
      refs.append(ref)

    observations = adapter.get_agent_observations_batch(refs)
    self.assertEqual(len(observations), 2)
    self.assertNotEqual(float(observations[0].x), float(observations[1].x))

  def test_scenario_loader_and_batch_runtime_share_setup_semantics(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())

    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader_agent_id = loader.load_compiled_scenario(compiled, seed=23)
    loader_obs = sim.get_agent_observation(int(loader_agent_id))

    adapter = RuntimeFacadeAdapter(1)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))
    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[23])
    self.assertEqual(len(worlds), 1)
    batch_obs = adapter.get_agent_observation(0, int(worlds[0].agent_id))

    self.assertAlmostEqual(float(loader.world_yaw_deg), float(worlds[0].layout.world_yaw_deg), places=6)
    self.assertAlmostEqual(float(loader_obs.x), float(batch_obs.x), places=6)
    self.assertAlmostEqual(float(loader_obs.y), float(batch_obs.y), places=6)
    self.assertAlmostEqual(float(loader_obs.z), float(batch_obs.z), places=6)
    self.assertEqual(set(loader.entities.keys()), set(worlds[0].entities.keys()))

  def test_route_ref_id_is_cached_after_waypoint_parse(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_route_scenario())

    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    agent_id = loader.load_compiled_scenario(compiled, seed=31)

    self.assertIsNotNone(agent_id)
    cached_before = loader._cached_route_ref_id
    route_ref_id_1 = infer_route_ref_id(loader)
    route_ref_id_2 = infer_route_ref_id(loader)

    self.assertGreater(int(route_ref_id_1), 0)
    self.assertEqual(int(route_ref_id_1), int(route_ref_id_2))
    if cached_before is not None:
      self.assertEqual(int(cached_before), int(route_ref_id_1))
    self.assertEqual(int(loader._cached_route_ref_id), int(route_ref_id_1))

  def test_compiled_route_metadata_materializes_runtime_waypoint_cache(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_route_scenario())

    self.assertEqual(len(compiled.runtime_metadata.normalized_route_waypoints), 2)
    self.assertGreater(int(compiled.runtime_metadata.mission_command_template.get("route_ref_id", 0)), 0)

    layout = build_compiled_world_layout(compiled, seed=41)
    mission_cmd = layout.scenario_data.get("mission_command", {})
    self.assertIsInstance(mission_cmd.get("_normalized_waypoints"), list)
    self.assertEqual(len(mission_cmd.get("_normalized_waypoints", [])), 2)
    self.assertEqual(
      int(mission_cmd.get("route_ref_id", 0)),
      int(compiled.runtime_metadata.mission_command_template.get("route_ref_id", 0)),
    )

  def test_compiled_layout_template_matches_legacy_layout_build(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())

    layout_compiled = build_compiled_world_layout(compiled, seed=41, use_compiled_template=True)
    legacy_data = compiled.instantiate_runtime()
    legacy_data["mission_command"] = _clone_runtime_mission_command(compiled.runtime_metadata.mission_command_template)
    legacy_layout = prepare_scenario_world_layout(
      legacy_data,
      seed=41,
      rng=np.random.RandomState(41),
      compiled_template=None,
    )

    self.assertAlmostEqual(float(layout_compiled.world_yaw_deg), float(legacy_layout.world_yaw_deg), places=6)
    self.assertEqual(len(layout_compiled.zones), len(legacy_layout.zones))
    self.assertEqual(len(layout_compiled.spawns), len(legacy_layout.spawns))
    self.assertAlmostEqual(float(layout_compiled.wind_speed_mps), float(legacy_layout.wind_speed_mps), places=6)
    self.assertAlmostEqual(float(layout_compiled.wind_dir_from_deg), float(legacy_layout.wind_dir_from_deg), places=6)
    self.assertAlmostEqual(float(layout_compiled.spawns[0].x), float(legacy_layout.spawns[0].x), places=6)
    self.assertAlmostEqual(float(layout_compiled.spawns[0].y), float(legacy_layout.spawns[0].y), places=6)
    self.assertAlmostEqual(float(layout_compiled.spawns[0].heading), float(legacy_layout.spawns[0].heading), places=6)

  def test_compiled_layout_template_defaults_missing_terrain_type_to_non_legacy_mainline(self) -> None:
    scenario = _inline_batch_scenario()
    scenario["environment"].pop("terrain_type", None)
    compiled = ScenarioCompiler.compile_data(scenario)

    layout_compiled = build_compiled_world_layout(compiled, seed=41, use_compiled_template=True)
    legacy_data = compiled.instantiate_runtime()
    legacy_data["mission_command"] = _clone_runtime_mission_command(compiled.runtime_metadata.mission_command_template)
    legacy_layout = prepare_scenario_world_layout(
      legacy_data,
      seed=41,
      rng=np.random.RandomState(41),
      compiled_template=None,
    )

    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type_source, TERRAIN_TYPE_SOURCE_DEFAULT)
    self.assertEqual(layout_compiled.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(layout_compiled.terrain_type_source, TERRAIN_TYPE_SOURCE_DEFAULT)
    self.assertEqual(legacy_layout.terrain_type, DEFAULT_TERRAIN_TYPE)
    self.assertEqual(legacy_layout.terrain_type_source, TERRAIN_TYPE_SOURCE_DEFAULT)

  def test_compiled_layout_template_marks_explicit_legacy_terrain_as_compatibility(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_batch_scenario())

    layout = build_compiled_world_layout(compiled, seed=41, use_compiled_template=True)

    self.assertEqual(compiled.runtime_metadata.layout_template.terrain_type, "legacy")
    self.assertEqual(
      compiled.runtime_metadata.layout_template.terrain_type_source,
      TERRAIN_TYPE_SOURCE_COMPATIBILITY,
    )
    self.assertEqual(layout.terrain_type, "legacy")
    self.assertEqual(layout.terrain_type_source, TERRAIN_TYPE_SOURCE_COMPATIBILITY)

  def test_batch_loaded_route_template_preserves_rotated_waypoint_cache(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_route_template_scenario())
    adapter = RuntimeFacadeAdapter(1)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))

    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[41])
    loader = adapter.make_scenario_loader(0)
    loader._compiled_scenario = compiled
    loader._compiled_runtime_metadata = compiled.runtime_metadata
    loader.load_prepared_world(worlds[0], seed=41, sync_to_kernel=False)

    cached = loader.mission_cmd.get("_normalized_waypoints", None)
    self.assertTrue(bool(loader.mission_cmd.get("_runtime_waypoint_cache_valid", False)))
    self.assertIsInstance(cached, list)
    self.assertEqual(len(cached), 2)
    self.assertGreater(int(loader.mission_cmd.get("route_ref_id", 0)), 0)
    self.assertEqual(
      int(loader.mission_cmd.get("route_ref_id", 0)),
      int(compiled.runtime_metadata.waypoint_template_route_ref_ids[0]),
    )
    self.assertAlmostEqual(float(cached[0]["x"]), float(loader.mission_cmd["waypoints"][0]["x"]), places=6)
    self.assertAlmostEqual(float(cached[0]["y"]), float(loader.mission_cmd["waypoints"][0]["y"]), places=6)

  def test_batch_loaded_route_generator_uses_runtime_agent_spawn_context(self) -> None:
    compiled = ScenarioCompiler.compile_data(_inline_route_generator_scenario())
    adapter = RuntimeFacadeAdapter(1)
    self.assertTrue(adapter.load_database(resolve_repo_path("examples", "config", "database")))

    worlds = load_compiled_scenario_for_setup_target(adapter, compiled, seeds=[53])
    loader = adapter.make_scenario_loader(0)
    loader._compiled_scenario = compiled
    loader._compiled_runtime_metadata = compiled.runtime_metadata
    loader.load_prepared_world(worlds[0], seed=53, sync_to_kernel=False)

    self.assertEqual(len(loader.waypoints), 3)
    self.assertTrue(bool(loader.mission_cmd.get("_route_generator_used", False)))
    self.assertGreater(int(loader.mission_cmd.get("route_ref_id", 0)), 0)
    self.assertNotIn("entities", worlds[0].layout.scenario_data)
    self.assertIn("_runtime_agent_spawn", worlds[0].layout.scenario_data)

  def test_world_batch_runtime_live_candidate_helpers_cover_sensor_visual_and_comm(self) -> None:
    batch = ef_py.WorldBatchRuntime(1)
    self.assertTrue(batch.load_database(resolve_repo_path("examples", "config", "database")))
    batch.reset_batch([17])

    lead = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Blue, "Aircraft", 0.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 0.0, 180.0, 0.0)
    friend = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Blue, "Aircraft", 0.0, 1200.0, 1200.0, 0.0, 0.0, 0.0, 0.0, 180.0, 0.0)
    foe_close = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Red, "Aircraft", 2000.0, 0.0, 1200.0, 180.0, 0.0, 0.0, 0.0, 180.0, 0.0)
    foe_far = batch.world_raw_quarantine(0).spawn_unit(ef_py.Side.Red, "Aircraft", 60000.0, 0.0, 1200.0, 180.0, 0.0, 0.0, 0.0, 180.0, 0.0)

    refs = [_entity_ref(0, int(lead))]
    expected_sensor_and_visual = [int(friend), int(foe_close)]
    expected_comm = [int(friend)]

    for use_gpu in (False, True):
      sensor_ids = [int(v) for v in batch.get_sensor_candidate_ids_batch(refs, use_gpu)[0]]
      visual_ids = [int(v) for v in batch.get_visual_candidate_ids_batch(refs, 25000.0, use_gpu)[0]]
      comm_ids = [int(v) for v in batch.get_comm_candidate_ids_batch(refs, use_gpu)[0]]

      for ids in (sensor_ids, visual_ids, comm_ids):
        self.assertEqual(ids, sorted(ids))
        self.assertNotIn(int(lead), ids)
        self.assertNotIn(int(foe_far), ids)

      self.assertEqual(sensor_ids, expected_sensor_and_visual)
      self.assertEqual(visual_ids, expected_sensor_and_visual)
      self.assertEqual(comm_ids, expected_comm)

    _assert_gpu_helper_capabilities_remain_fail_closed(self)

  def test_world_batch_runtime_execution_episode_controller_batch_prime_exports_state(self) -> None:
    runtime = ef_py.WorldBatchRuntime(2)
    self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
    runtime.reset_batch([181, 191])

    refs: list[ef_py.WorldEntityRef] = []
    states: list[ef_py.ExecutionEpisodeState] = []

    for world_index, seed in enumerate((181, 191)):
      loader = ScenarioLoader(runtime.world_raw_quarantine(world_index))
      loader.set_execution_step_runtime_mode("compiled")
      agent_id = loader.load_scenario_data(copy.deepcopy(_inline_route_scenario()), seed=seed)
      self.assertIsNotNone(agent_id)

      loader.steps = 7 + world_index
      loader.waypoint_idx = 1
      loader._waypoint_prev_dist_m = 875.0 - (25.0 * world_index)
      loader._waypoint_leg_origin_x = -1400.0 + (10.0 * world_index)
      loader._waypoint_leg_origin_y = 15.0 * world_index
      loader.waypoint_total_route_length_m = 4200.0 + (100.0 * world_index)
      loader.prev_alt = 1185.0 + world_index
      loader.prev_speed = 176.0 + world_index
      loader.liftoff_awarded = bool(world_index % 2 == 0)
      loader.gear_bonus_awarded = bool(world_index % 2 == 1)
      loader.off_runway_steps = 1 + world_index
      loader._approach_prev_dme_m = 4567.0 + world_index
      loader._approach_prev_loc_abs = 0.12 + (0.01 * world_index)
      loader._approach_prev_gs_abs = 0.08 + (0.01 * world_index)

      refs.append(_entity_ref(world_index, int(agent_id)))
      states.append(loader.build_execution_episode_state())

    runtime.prime_execution_episode_controller_batch(refs, states)

    self.assertTrue(bool(runtime.execution_episode_controller_ready(0)))
    self.assertTrue(bool(runtime.execution_episode_controller_ready(1)))

    exported = runtime.export_execution_episode_states_batch(refs)
    self.assertEqual(len(exported), len(states))
    for actual, expected in zip(exported, states, strict=True):
      self.assertTrue(bool(ef_py.execution_episode_states_equivalent(actual, expected)))

    runtime.clear_execution_episode_controller_batch()
    self.assertFalse(bool(runtime.execution_episode_controller_ready(0)))
    self.assertFalse(bool(runtime.execution_episode_controller_ready(1)))

  def test_world_batch_runtime_execution_episode_controller_batch_step_matches_loader_shadow(self) -> None:
    runtime = ef_py.WorldBatchRuntime(2)
    self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
    runtime.reset_batch([211, 223])

    refs: list[ef_py.WorldEntityRef] = []
    primed_states: list[ef_py.ExecutionEpisodeState] = []
    requests: list[ef_py.WorldExecutionEpisodeStepRequest] = []
    expected_reports: list[dict] = []
    loaders: list[ScenarioLoader] = []

    for world_index, seed in enumerate((211, 223)):
      loader = ScenarioLoader(runtime.world_raw_quarantine(world_index))
      loader.set_execution_step_runtime_mode("compiled")
      agent_id = loader.load_scenario_data(copy.deepcopy(_inline_route_scenario()), seed=seed)
      self.assertIsNotNone(agent_id)

      loader.steps = 3 + world_index
      loader.waypoint_idx = 0
      loader._waypoint_prev_dist_m = 950.0 - (40.0 * world_index)
      loader._waypoint_leg_origin_x = -1400.0
      loader._waypoint_leg_origin_y = 0.0
      loader.waypoint_total_route_length_m = 4300.0 + (50.0 * world_index)
      loader.prev_alt = 1180.0 + world_index
      loader.prev_speed = 175.0 + world_index
      loader.liftoff_awarded = True
      loader.gear_bonus_awarded = bool(world_index % 2 == 0)
      loader.off_runway_steps = world_index
      loader._approach_prev_dme_m = 4300.0 + (100.0 * world_index)
      loader._approach_prev_loc_abs = 0.10 + (0.01 * world_index)
      loader._approach_prev_gs_abs = 0.07 + (0.01 * world_index)

      truth = runtime.world_raw_quarantine(world_index).get_agent_observation(int(agent_id))
      inst_obj = runtime.world_raw_quarantine(world_index).get_instrument_state(int(agent_id))
      ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst_obj.alt_baro))
      inst_vec, _, _ = ef_py.compute_execution_observation_runtime_numpy(
        inst_obj,
        truth,
        float(ils_vec[0]),
        float(ils_vec[1]),
        float(ils_vec[2]),
        float(ils_vec[3]),
        int(loader.max_contacts),
        int(loader.max_rwr),
      )
      inst_vec = np.asarray(inst_vec, dtype=np.float32)
      ils_vec = np.asarray(ils_vec[:4], dtype=np.float32)
      mission_obs_mode = "nav_v2"
      step_eval = loader._prepare_step_evaluation(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(loader.steps),
        max_steps=loader.get_max_steps(),
        mission_obs_mode=mission_obs_mode,
      )
      mission_inputs = step_eval.get("mission_observation_inputs")
      batch_state = loader._build_step_evaluation_batch_env_state(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(loader.steps),
        max_steps=loader.get_max_steps(),
        mission_obs_mode=mission_obs_mode,
        mission_observation_inputs=mission_inputs,
      )
      batch_state.has_episode_state = False

      request = ef_py.WorldExecutionEpisodeStepRequest()
      request.world_index = int(world_index)
      request.entity_id = int(agent_id)
      request.config = loader._build_execution_episode_controller_shadow_config()
      request.env_state = batch_state

      report = loader.compare_execution_episode_controller_shadow(
        truth=truth,
        inst_obj=inst_obj,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=int(loader.steps),
        max_steps=loader.get_max_steps(),
        mission_obs_mode=mission_obs_mode,
        advance_state=True,
      )
      self.assertTrue(bool(report["comparison"]["overall_match"]), msg=str(report["comparison"]))

      refs.append(_entity_ref(world_index, int(agent_id)))
      primed_states.append(loader.build_execution_episode_state())
      requests.append(request)
      expected_reports.append(report)
      loaders.append(loader)

    runtime.prime_execution_episode_controller_batch(refs, primed_states)
    products = runtime.step_execution_episode_batch(requests)
    exported_states = runtime.export_execution_episode_states_batch(refs)

    self.assertEqual(len(products), len(expected_reports))
    self.assertEqual(len(exported_states), len(expected_reports))
    for world_index, (loader, actual_products, report, actual_state) in enumerate(
      zip(loaders, products, expected_reports, exported_states, strict=True)
    ):
      comparison = loader._compare_execution_episode_runtime_products(
        report["shadow_frame_products"],
        actual_products,
      )
      self.assertTrue(bool(comparison["overall_match"]), msg=f"world={world_index}: {comparison}")
      self.assertTrue(
        bool(ef_py.execution_episode_states_equivalent(actual_state, report["shadow_state"])),
        msg=f"world={world_index}: exported runtime-owned state diverged from shadow state",
      )




if __name__ == "__main__":
  unittest.main()