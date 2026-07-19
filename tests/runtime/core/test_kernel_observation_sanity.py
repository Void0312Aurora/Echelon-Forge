from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


class KernelObservationSanityTests(unittest.TestCase):
  def test_spawned_unit_exposes_health_and_fire_fields(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)
    self.assertTrue(kernel.load_database("examples/config/database"))

    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1000.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=100.0,
      vy=0.0,
      vz=0.0,
    )

    health = kernel.get_unit_health(entity_id)
    self.assertIsInstance(health, list)
    self.assertEqual(len(health), 2)

    obs = kernel.get_agent_observation(entity_id)
    self.assertTrue(hasattr(obs, "health"))
    self.assertTrue(hasattr(obs, "can_fire"))
    sensor = kernel.get_sensor_debug_view(entity_id)
    self.assertTrue(hasattr(sensor, "reference_snr_db"))
    self.assertTrue(hasattr(sensor, "confirm_hits_m"))
    self.assertTrue(hasattr(sensor, "alpha_beta_alpha"))
    tracks = kernel.get_track_debug_view(entity_id)
    self.assertIsInstance(tracks, list)
    tentative = kernel.get_tentative_track_debug_view(entity_id)
    self.assertIsInstance(tentative, list)

  def test_trackdata_contract_exposes_status_quality_and_confidence(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(77)
    self.assertTrue(kernel.load_database("examples/config/database"))

    own = kernel.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      3000.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=250.0,
      vz=0.0,
    )
    foe = kernel.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      0.0,
      20000.0,
      3000.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-250.0,
      vz=0.0,
    )

    det1 = ef_py.Detection()
    det1.target_id = int(foe)
    det1.range = 20000.0
    det1.bearing = 0.0
    det1.elevation = 0.0
    det1.closing_speed = 500.0
    det1.signal_strength = 1.0
    det1.timestamp = 0.0
    kernel.set_contact_list(int(own), [det1])
    kernel.step()

    det2 = ef_py.Detection()
    det2.target_id = int(foe)
    det2.range = 19800.0
    det2.bearing = 0.0
    det2.elevation = 0.0
    det2.closing_speed = 500.0
    det2.signal_strength = 1.0
    det2.timestamp = 0.0
    kernel.set_contact_list(int(own), [det2])
    kernel.step()

    obs = kernel.get_agent_observation(int(own))
    self.assertGreaterEqual(len(obs.contacts), 1)
    track = obs.contacts[0]
    self.assertTrue(hasattr(track, "status"))
    self.assertTrue(hasattr(track, "quality"))
    self.assertTrue(hasattr(track, "confidence"))
    self.assertTrue(hasattr(track, "usability"))
    self.assertTrue(hasattr(track, "iff_known"))
    self.assertTrue(hasattr(track, "classification_confidence"))
    self.assertEqual(int(track.status), 1)
    self.assertEqual(int(track.usability), 2)
    self.assertFalse(bool(track.iff_known))
    self.assertGreater(float(track.classification_confidence), 0.0)
    self.assertGreater(float(track.quality), 0.0)
    self.assertGreater(float(track.confidence), 0.0)

  def test_pitched_up_unit_reports_positive_aoa_for_level_velocity(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)

    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1000.0,
      heading=0.0,
      pitch=10.0,
      roll=0.0,
      vx=0.0,
      vy=100.0,
      vz=0.0,
    )

    kernel.step()
    inst = kernel.get_instrument_state(entity_id)
    self.assertGreater(float(inst.pitch), 5.0)
    self.assertGreater(float(inst.aoa), 5.0)
    self.assertAlmostEqual(float(inst.aoa), float(inst.pitch), delta=2.0)

  def test_positive_pilot_pitch_input_drives_positive_pitch_rate_and_aoa(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)
    self.assertTrue(kernel.load_database("examples/config/database"))

    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1200.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=180.0,
      vz=0.0,
    )

    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.stick_pitch = 0.5
    pilot.throttle = 0.8
    pilot.gear_handle = 0.0
    kernel.set_pilot_action(entity_id, pilot)

    inst = None
    for _ in range(10):
      kernel.step()
      inst = kernel.get_instrument_state(entity_id)

    self.assertIsNotNone(inst)
    self.assertGreater(float(inst.pitch), 0.0)
    self.assertGreater(float(inst.q), 0.0)
    self.assertGreater(float(inst.aoa), 0.0)

  def test_observation_throttle_matches_propulsion_spool_and_ab_state(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(42)
    self.assertTrue(kernel.load_database("examples/config/database"))

    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      1200.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=200.0,
      vy=0.0,
      vz=0.0,
    )

    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.throttle = 1.0
    pilot.gear_handle = 0.0

    for _ in range(80):
      kernel.set_pilot_action(entity_id, pilot)
      kernel.step()

    obs = kernel.get_agent_observation(entity_id)
    inst = kernel.get_instrument_state(entity_id)
    fd = kernel.get_flight_dynamics_debug_view(entity_id)

    expected_obs_throttle = float(fd.throttle_state) + (0.5 * float(fd.ab_state))
    self.assertAlmostEqual(float(obs.throttle), expected_obs_throttle, delta=1.0e-6)
    self.assertAlmostEqual(float(inst.throttle_pos), 1.0, delta=0.05)
    self.assertGreater(float(fd.throttle_state), 0.2)
    self.assertGreater(float(fd.ab_state), 0.05)
    self.assertGreater(float(inst.engine_rpm), 20.0)
    self.assertGreater(float(inst.fuel_flow), 0.0)


if __name__ == "__main__":
  unittest.main()
