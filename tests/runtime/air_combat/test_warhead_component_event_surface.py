from __future__ import annotations

import math
from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _make_warhead_profile,
  _spawn_geometry_pair,
  _spawn_structured_f16_pair,
  ef_py,
)


# --- warhead spatial component projection surface ---

ProjectionComponentKey = tuple[str, str]


@dataclass(frozen=True)
class ComponentProjectionCase:
  events: object
  effects: object
  spatial: object
  component_loads: list[object]
  loads_by_component: dict[ProjectionComponentKey, object]
  damage_report: object
  target_active: bool


def _generic_synthetic_projection_warhead_profile() -> object:
  profile = ef_py.WarheadProfile()
  profile.family = "blast_fragmentation"
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "test_warhead_spatial_component_projection_generic_research"
  return profile


def _projection_component_key(load: object) -> ProjectionComponentKey:
  return str(load.component_name), str(load.component_system)


def _assert_projection_component_loads_match_effect_rows(
  effects: object,
  component_loads: list[object],
) -> None:
  source_rows = [
    row
    for row in effects.component_mechanism_load_rows
    if str(row.component_name) or str(row.component_system)
  ]
  rows_by_component = {_projection_component_key(row): row for row in source_rows}

  assert source_rows
  assert len(rows_by_component) == len(source_rows)
  assert len(component_loads) == len(source_rows)

  for load in component_loads:
    key = _projection_component_key(load)
    assert key in rows_by_component
    row = rows_by_component[key]

    assert str(load.header.stage) == "component_load"
    assert str(load.header.status) == "projected"
    assert str(load.header.fidelity_mode) == "research_runtime"
    assert str(load.header.evidence_level) == "engineering_assumption"
    assert str(load.header.reason) == "generic_research_component_load_projection"
    assert str(load.component_name) == str(row.component_name)
    assert str(load.component_system) == str(row.component_system)
    assert str(load.component_redundancy_group_id) == str(
      row.component_redundancy_group_id
    )
    assert not bool(load.direct_hit)
    assert not bool(row.direct_hit)
    assert str(load.load_source) == "spatial_component_projection"
    assert float(load.distance_m) == float(row.distance_m)
    assert float(load.effect_scale) == float(row.effect_scale)
    assert float(load.fragment_energy_j) == float(row.mechanism_fragment_energy_j)
    assert float(load.fragment_density_per_m2) == float(
      row.mechanism_fragment_areal_density_per_m2
    )
    assert float(load.blast_overpressure_kpa) == float(
      row.mechanism_blast_overpressure_kpa
    )
    assert not hasattr(load, "component_failure_probability")
    assert not hasattr(load, "failure_probability")
    assert not bool(row.component_failure_probability_authority)
    assert not bool(row.component_failure_probability_calibrated)
    assert not bool(row.component_failure_probability_component_specific)


def _assert_projection_no_downstream_kill_or_real_parameter_claims(
  events: object,
  effects: object,
  damage_report: object,
  target_id: int,
  target_active: bool,
) -> None:
  assert len(events.launch_events) == 0
  assert str(effects.trigger_type) == "debug_profiled_local_proximity_hit"
  assert str(effects.effect_family) == "blast_fragmentation"
  assert bool(effects.warhead_profile_synthetic)
  assert bool(effects.damage_scalar_synthetic)
  assert float(effects.warhead_mass_kg) == 12.0
  assert float(effects.warhead_lethal_radius_m) == 35.0
  assert not bool(effects.direct_hitbox_intersection)

  assert int(effects.target.entity_id) == int(target_id)
  assert int(damage_report.target.entity_id) == int(target_id)
  assert int(damage_report.source_event_id) == int(effects.event_id)
  assert float(damage_report.hp_delta) == 0.0
  assert not bool(damage_report.destroyed)
  assert not bool(damage_report.mission_kill)
  assert not bool(damage_report.mobility_kill)
  assert not bool(damage_report.sensor_kill)
  assert not bool(damage_report.survivability_kill)
  assert not bool(damage_report.forced_landing)
  assert not bool(damage_report.flight_control_kill)
  assert not bool(damage_report.propulsion_kill)
  assert not bool(damage_report.crew_kill)
  assert str(damage_report.loss_state_to) != "lost"
  assert target_active

  assert int(effects.component_failure_count) == len(events.component_damage_events)
  assert not bool(effects.component_failure_probability_calibrated)
  assert not bool(effects.vulnerability_pk_authority)
  assert not bool(effects.vulnerability_calibrated_evidence)
  assert not bool(effects.vulnerability_deterministic_fuze_authority)
  assert not bool(effects.vulnerability_evidence_dataset_valid)
  assert str(effects.vulnerability_calibration_status) == "unvalidated"

  for damage_event in events.component_damage_events:
    assert str(damage_event.header.stage) == "component_damage"
    assert str(damage_event.header.status) == "sampled"
    assert int(damage_event.header.chain_id) == int(effects.event_id)
  assert list(events.platform_consequence_events) == []
  assert list(events.structural_breakup_events) == []
  assert list(events.lifecycle_transition_events) == []
  assert list(events.training_projection_events) == []

  real_model_text = " ".join(
    [
      str(effects.effect_family),
      str(effects.fuze_type),
      str(effects.fuze_signature_source),
      str(effects.vulnerability_evidence_dataset_ref),
      str(effects.vulnerability_evidence_source_ref),
      str(effects.vulnerability_evidence_validation_artifact_ref),
      str(effects.producer_node_id),
    ]
  ).lower()
  assert "aim-120" not in real_model_text
  assert "aim120" not in real_model_text
  assert "mq-9" not in real_model_text
  assert "mq9" not in real_model_text


