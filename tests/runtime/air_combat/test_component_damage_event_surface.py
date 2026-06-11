from __future__ import annotations

import math

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _drive_missile_with_truth_track,
  _make_warhead_profile,
  _make_baseline_kernel,
  _spawn_geometry_pair,
  _spawn_structured_f16_pair,
  ef_py,
)


ComponentKey = tuple[str, str, str]


def _component_key(row_or_event: object) -> ComponentKey:
  return (
    str(row_or_event.component_name),
    str(row_or_event.component_system),
    str(row_or_event.component_redundancy_group_id),
  )


def _positive(value: object) -> bool:
  number = float(value)
  return math.isfinite(number) and number > 0.0


def _valid_sample(value: object) -> bool:
  number = float(value)
  return math.isfinite(number) and 0.0 <= number <= 1.0


def _has_positive_load(row: object) -> bool:
  return any(
    _positive(value)
    for value in (
      row.effect_scale,
      row.mechanism_fragment_energy_j,
      row.mechanism_fragment_areal_density_per_m2,
      row.mechanism_penetration_margin,
      row.mechanism_blast_overpressure_kpa,
      row.mechanism_blast_impulse_kpa_ms,
      row.mechanism_rod_cut_margin,
    )
  )


def _is_component_damage_source_row(row: object) -> bool:
  return (
    bool(str(row.component_name))
    and bool(str(row.component_system))
    and _has_positive_load(row)
    and _positive(row.component_failure_probability)
    and _valid_sample(row.component_failure_sample)
    and float(row.component_failure_sample)
    <= _clamp_unit(row.component_failure_probability)
  )


def _clamp_unit(value: object) -> float:
  return min(max(float(value), 0.0), 1.0)


def _run_live_structured_air_detonation() -> tuple[object, int, int]:
  sim = _make_baseline_kernel()
  blue_id, red_id = _spawn_geometry_pair(
    sim,
    red_x=13000.0,
    red_y=9000.0,
    red_heading=270.0,
    red_vx=-260.0,
    red_vy=0.0,
  )
  missile_id = int(sim.fire_missile(blue_id, red_id))
  assert missile_id > 0

  result = _drive_missile_with_truth_track(
    sim,
    missile_id,
    red_id,
    max_steps=3600,
  )
  assert not bool(result["missile_active"])
  assert sim.is_unit_active(red_id)
  return sim.export_recent_engagement_events(), missile_id, red_id


def _run_profiled_sampled_component_failure() -> tuple[object, int]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile("continuous_rod", damage=180.0, radius=35.0)
  ok = sim.debug_apply_profiled_local_proximity_hit(
    attacker_id,
    target_id,
    -0.753,
    4.0,
    0.0,
    profile,
  )
  assert ok
  assert sim.is_unit_active(target_id)
  return sim.export_recent_engagement_events(), int(target_id)


def test_sampled_failure_exports_same_chain_component_damage_events() -> None:
  events, target_id = _run_profiled_sampled_component_failure()

  assert len(events.launch_events) == 0
  assert len(events.effects_events) == 1
  assert len(events.component_load_events) > 0
  assert hasattr(events, "component_damage_events")

  effects = events.effects_events[0]
  source_rows = [
    row
    for row in effects.component_mechanism_load_rows
    if _is_component_damage_source_row(row)
  ]
  component_loads = list(events.component_load_events)
  component_damage_events = list(events.component_damage_events)
  rows_by_component = {_component_key(row): row for row in source_rows}
  loads_by_component = {_component_key(load): load for load in component_loads}

  assert source_rows
  assert int(effects.component_failure_count) == len(source_rows)
  assert len(rows_by_component) == len(source_rows)
  assert len(component_damage_events) == len(source_rows)

  for damage_event in component_damage_events:
    key = _component_key(damage_event)
    assert key in rows_by_component
    assert key in loads_by_component
    row = rows_by_component[key]
    load = loads_by_component[key]

    assert str(damage_event.header.stage) == "component_damage"
    assert str(damage_event.header.status) == "sampled"
    assert str(damage_event.header.fidelity_mode) == "research_runtime"
    assert str(damage_event.header.evidence_level) == "engineering_assumption"
    assert str(damage_event.header.reason) == "generic_research_component_damage_candidate"
    assert int(damage_event.header.chain_id) == int(effects.event_id)
    assert int(damage_event.header.chain_id) == int(load.header.chain_id)
    assert int(damage_event.header.parent_event_id) == int(load.header.event_id)
    assert int(damage_event.header.munition.entity_id) == int(effects.munition.entity_id)
    assert int(damage_event.header.target.entity_id) == target_id

    assert str(damage_event.component_name) == str(row.component_name)
    assert str(damage_event.component_system) == str(row.component_system)
    assert str(damage_event.component_redundancy_group_id) == str(
      row.component_redundancy_group_id
    )
    assert str(damage_event.failure_mode) == str(row.component_failure_primary_mode)
    assert float(damage_event.failure_severity) == _clamp_unit(
      row.component_failure_primary_mode_severity
    )
    assert 0.0 < float(damage_event.failure_probability) <= 1.0
    assert float(damage_event.failure_probability) == _clamp_unit(
      row.component_failure_probability
    )
    assert 0.0 <= float(damage_event.failure_sample) <= 1.0
    assert float(damage_event.failure_sample) == float(row.component_failure_sample)
    assert 0.0 <= float(row.component_integrity_after) <= 1.0
    assert 0.0 <= float(row.component_integrity_before) <= 1.0
    assert float(row.component_integrity_before) > float(row.component_integrity_after)
    assert float(damage_event.integrity_before) == float(row.component_integrity_before)
    assert float(damage_event.integrity_after) == float(row.component_integrity_after)
    assert float(damage_event.integrity_before) > float(damage_event.integrity_after)
    assert 0.0 <= float(row.component_redundancy_group_availability_after) <= 1.0
    assert 0.0 <= float(row.component_redundancy_group_availability_before) <= 1.0

  assert list(events.platform_consequence_events) == []
  assert list(events.structural_breakup_events) == []
  assert list(events.lifecycle_transition_events) == []
  assert list(events.training_projection_events) == []


