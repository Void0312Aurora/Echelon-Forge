from __future__ import annotations

import math
from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _component_response_row_by_name,
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _spawn_geometry_pair,
  _spawn_structured_f16_pair,
  ef_py,
)
from tools.diagnostics import air_combat_weapon_employment_process_probe as probe


def _warhead_profile(family: str, provenance: str) -> object:
  profile = ef_py.WarheadProfile()
  profile.family = family
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = provenance
  return profile


@dataclass(frozen=True)
class _RodSurfaceCase:
  events: object
  effects: object
  warhead: object
  component_loads: list[object]
  source_rows: list[object]


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
    -0.985,
    _warhead_profile(family, "test_continuous_rod_event_surface"),
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
  primary_load = next(
    load
    for load in case.component_loads
    if str(load.component_name) == str(case.effects.component_primary_name)
    and str(load.component_system) == str(case.effects.component_primary_system)
  )
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == float(
    primary_load.rod_cut_margin
  )
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) <= max(
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
  tuning.warhead_profile = _warhead_profile("continuous_rod", "test_continuous_rod_event_surface_no_detonation")
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


@dataclass(frozen=True)
class _RodGeometryCase:
  effects: object
  warhead: object
  component_loads: list[object]


def _run_profiled_rod_geometry_case(
  local: tuple[float, float, float],
  velocity: tuple[float, float, float],
  attitude_deg: tuple[float, float, float] | None = None,
) -> _RodGeometryCase:
  sim = ef_py.SimulationKernel()
  sim.reset(20260611)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _warhead_profile("continuous_rod", "test_continuous_rod_geometry_response")

  if attitude_deg is None:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      float(local[0]),
      float(local[1]),
      float(local[2]),
      profile,
      float(velocity[0]),
      float(velocity[1]),
      float(velocity[2]),
    )
  else:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
      attacker_id,
      target_id,
      float(local[0]),
      float(local[1]),
      float(local[2]),
      profile,
      float(velocity[0]),
      float(velocity[1]),
      float(velocity[2]),
      float(attitude_deg[0]),
      float(attitude_deg[1]),
      float(attitude_deg[2]),
    )
  assert ok

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert len(events.warhead_mechanism_events) == 1
  assert len(events.component_load_events) > 0

  effects = events.effects_events[0]
  warhead = events.warhead_mechanism_events[0]
  assert str(effects.effect_family) == "continuous_rod"
  assert str(warhead.mechanism_family) == "continuous_rod"
  assert float(effects.mechanism_rod_cut_margin) == float(warhead.rod_cut_margin)
  assert float(effects.mechanism_rod_cut_margin) > 0.0

  return _RodGeometryCase(
    effects=effects,
    warhead=warhead,
    component_loads=list(events.component_load_events),
  )


def test_continuous_rod_cut_margin_falls_with_range() -> None:
  velocity = (0.0, -900.0, 0.0)
  near = _run_profiled_rod_geometry_case((-0.753, 7.1, 0.0), velocity)
  far = _run_profiled_rod_geometry_case((-0.753, 14.0, 0.0), velocity)

  assert float(near.effects.miss_distance_m) < float(far.effects.miss_distance_m)
  assert float(near.effects.warhead_spatial_hit_estimate) > float(
    far.effects.warhead_spatial_hit_estimate
  )
  assert float(near.effects.mechanism_rod_cut_margin) > float(
    far.effects.mechanism_rod_cut_margin
  )
  assert float(near.effects.component_primary_mechanism_rod_cut_margin) > float(
    far.effects.component_primary_mechanism_rod_cut_margin
  )


def test_continuous_rod_cut_margin_tracks_side_sweep_axis() -> None:
  local_wing = (-0.753, 7.1, 0.0)
  broadside = _run_profiled_rod_geometry_case(local_wing, (0.0, -900.0, 0.0))
  axial = _run_profiled_rod_geometry_case(local_wing, (-900.0, 0.0, 0.0))

  assert float(broadside.effects.miss_distance_m) == float(axial.effects.miss_distance_m)
  assert float(broadside.effects.warhead_spatial_pattern_scale) > float(
    axial.effects.warhead_spatial_pattern_scale
  )
  assert float(broadside.effects.warhead_spatial_hit_estimate) > float(
    axial.effects.warhead_spatial_hit_estimate
  )
  assert float(broadside.effects.mechanism_rod_cut_margin) > float(
    axial.effects.mechanism_rod_cut_margin
  )


