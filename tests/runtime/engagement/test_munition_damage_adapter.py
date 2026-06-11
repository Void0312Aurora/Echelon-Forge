from __future__ import annotations

import math
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _entity_ref(entity_id: int, *, world_index: int = 0) -> ef_py.EngagementEntityRef:
  ref = ef_py.EngagementEntityRef()
  ref.world_index = world_index
  ref.entity_id = entity_id
  return ref


def _make_detection(target_id: int, *, range_m: float = 30000.0) -> ef_py.Detection:
  detection = ef_py.Detection()
  detection.target_id = int(target_id)
  detection.range = float(range_m)
  detection.bearing = 0.0
  detection.elevation = 0.0
  detection.closing_speed = 500.0
  detection.signal_strength = 1.0
  detection.sensor_type = int(ef_py.SensorType.Radar)
  detection.local_sensor_hit = True
  detection.timestamp = 0.0
  return detection


def _make_air_missile_fixture() -> tuple[ef_py.SimulationKernel, int, int, int]:
  sim = ef_py.SimulationKernel()
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")

  sim.set_time_step(1.0 / 60.0)
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
      30000.0,
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
  sim.set_contact_list(blue_id, [_make_detection(red_id)])

  missile_id = int(sim.fire_missile(blue_id, red_id))
  if missile_id <= 0:
    raise AssertionError("expected legacy fire_missile launch to succeed")
  return sim, blue_id, red_id, missile_id


def _make_lifecycle_packet(
  *,
  sim: ef_py.SimulationKernel,
  attacker_id: int,
  target_id: int,
  missile_id: int,
  launch_event_id: int,
  source_time_s: float,
) -> ef_py.MunitionLifecyclePacket:
  runtime = sim.debug_get_missile_runtime_state(missile_id)

  packet = ef_py.MunitionLifecyclePacket()
  packet.packet_id = 9001
  packet.munition = _entity_ref(missile_id)
  packet.attacker = _entity_ref(attacker_id)
  packet.target_entity = _entity_ref(target_id)
  packet.has_target_entity = True
  packet.target_track_id = target_id
  packet.has_target_track = bool(runtime["seeker_has_valid_track"])
  packet.launch_event_id = launch_event_id
  packet.active = bool(sim.is_unit_active(missile_id))
  packet.seeker_mode = "terminal" if bool(runtime["terminal_seeker_active"]) else "midcourse"
  packet.guidance_cadence_s = float(runtime["guidance_update_period_s"])
  packet.track_memory_state = "valid" if bool(runtime["seeker_has_valid_track"]) else "coasting"
  fuel_remaining_fraction = (
    float(runtime["mass_fuel_kg"])
    / max(
      1.0e-9,
      float(runtime["mass_total_kg"]) - float(runtime["mass_empty_kg"]) - float(runtime["mass_stores_kg"]),
    )
  )
  packet.fuel_remaining_fraction = max(0.0, min(1.0, fuel_remaining_fraction))
  packet.burnout = source_time_s >= float(runtime["burnout_time_s"])
  packet.max_flight_time_s = float(runtime["max_flight_time_s"])
  packet.fuze_state = "armed" if float(runtime["fuse_distance_m"]) > 0.0 else "unknown"
  packet.source_time_s = source_time_s
  return packet


