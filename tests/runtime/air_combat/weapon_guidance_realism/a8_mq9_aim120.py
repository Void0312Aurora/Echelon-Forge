from __future__ import annotations

from .helpers import *


def _spawn_f16_mq9_pair(
  sim: ef_py.SimulationKernel,
  *,
  range_m: float,
  altitude_m: float = 5000.0,
  target_speed_mps: float = 120.0,
) -> tuple[int, int]:
  shooter_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      altitude_m,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "MQ-9_Reaper",
      0.0,
      range_m,
      altitude_m,
      180.0,
      0.0,
      0.0,
      0.0,
      -float(target_speed_mps),
      0.0,
    )
  )
  sim.set_unit_ammo(shooter_id, 4, 4)
  sim.set_weapon_cooldown(shooter_id, 0.0, -1.0)
  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.weapon_select_id = 1
  sim.set_pilot_action(shooter_id, pilot)
  _set_contacts(
    sim,
    shooter_id,
    [
      _relative_detection_from_truth(
        sim,
        shooter_id,
        target_id,
        timestamp=0.0,
        local_sensor_hit=True,
      )
    ],
  )
  return shooter_id, target_id


def _launch_and_drive_mq9_case(
  *,
  range_m: float,
  max_steps: int = 3600,
) -> tuple[ef_py.SimulationKernel, int, int, int, dict[str, float | bool], dict]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260607)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  shooter_id, target_id = _spawn_f16_mq9_pair(sim, range_m=range_m)
  missile_id = int(sim.fire_missile(shooter_id, target_id))
  if missile_id <= 0:
    raise AssertionError(f"expected AIM-120C launch against MQ-9 at {range_m} m")
  missile_runtime = _missile_runtime(sim, missile_id)
  result = _drive_missile_with_truth_track(
    sim,
    missile_id,
    target_id,
    max_steps=max_steps,
  )
  return sim, shooter_id, target_id, missile_id, result, missile_runtime


def _profiled_mq9_aim120_hit(
  local: tuple[float, float, float],
  *,
  damage: float = 120.0,
  radius: float = 35.0,
  velocity: tuple[float, float, float] = (900.0, -250.0, 0.0),
) -> tuple[dict[str, float], dict[str, float], object, object]:
  sim = _kernel_with_unit_overrides([])
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")
  before = _aircraft_damage_overlay(sim, target_id)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _make_warhead_profile("blast_fragmentation", damage=damage, radius=radius),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  if not ok:
    raise AssertionError("profiled MQ-9/AIM-120C local hit failed")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError("expected one MQ-9/AIM-120C effects event")
  if len(events.damage_reports) != 1:
    raise AssertionError("expected one MQ-9/AIM-120C damage report")
  return (
    before,
    _aircraft_damage_overlay(sim, target_id),
    events.effects_events[0],
    events.damage_reports[0],
  )


