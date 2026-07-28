from __future__ import annotations

import math
import unittest

import torch as th

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.grouped_stopping import (
  CENSOR_EARLY_EVENT_PREFIX,
  CENSOR_FORCED_HOLD,
  CENSOR_NONE,
  CENSOR_TIMEOUT,
  CENSOR_UNSUPPORTED,
  ROUTE_FORCED_HOLD_PROBE,
  ROUTE_ON_POLICY,
  GroupedStoppingEvidence,
  compute_grouped_stopping_loss,
)


class GroupedStoppingLossContractTests(unittest.TestCase):
  def _group(
    self,
    logits: th.Tensor,
    *,
    legal_mask: list[bool],
    quality_mask: list[bool],
    censoring_kind: str = CENSOR_NONE,
    accepted_event: list[bool] | None = None,
    support_horizon: int | None = None,
    route_source: str = ROUTE_ON_POLICY,
  ) -> GroupedStoppingEvidence:
    count = int(logits.numel())
    return GroupedStoppingEvidence(
      group_id="g0",
      episode_id="ep0",
      route_source=route_source,
      row_indices=list(range(count)),
      step_indices=list(range(count)),
      env_indices=[0] * count,
      legal_mask=legal_mask,
      quality_mask=quality_mask,
      stopping_logits=logits,
      accepted_event=accepted_event,
      forced_hold=[route_source == ROUTE_FORCED_HOLD_PROBE] * count,
      censoring_kind=censoring_kind,
      support_horizon=support_horizon,
    )

  def test_supported_window_uses_survival_event_mass_not_row_bce(self) -> None:
    logits = th.tensor([0.0, 0.0, 0.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
    )

    expected_window_mass = 0.5 * 0.5 + 0.5 * 0.5 * 0.5
    self.assertAlmostEqual(result.stats.mean_p_window, expected_window_mass, places=6)
    self.assertAlmostEqual(float(result.loss.detach().item()), -math.log(expected_window_mass), places=6)
    self.assertEqual(result.stats.window_group_count, 1)
    self.assertEqual(result.stats.active_row_count, 3)

    result.loss.backward()
    self.assertIsNotNone(logits.grad)
    row_bce_sum = th.nn.functional.binary_cross_entropy_with_logits(
      logits.detach(),
      th.tensor([0.0, 1.0, 1.0]),
      reduction="sum",
    )
    self.assertNotAlmostEqual(float(result.loss.detach().item()), float(row_bce_sum.item()))

  def test_early_survival_penalty_directly_punishes_prewindow_mass(self) -> None:
    low_early_logits = th.tensor([-8.0, 0.0, 0.0], requires_grad=True)
    high_early_logits = th.tensor([4.0, 0.0, 0.0], requires_grad=True)

    low = compute_grouped_stopping_loss(
      [
        self._group(
          low_early_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      early_survival_coef=5.0,
    )
    high = compute_grouped_stopping_loss(
      [
        self._group(
          high_early_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      early_survival_coef=5.0,
    )

    self.assertLess(low.stats.mean_p_early, high.stats.mean_p_early)
    self.assertLess(float(low.loss.detach().item()), float(high.loss.detach().item()))

  def test_window_delay_penalty_prefers_earlier_quality_mass(self) -> None:
    early_logits = th.tensor([4.0, -4.0, -4.0, -4.0], requires_grad=True)
    late_logits = th.tensor([-4.0, -4.0, -4.0, 4.0], requires_grad=True)

    early = compute_grouped_stopping_loss(
      [
        self._group(
          early_logits,
          legal_mask=[True, True, True, True],
          quality_mask=[True, True, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_delay_coef=5.0,
    )
    late = compute_grouped_stopping_loss(
      [
        self._group(
          late_logits,
          legal_mask=[True, True, True, True],
          quality_mask=[True, True, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_delay_coef=5.0,
    )

    self.assertAlmostEqual(early.stats.mean_p_window, late.stats.mean_p_window, places=6)
    self.assertLess(early.stats.mean_quality_delay, late.stats.mean_quality_delay)
    self.assertLess(float(early.loss.detach().item()), float(late.loss.detach().item()))

  def test_window_deadline_penalty_prefers_mass_before_deadline(self) -> None:
    on_time_logits = th.tensor([-4.0, 4.0, -4.0, -4.0], requires_grad=True)
    late_logits = th.tensor([-4.0, -4.0, -4.0, 4.0], requires_grad=True)

    on_time = compute_grouped_stopping_loss(
      [
        self._group(
          on_time_logits,
          legal_mask=[True, True, True, True],
          quality_mask=[True, True, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_deadline_coef=2.0,
      window_deadline_steps=2,
    )
    late = compute_grouped_stopping_loss(
      [
        self._group(
          late_logits,
          legal_mask=[True, True, True, True],
          quality_mask=[True, True, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_deadline_coef=2.0,
      window_deadline_steps=2,
    )

    self.assertAlmostEqual(on_time.stats.mean_p_window, late.stats.mean_p_window, places=6)
    self.assertGreater(on_time.stats.mean_p_deadline, late.stats.mean_p_deadline)
    self.assertLess(float(on_time.loss.detach().item()), float(late.loss.detach().item()))

  def test_window_contrastive_margin_penalizes_prewindow_anchor_over_quality_anchor(self) -> None:
    bad_logits = th.tensor([1.0, -1.0, -1.0], requires_grad=True)
    good_logits = th.tensor([-1.0, 1.5, 1.0], requires_grad=True)

    bad_base = compute_grouped_stopping_loss(
      [
        self._group(
          bad_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_contrastive_margin=2.0,
    )
    bad_margin = compute_grouped_stopping_loss(
      [
        self._group(
          bad_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_contrastive_margin_coef=3.0,
      window_contrastive_margin=2.0,
    )
    good_base = compute_grouped_stopping_loss(
      [
        self._group(
          good_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_contrastive_margin=2.0,
    )
    good_margin = compute_grouped_stopping_loss(
      [
        self._group(
          good_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_contrastive_margin_coef=3.0,
      window_contrastive_margin=2.0,
    )

    self.assertAlmostEqual(bad_margin.stats.mean_quality_prewindow_logit_margin, -2.0, places=6)
    self.assertAlmostEqual(bad_margin.stats.mean_quality_prewindow_margin_loss, 4.0, places=6)
    self.assertAlmostEqual(
      float(bad_margin.loss.detach().item() - bad_base.loss.detach().item()),
      12.0,
      places=5,
    )
    self.assertGreater(good_margin.stats.mean_quality_prewindow_logit_margin, 2.0)
    self.assertAlmostEqual(good_margin.stats.mean_quality_prewindow_margin_loss, 0.0, places=6)
    self.assertAlmostEqual(
      float(good_margin.loss.detach().item()),
      float(good_base.loss.detach().item()),
      places=6,
    )

  def test_window_quality_boundary_penalty_requires_at_least_one_quality_anchor_near_threshold(self) -> None:
    low_quality_logits = th.tensor([-3.0, -2.0, -4.0], requires_grad=True)
    high_quality_logits = th.tensor([-3.0, 0.5, -4.0], requires_grad=True)

    low_base = compute_grouped_stopping_loss(
      [
        self._group(
          low_quality_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_quality_boundary_logit=0.0,
    )
    low_boundary = compute_grouped_stopping_loss(
      [
        self._group(
          low_quality_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_quality_boundary_coef=2.0,
      window_quality_boundary_logit=0.0,
    )
    high_base = compute_grouped_stopping_loss(
      [
        self._group(
          high_quality_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_quality_boundary_logit=0.0,
    )
    high_boundary = compute_grouped_stopping_loss(
      [
        self._group(
          high_quality_logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_quality_boundary_coef=2.0,
      window_quality_boundary_logit=0.0,
    )

    self.assertAlmostEqual(low_boundary.stats.mean_quality_boundary_logit, -2.0, places=6)
    self.assertAlmostEqual(low_boundary.stats.mean_quality_boundary_margin_loss, 2.0, places=6)
    self.assertAlmostEqual(
      float(low_boundary.loss.detach().item() - low_base.loss.detach().item()),
      4.0,
      places=5,
    )
    self.assertAlmostEqual(high_boundary.stats.mean_quality_boundary_logit, 0.5, places=6)
    self.assertAlmostEqual(high_boundary.stats.mean_quality_boundary_margin_loss, 0.0, places=6)
    self.assertAlmostEqual(
      float(high_boundary.loss.detach().item()),
      float(high_base.loss.detach().item()),
      places=6,
    )

  def test_window_balanced_bce_penalizes_all_high_prewindow_logits(self) -> None:
    all_high = th.tensor([4.0, 4.0, 4.0], requires_grad=True)
    separated = th.tensor([-4.0, 4.0, 4.0], requires_grad=True)

    bad = compute_grouped_stopping_loss(
      [
        self._group(
          all_high,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_balanced_bce_coef=3.0,
    )
    good = compute_grouped_stopping_loss(
      [
        self._group(
          separated,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_balanced_bce_coef=3.0,
    )

    self.assertGreater(bad.stats.mean_window_balanced_bce_loss, good.stats.mean_window_balanced_bce_loss)
    self.assertLess(float(good.loss.detach().item()), float(bad.loss.detach().item()))

  def test_long_prewindow_keeps_survival_gradient_in_log_domain(self) -> None:
    logits = th.cat((th.zeros(800), th.full((100,), -8.0))).requires_grad_()
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True] * 900,
          quality_mask=([False] * 800) + ([True] * 100),
        )
      ],
      early_mass_coef=0.0,
      early_survival_coef=1.0,
      window_delay_coef=0.0,
      window_deadline_coef=0.0,
      window_quality_boundary_coef=0.0,
      window_contrastive_margin_coef=0.0,
      window_balanced_bce_coef=0.0,
    )

    result.loss.backward()

    self.assertTrue(th.isfinite(result.loss))
    self.assertIsNotNone(logits.grad)
    assert logits.grad is not None
    self.assertGreater(float(logits.grad[:800].mean().item()), 0.0)
    self.assertLess(float(logits.grad[800:].mean().item()), 0.0)

  def test_scale_separated_contract_punishes_prewindow_scale_and_quality_anchor_separately(self) -> None:
    logits = th.cat((th.zeros(800), th.full((100,), -2.0))).requires_grad_()
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True] * 900,
          quality_mask=([False] * 800) + ([True] * 100),
        )
      ],
      early_mass_coef=0.0,
      window_prewindow_hazard_scale_coef=1.0,
      window_prewindow_hazard_target=0.0,
      early_mass_budget=0.02,
      window_quality_hazard_target_coef=1.0,
      window_quality_hazard_target=0.75,
    )

    result.loss.backward()

    self.assertGreater(result.stats.mean_prewindow_hazard_mean, result.stats.mean_prewindow_hazard_target)
    self.assertGreater(result.stats.mean_prewindow_hazard_scale_loss, 0.0)
    self.assertAlmostEqual(result.stats.mean_quality_hazard_target, 0.75, places=6)
    self.assertGreater(result.stats.mean_quality_hazard_target_loss, 0.0)
    self.assertIsNotNone(logits.grad)
    assert logits.grad is not None
    self.assertGreater(float(logits.grad[:800].mean().item()), 0.0)
    self.assertLess(float(logits.grad[800:].mean().item()), 0.0)

  def test_logit_calibration_contract_pushes_prewindow_down_and_quality_up(self) -> None:
    logits = th.tensor([0.0, -1.0, -1.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True, True, True],
          quality_mask=[False, True, True],
        )
      ],
      early_mass_coef=0.0,
      window_prewindow_logit_ceiling_coef=2.0,
      window_prewindow_logit_ceiling=-2.0,
      window_quality_logit_floor_coef=2.0,
      window_quality_logit_floor=2.0,
    )

    result.loss.backward()

    self.assertAlmostEqual(result.stats.mean_prewindow_logit_ceiling, 0.0, places=6)
    self.assertAlmostEqual(result.stats.mean_prewindow_logit_ceiling_loss, 4.0, places=6)
    self.assertAlmostEqual(result.stats.mean_quality_logit_floor, -1.0, places=6)
    self.assertAlmostEqual(result.stats.mean_quality_logit_floor_loss, 9.0, places=6)
    self.assertIsNotNone(logits.grad)
    assert logits.grad is not None
    self.assertGreater(float(logits.grad[0].item()), 0.0)
    self.assertLess(float(logits.grad[1:].mean().item()), 0.0)

  def test_legal_mask_blocks_hazard_but_counts_closed_boundary_attempts(self) -> None:
    logits = th.tensor([8.0, 8.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[False, True],
          quality_mask=[False, True],
        )
      ],
      early_mass_coef=0.0,
      boundary_threshold=0.0,
    )

    expected_window_mass = float(th.sigmoid(th.tensor(8.0)).item())
    self.assertAlmostEqual(result.stats.mean_p_window, expected_window_mass, places=6)
    self.assertEqual(result.stats.closed_mask_stop_attempt_count, 1)
    self.assertEqual(result.stats.boundary_cross_count, 1)
    self.assertEqual(result.stats.boundary_cross_in_window_count, 1)

  def test_no_window_timeout_uses_right_censor_no_event_mass(self) -> None:
    logits = th.tensor([0.0, 0.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True, True],
          quality_mask=[False, False],
          censoring_kind=CENSOR_TIMEOUT,
        )
      ]
    )

    expected_no_event = 0.25
    self.assertAlmostEqual(result.stats.mean_p_none, expected_no_event, places=6)
    self.assertAlmostEqual(float(result.loss.detach().item()), -math.log(expected_no_event), places=6)
    self.assertEqual(result.stats.no_window_group_count, 1)
    self.assertEqual(result.stats.right_censor_group_count, 1)

  def test_early_event_prefix_does_not_train_unobserved_suffix(self) -> None:
    logits = th.tensor([0.0, 0.0, 8.0, 8.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True, True, True, True],
          quality_mask=[False, False, True, True],
          accepted_event=[False, True, False, False],
          censoring_kind=CENSOR_EARLY_EVENT_PREFIX,
        )
      ],
      early_mass_coef=0.0,
    )

    self.assertAlmostEqual(result.stats.mean_p_none, 0.5, places=6)
    self.assertAlmostEqual(float(result.loss.detach().item()), -math.log(0.5), places=6)
    self.assertEqual(result.stats.early_prefix_group_count, 1)

    result.loss.backward()
    self.assertAlmostEqual(float(logits.grad[0].item()), 0.5, places=6)
    self.assertAlmostEqual(float(logits.grad[1].item()), 0.0, places=6)
    self.assertAlmostEqual(float(logits.grad[2].item()), 0.0, places=6)
    self.assertAlmostEqual(float(logits.grad[3].item()), 0.0, places=6)

  def test_support_horizon_chunks_by_complete_supported_prefix(self) -> None:
    logits = th.tensor([0.0, 0.0, 8.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[True, True, True],
          quality_mask=[False, False, True],
          support_horizon=1,
          censoring_kind=CENSOR_FORCED_HOLD,
          route_source=ROUTE_FORCED_HOLD_PROBE,
        )
      ]
    )

    self.assertEqual(result.stats.active_row_count, 2)
    self.assertEqual(result.stats.no_window_group_count, 1)
    self.assertEqual(result.stats.right_censor_group_count, 1)
    self.assertAlmostEqual(result.stats.mean_p_none, 0.25, places=6)

  def test_all_closed_mask_group_is_diagnostic_only(self) -> None:
    logits = th.tensor([8.0, 8.0], requires_grad=True)
    result = compute_grouped_stopping_loss(
      [
        self._group(
          logits,
          legal_mask=[False, False],
          quality_mask=[True, True],
        )
      ]
    )

    self.assertEqual(float(result.loss.detach().item()), 0.0)
    self.assertEqual(result.stats.active_group_count, 0)
    self.assertEqual(result.stats.active_row_count, 0)
    self.assertEqual(result.stats.skipped_group_count, 1)
    self.assertEqual(result.stats.closed_mask_stop_attempt_count, 2)

  def test_empty_and_unsupported_groups_return_zero_loss_with_stats(self) -> None:
    empty = self._group(th.tensor([], dtype=th.float32), legal_mask=[], quality_mask=[])
    unsupported = self._group(
      th.tensor([0.0]),
      legal_mask=[True],
      quality_mask=[True],
      censoring_kind=CENSOR_UNSUPPORTED,
    )
    result = compute_grouped_stopping_loss([empty, unsupported])

    self.assertEqual(float(result.loss.detach().item()), 0.0)
    self.assertEqual(result.stats.group_count, 2)
    self.assertEqual(result.stats.active_group_count, 0)
    self.assertEqual(result.stats.skipped_group_count, 2)
    self.assertEqual(result.stats.unsupported_group_count, 1)


if __name__ == "__main__":
  unittest.main()