class MunitionDamageAdapterTests(unittest.TestCase):
  def test_air_missile_runtime_observation_fits_munition_lifecycle_packet(self) -> None:
    sim, blue_id, red_id, missile_id = _make_air_missile_fixture()
    sim.step()
    source_time_s = float(sim.get_time_step())

    packet = _make_lifecycle_packet(
      sim=sim,
      attacker_id=blue_id,
      target_id=red_id,
      missile_id=missile_id,
      launch_event_id=2001,
      source_time_s=source_time_s,
    )
    runtime = sim.debug_get_missile_runtime_state(missile_id)

    self.assertEqual(packet.munition.entity_id, missile_id)
    self.assertEqual(packet.attacker.entity_id, blue_id)
    self.assertEqual(packet.target_entity.entity_id, red_id)
    self.assertTrue(bool(packet.has_target_entity))
    self.assertEqual(packet.target_track_id, red_id)
    self.assertTrue(bool(packet.has_target_track))
    self.assertEqual(packet.launch_event_id, 2001)
    self.assertTrue(bool(packet.active))
    self.assertIn(packet.seeker_mode, ("midcourse", "terminal"))
    self.assertEqual(packet.track_memory_state, "valid")
    self.assertGreater(packet.fuel_remaining_fraction, 0.0)
    self.assertLessEqual(packet.fuel_remaining_fraction, 1.0)
    self.assertFalse(bool(packet.burnout))
    self.assertAlmostEqual(packet.max_flight_time_s, float(runtime["max_flight_time_s"]))
    self.assertEqual(packet.fuze_state, "armed")
    self.assertAlmostEqual(packet.source_time_s, source_time_s)

  def test_synthetic_proximity_hit_fits_effects_event_and_damage_report_shape(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(770)
    self.assertTrue(kernel.load_database(_DB_PATH))

    attacker_id = int(
      kernel.spawn_unit(
        ef_py.Side.Blue,
        "Aircraft",
        0.0,
        0.0,
        1000.0,
        0.0,
        0.0,
        0.0,
        0.0,
        100.0,
        0.0,
      )
    )
    target_id = int(
      kernel.spawn_unit(
        ef_py.Side.Red,
        "DDG-51_Flight_I_USS_Arleigh_Burke",
        0.0,
        1500.0,
        0.0,
        180.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
      )
    )

    health_before = [float(value) for value in kernel.get_unit_health(target_id)]
    damage_before = [float(value) for value in kernel.get_unit_damage_state(target_id)]
    hit_applied = bool(kernel.debug_apply_proximity_hit(attacker_id, target_id, 120.0, 80.0))
    health_after = [float(value) for value in kernel.get_unit_health(target_id)]
    damage_after = [float(value) for value in kernel.get_unit_damage_state(target_id)]

    effects = ef_py.EffectsEvent()
    effects.event_id = 9101
    effects.munition = _entity_ref(attacker_id)
    effects.target = _entity_ref(target_id)
    effects.trigger_type = "debug_proximity_hit"
    effects.outcome_state = "hit" if hit_applied else "rejected"
    effects.detonation_time_s = 0.0
    effects.nearest_approach_time_s = 0.0
    effects.quality = 1.0 if hit_applied else 0.0
    effects.confidence = 1.0
    effects.effect_family = "blast_fragmentation"
    effects.warhead_mass_kg = 0.0
    effects.warhead_lethal_radius_m = 80.0
    effects.warhead_profile_synthetic = True
    effects.damage_scalar_synthetic = True
    effects.fuze_type = "proximity"
    effects.fuze_trigger_radius_m = 80.0
    effects.fuze_delay_s = 0.0
    effects.fuze_reliability = 1.0
    effects.fuze_profile_synthetic = True
    effects.direct_hitbox_intersection = True
    effects.projected_hitbox_count = 0
    effects.spatial_effect_scale = 1.0
    effects.mechanism_armor_scale = 1.0
    effects.mechanism_exposure_scale = 1.0
    effects.mechanism_effect_scale = 1.0
    effects.mechanism_fragment_energy_j = 480.0
    effects.mechanism_fragment_areal_density_per_m2 = 11.0
    effects.mechanism_penetration_margin = 0.30
    effects.mechanism_blast_overpressure_kpa = 15.0
    effects.mechanism_blast_impulse_kpa_ms = 36.0
    effects.mechanism_rod_cut_margin = 0.0
    effects.warhead_spatial_sample_count = 1
    effects.warhead_spatial_hit_estimate = 1.0
    effects.warhead_spatial_hit_fraction = 1.0
    effects.warhead_spatial_energy_scale = 1.0
    effects.warhead_spatial_pattern_scale = 1.0
    effects.warhead_orientation_axis_forward = 1.0
    effects.warhead_orientation_axis_right = 0.0
    effects.warhead_orientation_axis_up = 0.0
    effects.warhead_orientation_pattern_scale = 1.0
    effects.component_threshold_scale = 1.0
    effects.component_failure_probability = 0.50
    effects.component_failure_probability_source = "synthetic_sigmoid"
    effects.component_failure_probability_calibrated = False
    effects.component_failure_probability_evidence_dataset_ref = ""
    effects.component_failure_sample = 0.25
    effects.component_failure_count = 1
    effects.component_hit_count = 1
    effects.component_primary_name = "test_component"
    effects.component_primary_system = "fuel"
    effects.component_primary_redundancy_group = 0.0
    effects.component_primary_critical = True
    effects.component_primary_redundancy_group_id = "fuel_singleton"
    effects.component_primary_integrity = 0.66
    effects.component_redundancy_group_availability = 0.66
    effects.component_redundancy_group_member_count = 1
    effects.component_redundancy_group_failed_count = 0

    report = ef_py.DamageReport()
    report.report_id = 9201
    report.target = _entity_ref(target_id)
    report.source_event_id = effects.event_id
    report.hp_delta = health_after[0] - health_before[0]
    report.system_health_delta = min(damage_after) - min(damage_before)
    report.platform_damage_state_delta = ",".join(
      f"{after - before:.6f}" for before, after in zip(damage_before, damage_after)
    )
    report.mission_kill = damage_after[0] < 0.5
    report.mobility_kill = damage_after[1] < 0.5
    report.sensor_kill = damage_after[2] < 0.5
    report.survivability_kill = damage_after[3] < 0.5
    report.loss_state_from = "active"
    report.loss_state_to = "destroyed" if not kernel.is_unit_active(target_id) else "damaged"
    report.destroyed = not bool(kernel.is_unit_active(target_id))
    report.report_time_s = 0.0

    self.assertTrue(hit_applied)
    self.assertEqual(effects.target.entity_id, target_id)
    self.assertEqual(effects.outcome_state, "hit")
    self.assertEqual(effects.effect_family, "blast_fragmentation")
    self.assertTrue(bool(effects.warhead_profile_synthetic))
    self.assertTrue(bool(effects.damage_scalar_synthetic))
    self.assertAlmostEqual(float(effects.detonation_heading_deg), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_pitch_deg), 0.0, delta=1.0e-6)
    self.assertAlmostEqual(float(effects.detonation_roll_deg), 0.0, delta=1.0e-6)
    self.assertTrue(math.isclose(effects.quality, 1.0))
    self.assertTrue(bool(effects.direct_hitbox_intersection))
    self.assertEqual(int(effects.projected_hitbox_count), 0)
    self.assertEqual(str(effects.component_primary_redundancy_group_id), "fuel_singleton")
    self.assertAlmostEqual(float(effects.component_primary_integrity), 0.66)
    self.assertAlmostEqual(float(effects.component_redundancy_group_availability), 0.66)
    self.assertTrue(math.isclose(float(effects.mechanism_effect_scale), 1.0))
    self.assertGreater(float(effects.mechanism_fragment_energy_j), 0.0)
    self.assertGreater(float(effects.mechanism_fragment_areal_density_per_m2), 0.0)
    self.assertGreater(float(effects.mechanism_penetration_margin), 0.0)
    self.assertGreater(float(effects.mechanism_blast_overpressure_kpa), 0.0)
    self.assertGreater(float(effects.mechanism_blast_impulse_kpa_ms), 0.0)
    self.assertEqual(int(effects.warhead_spatial_sample_count), 1)
    self.assertTrue(math.isclose(float(effects.warhead_spatial_hit_estimate), 1.0))
    self.assertTrue(math.isclose(float(effects.warhead_spatial_hit_fraction), 1.0))
    self.assertTrue(math.isclose(float(effects.warhead_orientation_axis_forward), 1.0))
    self.assertTrue(math.isclose(float(effects.warhead_orientation_pattern_scale), 1.0))
    self.assertTrue(math.isclose(float(effects.component_threshold_scale), 1.0))
    self.assertEqual(int(effects.component_hit_count), 1)
    self.assertEqual(str(effects.component_primary_system), "fuel")

    self.assertEqual(report.target.entity_id, target_id)
    self.assertEqual(report.source_event_id, effects.event_id)
    self.assertLess(report.hp_delta, 0.0)
    self.assertLess(report.system_health_delta, 0.0)
    self.assertTrue(bool(report.mission_kill))
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(report.loss_state_to, "damaged")
    self.assertIn("-0.", report.platform_damage_state_delta)


if __name__ == "__main__":
  unittest.main()
