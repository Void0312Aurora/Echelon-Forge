from __future__ import annotations

from python.testing.runtime import configure_sim_log_level

from .mq9_aim120 import _assert_mq9_event_is_non_authoritative
from .helpers import *


configure_sim_log_level("error")


def _neutral_f16_after_optional_right_aileron_damage(
  *,
  damaged: bool,
  steps: int = 60,
) -> tuple[object, dict[str, float], object | None]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260608)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  report = None
  if damaged:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.8,
      4.1,
      0.0,
      _make_warhead_profile("blast_fragmentation", damage=75.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    if not ok:
      raise AssertionError("profiled right-aileron hit failed")
    events = sim.export_recent_engagement_events()
    report = events.damage_reports[-1]

  for _ in range(int(steps)):
    sim.step()

  return sim.get_instrument_state(target_id), _aircraft_damage_overlay(sim, target_id), report


def _neutral_mq9_after_optional_right_aileron_damage(
  *,
  damaged: bool,
  steps: int = 60,
) -> tuple[object, dict[str, float], object | None, object | None, bool]:
  sim = _kernel_with_unit_overrides([])
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

  effect = None
  report = None
  if damaged:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.4,
      8.0,
      0.0,
      _make_warhead_profile("blast_fragmentation", damage=120.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    if not ok:
      raise AssertionError("profiled MQ-9 right-aileron hit failed")
    events = sim.export_recent_engagement_events()
    effect = events.effects_events[-1]
    report = events.damage_reports[-1]

  for _ in range(int(steps)):
    sim.step()

  return (
    sim.get_instrument_state(target_id),
    _aircraft_damage_overlay(sim, target_id),
    effect,
    report,
    bool(sim.is_unit_active(target_id)),
  )


def _stabilized_mq9_after_optional_right_aileron_damage(
  *,
  damaged: bool,
  steps: int = 18_000,
) -> tuple[object, dict[str, float], object | None, object | None, bool]:
  sim = _kernel_with_unit_overrides([])
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.throttle = 0.6
  sim.set_pilot_action(target_id, pilot)

  effect = None
  report = None
  if damaged:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.4,
      8.0,
      0.0,
      _make_warhead_profile("blast_fragmentation", damage=120.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    if not ok:
      raise AssertionError("profiled MQ-9 right-aileron hit failed")
    events = sim.export_recent_engagement_events()
    effect = events.effects_events[-1]
    report = events.damage_reports[-1]

  for _ in range(int(steps)):
    sim.set_pilot_action(target_id, pilot)
    sim.step()

  return (
    sim.get_instrument_state(target_id),
    _aircraft_damage_overlay(sim, target_id),
    effect,
    report,
    bool(sim.is_unit_active(target_id)),
  )


def _structural_continuous_rod_profile() -> object:
  profile = ef_py.WarheadProfile()
  profile.family = "continuous_rod"
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "test_mlf7_left_wing_loss_dynamic_aero_path"
  return profile


def _structural_profiled_hit_snapshot(
  *,
  local_forward_m: float,
  local_right_m: float,
  local_up_m: float,
  family: str = "continuous_rod",
  damage: float = 90.0,
  steps: int = 6,
) -> dict[str, object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260618)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  profile = _structural_continuous_rod_profile()
  profile.family = str(family)
  profile.damage_scalar = float(damage)
  profile.provenance = "test_mlf7_structural_profiled_snapshot"

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local_forward_m),
    float(local_right_m),
    float(local_up_m),
    profile,
    900.0,
    -250.0,
    0.0,
  )
  if not ok:
    raise AssertionError("profiled structural hit failed")

  for _ in range(int(steps)):
    sim.step()

  return {
    "events": sim.export_recent_engagement_events(),
    "overlay": _aircraft_damage_overlay(sim, target_id),
    "active": bool(sim.is_unit_active(target_id)),
  }


def _ground_contact_state(sim: ef_py.SimulationKernel, entity_id: int) -> dict[str, float | bool]:
  values = [float(value) for value in sim.debug_get_ground_contact_state(int(entity_id))]
  if len(values) != 9:
    raise AssertionError("expected nine ground-contact state fields")
  return {
    "on_ground": bool(values[0]),
    "terrain_z": values[1],
    "lifecycle": values[2],
    "impact_horizontal_speed": values[3],
    "impact_sink_rate": values[4],
    "impact_severity": values[5],
    "gear_stress": values[6],
    "gear_collapsed": bool(values[7]),
    "on_runway": bool(values[8]),
  }


def _left_wing_loss_dynamic_trace(*, max_steps: int = 30_000) -> dict[str, object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260618)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.throttle = 0.6
  sim.set_pilot_action(target_id, pilot)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    -0.753,
    -7.1,
    -0.985,
    _structural_continuous_rod_profile(),
    900.0,
    -250.0,
    0.0,
  )
  if not ok:
    raise AssertionError("profiled left-wing continuous-rod hit failed")

  max_abs_roll = 0.0
  max_abs_roll_rate = 0.0
  max_abs_beta = 0.0
  left_wing_loss = False
  structural_consequence = None
  consequence_overlay = None
  ground_state = None
  ground_contact_time_s = None
  final_instrument = None
  dt_s = float(sim.get_time_step())

  for step in range(int(max_steps) + 1):
    inst = sim.get_instrument_state(target_id)
    final_instrument = inst
    max_abs_roll = max(max_abs_roll, abs(float(inst.roll)))
    max_abs_roll_rate = max(max_abs_roll_rate, abs(float(inst.p)))
    max_abs_beta = max(max_abs_beta, abs(float(inst.beta)))

    events = sim.export_recent_engagement_events()
    left_wing_loss = left_wing_loss or any(
      str(event.break_mode) == "wing_loss"
      and str(event.detached_part_ref) == "left_wing"
      for event in events.structural_breakup_events
    )
    if structural_consequence is None:
      structural_consequence = next(
        (
          event
          for event in events.platform_consequence_events
          if str(event.header.producer_node_id)
          == "damage_system.structural_consequence"
        ),
        None,
      )
      if structural_consequence is not None:
        consequence_overlay = _aircraft_damage_overlay(sim, target_id)

    current_ground = _ground_contact_state(sim, target_id)
    if current_ground["on_ground"]:
      ground_state = current_ground
      ground_contact_time_s = step * dt_s
      break

    sim.set_pilot_action(target_id, pilot)
    sim.step()

  return {
    "left_wing_loss": left_wing_loss,
    "structural_consequence": structural_consequence,
    "consequence_overlay": consequence_overlay,
    "ground_state": ground_state,
    "ground_contact_time_s": ground_contact_time_s,
    "final_instrument": final_instrument,
    "target_active": bool(sim.is_unit_active(target_id)),
    "max_abs_roll": max_abs_roll,
    "max_abs_roll_rate": max_abs_roll_rate,
    "max_abs_beta": max_abs_beta,
  }


