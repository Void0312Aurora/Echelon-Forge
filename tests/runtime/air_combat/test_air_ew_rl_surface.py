"""Opt-in RL observation projection for the versioned Air EW state.

Pins the bounded slice that exposes the opt-in ``ew_state`` observation
component while leaving canonical env-config action admission unchanged:

* a world-batch env built with ``air_ew_hybrid_v2`` steps and its native
  PilotAction carries the countermeasure/jammer tail (read back from the
  instrument projection);
* with ``include_ew_state=True`` the observation carries ``ew_state`` with the
  declared shape/bounds and its values track the native state;
* the default flag leaves the observation keys/shapes exactly as before;
* the SB3 PPO stack accepts the 16D action space with ``ew_state`` present.
"""

from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from gym_envs.universal_env_parts import (  # noqa: E402
  EW_STATE_DIM,
  EW_STATE_FIELDS,
  EW_STATE_OBSERVATION_KEY,
  build_ew_state_observation,
)
from python.env_config import resolve_env_settings  # noqa: E402
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402

try:
  from stable_baselines3 import PPO  # noqa: E402

  from python.models.transformer import TemporalTransformerExtractor, TransformerExtractor  # noqa: E402
except Exception:  # pragma: no cover - optional training stack
  PPO = None
  TemporalTransformerExtractor = None
  TransformerExtractor = None

try:
  from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv  # noqa: E402
except Exception:  # pragma: no cover - optional gymnasium
  CooperativeWorldBatchVecEnv = None


_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "air_combat",
  "air_combat_1v1_headon_sensor_smoke_v1.json",
)
_SEED = 20260516
_FIELD = {name: idx for idx, name in enumerate(EW_STATE_FIELDS)}


def _make_env(*, action_mode: str, include_ew_state: bool, n_envs: int = 1) -> WorldBatchVecEnv:
  return WorldBatchVecEnv(
    scenario_path=_SCENARIO_PATH,
    n_envs=n_envs,
    include_visual=False,
    include_proprio=False,
    include_ew_state=include_ew_state,
    action_mode=action_mode,
    mission_obs_mode="basic",
    execution_step_runtime_mode="compiled",
    flight_shaping_backend="compiled",
    worker_threads=1,
  )


def _cruise_action(action_dim: int) -> np.ndarray:
  action = np.zeros((1, action_dim), dtype=np.float32)
  action[0, 3] = 0.7  # throttle; everything else neutral / switches off
  return action


def _settle(env: WorldBatchVecEnv, action_dim: int):
  """Reset and take one neutral frame.

  The reset-frame InstrumentState predates the first native instrument/EW
  projection, so it still carries the -1 "absent" EW sentinels; one neutral
  step produces the first projected snapshot.
  """

  env.seed(_SEED)
  env.reset()
  obs, _r, _d, _i = env.step(_cruise_action(action_dim))
  return obs