def test_no_detonation_exports_no_component_damage_events() -> None:
  sim = _make_baseline_kernel()
  sim.set_time_step(0.02)

  profile = ef_py.FuzeProfile()
  profile.type = "radar_proximity"
  profile.trigger_radius_m = 35.0
  profile.delay_s = 0.0
  profile.reliability = 0.0
  profile.synthetic = False
  profile.provenance = "test_component_damage_event_surface_no_detonation"

  tuning = sim.get_missile_tuning()
  tuning.fuze_profile = profile
  tuning.has_fuze_profile = True
  sim.set_missile_tuning(tuning)

  blue_id, red_id = _spawn_geometry_pair(
    sim,
    red_x=13000.0,
    red_y=9000.0,
    red_heading=270.0,
    red_vx=-260.0,
    red_vy=0.0,
  )
  missile_id = int(sim.fire_missile(blue_id, red_id))
  assert missile_id > 0

  result = _drive_missile_with_truth_track(
    sim,
    missile_id,
    red_id,
    max_steps=3600,
  )
  assert not bool(result["missile_active"])
  assert sim.is_unit_active(red_id)

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert str(events.effects_events[0].outcome_state) == "fuze_no_detonation"
  assert list(events.effects_events[0].component_mechanism_load_rows) == []
  assert list(events.component_load_events) == []
  assert list(events.component_damage_events) == []


def test_no_component_load_rows_export_no_component_damage_events() -> None:
  sim = ef_py.SimulationKernel()
  sim.reset(20260611)
  assert sim.load_database(_DB_PATH)

  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      100.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      1500.0,
      0.0,
      180.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
    )
  )

  assert sim.debug_apply_proximity_hit(attacker_id, target_id, 120.0, 80.0)
  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert list(events.effects_events[0].component_mechanism_load_rows) == []
  assert list(events.component_load_events) == []
  assert list(events.component_damage_events) == []


def test_component_damage_python_binding_exposes_event_fields() -> None:
  event = ef_py.ComponentDamageEvent()
  event.component_name = "right_aileron_actuator"
  event.component_system = "flight_control"
  event.component_redundancy_group_id = "flight_control:right_aileron"
  event.integrity_before = 1.0
  event.integrity_after = 1.0
  event.failure_mode = "jammed"
  event.failure_severity = 0.5
  event.failure_probability = 0.25
  event.failure_sample = 0.75

  row = ef_py.ComponentMechanismLoadRow()
  row.component_integrity_before = 1.0
  row.component_integrity_after = 0.72
  row.component_redundancy_group_availability_before = 1.0
  row.component_redundancy_group_availability_after = 0.86

  events = ef_py.RecentEngagementEvents()
  events.component_damage_events = [event]

  assert len(events.component_damage_events) == 1
  assert str(events.component_damage_events[0].component_name) == "right_aileron_actuator"
  assert str(events.component_damage_events[0].component_system) == "flight_control"
  assert str(events.component_damage_events[0].component_redundancy_group_id) == (
    "flight_control:right_aileron"
  )
  assert float(events.component_damage_events[0].integrity_before) == 1.0
  assert float(events.component_damage_events[0].integrity_after) == 1.0
  assert str(events.component_damage_events[0].failure_mode) == "jammed"
  assert float(events.component_damage_events[0].failure_severity) == 0.5
  assert float(events.component_damage_events[0].failure_probability) == 0.25
  assert float(events.component_damage_events[0].failure_sample) == 0.75
  assert float(row.component_integrity_before) == 1.0
  assert float(row.component_integrity_after) == 0.72
  assert float(row.component_redundancy_group_availability_before) == 1.0
  assert float(row.component_redundancy_group_availability_after) == 0.86
