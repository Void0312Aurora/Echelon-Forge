from __future__ import annotations

import json
import math
import tempfile
import unittest
import unittest.mock

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

try:
  from stable_baselines3 import PPO # noqa: E402
except ModuleNotFoundError: # pragma: no cover
  PPO = None

try:
  from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv # noqa: E402
except ModuleNotFoundError: # pragma: no cover
  CooperativeWorldBatchVecEnv = None

import python.rl.runtime.cooperative_world_batch_vec_env as cooperative_vec_env_module # noqa: E402
from python.rl.runtime.multi_agent_runtime import MultiAgentWorldRuntimeView # noqa: E402
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index # noqa: E402
from python.tasking_contracts.air_scripted_ew import AirScriptedEWActionModel # noqa: E402


def _cooperative_cruise_scenario() -> dict:
  return {
    "scenario_name": "cooperative_cruise_vec_env_smoke",
    "meta": {"max_steps": 16},
    "environment": {
      "time_step": 0.05,
      "terrain_type": "flat",
      "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
      "zones": [
        {
          "name": "Runway 09",
          "x": 0.0,
          "y": 0.0,
          "width": 45.0,
          "length": 3000.0,
          "heading": 90.0,
          "surface": "Concrete",
        }
      ],
    },
    "mission_command": {
      "command_code": 3,
      "target_heading": 90.0,
      "target_altitude": 1400.0,
      "target_speed": 210.0,
      "formation_id": 17,
      "form_offset_x": 180.0,
      "form_offset_y": -90.0,
      "form_offset_z": 30.0,
      "waypoint_mode": "flyby",
      "waypoints": [
        {"x": 15000.0, "y": 0.0, "z": 1400.0, "radius_m": 1000.0},
        {"x": 30000.0, "y": 3000.0, "z": 1400.0, "radius_m": 1000.0},
      ],
    },
    "entities": [
      {
        "name": "Lead",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [0.0, 0.0, 1400.0],
        "vel": [210.0, 0.0, 0.0],
        "heading": 90.0,
      },
      {
        "name": "Wing",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [-120.0, -180.0, 1400.0],
        "vel": [210.0, 0.0, 0.0],
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


def _cooperative_interval_takeoff_scenario() -> dict:
  return {
    "scenario_name": "cooperative_interval_takeoff_vec_env_smoke",
    "meta": {"max_steps": 16},
    "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
    "environment": {
      "time_step": 0.05,
      "terrain_type": "flat",
      "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
    },
    "mission_command": {
      "command_code": 2,
      "target_heading": 90.0,
      "target_altitude": 220.0,
      "target_speed": 155.0,
      "takeoff_procedure_code": 2,
      "takeoff_clearance_code": 3,
      "takeoff_interval_s": 6.0,
      "runway_slot_code": 1,
      "formation_id": 31,
      "form_offset_x": 180.0,
      "form_offset_y": -90.0,
      "form_offset_z": 25.0,
    },
    "entities": [
      {
        "name": "Lead",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1400.0, 0.0, 2.1],
        "vel": [0.0, 0.0, 0.0],
        "heading": 90.0,
      },
      {
        "name": "Wing",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1460.0, 0.0, 2.1],
        "vel": [0.0, 0.0, 0.0],
        "heading": 90.0,
      },
    ],
    "cooperative_roster": {
      "team_id": 7101,
      "element_id": 7101,
      "policy_route": "shared_execution",
      "members": [
        {
          "entity": "Lead",
          "role_code": 21,
          "formation_role_id": "ElementLead",
          "relative_slot_code": 11,
          "policy_route": "shared_execution",
          "mission_command_overrides": {
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 3,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "form_offset_x": 0.0,
            "form_offset_y": 0.0,
            "form_offset_z": 0.0,
          },
        },
        {
          "entity": "Wing",
          "role_code": 22,
          "formation_role_id": "Wingman",
          "relative_slot_code": 12,
          "reference_entity": "Lead",
          "policy_route": "shared_execution",
          "mission_command_overrides": {
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 1,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 25.0,
          },
        },
      ],
    },
  }


def _cooperative_air_2v2_scripted_opponent_scenario() -> dict:
  scenario = _cooperative_cruise_scenario()
  scenario["scenario_name"] = "cooperative_air_2v2_scripted_ew_smoke"
  scenario["meta"]["max_steps"] = 240
  scenario["mission_command"]["assigned_target_name"] = "Red_Lead"
  scenario["entities"].extend(
    [
      {
        "name": "Red_Lead",
        "type": "F-16C_Block50",
        "side": "Red",
        "is_agent": False,
        "pos": [0.0, 10000.0, 1400.0],
        "vel": [0.0, -220.0, 0.0],
        "heading": 180.0,
        "scripted_agent": {
          "name": "red_scripted_agent",
          "target_name": "Lead",
          "cruise_speed_mps": 220.0,
          "attack_speed_mps": 260.0,
          "defensive_speed_mps": 290.0,
          "threat_range_m": 9000.0,
          "merge_range_m": 3500.0,
          "fire_range_m": 9000.0,
          "beam_offset_deg": 85.0,
        },
        "ammo": {"missiles_remaining": 4, "max_missiles": 4},
        "weapon_cooldown": {"cooldown_s": 0.75, "last_fire_time": -1.0},
      },
      {
        "name": "Red_Wing",
        "type": "F-16C_Block50",
        "side": "Red",
        "is_agent": False,
        "pos": [-120.0, 10180.0, 1400.0],
        "vel": [0.0, -220.0, 0.0],
        "heading": 180.0,
        "scripted_agent": {
          "name": "red_scripted_agent",
          "target_name": "Wing",
          "cruise_speed_mps": 220.0,
          "attack_speed_mps": 260.0,
          "defensive_speed_mps": 290.0,
          "threat_range_m": 9000.0,
          "merge_range_m": 3500.0,
          "fire_range_m": 9000.0,
          "beam_offset_deg": 85.0,
        },
        "ammo": {"missiles_remaining": 4, "max_missiles": 4},
        "weapon_cooldown": {"cooldown_s": 0.75, "last_fire_time": -1.0},
      },
    ]
  )
  return scenario


def _cooperative_takeoff_to_cruise_scenario() -> dict:
  return {
    "scenario_name": "cooperative_takeoff_to_cruise_vec_env_smoke",
    "meta": {"max_steps": 16},
    "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
    "environment": {
      "time_step": 0.05,
      "terrain_type": "flat",
      "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
      "randomization": {
        "world_yaw_range": [0.0, 0.0],
        "world_yaw_origin": [0.0, 0.0],
        "rotate_mission_heading_with_world": True,
      },
    },
    "mission_command": {
      "command_code": 3,
      "target_heading": 90.0,
      "target_altitude": 1400.0,
      "target_speed": 205.0,
      "takeoff_procedure_code": 2,
      "takeoff_clearance_code": 3,
      "takeoff_interval_s": 6.0,
      "runway_slot_code": 1,
      "formation_id": 31,
      "form_offset_x": 180.0,
      "form_offset_y": -90.0,
      "form_offset_z": 30.0,
      "waypoint_mode": "flyby",
      "waypoints": [
        {"x": 14000.0, "y": 0.0, "z": 1400.0, "radius_m": 1000.0},
        {"x": 26000.0, "y": 3500.0, "z": 1400.0, "radius_m": 1000.0},
      ],
    },
    "entities": [
      {
        "name": "Lead",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1400.0, 0.0, 2.1],
        "vel": [0.0, 0.0, 0.0],
        "heading": 90.0,
      },
      {
        "name": "Wing",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1460.0, 0.0, 2.1],
        "vel": [0.0, 0.0, 0.0],
        "heading": 90.0,
      },
    ],
    "cooperative_roster": {
      "team_id": 7201,
      "element_id": 7201,
      "policy_route": "shared_execution",
      "members": [
        {
          "entity": "Lead",
          "role_code": 21,
          "formation_role_id": "ElementLead",
          "relative_slot_code": 11,
          "policy_route": "shared_execution",
          "mission_command_overrides": {
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 3,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "form_offset_x": 0.0,
            "form_offset_y": 0.0,
            "form_offset_z": 0.0,
          },
        },
        {
          "entity": "Wing",
          "role_code": 22,
          "formation_role_id": "Wingman",
          "relative_slot_code": 12,
          "reference_entity": "Lead",
          "policy_route": "shared_execution",
          "mission_command_overrides": {
            "takeoff_procedure_code": 2,
            "takeoff_clearance_code": 1,
            "takeoff_interval_s": 6.0,
            "runway_slot_code": 1,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 30.0,
          },
        },
      ],
    },
  }