def _run_profiled_component_projection_case(
  local: tuple[float, float, float],
  velocity: tuple[float, float, float],
) -> ComponentProjectionCase:
  sim = ef_py.SimulationKernel()
  sim.reset(20260610)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _generic_synthetic_projection_warhead_profile(),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  assert ok

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert len(events.warhead_mechanism_events) == 1
  assert len(events.spatial_coverage_events) == 1
  assert len(events.damage_reports) == 1
  assert len(events.component_load_events) > 0

  effects = events.effects_events[0]
  warhead = events.warhead_mechanism_events[0]
  spatial = events.spatial_coverage_events[0]
  component_loads = list(events.component_load_events)
  damage_report = events.damage_reports[0]

  assert str(warhead.header.stage) == "warhead_mechanism"
  assert str(warhead.header.status) == "applied"
  assert str(warhead.header.fidelity_mode) == "research_runtime"
  assert str(warhead.header.evidence_level) == "engineering_assumption"
  assert str(warhead.header.reason) == "generic_research_synthetic_warhead_profile"
  assert str(warhead.mechanism_family) == "blast_fragmentation"
  assert float(warhead.warhead_mass_kg) == 12.0
  assert float(warhead.lethal_radius_m) == 35.0

  assert str(spatial.header.stage) == "spatial_coverage"
  assert str(spatial.header.status) == "projected"
  assert str(spatial.header.fidelity_mode) == "research_runtime"
  assert str(spatial.header.evidence_level) == "engineering_assumption"
  assert str(spatial.header.reason) == "generic_research_spatial_projection"
  assert int(spatial.sample_count) == int(effects.warhead_spatial_sample_count)
  assert int(spatial.projected_hitbox_count) == int(effects.projected_hitbox_count)
  assert float(spatial.energy_scale) == float(effects.warhead_spatial_energy_scale)
  assert float(spatial.pattern_scale) == float(effects.warhead_spatial_pattern_scale)
  assert int(spatial.projected_hitbox_count) > 0

  _assert_projection_component_loads_match_effect_rows(effects, component_loads)
  _assert_projection_no_downstream_kill_or_real_parameter_claims(
    events,
    effects,
    damage_report,
    int(target_id),
    bool(sim.is_unit_active(target_id)),
  )

  loads_by_component = {_projection_component_key(load): load for load in component_loads}
  assert len(loads_by_component) == len(component_loads)
  return ComponentProjectionCase(
    events=events,
    effects=effects,
    spatial=spatial,
    component_loads=component_loads,
    loads_by_component=loads_by_component,
    damage_report=damage_report,
    target_active=bool(sim.is_unit_active(target_id)),
  )


def test_component_loads_track_spatial_coverage_and_local_projection() -> None:
  velocity = (900.0, -250.0, 0.0)
  right_near = _run_profiled_component_projection_case(
    (-0.753, 6.0, 0.0),
    velocity,
  )
  right_far = _run_profiled_component_projection_case(
    (-0.753, 10.0, 0.0),
    velocity,
  )
  left_near = _run_profiled_component_projection_case(
    (-0.753, -6.0, 0.0),
    velocity,
  )

  right_aileron = ("right_aileron_actuator", "flight_control")
  left_aileron = ("left_aileron_actuator", "flight_control")
  right_fuel = ("right_wing_fuel_cell", "fuel")
  left_fuel = ("left_wing_fuel_cell", "fuel")

  assert right_aileron in right_near.loads_by_component
  assert right_aileron in right_far.loads_by_component
  assert left_aileron in left_near.loads_by_component
  assert left_aileron not in right_near.loads_by_component
  assert right_aileron not in left_near.loads_by_component
  assert right_fuel in right_near.loads_by_component
  assert left_fuel in left_near.loads_by_component

  near_load = right_near.loads_by_component[right_aileron]
  far_load = right_far.loads_by_component[right_aileron]
  assert float(right_far.effects.miss_distance_m) > float(
    right_near.effects.miss_distance_m
  )
  assert float(right_far.spatial.energy_scale) < float(
    right_near.spatial.energy_scale
  )
  assert float(far_load.distance_m) > float(near_load.distance_m)
  assert float(far_load.effect_scale) < float(near_load.effect_scale)
  assert float(far_load.fragment_density_per_m2) < float(
    near_load.fragment_density_per_m2
  )
  assert float(far_load.blast_overpressure_kpa) < float(
    near_load.blast_overpressure_kpa
  )

  left_load = left_near.loads_by_component[left_aileron]
  assert str(near_load.component_system) == str(left_load.component_system)
  assert str(near_load.load_source) == str(left_load.load_source)
  assert str(left_load.component_name).startswith("left_")
  assert str(near_load.component_name).startswith("right_")
  assert right_near.target_active
  assert right_far.target_active
  assert left_near.target_active