def _fuselage_fuel_fire_terminal_trace(*, max_steps: int = 60_000) -> dict[str, object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260618)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.throttle = 0.6
  sim.set_pilot_action(target_id, pilot)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    -0.6,
    0.0,
    -0.1,
    _make_warhead_profile("blast_fragmentation", damage=180.0, radius=35.0),
    900.0,
    -250.0,
    0.0,
  )
  if not ok:
    raise AssertionError("profiled fuselage fuel/fire hit failed")

  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError("expected one fuselage fuel/fire effects event")
  if len(events.damage_reports) != 1:
    raise AssertionError("expected one fuselage fuel/fire damage report")

  hit_overlay = _aircraft_damage_overlay(sim, target_id)
  terminal_sample = None
  ground_state = None
  ground_contact_time_s = None
  target_active = True
  final_inst = None
  final_overlay = hit_overlay
  final_health = [float(value) for value in sim.get_unit_health(target_id)]
  dt_s = float(sim.get_time_step())

  for step in range(int(max_steps) + 1):
    if not bool(sim.is_unit_active(target_id)):
      target_active = False
      break
    inst = sim.get_instrument_state(target_id)
    overlay = _aircraft_damage_overlay(sim, target_id)
    health = [float(value) for value in sim.get_unit_health(target_id)]
    current_ground = _ground_contact_state(sim, target_id)
    final_inst = inst
    final_overlay = overlay
    final_health = health

    if terminal_sample is None and health[0] <= 0.0:
      terminal_sample = {
        "time_s": step * dt_s,
        "altitude_m": float(inst.alt_baro),
        "ground_speed_mps": float(inst.ground_speed),
        "vvi_mps": float(inst.vvi),
        "overlay": overlay,
        "ground": current_ground,
        "health": health,
      }

    if current_ground["on_ground"]:
      ground_state = current_ground
      ground_contact_time_s = step * dt_s
      sim.step()
      target_active = bool(sim.is_unit_active(target_id))
      break

    if terminal_sample is None:
      sim.set_pilot_action(target_id, pilot)
    sim.step()

  if target_active and bool(sim.is_unit_active(target_id)):
    final_inst = sim.get_instrument_state(target_id)
    final_overlay = _aircraft_damage_overlay(sim, target_id)
    final_health = [float(value) for value in sim.get_unit_health(target_id)]
  return {
    "effect": events.effects_events[0],
    "report": events.damage_reports[0],
    "hit_overlay": hit_overlay,
    "terminal_sample": terminal_sample,
    "ground_state": ground_state,
    "ground_contact_time_s": ground_contact_time_s,
    "final_overlay": final_overlay,
    "final_instrument": final_inst,
    "target_active": target_active and bool(sim.is_unit_active(target_id)),
    "final_health": final_health,
  }


