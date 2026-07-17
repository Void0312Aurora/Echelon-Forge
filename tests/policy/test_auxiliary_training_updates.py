from __future__ import annotations

import unittest
from collections import deque
from tempfile import gettempdir
from types import SimpleNamespace

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.first_event_hazard import (
  FIRST_EVENT_FIELD_ACTIVE,
  FIRST_EVENT_FIELD_SOURCE,
  FIRST_EVENT_FIELD_TARGET,
  FIRST_EVENT_FIELD_WEIGHT,
  FIRST_EVENT_FIELD_WINDOW_ID,
  FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
  FIRST_EVENT_SOURCE_SHADOW_QUALITY,
  FirstEventCreditLoss,
  FirstEventHazardLabels,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy, SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO, _WindowClassifierReplay
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv


from tests.support.auxiliary_policy_updates import (
  _FirstEventLabelBuffer,
  _NoopCallback,
  _TinyA6HybridAirCombatEnv,
  _TinyA7ProjectionHybridAirCombatEnv,
  _TinyHMoEEnv,
  _TinyHoldEnv,
  _TinyHybridAirCombatEnv,
  _WarmupSchedule,
)

class AuxiliaryA6TrainingUpdateTests(unittest.TestCase):
  def _make_first_event_label_model(self) -> AdaptiveKLPPO:
    model = object.__new__(AdaptiveKLPPO)
    model.device = th.device("cpu")
    model.first_event_hazard_coef = 0.0
    model.first_event_curriculum_coef = 0.0
    model.first_event_censored_survival_weight = 0.0
    model.first_event_deadline_weight = 0.0
    model.first_event_launch_window_enabled = True
    model.first_event_launch_window_min_window_age_steps = 32
    model.first_event_deadline_min_window_age_steps = 96
    model.first_event_launch_window_prewindow_hold_weight = 0.0
    model.first_event_launch_window_early_accept_weight = 0.0
    model.first_event_curriculum_min_window_age_steps = 32
    model.event_credit_value_coef = 0.5
    model.event_credit_delta_align_coef = 0.0
    model.event_credit_projection_value_coef = 0.0
    model.event_credit_projection_delta_align_coef = 0.0
    model.event_credit_prewindow_hold_weight = 0.25
    model.event_credit_early_accept_weight = 0.75
    model.event_credit_curriculum_coef = 0.0
    model.event_credit_curriculum_min_window_age_steps = 32
    model.event_credit_censored_survival_weight = 0.0
    model.event_credit_deadline_weight = 0.0
    model.event_credit_deadline_min_window_age_steps = 96
    model.event_credit_shadow_quality_weight = 0.5
    model.event_credit_legal_open_quality_weight = 0.0
    model.event_credit_legal_open_quality_min_window_age_steps = 1
    model.event_policy_margin_coef = 0.0
    model.event_policy_margin = 2.0
    model.event_policy_projection_margin_coef = 0.0
    model.event_policy_separate_update_enabled = False
    model.event_policy_separate_update_max_grad_norm = 0.5
    model.event_policy_separate_update_steps = 1
    return model

  def _make_policy_margin_model(
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
      event_credit_value_coef=0.0,
      event_credit_delta_align_coef=0.0,
      event_credit_legal_projection_enabled=True,
      event_credit_positive_mass_cap=1.0,
      event_credit_negative_mass_cap=1.0,
      event_policy_margin_coef=0.35,
      event_policy_margin=2.0,
      event_policy_projection_margin_coef=0.15,
      event_policy_separate_update_enabled=separate_update,
      event_policy_separate_update_max_grad_norm=0.5,
      event_policy_separate_update_steps=1,
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

  def _shadow_projection_rollout_data(self, model: AdaptiveKLPPO, env: DummyVecEnv):
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
      int(FIRST_EVENT_SOURCE_SHADOW_QUALITY),
      dtype=th.long,
      device=model.device,
    )
    window_id = th.zeros((batch_size,), dtype=th.long, device=model.device)
    return SimpleNamespace(
      observations=obs_t,
      **{
        FIRST_EVENT_FIELD_ACTIVE: active,
        FIRST_EVENT_FIELD_TARGET: target,
        FIRST_EVENT_FIELD_WEIGHT: weight,
        FIRST_EVENT_FIELD_SOURCE: source,
        FIRST_EVENT_FIELD_WINDOW_ID: window_id,
      },
    )

  def test_policy_fire_mask_uses_c2_roe_mission_window(self) -> None:
    mission = th.zeros((2, 20), dtype=th.float32)
    mission[:, 5] = 2.0
    mission[:, 6] = 1.0
    mission[:, 14] = 2.0
    mission[:, 15] = 1.0
    mission[:, 16] = 1.0
    mission[:, 19] = 1.0
    mission[1, 17] = 1.0

    mask = AdaptiveKLPPO._first_event_policy_fire_mask_from_obs({"mission": mission}, 2)

    self.assertEqual(mask, [True, False])

  def test_policy_fire_mask_uses_c2_roe_v2_quality_window_support(self) -> None:
    mode = "air_combat_c2_roe_v2"
    mission = th.zeros((3, mission_observation_dim(mode)), dtype=th.float32)
    mission[0, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
    mission[0, mission_observation_field_index(mode, "quality_window_ready")] = 0.0
    mission[1, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
    mission[1, mission_observation_field_index(mode, "quality_window_ready")] = 1.0

    event_action_mask = th.tensor([[1.0, 1.0], [1.0, 0.0], [1.0, 1.0]], dtype=th.float32)

    mask = AdaptiveKLPPO._first_event_policy_fire_mask_from_obs(
      {"mission": mission, "event_action_mask": event_action_mask},
      3,
    )

    self.assertEqual(mask, [False, True, False])

  def test_launch_window_uses_contact_range_and_track_age_from_policy_obs(self) -> None:
    contacts = th.zeros((2, 10, 5), dtype=th.float32)
    contacts[0, 0, 0] = 15000.0
    contacts[0, 0, 4] = 0.5
    contacts[1, 0, 0] = 42000.0
    contacts[1, 0, 4] = 0.5

    launch_window = AdaptiveKLPPO._first_event_policy_launch_window_from_obs(
      {"contacts": contacts},
      2,
      min_range_m=8000.0,
      max_range_m=30000.0,
      max_track_age_s=2.0,
    )

    self.assertEqual(launch_window, [True, False])

  def test_launch_window_uses_c2_roe_v2_explicit_state_completion(self) -> None:
    mode = "air_combat_c2_roe_v2"
    mission = th.zeros((2, mission_observation_dim(mode)), dtype=th.float32)
    mission[0, mission_observation_field_index(mode, "launch_window_open")] = 1.0
    contacts = th.zeros((2, 10, 5), dtype=th.float32)
    contacts[:, 0, 0] = 45000.0
    contacts[:, 0, 4] = 0.5

    launch_window = AdaptiveKLPPO._first_event_policy_launch_window_from_obs(
      {"mission": mission, "contacts": contacts},
      2,
      min_range_m=8000.0,
      max_range_m=30000.0,
      max_track_age_s=2.0,
    )

    self.assertEqual(launch_window, [True, False])

  def test_launch_window_prefers_latest_contacts_history_frame(self) -> None:
    contacts_history = th.zeros((2, 3, 10, 5), dtype=th.float32)
    contacts_history[0, 0, 0, 0] = 14000.0
    contacts_history[0, 0, 0, 4] = 0.2
    contacts_history[0, 2, 0, 0] = 42000.0
    contacts_history[0, 2, 0, 4] = 0.2
    contacts_history[1, 2, 0, 0] = 18000.0
    contacts_history[1, 2, 0, 4] = 3.5

    launch_window = AdaptiveKLPPO._first_event_policy_launch_window_from_obs(
      {"contacts_history": contacts_history},
      2,
      min_range_m=8000.0,
      max_range_m=30000.0,
      max_track_age_s=2.0,
    )

    self.assertEqual(launch_window, [False, False])

  def test_cross_rollout_first_event_state_recovers_shadow_quality_after_boundary(self) -> None:
    model = self._make_first_event_label_model()
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

    full_labels = model._build_first_event_labels_from_rollout_infos(
      engagement_state=engagement_state,
      fire_mask=fire_mask,
      fire_once_accepted=fire_once_accepted,
      episode_id=episode_id,
      launch_window_open=launch_window_open,
    )
    full_shadow_positive = (
      (full_labels.source == FIRST_EVENT_SOURCE_SHADOW_QUALITY)
      & (full_labels.target > 0.5)
      & full_labels.active
    )
    self.assertEqual(int(full_shadow_positive.sum().item()), episode_len - launch_open_start)

    local_shadow_positive_count = 0
    for start in range(0, episode_len, chunk_size):
      end = min(start + chunk_size, episode_len)
      local_labels = model._build_first_event_labels_from_rollout_infos(
        engagement_state=engagement_state[start:end],
        fire_mask=fire_mask[start:end],
        fire_once_accepted=fire_once_accepted[start:end],
        episode_id=episode_id[start:end],
        launch_window_open=launch_window_open[start:end],
      )
      local_shadow_positive_count += int(
        (
          (local_labels.source == FIRST_EVENT_SOURCE_SHADOW_QUALITY)
          & (local_labels.target > 0.5)
          & local_labels.active
        ).sum().item()
      )
    self.assertEqual(local_shadow_positive_count, 0)

    chunked_labels: list[FirstEventHazardLabels] = []
    for start in range(0, episode_len, chunk_size):
      end = min(start + chunk_size, episode_len)
      buffer = _FirstEventLabelBuffer(buffer_size=end - start)
      model._attach_first_event_labels_to_rollout_buffer(
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
    self.assertEqual(int(model._cross_rollout_last_carried_shadow_pending_envs), 1)
    self.assertEqual(int(model._cross_rollout_last_carried_shadow_positive_count), chunk_size)
    self.assertEqual(int(model._cross_rollout_last_first_event_count), chunk_size)

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

    model.policy.forward = wrapped_forward # type: ignore[method-assign]
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

  def test_first_event_labels_are_attached_to_rollout_minibatches(self) -> None:
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
      first_event_hazard_coef=0.2,
      first_event_curriculum_coef=0.5,
      first_event_curriculum_min_window_age_steps=2,
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
    self.assertTrue(hasattr(rollout_data, FIRST_EVENT_FIELD_ACTIVE))
    self.assertTrue(hasattr(rollout_data, FIRST_EVENT_FIELD_TARGET))
    self.assertEqual(int(getattr(rollout_data, FIRST_EVENT_FIELD_ACTIVE).sum().item()), 2)
    self.assertEqual(int((getattr(rollout_data, FIRST_EVENT_FIELD_TARGET) > 0.5).sum().item()), 1)

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
    self.assertEqual(int(getattr(second_rollout_data, FIRST_EVENT_FIELD_ACTIVE).sum().item()), 0)



if __name__ == "__main__":
  unittest.main()
