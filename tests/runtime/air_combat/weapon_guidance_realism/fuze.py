from __future__ import annotations

from .helpers import *


class FuzeRuntimeMixin:
    def test_global_fuze_profile_override_flows_into_runtime_and_effects_event(self) -> None:
        sim = _make_baseline_kernel()

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

        self.assertTrue(armed_seen)
        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        self.assertEqual(str(effects.fuze_type), "radar_proximity")
        self.assertAlmostEqual(float(effects.fuze_delay_s), 0.08, delta=1.0e-6)
        self.assertEqual(str(effects.fuze_signature_source), "target_rcs_aspect")
        self.assertGreater(float(effects.fuze_target_signature), 0.0)
        self.assertGreater(float(effects.fuze_signature_scale), 0.0)
        self.assertLessEqual(float(effects.fuze_effective_reliability), 1.0)
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

    def test_proximity_fuze_reliability_failure_records_no_detonation(self) -> None:
        sim = _make_baseline_kernel()
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
        self.assertGreaterEqual(len(events.effects_events), 1)
        self.assertGreaterEqual(len(events.damage_reports), 1)
        effects = events.effects_events[-1]
        report = events.damage_reports[-1]
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

    def test_fuze_event_records_detonation_attitude_evidence(self) -> None:
        sim = _make_baseline_kernel()
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
        def run_with_fuze(fuze_type: str) -> tuple[dict[str, float | bool], object]:
            sim = _make_baseline_kernel()
            sim.set_time_step(0.02)

            profile = ef_py.FuzeProfile()
            profile.type = fuze_type
            profile.trigger_radius_m = 35.0
            profile.delay_s = 0.0
            profile.reliability = 1.0
            profile.synthetic = False
            profile.provenance = "test_fuze_type_trigger_semantics"

            tuning = sim.get_missile_tuning()
            tuning.fuze_profile = profile
            tuning.has_fuze_profile = True
            sim.set_missile_tuning(tuning)

            blue_id, red_id = _spawn_geometry_pair(
                sim,
                red_x=0.0,
                red_y=22000.0,
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
            return result, sim.export_recent_engagement_events()

        proximity_result, proximity_events = run_with_fuze("radar_proximity")
        self.assertFalse(bool(proximity_result["missile_active"]))
        self.assertLess(float(proximity_result["truth_min_dist_m"]), 35.0)
        self.assertGreaterEqual(len(proximity_events.effects_events), 1)
        proximity_effect = proximity_events.effects_events[-1]
        self.assertEqual(str(proximity_effect.trigger_type), "proximity_fuze")
        self.assertEqual(str(proximity_effect.fuze_type), "radar_proximity")
        self.assertFalse(bool(proximity_effect.direct_hitbox_intersection))
        self.assertGreater(int(proximity_effect.projected_hitbox_count), 0)

        contact_result, contact_events = run_with_fuze("contact")
        self.assertFalse(bool(contact_result["missile_active"]))
        self.assertLess(float(contact_result["truth_min_dist_m"]), 35.0)
        self.assertEqual(len(contact_events.effects_events), 0)
        self.assertEqual(len(contact_events.damage_reports), 0)

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
