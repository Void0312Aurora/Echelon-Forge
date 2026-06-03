from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from gym_envs.universal_env_parts import AIR_COMBAT_HYBRID_V1_ACTION_MODE  # noqa: E402


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


def _missiles_remaining(env: UniversalEnv) -> int:
    return int(getattr(env.sim.get_agent_observation(env.agent_id), "missiles_remaining", -1))


def _step_until_fire_mask(env: UniversalEnv, *, expected_mask: int, max_steps: int = 180) -> dict:
    info: dict = {}
    for _ in range(max_steps):
        _obs, _reward, terminated, truncated, info = env.step(_action(fire=False, tms_up=True))
        if int(info.get("fire_mask", -1)) == int(expected_mask):
            return info
        if terminated or truncated:
            break
    raise AssertionError(f"expected fire_mask={expected_mask}, last info={info!r}")


class AirCombatA5EventActionRuntimeTests(unittest.TestCase):
    def _make_env(self) -> UniversalEnv:
        return UniversalEnv(
            _SCENARIO_PATH,
            include_visual=False,
            include_proprio=True,
            action_mode=AIR_COMBAT_HYBRID_V1_ACTION_MODE,
            mission_obs_mode="air_combat_c2_roe_v1",
            runtime_compatibility_enabled=True,
        )

    def test_fire_mask_zero_rejects_requested_fire_without_release(self) -> None:
        env = self._make_env()
        try:
            _obs, _info = env.reset(seed=20260603)
            env.loader.mission_cmd.update(
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

            _obs, _reward, _terminated, _truncated, info = env.step(_action(fire=True, tms_up=False))

            self.assertEqual(int(info["fire_mask"]), 0)
            self.assertTrue(bool(info["fire_once_requested"]))
            self.assertFalse(bool(info["fire_once_accepted"]))
            self.assertIn(info["fire_once_rejected_reason"], {"no_c2_authorization", "hold_state"})
            self.assertFalse(bool(info["release_executed"]))
            self.assertEqual(_missiles_remaining(env), missiles_before)
            self.assertEqual(float(env._last_action[9]), 0.0)
        finally:
            env.close()

    def test_authorized_fire_enters_fired_assess_and_suppresses_repeat_request(self) -> None:
        env = self._make_env()
        try:
            _obs, _info = env.reset(seed=20260604)
            ready_info = _step_until_fire_mask(env, expected_mask=1)
            self.assertEqual(ready_info["engagement_state"], "AuthorizedReady")
            missiles_before = _missiles_remaining(env)

            _obs, _reward, _terminated, _truncated, first_info = env.step(_action(fire=True, tms_up=False))

            self.assertTrue(bool(first_info["fire_once_requested"]))
            self.assertTrue(bool(first_info["fire_once_accepted"]))
            self.assertEqual(first_info["engagement_state"], "FiredAssess")
            self.assertEqual(int(first_info["fire_mask"]), 0)
            self.assertTrue(bool(first_info["release_executed"]))
            self.assertEqual(_missiles_remaining(env), missiles_before - 1)

            _obs, _reward, _terminated, _truncated, hold_info = env.step(_action(fire=False, tms_up=False))
            self.assertEqual(hold_info["engagement_state"], "FiredAssess")
            self.assertEqual(int(hold_info["fire_mask"]), 0)
            missiles_after_first = _missiles_remaining(env)

            _obs, _reward, _terminated, _truncated, repeat_info = env.step(_action(fire=True, tms_up=False))

            self.assertTrue(bool(repeat_info["fire_once_requested"]))
            self.assertFalse(bool(repeat_info["fire_once_accepted"]))
            self.assertTrue(bool(repeat_info["post_launch_suppressed"]))
            self.assertEqual(repeat_info["fire_once_rejected_reason"], "pending_assessment")
            self.assertEqual(repeat_info["engagement_state"], "FiredAssess")
            self.assertFalse(bool(repeat_info["release_executed"]))
            self.assertEqual(_missiles_remaining(env), missiles_after_first)
            self.assertEqual(float(env._last_action[9]), 0.0)
        finally:
            env.close()

    def test_explicit_reattack_command_reopens_fire_mask_without_auto_reattack(self) -> None:
        env = self._make_env()
        try:
            _obs, _info = env.reset(seed=20260605)
            _step_until_fire_mask(env, expected_mask=1)
            _obs, _reward, _terminated, _truncated, first_info = env.step(_action(fire=True, tms_up=False))
            self.assertEqual(first_info["engagement_state"], "FiredAssess")

            _obs, _reward, _terminated, _truncated, suppressed = env.step(_action(fire=False, tms_up=False))
            self.assertEqual(suppressed["engagement_state"], "FiredAssess")
            self.assertEqual(int(suppressed["fire_mask"]), 0)

            env.loader.mission_cmd.update(
                {
                    "shot_policy_state": 3,
                    "shot_budget_remaining": 1,
                    "pending_assessment": False,
                    "authorization_to_fire": True,
                    "engage_order_state": 2,
                    "wcs_state": 2,
                }
            )
            _obs, _reward, _terminated, _truncated, reattack_info = env.step(_action(fire=False, tms_up=False))

            self.assertEqual(reattack_info["engagement_state"], "ReattackReady")
            self.assertEqual(int(reattack_info["fire_mask"]), 1)
            self.assertTrue(bool(reattack_info["reattack_ready"]))
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
