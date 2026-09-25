from __future__ import annotations

import ef_py

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _spawn_geometry_pair,
)


def test_online_sensor_delayed_burst_stays_in_trigger_frame_geometry() -> None:
  sim = _make_baseline_kernel(seed=20260516)
  sim.set_time_step(0.05)

  profile = ef_py.FuzeProfile()
  profile.type = "radar_proximity"
  profile.trigger_radius_m = 15.0
  profile.delay_s = 0.015
  profile.reliability = 1.0
  profile.trigger_logic = "online_sensor"
  profile.synthetic = False
  profile.provenance = "test_online_sensor_delayed_burst_projection"

  tuning = sim.get_missile_tuning()
  tuning.fuze_profile = profile
  tuning.has_fuze_profile = True
  sim.set_missile_tuning(tuning)

  blue_id, red_id = _spawn_geometry_pair(
    sim,
    red_x=0.0,
    red_y=12000.0,
    red_heading=180.0,
    red_vx=0.0,
    red_vy=-250.0,
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
  assert str(effects.detonation_point_source) == "online_sensor_delay_solution"
  # The delayed burst may travel beyond the fuze trigger radius.  The gate is
  # that it remains near the trigger-frame solution instead of falling back to
  # the next ECS frame's missile pose (the pre-fix probe was about 49 m here).
  assert float(effects.miss_distance_m) < 25.0
  assert str(effects.outcome_state) in {"damage_applied", "detonated_no_effect"}