class AirEWHybridV2WorldBatchTests(unittest.TestCase):
  def test_v2_env_steps_random_actions_and_projects_the_jammer_tail(self) -> None:
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=False)
    try:
      self.assertEqual(tuple(env.action_space.shape), (16,))
      env.action_space.seed(_SEED)
      env.seed(_SEED)
      env.reset()
      for _ in range(3):
        sample = np.asarray(env.action_space.sample(), dtype=np.float32).reshape(1, -1)
        _obs, rewards, _dones, _infos = env.step(sample)
        self.assertTrue(np.isfinite(rewards).all())

      inst = env.envs[0].last_inst
      self.assertGreaterEqual(int(inst.jammer_mode), 0, "premise: the scenario F-16C carries a jammer pod")
      self.assertFalse(bool(inst.jammer_budget_enabled))
      self.assertEqual(float(inst.jammer_transmit_remaining_s), -1.0)
      self.assertEqual(float(inst.jammer_cooldown_remaining_s), -1.0)

      # Transmit with spot noise (technique code 1.x floors to 1).
      action = _cruise_action(16)
      action[0, 14] = 1.0
      action[0, 15] = 1.6
      env.step(action)
      inst = env.envs[0].last_inst
      self.assertTrue(bool(inst.jammer_transmitting))
      self.assertEqual(int(inst.jammer_mode), 1)
      self.assertGreaterEqual(float(inst.jammer_transmit_start_time_s), 0.0)
      self.assertGreaterEqual(float(inst.jammer_snapshot_time_s), 0.0)

      # Releasing the transmit switch stands the pod down.
      env.step(_cruise_action(16))
      inst = env.envs[0].last_inst
      self.assertFalse(bool(inst.jammer_transmitting))
      self.assertEqual(float(inst.jammer_transmit_start_time_s), -1.0)
    finally:
      env.close()

  def test_v2_chaff_tail_reaches_the_native_dispenser(self) -> None:
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=False)
    try:
      _settle(env, 16)
      before = int(env.envs[0].last_inst.countermeasure_chaff_remaining)
      self.assertGreater(before, 0)
      action = _cruise_action(16)
      action[0, 12] = 1.0
      released = False
      for _ in range(20):
        env.step(action)
        if int(env.envs[0].last_inst.countermeasure_chaff_remaining) < before:
          released = True
          break
      self.assertTrue(released, "chaff must release when the native interval permits it")
      self.assertEqual(int(env.envs[0].last_inst.countermeasure_chaff_remaining), before - 1)
    finally:
      env.close()


