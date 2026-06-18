from __future__ import annotations

import tempfile

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _copy_database_with_f16_vulnerability,
  _make_f16_component_redundancy_override,
  _make_warhead_profile,
  _profiled_local_hit_overlay_and_event_with_velocity,
  _profiled_local_hit_overlay_for_target,
  _spawn_structured_f16_pair,
  ef_py,
)


def _component_rows(event: object) -> list[object]:
  rows = list(event.component_mechanism_load_rows)
  assert rows
  return rows


def _row_for_component(event: object, component_name: str) -> object:
  matches = [
    row
    for row in _component_rows(event)
    if str(row.component_name) == component_name
  ]
  assert len(matches) == 1
  return matches[0]


def _assert_synthetic_probability(event: object) -> None:
  assert str(event.component_failure_probability_source) == "synthetic_sigmoid"
  assert not bool(event.component_failure_probability_calibrated)
  assert str(event.component_failure_probability_evidence_dataset_ref) == ""
  assert str(event.component_failure_probability_evidence_row_id) == ""
  assert not bool(event.vulnerability_pk_authority)
  assert not bool(event.vulnerability_deterministic_fuze_authority)
  for row in _component_rows(event):
    assert str(row.component_failure_probability_source) == "synthetic_sigmoid"
    assert not bool(row.component_failure_probability_authority)
    assert not bool(row.component_failure_probability_calibrated)
    assert str(row.component_failure_probability_evidence_row_id) == ""


def _seeded_profiled_local_event_with_velocity(
  seed: int,
  family: str,
  local: tuple[float, float, float],
  missile_velocity: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 35.0,
) -> object:
  sim = ef_py.SimulationKernel()
  sim.reset(seed)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
    float(missile_velocity[0]),
    float(missile_velocity[1]),
    float(missile_velocity[2]),
  )
  assert ok
  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  return events.effects_events[0]


def test_mlf5c_synthetic_sigmoid_is_uncalibrated_and_load_sensitive() -> None:
  _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (-0.8, 7.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=30.0,
    radius=35.0,
  )
  _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (-0.8, 7.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=180.0,
    radius=35.0,
  )

  _assert_synthetic_probability(low_event)
  _assert_synthetic_probability(high_event)
  assert str(high_event.vulnerability_calibration_status) == "unvalidated"
  assert float(high_event.component_primary_mechanism_rod_cut_margin) > float(
    low_event.component_primary_mechanism_rod_cut_margin
  )
  assert float(high_event.component_failure_probability) > float(
    low_event.component_failure_probability
  )


def test_mlf5c_synthetic_blast_near_miss_uses_plausible_component_scale() -> None:
  _overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "blast_fragmentation",
    (-0.753, 6.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=90.0,
    radius=35.0,
  )
  _overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "blast_fragmentation",
    (-0.753, 10.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=90.0,
    radius=35.0,
  )

  _assert_synthetic_probability(near_event)
  _assert_synthetic_probability(far_event)
  assert str(near_event.component_primary_name) == "right_aileron_actuator"
  assert float(near_event.component_primary_mechanism_blast_overpressure_kpa) > 100.0
  assert float(near_event.component_primary_mechanism_fragment_areal_density_per_m2) > 2.0
  assert float(near_event.component_failure_probability) > 0.10
  assert float(far_event.component_failure_probability) < float(
    near_event.component_failure_probability
  )
  assert float(far_event.component_failure_probability) < 0.03
  assert int(near_event.component_failure_count) == 0
  assert not bool(near_event.vulnerability_pk_authority)
  assert not bool(near_event.vulnerability_deterministic_fuze_authority)


def test_mlf5c_synthetic_rod_near_miss_uses_cut_exposure_scale() -> None:
  _overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (-0.8, 6.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=90.0,
    radius=35.0,
  )
  _overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (-0.8, 12.0, 0.0),
    (900.0, -250.0, 0.0),
    damage=90.0,
    radius=35.0,
  )

  _assert_synthetic_probability(near_event)
  _assert_synthetic_probability(far_event)
  assert str(near_event.component_primary_name) == "right_aileron_actuator"
  assert float(near_event.component_primary_mechanism_rod_cut_margin) > 1.0
  assert float(near_event.component_failure_probability) > 0.05
  assert float(far_event.component_failure_probability) < float(
    near_event.component_failure_probability
  )
  assert float(far_event.component_failure_probability) < 0.03
  assert not bool(near_event.vulnerability_pk_authority)
  assert not bool(near_event.vulnerability_deterministic_fuze_authority)


