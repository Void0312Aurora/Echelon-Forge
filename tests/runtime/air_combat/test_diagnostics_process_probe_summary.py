from __future__ import annotations

import math
import os
import tempfile
import unittest
from argparse import Namespace
from types import SimpleNamespace

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics import air_combat_weapon_employment_process_probe as probe # noqa: E402


class _DummyHybridDistribution:
  def __init__(self) -> None:
    self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
    self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
    self.categorical_logits = [
      (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
    ]

  def _fire_event_logits(self):
    return th.tensor([[1.0, 3.0]], dtype=th.float32)


def _entity(entity_id: int) -> SimpleNamespace:
  return SimpleNamespace(entity_id=int(entity_id), world_index=0)


def _header(
  *,
  chain_id: int,
  event_id: int,
  parent_event_id: int,
  stage: str,
  status: str,
  reason: str,
  munition_id: int = 501,
  target_id: int = 200,
) -> SimpleNamespace:
  return SimpleNamespace(
    schema_version=1,
    chain_id=int(chain_id),
    event_id=int(event_id),
    parent_event_id=int(parent_event_id),
    stage=str(stage),
    status=str(status),
    reason=str(reason),
    source_time_s=4.25,
    source_frame=0,
    munition=_entity(munition_id),
    shooter=_entity(100),
    target=_entity(target_id),
    producer_node_id="test",
    fidelity_mode="runtime",
    evidence_level="observed_runtime",
    confidence=1.0,
  )


def _standard_nearest_event(reason: str = "fuze_no_detonation") -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=102,
      parent_event_id=301,
      stage="nearest_approach",
      status="observed",
      reason=reason,
    ),
    nearest_approach_time_s=4.25,
    miss_distance_m=12.5,
    local_forward_m=1.0,
    local_right_m=2.0,
    local_up_m=2.0,
    closure_mps=725.0,
    aspect_bucket="beam",
  )


def _standard_fuze_event(
  *,
  reason: str = "fuze_no_detonation",
  armed: bool = True,
  triggered: bool = False,
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=103,
      parent_event_id=102,
      stage="fuze_evaluation",
      status="evaluated",
      reason=reason,
    ),
    fuze_type="radar_proximity",
    armed=armed,
    triggered=triggered,
    failure_reason="" if triggered else reason,
    delay_s=0.0,
    reliability=0.0 if not triggered else 0.98,
    sample=0.42,
    trigger_radius_m=35.0,
    contact_surface_distance_m=0.0,
    contact_penetration_depth_m=0.0,
    contact_surface_tolerance_m=0.0,
    contact_inside_hitbox=False,
    direct_hitbox_intersection=False,
  )


def _standard_warhead_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=104,
      parent_event_id=101,
      stage="warhead_mechanism",
      status="applied",
      reason="generic_research_warhead_profile",
      target_id=200,
    ),
    mechanism_family="blast_fragmentation",
    warhead_mass_kg=12.0,
    lethal_radius_m=35.0,
    fragment_energy_j=540.0,
    fragment_density_per_m2=17.0,
    blast_overpressure_kpa=18.0,
    blast_impulse_kpa_ms=41.0,
    blast_scaled_distance_m_kg13=2.5,
    rod_cut_margin=0.0,
    penetration_margin=0.35,
    surface_incidence_cos=0.8,
  )


def _standard_spatial_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=105,
      parent_event_id=101,
      stage="spatial_coverage",
      status="projected",
      reason="generic_research_spatial_projection",
      target_id=200,
    ),
    projected_hitbox_count=4,
    sample_count=360,
    hit_estimate=1.8,
    hit_fraction=0.005,
    energy_scale=0.74,
    pattern_scale=1.1,
  )


def _standard_component_load_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=106,
      parent_event_id=101,
      stage="component_load",
      status="projected",
      reason="generic_research_component_load_projection",
      target_id=200,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    direct_hit=True,
    distance_m=0.7,
    effect_scale=0.83,
    fragment_energy_j=420.0,
    fragment_density_per_m2=13.0,
    blast_overpressure_kpa=14.0,
    blast_impulse_kpa_ms=32.0,
    blast_scaled_distance_m_kg13=2.7,
    rod_cut_margin=0.0,
    penetration_margin=0.25,
    surface_incidence_cos=0.9,
    load_source="direct_component_hit",
  )


