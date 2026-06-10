from __future__ import annotations

import json
import tempfile
import unittest
from unittest import mock

import numpy as np

from gym_envs.leader_env import LeaderTrainingEnv
from tests.support._leader_env_runtime_test_support import (
    CountingWindowRuntime,
    DirectPredictModel,
    DummyFrozenPolicy,
    FakeExecutionRuntime,
    FakeLeaderWindowRuntime,
    FakePreparedExecutionRuntime,
    PendingLeaderState,
)


class LeaderEnvRuntimeControlTests(unittest.TestCase):
    def test_execution_action_repeat_reuses_predicted_action(self):
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env.execution_backend = "frozen_model"
        env.execution_action_repeat = 3
        env._exec_policy = DummyFrozenPolicy()
        env._last_exec_action = None
        env._exec_action_repeat_remaining = 0
        env._last_effective_execution_action_repeat = 1

        first = env._predict_execution_action({})
        second = env._predict_execution_action({})
        third = env._predict_execution_action({})
        fourth = env._predict_execution_action({})

        self.assertEqual(env._exec_policy.calls, 2)
        self.assertTrue(np.allclose(first, second))
        self.assertTrue(np.allclose(first, third))
        self.assertFalse(np.allclose(first, fourth))
        self.assertEqual(env._last_effective_execution_action_repeat, 3)

    def test_leader_env_can_inject_execution_runtime(self):
        fake_runtime = FakeExecutionRuntime()
        with mock.patch.object(LeaderTrainingEnv, "_build_execution_env", side_effect=AssertionError("should not build env")):
            with mock.patch.object(LeaderTrainingEnv, "_build_execution_policy", return_value=object()):
                env = LeaderTrainingEnv(
                    scenario_path="scenarios/combined/takeoff_to_landing_continuous_train_v1.json",
                    execution_runtime=fake_runtime,
                    execution_device="cuda",
                    execution_use_autocast=True,
                )

        try:
            self.assertIs(env.unwrapped, fake_runtime.unwrapped)
            self.assertIs(env._exec_runtime, fake_runtime)
            self.assertEqual(env.execution_device, "cuda")
            self.assertTrue(env.execution_use_autocast)
            env.set_randomization_overrides({"wind_speed_range": [1.0, 2.0]})
            self.assertEqual(fake_runtime.last_overrides, {"wind_speed_range": [1.0, 2.0]})
        finally:
            env.close()

    def test_leader_env_build_execution_policy_uses_direct_policy_forward(self):
        model = DirectPredictModel()
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env.execution_backend = "frozen_model"
        env.execution_model_path = "/tmp/frozen_exec.zip"
        env.execution_algo = "auto"
        env.execution_device = "cpu"
        env.execution_use_autocast = False
        env.execution_action_repeat = 1
        env.execution_torch_threads = None
        env.execution_torch_interop_threads = None

        with mock.patch(
            "gym_envs.leader_env_parts.execution_runtime.policy_runtime.load_policy",
            return_value=model,
        ) as load_policy:
            env._exec_policy = LeaderTrainingEnv._build_execution_policy(env)

        env._last_exec_action = None
        env._exec_action_repeat_remaining = 0
        env._last_effective_execution_action_repeat = 1
        action = env._predict_execution_action({"vec": np.asarray([1.0, 2.0, 3.0], dtype=np.float32)})
        env._exec_policy.reset({"vec": np.asarray([0.0, 0.0, 0.0], dtype=np.float32)})

        load_policy.assert_called_once_with("/tmp/frozen_exec.zip", algo_name="auto", device="cpu")
        self.assertTrue(np.allclose(action, np.asarray([0.25, -0.5], dtype=np.float32)))
        self.assertEqual(model.policy.training_modes, [False])
        self.assertEqual(model.policy.obs_calls, 1)
        self.assertEqual(model.policy.predict_calls, 1)
        self.assertEqual(model.reset_calls, 1)

    def test_leader_env_delegates_prepare_and_finalize_to_execution_runtime(self):
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env._exec_runtime = FakePreparedExecutionRuntime()
        env._pending_leader_state = PendingLeaderState()
        env._last_exec_obs = None
        env._last_c2_info = {}
        env._update_scripted_c2 = lambda: None
        env._cache_execution_runtime_state = lambda *args, **kwargs: None

        action, prepared_state = env.prepare_shared_execution_action(np.asarray([0.5, -0.5], dtype=np.float32))
        self.assertTrue(np.allclose(action, np.asarray([1.5, 0.5], dtype=np.float32)))
        self.assertEqual(prepared_state, {"prepared": True})

        env.apply_execution_step_result(
            {"obs": 1},
            3.0,
            False,
            False,
            {"raw": True},
            prepared_action_state=prepared_state,
        )

        self.assertEqual(env._exec_runtime.prepare_calls, 1)
        self.assertEqual(env._exec_runtime.finalize_calls, 1)
        self.assertEqual(env._pending_leader_state.exec_reward, 5.0)
        self.assertEqual(env._pending_leader_state.last_info["prepared_action_state"], {"prepared": True})

    def test_leader_env_rollout_pending_execution_window_runs_until_termination(self):
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env.decision_interval_steps = 5
        env.collect_step_timing = False
        env._exec_runtime = CountingWindowRuntime(terminate_after=2)
        env._pending_leader_state = PendingLeaderState()
        env._last_exec_obs = {"vec": np.asarray([0.0], dtype=np.float32)}
        env._last_c2_info = {}
        env._cache_execution_runtime_state = lambda *args, **kwargs: None
        env._update_scripted_c2 = lambda: None
        env._predict_execution_action = lambda obs: np.asarray([float(obs["vec"][0]) + 1.0], dtype=np.float32)

        step_count = LeaderTrainingEnv.rollout_pending_execution_window(env)

        self.assertEqual(step_count, 2)
        self.assertEqual(env._exec_runtime.step_calls, 2)
        self.assertTrue(env._pending_leader_state.terminated)
        self.assertEqual(env._pending_leader_state.execution_step_count, 2)
        self.assertAlmostEqual(env._pending_leader_state.exec_reward, 4.0)
        self.assertTrue(env._pending_leader_state.last_info["finalized"])
        self.assertTrue(np.allclose(env.borrow_execution_observation()["vec"], np.asarray([2.0], dtype=np.float32)))

    def test_leader_env_step_delegates_to_leader_window_runtime(self):
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env._leader_window_runtime = FakeLeaderWindowRuntime()

        obs, reward, terminated, truncated, info = LeaderTrainingEnv.step(
            env,
            np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32),
        )

        self.assertEqual(len(env._leader_window_runtime.run_calls), 1)
        self.assertTrue(
            np.allclose(env._leader_window_runtime.run_calls[0], np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32))
        )
        self.assertEqual(float(reward), 7.0)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(info["runtime"], "leader_window")
        self.assertIn("task", obs)

    def test_leader_env_resolve_execution_env_spec_runtime_mode_sources(self):
        cases = (
            {
                "name": "direct_override",
                "execution_train_config": None,
                "execution_step_runtime_mode": "legacy",
            },
            {
                "name": "execution_config",
                "execution_train_config_payload": {
                    "env": {
                        "execution_step_runtime_mode": "legacy",
                        "runtime_compatibility_enabled": True,
                    }
                },
                "execution_step_runtime_mode": None,
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                with tempfile.TemporaryDirectory() as tmpdir:
                    train_config_path = None
                    if "execution_train_config_payload" in case:
                        train_config_path = f"{tmpdir}/execution_env.json"
                        with open(train_config_path, "w", encoding="utf-8") as f:
                            json.dump(case["execution_train_config_payload"], f, ensure_ascii=True)

                    env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
                    env.execution_train_config = train_config_path if train_config_path is not None else case["execution_train_config"]
                    env.execution_step_runtime_mode = case["execution_step_runtime_mode"]
                    env.collect_step_timing = False
                    env._execution_env_settings = {}
                    env._execution_wrapper_class = None
                    env._execution_wrapper_kwargs = None

                    env_settings, wrapper_class, wrapper_kwargs = LeaderTrainingEnv._resolve_execution_env_spec(env)

                    self.assertEqual(env_settings["execution_step_runtime_mode"], "legacy")
                    self.assertIsNone(wrapper_class)
                    self.assertIsNone(wrapper_kwargs)
