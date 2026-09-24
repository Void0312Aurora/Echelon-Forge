from __future__ import annotations

import unittest

import torch as th
from gymnasium import spaces

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
  LaunchDecisionContractError,
  LaunchDecisionContributor,
  LaunchDecisionMode,
  resolve_launch_decision_contract,
)
from python.rl.policy_algo.policies import (
  HierarchicalMoEExecutionPolicy,
  LaunchDecisionComposer,
  _HybridActionDistribution,
  _normalize_hybrid_action_layout,
)


class _ConstantSchedule:
  def __call__(self, progress_remaining: float) -> float:
    return 1.0e-3


def _config(**policy_kwargs):
  if "launch_decision_mode" in policy_kwargs or "launch_decision_owner_mode" in policy_kwargs:
    policy_kwargs.setdefault(
      LAUNCH_DECISION_CONTRACT_VERSION_KEY,
      LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
    )
  return {
    "hyperparameters": {
      "policy_kwargs": {
        "hybrid_action_spec": "air_combat_hybrid_v1",
        "hmoe_residual_scale": 0.25,
        "hmoe_head_lr_scale": 0.35,
        **policy_kwargs,
      },
    },
  }


class LaunchDecisionComposerTests(unittest.TestCase):
  def test_legacy_composition_records_window_precedence_without_masking(self) -> None:
    contract = resolve_launch_decision_contract(
      _config(
        hybrid_event_head_lr_scale=1.0,
        hybrid_event_use_window_classifier_head=True,
        hybrid_event_use_stopping_head=True,
      )
    )
    composer = LaunchDecisionComposer(contract)
    result = composer.compose(
      base_event_pair=th.tensor([[1.0, 2.0]]),
      contributor_outputs={
        LaunchDecisionContributor.HMOE_EVENT_SLICE: th.tensor([[0.1, 0.2]]),
        LaunchDecisionContributor.HYBRID_EVENT_HEAD: th.tensor([[0.3, 0.4]]),
        LaunchDecisionContributor.WINDOW_CLASSIFIER_ADAPTER: th.tensor([4.0]),
        LaunchDecisionContributor.STOPPING_ADAPTER: th.tensor([-8.0]),
      },
    )

    th.testing.assert_close(result.event_pair, th.tensor([[0.0, 4.0]]))
    th.testing.assert_close(result.event_delta, th.tensor([4.0]))
    self.assertFalse(result.trace["mask_applied"])
    self.assertEqual(result.trace["mask_owner"], "_HybridActionDistribution")
    self.assertEqual(result.trace["compatibility_precedence"], "window_classifier_before_stopping")
    self.assertIn("stopping_adapter", result.trace["ignored_contributors"])
    names = [item["name"] for item in result.trace["contributors"]]
    self.assertEqual(names, [
      "base_action",
      "hmoe_event_slice",
      "hybrid_event_head",
      "window_classifier_adapter",
      "stopping_adapter",
    ])
    self.assertEqual(result.trace["contributors"][-1]["status"], "ignored_compatibility_precedence")

  def test_strict_composition_rejects_unadmitted_hmoe_event_contribution(self) -> None:
    contract = resolve_launch_decision_contract(
      _config(
        launch_decision_mode=LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT.value,
        hybrid_event_head_lr_scale=1.0,
      )
    )
    composer = LaunchDecisionComposer(contract)
    with self.assertRaisesRegex(ValueError, "hmoe_event_slice"):
      composer.compose(
        base_event_pair=th.tensor([[1.0, 2.0]]),
        contributor_outputs={
          LaunchDecisionContributor.HMOE_EVENT_SLICE: th.tensor([[100.0, 100.0]]),
        },
      )

  def test_new_governed_conflict_fails_closed(self) -> None:
    with self.assertRaises(LaunchDecisionContractError):
      resolve_launch_decision_contract(
        _config(
          launch_decision_mode=LaunchDecisionMode.GOVERNED_COMPOSED_V1.value,
          hybrid_event_head_lr_scale=1.0,
          hybrid_event_use_window_classifier_head=True,
          hybrid_event_use_stopping_head=True,
        )
      )

  def test_distribution_applies_support_mask_after_unmasked_composer(self) -> None:
    action_space = make_action_space("air_combat_hybrid_v1")
    layout = _normalize_hybrid_action_layout("air_combat_hybrid_v1", action_space)
    assert layout is not None
    params = th.zeros((1, layout.param_dim), dtype=th.float32)
    params[:, layout.event_fire_param_index] = 2.0
    distribution = _HybridActionDistribution(
      layout=layout,
      params=params,
      log_std=th.zeros((layout.continuous_count,), dtype=th.float32),
      action_low=action_space.low,
      action_high=action_space.high,
      fire_event_mask=th.tensor([False]),
    )

    th.testing.assert_close(distribution.fire_event_unmasked_logits(), th.tensor([[0.0, 2.0]]))
    self.assertLess(float(distribution._fire_event_logits()[0, 1]), -1.0e7)

  def test_policy_trace_and_sampling_keep_deterministic_and_stochastic_paths(self) -> None:
    observation_space = spaces.Dict({
      "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
      "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
    })
    policy = HierarchicalMoEExecutionPolicy(
      observation_space,
      make_action_space("air_combat_hybrid_v1"),
      _ConstantSchedule(),
      net_arch={"pi": [16], "vf": [16]},
      hybrid_action_spec="air_combat_hybrid_v1",
      launch_decision_mode=LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT.value,
      launch_decision_contract_version=LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
      hybrid_event_head_lr_scale=1.0,
    )
    obs = {
      "mission": th.zeros((2, 20), dtype=th.float32),
      "instruments": th.zeros((2, 42), dtype=th.float32),
    }
    distribution = policy.get_distribution(obs)
    deterministic = distribution.get_actions(deterministic=True)
    stochastic = distribution.get_actions(deterministic=False)
    log_prob = distribution.log_prob(stochastic)

    self.assertEqual(tuple(deterministic.shape), (2, 12))
    self.assertEqual(tuple(stochastic.shape), (2, 12))
    self.assertTrue(th.isfinite(log_prob).all())
    trace = policy.get_launch_decision_trace()
    self.assertEqual(trace["mode"], LaunchDecisionMode.DIRECT_BOUNDARY_V1_STRICT.value)
    self.assertFalse(trace["mask_applied"])
    self.assertEqual(trace["distribution_mask_source"], "_HybridActionDistribution")
    self.assertNotIn("hmoe_event_slice", [item["name"] for item in trace["contributors"]])


if __name__ == "__main__":
  unittest.main()