def test_mlf5c_debug_component_failure_sampling_varies_with_reset_seed() -> None:
  samples = []
  triggered = 0
  for offset in range(96):
    event = _seeded_profiled_local_event_with_velocity(
      2026061100 + offset,
      "continuous_rod",
      (-0.8, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _assert_synthetic_probability(event)
    samples.append(float(event.component_failure_sample))
    if int(event.component_failure_count) > 0:
      triggered += 1

  assert len({round(sample, 6) for sample in samples}) > 24
  assert 0 < triggered < len(samples)


def test_mlf5c_ideal_near_miss_samples_component_failure_at_expected_scale() -> None:
  triggered = 0
  total = 128
  for offset in range(total):
    event = _seeded_profiled_local_event_with_velocity(
      2026061200 + offset,
      "continuous_rod",
      (-0.8, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _assert_synthetic_probability(event)
    if int(event.component_failure_count) > 0:
      triggered += 1

  actual_rate = triggered / total
  assert 0.08 <= actual_rate <= 0.25


def test_mlf5c_expanded_aspect_distance_surface_preserves_gradients() -> None:
  def probability(
    family: str,
    local: tuple[float, float, float],
    velocity: tuple[float, float, float],
  ) -> float:
    _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
      family,
      local,
      velocity,
      damage=90.0,
      radius=35.0,
    )
    return float(event.component_failure_probability)

  blast_right_near = probability(
    "blast_fragmentation", (-0.753, 6.0, 0.0), (900.0, -250.0, 0.0)
  )
  blast_right_mid = probability(
    "blast_fragmentation", (-0.753, 8.0, 0.0), (900.0, -250.0, 0.0)
  )
  blast_right_edge = probability(
    "blast_fragmentation", (-0.753, 10.0, 0.0), (900.0, -250.0, 0.0)
  )
  blast_right_outside = probability(
    "blast_fragmentation", (-0.753, 22.0, 0.0), (900.0, -250.0, 0.0)
  )
  blast_left_near = probability(
    "blast_fragmentation", (0.753, -6.0, 0.0), (900.0, 250.0, 0.0)
  )
  blast_top_near = probability(
    "blast_fragmentation", (-0.8, 0.0, 2.0), (900.0, 0.0, -250.0)
  )
  blast_top_far = probability(
    "blast_fragmentation", (-0.8, 0.0, 10.0), (900.0, 0.0, -250.0)
  )

  assert blast_right_near > 0.10
  assert blast_right_near > blast_right_mid > blast_right_edge > blast_right_outside
  assert blast_left_near > blast_right_near
  assert blast_left_near < blast_top_near
  assert blast_top_near > 0.55
  assert blast_top_far < 0.02

  rod_right_near = probability(
    "continuous_rod", (-0.8, 6.0, 0.0), (900.0, -250.0, 0.0)
  )
  rod_right_mid = probability(
    "continuous_rod", (-0.8, 8.0, 0.0), (900.0, -250.0, 0.0)
  )
  rod_right_edge = probability(
    "continuous_rod", (-0.8, 12.0, 0.0), (900.0, -250.0, 0.0)
  )
  rod_right_outside = probability(
    "continuous_rod", (-0.8, 16.0, 0.0), (900.0, -250.0, 0.0)
  )
  rod_nose_axial = probability(
    "continuous_rod", (11.5, 0.0, 0.0), (-250.0, 900.0, 0.0)
  )
  rod_tail_axial = probability(
    "continuous_rod", (-8.0, 0.0, 0.0), (250.0, 900.0, 0.0)
  )
  rod_top_near = probability(
    "continuous_rod", (-0.8, 0.0, 6.0), (900.0, 0.0, -250.0)
  )
  rod_top_outside = probability(
    "continuous_rod", (-0.8, 0.0, 12.0), (900.0, 0.0, -250.0)
  )

  assert rod_right_near > 0.05
  assert rod_right_near > rod_right_mid > rod_right_edge > rod_right_outside
  assert rod_nose_axial < 0.005
  assert rod_tail_axial < rod_right_mid
  assert rod_top_near > 0.20
  assert rod_top_outside == 0.0


def test_mlf5c_direct_hit_load_floor_prevents_blast_tail_valley() -> None:
  _overlay, direct_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "blast_fragmentation",
    (-6.0, 0.0, 0.0),
    (250.0, 900.0, 0.0),
    damage=90.0,
    radius=35.0,
  )
  _overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "blast_fragmentation",
    (-8.0, 0.0, 0.0),
    (250.0, 900.0, 0.0),
    damage=90.0,
    radius=35.0,
  )

  _assert_synthetic_probability(direct_event)
  _assert_synthetic_probability(near_event)
  assert bool(direct_event.direct_hitbox_intersection)
  assert not bool(near_event.direct_hitbox_intersection)
  assert str(direct_event.component_primary_name) == "engine_core"
  assert float(direct_event.component_primary_mechanism_blast_overpressure_kpa) > 500.0
  assert float(direct_event.component_failure_probability) >= 0.55
  assert float(direct_event.component_failure_probability) > float(
    near_event.component_failure_probability
  )


def test_mlf5c_continuous_rod_nose_direct_hit_is_not_axial_grazing() -> None:
  _overlay, grazing_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (11.5, 0.0, 0.0),
    (-250.0, 900.0, 0.0),
    damage=90.0,
    radius=35.0,
  )
  _overlay, direct_event = _profiled_local_hit_overlay_and_event_with_velocity(
    "continuous_rod",
    (6.0, 0.0, 0.0),
    (-250.0, 900.0, 0.0),
    damage=90.0,
    radius=35.0,
  )

  _assert_synthetic_probability(grazing_event)
  _assert_synthetic_probability(direct_event)
  assert not bool(grazing_event.direct_hitbox_intersection)
  assert bool(direct_event.direct_hitbox_intersection)
  assert float(grazing_event.component_failure_probability) < 0.005
  assert float(direct_event.component_failure_probability) > 0.90
  assert float(direct_event.component_primary_mechanism_rod_cut_margin) > 1.0


