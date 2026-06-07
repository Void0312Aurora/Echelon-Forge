from __future__ import annotations

import unittest

import torch as th
from torch import nn

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics.m3s2_chain_breakpoint_probe import (  # noqa: E402
    _classification_metrics,
    _edge_trigger_summary,
    _fault_localization_summary,
    _head_module,
    _install_head,
    _masks_from_groups,
    _passes_window_classifier,
    _resolve_adapter_head_kind,
)
from tools.diagnostics.m3s2_real_update_path_probe import RealM3S2Group  # noqa: E402
from tools.diagnostics.m3s2_real_update_path_probe import _collector_action_for_m3s2  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
