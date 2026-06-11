from __future__ import annotations

from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _spawn_geometry_pair,
  _spawn_structured_f16_pair,
  ef_py,
)


@dataclass(frozen=True)
class _RodSurfaceCase:
  events: object
  effects: object
  warhead: object
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
  profile.provenance = "test_continuous_rod_event_surface"
  return profile


def _run_profiled_cut_surface_case(family: str) -> _RodSurfaceCase:
  sim = ef_py.SimulationKernel()
  sim.reset(20260611)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    -0.8,
    4.1,
    0.0,
    _warhead_profile(family),
    900.0,
    -250.0,
    0.0,
  )
  assert ok

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert len(events.warhead_mechanism_events) == 1
  assert len(events.component_load_events) > 0

  effects = events.effects_events[0]
  warhead = events.warhead_mechanism_events[0]
  component_loads = list(events.component_load_events)
  source_rows = [
    row
    for row in effects.component_mechanism_load_rows
    if str(row.component_name) or str(row.component_system)
  ]
  assert len(component_loads) == len(source_rows)

  return _RodSurfaceCase(
    events=events,
    effects=effects,
    warhead=warhead,
    component_loads=component_loads,
    source_rows=source_rows,
  )


def _assert_same_effects_chain(case: _RodSurfaceCase) -> None:
  effects = case.effects
  warhead = case.warhead

  assert str(warhead.header.stage) == "warhead_mechanism"
  assert str(warhead.header.status) == "applied"
  assert str(warhead.header.evidence_level) == "engineering_assumption"
  assert int(warhead.header.parent_event_id) == int(effects.event_id)
  assert int(warhead.header.chain_id) == int(effects.event_id)
  assert str(warhead.mechanism_family) == str(effects.effect_family)

  for load, row in zip(case.component_loads, case.source_rows):
    assert str(load.header.stage) == "component_load"
    assert str(load.header.status) == "projected"
    assert str(load.header.evidence_level) == "engineering_assumption"
    assert int(load.header.parent_event_id) == int(effects.event_id)
    assert int(load.header.chain_id) == int(effects.event_id)
    assert str(load.component_name) == str(row.component_name)
    assert str(load.component_system) == str(row.component_system)
    assert float(load.rod_cut_margin) == float(row.mechanism_rod_cut_margin)
    assert str(load.load_source) in {
      "direct_component_hit",
      "spatial_component_projection",
    }


def _assert_no_positive_rod_facts(case: _RodSurfaceCase) -> None:
  assert float(case.effects.mechanism_rod_cut_margin) == 0.0
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == 0.0
  assert float(case.warhead.rod_cut_margin) == 0.0
  assert all(float(load.rod_cut_margin) == 0.0 for load in case.component_loads)
  assert all(float(row.mechanism_rod_cut_margin) == 0.0 for row in case.source_rows)


def test_continuous_rod_detonation_reuses_standard_rod_fields() -> None:
  case = _run_profiled_cut_surface_case("continuous_rod")

  _assert_same_effects_chain(case)
  assert str(case.effects.effect_family) == "continuous_rod"
  assert float(case.effects.mechanism_rod_cut_margin) > 0.0
  assert float(case.warhead.rod_cut_margin) == float(
    case.effects.mechanism_rod_cut_margin
  )
  assert any(float(load.rod_cut_margin) > 0.0 for load in case.component_loads)
  assert any(float(row.mechanism_rod_cut_margin) > 0.0 for row in case.source_rows)
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == max(
    float(load.rod_cut_margin) for load in case.component_loads
  )


def test_non_rod_detonation_has_no_positive_standard_rod_facts() -> None:
  case = _run_profiled_cut_surface_case("blast_fragmentation")

  _assert_same_effects_chain(case)
  assert str(case.effects.effect_family) == "blast_fragmentation"
  assert float(case.warhead.fragment_energy_j) > 0.0
  assert float(case.warhead.blast_overpressure_kpa) > 0.0
  _assert_no_positive_rod_facts(case)


def test_no_detonation_has_no_positive_rod_or_cut_facts() -> None:
  sim = _make_baseline_kernel()
  sim.set_time_step(0.02)

  fuze = ef_py.FuzeProfile()
  fuze.type = "radar_proximity"
  fuze.trigger_radius_m = 35.0
  fuze.delay_s = 0.0
  fuze.reliability = 0.0
  fuze.synthetic = False
  fuze.provenance = "test_continuous_rod_event_surface_no_detonation"

  tuning = sim.get_missile_tuning()
  tuning.fuze_profile = fuze
  tuning.has_fuze_profile = True
  tuning.warhead_profile = _warhead_profile("continuous_rod")
  tuning.has_warhead_profile = True
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

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  effects = events.effects_events[0]
  assert str(effects.outcome_state) == "fuze_no_detonation"
  assert str(effects.effect_family) == "continuous_rod"
  assert float(effects.mechanism_rod_cut_margin) == 0.0
  assert float(effects.component_primary_mechanism_rod_cut_margin) == 0.0
  assert list(effects.component_mechanism_load_rows) == []

  fuze_events = list(events.fuze_evaluation_events)
  assert len(fuze_events) == 1
  assert not bool(fuze_events[0].triggered)
  assert str(fuze_events[0].failure_reason) == "fuze_no_detonation"

  assert list(events.warhead_mechanism_events) == []
  assert list(events.spatial_coverage_events) == []
  assert list(events.component_load_events) == []