def _standard_component_damage_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=107,
      parent_event_id=106,
      stage="component_damage",
      status="sampled",
      reason="generic_research_component_damage_candidate",
      target_id=200,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    component_redundancy_group_id="flight_control:right_aileron",
    integrity_before=1.0,
    integrity_after=0.68,
    failure_mode="cut",
    failure_severity=0.74,
    failure_probability=0.82,
    failure_sample=0.21,
  )


def _effect_component_damage_row(*, sample: float = 0.21) -> SimpleNamespace:
  return SimpleNamespace(
    component_name="right_aileron_actuator",
    component_system="flight_control",
    direct_hit=True,
    effect_scale=0.83,
    mechanism_fragment_energy_j=420.0,
    mechanism_fragment_areal_density_per_m2=13.0,
    mechanism_blast_overpressure_kpa=14.0,
    mechanism_blast_impulse_kpa_ms=32.0,
    mechanism_blast_scaled_distance_m_kg13=2.7,
    mechanism_rod_cut_margin=0.0,
    mechanism_penetration_margin=0.25,
    mechanism_surface_incidence_cos=0.9,
    component_integrity_before=1.0,
    component_integrity_after=0.68,
    component_failure_primary_mode="cut",
    component_failure_primary_mode_severity=0.74,
    component_failure_probability=0.82,
    component_failure_sample=sample,
  )


def _dummy_lethality_events() -> SimpleNamespace:
  effect = SimpleNamespace(
    event_id=101,
    munition=_entity(501),
    target=_entity(200),
    miss_distance_m=12.5,
    nearest_approach_time_s=4.25,
    detonation_local_forward_m=1.0,
    detonation_local_right_m=2.0,
    detonation_local_up_m=2.0,
    fuze_type="proximity",
    direct_hitbox_intersection=True,
    effect_family="blast_fragmentation",
    warhead_mass_kg=12.0,
    warhead_lethal_radius_m=35.0,
    mechanism_fragment_energy_j=540.0,
    mechanism_fragment_areal_density_per_m2=17.0,
    mechanism_blast_overpressure_kpa=18.0,
    mechanism_blast_impulse_kpa_ms=41.0,
    mechanism_blast_scaled_distance_m_kg13=2.5,
    mechanism_rod_cut_margin=0.0,
    mechanism_penetration_margin=0.35,
    mechanism_surface_incidence_cos=0.8,
    projected_hitbox_count=3,
    warhead_spatial_sample_count=240,
    warhead_spatial_hit_estimate=1.2,
    warhead_spatial_hit_fraction=0.005,
    warhead_spatial_energy_scale=0.7,
    warhead_spatial_pattern_scale=1.0,
    component_hit_count=2,
    component_mechanism_load_rows=[_effect_component_damage_row()],
    fuze_profile_synthetic=True,
    warhead_profile_synthetic=True,
    damage_scalar_synthetic=True,
    vulnerability_calibrated_evidence=False,
  )
  report = SimpleNamespace(
    report_id=201,
    target=_entity(200),
    source_event_id=101,
    system_health_delta=-0.35,
    mission_kill=True,
    mobility_kill=False,
    sensor_kill=True,
    destroyed=True,
    loss_state_to="lost",
  )
  trace = SimpleNamespace(
    chain_id=301,
    launch_event_id=301,
    effects_event_id=101,
    damage_report_id=201,
    munition=_entity(501),
  )
  return SimpleNamespace(
    effects_events=[effect],
    damage_reports=[report],
    diagnostics_traces=[trace],
    nearest_approach_events=[],
    fuze_evaluation_events=[],
    warhead_mechanism_events=[],
    spatial_coverage_events=[],
    component_load_events=[],
    component_damage_events=[],
  )


