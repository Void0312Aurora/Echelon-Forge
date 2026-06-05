from __future__ import annotations

import unittest
from collections import deque
from tempfile import gettempdir
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.first_event_hazard import (
    A6_FIRST_EVENT_FIELD_ACTIVE,
    A6_FIRST_EVENT_FIELD_SOURCE,
    A6_FIRST_EVENT_FIELD_TARGET,
    A6_FIRST_EVENT_FIELD_WEIGHT,
    A6_FIRST_EVENT_FIELD_WINDOW_ID,
    A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventCreditLoss,
    FirstEventHazardLabels,
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


class _TinyM3S1HybridAirCombatEnv(_TinyA6HybridAirCombatEnv):
    def _obs(self):
        obs = super()._obs()
        contacts = np.zeros((10, 5), dtype=np.float32)
        if self._steps >= 2:
            contacts[0, 0] = 1000.0
            contacts[0, 4] = 0.1
        obs["contacts"] = contacts
        return obs


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
        contacts[0, 0] = 1.0
        contacts[0, 4] = 0.2
        return {
            "instruments": np.zeros((42,), dtype=np.float32),
            "contacts": contacts,
            "rwr": np.zeros((4, 4), dtype=np.float32),
            "mission": mission,
            "proprio": np.zeros((12,), dtype=np.float32),
        }


class _TinyA7LegalOpenHybridAirCombatEnv(_TinyA7ProjectionHybridAirCombatEnv):
    def _obs(self):
        obs = super()._obs()
        mission = np.array(obs["mission"], copy=True)
        mission[5] = 2.0
        mission[6] = 1.0
        mission[14] = 2.0
        mission[15] = 1.0
        mission[16] = 1.0
        mission[17] = 0.0
        mission[19] = 1.0
        obs["mission"] = mission
        return obs


class _NoopCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


def _grad_norm(params) -> float:
    total = 0.0
    for param in params:
        if param.grad is not None:
            total += float(param.grad.detach().pow(2).sum().cpu().item())
    return total**0.5


class _FirstEventLabelBuffer:
    supports_a6_first_event_labels = True

    def __init__(self, buffer_size: int, n_envs: int = 1) -> None:
        self.buffer_size = int(buffer_size)
        self.n_envs = int(n_envs)
        self.labels: FirstEventHazardLabels | None = None

    def set_a6_first_event_labels(self, labels: FirstEventHazardLabels) -> None:
        self.labels = labels


class HMoEPPOWarmupTests(unittest.TestCase):
    def _make_a7_first_event_label_model(self) -> AdaptiveKLPPO:
        model = object.__new__(AdaptiveKLPPO)
        model.device = th.device("cpu")
        model.a6_first_event_hazard_coef = 0.0
        model.a6_first_event_curriculum_coef = 0.0
        model.a6_first_event_censored_survival_weight = 0.0
        model.a6_first_event_deadline_weight = 0.0
        model.a6_first_event_launch_window_enabled = True
        model.a6_first_event_launch_window_min_window_age_steps = 32
        model.a6_first_event_deadline_min_window_age_steps = 96
        model.a6_first_event_launch_window_prewindow_hold_weight = 0.0
        model.a6_first_event_launch_window_early_accept_weight = 0.0
        model.a6_first_event_curriculum_min_window_age_steps = 32
        model.a7_event_credit_value_coef = 0.5
        model.a7_event_credit_delta_align_coef = 0.0
        model.a7_event_credit_projection_value_coef = 0.0
        model.a7_event_credit_projection_delta_align_coef = 0.0
        model.a7_event_credit_prewindow_hold_weight = 0.25
        model.a7_event_credit_early_accept_weight = 0.75
        model.a7_event_credit_curriculum_coef = 0.0
        model.a7_event_credit_curriculum_min_window_age_steps = 32
        model.a7_event_credit_censored_survival_weight = 0.0
        model.a7_event_credit_deadline_weight = 0.0
        model.a7_event_credit_deadline_min_window_age_steps = 96
        model.a7_event_credit_shadow_quality_weight = 0.5
        model.a7_event_credit_legal_open_quality_weight = 0.0
        model.a7_event_credit_legal_open_quality_min_window_age_steps = 1
        model.a7_event_policy_margin_coef = 0.0
        model.a7_event_policy_margin = 2.0
        model.a7_event_policy_projection_margin_coef = 0.0
        model.a7_event_policy_separate_update_enabled = False
        model.a7_event_policy_separate_update_max_grad_norm = 0.5
        model.a7_event_policy_separate_update_steps = 1
        return model

    def _make_a7_policy_margin_model(
        self,
        *,
        separate_update: bool,
    ) -> tuple[AdaptiveKLPPO, DummyVecEnv]:
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
            a7_event_credit_delta_align_coef=0.0,
            a7_event_credit_legal_projection_enabled=True,
            a7_event_credit_positive_mass_cap=1.0,
            a7_event_credit_negative_mass_cap=1.0,
            a7_event_policy_margin_coef=0.35,
            a7_event_policy_margin=2.0,
            a7_event_policy_projection_margin_coef=0.15,
            a7_event_policy_separate_update_enabled=separate_update,
            a7_event_policy_separate_update_max_grad_norm=0.5,
            a7_event_policy_separate_update_steps=1,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_head_lr_scale": 10.0,
                "hybrid_event_credit_head_lr_scale": 6.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        with th.no_grad():
            model.policy.action_net.weight[9].fill_(0.01)
            model.policy.action_net.weight[11].fill_(-0.01)
        return model, env

    def _a7_shadow_projection_rollout_data(self, model: AdaptiveKLPPO, env: DummyVecEnv):
        obs = env.reset()
        obs_t = {
            key: th.as_tensor(value, device=model.device)
            for key, value in obs.items()
        }
        batch_size = int(next(iter(obs_t.values())).shape[0])
        active = th.ones((batch_size,), dtype=th.bool, device=model.device)
        target = th.ones((batch_size,), dtype=th.float32, device=model.device)
        weight = th.ones((batch_size,), dtype=th.float32, device=model.device)
        source = th.full(
            (batch_size,),
            int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY),
            dtype=th.long,
            device=model.device,
        )
        window_id = th.zeros((batch_size,), dtype=th.long, device=model.device)
        return SimpleNamespace(
            observations=obs_t,
            **{
                A6_FIRST_EVENT_FIELD_ACTIVE: active,
                A6_FIRST_EVENT_FIELD_TARGET: target,
                A6_FIRST_EVENT_FIELD_WEIGHT: weight,
                A6_FIRST_EVENT_FIELD_SOURCE: source,
                A6_FIRST_EVENT_FIELD_WINDOW_ID: window_id,
            },
        )

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

    def test_a6_policy_fire_mask_uses_c2_roe_v2_explicit_state_completion(self) -> None:
        mode = "air_combat_c2_roe_v2"
        mission = th.zeros((2, mission_observation_dim(mode)), dtype=th.float32)
        mission[0, mission_observation_field_index(mode, "fire_mask_open")] = 1.0

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

    def test_a6_launch_window_uses_c2_roe_v2_explicit_state_completion(self) -> None:
        mode = "air_combat_c2_roe_v2"
        mission = th.zeros((2, mission_observation_dim(mode)), dtype=th.float32)
        mission[0, mission_observation_field_index(mode, "launch_window_open")] = 1.0
        contacts = th.zeros((2, 10, 5), dtype=th.float32)
        contacts[:, 0, 0] = 45000.0
        contacts[:, 0, 4] = 0.5

        launch_window = AdaptiveKLPPO._a6_first_event_policy_launch_window_from_obs(
            {"mission": mission, "contacts": contacts},
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

    def test_a7_cross_rollout_first_event_state_recovers_shadow_quality_after_boundary(self) -> None:
        model = self._make_a7_first_event_label_model()
        episode_len = 512
        chunk_size = 128
        accepted_index = 5
        launch_open_start = 281
        engagement_state = [
            "AuthorizedReady" if idx <= accepted_index else "FiredAssess"
            for idx in range(episode_len)
        ]
        fire_mask = [idx <= accepted_index for idx in range(episode_len)]
        fire_once_accepted = [idx == accepted_index for idx in range(episode_len)]
        episode_id = [0] * episode_len
        launch_window_open = [idx >= launch_open_start for idx in range(episode_len)]

        full_labels = model._build_a6_first_event_labels_from_rollout_infos(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
        )
        full_shadow_positive = (
            (full_labels.source == A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY)
            & (full_labels.target > 0.5)
            & full_labels.active
        )
        self.assertEqual(int(full_shadow_positive.sum().item()), episode_len - launch_open_start)

        local_shadow_positive_count = 0
        for start in range(0, episode_len, chunk_size):
            end = min(start + chunk_size, episode_len)
            local_labels = model._build_a6_first_event_labels_from_rollout_infos(
                engagement_state=engagement_state[start:end],
                fire_mask=fire_mask[start:end],
                fire_once_accepted=fire_once_accepted[start:end],
                episode_id=episode_id[start:end],
                launch_window_open=launch_window_open[start:end],
            )
            local_shadow_positive_count += int(
                (
                    (local_labels.source == A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY)
                    & (local_labels.target > 0.5)
                    & local_labels.active
                ).sum().item()
            )
        self.assertEqual(local_shadow_positive_count, 0)

        chunked_labels: list[FirstEventHazardLabels] = []
        for start in range(0, episode_len, chunk_size):
            end = min(start + chunk_size, episode_len)
            buffer = _FirstEventLabelBuffer(buffer_size=end - start)
            model._attach_a6_first_event_labels_to_rollout_buffer(
                buffer,
                engagement_state=engagement_state[start:end],
                fire_mask=fire_mask[start:end],
                fire_once_accepted=fire_once_accepted[start:end],
                episode_id=episode_id[start:end],
                launch_window_open=launch_window_open[start:end],
                env_episode_id_after_rollout=np.array([0], dtype=np.int64),
            )
            self.assertIsNotNone(buffer.labels)
            assert buffer.labels is not None
            chunked_labels.append(buffer.labels)

        def concat_field(name: str) -> th.Tensor:
            return th.cat([getattr(labels, name).detach().cpu().reshape(-1) for labels in chunked_labels])

        self.assertTrue(th.equal(concat_field("active"), full_labels.active.cpu()))
        self.assertTrue(th.allclose(concat_field("target"), full_labels.target.cpu()))
        self.assertTrue(th.allclose(concat_field("weight"), full_labels.weight.cpu()))
        self.assertTrue(th.equal(concat_field("source"), full_labels.source.cpu()))
        self.assertTrue(th.allclose(concat_field("window_age"), full_labels.window_age.cpu()))
        self.assertTrue(th.equal(concat_field("window_id"), full_labels.window_id.cpu()))
        self.assertTrue(th.equal(concat_field("had_accepted"), full_labels.had_accepted.cpu()))
        self.assertEqual(int(model._a7_cross_rollout_last_carried_shadow_pending_envs), 1)
        self.assertEqual(int(model._a7_cross_rollout_last_carried_shadow_positive_count), chunk_size)
        self.assertEqual(int(model._a7_cross_rollout_last_first_event_count), chunk_size)

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
            a7_event_credit_separate_update_enabled=True,
            a7_event_credit_separate_update_max_grad_norm=0.5,
            a7_event_credit_delta_align_positive_only=True,
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

    def test_m3s1_sidecar_preserves_closed_mask_rows(self) -> None:
        model = object.__new__(AdaptiveKLPPO)
        model.m3s1_grouped_stopping_coef = 1.0
        model.a6_first_event_launch_window_min_window_age_steps = 1
        buffer = SimpleNamespace(
            n_envs=1,
            observations={
                "mission": np.zeros((3, 1, 21), dtype=np.float32),
            },
        )

        sidecar = model._build_m3s1_grouped_stopping_sidecar(
            buffer,
            fire_mask=[False, True, True],
            fire_once_accepted=[False, False, False],
            episode_id=[0, 0, 0],
            launch_window_open=[True, True, True],
        )

        self.assertIsNotNone(sidecar)
        assert sidecar is not None
        self.assertEqual(len(sidecar.groups), 1)
        self.assertEqual(sidecar.groups[0].row_indices, (0, 1, 2))
        self.assertEqual(sidecar.groups[0].legal_mask, (False, True, True))
        self.assertEqual(sidecar.groups[0].quality_mask, (False, True, True))
        self.assertEqual(sidecar.accepted_event_count, 0)
        self.assertEqual(sidecar.one_shot_violation_count, 0)
        self.assertEqual(sidecar.closed_mask_accepted_event_count, 0)

        violation_buffer = SimpleNamespace(
            n_envs=1,
            observations={
                "mission": np.zeros((4, 1, 21), dtype=np.float32),
            },
        )
        violation_sidecar = model._build_m3s1_grouped_stopping_sidecar(
            violation_buffer,
            fire_mask=[True, True, False, True],
            fire_once_accepted=[True, True, True, False],
            episode_id=[7, 7, 7, 7],
            launch_window_open=[True, True, True, True],
        )

        self.assertIsNotNone(violation_sidecar)
        assert violation_sidecar is not None
        self.assertEqual(violation_sidecar.accepted_event_count, 3)
        self.assertEqual(violation_sidecar.one_shot_violation_count, 2)
        self.assertEqual(violation_sidecar.closed_mask_accepted_event_count, 1)

    def test_m3s1_grouped_stopping_auxiliary_updates_from_complete_sidecar_group(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_range_m=1.0,
            a6_first_event_launch_window_max_range_m=2000.0,
            a6_first_event_launch_window_max_track_age_s=10.0,
            m3s1_grouped_stopping_coef=1.0,
            m3s1_grouped_stopping_early_mass_coef=0.5,
            m3s1_grouped_stopping_early_mass_budget=0.05,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "m3_stopping_head_lr_scale": 5.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        assert model.policy.m3_stopping_head is not None
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
        sidecar = getattr(model, "_m3s1_grouped_stopping_sidecar", None)
        self.assertIsNotNone(sidecar)
        assert sidecar is not None
        self.assertEqual(len(sidecar.groups), 1)
        self.assertEqual(sidecar.groups[0].row_indices, (0, 1, 2, 3))
        self.assertEqual(sidecar.groups[0].quality_mask, (False, False, True, True))

        before = model.policy.m3_stopping_head.bias.detach().clone()
        model.train()
        after = model.policy.m3_stopping_head.bias.detach().clone()

        self.assertFalse(th.allclose(before, after))
        logged = model.logger.name_to_value
        self.assertEqual(float(logged["m3s1/grouped_sidecar_group_count"]), 1.0)
        self.assertEqual(float(logged["m3s1/grouped_active_group_count"]), 1.0)
        self.assertEqual(float(logged["m3s1/grouped_row_count"]), 4.0)
        self.assertGreater(float(logged["m3s1/grouped_stopping_loss"]), 0.0)
        self.assertGreater(float(logged["m3s1/grouped_stopping_grad_norm"]), 0.0)
        self.assertGreater(float(logged["m3s1/hazard_early_mass"]), 0.0)
        for key in (
            "m3s1/grouped_labels_reached_loss",
            "m3s1/stop_logit_mean",
            "m3s1/stop_logit_desirable_mean",
            "m3s1/stop_logit_prewindow_mean",
            "m3s1/stop_logit_no_window_mean",
            "m3s1/event_logit_delta_diagnostic_mean",
            "m3s1/boundary_cross_ratio",
            "m3s1/boundary_cross_in_window_ratio",
            "m3s1/closed_mask_stop_attempt_ratio",
            "m3s1/one_shot_violation_count",
            "m3s1/closed_mask_accepted_event_count",
        ):
            self.assertIn(key, logged)
            self.assertTrue(np.isfinite(float(logged[key])), key)
        self.assertEqual(float(logged["m3s1/grouped_labels_reached_loss"]), 1.0)
        self.assertEqual(float(logged["m3s1/stop_logit_count"]), 4.0)
        self.assertEqual(float(logged["m3s1/stop_logit_desirable_count"]), 2.0)
        self.assertEqual(float(logged["m3s1/stop_logit_prewindow_count"]), 2.0)
        self.assertEqual(float(logged["m3s1/stop_logit_no_window_count"]), 0.0)
        self.assertEqual(float(logged["m3s1/event_logit_delta_diagnostic_count"]), 4.0)
        self.assertEqual(float(logged["m3s1/boundary_cross_count"]), 4.0)
        self.assertEqual(float(logged["m3s1/boundary_cross_in_window_count"]), 2.0)
        self.assertAlmostEqual(float(logged["m3s1/boundary_cross_ratio"]), 1.0, places=6)
        self.assertAlmostEqual(float(logged["m3s1/boundary_cross_in_window_ratio"]), 0.5, places=6)
        self.assertEqual(float(logged["m3s1/closed_mask_stop_attempt_count"]), 0.0)
        self.assertEqual(float(logged["m3s1/closed_mask_row_count"]), 0.0)
        self.assertEqual(float(logged["m3s1/accepted_event_count"]), 0.0)
        self.assertEqual(float(logged["m3s1/one_shot_violation_count"]), 0.0)
        self.assertEqual(float(logged["m3s1/closed_mask_accepted_event_count"]), 0.0)

    def test_m3s2_event_window_auxiliary_updates_executable_event_policy_path(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_range_m=1.0,
            a6_first_event_launch_window_max_range_m=2000.0,
            a6_first_event_launch_window_max_track_age_s=10.0,
            m3s2_event_window_coef=1.0,
            m3s2_event_window_early_mass_coef=0.5,
            m3s2_event_window_early_mass_budget=0.05,
            m3s2_event_window_delay_coef=0.25,
            m3s2_event_window_deadline_coef=0.25,
            m3s2_event_window_deadline_steps=2,
            m3s2_event_window_quality_boundary_coef=1.0,
            m3s2_event_window_quality_boundary_logit=0.0,
            m3s2_event_window_contrastive_margin_coef=1.0,
            m3s2_event_window_contrastive_margin=1.5,
            m3s2_event_window_separate_update_enabled=True,
            m3s2_event_window_dedicated_optimizer_enabled=True,
            m3s2_event_window_separate_update_steps=2,
            m3s2_event_window_max_grad_norm=2.0,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_head_lr_scale": 10.0,
                "hybrid_event_credit_head_lr_scale": 6.0,
                "m3_stopping_head_lr_scale": 5.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        self.assertFalse(model._m3s1_grouped_stopping_enabled())
        self.assertTrue(model._m3s2_event_window_enabled())
        self.assertTrue(model._first_event_label_collection_enabled())
        assert model.policy.hybrid_event_head is not None
        assert model.policy.hybrid_event_credit_head is not None
        assert model.policy.m3_stopping_head is not None

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
        sidecar = getattr(model, "_m3s1_grouped_stopping_sidecar", None)
        self.assertIsNotNone(sidecar)
        assert sidecar is not None
        self.assertEqual(len(sidecar.groups), 1)
        self.assertEqual(sidecar.groups[0].quality_mask, (False, False, True, True))

        before = {
            name: param.detach().clone()
            for name, param in model.policy.named_parameters()
        }
        event_window_loss = model._m3s2_event_window_auxiliary_update()

        self.assertIsNotNone(event_window_loss)
        assert event_window_loss is not None
        self.assertEqual(event_window_loss.stats.window_group_count, 1)
        self.assertGreater(float(event_window_loss.loss.detach().cpu().item()), 0.0)
        self.assertGreater(float(model._m3s2_last_event_window_grad_norm), 0.0)
        self.assertGreater(float(event_window_loss.stats.mean_p_window), 0.0)
        self.assertGreaterEqual(float(event_window_loss.stats.mean_p_deadline), 0.0)
        self.assertGreaterEqual(float(event_window_loss.stats.mean_quality_boundary_margin_loss), 0.0)
        self.assertGreaterEqual(float(event_window_loss.stats.mean_quality_prewindow_margin_loss), 0.0)

        selected_changed = False
        for name, param in model.policy.named_parameters():
            changed = not th.allclose(before[name], param.detach())
            if name.startswith(("action_net.", "hybrid_event_head.", "mlp_extractor.policy_net.")):
                selected_changed = selected_changed or changed
            else:
                self.assertFalse(changed, name)
        self.assertTrue(selected_changed)

    def test_m3s2_event_window_can_train_dedicated_stopping_head_adapter(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_range_m=1.0,
            a6_first_event_launch_window_max_range_m=2000.0,
            a6_first_event_launch_window_max_track_age_s=10.0,
            m3s2_event_window_coef=1.0,
            m3s2_event_window_early_mass_coef=0.5,
            m3s2_event_window_early_mass_budget=0.05,
            m3s2_event_window_quality_boundary_coef=1.0,
            m3s2_event_window_quality_boundary_logit=0.0,
            m3s2_event_window_contrastive_margin_coef=1.0,
            m3s2_event_window_contrastive_margin=1.5,
            m3s2_event_window_balanced_bce_coef=2.0,
            m3s2_event_window_use_stopping_head=True,
            m3s2_event_window_separate_update_enabled=True,
            m3s2_event_window_dedicated_optimizer_enabled=True,
            m3s2_event_window_separate_update_steps=2,
            m3s2_event_window_max_grad_norm=2.0,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_use_m3_stopping_head": True,
                "m3_stopping_head_lr_scale": 5.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        assert model.policy.m3_stopping_head is not None

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

        before = {
            name: param.detach().clone()
            for name, param in model.policy.named_parameters()
        }
        event_window_loss = model._m3s2_event_window_auxiliary_update()

        self.assertIsNotNone(event_window_loss)
        assert event_window_loss is not None
        self.assertEqual(event_window_loss.stats.window_group_count, 1)
        self.assertGreater(float(model._m3s2_last_event_window_grad_norm), 0.0)
        self.assertGreaterEqual(float(event_window_loss.stats.mean_window_balanced_bce_loss), 0.0)

        selected_changed = False
        for name, param in model.policy.named_parameters():
            changed = not th.allclose(before[name], param.detach())
            if name.startswith("m3_stopping_head."):
                selected_changed = selected_changed or changed
            else:
                self.assertFalse(changed, name)
        self.assertTrue(selected_changed)

    def test_m3s2_support_preserving_collect_masks_until_quality_ready(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_window_age_steps=3,
            m3s2_event_window_coef=1.0,
            m3s2_event_window_support_preserving_collect_enabled=True,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_head_lr_scale": 10.0,
            },
        )

        first = model._m3s2_support_preserving_collect_masks(
            fire_mask=[True],
            launch_window_open=[False],
            n_envs=1,
        )
        second = model._m3s2_support_preserving_collect_masks(
            fire_mask=[True],
            launch_window_open=[True],
            n_envs=1,
        )
        third = model._m3s2_support_preserving_collect_masks(
            fire_mask=[True],
            launch_window_open=[True],
            n_envs=1,
        )

        self.assertEqual(first, [True])
        self.assertEqual(second, [True])
        self.assertEqual(third, [False])
        self.assertEqual(model._m3s2_support_preserving_collect_hold_count, 2)
        self.assertEqual(model._m3s2_support_preserving_collect_candidate_count, 3)
        self.assertEqual(model._m3s2_support_preserving_collect_quality_count, 1)

        model.m3s2_event_window_support_preserving_hold_quality_enabled = True
        fourth = model._m3s2_support_preserving_collect_masks(
            fire_mask=[True],
            launch_window_open=[True],
            n_envs=1,
        )
        self.assertEqual(fourth, [True])
        self.assertEqual(model._m3s2_support_preserving_collect_hold_count, 3)
        self.assertEqual(model._m3s2_support_preserving_collect_quality_count, 2)

    def test_nonfinite_probe_preserves_m3s1_grouped_stopping_training_path(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_range_m=1.0,
            a6_first_event_launch_window_max_range_m=2000.0,
            a6_first_event_launch_window_max_track_age_s=10.0,
            m3s1_grouped_stopping_coef=1.0,
            m3s1_grouped_stopping_early_mass_coef=0.5,
            m3s1_grouped_stopping_early_mass_budget=0.05,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "m3_stopping_head_lr_scale": 5.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        probe = NonFiniteTrainingProbe(
            report_path=f"{gettempdir()}/m3s1_nonfinite_probe_regression.json",
            history_limit=32,
            enabled=True,
        )
        probe.install(model)
        assert model.policy.m3_stopping_head is not None
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
        sidecar = getattr(model, "_m3s1_grouped_stopping_sidecar", None)
        self.assertIsNotNone(sidecar)
        assert sidecar is not None
        self.assertEqual(len(sidecar.groups), 1)

        before = model.policy.m3_stopping_head.bias.detach().clone()
        model.train()
        after = model.policy.m3_stopping_head.bias.detach().clone()

        self.assertFalse(th.allclose(before, after))
        logged = model.logger.name_to_value
        self.assertEqual(float(logged["m3s1/grouped_sidecar_group_count"]), 1.0)
        self.assertEqual(float(logged["m3s1/grouped_active_group_count"]), 1.0)
        self.assertGreater(float(logged["m3s1/grouped_stopping_loss"]), 0.0)
        self.assertGreater(float(logged["m3s1/grouped_stopping_grad_norm"]), 0.0)
        self.assertEqual(float(logged["m3s1/grouped_labels_reached_loss"]), 1.0)
        self.assertEqual(float(logged["m3s1/stop_logit_count"]), 4.0)

    def test_nonfinite_probe_preserves_m3s2_event_window_training_path(self) -> None:
        env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=4,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            a6_first_event_launch_window_enabled=True,
            a6_first_event_launch_window_min_range_m=1.0,
            a6_first_event_launch_window_max_range_m=2000.0,
            a6_first_event_launch_window_max_track_age_s=10.0,
            m3s2_event_window_coef=1.0,
            m3s2_event_window_early_mass_coef=0.5,
            m3s2_event_window_early_mass_budget=0.05,
            m3s2_event_window_delay_coef=0.25,
            m3s2_event_window_deadline_coef=0.25,
            m3s2_event_window_deadline_steps=2,
            m3s2_event_window_quality_boundary_coef=1.0,
            m3s2_event_window_quality_boundary_logit=0.0,
            m3s2_event_window_contrastive_margin_coef=1.0,
            m3s2_event_window_contrastive_margin=1.5,
            m3s2_event_window_separate_update_enabled=True,
            m3s2_event_window_dedicated_optimizer_enabled=True,
            m3s2_event_window_separate_update_steps=2,
            m3s2_event_window_max_grad_norm=2.0,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_head_lr_scale": 10.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        probe = NonFiniteTrainingProbe(
            report_path=f"{gettempdir()}/m3s2_nonfinite_probe_regression.json",
            history_limit=32,
            enabled=True,
        )
        probe.install(model)
        assert model.policy.hybrid_event_head is not None
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
        sidecar = getattr(model, "_m3s1_grouped_stopping_sidecar", None)
        self.assertIsNotNone(sidecar)
        assert sidecar is not None
        self.assertEqual(len(sidecar.groups), 1)

        before = model.policy.hybrid_event_head.bias.detach().clone()
        model.train()
        after = model.policy.hybrid_event_head.bias.detach().clone()

        self.assertFalse(th.allclose(before, after))
        logged = model.logger.name_to_value
        self.assertEqual(float(logged["m3s2/grouped_sidecar_group_count"]), 1.0)
        self.assertEqual(float(logged["m3s2/grouped_active_group_count"]), 1.0)
        self.assertGreater(float(logged["m3s2/event_window_loss"]), 0.0)
        self.assertGreater(float(logged["m3s2/event_window_grad_norm"]), 0.0)
        self.assertEqual(float(logged["m3s2/window_group_count"]), 1.0)
        self.assertEqual(float(logged["m3s2/event_logit_delta_count"]), 4.0)
        self.assertEqual(float(logged["m3s2/ew_q_boundary_coef"]), 1.0)
        self.assertEqual(float(logged["m3s2/ew_q_boundary_logit"]), 0.0)
        self.assertEqual(float(logged["m3s2/ew_contrast_coef"]), 1.0)
        self.assertEqual(float(logged["m3s2/ew_contrast_margin"]), 1.5)
        self.assertEqual(float(logged["m3s2/event_window_dedicated_optimizer_enabled"]), 1.0)
        self.assertIn("m3s2/q_boundary_logit", logged)
        self.assertIn("m3s2/q_boundary_loss", logged)
        self.assertIn("m3s2/q_pre_margin", logged)
        self.assertIn("m3s2/q_pre_margin_loss", logged)

    def test_a7_separate_credit_update_only_writes_credit_head(self) -> None:
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
            a7_event_credit_separate_update_enabled=True,
            a7_event_credit_separate_update_max_grad_norm=0.5,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_credit_head_lr_scale": 6.0,
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

        before = {
            name: param.detach().clone()
            for name, param in model.policy.named_parameters()
        }
        credit_loss, grad_norm = model._first_event_credit_separate_value_update(rollout_data)
        self.assertIsNotNone(credit_loss)
        assert credit_loss is not None
        self.assertEqual(credit_loss.active_count, 1)
        self.assertGreater(float(credit_loss.value_loss.detach().cpu()), 0.0)
        self.assertGreater(float(grad_norm), 0.0)

        credit_changed = False
        for name, param in model.policy.named_parameters():
            changed = not th.allclose(before[name], param.detach())
            if name.startswith("hybrid_event_credit_head."):
                credit_changed = credit_changed or changed
            else:
                self.assertFalse(changed, name)
        self.assertTrue(credit_changed)

    def test_a7_policy_margin_loss_projects_shadow_rows_into_policy_path(self) -> None:
        model, env = self._make_a7_policy_margin_model(separate_update=False)
        rollout_data = self._a7_shadow_projection_rollout_data(model, env)

        margin_loss = model._first_event_policy_margin_loss(rollout_data)
        self.assertIsNotNone(margin_loss)
        assert margin_loss is not None
        self.assertEqual(margin_loss.active_count, 1)
        self.assertEqual(margin_loss.projection_active_count, 1)
        self.assertAlmostEqual(float(margin_loss.positive_frac), 1.0, places=6)
        self.assertGreater(float(margin_loss.loss.detach().cpu()), 0.0)

        assert model.policy.hybrid_event_head is not None
        assert model.policy.hybrid_event_credit_head is not None
        model.policy.optimizer.zero_grad(set_to_none=True)
        margin_loss.loss.backward()

        self.assertGreater(_grad_norm(model.policy.action_net.parameters()), 0.0)
        self.assertGreater(_grad_norm(model.policy.hybrid_event_head.parameters()), 0.0)
        self.assertGreater(_grad_norm(model.policy.mlp_extractor.policy_net.parameters()), 0.0)
        self.assertAlmostEqual(
            _grad_norm(model.policy.hybrid_event_credit_head.parameters()),
            0.0,
            places=8,
        )

    def test_a7_separate_policy_margin_update_only_writes_event_policy_path(self) -> None:
        model, env = self._make_a7_policy_margin_model(separate_update=True)
        rollout_data = self._a7_shadow_projection_rollout_data(model, env)
        before = {
            name: param.detach().clone()
            for name, param in model.policy.named_parameters()
        }

        margin_loss, grad_norm = model._first_event_policy_margin_separate_update(rollout_data)
        self.assertIsNotNone(margin_loss)
        assert margin_loss is not None
        self.assertEqual(margin_loss.projection_active_count, 1)
        self.assertGreater(float(grad_norm), 0.0)

        selected_changed = False
        for name, param in model.policy.named_parameters():
            changed = not th.allclose(before[name], param.detach())
            if name.startswith(("action_net.", "hybrid_event_head.", "mlp_extractor.policy_net.")):
                selected_changed = selected_changed or changed
            else:
                self.assertFalse(changed, name)
        self.assertTrue(selected_changed)

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
            a7_event_credit_separate_update_enabled=True,
            a7_event_credit_separate_update_max_grad_norm=0.5,
            a7_event_credit_delta_align_positive_only=True,
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
        self.assertEqual(float(model.logger.name_to_value["a7/evc_separate_update_enabled"]), 1.0)
        self.assertGreater(float(model.logger.name_to_value["a7/evc_separate_update_grad_norm_mean"]), 0.0)
        self.assertEqual(float(model.logger.name_to_value["a7/event_credit_delta_align_positive_only"]), 1.0)

    def test_nonfinite_probe_records_a7_projection_credit_stats(self) -> None:
        env = DummyVecEnv([_TinyA6HybridAirCombatEnv])
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
            a7_event_credit_legal_projection_enabled=True,
            a7_event_credit_projection_value_coef=0.5,
            a7_event_credit_projection_delta_align_coef=0.25,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hybrid_action_spec": "air_combat_hybrid_v1",
                "hybrid_event_credit_head_lr_scale": 6.0,
            },
        )
        model.set_logger(configure(format_strings=[]))
        probe = NonFiniteTrainingProbe(
            report_path=f"{gettempdir()}/a7_projection_nonfinite_probe_regression.json",
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

        def _projection_loss(_rollout_data, **_kwargs):
            anchor = next(model.policy.parameters()).sum() * 0.0
            loss = anchor + th.tensor(0.5, device=anchor.device)
            value_loss = anchor + th.tensor(0.3, device=anchor.device)
            delta_loss = anchor + th.tensor(0.2, device=anchor.device)
            return FirstEventCreditLoss(
                loss=loss,
                value_loss=value_loss,
                delta_align_loss=delta_loss,
                unscaled_value_loss=value_loss,
                unscaled_delta_align_loss=delta_loss,
                active_count=4,
                positive_count=2,
                weight_sum=4.0,
                positive_frac=0.5,
                advantage_mean=-0.1,
                advantage_abs_mean=0.1,
                projection_active_count=3,
                projection_candidate_count=4,
                projection_unsupported_count=1,
                projection_advantage_mean=0.75,
                projection_delta_mean=0.25,
                source_shadow_count=4,
                source_deadline_count=2,
                source_early_accepted_count=1,
                source_prewindow_count=5,
                source_legal_open_quality_count=6,
                source_legal_open_quality_positive_count=6,
                source_deadline_positive_count=2,
                source_shadow_positive_count=4,
                source_legal_open_quality_advantage_mean=0.4,
            )

        model._first_event_credit_loss = _projection_loss
        model.train()

        logged = model.logger.name_to_value
        self.assertEqual(float(logged["a7/evc_proj_enabled"]), 1.0)
        self.assertAlmostEqual(float(logged["a7/evc_proj_value_coef"]), 0.5)
        self.assertAlmostEqual(float(logged["a7/evc_proj_delta_coef"]), 0.25)
        self.assertEqual(float(logged["a7/evc_proj_active_count_mean"]), 3.0)
        self.assertEqual(float(logged["a7/evc_proj_candidate_count_mean"]), 4.0)
        self.assertEqual(float(logged["a7/evc_proj_unsupported_count_mean"]), 1.0)
        self.assertAlmostEqual(float(logged["a7/evc_proj_advantage_mean"]), 0.75)
        self.assertAlmostEqual(float(logged["a7/evc_proj_delta_mean"]), 0.25)
        self.assertEqual(float(logged["a7/evc_src_shadow_count_mean"]), 4.0)
        self.assertEqual(float(logged["a7/evc_src_deadline_count_mean"]), 2.0)
        self.assertEqual(float(logged["a7/evc_src_early_count_mean"]), 1.0)
        self.assertEqual(float(logged["a7/evc_src_pre_count_mean"]), 5.0)
        self.assertEqual(float(logged["a7/evc_src_legal_open_quality_count_mean"]), 6.0)
        self.assertEqual(float(logged["a7/evc_src_legal_open_quality_positive_count_mean"]), 6.0)
        self.assertEqual(float(logged["a7/evc_src_deadline_positive_count_mean"]), 2.0)
        self.assertEqual(float(logged["a7/evc_src_shadow_positive_count_mean"]), 4.0)
        self.assertAlmostEqual(float(logged["a7/evc_src_legal_open_quality_advantage_mean"]), 0.4)

    def test_a7_legal_open_quality_credit_aligns_event_logits_without_projection(self) -> None:
        env = DummyVecEnv([_TinyA7LegalOpenHybridAirCombatEnv])
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
            th.full((1,), A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY, dtype=th.long),
        )
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_WINDOW_ID, th.zeros((1,), dtype=th.long))

        credit_loss = model._first_event_credit_loss(_RolloutData)
        self.assertIsNotNone(credit_loss)
        assert credit_loss is not None
        self.assertEqual(credit_loss.source_legal_open_quality_count, 1)
        self.assertEqual(credit_loss.source_legal_open_quality_positive_count, 1)
        self.assertEqual(credit_loss.projection_candidate_count, 0)
        self.assertEqual(credit_loss.projection_active_count, 0)
        self.assertGreater(float(credit_loss.source_legal_open_quality_advantage_mean), 1.0)

        model.policy.optimizer.zero_grad()
        credit_loss.loss.backward()
        event_grad = 0.0
        for param in model.policy.hybrid_event_head.parameters():
            if param.grad is not None:
                event_grad += float(param.grad.detach().abs().sum().cpu().item())
        self.assertGreater(event_grad, 0.0)

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
        self.assertEqual(credit_loss.projection_candidate_count, 1)
        self.assertEqual(credit_loss.projection_active_count, 1)
        self.assertEqual(credit_loss.projection_unsupported_count, 0)
        self.assertEqual(credit_loss.source_shadow_count, 1)
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
