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


class DiagnosticsProcessProbeLethalityTests(unittest.TestCase):
  def test_distribution_policy_diagnostics_extract_hybrid_binary_probabilities(self) -> None:
    diagnostics = probe._distribution_policy_diagnostics(_DummyHybridDistribution())

    self.assertAlmostEqual(diagnostics["policy_logit_tms_up"], -1.0, places=6)
    self.assertAlmostEqual(diagnostics["policy_prob_tms_up"], 0.2689414, places=6)
    self.assertAlmostEqual(diagnostics["policy_logit_fire_weapon"], -0.5, places=6)
    self.assertAlmostEqual(diagnostics["policy_prob_fire_weapon"], 0.3775407, places=6)
    self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once"], 0.8807970, places=6)
    self.assertEqual(int(diagnostics["policy_event_mode"]), 1)
    self.assertEqual(int(diagnostics["policy_event_mask_fire_once"]), 1)
    self.assertEqual(int(diagnostics["policy_weapon_select_mode"]), 1)
    self.assertGreater(
      diagnostics["policy_weapon_select_station1_prob"],
      diagnostics["policy_weapon_select_station0_prob"],
    )

  def test_event_info_columns_copy_runtime_event_contract_fields(self) -> None:
    columns = probe._a5_event_info_columns(
      {
        "engagement_state": "FiredAssess",
        "fire_mask": 0,
        "event_action_mask": [1, 0],
        "fire_once_requested": True,
        "fire_once_accepted": False,
        "fire_once_rejected_reason": "pending_assessment",
        "release_executed": False,
        "post_launch_suppressed": True,
        "reattack_ready": False,
        "fire_mask_components": {
          "fire_mask_c2_authorized": 1,
          "fire_mask_not_pending_assessment": 0,
        },
      }
    )

    self.assertEqual(columns["engagement_state"], "FiredAssess")
    self.assertEqual(columns["fire_mask"], 0)
    self.assertEqual(columns["event_action_mask_json"], "[1,0]")
    self.assertEqual(columns["event_action_mask_hold"], 1)
    self.assertEqual(columns["event_action_mask_fire_once"], 0)
    self.assertEqual(columns["fire_once_requested"], 1)
    self.assertEqual(columns["fire_once_accepted"], 0)
    self.assertEqual(columns["fire_once_rejected"], 1)
    self.assertEqual(columns["fire_once_rejected_reason"], "pending_assessment")
    self.assertEqual(columns["post_launch_suppressed"], 1)
    self.assertEqual(
      columns["fire_mask_components_json"],
      '{"fire_mask_c2_authorized":1,"fire_mask_not_pending_assessment":0}',
    )
    self.assertEqual(columns["fire_mask_c2_authorized"], 1)
    self.assertEqual(columns["fire_mask_not_pending_assessment"], 0)

  def test_lethality_chain_rows_project_effect_and_damage_into_standard_stages(self) -> None:
    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=_dummy_lethality_events(),
    )

    self.assertEqual([row["stage"] for row in rows], list(probe.LETHALITY_CHAIN_STAGES))
    for row in rows:
      for field in probe.LETHALITY_CHAIN_ROW_FIELDS:
        self.assertIn(field, row)
      self.assertFalse(any(str(key).startswith("last_effect_") for key in row))
      self.assertFalse(any(str(key).startswith("last_damage_") for key in row))
      self.assertEqual(row["schema_version"], probe.LETHALITY_CHAIN_SCHEMA_VERSION)
      self.assertEqual(row["chain_id"], 301)
      self.assertEqual(row["munition_id"], 501)
      self.assertEqual(row["target_id"], 200)
      expected_status = "sampled" if row["stage"] == "component_damage" else "projected"
      self.assertEqual(row["status"], expected_status)

    nearest = next(row for row in rows if row["stage"] == "nearest_approach")
    self.assertAlmostEqual(nearest["miss_distance_m"], 12.5, places=6)
    self.assertAlmostEqual(nearest["local_forward_m"], 1.0, places=6)
    self.assertEqual(nearest["source_event_kind"], "EffectsEvent")
    self.assertEqual(nearest["source_event_id"], 101)

    fuze = next(row for row in rows if row["stage"] == "fuze")
    self.assertEqual(fuze["fuze_type"], "proximity")
    self.assertEqual(fuze["direct_hitbox_intersection"], 1)

    warhead = next(row for row in rows if row["stage"] == "warhead_mechanism")
    self.assertEqual(warhead["source_event_kind"], "EffectsEvent")
    self.assertEqual(warhead["mechanism_family"], "blast_fragmentation")
    self.assertAlmostEqual(warhead["fragment_energy_j"], 540.0, places=6)
    self.assertAlmostEqual(warhead["blast_overpressure_kpa"], 18.0, places=6)

    spatial = next(row for row in rows if row["stage"] == "spatial_coverage")
    self.assertEqual(spatial["source_event_kind"], "EffectsEvent")
    self.assertEqual(spatial["projected_hitbox_count"], 3)
    self.assertEqual(spatial["spatial_sample_count"], 240)

    component_damage = next(row for row in rows if row["stage"] == "component_damage")
    self.assertEqual(component_damage["source_event_kind"], "EffectsEvent")
    self.assertEqual(component_damage["reason"], "transitional_component_damage_projection")
    self.assertEqual(component_damage["component_hit_count"], 1)
    self.assertEqual(component_damage["component_name"], "right_aileron_actuator")
    self.assertEqual(component_damage["component_system"], "flight_control")
    self.assertEqual(component_damage["component_failure_mode"], "cut")
    self.assertAlmostEqual(component_damage["component_integrity_before"], 1.0, places=6)
    self.assertAlmostEqual(component_damage["component_integrity_after"], 0.68, places=6)
    self.assertAlmostEqual(component_damage["component_failure_probability"], 0.82, places=6)
    self.assertAlmostEqual(component_damage["component_failure_sample"], 0.21, places=6)

    platform = next(row for row in rows if row["stage"] == "platform_consequence")
    self.assertEqual(platform["parent_event_id"], 101)
    self.assertEqual(platform["damage_report_id"], 201)
    self.assertAlmostEqual(platform["system_health_delta"], -0.35, places=6)
    self.assertEqual(platform["mission_kill"], 1)
    self.assertEqual(platform["sensor_kill"], 1)

    lifecycle = next(row for row in rows if row["stage"] == "lifecycle")
    self.assertEqual(lifecycle["loss_state"], "lost")
    self.assertEqual(lifecycle["destroyed"], 1)

  def test_lethality_chain_rows_use_standard_geometry_and_fuze_events_without_effects(self) -> None:
    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=SimpleNamespace(
        nearest_approach_events=[_standard_nearest_event()],
        fuze_evaluation_events=[_standard_fuze_event()],
        effects_events=[],
        damage_reports=[],
        diagnostics_traces=[],
      ),
    )

    self.assertEqual([row["stage"] for row in rows], ["nearest_approach", "fuze"])
    for row in rows:
      for field in probe.LETHALITY_CHAIN_ROW_FIELDS:
        self.assertIn(field, row)
      self.assertFalse(any(str(key).startswith("last_effect_") for key in row))
      self.assertEqual(row["chain_id"], 301)
      self.assertEqual(row["munition_id"], 501)
      self.assertEqual(row["target_id"], 200)
      self.assertEqual(row["evidence_level"], "observed_runtime")

    nearest = rows[0]
    self.assertEqual(nearest["source_event_kind"], "NearestApproachEvent")
    self.assertEqual(nearest["source_event_id"], 102)
    self.assertEqual(nearest["status"], "observed")
    self.assertEqual(nearest["reason"], "fuze_no_detonation")
    self.assertAlmostEqual(nearest["miss_distance_m"], 12.5, places=6)
    self.assertAlmostEqual(nearest["closure_mps"], 725.0, places=6)
    self.assertEqual(nearest["aspect_bucket"], "beam")

    fuze = rows[1]
    self.assertEqual(fuze["source_event_kind"], "FuzeEvaluationEvent")
    self.assertEqual(fuze["source_event_id"], 103)
    self.assertEqual(fuze["parent_event_id"], 102)
    self.assertEqual(fuze["status"], "evaluated")
    self.assertEqual(fuze["reason"], "fuze_no_detonation")
    self.assertEqual(fuze["fuze_type"], "radar_proximity")
    self.assertEqual(fuze["fuze_armed"], 1)
    self.assertEqual(fuze["fuze_triggered"], 0)
    self.assertEqual(fuze["fuze_failure_reason"], "fuze_no_detonation")
    self.assertAlmostEqual(fuze["fuze_reliability"], 0.0, places=6)
    self.assertAlmostEqual(fuze["fuze_sample"], 0.42, places=6)
    self.assertAlmostEqual(fuze["fuze_trigger_radius_m"], 35.0, places=6)

    snapshot = probe._lethality_chain_snapshot_columns(rows)
    self.assertAlmostEqual(snapshot["lethality_chain_closure_mps"], 725.0, places=6)
    self.assertEqual(snapshot["lethality_chain_aspect_bucket"], "beam")
    self.assertEqual(snapshot["lethality_chain_fuze_armed"], 1)
    self.assertEqual(snapshot["lethality_chain_fuze_triggered"], 0)
    self.assertEqual(snapshot["lethality_chain_fuze_failure_reason"], "fuze_no_detonation")

  def test_standard_geometry_and_fuze_events_suppress_effects_fallback_rows(self) -> None:
    events = _dummy_lethality_events()
    events.nearest_approach_events = [_standard_nearest_event(reason="fuze_armed")]
    events.fuze_evaluation_events = [_standard_fuze_event(reason="fuze_armed", triggered=True)]

    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=events,
    )

    self.assertEqual([row["stage"] for row in rows], list(probe.LETHALITY_CHAIN_STAGES))
    nearest_rows = [row for row in rows if row["stage"] == "nearest_approach"]
    fuze_rows = [row for row in rows if row["stage"] == "fuze"]
    self.assertEqual(len(nearest_rows), 1)
    self.assertEqual(nearest_rows[0]["source_event_kind"], "NearestApproachEvent")
    self.assertEqual(nearest_rows[0]["reason"], "fuze_armed")
    self.assertEqual(len(fuze_rows), 1)
    self.assertEqual(fuze_rows[0]["source_event_kind"], "FuzeEvaluationEvent")
    self.assertEqual(fuze_rows[0]["fuze_triggered"], 1)
    self.assertEqual(fuze_rows[0]["fuze_failure_reason"], "")

  def test_standard_warhead_spatial_and_component_events_suppress_effects_fallback_rows(self) -> None:
    events = _dummy_lethality_events()
    events.warhead_mechanism_events = [_standard_warhead_event()]
    events.spatial_coverage_events = [_standard_spatial_event()]
    events.component_load_events = [_standard_component_load_event()]
    events.component_damage_events = [_standard_component_damage_event()]

    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=events,
    )

    warhead_rows = [row for row in rows if row["stage"] == "warhead_mechanism"]
    spatial_rows = [row for row in rows if row["stage"] == "spatial_coverage"]
    component_rows = [row for row in rows if row["stage"] == "component_load"]
    component_damage_rows = [row for row in rows if row["stage"] == "component_damage"]
    self.assertEqual(len(warhead_rows), 1)
    self.assertEqual(len(spatial_rows), 1)
    self.assertEqual(len(component_rows), 1)
    self.assertEqual(len(component_damage_rows), 1)
    self.assertEqual(warhead_rows[0]["source_event_kind"], "WarheadMechanismEvent")
    self.assertEqual(warhead_rows[0]["source_event_id"], 104)
    self.assertEqual(warhead_rows[0]["reason"], "generic_research_warhead_profile")
    self.assertEqual(warhead_rows[0]["mechanism_family"], "blast_fragmentation")
    self.assertAlmostEqual(warhead_rows[0]["fragment_density_per_m2"], 17.0, places=6)
    self.assertEqual(spatial_rows[0]["source_event_kind"], "SpatialCoverageEvent")
    self.assertEqual(spatial_rows[0]["projected_hitbox_count"], 4)
    self.assertEqual(spatial_rows[0]["spatial_sample_count"], 360)
    self.assertEqual(component_rows[0]["source_event_kind"], "ComponentLoadEvent")
    self.assertEqual(component_rows[0]["component_hit_count"], 1)
    self.assertEqual(component_rows[0]["component_name"], "right_aileron_actuator")
    self.assertEqual(component_rows[0]["component_system"], "flight_control")
    self.assertEqual(component_rows[0]["component_load_source"], "direct_component_hit")
    self.assertEqual(component_damage_rows[0]["source_event_kind"], "ComponentDamageEvent")
    self.assertEqual(component_damage_rows[0]["component_name"], "right_aileron_actuator")
    self.assertEqual(component_damage_rows[0]["component_failure_mode"], "cut")
    self.assertAlmostEqual(component_damage_rows[0]["component_integrity_after"], 0.68, places=6)
    snapshot = probe._lethality_chain_snapshot_columns(rows)
    self.assertEqual(snapshot["lethality_chain_component_damage_count"], 1)
    self.assertEqual(
      snapshot["lethality_chain_component_damage_name"],
      "right_aileron_actuator",
    )
    self.assertAlmostEqual(
      snapshot["lethality_chain_component_failure_probability"],
      0.82,
      places=6,
    )

  def test_standard_warhead_spatial_and_component_events_only_suppress_same_chain_effects(self) -> None:
    events = _dummy_lethality_events()
    events.warhead_mechanism_events = [_standard_warhead_event()]
    events.spatial_coverage_events = [_standard_spatial_event()]
    events.component_load_events = [_standard_component_load_event()]
    events.component_damage_events = [_standard_component_damage_event()]
    events.effects_events.append(
      SimpleNamespace(
        event_id=111,
        munition=_entity(501),
        target=_entity(200),
        miss_distance_m=18.0,
        nearest_approach_time_s=5.0,
        detonation_local_forward_m=3.0,
        detonation_local_right_m=4.0,
        detonation_local_up_m=5.0,
        fuze_type="proximity",
        direct_hitbox_intersection=False,
        effect_family="blast_fragmentation",
        warhead_mass_kg=10.0,
        warhead_lethal_radius_m=30.0,
        mechanism_fragment_energy_j=480.0,
        mechanism_fragment_areal_density_per_m2=11.0,
        mechanism_blast_overpressure_kpa=12.0,
        mechanism_blast_impulse_kpa_ms=25.0,
        mechanism_blast_scaled_distance_m_kg13=3.2,
        mechanism_rod_cut_margin=0.0,
        mechanism_penetration_margin=0.2,
        mechanism_surface_incidence_cos=0.6,
        projected_hitbox_count=2,
        warhead_spatial_sample_count=180,
        warhead_spatial_hit_estimate=0.8,
        warhead_spatial_hit_fraction=0.004,
        warhead_spatial_energy_scale=0.5,
        warhead_spatial_pattern_scale=0.9,
        component_hit_count=3,
        component_mechanism_load_rows=[_effect_component_damage_row()],
      )
    )
    events.diagnostics_traces.append(
      SimpleNamespace(
        chain_id=302,
        launch_event_id=302,
        effects_event_id=111,
        damage_report_id=0,
        munition=_entity(501),
      )
    )

    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=events,
    )

    standard_kind_by_stage = {
      "warhead_mechanism": "WarheadMechanismEvent",
      "spatial_coverage": "SpatialCoverageEvent",
      "component_load": "ComponentLoadEvent",
      "component_damage": "ComponentDamageEvent",
    }
    for stage in ("warhead_mechanism", "spatial_coverage", "component_load", "component_damage"):
      stage_rows = [row for row in rows if row["stage"] == stage]
      self.assertEqual(
        [(row["chain_id"], row["source_event_kind"]) for row in stage_rows],
        [(301, standard_kind_by_stage[stage]), (302, "EffectsEvent")],
      )
      self.assertFalse(
        any(
          row["chain_id"] == 301 and row["source_event_kind"] == "EffectsEvent"
          for row in stage_rows
        )
      )

    warhead_302 = next(
      row
      for row in rows
      if row["stage"] == "warhead_mechanism" and row["chain_id"] == 302
    )
    spatial_302 = next(
      row
      for row in rows
      if row["stage"] == "spatial_coverage" and row["chain_id"] == 302
    )
    component_302 = next(
      row
      for row in rows
      if row["stage"] == "component_load" and row["chain_id"] == 302
    )
    component_damage_302 = next(
      row
      for row in rows
      if row["stage"] == "component_damage" and row["chain_id"] == 302
    )
    self.assertEqual(warhead_302["source_event_kind"], "EffectsEvent")
    self.assertAlmostEqual(warhead_302["fragment_density_per_m2"], 11.0, places=6)
    self.assertEqual(spatial_302["source_event_kind"], "EffectsEvent")
    self.assertEqual(spatial_302["projected_hitbox_count"], 2)
    self.assertEqual(component_302["source_event_kind"], "EffectsEvent")
    self.assertEqual(component_302["component_hit_count"], 3)
    self.assertEqual(component_damage_302["source_event_kind"], "EffectsEvent")
    self.assertEqual(component_damage_302["component_hit_count"], 1)

  def test_untriggered_component_failure_sample_does_not_create_damage_stage(self) -> None:
    events = _dummy_lethality_events()
    events.effects_events[0].component_mechanism_load_rows = [
      _effect_component_damage_row(sample=0.99)
    ]

    rows = probe._lethality_chain_rows(
      episode=7,
      step=12,
      sim_time_s=4.5,
      engagement_events=events,
    )

    self.assertEqual(
      [row["stage"] for row in rows],
      [
        "nearest_approach",
        "fuze",
        "warhead_mechanism",
        "spatial_coverage",
        "component_load",
        "platform_consequence",
        "lifecycle",
      ],
    )
    self.assertNotIn("component_damage", {row["stage"] for row in rows})
    snapshot = probe._lethality_chain_snapshot_columns(rows)
    self.assertEqual(snapshot["lethality_chain_component_damage_count"], 0)
    self.assertTrue(math.isnan(snapshot["lethality_chain_component_failure_probability"]))



if __name__ == "__main__":
  unittest.main()