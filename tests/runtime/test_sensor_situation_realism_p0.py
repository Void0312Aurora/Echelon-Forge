from __future__ import annotations

import math
import unittest

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path


configure_sim_log_level("error")
ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _make_detection(target_id: int, *, range_m: float, bearing_deg: float, elevation_deg: float = 0.0, closing_mps: float = 200.0) -> ef_py.Detection:
    det = ef_py.Detection()
    det.target_id = int(target_id)
    det.range = float(range_m)
    det.bearing = float(bearing_deg)
    det.elevation = float(elevation_deg)
    det.closing_speed = float(closing_mps)
    det.signal_strength = 1.0
    det.timestamp = 0.0
    return det


class SensorSituationRealismP0Tests(unittest.TestCase):
    def test_sensor_runtime_defaults_expose_p0_fields(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(314)
        self.assertTrue(sim.load_database(_DB_PATH))

        own = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        sensor = sim.get_sensor_debug_view(int(own))

        self.assertAlmostEqual(float(sensor.reference_snr_db), 13.0, places=6)
        self.assertAlmostEqual(float(sensor.reference_rcs_m2), 5.0, places=6)
        self.assertAlmostEqual(float(sensor.pfa), 1.0e-6, places=12)
        self.assertEqual(int(sensor.confirm_hits_m), 2)
        self.assertEqual(int(sensor.confirm_window_n), 3)
        self.assertAlmostEqual(float(sensor.alpha_beta_alpha), 0.65, places=6)
        self.assertAlmostEqual(float(sensor.alpha_beta_beta), 0.12, places=6)

    def test_two_of_three_confirm_promotes_track(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(42)
        self.assertTrue(sim.load_database(_DB_PATH))

        own = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 20000.0, 3000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        sim.set_contact_list(int(own), [_make_detection(int(foe), range_m=20000.0, bearing_deg=0.0)])
        sim.step()
        obs1 = sim.get_agent_observation(int(own))
        self.assertGreaterEqual(len(obs1.contacts), 1)
        self.assertEqual(int(obs1.contacts[0].status), 0)
        self.assertEqual(int(obs1.contacts[0].usability), 0)
        self.assertFalse(bool(obs1.contacts[0].iff_known))
        self.assertAlmostEqual(float(obs1.contacts[0].classification_confidence), 0.0, places=6)
        self.assertGreater(float(obs1.contacts[0].quality), 0.0)
        self.assertGreater(float(obs1.contacts[0].confidence), 0.0)
        tentative = sim.get_tentative_track_debug_view(int(own))
        self.assertEqual(len(tentative), 1)
        self.assertEqual(int(tentative[0].status), 0)

        sim.set_contact_list(int(own), [_make_detection(int(foe), range_m=19800.0, bearing_deg=0.0)])
        sim.step()
        obs2 = sim.get_agent_observation(int(own))
        self.assertGreaterEqual(len(obs2.contacts), 1)
        self.assertEqual(int(obs2.contacts[0].status), 1)
        self.assertEqual(int(obs2.contacts[0].usability), 2)
        self.assertFalse(bool(obs2.contacts[0].iff_known))
        self.assertGreater(float(obs2.contacts[0].classification_confidence), 0.0)
        self.assertGreater(float(obs2.contacts[0].quality), 0.0)
        self.assertGreater(float(obs2.contacts[0].confidence), 0.0)
        tracks = sim.get_track_debug_view(int(own))
        self.assertGreaterEqual(len(tracks), 1)
        self.assertEqual(int(tracks[0].status), 1)
        self.assertEqual(int(tracks[0].usability), 2)
        self.assertGreater(float(tracks[0].quality), 0.0)
        self.assertGreater(float(tracks[0].confidence), 0.0)

    def test_alpha_beta_filter_estimates_nonzero_closing_speed_for_constant_target(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(123)
        self.assertTrue(sim.load_database(_DB_PATH))

        own = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 3000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 24000.0, 3000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        for idx, rng in enumerate((24000.0, 23000.0, 22000.0, 21000.0)):
            det = _make_detection(int(foe), range_m=rng, bearing_deg=0.0, closing_mps=500.0)
            det.timestamp = float(idx)
            sim.set_contact_list(int(own), [det])
            sim.step()

        initial_obs = sim.get_agent_observation(int(own))
        initial_age = float(initial_obs.contacts[0].time_since_update)

        # After confirmation, a coasted/predicted track should still be available even without a fresh contact.
        sim.set_contact_list(int(own), [])
        sim.step()
        obs = sim.get_agent_observation(int(own))
        self.assertGreaterEqual(len(obs.contacts), 1)
        self.assertGreater(float(obs.contacts[0].time_since_update), initial_age)
        self.assertLess(float(obs.contacts[0].time_since_update), 1.0)
        self.assertGreater(float(obs.contacts[0].closing_speed), 0.0)

    def test_datalink_track_report_does_not_create_local_contact(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(99)
        self.assertTrue(sim.load_database(_DB_PATH))

        sender = sim.spawn_unit(ef_py.Side.Blue, "E-3_Sentry_AWACS", 0.0, 0.0, 9000.0, 0.0, 0.0, 0.0, 0.0, 200.0, 0.0)
        receiver = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, -30000.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 130000.0, 4000.0, 180.0, 0.0, 0.0, 0.0, -200.0, 0.0)

        # Build a confirmed track on the sender by injecting two hits.
        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=130000.0, bearing_deg=0.0)])
        sim.step()
        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=129000.0, bearing_deg=0.0)])
        sim.step()

        # First step publishes the report into the receiver inbox.
        sim.step()

        msgs = list(sim.get_unit_messages(int(receiver)))
        report_types = {
            int(ef_py.CommMsgType.ReportContact),
            int(ef_py.CommMsgType.ReportTrack),
        }
        self.assertTrue(any(int(getattr(msg, "type", 0)) in report_types for msg in msgs))

        self.assertEqual(sim.debug_get_contact_count(int(receiver)), 0)

    def test_datalink_report_becomes_visible_track_without_fabricating_local_contact(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(100)
        self.assertTrue(sim.load_database(_DB_PATH))

        sender = sim.spawn_unit(ef_py.Side.Blue, "E-3_Sentry_AWACS", 0.0, 0.0, 9000.0, 0.0, 0.0, 0.0, 0.0, 200.0, 0.0)
        receiver = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, -30000.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 130000.0, 4000.0, 180.0, 0.0, 0.0, 0.0, -200.0, 0.0)

        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=130000.0, bearing_deg=0.0)])
        sim.step()
        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=129000.0, bearing_deg=0.0)])
        sim.step()

        visible_track = None
        debug_track = None
        for _ in range(4):
            sim.step()
            self.assertEqual(sim.debug_get_contact_count(int(receiver)), 0)

            obs = sim.get_agent_observation(int(receiver))
            matching = [c for c in obs.contacts if int(c.id) == int(foe) and int(c.source) == 3]
            if matching:
                visible_track = matching[0]
                break

        self.assertIsNotNone(visible_track)
        self.assertEqual(int(visible_track.status), 1)
        self.assertEqual(int(visible_track.usability), 2)
        self.assertGreater(float(visible_track.quality), 0.0)
        self.assertGreater(float(visible_track.confidence), 0.0)
        self.assertTrue(bool(visible_track.iff_known))
        self.assertGreaterEqual(float(visible_track.classification_confidence), 0.9)

        tracks = sim.get_track_debug_view(int(receiver))
        debug_matching = [t for t in tracks if int(t.id) == int(foe) and int(t.source) == 3]
        self.assertGreaterEqual(len(debug_matching), 1)
        debug_track = debug_matching[0]
        self.assertEqual(int(debug_track.status), 1)
        self.assertEqual(int(debug_track.usability), 2)
        self.assertTrue(bool(debug_track.iff_known))
        self.assertGreaterEqual(float(visible_track.quality), 0.5)
        self.assertAlmostEqual(float(visible_track.quality), float(debug_track.quality), delta=1e-6)
        self.assertAlmostEqual(float(visible_track.confidence), float(debug_track.confidence), delta=1e-6)
        self.assertAlmostEqual(float(visible_track.classification_confidence), float(debug_track.classification_confidence), delta=1e-6)

    def test_local_and_datalink_updates_merge_into_fused_track_semantics(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(101)
        self.assertTrue(sim.load_database(_DB_PATH))

        sender = sim.spawn_unit(ef_py.Side.Blue, "E-3_Sentry_AWACS", 0.0, 0.0, 9000.0, 0.0, 0.0, 0.0, 0.0, 200.0, 0.0)
        receiver = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, -30000.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 70000.0, 5000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=70000.0, bearing_deg=0.0)])
        sim.step()
        sim.set_contact_list(int(sender), [_make_detection(int(foe), range_m=69000.0, bearing_deg=0.0)])
        sim.step()

        visible_track = None
        debug_track = None
        for _ in range(8):
            sim.set_contact_list(int(receiver), [_make_detection(int(foe), range_m=100000.0, bearing_deg=0.0, closing_mps=500.0)])
            sim.step()

            obs = sim.get_agent_observation(int(receiver))
            matching = [c for c in obs.contacts if int(c.id) == int(foe)]
            if matching and int(matching[0].source) == 4:
                visible_track = matching[0]
                break

        self.assertIsNotNone(visible_track)
        self.assertEqual(int(visible_track.source), 4)
        self.assertEqual(int(visible_track.status), 1)
        self.assertEqual(int(visible_track.usability), 2)
        self.assertTrue(bool(visible_track.iff_known))
        self.assertGreaterEqual(float(visible_track.classification_confidence), 0.9)

        tracks = sim.get_track_debug_view(int(receiver))
        debug_matching = [t for t in tracks if int(t.id) == int(foe)]
        self.assertGreaterEqual(len(debug_matching), 1)
        debug_track = debug_matching[0]
        self.assertEqual(int(debug_track.source), 4)
        self.assertEqual(int(debug_track.status), 1)
        self.assertEqual(int(debug_track.usability), 2)
        self.assertTrue(bool(debug_track.iff_known))

    def test_confirmed_and_coasted_tracks_expose_different_usability_semantics(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(222)
        self.assertTrue(sim.load_database(_DB_PATH))

        own = sim.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 4000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe = sim.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 250000.0, 4000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        sim.set_contact_list(int(own), [_make_detection(int(foe), range_m=25000.0, bearing_deg=0.0)])
        sim.step()
        sim.set_contact_list(int(own), [_make_detection(int(foe), range_m=24800.0, bearing_deg=0.0)])
        sim.step()

        confirmed_obs = sim.get_agent_observation(int(own))
        self.assertGreaterEqual(len(confirmed_obs.contacts), 1)
        confirmed_track = confirmed_obs.contacts[0]
        self.assertEqual(int(confirmed_track.status), 1)
        self.assertEqual(int(confirmed_track.usability), 2)

        sim.set_contact_list(int(own), [])
        coasted_track = None
        for _ in range(360):
            sim.step()
            obs = sim.get_agent_observation(int(own))
            matching = [c for c in obs.contacts if int(c.id) == int(foe)]
            if matching and int(matching[0].status) == 2:
                coasted_track = matching[0]
                break

        self.assertIsNotNone(coasted_track)
        self.assertEqual(int(coasted_track.status), 2)
        self.assertEqual(int(coasted_track.usability), 1)
        self.assertGreater(float(coasted_track.quality), 0.0)
        self.assertGreater(float(coasted_track.confidence), 0.0)

        for _ in range(360):
            sim.step()

        aged_obs = sim.get_agent_observation(int(own))
        matching = [c for c in aged_obs.contacts if int(c.id) == int(foe)]
        self.assertEqual(len(matching), 0)

    def test_radar_pd_trend_stronger_for_close_target_than_far_target(self) -> None:
        sim_near = ef_py.SimulationKernel()
        sim_near.reset(7)
        self.assertTrue(sim_near.load_database(_DB_PATH))
        own_near = sim_near.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe_near = sim_near.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 20000.0, 5000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        sim_far = ef_py.SimulationKernel()
        sim_far.reset(7)
        self.assertTrue(sim_far.load_database(_DB_PATH))
        own_far = sim_far.spawn_unit(ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0, 0.0, 250.0, 0.0)
        foe_far = sim_far.spawn_unit(ef_py.Side.Red, "F-16C_Block50", 0.0, 60000.0, 5000.0, 180.0, 0.0, 0.0, 0.0, -250.0, 0.0)

        near_hits = 0
        far_hits = 0
        samples = 20
        for _ in range(samples):
            sim_near.step()
            sim_far.step()
            near_hits += 1 if sim_near.debug_get_contact_count(int(own_near)) > 0 else 0
            far_hits += 1 if sim_far.debug_get_contact_count(int(own_far)) > 0 else 0

        self.assertGreaterEqual(near_hits, far_hits)

    def test_detection_binding_exposes_extended_fields(self) -> None:
        det = _make_detection(99, range_m=12345.0, bearing_deg=12.0)
        det.snr_db = 7.5
        det.detection_prob_used = 0.82
        det.measured_vr = 145.0
        det.sensor_type = int(ef_py.SensorType.Radar)
        det.local_sensor_hit = True

        self.assertAlmostEqual(float(det.snr_db), 7.5, places=6)
        self.assertAlmostEqual(float(det.detection_prob_used), 0.82, places=6)
        self.assertAlmostEqual(float(det.measured_vr), 145.0, places=6)
        self.assertEqual(int(det.sensor_type), int(ef_py.SensorType.Radar))
        self.assertTrue(bool(det.local_sensor_hit))


if __name__ == "__main__":
    unittest.main()
