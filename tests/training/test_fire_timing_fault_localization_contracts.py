from __future__ import annotations

import unittest

import torch as th
from torch import nn

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics.fire_timing_fault_localization import learnability_audit as audit # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.chain_breakpoint import ( # noqa: E402
  _classification_metrics,
  _edge_trigger_summary,
  _fault_localization_summary,
  _head_module,
  _install_head,
  _masks_from_groups,
  _passes_window_classifier,
  _resolve_adapter_head_kind,
)
from tools.diagnostics.fire_timing_fault_localization.real_update import RealM3S2Group # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.real_update import _build_groups_from_rows # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.real_update import _collector_action_for_m3s2 # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.structural_toy import ToyProbeConfig, run_probe # noqa: E402


class AirCombatFireTimingLearnabilityAuditTests(unittest.TestCase):
  def test_verdict_identifies_reachable_release_but_unidentifiable_legal_timing(self) -> None:
    summaries = [
      {
        "case": "hold_fire",
        "mode": "hold_fire",
        "mean_total_reward": 70.0,
        "release_episode_count": 0,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
      {
        "case": "forced_fire_edge_at_reset",
        "mode": "forced_fire",
        "mean_total_reward": 70.0,
        "release_episode_count": 0,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {"no_target": 2},
      },
      {
        "case": "legal_mask_fire_delay_0",
        "mode": "legal_mask_fire",
        "fire_delay_steps": 0,
        "mean_total_reward": 520.0,
        "release_episode_count": 2,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
      {
        "case": "legal_mask_fire_delay_63",
        "mode": "legal_mask_fire",
        "fire_delay_steps": 63,
        "mean_total_reward": 520.25,
        "release_episode_count": 2,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
    ]

    verdict = audit._learnability_verdict(summaries, reward_epsilon=1.0)

    self.assertEqual(verdict["primary_breakpoint"], "legal_timing_unidentifiable_from_current_return")
    self.assertTrue(verdict["release_reachable_with_legal_oracle"])
    self.assertTrue(verdict["release_vs_hold_reward_distinguishable"])
    self.assertFalse(verdict["post_release_effect_observable"])
    self.assertFalse(verdict["legal_timing_reward_distinguishable"])
    self.assertTrue(verdict["edge_trigger_adapter_hazard"])

  def test_case_summary_counts_release_effects_and_rejection_reasons(self) -> None:
    summary = audit._case_summary(
      "legal_mask_fire_delay_0",
      {
        "mode": "legal_mask_fire",
        "fire_delay_steps": 0,
        "legal_fire_range_m": 0.0,
        "episode_summaries": [
          {
            "total_reward": 10.0,
            "final_target_health": 80.0,
            "release_count": 1,
            "fire_once_accepted_count": 1,
            "fire_once_rejected_count": 0,
            "effects_event_count": 1,
            "damage_report_count": 1,
            "first_release_step": 5,
            "first_effects_event_step": 40,
            "first_target_health_drop_step": 40,
            "release_steps": [5],
            "fire_once_rejected_reason_counts": {},
          },
          {
            "total_reward": 8.0,
            "final_target_health": 100.0,
            "release_count": 0,
            "fire_once_accepted_count": 0,
            "fire_once_rejected_count": 1,
            "effects_event_count": 0,
            "damage_report_count": 0,
            "first_release_step": None,
            "first_effects_event_step": None,
            "first_target_health_drop_step": None,
            "release_steps": [],
            "fire_once_rejected_reason_counts": {"no_target": 1},
          },
        ],
      },
    )

    self.assertEqual(summary["episodes"], 2)
    self.assertAlmostEqual(summary["mean_total_reward"], 9.0)
    self.assertAlmostEqual(summary["mean_release_count"], 0.5)
    self.assertEqual(summary["release_episode_count"], 1)
    self.assertEqual(summary["effects_episode_count"], 1)
    self.assertEqual(summary["damage_episode_count"], 1)
    self.assertEqual(summary["target_health_drop_episode_count"], 1)
    self.assertEqual(summary["release_steps"], [5])
    self.assertEqual(summary["rejected_reason_counts"], {"no_target": 1})


class M3S2ChainBreakpointProbeTests(unittest.TestCase):
  def test_model_event_hold_collector_preserves_model_action_except_fire_event(self) -> None:
    class DummyModel:
      def __init__(self) -> None:
        self.calls: list[bool] = []

      def predict(self, _obs, *, deterministic: bool):
        self.calls.append(bool(deterministic))
        return th.arange(12, dtype=th.float32).numpy(), None

    model = DummyModel()

    action = _collector_action_for_m3s2(
      model,
      env=None,
      obs={"dummy": 1},
      collector_action="model_event_hold",
      stochastic=False,
    )

    expected = th.arange(12, dtype=th.float32).numpy()
    expected[9] = 0.0
    self.assertEqual(model.calls, [True])
    self.assertEqual(action.tolist(), expected.tolist())

  def test_masks_from_groups_marks_prewindow_and_quality_rows(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3),
      step_indices=(0, 1, 2, 3),
      legal_mask=(False, True, True, True),
      quality_mask=(False, False, True, True),
      accepted_event=(False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=3,
    )

    masks = _masks_from_groups([group], row_count=5)

    self.assertEqual(masks.legal.tolist(), [False, True, True, True, False])
    self.assertEqual(masks.prewindow.tolist(), [False, True, False, False, False])
    self.assertEqual(masks.quality.tolist(), [False, False, True, True, False])
    self.assertEqual(masks.eligible.tolist(), [False, True, True, True, False])

  def test_classifier_pass_requires_no_prewindow_boundary_and_all_quality_boundary(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3),
      step_indices=(0, 1, 2, 3),
      legal_mask=(True, True, True, True),
      quality_mask=(False, False, True, True),
      accepted_event=(False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=3,
    )
    masks = _masks_from_groups([group], row_count=4)

    good = _classification_metrics(th.tensor([-2.0, -1.0, 1.0, 2.0]), masks)
    bad = _classification_metrics(th.tensor([-2.0, 1.0, 1.0, 2.0]), masks)

    self.assertTrue(_passes_window_classifier(good, min_accuracy=0.99))
    self.assertFalse(_passes_window_classifier(bad, min_accuracy=0.99))

  def test_edge_trigger_counts_first_quality_pulse(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3, 4),
      step_indices=(0, 1, 2, 3, 4),
      legal_mask=(True, True, True, True, True),
      quality_mask=(False, False, True, True, True),
      accepted_event=(False, False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=4,
    )
    masks = _masks_from_groups([group], row_count=5)

    summary = _edge_trigger_summary(th.tensor([False, False, True, True, True]), masks)

    self.assertEqual(summary["pulse_count"], 1)
    self.assertEqual(summary["quality_pulse_count"], 1)
    self.assertEqual(summary["prewindow_pulse_count"], 0)
    self.assertEqual(summary["first_quality_pulse"]["row"], 2)

  def test_auto_adapter_head_prefers_executable_window_classifier(self) -> None:
    class DummyPolicy:
      _hybrid_event_use_m3_window_classifier_head = True
      _hybrid_event_use_m3_stopping_head = True

      def __init__(self) -> None:
        self.m3_window_classifier_head = nn.Linear(2, 1)
        self.m3_stopping_head = nn.Linear(2, 1)

    policy = DummyPolicy()
    source = nn.Linear(2, 1)
    with th.no_grad():
      source.weight.fill_(3.0)
      source.bias.fill_(1.0)
      policy.m3_stopping_head.weight.fill_(-4.0)
      policy.m3_stopping_head.bias.fill_(-2.0)

    head_kind = _resolve_adapter_head_kind(policy, "auto")
    _install_head(policy, source, head_kind=head_kind)

    self.assertEqual(head_kind, "window_classifier")
    self.assertIs(_head_module(policy, head_kind), policy.m3_window_classifier_head)
    self.assertTrue(th.allclose(policy.m3_window_classifier_head.weight, source.weight))
    self.assertTrue(th.allclose(policy.m3_window_classifier_head.bias, source.bias))
    self.assertTrue(th.all(policy.m3_stopping_head.weight == -4.0))
    self.assertTrue(th.all(policy.m3_stopping_head.bias == -2.0))

  def test_fault_localization_reports_optimizer_breakpoint(self) -> None:
    summary = _fault_localization_summary(
      label_contract={
        "row_count": 4,
        "legal_count": 4,
        "prewindow_count": 2,
        "quality_count": 2,
        "pass": True,
      },
      fresh_latent={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      trained_m3_head={
        "pass": False,
        "accuracy": 0.75,
        "prewindow_boundary_count": 1,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      adapter_from_fresh={
        "pass": True,
        "edge_trigger_pass": True,
        "event_mode_fire_prewindow_count": 0,
        "event_mode_fire_quality_count": 2,
      },
      current_policy_pass=False,
      first_breakpoint="m3_head_optimization_conditioning",
    )

    self.assertEqual(summary["first_failed_stage"], "optimizer")
    self.assertTrue(bool(summary["blocks_feature_addition"]))
    stages = {stage["stage"]: stage for stage in summary["stages"]}
    self.assertFalse(bool(stages["optimizer"]["passed"]))
    self.assertFalse(bool(stages["loss_object"]["checked"]))
    self.assertEqual(summary["legacy_first_breakpoint"], "m3_head_optimization_conditioning")

  def test_fault_localization_reports_evaluation_breakpoint_after_local_chain_passes(self) -> None:
    summary = _fault_localization_summary(
      label_contract={
        "row_count": 4,
        "legal_count": 4,
        "prewindow_count": 2,
        "quality_count": 2,
        "pass": True,
      },
      fresh_latent={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      trained_m3_head={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      adapter_from_fresh={
        "pass": True,
        "edge_trigger_pass": True,
        "event_mode_fire_prewindow_count": 0,
        "event_mode_fire_quality_count": 2,
      },
      current_policy_pass=False,
      first_breakpoint="online_training_or_learned_parameter_contract",
    )

    self.assertEqual(summary["first_failed_stage"], "evaluation")
    stages = {stage["stage"]: stage for stage in summary["stages"]}
    self.assertTrue(bool(stages["optimizer"]["passed"]))
    self.assertFalse(bool(stages["evaluation"]["passed"]))


class M3S2RealUpdatePathProbeTests(unittest.TestCase):
  def test_build_groups_marks_quality_after_launch_and_min_age(self) -> None:
    groups = _build_groups_from_rows(
      fire_mask=[False, True, True, True, True],
      fire_once_accepted=[False, False, False, False, False],
      episode_id=[0, 0, 0, 0, 0],
      launch_window_open=[False, False, True, True, True],
      launch_min_age=3,
    )

    self.assertEqual(len(groups), 1)
    self.assertEqual(groups[0].legal_mask, (False, True, True, True, True))
    self.assertEqual(groups[0].quality_mask, (False, False, False, True, True))
    self.assertEqual(groups[0].censoring_kind, "timeout")

  def test_build_groups_early_accepted_before_quality_is_prefix_censored(self) -> None:
    groups = _build_groups_from_rows(
      fire_mask=[True, True, True, True],
      fire_once_accepted=[False, True, False, False],
      episode_id=[0, 0, 0, 0],
      launch_window_open=[False, False, True, True],
      launch_min_age=3,
    )

    self.assertEqual(groups[0].row_indices, (0, 1))
    self.assertEqual(groups[0].accepted_event, (False, True))
    self.assertEqual(groups[0].censoring_kind, "early_event_prefix")


class M3S2StructuralToyProbeTests(unittest.TestCase):
  def _config(self, *, model: str, train_steps: int, learning_rate: float) -> ToyProbeConfig:
    return ToyProbeConfig(
      model=model,
      prewindow_steps=12,
      quality_steps=24,
      train_steps=train_steps,
      learning_rate=learning_rate,
      initial_logit=-6.0,
      hidden_size=16,
      seed=7,
      early_mass_coef=2.0,
      early_mass_budget=0.02,
      early_survival_coef=8.0,
      window_delay_coef=0.5,
      window_deadline_coef=0.5,
      window_deadline_steps=8,
      max_grad_norm=2.0,
      prewindow_risk_gate=0.02,
      window_mass_gate=0.95,
    )

  def test_free_logits_structural_toy_crosses_quality_boundary(self) -> None:
    result = run_probe(self._config(model="free_logits", train_steps=500, learning_rate=0.1))

    self.assertTrue(result["verdict"]["structural_toy_pass"])
    final = result["final"]
    self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
    self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
    self.assertIsNotNone(final["first_quality_boundary_cross_step"])
    self.assertGreaterEqual(float(final["mean_p_window"]), 0.95)

  def test_mlp_structural_toy_learns_with_explicit_quality_feature(self) -> None:
    result = run_probe(self._config(model="mlp", train_steps=800, learning_rate=0.02))

    self.assertTrue(result["verdict"]["structural_toy_pass"])
    final = result["final"]
    self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
    self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
    self.assertIsNotNone(final["first_quality_boundary_cross_step"])
    self.assertGreaterEqual(float(final["quality_prob_max"]), 0.5)


if __name__ == "__main__":
  unittest.main()
