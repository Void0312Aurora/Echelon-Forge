from __future__ import annotations

from .helpers import *


class MissileDynamicsRuntimeMixin:
  def test_launch_initializes_mass_and_runtime_state(self) -> None:
    sim = _make_kernel()
    tuning = sim.get_missile_tuning()
    tuning.propellant_mass_kg = 22.0
    tuning.track_break_time_s = 1.4
    tuning.boost_time_s = 2.5
    tuning.sustain_time_s = 0.7
    sim.set_missile_tuning(tuning)

    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=8.0)])

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    mass_state = sim.debug_get_mass_state(missile_id)
    self.assertEqual(len(mass_state), 6)
    self.assertAlmostEqual(float(mass_state[0]), 58.0, delta=1.0e-6)
    self.assertAlmostEqual(float(mass_state[1]), 22.0, delta=1.0e-6)
    self.assertAlmostEqual(float(mass_state[3]), 80.0, delta=1.0e-6)
    self.assertAlmostEqual(float(mass_state[4]), 58.0, delta=1.0e-6)
    self.assertAlmostEqual(float(mass_state[5]), 80.0, delta=1.0e-6)

    runtime = sim.debug_get_missile_runtime_state(missile_id)
    self.assertTrue(bool(runtime["p0_runtime_initialized"]))
    self.assertTrue(bool(runtime["seeker_has_valid_track"]))
    self.assertTrue(bool(runtime["seeker_has_range"]))
    self.assertEqual(int(runtime["seeker_mode"]), 0)
    self.assertAlmostEqual(float(runtime["track_memory_timeout_s"]), 1.4, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["filtered_bearing_deg"]), 8.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["filtered_range_m"]), 30000.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["current_speed_mps"]), 250.0, delta=1.0e-6)
    self.assertAlmostEqual(float(runtime["burnout_time_s"]), 3.2, delta=1.0e-6)

  def test_shared_burn_window_changes_guidance_speed_profile(self) -> None:
    short_sim = _make_kernel()
    short_tuning = short_sim.get_missile_tuning()
    short_tuning.boost_time_s = 0.6
    short_tuning.sustain_time_s = 0.0
    short_sim.set_missile_tuning(short_tuning)

    long_sim = _make_kernel()
    long_tuning = long_sim.get_missile_tuning()
    long_tuning.boost_time_s = 4.0
    long_tuning.sustain_time_s = 0.0
    long_sim.set_missile_tuning(long_tuning)

    short_blue, short_red = _spawn_pair(short_sim)
    long_blue, long_red = _spawn_pair(long_sim)
    _set_contacts(short_sim, short_blue, [_make_detection(short_red, range_m=28000.0, bearing_deg=0.0)])
    _set_contacts(long_sim, long_blue, [_make_detection(long_red, range_m=28000.0, bearing_deg=0.0)])

    short_id = int(short_sim.fire_missile(short_blue, short_red))
    long_id = int(long_sim.fire_missile(long_blue, long_red))
    self.assertGreater(short_id, 0)
    self.assertGreater(long_id, 0)

    sample_short = 0.0
    sample_long = 0.0
    for step_idx in range(180):
      t_short = step_idx * short_sim.get_time_step()
      t_long = step_idx * long_sim.get_time_step()
      _set_contacts(short_sim, short_id, [_make_detection(short_red, range_m=max(2000.0, 28000.0 - 350.0 * t_short), bearing_deg=0.0, timestamp=t_short)])
      _set_contacts(long_sim, long_id, [_make_detection(long_red, range_m=max(2000.0, 28000.0 - 350.0 * t_long), bearing_deg=0.0, timestamp=t_long)])
      short_sim.step()
      long_sim.step()
      if step_idx == 120:
        sample_short = _velocity_speed(short_sim, short_id)
        sample_long = _velocity_speed(long_sim, long_id)

    self.assertGreater(sample_long, sample_short + 40.0)

  def test_shared_reference_area_changes_drag_cost(self) -> None:
    clean_sim = _make_kernel()
    clean_tuning = clean_sim.get_missile_tuning()
    clean_tuning.reference_area_m2 = 0.015
    clean_sim.set_missile_tuning(clean_tuning)

    draggy_sim = _make_kernel()
    draggy_tuning = draggy_sim.get_missile_tuning()
    draggy_tuning.reference_area_m2 = 0.060
    draggy_sim.set_missile_tuning(draggy_tuning)

    clean_blue, clean_red = _spawn_pair(clean_sim)
    draggy_blue, draggy_red = _spawn_pair(draggy_sim)
    _set_contacts(clean_sim, clean_blue, [_make_detection(clean_red, range_m=30000.0, bearing_deg=0.0)])
    _set_contacts(draggy_sim, draggy_blue, [_make_detection(draggy_red, range_m=30000.0, bearing_deg=0.0)])

    clean_id = int(clean_sim.fire_missile(clean_blue, clean_red))
    draggy_id = int(draggy_sim.fire_missile(draggy_blue, draggy_red))
    self.assertGreater(clean_id, 0)
    self.assertGreater(draggy_id, 0)

    for step_idx in range(240):
      t_clean = step_idx * clean_sim.get_time_step()
      t_draggy = step_idx * draggy_sim.get_time_step()
      _set_contacts(clean_sim, clean_id, [_make_detection(clean_red, range_m=max(3000.0, 30000.0 - 350.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)])
      _set_contacts(draggy_sim, draggy_id, [_make_detection(draggy_red, range_m=max(3000.0, 30000.0 - 350.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)])
      clean_sim.step()
      draggy_sim.step()

    clean_speed = _velocity_speed(clean_sim, clean_id)
    draggy_speed = _velocity_speed(draggy_sim, draggy_id)
    self.assertGreater(clean_speed, draggy_speed + 20.0)

  def test_shared_cd0_subsonic_changes_low_speed_drag_cost(self) -> None:
    clean_sim = _make_kernel()
    clean_tuning = clean_sim.get_missile_tuning()
    clean_tuning.boost_time_s = 0.0
    clean_tuning.sustain_time_s = 0.0
    clean_tuning.max_speed = 320.0
    clean_tuning.reference_area_m2 = 0.050
    clean_tuning.cd0_subsonic = 0.12
    clean_tuning.cd0_supersonic = 0.12
    clean_sim.set_missile_tuning(clean_tuning)

    draggy_sim = _make_kernel()
    draggy_tuning = draggy_sim.get_missile_tuning()
    draggy_tuning.boost_time_s = 0.0
    draggy_tuning.sustain_time_s = 0.0
    draggy_tuning.max_speed = 320.0
    draggy_tuning.reference_area_m2 = 0.050
    draggy_tuning.cd0_subsonic = 0.80
    draggy_tuning.cd0_supersonic = 0.80
    draggy_sim.set_missile_tuning(draggy_tuning)

    _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=30000.0, bearing_deg=0.0)
    _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=30000.0, bearing_deg=0.0)

    for step_idx in range(180):
      t_clean = step_idx * clean_sim.get_time_step()
      t_draggy = step_idx * draggy_sim.get_time_step()
      _set_contacts(
        clean_sim,
        clean_id,
        [_make_detection(clean_red, range_m=max(6000.0, 30000.0 - 250.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)],
      )
      _set_contacts(
        draggy_sim,
        draggy_id,
        [_make_detection(draggy_red, range_m=max(6000.0, 30000.0 - 250.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)],
      )
      clean_sim.step()
      draggy_sim.step()

    clean_speed = _velocity_speed(clean_sim, clean_id)
    draggy_speed = _velocity_speed(draggy_sim, draggy_id)
    self.assertGreater(clean_speed, draggy_speed + 20.0)

  def test_shared_cd0_supersonic_changes_high_speed_drag_cost(self) -> None:
    clean_sim = _make_kernel()
    clean_tuning = clean_sim.get_missile_tuning()
    clean_tuning.max_speed = 1800.0
    clean_tuning.propellant_mass_kg = 24.0
    clean_tuning.reference_area_m2 = 0.030
    clean_tuning.boost_time_s = 1.2
    clean_tuning.sustain_time_s = 1.2
    clean_tuning.boost_thrust_n = 28000.0
    clean_tuning.sustain_thrust_n = 12000.0
    clean_tuning.cd0_subsonic = 0.20
    clean_tuning.cd0_supersonic = 0.28
    clean_sim.set_missile_tuning(clean_tuning)

    draggy_sim = _make_kernel()
    draggy_tuning = draggy_sim.get_missile_tuning()
    draggy_tuning.max_speed = 1800.0
    draggy_tuning.propellant_mass_kg = 24.0
    draggy_tuning.reference_area_m2 = 0.030
    draggy_tuning.boost_time_s = 1.2
    draggy_tuning.sustain_time_s = 1.2
    draggy_tuning.boost_thrust_n = 28000.0
    draggy_tuning.sustain_thrust_n = 12000.0
    draggy_tuning.cd0_subsonic = 0.20
    draggy_tuning.cd0_supersonic = 1.10
    draggy_sim.set_missile_tuning(draggy_tuning)

    _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=26000.0, bearing_deg=0.0)
    _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=26000.0, bearing_deg=0.0)

    sample_clean = 0.0
    sample_draggy = 0.0
    for step_idx in range(144):
      t_clean = step_idx * clean_sim.get_time_step()
      t_draggy = step_idx * draggy_sim.get_time_step()
      _set_contacts(
        clean_sim,
        clean_id,
        [_make_detection(clean_red, range_m=max(4000.0, 26000.0 - 350.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)],
      )
      _set_contacts(
        draggy_sim,
        draggy_id,
        [_make_detection(draggy_red, range_m=max(4000.0, 26000.0 - 350.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)],
      )
      clean_sim.step()
      draggy_sim.step()
      if step_idx == 100:
        sample_clean = _velocity_speed(clean_sim, clean_id)
        sample_draggy = _velocity_speed(draggy_sim, draggy_id)

    self.assertGreater(sample_clean, sample_draggy + 35.0)

  def test_shared_induced_drag_changes_turn_energy_loss(self) -> None:
    clean_sim = _make_kernel()
    clean_tuning = clean_sim.get_missile_tuning()
    clean_tuning.nav_gain = 10.0
    clean_tuning.max_lateral_g = 24.0
    clean_tuning.autopilot_tau_s = 0.03
    clean_tuning.max_accel_response_g_per_s = 400.0
    clean_tuning.reference_area_m2 = 0.020
    clean_tuning.induced_drag_k = 1.5
    clean_sim.set_missile_tuning(clean_tuning)

    draggy_sim = _make_kernel()
    draggy_tuning = draggy_sim.get_missile_tuning()
    draggy_tuning.nav_gain = 10.0
    draggy_tuning.max_lateral_g = 24.0
    draggy_tuning.autopilot_tau_s = 0.03
    draggy_tuning.max_accel_response_g_per_s = 400.0
    draggy_tuning.reference_area_m2 = 0.020
    draggy_tuning.induced_drag_k = 18.0
    draggy_sim.set_missile_tuning(draggy_tuning)

    _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=6000.0, bearing_deg=85.0)
    _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=6000.0, bearing_deg=85.0)

    clean_speed = 0.0
    draggy_speed = 0.0
    for step_idx in range(120):
      t_clean = step_idx * clean_sim.get_time_step()
      t_draggy = step_idx * draggy_sim.get_time_step()
      _set_contacts(
        clean_sim,
        clean_id,
        [_make_detection(clean_red, range_m=6000.0, bearing_deg=85.0, timestamp=t_clean)],
      )
      _set_contacts(
        draggy_sim,
        draggy_id,
        [_make_detection(draggy_red, range_m=6000.0, bearing_deg=85.0, timestamp=t_draggy)],
      )
      clean_sim.step()
      draggy_sim.step()
      if step_idx == 100:
        clean_speed = _velocity_speed(clean_sim, clean_id)
        draggy_speed = _velocity_speed(draggy_sim, draggy_id)

    self.assertGreater(clean_speed, draggy_speed + 25.0)

  def test_shared_boost_and_sustain_thrust_change_speed_profile(self) -> None:
    low_sim = _make_kernel()
    low_tuning = low_sim.get_missile_tuning()
    low_tuning.max_speed = 1800.0
    low_tuning.propellant_mass_kg = 24.0
    low_tuning.reference_area_m2 = 0.015
    low_tuning.boost_time_s = 0.8
    low_tuning.sustain_time_s = 1.6
    low_tuning.boost_thrust_n = 14000.0
    low_tuning.sustain_thrust_n = 3500.0
    low_sim.set_missile_tuning(low_tuning)

    high_sim = _make_kernel()
    high_tuning = high_sim.get_missile_tuning()
    high_tuning.max_speed = 1800.0
    high_tuning.propellant_mass_kg = 24.0
    high_tuning.reference_area_m2 = 0.015
    high_tuning.boost_time_s = 0.8
    high_tuning.sustain_time_s = 1.6
    high_tuning.boost_thrust_n = 26000.0
    high_tuning.sustain_thrust_n = 9000.0
    high_sim.set_missile_tuning(high_tuning)

    _, low_red, low_id = _spawn_and_fire(low_sim, range_m=26000.0, bearing_deg=0.0)
    _, high_red, high_id = _spawn_and_fire(high_sim, range_m=26000.0, bearing_deg=0.0)

    boost_low = 0.0
    boost_high = 0.0
    sustain_low = 0.0
    sustain_high = 0.0
    for step_idx in range(120):
      t_low = step_idx * low_sim.get_time_step()
      t_high = step_idx * high_sim.get_time_step()
      _set_contacts(
        low_sim,
        low_id,
        [_make_detection(low_red, range_m=max(4000.0, 26000.0 - 350.0 * t_low), bearing_deg=0.0, timestamp=t_low)],
      )
      _set_contacts(
        high_sim,
        high_id,
        [_make_detection(high_red, range_m=max(4000.0, 26000.0 - 350.0 * t_high), bearing_deg=0.0, timestamp=t_high)],
      )
      low_sim.step()
      high_sim.step()
      if step_idx == 24:
        boost_low = _velocity_speed(low_sim, low_id)
        boost_high = _velocity_speed(high_sim, high_id)
      if step_idx == 84:
        sustain_low = _velocity_speed(low_sim, low_id)
        sustain_high = _velocity_speed(high_sim, high_id)

    self.assertGreater(boost_high, boost_low + 35.0)
    self.assertGreater(sustain_high, sustain_low + 45.0)

  def test_boost_then_decay_speed_profile(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    speeds: list[float] = []
    time_s = 0.0
    for _ in range(420):
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=max(2000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
      )
      sim.step()
      time_s += sim.get_time_step()
      if not sim.is_unit_active(missile_id):
        break
      speeds.append(_velocity_speed(sim, missile_id))

    self.assertGreater(len(speeds), 120)
    peak_speed = max(speeds)
    self.assertGreater(peak_speed, speeds[5] + 80.0)
    self.assertLess(speeds[-1], peak_speed - 40.0)

  def test_shared_bearing_filter_tau_changes_track_response(self) -> None:
    fast_sim = _make_kernel()
    fast_tuning = fast_sim.get_missile_tuning()
    fast_tuning.bearing_filter_tau_s = 0.02
    fast_tuning.elevation_filter_tau_s = 0.02
    fast_tuning.range_filter_tau_s = 0.02
    fast_sim.set_missile_tuning(fast_tuning)

    slow_sim = _make_kernel()
    slow_tuning = slow_sim.get_missile_tuning()
    slow_tuning.bearing_filter_tau_s = 1.0
    slow_tuning.elevation_filter_tau_s = 1.0
    slow_tuning.range_filter_tau_s = 1.0
    slow_sim.set_missile_tuning(slow_tuning)

    _, fast_red, fast_id = _spawn_and_fire(fast_sim, range_m=24000.0, bearing_deg=0.0)
    _, slow_red, slow_id = _spawn_and_fire(slow_sim, range_m=24000.0, bearing_deg=0.0)

    for step_idx in range(10):
      t_fast = step_idx * fast_sim.get_time_step()
      t_slow = step_idx * slow_sim.get_time_step()
      _set_contacts(
        fast_sim,
        fast_id,
        [_make_detection(fast_red, range_m=22000.0, bearing_deg=60.0, timestamp=t_fast)],
      )
      _set_contacts(
        slow_sim,
        slow_id,
        [_make_detection(slow_red, range_m=22000.0, bearing_deg=60.0, timestamp=t_slow)],
      )
      fast_sim.step()
      slow_sim.step()

    fast_runtime = _missile_runtime(fast_sim, fast_id)
    slow_runtime = _missile_runtime(slow_sim, slow_id)
    fast_bearing = float(fast_runtime["filtered_bearing_deg"])
    slow_bearing = float(slow_runtime["filtered_bearing_deg"])
    self.assertGreater(fast_bearing, 55.0)
    self.assertLess(slow_bearing, 12.0)
    self.assertGreater(fast_bearing, slow_bearing + 35.0)

  def test_mass_depletion_during_propulsion(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    masses: list[float] = []
    time_s = 0.0
    for _ in range(300):
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=max(2000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
      )
      sim.step()
      time_s += sim.get_time_step()
      state = sim.debug_get_mass_state(missile_id)
      self.assertTrue(len(state) >= 6)
      masses.append(float(state[3]))

    self.assertGreater(masses[0], masses[60])
    self.assertGreater(masses[60], masses[120])
    self.assertAlmostEqual(masses[-1], masses[-30], delta=0.5)

  def test_shared_autopilot_tau_changes_response_buildup(self) -> None:
    fast_sim = _make_kernel()
    fast_tuning = fast_sim.get_missile_tuning()
    fast_tuning.nav_gain = 10.0
    fast_tuning.max_lateral_g = 28.0
    fast_tuning.max_accel_response_g_per_s = 400.0
    fast_tuning.autopilot_tau_s = 0.03
    fast_sim.set_missile_tuning(fast_tuning)

    slow_sim = _make_kernel()
    slow_tuning = slow_sim.get_missile_tuning()
    slow_tuning.nav_gain = 10.0
    slow_tuning.max_lateral_g = 28.0
    slow_tuning.max_accel_response_g_per_s = 400.0
    slow_tuning.autopilot_tau_s = 0.75
    slow_sim.set_missile_tuning(slow_tuning)

    _, fast_red, fast_id = _spawn_and_fire(fast_sim, range_m=4000.0, bearing_deg=88.0)
    _, slow_red, slow_id = _spawn_and_fire(slow_sim, range_m=4000.0, bearing_deg=88.0)

    fast_achieved = 0.0
    slow_achieved = 0.0
    for step_idx in range(8):
      t_fast = step_idx * fast_sim.get_time_step()
      t_slow = step_idx * slow_sim.get_time_step()
      _set_contacts(
        fast_sim,
        fast_id,
        [_make_detection(fast_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_fast)],
      )
      _set_contacts(
        slow_sim,
        slow_id,
        [_make_detection(slow_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_slow)],
      )
      fast_sim.step()
      slow_sim.step()
      if step_idx == 5:
        fast_achieved = float(_missile_runtime(fast_sim, fast_id)["achieved_lateral_accel_mps2"])
        slow_achieved = float(_missile_runtime(slow_sim, slow_id)["achieved_lateral_accel_mps2"])

    self.assertGreater(fast_achieved, slow_achieved + 80.0)

  def test_third_order_autopilot_keeps_independent_filter_state(self) -> None:
    def make_ordered_launch(order: int) -> tuple[object, int, int]:
      sim = _make_kernel()
      tuning = sim.get_missile_tuning()
      tuning.nav_gain = 10.0
      tuning.max_lateral_g = 30.0
      tuning.max_accel_response_g_per_s = 120.0
      tuning.autopilot_tau_s = 0.12
      tuning.autopilot_damping = 0.7
      tuning.autopilot_order = order
      sim.set_missile_tuning(tuning)
      _, red_id, missile_id = _spawn_and_fire(sim, range_m=4000.0, bearing_deg=88.0)
      return sim, red_id, missile_id

    def sample_response(sim: object, red_id: int, missile_id: int) -> tuple[float | None, float | None, float]:
      dt = sim.get_time_step()
      t10: float | None = None
      t20: float | None = None
      peak_g = 0.0
      for step_idx in range(180):
        time_s = step_idx * dt
        _set_contacts(
          sim,
          missile_id,
          [_make_detection(red_id, range_m=4000.0, bearing_deg=88.0, timestamp=time_s)],
        )
        sim.step()
        achieved_g = float(_missile_runtime(sim, missile_id)["achieved_lateral_accel_mps2"]) / 9.80665
        peak_g = max(peak_g, achieved_g)
        if t10 is None and achieved_g >= 10.0:
          t10 = time_s
        if t20 is None and achieved_g >= 20.0:
          t20 = time_s
      return t10, t20, peak_g

    order2_sim, order2_red, order2_id = make_ordered_launch(2)
    order3_sim, order3_red, order3_id = make_ordered_launch(3)

    _, order2_t20, order2_peak_g = sample_response(order2_sim, order2_red, order2_id)
    order3_t10, order3_t20, order3_peak_g = sample_response(order3_sim, order3_red, order3_id)

    if order2_t20 is None or order3_t10 is None or order3_t20 is None:
      self.fail(
        "expected order=2 and order=3 autopilots to reach 20g/10g in the "
        f"sample window; order2_t20={order2_t20}, order3_t10={order3_t10}, "
        f"order3_t20={order3_t20}, order2_peak={order2_peak_g:.2f}g, "
        f"order3_peak={order3_peak_g:.2f}g"
      )

    self.assertGreater(order2_peak_g, 20.0)
    self.assertGreater(order3_peak_g, 20.0)
    self.assertLess(order3_t10, 1.6)
    self.assertLess(order3_t20, 2.6)
    self.assertLess(order3_t20, order2_t20 + 0.8)

  def test_shared_max_lateral_g_changes_guidance_cap(self) -> None:
    low_sim = _make_kernel()
    low_tuning = low_sim.get_missile_tuning()
    low_tuning.nav_gain = 10.0
    low_tuning.max_lateral_g = 8.0
    low_tuning.autopilot_tau_s = 0.03
    low_tuning.max_accel_response_g_per_s = 400.0
    low_sim.set_missile_tuning(low_tuning)

    high_sim = _make_kernel()
    high_tuning = high_sim.get_missile_tuning()
    high_tuning.nav_gain = 10.0
    high_tuning.max_lateral_g = 26.0
    high_tuning.autopilot_tau_s = 0.03
    high_tuning.max_accel_response_g_per_s = 400.0
    high_sim.set_missile_tuning(high_tuning)

    _, low_red, low_id = _spawn_and_fire(low_sim, range_m=4000.0, bearing_deg=88.0)
    _, high_red, high_id = _spawn_and_fire(high_sim, range_m=4000.0, bearing_deg=88.0)

    low_peak_g = 0.0
    high_peak_g = 0.0
    for step_idx in range(100):
      t_low = step_idx * low_sim.get_time_step()
      t_high = step_idx * high_sim.get_time_step()
      _set_contacts(
        low_sim,
        low_id,
        [_make_detection(low_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_low)],
      )
      _set_contacts(
        high_sim,
        high_id,
        [_make_detection(high_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_high)],
      )
      low_sim.step()
      high_sim.step()
      low_peak_g = max(
        low_peak_g,
        float(_missile_runtime(low_sim, low_id)["achieved_lateral_accel_mps2"]) / 9.80665,
      )
      high_peak_g = max(
        high_peak_g,
        float(_missile_runtime(high_sim, high_id)["achieved_lateral_accel_mps2"]) / 9.80665,
      )

    self.assertLess(low_peak_g, 9.5)
    self.assertGreater(high_peak_g, low_peak_g + 12.0)

  def test_bounded_lateral_accel_and_response_lag(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=25000.0, bearing_deg=85.0)])

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    dt = sim.get_time_step()
    headings: list[float] = []
    speeds: list[float] = []
    for step_idx in range(120):
      bearing = 85.0 if step_idx < 80 else -70.0
      _set_contacts(
        sim,
        missile_id,
        [_make_detection(red_id, range_m=25000.0, bearing_deg=bearing, timestamp=step_idx * dt)],
      )
      sim.step()
      if not sim.is_unit_active(missile_id):
        break
      headings.append(_heading_from_velocity(sim, missile_id))
      speeds.append(_velocity_speed(sim, missile_id))

    self.assertGreater(len(headings), 30)
    first_delta = abs(headings[1] - headings[0])
    if first_delta > 180.0:
      first_delta = 360.0 - first_delta
    self.assertLess(first_delta, 3.0)

    max_lateral_g_est = 0.0
    for idx in range(1, len(headings)):
      delta = abs(headings[idx] - headings[idx - 1])
      if delta > 180.0:
        delta = 360.0 - delta
      yaw_rate = math.radians(delta) / dt
      lat_accel = speeds[idx] * yaw_rate
      max_lateral_g_est = max(max_lateral_g_est, lat_accel / 9.80665)

    self.assertLess(max_lateral_g_est, 45.0)

  def test_large_turn_costs_speed(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    sim.set_unit_ammo(blue_id, 4, 4)

    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])
    straight_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(straight_id, 0)

    turning_bearing_deg = 85.0
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=turning_bearing_deg)])
    turning_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(turning_id, 0)

    time_s = 0.0
    for _ in range(240):
      _set_contacts(
        sim,
        straight_id,
        [_make_detection(red_id, range_m=max(5000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
      )
      _set_contacts(
        sim,
        turning_id,
        [_make_detection(red_id, range_m=max(5000.0, 30000.0 - 350.0 * time_s), bearing_deg=turning_bearing_deg, timestamp=time_s)],
      )
      sim.step()
      time_s += sim.get_time_step()
      if not sim.is_unit_active(straight_id) or not sim.is_unit_active(turning_id):
        break

    straight_speed = _velocity_speed(sim, straight_id)
    turning_speed = _velocity_speed(sim, turning_id)
    self.assertGreater(straight_speed, turning_speed + 15.0)

  def test_track_memory_timeout(self) -> None:
    sim = _make_kernel()
    blue_id, red_id = _spawn_pair(sim)
    _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    dt = sim.get_time_step()
    headings: list[float] = []
    time_s = 0.0
    for step_idx in range(170):
      if step_idx < 30:
        bearing = 5.0 + 0.7 * step_idx
        contacts = [_make_detection(red_id, range_m=22000.0, bearing_deg=bearing, timestamp=time_s)]
      else:
        contacts = []
      _set_contacts(sim, missile_id, contacts)
      sim.step()
      time_s += dt
      if not sim.is_unit_active(missile_id):
        break
      headings.append(_heading_from_velocity(sim, missile_id))

    self.assertGreater(len(headings), 120)

    early_memory_delta = abs(headings[55] - headings[30])
    if early_memory_delta > 180.0:
      early_memory_delta = 360.0 - early_memory_delta

    late_delta = abs(headings[150] - headings[120])
    if late_delta > 180.0:
      late_delta = 360.0 - late_delta

    self.assertGreater(early_memory_delta, 2.0)
    self.assertLess(late_delta, early_memory_delta * 0.5)

  # ── boundary / edge-case tests ──────────────────────────────────────
