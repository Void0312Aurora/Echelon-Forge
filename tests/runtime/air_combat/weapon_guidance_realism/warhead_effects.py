from __future__ import annotations

from .helpers import *


class WarheadEffectsRuntimeMixin:
  def test_global_warhead_profile_override_flows_into_runtime_and_effects_event(self) -> None:
    sim = _make_baseline_kernel()

    profile = ef_py.WarheadProfile()
    profile.family = "continuous_rod"
    profile.mass_kg = 12.5
    profile.lethal_radius_m = 35.0
    profile.damage_scalar = 77.0
    profile.synthetic = False
    profile.damage_scalar_synthetic = False
    profile.provenance = "test_authored_profile"

    tuning = sim.get_missile_tuning()
    tuning.warhead_profile = profile
    tuning.has_warhead_profile = True
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
    self.assertAlmostEqual(float(runtime["damage"]), 77.0, delta=1.0e-6)
    self.assertEqual(str(runtime["warhead_family"]), "continuous_rod")
    self.assertAlmostEqual(float(runtime["warhead_mass_kg"]), 12.5, delta=1.0e-6)
    self.assertFalse(bool(runtime["warhead_profile_synthetic"]))
    self.assertFalse(bool(runtime["warhead_damage_scalar_synthetic"]))

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
    self.assertEqual(str(effects.effect_family), "continuous_rod")
    self.assertAlmostEqual(float(effects.warhead_mass_kg), 12.5, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.warhead_lethal_radius_m), 35.0, delta=1.0e-6)
    self.assertFalse(bool(effects.warhead_profile_synthetic))
    self.assertFalse(bool(effects.damage_scalar_synthetic))
    self.assertEqual(str(effects.fuze_type), "proximity")
    self.assertAlmostEqual(float(effects.fuze_trigger_radius_m), 35.0, delta=1.0e-6)
    self.assertTrue(bool(effects.fuze_profile_synthetic))

  def test_a8_shot_effect_record_links_fuze_geometry_warhead_part_entry_and_consequence_hook(self) -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(20260607)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_structured_f16_pair(sim)

    local = (-0.8, 4.1, 0.0)
    missile_velocity = (900.0, -250.0, 0.0)
    profile = _make_warhead_profile(
      "blast_fragmentation",
      damage=90.0,
      radius=35.0,
    )
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      float(local[0]),
      float(local[1]),
      float(local[2]),
      profile,
      float(missile_velocity[0]),
      float(missile_velocity[1]),
      float(missile_velocity[2]),
    )
    self.assertTrue(bool(ok))

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    self.assertEqual(len(events.damage_reports), 1)
    effects = events.effects_events[0]
    report = events.damage_reports[0]
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

    self.assertEqual(str(effects.trigger_type), "debug_profiled_local_proximity_hit")
    self.assertEqual(str(effects.outcome_state), "hit")
    self.assertEqual(str(effects.fuze_type), "proximity")
    self.assertAlmostEqual(float(effects.fuze_trigger_radius_m), 35.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.fuze_effective_reliability), 1.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_local_forward_m), local[0], delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_local_right_m), local[1], delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_local_up_m), local[2], delta=1.0e-6)
    self.assertAlmostEqual(
      float(effects.miss_distance_m),
      math.sqrt(local[0] ** 2 + local[1] ** 2 + local[2] ** 2),
      delta=1.0e-6,
    )
    self.assertGreater(float(effects.closure_mps), 0.0)

    self.assertEqual(str(effects.effect_family), "blast_fragmentation")
    self.assertAlmostEqual(float(effects.warhead_mass_kg), 12.0, delta=1.0e-6)
    self.assertFalse(bool(effects.warhead_profile_synthetic))
    self.assertFalse(bool(effects.damage_scalar_synthetic))
    self.assertTrue(bool(effects.direct_hitbox_intersection))
    self.assertGreater(float(effects.mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(effects.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(float(effects.mechanism_blast_impulse_kpa_ms), 0.0)
    self.assertGreater(int(effects.warhead_spatial_sample_count), 0)

    self.assertEqual(str(effects.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(effects.component_primary_system), "flight_control")
    self.assertGreater(float(effects.component_failure_probability), 0.0)
    self.assertEqual(str(effects.component_failure_probability_source), "synthetic_sigmoid")
    self.assertFalse(bool(effects.component_failure_probability_calibrated))
    self.assertGreater(int(effects.component_failure_count), 0)
    self.assertLess(float(effects.component_primary_integrity), 1.0)
    self.assertGreater(float(effects.component_primary_mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(effects.component_primary_mechanism_blast_overpressure_kpa), 0.0)

    rows = list(effects.component_mechanism_load_rows)
    self.assertEqual(len(rows), int(effects.component_hit_count))
    primary_row = next(
      (
        row
        for row in rows
        if str(row.component_name) == str(effects.component_primary_name)
      ),
      None,
    )
    self.assertIsNotNone(primary_row)
    assert primary_row is not None
    self.assertEqual(str(primary_row.component_system), str(effects.component_primary_system))
    self.assertTrue(bool(primary_row.direct_hit))
    self.assertGreater(float(primary_row.component_failure_probability), 0.0)
    self.assertEqual(str(primary_row.component_failure_probability_source), "synthetic_sigmoid")
    self.assertFalse(bool(primary_row.component_failure_probability_authority))
    self.assertEqual(str(primary_row.component_failure_probability_weapon_family), "blast_fragmentation")
    self.assertGreater(float(primary_row.mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(primary_row.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(int(primary_row.component_dependency_propagation_count), 0)
    self.assertNotEqual(str(primary_row.component_dependency_target_system), "")

    self.assertEqual(int(report.source_event_id), int(effects.event_id))
    self.assertLess(float(report.system_health_delta), 0.0)
    self.assertIn("mission=", str(report.platform_damage_state_delta))
    self.assertIn("mobility=", str(report.platform_damage_state_delta))
    self.assertIn("sensor=", str(report.platform_damage_state_delta))
    self.assertIn("survivability=", str(report.platform_damage_state_delta))
    self.assertFalse(bool(report.destroyed))
    self.assertNotEqual(str(report.loss_state_to), "lost")
    self.assertEqual(int(damage_trace.damage_report_id), int(report.report_id))

  def test_phase3_warhead_family_changes_structured_air_effect_distribution(self) -> None:
    fuselage = (0.0, 0.0, 0.3)
    wing = (-0.753, 4.0, 0.0)
    nose = (6.024, 0.0, 0.0)

    blast_fragmentation_fuselage, baseline_event = _profiled_local_hit_damage_state(
      "blast_fragmentation",
      fuselage,
    )
    blast_fuselage, blast_event = _profiled_local_hit_damage_state("blast", fuselage)
    self.assertEqual(str(baseline_event.effect_family), "blast_fragmentation")
    self.assertEqual(str(blast_event.effect_family), "blast")
    self.assertFalse(bool(blast_event.warhead_profile_synthetic))
    self.assertFalse(bool(blast_event.damage_scalar_synthetic))
    self.assertGreater(float(blast_event.component_threshold_scale), 1.0)
    self.assertLess(blast_fuselage[3], blast_fragmentation_fuselage[3])

    blast_fragmentation_wing, _ = _profiled_local_hit_damage_state(
      "blast_fragmentation",
      wing,
    )
    continuous_rod_wing, continuous_event = _profiled_local_hit_damage_state(
      "continuous_rod",
      wing,
    )
    self.assertEqual(str(continuous_event.effect_family), "continuous_rod")
    self.assertGreater(float(continuous_event.component_threshold_scale), 1.0)
    self.assertLess(continuous_rod_wing[1], blast_fragmentation_wing[1])

    blast_fragmentation_nose, _ = _profiled_local_hit_damage_state(
      "blast_fragmentation",
      nose,
      damage=60.0,
    )
    hit_to_kill_nose, hit_to_kill_event = _profiled_local_hit_damage_state(
      "hit_to_kill",
      nose,
      damage=60.0,
    )
    self.assertEqual(str(hit_to_kill_event.effect_family), "hit_to_kill")
    self.assertGreater(float(hit_to_kill_event.component_threshold_scale), 1.0)
    self.assertLess(hit_to_kill_nose[0], blast_fragmentation_nose[0])
    self.assertLess(hit_to_kill_nose[2], blast_fragmentation_nose[2])

  def test_phase3_proximity_field_projects_near_miss_onto_nearest_air_hitbox(self) -> None:
    direct_wing_overlay, direct_damage, _ = _profiled_local_hit_overlay(
      "blast_fragmentation",
      (-0.753, 4.0, 0.0),
      damage=90.0,
      radius=25.0,
    )
    near_wing_overlay, near_damage, near_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      (-0.753, 7.1, 0.0),
      damage=90.0,
      radius=25.0,
    )
    far_overlay, far_damage, far_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      (-0.753, 20.0, 0.0),
      damage=90.0,
      radius=25.0,
    )

    self.assertEqual(str(near_event.effect_family), "blast_fragmentation")
    self.assertAlmostEqual(float(near_event.miss_distance_m), math.hypot(-0.753, 7.1), delta=1.0e-6)
    self.assertAlmostEqual(float(near_event.detonation_local_forward_m), -0.753, delta=1.0e-6)
    self.assertAlmostEqual(float(near_event.detonation_local_right_m), 7.1, delta=1.0e-6)
    self.assertAlmostEqual(float(near_event.detonation_local_up_m), 0.0, delta=1.0e-6)
    self.assertFalse(bool(near_event.direct_hitbox_intersection))
    self.assertGreater(int(near_event.projected_hitbox_count), 0)
    self.assertGreater(float(near_event.spatial_effect_scale), 0.0)
    self.assertLess(float(near_event.spatial_effect_scale), 1.0)
    self.assertGreater(float(near_event.mechanism_effect_scale), 0.0)
    self.assertLessEqual(float(near_event.mechanism_effect_scale), 1.10)
    self.assertGreater(int(near_event.warhead_spatial_sample_count), 100)
    self.assertGreater(float(near_event.warhead_spatial_hit_estimate), 0.0)
    self.assertGreater(float(near_event.warhead_spatial_energy_scale), 0.0)
    self.assertLess(near_wing_overlay["structure"], 1.0)
    self.assertLess(near_wing_overlay["flight_control"], 1.0)
    self.assertLess(near_wing_overlay["hydraulic"], 1.0)
    self.assertLess(near_wing_overlay["fuel"], 1.0)
    self.assertGreater(near_wing_overlay["fuel_leak"], 0.0)
    self.assertGreater(min(far_damage), 0.99)
    self.assertAlmostEqual(far_overlay["structure"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(far_overlay["flight_control"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(far_overlay["fuel"], 1.0, delta=1.0e-6)
    self.assertEqual(str(far_event.effect_family), "blast_fragmentation")

    self.assertGreater(near_wing_overlay["structure"], direct_wing_overlay["structure"])
    self.assertGreater(near_wing_overlay["flight_control"], direct_wing_overlay["flight_control"])
    self.assertGreater(near_damage[1], direct_damage[1])

  def test_phase3_spatial_projection_respects_warhead_family_footprint(self) -> None:
    near_wing = (-0.753, 7.1, 0.0)
    blast_fragmentation_overlay, _, blast_fragmentation_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      near_wing,
      damage=90.0,
      radius=35.0,
    )
    hit_to_kill_overlay, _, hit_to_kill_event = _profiled_local_hit_overlay(
      "hit_to_kill",
      near_wing,
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(blast_fragmentation_event.effect_family), "blast_fragmentation")
    self.assertEqual(str(hit_to_kill_event.effect_family), "hit_to_kill")
    self.assertFalse(bool(blast_fragmentation_event.direct_hitbox_intersection))
    self.assertEqual(int(blast_fragmentation_event.projected_hitbox_count), 3)
    self.assertFalse(bool(hit_to_kill_event.direct_hitbox_intersection))
    self.assertEqual(int(hit_to_kill_event.projected_hitbox_count), 1)

    self.assertLess(blast_fragmentation_overlay["flight_control"], 1.0)
    self.assertLess(blast_fragmentation_overlay["hydraulic"], 1.0)
    self.assertLess(blast_fragmentation_overlay["fuel"], 1.0)
    self.assertLess(blast_fragmentation_overlay["propulsion"], 1.0)
    self.assertLess(blast_fragmentation_overlay["avionics"], 1.0)
    self.assertAlmostEqual(blast_fragmentation_overlay["crew"], 1.0, delta=1.0e-6)

    self.assertLess(hit_to_kill_overlay["flight_control"], 1.0)
    self.assertLess(hit_to_kill_overlay["hydraulic"], 1.0)
    self.assertAlmostEqual(hit_to_kill_overlay["fuel"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(hit_to_kill_overlay["propulsion"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(hit_to_kill_overlay["avionics"], 1.0, delta=1.0e-6)
    self.assertAlmostEqual(hit_to_kill_overlay["crew"], 1.0, delta=1.0e-6)

  def test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor(self) -> None:
    low_armor_name = "F-16C_A2_LowArmor_Test"
    high_armor_name = "F-16C_A2_HighArmor_Test"
    overrides = [
      _make_f16_armor_override(low_armor_name, wing_armor_mm=1.0),
      _make_f16_armor_override(high_armor_name, wing_armor_mm=80.0),
    ]

    low_armor_overlay, low_armor_damage, low_event = _profiled_local_hit_overlay_for_target(
      low_armor_name,
      "blast_fragmentation",
      (-0.753, 4.0, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )
    high_armor_overlay, high_armor_damage, high_event = _profiled_local_hit_overlay_for_target(
      high_armor_name,
      "blast_fragmentation",
      (-0.753, 4.0, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertEqual(str(low_event.effect_family), "blast_fragmentation")
    self.assertEqual(str(high_event.effect_family), "blast_fragmentation")
    self.assertAlmostEqual(float(low_event.miss_distance_m), float(high_event.miss_distance_m), delta=1.0e-6)
    self.assertTrue(bool(low_event.direct_hitbox_intersection))
    self.assertTrue(bool(high_event.direct_hitbox_intersection))
    self.assertGreater(
      float(low_event.mechanism_armor_scale),
      float(high_event.mechanism_armor_scale),
    )
    self.assertGreater(
      float(low_event.mechanism_effect_scale),
      float(high_event.mechanism_effect_scale),
    )
    self.assertLess(low_armor_overlay["flight_control"], high_armor_overlay["flight_control"])
    self.assertLess(low_armor_overlay["hydraulic"], high_armor_overlay["hydraulic"])
    self.assertLess(low_armor_overlay["structure"], high_armor_overlay["structure"])
    self.assertLess(low_armor_damage[1], high_armor_damage[1])

  def test_phase3_mechanism_load_tracks_target_geometry_intercept_scale(self) -> None:
    narrow_name = "F-16C_A2_NarrowWing_Test"
    wide_name = "F-16C_A2_WideWing_Test"
    overrides = [
      _make_f16_wing_only_geometry_override(narrow_name, wing_width_m=7.0),
      _make_f16_wing_only_geometry_override(wide_name, wing_width_m=12.4),
    ]
    narrow_local = (-0.8, 4.6, 0.0)
    wide_local = (-0.8, 7.3, 0.0)
    _narrow_overlay, _, narrow_event = _profiled_local_hit_overlay_for_target(
      narrow_name,
      "blast_fragmentation",
      narrow_local,
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )
    _wide_overlay, _, wide_event = _profiled_local_hit_overlay_for_target(
      wide_name,
      "blast_fragmentation",
      wide_local,
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertFalse(bool(narrow_event.direct_hitbox_intersection))
    self.assertFalse(bool(wide_event.direct_hitbox_intersection))
    self.assertGreater(int(narrow_event.projected_hitbox_count), 0)
    self.assertGreater(int(wide_event.projected_hitbox_count), 0)
    self.assertGreater(
      float(wide_event.mechanism_fragment_areal_density_per_m2),
      float(narrow_event.mechanism_fragment_areal_density_per_m2),
    )
    self.assertGreater(
      float(wide_event.mechanism_blast_impulse_kpa_ms),
      float(narrow_event.mechanism_blast_impulse_kpa_ms),
    )
    self.assertGreater(int(narrow_event.component_hit_count), 0)
    self.assertGreater(int(wide_event.component_hit_count), 0)

  def test_phase3_blast_fragmentation_mechanism_load_tracks_closure_intercept_scale(self) -> None:
    wing = (-0.753, 7.1, 0.0)
    _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      wing,
      (300.0, -83.3, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      wing,
      (1200.0, -333.3, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertFalse(bool(low_event.direct_hitbox_intersection))
    self.assertFalse(bool(high_event.direct_hitbox_intersection))
    self.assertGreater(float(high_event.closure_mps), float(low_event.closure_mps))
    self.assertGreater(
      float(high_event.mechanism_fragment_energy_j),
      float(low_event.mechanism_fragment_energy_j),
    )
    self.assertGreater(
      float(high_event.mechanism_fragment_areal_density_per_m2),
      float(low_event.mechanism_fragment_areal_density_per_m2),
    )
    self.assertGreater(
      float(high_event.mechanism_blast_impulse_kpa_ms),
      float(low_event.mechanism_blast_impulse_kpa_ms),
    )
    self.assertGreater(
      float(high_event.component_failure_probability),
      float(low_event.component_failure_probability),
    )

  def test_phase3_continuous_rod_near_miss_uses_relative_velocity_axis(self) -> None:
    near_wing = (-0.753, 7.1, 0.0)
    broadside_sweep = _profiled_local_hit_overlay_with_velocity(
      "continuous_rod",
      near_wing,
      (0.0, -900.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    axial_pass = _profiled_local_hit_overlay_with_velocity(
      "continuous_rod",
      near_wing,
      (-900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    blast_fragmentation_broadside = _profiled_local_hit_overlay_with_velocity(
      "blast_fragmentation",
      near_wing,
      (0.0, -900.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    blast_fragmentation_axial = _profiled_local_hit_overlay_with_velocity(
      "blast_fragmentation",
      near_wing,
      (-900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertLess(broadside_sweep["flight_control"], axial_pass["flight_control"])
    self.assertLess(broadside_sweep["hydraulic"], axial_pass["hydraulic"])
    self.assertLess(broadside_sweep["structure"], axial_pass["structure"])
    self.assertLess(
      abs(blast_fragmentation_broadside["flight_control"] - blast_fragmentation_axial["flight_control"]),
      abs(broadside_sweep["flight_control"] - axial_pass["flight_control"]),
    )

  def test_phase3_surface_incidence_cos_reports_obliquity_evidence(self) -> None:
    normal_side = (-0.8, 4.49, 0.0)
    oblique_side = (-0.36, 4.1, 0.0)
    _normal_overlay, normal_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      normal_side,
      (900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _oblique_overlay, oblique_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      oblique_side,
      (900.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _invalid_overlay, invalid_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      normal_side,
      (0.0, 0.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertGreater(float(normal_event.mechanism_surface_incidence_cos), 0.5)
    self.assertLess(float(oblique_event.mechanism_surface_incidence_cos), 0.5)
    self.assertAlmostEqual(float(invalid_event.mechanism_surface_incidence_cos), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(
      float(normal_event.component_primary_mechanism_surface_incidence_cos),
      float(normal_event.mechanism_surface_incidence_cos),
      delta=1.0e-6,
    )
    normal_rows = list(normal_event.component_mechanism_load_rows)
    self.assertGreater(len(normal_rows), 0)
    self.assertGreaterEqual(
      min(float(row.mechanism_surface_incidence_cos) for row in normal_rows),
      0.0,
    )
    self.assertLessEqual(
      max(float(row.mechanism_surface_incidence_cos) for row in normal_rows),
      1.0,
    )

  def test_phase3_warhead_spatial_sampling_reports_fragment_and_rod_evidence(self) -> None:
    near_wing = (-0.753, 7.1, 0.0)
    _blast_overlay, _, blast_event = _profiled_local_hit_overlay(
      "blast_fragmentation",
      near_wing,
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(blast_event.effect_family), "blast_fragmentation")
    self.assertGreater(int(blast_event.warhead_spatial_sample_count), 100)
    self.assertGreater(float(blast_event.warhead_spatial_hit_estimate), 0.0)
    self.assertLess(float(blast_event.warhead_spatial_hit_fraction), 0.10)
    self.assertGreater(float(blast_event.warhead_spatial_energy_scale), 0.0)
    self.assertGreater(float(blast_event.mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(blast_event.mechanism_penetration_margin), 0.0)
    self.assertGreater(float(blast_event.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(float(blast_event.mechanism_blast_impulse_kpa_ms), 0.0)

    sim = ef_py.SimulationKernel()
    sim.reset(20260526)
    self.assertTrue(sim.load_database(_DB_PATH))
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    rod_profile = _make_warhead_profile("continuous_rod", damage=90.0, radius=35.0)

    self.assertTrue(
      bool(
        sim.debug_apply_profiled_local_proximity_hit_with_velocity(
          attacker_id,
          target_id,
          near_wing[0],
          near_wing[1],
          near_wing[2],
          rod_profile,
          0.0,
          -900.0,
          0.0,
        )
      )
    )
    broadside_event = sim.export_recent_engagement_events().effects_events[-1]

    self.assertTrue(
      bool(
        sim.debug_apply_profiled_local_proximity_hit_with_velocity(
          attacker_id,
          target_id,
          near_wing[0],
          near_wing[1],
          near_wing[2],
          rod_profile,
          -900.0,
          0.0,
          0.0,
        )
      )
    )
    axial_event = sim.export_recent_engagement_events().effects_events[-1]

    self.assertEqual(str(broadside_event.effect_family), "continuous_rod")
    self.assertGreater(int(broadside_event.warhead_spatial_sample_count), 20)
    self.assertGreater(
      float(broadside_event.warhead_spatial_pattern_scale),
      float(axial_event.warhead_spatial_pattern_scale),
    )
    self.assertGreater(
      float(broadside_event.warhead_spatial_hit_estimate),
      float(axial_event.warhead_spatial_hit_estimate),
    )
    self.assertGreater(float(broadside_event.mechanism_rod_cut_margin), 0.0)
    self.assertGreater(
      float(broadside_event.mechanism_rod_cut_margin),
      float(axial_event.mechanism_rod_cut_margin),
    )

  def test_phase3_warhead_mechanism_load_evidence_tracks_mechanism_family(self) -> None:
    direct_wing = (-0.8, 4.1, 0.0)
    _blast_overlay, blast_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast",
      direct_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _frag_overlay, frag_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      direct_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _rod_overlay, rod_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      direct_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(blast_event.effect_family), "blast")
    self.assertGreater(float(blast_event.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(float(blast_event.mechanism_blast_impulse_kpa_ms), 0.0)
    self.assertGreater(float(blast_event.mechanism_blast_scaled_distance_m_kg13), 0.0)
    self.assertAlmostEqual(float(blast_event.mechanism_fragment_energy_j), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(blast_event.mechanism_rod_cut_margin), 0.0, delta=1.0e-6)

    self.assertEqual(str(frag_event.effect_family), "blast_fragmentation")
    self.assertGreater(float(frag_event.mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(frag_event.mechanism_fragment_areal_density_per_m2), 0.0)
    self.assertGreater(float(frag_event.mechanism_penetration_margin), 0.0)
    self.assertGreater(float(frag_event.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(float(frag_event.mechanism_blast_scaled_distance_m_kg13), 0.0)

    self.assertEqual(str(rod_event.effect_family), "continuous_rod")
    self.assertGreater(float(rod_event.mechanism_rod_cut_margin), 0.0)
    self.assertGreater(float(rod_event.mechanism_penetration_margin), 0.0)
    self.assertAlmostEqual(float(rod_event.mechanism_blast_overpressure_kpa), 0.0, delta=1.0e-6)

  def test_phase3_blast_scaled_distance_tracks_standoff_and_pressure(self) -> None:
    near_wing = (-0.753, 6.0, 0.0)
    far_wing = (-0.753, 10.0, 0.0)
    _near_overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast",
      near_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast",
      far_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertGreater(float(near_event.mechanism_blast_scaled_distance_m_kg13), 0.0)
    self.assertGreater(
      float(far_event.mechanism_blast_scaled_distance_m_kg13),
      float(near_event.mechanism_blast_scaled_distance_m_kg13),
    )
    self.assertLess(
      float(far_event.mechanism_blast_overpressure_kpa),
      float(near_event.mechanism_blast_overpressure_kpa),
    )
    self.assertLess(
      float(far_event.mechanism_blast_impulse_kpa_ms),
      float(near_event.mechanism_blast_impulse_kpa_ms),
    )

  def test_phase3_fragment_areal_density_tracks_standoff(self) -> None:
    near_wing = (-0.753, 6.0, 0.0)
    far_wing = (-0.753, 10.0, 0.0)
    _near_overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      near_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      far_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertGreater(float(near_event.mechanism_fragment_areal_density_per_m2), 0.0)
    self.assertLess(
      float(far_event.mechanism_fragment_areal_density_per_m2),
      float(near_event.mechanism_fragment_areal_density_per_m2),
    )
    self.assertLess(
      float(far_event.warhead_spatial_hit_estimate),
      float(near_event.warhead_spatial_hit_estimate),
    )

  def test_phase3_mechanism_load_tracks_authored_damage_scalar_when_mass_is_fixed(self) -> None:
    local = (-0.753, 6.0, 0.0)
    missile_velocity = (900.0, -250.0, 0.0)
    _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      local,
      missile_velocity,
      damage=30.0,
      radius=35.0,
    )
    _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      local,
      missile_velocity,
      damage=180.0,
      radius=35.0,
    )

    self.assertAlmostEqual(float(low_event.warhead_mass_kg), 12.0, delta=1.0e-6)
    self.assertAlmostEqual(float(high_event.warhead_mass_kg), 12.0, delta=1.0e-6)
    self.assertGreater(
      float(high_event.mechanism_fragment_energy_j),
      float(low_event.mechanism_fragment_energy_j),
    )
    self.assertGreater(
      float(high_event.mechanism_fragment_areal_density_per_m2),
      float(low_event.mechanism_fragment_areal_density_per_m2),
    )
    self.assertLess(
      float(high_event.mechanism_blast_scaled_distance_m_kg13),
      float(low_event.mechanism_blast_scaled_distance_m_kg13),
    )
    self.assertGreater(
      float(high_event.mechanism_blast_overpressure_kpa),
      float(low_event.mechanism_blast_overpressure_kpa),
    )
    self.assertGreater(
      float(high_event.component_failure_probability),
      float(low_event.component_failure_probability),
    )

  def test_phase3_mechanism_load_keeps_authored_mass_anchor_when_damage_scalar_is_synthetic(self) -> None:
    local = (-0.753, 6.0, 0.0)
    velocity = (900.0, -250.0, 0.0)

    def run_case(damage: float) -> object:
      sim = ef_py.SimulationKernel()
      sim.reset(20260526)
      if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
      attacker_id, target_id = _spawn_structured_f16_pair(sim)
      profile = _make_warhead_profile(
        "blast_fragmentation",
        damage=damage,
        radius=35.0,
        mass_kg=12.0,
        damage_scalar_synthetic=True,
      )
      ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        float(local[0]),
        float(local[1]),
        float(local[2]),
        profile,
        float(velocity[0]),
        float(velocity[1]),
        float(velocity[2]),
      )
      self.assertTrue(bool(ok))
      return sim.export_recent_engagement_events().effects_events[-1]

    low_event = run_case(30.0)
    high_event = run_case(180.0)

    self.assertAlmostEqual(
      float(high_event.mechanism_fragment_energy_j),
      float(low_event.mechanism_fragment_energy_j),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(high_event.mechanism_fragment_areal_density_per_m2),
      float(low_event.mechanism_fragment_areal_density_per_m2),
      delta=1.0e-9,
    )
    self.assertAlmostEqual(
      float(high_event.mechanism_blast_scaled_distance_m_kg13),
      float(low_event.mechanism_blast_scaled_distance_m_kg13),
      delta=1.0e-9,
    )

  def test_phase3_near_miss_component_failure_probability_is_meaningful_but_not_certain(self) -> None:
    close_wing = (-0.753, 6.0, 0.0)
    far_wing = (-0.753, 10.0, 0.0)
    _close_overlay, close_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      close_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      far_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertFalse(bool(close_event.direct_hitbox_intersection))
    self.assertFalse(bool(far_event.direct_hitbox_intersection))
    self.assertGreater(float(close_event.component_failure_probability), 0.0)
    self.assertGreaterEqual(float(far_event.component_failure_probability), 0.0)
    self.assertGreaterEqual(float(close_event.component_failure_probability), 0.24)
    self.assertLess(float(close_event.component_failure_probability), 0.42)
    self.assertGreater(
      float(close_event.component_failure_probability),
      float(far_event.component_failure_probability),
    )

  def test_phase3_primary_component_reports_mechanism_load_vector(self) -> None:
    direct_wing = (-0.8, 4.1, 0.0)
    _frag_overlay, frag_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "blast_fragmentation",
      direct_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )
    _rod_overlay, rod_event = _profiled_local_hit_overlay_and_event_with_velocity(
      "continuous_rod",
      direct_wing,
      (900.0, -250.0, 0.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertEqual(str(frag_event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(frag_event.component_primary_system), "flight_control")
    frag_rows = list(frag_event.component_mechanism_load_rows)
    self.assertEqual(len(frag_rows), int(frag_event.component_hit_count))
    frag_primary_row = next(
      (
        row
        for row in frag_rows
        if str(row.component_name) == str(frag_event.component_primary_name)
      ),
      None,
    )
    self.assertIsNotNone(frag_primary_row)
    assert frag_primary_row is not None
    self.assertEqual(str(frag_primary_row.component_system), "flight_control")
    self.assertEqual(
      str(frag_primary_row.component_redundancy_group_id),
      str(frag_event.component_primary_redundancy_group_id),
    )
    self.assertTrue(bool(frag_primary_row.direct_hit))
    self.assertAlmostEqual(float(frag_primary_row.distance_m), 0.0, delta=1.0e-6)
    self.assertGreater(float(frag_primary_row.effect_scale), 0.0)
    self.assertGreater(float(frag_primary_row.component_threshold_scale), 0.0)
    self.assertGreater(float(frag_primary_row.component_failure_probability), 0.0)
    self.assertEqual(
      str(frag_primary_row.component_failure_probability_source),
      "synthetic_sigmoid",
    )
    self.assertFalse(bool(frag_primary_row.component_failure_probability_calibrated))
    self.assertEqual(
      str(frag_primary_row.component_failure_probability_evidence_dataset_ref),
      "",
    )
    self.assertGreaterEqual(float(frag_primary_row.component_failure_sample), 0.0)
    self.assertLessEqual(float(frag_primary_row.component_failure_sample), 1.0)
    self.assertFalse(bool(frag_primary_row.component_failure_probability_authority))
    self.assertEqual(
      str(frag_primary_row.component_failure_probability_weapon_family),
      "blast_fragmentation",
    )
    self.assertEqual(str(frag_primary_row.component_failure_probability_aspect_bucket), "beam")
    self.assertEqual(str(frag_primary_row.component_failure_probability_closure_bucket), "high")
    self.assertEqual(
      str(frag_primary_row.component_failure_probability_miss_distance_bucket),
      "direct_hit",
    )
    self.assertGreater(float(frag_event.component_primary_mechanism_fragment_energy_j), 0.0)
    self.assertGreater(
      float(frag_event.component_primary_mechanism_fragment_areal_density_per_m2),
      0.0,
    )
    self.assertGreater(float(frag_event.component_primary_mechanism_penetration_margin), 0.0)
    self.assertGreater(
      float(frag_event.component_primary_mechanism_blast_overpressure_kpa),
      0.0,
    )
    self.assertGreater(
      float(frag_event.component_primary_mechanism_blast_impulse_kpa_ms),
      0.0,
    )
    self.assertGreater(
      float(frag_event.component_primary_mechanism_blast_scaled_distance_m_kg13),
      0.0,
    )
    self.assertAlmostEqual(
      float(frag_event.component_primary_mechanism_rod_cut_margin),
      0.0,
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_fragment_energy_j),
      float(frag_event.component_primary_mechanism_fragment_energy_j),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_fragment_areal_density_per_m2),
      float(frag_event.component_primary_mechanism_fragment_areal_density_per_m2),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_penetration_margin),
      float(frag_event.component_primary_mechanism_penetration_margin),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_blast_overpressure_kpa),
      float(frag_event.component_primary_mechanism_blast_overpressure_kpa),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_blast_impulse_kpa_ms),
      float(frag_event.component_primary_mechanism_blast_impulse_kpa_ms),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_blast_scaled_distance_m_kg13),
      float(frag_event.component_primary_mechanism_blast_scaled_distance_m_kg13),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(frag_primary_row.mechanism_rod_cut_margin),
      float(frag_event.component_primary_mechanism_rod_cut_margin),
      delta=1.0e-6,
    )

    self.assertEqual(str(rod_event.component_primary_name), "right_aileron_actuator")
    rod_rows = list(rod_event.component_mechanism_load_rows)
    self.assertEqual(len(rod_rows), int(rod_event.component_hit_count))
    rod_primary_row = next(
      (
        row
        for row in rod_rows
        if str(row.component_name) == str(rod_event.component_primary_name)
      ),
      None,
    )
    self.assertIsNotNone(rod_primary_row)
    assert rod_primary_row is not None
    self.assertGreater(float(rod_event.component_primary_mechanism_rod_cut_margin), 0.0)
    self.assertGreater(float(rod_event.component_primary_mechanism_penetration_margin), 0.0)
    self.assertAlmostEqual(
      float(rod_event.component_primary_mechanism_blast_overpressure_kpa),
      0.0,
      delta=1.0e-6,
    )
    self.assertGreater(float(rod_primary_row.mechanism_rod_cut_margin), 0.0)
    self.assertAlmostEqual(
      float(rod_primary_row.mechanism_rod_cut_margin),
      float(rod_event.component_primary_mechanism_rod_cut_margin),
      delta=1.0e-6,
    )
    self.assertAlmostEqual(
      float(rod_primary_row.mechanism_blast_overpressure_kpa),
      0.0,
      delta=1.0e-6,
    )

  def test_phase3_near_miss_component_primary_prefers_highest_consequence_projection(self) -> None:
    target_name = "F-16C_A2_ProjectionPriority_Test"
    overrides = [_make_f16_projection_priority_override(target_name)]

    overlay, _, event = _profiled_local_hit_overlay_for_target(
      target_name,
      "blast_fragmentation",
      (-0.8, 5.25, 0.0),
      damage=90.0,
      radius=35.0,
      overrides=overrides,
    )

    self.assertFalse(bool(event.direct_hitbox_intersection))
    self.assertGreater(int(event.projected_hitbox_count), 0)
    rows = list(event.component_mechanism_load_rows)
    self.assertGreaterEqual(len(rows), 2)
    by_name = {str(row.component_name): row for row in rows}
    near_row = by_name["near_resistant_wing_structure"]
    far_row = by_name["far_vulnerable_flight_servo"]

    self.assertLess(float(near_row.distance_m), float(far_row.distance_m))
    self.assertGreater(
      float(far_row.effect_scale),
      float(near_row.effect_scale),
    )
    self.assertGreater(int(event.component_hit_count), int(event.projected_hitbox_count))
    self.assertEqual(str(event.component_primary_name), "far_vulnerable_flight_servo")
    self.assertEqual(str(event.component_primary_system), "flight_control")
    self.assertLess(overlay["flight_control"], 1.0)

  def test_phase3_warhead_orientation_axis_modulates_rod_pattern_evidence(self) -> None:
    near_wing = (-0.753, 7.1, 0.0)
    missile_velocity = (0.0, -900.0, 0.0)
    broadside_overlay, broadside_event = (
      _profiled_local_hit_overlay_and_event_with_velocity_and_attitude(
        "continuous_rod",
        near_wing,
        missile_velocity,
        (0.0, 0.0, 0.0),
        damage=90.0,
        radius=35.0,
      )
    )
    axial_overlay, axial_event = (
      _profiled_local_hit_overlay_and_event_with_velocity_and_attitude(
        "continuous_rod",
        near_wing,
        missile_velocity,
        (90.0, 0.0, 0.0),
        damage=90.0,
        radius=35.0,
      )
    )

    self.assertEqual(str(broadside_event.effect_family), "continuous_rod")
    self.assertAlmostEqual(abs(float(broadside_event.warhead_orientation_axis_forward)), 1.0, delta=1.0e-6)
    self.assertAlmostEqual(abs(float(axial_event.warhead_orientation_axis_right)), 1.0, delta=1.0e-6)
    self.assertGreater(
      float(broadside_event.warhead_orientation_pattern_scale),
      float(axial_event.warhead_orientation_pattern_scale),
    )
    self.assertGreater(
      float(broadside_event.warhead_spatial_pattern_scale),
      float(axial_event.warhead_spatial_pattern_scale),
    )
    self.assertGreater(
      float(broadside_event.warhead_spatial_hit_estimate),
      float(axial_event.warhead_spatial_hit_estimate),
    )
    self.assertLess(
      broadside_overlay["flight_control"],
      axial_overlay["flight_control"],
    )

  def test_phase3_local_hit_geometry_respects_target_pitch_and_roll(self) -> None:
    local_aileron = (-0.8, 4.1, 0.0)
    overlay, event = _profiled_local_hit_overlay_and_event_with_target_attitude(
      "continuous_rod",
      local_aileron,
      (12.0, 25.0),
      damage=90.0,
      radius=35.0,
    )

    self.assertAlmostEqual(float(event.detonation_local_forward_m), local_aileron[0], delta=1.0e-5)
    self.assertAlmostEqual(float(event.detonation_local_right_m), local_aileron[1], delta=1.0e-5)
    self.assertAlmostEqual(float(event.detonation_local_up_m), local_aileron[2], delta=1.0e-5)
    self.assertTrue(bool(event.direct_hitbox_intersection))
    self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
    self.assertEqual(str(event.component_primary_system), "flight_control")
    self.assertLess(overlay["flight_control"], 1.0)
    self.assertLess(overlay["roll_control"], 1.0)
