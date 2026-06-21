from __future__ import annotations

import unittest

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.first_event_hazard import (
  FIRST_EVENT_FIELD_ACTIVE,
  FIRST_EVENT_FIELD_TARGET,
  FIRST_EVENT_FIELD_WEIGHT,
  FIRST_EVENT_SOURCE_ACCEPTED,
  FIRST_EVENT_SOURCE_CENSORED,
  FIRST_EVENT_SOURCE_CURRICULUM,
  FIRST_EVENT_SOURCE_DEADLINE,
  FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
  FIRST_EVENT_SOURCE_INACTIVE,
  FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
  FIRST_EVENT_SOURCE_PREWINDOW,
  FIRST_EVENT_SOURCE_SHADOW_QUALITY,
  build_first_event_hazard_labels,
  compute_first_event_credit_loss,
  compute_first_event_hazard_loss,
  current_first_event_curriculum_coef,
  first_event_hazard_batch_from_rollout_data,
)
from python.rl.policy_algo.first_event_projection import project_air_combat_c2_roe_legal_open_observations
from python.rl.policy_algo.policies import _HybridActionDistribution, _normalize_hybrid_action_layout


class FirstEventTimingContractTests(unittest.TestCase):
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
    self.assertTrue(th.equal(labels.source[:3], th.full((3,), FIRST_EVENT_SOURCE_ACCEPTED, dtype=th.long)))
    self.assertEqual(int(labels.source[4]), 0)
    self.assertEqual(int(labels.source[5]), FIRST_EVENT_SOURCE_CENSORED)
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
    self.assertEqual(int(labels.source[0]), FIRST_EVENT_SOURCE_CENSORED)
    self.assertEqual(int(labels.source[1]), FIRST_EVENT_SOURCE_CENSORED)
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
      (labels.source == FIRST_EVENT_SOURCE_CURRICULUM)
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
    self.assertTrue(th.equal(labels.source[3:6], th.full((3,), FIRST_EVENT_SOURCE_DEADLINE, dtype=th.long)))
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
    self.assertTrue(th.equal(labels.source[:3], th.full((3,), FIRST_EVENT_SOURCE_PREWINDOW, dtype=th.long)))
    self.assertTrue(th.equal(labels.source[3:], th.full((3,), FIRST_EVENT_SOURCE_DEADLINE, dtype=th.long)))

  def test_legal_open_quality_credit_marks_no_release_quality_rows_before_deadline(self) -> None:
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
      legal_open_quality_weight=0.75,
      legal_open_quality_min_window_age_steps=3,
    )

    self.assertTrue(th.equal(labels.active, th.ones((6,), dtype=th.bool)))
    self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 0, 1, 1, 1], dtype=th.float32)))
    self.assertTrue(th.allclose(labels.weight, th.tensor([0.2, 0.2, 0.2, 0.75, 0.75, 0.75])))
    self.assertTrue(th.equal(labels.source[:3], th.full((3,), FIRST_EVENT_SOURCE_PREWINDOW, dtype=th.long)))
    self.assertTrue(
      th.equal(labels.source[3:], th.full((3,), FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY, dtype=th.long))
    )

  def test_legal_open_quality_credit_requires_launch_window_evidence(self) -> None:
    labels = build_first_event_hazard_labels(
      engagement_state=["AuthorizedReady"] * 4,
      fire_mask=[1, 1, 1, 1],
      fire_once_accepted=[0, 0, 0, 0],
      episode_id=[0, 0, 0, 0],
      legal_open_quality_weight=0.75,
    )

    self.assertTrue(th.all(labels.active == th.zeros_like(labels.active)))
    self.assertTrue(th.all(labels.weight == th.zeros_like(labels.weight)))
    self.assertTrue(th.all(labels.source == FIRST_EVENT_SOURCE_CENSORED))

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
    self.assertEqual(int(labels.source[0]), FIRST_EVENT_SOURCE_PREWINDOW)
    self.assertEqual(int(labels.source[1]), FIRST_EVENT_SOURCE_EARLY_ACCEPTED)
    self.assertTrue(th.equal(labels.had_accepted[:2], th.tensor([1, 1], dtype=th.bool)))

  def test_shadow_quality_repair_adds_post_early_positive_credit_without_reopening_fire_mask(self) -> None:
    labels = build_first_event_hazard_labels(
      engagement_state=[
        "AuthorizedReady",
        "AuthorizedReady",
        "FiredAssess",
        "FiredAssess",
        "FiredAssess",
        "FiredAssess",
      ],
      fire_mask=[1, 1, 0, 0, 0, 0],
      fire_once_accepted=[0, 1, 0, 0, 0, 0],
      episode_id=[0, 0, 0, 0, 0, 0],
      launch_window_open=[0, 0, 0, 1, 1, 1],
      launch_window_min_window_age_steps=3,
      launch_window_prewindow_hold_weight=0.25,
      launch_window_early_accept_weight=0.75,
      shadow_quality_after_early_accept=True,
      shadow_quality_positive_weight=0.5,
      legal_open_quality_weight=0.75,
    )

    self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 0, 1, 1, 1], dtype=th.bool)))
    self.assertTrue(th.allclose(labels.target, th.tensor([0, 0, 0, 1, 1, 1], dtype=th.float32)))
    self.assertTrue(th.allclose(labels.weight, th.tensor([0.25, 0.75, 0.0, 0.5, 0.5, 0.5])))
    self.assertEqual(int(labels.source[0]), FIRST_EVENT_SOURCE_PREWINDOW)
    self.assertEqual(int(labels.source[1]), FIRST_EVENT_SOURCE_EARLY_ACCEPTED)
    self.assertTrue(th.equal(labels.source[3:], th.full((3,), FIRST_EVENT_SOURCE_SHADOW_QUALITY)))
    self.assertTrue(th.equal(labels.window_id[[0, 1, 3, 4, 5]], th.zeros((5,), dtype=th.long)))
    self.assertTrue(th.all(labels.window_id[2] < 0))
    self.assertTrue(th.equal(labels.had_accepted[[0, 1, 3, 4, 5]], th.ones((5,), dtype=th.bool)))

  def test_shadow_quality_repair_keeps_early_accepted_negative_when_no_future_quality_exists(self) -> None:
    labels = build_first_event_hazard_labels(
      engagement_state=["AuthorizedReady", "AuthorizedReady", "FiredAssess", "FiredAssess"],
      fire_mask=[1, 1, 0, 0],
      fire_once_accepted=[0, 1, 0, 0],
      episode_id=[0, 0, 0, 0],
      launch_window_open=[0, 0, 0, 0],
      launch_window_prewindow_hold_weight=0.25,
      launch_window_early_accept_weight=0.75,
      shadow_quality_after_early_accept=True,
      shadow_quality_positive_weight=0.5,
    )

    self.assertTrue(th.equal(labels.active, th.tensor([1, 1, 0, 0], dtype=th.bool)))
    self.assertTrue(th.allclose(labels.target, th.zeros(4)))
    self.assertTrue(th.all(labels.source[2:] == FIRST_EVENT_SOURCE_INACTIVE))

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
    self.assertTrue(th.equal(labels.source[:3], th.full((3,), FIRST_EVENT_SOURCE_ACCEPTED)))

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

    setattr(_RolloutData, FIRST_EVENT_FIELD_ACTIVE, th.tensor([1, 0], dtype=th.float32))
    setattr(_RolloutData, FIRST_EVENT_FIELD_TARGET, th.tensor([1, 0], dtype=th.float32))
    setattr(_RolloutData, FIRST_EVENT_FIELD_WEIGHT, th.tensor([0.5, 0.0], dtype=th.float32))

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

  def test_shadow_quality_credit_can_skip_delta_alignment_for_closed_mask_rows(self) -> None:
    q_values = th.zeros((2, 2), dtype=th.float32, requires_grad=True)
    event_delta = th.ones((2,), dtype=th.float32, requires_grad=True)
    target = th.ones((2,), dtype=th.float32)
    active = th.ones((2,), dtype=th.bool)
    weight = th.ones((2,), dtype=th.float32)
    delta_align_active = th.tensor([0, 1], dtype=th.bool)

    result = compute_first_event_credit_loss(
      q_values,
      target,
      active,
      weight,
      event_logit_delta=event_delta,
      value_coef=0.0,
      delta_align_coef=1.0,
      delta_align_active=delta_align_active,
    )
    result.loss.backward()

    self.assertIsNotNone(event_delta.grad)
    assert event_delta.grad is not None
    self.assertAlmostEqual(float(event_delta.grad[0].detach().cpu().item()), 0.0, places=8)
    self.assertNotEqual(float(event_delta.grad[1].detach().cpu().item()), 0.0)

  def test_legal_state_projection_rewrites_only_event_legality_surface(self) -> None:
    mission = th.zeros((2, 20), dtype=th.float32)
    mission[:, 5] = 1.0
    mission[:, 6] = 0.0
    mission[:, 14] = 4.0
    mission[:, 15] = 0.0
    mission[:, 16] = 0.0
    mission[:, 17] = 1.0
    mission[:, 19] = 0.0
    contacts = th.zeros((2, 10, 5), dtype=th.float32)
    contacts[0, 0, 0] = 16000.0
    obs = {
      "mission": mission,
      "contacts": contacts,
      "event_action_mask": th.tensor([[1, 0], [1, 0]], dtype=th.float32),
      "fire_mask": th.zeros((2,), dtype=th.float32),
      "instruments": th.ones((2, 4), dtype=th.float32),
    }

    projection = project_air_combat_c2_roe_legal_open_observations(obs, th.tensor([1, 1], dtype=th.bool))

    self.assertIsNotNone(projection)
    assert projection is not None
    self.assertTrue(th.equal(projection.active, th.tensor([1, 0], dtype=th.bool)))
    self.assertEqual(projection.unsupported_count, 1)
    projected_mission = projection.observations["mission"]
    self.assertEqual(float(projected_mission[0, 5].item()), 2.0)
    self.assertEqual(float(projected_mission[0, 6].item()), 1.0)
    self.assertEqual(float(projected_mission[0, 14].item()), 2.0)
    self.assertEqual(float(projected_mission[0, 15].item()), 1.0)
    self.assertEqual(float(projected_mission[0, 16].item()), 1.0)
    self.assertEqual(float(projected_mission[0, 17].item()), 0.0)
    self.assertEqual(float(projected_mission[0, 19].item()), 1.0)
    self.assertTrue(th.equal(projection.observations["event_action_mask"][0], th.tensor([1.0, 1.0])))
    self.assertEqual(float(projection.observations["fire_mask"][0].item()), 1.0)
    self.assertTrue(th.equal(projection.observations["instruments"], obs["instruments"]))
    self.assertTrue(th.equal(obs["event_action_mask"][0], th.tensor([1.0, 0.0])))

  def test_legal_state_projection_rewrites_c2_roe_v2_explicit_fire_mask(self) -> None:
    mode = "air_combat_c2_roe_v2"
    mission = th.zeros((1, mission_observation_dim(mode)), dtype=th.float32)
    mission[:, mission_observation_field_index(mode, "wcs_state")] = 1.0
    mission[:, mission_observation_field_index(mode, "target_contact_present")] = 1.0
    mission[:, mission_observation_field_index(mode, "fire_mask_open")] = 0.0
    obs = {
      "mission": mission,
      "event_action_mask": th.tensor([[1, 0]], dtype=th.float32),
      "fire_mask": th.zeros((1,), dtype=th.float32),
    }

    projection = project_air_combat_c2_roe_legal_open_observations(obs, th.ones((1,), dtype=th.bool))

    self.assertIsNotNone(projection)
    assert projection is not None
    projected_mission = projection.observations["mission"]
    self.assertEqual(float(projected_mission[0, mission_observation_field_index(mode, "wcs_state")].item()), 2.0)
    self.assertEqual(
      float(projected_mission[0, mission_observation_field_index(mode, "authorization_to_fire")].item()),
      1.0,
    )
    self.assertEqual(
      float(projected_mission[0, mission_observation_field_index(mode, "fire_mask_open")].item()),
      1.0,
    )
    self.assertEqual(
      float(projected_mission[0, mission_observation_field_index(mode, "quality_window_ready")].item()),
      1.0,
    )
    self.assertTrue(th.equal(projection.observations["event_action_mask"][0], th.tensor([1.0, 1.0])))
    self.assertEqual(float(projection.observations["fire_mask"][0].item()), 1.0)

  def test_legal_state_projection_refuses_unsupported_mission_layout(self) -> None:
    projection = project_air_combat_c2_roe_legal_open_observations(
      {"mission": th.zeros((1, 21), dtype=th.float32)},
      th.ones((1,), dtype=th.bool),
    )

    self.assertIsNone(projection)

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
