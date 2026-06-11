from __future__ import annotations

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _spawn_geometry_pair,
  ef_py,
)


def test_no_detonation_does_not_emit_standard_load_events() -> None:
  sim = _make_baseline_kernel()
  sim.set_time_step(0.02)

  profile = ef_py.FuzeProfile()
  profile.type = "radar_proximity"
  profile.trigger_radius_m = 35.0
  profile.delay_s = 0.0
  profile.reliability = 0.0
  profile.synthetic = False
  profile.provenance = "test_fuze_no_detonation_event_gate"

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
  assert len(events.damage_reports) == 1

  effects = events.effects_events[0]
  damage_report = events.damage_reports[0]

  nearest_events = list(getattr(events, "nearest_approach_events", []) or [])
  if nearest_events:
    assert str(nearest_events[0].header.reason) == "fuze_no_detonation"
  fuze_events = list(getattr(events, "fuze_evaluation_events", []) or [])
  if fuze_events:
    fuze = fuze_events[0]
    assert str(fuze.header.reason) == "fuze_no_detonation"
    assert not bool(fuze.triggered)
    assert str(fuze.failure_reason) == "fuze_no_detonation"
  assert str(effects.outcome_state) == "fuze_no_detonation"
  assert float(effects.confidence) == 0.0
  assert int(effects.component_hit_count) == 0
  assert list(effects.component_mechanism_load_rows) == []
  assert int(damage_report.source_event_id) == int(effects.event_id)
  assert float(damage_report.hp_delta) == 0.0
  assert not bool(damage_report.destroyed)

  standard_load_counts = {
    "warhead_mechanism_events": len(events.warhead_mechanism_events),
    "spatial_coverage_events": len(events.spatial_coverage_events),
    "component_load_events": len(events.component_load_events),
  }
  assert standard_load_counts == {
    "warhead_mechanism_events": 0,
    "spatial_coverage_events": 0,
    "component_load_events": 0,
  }