# --- warhead blast fragmentation loads surface ---

@dataclass(frozen=True)
class MechanismCase:
  effects: object
  warhead: object
  spatial: object
  component_loads: list[object]
  damage_report: object
  target_active: bool

  @property
  def max_component_fragment_density(self) -> float:
    return max(
      (float(load.fragment_density_per_m2) for load in self.component_loads),
      default=0.0,
    )

  @property
  def max_component_overpressure(self) -> float:
    return max(
      (float(load.blast_overpressure_kpa) for load in self.component_loads),
      default=0.0,
    )


def _generic_synthetic_blast_warhead_profile(family: str) -> object:
  profile = ef_py.WarheadProfile()
  profile.family = family
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "test_warhead_blast_fragmentation_loads"
  return profile


def _run_profiled_standard_case(
  family: str,
  local: tuple[float, float, float],
  velocity: tuple[float, float, float],
) -> MechanismCase:
  sim = ef_py.SimulationKernel()
  sim.reset(20260610)
  assert sim.load_database(_DB_PATH)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _generic_synthetic_blast_warhead_profile(family),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  assert ok

  events = sim.export_recent_engagement_events()
  assert len(events.effects_events) == 1
  assert len(events.warhead_mechanism_events) == 1
  assert len(events.spatial_coverage_events) == 1
  assert len(events.damage_reports) == 1
  assert len(events.component_load_events) > 0

  effects = events.effects_events[0]
  warhead = events.warhead_mechanism_events[0]
  spatial = events.spatial_coverage_events[0]
  component_loads = list(events.component_load_events)
  damage_report = events.damage_reports[0]

  assert str(warhead.header.stage) == "warhead_mechanism"
  assert str(warhead.header.status) == "applied"
  assert str(warhead.header.evidence_level) == "engineering_assumption"
  assert str(spatial.header.stage) == "spatial_coverage"
  assert str(spatial.header.status) == "projected"
  assert str(spatial.header.evidence_level) == "engineering_assumption"
  assert str(warhead.mechanism_family) == str(effects.effect_family)
  assert float(warhead.fragment_energy_j) == float(effects.mechanism_fragment_energy_j)
  assert float(warhead.fragment_density_per_m2) == float(
    effects.mechanism_fragment_areal_density_per_m2
  )
  assert float(warhead.blast_overpressure_kpa) == float(
    effects.mechanism_blast_overpressure_kpa
  )
  assert float(warhead.blast_impulse_kpa_ms) == float(
    effects.mechanism_blast_impulse_kpa_ms
  )
  assert float(warhead.blast_scaled_distance_m_kg13) == float(
    effects.mechanism_blast_scaled_distance_m_kg13
  )
  assert int(spatial.sample_count) == int(effects.warhead_spatial_sample_count)
  assert float(spatial.energy_scale) == float(effects.warhead_spatial_energy_scale)
  assert float(spatial.pattern_scale) == float(effects.warhead_spatial_pattern_scale)

  source_rows = [
    row
    for row in effects.component_mechanism_load_rows
    if str(row.component_name) or str(row.component_system)
  ]
  assert len(component_loads) == len(source_rows)
  for load, row in zip(component_loads, source_rows):
    assert str(load.header.stage) == "component_load"
    assert str(load.header.status) == "projected"
    assert str(load.header.evidence_level) == "engineering_assumption"
    assert str(load.component_name) == str(row.component_name)
    assert str(load.component_system) == str(row.component_system)
    assert bool(load.direct_hit) == bool(row.direct_hit)
    assert float(load.distance_m) == float(row.distance_m)
    assert float(load.effect_scale) == float(row.effect_scale)
    assert float(load.fragment_energy_j) == float(row.mechanism_fragment_energy_j)
    assert float(load.fragment_density_per_m2) == float(
      row.mechanism_fragment_areal_density_per_m2
    )
    assert float(load.blast_overpressure_kpa) == float(
      row.mechanism_blast_overpressure_kpa
    )
    assert str(load.load_source) in {
      "direct_component_hit",
      "spatial_component_projection",
    }

  assert int(damage_report.source_event_id) == int(effects.event_id)
  assert float(damage_report.hp_delta) == 0.0
  assert not bool(damage_report.destroyed)
  assert str(damage_report.loss_state_to) != "lost"
  assert sim.is_unit_active(target_id)

  return MechanismCase(
    effects=effects,
    warhead=warhead,
    spatial=spatial,
    component_loads=component_loads,
    damage_report=damage_report,
    target_active=bool(sim.is_unit_active(target_id)),
  )


