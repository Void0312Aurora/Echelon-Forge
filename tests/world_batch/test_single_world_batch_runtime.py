from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

import python.rl.runtime.leader_world_batch_runtime as leader_runtime_module # noqa: E402
import python.rl.runtime.single_world_batch_runtime as single_runtime_module # noqa: E402
from _world_model_train_impl.runtime_env import build_world_model_execution_env # noqa: E402
from evaluate import _build_evaluation_env # noqa: E402
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec # noqa: E402
from python.rl.runtime.single_world_batch_runtime import ( # noqa: E402
  SingleWorldBatchExecutionRuntimeHandle,
  build_single_world_batch_execution_runtime,
)


def _inline_single_world_scenario() -> dict:
  return {
    "scenario_name": "wp16_single_world_runtime_window_inline",
    "meta": {
      "max_steps": 2,
    },
    "environment": {
      "time_step": 0.05,
      "terrain_type": "legacy",
      "wind": {
        "speed_mps": 2.0,
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


class SingleWorldBatchRuntimeTests(unittest.TestCase):
  def test_maintained_evaluation_and_world_model_entry_envs_smoke(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      factories = {
        "evaluate": lambda: _build_evaluation_env(
          scenario_path,
          {
            "include_visual": False,
            "include_proprio": False,
            "action_mode": "full",
          },
          worker_threads=1,
        ),
        "world_model": lambda: build_world_model_execution_env(
          scenario_path=scenario_path,
          include_visual=False,
          include_proprio=False,
          action_mode="full",
        ),
      }

      for entry_name, factory in factories.items():
        with self.subTest(entry=entry_name):
          runtime = factory()
          try:
            self.assertIsInstance(runtime, SingleWorldBatchExecutionRuntimeHandle)
            obs, _info = runtime.reset(seed=17)
            self.assertIs(runtime.loader, runtime.unwrapped.loader)
            self.assertIs(runtime.sim, runtime.unwrapped.sim)
            self.assertEqual(runtime.agent_id, runtime.unwrapped.agent_id)
            self.assertEqual(runtime.steps, 0)
            self.assertGreater(runtime.max_steps, 0)
            self.assertGreater(runtime.get_time_step(), 0.0)
            self.assertIn("instruments", obs)
            _obs, reward, _terminated, _truncated, info = runtime.step(
              np.zeros((17,), dtype=np.float32)
            )
            self.assertTrue(np.isfinite(float(reward)))
            self.assertIn("runtime_window_evidence", info)
          finally:
            runtime.close()

  def test_multi_timescale_evaluation_env_is_sb3_dummy_vec_compatible(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      wrapper_class, wrapper_kwargs = get_action_wrapper_spec({
        "wrappers": {
          "multi_timescale_action": {
            "enabled": True,
            "hold_steps": 2,
          },
        },
      })
      self.assertIs(wrapper_class, MultiTimescaleActionWrapper)

      vec_env = DummyVecEnv([
        lambda: _build_evaluation_env(
          scenario_path,
          {
            "include_visual": False,
            "include_proprio": False,
            "action_mode": "full",
          },
          wrapper_class=wrapper_class,
          wrapper_kwargs=wrapper_kwargs,
          worker_threads=1,
        ),
      ])
      try:
        self.assertIsInstance(vec_env.envs[0], MultiTimescaleActionWrapper)
        observation = vec_env.reset()
        self.assertIsNotNone(observation)
        action = np.zeros((1, *vec_env.action_space.shape), dtype=np.float32)
        _obs, rewards, dones, infos = vec_env.step(action)
        self.assertEqual(rewards.shape, (1,))
        self.assertEqual(dones.shape, (1,))
        self.assertEqual(len(infos), 1)
      finally:
        vec_env.close()

  def test_single_world_runtime_step_uses_runtime_window_evidence_when_facade_api_available(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      runtime = build_single_world_batch_execution_runtime(
        scenario_path=scenario_path,
        env_settings={
          "include_visual": False,
          "include_proprio": False,
        },
      )
      try:
        _obs, _reset_info = runtime.reset(seed=7)
        action = np.zeros((17,), dtype=np.float32)
        _next_obs, _reward, _terminated, _truncated, info = runtime.step(action)

        evidence = runtime.last_runtime_window_evidence
        self.assertIsNotNone(evidence)
        assert evidence is not None
        self.assertFalse(bool(evidence.uses_compat_fallback))
        self.assertEqual(
          [str(getattr(record, "barrier_id", "") or "") for record in evidence.barrier_trace],
          ["input_injection", "window_commit", "export"],
        )
        self.assertEqual(
          [str(getattr(record, "node_id", "") or "") for record in evidence.executed_nodes],
          [
            "fire_control_launch.v1",
            "effects_damage.v1",
            "observation_export.v1",
          ],
        )
        self.assertAlmostEqual(
          float(getattr(evidence.window_result.cadence_config, "window_duration_s", 0.0)),
          0.1,
          places=6,
        )
        cadence_domains = [
          str(getattr(record, "domain", "") or "")
          for record in list(getattr(evidence.window_result, "cadence_trace", []))
        ]
        self.assertEqual(cadence_domains.count("policy"), 1)
        self.assertEqual(cadence_domains.count("control"), 2)
        self.assertEqual(cadence_domains.count("physics"), 6)
        self.assertEqual(cadence_domains.count("export"), 1)
        self.assertTrue(
          any(
            bool(getattr(record, "held", False))
            or str(getattr(record, "decision", "") or "") in {"held", "expired"}
            for record in list(getattr(evidence.window_result, "cadence_trace", []))
            if str(getattr(record, "domain", "") or "") == "control"
          )
        )
        self.assertEqual(str(evidence.observation_packet.barrier_id), "export")
        self.assertEqual(
          str(evidence.observation_packet.provenance.source_label),
          "facade_observation_packet",
        )
        self.assertEqual(str(evidence.engagement_packet.barrier_id), "export")
        self.assertEqual(
          str(evidence.engagement_packet.packet_provenance.source_label),
          "track_state_packet",
        )
        self.assertEqual(
          str(evidence.engagement_packet.diagnostics_provenance.source_label),
          "world_truth_diagnostics",
        )
        self.assertIn("runtime_window_evidence", info)
        self.assertEqual(
          info["runtime_window_evidence"]["barrier_ids"],
          ["input_injection", "window_commit", "export"],
        )
        self.assertEqual(
          info["runtime_window_evidence"]["observation_provenance"],
          "facade_observation_packet",
        )
        self.assertEqual(
          info["runtime_window_evidence"]["engagement_provenance"],
          "track_state_packet",
        )
        self.assertEqual(
          info["runtime_window_evidence"]["diagnostics_provenance"],
          "world_truth_diagnostics",
        )
        self.assertEqual(
          info["runtime_window_evidence"]["cadence_reason"],
          "selected_slice_cadence_trace_runtime_window",
        )
      finally:
        runtime.close()

  def test_single_world_air_combat_hybrid_uses_event_action_contract(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario = _inline_single_world_scenario()
      scenario["scenario_name"] = "air_combat_single_world_event_contract"
      scenario["domain"] = "air_combat"
      scenario_path = f"{tmpdir}/single_world_air_combat_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=True)

      runtime = build_single_world_batch_execution_runtime(
        scenario_path=scenario_path,
        env_settings={
          "include_visual": False,
          "include_proprio": False,
          "action_mode": "air_combat_hybrid_v1",
        },
      )
      calls: list[str] = []
      original_gate = single_runtime_module.apply_air_combat_event_action_gate
      original_finalize = single_runtime_module.finalize_air_combat_event_action_info
      original_add_info = single_runtime_module.add_air_combat_event_action_info

      def _tracked_gate(*args, **kwargs):
        calls.append("gate")
        return original_gate(*args, **kwargs)

      def _tracked_finalize(*args, **kwargs):
        calls.append("finalize")
        return original_finalize(*args, **kwargs)

      def _tracked_add_info(*args, **kwargs):
        calls.append("info")
        return original_add_info(*args, **kwargs)

      single_runtime_module.apply_air_combat_event_action_gate = _tracked_gate
      single_runtime_module.finalize_air_combat_event_action_info = _tracked_finalize
      single_runtime_module.add_air_combat_event_action_info = _tracked_add_info
      try:
        runtime.reset(seed=19)
        action = np.zeros(runtime.action_space.shape, dtype=np.float32)
        runtime.step(action)
        self.assertEqual(calls, ["gate", "finalize", "info"])
        self.assertEqual(runtime.loader._last_action_mode, "air_combat_hybrid_v1")
      finally:
        single_runtime_module.apply_air_combat_event_action_gate = original_gate
        single_runtime_module.finalize_air_combat_event_action_info = original_finalize
        single_runtime_module.add_air_combat_event_action_info = original_add_info
        runtime.close()

  def test_single_world_runtime_requires_runtime_window_api(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      runtime = build_single_world_batch_execution_runtime(
        scenario_path=scenario_path,
        env_settings={
          "include_visual": False,
          "include_proprio": False,
        },
      )
      try:
        original_supports = runtime.access.supports_runtime_window_api
        runtime.access.supports_runtime_window_api = lambda: False # type: ignore[method-assign]
        _obs, _reset_info = runtime.reset(seed=9)
        action = np.zeros((17,), dtype=np.float32)
        with self.assertRaisesRegex(RuntimeError, "run_window\\(\\) is required"):
          runtime.step(action)
        runtime.access.supports_runtime_window_api = original_supports # type: ignore[method-assign]
      finally:
        runtime.close()

  def test_single_world_runtime_uses_named_compat_reward_and_info_helpers(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      runtime = build_single_world_batch_execution_runtime(
        scenario_path=scenario_path,
        env_settings={
          "include_visual": False,
          "include_proprio": False,
        },
      )
      try:
        _obs, _reset_info = runtime.reset(seed=11)
        original_compute = single_runtime_module.compute_loader_step_outcome
        original_build = single_runtime_module.build_loader_step_info
        observed: dict[str, object] = {}

        def _wrapped_compute(loader, **kwargs):
          observed["compute_loader"] = loader
          return original_compute(loader, **kwargs)

        def _wrapped_build(loader, **kwargs):
          observed["build_loader"] = loader
          observed["entity_id"] = kwargs.get("entity_id")
          return original_build(loader, **kwargs)

        single_runtime_module.compute_loader_step_outcome = _wrapped_compute
        single_runtime_module.build_loader_step_info = _wrapped_build
        try:
          _next_obs, reward, _terminated, _truncated, info = runtime.step(np.zeros((17,), dtype=np.float32))
        finally:
          single_runtime_module.compute_loader_step_outcome = original_compute
          single_runtime_module.build_loader_step_info = original_build

        self.assertIs(observed.get("compute_loader"), runtime.unwrapped.loader)
        self.assertIs(observed.get("build_loader"), runtime.unwrapped.loader)
        self.assertEqual(int(observed.get("entity_id", -1)), int(runtime.unwrapped.agent_id))
        self.assertTrue(np.isfinite(float(reward)))
        self.assertIn("runtime_window_evidence", info)
      finally:
        runtime.close()

  def test_leader_group_uses_named_compat_reward_and_info_helpers(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
      from python.rl.runtime.leader_world_batch_runtime import ( # noqa: E402
        LeaderWorldBatchExecutionRuntimeGroup,
      )

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(5)
        _ = vec_env.reset()
        group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
        original_compute = leader_runtime_module.compute_loader_step_outcome
        original_build = leader_runtime_module.build_loader_step_info
        observed: dict[str, object] = {}

        def _wrapped_compute(loader, **kwargs):
          observed["compute_loader"] = loader
          return original_compute(loader, **kwargs)

        def _wrapped_build(loader, **kwargs):
          observed["build_loader"] = loader
          observed["entity_id"] = kwargs.get("entity_id")
          return original_build(loader, **kwargs)

        leader_runtime_module.compute_loader_step_outcome = _wrapped_compute
        leader_runtime_module.build_loader_step_info = _wrapped_build
        try:
          results = group.step_indices([0], [np.zeros((17,), dtype=np.float32)])
        finally:
          leader_runtime_module.compute_loader_step_outcome = original_compute
          leader_runtime_module.build_loader_step_info = original_build

        self.assertEqual(len(results), 1)
        self.assertIs(observed.get("compute_loader"), vec_env.envs[0].loader)
        self.assertIs(observed.get("build_loader"), vec_env.envs[0].loader)
        self.assertEqual(int(observed.get("entity_id", -1)), int(vec_env.envs[0].agent_id))
        self.assertTrue(np.isfinite(float(results[0][1])))
      finally:
        vec_env.close()

  def test_leader_group_step_uses_runtime_window_evidence_when_facade_api_available(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
      from python.rl.runtime.leader_world_batch_runtime import ( # noqa: E402
        LeaderWorldBatchExecutionRuntimeGroup,
      )

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(13)
        _ = vec_env.reset()
        group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
        results = group.step_indices([0], [np.zeros((17,), dtype=np.float32)])

        self.assertEqual(len(results), 1)
        _obs, _reward, _terminated, _truncated, info = results[0]
        evidence = group.last_runtime_window_evidence
        self.assertIsNotNone(evidence)
        assert evidence is not None
        self.assertFalse(bool(evidence.uses_compat_fallback))
        self.assertIn("runtime_window_evidence", info)
        self.assertEqual(
          info["runtime_window_evidence"]["cadence_reason"],
          "selected_slice_cadence_trace_runtime_window",
        )
        self.assertFalse(bool(info["runtime_window_evidence"]["uses_compat_fallback"]))
        self.assertEqual(
          info["runtime_window_evidence"]["barrier_ids"],
          ["input_injection", "window_commit", "export"],
        )
      finally:
        vec_env.close()

  def test_leader_group_requires_runtime_window_api(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
      from python.rl.runtime.leader_world_batch_runtime import ( # noqa: E402
        LeaderWorldBatchExecutionRuntimeGroup,
      )

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(17)
        _ = vec_env.reset()
        group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
        original_supports = group.access.supports_runtime_window_api
        group.access.supports_runtime_window_api = lambda: False # type: ignore[method-assign]
        try:
          with self.assertRaisesRegex(RuntimeError, "run_window\\(\\) is required"):
            group.step_indices([0], [np.zeros((17,), dtype=np.float32)])
        finally:
          group.access.supports_runtime_window_api = original_supports # type: ignore[method-assign]
      finally:
        vec_env.close()

  def test_leader_group_rejects_removed_compatibility_fallback_even_when_opted_in(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
      from python.rl.runtime.leader_world_batch_runtime import ( # noqa: E402
        LeaderWorldBatchExecutionRuntimeGroup,
      )

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        vec_env.seed(19)
        _ = vec_env.reset()
        group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
        original_supports = group.access.supports_runtime_window_api
        group.access.supports_runtime_window_api = lambda: False # type: ignore[method-assign]
        try:
          with self.assertRaisesRegex(RuntimeError, "run_window\\(\\) is required"):
            group.step_indices([0], [np.zeros((17,), dtype=np.float32)])
        finally:
          group.access.supports_runtime_window_api = original_supports # type: ignore[method-assign]
      finally:
        vec_env.close()

  def test_world_batch_vec_env_and_leader_group_expose_window_evidence_accessors_without_forcing_migration(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = f"{tmpdir}/single_world_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_inline_single_world_scenario(), f, ensure_ascii=True)

      from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402
      from python.rl.runtime.leader_world_batch_runtime import ( # noqa: E402
        LeaderWorldBatchExecutionRuntimeGroup,
      )

      vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
      )
      try:
        self.assertTrue(hasattr(vec_env, "last_runtime_window_evidence"))
        self.assertIsNone(vec_env.last_runtime_window_evidence)

        group = LeaderWorldBatchExecutionRuntimeGroup(vec_env)
        self.assertTrue(hasattr(group, "last_runtime_window_evidence"))
        self.assertIsNone(group.last_runtime_window_evidence)
      finally:
        vec_env.close()


if __name__ == "__main__":
  unittest.main()
