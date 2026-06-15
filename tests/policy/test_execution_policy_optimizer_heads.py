from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.models.transformer import (
  TemporalTransformerExtractor,
  TransformerExtractor,
  preprocess_mission_tensor,
  preprocess_transformer_observations,
)
from gym_envs.universal_env_parts import make_action_space
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.policies import (
  HierarchicalMoEExecutionPolicy,
  SquashedMultiInputPolicy,
  _HybridActionDistribution,
  _normalize_hybrid_action_layout,
)
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
from train import apply_safe_action_bias


class _ConstantSchedule:
  def __call__(self, progress_remaining: float) -> float:
    return 3.0e-4


class ExecutionPolicyOptimizerHeadTests(unittest.TestCase):
  def _make_air_combat_hybrid_distribution(
    self,
    params: th.Tensor,
    *,
    fire_mask: th.Tensor | None = None,
  ) -> _HybridActionDistribution:
    action_space = make_action_space("air_combat_hybrid_v1")
    layout = _normalize_hybrid_action_layout("air_combat_hybrid_v1", action_space)
    assert layout is not None
    return _HybridActionDistribution(
      layout=layout,
      params=params,
      log_std=th.zeros((6,), dtype=params.dtype, device=params.device),
      action_low=action_space.low,
      action_high=action_space.high,
      fire_event_mask=fire_mask,
    )

  def _make_policy(self) -> HierarchicalMoEExecutionPolicy:
    observation_space = spaces.Dict(
      {
        "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=float),
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
        "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
      }
    )
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float)
    return HierarchicalMoEExecutionPolicy(
      observation_space,
      action_space,
      _ConstantSchedule(),
      net_arch={"pi": [32], "vf": [32]},
    )

  def _make_air_combat_hybrid_observation_space(self, mission_dim: int = 20) -> spaces.Dict:
    return spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
        "event_action_mask": spaces.Box(low=0.0, high=1.0, shape=(2,), dtype=float),
      }
    )

  def _make_air_combat_hybrid_policy(self, **policy_kwargs) -> HierarchicalMoEExecutionPolicy:
    return HierarchicalMoEExecutionPolicy(
      self._make_air_combat_hybrid_observation_space(),
      make_action_space("air_combat_hybrid_v1"),
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
      hybrid_action_spec="air_combat_hybrid_v1",
      **policy_kwargs,
    )

  def _make_authorized_fire_obs(self, batch_size: int) -> dict[str, th.Tensor]:
    mission = th.zeros((batch_size, 20), dtype=th.float32)
    mission[:, 5] = 2.0
    mission[:, 6] = 1.0
    mission[:, 14] = 2.0
    mission[:, 15] = 1.0
    mission[:, 16] = 1.0
    mission[:, 19] = 1.0
    return {
      "instruments": th.zeros((batch_size, 42), dtype=th.float32),
      "contacts": th.zeros((batch_size, 10, 5), dtype=th.float32),
      "rwr": th.zeros((batch_size, 4, 4), dtype=th.float32),
      "mission": mission,
      "proprio": th.zeros((batch_size, 12), dtype=th.float32),
    }

  def test_optimizer_includes_hmoe_head_parameters(self) -> None:
    policy = self._make_policy()
    head_param_ids = {id(param) for param in policy.hmoe_head_bank.parameters()}
    optimizer_param_ids = {
      id(param)
      for group in policy.optimizer.param_groups
      for param in group.get("params", [])
    }
    self.assertTrue(head_param_ids)
    self.assertTrue(head_param_ids.issubset(optimizer_param_ids))

  def test_optimizer_uses_lower_lr_for_hmoe_heads(self) -> None:
    policy = self._make_policy()
    self.assertEqual(len(policy.optimizer.param_groups), 2)
    shared_group, hmoe_group = policy.optimizer.param_groups
    self.assertEqual(shared_group.get("name"), "shared")
    self.assertEqual(hmoe_group.get("name"), "hmoe")
    self.assertAlmostEqual(float(shared_group.get("lr_scale", 0.0)), 1.0, places=6)
    self.assertAlmostEqual(float(hmoe_group.get("lr_scale", 0.0)), 0.35, places=6)
    self.assertAlmostEqual(float(shared_group["lr"]), 3.0e-4, places=10)
    self.assertAlmostEqual(float(hmoe_group["lr"]), 3.0e-4 * 0.35, places=10)

  def test_hybrid_event_head_gets_dedicated_optimizer_lane(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
      }
    )
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      make_action_space("air_combat_hybrid_v1"),
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
      hybrid_action_spec="air_combat_hybrid_v1",
      hybrid_event_head_lr_scale=8.0,
    )

    self.assertIsNotNone(policy.hybrid_event_head)
    assert policy.hybrid_event_head is not None
    self.assertTrue(th.allclose(policy.hybrid_event_head.weight.detach(), th.zeros_like(policy.hybrid_event_head.weight)))
    self.assertTrue(th.allclose(policy.hybrid_event_head.bias.detach(), th.zeros_like(policy.hybrid_event_head.bias)))
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hybrid_event_head", "hmoe"])
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 8.0, places=6)
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 8.0, places=10)

    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -5.0
      policy.action_net.bias[11] = 0.0
    obs = {
      "instruments": th.zeros((2, 42), dtype=th.float32),
      "contacts": th.zeros((2, 10, 5), dtype=th.float32),
      "rwr": th.zeros((2, 4, 4), dtype=th.float32),
      "mission": th.zeros((2, 20), dtype=th.float32),
      "proprio": th.zeros((2, 12), dtype=th.float32),
    }
    obs["mission"][:, 5] = 2.0
    obs["mission"][:, 6] = 1.0
    obs["mission"][:, 14] = 2.0
    obs["mission"][:, 15] = 1.0
    obs["mission"][:, 16] = 1.0
    obs["mission"][:, 19] = 1.0

    with th.no_grad():
      delta = policy.get_distribution(obs).fire_event_logit_delta()

    self.assertIsNotNone(delta)
    assert delta is not None
    self.assertTrue(th.allclose(delta, th.full_like(delta, -5.0)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["a6/event_head_delta_abs_mean"]), 0.0, places=6)

  def test_hybrid_event_head_is_executable_when_m3_adapters_are_disabled(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      hybrid_event_use_m3_stopping_head=False,
      hybrid_event_use_m3_window_classifier_head=False,
    )
    assert policy.hybrid_event_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -5.0
      policy.action_net.bias[11] = 0.0
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.copy_(th.tensor([0.0, 6.0], dtype=th.float32))

    obs = self._make_authorized_fire_obs(batch_size=2)
    with th.no_grad():
      direct_delta = policy.get_hybrid_event_head_delta(obs)
      distribution = policy.get_distribution(obs)
      executable_delta = distribution.fire_event_logit_delta()
      actions = distribution.mode()

    self.assertIsNotNone(direct_delta)
    self.assertIsNotNone(executable_delta)
    assert direct_delta is not None
    assert executable_delta is not None
    self.assertTrue(th.allclose(direct_delta, th.full_like(direct_delta, 6.0)))
    self.assertTrue(th.allclose(executable_delta, th.full_like(executable_delta, 1.0)))
    self.assertTrue(th.all(actions[:, 9] > 0.5))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s2/event_adapter_enabled"]), 0.0)
    self.assertEqual(float(stats["m3s2/window_classifier_event_adapter_enabled"]), 0.0)

  def test_hybrid_event_credit_head_is_disabled_by_default(self) -> None:
    policy = self._make_air_combat_hybrid_policy()

    self.assertIsNone(policy.hybrid_event_credit_head)
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hmoe"])
    self.assertAlmostEqual(
      float(policy._get_constructor_parameters().get("hybrid_event_credit_head_lr_scale", -1.0)),
      0.0,
      places=6,
    )
    obs = self._make_authorized_fire_obs(batch_size=2)

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      credit = policy.get_hybrid_event_credit(obs)
      q_values = distribution.fire_event_q_values()
      advantage = distribution.fire_event_advantage()

    self.assertIsNone(credit)
    self.assertIsNone(q_values)
    self.assertIsNone(advantage)
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 0.0)
    self.assertAlmostEqual(float(stats["a7/event_credit_head_lr_scale"]), 0.0, places=6)

  def test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
      }
    )
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      make_action_space("air_combat_hybrid_v1"),
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
      hybrid_action_spec="air_combat_hybrid_v1",
      hybrid_event_credit_head_lr_scale=6.0,
    )

    self.assertIsNotNone(policy.hybrid_event_credit_head)
    assert policy.hybrid_event_credit_head is not None
    self.assertTrue(
      th.allclose(
        policy.hybrid_event_credit_head.weight.detach(),
        th.zeros_like(policy.hybrid_event_credit_head.weight),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.hybrid_event_credit_head.bias.detach(),
        th.zeros_like(policy.hybrid_event_credit_head.bias),
      )
    )
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hybrid_event_credit_head", "hmoe"])
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 6.0, places=6)
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 6.0, places=10)
    self.assertAlmostEqual(
      float(policy._get_constructor_parameters().get("hybrid_event_credit_head_lr_scale", 0.0)),
      6.0,
      places=6,
    )

    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -5.0
      policy.action_net.bias[11] = 0.0
    obs = {
      "instruments": th.zeros((2, 42), dtype=th.float32),
      "contacts": th.zeros((2, 10, 5), dtype=th.float32),
      "rwr": th.zeros((2, 4, 4), dtype=th.float32),
      "mission": th.zeros((2, 20), dtype=th.float32),
      "proprio": th.zeros((2, 12), dtype=th.float32),
    }
    obs["mission"][:, 5] = 2.0
    obs["mission"][:, 6] = 1.0
    obs["mission"][:, 14] = 2.0
    obs["mission"][:, 15] = 1.0
    obs["mission"][:, 16] = 1.0
    obs["mission"][:, 19] = 1.0

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      credit = policy.get_hybrid_event_credit(obs)
      delta = distribution.fire_event_logit_delta()
      q_values = distribution.fire_event_q_values()
      advantage = distribution.fire_event_advantage()

    self.assertIsNotNone(credit)
    self.assertIsNotNone(delta)
    self.assertIsNotNone(q_values)
    self.assertIsNotNone(advantage)
    assert credit is not None
    assert delta is not None
    assert q_values is not None
    assert advantage is not None
    self.assertTrue(th.allclose(delta, th.full_like(delta, -5.0)))
    self.assertEqual(tuple(q_values.shape), (2, 2))
    self.assertTrue(th.allclose(q_values, th.zeros_like(q_values)))
    self.assertTrue(th.allclose(advantage, th.zeros_like(advantage)))
    self.assertTrue(th.allclose(credit.q_hold, th.zeros_like(credit.q_hold)))
    self.assertTrue(th.allclose(credit.q_fire_once, th.zeros_like(credit.q_fire_once)))
    self.assertTrue(th.allclose(credit.event_advantage, th.zeros_like(credit.event_advantage)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["a7/event_credit_head_lr_scale"]), 6.0, places=6)
    self.assertAlmostEqual(float(stats["a7/event_credit_advantage_abs_mean"]), 0.0, places=6)

  def test_hybrid_event_credit_head_coexists_with_event_logit_head(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      hybrid_event_credit_head_lr_scale=6.0,
    )

    self.assertIsNotNone(policy.hybrid_event_head)
    self.assertIsNotNone(policy.hybrid_event_credit_head)
    self.assertEqual(
      [group.get("name") for group in policy.optimizer.param_groups],
      ["shared", "hybrid_event_head", "hybrid_event_credit_head", "hmoe"],
    )
    assert policy.hybrid_event_head is not None
    assert policy.hybrid_event_credit_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -2.0
      policy.action_net.bias[11] = 0.5
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.copy_(th.tensor([0.25, 1.25], dtype=th.float32))
      policy.hybrid_event_credit_head.weight.zero_()
      policy.hybrid_event_credit_head.bias.copy_(th.tensor([2.0, 5.0], dtype=th.float32))
    obs = self._make_authorized_fire_obs(batch_size=4)

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      credit = policy.get_hybrid_event_credit(obs)
      delta = distribution.fire_event_logit_delta()
      q_values = distribution.fire_event_q_values()
      advantage = distribution.fire_event_advantage()

    self.assertIsNotNone(credit)
    assert credit is not None
    assert delta is not None
    assert q_values is not None
    assert advantage is not None
    self.assertTrue(th.allclose(delta, th.full((4,), -1.5)))
    self.assertTrue(th.allclose(q_values[:, 0], th.full((4,), 2.0)))
    self.assertTrue(th.allclose(q_values[:, 1], th.full((4,), 5.0)))
    self.assertTrue(th.allclose(advantage, th.full((4,), 3.0)))
    self.assertTrue(th.allclose(credit.event_advantage, th.full((4,), 3.0)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
    self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 1.0)

  def test_m3_stopping_head_can_override_hybrid_fire_event_delta(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      hybrid_event_use_m3_stopping_head=True,
      m3_stopping_head_lr_scale=5.0,
    )

    self.assertIsNotNone(policy.hybrid_event_head)
    self.assertIsNotNone(policy.m3_stopping_head)
    self.assertEqual(
      [group.get("name") for group in policy.optimizer.param_groups],
      ["shared", "hybrid_event_head", "m3_stopping_head", "hmoe"],
    )
    assert policy.hybrid_event_head is not None
    assert policy.m3_stopping_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -2.0
      policy.action_net.bias[11] = 0.5
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.copy_(th.tensor([0.25, 1.25], dtype=th.float32))
      policy.m3_stopping_head.weight.zero_()
      policy.m3_stopping_head.bias.fill_(3.0)
    obs = self._make_authorized_fire_obs(batch_size=4)

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      delta = distribution.fire_event_logit_delta()
      mode = distribution.mode()

    assert delta is not None
    self.assertTrue(th.allclose(delta, th.full((4,), 3.0)))
    self.assertTrue(th.allclose(mode[:, 9], th.ones((4,), dtype=mode.dtype)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s2/event_adapter_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["m3s2/event_adapter_logit_mean"]), 3.0, places=6)

  def test_m3_window_classifier_head_can_override_hybrid_fire_event_delta(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      hybrid_event_use_m3_window_classifier_head=True,
      m3_window_classifier_head_lr_scale=5.0,
      m3_window_classifier_head_norm_enabled=True,
    )

    self.assertIsNotNone(policy.hybrid_event_head)
    self.assertIsNotNone(policy.m3_window_classifier_head)
    self.assertIsNotNone(policy.m3_window_classifier_norm)
    self.assertEqual(
      [group.get("name") for group in policy.optimizer.param_groups],
      ["shared", "hybrid_event_head", "m3_window_classifier_head", "hmoe"],
    )
    assert policy.hybrid_event_head is not None
    assert policy.m3_window_classifier_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -2.0
      policy.action_net.bias[11] = 0.5
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.copy_(th.tensor([0.25, 1.25], dtype=th.float32))
      policy.m3_window_classifier_head.weight.zero_()
      policy.m3_window_classifier_head.bias.fill_(4.0)
    obs = self._make_authorized_fire_obs(batch_size=4)

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      delta = distribution.fire_event_logit_delta()
      mode = distribution.mode()
      window_logits = policy.get_m3_window_logits(obs)

    assert delta is not None
    assert window_logits is not None
    self.assertTrue(th.allclose(delta, th.full((4,), 4.0)))
    self.assertTrue(th.allclose(window_logits, th.full((4,), 4.0)))
    self.assertTrue(th.allclose(mode[:, 9], th.ones((4,), dtype=mode.dtype)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s2/event_adapter_enabled"]), 1.0)
    self.assertEqual(float(stats["m3s2/window_classifier_event_adapter_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["m3s2/event_adapter_logit_mean"]), 4.0, places=6)

  def test_m3_window_classifier_event_adapter_does_not_receive_actor_gradients(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      hybrid_event_use_m3_window_classifier_head=True,
      m3_window_classifier_head_lr_scale=5.0,
      m3_window_classifier_head_norm_enabled=True,
    )
    assert policy.hybrid_event_head is not None
    assert policy.m3_window_classifier_head is not None
    assert policy.m3_window_classifier_norm is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.zero_()
      policy.m3_window_classifier_head.weight.zero_()
      policy.m3_window_classifier_head.bias.fill_(4.0)
    obs = self._make_authorized_fire_obs(batch_size=4)
    actions = th.zeros((4, 12), dtype=th.float32)

    policy.optimizer.zero_grad(set_to_none=True)
    distribution = policy.get_distribution(obs)
    actor_loss = -distribution.log_prob(actions).mean()
    self.assertTrue(bool(actor_loss.requires_grad))
    actor_loss.backward()

    classifier_params = list(policy.m3_window_classifier_head.parameters()) + list(
      policy.m3_window_classifier_norm.parameters()
    )
    for param in classifier_params:
      self.assertTrue(param.grad is None or th.allclose(param.grad, th.zeros_like(param.grad)))

    policy.optimizer.zero_grad(set_to_none=True)
    direct_logits = policy.get_m3_window_logits(obs)
    assert direct_logits is not None
    direct_logits.mean().backward()
    self.assertTrue(
      any(
        param.grad is not None and float(param.grad.detach().abs().sum().item()) > 0.0
        for param in classifier_params
      )
    )

  def test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
      }
    )
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      make_action_space("air_combat_hybrid_v1"),
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
      hybrid_action_spec="air_combat_hybrid_v1",
      hybrid_event_credit_head_lr_scale=6.0,
    )
    assert policy.hybrid_event_credit_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -2.0
      policy.action_net.bias[11] = 0.5
      policy.hybrid_event_credit_head.weight.zero_()
      policy.hybrid_event_credit_head.bias.copy_(th.tensor([1.25, -0.75], dtype=th.float32))
    obs = {
      "instruments": th.zeros((3, 42), dtype=th.float32),
      "contacts": th.zeros((3, 10, 5), dtype=th.float32),
      "rwr": th.zeros((3, 4, 4), dtype=th.float32),
      "mission": th.zeros((3, 20), dtype=th.float32),
      "proprio": th.zeros((3, 12), dtype=th.float32),
    }
    obs["mission"][:, 5] = 2.0
    obs["mission"][:, 6] = 1.0
    obs["mission"][:, 14] = 2.0
    obs["mission"][:, 15] = 1.0
    obs["mission"][:, 16] = 1.0
    obs["mission"][:, 19] = 1.0

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      credit = policy.get_hybrid_event_credit(obs)
      delta = distribution.fire_event_logit_delta()
      q_values = distribution.fire_event_q_values()
      advantage = distribution.fire_event_advantage()

    self.assertIsNotNone(credit)
    assert credit is not None
    assert delta is not None
    assert q_values is not None
    assert advantage is not None
    self.assertTrue(th.allclose(delta, th.full_like(delta, -2.5)))
    self.assertTrue(th.allclose(q_values[:, 0], th.full((3,), 1.25)))
    self.assertTrue(th.allclose(q_values[:, 1], th.full((3,), -0.75)))
    self.assertTrue(th.allclose(advantage, th.full((3,), -2.0)))
    self.assertTrue(th.allclose(credit.q_hold, th.full((3,), 1.25)))
    self.assertTrue(th.allclose(credit.q_fire_once, th.full((3,), -0.75)))
    self.assertTrue(th.allclose(credit.event_advantage, th.full((3,), -2.0)))
    stats = policy.get_hmoe_route_stats()
    self.assertAlmostEqual(float(stats["a7/event_credit_q_hold_mean"]), 1.25, places=6)
    self.assertAlmostEqual(float(stats["a7/event_credit_q_fire_mean"]), -0.75, places=6)
    self.assertAlmostEqual(float(stats["a7/event_credit_advantage_mean"]), -2.0, places=6)

  def test_hybrid_event_credit_head_state_dict_load_smoke(self) -> None:
    source = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
    target = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
    assert source.hybrid_event_credit_head is not None
    with th.no_grad():
      source.hybrid_event_credit_head.weight.zero_()
      source.hybrid_event_credit_head.bias.copy_(th.tensor([0.5, 3.5], dtype=th.float32))

    target.load_state_dict({key: value.detach().clone() for key, value in source.state_dict().items()})
    obs = self._make_authorized_fire_obs(batch_size=2)

    with th.no_grad():
      credit = target.get_hybrid_event_credit(obs)

    self.assertIsNotNone(credit)
    assert credit is not None
    self.assertTrue(th.allclose(credit.q_hold, th.full((2,), 0.5)))
    self.assertTrue(th.allclose(credit.q_fire_once, th.full((2,), 3.5)))
    self.assertTrue(th.allclose(credit.event_advantage, th.full((2,), 3.0)))

  def test_m3_stopping_head_is_disabled_by_default(self) -> None:
    policy = self._make_air_combat_hybrid_policy()
    obs = self._make_authorized_fire_obs(batch_size=2)

    with th.no_grad():
      stopping = policy.get_m3_stopping(obs)
      logits = policy.get_m3_stopping_logits(obs)
      window_logits = policy.get_m3_window_logits(obs)

    self.assertIsNone(policy.m3_stopping_head)
    self.assertIsNone(policy.m3_stopping_norm)
    self.assertIsNone(policy.m3_window_classifier_head)
    self.assertIsNone(policy.m3_window_classifier_norm)
    self.assertIsNone(stopping)
    self.assertIsNone(logits)
    self.assertIsNone(window_logits)
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hmoe"])
    self.assertAlmostEqual(
      float(policy._get_constructor_parameters().get("m3_stopping_head_lr_scale", -1.0)),
      0.0,
      places=6,
    )
    self.assertFalse(bool(policy._get_constructor_parameters().get("m3_stopping_head_norm_enabled", True)))
    self.assertAlmostEqual(
      float(policy._get_constructor_parameters().get("m3_window_classifier_head_lr_scale", -1.0)),
      0.0,
      places=6,
    )
    self.assertFalse(
      bool(policy._get_constructor_parameters().get("m3_window_classifier_head_norm_enabled", True))
    )
    self.assertTrue(
      bool(policy._get_constructor_parameters().get("m3_window_classifier_event_adapter_detach", False))
    )
    self.assertFalse(
      bool(
        policy._get_constructor_parameters().get(
          "m3_window_classifier_input_standardization_enabled",
          True,
        )
      )
    )
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s1/stopping_head_enabled"]), 0.0)
    self.assertAlmostEqual(float(stats["m3s1/stopping_head_lr_scale"]), 0.0, places=6)
    self.assertEqual(float(stats["m3s2/window_classifier_head_enabled"]), 0.0)
    self.assertAlmostEqual(float(stats["m3s2/window_classifier_head_lr_scale"]), 0.0, places=6)

  def test_m3_stopping_head_gets_dedicated_optimizer_lane_and_zero_outputs(self) -> None:
    policy = self._make_air_combat_hybrid_policy(m3_stopping_head_lr_scale=5.0)

    self.assertIsNotNone(policy.m3_stopping_head)
    assert policy.m3_stopping_head is not None
    self.assertTrue(th.allclose(policy.m3_stopping_head.weight.detach(), th.zeros_like(policy.m3_stopping_head.weight)))
    self.assertTrue(th.allclose(policy.m3_stopping_head.bias.detach(), th.zeros_like(policy.m3_stopping_head.bias)))
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "m3_stopping_head", "hmoe"])
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 5.0, places=6)
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 5.0, places=10)
    self.assertAlmostEqual(
      float(policy._get_constructor_parameters().get("m3_stopping_head_lr_scale", 0.0)),
      5.0,
      places=6,
    )
    obs = self._make_authorized_fire_obs(batch_size=3)

    with th.no_grad():
      stopping = policy.get_m3_stopping(obs)
      logits = policy.get_m3_stopping_hazard_logits(obs)

    self.assertIsNotNone(stopping)
    assert stopping is not None
    assert logits is not None
    self.assertTrue(th.allclose(stopping.stopping_logit, th.zeros_like(stopping.stopping_logit)))
    self.assertTrue(th.allclose(stopping.hazard_logit, th.zeros_like(stopping.hazard_logit)))
    self.assertTrue(th.allclose(stopping.hazard, th.full_like(stopping.hazard, 0.5)))
    self.assertTrue(th.allclose(logits, th.zeros_like(logits)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s1/stopping_head_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["m3s1/stopping_head_lr_scale"]), 5.0, places=6)
    self.assertAlmostEqual(float(stats["m3s1/stop_logit_mean"]), 0.0, places=6)
    self.assertAlmostEqual(float(stats["m3s1/hazard_mean"]), 0.5, places=6)


if __name__ == "__main__":
  unittest.main()