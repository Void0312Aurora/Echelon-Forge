from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

from python.rl.execution_batch_predictor import ExecutionBatchPredictor


class LeaderBatchedVecEnv(DummyVecEnv):
    """
    DummyVecEnv variant that batches frozen execution-policy inference across leader envs.

    This keeps the high-level PPO interface unchanged while replacing N independent
    single-sample execution forwards with one batched GPU forward per low-level step.
    """

    def __init__(
        self,
        env_fns,
        *,
        execution_device: str = "cuda",
        execution_use_autocast: bool = True,
        step_executor_workers: int = 0,
    ):
        super().__init__(env_fns)
        self.execution_device = str(execution_device or "cuda")
        self.execution_use_autocast = bool(execution_use_autocast)
        self.step_executor_workers = max(0, int(step_executor_workers))
        self._step_executor = (
            ThreadPoolExecutor(max_workers=self.step_executor_workers)
            if self.step_executor_workers > 1
            else None
        )
        self._batch_predictor = self._build_batch_predictor()

    def _build_batch_predictor(self):
        if not self.envs:
            return None
        env0 = self.envs[0]
        if str(getattr(env0, "execution_backend", "")) != "frozen_model":
            return None
        model_path = getattr(env0, "execution_model_path", None)
        algo_name = getattr(env0, "execution_algo", "auto")
        if not model_path:
            return None
        for env in self.envs[1:]:
            if str(getattr(env, "execution_backend", "")) != "frozen_model":
                return None
            if getattr(env, "execution_model_path", None) != model_path:
                return None
            if getattr(env, "execution_algo", "auto") != algo_name:
                return None
        return ExecutionBatchPredictor(
            model_path,
            algo_name=str(algo_name or "auto"),
            device=self.execution_device,
            use_autocast=self.execution_use_autocast,
        )

    def step_wait(self):
        if self._batch_predictor is None:
            return super().step_wait()

        for env_idx in range(self.num_envs):
            self.envs[env_idx].begin_batched_leader_step(self.actions[env_idx])

        max_interval = max(int(getattr(env, "decision_interval_steps", 1)) for env in self.envs)
        for _ in range(max_interval):
            live_indices: list[int] = []
            obs_batch = []
            for env_idx, env in enumerate(self.envs):
                if env.has_pending_execution_step():
                    live_indices.append(env_idx)
                    obs_batch.append(env.current_execution_observation())
            if not live_indices:
                break
            action_batch = self._batch_predictor.predict_batch(obs_batch)
            if self._step_executor is None:
                for batch_idx, env_idx in enumerate(live_indices):
                    self.envs[env_idx].step_execution_once(action_batch[batch_idx])
            else:
                futures = [
                    self._step_executor.submit(self.envs[env_idx].step_execution_once, action_batch[batch_idx])
                    for batch_idx, env_idx in enumerate(live_indices)
                ]
                for future in futures:
                    future.result()

        for env_idx in range(self.num_envs):
            obs, self.buf_rews[env_idx], terminated, truncated, self.buf_infos[env_idx] = self.envs[env_idx].finish_batched_leader_step()
            self.buf_dones[env_idx] = terminated or truncated
            self.buf_infos[env_idx]["TimeLimit.truncated"] = truncated and not terminated

            if self.buf_dones[env_idx]:
                self.buf_infos[env_idx]["terminal_observation"] = obs
                obs, self.reset_infos[env_idx] = self.envs[env_idx].reset()
            self._save_obs(env_idx, obs)

        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), deepcopy(self.buf_infos)

    def close(self):
        try:
            if self._step_executor is not None:
                self._step_executor.shutdown(wait=True, cancel_futures=False)
                self._step_executor = None
        finally:
            super().close()
