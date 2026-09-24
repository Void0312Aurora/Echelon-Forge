from __future__ import annotations

import unittest
from types import SimpleNamespace

import torch as th
from gymnasium import spaces

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo._event_credit_mixin import _EventCreditMixin
from python.rl.policy_algo._event_window_mixin import _EventWindowMixin
from python.rl.policy_algo.model_contracts import (
  LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
  LAUNCH_DECISION_CONTRACT_VERSION_KEY,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy


class _ConstantSchedule:
  def __call__(self, progress_remaining: float) -> float:
    return 1.0e-3


def _observation_space() -> spaces.Dict:
  return spaces.Dict({
    "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
    "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
  })


def _make_policy(mode: str | None) -> HierarchicalMoEExecutionPolicy:
  kwargs = {
    "net_arch": {"pi": [16], "vf": [16]},
    "hybrid_action_spec": "air_combat_hybrid_v1",
    "hmoe_residual_scale": 1.0,
    "hmoe_head_lr_scale": 1.0,
    "hybrid_event_head_lr_scale": 1.0,
  }
  if mode is not None:
    kwargs["launch_decision_mode"] = mode
    kwargs[LAUNCH_DECISION_CONTRACT_VERSION_KEY] = LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION
  return HierarchicalMoEExecutionPolicy(
    _observation_space(),
    make_action_space("air_combat_hybrid_v1"),
    _ConstantSchedule(),
    **kwargs,
  )


def _ids(parameters) -> set[int]:
  return {id(parameter) for parameter in parameters}


class LaunchDecisionOptimizerOwnershipTests(unittest.TestCase):
  def test_strict_margin_and_fire_boundary_select_only_event_head(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    margin_host = object.__new__(_EventCreditMixin)
    margin_host.policy = policy
    margin_parameters = margin_host._event_policy_margin_parameters()
    event_ids = _ids(policy.hybrid_event_head.parameters())
    self.assertEqual(_ids(margin_parameters), event_ids)

    fire_host = object.__new__(_EventWindowMixin)
    fire_host.policy = policy
    fire_parameters = fire_host._fire_boundary_parameters()
    self.assertEqual(_ids(fire_parameters), event_ids)

  def test_governed_margin_declares_composed_write_set(self) -> None:
    policy = _make_policy("governed_composed_v1")
    host = object.__new__(_EventCreditMixin)
    host.policy = policy
    selected = _ids(host._event_policy_margin_parameters())
    expected = (
      _ids(policy.action_net.parameters())
      | _ids(policy.hmoe_head_bank.parameters())
      | _ids(policy.hybrid_event_head.parameters())
      | _ids(policy.mlp_extractor.policy_net.parameters())
    )
    self.assertEqual(selected, expected)

  def test_legacy_margin_keeps_historical_write_set(self) -> None:
    policy = _make_policy(None)
    host = object.__new__(_EventCreditMixin)
    host.policy = policy
    selected = _ids(host._event_policy_margin_parameters())
    expected = (
      _ids(policy.action_net.parameters())
      | _ids(policy.hybrid_event_head.parameters())
      | _ids(policy.mlp_extractor.policy_net.parameters())
    )
    self.assertEqual(selected, expected)
    self.assertTrue(_ids(policy.hmoe_head_bank.parameters()).isdisjoint(selected))

  def test_strict_event_delta_has_no_action_or_hmoe_gradient(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    obs = {
      "mission": th.zeros((2, 20), dtype=th.float32),
      "instruments": th.zeros((2, 42), dtype=th.float32),
    }
    delta = policy.get_distribution(obs).fire_event_logit_delta()
    self.assertIsNotNone(delta)
    assert delta is not None
    delta.sum().backward()

    action_grad = sum(
      float(parameter.grad.detach().abs().sum().cpu().item())
      for parameter in policy.action_net.parameters()
      if parameter.grad is not None
    )
    hmoe_grad = sum(
      float(parameter.grad.detach().abs().sum().cpu().item())
      for parameter in policy.hmoe_head_bank.parameters()
      if parameter.grad is not None
    )
    event_grad = sum(
      float(parameter.grad.detach().abs().sum().cpu().item())
      for parameter in policy.hybrid_event_head.parameters()
      if parameter.grad is not None
    )
    self.assertAlmostEqual(action_grad, 0.0, places=8)
    self.assertAlmostEqual(hmoe_grad, 0.0, places=8)
    self.assertGreater(event_grad, 0.0)

  def test_update_trace_records_parameter_ids(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    parameters = list(policy.hybrid_event_head.parameters())
    policy.record_launch_decision_update("direct_boundary", parameters)
    trace = policy.get_launch_decision_trace()
    self.assertEqual(trace["last_update"]["scope"], "direct_boundary")
    self.assertEqual(set(trace["last_update"]["parameter_ids"]), _ids(parameters))
    self.assertIn("hybrid_event_head", trace["last_update"]["parameter_roles"])


if __name__ == "__main__":
  unittest.main()
