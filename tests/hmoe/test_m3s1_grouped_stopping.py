from __future__ import annotations

import math
import unittest

import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.m3s1_grouped_stopping import (
    M3S1_CENSOR_EARLY_EVENT_PREFIX,
    M3S1_CENSOR_FORCED_HOLD,
    M3S1_CENSOR_NONE,
    M3S1_CENSOR_TIMEOUT,
    M3S1_CENSOR_UNSUPPORTED,
    M3S1_ROUTE_FORCED_HOLD_PROBE,
    M3S1_ROUTE_ON_POLICY,
    M3S1GroupedStoppingEvidence,
    compute_m3s1_grouped_stopping_loss,
)


class M3S1GroupedStoppingTests(unittest.TestCase):
    def _group(
        self,
        logits: th.Tensor,
        *,
        legal_mask: list[bool],
        quality_mask: list[bool],
        censoring_kind: str = M3S1_CENSOR_NONE,
        accepted_event: list[bool] | None = None,
        support_horizon: int | None = None,
        route_source: str = M3S1_ROUTE_ON_POLICY,
    ) -> M3S1GroupedStoppingEvidence:
        count = int(logits.numel())
        return M3S1GroupedStoppingEvidence(
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
            forced_hold=[route_source == M3S1_ROUTE_FORCED_HOLD_PROBE] * count,
            censoring_kind=censoring_kind,
            support_horizon=support_horizon,
        )

    def test_supported_window_uses_survival_event_mass_not_row_bce(self) -> None:
        logits = th.tensor([0.0, 0.0, 0.0], requires_grad=True)
        result = compute_m3s1_grouped_stopping_loss(
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

    def test_legal_mask_blocks_hazard_but_counts_closed_boundary_attempts(self) -> None:
        logits = th.tensor([8.0, 8.0], requires_grad=True)
        result = compute_m3s1_grouped_stopping_loss(
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
        result = compute_m3s1_grouped_stopping_loss(
            [
                self._group(
                    logits,
                    legal_mask=[True, True],
                    quality_mask=[False, False],
                    censoring_kind=M3S1_CENSOR_TIMEOUT,
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
        result = compute_m3s1_grouped_stopping_loss(
            [
                self._group(
                    logits,
                    legal_mask=[True, True, True, True],
                    quality_mask=[False, False, True, True],
                    accepted_event=[False, True, False, False],
                    censoring_kind=M3S1_CENSOR_EARLY_EVENT_PREFIX,
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
        result = compute_m3s1_grouped_stopping_loss(
            [
                self._group(
                    logits,
                    legal_mask=[True, True, True],
                    quality_mask=[False, False, True],
                    support_horizon=1,
                    censoring_kind=M3S1_CENSOR_FORCED_HOLD,
                    route_source=M3S1_ROUTE_FORCED_HOLD_PROBE,
                )
            ]
        )

        self.assertEqual(result.stats.active_row_count, 2)
        self.assertEqual(result.stats.no_window_group_count, 1)
        self.assertEqual(result.stats.right_censor_group_count, 1)
        self.assertAlmostEqual(result.stats.mean_p_none, 0.25, places=6)

    def test_all_closed_mask_group_is_diagnostic_only(self) -> None:
        logits = th.tensor([8.0, 8.0], requires_grad=True)
        result = compute_m3s1_grouped_stopping_loss(
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
            censoring_kind=M3S1_CENSOR_UNSUPPORTED,
        )
        result = compute_m3s1_grouped_stopping_loss([empty, unsupported])

        self.assertEqual(float(result.loss.detach().item()), 0.0)
        self.assertEqual(result.stats.group_count, 2)
        self.assertEqual(result.stats.active_group_count, 0)
        self.assertEqual(result.stats.skipped_group_count, 2)
        self.assertEqual(result.stats.unsupported_group_count, 1)


if __name__ == "__main__":
    unittest.main()
