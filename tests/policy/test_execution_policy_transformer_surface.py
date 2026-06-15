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


class ExecutionPolicyTransformerSurfaceTests(unittest.TestCase):
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

  def test_air_combat_hybrid_fire_event_mask_blocks_deterministic_and_stochastic_fire(self) -> None:
    params = th.zeros((4, 20), dtype=th.float32)
    params[:, 9] = 8.0
    params[:, 11] = -2.0
    dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.zeros((4,), dtype=th.bool))

    deterministic_actions = dist.get_actions(deterministic=True)
    stochastic_actions = dist.get_actions(deterministic=False)

    self.assertTrue(th.all(deterministic_actions[:, 9] == 0.0))
    self.assertTrue(th.all(stochastic_actions[:, 9] == 0.0))

  def test_air_combat_hybrid_fire_event_logprob_and_entropy_are_finite_when_masked(self) -> None:
    params = th.zeros((2, 20), dtype=th.float32)
    params[:, 9] = 8.0
    params[:, 11] = -2.0
    dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.zeros((2,), dtype=th.bool))
    hold_actions = th.zeros((2, 12), dtype=th.float32)
    fire_actions = hold_actions.clone()
    fire_actions[:, 9] = 1.0

    hold_log_prob = dist.log_prob(hold_actions)
    fire_log_prob = dist.log_prob(fire_actions)
    entropy = dist.entropy()

    self.assertTrue(th.isfinite(hold_log_prob).all())
    self.assertTrue(th.isfinite(fire_log_prob).all())
    self.assertTrue(th.isfinite(entropy).all())
    self.assertTrue(th.all(fire_log_prob < hold_log_prob - 1.0e6))

  def test_air_combat_hybrid_fire_event_deterministic_uses_hold_fire_argmax(self) -> None:
    params = th.zeros((1, 20), dtype=th.float32)
    params[:, 9] = 0.25
    params[:, 11] = 2.0
    dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.ones((1,), dtype=th.bool))

    actions = dist.get_actions(deterministic=True)

    self.assertEqual(float(actions[0, 9]), 0.0)

  def test_air_combat_hybrid_non_event_binary_heads_still_use_bernoulli_semantics(self) -> None:
    params = th.zeros((1, 20), dtype=th.float32)
    params[:, 6] = -1.0
    params[:, 7] = 1.0
    params[:, 8] = 2.0
    params[:, 9] = -3.0
    params[:, 10] = -2.0
    params[:, 11] = 0.0
    dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.ones((1,), dtype=th.bool))

    actions = dist.get_actions(deterministic=True)

    self.assertEqual(float(actions[0, 6]), 0.0)
    self.assertEqual(float(actions[0, 7]), 1.0)
    self.assertEqual(float(actions[0, 8]), 1.0)
    self.assertEqual(float(actions[0, 10]), 0.0)

  def test_air_combat_c2_roe_mission_mask_plumbs_into_policy_distribution(self) -> None:
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
    )
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = 8.0
      policy.action_net.bias[11] = -2.0
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
      actions = policy.get_distribution(obs).get_actions(deterministic=True)

    self.assertEqual(float(actions[0, 9]), 0.0)
    self.assertEqual(float(actions[1, 9]), 1.0)

  def test_air_combat_c2_roe_v2_quality_window_gates_policy_fire_support(self) -> None:
    mode = "air_combat_c2_roe_v2"
    mission_dim = mission_observation_dim(mode)
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
        "event_action_mask": spaces.Box(low=0.0, high=1.0, shape=(2,), dtype=float),
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
    )
    with th.no_grad():
      policy.action_net.weight.zero_()
      policy.action_net.bias.zero_()
      policy.action_net.bias[9] = 8.0
      policy.action_net.bias[11] = -2.0
    mission = th.zeros((3, mission_dim), dtype=th.float32)
    mission[1, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
    mission[1, mission_observation_field_index(mode, "quality_window_ready")] = 0.0
    mission[2, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
    mission[2, mission_observation_field_index(mode, "quality_window_ready")] = 1.0
    obs = {
      "instruments": th.zeros((3, 42), dtype=th.float32),
      "contacts": th.zeros((3, 10, 5), dtype=th.float32),
      "rwr": th.zeros((3, 4, 4), dtype=th.float32),
      "mission": mission,
      "proprio": th.zeros((3, 12), dtype=th.float32),
      "event_action_mask": th.tensor([[1.0, 1.0], [1.0, 1.0], [1.0, 0.0]], dtype=th.float32),
    }

    with th.no_grad():
      actions = policy.get_distribution(obs).get_actions(deterministic=True)

    self.assertEqual(float(actions[0, 9]), 0.0)
    self.assertEqual(float(actions[1, 9]), 0.0)
    self.assertEqual(float(actions[2, 9]), 1.0)

  def test_safe_action_bias_initializes_air_combat_hybrid_switch_logits(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
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
    )
    with th.no_grad():
      policy.action_net.weight.fill_(0.25)
      policy.action_net.bias.fill_(0.1)

    class _Model:
      pass

    model = _Model()
    model.policy = policy
    apply_safe_action_bias(
      model,
      "air_combat_hybrid_v1",
      "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
    )

    bias = policy.action_net.bias.detach().cpu()
    self.assertTrue(th.allclose(policy.action_net.weight.detach(), th.zeros_like(policy.action_net.weight)))
    self.assertGreater(float(bias[6]), 0.0)
    self.assertGreater(float(bias[8]), 0.0)
    self.assertLess(float(bias[7]), -3.0)
    self.assertLess(float(bias[9]), -5.0)
    self.assertLess(float(bias[9]), 0.0)
    self.assertLess(float(bias[10]), 0.0)
    self.assertGreater(float(bias[11]), float(bias[9]))
    self.assertGreater(float(bias[13]), float(bias[12]))
    for head in policy.hmoe_head_bank.family_heads:
      self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    with th.no_grad():
      policy.action_net.weight.fill_(0.25)
      policy.action_net.bias.fill_(0.1)
    apply_safe_action_bias(
      model,
      "air_combat_hybrid_v1",
      "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
      train_config={
        "hyperparameters": {
          "a7_event_policy_margin_coef": 0.35,
          "a7_event_policy_projection_margin_coef": 0.15,
        }
      },
    )

    bias = policy.action_net.bias.detach().cpu()
    self.assertTrue(th.allclose(policy.action_net.weight.detach(), th.zeros_like(policy.action_net.weight)))
    self.assertLess(float(bias[9]), -5.0)
    self.assertLess(float(bias[9]), 0.0)
    self.assertGreater(float(bias[11]), float(bias[9]))
    self.assertLess(float(th.sigmoid(bias[9] - bias[11]).item()), 0.01)

  def test_initialize_hmoe_from_shared_action_head_preserves_zero_residual_bootstrap(self) -> None:
    policy = self._make_policy()
    with th.no_grad():
      policy.action_net.weight.fill_(0.25)
      policy.action_net.bias.fill_(0.1)
      policy.hmoe_head_bank.family_heads[0].weight.fill_(1.0)
      policy.hmoe_head_bank.family_heads[0].bias.fill_(1.0)
      policy.hmoe_head_bank.subexpert_heads[0][0].weight.fill_(1.0)
      policy.hmoe_head_bank.subexpert_heads[0][0].bias.fill_(1.0)

    policy.initialize_hmoe_from_shared_action_head()

    for head in policy.hmoe_head_bank.family_heads:
      self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
      self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
    for family_subheads in policy.hmoe_head_bank.subexpert_heads:
      for head in family_subheads:
        self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
        self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

  def test_initialize_hmoe_from_shared_action_head_zeroes_hybrid_event_credit_head(self) -> None:
    policy = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
    assert policy.hybrid_event_credit_head is not None
    with th.no_grad():
      policy.hybrid_event_credit_head.weight.fill_(1.0)
      policy.hybrid_event_credit_head.bias.fill_(1.0)

    policy.initialize_hmoe_from_shared_action_head()

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

  def test_initialize_hmoe_from_shared_action_head_zeroes_m3_stopping_head(self) -> None:
    policy = self._make_air_combat_hybrid_policy(
      m3_stopping_head_lr_scale=5.0,
      m3_stopping_head_norm_enabled=True,
    )
    assert policy.m3_stopping_head is not None
    assert policy.m3_stopping_norm is not None
    with th.no_grad():
      policy.m3_stopping_head.weight.fill_(1.0)
      policy.m3_stopping_head.bias.fill_(1.0)
      policy.m3_stopping_norm.weight.fill_(2.0)
      policy.m3_stopping_norm.bias.fill_(3.0)

    policy.initialize_hmoe_from_shared_action_head()

    self.assertTrue(
      th.allclose(
        policy.m3_stopping_head.weight.detach(),
        th.zeros_like(policy.m3_stopping_head.weight),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.m3_stopping_head.bias.detach(),
        th.zeros_like(policy.m3_stopping_head.bias),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.m3_stopping_norm.weight.detach(),
        th.ones_like(policy.m3_stopping_norm.weight),
      )
    )
    self.assertTrue(
      th.allclose(
        policy.m3_stopping_norm.bias.detach(),
        th.zeros_like(policy.m3_stopping_norm.bias),
      )
    )

  def test_hmoe_parameter_stats_report_nonzero_fraction(self) -> None:
    policy = self._make_policy()
    stats = policy.get_hmoe_parameter_stats()
    self.assertAlmostEqual(stats["hmoe_params/family/nonzero_frac"], 0.0, places=6)
    self.assertAlmostEqual(stats["hmoe_params/sub/nonzero_frac"], 0.0, places=6)

    with th.no_grad():
      policy.hmoe_head_bank.family_heads[0].weight.fill_(0.5)
      policy.hmoe_head_bank.subexpert_heads[0][0].weight.fill_(0.5)
    stats = policy.get_hmoe_parameter_stats()
    self.assertGreater(stats["hmoe_params/family/nonzero_frac"], 0.0)
    self.assertGreater(stats["hmoe_params/sub/nonzero_frac"], 0.0)

  def test_transformer_extractor_prefers_bf16_when_supported(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0, high=1.0, shape=(21,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
      }
    )
    extractor = TransformerExtractor(
      observation_space,
      features_dim=32,
      n_heads=4,
      n_layers=1,
      use_amp=True,
      use_checkpointing=False,
    )

    with mock.patch("torch.cuda.is_available", return_value=True), mock.patch(
      "torch.cuda.is_bf16_supported", return_value=True
    ):
      self.assertTrue(extractor._autocast_enabled_for_forward())
      self.assertEqual(extractor._autocast_dtype(), th.bfloat16)

    extractor_fp16 = TransformerExtractor(
      observation_space,
      features_dim=32,
      n_heads=4,
      n_layers=1,
      use_amp=True,
      amp_dtype="fp16",
      use_checkpointing=False,
    )
    self.assertEqual(extractor_fp16._autocast_dtype(), th.float16)

  def test_transformer_observation_preprocessing_compresses_large_scales(self) -> None:
    observations = {
      "instruments": th.tensor(
        [[
          180.0, 0.7, 6800.0, 240.0, -12.0, 8.0, 2.0, 5.0, -15.0, 270.0,
          1.2, 0.8, 12.0, -4.0, 6.0, 92.0, 4200.0, 34708.0, 1.0, 0.2,
          0.1, 185.0, 7200.0, 170.0, 31.2, 121.4, 110.0, 90.0, -4.0, 145.0,
          268.0, 12.0, 300.0, 24.0, 1.0, 35.0, 1.0, 4.0, 0.3, -0.2, 1.0, 7200.0,
        ]],
        dtype=th.float32,
      ),
      "contacts": th.tensor(
        [[[34055.0, 190.0, 12.0, -320.0, 3.5]] * 10],
        dtype=th.float32,
      ),
      "rwr": th.tensor(
        [[[270.0, 8.0, 1.0, 0.0]] * 4],
        dtype=th.float32,
      ),
      "mission": th.tensor(
        [[
          3.0, 275.0, 7600.0, 175.0, 2.0, 1.0, 17423.0, -135.0, -1700.0, 0.8,
          28.0, 17423.0, 35.0, 9200.0, 2.0, 1.0, 30.0, 2.0, 120.0, -80.0,
          35.0, 21.0, 2.0, 12.0, 11.0,
        ]],
        dtype=th.float32,
      ),
      "proprio": th.tensor([[0.2] * 17], dtype=th.float32),
    }

    processed = preprocess_transformer_observations(observations)
    self.assertTrue(th.isfinite(processed["instruments"]).all())
    self.assertTrue(th.isfinite(processed["contacts"]).all())
    self.assertTrue(th.isfinite(processed["rwr"]).all())
    self.assertTrue(th.isfinite(processed["mission"]).all())

    self.assertLess(float(processed["instruments"].abs().max().item()), 6.0)
    self.assertLess(float(processed["contacts"].abs().max().item()), 6.0)
    self.assertLess(float(processed["rwr"].abs().max().item()), 6.0)
    self.assertLess(float(processed["mission"].abs().max().item()), 6.0)

    self.assertAlmostEqual(float(processed["instruments"][0, 17].item()), float(th.log1p(th.tensor(34.708)).item()), places=5)
    self.assertAlmostEqual(float(processed["contacts"][0, 0, 0].item()), float(th.log1p(th.tensor(34.055)).item()), places=5)
    self.assertAlmostEqual(float(processed["mission"][0, 6].item()), float(th.log1p(th.tensor(17.423)).item()), places=5)
    self.assertAlmostEqual(float(processed["rwr"][0, 0, 1].item()), 4.0, places=6)

  def test_transformer_preprocesses_naval_screen_station_mission_by_domain_fields(self) -> None:
    mode = "naval_screen_station_v1"
    mission = th.zeros((1, 23), dtype=th.float32)
    mission[0, mission_observation_field_index(mode, "command_code")] = 3.0
    mission[0, mission_observation_field_index(mode, "target_heading_deg")] = 90.0
    mission[0, mission_observation_field_index(mode, "target_speed_mps")] = 10.29
    mission[0, mission_observation_field_index(mode, "station_radius_m")] = 14816.0
    mission[0, mission_observation_field_index(mode, "station_bearing_deg")] = 90.0
    mission[0, mission_observation_field_index(mode, "station_error_m")] = 4040.0
    mission[0, mission_observation_field_index(mode, "station_error_norm")] = 0.306
    mission[0, mission_observation_field_index(mode, "screen_separation_m")] = 14816.0
    mission[0, mission_observation_field_index(mode, "screen_separation_error_m")] = 1618.0
    mission[0, mission_observation_field_index(mode, "target_contact_present")] = 1.0
    mission[0, mission_observation_field_index(mode, "support_track_present")] = 1.0
    mission[0, mission_observation_field_index(mode, "report_chain_seen")] = 0.5
    mission[0, mission_observation_field_index(mode, "roe_state")] = 1.0
    mission[0, mission_observation_field_index(mode, "assigned_target_id")] = 580.0

    processed = preprocess_mission_tensor(mission)

    self.assertTrue(th.isfinite(processed).all())
    self.assertLess(float(processed.abs().max().item()), 6.0)
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "station_bearing_deg")].item()),
      0.5,
      places=6,
    )
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "station_radius_m")].item()),
      float(th.log1p(th.tensor(14.816)).item()),
      places=5,
    )
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "station_error_m")].item()),
      float(th.log1p(th.tensor(4.04)).item()),
      places=5,
    )
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "station_error_norm")].item()),
      0.306,
      places=6,
    )
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "target_contact_present")].item()),
      1.0,
      places=6,
    )
    self.assertAlmostEqual(
      float(processed[0, mission_observation_field_index(mode, "report_chain_seen")].item()),
      0.5,
      places=6,
    )

  def test_transformer_extractor_forward_stays_finite_on_large_observations(self) -> None:
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0e6, high=1.0e6, shape=(42,), dtype=float),
        "contacts": spaces.Box(low=-1.0e6, high=1.0e6, shape=(10, 5), dtype=float),
        "rwr": spaces.Box(low=-1.0e6, high=1.0e6, shape=(4, 4), dtype=float),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(25,), dtype=float),
        "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
      }
    )
    extractor = TransformerExtractor(
      observation_space,
      features_dim=32,
      n_heads=4,
      n_layers=1,
      use_amp=False,
      use_checkpointing=False,
    )
    observations = {
      "instruments": th.full((2, 42), 25000.0, dtype=th.float32),
      "contacts": th.full((2, 10, 5), 34055.0, dtype=th.float32),
      "rwr": th.full((2, 4, 4), 270.0, dtype=th.float32),
      "mission": th.full((2, 25), 17423.0, dtype=th.float32),
      "proprio": th.zeros((2, 17), dtype=th.float32),
    }

    with th.no_grad():
      features = extractor(observations)

    self.assertEqual(tuple(features.shape), (2, 32))
    self.assertTrue(th.isfinite(features).all())

  def test_temporal_transformer_extractor_forward_is_finite(self) -> None:
    history_len = 4
    observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32),
        "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(10, 5), dtype=np.float32),
        "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(4, 4), dtype=np.float32),
        "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(21,), dtype=np.float32),
        "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32),
        "instruments_history": spaces.Box(
          low=-np.inf,
          high=np.inf,
          shape=(history_len, 42),
          dtype=np.float32,
        ),
        "contacts_history": spaces.Box(
          low=-np.inf,
          high=np.inf,
          shape=(history_len, 10, 5),
          dtype=np.float32,
        ),
        "rwr_history": spaces.Box(
          low=-np.inf,
          high=np.inf,
          shape=(history_len, 4, 4),
          dtype=np.float32,
        ),
        "mission_history": spaces.Box(
          low=-np.inf,
          high=np.inf,
          shape=(history_len, 21),
          dtype=np.float32,
        ),
        "proprio_history": spaces.Box(
          low=-np.inf,
          high=np.inf,
          shape=(history_len, 17),
          dtype=np.float32,
        ),
      }
    )
    extractor = TemporalTransformerExtractor(
      observation_space,
      features_dim=32,
      n_heads=4,
      n_layers=1,
      temporal_n_layers=1,
      use_checkpointing=False,
    )
    observations = {
      "instruments_history": th.randn((2, history_len, 42), dtype=th.float32),
      "contacts_history": th.randn((2, history_len, 10, 5), dtype=th.float32),
      "rwr_history": th.randn((2, history_len, 4, 4), dtype=th.float32),
      "mission_history": th.randn((2, history_len, 21), dtype=th.float32),
      "proprio_history": th.randn((2, history_len, 17), dtype=th.float32),
    }

    features = extractor(observations)

    self.assertEqual(tuple(features.shape), (2, 32))
    self.assertTrue(th.isfinite(features).all())



if __name__ == "__main__":
  unittest.main()