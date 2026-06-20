from __future__ import annotations

from .helpers import *


class LaunchGuidanceRuntimeMixin:
  def test_definition_missile_tuning_flows_into_launch_runtime(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    sim.set_time_step(1.0 / 60.0)

    _, _, aim120_id = _spawn_and_fire_with_station(sim, 1, range_m=22000.0, bearing_deg=5.0)
    aim120 = _missile_runtime(sim, aim120_id)
    self.assertAlmostEqual(float(aim120["mass_total_kg"]), 152.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["max_speed_mps"]), 1372.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["turn_rate_deg_s"]), 30.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["guidance_max_lateral_g"]), 35.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["nav_gain"]), 4.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["apn_target_accel_gain"]), 0.5, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["guidance_autopilot_tau_s"]), 0.04, delta=1.0e-6)
    self.assertAlmostEqual(
      float(aim120["guidance_max_accel_response_g_per_s"]),
      500.0,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(float(aim120["fuse_distance_m"]), 15.0, delta=1.0e-6)
    self.assertEqual(str(aim120["warhead_family"]), "blast_fragmentation")
    self.assertAlmostEqual(float(aim120["warhead_mass_kg"]), 18.144, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["warhead_lethal_radius_m"]), 15.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["warhead_damage_scalar"]), 180.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["warhead_explosive_mass_kg"]), 7.257, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["warhead_case_mass_kg"]), 10.887, delta=1.0e-6)
    self.assertAlmostEqual(
      float(aim120["warhead_projection_radius_fraction"]),
      0.60,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(aim120["warhead_projection_max_radius_m"]),
      20.0,
      delta=1.0e-6,
    )
    self.assertEqual(int(aim120["warhead_projection_max_projected_hitboxes"]), 3)
    self.assertFalse(bool(aim120["warhead_profile_synthetic"]))
    self.assertFalse(bool(aim120["warhead_damage_scalar_synthetic"]))
    self.assertIn("WDU-41/B", str(aim120["warhead_provenance"]))
    self.assertEqual(str(aim120["fuze_type"]), "radar_proximity")
    self.assertAlmostEqual(float(aim120["fuze_trigger_radius_m"]), 15.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["fuze_delay_s"]), 0.015, delta=1.0e-6)
    self.assertAlmostEqual(float(aim120["fuze_reliability"]), 0.94, delta=1.0e-6)
    self.assertFalse(bool(aim120["fuze_profile_synthetic"]))
    self.assertAlmostEqual(float(aim120["sensor_max_range_m"]), 16000.0, delta=1.0e-6)
    self.assertEqual(int(aim120["sensor_type"]), int(ef_py.SensorType.Radar))

    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    sim.set_time_step(1.0 / 60.0)

    _, _, aim9x_id = _spawn_and_fire_with_station(sim, 2, range_m=9000.0, bearing_deg=20.0)
    aim9x = _missile_runtime(sim, aim9x_id)
    self.assertAlmostEqual(float(aim9x["mass_total_kg"]), 85.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["max_speed_mps"]), 850.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["turn_rate_deg_s"]), 60.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["guidance_max_lateral_g"]), 60.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["nav_gain"]), 5.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["apn_target_accel_gain"]), 0.5, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["guidance_autopilot_tau_s"]), 0.03, delta=1.0e-6)
    self.assertAlmostEqual(
      float(aim9x["guidance_max_accel_response_g_per_s"]),
      600.0,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(float(aim9x["fuse_distance_m"]), 8.0, delta=1.0e-6)
    self.assertEqual(str(aim9x["warhead_family"]), "blast_fragmentation")
    self.assertAlmostEqual(float(aim9x["warhead_mass_kg"]), 9.4, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["warhead_lethal_radius_m"]), 8.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["warhead_damage_scalar"]), 84.6, delta=1.0e-6)
    self.assertFalse(bool(aim9x["warhead_profile_synthetic"]))
    self.assertTrue(bool(aim9x["warhead_damage_scalar_synthetic"]))
    self.assertEqual(str(aim9x["fuze_type"]), "laser_proximity")
    self.assertAlmostEqual(float(aim9x["fuze_trigger_radius_m"]), 8.0, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["fuze_delay_s"]), 0.008, delta=1.0e-6)
    self.assertAlmostEqual(float(aim9x["fuze_reliability"]), 0.92, delta=1.0e-6)
    self.assertFalse(bool(aim9x["fuze_profile_synthetic"]))
    self.assertEqual(int(aim9x["sensor_type"]), int(ef_py.SensorType.Infrared))

  def test_global_missile_tuning_can_override_definition_baseline(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    sim.set_time_step(1.0 / 60.0)

    tuning = ef_py.MissileTuning()
    tuning.max_speed = 910.0
    tuning.turn_rate = 44.0
    tuning.fuse_distance = 21.0
    tuning.sensor_max_range = 12345.0
    tuning.sensor_scan_period = 0.25
    tuning.sensor_track_memory_s = 3.0
    tuning.seeker_type = int(ef_py.SensorType.Radar)
    tuning.propellant_mass_kg = 33.0
    tuning.reference_area_m2 = 0.041
    tuning.boost_time_s = 1.7
    tuning.sustain_time_s = 0.3
    tuning.max_lateral_g = 47.0
    sim.set_missile_tuning(tuning)

    _, _, missile_id = _spawn_and_fire_with_station(sim, 2, range_m=9000.0, bearing_deg=15.0)
    runtime = _missile_runtime(sim, missile_id)
    self.assertAlmostEqual(float(runtime["mass_total_kg"]), 85.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["mass_fuel_kg"]), 33.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["reference_area_m2"]), 0.041, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["max_speed_mps"]), 910.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["turn_rate_deg_s"]), 44.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["fuse_distance_m"]), 21.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["sensor_max_range_m"]), 12345.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["sensor_scan_period_s"]), 0.25, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["sensor_track_memory_s"]), 3.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["guidance_max_lateral_g"]), 47.0, delta=1.0e-6)
    self.assertEqual(int(runtime["sensor_type"]), int(ef_py.SensorType.Radar))

  def test_min_launch_range_rejects_without_consuming_ammo_or_cooldown(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.min_launch_range_m = 15000.0
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=12000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )

    blocked_id = int(sim.fire_missile(blue_id, red_id))
    self.assertEqual(blocked_id, 0)
    blocked_obs = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
    self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    fired_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(fired_id, 0)
    post_fire = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
    self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

  def test_off_boresight_cap_rejects_without_consuming_ammo_or_cooldown(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.max_launch_off_boresight_deg = 10.0
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=22000.0, bearing_deg=25.0, local_sensor_hit=True)],
    )

    blocked_id = int(sim.fire_missile(blue_id, red_id))
    self.assertEqual(blocked_id, 0)
    blocked_obs = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
    self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=22000.0, bearing_deg=5.0, local_sensor_hit=True)],
    )
    fired_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(fired_id, 0)
    post_fire = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
    self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

  def test_lobl_requirement_rejects_nonlocal_track_without_consuming_ammo_or_cooldown(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.lobl_required = True
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=False)],
    )

    blocked_id = int(sim.fire_missile(blue_id, red_id))
    self.assertEqual(blocked_id, 0)
    blocked_obs = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
    self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    fired_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(fired_id, 0)
    post_fire = sim.get_agent_observation(blue_id)
    self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
    self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

  def test_missile_tuning_roundtrip_shared_api(self) -> None:
    sim = _make_kernel()

    tuning = ef_py.MissileTuning()
    tuning.max_speed = 1234.0
    tuning.turn_rate = 27.5
    tuning.nav_gain = 4.2
    tuning.seeker_type = int(ef_py.SensorType.Radar)
    tuning.bearing_filter_tau_s = 0.07
    tuning.elevation_filter_tau_s = 0.11
    tuning.range_filter_tau_s = 0.19
    tuning.track_break_time_s = 1.35
    tuning.boost_time_s = 2.8
    tuning.sustain_time_s = 1.1
    tuning.boost_thrust_n = 21000.0
    tuning.sustain_thrust_n = 7200.0
    tuning.reference_area_m2 = 0.031
    tuning.cd0_subsonic = 0.24
    tuning.cd0_supersonic = 0.68
    tuning.induced_drag_k = 7.5
    tuning.propellant_mass_kg = 24.0
    tuning.max_lateral_g = 28.0
    tuning.autopilot_tau_s = 0.16
    tuning.max_accel_response_g_per_s = 95.0
    tuning.lobl_required = True
    tuning.midcourse_datalink_supported = True
    sim.set_missile_tuning(tuning)

    got = sim.get_missile_tuning()
    self.assertEqual(got.seeker_type, int(ef_py.SensorType.Radar))
    self.assertAlmostEqual(got.max_speed, 1234.0)
    self.assertAlmostEqual(got.turn_rate, 27.5)
    self.assertAlmostEqual(got.nav_gain, 4.2)
    self.assertAlmostEqual(got.bearing_filter_tau_s, 0.07)
    self.assertAlmostEqual(got.elevation_filter_tau_s, 0.11)
    self.assertAlmostEqual(got.range_filter_tau_s, 0.19)
    self.assertAlmostEqual(got.track_break_time_s, 1.35)
    self.assertAlmostEqual(got.boost_time_s, 2.8)
    self.assertAlmostEqual(got.sustain_time_s, 1.1)
    self.assertAlmostEqual(got.boost_thrust_n, 21000.0)
    self.assertAlmostEqual(got.sustain_thrust_n, 7200.0)
    self.assertAlmostEqual(got.reference_area_m2, 0.031)
    self.assertAlmostEqual(got.cd0_subsonic, 0.24)
    self.assertAlmostEqual(got.cd0_supersonic, 0.68)
    self.assertAlmostEqual(got.induced_drag_k, 7.5)
    self.assertAlmostEqual(got.propellant_mass_kg, 24.0)
    self.assertAlmostEqual(got.max_lateral_g, 28.0)
    self.assertAlmostEqual(got.autopilot_tau_s, 0.16)
    self.assertAlmostEqual(got.max_accel_response_g_per_s, 95.0)
    self.assertTrue(got.lobl_required)
    self.assertTrue(got.midcourse_datalink_supported)

  def test_seeker_activation_range_requires_local_terminal_contact(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.seeker_activation_range_m = 8000.0
    tuning.midcourse_datalink_supported = True
    tuning.track_break_time_s = 0.3
    tuning.range_filter_tau_s = 0.0
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    runtime = _missile_runtime(sim, missile_id)
    self.assertFalse(bool(runtime["terminal_seeker_active"]))
    self.assertTrue(bool(runtime["midcourse_datalink_supported"]))
    self.assertAlmostEqual(float(runtime["seeker_activation_range_m"]), 8000.0, delta=1.0e-6)

    for step_idx in range(12):
      t_s = step_idx * sim.get_time_step()
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=25000.0, bearing_deg=12.0, local_sensor_hit=False, timestamp=t_s)],
      )
      sim.step()

    midcourse_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(midcourse_runtime["seeker_has_valid_track"]))
    self.assertEqual(int(midcourse_runtime["seeker_mode"]), 0)
    self.assertFalse(bool(midcourse_runtime["terminal_seeker_active"]))
    self.assertGreater(float(midcourse_runtime["filtered_range_m"]), 8000.0)

    _set_contacts(
      sim,
      missile_id,
      [_make_detection(red_id, range_m=6000.0, bearing_deg=6.0, local_sensor_hit=False, timestamp=1.0)],
    )
    sim.step()
    activated_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
    self.assertLess(float(activated_runtime["filtered_range_m"]), 8000.0)

    _set_contacts(sim, missile_id, [])
    for _ in range(30):
      sim.step()

    no_local_terminal_runtime = _missile_runtime(sim, missile_id)
    self.assertFalse(bool(no_local_terminal_runtime["seeker_has_valid_track"]))
    self.assertEqual(int(no_local_terminal_runtime["seeker_mode"]), 2)
    self.assertTrue(bool(no_local_terminal_runtime["terminal_seeker_active"]))

    _set_contacts(
      sim,
      missile_id,
      [_make_detection(red_id, range_m=5500.0, bearing_deg=3.0, local_sensor_hit=True, timestamp=2.0)],
    )
    sim.step()
    local_terminal_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(local_terminal_runtime["seeker_has_valid_track"]))
    self.assertEqual(int(local_terminal_runtime["seeker_mode"]), 0)
    self.assertTrue(bool(local_terminal_runtime["terminal_seeker_active"]))
    self.assertLess(float(local_terminal_runtime["filtered_range_m"]), 8000.0)

  def test_without_midcourse_datalink_nonlocal_updates_do_not_drive_track(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.seeker_activation_range_m = 8000.0
    tuning.midcourse_datalink_supported = False
    tuning.track_break_time_s = 0.1
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    for step_idx in range(20):
      t_s = step_idx * sim.get_time_step()
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=22000.0, bearing_deg=15.0, local_sensor_hit=False, timestamp=t_s)],
      )
      sim.step()

    runtime = _missile_runtime(sim, missile_id)
    self.assertFalse(bool(runtime["midcourse_datalink_supported"]))
    self.assertFalse(bool(runtime["terminal_seeker_active"]))
    self.assertFalse(bool(runtime["seeker_has_valid_track"]))
    self.assertEqual(int(runtime["seeker_mode"]), 2)

  def test_guidance_keeps_assigned_target_even_if_stronger_nonassigned_contact_appears(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    intruder_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        "Aircraft",
        5000.0,
        26000.0,
        5000.0,
        180.0,
        0.0,
        0.0,
        0.0,
        -250.0,
        0.0,
      )
    )

    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, signal_strength=1.0)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    for step_idx in range(6):
      t_s = step_idx * sim.get_time_step()
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=25000.0, bearing_deg=4.0, signal_strength=0.6, timestamp=t_s)],
      )
      sim.step()

    for step_idx in range(6, 12):
      t_s = step_idx * sim.get_time_step()
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(intruder_id, range_m=18000.0, bearing_deg=20.0, signal_strength=4.0, timestamp=t_s)],
      )
      sim.step()

    runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(runtime["seeker_has_valid_track"]))
    self.assertEqual(int(runtime["seeker_mode"]), 1)

  def test_terminal_seeker_activation_latches_after_entry(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.seeker_activation_range_m = 8000.0
    tuning.midcourse_datalink_supported = True
    tuning.track_break_time_s = 0.5
    tuning.range_filter_tau_s = 0.0
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    _set_contacts(
      sim,
      missile_id,
      [_make_detection(red_id, range_m=6000.0, bearing_deg=2.0, local_sensor_hit=True, timestamp=0.0)],
    )
    sim.step()
    activated_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
    self.assertLess(float(activated_runtime["filtered_range_m"]), 8000.0)

    _set_contacts(
      sim,
      missile_id,
      [_make_detection(red_id, range_m=12000.0, bearing_deg=2.5, local_sensor_hit=False, timestamp=sim.get_time_step())],
    )
    sim.step()
    post_expand_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(post_expand_runtime["terminal_seeker_active"]))
    self.assertTrue(bool(post_expand_runtime["seeker_has_valid_track"]))
    self.assertEqual(int(post_expand_runtime["seeker_mode"]), 1)
    self.assertLess(float(post_expand_runtime["filtered_range_m"]), 8000.0)

    _set_contacts(sim, missile_id, [])
    for _ in range(40):
      sim.step()

    decayed_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(decayed_runtime["terminal_seeker_active"]))
    self.assertFalse(bool(decayed_runtime["seeker_has_valid_track"]))
    self.assertEqual(int(decayed_runtime["seeker_mode"]), 2)

  def test_terminal_proximity_fuze_does_not_resolve_hit_after_terminal_track_fully_decays(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.seeker_activation_range_m = 8000.0
    tuning.midcourse_datalink_supported = True
    tuning.track_break_time_s = 0.12
    tuning.range_filter_tau_s = 0.0
    tuning.max_speed = 120.0
    tuning.boost_time_s = 0.0
    tuning.sustain_time_s = 0.0
    tuning.reference_area_m2 = 0.01
    tuning.fuse_distance = 50.0
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(
      sim,
      blue_id,
      [_make_detection(red_id, range_m=9000.0, bearing_deg=0.0, local_sensor_hit=True)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    target_health_before = list(sim.get_unit_health(red_id))

    for step_idx in range(6):
      t_s = step_idx * sim.get_time_step()
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=40.0, bearing_deg=0.0, local_sensor_hit=True, timestamp=t_s)],
      )
      sim.step()

    activated_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
    self.assertTrue(bool(activated_runtime["seeker_has_valid_track"]))

    for _ in range(20):
      _set_contacts(sim, missile_id, [])
      sim.step()
      if not sim.is_unit_active(missile_id):
        break

    self.assertTrue(sim.is_unit_active(red_id))
    self.assertEqual(list(sim.get_unit_health(red_id)), target_health_before)

  def test_debug_runtime_exposes_proximity_fuze_miss_distance_state(self) -> None:
    sim = _make_baseline_kernel()
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

    initial_runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(math.isinf(float(initial_runtime["proximity_min_dist_m"])))
    self.assertTrue(math.isinf(float(initial_runtime["proximity_last_dist_m"])))
    self.assertFalse(bool(initial_runtime["proximity_engaged"]))

    for step_idx in range(3):
      _set_contacts(
        sim,
        missile_id,
        [_relative_detection_from_truth(sim, missile_id, red_id, timestamp=step_idx * sim.get_time_step())],
      )
      sim.step()

    runtime = _missile_runtime(sim, missile_id)
    self.assertTrue(math.isfinite(float(runtime["proximity_min_dist_m"])))
    self.assertTrue(math.isfinite(float(runtime["proximity_last_dist_m"])))
    self.assertGreater(float(runtime["proximity_min_dist_m"]), 0.0)
    self.assertGreater(float(runtime["proximity_last_dist_m"]), 0.0)

  def test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries(self) -> None:
    cases = {
      "head_on": _run_miss_distance_case(
        red_x=0.0,
        red_y=26000.0,
        red_heading=180.0,
        red_vx=0.0,
        red_vy=-250.0,
      ),
      "tail_chase": _run_miss_distance_case(
        red_x=0.0,
        red_y=18000.0,
        red_heading=0.0,
        red_vx=0.0,
        red_vy=290.0,
      ),
      "beam": _run_miss_distance_case(
        red_x=-9000.0,
        red_y=15000.0,
        red_heading=90.0,
        red_vx=300.0,
        red_vy=0.0,
      ),
      "high_off_boresight": _run_miss_distance_case(
        red_x=13000.0,
        red_y=9000.0,
        red_heading=270.0,
        red_vx=-260.0,
        red_vy=0.0,
      ),
    }

    for name, result in cases.items():
      with self.subTest(geometry=name):
        self.assertFalse(bool(result["missile_active"]))
        self.assertTrue(math.isfinite(float(result["truth_min_dist_m"])))
        self.assertTrue(math.isfinite(float(result["proximity_min_dist_m"])))
        self.assertGreaterEqual(float(result["proximity_min_dist_m"]), 0.0)
        self.assertLess(
          abs(float(result["truth_min_dist_m"]) - float(result["proximity_min_dist_m"])),
          500.0,
        )
        self.assertTrue(bool(result["proximity_engaged"]))
        self.assertTrue(bool(result["terminal_seeker_active"]))

    self.assertLess(float(cases["head_on"]["proximity_min_dist_m"]), 50.0)
    self.assertGreater(float(cases["tail_chase"]["proximity_min_dist_m"]), 5000.0)
    self.assertGreater(
      float(cases["beam"]["proximity_min_dist_m"]),
      float(cases["head_on"]["proximity_min_dist_m"]) + 10.0,
    )
    self.assertLess(float(cases["beam"]["proximity_min_dist_m"]), 250.0)
    self.assertLess(float(cases["high_off_boresight"]["proximity_min_dist_m"]), 5.0)
    self.assertGreater(
      float(cases["head_on"]["max_achieved_lateral_accel_mps2"]),
      float(cases["tail_chase"]["max_achieved_lateral_accel_mps2"]) + 100.0,
    )
