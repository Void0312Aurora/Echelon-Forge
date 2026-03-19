from __future__ import annotations

from typing import Any

import numpy as np
import torch

from gym_envs.leader_env import _load_policy


class ExecutionBatchPredictor:
    """
    Shared execution-policy inference helper for leader-layer training.

    The frozen execution model is expensive mainly because leader training was calling it
    one environment at a time. This helper turns a list of execution observations into a
    single batched policy forward pass so the visual backbone can actually use the GPU.
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
        self.model = _load_policy(model_path, algo_name=algo_name, device=self.device)
        self.policy = self.model.policy
        self.policy.set_training_mode(False)

    def _stack_observations(self, obs_batch: list[dict[str, Any]]) -> dict[str, np.ndarray]:
        if not obs_batch:
            raise ValueError("ExecutionBatchPredictor requires at least one observation")
        keys = list(obs_batch[0].keys())
        stacked: dict[str, np.ndarray] = {}
        for key in keys:
            stacked[key] = np.stack([np.asarray(obs[key]) for obs in obs_batch], axis=0)
        return stacked

    def predict_batch(self, obs_batch: list[dict[str, Any]]) -> np.ndarray:
        batch_obs = self._stack_observations(obs_batch)
        obs_tensor, _ = self.policy.obs_to_tensor(batch_obs)
        obs_tensor = {
            key: value.to(self.device, non_blocking=(self.device.startswith("cuda")))
            for key, value in obs_tensor.items()
        }
        autocast_enabled = self.use_autocast and self.device.startswith("cuda")
        with torch.inference_mode(), torch.autocast("cuda", enabled=autocast_enabled):
            actions = self.policy._predict(obs_tensor, deterministic=True)
        actions_np = actions.detach().cpu().numpy()
        if bool(getattr(self.policy, "squash_output", False)):
            actions_np = self.policy.unscale_action(actions_np)
        return np.asarray(actions_np, dtype=np.float32)
