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
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy, SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO, _WindowClassifierReplay
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv


from tests.support.auxiliary_policy_updates import (
  _NoopCallback,
  _TinyA6HybridAirCombatEnv,
  _TinyA7ProjectionHybridAirCombatEnv,
  _TinyM3S1HybridAirCombatEnv,
  _WarmupSchedule,
)

class AuxiliaryA7EventCreditUpdateTests(unittest.TestCase):
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

  def test_event_credit_only_collects_labels_and_updates_credit_head(self) -> None:
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
      event_credit_value_coef=0.5,
      event_credit_curriculum_coef=0.5,
      event_credit_curriculum_min_window_age_steps=1,
      event_credit_separate_update_enabled=True,
      event_credit_separate_update_max_grad_norm=0.5,
      event_credit_delta_align_positive_only=True,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_credit_head_lr_scale": 6.0,
      },
    )
    self.assertFalse(model._first_event_enabled())
    self.assertTrue(model._event_credit_enabled())
    self.assertTrue(getattr(model.rollout_buffer, "supports_first_event_labels", False))
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
    self.assertEqual(int(getattr(rollout_data, FIRST_EVENT_FIELD_ACTIVE).sum().item()), 1)
    self.assertEqual(int((getattr(rollout_data, FIRST_EVENT_FIELD_TARGET) > 0.5).sum().item()), 1)

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

  def test_sidecar_preserves_closed_mask_rows(self) -> None:
    model = object.__new__(AdaptiveKLPPO)
    model.grouped_stopping_coef = 1.0
    model.first_event_launch_window_min_window_age_steps = 1
    buffer = SimpleNamespace(
      n_envs=1,
      observations={
        "mission": np.zeros((3, 1, 21), dtype=np.float32),
      },
    )

    sidecar = model._build_grouped_stopping_sidecar(
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
    violation_sidecar = model._build_grouped_stopping_sidecar(
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

  def test_grouped_stopping_auxiliary_updates_from_complete_sidecar_group(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      grouped_stopping_coef=1.0,
      grouped_stopping_early_mass_coef=0.5,
      grouped_stopping_early_mass_budget=0.05,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "stopping_head_lr_scale": 5.0,
      },
    )
    model.set_logger(configure(format_strings=[]))
    assert model.policy.stopping_head is not None
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
    sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(sidecar)
    assert sidecar is not None
    self.assertEqual(len(sidecar.groups), 1)
    self.assertEqual(sidecar.groups[0].row_indices, (0, 1, 2, 3))
    self.assertEqual(sidecar.groups[0].quality_mask, (False, False, True, True))

    before = model.policy.stopping_head.bias.detach().clone()
    model.train()
    after = model.policy.stopping_head.bias.detach().clone()

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

  def test_event_window_auxiliary_updates_executable_event_policy_path(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      event_window_coef=1.0,
      event_window_early_mass_coef=0.5,
      event_window_early_mass_budget=0.05,
      event_window_delay_coef=0.25,
      event_window_deadline_coef=0.25,
      event_window_deadline_steps=2,
      event_window_quality_boundary_coef=1.0,
      event_window_quality_boundary_logit=0.0,
      event_window_contrastive_margin_coef=1.0,
      event_window_contrastive_margin=1.5,
      event_window_separate_update_enabled=True,
      event_window_dedicated_optimizer_enabled=True,
      event_window_separate_update_steps=2,
      event_window_max_grad_norm=2.0,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_head_lr_scale": 10.0,
        "hybrid_event_credit_head_lr_scale": 6.0,
        "stopping_head_lr_scale": 5.0,
      },
    )
    model.set_logger(configure(format_strings=[]))
    self.assertFalse(model._grouped_stopping_enabled())
    self.assertTrue(model._event_window_enabled())
    self.assertTrue(model._first_event_label_collection_enabled())
    assert model.policy.hybrid_event_head is not None
    assert model.policy.hybrid_event_credit_head is not None
    assert model.policy.stopping_head is not None

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
    sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(sidecar)
    assert sidecar is not None
    self.assertEqual(len(sidecar.groups), 1)
    self.assertEqual(sidecar.groups[0].quality_mask, (False, False, True, True))

    before = {
      name: param.detach().clone()
      for name, param in model.policy.named_parameters()
    }
    event_window_loss = model._event_window_auxiliary_update()

    self.assertIsNotNone(event_window_loss)
    assert event_window_loss is not None
    self.assertEqual(event_window_loss.stats.window_group_count, 1)
    self.assertGreater(float(event_window_loss.loss.detach().cpu().item()), 0.0)
    self.assertGreater(float(model._last_event_window_grad_norm), 0.0)
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

  def test_event_window_can_train_dedicated_stopping_head_adapter(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      event_window_coef=1.0,
      event_window_early_mass_coef=0.5,
      event_window_early_mass_budget=0.05,
      event_window_quality_boundary_coef=1.0,
      event_window_quality_boundary_logit=0.0,
      event_window_contrastive_margin_coef=1.0,
      event_window_contrastive_margin=1.5,
      event_window_balanced_bce_coef=2.0,
      event_window_use_stopping_head=True,
      event_window_separate_update_enabled=True,
      event_window_dedicated_optimizer_enabled=True,
      event_window_separate_update_steps=2,
      event_window_max_grad_norm=2.0,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_use_stopping_head": True,
        "stopping_head_lr_scale": 5.0,
      },
    )
    model.set_logger(configure(format_strings=[]))
    assert model.policy.stopping_head is not None

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
    event_window_loss = model._event_window_auxiliary_update()

    self.assertIsNotNone(event_window_loss)
    assert event_window_loss is not None
    self.assertEqual(event_window_loss.stats.window_group_count, 1)
    self.assertGreater(float(model._last_event_window_grad_norm), 0.0)
    self.assertGreaterEqual(float(event_window_loss.stats.mean_window_balanced_bce_loss), 0.0)

    selected_changed = False
    for name, param in model.policy.named_parameters():
      changed = not th.allclose(before[name], param.detach())
      if name.startswith("stopping_head."):
        selected_changed = selected_changed or changed
      else:
        self.assertFalse(changed, name)
    self.assertTrue(selected_changed)

  def test_window_classifier_auxiliary_update_separates_quality_window_logits(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      window_classifier_coef=2.0,
      window_classifier_prewindow_logit_ceiling_coef=1.0,
      window_classifier_prewindow_logit_ceiling=-1.0,
      window_classifier_quality_logit_floor_coef=1.0,
      window_classifier_quality_logit_floor=1.0,
      window_classifier_detach_latent=True,
      window_classifier_separate_update_enabled=True,
      window_classifier_dedicated_optimizer_enabled=True,
      window_classifier_separate_update_steps=8,
      window_classifier_max_grad_norm=5.0,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_use_window_classifier_head": True,
        "window_classifier_head_lr_scale": 20.0,
        "window_classifier_head_norm_enabled": True,
      },
    )
    model.set_logger(configure(format_strings=[]))
    self.assertTrue(model._window_classifier_enabled())
    self.assertTrue(model._grouped_stopping_sidecar_enabled())
    self.assertTrue(model._first_event_label_collection_enabled())
    assert model.policy.window_classifier_head is not None

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
    sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(sidecar)
    assert sidecar is not None
    self.assertEqual(len(sidecar.groups), 1)
    self.assertEqual(sidecar.groups[0].quality_mask, (False, False, True, True))

    before_loss = model._window_classifier_loss_from_sidecar()
    self.assertIsNotNone(before_loss)
    assert before_loss is not None
    self.assertEqual(before_loss.positive_count, 2)
    self.assertEqual(before_loss.negative_count, 2)
    self.assertAlmostEqual(float(before_loss.positive_prob_mean), 0.5, places=6)
    self.assertAlmostEqual(float(before_loss.negative_prob_mean), 0.5, places=6)

    before = {
      name: param.detach().clone()
      for name, param in model.policy.named_parameters()
    }
    classifier_loss = model._window_classifier_auxiliary_update()

    self.assertIsNotNone(classifier_loss)
    assert classifier_loss is not None
    self.assertGreater(float(model._last_window_classifier_grad_norm), 0.0)
    self.assertEqual(classifier_loss.positive_count, 2)
    self.assertEqual(classifier_loss.negative_count, 2)

    after_loss = model._window_classifier_loss_from_sidecar()
    self.assertIsNotNone(after_loss)
    assert after_loss is not None
    self.assertGreater(after_loss.positive_logit_mean, after_loss.negative_logit_mean)
    self.assertGreater(after_loss.positive_prob_mean, after_loss.negative_prob_mean)

    selected_changed = False
    for name, param in model.policy.named_parameters():
      changed = not th.allclose(before[name], param.detach())
      if name.startswith("window_classifier_"):
        selected_changed = selected_changed or changed
      else:
        self.assertFalse(changed, name)
    self.assertTrue(selected_changed)

  def test_window_classifier_replay_balances_single_class_rollouts(self) -> None:
    env = DummyVecEnv([_TinyM3S1HybridAirCombatEnv])
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      window_classifier_coef=2.0,
      window_classifier_prewindow_logit_ceiling_coef=1.0,
      window_classifier_prewindow_logit_ceiling=-1.0,
      window_classifier_quality_logit_floor_coef=1.0,
      window_classifier_quality_logit_floor=1.0,
      window_classifier_detach_latent=True,
      window_classifier_separate_update_enabled=True,
      window_classifier_dedicated_optimizer_enabled=True,
      window_classifier_separate_update_steps=32,
      window_classifier_max_grad_norm=5.0,
      window_classifier_replay_enabled=True,
      window_classifier_replay_storage="observation",
      window_classifier_replay_capacity=16,
      window_classifier_replay_batch_size=16,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_use_window_classifier_head": True,
        "window_classifier_head_lr_scale": 50.0,
        "window_classifier_head_norm_enabled": True,
      },
    )
    model.set_logger(configure(format_strings=[]))
    assert model.policy.window_classifier_head is not None

    model._last_obs = env.reset()
    model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
    model.ep_info_buffer = deque(maxlen=model._stats_window_size)
    model.ep_success_buffer = deque(maxlen=model._stats_window_size)
    callback = _NoopCallback()
    callback.init_callback(model)

    ok = model.collect_rollouts(env, callback, model.rollout_buffer, n_rollout_steps=model.n_steps)
    self.assertTrue(ok)
    first_sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(first_sidecar)
    assert first_sidecar is not None
    self.assertEqual(first_sidecar.groups[0].quality_mask, (False, False))
    first_loss = model._window_classifier_auxiliary_update()
    self.assertIsNotNone(first_loss)
    assert first_loss is not None
    self.assertTrue(first_loss.replay_enabled)
    self.assertFalse(first_loss.replay_used)
    self.assertEqual(first_loss.replay_positive_count, 0)
    self.assertEqual(first_loss.replay_negative_count, 2)

    ok = model.collect_rollouts(env, callback, model.rollout_buffer, n_rollout_steps=model.n_steps)
    self.assertTrue(ok)
    second_sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(second_sidecar)
    assert second_sidecar is not None
    self.assertEqual(second_sidecar.groups[0].quality_mask, (True, True))
    second_loss = model._window_classifier_auxiliary_update()

    self.assertIsNotNone(second_loss)
    assert second_loss is not None
    self.assertTrue(second_loss.replay_used)
    self.assertEqual(second_loss.positive_count, second_loss.negative_count)
    self.assertEqual(second_loss.replay_positive_count, 2)
    self.assertEqual(second_loss.replay_negative_count, 2)
    self.assertGreater(second_loss.positive_logit_mean, second_loss.negative_logit_mean)
    self.assertGreater(float(model._last_window_classifier_grad_norm), 0.0)

  def test_window_classifier_replay_calibration_is_latest_balanced_population(self) -> None:
    replay = _WindowClassifierReplay(capacity=8, storage="latent")
    latents = th.arange(15, dtype=th.float32).reshape(5, 3)
    labels = th.tensor([1.0, 1.0, 1.0, 0.0, 0.0], dtype=th.float32)

    replay.append(latents, labels)
    sampled = replay.calibration_balanced(
      max_rows=4,
      device=th.device("cpu"),
      dtype=th.float32,
    )

    self.assertIsNotNone(sampled)
    assert sampled is not None
    calibration_latents, calibration_labels = sampled
    self.assertTrue(th.is_tensor(calibration_latents))
    self.assertTrue(
      th.allclose(
        calibration_latents,
        th.cat((latents[1:3], latents[3:5]), dim=0),
      )
    )
    self.assertTrue(
      th.allclose(
        calibration_labels,
        th.tensor([1.0, 1.0, 0.0, 0.0], dtype=th.float32),
      )
    )

  def test_support_preserving_collect_masks_until_quality_ready(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_window_age_steps=3,
      event_window_coef=1.0,
      event_window_support_preserving_collect_enabled=True,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hybrid_event_head_lr_scale": 10.0,
      },
    )

    first = model._support_preserving_collect_masks(
      fire_mask=[True],
      launch_window_open=[False],
      n_envs=1,
    )
    second = model._support_preserving_collect_masks(
      fire_mask=[True],
      launch_window_open=[True],
      n_envs=1,
    )
    third = model._support_preserving_collect_masks(
      fire_mask=[True],
      launch_window_open=[True],
      n_envs=1,
    )

    self.assertEqual(first, [True])
    self.assertEqual(second, [True])
    self.assertEqual(third, [False])
    self.assertEqual(model._support_preserving_collect_hold_count, 2)
    self.assertEqual(model._support_preserving_collect_candidate_count, 3)
    self.assertEqual(model._support_preserving_collect_quality_count, 1)

    model.event_window_support_preserving_hold_quality_enabled = True
    fourth = model._support_preserving_collect_masks(
      fire_mask=[True],
      launch_window_open=[True],
      n_envs=1,
    )
    self.assertEqual(fourth, [True])
    self.assertEqual(model._support_preserving_collect_hold_count, 3)
    self.assertEqual(model._support_preserving_collect_quality_count, 2)

  def test_nonfinite_probe_preserves_grouped_stopping_training_path(self) -> None:
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
      first_event_launch_window_enabled=True,
      first_event_launch_window_min_range_m=1.0,
      first_event_launch_window_max_range_m=2000.0,
      first_event_launch_window_max_track_age_s=10.0,
      grouped_stopping_coef=1.0,
      grouped_stopping_early_mass_coef=0.5,
      grouped_stopping_early_mass_budget=0.05,
      policy_kwargs={
        "net_arch": {"pi": [32], "vf": [32]},
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "stopping_head_lr_scale": 5.0,
      },
    )
    model.set_logger(configure(format_strings=[]))
    probe = NonFiniteTrainingProbe(
      report_path=f"{gettempdir()}/grouped_stopping_nonfinite_probe_regression.json",
      history_limit=32,
      enabled=True,
    )
    probe.install(model)
    assert model.policy.stopping_head is not None
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
    sidecar = getattr(model, "_grouped_stopping_sidecar", None)
    self.assertIsNotNone(sidecar)
    assert sidecar is not None
    self.assertEqual(len(sidecar.groups), 1)

    before = model.policy.stopping_head.bias.detach().clone()
    model.train()
    after = model.policy.stopping_head.bias.detach().clone()

    self.assertFalse(th.allclose(before, after))
    logged = model.logger.name_to_value
    self.assertEqual(float(logged["m3s1/grouped_sidecar_group_count"]), 1.0)
    self.assertEqual(float(logged["m3s1/grouped_active_group_count"]), 1.0)
    self.assertGreater(float(logged["m3s1/grouped_stopping_loss"]), 0.0)
    self.assertGreater(float(logged["m3s1/grouped_stopping_grad_norm"]), 0.0)
    self.assertEqual(float(logged["m3s1/grouped_labels_reached_loss"]), 1.0)
    self.assertEqual(float(logged["m3s1/stop_logit_count"]), 4.0)



if __name__ == "__main__":
  unittest.main()
