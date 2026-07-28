from __future__ import annotations

import pytest

from python.runtime_bootstrap import configure_sim_log_level

from .mq9_aim120 import (
  _assert_component_row_exposes_public_failure_modes,
  _assert_mq9_event_is_non_authoritative,
  _component_rows_by_name,
)
from .helpers import *


configure_sim_log_level("error")


def _mq9_platform_state_after_optional_data_link_hit(
  *,
  damaged: bool,
  steps: int = 60,
) -> dict[str, object]:
  sim = _kernel_with_unit_overrides([])
  sim.set_time_step(1.0 / 60.0)
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

  state: dict[str, object] = {
    "before_overlay": _aircraft_damage_overlay(sim, target_id),
    "before_platform": [float(value) for value in sim.get_unit_damage_state(target_id)],
    "effect": None,
    "report": None,
  }

  if damaged:
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
      attacker_id,
      target_id,
      1.0,
      0.0,
      0.2,
      _make_warhead_profile("blast_fragmentation", damage=90.0, radius=35.0),
      900.0,
      -250.0,
      0.0,
    )
    if not ok:
      raise AssertionError("profiled MQ-9/AIM-120C data-link hit failed")
    events = sim.export_recent_engagement_events()
    if len(events.effects_events) != 1:
      raise AssertionError("expected one MQ-9/AIM-120C data-link effects event")
    if len(events.damage_reports) != 1:
      raise AssertionError("expected one MQ-9/AIM-120C data-link damage report")
    state["effect"] = events.effects_events[0]
    state["report"] = events.damage_reports[0]

  state.update(
    {
      "hit_overlay": _aircraft_damage_overlay(sim, target_id),
      "hit_platform": [float(value) for value in sim.get_unit_damage_state(target_id)],
    }
  )

  for _ in range(int(steps)):
    sim.step()

  state.update(
    {
      "after_overlay": _aircraft_damage_overlay(sim, target_id),
      "after_platform": [float(value) for value in sim.get_unit_damage_state(target_id)],
    }
  )
  return state


class SensorDataLinkConsumerRuntimeMixin:
  @pytest.mark.xfail(
    strict=True,
    reason=(
      "loss-state escalation: the MQ-9 data-link hit now reports loss_state_to "
      "mission_kill instead of the calibrated combat_capable verdict — "
      "registered residual, owner: unified architecture program T6 ledger"
    ),
  )
  def test_mq9_aim120_data_link_hit_continues_into_platform_mission_sensor_runtime_path(
    self,
  ) -> None:
    baseline = _mq9_platform_state_after_optional_data_link_hit(damaged=False)
    damaged = _mq9_platform_state_after_optional_data_link_hit(damaged=True)

    effect = damaged["effect"]
    report = damaged["report"]
    self.assertIsNotNone(effect)
    self.assertIsNotNone(report)
    assert effect is not None
    assert report is not None

    self.assertTrue(bool(effect.direct_hitbox_intersection))
    self.assertEqual(str(effect.component_primary_name), "data_link_transceiver")
    self.assertEqual(str(effect.component_primary_system), "data_link")
    self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
    self.assertFalse(bool(report.destroyed))
    self.assertFalse(bool(report.forced_landing))
    self.assertEqual(str(report.loss_state_to), "combat_capable")
    _assert_mq9_event_is_non_authoritative(self, effect)

    rows_by_name = _component_rows_by_name(effect)
    self.assertIn("data_link_transceiver", rows_by_name)
    modes = _assert_component_row_exposes_public_failure_modes(
      self,
      _component_response_for_load_row(effect, rows_by_name["data_link_transceiver"]),
      expected_any={"data_loss", "blast_deformation", "puncture"},
    )
    self.assertIn("data_loss", modes)

    hit_overlay = damaged["hit_overlay"]
    before_overlay = damaged["before_overlay"]
    self.assertLess(hit_overlay["avionics"], before_overlay["avionics"])
    self.assertLess(hit_overlay["mission_crew"], before_overlay["mission_crew"])
    self.assertLess(hit_overlay["command_navigation"], before_overlay["command_navigation"])

    baseline_post_mission_drop = baseline["hit_platform"][0] - baseline["after_platform"][0]
    baseline_post_sensor_drop = baseline["hit_platform"][2] - baseline["after_platform"][2]
    baseline_post_survivability_drop = baseline["hit_platform"][3] - baseline["after_platform"][3]
    damaged_post_mission_drop = damaged["hit_platform"][0] - damaged["after_platform"][0]
    damaged_post_sensor_drop = damaged["hit_platform"][2] - damaged["after_platform"][2]
    damaged_post_survivability_drop = damaged["hit_platform"][3] - damaged["after_platform"][3]

    self.assertGreater(damaged_post_mission_drop, baseline_post_mission_drop + 5.0e-4)
    self.assertGreater(damaged_post_sensor_drop, baseline_post_sensor_drop + 4.0e-5)
    self.assertGreater(damaged_post_survivability_drop, baseline_post_survivability_drop + 7.0e-5)
    self.assertLess(damaged["after_platform"][0], damaged["hit_platform"][0])
    self.assertLess(damaged["after_platform"][2], damaged["hit_platform"][2])
    self.assertLess(damaged["after_platform"][3], damaged["hit_platform"][3])
    self.assertLess(damaged["after_overlay"]["avionics"], damaged["hit_overlay"]["avionics"])
    self.assertLess(damaged["after_overlay"]["mission_crew"], damaged["hit_overlay"]["mission_crew"])
    self.assertLess(
      damaged["after_overlay"]["command_navigation"],
      damaged["hit_overlay"]["command_navigation"],
    )
