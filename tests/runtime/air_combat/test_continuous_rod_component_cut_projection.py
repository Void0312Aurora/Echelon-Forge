from __future__ import annotations

from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _spawn_structured_f16_pair,
  ef_py,
)


@dataclass(frozen=True)
class _ComponentCutCase:
  events: object
  effects: object
  component_loads: list[object]
  source_rows: list[object]


def _warhead_profile(family: str) -> object:
  profile = ef_py.WarheadProfile()
  profile.family = family
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "test_continuous_rod_component_cut_projection"
  return profile


def _run_component_cut_case(
  family: str,
  local: tuple[float, float, float],
  velocity: tuple[float, float, float] = (900.0, -250.0, 0.0),
) -> _ComponentCutCase:
  sim = ef_py.SimulationKernel()
  sim.reset(20260611)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _warhead_profile(family),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  assert ok

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  effects = events.effects_events[0]
  component_loads = list(events.component_load_events)
  source_rows = [
    row
    for row in effects.component_mechanism_load_rows
    if str(row.component_name) or str(row.component_system)
  ]
  assert len(component_loads) == len(source_rows)

  return _ComponentCutCase(
    events=events,
    effects=effects,
    component_loads=component_loads,
    source_rows=source_rows,
  )


def _assert_no_downstream_failure_or_consequence_events(case: _ComponentCutCase) -> None:
  assert list(case.events.component_damage_events) == []
  assert list(case.events.structural_breakup_events) == []
  assert list(case.events.lifecycle_transition_events) == []
  assert list(case.events.training_projection_events) == []


def _assert_component_load_rows_match_events(case: _ComponentCutCase) -> None:
  effects = case.effects
  assert case.component_loads
  assert case.source_rows

  for row, load in zip(case.source_rows, case.component_loads):
    assert str(load.header.stage) == "component_load"
    assert str(load.header.status) == "projected"
    assert str(load.header.evidence_level) == "engineering_assumption"
    assert int(load.header.parent_event_id) == int(effects.event_id)
    assert int(load.header.chain_id) == int(effects.event_id)
    assert str(load.component_name) == str(row.component_name)
    assert str(load.component_system) == str(row.component_system)
    assert str(load.component_redundancy_group_id) == str(
      row.component_redundancy_group_id
    )
    assert bool(load.direct_hit) is bool(row.direct_hit)
    assert float(load.distance_m) == float(row.distance_m)
    assert float(load.effect_scale) == float(row.effect_scale)
    assert float(load.rod_cut_margin) == float(row.mechanism_rod_cut_margin)
    assert str(load.load_source) == (
      "direct_component_hit"
      if bool(row.direct_hit)
      else "spatial_component_projection"
    )
    assert not hasattr(load, "failure_probability")
    assert not hasattr(load, "integrity_after")


def _primary_source_row(case: _ComponentCutCase) -> object:
  for row in case.source_rows:
    if (
      str(row.component_name) == str(case.effects.component_primary_name)
      and str(row.component_system) == str(case.effects.component_primary_system)
    ):
      return row
  raise AssertionError("primary component row not found")


def test_spatial_component_rows_expose_continuous_rod_cut_facts() -> None:
  case = _run_component_cut_case("continuous_rod", (-0.753, 7.1, 0.0))

  assert str(case.effects.effect_family) == "continuous_rod"
  assert {str(row.component_name) for row in case.source_rows} == {
    "right_aileron_actuator",
    "right_wing_fuel_cell",
  }
  assert all(not bool(row.direct_hit) for row in case.source_rows)
  assert all(str(load.load_source) == "spatial_component_projection" for load in case.component_loads)
  assert all(float(row.mechanism_rod_cut_margin) > 0.0 for row in case.source_rows)
  assert all(float(load.rod_cut_margin) > 0.0 for load in case.component_loads)

  _assert_component_load_rows_match_events(case)
  _assert_no_downstream_failure_or_consequence_events(case)

  primary_row = _primary_source_row(case)
  assert str(case.effects.component_primary_name) == "right_aileron_actuator"
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == float(
    primary_row.mechanism_rod_cut_margin
  )


def test_direct_component_hit_uses_direct_load_source() -> None:
  case = _run_component_cut_case("continuous_rod", (-0.8, 4.1, 0.0))

  assert str(case.effects.effect_family) == "continuous_rod"
  assert [str(row.component_name) for row in case.source_rows] == [
    "right_aileron_actuator"
  ]
  assert [str(load.load_source) for load in case.component_loads] == [
    "direct_component_hit"
  ]
  assert all(bool(row.direct_hit) for row in case.source_rows)
  assert all(bool(load.direct_hit) for load in case.component_loads)
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) > 0.0
  assert float(case.component_loads[0].rod_cut_margin) == float(
    case.effects.component_primary_mechanism_rod_cut_margin
  )

  _assert_component_load_rows_match_events(case)
  _assert_no_downstream_failure_or_consequence_events(case)


def test_local_side_changes_emphasized_component_rows() -> None:
  right = _run_component_cut_case("continuous_rod", (-0.753, 7.1, 0.0))
  left = _run_component_cut_case("continuous_rod", (-0.753, -7.1, 0.0))

  assert str(right.effects.component_primary_name) == "right_aileron_actuator"
  assert str(left.effects.component_primary_name) == "left_aileron_actuator"
  assert {str(row.component_name) for row in right.source_rows} == {
    "right_aileron_actuator",
    "right_wing_fuel_cell",
  }
  assert {str(row.component_name) for row in left.source_rows} == {
    "left_aileron_actuator",
    "left_wing_fuel_cell",
  }
  assert all(str(load.load_source) == "spatial_component_projection" for load in right.component_loads)
  assert all(str(load.load_source) == "spatial_component_projection" for load in left.component_loads)
  assert any(float(load.rod_cut_margin) > 0.0 for load in right.component_loads)
  assert any(float(load.rod_cut_margin) > 0.0 for load in left.component_loads)

  _assert_component_load_rows_match_events(right)
  _assert_component_load_rows_match_events(left)
  _assert_no_downstream_failure_or_consequence_events(right)
  _assert_no_downstream_failure_or_consequence_events(left)


def test_non_rod_component_projection_carries_no_rod_cut_facts() -> None:
  case = _run_component_cut_case("blast_fragmentation", (-0.8, 4.1, 0.0))

  assert str(case.effects.effect_family) == "blast_fragmentation"
  assert case.component_loads
  assert case.source_rows
  assert all(float(row.mechanism_rod_cut_margin) == 0.0 for row in case.source_rows)
  assert all(float(load.rod_cut_margin) == 0.0 for load in case.component_loads)
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == 0.0

  _assert_component_load_rows_match_events(case)
  _assert_no_downstream_failure_or_consequence_events(case)