def test_mlf5c_synthetic_probability_responds_to_redundancy_and_pre_damage() -> None:
  single_name = "F-16C_MLF5C_SingleCriticalActuator"
  redundant_name = "F-16C_MLF5C_RedundantActuator"
  overrides = [
    _make_f16_component_redundancy_override(
      single_name,
      redundancy_group=0.0,
      critical=True,
    ),
    _make_f16_component_redundancy_override(
      redundant_name,
      redundancy_group=2.0,
      critical=False,
    ),
  ]

  _overlay, _damage_state, single_event = _profiled_local_hit_overlay_for_target(
    single_name,
    "continuous_rod",
    (-0.8, 6.0, 0.0),
    damage=140.0,
    radius=35.0,
    overrides=overrides,
  )
  _overlay, _damage_state, redundant_event = _profiled_local_hit_overlay_for_target(
    redundant_name,
    "continuous_rod",
    (-0.8, 6.0, 0.0),
    damage=140.0,
    radius=35.0,
    overrides=overrides,
  )

  _assert_synthetic_probability(single_event)
  _assert_synthetic_probability(redundant_event)
  assert bool(single_event.component_primary_critical)
  assert not bool(redundant_event.component_primary_critical)
  assert float(single_event.component_primary_redundancy_group) == 0.0
  assert float(redundant_event.component_primary_redundancy_group) == 2.0
  assert float(single_event.component_redundancy_group_availability) < float(
    redundant_event.component_redundancy_group_availability
  )

  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile("continuous_rod", damage=90.0, radius=35.0)
  for _ in range(2):
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.8,
      6.0,
      0.0,
      profile,
      900.0,
      -250.0,
      0.0,
    )
    assert ok
  events = sim.export_recent_engagement_events()
  first_event = events.effects_events[-2]
  second_event = events.effects_events[-1]

  _assert_synthetic_probability(first_event)
  _assert_synthetic_probability(second_event)
  assert float(second_event.component_primary_integrity) < float(
    first_event.component_primary_integrity
  )
  assert float(second_event.component_redundancy_group_availability) < float(
    first_event.component_redundancy_group_availability
  )