class AeroConsumerRuntimeMixin:
  def test_wing_control_damage_reaches_neutral_aero_response_with_mobility_verdict(
    self,
  ) -> None:
    baseline_inst, baseline_overlay, _baseline_report = (
      _neutral_f16_after_optional_right_aileron_damage(damaged=False)
    )
    damaged_inst, damaged_overlay, damaged_report = (
      _neutral_f16_after_optional_right_aileron_damage(damaged=True)
    )

    self.assertIsNotNone(damaged_report)
    assert damaged_report is not None
    self.assertFalse(bool(damaged_report.destroyed))
    self.assertEqual(str(damaged_report.loss_state_to), "combat_capable")
    self.assertFalse(bool(damaged_report.forced_landing))
    self.assertFalse(bool(damaged_report.mobility_kill))
    self.assertFalse(bool(damaged_report.flight_control_kill))
    self.assertLess(damaged_overlay["flight_control"], baseline_overlay["flight_control"])
    self.assertGreater(damaged_overlay["flight_control"], 0.55)
    self.assertLess(damaged_overlay["roll_control"], baseline_overlay["roll_control"])
    self.assertGreater(damaged_overlay["roll_control"], 0.70)
    self.assertGreater(damaged_overlay["control_asymmetry"], baseline_overlay["control_asymmetry"])

    roll_delta_deg = abs(float(damaged_inst.roll) - float(baseline_inst.roll))
    beta_delta_deg = abs(float(damaged_inst.beta) - float(baseline_inst.beta))
    self.assertGreater(roll_delta_deg, 5.0)
    self.assertGreater(beta_delta_deg, 2.0)

  def test_mq9_aim120_right_aileron_damage_changes_roll_response_through_aero_path(
    self,
  ) -> None:
    baseline_inst, baseline_overlay, _baseline_effect, _baseline_report, baseline_active = (
      _neutral_mq9_after_optional_right_aileron_damage(damaged=False)
    )
    damaged_inst, damaged_overlay, damaged_effect, damaged_report, damaged_active = (
      _neutral_mq9_after_optional_right_aileron_damage(damaged=True)
    )

    self.assertTrue(baseline_active)
    self.assertTrue(damaged_active)
    self.assertIsNotNone(damaged_effect)
    self.assertIsNotNone(damaged_report)
    assert damaged_effect is not None
    assert damaged_report is not None

    self.assertEqual(str(damaged_effect.component_primary_name), "right_aileron_servo")
    self.assertEqual(str(damaged_effect.component_primary_system), "flight_control")
    self.assertAlmostEqual(float(damaged_report.hp_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(damaged_report.destroyed))
    self.assertTrue(bool(damaged_effect.direct_hitbox_intersection))
    _assert_mq9_event_is_non_authoritative(self, damaged_effect)

    self.assertLess(damaged_overlay["flight_control"], baseline_overlay["flight_control"])
    self.assertLess(damaged_overlay["roll_control"], baseline_overlay["roll_control"])
    self.assertGreater(
      damaged_overlay["control_asymmetry"],
      baseline_overlay["control_asymmetry"],
    )

    roll_delta_deg = abs(float(damaged_inst.roll) - float(baseline_inst.roll))
    beta_delta_deg = abs(float(damaged_inst.beta) - float(baseline_inst.beta))
    speed_delta_mps = abs(
      float(damaged_inst.ground_speed) - float(baseline_inst.ground_speed)
    )
    self.assertGreater(roll_delta_deg, 5.0)
    self.assertGreater(beta_delta_deg, 2.0)
    self.assertGreater(speed_delta_mps, 2.0)

  def test_mq9_aim120_right_aileron_damage_long_run_remains_observable_with_degraded_control(
    self,
  ) -> None:
    baseline_inst, baseline_overlay, _baseline_effect, _baseline_report, baseline_active = (
      _stabilized_mq9_after_optional_right_aileron_damage(damaged=False)
    )
    damaged_inst, damaged_overlay, damaged_effect, damaged_report, damaged_active = (
      _stabilized_mq9_after_optional_right_aileron_damage(damaged=True)
    )

    self.assertTrue(baseline_active)
    self.assertGreater(float(baseline_inst.alt_baro), 4_500.0)
    self.assertGreater(float(baseline_inst.ground_speed), 200.0)
    self.assertAlmostEqual(baseline_overlay["flight_control"], 1.0, delta=1.0e-6)

    self.assertIsNotNone(damaged_effect)
    self.assertIsNotNone(damaged_report)
    assert damaged_effect is not None
    assert damaged_report is not None
    self.assertEqual(str(damaged_effect.component_primary_name), "right_aileron_servo")
    self.assertEqual(str(damaged_effect.component_primary_system), "flight_control")
    self.assertFalse(bool(damaged_report.destroyed))
    _assert_mq9_event_is_non_authoritative(self, damaged_effect)

    self.assertLess(damaged_overlay["flight_control"], baseline_overlay["flight_control"])
    self.assertLess(damaged_overlay["roll_control"], baseline_overlay["roll_control"])
    self.assertGreater(
      damaged_overlay["control_asymmetry"],
      baseline_overlay["control_asymmetry"],
    )

    altitude_delta_m = float(damaged_inst.alt_baro) - float(baseline_inst.alt_baro)
    speed_delta_mps = float(damaged_inst.ground_speed) - float(baseline_inst.ground_speed)
    beta_delta_deg = abs(float(damaged_inst.beta) - float(baseline_inst.beta))
    self.assertLess(altitude_delta_m, -10.0)
    self.assertGreater(float(damaged_inst.alt_baro), 4_500.0)
    self.assertLess(speed_delta_mps, -80.0)
    self.assertGreater(float(damaged_inst.ground_speed), 120.0)
    self.assertGreater(beta_delta_deg, 5.0)
    self.assertTrue(damaged_active)

  def test_mlf7_left_wing_loss_rolls_off_and_reaches_crashed_wreck_through_aero_path(
    self,
  ) -> None:
    trace = _left_wing_loss_dynamic_trace()

    self.assertTrue(bool(trace["left_wing_loss"]))
    consequence = trace["structural_consequence"]
    self.assertIsNotNone(consequence)
    assert consequence is not None
    self.assertEqual(str(consequence.loss_state_to), "mobility_kill")
    self.assertLessEqual(float(consequence.mobility_capability_after), 0.25)

    overlay = trace["consequence_overlay"]
    self.assertIsNotNone(overlay)
    assert isinstance(overlay, dict)
    self.assertLessEqual(float(overlay["structure"]), 0.35)
    self.assertLessEqual(float(overlay["roll_control"]), 0.18)
    self.assertGreaterEqual(float(overlay["control_asymmetry"]), 0.78)
    self.assertGreaterEqual(float(overlay["forced_landing"]), 1.0)

    self.assertGreater(float(trace["max_abs_roll"]), 45.0)
    self.assertGreater(float(trace["max_abs_roll_rate"]), 30.0)
    self.assertGreater(float(trace["max_abs_beta"]), 60.0)

    ground = trace["ground_state"]
    self.assertIsNotNone(ground)
    assert isinstance(ground, dict)
    self.assertTrue(bool(ground["on_ground"]))
    self.assertEqual(int(float(ground["lifecycle"])), 2)
    self.assertGreater(float(ground["impact_sink_rate"]), 15.0)
    self.assertGreater(float(ground["impact_severity"]), 1.0)
    self.assertTrue(bool(trace["target_active"]))

  def test_mlf7_fuselage_fuel_fire_burns_down_then_retires_after_terminal_loss(
    self,
  ) -> None:
    trace = _fuselage_fuel_fire_terminal_trace()

    effect = trace["effect"]
    report = trace["report"]
    self.assertEqual(str(effect.component_primary_name), "center_fuselage_fuel_cell")
    self.assertEqual(str(effect.component_primary_system), "fuel")
    self.assertTrue(bool(effect.direct_hitbox_intersection))
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    self.assertFalse(bool(report.flight_control_kill))

    hit_overlay = trace["hit_overlay"]
    assert isinstance(hit_overlay, dict)
    self.assertGreater(float(hit_overlay["fire"]), 0.10)
    self.assertGreater(float(hit_overlay["fuel_leak"]), 0.30)
    self.assertGreater(float(hit_overlay["flammable_fluid"]), 0.30)
    self.assertGreater(float(hit_overlay["flight_control"]), 0.70)
    self.assertLess(float(hit_overlay["fuel"]), 0.70)

    terminal = trace["terminal_sample"]
    self.assertIsNotNone(terminal)
    assert isinstance(terminal, dict)
    terminal_overlay = terminal["overlay"]
    assert isinstance(terminal_overlay, dict)
    terminal_ground = terminal["ground"]
    assert isinstance(terminal_ground, dict)
    self.assertFalse(bool(terminal_ground["on_ground"]))
    self.assertGreater(float(terminal["altitude_m"]), 1_000.0)
    self.assertGreaterEqual(float(terminal_overlay["fire"]), 1.0)
    self.assertLessEqual(float(terminal_overlay["structure"]), 0.05)
    self.assertGreaterEqual(float(terminal_overlay["flight_control_kill"]), 1.0)
    self.assertGreaterEqual(float(terminal_overlay["propulsion_kill"]), 1.0)

    ground = trace["ground_state"]
    if ground is not None:
      assert isinstance(ground, dict)
      self.assertTrue(bool(ground["on_ground"]))
      self.assertEqual(int(float(ground["lifecycle"])), 2)
      self.assertGreater(float(ground["impact_sink_rate"]), 15.0)
      self.assertGreater(float(ground["impact_severity"]), 1.0)
      self.assertGreater(float(trace["ground_contact_time_s"]), float(terminal["time_s"]))
    else:
      self.assertIsNone(trace["ground_contact_time_s"])
    self.assertFalse(bool(trace["target_active"]))
    self.assertEqual(trace["final_health"][0], 0.0)

  def test_mlf7_mirrored_right_wing_loss_reaches_symmetric_structural_consequence(
    self,
  ) -> None:
    left = _structural_profiled_hit_snapshot(
      local_forward_m=-0.753,
      local_right_m=-7.1,
      local_up_m=-0.985,
    )
    right = _structural_profiled_hit_snapshot(
      local_forward_m=-0.753,
      local_right_m=7.1,
      local_up_m=-0.985,
    )

    for expected_part, snapshot in (("left_wing", left), ("right_wing", right)):
      events = snapshot["events"]
      self.assertTrue(
        any(
          str(event.break_mode) == "wing_loss"
          and str(event.detached_part_ref) == expected_part
          for event in events.structural_breakup_events
        )
      )
      overlay = snapshot["overlay"]
      assert isinstance(overlay, dict)
      self.assertLessEqual(float(overlay["structure"]), 0.35)
      self.assertLessEqual(float(overlay["roll_control"]), 0.18)
      self.assertGreaterEqual(float(overlay["control_asymmetry"]), 0.78)
      self.assertGreaterEqual(float(overlay["flight_control_kill"]), 1.0)

    left_overlay = left["overlay"]
    right_overlay = right["overlay"]
    assert isinstance(left_overlay, dict)
    assert isinstance(right_overlay, dict)
    self.assertAlmostEqual(
      float(left_overlay["flight_control"]),
      float(right_overlay["flight_control"]),
      delta=0.01,
    )
    self.assertAlmostEqual(
      float(left_overlay["roll_control"]),
      float(right_overlay["roll_control"]),
      delta=0.01,
    )

  def test_mlf7_stabilator_component_damage_stays_bounded_without_tail_loss(
    self,
  ) -> None:
    snapshot = _structural_profiled_hit_snapshot(
      local_forward_m=-6.0,
      local_right_m=-1.79,
      local_up_m=-1.05,
      damage=180.0,
    )
    events = snapshot["events"]
    self.assertFalse(
      any(str(event.break_mode) == "tail_loss" for event in events.structural_breakup_events)
    )
    tail_damage = next(
      event
      for event in events.component_damage_events
      if str(event.component_name)
      == "left_horizontal_tail_actuator_or_surface_component"
    )
    self.assertGreater(float(tail_damage.integrity_after), 0.20)

    overlay = snapshot["overlay"]
    assert isinstance(overlay, dict)
    self.assertGreater(float(overlay["flight_control"]), 0.40)
    self.assertLess(float(overlay["pitch_control"]), 0.95)
    self.assertLess(float(overlay["pitch_control"]), float(overlay["roll_control"]))
    self.assertLess(float(overlay["pitch_control"]), float(overlay["yaw_control"]))
    self.assertLess(float(overlay["flight_control_kill"]), 1.0)
    self.assertLess(float(overlay["forced_landing"]), 1.0)
