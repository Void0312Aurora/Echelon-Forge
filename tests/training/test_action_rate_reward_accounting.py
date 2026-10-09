from __future__ import annotations

import copy
import json

import gymnasium as gym
import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.rl.control.wrappers import MultiTimescaleActionController, MultiTimescaleActionWrapper
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv
from python.training.diagnostics import record_basic_step_diagnostics, record_reward_term_diagnostics
from python.training_callbacks import CMODiagnosticsCallback
from tests.support._world_batch_vec_env_test_support import _inline_vec_env_scenario


OPTIONS = dict(hold_steps=1, low_freq_indices=(), snap_binary_indices=(),
               center_deadband_indices=(), action_rate_penalty_coef=1.0)


class RewardEnv(gym.Env):
    action_space = gym.spaces.Box(-1.0, 1.0, (8,), dtype=np.float32)
    observation_space = gym.spaces.Box(-1.0, 1.0, (1,), dtype=np.float32)

    def __init__(self, reward, info):
        self.reward = reward
        self.info = info

    def step(self, action):
        return np.zeros(1, dtype=np.float32), self.reward, False, False, self.info


@pytest.mark.parametrize("path", ["controller", "wrapper"])
@pytest.mark.parametrize("reward,tracked", [(3.0, 3.0), (-1.0, -1.5)])
def test_final_reward_accounting_preserves_base_info_and_untracked_residual(path, reward, tracked):
    info = {"reward_terms": {"total": reward, "tracked_total": tracked,
                             "untracked": reward - tracked, "survival": tracked}}
    original = copy.deepcopy(info)
    if path == "controller":
        controller = MultiTimescaleActionController(
            action_space=RewardEnv.action_space, loader_getter=lambda: None,
            dt_getter=lambda: 0.05, **OPTIONS,
        )
        def step(action):
            prepared = controller.prepare_action(action)
            return controller.finalize_step_result(None, reward, info, prepared)[1:]
    else:
        wrapper = MultiTimescaleActionWrapper(RewardEnv(reward, info), **OPTIONS)
        def step(action):
            _, result, _, _, details = wrapper.step(action)
            return result, details
    for value, penalty in ((0.5, 0.0), (-0.5, 1.0)):
        returned, details = step(np.full(8, value, dtype=np.float32))
        terms = details["reward_terms"]
        assert returned == pytest.approx(reward - penalty)
        assert terms["total"] == returned
        assert terms["action_rate_penalty"] == -penalty
        assert terms["tracked_total"] == pytest.approx(tracked - penalty)
        assert terms["untracked"] == pytest.approx(reward - tracked)
        assert terms["tracked_total"] + terms["untracked"] == pytest.approx(returned)
        assert info == original


def test_partial_breakdown_infers_tracked_total():
    controller = MultiTimescaleActionController(
        action_space=RewardEnv.action_space, loader_getter=lambda: None,
        dt_getter=lambda: 0.05, **OPTIONS,
    )
    for value in (0.5, -0.5):
        prepared = controller.prepare_action(np.full(8, value, dtype=np.float32))
        _, reward, info = controller.finalize_step_result(None, 3.0, {"reward_terms": {"survival": 3.0}}, prepared)
    assert reward == 2.0
    assert info["reward_terms"]["tracked_total"] == 2.0
    assert info["reward_terms"]["untracked"] == 0.0


def test_vecenv_reward_and_diagnostic_total_agree_after_nonzero_penalty(tmp_path):
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 3
    scenario["rewards"] = {"survival": 3.0}
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    env = WorldBatchVecEnv(scenario_path=str(scenario_path), n_envs=1,
                          include_visual=False, include_proprio=False,
                          action_wrapper_kwargs=OPTIONS)
    try:
        env.reset()
        env.step(np.full((1, 17), 0.5, dtype=np.float32))
        obs, rewards, _, infos = env.step(np.full((1, 17), 0.1, dtype=np.float32))
        terms = infos[0]["reward_terms"]
        assert infos[0]["action_rate_penalty"] > 0
        assert terms["total"] == pytest.approx(float(rewards[0]), abs=1e-6)
        assert terms["tracked_total"] + terms["untracked"] == pytest.approx(terms["total"])
        assert terms["action_rate_penalty"] == -infos[0]["action_rate_penalty"]
        class Logger:
            def __init__(self):
                self.records = {}
            def record(self, key, value):
                self.records[key] = float(value)
        logger = Logger()
        record_basic_step_diagnostics(logger=logger, obs=obs, rewards=rewards)
        record_reward_term_diagnostics(logger=logger, infos=infos,
                                       reward_keys=CMODiagnosticsCallback.STEP_REWARD_KEYS)
        assert logger.records["diag/rew_total"] == pytest.approx(logger.records["diag/reward_mean"], abs=1e-6)
        assert logger.records["diag/rew_action_rate_penalty"] == pytest.approx(terms["action_rate_penalty"])
    finally:
        env.close()
