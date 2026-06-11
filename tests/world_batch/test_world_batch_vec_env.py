from __future__ import annotations

import json
import tempfile
from typing import Any
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import torch # noqa: E402,F401

import ef_py # noqa: E402

from gym_envs.universal_env import UniversalEnv # noqa: E402
from gym_envs.universal_env_parts import NAVAL_STATION3_ACTION_FAMILY # noqa: E402
from python.rl.runtime.world_batch import command_chain_cache # noqa: E402
from python.rl.runtime.world_batch.command_chain_cache import ( # noqa: E402
  project_world_leader_intent_maintained_assignment,
  project_world_mission_command_maintained_assignment,
  project_world_pilot_report_maintained_assignment,
  project_world_task_order_maintained_assignment,
)
import python.rl.runtime.world_batch.adapter as world_batch_adapter_module # noqa: E402
import python.rl.runtime.world_batch_vec_env as vec_env_module # noqa: E402
from python.rl.control.wrappers import MultiTimescaleActionWrapper # noqa: E402
from python.rl.policy_algo.device_dict_rollout_buffer import DeviceDictRolloutBuffer # noqa: E402
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO # noqa: E402
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv # noqa: E402
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv # noqa: E402
from python.mission_obs_taxonomy import ( # noqa: E402
  mission_observation_dim,
  mission_observation_field_index,
)
from tests.support._leader_env_runtime_test_support import CounterDictEnv # noqa: E402


def _inline_vec_env_scenario() -> dict:
  return {
    "scenario_name": "phase4_world_batch_vec_env_inline",
    "meta": {
      "max_steps": 1,
    },
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
      }
    ],
  }


def _inline_vec_env_maritime_scenario() -> dict:
  scenario = _inline_vec_env_scenario()
  scenario["environment"]["maritime"] = {
    "sea_state": 0.0,
    "wave_heading_deg": 135.0,
    "wave_period_s": 11.0,
  }
  return scenario


def _legacy_step_result_state_with_poisoned_report_fields(source_state) -> ef_py.ExecutionEpisodeState:
  state = ef_py.ExecutionEpisodeState()
  state.agent_id = int(getattr(source_state, "agent_id", 0))
  state.step_count = int(getattr(source_state, "step_count", 0)) + 100
  state.prev_altitude_m = float(getattr(source_state, "prev_altitude_m", 0.0)) + 250.0
  state.last_termination_reason = "legacy_step_result_reason"
  state.last_reward_total = 91.25
  state.last_reward_breakdown_json = json.dumps(
    {"legacy_total": 91.25, "total": 91.25},
    ensure_ascii=True,
    sort_keys=True,
  )
  return state


def _inline_vec_env_route_transition_scenario() -> dict:
  scenario = _inline_vec_env_scenario()
  scenario["meta"]["max_steps"] = 3
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "waypoints": [
      {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
    ],
    "post_waypoint_transition": {
      "command_code": 2,
      "target_heading": 45.0,
      "target_altitude": 900.0,
      "target_speed": 160.0,
      "phase_name": "post_route",
      "transition_reward": 123.0,
    },
  }
  return scenario


