from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import torch as th
from gymnasium import spaces

from python.runtime_bootstrap import ensure_repo_imports

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


class ExecutionPolicyEventHeadTests(unittest.TestCase):
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

  def test_window_classifier_head_gets_dedicated_optimizer_lane_and_zero_outputs(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      window_classifier_head_lr_scale=5.0,
      window_classifier_head_norm_enabled=True,
    )

    self.assertIsNotNone(policy.window_classifier_head)
    self.assertIsNotNone(policy.window_classifier_norm)
    assert policy.window_classifier_head is not None
    assert policy.window_classifier_norm is not None
    self.assertEqual(
      [group.get("name") for group in policy.optimizer.param_groups],
      ["shared", "window_classifier_head", "hmoe"],
    )
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 5.0, places=6)
    self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 5.0, places=10)
    self.assertTrue(
      th.allclose(
        policy.window_classifier_head.weight.detach(),
        th.zeros_like(policy.window_classifier_head.weight),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.window_classifier_head.bias.detach(),
        th.zeros_like(policy.window_classifier_head.bias),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.window_classifier_norm.weight.detach(),
        th.ones_like(policy.window_classifier_norm.weight),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.window_classifier_norm.bias.detach(),
        th.zeros_like(policy.window_classifier_norm.bias),
      )
    )

    obs = self._make_authorized_fire_obs(batch_size=3)
    with th.no_grad():
      logits = policy.get_window_logits(obs)

    self.assertIsNotNone(logits)
    assert logits is not None
    self.assertTrue(th.allclose(logits, th.zeros_like(logits)))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["m3s2/window_classifier_head_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["m3s2/window_classifier_head_lr_scale"]), 5.0, places=6)
    self.assertAlmostEqual(float(stats["m3s2/window_classifier_prob_mean"]), 0.5, places=6)

  def test_window_classifier_input_standardization_updates_saved_buffers(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      window_classifier_head_lr_scale=5.0,
      window_classifier_input_standardization_enabled=True,
      window_classifier_input_standardization_momentum=1.0,
    )
    self.assertIsNotNone(policy.window_classifier_head)
    self.assertTrue(
      bool(
        policy._get_constructor_parameters().get(
          "window_classifier_input_standardization_enabled",
          False,
        )
      )
    )

    latent_dim = int(policy.mlp_extractor.latent_dim_pi)
    latent = th.arange(4 * latent_dim, dtype=th.float32).reshape(4, latent_dim)
    updated = policy.update_window_classifier_input_standardization(latent)

    self.assertTrue(updated)
    self.assertAlmostEqual(
      float(policy.window_classifier_input_standardization_initialized.item()),
      1.0,
      places=6,
    )
    standardized = policy._window_classifier_latent(latent)
    self.assertTrue(th.allclose(standardized.mean(dim=0), th.zeros((latent_dim,)), atol=1.0e-5))
    self.assertTrue(th.allclose(standardized.std(dim=0, unbiased=False), th.ones((latent_dim,)), atol=1.0e-5))

  def test_stopping_head_norm_uses_dedicated_optimizer_lane_and_zero_outputs(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      stopping_head_lr_scale=5.0,
      stopping_head_norm_enabled=True,
    )

    self.assertIsNotNone(policy.stopping_head)
    self.assertIsNotNone(policy.stopping_norm)
    assert policy.stopping_head is not None
    assert policy.stopping_norm is not None
    self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "stopping_head", "hmoe"])
    stopping_param_ids = {id(param) for param in policy.optimizer.param_groups[1]["params"]}
    expected_param_ids = {
      id(param)
      for module in (policy.stopping_norm, policy.stopping_head)
      for param in module.parameters()
    }
    self.assertEqual(stopping_param_ids, expected_param_ids)
    self.assertTrue(th.allclose(policy.stopping_norm.weight.detach(), th.ones_like(policy.stopping_norm.weight)))
    self.assertTrue(th.allclose(policy.stopping_norm.bias.detach(), th.zeros_like(policy.stopping_norm.bias)))
    self.assertTrue(th.allclose(policy.stopping_head.weight.detach(), th.zeros_like(policy.stopping_head.weight)))
    self.assertTrue(th.allclose(policy.stopping_head.bias.detach(), th.zeros_like(policy.stopping_head.bias)))
    self.assertTrue(bool(policy._get_constructor_parameters().get("stopping_head_norm_enabled", False)))

    obs = self._make_authorized_fire_obs(batch_size=3)
    with th.no_grad():
      stopping = policy.get_stopping(obs)

    self.assertIsNotNone(stopping)
    assert stopping is not None
    self.assertTrue(th.allclose(stopping.stopping_logit, th.zeros_like(stopping.stopping_logit)))
    stats = policy.get_hmoe_parameter_stats()
    self.assertEqual(float(stats["m3s1/stop_params/norm_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["m3s1/stop_params/norm_weight_mean"]), 1.0, places=6)

  def test_stopping_head_is_independent_from_executable_event_logits(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      hybrid_event_head_lr_scale=8.0,
      stopping_head_lr_scale=5.0,
    )
    assert policy.hybrid_event_head is not None
    assert policy.stopping_head is not None
    self.assertEqual(
      [group.get("name") for group in policy.optimizer.param_groups],
      ["shared", "hybrid_event_head", "stopping_head", "hmoe"],
    )
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = -2.0
      policy.action_net.bias[11] = 0.5
      policy.hybrid_event_head.weight.zero_()
      policy.hybrid_event_head.bias.copy_(th.tensor([0.25, 1.25], dtype=th.float32))
      policy.stopping_head.weight.zero_()
      policy.stopping_head.bias.fill_(3.0)
    obs = self._make_authorized_fire_obs(batch_size=4)

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      delta = distribution.fire_event_logit_delta()
      stopping = policy.get_stopping(obs)

    self.assertIsNotNone(delta)
    self.assertIsNotNone(stopping)
    assert delta is not None
    assert stopping is not None
    self.assertTrue(th.allclose(delta, th.full((4,), -1.5)))
    self.assertTrue(th.allclose(stopping.stopping_logit, th.full((4,), 3.0)))
    self.assertTrue(th.allclose(stopping.hazard, th.sigmoid(th.full((4,), 3.0))))
    stats = policy.get_hmoe_route_stats()
    self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
    self.assertEqual(float(stats["m3s1/stopping_head_enabled"]), 1.0)
    self.assertAlmostEqual(float(stats["a6/event_head_delta_fire_mean"]), 1.25, places=6)
    self.assertAlmostEqual(float(stats["m3s1/stop_logit_mean"]), 3.0, places=6)

  def test_stopping_head_does_not_bypass_fire_mask(self) -> None:
    policy = self._make_air_combat_hybrid_policy(stopping_head_lr_scale=5.0)
    assert policy.stopping_head is not None
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = 8.0
      policy.action_net.bias[11] = -2.0
      policy.stopping_head.weight.zero_()
      policy.stopping_head.bias.fill_(12.0)
    mission = th.zeros((2, 20), dtype=th.float32)
    mission[1, 5] = 2.0
    mission[1, 6] = 1.0
    mission[1, 14] = 2.0
    mission[1, 15] = 1.0
    mission[1, 16] = 1.0
    mission[1, 19] = 1.0
    obs = {
      "instruments": th.zeros((2, 42), dtype=th.float32),
      "contacts": th.zeros((2, 10, 5), dtype=th.float32),
      "rwr": th.zeros((2, 4, 4), dtype=th.float32),
      "mission": mission,
      "proprio": th.zeros((2, 12), dtype=th.float32),
    }

    with th.no_grad():
      distribution = policy.get_distribution(obs)
      actions = distribution.get_actions(deterministic=True)
      stopping = policy.get_stopping(obs)

    self.assertIsNotNone(stopping)
    assert stopping is not None
    self.assertTrue(th.allclose(stopping.stopping_logit, th.full((2,), 12.0)))
    self.assertEqual(float(actions[0, 9]), 0.0)
    self.assertEqual(float(actions[1, 9]), 1.0)

  def test_route_stats_follow_mission_semantics(self) -> None:
    policy = self._make_policy()
    obs = {
      "image": th.zeros((2, 1, 8, 8), dtype=th.float32),
      "instruments": th.zeros((2, 26), dtype=th.float32),
      "prev_action": th.zeros((2, 17), dtype=th.float32),
      "mission": th.tensor(
        [
          [2.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 21.0, 1.0, 11.0, 0.0],
          [3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
        ],
        dtype=th.float32,
      ),
    }
    with th.no_grad():
      actions, values, log_prob = policy.forward(obs, deterministic=True)

    self.assertEqual(tuple(actions.shape), (2, 17))
    self.assertEqual(tuple(values.shape), (2, 1))
    self.assertEqual(tuple(log_prob.shape), (2,))

    stats = policy.get_hmoe_route_stats()
    self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/form/lead"], 0.5, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 0.5, places=6)

  def test_predict_path_uses_observation_aware_routing(self) -> None:
    policy = self._make_policy()
    obs = {
      "image": th.zeros((1, 1, 8, 8), dtype=th.float32),
      "instruments": th.zeros((1, 26), dtype=th.float32),
      "prev_action": th.zeros((1, 17), dtype=th.float32),
      "mission": th.tensor(
        [[3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0]],
        dtype=th.float32,
      ),
    }
    with th.no_grad():
      dist = policy.get_distribution(obs)
      actions = dist.get_actions(deterministic=True)

    self.assertEqual(tuple(actions.shape), (1, 17))
    stats = policy.get_hmoe_route_stats()
    self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 1.0, places=6)

  def test_air_combat_c2_roe_route_stats_use_combat_weapons_family(self) -> None:
    observation_space = spaces.Dict(
      {
        "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=float),
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
        "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
      }
    )
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
      _ConstantSchedule(),
      net_arch={"pi": [32], "vf": [32]},
    )
    obs = {
      "image": th.zeros((3, 1, 8, 8), dtype=th.float32),
      "instruments": th.zeros((3, 26), dtype=th.float32),
      "prev_action": th.zeros((3, 17), dtype=th.float32),
      "mission": th.tensor(
        [
          [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 1.0, 0.0, 0.0, 1.0],
          [2.0, 0.0, 7000.0, 230.0, 2.0, 1.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0],
          [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        ],
        dtype=th.float32,
      ),
    }

    with th.no_grad():
      actions, values, log_prob = policy.forward(obs, deterministic=True)

    self.assertEqual(tuple(actions.shape), (3, 17))
    self.assertEqual(tuple(values.shape), (3, 1))
    self.assertEqual(tuple(log_prob.shape), (3,))
    stats = policy.get_hmoe_route_stats()
    self.assertAlmostEqual(stats["hmoe/fam/combat"], 1.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/combat/first_shot"], 1.0 / 3.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/combat/hold"], 1.0 / 3.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/combat/assess"], 1.0 / 3.0, places=6)

  def test_nonfinite_probe_preserves_observation_aware_routing(self) -> None:
    policy = self._make_policy()
    probe = NonFiniteTrainingProbe(report_path="/tmp/hmoe_nonfinite_probe_test.json", enabled=True)

    class _Model:
      def __init__(self, policy) -> None:
        self.policy = policy
        self.device = th.device("cpu")
        self.policy_kwargs = {}
        self._excluded_save_params = lambda: []

    probe._patch_policy(_Model(policy).policy)
    obs = {
      "image": th.zeros((1, 1, 8, 8), dtype=th.float32),
      "instruments": th.zeros((1, 26), dtype=th.float32),
      "prev_action": th.zeros((1, 17), dtype=th.float32),
      "mission": th.tensor(
        [[3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0]],
        dtype=th.float32,
      ),
    }

    with th.no_grad():
      dist = policy.get_distribution(obs)
      actions = dist.get_actions(deterministic=True)

    self.assertEqual(tuple(actions.shape), (1, 17))
    stats = policy.get_hmoe_route_stats()
    self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
    self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 1.0, places=6)

  def test_hmoe_heads_start_as_zero_residuals(self) -> None:
    policy = self._make_policy()
    for head in policy.hmoe_head_bank.family_heads:
      self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
      self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
    for family_subheads in policy.hmoe_head_bank.subexpert_heads:
      for head in family_subheads:
        self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
        self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

  def test_residual_gate_warms_up_from_zero(self) -> None:
    policy = self._make_policy()
    self.assertAlmostEqual(policy._hmoe_residual_gate, 0.0, places=6)
    policy.set_hmoe_training_progress(1.0)
    self.assertAlmostEqual(policy._hmoe_residual_gate, 0.0, places=6)

    policy.set_hmoe_training_progress(0.925)
    self.assertAlmostEqual(policy._hmoe_residual_gate, 0.5, places=6)

    policy.set_hmoe_training_progress(0.85)
    self.assertAlmostEqual(policy._hmoe_residual_gate, 1.0, places=6)

  def test_safe_action_bias_keeps_hmoe_residual_heads_zero(self) -> None:
    policy = self._make_policy()

    class _Model:
      pass

    model = _Model()
    model.policy = policy
    apply_safe_action_bias(model, "full", "scenarios/combined/cruise_to_landing_continuous_train_v1.json")

    # Shared action head keeps the realistic initialization bias.
    self.assertGreater(float(policy.action_net.bias[3].detach().cpu().item()), 0.0)

    # Routed residual heads stay neutral so they do not amplify the initial policy.
    for head in policy.hmoe_head_bank.family_heads:
      self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
    for family_subheads in policy.hmoe_head_bank.subexpert_heads:
      for head in family_subheads:
        self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

  def test_safe_action_bias_zeroes_naval_station_action_head(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(23,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=float),
      }
    )
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=float)
    policy = SquashedMultiInputPolicy(
      observation_space,
      action_space,
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
    )
    with th.no_grad():
      policy.action_net.weight.fill_(0.25)
      policy.action_net.bias.fill_(0.1)

    class _Model:
      pass

    model = _Model()
    model.policy = policy
    apply_safe_action_bias(model, "naval_station3", "scenarios/naval/ddg51_take1_screen_threat_roe_v1.json")

    self.assertTrue(th.allclose(policy.action_net.weight.detach(), th.zeros_like(policy.action_net.weight)))
    self.assertTrue(th.allclose(policy.action_net.bias.detach(), th.zeros_like(policy.action_net.bias)))

  def test_air_combat_hybrid_policy_uses_mixed_distribution_over_flat_transport(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
      }
    )
    action_space = make_action_space("air_combat_hybrid_v1")
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      action_space,
      _ConstantSchedule(),
      features_extractor_class=TransformerExtractor,
      features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
      net_arch={"pi": [32], "vf": [32]},
      hybrid_action_spec="air_combat_hybrid_v1",
      log_std_init=-1.2,
    )
    obs = {
      "instruments": th.zeros((2, 42), dtype=th.float32),
      "contacts": th.zeros((2, 10, 5), dtype=th.float32),
      "rwr": th.zeros((2, 4, 4), dtype=th.float32),
      "mission": th.zeros((2, 21), dtype=th.float32),
      "proprio": th.zeros((2, 12), dtype=th.float32),
    }

    with th.no_grad():
      actions, values, log_prob = policy.forward(obs, deterministic=True)
      eval_values, eval_log_prob, entropy = policy.evaluate_actions(obs, actions)

    self.assertEqual(int(policy.action_net.out_features), 20)
    self.assertEqual(int(policy.log_std.shape[0]), 6)
    self.assertTrue(th.allclose(policy.log_std.detach(), th.full_like(policy.log_std.detach(), -1.2)))
    self.assertEqual(tuple(actions.shape), (2, 12))
    self.assertEqual(tuple(values.shape), (2, 1))
    self.assertEqual(tuple(log_prob.shape), (2,))
    self.assertEqual(tuple(eval_values.shape), (2, 1))
    self.assertEqual(tuple(eval_log_prob.shape), (2,))
    self.assertTrue(th.isfinite(actions).all())
    self.assertTrue(th.isfinite(log_prob).all())
    self.assertTrue(th.isfinite(eval_log_prob).all())
    self.assertIsNotNone(entropy)
    self.assertEqual(tuple(entropy.shape), (2,))
    self.assertTrue(th.isfinite(entropy).all())
    self.assertTrue(th.all(entropy > 0.0))
    for idx in (6, 7, 8, 9, 10):
      self.assertTrue(th.all((actions[:, idx] == 0.0) | (actions[:, idx] == 1.0)))
    self.assertTrue(th.all(actions[:, 11] == th.round(actions[:, 11])))
    self.assertTrue(th.all(actions[:, 11] >= 0.0))
    self.assertTrue(th.all(actions[:, 11] <= 7.0))


if __name__ == "__main__":
  unittest.main()