class AirEWStateObservationTests(unittest.TestCase):
  def test_ew_state_space_declares_shape_and_bounds(self) -> None:
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=True)
    try:
      space = env.observation_space[EW_STATE_OBSERVATION_KEY]
      self.assertEqual(tuple(space.shape), (EW_STATE_DIM,))
      self.assertEqual(EW_STATE_DIM, 6)
      self.assertEqual(space.dtype, np.float32)
      np.testing.assert_array_equal(space.low, np.array([-1.0, -1.0, -1.0, 0.0, -1.0, -1.0], dtype=np.float32))
      self.assertEqual(float(space.high[_FIELD["jammer_transmitting"]]), 1.0)
      self.assertEqual(float(space.high[_FIELD["jammer_mode"]]), 2.0)
      for name in ("chaff_remaining", "flare_remaining", "seconds_since_last_release",
                   "seconds_since_jammer_transmit_start"):
        self.assertTrue(np.isinf(space.high[_FIELD[name]]), name)
    finally:
      env.close()

  def test_ew_state_tracks_native_countermeasure_and_jammer_state(self) -> None:
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=True)
    try:
      env.seed(_SEED)
      obs = env.reset()
      self.assertIn(EW_STATE_OBSERVATION_KEY, obs)
      self.assertEqual(obs[EW_STATE_OBSERVATION_KEY].shape, (1, EW_STATE_DIM))
      space = env.observation_space[EW_STATE_OBSERVATION_KEY]
      # Reset frame: whatever the native snapshot holds, ew_state mirrors it.
      reset_inst = env.envs[0].last_inst
      reset_ew = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertTrue(space.contains(reset_ew.astype(np.float32)))
      self.assertEqual(reset_ew[_FIELD["chaff_remaining"]], float(reset_inst.countermeasure_chaff_remaining))
      self.assertEqual(reset_ew[_FIELD["jammer_mode"]], float(reset_inst.jammer_mode))

      obs, _r, _d, _i = env.step(_cruise_action(16))
      ew0 = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertTrue(space.contains(ew0.astype(np.float32)))
      inst = env.envs[0].last_inst
      self.assertEqual(ew0[_FIELD["chaff_remaining"]], float(inst.countermeasure_chaff_remaining))
      self.assertEqual(ew0[_FIELD["flare_remaining"]], float(inst.countermeasure_flare_remaining))
      self.assertGreaterEqual(ew0[_FIELD["seconds_since_last_release"]], 0.0)
      self.assertEqual(ew0[_FIELD["jammer_transmitting"]], 0.0)
      self.assertGreaterEqual(ew0[_FIELD["jammer_mode"]], 0.0, "premise: installed jammer pod")
      self.assertEqual(ew0[_FIELD["seconds_since_jammer_transmit_start"]], -1.0)
      initial_chaff = float(ew0[_FIELD["chaff_remaining"]])
      dt = float(env._world_time_step(0))

      # Hold the chaff program switch until the native dispenser interval
      # admits a release; subsequent frames remain interval-gated.
      chaff = _cruise_action(16)
      chaff[0, 12] = 1.0
      released = False
      for _ in range(20):
        obs, _r, _d, _i = env.step(chaff)
        ew = obs[EW_STATE_OBSERVATION_KEY][0]
        if ew[_FIELD["chaff_remaining"]] < initial_chaff:
          released = True
          break
      self.assertTrue(released, "chaff must release when the native interval permits it")
      self.assertEqual(ew[_FIELD["chaff_remaining"]], initial_chaff - 1.0)
      self.assertGreaterEqual(ew[_FIELD["seconds_since_last_release"]], 0.0)
      self.assertLessEqual(ew[_FIELD["seconds_since_last_release"]], dt + 1.0e-4)

      interval = float(env.envs[0].last_inst.countermeasure_release_interval_s)
      self.assertGreater(interval, dt, "premise: the release interval spans several frames")
      within_interval = max(1, int(np.floor(interval / dt)) - 2)
      for _ in range(within_interval):
        obs, _r, _d, _i = env.step(chaff)
      ew = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertEqual(ew[_FIELD["chaff_remaining"]], initial_chaff - 1.0)
      self.assertGreater(ew[_FIELD["seconds_since_last_release"]], 0.0)
      self.assertLess(ew[_FIELD["seconds_since_last_release"]], interval)

      released_again = False
      for _ in range(int(np.ceil(interval / dt)) + 4):
        obs, _r, _d, _i = env.step(chaff)
        ew = obs[EW_STATE_OBSERVATION_KEY][0]
        if ew[_FIELD["chaff_remaining"]] < initial_chaff - 1.0:
          released_again = True
          break
      self.assertTrue(released_again, "chaff must decrement again after the release interval")
      self.assertEqual(ew[_FIELD["chaff_remaining"]], initial_chaff - 2.0)
      self.assertEqual(ew[_FIELD["chaff_remaining"]], float(env.envs[0].last_inst.countermeasure_chaff_remaining))

      # Jammer transmit request: transmitting flips to 1 and the elapsed
      # transmit time starts counting from the native stamp.
      jam = _cruise_action(16)
      jam[0, 14] = 1.0
      jam[0, 15] = 2.0  # DRFM
      obs, _r, _d, _i = env.step(jam)
      ew = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertEqual(ew[_FIELD["jammer_transmitting"]], 1.0)
      self.assertEqual(ew[_FIELD["jammer_mode"]], 2.0)
      first_elapsed = float(ew[_FIELD["seconds_since_jammer_transmit_start"]])
      self.assertGreaterEqual(first_elapsed, 0.0)
      for _ in range(4):
        obs, _r, _d, _i = env.step(jam)
      ew = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertAlmostEqual(
        float(ew[_FIELD["seconds_since_jammer_transmit_start"]]),
        first_elapsed + 4.0 * dt,
        places=4,
      )
      self.assertTrue(space.contains(ew.astype(np.float32)))

      obs, _r, _d, _i = env.step(_cruise_action(16))
      ew = obs[EW_STATE_OBSERVATION_KEY][0]
      self.assertEqual(ew[_FIELD["jammer_transmitting"]], 0.0)
      self.assertEqual(ew[_FIELD["seconds_since_jammer_transmit_start"]], -1.0)
    finally:
      env.close()

  def test_ew_state_projection_keeps_absent_equipment_sentinels(self) -> None:
    inst = ef_py.InstrumentState()
    ew = build_ew_state_observation(inst, 12.5)
    np.testing.assert_array_equal(ew, np.array([-1.0, -1.0, -1.0, 0.0, -1.0, -1.0], dtype=np.float32))
    # A stale transmitting flag without a pod is not reported as transmitting.
    inst.jammer_transmitting = True
    inst.jammer_transmit_start_time_s = 3.0
    ew = build_ew_state_observation(inst, 12.5)
    self.assertEqual(ew[_FIELD["jammer_transmitting"]], 0.0)
    self.assertEqual(ew[_FIELD["seconds_since_jammer_transmit_start"]], -1.0)

  def test_default_flag_keeps_observation_keys_and_shapes_unchanged(self) -> None:
    baseline = _make_env(action_mode="air_combat_hybrid_v1", include_ew_state=False)
    candidate = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=False)
    try:
      baseline_spaces = {key: (space.shape, space.dtype) for key, space in baseline.observation_space.spaces.items()}
      candidate_spaces = {key: (space.shape, space.dtype) for key, space in candidate.observation_space.spaces.items()}
      self.assertEqual(candidate_spaces, baseline_spaces)
      self.assertNotIn(EW_STATE_OBSERVATION_KEY, candidate_spaces)
      self.assertEqual(candidate_spaces["instruments"][0], (42,))

      baseline.seed(_SEED)
      candidate.seed(_SEED)
      baseline_obs = baseline.reset()
      candidate_obs = candidate.reset()
      self.assertEqual(list(candidate_obs.keys()), list(baseline_obs.keys()))
      for key, value in baseline_obs.items():
        self.assertEqual(candidate_obs[key].shape, value.shape, key)
      baseline_step, _r, _d, _i = baseline.step(_cruise_action(12))
      candidate_step, _r, _d, _i = candidate.step(_cruise_action(16))
      self.assertEqual(list(candidate_step.keys()), list(baseline_step.keys()))
      for key, value in baseline_step.items():
        self.assertEqual(candidate_step[key].shape, value.shape, key)
    finally:
      baseline.close()
      candidate.close()

  def test_env_config_flag_builds_the_ew_state_env(self) -> None:
    settings = resolve_env_settings(
      {"env": {"action_mode": "air_combat_hybrid_v1", "include_ew_state": True, "mission_obs_mode": "basic"}},
      object(),
    )
    env = WorldBatchVecEnv(scenario_path=_SCENARIO_PATH, n_envs=1, worker_threads=1, **settings)
    try:
      self.assertEqual(tuple(env.action_space.shape), (12,))
      self.assertIn(EW_STATE_OBSERVATION_KEY, env.observation_space.spaces)
    finally:
      env.close()