def _inline_air_combat_scripted_opponent_scenario() -> dict:
  return {
    "scenario_name": "air_combat_world_batch_scripted_opponent_inline",
    "environment": {
      "time_step": 0.05,
      "max_steps": 320,
      "terrain_type": "flat",
      "wind": {
        "speed_mps": 0.0,
        "dir_from_deg": 0.0,
        "shear_mps_per_km": 0.0,
      },
    },
    "mission_command": {
      "command_code": 0,
      "target_heading": 0.0,
      "target_altitude": 1200.0,
      "target_speed": 180.0,
      "assigned_target_name": "Red_Fighter",
      "authorization_to_fire": True,
    },
    "entities": [
      {
        "name": "Blue_Fighter",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [0.0, 0.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 0.0,
        "ammo": {
          "missiles_remaining": 4,
          "max_missiles": 4,
        },
        "weapon_cooldown": {
          "cooldown_s": 0.75,
          "last_fire_time": -1.0,
        },
      },
      {
        "name": "Red_Fighter",
        "type": "F-16C_Block50",
        "side": "Red",
        "pos": [0.0, 8000.0, 1200.0],
        "vel": [0.0, -180.0, 0.0],
        "heading": 180.0,
        "scripted_agent": {
          "name": "red_scripted_agent",
          "target_name": "Blue_Fighter",
          "fire_range_m": 9000.0,
          "threat_range_m": 9000.0,
          "merge_range_m": 3500.0,
        },
        "ammo": {
          "missiles_remaining": 4,
          "max_missiles": 4,
        },
        "weapon_cooldown": {
          "cooldown_s": 0.75,
          "last_fire_time": -1.0,
        },
      },
    ],
  }


def _controller_runtime_state_matches_loader_state(runtime_state, loader_state) -> bool:
  def _canonicalize_json(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
      return str(raw or "")
    try:
      parsed = json.loads(raw)
    except Exception:
      return str(raw)

    def _strip_internal_fields(value):
      if isinstance(value, dict):
        return {
          str(key): _strip_internal_fields(item)
          for key, item in value.items()
          if not str(key).startswith("_")
        }
      if isinstance(value, list):
        return [_strip_internal_fields(item) for item in value]
      return value

    return json.dumps(_strip_internal_fields(parsed), ensure_ascii=True, sort_keys=True)

  def _route_digest(state) -> list[tuple[float, float, float, float, float, float, str]]:
    route = []
    for waypoint in list(getattr(state, "route_waypoints", [])):
      route.append(
        (
          float(getattr(waypoint, "x_m", 0.0)),
          float(getattr(waypoint, "y_m", 0.0)),
          float(getattr(waypoint, "z_m", 0.0)),
          float(getattr(waypoint, "radius_m", 0.0)),
          float(getattr(waypoint, "altitude_m", 0.0)),
          float(getattr(waypoint, "speed_mps", 0.0)),
          str(getattr(waypoint, "waypoint_mode", "")),
        )
      )
    return route

  runtime_digest = {
    "has_mission_command_json": bool(getattr(runtime_state, "has_mission_command_json", False)),
    "mission_command_json": _canonicalize_json(str(getattr(runtime_state, "mission_command_json", ""))),
    "route_waypoints": _route_digest(runtime_state),
    "has_post_waypoint_transition_json": bool(getattr(runtime_state, "has_post_waypoint_transition_json", False)),
    "post_waypoint_transition_json": _canonicalize_json(str(getattr(runtime_state, "post_waypoint_transition_json", ""))),
    "mission_phase_name": str(getattr(runtime_state, "mission_phase_name", "")),
    "has_cached_route_ref_id": bool(getattr(runtime_state, "has_cached_route_ref_id", False)),
    "cached_route_ref_id": int(getattr(runtime_state, "cached_route_ref_id", 0)),
  }
  loader_digest = {
    "has_mission_command_json": bool(getattr(loader_state, "has_mission_command_json", False)),
    "mission_command_json": _canonicalize_json(str(getattr(loader_state, "mission_command_json", ""))),
    "route_waypoints": _route_digest(loader_state),
    "has_post_waypoint_transition_json": bool(getattr(loader_state, "has_post_waypoint_transition_json", False)),
    "post_waypoint_transition_json": _canonicalize_json(str(getattr(loader_state, "post_waypoint_transition_json", ""))),
    "mission_phase_name": str(getattr(loader_state, "mission_phase_name", "")),
    "has_cached_route_ref_id": bool(getattr(loader_state, "has_cached_route_ref_id", False)),
    "cached_route_ref_id": int(getattr(loader_state, "cached_route_ref_id", 0)),
  }
  return runtime_digest == loader_digest


class WorldBatchVecEnvTests(unittest.TestCase):
  def test_command_chain_cache_leader_intent_snapshot_uses_named_owner_slice_projections(self) -> None:
    intent = ef_py.LeaderIntent()
    intent.command_code = 3
    intent.cmd_heading_deg = 91.0
    intent.cmd_altitude_m = 1250.0
    intent.cmd_speed_mps = 210.0
    intent.phase_id = ef_py.LeaderPhase.Reposition
    intent.formation_id = 17
    intent.form_offset_x = 120.0
    intent.recovery_base_id = 88
    intent.warfare_role_code = 5
    intent.officer_in_tactical_command = 7001

    snapshot = command_chain_cache.leader_intent_snapshot(intent)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "leader_intent_shared_core",
        "leader_intent_air_owner_slice",
        "leader_intent_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(projection_map["leader_intent_shared_core"]["command_code"], 3)
    self.assertEqual(projection_map["leader_intent_shared_core"]["cmd_heading_deg"], 91.0)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["phase_id"], ef_py.LeaderPhase.Reposition)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["formation_id"], 17)
    self.assertEqual(projection_map["leader_intent_air_owner_slice"]["recovery_base_id"], 88)
    self.assertEqual(projection_map["leader_intent_naval_owner_slice"]["warfare_role_code"], 5)
    self.assertEqual(projection_map["leader_intent_naval_owner_slice"]["officer_in_tactical_command"], 7001)
    self.assertEqual(
      tuple(projection_map["leader_intent_shared_core"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_shared_core(intent)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["leader_intent_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_air_owner_slice(intent)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["leader_intent_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.leader_intent_naval_owner_slice(intent)) if not name.startswith("_")),
    )

  def test_command_chain_cache_pilot_report_snapshot_uses_named_owner_slice_projections(self) -> None:
    report = ef_py.PilotReport()
    report.report_type = ef_py.CommMsgType.ACK_CANT_DO
    report.sender_id = 101
    report.status_value = 2.5
    report.element_id = 55
    report.phase_id = 8
    report.formation_role_id = 3
    report.formation_error_m = 12.0
    report.warfare_role_code = 9
    report.officer_in_tactical_command = 9002

    snapshot = command_chain_cache.pilot_report_snapshot(report)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "pilot_report_shared_core",
        "pilot_report_air_owner_slice",
        "pilot_report_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(
      projection_map["pilot_report_shared_core"]["report_type"],
      ef_py.CommMsgType.ACK_CANT_DO,
    )
    self.assertEqual(projection_map["pilot_report_shared_core"]["sender_id"], 101)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["element_id"], 55)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["phase_id"], 8)
    self.assertEqual(projection_map["pilot_report_air_owner_slice"]["formation_role_id"], 3)
    self.assertEqual(projection_map["pilot_report_naval_owner_slice"]["warfare_role_code"], 9)
    self.assertEqual(projection_map["pilot_report_naval_owner_slice"]["officer_in_tactical_command"], 9002)
    self.assertEqual(
      tuple(projection_map["pilot_report_shared_core"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_shared_core(report)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["pilot_report_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_air_owner_slice(report)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["pilot_report_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.pilot_report_naval_owner_slice(report)) if not name.startswith("_")),
    )

  def test_command_chain_cache_task_order_snapshot_uses_named_owner_slice_projections(self) -> None:
    order = ef_py.TaskOrder()
    order.task_id = 8
    order.active = True
    order.priority = 6
    order.issue_time_s = 12.5
    order.element_id = 13
    order.package_id = 21
    order.recovery_base_id = 22
    order.recovery_runway_id = 23
    order.recovery_approach_type = ef_py.RecoveryApproachType.ILS
    order.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
    order.takeoff_clearance_id = ef_py.TakeoffClearanceState.ClearedForTakeoff
    order.takeoff_interval_s = 17.5
    order.runway_slot_id = ef_py.RunwaySlotPosition.Right
    order.warfare_role_code = 4
    order.officer_in_tactical_command = 8004

    snapshot = command_chain_cache.task_order_snapshot(order)

    self.assertIsNotNone(snapshot)
    assert snapshot is not None
    projection_names = tuple(name for name, _fields in snapshot)
    self.assertEqual(
      projection_names,
      (
        "task_order_shared_core",
        "task_order_air_owner_slice",
        "task_order_naval_owner_slice",
      ),
    )
    projection_map = {name: dict(fields) for name, fields in snapshot}
    self.assertEqual(projection_map["task_order_shared_core"]["task_id"], 8)
    self.assertEqual(projection_map["task_order_shared_core"]["active"], True)
    self.assertEqual(projection_map["task_order_shared_core"]["priority"], 6)
    self.assertEqual(projection_map["task_order_shared_core"]["issue_time_s"], 12.5)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["element_id"], 13)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["package_id"], 21)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["recovery_base_id"], 22)
    self.assertEqual(projection_map["task_order_air_owner_slice"]["takeoff_interval_s"], 17.5)
    self.assertEqual(projection_map["task_order_naval_owner_slice"]["warfare_role_code"], 4)
    self.assertEqual(projection_map["task_order_naval_owner_slice"]["officer_in_tactical_command"], 8004)
    self.assertEqual(
      tuple(projection_map["task_order_shared_core"].keys()),
      tuple(name for name in dir(ef_py.task_order_shared_core(order)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["task_order_air_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.task_order_air_owner_slice(order)) if not name.startswith("_")),
    )
    self.assertEqual(
      tuple(projection_map["task_order_naval_owner_slice"].keys()),
      tuple(name for name in dir(ef_py.task_order_naval_owner_slice(order)) if not name.startswith("_")),
    )

  def test_world_batch_vec_env_applies_worker_thread_config(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        worker_threads=1,
      )
      try:
        self.assertEqual(int(vec_env.runtime_facade.worker_threads()), 1)
        self.assertEqual(int(vec_env.runtime_facade.effective_worker_threads()), 1)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_steps_and_auto_resets(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
      )
      try:
        vec_env.seed(123)
        obs = vec_env.reset()
        self.assertEqual(obs["instruments"].shape, (2, 42))
        self.assertEqual(obs["proprio"].shape, (2, 17))
        self.assertTrue(np.allclose(obs["proprio"], 0.0))

        obs, rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertEqual(rewards.shape, (2,))
        self.assertTrue(np.all(dones == np.asarray([True, True])))
        self.assertIn("terminal_observation", infos[0])
        self.assertIn("episode", infos[0])
        self.assertGreaterEqual(int(infos[0]["episode"]["l"]), 1)
        self.assertTrue(np.allclose(obs["proprio"], 0.0))
        self.assertEqual(vec_env.reset_infos, [{}, {}])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation(self) -> None:
    mode = "air_combat_c2_roe_v1"
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["mission_command"].update(
        {
          "roe_state": 3,
          "wcs_state": 2,
          "authorization_to_fire": True,
          "engage_order_state": 2,
          "shot_policy_state": 1,
          "shot_budget_remaining": 1,
          "pending_assessment": True,
        }
      )
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        mission_obs_mode=mode,
      )
      try:
        obs = vec_env.reset()
        mission = np.asarray(obs["mission"], dtype=np.float32)
        self.assertEqual(mission.shape, (2, mission_observation_dim(mode)))
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "roe_state")], 3.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "wcs_state")], 2.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "authorization_to_fire")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "shot_policy_state")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "shot_budget_remaining")], 1.0)
        )
        self.assertTrue(
          np.allclose(mission[:, mission_observation_field_index(mode, "pending_assessment")], 1.0)
        )
      finally:
        vec_env.close()

  def test_world_batch_vec_env_reset_uses_runtime_facade_compatibly(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
      )
      try:
        packet_requests: list[object] = []
        original_read_observation_packet = vec_env._runtime_adapter.read_observation_packet

        def _track_read_observation_packet(refs, **kwargs):
          packet_requests.append(kwargs)
          return original_read_observation_packet(refs, **kwargs)

        def _unexpected_get_agent_observations_batch(_refs):
          raise AssertionError("maintained vec-env observation reads should use export_observation_packet()")

        def _unexpected_get_instrument_states_batch(_refs):
          raise AssertionError("maintained vec-env observation reads should use export_observation_packet()")

        vec_env._runtime_adapter.read_observation_packet = _track_read_observation_packet # type: ignore[method-assign]
        vec_env._runtime_adapter.get_agent_observations_batch = _unexpected_get_agent_observations_batch # type: ignore[method-assign]
        vec_env._runtime_adapter.get_instrument_states_batch = _unexpected_get_instrument_states_batch # type: ignore[method-assign]

        self.assertTrue(hasattr(vec_env, "runtime_facade"))
        self.assertIsNotNone(vec_env.runtime_facade)
        self.assertEqual(int(vec_env.runtime_facade.world_count()), 2)

        vec_env.seed(123)
        obs = vec_env.reset()
        _obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))

        self.assertEqual(obs["instruments"].shape, (2, 42))
        self.assertEqual(obs["contacts"].shape[0], 2)
        self.assertEqual(obs["mission"].shape[0], 2)
        self.assertIsNotNone(vec_env.envs[0].agent_id)
        self.assertIsNotNone(vec_env.envs[1].agent_id)
        self.assertGreaterEqual(len(packet_requests), 2)
        self.assertTrue(
          all(bool(request.get("include_agent_observations", False)) for request in packet_requests)
        )
        self.assertTrue(
          all(bool(request.get("include_instrument_states", False)) for request in packet_requests)
        )
        self.assertTrue(all("include_mission_commands" not in request for request in packet_requests))
        self.assertTrue(all("include_task_orders" not in request for request in packet_requests))
        self.assertTrue(all("include_task_order_contracts" not in request for request in packet_requests))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_skips_stable_command_chain_exports(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(7)

        mission_calls: list[int] = []
        task_calls: list[int] = []
        intent_calls: list[int] = []
        report_calls: list[int] = []

        original_set_mission = vec_env._runtime_adapter.set_mission_commands_maintained_batch
        original_set_task = vec_env._runtime_adapter.set_task_orders_maintained_batch
        original_set_intent = vec_env._runtime_adapter.set_leader_intents_maintained_batch
        original_set_report = vec_env._runtime_adapter.set_pilot_reports_maintained_batch
        original_project_mission = vec_env_module.project_world_mission_command_maintained_assignment
        original_project_task = vec_env_module.project_world_task_order_maintained_assignment
        original_project_intent = vec_env_module.project_world_leader_intent_maintained_assignment
        original_project_report = vec_env_module.project_world_pilot_report_maintained_assignment
        projection_calls: list[tuple[str, int, int]] = []

        def _track_mission(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "mission_command") for assignment in materialized))
          mission_calls.append(len(materialized))
          return original_set_mission(materialized)

        def _track_task(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "task_order") for assignment in materialized))
          task_calls.append(len(materialized))
          return original_set_task(materialized)

        def _track_intent(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "leader_intent") for assignment in materialized))
          intent_calls.append(len(materialized))
          return original_set_intent(materialized)

        def _track_report(assignments):
          materialized = list(assignments)
          self.assertTrue(all(hasattr(assignment, "pilot_report") for assignment in materialized))
          report_calls.append(len(materialized))
          return original_set_report(materialized)

        def _track_project_mission(assignment, *, world_index, entity_id, compatibility_mission_command_shell):
          projection_calls.append(("mission", int(world_index), int(entity_id)))
          return original_project_mission(
            assignment,
            world_index=world_index,
            entity_id=entity_id,
            compatibility_mission_command_shell=compatibility_mission_command_shell,
          )

        def _track_project_intent(assignment, *, world_index, entity_id, compatibility_intent_shell):
          projection_calls.append(("intent", int(world_index), int(entity_id)))
          return original_project_intent(
            assignment,
            world_index=world_index,
            entity_id=entity_id,
            compatibility_intent_shell=compatibility_intent_shell,
          )

        def _track_project_report(assignment, *, world_index, entity_id, compatibility_report_shell):
          projection_calls.append(("report", int(world_index), int(entity_id)))
          return original_project_report(
            assignment,
            world_index=world_index,
            entity_id=entity_id,
            compatibility_report_shell=compatibility_report_shell,
          )

        def _track_project_task(assignment, *, world_index, entity_id, compatibility_task_order_shell):
          projection_calls.append(("task", int(world_index), int(entity_id)))
          return original_project_task(
            assignment,
            world_index=world_index,
            entity_id=entity_id,
            compatibility_task_order_shell=compatibility_task_order_shell,
          )

        vec_env._runtime_adapter.set_mission_commands_maintained_batch = _track_mission # type: ignore[method-assign]
        vec_env._runtime_adapter.set_task_orders_maintained_batch = _track_task # type: ignore[method-assign]
        vec_env._runtime_adapter.set_leader_intents_maintained_batch = _track_intent # type: ignore[method-assign]
        vec_env._runtime_adapter.set_pilot_reports_maintained_batch = _track_report # type: ignore[method-assign]
        vec_env_module.project_world_mission_command_maintained_assignment = _track_project_mission # type: ignore[assignment]
        vec_env_module.project_world_task_order_maintained_assignment = _track_project_task # type: ignore[assignment]
        vec_env_module.project_world_leader_intent_maintained_assignment = _track_project_intent # type: ignore[assignment]
        vec_env_module.project_world_pilot_report_maintained_assignment = _track_project_report # type: ignore[assignment]

        try:
          vec_env.reset()
          first_counts = (
            sum(mission_calls),
            sum(task_calls),
            sum(intent_calls),
            sum(report_calls),
          )
          self.assertGreater(first_counts[0], 0)
          self.assertGreater(first_counts[1], 0)
          self.assertGreater(first_counts[2], 0)
          self.assertGreater(first_counts[3], 0)
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_mission_commands_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_task_orders_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_leader_intents_batch"))
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_pilot_reports_batch"))
          self.assertTrue(any(kind == "mission" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "task" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "intent" for kind, _world_index, _entity_id in projection_calls))
          self.assertTrue(any(kind == "report" for kind, _world_index, _entity_id in projection_calls))

          vec_env._sync_command_chain_batch([0])
          second_counts = (
            sum(mission_calls),
            sum(task_calls),
            sum(intent_calls),
            sum(report_calls),
          )
          self.assertEqual(first_counts, second_counts)
          self.assertFalse(hasattr(vec_env._runtime_adapter, "set_task_orders_batch"))
        finally:
          vec_env_module.project_world_mission_command_maintained_assignment = original_project_mission # type: ignore[assignment]
          vec_env_module.project_world_task_order_maintained_assignment = original_project_task # type: ignore[assignment]
          vec_env_module.project_world_leader_intent_maintained_assignment = original_project_intent # type: ignore[assignment]
          vec_env_module.project_world_pilot_report_maintained_assignment = original_project_report # type: ignore[assignment]
      finally:
        vec_env.close()

  def test_world_batch_vec_env_reset_rearms_command_chain_exports(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(7)

        mission_calls: list[int] = []
        original_set_mission = vec_env._runtime_adapter.set_mission_commands_maintained_batch

        def _track_mission(assignments):
          materialized = list(assignments)
          mission_calls.append(len(materialized))
          return original_set_mission(materialized)

        vec_env._runtime_adapter.set_mission_commands_maintained_batch = _track_mission # type: ignore[method-assign]

        vec_env.reset()
        first_total = sum(mission_calls)
        self.assertGreater(first_total, 0)

        vec_env.reset()
        self.assertGreater(sum(mission_calls), first_total)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_batch_runtime_surface_is_removed(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        with self.assertRaises(AttributeError):
          _ = vec_env.batch_runtime
      finally:
        vec_env.close()

  def test_world_batch_vec_env_exposes_runtime_facade_for_diagnostics(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        self.assertIs(vec_env.runtime_facade, vec_env._runtime_adapter.facade)
        self.assertEqual(int(vec_env.runtime_facade.world_count()), 1)
        self.assertTrue(hasattr(vec_env.runtime_facade, "export_execution_episode_states"))
        self.assertTrue(hasattr(vec_env.runtime_facade, "execution_episode_ready"))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_loader_construction_does_not_require_raw_world_access(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      original_factory = vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime
      touched_fallback_calls: list[str] = []

      def _proxy_factory(adapter, env_idx):
        class _NoWorldConstructionProxy:
          def get_agent_observation(self, entity_id):
            return adapter.get_agent_observation(int(env_idx), int(entity_id))

          def get_instrument_state(self, entity_id):
            return adapter.get_instrument_state(int(env_idx), int(entity_id))

          def get_time_step(self):
            return adapter.get_time_step(int(env_idx))

          def set_mission_command(self, entity_id, command):
            assignment = ef_py.WorldMissionCommandMaintainedAssignment()
            project_world_mission_command_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_mission_command_shell=command,
            )
            adapter.set_mission_commands_maintained_batch([assignment])

          def set_task_order(self, entity_id, order):
            assignment = ef_py.WorldTaskOrderMaintainedAssignment()
            project_world_task_order_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_task_order_shell=order,
            )
            adapter.set_task_orders_maintained_batch([assignment])

          def set_leader_intent(self, entity_id, intent):
            assignment = ef_py.WorldLeaderIntentMaintainedAssignment()
            project_world_leader_intent_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_intent_shell=intent,
            )
            adapter.set_leader_intents_maintained_batch([assignment])

          def set_pilot_report(self, entity_id, report):
            assignment = ef_py.WorldPilotReportMaintainedAssignment()
            project_world_pilot_report_maintained_assignment(
              assignment,
              world_index=int(env_idx),
              entity_id=int(entity_id),
              compatibility_report_shell=report,
            )
            adapter.set_pilot_reports_maintained_batch([assignment])

          def __getattr__(self, name):
            touched_fallback_calls.append(str(name))
            raise AssertionError(f"loader construction/reset should not require fallback world method {name}")

        return _NoWorldConstructionProxy()

      vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime = _proxy_factory
      try:
        vec_env = WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=False,
          include_proprio=False,
        )
        try:
          vec_env.seed(123)
          obs = vec_env.reset()
          self.assertEqual(obs["instruments"].shape, (1, 42))
          self.assertEqual(touched_fallback_calls, [])
        finally:
          vec_env.close()
      finally:
        vec_env_module._RuntimeFacadeAdapter._scenario_loader_runtime = original_factory

  def test_world_batch_adapter_loader_runtime_task_order_write_routes_through_maintained_helper(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    original_project_task = world_batch_adapter_module.project_world_task_order_maintained_assignment
    project_calls: list[tuple[int, int, Any]] = []
    assignment_batches: list[list[Any]] = []

    def _track_project_task(assignment, *, world_index, entity_id, compatibility_task_order_shell):
      project_calls.append((int(world_index), int(entity_id), compatibility_task_order_shell))
      return original_project_task(
        assignment,
        world_index=world_index,
        entity_id=entity_id,
        compatibility_task_order_shell=compatibility_task_order_shell,
      )

    def _track_set_task_orders_batch(assignments):
      materialized = list(assignments)
      assignment_batches.append(materialized)

    world_batch_adapter_module.project_world_task_order_maintained_assignment = _track_project_task # type: ignore[assignment]
    adapter.set_task_orders_maintained_batch = _track_set_task_orders_batch # type: ignore[method-assign]
    try:
      proxy = adapter._scenario_loader_runtime(0)
      order = ef_py.TaskOrder()
      order.task_id = 23

      proxy.set_task_order(91, order)

      self.assertFalse(hasattr(adapter, "set_task_orders_batch"))
      self.assertEqual(project_calls, [(0, 91, order)])
      self.assertEqual(len(assignment_batches), 1)
      self.assertEqual(len(assignment_batches[0]), 1)
      assignment = assignment_batches[0][0]
      self.assertEqual(int(assignment.world_index), 0)
      self.assertEqual(int(assignment.entity_id), 91)
      self.assertEqual(int(assignment.task_order.shared_core.task_id), 23)
    finally:
      world_batch_adapter_module.project_world_task_order_maintained_assignment = original_project_task # type: ignore[assignment]

  def test_world_batch_adapter_scripted_fire_uses_launch_request_not_pilot_action(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    proxy = adapter._scenario_loader_runtime(0)
    mission_batches: list[list[Any]] = []
    launch_batches: list[list[Any]] = []
    pilot_batches: list[list[Any]] = []

    class _Observation:
      health = 1.0

    adapter.get_time_step = lambda _world_index: 0.05 # type: ignore[method-assign]
    adapter.get_agent_observation = lambda _world_index, _entity_id: _Observation() # type: ignore[method-assign]

    def _capture_mission(assignments):
      mission_batches.append(list(assignments))

    def _capture_launch(requests):
      materialized = list(requests)
      launch_batches.append(materialized)
      event = ef_py.LaunchEvent()
      event.request_id = int(materialized[0].request_id)
      event.accepted = True
      event.has_spawned_munition = True
      event.spawned_munition.world_index = int(materialized[0].shooter.world_index)
      event.spawned_munition.entity_id = 9101
      return [event]

    def _capture_pilot(assignments):
      pilot_batches.append(list(assignments))

    adapter.set_mission_commands_maintained_batch = _capture_mission # type: ignore[method-assign]
    adapter.apply_launch_requests_batch = _capture_launch # type: ignore[method-assign]
    adapter.set_pilot_actions_batch = _capture_pilot # type: ignore[method-assign]

    missile_id = proxy.fire_missile(17, 23)

    self.assertEqual(missile_id, 9101)
    self.assertEqual(len(mission_batches), 1)
    self.assertEqual(len(launch_batches), 1)
    self.assertEqual(pilot_batches, [])
    request = launch_batches[0][0]
    self.assertEqual(int(request.shooter.world_index), 0)
    self.assertEqual(int(request.shooter.entity_id), 17)
    self.assertEqual(int(request.target_entity.entity_id), 23)
    self.assertTrue(bool(request.has_target_entity))
    self.assertEqual(str(request.authority), "scripted_opponent")

  def test_world_batch_vec_env_skips_command_sync_for_inactive_terminal_agent(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(5)
        vec_env.reset()
        handle = vec_env.envs[0]

        class _InactiveTruth:
          health = 0.0

        handle.last_truth = _InactiveTruth()
        calls: list[str] = []
        vec_env._runtime_adapter.set_mission_commands_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"mission:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_task_orders_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"task:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_leader_intents_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"intent:{len(list(assignments))}")
        )
        vec_env._runtime_adapter.set_pilot_reports_maintained_batch = ( # type: ignore[method-assign]
          lambda assignments: calls.append(f"report:{len(list(assignments))}")
        )

        vec_env._sync_command_chain_batch([0])

        self.assertEqual(calls, [])
      finally:
        vec_env.close()

  def test_world_batch_adapter_legacy_task_order_batch_writer_is_removed(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    compat_adapter = vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled=True)

    self.assertFalse(hasattr(adapter, "set_task_orders_batch"))
    self.assertFalse(hasattr(adapter, "set_task_orders_batch_compatibility"))
    self.assertFalse(hasattr(compat_adapter, "set_task_orders_batch"))
    self.assertFalse(hasattr(compat_adapter, "set_task_orders_batch_compatibility"))

  def test_world_batch_adapter_runtime_compatibility_flag_is_strict(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled="false")
    compat_adapter = vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled="yes")

    self.assertFalse(adapter.runtime_compatibility_enabled)
    self.assertFalse(adapter.capabilities.runtime_compatibility_enabled)
    self.assertTrue(compat_adapter.runtime_compatibility_enabled)
    self.assertTrue(compat_adapter.capabilities.runtime_compatibility_enabled)

    with self.assertRaisesRegex(ValueError, "Unknown runtime_compatibility_enabled"):
      vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled="legacy-ish")

  def test_world_batch_adapter_capability_snapshot_tracks_facade_swaps(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled=True)

    self.assertTrue(adapter.capabilities.runtime_compatibility_enabled)

    class _TaskOrderCapableFacade:
      def __init__(self) -> None:
        self.batches: list[list[Any]] = []

      def set_task_orders_maintained_batch(self, assignments):
        self.batches.append(list(assignments))

    task_capable = _TaskOrderCapableFacade()
    adapter.facade = task_capable # type: ignore[assignment]

    self.assertTrue(adapter.capabilities.has_set_task_orders_maintained_batch)
    adapter.set_task_orders_maintained_batch([])
    self.assertEqual(task_capable.batches, [[]])

    class _TaskOrderMissingFacade:
      def set_task_orders_batch(self, assignments):
        raise AssertionError("legacy task-order fallback must not be probed")

    adapter.facade = _TaskOrderMissingFacade() # type: ignore[assignment]

    self.assertFalse(adapter.capabilities.has_set_task_orders_maintained_batch)
    with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
      adapter.set_task_orders_maintained_batch([])

  def test_world_batch_adapter_step_worlds_uses_facade_batch_step_without_raw_runtime_escape(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(2)

    class _FacadeStepOnly:
      def __init__(self) -> None:
        self.step_batch_calls = 0

      def step_batch(self):
        self.step_batch_calls += 1

      def world_count(self):
        return 2

      def runtime(self):
        raise AssertionError("maintained step_worlds must not request raw facade.runtime_compatibility_quarantine()")

    facade = _FacadeStepOnly()
    adapter.facade = facade # type: ignore[assignment]

    adapter.step_worlds([0, 1])

    self.assertEqual(facade.step_batch_calls, 1)

  def test_world_batch_adapter_step_worlds_rejects_partial_raw_runtime_step(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(2, runtime_compatibility_enabled=True)

    class _FacadeWithRawRuntime:
      def step_batch(self):
        raise AssertionError("partial step should not be widened silently")

      def world_count(self):
        return 2

      def runtime(self):
        raise AssertionError("partial maintained step must fail closed before raw runtime")

    adapter.facade = _FacadeWithRawRuntime() # type: ignore[assignment]

    with self.assertRaisesRegex(RuntimeError, "requires a full facade-owned batch step"):
      adapter.step_worlds([1])

  def test_world_batch_adapter_maintained_window_authorizes_explicit_facade_observation_provenance(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def __init__(self) -> None:
        self.requests: list[Any] = []

      def run_wp10_window(self, request):
        self.requests.append(request)
        result = ef_py.RuntimeWindowResult()
        result.observation_packet = ef_py.ObservationBatchPacket()
        result.engagement_packet = ef_py.EngagementEventPacket()
        return result

    facade = _FacadeWindow()
    adapter.facade = facade # type: ignore[assignment]
    action = ef_py.PilotAction()
    action.throttle = 0.75

    evidence = adapter.run_maintained_window(
      world_index=0,
      entity_id=42,
      pilot_action=action,
      input_snapshot_version="obs:0:42:7",
      information_state_label="facade_observation_packet",
      decision_model_id="blue-policy",
    )

    self.assertIsNotNone(evidence)
    self.assertEqual(len(facade.requests), 1)
    action_request = list(facade.requests[0].action_requests)[0]
    self.assertEqual(str(action_request.input_snapshot_version), "obs:0:42:7")
    self.assertEqual(str(action_request.action_intent.action_interface.kind), "PilotActionAssignmentCompat")
    self.assertEqual(str(action_request.action_intent.action_interface.payload_type), "pilot_action")
    self.assertEqual(str(action_request.action_intent.action_family), "direct_control")

  def test_world_batch_adapter_maintained_window_accepts_explicit_naval_action_family_while_using_pilot_action_transport(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def __init__(self) -> None:
        self.requests: list[Any] = []

      def run_wp10_window(self, request):
        self.requests.append(request)
        result = ef_py.RuntimeWindowResult()
        result.observation_packet = ef_py.ObservationBatchPacket()
        result.engagement_packet = ef_py.EngagementEventPacket()
        return result

    facade = _FacadeWindow()
    adapter.facade = facade # type: ignore[assignment]

    evidence = adapter.run_maintained_window(
      world_index=0,
      entity_id=42,
      pilot_action=ef_py.PilotAction(),
      input_snapshot_version="obs:0:42:8",
      information_state_label="facade_observation_packet",
      action_family=NAVAL_STATION3_ACTION_FAMILY,
      decision_model_id="naval-station-policy",
    )

    self.assertIsNotNone(evidence)
    self.assertEqual(len(facade.requests), 1)
    action_request = list(facade.requests[0].action_requests)[0]
    self.assertEqual(str(action_request.action_intent.action_family), NAVAL_STATION3_ACTION_FAMILY)
    self.assertEqual(str(action_request.action_intent.action_interface.kind), "PilotActionAssignmentCompat")
    self.assertEqual(str(action_request.action_intent.action_interface.payload_type), "pilot_action")

  def test_world_batch_adapter_maintained_window_rejects_compatibility_provenance_label(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _FacadeWindow:
      def run_wp10_window(self, request):
        raise AssertionError("authorization should fail before runtime window execution")

    adapter.facade = _FacadeWindow() # type: ignore[assignment]

    with self.assertRaisesRegex(RuntimeError, "requires explicit maintained ObservationPacket/DecisionBelief"):
      adapter.run_maintained_window(
        world_index=0,
        entity_id=42,
        pilot_action=ef_py.PilotAction(),
        information_state_label="agent_observation_compat",
      )

  def test_world_batch_adapter_loader_runtime_task_order_write_requires_maintained_binding(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)
    proxy = adapter._scenario_loader_runtime(0)
    original_ef_py = world_batch_adapter_module.ef_py

    class _NoMaintainedTaskOrderBindings:
      pass

    world_batch_adapter_module.ef_py = _NoMaintainedTaskOrderBindings() # type: ignore[assignment]
    try:
      with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
        proxy.set_task_order(91, object())
    finally:
      world_batch_adapter_module.ef_py = original_ef_py # type: ignore[assignment]

  def test_world_batch_adapter_task_order_reverse_projection_is_removed(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1)

    class _LegacyOnlyTarget:
      def __init__(self) -> None:
        self.legacy_batches: list[list[Any]] = []

      def set_task_orders_batch(self, assignments):
        self.legacy_batches.append(list(assignments))

    target = _LegacyOnlyTarget()
    adapter.facade = target # type: ignore[assignment]
    assignment = ef_py.WorldTaskOrderMaintainedAssignment()
    order = ef_py.TaskOrder()
    order.task_id = 31
    project_world_task_order_maintained_assignment(
      assignment,
      world_index=0,
      entity_id=91,
      compatibility_task_order_shell=order,
    )

    with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
      adapter.set_task_orders_maintained_batch([assignment])

    self.assertEqual(target.legacy_batches, [])

  def test_world_batch_adapter_task_order_reverse_projection_stays_removed_with_compatibility_opt_in(self) -> None:
    adapter = vec_env_module._RuntimeFacadeAdapter(1, runtime_compatibility_enabled=True)

    class _LegacyOnlyTarget:
      def __init__(self) -> None:
        self.legacy_batches: list[list[Any]] = []

      def set_task_orders_batch(self, assignments):
        self.legacy_batches.append(list(assignments))

    target = _LegacyOnlyTarget()
    adapter.facade = target # type: ignore[assignment]
    assignment = ef_py.WorldTaskOrderMaintainedAssignment()
    order = ef_py.TaskOrder()
    order.task_id = 37
    order.task_type = ef_py.TaskType.CAP
    order.element_id = 7001
    order.package_id = 7002
    order.lead_aircraft_id = 7003
    order.station_type = ef_py.StationType.Racetrack
    order.target_altitude_m = 6100.0
    order.target_speed_mps = 205.0
    order.formation_role_id = ef_py.FormationRole.Wingman
    order.wingman_slot_id = ef_py.WingmanSlot.Left
    order.naval_station_type = ef_py.NavalStationType.Screen
    project_world_task_order_maintained_assignment(
      assignment,
      world_index=0,
      entity_id=91,
      compatibility_task_order_shell=order,
    )

    with self.assertRaisesRegex(RuntimeError, "requires maintained TaskOrder batch bindings"):
      adapter.set_task_orders_maintained_batch([assignment])

    self.assertEqual(target.legacy_batches, [])

  def test_world_batch_vec_env_reset_layout_and_time_step_do_not_require_raw_world_fallback(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_maritime_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(19)
        layout = vec_env_module.build_compiled_world_layout(vec_env._compiled_scenario, seed=19)
        applied_world = vec_env._runtime_adapter.apply_world_layout(0, layout)
        self.assertIsNotNone(applied_world.agent_id)
        self.assertFalse(hasattr(vec_env._runtime_adapter, "_compat_world"))
        self.assertFalse(hasattr(vec_env._runtime_adapter, "_compat_runtime_handle"))
        obs = vec_env.reset()
        self.assertIsNotNone(obs)
        self.assertIsInstance(vec_env.reset_infos, list)
        self.assertAlmostEqual(float(vec_env._runtime_adapter.get_time_step(0)), 0.05, places=6)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_layout_materialization_routes_through_named_request_helper(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_maritime_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      original_apply = vec_env._runtime_adapter._apply_runtime_world_layout_request
      seen_requests: list[tuple[int, bool, float, float]] = []

      def _recording_apply(request):
        seen_requests.append(
          (
            int(request.world_index),
            bool(request.maritime_configured),
            float(request.wave_heading_deg),
            float(request.wave_period_s),
          )
        )
        return original_apply(request)

      vec_env._runtime_adapter._apply_runtime_world_layout_request = _recording_apply # type: ignore[method-assign]
      try:
        layout = vec_env_module.build_compiled_world_layout(vec_env._compiled_scenario, seed=37)
        applied_world = vec_env._runtime_adapter.apply_world_layout(0, layout)
        self.assertIsNotNone(applied_world.agent_id)
        self.assertEqual(seen_requests, [(0, True, 135.0, 11.0)])
      finally:
        vec_env._runtime_adapter._apply_runtime_world_layout_request = original_apply # type: ignore[method-assign]
        vec_env.close()

  def test_world_batch_adapter_exposes_layout_and_time_step_without_raw_world_proxy(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_maritime_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        layout = vec_env_module.build_compiled_world_layout(vec_env._compiled_scenario, seed=41)
        vec_env._runtime_adapter.apply_world_layout(0, layout)
        proxy_layout = vec_env._runtime_adapter.get_world_layout(0)
        self.assertIsNotNone(proxy_layout)
        assert proxy_layout is not None
        self.assertEqual(proxy_layout.terrain_type, "legacy")
        self.assertAlmostEqual(float(vec_env._runtime_adapter.get_time_step(0)), 0.05, places=6)
        self.assertFalse(hasattr(vec_env._runtime_adapter, "world_compatibility_quarantine"))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_drives_scripted_red_opponent_on_default_path(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/air_combat_scripted_opponent.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_air_combat_scripted_opponent_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(20260516)
        _obs = vec_env.reset()
        loader_red_id = int(vec_env.envs[0].loader.entities["Red_Fighter"])
        initial_missiles = int(
          getattr(vec_env.envs[0].loader.sim.get_agent_observation(loader_red_id), "missiles_remaining", -1)
        )

        action = np.zeros((1, 17), dtype=np.float32)
        action[0, 0] = 0.03
        action[0, 3] = 0.62
        action[0, 9] = 1.0

        saw_red_behavior = False
        red_fired = False
        for _ in range(220):
          _obs, _rewards, dones, _infos = vec_env.step(action)
          report = vec_env.envs[0].loader.scripted_opponent_reports.get(loader_red_id, {})
          if bool(report.get("active", False)):
            saw_red_behavior = True
          missiles_remaining = int(
            getattr(vec_env.envs[0].loader.sim.get_agent_observation(loader_red_id), "missiles_remaining", -1)
          )
          if missiles_remaining < initial_missiles:
            red_fired = True
            break
          if bool(dones[0]):
            break

        self.assertTrue(saw_red_behavior)
        self.assertTrue(red_fired)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_combat_loss_does_not_stack_crash_penalty(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/air_combat_scripted_opponent.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_air_combat_scripted_opponent_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        mission_obs_mode="basic",
        step_info_mode="terminal",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
      )
      try:
        vec_env.seed(20260516)
        vec_env.reset()

        action = np.zeros((1, 17), dtype=np.float32)
        for _step in range(260):
          _obs, rewards, dones, infos = vec_env.step(action)
          if bool(dones[0]):
            break
        else:
          self.fail("scripted red opponent did not terminate the 1v1 probe")

        self.assertEqual(str(infos[0].get("termination_reason")), "combat_loss")
        reward_terms = dict(infos[0].get("reward_terms", {}))
        self.assertEqual(float(rewards[0]), -1500.0)
        self.assertEqual(float(reward_terms.get("combat_loss_penalty", 0.0)), -1500.0)
        self.assertNotIn("crash_penalty", reward_terms)
        self.assertAlmostEqual(float(reward_terms.get("total", 0.0)), -1500.0, places=6)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_supports_visual_observations(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=True,
        include_proprio=False,
        visual_downsample=2,
        visual_update_interval=2,
      )
      try:
        obs = vec_env.reset()
        self.assertEqual(obs["visual"].shape, (2, 24, 48, 10))
        obs2, rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertEqual(obs2["visual"].shape, (2, 24, 48, 10))
        self.assertEqual(rewards.shape, (2,))
        self.assertEqual(dones.shape, (2,))
        self.assertEqual(len(infos), 2)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_visual_batch_export_prefers_facade_owned_helper(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=True,
        include_proprio=False,
        visual_downsample=2,
      )
      try:
        calls: list[str] = []
        original_facade_fn = ef_py.compute_world_batch_visual_observation_batch_numpy

        def _wrapped(target, refs, downsample, use_gpu):
          calls.append(type(target).__name__)
          if isinstance(target, ef_py.RuntimeFacade):
            return original_facade_fn(target, refs, downsample, use_gpu)
          raise AssertionError("maintained visual export should prefer RuntimeFacade target")

        ef_py.compute_world_batch_visual_observation_batch_numpy = _wrapped
        try:
          obs = vec_env.reset()
        finally:
          ef_py.compute_world_batch_visual_observation_batch_numpy = original_facade_fn

        self.assertEqual(obs["visual"].shape, (1, 24, 48, 10))
        self.assertEqual(calls, ["RuntimeFacade"])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_legacy_visual_backend_is_removed(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      with self.assertRaisesRegex(ValueError, "batch_visual_backend='legacy' has been removed"):
        WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=True,
          include_proprio=False,
          visual_downsample=2,
          batch_visual_backend="legacy",
        )

  def test_world_batch_vec_env_attaches_visual_without_redundant_refresh(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=True,
        include_proprio=False,
        visual_downsample=2,
        visual_update_interval=2,
      )
      try:
        refresh_calls: list[list[int]] = []
        original_refresh = vec_env._refresh_visual_batch

        def _tracked_refresh(indices=None):
          target = list(range(vec_env.num_envs)) if indices is None else [int(i) for i in indices]
          refresh_calls.append(target)
          return original_refresh(indices)

        vec_env._refresh_visual_batch = _tracked_refresh # type: ignore[method-assign]
        obs = vec_env.reset()
        self.assertEqual(obs["visual"].shape, (2, 24, 48, 10))
        self.assertEqual(refresh_calls, [[0, 1]])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_supports_per_env_randomization_overrides(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 4
      scenario_data["environment"]["randomization"] = {
        "world_yaw_range": [-15.0, 15.0],
        "world_yaw_origin": [0.0, 0.0],
      }
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.env_method("set_randomization_overrides", {"world_yaw_range": [-5.0, -5.0]}, indices=[0])
        vec_env.env_method("set_randomization_overrides", {"world_yaw_range": [10.0, 10.0]}, indices=[1])
        obs = vec_env.reset()
        self.assertEqual(obs["instruments"].shape, (2, 42))
        overrides = vec_env.get_attr("randomization_overrides")
        self.assertEqual(float(overrides[0]["world_yaw_range"][0]), -5.0)
        self.assertEqual(float(overrides[1]["world_yaw_range"][0]), 10.0)
        yaw_values = vec_env.get_attr("world_yaw_deg")
        self.assertNotEqual(float(yaw_values[0]), float(yaw_values[1]))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_legacy_batch_observation_backend_is_removed(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      with self.assertRaisesRegex(ValueError, "batch_observation_backend='legacy' has been removed"):
        WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=2,
          include_visual=False,
          include_proprio=True,
          batch_observation_backend="legacy",
        )

  def test_world_batch_vec_env_compiled_observation_arrays_are_float32(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
        batch_observation_backend="compiled",
      )
      try:
        obs = vec_env.reset()
        for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
          self.assertEqual(obs[key].dtype, np.float32)
        obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
          self.assertEqual(obs[key].dtype, np.float32)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_temporal_history_tracks_reset_and_last_action(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 3
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
        temporal_history_len=4,
        batch_observation_backend="compiled",
      )
      try:
        obs = vec_env.reset()
        self.assertEqual(obs["instruments_history"].shape, (2, 4, 42))
        self.assertEqual(obs["contacts_history"].shape, (2, 4, 10, 5))
        self.assertEqual(obs["rwr_history"].shape, (2, 4, 4, 4))
        self.assertEqual(obs["mission_history"].shape, (2, 4, obs["mission"].shape[-1]))
        self.assertEqual(obs["proprio_history"].shape, (2, 4, 17))
        self.assertTrue(np.allclose(obs["instruments_history"][:, -1], obs["instruments"]))
        self.assertTrue(np.allclose(obs["proprio_history"], 0.0))

        actions = np.zeros((2, 17), dtype=np.float32)
        actions[0, 0] = 0.25
        actions[0, 3] = 0.75
        actions[1, 1] = -0.5
        obs, _rewards, _dones, _infos = vec_env.step(actions)

        self.assertTrue(np.allclose(obs["proprio"], actions))
        self.assertTrue(np.allclose(obs["proprio_history"][:, -1, :], actions))
        self.assertTrue(np.allclose(obs["instruments_history"][:, -1], obs["instruments"]))
        self.assertTrue(np.allclose(obs["proprio_history"][:, -2, :], 0.0))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_auto_batch_observation_backend_uses_compiled(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
        temporal_history_len=3,
        batch_observation_backend="auto",
      )
      try:
        vec_env.seed(123)
        obs = vec_env.reset()
        self.assertEqual(vec_env._batch_observation_backend_mode(), "compiled")
        for key in (
          "instruments_history",
          "contacts_history",
          "rwr_history",
          "mission_history",
          "proprio_history",
        ):
          self.assertEqual(obs[key].shape[0], 2)
          self.assertEqual(obs[key].shape[1], 3)

        actions = np.full((2, 17), 0.1, dtype=np.float32)
        obs, _rewards, _dones, _infos = vec_env.step(actions)
        for key in (
          "instruments_history",
          "contacts_history",
          "rwr_history",
          "mission_history",
          "proprio_history",
        ):
          self.assertEqual(obs[key].shape[0], 2)
          self.assertEqual(obs[key].shape[1], 3)
        self.assertTrue(np.allclose(obs["proprio"], actions))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_compiled_batch_visual_is_deterministic(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      first_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=True,
        include_proprio=False,
        visual_downsample=2,
        visual_update_interval=1,
        batch_visual_backend="compiled",
      )
      second_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=True,
        include_proprio=False,
        visual_downsample=2,
        visual_update_interval=1,
        batch_visual_backend="compiled",
      )
      try:
        first_env.seed(123)
        second_env.seed(123)
        first_obs = first_env.reset()
        second_obs = second_env.reset()
        self.assertTrue(
          np.allclose(first_obs["visual"], second_obs["visual"], atol=1.0e-5),
          msg="reset visual mismatch",
        )

        actions = np.zeros((2, 17), dtype=np.float32)
        first_obs, first_rewards, first_dones, _first_infos = first_env.step(actions)
        second_obs, second_rewards, second_dones, _second_infos = second_env.step(actions)
        self.assertTrue(
          np.allclose(first_obs["visual"], second_obs["visual"], atol=1.0e-5),
          msg="step visual mismatch",
        )
        self.assertTrue(np.allclose(first_rewards, second_rewards, atol=1.0e-6))
        self.assertTrue(np.array_equal(first_dones, second_dones))
      finally:
        first_env.close()
        second_env.close()

  def test_world_batch_vec_env_binds_compiled_runtime_metadata_to_loaders(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["environment"]["randomization"] = {
        "world_yaw_range": [-10.0, 10.0],
        "world_yaw_origin": [0.0, 0.0],
      }
      scenario_data["objectives"] = [
        {
          "type": "conditional",
          "reward": 25.0,
          "conditions": [
            {"property": "heading", "op": ">=", "value": 0.0},
          ],
        }
      ]
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        for handle in vec_env.envs:
          self.assertIsNotNone(handle.loader._compiled_runtime_metadata)
          self.assertIs(handle.loader._compiled_runtime_metadata, vec_env._compiled_scenario.runtime_metadata)
          self.assertEqual(len(handle.loader._compiled_conditional_objectives), 1)
          self.assertEqual(len(handle.loader.ils_beacons), 1)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_propagates_execution_step_runtime_mode(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
      )
      try:
        for handle in vec_env.envs:
          self.assertEqual(handle.loader.execution_step_runtime_mode, "compiled")
          self.assertTrue(bool(handle.loader.use_compiled_execution_step_runtime))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_rejects_legacy_runtime_mode(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      with self.assertRaisesRegex(ValueError, "execution_step_runtime_mode='legacy' has been removed"):
        WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=False,
          include_proprio=False,
          execution_step_runtime_mode="legacy",
          runtime_compatibility_enabled=True,
        )

  def test_world_batch_vec_env_rejects_boolean_style_runtime_mode_aliases(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      for mode_alias in ("python", "off", "0", "false", "on", "1", "true"):
        with self.subTest(runtime_mode=mode_alias):
          with self.assertRaisesRegex(ValueError, "Unknown execution_step_runtime_mode"):
            WorldBatchVecEnv(
              scenario_path=scenario_path,
              n_envs=1,
              include_visual=False,
              include_proprio=False,
              execution_step_runtime_mode=mode_alias,
              runtime_compatibility_enabled=True,
            )

        with self.subTest(flight_shaping_backend=mode_alias):
          with self.assertRaisesRegex(ValueError, "Unknown flight_shaping_backend"):
            WorldBatchVecEnv(
              scenario_path=scenario_path,
              n_envs=1,
              include_visual=False,
              include_proprio=False,
              flight_shaping_backend=mode_alias,
              runtime_compatibility_enabled=True,
            )

  def test_world_batch_vec_env_reports_effective_flight_shaping_backend_mode(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      compiled_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="auto",
      )
      gpu_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="gpu_host",
      )
      try:
        self.assertEqual(compiled_env._flight_shaping_backend_mode(), "compiled")
        self.assertEqual(gpu_env._flight_shaping_backend_mode(), "gpu_host")
      finally:
        compiled_env.close()
        gpu_env.close()

  def test_world_batch_vec_env_rejects_legacy_flight_shaping_backend(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      with self.assertRaisesRegex(ValueError, "flight_shaping_backend='legacy' has been removed"):
        WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=False,
          include_proprio=False,
          flight_shaping_backend="legacy",
          runtime_compatibility_enabled=True,
        )

  def test_world_batch_vec_env_execution_episode_controller_shadow_compare_flag_off_is_noop(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        self.assertFalse(bool(dones[0]))
        self.assertNotIn("execution_episode_controller_shadow_compare", infos[0])
        self.assertEqual(vec_env.last_execution_episode_controller_shadow_compare, [None])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_execution_episode_controller_shadow_compare_reports_parity(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        execution_episode_controller_shadow_compare=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        self.assertFalse(bool(dones[0]))
        report = infos[0].get("execution_episode_controller_shadow_compare")
        self.assertIsNotNone(report)
        comparison = dict(report["comparison"])
        self.assertTrue(bool(comparison["overall_match"]), msg=str(comparison))
        self.assertTrue(bool(report["advance_state"]))
        self.assertEqual(int(report["shadow_state"]["step_count"]), 1)
        latest_report = vec_env.last_execution_episode_controller_shadow_compare[0]
        self.assertIsNotNone(latest_report)
        self.assertTrue(bool(latest_report["comparison"]["overall_match"]))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_execution_episode_controller_shadow_compare_resyncs_on_autoreset(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 1
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_episode_controller_shadow_compare=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        for step_idx in range(2):
          _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
          self.assertTrue(bool(dones[0]))
          report = infos[0].get("execution_episode_controller_shadow_compare")
          self.assertIsNotNone(report)
          comparison = dict(report["comparison"])
          self.assertTrue(bool(comparison["overall_match"]), msg=f"step={step_idx}: {comparison}")

          ref = ef_py.WorldEntityRef()
          ref.world_index = 0
          ref.entity_id = int(vec_env.envs[0].agent_id)
          controller_state = vec_env.export_execution_episode_states([ref])[0]
          loader_state = vec_env.envs[0].loader.build_execution_episode_state()
          self.assertTrue(ef_py.execution_episode_states_equivalent(controller_state, loader_state))
          self.assertEqual(int(controller_state.step_count), 0)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_execution_episode_controller_mainline_rejects_shadow_compare(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

      with self.assertRaises(RuntimeError):
        WorldBatchVecEnv(
          scenario_path=scenario_path,
          n_envs=1,
          include_visual=False,
          include_proprio=False,
          execution_episode_controller_shadow_compare=True,
          execution_episode_controller_mainline=True,
        )

  def test_world_batch_vec_env_execution_episode_controller_mainline_matches_compiled_default(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 3
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      legacy_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
      )
      mainline_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        legacy_env.seed(123)
        mainline_env.seed(123)
        legacy_obs = legacy_env.reset()
        mainline_obs = mainline_env.reset()
        for key in ("instruments", "contacts", "rwr", "mission"):
          self.assertTrue(
            np.allclose(np.asarray(legacy_obs[key]), np.asarray(mainline_obs[key]), atol=1.0e-6),
            msg=f"reset mismatch for key={key}",
          )

        action = np.zeros((1, 17), dtype=np.float32)
        for step_idx in range(2):
          legacy_obs, legacy_rewards, legacy_dones, legacy_infos = legacy_env.step(action)
          mainline_obs, mainline_rewards, mainline_dones, mainline_infos = mainline_env.step(action)
          self.assertFalse(bool(legacy_dones[0]), msg=f"legacy unexpectedly done at step={step_idx}")
          self.assertFalse(bool(mainline_dones[0]), msg=f"mainline unexpectedly done at step={step_idx}")
          self.assertAlmostEqual(float(legacy_rewards[0]), float(mainline_rewards[0]), places=6)
          self.assertTrue(
            np.allclose(
              np.asarray(legacy_infos[0]["mission_status"], dtype=np.float32),
              np.asarray(mainline_infos[0]["mission_status"], dtype=np.float32),
              atol=1.0e-6,
            ),
            msg=f"mission_status mismatch at step={step_idx}",
          )
          self.assertEqual(
            legacy_infos[0].get("termination_reason"),
            mainline_infos[0].get("termination_reason"),
          )
          self.assertEqual(
            set(dict(legacy_infos[0].get("reward_terms", {})).keys()),
            set(dict(mainline_infos[0].get("reward_terms", {})).keys()),
          )
          for key, value in dict(legacy_infos[0].get("reward_terms", {})).items():
            self.assertAlmostEqual(
              float(value),
              float(dict(mainline_infos[0]["reward_terms"])[key]),
              places=6,
              msg=f"reward term mismatch for {key} at step={step_idx}",
            )
          for key in ("instruments", "contacts", "rwr", "mission"):
            self.assertTrue(
              np.allclose(np.asarray(legacy_obs[key]), np.asarray(mainline_obs[key]), atol=1.0e-5),
              msg=f"step={step_idx} mismatch for key={key}",
            )

        ref = ef_py.WorldEntityRef()
        ref.world_index = 0
        ref.entity_id = int(mainline_env.envs[0].agent_id)
        runtime_state = mainline_env.export_execution_episode_states([ref])[0]
        loader_state = mainline_env.envs[0].loader.build_execution_episode_state()
        self.assertTrue(
          _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
        )
      finally:
        legacy_env.close()
        mainline_env.close()

  def test_world_batch_vec_env_execution_episode_controller_mainline_resyncs_on_autoreset(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 1
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        for _step_idx in range(2):
          _obs, _rewards, dones, _infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
          self.assertTrue(bool(dones[0]))
          self.assertTrue(bool(vec_env.execution_episode_ready(0)))
          ref = ef_py.WorldEntityRef()
          ref.world_index = 0
          ref.entity_id = int(vec_env.envs[0].agent_id)
          runtime_state = vec_env.export_execution_episode_states([ref])[0]
          loader_state = vec_env.envs[0].loader.build_execution_episode_state()
          self.assertEqual(int(runtime_state.step_count), 0)
          self.assertTrue(
            _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
          )
      finally:
        vec_env.close()

  def test_world_batch_vec_env_execution_episode_controller_mainline_reprime_handles_post_waypoint_transition(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      legacy_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
      )
      mainline_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        legacy_env.seed(123)
        mainline_env.seed(123)
        _ = legacy_env.reset()
        _ = mainline_env.reset()
        action = np.zeros((1, 17), dtype=np.float32)
        _legacy_obs, legacy_rewards, legacy_dones, legacy_infos = legacy_env.step(action)
        _mainline_obs, mainline_rewards, mainline_dones, mainline_infos = mainline_env.step(action)

        self.assertAlmostEqual(float(legacy_rewards[0]), float(mainline_rewards[0]), places=6)
        self.assertEqual(bool(legacy_dones[0]), bool(mainline_dones[0]))
        self.assertTrue(
          np.allclose(
            np.asarray(legacy_infos[0]["mission_status"], dtype=np.float32),
            np.asarray(mainline_infos[0]["mission_status"], dtype=np.float32),
            atol=1.0e-6,
          )
        )
        self.assertAlmostEqual(
          float(mainline_infos[0]["reward_terms"]["phase_transition_bonus"]),
          123.0,
          places=6,
        )
        self.assertEqual(int(mainline_env.envs[0].loader.mission_cmd["command_code"]), 2)
        self.assertEqual(str(mainline_env.envs[0].loader.mission_phase_name), "post_route")

        ref = ef_py.WorldEntityRef()
        ref.world_index = 0
        ref.entity_id = int(mainline_env.envs[0].agent_id)
        runtime_state = mainline_env.export_execution_episode_states([ref])[0]
        loader_state = mainline_env.envs[0].loader.build_execution_episode_state()
        self.assertTrue(
          _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
        )
        self.assertEqual(str(runtime_state.mission_phase_name), "post_route")
        self.assertEqual(len(list(runtime_state.route_waypoints)), 0)
      finally:
        legacy_env.close()
        mainline_env.close()

  def test_world_batch_vec_env_execution_episode_controller_mainline_skips_python_behavior_updates(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        def _unexpected_update_behaviors(*_args, **_kwargs):
          raise AssertionError("mainline path should not call ScenarioLoader.update_behaviors()")

        vec_env.envs[0].loader.update_behaviors = _unexpected_update_behaviors
        obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

        self.assertFalse(bool(dones[0]))
        self.assertGreaterEqual(float(rewards[0]), 0.0)
        self.assertEqual(obs["mission"].shape[0], 1)
        self.assertIn("mission_status", infos[0])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_prefers_facade_batch_step_contract_fields(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        original = vec_env._step_execution_episode_controller_mainline_requests

        def _wrapped(requests):
          result = original(requests)
          step_result = result.step_results[0]
          result.rewards = [-42.5]
          result.terminated = [bool(step_result.terminated)]
          result.truncated = [bool(step_result.truncated)]
          result.status_vectors = [[9.0, 8.0, 7.0, 6.0]]
          result.termination_reasons = ["facade_contract_reason"]
          result.reward_breakdown_jsons = ['{"facade_bonus": 3.25, "total": -42.5}']
          step_info_inputs = ef_py.StepInfoInputs()
          step_info_inputs.on_runway = False
          step_info_inputs.gear_collapsed = True
          step_info_inputs.gear_stress = 12.5
          step_info_inputs.alt_agl_m = 0.0
          step_info_inputs.on_ground_alt_threshold_m = 2.5
          step_info_inputs.airborne_alt_threshold_m = 5.0
          step_info_inputs.has_runway_frame = True
          step_info_inputs.runway_frame.valid = True
          step_info_inputs.runway_frame.cross_m = 123.0
          step_info_inputs.runway_frame.along_m = 456.0
          step_info_inputs.runway_frame.length_m = 2000.0
          step_info_inputs.runway_frame.width_m = 50.0
          step_info_inputs.runway_width_margin_m = 2.0
          step_info_inputs.runway_length_margin_m = 0.0
          step_info = ef_py.compute_step_info_runtime(step_info_inputs)
          result.step_infos = [step_info]
          result.step_info_valid_flags = [True]
          result.controller_state_changed_flags = [bool(step_result.structural_state_changed)]
          return result

        vec_env._step_execution_episode_controller_mainline_requests = _wrapped
        _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

        self.assertFalse(bool(dones[0]))
        self.assertAlmostEqual(float(rewards[0]), -42.5, places=6)
        self.assertTrue(
          np.allclose(
            np.asarray(infos[0]["mission_status"], dtype=np.float32),
            np.asarray([9.0, 8.0, 7.0, 6.0], dtype=np.float32),
            atol=1.0e-6,
          )
        )
        self.assertEqual(str(infos[0]["termination_reason"]), "facade_contract_reason")
        self.assertAlmostEqual(float(infos[0]["reward_terms"]["facade_bonus"]), 3.25, places=6)
        self.assertAlmostEqual(float(infos[0]["reward_terms"]["total"]), -42.5, places=6)
        self.assertEqual(float(infos[0]["on_runway"]), 0.0)
        self.assertEqual(float(infos[0]["gear_collapsed"]), 1.0)
        self.assertAlmostEqual(float(infos[0]["gear_stress"]), 12.5, places=6)
        self.assertEqual(float(infos[0]["on_ground"]), 1.0)
        self.assertEqual(float(infos[0]["on_runway_geom"]), 0.0)
        self.assertAlmostEqual(float(infos[0]["runway_cross_m"]), 123.0, places=6)
        self.assertAlmostEqual(float(infos[0]["runway_along_m"]), 456.0, places=6)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_full_step_info_reuses_facade_fields_without_python_rebuild(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
        step_info_mode="full",
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        original = vec_env._step_execution_episode_controller_mainline_requests

        def _wrapped(requests):
          result = original(requests)
          step_result = result.step_results[0]
          result.rewards = [float(getattr(step_result, "reward_total", 0.0))]
          result.terminated = [bool(step_result.terminated)]
          result.truncated = [bool(step_result.truncated)]
          result.status_vectors = [[1.0, 2.0, 3.0, 4.0]]
          result.termination_reasons = ["facade_contract_reason"]
          result.reward_breakdown_jsons = ['{"facade_bonus": 1.0, "total": 1.0}']
          step_info_inputs = ef_py.StepInfoInputs()
          step_info_inputs.on_runway = False
          step_info_inputs.gear_collapsed = True
          step_info_inputs.gear_stress = 9.5
          step_info_inputs.alt_agl_m = 0.0
          step_info_inputs.on_ground_alt_threshold_m = 2.5
          step_info_inputs.airborne_alt_threshold_m = 5.0
          step_info_inputs.has_runway_frame = True
          step_info_inputs.runway_frame.valid = True
          step_info_inputs.runway_frame.cross_m = 321.0
          step_info_inputs.runway_frame.along_m = 654.0
          step_info_inputs.runway_frame.length_m = 2000.0
          step_info_inputs.runway_frame.width_m = 50.0
          step_info_inputs.runway_width_margin_m = 2.0
          step_info_inputs.runway_length_margin_m = 0.0
          step_info = ef_py.compute_step_info_runtime(step_info_inputs)
          result.step_infos = [step_info]
          result.step_info_valid_flags = [True]
          result.controller_state_changed_flags = [bool(step_result.structural_state_changed)]
          return result

        vec_env._step_execution_episode_controller_mainline_requests = _wrapped
        original_build_loader_step_info = vec_env_module._build_loader_step_info

        def _unexpected_build_loader_step_info(*_args, **_kwargs):
          raise AssertionError("mainline full step info should reuse facade step_info_fields")

        vec_env_module._build_loader_step_info = _unexpected_build_loader_step_info
        try:
          _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          vec_env_module._build_loader_step_info = original_build_loader_step_info

        self.assertFalse(bool(dones[0]))
        self.assertEqual(float(infos[0]["on_runway"]), 0.0)
        self.assertEqual(float(infos[0]["gear_collapsed"]), 1.0)
        self.assertAlmostEqual(float(infos[0]["gear_stress"]), 9.5, places=6)
        self.assertEqual(float(infos[0]["on_ground"]), 1.0)
        self.assertEqual(float(infos[0]["on_runway_geom"]), 0.0)
        self.assertAlmostEqual(float(infos[0]["runway_cross_m"]), 321.0, places=6)
        self.assertAlmostEqual(float(infos[0]["runway_along_m"]), 654.0, places=6)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_filters_airfield_step_info_for_naval_profile(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_naval_route_transition_scenario.json"
      scenario = _inline_vec_env_route_transition_scenario()
      scenario["tasking_profile"] = "naval"
      scenario["mission_command"]["tasking_profile"] = "naval"
      scenario["task_order"] = {
        "tasking_profile": "naval",
        "service_profile": "Navy",
        "task_name": "TASK_SCREEN",
      }
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
        step_info_mode="full",
        action_mode="naval_station3",
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        original = vec_env._step_execution_episode_controller_mainline_requests

        def _wrapped(requests):
          result = original(requests)
          step_result = result.step_results[0]
          result.rewards = [float(getattr(step_result, "reward_total", 0.0))]
          result.terminated = [bool(step_result.terminated)]
          result.truncated = [bool(step_result.truncated)]
          result.status_vectors = [[1.0, 2.0, 3.0, 4.0]]
          result.termination_reasons = ["facade_contract_reason"]
          result.reward_breakdown_jsons = ['{"facade_bonus": 1.0, "total": 1.0}']
          step_info_inputs = ef_py.StepInfoInputs()
          step_info_inputs.on_runway = False
          step_info_inputs.gear_collapsed = True
          step_info_inputs.gear_stress = 9.5
          step_info_inputs.alt_agl_m = 0.0
          step_info_inputs.has_runway_frame = True
          step_info_inputs.runway_frame.valid = True
          step_info_inputs.runway_frame.cross_m = 321.0
          step_info_inputs.runway_frame.along_m = 654.0
          step_info_inputs.runway_frame.length_m = 2000.0
          step_info_inputs.runway_frame.width_m = 50.0
          result.step_infos = [ef_py.compute_step_info_runtime(step_info_inputs)]
          result.step_info_valid_flags = [True]
          result.controller_state_changed_flags = [bool(step_result.structural_state_changed)]
          return result

        vec_env._step_execution_episode_controller_mainline_requests = _wrapped
        _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 3), dtype=np.float32))

        self.assertFalse(bool(dones[0]))
        for key in (
          "on_runway",
          "gear_collapsed",
          "gear_stress",
          "on_runway_geom",
          "runway_cross_m",
          "runway_along_m",
        ):
          self.assertNotIn(key, infos[0])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_disables_execution_device_export_for_naval_profile(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_naval_route_transition_scenario.json"
      scenario = _inline_vec_env_route_transition_scenario()
      scenario["tasking_profile"] = "naval"
      scenario["mission_command"]["tasking_profile"] = "naval"
      scenario["task_order"] = {
        "tasking_profile": "naval",
        "service_profile": "Navy",
        "task_name": "TASK_SCREEN",
      }
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode="naval_station3",
        batch_observation_backend="compiled",
        policy_observation_torch_bridge=True,
      )
      observed_allow_device_export: list[bool] = []
      original_compute_batch = vec_env_module.compute_execution_observation_batch

      def _wrapped_compute_execution_observation_batch(**kwargs):
        observed_allow_device_export.append(bool(kwargs.get("allow_device_export")))
        return original_compute_batch(**kwargs)

      try:
        vec_env_module.compute_execution_observation_batch = _wrapped_compute_execution_observation_batch # type: ignore[assignment]
        vec_env.seed(123)
        _ = vec_env.reset()
        self.assertTrue(observed_allow_device_export)
        self.assertTrue(all(not value for value in observed_allow_device_export))
        self.assertIsNone(vec_env._policy_execution_device_view)
      finally:
        vec_env_module.compute_execution_observation_batch = original_compute_batch # type: ignore[assignment]
        vec_env.close()

  def test_world_batch_vec_env_mainline_request_build_skips_unused_episode_state(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        loader = vec_env.envs[0].loader
        original_build_execution_episode_state = loader.build_execution_episode_state
        original_mainline_requests = vec_env._step_execution_episode_controller_mainline_requests
        observed: dict[str, int] = {}

        def _unexpected_build_execution_episode_state():
          raise AssertionError("mainline request build should skip unused episode_state materialization")

        def _wrapped_mainline_requests(requests):
          request_list = list(requests)
          observed["request_count"] = len(request_list)
          self.assertEqual(len(request_list), 1)
          self.assertFalse(bool(request_list[0].env_state.has_episode_state))
          return original_mainline_requests(request_list)

        loader.build_execution_episode_state = _unexpected_build_execution_episode_state
        vec_env._step_execution_episode_controller_mainline_requests = _wrapped_mainline_requests
        try:
          _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          loader.build_execution_episode_state = original_build_execution_episode_state
          vec_env._step_execution_episode_controller_mainline_requests = original_mainline_requests

        self.assertEqual(int(observed.get("request_count", 0)), 1)
        self.assertFalse(bool(dones[0]))
        self.assertIsInstance(infos[0], dict)
        self.assertTrue(np.isfinite(float(rewards[0])))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_steady_state_uses_light_runtime_field_sync(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 4
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        loader = vec_env.envs[0].loader
        original_apply_runtime_fields = loader.apply_execution_episode_runtime_fields
        observed: list[tuple[bool, bool]] = []

        def _wrapped_apply_runtime_fields(
          state,
          *,
          include_navigation_state=True,
          include_navigation_structure=True,
        ):
          observed.append((bool(include_navigation_state), bool(include_navigation_structure)))
          return original_apply_runtime_fields(
            state,
            include_navigation_state=include_navigation_state,
            include_navigation_structure=include_navigation_structure,
          )

        loader.apply_execution_episode_runtime_fields = _wrapped_apply_runtime_fields
        try:
          _obs, _rewards, dones, _infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          loader.apply_execution_episode_runtime_fields = original_apply_runtime_fields

        self.assertFalse(bool(dones[0]))
        self.assertEqual(observed, [(True, False)])
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_step_prefers_batch_step_observation_packet(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 4
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        original_step_execution_batch = vec_env._runtime_adapter.step_execution_batch
        original_read_observation_packet = vec_env._runtime_adapter.read_observation_packet
        observed: dict[str, object] = {}

        def _wrapped_read_observation_packet(refs, **kwargs):
          observed["read_observation_packet_calls"] = int(observed.get("read_observation_packet_calls", 0)) + 1
          packet = original_read_observation_packet(refs, **kwargs)
          if "pre_step_truth" not in observed:
            observed["pre_step_truth"] = packet.agent_observations[0]
            observed["pre_step_inst"] = packet.instrument_states[0]
          return packet

        def _wrapped_step_execution_batch(batch_request):
          observed["step_execution_batch_calls"] = int(observed.get("step_execution_batch_calls", 0)) + 1
          observed["step_request_count"] = len(list(getattr(batch_request, "step_requests", []) or []))
          observed["include_agent_observations"] = bool(
            getattr(batch_request, "include_agent_observations", False)
          )
          observed["include_instrument_states"] = bool(
            getattr(batch_request, "include_instrument_states", False)
          )
          observed["has_include_task_orders"] = hasattr(batch_request, "include_task_orders")
          observed["include_task_order_contracts"] = bool(
            getattr(batch_request, "include_task_order_contracts", False)
          )
          result = original_step_execution_batch(batch_request)
          ref = ef_py.WorldEntityRef()
          ref.world_index = 0
          ref.entity_id = int(vec_env.envs[0].agent_id)
          result.observation_packet = original_read_observation_packet(
            [ref],
            include_agent_observations=True,
            include_instrument_states=True,
          )
          observed["mainline_truth"] = result.observation_packet.agent_observations[0]
          observed["mainline_inst"] = result.observation_packet.instrument_states[0]
          return result

        vec_env._runtime_adapter.read_observation_packet = _wrapped_read_observation_packet # type: ignore[method-assign]
        vec_env._runtime_adapter.step_execution_batch = _wrapped_step_execution_batch # type: ignore[method-assign]
        try:
          _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          vec_env._runtime_adapter.read_observation_packet = original_read_observation_packet # type: ignore[method-assign]
          vec_env._runtime_adapter.step_execution_batch = original_step_execution_batch # type: ignore[method-assign]

        self.assertEqual(int(observed.get("step_execution_batch_calls", 0)), 1)
        self.assertEqual(int(observed.get("step_request_count", 0)), 1)
        self.assertTrue(bool(observed.get("include_agent_observations", False)))
        self.assertTrue(bool(observed.get("include_instrument_states", False)))
        self.assertFalse(bool(observed.get("has_include_task_orders", True)))
        self.assertFalse(bool(observed.get("include_task_order_contracts", False)))
        self.assertEqual(int(observed.get("read_observation_packet_calls", 0)), 1)
        self.assertIs(vec_env.envs[0].last_truth, observed.get("mainline_truth"))
        self.assertIs(vec_env.envs[0].last_inst, observed.get("mainline_inst"))
        self.assertIsNot(vec_env.envs[0].last_truth, observed.get("pre_step_truth"))
        self.assertIsNot(vec_env.envs[0].last_inst, observed.get("pre_step_inst"))
        self.assertFalse(bool(dones[0]))
        self.assertIsInstance(infos[0], dict)
        self.assertTrue(np.isfinite(float(rewards[0])))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_prefers_facade_execution_episode_state_export(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        original = vec_env._step_execution_episode_controller_mainline_requests
        observed: dict[str, Any] = {}

        def _wrapped(requests):
          result = original(requests)
          exported_state = result.execution_episode_states[0]
          observed["exported_step_count"] = int(exported_state.step_count)
          observed["compat_step_count"] = int(exported_state.step_count) + 100
          compat_state = _legacy_step_result_state_with_poisoned_report_fields(exported_state)
          compat_state.last_termination_reason = "compatibility_fallback_should_not_win"
          result.step_results[0].controller_state = compat_state
          return result

        vec_env._step_execution_episode_controller_mainline_requests = _wrapped
        try:
          _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          vec_env._step_execution_episode_controller_mainline_requests = original

        self.assertFalse(bool(dones[0]))
        exported_state = vec_env.export_execution_episode_state(0)
        loader_state = vec_env.envs[0].loader.build_execution_episode_state()
        self.assertTrue(
          _controller_runtime_state_matches_loader_state(exported_state, loader_state)
        )
        self.assertEqual(int(loader_state.step_count), int(observed["exported_step_count"]))
        self.assertEqual(int(exported_state.step_count), int(observed["exported_step_count"]))
        self.assertEqual(int(observed["compat_step_count"]), int(observed["exported_step_count"]) + 100)
        self.assertNotEqual(int(loader_state.step_count), int(observed["compat_step_count"]))
        self.assertNotEqual(
          str(infos[0].get("termination_reason")),
          "compatibility_fallback_should_not_win",
        )
      finally:
        vec_env.close()

  def test_world_batch_vec_env_mainline_prefers_facade_batch_fields_over_legacy_step_result(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        execution_episode_controller_mainline=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()

        original = vec_env._step_execution_episode_controller_mainline_requests
        original_apply_state = vec_env.envs[0].loader.apply_execution_episode_state
        original_apply_runtime_fields = vec_env.envs[0].loader.apply_execution_episode_runtime_fields
        observed: dict[str, Any] = {}

        def _wrapped_apply_state(state):
          observed["apply_state_calls"] = int(observed.get("apply_state_calls", 0)) + 1
          return original_apply_state(state)

        def _wrapped_apply_runtime_fields(state, **kwargs):
          observed["apply_runtime_fields_calls"] = int(
            observed.get("apply_runtime_fields_calls", 0)
          ) + 1
          return original_apply_runtime_fields(state, **kwargs)

        def _wrapped(requests):
          result = original(requests)
          step_result = result.step_results[0]
          step_result.reward_total = 91.25
          step_result.terminated = False
          step_result.truncated = True
          step_result.status0 = -1.0
          step_result.status1 = -2.0
          step_result.status2 = -3.0
          step_result.status3 = -4.0
          step_result.structural_state_changed = False
          step_result.controller_state = _legacy_step_result_state_with_poisoned_report_fields(
            result.execution_episode_states[0]
          )

          result.rewards = [-17.75]
          result.terminated = [True]
          result.truncated = [False]
          result.status_vectors = [[6.0, 7.0, 8.0, 9.0]]
          result.termination_reasons = ["facade_owned_reason"]
          result.reward_breakdown_jsons = [
            json.dumps(
              {"facade_total": -17.75, "total": -17.75},
              ensure_ascii=True,
              sort_keys=True,
            )
          ]
          result.controller_state_changed_flags = [True]
          return result

        vec_env.envs[0].loader.apply_execution_episode_state = _wrapped_apply_state
        vec_env.envs[0].loader.apply_execution_episode_runtime_fields = _wrapped_apply_runtime_fields
        vec_env._step_execution_episode_controller_mainline_requests = _wrapped
        try:
          _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          vec_env._step_execution_episode_controller_mainline_requests = original
          vec_env.envs[0].loader.apply_execution_episode_state = original_apply_state
          vec_env.envs[0].loader.apply_execution_episode_runtime_fields = original_apply_runtime_fields

        self.assertTrue(bool(dones[0]))
        self.assertAlmostEqual(float(rewards[0]), -17.75, places=6)
        self.assertFalse(bool(infos[0]["TimeLimit.truncated"]))
        self.assertTrue(
          np.allclose(
            np.asarray(infos[0]["mission_status"], dtype=np.float32),
            np.asarray([6.0, 7.0, 8.0, 9.0], dtype=np.float32),
            atol=1.0e-6,
          )
        )
        self.assertEqual(str(infos[0]["termination_reason"]), "facade_owned_reason")
        self.assertAlmostEqual(float(infos[0]["reward_terms"]["facade_total"]), -17.75, places=6)
        self.assertAlmostEqual(float(infos[0]["reward_terms"]["total"]), -17.75, places=6)
        self.assertNotIn("legacy_total", infos[0]["reward_terms"])
        self.assertEqual(int(observed.get("apply_state_calls", 0)), 1)
        self.assertEqual(int(observed.get("apply_runtime_fields_calls", 0)), 0)
      finally:
        vec_env.close()

  def test_world_batch_vec_env_reuses_cached_step_evaluation_for_reward_tail(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        execution_step_batch_prepare=True,
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        original_compute_full_step = vec_env.envs[0].loader.compute_full_step
        captured: dict[str, object] = {}

        def _wrapped_compute_full_step(*args, **kwargs):
          captured["step_evaluation"] = kwargs.get("step_evaluation")
          return original_compute_full_step(*args, **kwargs)

        vec_env.envs[0].loader.compute_full_step = _wrapped_compute_full_step
        _obs, _rewards, _dones, _infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

        self.assertIsInstance(captured.get("step_evaluation"), dict)
        self.assertIs(
          captured["step_evaluation"],
          vec_env.envs[0].loader._runtime_eval_cache.get("step_evaluation"),
        )
      finally:
        vec_env.close()

  def test_world_batch_vec_env_legacy_reward_and_info_eval_flow_through_named_compat_helpers(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
      )
      try:
        vec_env.seed(123)
        _ = vec_env.reset()
        original_compute = vec_env_module._compute_loader_step_outcome
        original_build = vec_env_module._build_loader_step_info
        observed: dict[str, Any] = {}

        def _wrapped_compute(loader, **kwargs):
          observed["compute_loader"] = loader
          return original_compute(loader, **kwargs)

        def _wrapped_build(loader, **kwargs):
          observed["build_loader"] = loader
          observed["build_entity_id"] = kwargs.get("entity_id")
          return original_build(loader, **kwargs)

        vec_env_module._compute_loader_step_outcome = _wrapped_compute
        vec_env_module._build_loader_step_info = _wrapped_build
        try:
          _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
        finally:
          vec_env_module._compute_loader_step_outcome = original_compute
          vec_env_module._build_loader_step_info = original_build

        self.assertIs(observed.get("compute_loader"), vec_env.envs[0].loader)
        self.assertIs(observed.get("build_loader"), vec_env.envs[0].loader)
        self.assertEqual(int(observed.get("build_entity_id", -1)), int(vec_env.envs[0].agent_id))
        self.assertTrue(np.isfinite(float(rewards[0])))
        self.assertIsInstance(infos[0], dict)
        self.assertEqual(bool(dones[0]), bool(infos[0]["terminated"] or infos[0]["truncated"]))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_matches_multi_timescale_action_wrapper(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 3
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      wrapper_kwargs = {
        "hold_steps": 4,
        "low_freq_indices": [4, 5, 6, 9, 12, 13, 14, 15, 16],
        "snap_binary_indices": [4, 9, 12, 13, 14, 15],
        "binary_hysteresis_indices": [4, 9, 12, 13, 14, 15],
        "binary_on_threshold": 0.75,
        "binary_off_threshold": 0.25,
        "binary_initial_values": {"4": 1.0, "9": 0.0, "12": 0.0, "13": 0.0, "14": 0.0, "15": 0.0},
        "center_deadband_indices": [5, 6, 7, 8],
        "center_deadband_center": 0.5,
        "center_deadband_half_width": 0.18,
        "scripted_baseline_mode": "stable_flight",
        "scripted_residual_scale": 0.0,
        "action_rate_penalty_coef": 0.0002,
      }
      direct_env = MultiTimescaleActionWrapper(
        UniversalEnv(
          scenario_path=scenario_path,
          include_visual=False,
          include_proprio=True,
          action_mode="full",
          mission_obs_mode="basic",
          runtime_compatibility_enabled=True,
        ),
        **wrapper_kwargs,
      )
      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_wrapper_kwargs=wrapper_kwargs,
      )
      try:
        direct_obs, _direct_info = direct_env.reset(seed=123)
        vec_env.seed(123)
        vec_obs = vec_env.reset()
        for key in ("contacts", "rwr", "mission", "proprio"):
          self.assertTrue(
            np.allclose(np.asarray(direct_obs[key]), np.asarray(vec_obs[key][0]), atol=1.0e-5),
            msg=f"reset mismatch for key={key}",
          )

        action = np.full((17,), 0.9, dtype=np.float32)
        direct_obs_1, direct_reward_1, direct_done_1, direct_trunc_1, direct_info_1 = direct_env.step(action)
        vec_obs_1, vec_rew_1, vec_done_1, vec_info_1 = vec_env.step(action.reshape(1, -1))
        self.assertFalse(bool(direct_done_1 or direct_trunc_1))
        self.assertFalse(bool(vec_done_1[0]))
        for key in ("contacts", "rwr", "mission", "proprio"):
          self.assertTrue(
            np.allclose(np.asarray(direct_obs_1[key]), np.asarray(vec_obs_1[key][0]), atol=1.0e-5),
            msg=f"step1 mismatch for key={key}",
          )
        self.assertAlmostEqual(float(direct_reward_1), float(vec_rew_1[0]), places=5)
        self.assertTrue(
          np.allclose(
            np.asarray(direct_info_1["effective_action"], dtype=np.float32),
            np.asarray(vec_info_1[0]["effective_action"], dtype=np.float32),
            atol=1.0e-6,
          )
        )

        direct_obs_2, direct_reward_2, direct_done_2, direct_trunc_2, direct_info_2 = direct_env.step(action)
        vec_obs_2, vec_rew_2, vec_done_2, vec_info_2 = vec_env.step(action.reshape(1, -1))
        self.assertTrue(
          np.allclose(
            np.asarray(direct_info_2["effective_action"], dtype=np.float32),
            np.asarray(vec_info_2[0]["effective_action"], dtype=np.float32),
            atol=1.0e-6,
          )
        )
      finally:
        direct_env.close()
        vec_env.close()

  def test_world_batch_vec_env_cuda_bridge_uses_device_rollout_buffer(self) -> None:
    if not torch.cuda.is_available():
      self.skipTest("CUDA is not available")

    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        batch_observation_backend="gpu_host",
        policy_observation_torch_bridge=True,
      )
      try:
        model = AdaptiveKLPPO(
          "MultiInputPolicy",
          vec_env,
          n_steps=2,
          batch_size=4,
          n_epochs=1,
          learning_rate=3.0e-4,
          gamma=0.99,
          gae_lambda=0.95,
          ent_coef=0.0,
          vf_coef=0.5,
          max_grad_norm=0.5,
          device="cuda",
          verbose=0,
        )
        self.assertIsInstance(model.rollout_buffer, DeviceDictRolloutBuffer)
        model.learn(total_timesteps=4)
        self.assertTrue(torch.is_tensor(model.rollout_buffer.observations["instruments"]))
        self.assertEqual(model.rollout_buffer.observations["instruments"].device.type, "cuda")
      finally:
        vec_env.close()

  def test_world_batch_vec_env_observation_return_mode_view_shares_memory(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
        observation_return_mode="view",
      )
      try:
        obs = vec_env.reset()
        self.assertTrue(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
        self.assertTrue(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

        obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertTrue(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
        self.assertTrue(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

        _obs, _rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertTrue(np.all(dones == np.asarray([True, True])))
        self.assertFalse(np.shares_memory(infos[0]["terminal_observation"]["instruments"], vec_env.buf_obs["instruments"][0]))
        self.assertFalse(np.shares_memory(infos[0]["terminal_observation"]["proprio"], vec_env.buf_obs["proprio"][0]))
      finally:
        vec_env.close()

  def test_world_batch_vec_env_observation_return_mode_copy_detaches_memory(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
      )
      try:
        obs = vec_env.reset()
        self.assertFalse(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
        self.assertFalse(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

        obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertFalse(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
        self.assertFalse(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))
      finally:
        vec_env.close()


class VecEnvAdapterTests(unittest.TestCase):
  def test_returns_shared_observation_views(self):
    vec_env = SharedMemorySubprocVecEnv(
      [lambda env_id=i: CounterDictEnv(env_id) for i in range(2)],
      start_method="forkserver",
    )
    try:
      obs = vec_env.reset()
      self.assertEqual(obs["vec"].shape, (2, 3))
      self.assertEqual(obs["mat"].shape, (2, 2, 2))
      self.assertTrue(np.shares_memory(obs["vec"], vec_env.buf_obs["vec"]))
      self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))

      obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
      self.assertTrue(np.allclose(rewards, np.asarray([1.0, 1.0], dtype=np.float32)))
      self.assertTrue(np.all(dones == np.asarray([False, False])))
      self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([1.0, 1.0], dtype=np.float32)))
      self.assertEqual(infos[0]["count"], 1)

      obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
      self.assertTrue(np.all(dones == np.asarray([True, True])))
      self.assertTrue(np.allclose(rewards, np.asarray([2.0, 2.0], dtype=np.float32)))
      self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))
      self.assertEqual(infos[0]["terminal_observation"]["vec"][1], 2.0)
      self.assertEqual(infos[1]["terminal_observation"]["vec"][1], 2.0)
    finally:
      vec_env.close()

  def test_world_batch_vec_env_reports_timing_breakdown(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_data = _inline_vec_env_scenario()
      scenario_data["meta"]["max_steps"] = 2
      scenario_path = f"{tmpdir}/inline_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, ensure_ascii=True)

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        collect_step_timing=True,
      )
      try:
        _ = vec_env.reset()
        self.assertIn("timing", vec_env.reset_infos[0])
        self.assertTrue(
          "layout_build_ms" in vec_env.reset_infos[0]["timing"]
          or "batch_setup_ms" in vec_env.reset_infos[0]["timing"]
        )
        self.assertIn("total_ms", vec_env.reset_infos[0]["timing"])

        _obs, _rewards, _dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        self.assertIn("timing", infos[0])
        self.assertIn("batch_step_ms", infos[0]["timing"])
        self.assertIn("command_sync_ms", infos[0]["timing"])
        self.assertIn("total_ms", infos[0]["timing"])
      finally:
        vec_env.close()


if __name__ == "__main__":
  unittest.main()