class DiagnosticsProcessProbeSummaryTests(unittest.TestCase):
  def test_episode_summary_reports_authorized_window_policy_diagnostics(self) -> None:
    def row(
      step: int,
      *,
      auth: int = 1,
      pending: int = 0,
      shot_budget: int = 1,
      fire_prob: float = 0.2,
      fire_logit: float = -1.0,
    ) -> dict:
      return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "can_fire": 1,
        "target_contact": 1,
        "target_active": 1,
        "missiles_remaining": 4,
        "missile_release": 0,
        "missile_release_delta": 0,
        "action_radar_on": 1,
        "action_master_arm_on": 1,
        "action_fire_weapon_on": 0,
        "action_radar_active": 1.0,
        "action_master_arm": 1.0,
        "action_fire_weapon": 0.0,
        "effective_action_fire_weapon": 0.0,
        "authorization_to_fire": auth,
        "shot_budget_remaining": shot_budget,
        "pending_assessment": pending,
        "c2_roe_hold_fire": 0,
        "c2_roe_hold_fire_obeyed": 0,
        "c2_roe_hold_fire_violation": 0,
        "c2_roe_unauthorized_release_count": 0,
        "c2_roe_authorized_release_count": 0,
        "c2_roe_valid_authorized_release_count": 0,
        "c2_roe_violation_release_count": 0,
        "c2_roe_pending_assessment_release_count": 0,
        "c2_roe_premature_second_shot": 0,
        "c2_roe_shot_budget_violation": 0,
        "c2_roe_authorized_salvo_release_count": 0,
        "c2_roe_authorized_reattack_release_count": 0,
        "policy_prob_tms_up": 0.4,
        "policy_logit_tms_up": -0.25,
        "policy_prob_fire_weapon": fire_prob,
        "policy_logit_fire_weapon": fire_logit,
        "effects_event_count": 0,
        "damage_report_count": 0,
      }

    summary = probe._summarize_episode(
      [
        row(0, auth=0),
        row(1, fire_prob=0.25, fire_logit=-0.8),
        row(2, fire_prob=0.55, fire_logit=0.2),
        row(3, pending=1, shot_budget=0, fire_prob=0.9, fire_logit=1.2),
      ]
    )

    self.assertEqual(summary["authorized_window_step_count"], 2)
    self.assertAlmostEqual(summary["policy_prob_fire_weapon_max"], 0.9, places=6)
    self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_mean"], 0.4, places=6)
    self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_max"], 0.55, places=6)
    self.assertAlmostEqual(summary["authorized_window_policy_logit_fire_weapon_max"], 0.2, places=6)

  def test_episode_summary_reports_a5_event_action_counts(self) -> None:
    def row(
      step: int,
      *,
      state: str = "Hold",
      mask: int = 0,
      requested: int = 0,
      accepted: int = 0,
      executed: int = 0,
      suppressed: int = 0,
      reason: str = "",
      event_prob: float = 0.0,
      event_mode: int = 0,
    ) -> dict:
      return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "can_fire": 1,
        "target_contact": 1,
        "target_active": 1,
        "missiles_remaining": 4 - executed,
        "missile_release": executed,
        "missile_release_delta": executed,
        "action_radar_on": 1,
        "action_master_arm_on": 1,
        "action_fire_weapon_on": requested,
        "action_radar_active": 1.0,
        "action_master_arm": 1.0,
        "action_fire_weapon": float(requested),
        "effective_action_fire_weapon": float(accepted),
        "authorization_to_fire": int(mask),
        "shot_budget_remaining": 1,
        "pending_assessment": int(state == "FiredAssess"),
        "engagement_state": state,
        "fire_mask": mask,
        "fire_once_requested": requested,
        "fire_once_accepted": accepted,
        "fire_once_rejected": int(requested and not accepted),
        "fire_once_rejected_reason": reason,
        "release_executed": executed,
        "post_launch_suppressed": suppressed,
        "policy_event_prob_fire_once": event_prob,
        "policy_event_logit_fire_once": event_prob,
        "policy_event_mode": event_mode,
        "policy_event_mask_fire_once": mask,
        "effects_event_count": 0,
        "damage_report_count": 0,
      }

    summary = probe._summarize_episode(
      [
        row(0),
        row(1, state="AuthorizedReady", mask=1, requested=1, accepted=1, executed=1, event_prob=0.8, event_mode=1),
        row(2, state="FiredAssess", requested=1, reason="pending_assessment", suppressed=1, event_prob=0.0),
        row(3, state="FiredAssess"),
      ]
    )

    self.assertEqual(summary["fire_mask_open_step_count"], 1)
    self.assertEqual(summary["fire_once_requested_count"], 2)
    self.assertEqual(summary["fire_once_accepted_count"], 1)
    self.assertEqual(summary["fire_once_rejected_count"], 1)
    self.assertEqual(summary["release_executed_count"], 1)
    self.assertEqual(summary["post_launch_suppressed_count"], 1)
    self.assertEqual(summary["fire_once_rejected_reason_counts"], {"pending_assessment": 1})
    self.assertEqual(summary["engagement_state_counts"], {"AuthorizedReady": 1, "FiredAssess": 2})
    self.assertEqual(summary["policy_event_mode_fire_once_count"], 1)
    self.assertEqual(summary["policy_event_mask_fire_once_open_count"], 1)

  def test_c2_roe_event_columns_split_authorized_salvo_and_budget_violation(self) -> None:
    state = {
      "contract_present": True,
      "roe_state": 2,
      "wcs_state": 2,
      "authorization_to_fire": True,
      "engage_order_state": 2,
      "shot_policy_state": 2,
      "shot_budget_remaining": 1,
      "pending_assessment": False,
    }

    columns = probe._c2_roe_event_columns(
      state,
      release_delta=2,
      fire_attempted=True,
      previous_release_count=0,
    )

    self.assertEqual(columns["c2_roe_release_bucket"], "authorized_salvo")
    self.assertEqual(columns["c2_roe_authorized_release_count"], 1)
    self.assertEqual(columns["c2_roe_authorized_salvo_release_count"], 1)
    self.assertEqual(columns["c2_roe_shot_budget_violation"], 1)
    self.assertEqual(columns["c2_roe_violation_release_count"], 1)

  def test_episode_summary_reports_c2_roe_release_discipline_buckets(self) -> None:
    def row(
      step: int,
      *,
      fire: int = 0,
      release_delta: int = 0,
      auth: int = 1,
      wcs: int = 2,
      pending: int = 0,
      authorized: int = 0,
      violation: int = 0,
      unauthorized: int = 0,
      pending_release: int = 0,
      salvo: int = 0,
      reattack: int = 0,
      hold_violation: int = 0,
    ) -> dict:
      return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 4),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 4 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "can_fire": 1,
        "target_contact": 1,
        "target_active": 1,
        "missiles_remaining": 4 - release_delta,
        "missile_release": int(release_delta > 0),
        "missile_release_delta": release_delta,
        "action_radar_on": 1,
        "action_master_arm_on": 1,
        "action_fire_weapon_on": fire,
        "action_radar_active": 1.0,
        "action_master_arm": 1.0,
        "action_fire_weapon": float(fire),
        "effective_action_fire_weapon": float(fire),
        "roe_state": 2,
        "wcs_state": wcs,
        "authorization_to_fire": auth,
        "pending_assessment": pending,
        "c2_roe_hold_fire": int(wcs == 1),
        "c2_roe_hold_fire_obeyed": 0,
        "c2_roe_hold_fire_violation": hold_violation,
        "c2_roe_unauthorized_release_count": unauthorized,
        "c2_roe_authorized_release_count": authorized,
        "c2_roe_valid_authorized_release_count": authorized,
        "c2_roe_violation_release_count": violation,
        "c2_roe_pending_assessment_release_count": pending_release,
        "c2_roe_premature_second_shot": 0,
        "c2_roe_shot_budget_violation": 0,
        "c2_roe_authorized_salvo_release_count": salvo,
        "c2_roe_authorized_reattack_release_count": reattack,
        "effects_event_count": 0,
        "damage_report_count": 0,
      }

    summary = probe._summarize_episode(
      [
        row(0, fire=0, auth=0, wcs=1),
        row(1, fire=1, release_delta=1, authorized=1, salvo=1),
        row(2, fire=0),
        row(3, fire=1, release_delta=1, auth=1, pending=1, violation=1, pending_release=1),
        row(4, fire=1, release_delta=1, auth=0, wcs=1, violation=1, unauthorized=1, hold_violation=1),
      ]
    )

    self.assertEqual(summary["authorized_release_count"], 1)
    self.assertEqual(summary["unauthorized_release_count"], 1)
    self.assertEqual(summary["violation_release_count"], 2)
    self.assertEqual(summary["pending_assessment_release_count"], 1)
    self.assertEqual(summary["authorized_salvo_release_count"], 1)
    self.assertEqual(summary["authorized_reattack_release_count"], 0)
    self.assertEqual(summary["fire_under_hold_count"], 1)
    self.assertEqual(summary["release_count_by_authorization_state"]["authorized"], 1)
    self.assertEqual(summary["release_count_by_authorization_state"]["unauthorized"], 1)
    self.assertEqual(summary["release_count_by_authorization_state"]["violation"], 2)
    self.assertEqual(summary["release_count_by_authorization_state"]["unknown"], 0)
    self.assertEqual(summary["roe_state_at_fire"], [2, 2])
    self.assertEqual(summary["authorization_to_fire_at_fire"], [1, 1])

  def test_legal_mask_fire_action_waits_for_open_mask_delay_and_one_shot(self) -> None:
    old_open = probe._legal_fire_mask_open
    try:
      probe._legal_fire_mask_open = lambda *args, **kwargs: True

      action, fired, age = probe._legal_mask_fire_action(
        env=object(),
        action_mode="air_combat_hybrid_v1",
        already_fired=False,
        legal_open_age_steps=30,
        fire_delay_steps=31,
      )

      self.assertFalse(fired)
      self.assertEqual(age, 31)
      self.assertEqual(float(action[9]), 0.0)

      action, fired, age = probe._legal_mask_fire_action(
        env=object(),
        action_mode="air_combat_hybrid_v1",
        already_fired=False,
        legal_open_age_steps=31,
        fire_delay_steps=31,
      )

      self.assertTrue(fired)
      self.assertEqual(age, 32)
      self.assertEqual(float(action[9]), 1.0)

      action, fired, age = probe._legal_mask_fire_action(
        env=object(),
        action_mode="air_combat_hybrid_v1",
        already_fired=True,
        legal_open_age_steps=32,
        fire_delay_steps=31,
      )

      self.assertFalse(fired)
      self.assertEqual(age, 33)
      self.assertEqual(float(action[9]), 0.0)
    finally:
      probe._legal_fire_mask_open = old_open

  def test_legal_mask_fire_action_resets_age_when_mask_closes(self) -> None:
    old_open = probe._legal_fire_mask_open
    try:
      probe._legal_fire_mask_open = lambda *args, **kwargs: False

      action, fired, age = probe._legal_mask_fire_action(
        env=object(),
        action_mode="air_combat_hybrid_v1",
        already_fired=False,
        legal_open_age_steps=12,
        fire_delay_steps=0,
      )

      self.assertFalse(fired)
      self.assertEqual(age, 0)
      self.assertEqual(float(action[9]), 0.0)
    finally:
      probe._legal_fire_mask_open = old_open


