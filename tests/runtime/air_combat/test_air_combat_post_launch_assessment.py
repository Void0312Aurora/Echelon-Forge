from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from gym_envs.universal_env_parts.common import gym as _gym # noqa: E402
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv # noqa: E402


_STAGE1_C2_SCENARIO = resolve_repo_path(
  "scenarios",
  "air_combat",
  "1v1",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)


def _fire_action(*, fire: bool) -> np.ndarray:
  action = np.zeros((12,), dtype=np.float32)
  action[3] = 0.65
  action[6] = 1.0
  action[7] = 1.0 if fire else 0.0
  action[8] = 1.0
  action[9] = 1.0 if fire else 0.0
  action[11] = 1.0
  return action.reshape(1, -1)


def _run_until_release(env: WorldBatchVecEnv, *, max_steps: int = 120) -> tuple[float, bool, dict]:
  env.reset()
  last_info: dict = {}
  for step in range(int(max_steps)):
    _obs, rewards, dones, infos = env.step(_fire_action(fire=(step % 2 == 0)))
    last_info = dict(infos[0])
    if bool(last_info.get("release_executed", False)):
      return float(rewards[0]), bool(dones[0]), last_info
  raise AssertionError(f"release was not observed; last_info={last_info!r}")


@unittest.skipIf(_gym is None, "WorldBatchVecEnv requires gymnasium")
class AirCombatPostLaunchAssessmentTests(unittest.TestCase):
  def _make_env(self, *, enabled: bool) -> WorldBatchVecEnv:
    return WorldBatchVecEnv(
      scenario_path=_STAGE1_C2_SCENARIO,
      n_envs=1,
      include_visual=False,
      include_proprio=True,
      action_mode="air_combat_hybrid_v1",
      mission_obs_mode="air_combat_c2_roe_v2",
      step_info_mode="full",
      execution_step_runtime_mode="compiled",
      flight_shaping_backend="compiled",
      worker_threads=0,
      air_combat_post_launch_assessment_enabled=enabled,
      air_combat_post_launch_assessment_stages=["A1-S1"],
      air_combat_post_launch_assessment_max_steps=4,
      air_combat_post_launch_assessment_gamma=0.5,
    )

  def test_disabled_post_launch_assessment_only_reports_release_step(self) -> None:
    env = self._make_env(enabled=False)
    try:
      _reward, _done, info = _run_until_release(env)
      self.assertTrue(bool(info.get("release_executed", False)))
      self.assertNotIn("post_launch_assessment", info)
    finally:
      env.close()

  def test_enabled_post_launch_assessment_runs_internal_consequence_steps(self) -> None:
    env = self._make_env(enabled=True)
    try:
      _reward, done, info = _run_until_release(env)
      self.assertTrue(bool(info.get("release_executed", False)))
      self.assertTrue(done)
      self.assertTrue(bool(info.get("post_launch_assessment", False)))
      self.assertGreater(int(info.get("post_launch_assessment_steps", 0)), 0)
      self.assertLessEqual(int(info.get("post_launch_assessment_steps", 0)), 4)
      self.assertEqual(str(info.get("post_launch_assessment_reward_mode")), "combat_consequence_terms")
      self.assertIn(str(info.get("termination_reason")), {"combat_win", "post_launch_assessment_timeout"})
    finally:
      env.close()


if __name__ == "__main__":
  unittest.main()