def test_standard_mechanism_loads_track_range_and_miss_distance() -> None:
  velocity = (900.0, -250.0, 0.0)
  near = _run_profiled_standard_case(
    "blast_fragmentation",
    (-0.753, 6.0, 0.0),
    velocity,
  )
  far = _run_profiled_standard_case(
    "blast_fragmentation",
    (-0.753, 10.0, 0.0),
    velocity,
  )

  assert not bool(near.effects.direct_hitbox_intersection)
  assert not bool(far.effects.direct_hitbox_intersection)
  assert float(far.effects.miss_distance_m) > float(near.effects.miss_distance_m)
  assert float(far.warhead.blast_scaled_distance_m_kg13) > float(
    near.warhead.blast_scaled_distance_m_kg13
  )
  assert float(far.warhead.fragment_energy_j) < float(near.warhead.fragment_energy_j)
  assert float(far.warhead.fragment_density_per_m2) < float(
    near.warhead.fragment_density_per_m2
  )
  assert float(far.warhead.blast_overpressure_kpa) < float(
    near.warhead.blast_overpressure_kpa
  )
  assert far.max_component_fragment_density < near.max_component_fragment_density
  assert far.max_component_overpressure < near.max_component_overpressure


def test_standard_mechanism_loads_track_directional_aspect() -> None:
  local = (-0.753, 7.1, 0.0)
  broadside = _run_profiled_standard_case(
    "blast_fragmentation",
    local,
    (0.0, -900.0, 0.0),
  )
  axial = _run_profiled_standard_case(
    "blast_fragmentation",
    local,
    (-900.0, 0.0, 0.0),
  )

  assert math.isclose(
    float(broadside.effects.miss_distance_m),
    float(axial.effects.miss_distance_m),
    rel_tol=0.0,
    abs_tol=1.0e-9,
  )
  assert float(broadside.spatial.pattern_scale) > float(axial.spatial.pattern_scale)
  assert float(broadside.warhead.fragment_energy_j) > float(
    axial.warhead.fragment_energy_j
  )
  assert float(broadside.warhead.fragment_density_per_m2) > float(
    axial.warhead.fragment_density_per_m2
  )
  assert (
    broadside.max_component_fragment_density
    > axial.max_component_fragment_density
  )


def test_standard_mechanism_loads_track_warhead_family() -> None:
  local = (-0.753, 7.1, 0.0)
  velocity = (900.0, -250.0, 0.0)
  blast = _run_profiled_standard_case("blast", local, velocity)
  blast_fragmentation = _run_profiled_standard_case(
    "blast_fragmentation",
    local,
    velocity,
  )

  assert str(blast.warhead.mechanism_family) == "blast"
  assert float(blast.warhead.blast_overpressure_kpa) > 0.0
  assert float(blast.warhead.blast_impulse_kpa_ms) > 0.0
  assert float(blast.warhead.fragment_energy_j) == 0.0
  assert float(blast.warhead.fragment_density_per_m2) == 0.0
  assert blast.max_component_fragment_density == 0.0

  assert str(blast_fragmentation.warhead.mechanism_family) == "blast_fragmentation"
  assert float(blast_fragmentation.warhead.fragment_energy_j) > 0.0
  assert float(blast_fragmentation.warhead.fragment_density_per_m2) > 0.0
  assert float(blast_fragmentation.warhead.blast_overpressure_kpa) > 0.0
  assert blast_fragmentation.max_component_fragment_density > 0.0
  assert blast_fragmentation.target_active
  assert blast.target_active


# --- component damage event surface ---

DamageComponentKey = tuple[str, str, str]


def _damage_component_key(row_or_event: object) -> DamageComponentKey:
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
  rows_by_component = {_damage_component_key(row): row for row in source_rows}
  loads_by_component = {_damage_component_key(load): load for load in component_loads}

  assert source_rows
  assert int(effects.component_failure_count) == len(source_rows)
  assert len(rows_by_component) == len(source_rows)
  assert len(component_damage_events) == len(source_rows)

  for damage_event in component_damage_events:
    key = _damage_component_key(damage_event)
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