def test_mlf5c_authorized_component_specific_rows_override_generic_baseline() -> None:
  with tempfile.TemporaryDirectory(prefix="cmo_mlf5c_component_specific_") as tmpdir:
    db_dir = _copy_database_with_f16_vulnerability(
      tmpdir,
      {
        "synthetic": False,
        "calibrated": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "evidence_dataset_ref": "mlf5c_component_specific_fixture",
        "calibration_status": "calibrated",
        "provenance": "MLF-5C unit fixture; component probability only",
      },
      descriptor={
        "dataset_id": "mlf5c_component_specific_fixture",
        "target_type": "F-16C_Block50",
        "weapon_family": "continuous_rod",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss",
        "source_kind": "external_calibration_dataset",
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": "MLF-5C unit fixture descriptor",
        "rows": [
          {
            "component_failure_probability": 0.21,
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
          },
          {
            "row_id": "right-aileron-actuator-specific",
            "source_ref": "fixture://mlf5c/right-aileron",
            "provenance": "MLF-5C component-specific row fixture",
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "component_name": "right_aileron_actuator",
            "component_system": "flight_control",
            "component_redundancy_group_id": "lateral_flight_control_actuators",
            "component_failure_probability": 0.73,
          },
        ],
      },
    )

    _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      (-0.8, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )

  assert bool(event.vulnerability_calibrated_evidence)
  assert bool(event.vulnerability_evidence_dataset_valid)
  assert not bool(event.vulnerability_pk_authority)
  assert not bool(event.vulnerability_deterministic_fuze_authority)
  assert str(event.component_primary_name) == "right_aileron_actuator"
  assert float(event.component_failure_probability) == 0.73
  assert str(event.component_failure_probability_source) == "vulnerability_evidence_row"
  assert bool(event.component_failure_probability_calibrated)
  assert str(event.component_failure_probability_evidence_dataset_ref) == (
    "mlf5c_component_specific_fixture"
  )
  assert str(event.component_failure_probability_evidence_row_id) == (
    "right-aileron-actuator-specific"
  )
  assert str(event.component_failure_probability_evidence_source_ref) == (
    "fixture://mlf5c/right-aileron"
  )

  row = _row_for_component(event, "right_aileron_actuator")
  assert float(row.component_failure_probability) == 0.73
  assert bool(row.component_failure_probability_authority)
  assert bool(row.component_failure_probability_component_specific)
  assert str(row.component_failure_probability_evidence_component_name) == (
    "right_aileron_actuator"
  )
  assert str(row.component_failure_probability_evidence_component_system) == (
    "flight_control"
  )
  assert str(row.component_failure_probability_evidence_component_redundancy_group_id) == (
    "lateral_flight_control_actuators"
  )


def test_mlf5c_probability_rows_fail_closed_without_authority_or_matching_load_gate() -> None:
  with tempfile.TemporaryDirectory(prefix="cmo_mlf5c_authority_denied_") as tmpdir:
    db_dir = _copy_database_with_f16_vulnerability(
      tmpdir,
      {
        "synthetic": False,
        "calibrated": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "evidence_dataset_ref": "mlf5c_authority_denied_fixture",
        "calibration_status": "calibrated",
        "provenance": "MLF-5C authority denied fixture",
      },
      descriptor={
        "dataset_id": "mlf5c_authority_denied_fixture",
        "target_type": "F-16C_Block50",
        "weapon_family": "continuous_rod",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss",
        "source_kind": "external_calibration_dataset",
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": False,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": "MLF-5C descriptor with component probability authority denied",
        "rows": [
          {
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "component_failure_probability": 0.37,
          }
        ],
      },
    )
    _overlay, denied_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      (-0.8, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )

  _assert_synthetic_probability(denied_event)
  assert float(denied_event.component_failure_probability) != 0.37

  with tempfile.TemporaryDirectory(prefix="cmo_mlf5c_rod_gate_") as tmpdir:
    db_dir = _copy_database_with_f16_vulnerability(
      tmpdir,
      {
        "synthetic": False,
        "calibrated": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "evidence_dataset_ref": "mlf5c_rod_gate_fixture",
        "calibration_status": "calibrated",
        "provenance": "MLF-5C rod load gate fixture",
      },
      descriptor={
        "dataset_id": "mlf5c_rod_gate_fixture",
        "target_type": "F-16C_Block50",
        "weapon_family": "continuous_rod",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss",
        "source_kind": "external_calibration_dataset",
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": "MLF-5C descriptor proving rod-load gates only",
        "rows": [
          {
            "row_id": "unreachable-high-rod-margin",
            "source_ref": "fixture://mlf5c/unreachable-high-rod",
            "provenance": "MLF-5C unreachable rod gate fixture",
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "min_rod_cut_margin": 9.0,
            "component_failure_probability": 0.97,
          },
          {
            "row_id": "reachable-fallback-rod-margin",
            "source_ref": "fixture://mlf5c/reachable-rod",
            "provenance": "MLF-5C reachable rod gate fixture",
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "component_failure_probability": 0.33,
          },
        ],
      },
    )
    _overlay, gated_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      (-0.8, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )

  assert float(gated_event.component_primary_mechanism_rod_cut_margin) < 9.0
  assert float(gated_event.component_failure_probability) == 0.33
  assert str(gated_event.component_failure_probability_source) == "vulnerability_evidence_row"
  assert str(gated_event.component_failure_probability_evidence_row_id) == (
    "reachable-fallback-rod-margin"
  )