class AirEWCooperativeObservationTests(unittest.TestCase):
  def test_cooperative_env_carries_ew_state_per_slot(self) -> None:
    if CooperativeWorldBatchVecEnv is None:
      self.skipTest("gymnasium is not available in the active interpreter")
    with tempfile.TemporaryDirectory() as tmpdir:
      from tests.runtime.multi_agent.test_cooperative_vec_env_tasking import _cooperative_cruise_scenario

      scenario_path = f"{tmpdir}/cooperative_scenario.json"
      with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(_cooperative_cruise_scenario(), f, ensure_ascii=True)
      vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        include_ew_state=True,
        action_mode="air_ew_hybrid_v1",
        mission_obs_mode="basic",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=1,
      )
      try:
        vec_env.seed(_SEED)
        vec_env.reset()
        neutral = np.zeros((2, 14), dtype=np.float32)
        neutral[:, 3] = 0.7
        obs, _r, _d, _i = vec_env.step(neutral)
        self.assertEqual(obs[EW_STATE_OBSERVATION_KEY].shape, (2, EW_STATE_DIM))
        initial = obs[EW_STATE_OBSERVATION_KEY].copy()
        self.assertTrue(bool(np.all(initial[:, _FIELD["chaff_remaining"]] > 0.0)))
        self.assertTrue(bool(np.all(initial[:, _FIELD["flare_remaining"]] > 0.0)))
        actions = neutral.copy()
        actions[0, 12] = 1.0  # lead: chaff
        actions[1, 13] = 1.0  # wing: flare
        released = False
        for _ in range(20):
          obs, _r, _d, _i = vec_env.step(actions)
          ew = obs[EW_STATE_OBSERVATION_KEY]
          if (
            ew[0, _FIELD["chaff_remaining"]] < initial[0, _FIELD["chaff_remaining"]]
            and ew[1, _FIELD["flare_remaining"]] < initial[1, _FIELD["flare_remaining"]]
          ):
            released = True
            break
        self.assertTrue(released, "both cooperative dispensers must release when permitted")
        self.assertEqual(ew[0, _FIELD["chaff_remaining"]], initial[0, _FIELD["chaff_remaining"]] - 1.0)
        self.assertEqual(ew[0, _FIELD["flare_remaining"]], initial[0, _FIELD["flare_remaining"]])
        self.assertEqual(ew[1, _FIELD["flare_remaining"]], initial[1, _FIELD["flare_remaining"]] - 1.0)
        self.assertEqual(ew[1, _FIELD["chaff_remaining"]], initial[1, _FIELD["chaff_remaining"]])
        for slot in (0, 1):
          self.assertEqual(
            ew[slot, _FIELD["chaff_remaining"]],
            float(vec_env._slots[slot].last_inst.countermeasure_chaff_remaining),
          )
      finally:
        vec_env.close()


