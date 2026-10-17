from __future__ import annotations

from types import SimpleNamespace

import torch as th
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv

from python.rl.policy_algo.first_event_hazard import (
  FIRST_EVENT_FIELD_ACTIVE,
  FIRST_EVENT_FIELD_SOURCE,
  FIRST_EVENT_FIELD_TARGET,
  FIRST_EVENT_FIELD_WEIGHT,
  FIRST_EVENT_FIELD_WINDOW_ID,
  FIRST_EVENT_SOURCE_SHADOW_QUALITY,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from tests.support.auxiliary_policy_updates import _TinyA7ProjectionHybridAirCombatEnv, _WarmupSchedule

def _make_first_event_label_model() -> AdaptiveKLPPO:
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

def _shadow_projection_rollout_data(model: AdaptiveKLPPO, env: DummyVecEnv):
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