def test_continuous_rod_cut_margin_tracks_local_aspect() -> None:
  velocity = (0.0, -900.0, 0.0)
  beam = _run_profiled_rod_geometry_case((-0.753, 7.1, 0.0), velocity)
  tail = _run_profiled_rod_geometry_case((-6.5, 0.0, 0.0), velocity)

  assert str(beam.effects.vulnerability_aspect_bucket) == "beam"
  assert str(tail.effects.vulnerability_aspect_bucket) == "tail"
  assert float(beam.effects.vulnerability_aspect_scale) > float(
    tail.effects.vulnerability_aspect_scale
  )
  assert float(beam.effects.mechanism_rod_cut_margin) > float(
    tail.effects.mechanism_rod_cut_margin
  )


def test_continuous_rod_cut_margin_tracks_orientation_axis() -> None:
  local_wing = (-0.753, 7.1, 0.0)
  velocity = (0.0, -900.0, 0.0)
  forward_oriented = _run_profiled_rod_geometry_case(
    local_wing,
    velocity,
    (0.0, 0.0, 0.0),
  )
  right_oriented = _run_profiled_rod_geometry_case(
    local_wing,
    velocity,
    (90.0, 0.0, 0.0),
  )

  assert abs(float(forward_oriented.effects.warhead_orientation_axis_forward)) == 1.0
  assert abs(float(right_oriented.effects.warhead_orientation_axis_right)) == 1.0
  assert float(forward_oriented.effects.warhead_orientation_pattern_scale) > float(
    right_oriented.effects.warhead_orientation_pattern_scale
  )
  assert float(forward_oriented.effects.warhead_spatial_pattern_scale) > float(
    right_oriented.effects.warhead_spatial_pattern_scale
  )
  assert float(forward_oriented.effects.mechanism_rod_cut_margin) > float(
    right_oriented.effects.mechanism_rod_cut_margin
  )


@dataclass(frozen=True)
class _ComponentCutCase:
  events: object
  effects: object
  component_loads: list[object]
  source_rows: list[object]


