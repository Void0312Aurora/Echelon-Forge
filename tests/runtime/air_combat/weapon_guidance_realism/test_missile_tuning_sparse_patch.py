from __future__ import annotations

import unittest

from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
  _AIM120,
  _make_detection,
  _missile_runtime,
  _select_weapon,
  _set_contacts,
  _spawn_and_fire_weapon,
  _spawn_pair,
  ef_py,
)
from tests.support.unit_database import patched_database


class MissileTuningSparsePatchTests(unittest.TestCase):
  def test_public_default_autopilot_order_remains_one(self) -> None:
    self.assertEqual(int(ef_py.MissileTuning().autopilot_order), 1)

  def _launch_aim120(
    self,
    *,
    definition_patch: dict[str, object],
    global_patch: dict[str, object],
  ) -> dict:
    with patched_database(
      {_AIM120: lambda weapon: weapon["guidance"].update(definition_patch)},
      prefix="cmo_missile_tuning_patch_",
    ) as database_path:
      sim = ef_py.SimulationKernel()
      self.assertTrue(sim.load_database(str(database_path)))
      sim.set_time_step(1.0 / 60.0)
      tuning = ef_py.MissileTuning()
      for field_name, value in global_patch.items():
        setattr(tuning, field_name, value)
      sim.set_missile_tuning(tuning)

      _, _, missile_id = _spawn_and_fire_weapon(
        sim,
        _AIM120,
        range_m=22000.0,
        bearing_deg=5.0,
      )
      return _missile_runtime(sim, missile_id)

  def test_damping_only_patch_preserves_definition_autopilot_order(self) -> None:
    runtime = self._launch_aim120(
      definition_patch={"autopilot_order": 3, "autopilot_damping": 0.65},
      global_patch={"autopilot_damping": 0.82},
    )

    self.assertEqual(int(runtime["autopilot_order"]), 3)
    self.assertAlmostEqual(float(runtime["autopilot_damping"]), 0.82, delta=1.0e-9)

  def test_order_only_patch_preserves_definition_autopilot_damping(self) -> None:
    runtime = self._launch_aim120(
      definition_patch={"autopilot_order": 3, "autopilot_damping": 0.65},
      global_patch={"autopilot_order": 2},
    )

    self.assertEqual(int(runtime["autopilot_order"]), 2)
    self.assertAlmostEqual(float(runtime["autopilot_damping"]), 0.65, delta=1.0e-9)

  def test_unrelated_global_patch_does_not_force_autopilot_order_one(self) -> None:
    runtime = self._launch_aim120(
      definition_patch={"autopilot_order": 3, "autopilot_damping": 0.65},
      global_patch={"max_speed": 910.0},
    )

    self.assertAlmostEqual(float(runtime["max_speed_mps"]), 910.0, delta=1.0e-9)
    self.assertEqual(int(runtime["autopilot_order"]), 3)
    self.assertAlmostEqual(float(runtime["autopilot_damping"]), 0.65, delta=1.0e-9)

  def test_explicit_false_patch_overrides_true_definition_booleans(self) -> None:
    boolean_patch = {
      "lobl_required": True,
      "midcourse_datalink_supported": True,
      "use_kalman_seeker": True,
    }
    with patched_database(
      {_AIM120: lambda weapon: weapon["guidance"].update(boolean_patch)},
      prefix="cmo_missile_boolean_patch_",
    ) as database_path:
      sim = ef_py.SimulationKernel()
      self.assertTrue(sim.load_database(str(database_path)))
      sim.set_time_step(1.0 / 60.0)
      tuning = ef_py.MissileTuning()
      tuning.lobl_required = False
      tuning.midcourse_datalink_supported = False
      tuning.use_kalman_seeker = False
      sim.set_missile_tuning(tuning)

      blue_id, red_id = _spawn_pair(sim)
      _select_weapon(sim, blue_id, _AIM120)
      _set_contacts(
        sim,
        blue_id,
        [
          _make_detection(
            red_id,
            range_m=22000.0,
            bearing_deg=5.0,
            local_sensor_hit=False,
          )
        ],
      )
      missile_id = int(sim.fire_missile(blue_id, red_id))
      self.assertGreater(missile_id, 0)

      runtime = _missile_runtime(sim, missile_id)
      self.assertFalse(bool(runtime["midcourse_datalink_supported"]))
      self.assertFalse(bool(runtime["use_kalman_seeker"]))


if __name__ == "__main__":
  unittest.main()
