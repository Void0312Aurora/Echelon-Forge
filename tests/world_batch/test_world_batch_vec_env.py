from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import torch  # noqa: E402,F401

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.device_dict_rollout_buffer import DeviceDictRolloutBuffer  # noqa: E402
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402
from python.rl.shared_memory_vec_env import SharedMemorySubprocVecEnv  # noqa: E402
from python.rl.wrappers import MultiTimescaleActionWrapper  # noqa: E402
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

    def test_world_batch_vec_env_compiled_batch_observation_matches_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                batch_observation_backend="legacy",
            )
            compiled_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                batch_observation_backend="compiled",
            )
            try:
                legacy_env.seed(123)
                compiled_env.seed(123)
                legacy_obs = legacy_env.reset()
                compiled_obs = compiled_env.reset()
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(legacy_obs[key], compiled_obs[key], atol=1.0e-6),
                        msg=f"reset mismatch for key={key}",
                    )

                actions = np.zeros((2, 17), dtype=np.float32)
                legacy_obs, legacy_rewards, legacy_dones, _legacy_infos = legacy_env.step(actions)
                compiled_obs, compiled_rewards, compiled_dones, _compiled_infos = compiled_env.step(actions)
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(legacy_obs[key], compiled_obs[key], atol=1.0e-6),
                        msg=f"step mismatch for key={key}",
                    )
                self.assertTrue(np.allclose(legacy_rewards, compiled_rewards, atol=1.0e-6))
                self.assertTrue(np.array_equal(legacy_dones, compiled_dones))
            finally:
                legacy_env.close()
                compiled_env.close()

    def test_world_batch_vec_env_compiled_batch_visual_matches_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=True,
                include_proprio=False,
                visual_downsample=2,
                visual_update_interval=1,
                batch_visual_backend="legacy",
            )
            compiled_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=True,
                include_proprio=False,
                visual_downsample=2,
                visual_update_interval=1,
                batch_visual_backend="compiled",
            )
            try:
                legacy_env.seed(123)
                compiled_env.seed(123)
                legacy_obs = legacy_env.reset()
                compiled_obs = compiled_env.reset()
                self.assertTrue(
                    np.allclose(legacy_obs["visual"], compiled_obs["visual"], atol=1.0e-5),
                    msg="reset visual mismatch",
                )

                actions = np.zeros((2, 17), dtype=np.float32)
                legacy_obs, legacy_rewards, legacy_dones, _legacy_infos = legacy_env.step(actions)
                compiled_obs, compiled_rewards, compiled_dones, _compiled_infos = compiled_env.step(actions)
                self.assertTrue(
                    np.allclose(legacy_obs["visual"], compiled_obs["visual"], atol=1.0e-5),
                    msg="step visual mismatch",
                )
                self.assertTrue(np.allclose(legacy_rewards, compiled_rewards, atol=1.0e-6))
                self.assertTrue(np.array_equal(legacy_dones, compiled_dones))
            finally:
                legacy_env.close()
                compiled_env.close()

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

    def test_world_batch_vec_env_reports_effective_flight_shaping_backend_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="legacy",
                flight_shaping_backend="auto",
            )
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
                self.assertEqual(legacy_env._flight_shaping_backend_mode(), "legacy")
                self.assertEqual(compiled_env._flight_shaping_backend_mode(), "compiled")
                self.assertEqual(gpu_env._flight_shaping_backend_mode(), "gpu_host")
            finally:
                legacy_env.close()
                compiled_env.close()
                gpu_env.close()

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