# A6/A7 event-value diagnostics share the same operator-facing process probe.
class _DummyA6HybridDistribution:
  def __init__(self) -> None:
    self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
    self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
    self.categorical_logits = [
      (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
    ]
    self._q_values = th.tensor([[1.5, -0.5]], dtype=th.float32)

  def _fire_event_logits(self):
    return th.tensor([[1.0, 3.0]], dtype=th.float32)

  def fire_event_logit_delta(self):
    return th.tensor([2.0], dtype=th.float32)

  def fire_event_probability(self):
    return th.sigmoid(self.fire_event_logit_delta())

  def fire_event_q_values(self):
    return self._q_values

  def fire_event_advantage(self):
    return self._q_values[:, 1] - self._q_values[:, 0]


class _DummyM3Policy:
  def obs_to_tensor(self, obs):
    return obs, False

  def get_distribution(self, _obs):
    return _DummyA6HybridDistribution()

  def get_m3_stopping(self, _obs, *, detach_latent: bool = False):
    logit = th.tensor([1.5], dtype=th.float32)
    return SimpleNamespace(
      stopping_logit=logit,
      hazard_logit=logit,
      hazard=th.sigmoid(logit),
    )


def _row(
  step: int,
  *,
  state: str = "Hold",
  mask: int = 0,
  event_delta: float = 0.0,
  event_prob: float = 0.0,
  event_mode: int = 0,
  event_advantage: float = 0.0,
  m3_stop_logit: float = 0.0,
  m3_stop_prob: float = 0.0,
  m3_boundary: int = 0,
  target_range_m: float | None = None,
  target_track_age_s: float = 1.0,
) -> dict:
  target_range = (12000.0 - step) if target_range_m is None else float(target_range_m)
  return {
    "episode": 0,
    "step": step,
    "reward": 0.0,
    "terminated": int(step == 3),
    "truncated": 0,
    "termination_reason": "combat_timeout" if step == 3 else "",
    "target_range_geom_m": target_range,
    "target_range_track_m": target_range,
    "target_track_age_s": target_track_age_s,
    "target_health": 100.0,
    "can_fire": 1,
    "target_contact": 1,
    "target_active": 1,
    "missiles_remaining": 4,
    "missile_release": 0,
    "missile_release_delta": 0,
    "action_radar_on": 1,
    "action_master_arm_on": 1,
    "action_fire_weapon_on": 0,
    "action_radar_active": 1.0,
    "action_master_arm": 1.0,
    "action_fire_weapon": 0.0,
    "effective_action_fire_weapon": 0.0,
    "authorization_to_fire": int(mask),
    "shot_budget_remaining": 1,
    "pending_assessment": 0,
    "engagement_state": state,
    "fire_mask": mask,
    "fire_once_requested": 0,
    "fire_once_accepted": 0,
    "fire_once_rejected": 0,
    "fire_once_rejected_reason": "",
    "release_executed": 0,
    "post_launch_suppressed": 0,
    "policy_event_logit_delta": event_delta,
    "policy_event_prob_fire_once_unmasked": event_prob,
    "policy_event_prob_fire_once": event_prob,
    "policy_event_logit_fire_once": event_delta,
    "policy_event_mode": event_mode,
    "policy_event_mask_fire_once": mask,
    "policy_event_q_hold": 0.0,
    "policy_event_q_fire_once": event_advantage,
    "policy_event_advantage": event_advantage,
    "policy_m3_stop_logit": m3_stop_logit,
    "policy_m3_stop_prob": m3_stop_prob,
    "policy_m3_boundary_cross": m3_boundary,
    "policy_m3_stopping_head_enabled": 1,
    "effects_event_count": 0,
    "damage_report_count": 0,
    "last_effect_miss_distance_m": math.nan,
    "last_effect_detonation_local_forward_m": math.nan,
    "last_effect_detonation_local_right_m": math.nan,
    "last_effect_detonation_local_up_m": math.nan,
    "last_effect_direct_hitbox_intersection": 0,
    "last_effect_projected_hitbox_count": 0,
    "last_effect_component_hit_count": 0,
    "last_effect_fuze_type": "",
    "last_damage_loss_state": "",
    "last_damage_system_health_delta": math.nan,
    "last_damage_mission_kill": 0,
    "last_damage_mobility_kill": 0,
    "last_damage_sensor_kill": 0,
    "last_damage_destroyed": 0,
  }


class A6EventValueProcessProbeTests(unittest.TestCase):
  def test_distribution_diagnostics_include_a6_unmasked_event_delta(self) -> None:
    diagnostics = probe._distribution_policy_diagnostics(_DummyA6HybridDistribution())

    self.assertAlmostEqual(diagnostics["policy_event_logit_delta"], 2.0, places=6)
    self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once_unmasked"], 0.8807970, places=6)
    self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once"], 0.8807970, places=6)
    self.assertEqual(int(diagnostics["policy_event_mode"]), 1)
    self.assertEqual(int(diagnostics["policy_event_mask_fire_once"]), 1)
    self.assertAlmostEqual(diagnostics["policy_event_q_hold"], 1.5, places=6)
    self.assertAlmostEqual(diagnostics["policy_event_q_fire_once"], -0.5, places=6)
    self.assertAlmostEqual(diagnostics["policy_event_advantage"], -2.0, places=6)

  def test_model_policy_diagnostics_include_m3_stopping_head_probe(self) -> None:
    diagnostics = probe._model_policy_diagnostics(
      SimpleNamespace(policy=_DummyM3Policy()),
      {"mission": th.zeros((1, 20), dtype=th.float32)},
    )

    self.assertAlmostEqual(diagnostics["policy_m3_stop_logit"], 1.5, places=6)
    self.assertAlmostEqual(
      diagnostics["policy_m3_stop_prob"],
      float(th.sigmoid(th.tensor(1.5)).item()),
      places=6,
    )
    self.assertEqual(int(diagnostics["policy_m3_boundary_cross"]), 1)
    self.assertEqual(int(diagnostics["policy_m3_stopping_head_enabled"]), 1)
    self.assertAlmostEqual(diagnostics["policy_event_logit_delta"], 2.0, places=6)

  def test_episode_summary_reports_a6_open_window_event_metrics(self) -> None:
    summary = probe._summarize_episode(
      [
        _row(0),
        _row(1, state="AuthorizedReady", mask=1, event_delta=1.0, event_prob=0.25),
        _row(2, state="AuthorizedReady", mask=1, event_delta=3.0, event_prob=0.75, event_mode=1),
        _row(3, state="FiredAssess", mask=0, event_delta=10.0, event_prob=0.99, event_mode=1),
      ]
    )

    self.assertEqual(summary["a6_open_window_step_count"], 2)
    self.assertAlmostEqual(summary["a6_event_logit_delta_mean_open"], 2.0, places=6)
    self.assertAlmostEqual(summary["a6_event_fire_prob_mean_open"], 0.5, places=6)
    self.assertAlmostEqual(summary["a6_event_fire_prob_max_open"], 0.75, places=6)
    self.assertEqual(summary["policy_event_mode_fire_once_count"], 2)

  def test_episode_summary_reports_a7_credit_signs_and_prewindow_cumulative_hazard(self) -> None:
    summary = probe._summarize_episode(
      [
        _row(0),
        _row(
          1,
          state="AuthorizedReady",
          mask=1,
          event_prob=0.1,
          event_advantage=-1.0,
          m3_stop_logit=-2.0,
          m3_stop_prob=0.1,
        ),
        _row(
          2,
          state="AuthorizedReady",
          mask=1,
          event_prob=0.2,
          event_advantage=-2.0,
          m3_stop_logit=-1.0,
          m3_stop_prob=0.2,
        ),
        _row(
          3,
          state="AuthorizedReady",
          mask=1,
          event_prob=0.6,
          event_advantage=1.0,
          m3_stop_logit=0.5,
          m3_stop_prob=0.6,
          m3_boundary=1,
        ),
        _row(
          4,
          state="AuthorizedReady",
          mask=1,
          event_prob=0.8,
          event_advantage=2.0,
          m3_stop_logit=1.0,
          m3_stop_prob=0.8,
          m3_boundary=1,
        ),
      ],
      launch_window_config={
        "min_range_m": 8000.0,
        "max_range_m": 30000.0,
        "max_track_age_s": 5.0,
        "min_window_age_steps": 3,
      },
    )

    self.assertEqual(summary["a7_prewindow_step_count"], 2)
    self.assertEqual(summary["a7_quality_window_step_count"], 2)
    self.assertAlmostEqual(summary["a7_prewindow_event_fire_prob_cum"], 0.28, places=6)
    self.assertAlmostEqual(summary["a7_prewindow_event_fire_prob_mean"], 0.15, places=6)
    self.assertAlmostEqual(summary["a7_quality_window_event_fire_prob_mean"], 0.7, places=6)
    self.assertAlmostEqual(summary["a7_prewindow_m3_stop_prob_cum"], 0.28, places=6)
    self.assertAlmostEqual(summary["a7_prewindow_m3_stop_prob_mean"], 0.15, places=6)
    self.assertAlmostEqual(summary["a7_quality_window_m3_stop_prob_mean"], 0.7, places=6)
    self.assertEqual(summary["a7_prewindow_m3_boundary_cross_count"], 0)
    self.assertEqual(summary["a7_quality_window_m3_boundary_cross_count"], 2)
    self.assertEqual(summary["a7_first_quality_window_m3_boundary_cross_step"], 3)
    self.assertEqual(summary["policy_m3_boundary_cross_count"], 2)
    self.assertEqual(summary["policy_m3_first_boundary_cross_step"], 3)
    self.assertAlmostEqual(summary["a7_event_credit_advantage_mean_prewindow"], -1.5, places=6)
    self.assertAlmostEqual(summary["a7_event_credit_advantage_negative_frac_prewindow"], 1.0, places=6)
    self.assertAlmostEqual(summary["a7_event_credit_advantage_mean_quality"], 1.5, places=6)
    self.assertAlmostEqual(summary["a7_event_credit_advantage_positive_frac_quality"], 1.0, places=6)




if __name__ == "__main__":
  unittest.main()