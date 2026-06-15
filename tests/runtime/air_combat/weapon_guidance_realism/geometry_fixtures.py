from __future__ import annotations

import math

from .helpers import (
  _drive_missile_with_truth_track,
  _make_baseline_kernel,
  _relative_detection_from_truth,
  _spawn_geometry_pair,
)


class GeometryFixtureRuntimeMixin:
  def _run_controlled_geometry_case(self, **geometry: float) -> dict[str, object]:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)
    blue_id, red_id = _spawn_geometry_pair(sim, **geometry)
    initial_detection = _relative_detection_from_truth(
      sim,
      blue_id,
      red_id,
      timestamp=0.0,
    )

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    result = _drive_missile_with_truth_track(
      sim,
      missile_id,
      red_id,
      max_steps=3600,
    )
    events = sim.export_recent_engagement_events()
    self.assertGreaterEqual(len(events.effects_events), 1)
    self.assertGreaterEqual(len(events.nearest_approach_events), 1)
    self.assertGreaterEqual(len(events.fuze_evaluation_events), 1)
    effects = events.effects_events[-1]
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]

    self.assertFalse(bool(result["missile_active"]))
    self.assertTrue(bool(result["proximity_engaged"]))
    self.assertEqual(str(effects.trigger_type), "proximity_fuze")
    self.assertEqual(str(nearest.header.stage), "nearest_approach")
    self.assertEqual(str(nearest.header.status), "observed")
    self.assertIn(
      str(nearest.header.reason),
      {
        "fuze_armed",
        "fuze_no_detonation",
        "fuze_no_terminal_track",
        "miss_outside_trigger_radius",
      },
    )
    self.assertGreater(int(nearest.header.event_id), 0)
    self.assertGreater(int(nearest.header.chain_id), 0)
    self.assertEqual(int(nearest.header.parent_event_id), int(nearest.header.chain_id))
    self.assertEqual(int(nearest.header.munition.entity_id), missile_id)
    self.assertEqual(int(nearest.header.target.entity_id), red_id)
    self.assertEqual(str(fuze.header.stage), "fuze")
    self.assertEqual(str(fuze.header.status), "evaluated")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertEqual(int(fuze.header.chain_id), int(nearest.header.chain_id))
    self.assertEqual(int(fuze.header.parent_event_id), int(nearest.header.event_id))
    self.assertEqual(int(fuze.header.munition.entity_id), missile_id)
    self.assertEqual(int(fuze.header.target.entity_id), red_id)
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertGreater(float(fuze.trigger_radius_m), 0.0)
    self.assertGreaterEqual(float(fuze.sample), 0.0)
    self.assertLessEqual(float(fuze.sample), 1.0)
    self.assertTrue(math.isfinite(float(effects.miss_distance_m)))
    self.assertTrue(math.isfinite(float(effects.nearest_approach_time_s)))
    self.assertAlmostEqual(
      float(result["proximity_min_dist_m"]),
      float(effects.miss_distance_m),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(nearest.miss_distance_m),
      float(result["proximity_min_dist_m"]),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(nearest.nearest_approach_time_s),
      float(effects.nearest_approach_time_s),
      delta=sim.get_time_step() + 1.0e-6,
    )
    self.assertAlmostEqual(
      float(nearest.local_forward_m),
      float(effects.detonation_local_forward_m),
      delta=1.0e-3,
    )
    self.assertAlmostEqual(
      float(nearest.local_right_m),
      float(effects.detonation_local_right_m),
      delta=1.0e-3,
    )
    self.assertAlmostEqual(
      float(nearest.local_up_m),
      float(effects.detonation_local_up_m),
      delta=1.0e-3,
    )
    self.assertAlmostEqual(
      float(nearest.closure_mps),
      float(effects.closure_mps),
      delta=1.0e-6,
    )
    self.assertIn(str(nearest.aspect_bucket), {"nose", "tail", "beam"})
    return {
      "initial_detection": initial_detection,
      "result": result,
      "effects": effects,
      "nearest": nearest,
      "fuze": fuze,
    }

  def test_live_controlled_geometry_varies_range_and_closure_without_policy_fire(self) -> None:
    near_fast = self._run_controlled_geometry_case(
      red_x=0.0,
      red_y=9000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-260.0,
    )
    far_fast = self._run_controlled_geometry_case(
      red_x=0.0,
      red_y=15000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-260.0,
    )
    near_slow = self._run_controlled_geometry_case(
      red_x=0.0,
      red_y=9000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=100.0,
    )

    near_fast_detection = near_fast["initial_detection"]
    far_fast_detection = far_fast["initial_detection"]
    near_slow_detection = near_slow["initial_detection"]
    near_fast_effects = near_fast["effects"]
    far_fast_effects = far_fast["effects"]
    near_slow_effects = near_slow["effects"]

    self.assertGreater(
      float(far_fast_detection.range),
      float(near_fast_detection.range) + 4000.0,
    )
    self.assertGreater(
      float(far_fast_effects.nearest_approach_time_s),
      float(near_fast_effects.nearest_approach_time_s) + 3.0,
    )
    self.assertGreater(
      float(near_fast_detection.closing_speed),
      float(near_slow_detection.closing_speed) + 250.0,
    )
    self.assertGreater(
      float(near_fast_effects.closure_mps),
      float(near_slow_effects.closure_mps) + 100.0,
    )

  def test_live_controlled_geometry_varies_aspect_and_altitude_offset(self) -> None:
    head_on_level = self._run_controlled_geometry_case(
      red_x=0.0,
      red_y=9000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-260.0,
    )
    crossing_level = self._run_controlled_geometry_case(
      red_x=5000.0,
      red_y=9000.0,
      red_heading=270.0,
      red_vx=-260.0,
      red_vy=0.0,
    )
    head_on_high = self._run_controlled_geometry_case(
      red_x=0.0,
      red_y=9000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-260.0,
      red_z=6500.0,
    )

    head_on_detection = head_on_level["initial_detection"]
    crossing_detection = crossing_level["initial_detection"]
    high_detection = head_on_high["initial_detection"]
    head_on_effects = head_on_level["effects"]
    high_effects = head_on_high["effects"]

    self.assertAlmostEqual(float(head_on_detection.bearing), 0.0, delta=1.0)
    self.assertGreater(abs(float(crossing_detection.bearing)), 20.0)
    self.assertAlmostEqual(float(head_on_detection.elevation), 0.0, delta=1.0)
    self.assertGreater(float(high_detection.elevation), 5.0)
    self.assertGreater(
      abs(float(high_effects.detonation_local_up_m)),
      abs(float(head_on_effects.detonation_local_up_m)) + 2.0,
    )