def _run_component_cut_case(
  family: str,
  local: tuple[float, float, float],
  velocity: tuple[float, float, float] = (900.0, -250.0, 0.0),
  step_after_hit: bool = False,
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
    _warhead_profile(family, "test_continuous_rod_component_cut_projection"),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  assert ok

  if step_after_hit:
    sim.step()

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


def _assert_no_platform_consequence_events(case: _ComponentCutCase) -> None:
  assert list(case.events.structural_breakup_events) == []
  assert list(case.events.lifecycle_transition_events) == []
  assert list(case.events.training_projection_events) == []


def _assert_no_lifecycle_or_training_events(case: _ComponentCutCase) -> None:
  assert list(case.events.lifecycle_transition_events) == []
  assert list(case.events.training_projection_events) == []


def _assert_detached_part_lifecycle_and_no_training_events(
  case: _ComponentCutCase,
) -> None:
  structural_events = list(case.events.structural_breakup_events)
  lifecycle_events = list(case.events.lifecycle_transition_events)
  assert structural_events
  assert len(lifecycle_events) == len(structural_events)
  assert list(case.events.training_projection_events) == []

  structural_by_event_id = {
    int(event.header.event_id): event for event in structural_events
  }
  for lifecycle in lifecycle_events:
    parent_event_id = int(lifecycle.header.parent_event_id)
    assert parent_event_id in structural_by_event_id
    structural = structural_by_event_id[parent_event_id]

    assert str(lifecycle.header.stage) == "lifecycle"
    assert int(lifecycle.header.chain_id) == int(structural.header.chain_id)
    assert str(lifecycle.header.producer_node_id) == "damage_system.structural_lifecycle"
    assert str(lifecycle.header.consumer_visibility) == "diagnostics_only"
    assert str(lifecycle.lifecycle_from) == "attached_airframe_part"
    assert str(lifecycle.lifecycle_to) == "detached_part_debris_fact"
    assert str(lifecycle.ground_lifecycle) == "unknown"
    assert int(lifecycle.debris_count) == int(structural.detached_part_count)
    assert not bool(lifecycle.terminal)
    assert int(lifecycle.terminal_projection_id) == int(structural.header.event_id)


def _assert_wing_loss_event(case: _ComponentCutCase, detached_part_ref: str) -> None:
  assert any(
    str(event.break_mode) == "wing_loss"
    and str(event.detached_part_ref) == detached_part_ref
    for event in case.events.structural_breakup_events
  )


def _assert_component_damage_events_match_failed_rows(
  case: _ComponentCutCase,
  *,
  allow_structural_breakup: bool = False,
) -> None:
  damages = list(case.events.component_damage_events)
  assert damages
  for damage in damages:
    row = _component_response_row_by_name(case.effects, str(damage.component_name))
    assert float(row.failure_sample) <= float(row.failure_probability)
    assert float(damage.failure_probability) == float(row.failure_probability)
    assert float(damage.failure_sample) == float(row.failure_sample)
    assert float(damage.integrity_after) == float(row.integrity_after)
  if allow_structural_breakup:
    _assert_detached_part_lifecycle_and_no_training_events(case)
  else:
    _assert_no_platform_consequence_events(case)


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
  case = _run_component_cut_case(
    "continuous_rod",
    (-0.753, 7.1, -0.985),
    step_after_hit=True,
  )

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
  _assert_wing_loss_event(case, "right_wing")
  _assert_detached_part_lifecycle_and_no_training_events(case)

  primary_row = _primary_source_row(case)
  assert str(case.effects.component_primary_name) == "right_aileron_actuator"
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == float(
    primary_row.mechanism_rod_cut_margin
  )


def test_component_center_projection_uses_spatial_load_source() -> None:
  case = _run_component_cut_case(
    "continuous_rod",
    (-0.8, 4.1, -0.985),
    step_after_hit=True,
  )

  assert str(case.effects.effect_family) == "continuous_rod"
  assert [str(row.component_name) for row in case.source_rows] == [
    "right_aileron_actuator",
    "right_wing_fuel_cell",
  ]
  assert all(str(load.load_source) == "spatial_component_projection" for load in case.component_loads)
  assert all(not bool(row.direct_hit) for row in case.source_rows)
  assert all(not bool(load.direct_hit) for load in case.component_loads)
  assert str(case.effects.component_primary_name) == "right_aileron_actuator"
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) > 0.0
  primary_row = _primary_source_row(case)
  assert float(primary_row.mechanism_rod_cut_margin) == float(
    case.effects.component_primary_mechanism_rod_cut_margin
  )

  _assert_component_load_rows_match_events(case)
  _assert_component_damage_events_match_failed_rows(
    case,
    allow_structural_breakup=True,
  )
  _assert_wing_loss_event(case, "right_wing")


def test_local_side_changes_emphasized_component_rows() -> None:
  right = _run_component_cut_case(
    "continuous_rod",
    (-0.753, 7.1, -0.985),
    step_after_hit=True,
  )
  left = _run_component_cut_case(
    "continuous_rod",
    (-0.753, -7.1, -0.985),
    step_after_hit=True,
  )

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
  _assert_wing_loss_event(right, "right_wing")
  _assert_wing_loss_event(left, "left_wing")
  _assert_detached_part_lifecycle_and_no_training_events(right)
  _assert_detached_part_lifecycle_and_no_training_events(left)


def test_non_rod_component_projection_carries_no_rod_cut_facts() -> None:
  case = _run_component_cut_case("blast_fragmentation", (-0.8, 4.1, -0.985))

  assert str(case.effects.effect_family) == "blast_fragmentation"
  assert case.component_loads
  assert case.source_rows
  assert all(float(row.mechanism_rod_cut_margin) == 0.0 for row in case.source_rows)
  assert all(float(load.rod_cut_margin) == 0.0 for load in case.component_loads)
  assert float(case.effects.component_primary_mechanism_rod_cut_margin) == 0.0

  _assert_component_load_rows_match_events(case)
  _assert_component_damage_events_match_failed_rows(case)


def _run_profiled_diagnostic_case(family: str) -> object:
  sim = ef_py.SimulationKernel()
  sim.reset(20260611)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    -0.753,
    7.1,
    0.0,
    _warhead_profile(family, "test_continuous_rod_diagnostic_projection"),
    0.0,
    -900.0,
    0.0,
  )
  assert ok
  return sim.export_recent_engagement_events()


