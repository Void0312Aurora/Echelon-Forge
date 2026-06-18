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

from gym_envs.universal_env_parts import NAVAL_STATION3_ACTION_FAMILY # noqa: E402
from gym_envs.scenario_loader.execution_runtime.mainline import ( # noqa: E402
  _apply_combat_terminal_override,
)
from python.rl.runtime.world_batch import command_chain_cache # noqa: E402
from python.rl.runtime.world_batch.command_chain_cache import ( # noqa: E402
  project_world_leader_intent_maintained_assignment,
  project_world_mission_command_maintained_assignment,
  project_world_pilot_report_maintained_assignment,
  project_world_task_order_maintained_assignment,
)
import python.rl.runtime.world_batch.adapter as world_batch_adapter_module # noqa: E402
import python.rl.runtime.world_batch_vec_env as vec_env_module # noqa: E402
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


class WorldBatchVecEnvAdapterSurfaceTests(unittest.TestCase):
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
        self.assertFalse(hasattr(vec_env._runtime_adapter, "world_raw_quarantine"))
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

  def test_combat_loss_terminal_override_does_not_stack_crash_penalty(self) -> None:
    class FakeLoader:
      agent_id = 1
      primary_target_id = 2
      _compiled_meta_cfg = {"combat_loss_penalty": -1500.0}

      def _add_breakdown_term(self, rb, name, value):
        rb[str(name)] = float(rb.get(str(name), 0.0)) + float(value)

    class FakeSim:
      def is_unit_active(self, entity_id):
        return int(entity_id) == 2

    reward, terminated, truncated, status, reward_terms, reason = (
      _apply_combat_terminal_override(
        FakeLoader(),
        FakeSim(),
        truth=object(),
        reward=-1000.0,
        terminated=True,
        truncated=False,
        status=[0.0, 0.0, 0.0, -1.0],
        rb={"crash_penalty": -1000.0, "total": -1000.0},
      )
    )

    self.assertTrue(terminated)
    self.assertFalse(truncated)
    self.assertEqual(reason, "combat_loss")
    self.assertEqual(status[3], -1.0)
    self.assertEqual(float(reward), -1500.0)
    self.assertEqual(float(reward_terms.get("combat_loss_penalty", 0.0)), -1500.0)
    self.assertNotIn("crash_penalty", reward_terms)

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
            )

        with self.subTest(flight_shaping_backend=mode_alias):
          with self.assertRaisesRegex(ValueError, "Unknown flight_shaping_backend"):
            WorldBatchVecEnv(
              scenario_path=scenario_path,
              n_envs=1,
              include_visual=False,
              include_proprio=False,
              flight_shaping_backend=mode_alias,
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



if __name__ == "__main__":
  unittest.main()