class CooperativeVecEnvTaskingTests(unittest.TestCase):
  def test_multi_agent_runtime_view_task_order_export_uses_maintained_contracts_only(self) -> None:
    class _Loader:
      active_roster = []

    class _TaskingPacket:
      def __init__(self, refs, task_order_contracts):
        self.refs = list(refs)
        self.task_order_contracts = list(task_order_contracts)

    class _Runtime:
      def __init__(self) -> None:
        self.requests: list[object] = []

      def export_tasking_packet(self, request):
        self.requests.append(request)
        contract = cooperative_vec_env_module.ef_py.TaskOrderMaintainedBatchContract()
        contract.shared_core.task_id = 451
        return _TaskingPacket(request.refs, [contract])

    runtime = _Runtime()
    view = MultiAgentWorldRuntimeView(
      runtime=runtime,
      loader=_Loader(),
      world_index=0,
      action_space=None,
      action_mode="full",
      mission_obs_mode="basic",
      include_proprio=False,
    )
    ref = cooperative_vec_env_module.ef_py.WorldEntityRef()
    ref.world_index = 0
    ref.entity_id = 91
    view.refs = lambda: [ref] # type: ignore[method-assign]

    packet = view.export_tasking_packet(
      include_mission_command_contracts=False,
      include_task_order_contracts=True,
    )

    self.assertEqual(len(runtime.requests), 1)
    request = runtime.requests[0]
    self.assertTrue(bool(request.include_task_order_contracts))
    self.assertFalse(bool(request.include_mission_command_contracts))
    self.assertFalse(hasattr(request, "include_task_orders"))
    self.assertEqual(len(packet.task_order_contracts), 1)
    self.assertEqual(int(packet.task_order_contracts[0].shared_core.task_id), 451)
    self.assertFalse(hasattr(packet, "task_orders"))

  def test_multi_agent_runtime_view_default_observation_export_does_not_request_task_orders(self) -> None:
    class _Loader:
      active_roster = []

    class _Runtime:
      def __init__(self) -> None:
        self.requests: list[object] = []

      def export_observation_packet(self, request):
        self.requests.append(request)
        return cooperative_vec_env_module.ef_py.ObservationBatchPacket()

    runtime = _Runtime()
    view = MultiAgentWorldRuntimeView(
      runtime=runtime,
      loader=_Loader(),
      world_index=0,
      action_space=None,
      action_mode="full",
      mission_obs_mode="basic",
      include_proprio=False,
    )

    view.export_packet()

    self.assertEqual(len(runtime.requests), 1)
    request = runtime.requests[0]
    self.assertFalse(hasattr(request, "include_task_order_contracts"))
    self.assertFalse(hasattr(request, "include_mission_commands"))
    self.assertFalse(hasattr(request, "include_leader_intents"))
    self.assertFalse(hasattr(request, "include_pilot_reports"))
    self.assertFalse(hasattr(request, "include_mission_command_contracts"))
    self.assertFalse(hasattr(request, "include_leader_intent_contracts"))
    self.assertFalse(hasattr(request, "include_pilot_report_contracts"))
    self.assertFalse(hasattr(request, "include_task_orders"))

  def test_cooperative_world_batch_vec_env_batch_runtime_surface_is_removed(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        with self.assertRaises(AttributeError):
          _ = vec_env.batch_runtime
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_exposes_runtime_facade(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        self.assertIs(vec_env.runtime_facade, vec_env._runtime_adapter.facade)
        self.assertEqual(int(vec_env.runtime_facade.world_count()), 1)
        self.assertTrue(hasattr(vec_env.runtime_facade, "export_observation_packet"))
        self.assertTrue(hasattr(vec_env.runtime_facade, "step_batch"))
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_legacy_runtime_and_backends_are_removed(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      base_kwargs = {
        "scenario_path": scenario_path,
        "n_envs": 1,
        "include_visual": False,
        "include_proprio": True,
        "action_mode": "full",
        "mission_obs_mode": "nav_v2_formation_v1",
      }

      with self.subTest(option="execution_step_runtime_mode"):
        with self.assertRaisesRegex(ValueError, "execution_step_runtime_mode='legacy' has been removed"):
          CooperativeWorldBatchVecEnv(
            **base_kwargs,
            execution_step_runtime_mode="legacy",
          )

      with self.subTest(option="batch_observation_backend"):
        with self.assertRaisesRegex(ValueError, "batch_observation_backend='legacy' has been removed"):
          CooperativeWorldBatchVecEnv(
            **base_kwargs,
            batch_observation_backend="legacy",
          )

      with self.subTest(option="flight_shaping_backend"):
        with self.assertRaisesRegex(ValueError, "flight_shaping_backend='legacy' has been removed"):
          CooperativeWorldBatchVecEnv(
            **base_kwargs,
            flight_shaping_backend="legacy",
          )

  def test_cooperative_world_batch_vec_env_smoke(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        vec_env.seed(7)
        obs = vec_env.reset()
        self.assertEqual(obs["instruments"].shape[0], 2)
        self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_v1")))
        self.assertEqual(obs["proprio"].shape, (2, 17))

        actions = np.zeros((2, 17), dtype=np.float32)
        obs, rewards, dones, infos = vec_env.step(actions)
        self.assertEqual(rewards.shape, (2,))
        self.assertEqual(dones.shape, (2,))
        self.assertEqual(len(infos), 2)
        self.assertTrue(np.all(np.isfinite(rewards)))
        self.assertEqual(int(vec_env.slots_per_world), 2)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_role_mode_exposes_role_semantics(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_role_v1",
      )
      try:
        vec_env.seed(7)
        obs = vec_env.reset()
        self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_role_v1")))
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code")]),
          21.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_role_v1", "relative_slot_code")]),
          11.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(
            obs["mission"][0][
              mission_observation_field_index("nav_v2_formation_role_v1", "reference_relative_slot_code")
            ]
          ),
          0.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code")]),
          22.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_role_v1", "relative_slot_code")]),
          12.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(
            obs["mission"][1][
              mission_observation_field_index("nav_v2_formation_role_v1", "reference_relative_slot_code")
            ]
          ),
          11.0,
          places=6,
        )
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_takeoff_mode_exposes_interval_clearance_semantics(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_cooperative_takeoff_v1",
      )
      try:
        vec_env.seed(7)
        obs = vec_env.reset()
        self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_cooperative_takeoff_v1")))
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code")]),
          2.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
          3.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_interval_s")]),
          6.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "runway_slot_code")]),
          1.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code")]),
          2.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
          1.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_interval_s")]),
          6.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "runway_slot_code")]),
          1.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "self_role_code")]),
          22.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(
            obs["mission"][1][
              mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "reference_relative_slot_code")
            ]
          ),
          11.0,
          places=6,
        )
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_interval_director_promotes_wing_clearance_after_gate_open(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_cooperative_takeoff_v1",
      )
      try:
        vec_env.seed(7)
        vec_env.reset()
        world = vec_env._worlds[0]
        lead = vec_env._slots[0]
        wing = vec_env._slots[1]
        self.assertIsNotNone(lead)
        self.assertIsNotNone(wing)
        assert lead is not None
        assert wing is not None

        self.assertEqual(int(wing.loader.mission_cmd.get("takeoff_clearance_code", 0)), 1)
        lead.last_inst.ground_speed = 40.0
        lead.last_inst.alt_radar = 0.0
        lead.steps = 200
        wing.steps = 200
        lead.loader._coop_takeoff_roll_start_time_s = 0.0

        world.director.update(world, vec_env._world_slot_states(world), force=True)

        self.assertEqual(int(wing.loader.mission_cmd.get("takeoff_clearance_code", 0)), 3)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_interval_takeoff_starts_both_aircraft_on_runway_geometry(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_takeoff_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_interval_takeoff_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_cooperative_takeoff_v1",
      )
      try:
        vec_env.seed(7)
        vec_env.reset()
        for slot_state in vec_env._slots[:2]:
          self.assertIsNotNone(slot_state)
          assert slot_state is not None
          truth = slot_state.last_truth
          loader = slot_state.loader
          valid_rf, along_m, cross_m, rw_len, rw_wid = loader.get_runway_local_frame(
            float(truth.x),
            float(truth.y),
          )
          self.assertTrue(bool(valid_rf))
          self.assertLessEqual(abs(float(cross_m)), 0.5 * float(rw_wid) + 1.0)
          self.assertLessEqual(abs(float(along_m)), 0.5 * float(rw_len))
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_takeoff_to_cruise_bridge_exposes_route_and_takeoff_semantics(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_takeoff_to_cruise_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_takeoff_to_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_cooperative_takeoff_v1",
      )
      try:
        vec_env.seed(7)
        obs = vec_env.reset()
        self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_cooperative_takeoff_v1")))
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "command_code")]),
          3.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
          3.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_clearance_code")]),
          1.0,
          places=6,
        )
        self.assertGreater(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "dist_m")]),
          1000.0,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "form_offset_x_m")]),
          180.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "form_offset_y_m")]),
          -90.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "self_role_code")]),
          22.0,
          places=6,
        )

        actions = np.zeros((2, 17), dtype=np.float32)
        obs, rewards, dones, infos = vec_env.step(actions)
        self.assertEqual(obs["mission"].shape, (2, 25))
        self.assertEqual(rewards.shape, (2,))
        self.assertEqual(dones.shape, (2,))
        self.assertEqual(len(infos), 2)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_reuses_cached_step_evaluation(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      cached_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      uncached_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        cached_env.seed(7)
        uncached_env.seed(7)
        cached_env.reset()
        uncached_env.reset()

        cached_slot = cached_env._slots[0]
        uncached_slot = uncached_env._slots[0]
        self.assertIsNotNone(cached_slot)
        self.assertIsNotNone(uncached_slot)
        assert cached_slot is not None
        assert uncached_slot is not None

        cached_loader = cached_slot.loader
        uncached_loader = uncached_slot.loader

        self.assertIsNotNone(cached_loader._runtime_eval_cache.get("step_evaluation"))

        with unittest.mock.patch.object(
          cached_loader,
          "_build_step_evaluation_inputs",
          wraps=cached_loader._build_step_evaluation_inputs,
        ) as mocked_cached_build:
          cached_reward, cached_terminated, cached_truncated, cached_status = cached_loader.compute_full_step(
            cached_slot.last_obs,
            cached_loader.sim,
            cached_slot.steps,
            cached_slot.max_steps,
            truth=cached_slot.last_truth,
            inst_state=cached_slot.last_inst,
          )
          self.assertEqual(mocked_cached_build.call_count, 0)

        uncached_loader.reset_runtime_eval_cache()
        with unittest.mock.patch.object(
          uncached_loader,
          "_build_step_evaluation_inputs",
          wraps=uncached_loader._build_step_evaluation_inputs,
        ) as mocked_uncached_build:
          uncached_reward, uncached_terminated, uncached_truncated, uncached_status = (
            uncached_loader.compute_full_step(
              uncached_slot.last_obs,
              uncached_loader.sim,
              uncached_slot.steps,
              uncached_slot.max_steps,
              truth=uncached_slot.last_truth,
              inst_state=uncached_slot.last_inst,
            )
          )
          self.assertGreater(mocked_uncached_build.call_count, 0)

        self.assertAlmostEqual(float(cached_reward), float(uncached_reward), places=6)
        self.assertEqual(bool(cached_terminated), bool(uncached_terminated))
        self.assertEqual(bool(cached_truncated), bool(uncached_truncated))
        self.assertTrue(np.allclose(np.asarray(cached_status, dtype=np.float32), np.asarray(uncached_status, dtype=np.float32), atol=1.0e-6))
      finally:
        cached_env.close()
        uncached_env.close()

  def test_cooperative_world_batch_vec_env_applies_world_director_offsets(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        vec_env.set_leader_overrides(
          {
            "leader_form_offset_x": 0.0,
            "leader_form_offset_y": 0.0,
            "leader_form_offset_z": 0.0,
            "wingman_form_offset_x": 220.0,
            "wingman_form_offset_y": -110.0,
            "wingman_form_offset_z": 40.0,
          }
        )
        obs = vec_env.reset()
        self.assertEqual(obs["mission"].shape, (2, mission_observation_dim("nav_v2_formation_v1")))
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
          0.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
          220.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_y_m")]),
          -110.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_z_m")]),
          40.0,
          places=6,
        )

        actions = np.zeros((2, 17), dtype=np.float32)
        obs, rewards, dones, infos = vec_env.step(actions)
        self.assertEqual(rewards.shape, (2,))
        self.assertTrue(np.all(np.isfinite(rewards)))
        self.assertAlmostEqual(
          float(obs["mission"][0][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
          0.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m")]),
          220.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_y_m")]),
          -110.0,
          places=6,
        )
        self.assertAlmostEqual(
          float(obs["mission"][1][mission_observation_field_index("nav_v2_formation_v1", "form_offset_z_m")]),
          40.0,
          places=6,
        )
        self.assertEqual(len(infos), 2)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_runs_short_sb3_rollout(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    if PPO is None:
      self.skipTest("stable_baselines3 is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
      )
      try:
        model = PPO(
          "MultiInputPolicy",
          vec_env,
          n_steps=2,
          batch_size=2,
          n_epochs=1,
          learning_rate=3.0e-4,
          gamma=0.99,
          gae_lambda=0.95,
          ent_coef=0.0,
          vf_coef=0.5,
          max_grad_norm=0.5,
          device="cpu",
          verbose=0,
        )
        model.learn(total_timesteps=4)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_reports_observation_timing(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="full",
        mission_obs_mode="nav_v2_formation_v1",
        collect_step_timing=True,
        batch_observation_backend="compiled",
      )
      try:
        vec_env.seed(7)
        _obs = vec_env.reset()
        actions = np.zeros((2, 17), dtype=np.float32)
        _obs, _rewards, _dones, infos = vec_env.step(actions)
        timing = infos[0].get("timing", {})
        self.assertIn("obs_execution_observation_batch_ms", timing)
        self.assertIn("obs_mission_input_build_ms", timing)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_routes_ew_resources_per_roster_slot(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        scenario = _cooperative_cruise_scenario()
        scenario["meta"]["max_steps"] = 80
        json.dump(scenario, f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode="air_ew_hybrid_v1",
        mission_obs_mode="basic",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
      )
      try:
        vec_env.seed(20260516)
        vec_env.reset()
        self.assertEqual(tuple(vec_env.action_space.shape), (14,))
        actions = np.zeros((2, 14), dtype=np.float32)
        actions[0, 12] = 1.0
        actions[1, 13] = 1.0
        for _step in range(42):
          _obs, _rewards, dones, infos = vec_env.step(actions)

        self.assertEqual([info["entity_name"] for info in infos], ["Lead", "Wing"])
        self.assertEqual([info["formation_role_id"] for info in infos], ["ElementLead", "Wingman"])
        self.assertFalse(any(bool(done) for done in dones))
        lead = vec_env._slots[0].last_inst
        wing = vec_env._slots[1].last_inst
        self.assertLess(int(lead.countermeasure_chaff_remaining), 60)
        self.assertEqual(int(lead.countermeasure_flare_remaining), 30)
        self.assertEqual(int(wing.countermeasure_chaff_remaining), 60)
        self.assertLess(int(wing.countermeasure_flare_remaining), 30)
      finally:
        vec_env.close()

  def test_cooperative_world_batch_vec_env_runs_scripted_ew_against_two_opponents(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/cooperative_air_2v2.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_air_2v2_scripted_opponent_scenario(), f, ensure_ascii=True)

      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode="air_ew_hybrid_v1",
        mission_obs_mode="basic",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
      )
      models = [AirScriptedEWActionModel(dt=0.05), AirScriptedEWActionModel(dt=0.05)]
      try:
        vec_env.seed(20260516)
        observation_batch = vec_env.reset()
        self.assertGreaterEqual(len(vec_env._slots[0].loader.scripted_opponents), 2)
        self.assertEqual(len(vec_env._slots[1].loader.scripted_opponents), 0)
        owner_loader = vec_env._slots[0].loader
        self.assertEqual(
          {
            int(report["target_id"])
            for report in owner_loader.scripted_opponent_reports.values()
          },
          {
            int(owner_loader.entities["Lead"]),
            int(owner_loader.entities["Wing"]),
          },
        )
        models[0].reset(
          context={
            "observation": {key: np.asarray(value)[0] for key, value in observation_batch.items()},
            "phase_name": "stable_flight",
            "response_doctrine": "countermeasure_ready",
          }
        )
        models[1].reset(
          context={
            "observation": {key: np.asarray(value)[1] for key, value in observation_batch.items()},
            "phase_name": "stable_flight",
            "response_doctrine": "countermeasure_ready",
          }
        )

        launch_warning_steps = [[], []]
        request_steps = [[], []]
        resource_snapshot = None
        for step in range(1, 241):
          actions = []
          for slot_index, model in enumerate(models):
            observation = {key: np.asarray(value)[slot_index] for key, value in observation_batch.items()}
            rwr = np.asarray(observation.get("rwr", []), dtype=np.float32).reshape(-1, 4)
            if rwr.size and bool(np.any(rwr[:, 3] > 0.5)):
              launch_warning_steps[slot_index].append(step)
            action = model.decide(
              observation=observation,
              context={
                "phase_name": "stable_flight",
                "response_doctrine": "countermeasure_ready",
              },
              dt=0.05,
            )
            if bool(np.any(np.asarray(action[12:14]) > 0.5)):
              request_steps[slot_index].append(step)
            actions.append(action)
          observation_batch, _rewards, dones, _infos = vec_env.step(np.asarray(actions, dtype=np.float32))
          current_resources = [
            int(getattr(vec_env._slots[index].last_inst, "countermeasure_chaff_remaining", -1))
            for index in (0, 1)
          ]
          if all(launch_warning_steps) and all(
            current_resources[index] < 60
            for index in (0, 1)
          ):
            resource_snapshot = list(current_resources)
            break
          if any(bool(done) for done in dones):
            break

        self.assertTrue(launch_warning_steps[0])
        self.assertTrue(launch_warning_steps[1])
        self.assertTrue(request_steps[0])
        self.assertTrue(request_steps[1])
        self.assertEqual(launch_warning_steps, [[162, 202], [202]])
        self.assertEqual(request_steps, [[162, 202], [202]])
        self.assertIsNotNone(resource_snapshot)
        self.assertEqual(resource_snapshot, [58, 59])
        self.assertLess(int(resource_snapshot[0]), 60)
        self.assertLess(int(resource_snapshot[1]), 60)
      finally:
        for model in models:
          model.close()
        vec_env.close()



if __name__ == "__main__":
  unittest.main()
