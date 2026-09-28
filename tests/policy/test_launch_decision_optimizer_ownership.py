from __future__ import annotations

import unittest

import torch as th
from gymnasium import spaces

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo._event_credit_mixin import _EventCreditMixin
from python.rl.policy_algo._event_window_mixin import _EventWindowMixin
from python.rl.policy_algo.model_contracts import LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION
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
    kwargs["launch_decision_contract_version"] = LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION
    kwargs["launch_decision_mode"] = mode
  return HierarchicalMoEExecutionPolicy(
    _observation_space(),
    make_action_space("air_combat_hybrid_v1"),
    _ConstantSchedule(),
    **kwargs,
  )


def _obs(batch: int = 2) -> dict[str, th.Tensor]:
  return {
    "mission": th.zeros((batch, 20), dtype=th.float32),
    "instruments": th.zeros((batch, 42), dtype=th.float32),
  }


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

  def test_governed_margin_uses_contract_write_set_exactly(self) -> None:
    policy = _make_policy("governed_composed_v1")
    host = object.__new__(_EventCreditMixin)
    host.policy = policy
    selected = _ids(host._event_policy_margin_parameters())
    contract = policy.get_launch_decision_owner_contract()
    expected = _ids(policy.get_launch_decision_parameters(contract.trainable_parameter_roles))
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
    delta = policy.get_distribution(_obs()).fire_event_logit_delta()
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

  def test_strict_fast_fire_boundary_matches_composer_delta(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    policy._hmoe_residual_gate = 1.0
    with th.no_grad():
      for parameter in policy.hmoe_head_bank.parameters():
        parameter.fill_(0.25)
    fast = policy.get_hybrid_event_fire_boundary_deltas_for_head_update(_obs())
    self.assertIsNotNone(fast)
    assert fast is not None
    fast_delta, _direct_delta = fast
    composed_delta = policy.get_distribution(_obs()).fire_event_logit_delta()
    self.assertIsNotNone(composed_delta)
    assert composed_delta is not None
    self.assertTrue(th.allclose(fast_delta, composed_delta, atol=1.0e-6, rtol=1.0e-6))

  def test_explicit_strict_ordinary_optimizer_step_cannot_write_launch_roles(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    launch_params = policy.get_launch_decision_parameters()
    before = {id(parameter): parameter.detach().clone() for parameter in launch_params}
    policy.optimizer.zero_grad(set_to_none=True)
    for parameter in launch_params:
      parameter.grad = th.ones_like(parameter)
    policy.optimizer.step()
    for parameter in launch_params:
      self.assertTrue(th.equal(parameter.detach(), before[id(parameter)]))

  def test_update_trace_requires_observed_parameter_change(self) -> None:
    policy = _make_policy("direct_boundary_v1_strict")
    parameters = list(policy.hybrid_event_head.parameters())
    policy.prepare_launch_decision_update("direct_boundary", parameters)
    policy.record_launch_decision_update("direct_boundary", parameters)
    self.assertNotIn("last_update", policy.get_launch_decision_trace())

    policy.prepare_launch_decision_update("direct_boundary", parameters)
    with th.no_grad():
      parameters[0].add_(1.0)
    policy.record_launch_decision_update("direct_boundary", parameters)
    trace = policy.get_launch_decision_trace()
    self.assertEqual(trace["last_update"]["scope"], "direct_boundary")
    self.assertEqual(set(trace["last_update"]["parameter_ids"]), {id(parameters[0])})
    self.assertIn("hybrid_event_head", trace["last_update"]["parameter_roles"])

    policy.get_distribution(_obs())
    trace_after_forward = policy.get_launch_decision_trace()
    self.assertEqual(trace_after_forward["last_update"], trace["last_update"])


if __name__ == "__main__":
  unittest.main()
