from __future__ import annotations

import unittest

import pytest

from .helpers import *


class BoundaryCaseRuntimeMixin:
  # Boundary / edge-case tests.

  def test_degenerate_hitbox_geometry_produces_sensible_output(self) -> None:
    degenerate_name = "F-16C_A2_DegenerateHitbox_Test"
    with open(
      resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
      "r",
      encoding="utf-8",
    ) as handle:
      unit = json.load(handle)
    unit["name"] = degenerate_name
    damage_model = unit["damage_model"]
    damage_model.pop("vulnerability", None)
    for hitbox in damage_model["hitboxes"]:
      hitbox["size"] = [0.0, 0.0, 0.0]
      hitbox["armor"] = 0.0
      for component in hitbox.get("components", []):
        component["size"] = [0.0, 0.0, 0.0]
        component["armor"] = 0.0

    sim = _kernel_with_unit_overrides([unit])
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, degenerate_name)
    profile = _make_warhead_profile("continuous_rod", damage=90.0, radius=35.0)
    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id, target_id, -0.8, 4.1, 0.0, profile,
    )
    self.assertTrue(bool(ok))
    self.assertTrue(sim.is_unit_active(target_id))

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    effect = events.effects_events[0]
    self.assertAlmostEqual(float(effect.mechanism_surface_incidence_cos), 0.0, delta=1.0e-6)
    self.assertFalse(bool(effect.direct_hitbox_intersection))

    overlay = _aircraft_damage_overlay(sim, target_id)
    for field_name, value in overlay.items():
      with self.subTest(overlay_field=field_name):
        self.assertTrue(math.isfinite(value))
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

  def test_degenerate_hitbox_extreme_offset_still_no_crash(self) -> None:
    far_name = "F-16C_A2_ExtremeOffsetHitbox_Test"
    with open(
      resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
      "r",
      encoding="utf-8",
    ) as handle:
      unit = json.load(handle)
    unit["name"] = far_name
    damage_model = unit["damage_model"]
    damage_model.pop("vulnerability", None)
    for hitbox in damage_model["hitboxes"]:
      hitbox["offset"] = [1e300, 0.0, 0.0]
      hitbox["size"] = [1.0, 1.0, 1.0]

    sim = _kernel_with_unit_overrides([unit])
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, far_name)
    profile = _make_warhead_profile("blast_fragmentation", damage=90.0, radius=35.0)
    ok = sim.debug_apply_profiled_local_proximity_hit(
      attacker_id, target_id, -0.8, 4.1, 0.0, profile,
    )
    self.assertTrue(bool(ok))
    self.assertTrue(sim.is_unit_active(target_id))
    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    self.assertFalse(bool(events.effects_events[0].direct_hitbox_intersection))

  @pytest.mark.xfail(
    strict=True,
    reason=(
      "loss-state escalation: the live missile hit drains legacy aircraft HP to "
      "[0, 0] where the structured damage path must keep HP untouched — "
      "registered residual, owner: unified architecture program T6 ledger"
    ),
  )
  def test_legacy_aircraft_hp_path_live_missile_hit_records_damage_report(self) -> None:
    sim = _make_kernel()
    blue_id = int(
      sim.spawn_unit(
        ef_py.Side.Blue,
        "F-16C_Block50",
        0.0,
        0.0,
        5000.0,
        0.0,
        0.0,
        0.0,
        0.0,
        250.0,
        0.0,
      )
    )
    red_id = int(
      sim.spawn_unit(
        ef_py.Side.Red,
        "Aircraft",
        0.0,
        10000.0,
        5000.0,
        180.0,
        0.0,
        0.0,
        0.0,
        -250.0,
        0.0,
      )
    )
    sim.set_unit_ammo(blue_id, 4, 4)
    sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
    _set_contacts(
      sim,
      blue_id,
      [_relative_detection_from_truth(sim, blue_id, red_id, timestamp=0.0)],
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    health_before = [float(value) for value in sim.get_unit_health(red_id)]
    self.assertGreater(health_before[0], 0.0)

    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim,
        missile_id,
        [
          _relative_detection_from_truth(
            sim, missile_id, red_id,
            timestamp=step_idx * sim.get_time_step(),
            local_sensor_hit=True,
          )
        ],
      )
      sim.step()

    self.assertFalse(sim.is_unit_active(missile_id))
    health_after = [float(value) for value in sim.get_unit_health(red_id)]
    self.assertEqual(health_after, health_before)

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.launch_events), 1)
    self.assertGreaterEqual(len(events.effects_events), 1)
    self.assertGreaterEqual(len(events.damage_reports), 1)
    effect = events.effects_events[0]
    report = events.damage_reports[0]
    self.assertEqual(int(effect.munition.entity_id), missile_id)
    self.assertEqual(int(effect.target.entity_id), red_id)
    self.assertEqual(str(effect.trigger_type), "proximity_fuze")
    self.assertTrue(math.isfinite(float(effect.miss_distance_m)))
    self.assertGreaterEqual(float(effect.miss_distance_m), 0.0)
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(report.system_health_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))

  def test_cumulative_component_integrity_after_repeated_hits(self) -> None:
    sim = _make_kernel()
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _make_warhead_profile("continuous_rod", damage=90.0, radius=35.0)

    integrities = []
    for _ in range(3):
      ok = sim.debug_apply_profiled_local_proximity_hit(
        attacker_id, target_id, -0.8, 4.1, 0.0, profile,
      )
      self.assertTrue(bool(ok))
      self.assertTrue(sim.is_unit_active(target_id))
      events = sim.export_recent_engagement_events()
      self.assertGreaterEqual(len(events.effects_events), 1)
      effect = events.effects_events[-1]
      self.assertEqual(str(effect.component_primary_name), "right_aileron_actuator")
      integrities.append(float(effect.component_primary_integrity))

    self.assertLess(integrities[0], 1.0)
    self.assertLess(integrities[1], integrities[0])
    self.assertLess(integrities[2], integrities[1])
    for i, integrity in enumerate(integrities):
      self.assertTrue(math.isfinite(integrity), f"integrity[{i}] not finite")
      self.assertGreaterEqual(integrity, 0.0, f"integrity[{i}] < 0")

    overlay = _aircraft_damage_overlay(sim, target_id)
    self.assertLess(overlay["flight_control"], 1.0)

  def test_redundancy_group_single_member_failure_drives_availability_to_zero(self) -> None:
    target_name = "F-16C_A2_SoloRedundancyComponent_Test"
    overrides = [
      _make_f16_component_redundancy_override(
        target_name, redundancy_group=0.0, critical=True,
      )
    ]
    sim = _kernel_with_unit_overrides(overrides)
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_name)
    profile = _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0)

    for hit_idx in range(4):
      ok = sim.debug_apply_profiled_local_proximity_hit(
        attacker_id, target_id, -0.8, 4.1, 0.0, profile,
      )
      self.assertTrue(bool(ok))
      self.assertTrue(sim.is_unit_active(target_id))
      events = sim.export_recent_engagement_events()
      effect = events.effects_events[-1]
      integrity = float(effect.component_primary_integrity)
      if integrity < 0.35:
        break
    else:
      self.fail("component integrity did not drop below 0.35 after 4 hits")

    self.assertLess(float(effect.component_primary_integrity), 0.35)
    self.assertLess(float(effect.component_redundancy_group_availability), 0.25)
    self.assertEqual(int(effect.component_redundancy_group_member_count), 1)
    self.assertGreaterEqual(int(effect.component_redundancy_group_failed_count), 1)
    self.assertTrue(bool(effect.component_primary_critical))
    self.assertGreater(float(effect.component_failure_probability), 0.5)

  def test_surface_incidence_cos_reported_on_live_missile_event(self) -> None:
    sim = _make_baseline_kernel()
    blue_id, red_id = _spawn_geometry_pair(
      sim,
      red_x=13000.0, red_y=9000.0, red_heading=270.0,
      red_vx=-260.0, red_vy=0.0,
    )
    missile_id = int(sim.fire_missile(blue_id, red_id))
    self.assertGreater(missile_id, 0)

    for step_idx in range(3600):
      if not sim.is_unit_active(missile_id):
        break
      _set_contacts(
        sim, missile_id,
        [_relative_detection_from_truth(
          sim, missile_id, red_id,
          timestamp=step_idx * sim.get_time_step(),
          local_sensor_hit=True,
        )],
      )
      sim.step()

    self.assertFalse(sim.is_unit_active(missile_id))
    events = sim.export_recent_engagement_events()
    self.assertGreaterEqual(len(events.effects_events), 1)
    effect = events.effects_events[0]
    cos_val = float(effect.mechanism_surface_incidence_cos)
    comp_cos = float(effect.component_primary_mechanism_surface_incidence_cos)
    self.assertTrue(math.isfinite(cos_val))
    self.assertGreaterEqual(cos_val, 0.0)
    self.assertLessEqual(cos_val, 1.0)
    self.assertTrue(math.isfinite(comp_cos))
    self.assertGreaterEqual(comp_cos, 0.0)
    self.assertLessEqual(comp_cos, 1.0)
    # both event-level and component-level incidence cos are valid
    # (may differ when multiple hitboxes contribute to the event)

  def test_multi_component_hit_overlay_is_superposition_without_overflow(self) -> None:
    sim = _make_kernel()
    attacker_id, target_id = _spawn_structured_f16_pair(sim)
    profile = _make_warhead_profile("continuous_rod", damage=60.0, radius=15.0)

    hit_cases = [
      {"local": (6.6, 0.0, 0.0), "label": "nose_radar"},
      {"local": (-5.8, 0.0, 0.0), "label": "fuselage_engine"},
      {"local": (-0.8, 4.1, 0.0), "label": "wing_aileron"},
    ]

    for case in hit_cases:
      ok = sim.debug_apply_profiled_local_proximity_hit(
        attacker_id,
        target_id,
        float(case["local"][0]),
        float(case["local"][1]),
        float(case["local"][2]),
        profile,
      )
      self.assertTrue(bool(ok), f"hit at {case['label']} failed")
      self.assertTrue(sim.is_unit_active(target_id))
      overlay = _aircraft_damage_overlay(sim, target_id)
      for field_name, value in overlay.items():
        with self.subTest(hit_label=case["label"], overlay_field=field_name):
          self.assertTrue(math.isfinite(value), f"{field_name} not finite")
          self.assertGreaterEqual(value, 0.0, f"{field_name} < 0")
          self.assertLessEqual(value, 1.0, f"{field_name} > 1")

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 3)

  @pytest.mark.xfail(
    strict=True,
    reason=(
      "loss-state escalation: live hits now drain the Su-35S/E-3 platform "
      "damage state that the structured component path must leave pristine — "
      "registered residual, owner: unified architecture program T6 ledger"
    ),
  )
  # unittest.expectedFailure folds the subTest failures into one expected
  # failure so the strict xfail contract still reverse-alarms on recovery.
  @unittest.expectedFailure
  def test_live_missile_hit_against_non_f16_structured_target_produces_component_damage(self) -> None:
    targets = ["Su-35S_Flanker-E", "E-3_Sentry_AWACS"]
    for target_type in targets:
      with self.subTest(target_type=target_type):
        sim = _make_baseline_kernel()
        if target_type == "E-3_Sentry_AWACS":
          blue_id, red_id = _spawn_attacker_and_e3_target(sim)
        else:
          blue_id, red_id = _spawn_attacker_and_named_target(sim, target_type)
        sim.set_unit_ammo(blue_id, 4, 4)
        sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
        _set_contacts(
          sim, blue_id,
          [_relative_detection_from_truth(
            sim, blue_id, red_id,
            timestamp=0.0,
            local_sensor_hit=True,
          )],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        health_before = [float(value) for value in sim.get_unit_health(red_id)]
        damage_before = [float(value) for value in sim.get_unit_damage_state(red_id)]

        for step_idx in range(3600):
          if not sim.is_unit_active(missile_id):
            break
          _set_contacts(
            sim,
            missile_id,
            [
              _relative_detection_from_truth(
                sim, missile_id, red_id,
                timestamp=step_idx * sim.get_time_step(),
                local_sensor_hit=True,
              )
            ],
          )
          sim.step()

        self.assertFalse(sim.is_unit_active(missile_id))
        self.assertTrue(sim.is_unit_active(red_id))
        self.assertEqual(
          [float(v) for v in sim.get_unit_health(red_id)], health_before,
        )
        damage_after = [float(v) for v in sim.get_unit_damage_state(red_id)]
        self.assertEqual(damage_after, damage_before)

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.launch_events), 1)
        self.assertGreaterEqual(len(events.effects_events), 1)
        self.assertGreaterEqual(len(events.damage_reports), 1)
        effect = events.effects_events[0]
        report = events.damage_reports[0]
        self.assertEqual(int(effect.munition.entity_id), missile_id)
        self.assertEqual(int(effect.target.entity_id), red_id)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(report.system_health_delta), 0.0, delta=1.0e-6)
        self.assertFalse(bool(report.destroyed))
        self.assertEqual(str(report.loss_state_to), "combat_capable")
        self.assertEqual(int(effect.component_hit_count), 0)
        self.assertEqual(str(effect.component_primary_name), "")

  def test_zero_closure_speed_exercises_htk_impact_velocity_fallback(self) -> None:
    sim = _kernel_with_unit_overrides([])
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "F-16C_Block50")
    profile = _make_warhead_profile("hit_to_kill", damage=180.0, radius=10.0)
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      -0.8,
      4.1,
      0.0,
      profile,
      0.0,
      -200.0,
      0.0,
    )
    self.assertTrue(bool(ok))
    self.assertTrue(sim.is_unit_active(target_id))

    events = sim.export_recent_engagement_events()
    self.assertEqual(len(events.effects_events), 1)
    effect = events.effects_events[0]
    self.assertEqual(str(effect.effect_family), "hit_to_kill")
    self.assertLess(float(effect.closure_mps), 10.0)
    self.assertGreater(float(effect.mechanism_penetration_margin), 0.0)
    self.assertGreater(float(effect.warhead_spatial_energy_scale), 0.0)
    self.assertLess(float(effect.component_primary_integrity), 1.0)

    # contrast: non-zero closure produces different closure_mps but same
    # penetration_margin when max_speed dominates the fallback
    contrast_sim = _kernel_with_unit_overrides([])
    c_attacker_id, c_target_id = _spawn_attacker_and_named_target(contrast_sim, "F-16C_Block50")
    ok2 = contrast_sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      c_attacker_id,
      c_target_id,
      -0.8,
      4.1,
      0.0,
      profile,
      600.0,
      -200.0,
      0.0,
    )
    self.assertTrue(bool(ok2))
    contrast_events = contrast_sim.export_recent_engagement_events()
    contrast_effect = contrast_events.effects_events[0]
    self.assertGreater(float(contrast_effect.closure_mps), 100.0)
    self.assertAlmostEqual(
      float(effect.mechanism_penetration_margin),
      float(contrast_effect.mechanism_penetration_margin),
      delta=1.0e-6,
    )
