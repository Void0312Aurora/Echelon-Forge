from __future__ import annotations

import unittest
from collections import deque
from tempfile import gettempdir

import gymnasium as gym
import numpy as np
import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo.first_event_hazard import (
    A6_FIRST_EVENT_FIELD_ACTIVE,
    A6_FIRST_EVENT_FIELD_SOURCE,
    A6_FIRST_EVENT_FIELD_TARGET,
    A6_FIRST_EVENT_FIELD_WEIGHT,
    A6_FIRST_EVENT_FIELD_WINDOW_ID,
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy, SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv


class _WarmupSchedule:
    def __call__(self, progress_remaining: float) -> float:
        return 3.0e-4


class _TinyHMoEEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=np.float32),
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=np.float32),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=np.float32),
                "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32),
            }
        )
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32)
        self._steps = 0

    def reset(self, *, seed=None, options=None):
        self._steps = 0
        return self._obs(), {}

    def step(self, action):
        self._steps += 1
        terminated = self._steps >= 1
        truncated = False
        return self._obs(), 0.0, terminated, truncated, {}

    def _obs(self):
        return {
            "image": np.zeros((1, 8, 8), dtype=np.float32),
            "instruments": np.zeros((26,), dtype=np.float32),
            "mission": np.zeros((21,), dtype=np.float32),
            "prev_action": np.zeros((17,), dtype=np.float32),
        }


class _TinyHoldEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32),
                "mission": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
            }
        )
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        self._steps = 0

    def reset(self, *, seed=None, options=None):
        self._steps = 0
        return self._obs(), {}

    def step(self, action):
        self._steps += 1
        reward = -float(np.mean(np.square(np.asarray(action, dtype=np.float32))))
        terminated = self._steps >= 1
        truncated = False
        return self._obs(), reward, terminated, truncated, {}

    def _obs(self):
        return {
            "instruments": np.zeros((4,), dtype=np.float32),
            "mission": np.zeros((3,), dtype=np.float32),
        }


class _TinyHybridAirCombatEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=np.float32),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=np.float32),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=np.float32),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=np.float32),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=np.float32),
            }
        )
        self.action_space = make_action_space("air_combat_hybrid_v1")
        self._steps = 0

    def reset(self, *, seed=None, options=None):
        self._steps = 0
        return self._obs(), {}

    def step(self, action):
        self._steps += 1
        action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
        reward = -float(np.mean(np.square(action_arr[:6])))
        terminated = self._steps >= 1
        truncated = False
        return self._obs(), reward, terminated, truncated, {}

    def _obs(self):
        return {
            "instruments": np.zeros((42,), dtype=np.float32),
            "contacts": np.zeros((10, 5), dtype=np.float32),
            "rwr": np.zeros((4, 4), dtype=np.float32),
            "mission": np.zeros((21,), dtype=np.float32),
            "proprio": np.zeros((12,), dtype=np.float32),
        }


class _TinyA6HybridAirCombatEnv(_TinyHybridAirCombatEnv):
    def step(self, action):
        self._steps += 1
        action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
        reward = -float(np.mean(np.square(action_arr[:6])))
        terminated = False
        truncated = False
        info = {
            "engagement_state": "AuthorizedReady",
            "fire_mask": 1,
            "event_action_mask": [1, 1],
            "fire_once_accepted": False,
        }
        return self._obs(), reward, terminated, truncated, info


class _TinyA7ProjectionHybridAirCombatEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=np.float32),
                "contacts": spaces.Box(low=-1.0e6, high=1.0e6, shape=(10, 5), dtype=np.float32),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=np.float32),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=np.float32),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=np.float32),
            }
        )
        self.action_space = make_action_space("air_combat_hybrid_v1")

    def reset(self, *, seed=None, options=None):
        return self._obs(), {}

    def step(self, action):
        return self._obs(), 0.0, False, False, {}

    def _obs(self):
        mission = np.zeros((20,), dtype=np.float32)
        mission[5] = 1.0
        mission[6] = 0.0
        mission[14] = 4.0
        mission[15] = 0.0
        mission[16] = 0.0
        mission[17] = 1.0
        mission[19] = 0.0
        contacts = np.zeros((10, 5), dtype=np.float32)
        contacts[0, 0] = 16000.0
        contacts[0, 4] = 0.2
        return {
            "instruments": np.zeros((42,), dtype=np.float32),
            "contacts": contacts,
            "rwr": np.zeros((4, 4), dtype=np.float32),
            "mission": mission,
            "proprio": np.zeros((12,), dtype=np.float32),
        }


class _NoopCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


