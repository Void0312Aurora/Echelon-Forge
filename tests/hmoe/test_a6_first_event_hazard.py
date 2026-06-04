from __future__ import annotations

import unittest

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo.first_event_hazard import (
    A6_FIRST_EVENT_FIELD_ACTIVE,
    A6_FIRST_EVENT_FIELD_TARGET,
    A6_FIRST_EVENT_FIELD_WEIGHT,
    A6_FIRST_EVENT_SOURCE_ACCEPTED,
    A6_FIRST_EVENT_SOURCE_CENSORED,
    A6_FIRST_EVENT_SOURCE_CURRICULUM,
    A6_FIRST_EVENT_SOURCE_DEADLINE,
    A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
    A6_FIRST_EVENT_SOURCE_PREWINDOW,
    build_first_event_hazard_labels,
    compute_first_event_hazard_loss,
    current_first_event_curriculum_coef,
    first_event_hazard_batch_from_rollout_data,
)
from python.rl.policy_algo.policies import _HybridActionDistribution, _normalize_hybrid_action_layout


class A6FirstEventHazardTests(unittest.TestCase):
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

    def test_accepted_window_builds_pre_survival_and_positive_tau_labels(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=[
                "AuthorizedReady",
                "AuthorizedReady",
                "AuthorizedReady",
                "AuthorizedReady",
                "ReattackReady",
                "AuthorizedReady",
                "AuthorizedReady",
            ],
            fire_mask=[1, 1, 1, 1, 1, 1, 1],
            fire_once_accepted=[0, 0, 1, 0, 0, 0, 0],
            episode_id=[0, 0, 0, 0, 0, 1, 1],
        )

        self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 1, 0, 0, 0, 0], dtype=th.bool)))
        self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 1, 0, 0, 0, 0], dtype=th.float32)))
        self.assertTrue(th.equal(labels.source[:3], th.full((3,), A6_FIRST_EVENT_SOURCE_ACCEPTED, dtype=th.long)))
        self.assertEqual(int(labels.source[4]), 0)
        self.assertEqual(int(labels.source[5]), A6_FIRST_EVENT_SOURCE_CENSORED)
        self.assertTrue(th.all(labels.weight[5:] == 0.0))

    def test_censored_windows_do_not_create_default_full_window_negatives(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=["AuthorizedReady", "AuthorizedReady", "Hold", "ReattackReady"],
            fire_mask=[1, 1, 0, 1],
            fire_once_accepted=[0, 0, 0, 0],
            episode_id=[0, 0, 0, 0],
        )

        self.assertTrue(th.all(labels.active == th.zeros_like(labels.active)))
        self.assertTrue(th.all(labels.weight == th.zeros_like(labels.weight)))
        self.assertEqual(int(labels.source[0]), A6_FIRST_EVENT_SOURCE_CENSORED)
        self.assertEqual(int(labels.source[1]), A6_FIRST_EVENT_SOURCE_CENSORED)
        self.assertEqual(int(labels.source[3]), 0)

    def test_curriculum_creates_one_positive_seed_per_episode_inside_authorized_open_window(self) -> None:
        states = ["AuthorizedReady"] * 40 + ["ReattackReady"] * 40
        fire_mask = [1] * 80
        labels = build_first_event_hazard_labels(
            engagement_state=states,
            fire_mask=fire_mask,
            fire_once_accepted=[0] * 80,
            episode_id=[0] * 40 + [1] * 40,
            curriculum_weight=0.5,
            curriculum_min_window_age_steps=32,
        )

        curriculum_positive = (
            (labels.source == A6_FIRST_EVENT_SOURCE_CURRICULUM)
            & (labels.target > 0.5)
            & (labels.weight > 0.0)
        )
        self.assertEqual(int(curriculum_positive.sum().item()), 1)
        self.assertEqual(int(th.nonzero(curriculum_positive, as_tuple=False).flatten()[0].item()), 31)
        self.assertTrue(th.all(labels.active[:32]))
        self.assertTrue(th.all(labels.weight[:32] == 0.5))
        self.assertTrue(th.all(labels.source[40:] == 0))

    def test_deadline_bootstrap_marks_sustained_positive_after_window_age_threshold(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=["AuthorizedReady"] * 6 + ["Hold"],
            fire_mask=[1, 1, 1, 1, 1, 1, 0],
            fire_once_accepted=[0, 0, 0, 0, 0, 0, 0],
            episode_id=[0, 0, 0, 0, 0, 0, 0],
            deadline_weight=0.25,
            deadline_min_window_age_steps=4,
        )

        self.assertTrue(th.equal(labels.active, th.tensor([0, 0, 0, 1, 1, 1, 0], dtype=th.bool)))
        self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 0, 1, 1, 1, 0], dtype=th.float32)))
        self.assertTrue(th.allclose(labels.weight, th.tensor([0, 0, 0, 0.25, 0.25, 0.25, 0], dtype=th.float32)))
        self.assertTrue(th.equal(labels.source[3:6], th.full((3,), A6_FIRST_EVENT_SOURCE_DEADLINE, dtype=th.long)))
        self.assertEqual(int(labels.source[6]), 0)

    def test_launch_window_gate_marks_prewindow_hold_and_delays_deadline_positive(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=["AuthorizedReady"] * 6,
            fire_mask=[1, 1, 1, 1, 1, 1],
            fire_once_accepted=[0, 0, 0, 0, 0, 0],
            episode_id=[0, 0, 0, 0, 0, 0],
            launch_window_open=[0, 0, 0, 1, 1, 1],
            launch_window_min_window_age_steps=3,
            launch_window_prewindow_hold_weight=0.2,
            deadline_weight=0.5,
            deadline_min_window_age_steps=2,
        )

        self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 1, 1, 1, 1], dtype=th.bool)))
        self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 0, 1, 1, 1], dtype=th.float32)))
        self.assertTrue(th.allclose(labels.weight, th.tensor([0.2, 0.2, 0.2, 0.5, 0.5, 0.5])))
        self.assertTrue(th.equal(labels.source[:3], th.full((3,), A6_FIRST_EVENT_SOURCE_PREWINDOW, dtype=th.long)))
        self.assertTrue(th.equal(labels.source[3:], th.full((3,), A6_FIRST_EVENT_SOURCE_DEADLINE, dtype=th.long)))

    def test_launch_window_gate_treats_early_accepted_release_as_negative(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=["AuthorizedReady"] * 4,
            fire_mask=[1, 1, 1, 1],
            fire_once_accepted=[0, 1, 0, 0],
            episode_id=[0, 0, 0, 0],
            launch_window_open=[0, 0, 1, 1],
            launch_window_prewindow_hold_weight=0.25,
            launch_window_early_accept_weight=0.75,
        )

        self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 0, 0], dtype=th.bool)))
        self.assertTrue(th.allclose(labels.target, th.zeros(4)))
        self.assertTrue(th.allclose(labels.weight, th.tensor([0.25, 0.75, 0.0, 0.0])))
        self.assertEqual(int(labels.source[0]), A6_FIRST_EVENT_SOURCE_PREWINDOW)
        self.assertEqual(int(labels.source[1]), A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED)
        self.assertTrue(th.equal(labels.had_accepted[:2], th.tensor([1, 1], dtype=th.bool)))

    def test_launch_window_gate_keeps_accepted_positive_inside_quality_window(self) -> None:
        labels = build_first_event_hazard_labels(
            engagement_state=["AuthorizedReady"] * 4,
            fire_mask=[1, 1, 1, 1],
            fire_once_accepted=[0, 0, 1, 0],
            episode_id=[0, 0, 0, 0],
            launch_window_open=[0, 1, 1, 1],
            launch_window_min_window_age_steps=2,
            launch_window_prewindow_hold_weight=0.25,
        )

        self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 1, 0], dtype=th.bool)))
        self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 1, 0], dtype=th.float32)))
        self.assertTrue(th.allclose(labels.weight, th.tensor([1.0, 1.0, 1.0, 0.0])))
        self.assertTrue(th.equal(labels.source[:3], th.full((3,), A6_FIRST_EVENT_SOURCE_ACCEPTED)))

    def test_curriculum_schedule_is_zero_after_first_quarter_training(self) -> None:
        self.assertAlmostEqual(
            current_first_event_curriculum_coef(2.0, progress_remaining=1.0),
            2.0,
            places=6,
        )
        self.assertAlmostEqual(
            current_first_event_curriculum_coef(2.0, progress_remaining=0.875),
            1.0,
            places=6,
        )
        self.assertAlmostEqual(
            current_first_event_curriculum_coef(2.0, progress_remaining=0.75),
            0.0,
            places=6,
        )
        self.assertAlmostEqual(
            current_first_event_curriculum_coef(2.0, progress_remaining=0.25),
            0.0,
            places=6,
        )

    def test_hazard_loss_zero_when_coef_zero_or_no_active_weight(self) -> None:
        logits = th.tensor([-2.0, 0.5], dtype=th.float32, requires_grad=True)
        target = th.tensor([0.0, 1.0], dtype=th.float32)
        active = th.tensor([1, 1], dtype=th.bool)
        zero_coef = compute_first_event_hazard_loss(logits, target, active, coef=0.0)
        self.assertEqual(float(zero_coef.loss.detach().cpu().item()), 0.0)

        inactive = compute_first_event_hazard_loss(logits, target, th.zeros_like(active), coef=1.0)
        self.assertEqual(float(inactive.loss.detach().cpu().item()), 0.0)

    def test_rollout_interface_reads_auxiliary_fields_outside_policy_observations(self) -> None:
        class _RolloutData:
            observations = {"mission": th.zeros((2, 20), dtype=th.float32)}

        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_ACTIVE, th.tensor([1, 0], dtype=th.float32))
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_TARGET, th.tensor([1, 0], dtype=th.float32))
        setattr(_RolloutData, A6_FIRST_EVENT_FIELD_WEIGHT, th.tensor([0.5, 0.0], dtype=th.float32))

        batch = first_event_hazard_batch_from_rollout_data(_RolloutData)

        self.assertIsNotNone(batch)
        assert batch is not None
        active, target, weight = batch
        self.assertTrue(th.equal(active, th.tensor([1, 0], dtype=th.bool)))
        self.assertTrue(th.allclose(target, th.tensor([1.0, 0.0])))
        self.assertTrue(th.allclose(weight, th.tensor([0.5, 0.0])))

    def test_accepted_and_curriculum_labels_produce_finite_gradients_on_delta(self) -> None:
        logits = th.tensor([-1.5, 0.25, 1.0], dtype=th.float32, requires_grad=True)
        target = th.tensor([0.0, 1.0, 1.0], dtype=th.float32)
        active = th.tensor([1, 1, 1], dtype=th.bool)
        weight = th.tensor([1.0, 1.0, 0.5], dtype=th.float32)

        result = compute_first_event_hazard_loss(logits, target, active, weight, coef=2.0)
        self.assertTrue(th.isfinite(result.loss))
        self.assertGreater(float(result.loss.detach().cpu().item()), 0.0)
        result.loss.backward()
        self.assertIsNotNone(logits.grad)
        self.assertTrue(th.isfinite(logits.grad).all())
        self.assertGreater(float(logits.grad.detach().abs().sum().cpu().item()), 0.0)

    def test_event_logit_delta_is_unmasked_while_categorical_semantics_stay_masked(self) -> None:
        params = th.zeros((2, 20), dtype=th.float32)
        params[:, 9] = 4.0
        params[:, 11] = -1.0
        dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.zeros((2,), dtype=th.bool))
        hold_actions = th.zeros((2, 12), dtype=th.float32)
        fire_actions = hold_actions.clone()
        fire_actions[:, 9] = 1.0

        delta = dist.fire_event_logit_delta()
        probability = dist.fire_event_probability()
        deterministic_actions = dist.get_actions(deterministic=True)
        stochastic_actions = dist.get_actions(deterministic=False)
        hold_log_prob = dist.log_prob(hold_actions)
        fire_log_prob = dist.log_prob(fire_actions)
        entropy = dist.entropy()

        self.assertIsNotNone(delta)
        self.assertTrue(th.allclose(delta, th.full((2,), 5.0)))
        self.assertIsNotNone(probability)
        self.assertTrue(np.allclose(probability.detach().cpu().numpy(), np.full((2,), 0.9933072), atol=1e-6))
        self.assertTrue(th.all(deterministic_actions[:, 9] == 0.0))
        self.assertTrue(th.all(stochastic_actions[:, 9] == 0.0))
        self.assertTrue(th.all(fire_log_prob < hold_log_prob - 1.0e6))
        self.assertTrue(th.isfinite(entropy).all())


if __name__ == "__main__":
    unittest.main()
