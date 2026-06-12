from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from gym_envs.universal_env_parts import AIR_COMBAT_HYBRID_V1_ACTION_MODE # noqa: E402
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv # noqa: E402


_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "air_combat",
  "1v1",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)


def _action(*, fire: bool = False, master_arm: bool = True, radar_active: bool = True, tms_up: bool = False):
  action = np.zeros((12,), dtype=np.float32)
  action[3] = 0.62
  action[6] = 1.0 if radar_active else 0.0
  action[7] = 1.0 if tms_up else 0.0
  action[8] = 1.0 if master_arm else 0.0
  action[9] = 1.0 if fire else 0.0
  action[11] = 1.0
  return action


def _step(env: WorldBatchVecEnv, action: np.ndarray) -> tuple[dict, bool]:
  _obs, _reward, done, infos = env.step(action.reshape(1, -1))
  return dict(infos[0]), bool(done[0])


def _missiles_remaining(env: WorldBatchVecEnv) -> int:
  return int(getattr(env.envs[0].last_truth, "missiles_remaining", -1))


def _step_until_fire_mask(env: WorldBatchVecEnv, *, expected_mask: int, max_steps: int = 180) -> dict:
  info: dict = {}
  for _ in range(max_steps):
    info, done = _step(env, _action(fire=False, tms_up=True))
    if int(info.get("fire_mask", -1)) == int(expected_mask):
      return info
    if done:
      break
  raise AssertionError(f"expected fire_mask={expected_mask}, last info={info!r}")


class AirCombatFireActionReleaseGateTests(unittest.TestCase):
  def _make_env(self) -> WorldBatchVecEnv:
    return WorldBatchVecEnv(
      scenario_path=_SCENARIO_PATH,
      n_envs=1,
      include_visual=False,
      include_proprio=True,
      action_mode=AIR_COMBAT_HYBRID_V1_ACTION_MODE,
      mission_obs_mode="air_combat_c2_roe_v1",
    )

  def test_fire_mask_zero_rejects_requested_fire_without_release(self) -> None:
    env = self._make_env()
    try:
      env.seed(20260603)
      env.reset()
      env.envs[0].loader.mission_cmd.update(
        {
          "wcs_state": 1,
          "authorization_to_fire": False,
          "engage_order_state": 3,
          "shot_policy_state": 0,
          "shot_budget_remaining": 0,
          "pending_assessment": False,
        }
      )
      _step_until_fire_mask(env, expected_mask=0)
      missiles_before = _missiles_remaining(env)

      info, _done = _step(env, _action(fire=True, tms_up=False))

      self.assertEqual(int(info["fire_mask"]), 0)
      self.assertTrue(bool(info["fire_once_requested"]))
      self.assertFalse(bool(info["fire_once_accepted"]))
      self.assertIn(info["fire_once_rejected_reason"], {"no_c2_authorization", "hold_state"})
      self.assertFalse(bool(info["release_executed"]))
      self.assertEqual(_missiles_remaining(env), missiles_before)
      self.assertEqual(float(env.envs[0].last_action[9]), 0.0)
    finally:
      env.close()

  def test_authorized_fire_enters_fired_assess_and_suppresses_repeat_request(self) -> None:
    env = self._make_env()
    try:
      env.seed(20260604)
      env.reset()
      ready_info = _step_until_fire_mask(env, expected_mask=1)
      self.assertEqual(ready_info["engagement_state"], "AuthorizedReady")
      missiles_before = _missiles_remaining(env)

      first_info, _done = _step(env, _action(fire=True, tms_up=False))

      self.assertTrue(bool(first_info["fire_once_requested"]))
      self.assertTrue(bool(first_info["fire_once_accepted"]))
      self.assertEqual(first_info["engagement_state"], "FiredAssess")
      self.assertEqual(int(first_info["fire_mask"]), 0)
      self.assertTrue(bool(first_info["release_executed"]))
      self.assertEqual(_missiles_remaining(env), missiles_before - 1)

      hold_info, _done = _step(env, _action(fire=False, tms_up=False))
      self.assertEqual(hold_info["engagement_state"], "FiredAssess")
      self.assertEqual(int(hold_info["fire_mask"]), 0)
      missiles_after_first = _missiles_remaining(env)

      repeat_info, _done = _step(env, _action(fire=True, tms_up=False))

      self.assertTrue(bool(repeat_info["fire_once_requested"]))
      self.assertFalse(bool(repeat_info["fire_once_accepted"]))
      self.assertTrue(bool(repeat_info["post_launch_suppressed"]))
      self.assertEqual(repeat_info["fire_once_rejected_reason"], "pending_assessment")
      self.assertEqual(repeat_info["engagement_state"], "FiredAssess")
      self.assertFalse(bool(repeat_info["release_executed"]))
      self.assertEqual(_missiles_remaining(env), missiles_after_first)
      self.assertEqual(float(env.envs[0].last_action[9]), 0.0)
    finally:
      env.close()

  def test_fire_once_derives_master_arm_for_authorized_event(self) -> None:
    env = self._make_env()
    try:
      env.seed(20260608)
      env.reset()
      _step_until_fire_mask(env, expected_mask=1)
      missiles_before = _missiles_remaining(env)

      info, _done = _step(env, _action(fire=True, master_arm=False, tms_up=False))

      self.assertTrue(bool(info["fire_once_requested"]))
      self.assertTrue(bool(info["fire_once_accepted"]))
      self.assertEqual(info["fire_once_rejected_reason"], "")
      self.assertTrue(bool(info["release_executed"]))
      self.assertEqual(_missiles_remaining(env), missiles_before - 1)
      self.assertEqual(float(env.envs[0].last_action[8]), 1.0)
      self.assertEqual(float(env.envs[0].last_action[9]), 1.0)
    finally:
      env.close()

  def test_explicit_reattack_command_reopens_fire_mask_without_auto_reattack(self) -> None:
    env = self._make_env()
    try:
      env.seed(20260605)
      env.reset()
      _step_until_fire_mask(env, expected_mask=1)
      first_info, _done = _step(env, _action(fire=True, tms_up=False))
      self.assertEqual(first_info["engagement_state"], "FiredAssess")

      suppressed, _done = _step(env, _action(fire=False, tms_up=False))
      self.assertEqual(suppressed["engagement_state"], "FiredAssess")
      self.assertEqual(int(suppressed["fire_mask"]), 0)

      env.envs[0].loader.mission_cmd.update(
        {
          "shot_policy_state": 3,
          "shot_budget_remaining": 1,
          "pending_assessment": False,
          "authorization_to_fire": True,
          "engage_order_state": 2,
          "wcs_state": 2,
        }
      )
      reattack_info, _done = _step(env, _action(fire=False, tms_up=False))

      self.assertEqual(reattack_info["engagement_state"], "ReattackReady")
      self.assertEqual(int(reattack_info["fire_mask"]), 1)
      self.assertTrue(bool(reattack_info["reattack_ready"]))
    finally:
      env.close()


if __name__ == "__main__":
  unittest.main()
