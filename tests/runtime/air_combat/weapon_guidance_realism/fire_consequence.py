from __future__ import annotations

from python.runtime_bootstrap import configure_sim_log_level

from .mq9_aim120 import (
  _assert_component_row_exposes_public_failure_modes,
  _assert_mq9_event_is_non_authoritative,
  _component_rows_by_name,
)
from .helpers import *


configure_sim_log_level("error")


def _mq9_fire_consequence_state_after_local_hit(
  local: tuple[float, float, float],
  *,
  damage: float = 120.0,
  steps: int = 80,
) -> dict[str, object]:
  sim = _kernel_with_unit_overrides([])
  sim.set_time_step(0.5)
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

  before_overlay = _aircraft_damage_overlay(sim, target_id)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _make_warhead_profile("blast_fragmentation", damage=damage, radius=35.0),
    900.0,
    -250.0,
    0.0,
  )
  if not ok:
    raise AssertionError("profiled MQ-9/AIM-120C fire-consequence hit failed")

  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError("expected one MQ-9/AIM-120C fire effects event")
  if len(events.damage_reports) != 1:
    raise AssertionError("expected one MQ-9/AIM-120C fire damage report")

  hit_overlay = _aircraft_damage_overlay(sim, target_id)
  for _ in range(int(steps)):
    sim.step()

  return {
    "sim": sim,
    "target_id": target_id,
    "before_overlay": before_overlay,
    "hit_overlay": hit_overlay,
    "after_overlay": _aircraft_damage_overlay(sim, target_id),
    "effect": events.effects_events[0],
    "report": events.damage_reports[0],
  }


class FireConsequenceRuntimeMixin:
  def test_mq9_aim120_left_wing_fuel_hit_grows_fire_and_secondary_damage_through_runtime_path(
    self,
  ) -> None:
    state = _mq9_fire_consequence_state_after_local_hit((-0.4, -4.8, 0.0))

    effect = state["effect"]
    report = state["report"]
    sim = state["sim"]
    target_id = int(state["target_id"])
    self.assertEqual(str(effect.component_primary_name), "left_wing_fuel_cell")
    self.assertEqual(str(effect.component_primary_system), "fuel")
    self.assertTrue(bool(effect.direct_hitbox_intersection))
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    self.assertTrue(bool(sim.is_unit_active(target_id)))
    _assert_mq9_event_is_non_authoritative(self, effect)

    rows_by_name = _component_rows_by_name(effect)
    self.assertIn("left_wing_fuel_cell", rows_by_name)
    modes = _assert_component_row_exposes_public_failure_modes(
      self,
      _component_response_for_load_row(effect, rows_by_name["left_wing_fuel_cell"]),
      expected_any={"puncture", "fuel_leak", "fire_source"},
    )
    self.assertIn("fuel_leak", modes)
    self.assertIn("fire_source", modes)

    hit_overlay = state["hit_overlay"]
    after_overlay = state["after_overlay"]
    before_overlay = state["before_overlay"]

    self.assertGreater(hit_overlay["wing_fire_zone"], before_overlay["wing_fire_zone"])
    self.assertGreater(hit_overlay["fire"], before_overlay["fire"])
    self.assertGreater(hit_overlay["fuel_leak"], before_overlay["fuel_leak"])
    self.assertGreater(hit_overlay["flammable_fluid"], before_overlay["flammable_fluid"])

    self.assertGreater(after_overlay["fire"], hit_overlay["fire"] + 0.05)
    self.assertGreater(after_overlay["wing_fire_zone"], 0.05)
    self.assertGreater(after_overlay["fuselage_fire_zone"], hit_overlay["fuselage_fire_zone"])
    self.assertLess(after_overlay["fuel"], hit_overlay["fuel"] - 0.02)
    self.assertLess(after_overlay["flight_control"], hit_overlay["flight_control"] - 0.005)
    self.assertLess(after_overlay["avionics"], hit_overlay["avionics"] - 0.02)
    self.assertLess(after_overlay["crew"], hit_overlay["crew"] - 0.01)

  def test_mq9_aim120_rear_engine_hit_seeds_engine_fire_zone_and_propulsion_consequence(
    self,
  ) -> None:
    state = _mq9_fire_consequence_state_after_local_hit((-4.4, 0.0, 0.0))

    effect = state["effect"]
    report = state["report"]
    sim = state["sim"]
    target_id = int(state["target_id"])
    self.assertEqual(str(effect.component_primary_name), "rear_engine_block")
    self.assertEqual(str(effect.component_primary_system), "engine")
    self.assertTrue(bool(effect.direct_hitbox_intersection))
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    self.assertTrue(bool(sim.is_unit_active(target_id)))
    _assert_mq9_event_is_non_authoritative(self, effect)

    rows_by_name = _component_rows_by_name(effect)
    self.assertIn("rear_engine_block", rows_by_name)
    modes = _assert_component_row_exposes_public_failure_modes(
      self,
      _component_response_for_load_row(effect, rows_by_name["rear_engine_block"]),
      expected_any={"puncture", "cut", "blast_deformation", "fire_source"},
    )
    self.assertIn("fire_source", modes)

    hit_overlay = state["hit_overlay"]
    after_overlay = state["after_overlay"]
    before_overlay = state["before_overlay"]

    self.assertGreater(hit_overlay["engine_fire_zone"], before_overlay["engine_fire_zone"])
    self.assertGreater(hit_overlay["ignition_source"], before_overlay["ignition_source"])
    self.assertGreater(hit_overlay["smoke_heat"], before_overlay["smoke_heat"])
    self.assertLess(hit_overlay["propulsion"], before_overlay["propulsion"])

    self.assertGreater(after_overlay["engine_fire_zone"], 0.01)
    self.assertLess(after_overlay["propulsion"], hit_overlay["propulsion"] - 0.005)
    self.assertGreaterEqual(after_overlay["fire"], 0.0)
    self.assertLessEqual(after_overlay["fire"], 0.05)
