from __future__ import annotations

from .helpers import *


class FuzeRuntimeMixin:
  def test_global_fuze_profile_override_flows_into_runtime_and_effects_event(self) -> None:
    sim = _make_baseline_kernel(seed=2026061000)

    profile = ef_py.FuzeProfile()
    profile.type = "laser_proximity"
    profile.trigger_radius_m = 35.0
    profile.delay_s = 0.02
    profile.reliability = 0.88
    profile.synthetic = False
    profile.provenance = "test_authored_fuze_profile"

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
    self.assertGreater(missile_id, 0)
    runtime = _missile_runtime(sim, missile_id)
    self.assertAlmostEqual(float(runtime["fuse_distance_m"]), 35.0, delta=1.0e-6)
    self.assertEqual(str(runtime["fuze_type"]), "laser_proximity")
    self.assertAlmostEqual(float(runtime["fuze_trigger_radius_m"]), 35.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["fuze_delay_s"]), 0.02, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["fuze_reliability"]), 0.88, delta=1.0e-6)
    self.assertEqual(str(runtime["fuze_trigger_logic"]), "online_sensor")
    self.assertFalse(bool(runtime["fuze_profile_synthetic"]))

    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()

    events = sim.export_recent_engagement_events()
    self.assertGreaterEqual(len(events.effects_events), 1)
    effects = events.effects_events[-1]
    self.assertEqual(str(effects.fuze_type), "laser_proximity")
    self.assertAlmostEqual(float(effects.fuze_trigger_radius_m), 35.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.fuze_delay_s), 0.02, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.fuze_reliability), 0.88, delta=1.0e-6)
    self.assertFalse(bool(effects.fuze_profile_synthetic))
    self.assertEqual(str(effects.detonation_point_source), "online_sensor_delay_solution")
    self.assertEqual(str(effects.fuze_signature_source), "target_projected_geometry")
    self.assertGreater(float(effects.fuze_target_signature), 1.0)
    self.assertGreater(float(effects.fuze_signature_scale), 0.0)
    self.assertLessEqual(float(effects.fuze_signature_scale), 1.15)
    self.assertAlmostEqual(
      float(effects.fuze_effective_reliability),
      min(1.0, 0.88 * float(effects.fuze_signature_scale)),
      delta=1.0e-6,
    )

  def test_fuze_delay_schedules_detonation_after_nearest_approach(self) -> None:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 35.0
    profile.delay_s = 0.08
    profile.reliability = 1.0
    profile.trigger_logic = "nearest_approach"
    profile.synthetic = False
    profile.provenance = "test_delay_fuze_profile"

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
    self.assertGreater(missile_id, 0)

    armed_seen = False
    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()
      if sim.is_unit_active(missile_id):
        runtime = _missile_runtime(sim, missile_id)
        if bool(runtime["fuze_delay_armed"]):
          armed_seen = True
          self.assertTrue(math.isfinite(float(runtime["fuze_nearest_approach_time_s"])))
          min_local_norm = math.sqrt(
            float(runtime["proximity_min_local_forward_m"]) ** 2
            + float(runtime["proximity_min_local_right_m"]) ** 2
            + float(runtime["proximity_min_local_up_m"]) ** 2
          )
          self.assertAlmostEqual(
            min_local_norm,
            float(runtime["proximity_min_dist_m"]),
            delta=1.0e-3,
          )
          self.assertEqual(str(runtime["fuze_signature_source"]), "target_rcs_aspect")
          self.assertGreater(float(runtime["fuze_target_signature"]), 0.0)
          self.assertGreater(float(runtime["fuze_signature_scale"]), 0.0)
          self.assertLessEqual(float(runtime["fuze_effective_reliability"]), 1.0)
          self.assertAlmostEqual(
            float(runtime["fuze_detonation_time_s"]) -
            float(runtime["fuze_nearest_approach_time_s"]),
            0.08,
            delta=sim.get_time_step() + 1.0e-6,
          )
          self.assertGreater(float(runtime["fuze_hit_probability"]), 0.0)
          self.assertEqual(str(runtime["fuze_sensor_opportunity_source"]), "proximity_sensor_window")
          self.assertGreater(float(runtime["fuze_sensor_opportunity_score"]), 0.0)
          self.assertTrue(bool(runtime["fuze_terminal_track_valid"]))
          self.assertTrue(bool(runtime["fuze_target_detected"]))
          self.assertEqual(str(runtime["fuze_target_detection_source"]), "target_rcs_aspect")
          self.assertGreaterEqual(
            float(runtime["fuze_target_detection_confidence"]),
            float(runtime["fuze_target_detection_threshold"]),
          )
          self.assertEqual(str(runtime["fuze_detonation_point_source"]), "sensor_window_delay_solution")
          self.assertGreater(float(runtime["fuze_mechanism_coverage_score"]), 0.0)

    self.assertTrue(armed_seen)
    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]
    self.assertEqual(str(nearest.header.reason), "fuze_armed")
    self.assertEqual(str(fuze.header.stage), "fuze")
    self.assertEqual(str(fuze.header.status), "evaluated")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertEqual(int(fuze.header.parent_event_id), int(nearest.header.event_id))
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertEqual(str(fuze.sensor_opportunity_source), "proximity_sensor_window")
    self.assertGreater(float(fuze.sensor_opportunity_score), 0.0)
    self.assertTrue(bool(fuze.terminal_track_valid))
    self.assertTrue(bool(fuze.target_detected))
    self.assertEqual(str(fuze.target_detection_source), "target_rcs_aspect")
    self.assertGreaterEqual(
      float(fuze.target_detection_confidence),
      float(fuze.target_detection_threshold),
    )
    self.assertEqual(str(fuze.detonation_point_source), "sensor_window_delay_solution")
    self.assertGreater(float(fuze.mechanism_coverage_score), 0.0)
    self.assertEqual(str(effects.fuze_type), "radar_proximity")
    self.assertAlmostEqual(float(effects.fuze_delay_s), 0.08, delta=1.0e-6)
    self.assertEqual(str(effects.fuze_signature_source), "target_rcs_aspect")
    self.assertGreater(float(effects.fuze_target_signature), 0.0)
    self.assertGreater(float(effects.fuze_signature_scale), 0.0)
    self.assertLessEqual(float(effects.fuze_effective_reliability), 1.0)
    self.assertEqual(str(effects.fuze_sensor_opportunity_source), "proximity_sensor_window")
    self.assertGreater(float(effects.fuze_sensor_opportunity_score), 0.0)
    self.assertTrue(bool(effects.fuze_terminal_track_valid))
    self.assertTrue(bool(effects.fuze_target_detected))
    self.assertEqual(str(effects.fuze_target_detection_source), "target_rcs_aspect")
    self.assertGreaterEqual(
      float(effects.fuze_target_detection_confidence),
      float(effects.fuze_target_detection_threshold),
    )
    self.assertEqual(str(effects.detonation_point_source), "sensor_window_delay_solution")
    self.assertGreater(float(effects.fuze_mechanism_coverage_score), 0.0)
    self.assertGreater(float(effects.detonation_time_s), float(effects.nearest_approach_time_s))
    self.assertAlmostEqual(
      float(effects.detonation_time_s) - float(effects.nearest_approach_time_s),
      0.08,
      delta=sim.get_time_step() + 1.0e-6,
    )
    detonation_local_norm = math.sqrt(
      float(effects.detonation_local_forward_m) ** 2
      + float(effects.detonation_local_right_m) ** 2
      + float(effects.detonation_local_up_m) ** 2
    )
    self.assertAlmostEqual(
      detonation_local_norm,
      float(effects.miss_distance_m),
      delta=1.0e-3,
    )
    self.assertTrue(
      bool(effects.direct_hitbox_intersection)
      or int(effects.projected_hitbox_count) > 0
      or int(effects.component_hit_count) > 0
    )

  def test_online_sensor_fuze_triggers_before_legacy_nearest_point_proxy(self) -> None:
    def run_case(trigger_logic: str) -> tuple[object, object, object]:
      sim = _make_baseline_kernel(seed=2026061000)
      sim.set_time_step(0.02)

      profile = ef_py.FuzeProfile()
      profile.type = "radar_proximity"
      profile.trigger_radius_m = 35.0
      profile.delay_s = 0.04
      profile.reliability = 1.0
      profile.trigger_logic = trigger_logic
      profile.synthetic = False
      profile.provenance = f"test_{trigger_logic}_fuze_profile"

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
      self.assertGreater(missile_id, 0)

      _drive_missile_with_truth_track(
        sim,
        missile_id,
        red_id,
        max_steps=3600,
      )
      events = sim.export_recent_engagement_events()
      self.assertEqual(len(events.nearest_approach_events), 1)
      self.assertEqual(len(events.fuze_evaluation_events), 1)
      self.assertEqual(len(events.effects_events), 1)
      return (
        events.nearest_approach_events[-1],
        events.fuze_evaluation_events[-1],
        events.effects_events[-1],
      )

    legacy_nearest, legacy_fuze, legacy_effects = run_case("nearest_approach")
    online_nearest, online_fuze, online_effects = run_case("online_sensor")

    self.assertEqual(str(legacy_fuze.header.reason), "fuze_armed")
    self.assertEqual(str(online_fuze.header.reason), "fuze_armed")
    self.assertEqual(str(legacy_effects.detonation_point_source), "sensor_window_delay_solution")
    self.assertEqual(str(online_effects.detonation_point_source), "online_sensor_delay_solution")
    self.assertLessEqual(
      float(online_fuze.header.source_time_s),
      float(legacy_fuze.header.source_time_s),
    )
    self.assertLessEqual(
      float(online_effects.detonation_time_s),
      float(legacy_effects.detonation_time_s),
    )
    self.assertGreater(
      float(online_effects.miss_distance_m),
      float(legacy_effects.miss_distance_m) + 1.0,
    )
    self.assertLess(float(online_effects.miss_distance_m), 35.0)
    self.assertGreater(float(online_fuze.target_detection_confidence), 0.0)
    self.assertGreaterEqual(
      float(online_fuze.target_detection_confidence),
      float(online_fuze.target_detection_threshold),
    )
    online_detonation_local_norm = math.sqrt(
      float(online_effects.detonation_local_forward_m) ** 2
      + float(online_effects.detonation_local_right_m) ** 2
      + float(online_effects.detonation_local_up_m) ** 2
    )
    self.assertAlmostEqual(
      online_detonation_local_norm,
      float(online_effects.miss_distance_m),
      delta=1.0e-3,
    )
    self.assertGreater(
      float(online_nearest.miss_distance_m),
      float(online_effects.miss_distance_m),
    )

  def test_proximity_fuze_reliability_failure_records_no_detonation(self) -> None:
    sim = _make_baseline_kernel(seed=2026061000)
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 35.0
    profile.delay_s = 0.0
    profile.reliability = 0.0
    profile.synthetic = False
    profile.provenance = "test_no_detonation_record"

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
    self.assertGreater(missile_id, 0)

    result = _drive_missile_with_truth_track(
      sim,
      missile_id,
      red_id,
      max_steps=3600,
    )
    self.assertFalse(bool(result["missile_active"]))
    self.assertTrue(sim.is_unit_active(red_id))

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]
    report = events.damage_reports[-1]
    self.assertEqual(str(nearest.header.stage), "nearest_approach")
    self.assertEqual(str(nearest.header.status), "observed")
    self.assertEqual(str(nearest.header.reason), "fuze_no_detonation")
    self.assertEqual(int(nearest.header.munition.entity_id), missile_id)
    self.assertEqual(int(nearest.header.target.entity_id), red_id)
    self.assertLess(float(nearest.miss_distance_m), 35.0)
    self.assertAlmostEqual(
      float(nearest.nearest_approach_time_s),
      float(effects.nearest_approach_time_s),
      delta=sim.get_time_step() + 1.0e-6,
    )
    self.assertEqual(str(fuze.header.stage), "fuze")
    self.assertEqual(str(fuze.header.status), "evaluated")
    self.assertEqual(str(fuze.header.reason), "fuze_no_detonation")
    self.assertEqual(int(fuze.header.chain_id), int(nearest.header.chain_id))
    self.assertEqual(int(fuze.header.parent_event_id), int(nearest.header.event_id))
    self.assertEqual(int(fuze.header.munition.entity_id), missile_id)
    self.assertEqual(int(fuze.header.target.entity_id), red_id)
    self.assertTrue(bool(fuze.armed))
    self.assertFalse(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "fuze_no_detonation")
    self.assertAlmostEqual(float(fuze.reliability), 0.0, delta=1.0e-6)
    self.assertGreaterEqual(float(fuze.sample), 0.0)
    self.assertLessEqual(float(fuze.sample), 1.0)
    self.assertEqual(str(effects.trigger_type), "proximity_fuze")
    self.assertEqual(str(effects.outcome_state), "fuze_no_detonation")
    self.assertLess(float(effects.miss_distance_m), 35.0)
    self.assertAlmostEqual(float(effects.confidence), 0.0, delta=1.0e-6)
    self.assertEqual(int(effects.component_hit_count), 0)
    self.assertEqual(int(effects.component_failure_count), 0)
    self.assertEqual(str(effects.component_primary_name), "")
    self.assertEqual(list(effects.component_mechanism_load_rows), [])
    self.assertAlmostEqual(float(effects.spatial_effect_scale), 0.0, delta=1.0e-9)
    self.assertAlmostEqual(float(effects.mechanism_fragment_energy_j), 0.0, delta=1.0e-9)
    self.assertAlmostEqual(float(effects.mechanism_blast_overpressure_kpa), 0.0, delta=1.0e-9)
    self.assertAlmostEqual(float(effects.mechanism_rod_cut_margin), 0.0, delta=1.0e-9)
    self.assertEqual(int(effects.warhead_spatial_sample_count), 0)
    self.assertEqual(int(report.source_event_id), int(effects.event_id))
    self.assertAlmostEqual(float(report.system_health_delta), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertIn("mission=0.000000", str(report.platform_damage_state_delta))
    self.assertIn("mobility=0.000000", str(report.platform_damage_state_delta))
    self.assertFalse(bool(report.destroyed))
    damage_trace = next(
      (
        trace
        for trace in events.diagnostics_traces
        if int(trace.effects_event_id) == int(effects.event_id)
      ),
      None,
    )
    self.assertIsNotNone(damage_trace)
    assert damage_trace is not None
    self.assertEqual(int(damage_trace.damage_report_id), int(report.report_id))

  def test_proximity_fuze_detonation_is_not_gated_by_warhead_coverage(self) -> None:
    sim = _make_kernel(seed=20260708)
    sim.set_time_step(1.0 / 60.0)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 15.0
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.trigger_logic = "nearest_approach"
    profile.synthetic = False
    profile.provenance = "test_fuze_detonation_separated_from_coverage"

    tuning = sim.get_missile_tuning()
    tuning.sensor_scan_period = 1.0e9
    tuning.sensor_detection_prob = 0.0
    tuning.sensor_track_memory_s = 0.0
    tuning.seeker_fov_deg = 180.0
    tuning.seeker_lock_range = 1.0e6
    tuning.max_speed = 1100.0
    tuning.turn_rate = 45.0
    tuning.max_lateral_g = 35.0
    tuning.autopilot_tau_s = 0.08
    tuning.max_accel_response_g_per_s = 120.0
    tuning.nav_gain = 3.0
    tuning.apn_target_accel_gain = 0.5
    tuning.fuse_distance = 15.0
    tuning.max_flight_time_s = 40.0
    tuning.boost_time_s = 3.0
    tuning.sustain_time_s = 0.0
    tuning.fuze_profile = profile
    tuning.has_fuze_profile = True
    sim.set_missile_tuning(tuning)

    bearing_rad = math.radians(20.0)
    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=20000.0 * math.sin(bearing_rad),
      red_y=20000.0 * math.cos(bearing_rad),
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-250.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    result = _drive_missile_with_truth_track(
      sim,
      missile_id,
      red_id,
      max_steps=3600,
    )
    self.assertFalse(bool(result["missile_active"]))
    self.assertLess(float(result["proximity_min_dist_m"]), 5.0)

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertGreaterEqual(len(events.effects_events), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]

    self.assertEqual(str(nearest.header.reason), "fuze_armed")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertAlmostEqual(float(fuze.expected_detonation_probability), 1.0, delta=1.0e-9)
    self.assertTrue(bool(fuze.terminal_track_valid))
    self.assertTrue(bool(fuze.target_detected))
    self.assertGreaterEqual(
      float(fuze.target_detection_confidence),
      float(fuze.target_detection_threshold),
    )
    self.assertGreater(float(fuze.mechanism_coverage_score), 0.0)
    self.assertEqual(str(effects.trigger_type), "proximity_fuze")
    self.assertIn(str(effects.outcome_state), {"damage_applied", "detonated_no_effect"})
    self.assertNotEqual(str(effects.outcome_state), "fuze_no_detonation")
    self.assertAlmostEqual(float(effects.confidence), 1.0, delta=1.0e-9)

  def test_proximity_fuze_sensor_window_arms_with_terminal_track(self) -> None:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 20.0
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.synthetic = False
    profile.provenance = "test_target_not_detected_record"

    tuning = sim.get_missile_tuning()
    tuning.fuze_profile = profile
    tuning.has_fuze_profile = True
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=0.0,
      red_y=26000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-250.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    result = _drive_missile_with_truth_track(
      sim,
      missile_id,
      red_id,
      max_steps=3600,
    )
    self.assertFalse(bool(result["missile_active"]))
    self.assertLess(float(result["proximity_min_dist_m"]), 20.0)

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertEqual(len(events.effects_events), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]

    self.assertEqual(str(nearest.header.reason), "fuze_armed")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertEqual(str(fuze.sensor_opportunity_source), "proximity_sensor_window")
    self.assertGreater(float(fuze.sensor_opportunity_score), 0.0)
    self.assertTrue(bool(fuze.terminal_track_valid))
    self.assertTrue(bool(fuze.target_detected))
    self.assertEqual(str(fuze.target_detection_source), "target_rcs_aspect")
    self.assertGreaterEqual(
      float(fuze.target_detection_confidence),
      float(fuze.target_detection_threshold),
    )
    self.assertEqual(str(fuze.detonation_point_source), "online_sensor_current_point")
    self.assertGreater(float(fuze.mechanism_coverage_score), 0.0)

    self.assertIn(str(effects.outcome_state), {"damage_applied", "detonated_no_effect"})
    self.assertAlmostEqual(float(effects.confidence), 1.0, delta=1.0e-9)
    self.assertEqual(str(effects.fuze_sensor_opportunity_source), "proximity_sensor_window")
    self.assertGreater(float(effects.fuze_sensor_opportunity_score), 0.0)
    self.assertTrue(bool(effects.fuze_terminal_track_valid))
    self.assertTrue(bool(effects.fuze_target_detected))
    self.assertEqual(str(effects.fuze_target_detection_source), "target_rcs_aspect")
    self.assertGreaterEqual(
      float(effects.fuze_target_detection_confidence),
      float(effects.fuze_target_detection_threshold),
    )
    self.assertEqual(str(effects.detonation_point_source), "online_sensor_current_point")
    self.assertGreater(float(effects.fuze_mechanism_coverage_score), 0.0)

  def test_proximity_fuze_edge_of_radius_still_detects_tracked_target(self) -> None:
    sim = _make_kernel(seed=20260622)
    sim.set_time_step(1.0 / 60.0)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 15.0
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.trigger_logic = "nearest_approach"
    profile.synthetic = False
    profile.provenance = "test_edge_of_radius_target_detection"

    tuning = ef_py.MissileTuning()
    tuning.sensor_scan_period = 1.0e9
    tuning.sensor_detection_prob = 0.0
    tuning.sensor_track_memory_s = 0.0
    tuning.seeker_fov_deg = 180.0
    tuning.seeker_lock_range = 1.0e6
    tuning.fuse_distance = 15.0
    tuning.max_flight_time_s = 45.0
    tuning.fuze_profile = profile
    tuning.has_fuze_profile = True
    sim.set_missile_tuning(tuning)

    range_m = 12000.0
    bearing_rad = math.radians(15.0)
    initial_x = range_m * math.sin(bearing_rad)
    initial_y = range_m * math.cos(bearing_rad)
    target_vx = 0.0
    target_vy = -250.0
    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=initial_x,
      red_y=initial_y,
      red_heading=180.0,
      red_vx=target_vx,
      red_vy=target_vy,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    dt = float(sim.get_time_step())
    for step_idx in range(4200):
      time_s = step_idx * dt
      _set_unit_truth_state(
        sim,
        red_id,
        x=initial_x + target_vx * time_s,
        y=initial_y + target_vy * time_s,
        z=5000.0,
        heading=180.0,
        vx=target_vx,
        vy=target_vy,
      )
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=time_s,
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertGreaterEqual(len(events.effects_events), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]

    self.assertLess(float(nearest.miss_distance_m), 15.0)
    self.assertGreater(float(nearest.miss_distance_m), 10.0)
    self.assertEqual(str(nearest.header.reason), "fuze_armed")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertTrue(bool(fuze.target_detected))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertGreaterEqual(
      float(fuze.target_detection_confidence),
      float(fuze.target_detection_threshold),
    )
    self.assertEqual(str(effects.trigger_type), "proximity_fuze")
    self.assertNotEqual(str(effects.outcome_state), "target_not_detected")

  def test_proximity_fuze_soft_tail_can_trigger_beyond_reliable_radius(self) -> None:
    sim = _make_database_kernel(seed=20260622)
    sim.set_time_step(1.0 / 60.0)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 15.0
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.trigger_logic = "nearest_approach"
    profile.synthetic = False
    profile.provenance = "test_soft_tail_proximity_trigger"

    tuning = sim.get_missile_tuning()
    tuning.sensor_scan_period = 1.0e9
    tuning.sensor_detection_prob = 0.0
    tuning.sensor_track_memory_s = 0.0
    tuning.seeker_fov_deg = 180.0
    tuning.seeker_lock_range = 1.0e6
    tuning.fuse_distance = 15.0
    tuning.max_flight_time_s = 45.0
    tuning.fuze_profile = profile
    tuning.has_fuze_profile = True
    sim.set_missile_tuning(tuning)

    range_m = 18000.0
    bearing_rad = math.radians(27.5)
    initial_x = range_m * math.sin(bearing_rad)
    initial_y = range_m * math.cos(bearing_rad)
    target_vx = 0.0
    target_vy = -250.0
    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=initial_x,
      red_y=initial_y,
      red_heading=180.0,
      red_vx=target_vx,
      red_vy=target_vy,
    )
    _select_weapon_station(sim, blue_id, 1)
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    dt = float(sim.get_time_step())
    for step_idx in range(4200):
      time_s = step_idx * dt
      _set_unit_truth_state(
        sim,
        red_id,
        x=initial_x + target_vx * time_s,
        y=initial_y + target_vy * time_s,
        z=5000.0,
        heading=180.0,
        vx=target_vx,
        vy=target_vy,
      )
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=time_s,
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.nearest_approach_events), 1)
    self.assertEqual(len(events.fuze_evaluation_events), 1)
    self.assertGreaterEqual(len(events.effects_events), 1)
    nearest = events.nearest_approach_events[-1]
    fuze = events.fuze_evaluation_events[-1]
    effects = events.effects_events[-1]

    self.assertGreater(float(nearest.miss_distance_m), 15.0)
    self.assertLess(float(nearest.miss_distance_m), 20.0)
    self.assertEqual(str(nearest.header.reason), "fuze_armed")
    self.assertEqual(str(fuze.header.reason), "fuze_armed")
    self.assertTrue(bool(fuze.armed))
    self.assertTrue(bool(fuze.triggered))
    self.assertEqual(str(fuze.failure_reason), "")
    self.assertGreater(float(fuze.expected_detonation_probability), 0.0)
    self.assertLess(float(fuze.expected_detonation_probability), 1.0)
    self.assertGreater(float(fuze.sensor_opportunity_score), 0.0)
    self.assertLess(float(fuze.sensor_opportunity_score), 1.0)
    self.assertTrue(bool(fuze.target_detected))
    self.assertLess(float(fuze.sample), float(fuze.expected_detonation_probability))
    self.assertEqual(str(effects.trigger_type), "proximity_fuze")
    self.assertIn(str(effects.outcome_state), {"damage_applied", "detonated_no_effect"})
    self.assertGreater(float(effects.confidence), 0.0)
    self.assertLess(float(effects.confidence), 1.0)
    self.assertGreater(float(effects.quality), 0.0)
    self.assertLess(float(effects.quality), 0.30)

  def test_fuze_event_records_detonation_attitude_evidence(self) -> None:
    sim = _make_baseline_kernel(seed=2026061000)
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "radar_proximity"
    profile.trigger_radius_m = 35.0
    profile.delay_s = 0.08
    profile.reliability = 1.0
    profile.synthetic = False
    profile.provenance = "test_detonation_attitude_evidence"

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
    self.assertGreater(missile_id, 0)

    armed_attitude: tuple[float, float, float] | None = None
    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()
      if sim.is_unit_active(missile_id):
        runtime = _missile_runtime(sim, missile_id)
        if bool(runtime["fuze_delay_armed"]):
          armed_attitude = (
            float(runtime["fuze_detonation_heading_deg"]),
            float(runtime["fuze_detonation_pitch_deg"]),
            float(runtime["fuze_detonation_roll_deg"]),
          )
          self.assertTrue(all(math.isfinite(value) for value in armed_attitude))
          break

    self.assertIsNotNone(armed_attitude)
    while sim.is_unit_active(missile_id):
      sim.step()

    events = sim.export_recent_engagement_events()
    self.assertGreaterEqual(len(events.effects_events), 1)
    effects = events.effects_events[-1]
    assert armed_attitude is not None
    self.assertAlmostEqual(float(effects.detonation_heading_deg), armed_attitude[0], delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_pitch_deg), armed_attitude[1], delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_roll_deg), armed_attitude[2], delta=1.0e-6)
    self.assertEqual(str(effects.fuze_type), "radar_proximity")

  def test_contact_fuze_does_not_trigger_from_near_miss_radius(self) -> None:
    def run_with_fuze(fuze_type: str) -> tuple[dict[str, float | bool], object, int, int]:
      sim = _make_baseline_kernel()
      sim.set_time_step(0.02)

      profile = ef_py.FuzeProfile()
      profile.type = fuze_type
      profile.trigger_radius_m = 35.0
      profile.delay_s = 0.0
      profile.reliability = 1.0
      if fuze_type == "radar_proximity":
        profile.trigger_logic = "nearest_approach"
      profile.synthetic = False
      profile.provenance = "test_fuze_type_trigger_semantics"

      tuning = sim.get_missile_tuning()
      tuning.fuze_profile = profile
      tuning.has_fuze_profile = True
      sim.set_missile_tuning(tuning)

      blue_id, red_id = _spawn_geometry_pair(
        sim,
        red_x=0.0,
        red_y=26000.0,
        red_heading=180.0,
        red_vx=0.0,
        red_vy=-250.0,
      )
      missile_id = int(sim.fire_missile(blue_id, red_id))
      self.assertGreater(missile_id, 0)

      result = _drive_missile_with_truth_track(
        sim,
        missile_id,
        red_id,
        max_steps=3600,
      )
      return result, sim.export_recent_engagement_events(), missile_id, red_id

    proximity_result, proximity_events, _proximity_missile_id, _proximity_red_id = (
      run_with_fuze("radar_proximity")
    )
    self.assertFalse(bool(proximity_result["missile_active"]))
    self.assertLess(float(proximity_result["truth_min_dist_m"]), 35.0)
    self.assertGreaterEqual(len(proximity_events.effects_events), 1)
    proximity_effect = proximity_events.effects_events[-1]
    self.assertEqual(str(proximity_effect.trigger_type), "proximity_fuze")
    self.assertEqual(str(proximity_effect.fuze_type), "radar_proximity")
    self.assertFalse(bool(proximity_effect.direct_hitbox_intersection))
    self.assertEqual(str(proximity_effect.outcome_state), "fuze_no_terminal_track")
    self.assertAlmostEqual(float(proximity_effect.confidence), 0.0, delta=1.0e-9)
    self.assertFalse(bool(proximity_effect.fuze_terminal_track_valid))
    self.assertFalse(bool(proximity_effect.fuze_target_detected))
    self.assertEqual(int(proximity_effect.component_hit_count), 0)
    self.assertEqual(int(proximity_effect.component_failure_count), 0)

    contact_result, contact_events, contact_missile_id, contact_red_id = run_with_fuze("contact")
    self.assertFalse(bool(contact_result["missile_active"]))
    self.assertLess(float(contact_result["truth_min_dist_m"]), 35.0)
    self.assertEqual(len(contact_events.nearest_approach_events), 1)
    self.assertEqual(len(contact_events.fuze_evaluation_events), 1)
    self.assertEqual(len(contact_events.effects_events), 0)
    self.assertEqual(len(contact_events.damage_reports), 0)
    contact_nearest = contact_events.nearest_approach_events[-1]
    contact_fuze = contact_events.fuze_evaluation_events[-1]
    self.assertEqual(str(contact_nearest.header.reason), "miss_outside_trigger_radius")
    self.assertEqual(str(contact_fuze.header.stage), "fuze")
    self.assertEqual(str(contact_fuze.header.status), "evaluated")
    self.assertEqual(str(contact_fuze.header.reason), "miss_outside_trigger_radius")
    self.assertEqual(int(contact_fuze.header.chain_id), int(contact_nearest.header.chain_id))
    self.assertEqual(int(contact_fuze.header.parent_event_id), int(contact_nearest.header.event_id))
    self.assertEqual(int(contact_fuze.header.munition.entity_id), contact_missile_id)
    self.assertEqual(int(contact_fuze.header.target.entity_id), contact_red_id)
    self.assertFalse(bool(contact_fuze.armed))
    self.assertFalse(bool(contact_fuze.triggered))
    self.assertEqual(str(contact_fuze.failure_reason), "miss_outside_trigger_radius")
    self.assertEqual(str(contact_fuze.fuze_type), "contact")

  def test_contact_fuze_records_surface_and_penetration_evidence(self) -> None:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "impact"
    profile.trigger_radius_m = 0.25
    profile.delay_s = 0.0
    profile.reliability = 1.0
    profile.synthetic = False
    profile.provenance = "test_contact_penetration_evidence"

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
    self.assertGreater(missile_id, 0)

    armed_seen = False
    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()
      if sim.is_unit_active(missile_id):
        runtime = _missile_runtime(sim, missile_id)
        if bool(runtime["fuze_delay_armed"]):
          armed_seen = True
          self.assertEqual(str(runtime["fuze_signature_source"]), "contact_surface")
          self.assertAlmostEqual(
            float(runtime["fuze_contact_surface_tolerance_m"]),
            0.25,
            delta=1.0e-6,
          )
          self.assertLessEqual(
            float(runtime["fuze_contact_surface_distance_m"]),
            float(runtime["fuze_contact_surface_tolerance_m"]) + 1.0e-6,
          )
          self.assertTrue(bool(runtime["fuze_contact_inside_hitbox"]))
          self.assertGreater(float(runtime["fuze_contact_penetration_depth_m"]), 0.0)

    self.assertTrue(armed_seen)
    events = sim.export_recent_engagement_events()
    self.assertGreaterEqual(len(events.effects_events), 1)
    effects = events.effects_events[-1]
    self.assertEqual(str(effects.trigger_type), "contact_fuze")
    self.assertEqual(str(effects.fuze_type), "impact")
    self.assertEqual(str(effects.fuze_signature_source), "contact_surface")
    self.assertAlmostEqual(float(effects.fuze_contact_surface_tolerance_m), 0.25, delta=1.0e-6)
    self.assertLessEqual(
      float(effects.fuze_contact_surface_distance_m),
      float(effects.fuze_contact_surface_tolerance_m) + 1.0e-6,
    )
    self.assertTrue(bool(effects.fuze_contact_inside_hitbox))
    self.assertGreater(float(effects.fuze_contact_penetration_depth_m), 0.0)
    self.assertAlmostEqual(float(effects.fuze_target_signature), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.fuze_signature_scale), 1.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.fuze_effective_reliability), 1.0, delta=1.0e-6)

  def test_timed_fuze_detonates_on_delay_without_proximity_gate(self) -> None:
    sim = _make_baseline_kernel()
    sim.set_time_step(0.02)

    profile = ef_py.FuzeProfile()
    profile.type = "timed"
    profile.trigger_radius_m = 35.0
    profile.delay_s = 0.10
    profile.reliability = 1.0
    profile.synthetic = False
    profile.provenance = "test_timed_fuze_independent_trigger"

    tuning = sim.get_missile_tuning()
    tuning.fuze_profile = profile
    tuning.has_fuze_profile = True
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=0.0,
      red_y=26000.0,
      red_heading=180.0,
      red_vx=0.0,
      red_vy=-250.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    launch_time = 0.0
    for step_idx in range(60):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim,
            missile_id,
            red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()

    self.assertFalse(sim.is_unit_active(missile_id))
    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)

    effects = events.effects_events[-1]
    report = events.damage_reports[-1]
    self.assertEqual(str(effects.trigger_type), "timed_fuze")
    self.assertEqual(str(effects.fuze_type), "timed")
    self.assertEqual(str(effects.outcome_state), "detonated_no_effect")
    self.assertGreater(float(effects.miss_distance_m), 1000.0)
    self.assertFalse(bool(effects.direct_hitbox_intersection))
    self.assertEqual(int(effects.projected_hitbox_count), 0)
    self.assertAlmostEqual(float(effects.fuze_delay_s), 0.10, delta=1.0e-6)
    self.assertAlmostEqual(
      float(effects.detonation_time_s) - launch_time,
      0.10,
      delta=(2.0 * sim.get_time_step()) + 1.0e-6,
    )
    self.assertAlmostEqual(float(report.system_health_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))
