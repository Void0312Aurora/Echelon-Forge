from __future__ import annotations

import math
from dataclasses import dataclass

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _DB_PATH,
  _spawn_structured_f16_pair,
  ef_py,
)


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


def _generic_synthetic_warhead_profile(family: str) -> object:
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
    _generic_synthetic_warhead_profile(family),
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
