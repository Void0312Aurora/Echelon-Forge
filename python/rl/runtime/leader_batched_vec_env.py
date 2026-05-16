from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
import torch
from stable_baselines3.common.vec_env import DummyVecEnv

from gym_envs.leader_env_parts import load_policy
from python.rl.runtime.execution_runtime import unwrap_nested_env
from .leader_world_batch_runtime import LeaderWorldBatchExecutionRuntimeGroup


class ExecutionBatchPredictor:
    """
    Shared execution-policy inference helper for leader-layer training.

    This stays local to `LeaderBatchedVecEnv` because no other maintained runtime uses it.
    """

    def __init__(
        self,
        model_path: str,
        *,
        algo_name: str = "auto",
        device: str = "cuda",
        use_autocast: bool = True,
    ) -> None:
        self.device = str(device or "cuda")
        self.use_autocast = bool(use_autocast)
        self.model = load_policy(model_path, algo_name=algo_name, device=self.device)
        self.policy = self.model.policy
        self.policy.set_training_mode(False)

    def _stack_observations(self, obs_batch: list[dict[str, Any]]) -> dict[str, np.ndarray]:
        if not obs_batch:
            raise ValueError("ExecutionBatchPredictor requires at least one observation")
        keys = list(obs_batch[0].keys())
        return {
            key: np.stack([np.asarray(obs[key]) for obs in obs_batch], axis=0)
            for key in keys
        }

    def predict_batch(self, obs_batch: list[dict[str, Any]]) -> np.ndarray:
        batch_obs = self._stack_observations(obs_batch)
        obs_tensor, _ = self.policy.obs_to_tensor(batch_obs)
        obs_tensor = {
            key: value.to(self.device, non_blocking=self.device.startswith("cuda"))
            for key, value in obs_tensor.items()
        }
        autocast_enabled = self.use_autocast and self.device.startswith("cuda")
        with torch.inference_mode(), torch.autocast("cuda", enabled=autocast_enabled):
            actions = self.policy._predict(obs_tensor, deterministic=True)
        actions_np = actions.detach().cpu().numpy()
        if bool(getattr(self.policy, "squash_output", False)):
            actions_np = self.policy.unscale_action(actions_np)
        return np.asarray(actions_np, dtype=np.float32)


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
        use_shared_world_batch_runtime: bool = False,
        world_batch_threads: int | None = None,
    ):
        super().__init__(env_fns)
        self.execution_device = str(execution_device or "cuda")
        self.execution_use_autocast = bool(execution_use_autocast)
        self.step_executor_workers = max(0, int(step_executor_workers))
        self.use_shared_world_batch_runtime = bool(use_shared_world_batch_runtime)
        self.world_batch_threads = None if world_batch_threads is None else max(0, int(world_batch_threads))
        self._step_executor = (
            ThreadPoolExecutor(max_workers=self.step_executor_workers)
            if self.step_executor_workers > 1
            else None
        )
        self._batch_predictor = None
        self._shared_execution_group = None
        self._shared_execution_group_reason = ""
        try:
            self._batch_predictor = self._build_batch_predictor()
            self._shared_execution_group = self._build_shared_execution_group()
        except Exception:
            try:
                if self._step_executor is not None:
                    self._step_executor.shutdown(wait=True, cancel_futures=False)
                    self._step_executor = None
            finally:
                super().close()
            raise

    @staticmethod
    def _leader_env(env):
        return unwrap_nested_env(env)

    def _leader_window_runtime(self, env):
        leader_env = self._leader_env(env)
        runtime = getattr(leader_env, "leader_window_runtime", None)
        return runtime if runtime is not None else leader_env

    def _build_batch_predictor(self):
        if not self.envs:
            return None
        env0 = self._leader_env(self.envs[0])
        if str(getattr(env0, "execution_backend", "")) != "frozen_model":
            return None
        model_path = getattr(env0, "execution_model_path", None)
        algo_name = getattr(env0, "execution_algo", "auto")
        if not model_path:
            return None
        for wrapped_env in self.envs[1:]:
            env = self._leader_env(wrapped_env)
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

    def _build_shared_execution_group(self):
        if not self.use_shared_world_batch_runtime:
            return None
        supported, reason = LeaderWorldBatchExecutionRuntimeGroup.compatibility_report(self.envs)
        self._shared_execution_group_reason = str(reason or "")
        if not supported:
            raise ValueError(
                "shared low-level WorldBatchRuntime requested for LeaderBatchedVecEnv, but the execution env "
                f"is incompatible: {self._shared_execution_group_reason}"
            )
        return LeaderWorldBatchExecutionRuntimeGroup.from_leader_envs(
            self.envs,
            world_batch_threads=self.world_batch_threads,
        )

    def _rollout_pending_leader_windows(self):
        if self._shared_execution_group is not None:
            target_indices = range(self.num_envs)
            self._shared_execution_group.begin_leader_steps(self.actions, target_indices)
            max_interval = self._shared_execution_group.max_decision_interval_steps(target_indices)
        else:
            for env_idx in range(self.num_envs):
                self._leader_window_runtime(self.envs[env_idx]).begin(self.actions[env_idx])
            max_interval = max(int(getattr(self._leader_env(env), "decision_interval_steps", 1)) for env in self.envs)

        for _ in range(max_interval):
            if self._shared_execution_group is not None:
                live_indices, obs_batch = self._shared_execution_group.collect_live_execution_batch(range(self.num_envs))
            else:
                live_indices = []
                obs_batch = []
                for env_idx, wrapped_env in enumerate(self.envs):
                    runtime = self._leader_window_runtime(wrapped_env)
                    if runtime.has_pending_execution_step():
                        live_indices.append(env_idx)
                        obs_batch.append(runtime.borrow_execution_observation())
            if not live_indices:
                break
            if self._batch_predictor is not None:
                action_batch = self._batch_predictor.predict_batch(obs_batch)
            else:
                action_batch = [
                    self._leader_window_runtime(self.envs[env_idx]).predict_execution_action(obs_batch[batch_idx])
                    for batch_idx, env_idx in enumerate(live_indices)
                ]

            if self._shared_execution_group is not None:
                self._shared_execution_group.step_leader_envs(live_indices, action_batch)
            elif self._step_executor is None:
                for batch_idx, env_idx in enumerate(live_indices):
                    self._leader_window_runtime(self.envs[env_idx]).step_execution_once(action_batch[batch_idx])
            else:
                futures = [
                    self._step_executor.submit(
                        self._leader_window_runtime(self.envs[env_idx]).step_execution_once,
                        action_batch[batch_idx],
                    )
                    for batch_idx, env_idx in enumerate(live_indices)
                ]
                for future in futures:
                    future.result()

        if self._shared_execution_group is not None:
            return self._shared_execution_group.finish_leader_steps(range(self.num_envs))
        return {
            int(env_idx): self._leader_window_runtime(self.envs[env_idx]).finish()
            for env_idx in range(self.num_envs)
        }

    def step_wait(self):
        if self._batch_predictor is None and self._shared_execution_group is None:
            return super().step_wait()

        finish_results = self._rollout_pending_leader_windows()
        for env_idx in range(self.num_envs):
            obs, self.buf_rews[env_idx], terminated, truncated, self.buf_infos[env_idx] = finish_results[int(env_idx)]
            self.buf_dones[env_idx] = terminated or truncated
            self.buf_infos[env_idx]["TimeLimit.truncated"] = truncated and not terminated
            self._save_obs(env_idx, obs)

        done_indices = [env_idx for env_idx in range(self.num_envs) if bool(self.buf_dones[env_idx])]
        if self._shared_execution_group is not None and done_indices:
            terminal_obs_map = {env_idx: self._copy_terminal_obs(env_idx) for env_idx in done_indices}
            reset_results = self._shared_execution_group.reset_leader_envs(done_indices, seeds=[None] * len(done_indices))
            for env_idx in done_indices:
                leader_obs, self.reset_infos[env_idx] = reset_results[int(env_idx)]
                self.buf_infos[env_idx]["terminal_observation"] = terminal_obs_map[int(env_idx)]
                self._save_obs(env_idx, leader_obs)
        else:
            for env_idx in done_indices:
                terminal_obs = self._copy_terminal_obs(env_idx)
                self.buf_infos[env_idx]["terminal_observation"] = terminal_obs
                obs, self.reset_infos[env_idx] = self.envs[env_idx].reset()
                self._save_obs(env_idx, obs)

        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), deepcopy(self.buf_infos)

    def _copy_terminal_obs(self, env_idx: int):
        terminal_obs = {}
        for key in self.keys:
            terminal_obs[key] = np.array(self.buf_obs[key][env_idx], copy=True)
        return terminal_obs

    def reset(self):
        if self._shared_execution_group is None:
            return super().reset()

        seeds = [self._seeds[env_idx] for env_idx in range(self.num_envs)]
        reset_results = self._shared_execution_group.reset_leader_envs(range(self.num_envs), seeds=seeds)
        for env_idx in range(self.num_envs):
            leader_obs, self.reset_infos[env_idx] = reset_results[int(env_idx)]
            self._save_obs(env_idx, leader_obs)
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def close(self):
        try:
            if self._shared_execution_group is not None:
                self._shared_execution_group.close()
                self._shared_execution_group = None
            if self._step_executor is not None:
                self._step_executor.shutdown(wait=True, cancel_futures=False)
                self._step_executor = None
        finally:
            super().close()
