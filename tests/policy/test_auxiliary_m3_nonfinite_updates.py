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
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO, _M3S2WindowClassifierReplay
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


class AuxiliaryM3NonfiniteUpdateTests(unittest.TestCase):
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

  def test_m3s2_fire_boundary_update_only_writes_executable_event_head(self) -> None:
    env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
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
      a6_first_event_launch_window_enabled=True,
      a6_first_event_launch_window_min_range_m=1.0,
      a6_first_event_launch_window_max_range_m=2000.0,
      a6_first_event_launch_window_max_track_age_s=10.0,
      m3s2_fire_boundary_coef=20.0,
      m3s2_fire_boundary_negative_logit_ceiling_coef=4.0,
      m3s2_fire_boundary_negative_logit_ceiling=-1.0,
      m3s2_fire_boundary_positive_logit_floor_coef=4.0,
      m3s2_fire_boundary_positive_logit_floor=1.0,
      m3s2_fire_boundary_separate_update_enabled=True,
      m3s2_fire_boundary_dedicated_optimizer_enabled=True,
      m3s2_fire_boundary_separate_update_steps=96,
      m3s2_fire_boundary_max_grad_norm=10.0,
      m3s2_fire_boundary_support_preserving_collect_enabled=True,
      m3s2_fire_boundary_support_preserving_hold_quality_enabled=True,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_head_lr_scale": 10.0,
        "hybrid_event_use_m3_stopping_head": False,
        "hybrid_event_use_m3_window_classifier_head": False,
      },
    )
    model.set_logger(configure(format_strings=[]))
    assert model.policy.hybrid_event_head is not None
    with th.no_grad():
      model.policy.action_net.weight.zero_()
      model.policy.action_net.bias.zero_()
      model.policy.action_net.bias[9] = -2.0
      model.policy.action_net.bias[11] = 0.0

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
    group = sidecar.groups[0]
    self.assertEqual(tuple(group.quality_mask), (False, False, True, True))
    self.assertEqual(tuple(group.accepted_event), (False, False, False, False))

    obs = model._m3s1_observations_for_group(sidecar, group)
    with th.no_grad():
      before_delta = model.policy.get_distribution(obs).fire_event_logit_delta()
    self.assertIsNotNone(before_delta)
    assert before_delta is not None
    self.assertTrue(th.allclose(before_delta, th.full_like(before_delta, -2.0)))
    before_params = {
      name: param.detach().clone()
      for name, param in model.policy.named_parameters()
    }

    original_get_distribution = model.policy.get_distribution

    def _fail_get_distribution(_obs):
      raise AssertionError("M3-S2 event-head-only fire boundary update should not build full distributions")

    object.__setattr__(model.policy, "get_distribution", _fail_get_distribution)
    try:
      fire_boundary_loss = model._m3s2_fire_boundary_auxiliary_update()
    finally:
      object.__setattr__(model.policy, "get_distribution", original_get_distribution)

    self.assertIsNotNone(fire_boundary_loss)
    assert fire_boundary_loss is not None
    self.assertEqual(fire_boundary_loss.positive_count, 2)
    self.assertEqual(fire_boundary_loss.negative_count, 2)
    self.assertGreater(float(model._m3s2_last_fire_boundary_grad_norm), 0.0)
    self.assertGreater(fire_boundary_loss.executable_positive_logit_mean, 0.0)
    self.assertLess(fire_boundary_loss.executable_negative_logit_mean, 0.0)
    with th.no_grad():
      after_dist = model.policy.get_distribution(obs)
      after_delta = after_dist.fire_event_logit_delta()
      after_actions = after_dist.mode()
    self.assertIsNotNone(after_delta)
    assert after_delta is not None
    self.assertTrue(th.all(after_delta[2:] > 0.0), after_delta)
    self.assertTrue(th.all(after_delta[:2] < 0.0), after_delta)
    self.assertTrue(th.all(after_actions[2:, 9] > 0.5))
    self.assertTrue(th.all(after_actions[:2, 9] < 0.5))

    event_head_changed = False
    for name, param in model.policy.named_parameters():
      changed = not th.allclose(before_params[name], param.detach())
      if name.startswith("hybrid_event_head."):
        event_head_changed = event_head_changed or changed
      else:
        self.assertFalse(changed, name)
    self.assertTrue(event_head_changed)

  def test_nonfinite_probe_traced_train_runs_m3s2_fire_boundary_update(self) -> None:
    env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
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
      a6_first_event_launch_window_enabled=True,
      a6_first_event_launch_window_min_range_m=1.0,
      a6_first_event_launch_window_max_range_m=2000.0,
      a6_first_event_launch_window_max_track_age_s=10.0,
      m3s2_fire_boundary_coef=20.0,
      m3s2_fire_boundary_negative_logit_ceiling_coef=4.0,
      m3s2_fire_boundary_negative_logit_ceiling=-1.0,
      m3s2_fire_boundary_positive_logit_floor_coef=4.0,
      m3s2_fire_boundary_positive_logit_floor=1.0,
      m3s2_fire_boundary_separate_update_enabled=True,
      m3s2_fire_boundary_dedicated_optimizer_enabled=True,
      m3s2_fire_boundary_separate_update_steps=4,
      m3s2_fire_boundary_max_grad_norm=10.0,
      m3s2_fire_boundary_support_preserving_collect_enabled=True,
      m3s2_fire_boundary_support_preserving_hold_quality_enabled=True,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_head_lr_scale": 10.0,
        "hybrid_event_use_m3_stopping_head": False,
        "hybrid_event_use_m3_window_classifier_head": False,
      },
    )
    model.set_logger(configure(format_strings=[]))
    probe = NonFiniteTrainingProbe(
      report_path=f"{gettempdir()}/m3s2_fire_boundary_probe_test.json",
      history_limit=64,
    )
    probe.install(model)
    assert model.policy.hybrid_event_head is not None
    with th.no_grad():
      model.policy.action_net.weight.zero_()
      model.policy.action_net.bias.zero_()
      model.policy.action_net.bias[9] = -2.0
      model.policy.action_net.bias[11] = 0.0

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

    fire_boundary_loss = getattr(model, "_m3s2_last_fire_boundary_loss", None)
    self.assertIsNotNone(fire_boundary_loss)
    assert fire_boundary_loss is not None
    self.assertEqual(fire_boundary_loss.positive_count, 2)
    self.assertEqual(fire_boundary_loss.negative_count, 2)
    self.assertGreater(float(model._m3s2_last_fire_boundary_grad_norm), 0.0)
    logged = model.logger.name_to_value
    self.assertEqual(float(logged["m3s2/fb_coef"]), 20.0)
    self.assertEqual(float(logged["m3s2/fb_active_count"]), 4.0)
    self.assertEqual(float(logged["m3s2/fb_positive_count"]), 2.0)
    self.assertEqual(float(logged["m3s2/fb_negative_count"]), 2.0)
    self.assertGreater(float(logged["m3s2/fb_grad_norm"]), 0.0)

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