def _mq9_fuel_mass_state_after_optional_center_fuel_hit(
  *,
  damaged: bool,
  steps: int = 60,
) -> dict[str, object]:
  sim = _kernel_with_unit_overrides([])
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.throttle = 0.65
  sim.set_pilot_action(target_id, pilot)
  for _ in range(5):
    sim.step()

  state: dict[str, object] = {
    "before_overlay": _aircraft_damage_overlay(sim, target_id),
    "before_fuel": [float(value) for value in sim.get_unit_fuel(target_id)],
    "before_mass": [float(value) for value in sim.debug_get_mass_state(target_id)],
    "before_debug": sim.get_flight_dynamics_debug_view(target_id),
    "effect": None,
    "report": None,
  }

  if damaged:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.4,
      0.0,
      0.0,
      _make_warhead_profile("blast_fragmentation", damage=90.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    if not ok:
      raise AssertionError("profiled MQ-9/AIM-120C center fuel hit failed")
    events = sim.export_recent_engagement_events()
    if len(events.effects_events) != 1:
      raise AssertionError("expected one MQ-9/AIM-120C fuel effects event")
    if len(events.damage_reports) != 1:
      raise AssertionError("expected one MQ-9/AIM-120C fuel damage report")
    state["effect"] = events.effects_events[0]
    state["report"] = events.damage_reports[0]

  state.update(
    {
      "hit_overlay": _aircraft_damage_overlay(sim, target_id),
      "hit_fuel": [float(value) for value in sim.get_unit_fuel(target_id)],
      "hit_mass": [float(value) for value in sim.debug_get_mass_state(target_id)],
      "hit_debug": sim.get_flight_dynamics_debug_view(target_id),
    }
  )

  for _ in range(int(steps)):
    sim.step()

  state.update(
    {
      "after_overlay": _aircraft_damage_overlay(sim, target_id),
      "after_fuel": [float(value) for value in sim.get_unit_fuel(target_id)],
      "after_mass": [float(value) for value in sim.debug_get_mass_state(target_id)],
      "after_debug": sim.get_flight_dynamics_debug_view(target_id),
    }
  )
  return state


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


def _assert_mq9_event_is_non_authoritative(testcase: unittest.TestCase, event: object) -> None:
  testcase.assertTrue(bool(event.vulnerability_profile_present))
  testcase.assertTrue(bool(event.vulnerability_profile_synthetic))
  testcase.assertFalse(bool(event.vulnerability_calibrated_evidence))
  testcase.assertFalse(bool(event.vulnerability_pk_authority))
  testcase.assertFalse(bool(event.vulnerability_deterministic_fuze_authority))
  testcase.assertEqual(str(event.vulnerability_calibration_status), "unvalidated")
  testcase.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
  testcase.assertFalse(bool(event.component_failure_probability_calibrated))


def _component_rows_by_name(event: object) -> dict[str, object]:
  return {str(row.component_name): row for row in event.component_mechanism_load_rows}


def _failure_modes_by_name(row: object) -> dict[str, float]:
  return {
    str(name): float(severity)
    for name, severity in zip(
      row.component_failure_mode_names,
      row.component_failure_mode_severities,
    )
  }


def _assert_component_row_exposes_public_failure_modes(
  testcase: unittest.TestCase,
  row: object,
  *,
  expected_any: set[str],
) -> dict[str, float]:
  modes = _failure_modes_by_name(row)
  testcase.assertEqual(
    len(modes),
    len(list(row.component_failure_mode_names)),
    "mode names must stay one-to-one with severities",
  )
  testcase.assertGreater(len(modes), 0)
  testcase.assertIn(str(row.component_failure_primary_mode), modes)
  testcase.assertAlmostEqual(
    float(row.component_failure_primary_mode_severity),
    modes[str(row.component_failure_primary_mode)],
    delta=1.0e-12,
  )
  testcase.assertGreater(
    len(expected_any.intersection(modes)),
    0,
    f"expected at least one of {sorted(expected_any)} in {sorted(modes)}",
  )
  testcase.assertEqual(
    str(row.component_failure_mode_source),
    "synthetic_inferred_part_failure_modes",
  )
  testcase.assertFalse(bool(row.component_failure_mode_authority))
  for mode, severity in modes.items():
    testcase.assertGreater(severity, 0.0, mode)
    testcase.assertLessEqual(severity, 1.0, mode)
  return modes


def _a8_engine_tuned_f16_override() -> dict:
  with open(
    resolve_repo_path(
      "examples",
      "config",
      "database",
      "aircraft",
      "units",
      "f16c_block50.json",
    ),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = "F-16C_A8_EngineTuned"
  unit["engine_tuning"] = {
    "enabled": True,
    "mil_thrust_n": 76310.0,
    "ab_thrust_n": 131000.0,
    "throttle_ab_threshold": 0.9,
    "tau_spool_up_s": 0.4,
    "tau_spool_down_s": 0.3,
    "tsfc_mil_kg_per_nh": 0.76,
    "tsfc_ab_kg_per_nh": 1.90,
  }
  return unit


class A8Mq9Aim120ValidationRuntimeMixin:
  def test_a8_mq9_aim120_near_range_live_chain_records_launch_effect_damage(
    self,
  ) -> None:
    sim, _shooter_id, target_id, missile_id, result, missile_runtime = (
      _launch_and_drive_mq9_case(range_m=8000.0)
    )

    self.assertFalse(bool(result["missile_active"]))
    self.assertTrue(bool(result["target_active"]))
    self.assertTrue(sim.is_unit_active(target_id))
    self.assertLessEqual(float(result["proximity_min_dist_m"]), 15.0)
    self.assertAlmostEqual(
      float(missile_runtime["mass_total_kg"]),
      152.0,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(missile_runtime["max_speed_mps"]),
      1372.0,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(missile_runtime["seeker_lock_range_m"]),
      16000.0,
      delta=1.0e-6,
    )
    self.assertEqual(int(missile_runtime["sensor_type"]), int(ef_py.SensorType.Radar))

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.launch_events), 1)
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)
    effect = events.effects_events[0]
    report = events.damage_reports[0]

    self.assertEqual(int(effect.munition.entity_id), missile_id)
    self.assertEqual(int(effect.target.entity_id), target_id)
    self.assertEqual(str(effect.trigger_type), "proximity_fuze")
    self.assertEqual(str(effect.fuze_type), "radar_proximity")
    self.assertEqual(str(effect.effect_family), "blast_fragmentation")
    self.assertEqual(str(effect.component_primary_name), "right_aileron_servo")
    self.assertEqual(str(effect.component_primary_system), "flight_control")
    self.assertGreaterEqual(int(effect.component_hit_count), 1)
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertLess(float(report.system_health_delta), 0.0)
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    _assert_mq9_event_is_non_authoritative(self, effect)

    overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertLess(overlay["flight_control"], 1.0)
    self.assertLess(overlay["roll_control"], 1.0)
    self.assertLess(overlay["propulsion"], 1.0)
    self.assertLess(overlay["fuel"], 1.0)
    self.assertGreater(overlay["fuel_leak"], 0.0)

  def test_a8_mq9_aim120_longer_range_live_chain_is_auditable_without_lethality_claim(
    self,
  ) -> None:
    sim, _shooter_id, target_id, _missile_id, result, missile_runtime = (
      _launch_and_drive_mq9_case(range_m=14000.0)
    )

    self.assertFalse(bool(result["missile_active"]))
    self.assertTrue(bool(result["target_active"]))
    self.assertGreater(float(result["time_s"]), 8.0)
    self.assertLessEqual(float(result["proximity_min_dist_m"]), 15.0)
    self.assertAlmostEqual(
      float(missile_runtime["max_flight_time_s"]),
      45.0,
      delta=1.0e-6,
    )

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.launch_events), 1)
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)
    effect = events.effects_events[0]
    report = events.damage_reports[0]

    self.assertEqual(str(effect.trigger_type), "proximity_fuze")
    self.assertEqual(str(effect.effect_family), "blast_fragmentation")
    self.assertGreaterEqual(int(effect.component_hit_count), 1)
    self.assertNotEqual(str(effect.component_primary_name), "")
    self.assertGreater(float(effect.miss_distance_m), 0.0)
    self.assertLessEqual(float(effect.miss_distance_m), 15.0)
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertLess(float(report.system_health_delta), 0.0)
    self.assertFalse(bool(report.destroyed))
    self.assertTrue(sim.is_unit_active(target_id))
    _assert_mq9_event_is_non_authoritative(self, effect)

    health_after = [float(value) for value in sim.get_unit_health(target_id)]
    self.assertEqual(health_after, [40.0, 40.0])
    overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertLess(
      min(
        overlay["flight_control"],
        overlay["propulsion"],
        overlay["fuel"],
        overlay["avionics"],
      ),
      1.0,
    )

  def test_a8_mq9_aim120_right_aileron_and_flap_control_hits_are_fixed_component_cases(
    self,
  ) -> None:
    cases = [
      {
        "label": "right_aileron",
        "local": (-0.4, 8.0, 0.0),
        "component": "right_aileron_servo",
        "drops": ("flight_control", "roll_control"),
        "stable": ("pitch_control", "yaw_control"),
        "rises": ("control_asymmetry",),
      },
      {
        "label": "right_flap",
        "local": (-0.2, 2.8, 0.0),
        "component": "right_inboard_flap_servo",
        "drops": ("flight_control", "roll_control", "pitch_control"),
        "stable": ("yaw_control",),
        "rises": ("control_asymmetry",),
      },
    ]

    for case in cases:
      with self.subTest(case=case["label"]):
        before, after, effect, report = _profiled_mq9_aim120_hit(case["local"])
        self.assertTrue(bool(effect.direct_hitbox_intersection))
        self.assertEqual(str(effect.component_primary_name), case["component"])
        self.assertEqual(str(effect.component_primary_system), "flight_control")
        rows_by_name = _component_rows_by_name(effect)
        self.assertIn(case["component"], rows_by_name)
        _assert_component_row_exposes_public_failure_modes(
          self,
          rows_by_name[case["component"]],
          expected_any={
            "cut",
            "blast_deformation",
            "hydraulic_pressure_loss",
          },
        )
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertFalse(bool(report.destroyed))
        _assert_mq9_event_is_non_authoritative(self, effect)

        for field in case["drops"]:
          self.assertLess(after[field], before[field], field)
        for field in case["stable"]:
          self.assertAlmostEqual(after[field], before[field], delta=1.0e-6, msg=field)
        for field in case["rises"]:
          self.assertGreater(after[field], before[field], field)

  def test_a8_mq9_aim120_data_link_and_power_distribution_hits_degrade_mission_path_without_crash(
    self,
  ) -> None:
    cases = [
      {
        "label": "data_link",
        "local": (1.0, 0.0, 0.2),
        "component": "data_link_transceiver",
        "system": "data_link",
        "drops": ("avionics", "mission_crew", "command_navigation"),
      },
      {
        "label": "power_distribution",
        "local": (-1.8, 0.0, 0.2),
        "component": "power_distribution_unit",
        "system": "avionics",
        "drops": ("avionics", "flight_control", "command_navigation"),
      },
    ]

    for case in cases:
      with self.subTest(case=case["label"]):
        before, after, effect, report = _profiled_mq9_aim120_hit(case["local"])
        self.assertTrue(bool(effect.direct_hitbox_intersection))
        self.assertEqual(str(effect.component_primary_name), case["component"])
        self.assertEqual(str(effect.component_primary_system), case["system"])
        self.assertGreaterEqual(int(effect.component_hit_count), 1)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertNotEqual(str(report.loss_state_to), "lost")
        _assert_mq9_event_is_non_authoritative(self, effect)

        for field in case["drops"]:
          self.assertLess(after[field], before[field], field)

  def test_a8_mq9_aim120_center_fuel_hit_continues_into_leak_and_mass_runtime_path(
    self,
  ) -> None:
    baseline = _mq9_fuel_mass_state_after_optional_center_fuel_hit(damaged=False)
    damaged = _mq9_fuel_mass_state_after_optional_center_fuel_hit(damaged=True)

    effect = damaged["effect"]
    report = damaged["report"]
    self.assertIsNotNone(effect)
    self.assertIsNotNone(report)
    assert effect is not None
    assert report is not None

    self.assertTrue(bool(effect.direct_hitbox_intersection))
    self.assertEqual(str(effect.component_primary_name), "center_fuel_cell")
    self.assertEqual(str(effect.component_primary_system), "fuel")
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))
    self.assertFalse(bool(report.forced_landing))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    _assert_mq9_event_is_non_authoritative(self, effect)

    rows_by_name = _component_rows_by_name(effect)
    self.assertIn("center_fuel_cell", rows_by_name)
    modes = _assert_component_row_exposes_public_failure_modes(
      self,
      rows_by_name["center_fuel_cell"],
      expected_any={"puncture", "fuel_leak", "fire_source"},
    )
    self.assertIn("fuel_leak", modes)
    self.assertIn("fire_source", modes)

    hit_overlay = damaged["hit_overlay"]
    before_overlay = damaged["before_overlay"]
    self.assertLess(hit_overlay["fuel"], before_overlay["fuel"])
    self.assertGreater(hit_overlay["fuel_leak"], before_overlay["fuel_leak"])
    self.assertGreater(hit_overlay["fire"], before_overlay["fire"])
    self.assertGreater(hit_overlay["flammable_fluid"], before_overlay["flammable_fluid"])

    # The shot record names the damage path; maintained runtime systems drain mass later.
    self.assertAlmostEqual(damaged["hit_fuel"][0], damaged["before_fuel"][0], delta=1.0e-6)
    self.assertAlmostEqual(damaged["hit_mass"][1], damaged["before_mass"][1], delta=1.0e-6)
    self.assertAlmostEqual(float(damaged["hit_debug"].fuel_leak_rate_kg_s), 0.0, delta=1.0e-9)

    baseline_fuel_loss = baseline["before_fuel"][0] - baseline["after_fuel"][0]
    damaged_fuel_loss = damaged["before_fuel"][0] - damaged["after_fuel"][0]
    self.assertGreater(damaged_fuel_loss, baseline_fuel_loss + 2.0)
    self.assertGreater(float(damaged["after_debug"].fuel_leak_rate_kg_s), 1.0)
    self.assertAlmostEqual(float(baseline["after_debug"].fuel_leak_rate_kg_s), 0.0, delta=1.0e-9)
    self.assertLess(damaged["after_fuel"][0], baseline["after_fuel"][0] - 2.0)
    self.assertLess(damaged["after_mass"][3], baseline["after_mass"][3] - 2.0)
    self.assertAlmostEqual(damaged["after_mass"][1], damaged["after_fuel"][0], delta=1.0e-6)
    self.assertAlmostEqual(damaged["after_mass"][3], damaged["after_mass"][5], delta=1.0e-6)

  def test_a8_ground_contact_lifecycle_keeps_safe_runway_contact_observable(
    self,
  ) -> None:
    sim = _kernel_with_unit_overrides([])
    sim.clear_zones()
    sim.add_zone("a8_runway", 0.0, 0.0, 200.0, 2000.0, 0.0, 0)
    target_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        "MQ-9_Reaper",
        0.0,
        0.0,
        1.4,
        0.0,
        0.0,
        0.0,
        0.0,
        7.0,
        -0.5,
      )
    )

    sim.step()
    state = _ground_contact_state(sim, target_id)

    self.assertTrue(bool(sim.is_unit_active(target_id)))
    self.assertTrue(bool(state["on_ground"]))
    self.assertTrue(bool(state["on_runway"]))
    self.assertEqual(int(state["lifecycle"]), 1)
    self.assertFalse(bool(state["gear_collapsed"]))
    self.assertEqual([float(value) for value in sim.get_unit_health(target_id)], [40.0, 40.0])

  def test_a8_ground_contact_lifecycle_records_crashed_wreck_without_disappearance(
    self,
  ) -> None:
    sim = _kernel_with_unit_overrides([])
    sim.clear_zones()
    target_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        "MQ-9_Reaper",
        5000.0,
        5000.0,
        1.2,
        0.0,
        0.0,
        0.0,
        0.0,
        58.0,
        -6.0,
      )
    )

    sim.step()
    state = _ground_contact_state(sim, target_id)

    self.assertTrue(bool(sim.is_unit_active(target_id)))
    self.assertTrue(bool(state["on_ground"]))
    self.assertFalse(bool(state["on_runway"]))
    self.assertEqual(int(state["lifecycle"]), 2)
    self.assertGreater(float(state["impact_horizontal_speed"]), 45.0)
    self.assertGreater(float(state["impact_severity"]), 1.0)
    self.assertEqual([float(value) for value in sim.get_unit_health(target_id)], [40.0, 40.0])

  def test_a8_ground_contact_lifecycle_does_not_turn_low_speed_contact_into_crash(
    self,
  ) -> None:
    sim = _kernel_with_unit_overrides([])
    sim.clear_zones()
    target_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        "MQ-9_Reaper",
        7000.0,
        7000.0,
        1.4,
        0.0,
        0.0,
        0.0,
        0.0,
        4.0,
        -0.4,
      )
    )

    sim.step()
    state = _ground_contact_state(sim, target_id)

    self.assertTrue(bool(sim.is_unit_active(target_id)))
    self.assertTrue(bool(state["on_ground"]))
    self.assertEqual(int(state["lifecycle"]), 1)
    self.assertNotEqual(int(state["lifecycle"]), 2)
    self.assertLess(float(state["impact_severity"]), 1.0)
    self.assertEqual([float(value) for value in sim.get_unit_health(target_id)], [40.0, 40.0])

  def test_a8_mq9_aim120_explicit_non_authority_guard_for_fixture_and_events(
    self,
  ) -> None:
    with open(
      resolve_repo_path(
        "examples",
        "config",
        "database",
        "aircraft",
        "units",
        "mq9_reaper.json",
      ),
      "r",
      encoding="utf-8",
    ) as handle:
      mq9 = json.load(handle)
    vulnerability = mq9["damage_model"]["vulnerability"]
    self.assertTrue(bool(vulnerability["synthetic"]))
    self.assertFalse(bool(vulnerability["calibrated"]))
    self.assertFalse(bool(vulnerability["pk_authority"]))
    self.assertFalse(bool(vulnerability["deterministic_fuze_authority"]))
    self.assertEqual(str(vulnerability["calibration_status"]), "unvalidated")

    sim = _kernel_with_unit_overrides([])
    _attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")
    evidence = [
      float(value)
      for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
    ]
    authority = [
      float(value)
      for value in sim.debug_get_aircraft_vulnerability_authority_state(target_id)
    ]
    self.assertEqual(evidence, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    self.assertEqual(authority, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    _before, _after, effect, _report = _profiled_mq9_aim120_hit((-4.4, 0.0, 0.0))
    _assert_mq9_event_is_non_authoritative(self, effect)

  def test_a8_mq9_aim120_public_failure_mode_rows_are_non_authoritative(self) -> None:
    _before, _after, effect, report = _profiled_mq9_aim120_hit((-0.4, 8.0, 0.0))
    self.assertEqual(str(effect.component_primary_name), "right_aileron_servo")
    self.assertEqual(str(effect.component_primary_system), "flight_control")
    self.assertFalse(bool(report.destroyed))
    _assert_mq9_event_is_non_authoritative(self, effect)

    rows_by_name = _component_rows_by_name(effect)
    self.assertIn("right_aileron_servo", rows_by_name)
    modes = _assert_component_row_exposes_public_failure_modes(
      self,
      rows_by_name["right_aileron_servo"],
      expected_any={
        "cut",
        "blast_deformation",
        "hydraulic_pressure_loss",
      },
    )
    self.assertNotIn("fuel_leak", modes)

  def test_a8_engine_damage_scales_actual_thrust_with_explicit_engine_tuning(self) -> None:
    sim = _kernel_with_unit_overrides([_a8_engine_tuned_f16_override()])
    attacker_id, target_id = _spawn_attacker_and_named_target(
      sim,
      "F-16C_A8_EngineTuned",
    )
    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.throttle = 1.0
    sim.set_pilot_action(target_id, pilot)
    for _ in range(120):
      sim.step()

    before = sim.get_flight_dynamics_debug_view(target_id)
    self.assertGreater(float(before.current_thrust_n), 10000.0)
    self.assertAlmostEqual(float(before.mil_thrust_n), 76310.0, delta=1.0)

    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -5.8,
      0.0,
      0.0,
      _make_warhead_profile("blast_fragmentation", damage=140.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    self.assertTrue(bool(ok))
    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    effect = events.effects_events[0]
    self.assertEqual(str(effect.component_primary_name), "engine_core")
    self.assertEqual(str(effect.component_primary_system), "engine")

    overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertLess(overlay["propulsion"], 1.0)
    for _ in range(8):
      sim.step()

    after = sim.get_flight_dynamics_debug_view(target_id)
    self.assertLess(float(after.mil_thrust_n), float(before.mil_thrust_n))
    self.assertLess(float(after.current_thrust_n), float(before.current_thrust_n) * 0.80)
