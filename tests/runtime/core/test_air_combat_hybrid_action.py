from __future__ import annotations

import unittest

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from gym_envs.universal_env_parts import ( # noqa: E402
  AIR_COMBAT_HYBRID_V1_ACTION_MODE,
  air_combat_hybrid_effective_action,
  build_pilot_action,
  expected_action_dim,
  make_action_space,
  normalize_action,
)


class AirCombatHybridActionTests(unittest.TestCase):
  def test_action_space_declares_flat_transport_for_hybrid_policy(self) -> None:
    action_space = make_action_space(AIR_COMBAT_HYBRID_V1_ACTION_MODE)

    self.assertEqual(expected_action_dim(AIR_COMBAT_HYBRID_V1_ACTION_MODE), 12)
    self.assertEqual(tuple(action_space.shape), (12,))
    self.assertEqual(float(action_space.low[11]), 0.0)
    self.assertEqual(float(action_space.high[11]), 7.0)

  def test_effective_action_turns_trigger_intent_into_single_frame_pulse(self) -> None:
    raw = np.array(
      [0.1, -0.2, 0.3, 0.7, 0.25, -0.5, 0.9, 0.9, 0.8, 0.9, 0.9, 1.2],
      dtype=np.float32,
    )

    first = air_combat_hybrid_effective_action(raw)
    held = air_combat_hybrid_effective_action(raw, previous_intent=raw)
    released = raw.copy()
    released[[7, 9, 10]] = 0.0
    pressed_again = air_combat_hybrid_effective_action(raw, previous_intent=released)

    self.assertEqual(float(first[6]), 1.0)
    self.assertEqual(float(first[8]), 1.0)
    self.assertEqual(float(first[7]), 1.0)
    self.assertEqual(float(first[9]), 1.0)
    self.assertEqual(float(first[10]), 1.0)
    self.assertEqual(float(first[11]), 1.0)

    self.assertEqual(float(held[7]), 0.0)
    self.assertEqual(float(held[9]), 0.0)
    self.assertEqual(float(held[10]), 0.0)

    self.assertEqual(float(pressed_again[7]), 1.0)
    self.assertEqual(float(pressed_again[9]), 1.0)
    self.assertEqual(float(pressed_again[10]), 1.0)

  def test_build_pilot_action_uses_effective_hybrid_transport(self) -> None:
    action_space = make_action_space(AIR_COMBAT_HYBRID_V1_ACTION_MODE)
    raw = np.array(
      [0.1, -0.2, 0.3, 0.7, 0.25, -0.5, 0.9, 0.9, 0.8, 0.9, 0.9, 1.2],
      dtype=np.float32,
    )
    normalized = normalize_action(raw, action_space=action_space, action_mode=AIR_COMBAT_HYBRID_V1_ACTION_MODE)
    effective = air_combat_hybrid_effective_action(normalized)

    pilot = build_pilot_action(effective, action_mode=AIR_COMBAT_HYBRID_V1_ACTION_MODE)

    self.assertAlmostEqual(float(pilot.stick_pitch), 0.1, places=5)
    self.assertAlmostEqual(float(pilot.throttle), 0.7, places=5)
    self.assertTrue(bool(pilot.radar_active))
    self.assertTrue(bool(pilot.tms_up))
    self.assertTrue(bool(pilot.master_arm))
    self.assertTrue(bool(pilot.fire_weapon))
    self.assertTrue(bool(pilot.fire_gun))
    self.assertEqual(int(pilot.weapon_select_id), 1)
    self.assertAlmostEqual(float(pilot.radar_scan_az), 15.0, places=5)
    self.assertAlmostEqual(float(pilot.radar_scan_el), -15.0, places=5)


if __name__ == "__main__":
  unittest.main()