class HMoEPPOWarmupTests(unittest.TestCase):
    def test_a6_policy_fire_mask_uses_c2_roe_mission_window(self) -> None:
        mission = th.zeros((2, 20), dtype=th.float32)
        mission[:, 5] = 2.0
        mission[:, 6] = 1.0
        mission[:, 14] = 2.0
        mission[:, 15] = 1.0
        mission[:, 16] = 1.0
        mission[:, 19] = 1.0
        mission[1, 17] = 1.0

        mask = AdaptiveKLPPO._a6_first_event_policy_fire_mask_from_obs({"mission": mission}, 2)

        self.assertEqual(mask, [True, False])

    def test_a6_launch_window_uses_contact_range_and_track_age_from_policy_obs(self) -> None:
        contacts = th.zeros((2, 10, 5), dtype=th.float32)
        contacts[0, 0, 0] = 15000.0
        contacts[0, 0, 4] = 0.5
        contacts[1, 0, 0] = 42000.0
        contacts[1, 0, 4] = 0.5

        launch_window = AdaptiveKLPPO._a6_first_event_policy_launch_window_from_obs(
            {"contacts": contacts},
            2,
            min_range_m=8000.0,
            max_range_m=30000.0,
            max_track_age_s=2.0,
        )

        self.assertEqual(launch_window, [True, False])

    def test_a6_launch_window_prefers_latest_contacts_history_frame(self) -> None:
        contacts_history = th.zeros((2, 3, 10, 5), dtype=th.float32)
        contacts_history[0, 0, 0, 0] = 14000.0
        contacts_history[0, 0, 0, 4] = 0.2
        contacts_history[0, 2, 0, 0] = 42000.0
        contacts_history[0, 2, 0, 4] = 0.2
        contacts_history[1, 2, 0, 0] = 18000.0
        contacts_history[1, 2, 0, 4] = 3.5

        launch_window = AdaptiveKLPPO._a6_first_event_policy_launch_window_from_obs(
            {"contacts_history": contacts_history},
            2,
            min_range_m=8000.0,
            max_range_m=30000.0,
            max_track_age_s=2.0,
        )

        self.assertEqual(launch_window, [False, False])

    def test_collect_rollouts_applies_hmoe_warmup_before_first_step(self) -> None:
        env = DummyVecEnv([_TinyHMoEEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hmoe_residual_warmup_fraction": 0.3,
                "hmoe_residual_start_factor": 0.0,
            },
        )
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        recorded: list[float] = []
        original_forward = model.policy.forward

        def wrapped_forward(obs, deterministic: bool = False):
            recorded.append(float(model.policy._hmoe_residual_gate))
            return original_forward(obs, deterministic=deterministic)

        model.policy.forward = wrapped_forward  # type: ignore[method-assign]
        callback = _NoopCallback()
        callback.init_callback(model)

        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )

        self.assertTrue(ok)
        self.assertTrue(recorded)
        self.assertAlmostEqual(recorded[0], 0.0, places=6)

    def test_action_mean_regularization_pulls_deterministic_action_toward_target(self) -> None:
        env = DummyVecEnv([_TinyHoldEnv])
        model = AdaptiveKLPPO(
            SquashedMultiInputPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            action_mean_regularization_coef=5.0,
            action_mean_regularization_target=[0.0, 0.0, 0.0],
            policy_kwargs={
                "net_arch": {"pi": [16], "vf": [16]},
            },
        )
        model.set_logger(configure(format_strings=[]))
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)
        with th.no_grad():
            model.policy.action_net.weight.zero_()
            model.policy.action_net.bias.fill_(0.5)

        obs = env.reset()
        before, _ = model.predict(obs, deterministic=True)
        before_abs = float(np.mean(np.abs(before)))

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)
        model.train()

        after, _ = model.predict(obs, deterministic=True)
        after_abs = float(np.mean(np.abs(after)))

        self.assertLess(after_abs, before_abs)

    def test_air_combat_hybrid_policy_collects_and_trains_one_rollout(self) -> None:
        env = DummyVecEnv([_TinyHybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
            },
        )
        model.set_logger(configure(format_strings=[]))
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)
        model.train()

        obs = env.reset()
        action, _ = model.predict(obs, deterministic=True)
        self.assertEqual(tuple(action.shape), (1, 12))
        self.assertTrue(np.isfinite(action).all())

    def test_a6_first_event_labels_are_attached_to_rollout_minibatches(self) -> None:
        env = DummyVecEnv([_TinyA6HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=4,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_hazard_coef=0.2,
            a6_first_event_curriculum_coef=0.5,
            a6_first_event_curriculum_min_window_age_steps=2,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
            },
        )
        model.set_logger(configure(format_strings=[]))
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)

        rollout_data = next(model.rollout_buffer.get(model.n_steps))
        self.assertTrue(hasattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE))
        self.assertTrue(hasattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET))
        self.assertEqual(int(getattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE).sum().item()), 2)
        self.assertEqual(int((getattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET) > 0.5).sum().item()), 1)

        hazard_loss = model._first_event_hazard_loss(rollout_data)
        self.assertIsNotNone(hazard_loss)
        assert hazard_loss is not None
        self.assertEqual(hazard_loss.active_count, 2)
        self.assertGreater(float(hazard_loss.loss.detach().cpu().item()), 0.0)

        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)
        second_rollout_data = next(model.rollout_buffer.get(model.n_steps))
        self.assertEqual(int(getattr(second_rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE).sum().item()), 0)

    def test_a7_event_credit_only_collects_labels_and_updates_credit_head(self) -> None:
        env = DummyVecEnv([_TinyA6HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=4,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a7_event_credit_value_coef=0.5,
            a7_event_credit_curriculum_coef=0.5,
            a7_event_credit_curriculum_min_window_age_steps=1,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_credit_head_lr_scale": 6.0,
            },
        )
        self.assertFalse(model._a6_first_event_enabled())
        self.assertTrue(model._a7_event_credit_enabled())
        self.assertTrue(getattr(model.rollout_buffer, "supports_a6_first_event_labels", False))
        model.set_logger(configure(format_strings=[]))
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)

        rollout_data = next(model.rollout_buffer.get(model.n_steps))
        self.assertTrue(hasattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE))
        self.assertTrue(hasattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET))
        self.assertEqual(int(getattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE).sum().item()), 1)
        self.assertEqual(int((getattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET) > 0.5).sum().item()), 1)

        credit_loss = model._first_event_credit_loss(rollout_data)
        self.assertIsNotNone(credit_loss)
        assert credit_loss is not None
        self.assertEqual(credit_loss.active_count, 1)
        self.assertGreater(float(credit_loss.loss.detach().cpu().item()), 0.0)

        assert model.policy.hybrid_event_credit_head is not None
        before = model.policy.hybrid_event_credit_head.bias.detach().clone()
        model.train()
        after = model.policy.hybrid_event_credit_head.bias.detach().clone()
        self.assertFalse(th.allclose(before, after))

    def test_nonfinite_probe_preserves_a7_event_credit_training_path(self) -> None:
        env = DummyVecEnv([_TinyA6HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=4,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a7_event_credit_value_coef=0.5,
            a7_event_credit_curriculum_coef=0.5,
            a7_event_credit_curriculum_min_window_age_steps=1,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_credit_head_lr_scale": 6.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        probe = NonFiniteTrainingProbe(
            report_path=f"{gettempdir()}/a7_nonfinite_probe_regression.json",
            history_limit=32,
            enabled=True,
        )
        probe.install(model)

        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)

        rollout_data = next(model.rollout_buffer.get(model.n_steps))
        self.assertEqual(int(getattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE).sum().item()), 1)
        self.assertEqual(int((getattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET) > 0.5).sum().item()), 1)

        assert model.policy.hybrid_event_credit_head is not None
        before = model.policy.hybrid_event_credit_head.bias.detach().clone()
        model.train()
        after = model.policy.hybrid_event_credit_head.bias.detach().clone()

        self.assertFalse(th.allclose(before, after))
        self.assertIn("a7/event_credit_loss", model.logger.name_to_value)
        self.assertGreater(float(model.logger.name_to_value["a7/event_credit_active_count_mean"]), 0.0)

    def test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits(self) -> None:
        env = DummyVecEnv([_TinyA7ProjectionHybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a7_event_credit_value_coef=0.0,
            a7_event_credit_delta_align_coef=0.5,
            a7_event_credit_legal_projection_enabled=True,
            a7_event_credit_projection_value_coef=0.5,
            a7_event_credit_projection_delta_align_coef=0.5,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_head_lr_scale": 6.0,
                "hybrid_event_credit_head_lr_scale": 6.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        assert model.policy.hybrid_event_credit_head is not None
        assert model.policy.hybrid_event_head is not None
        with th.no_grad():
            model.policy.hybrid_event_credit_head.weight.zero_()
            model.policy.hybrid_event_credit_head.bias.copy_(th.tensor([0.0, 2.0], dtype=th.float32))

        obs_np = env.reset()
        obs = model.policy.obs_to_tensor(obs_np)[0]

        class _RolloutData:
            observations = obs

        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_ACTIVE, th.ones((1,), dtype=th.float32))
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_TARGET, th.ones((1,), dtype=th.float32))
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_WEIGHT, th.ones((1,), dtype=th.float32))
        setattr(
            _RolloutData,
            A6_FIRST_EVENT_FIELD_SOURCE,
            th.full((1,), A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY, dtype=th.long),
        )
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_WINDOW_ID, th.zeros((1,), dtype=th.long))

        credit_loss = model._first_event_credit_loss(_RolloutData)
        self.assertIsNotNone(credit_loss)
        assert credit_loss is not None
        self.assertEqual(credit_loss.projection_active_count, 1)
        self.assertEqual(credit_loss.projection_unsupported_count, 0)
        self.assertGreater(float(credit_loss.projection_advantage_mean), 1.0)
        self.assertGreater(float(credit_loss.loss.detach().cpu().item()), 0.0)

        model.policy.optimizer.zero_grad()
        credit_loss.loss.backward()
        event_grad = 0.0
        for param in model.policy.hybrid_event_head.parameters():
            if param.grad is not None:
                event_grad += float(param.grad.detach().abs().sum().cpu().item())
        self.assertGreater(event_grad, 0.0)


if __name__ == "__main__":
    unittest.main()
