from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.shared_memory_vec_env import SharedMemorySubprocVecEnv  # noqa: E402
from python.rl.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402

try:
    from tests.support._leader_env_runtime_test_support import CounterDictEnv  # noqa: E402
except ModuleNotFoundError:
    from _leader_env_runtime_test_support import CounterDictEnv  # type: ignore # noqa: E402


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


class WorldBatchVecEnvTests(unittest.TestCase):
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
                self.assertEqual(int(vec_env.batch_runtime.worker_threads()), 1)
                self.assertEqual(int(vec_env.batch_runtime.effective_worker_threads()), 1)
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
                execution_step_runtime_mode="legacy",
            )
            try:
                for handle in vec_env.envs:
                    self.assertEqual(handle.loader.execution_step_runtime_mode, "legacy")
                    self.assertFalse(bool(handle.loader.use_compiled_execution_step_runtime))
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