def test_mlf5c_mechanism_load_buckets_can_select_fragment_density_and_surface_incidence() -> None:
  with tempfile.TemporaryDirectory(prefix="cmo_mlf5c_fragment_gate_") as tmpdir:
    db_dir = _copy_database_with_f16_vulnerability(
      tmpdir,
      {
        "synthetic": False,
        "calibrated": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "evidence_dataset_ref": "mlf5c_fragment_density_fixture",
        "calibration_status": "calibrated",
        "provenance": "MLF-5C fragment-density gate fixture",
      },
      descriptor={
        "dataset_id": "mlf5c_fragment_density_fixture",
        "target_type": "F-16C_Block50",
        "weapon_family": "blast_fragmentation",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss",
        "source_kind": "external_calibration_dataset",
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": "MLF-5C descriptor proving fragment-density gates",
        "rows": [
          {
            "row_id": "component-high-fragment-density",
            "source_ref": "fixture://mlf5c/fragment-density-high",
            "provenance": "MLF-5C high fragment-density row fixture",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "min_fragment_areal_density_per_m2": 2.0,
            "component_failure_probability": 0.62,
          },
          {
            "row_id": "component-low-fragment-density",
            "source_ref": "fixture://mlf5c/fragment-density-low",
            "provenance": "MLF-5C low fragment-density row fixture",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "max_fragment_areal_density_per_m2": 2.0,
            "component_failure_probability": 0.18,
          },
        ],
      },
    )
    _overlay, close_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      (-0.753, 6.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )
    _overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      (-0.753, 10.0, 0.0),
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )

  assert float(close_event.mechanism_fragment_areal_density_per_m2) > 2.0
  assert float(far_event.mechanism_fragment_areal_density_per_m2) < 2.0
  assert float(close_event.component_failure_probability) == 0.62
  assert float(far_event.component_failure_probability) == 0.18
  assert str(close_event.component_failure_probability_evidence_row_id) == (
    "component-high-fragment-density"
  )
  assert str(far_event.component_failure_probability_evidence_row_id) == (
    "component-low-fragment-density"
  )

  with tempfile.TemporaryDirectory(prefix="cmo_mlf5c_surface_gate_") as tmpdir:
    db_dir = _copy_database_with_f16_vulnerability(
      tmpdir,
      {
        "synthetic": False,
        "calibrated": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "evidence_dataset_ref": "mlf5c_surface_incidence_fixture",
        "calibration_status": "calibrated",
        "provenance": "MLF-5C surface-incidence gate fixture",
      },
      descriptor={
        "dataset_id": "mlf5c_surface_incidence_fixture",
        "target_type": "F-16C_Block50",
        "weapon_family": "continuous_rod",
        "aspect_bucket": "beam",
        "closure_bucket": "high",
        "miss_distance_bucket": "near_miss",
        "source_kind": "external_calibration_dataset",
        "calibration_status": "calibrated",
        "effect_scale_authority": False,
        "component_failure_probability_authority": True,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "provenance": "MLF-5C descriptor proving surface-incidence gates",
        "rows": [
          {
            "row_id": "component-normal-surface-incidence",
            "source_ref": "fixture://mlf5c/surface-normal",
            "provenance": "MLF-5C normal-incidence row fixture",
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "component_name": "right_aileron_actuator",
            "component_system": "flight_control",
            "component_redundancy_group_id": "lateral_flight_control_actuators",
            "min_surface_incidence_cos": 0.5,
            "component_failure_probability": 0.61,
          },
          {
            "row_id": "component-oblique-surface-incidence",
            "source_ref": "fixture://mlf5c/surface-oblique",
            "provenance": "MLF-5C oblique-incidence row fixture",
            "weapon_family": "continuous_rod",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss",
            "max_surface_incidence_cos": 0.5,
            "component_failure_probability": 0.19,
          },
        ],
      },
    )
    _overlay, normal_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      (-0.8, 5.2, 0.0),
      (900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )
    _overlay, oblique_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      (-1.6, 5.2, 0.0),
      (900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
      database_path=db_dir,
    )

  normal_row = _row_for_component(normal_event, "right_aileron_actuator")
  oblique_row = _row_for_component(oblique_event, "right_aileron_actuator")
  assert float(normal_row.mechanism_surface_incidence_cos) > 0.5
  assert float(oblique_row.mechanism_surface_incidence_cos) < 0.5
  assert float(normal_event.component_failure_probability) == 0.61
  assert float(oblique_event.component_failure_probability) == 0.19
  assert str(normal_event.component_failure_probability_evidence_row_id) == (
    "component-normal-surface-incidence"
  )
  assert str(oblique_event.component_failure_probability_evidence_row_id) == (
    "component-oblique-surface-incidence"
  )