class AirEWPolicyStackTests(unittest.TestCase):
  def _ppo(self, env, extractor_class):
    return PPO(
      "MultiInputPolicy",
      env,
      n_steps=2,
      batch_size=2,
      n_epochs=1,
      learning_rate=3.0e-4,
      gamma=0.99,
      gae_lambda=0.95,
      ent_coef=0.0,
      vf_coef=0.5,
      max_grad_norm=0.5,
      device="cpu",
      verbose=0,
      policy_kwargs={
        "features_extractor_class": extractor_class,
        "features_extractor_kwargs": {"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
        "net_arch": {"pi": [32], "vf": [32]},
      },
    )

  def test_ppo_accepts_the_16d_action_space_with_ew_state(self) -> None:
    if PPO is None:
      self.skipTest("stable_baselines3 is not available in the active interpreter")
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=True)
    try:
      env.seed(_SEED)
      model = self._ppo(env, TransformerExtractor)
      extractor = model.policy.features_extractor
      self.assertTrue(extractor.has_ew_state)
      model.learn(total_timesteps=4)
      action, _ = model.predict(env.reset(), deterministic=True)
      self.assertEqual(tuple(np.asarray(action).shape), (1, 16))
      self.assertTrue(np.isfinite(action).all())
    finally:
      env.close()

  def test_extractor_without_ew_state_keeps_its_parameter_set(self) -> None:
    if PPO is None:
      self.skipTest("stable_baselines3 is not available in the active interpreter")
    env = _make_env(action_mode="air_ew_hybrid_v2", include_ew_state=False)
    try:
      extractor = TransformerExtractor(env.observation_space, features_dim=32, n_heads=4, n_layers=1)
      self.assertFalse(extractor.has_ew_state)
      self.assertFalse(hasattr(extractor, "embed_ew_state"))
      self.assertEqual(int(extractor.type_embed.num_embeddings), 4)
    finally:
      env.close()

  def test_temporal_extractor_refuses_ew_state_explicitly(self) -> None:
    if PPO is None:
      self.skipTest("stable_baselines3 is not available in the active interpreter")
    from gymnasium import spaces

    from gym_envs.universal_env_parts import make_action_space, make_observation_space

    space = make_observation_space(
      action_space=make_action_space("air_ew_hybrid_v2"),
      mission_obs_mode="basic",
      include_visual=False,
      include_proprio=True,
      arb_height=48,
      arb_width=96,
      arb_channels=10,
      temporal_history_len=4,
      include_ew_state=True,
    )
    self.assertIsInstance(space, spaces.Dict)
    with self.assertRaisesRegex(ValueError, "does not consume the opt-in 'ew_state'"):
      TemporalTransformerExtractor(space, features_dim=32, n_heads=4, n_layers=1)


if __name__ == "__main__":
  unittest.main()
