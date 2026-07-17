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


class WorldBatchVecEnvExecutionAndObservationTests(unittest.TestCase):
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

  def test_world_batch_vec_env_applies_multi_timescale_action_controller(self) -> None:
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
      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_wrapper_kwargs=wrapper_kwargs,
      )
      try:
        vec_env.seed(123)
        vec_obs = vec_env.reset()
        for key in ("contacts", "rwr", "mission", "proprio"):
          self.assertEqual(np.asarray(vec_obs[key][0]).shape, tuple(vec_env.observation_space[key].shape))

        first_action = np.full((17,), 0.9, dtype=np.float32)
        vec_obs_1, vec_rew_1, vec_done_1, vec_info_1 = vec_env.step(first_action.reshape(1, -1))
        self.assertFalse(bool(vec_done_1[0]))
        for key in ("contacts", "rwr", "mission", "proprio"):
          self.assertEqual(np.asarray(vec_obs_1[key][0]).shape, tuple(vec_env.observation_space[key].shape))
        self.assertTrue(np.isfinite(float(vec_rew_1[0])))
        first_effective = np.asarray(vec_info_1[0]["effective_action"], dtype=np.float32)
        self.assertEqual(first_effective.shape, (17,))
        self.assertEqual(float(first_effective[4]), 1.0)
        self.assertEqual(float(first_effective[9]), 1.0)

        second_action = np.full((17,), 0.1, dtype=np.float32)
        _vec_obs_2, vec_rew_2, _vec_done_2, vec_info_2 = vec_env.step(second_action.reshape(1, -1))
        second_effective = np.asarray(vec_info_2[0]["effective_action"], dtype=np.float32)
        self.assertTrue(np.isfinite(float(vec_rew_2[0])))
        held_indices = np.asarray(wrapper_kwargs["low_freq_indices"], dtype=np.int64)
        free_indices = np.asarray([0, 1, 2, 3, 7, 8, 10, 11], dtype=np.int64)
        self.assertTrue(np.allclose(second_effective[held_indices], first_effective[held_indices], atol=1.0e-6))
        self.assertTrue(np.allclose(second_effective[free_indices], second_action[free_indices], atol=1.0e-6))
      finally:
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
  def test_shared_memory_vec_env_rejects_action_batch_size_mismatch(self) -> None:
    vec_env = SharedMemorySubprocVecEnv(
      [lambda env_id=i: CounterDictEnv(env_id) for i in range(2)],
      start_method="forkserver",
    )
    try:
      vec_env.reset()
      for action_count in (1, 3):
        with self.subTest(action_count=action_count):
          with self.assertRaisesRegex(ValueError, "action batch size mismatch"):
            vec_env.step_async(np.zeros((action_count, 1), dtype=np.float32))
          self.assertFalse(vec_env.waiting)
    finally:
      vec_env.close()

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