def _run_no_detonation_diagnostic_case() -> object:
  sim = _make_baseline_kernel()
  sim.set_time_step(0.02)

  fuze = ef_py.FuzeProfile()
  fuze.type = "radar_proximity"
  fuze.trigger_radius_m = 35.0
  fuze.delay_s = 0.0
  fuze.reliability = 0.0
  fuze.synthetic = False
  fuze.provenance = "test_continuous_rod_diagnostic_projection_no_detonation"

  tuning = sim.get_missile_tuning()
  tuning.fuze_profile = fuze
  tuning.has_fuze_profile = True
  tuning.warhead_profile = _warhead_profile("continuous_rod", "test_continuous_rod_diagnostic_projection_no_detonation")
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
  return sim.export_recent_engagement_events()


def _diagnostic_rows(events: object) -> list[dict[str, object]]:
  return probe._lethality_chain_rows(
    episode=7,
    step=12,
    sim_time_s=4.5,
    engagement_events=events,
  )


def _stage_rows(rows: list[dict[str, object]], stage: str) -> list[dict[str, object]]:
  return [row for row in rows if str(row.get("stage", "")) == stage]


def test_diagnostics_explain_standard_continuous_rod_facts() -> None:
  rows = _diagnostic_rows(_run_profiled_diagnostic_case("continuous_rod"))
  warhead_rows = _stage_rows(rows, "warhead_mechanism")
  component_rows = _stage_rows(rows, "component_load")

  assert len(warhead_rows) == 1
  assert warhead_rows[0]["source_event_kind"] == "WarheadMechanismEvent"
  assert warhead_rows[0]["mechanism_family"] == "continuous_rod"
  assert float(warhead_rows[0]["rod_cut_margin"]) > 0.0
  assert component_rows
  assert all(row["source_event_kind"] == "ComponentLoadEvent" for row in component_rows)
  assert any(float(row["rod_cut_margin"]) > 0.0 for row in component_rows)
  assert all(
    str(row["component_load_source"]) == "spatial_component_projection"
    for row in component_rows
  )

  snapshot = probe._lethality_chain_snapshot_columns(rows)
  assert snapshot["lethality_chain_mechanism_family"] == "continuous_rod"
  assert float(snapshot["lethality_chain_rod_cut_margin"]) == float(
    warhead_rows[0]["rod_cut_margin"]
  )
  assert float(snapshot["lethality_chain_component_rod_cut_margin"]) == float(
    component_rows[-1]["rod_cut_margin"]
  )


def test_diagnostics_keep_non_rod_cut_facts_zero() -> None:
  rows = _diagnostic_rows(_run_profiled_diagnostic_case("blast_fragmentation"))
  warhead_rows = _stage_rows(rows, "warhead_mechanism")
  component_rows = _stage_rows(rows, "component_load")

  assert len(warhead_rows) == 1
  assert warhead_rows[0]["source_event_kind"] == "WarheadMechanismEvent"
  assert warhead_rows[0]["mechanism_family"] == "blast_fragmentation"
  assert float(warhead_rows[0]["rod_cut_margin"]) == 0.0
  assert component_rows
  assert all(row["source_event_kind"] == "ComponentLoadEvent" for row in component_rows)
  assert all(float(row["rod_cut_margin"]) == 0.0 for row in component_rows)

  snapshot = probe._lethality_chain_snapshot_columns(rows)
  assert snapshot["lethality_chain_mechanism_family"] == "blast_fragmentation"
  assert float(snapshot["lethality_chain_rod_cut_margin"]) == 0.0
  assert float(snapshot["lethality_chain_component_rod_cut_margin"]) == 0.0


def test_no_detonation_does_not_synthesize_rod_diagnostic_rows() -> None:
  events = _run_no_detonation_diagnostic_case()
  rows = _diagnostic_rows(events)
  stages = {str(row["stage"]) for row in rows}

  assert str(events.effects_events[0].outcome_state) == "fuze_no_detonation"
  assert "nearest_approach" in stages
  assert "fuze" in stages
  assert "warhead_mechanism" not in stages
  assert "spatial_coverage" not in stages
  assert "component_load" not in stages

  snapshot = probe._lethality_chain_snapshot_columns(rows)
  assert snapshot["lethality_chain_fuze_triggered"] == 0
  assert snapshot["lethality_chain_fuze_failure_reason"] == "fuze_no_detonation"
  assert math.isnan(float(snapshot["lethality_chain_rod_cut_margin"]))
  assert math.isnan(float(snapshot["lethality_chain_component_rod_cut_margin"]))
