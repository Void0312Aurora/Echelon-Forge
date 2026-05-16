from __future__ import annotations

from typing import Any

import numpy as np
import torch
from stable_baselines3 import PPO

from python.artifact_paths import resolve_artifact_path
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO


def load_policy(model_path: str, algo_name: str = "auto", device: str = "cpu"):
    resolved_path = resolve_artifact_path(model_path) or str(model_path)
    load_path = resolved_path[:-4] if str(resolved_path).endswith(".zip") else str(resolved_path)
    algo_norm = str(algo_name or "auto").strip()
    if algo_norm in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device=device)
        except Exception:
            if algo_norm != "auto":
                raise
    return PPO.load(load_path, device=device)


class FrozenExecutionPolicyAdapter:
    """
    Thin inference wrapper around a frozen SB3 policy.

    LeaderTrainingEnv was previously calling ``model.predict()`` for every low-level step,
    which repeats observation conversion and policy dispatch in Python. This adapter keeps the
    existing output semantics while using the thinner ``policy.obs_to_tensor()`` +
    ``policy._predict()`` path directly.
    """

    def __init__(self, model: Any, *, device: str = "cpu", use_autocast: bool = False) -> None:
        self.model = model
        self.policy = model.policy
        self.device = str(device or "cpu")
        self.use_autocast = bool(use_autocast)
        self.policy.set_training_mode(False)

    def predict(self, obs: Any, deterministic: bool = True):
        obs_tensor, _ = self.policy.obs_to_tensor(obs)
        if isinstance(obs_tensor, dict):
            obs_tensor = {
                key: value.to(self.device, non_blocking=self.device.startswith("cuda"))
                for key, value in obs_tensor.items()
            }
        else:
            obs_tensor = obs_tensor.to(self.device, non_blocking=self.device.startswith("cuda"))
        autocast_enabled = self.use_autocast and self.device.startswith("cuda")
        with torch.inference_mode(), torch.autocast("cuda", enabled=autocast_enabled):
            actions = self.policy._predict(obs_tensor, deterministic=deterministic)
        actions_np = actions.detach().cpu().numpy()
        if bool(getattr(self.policy, "squash_output", False)):
            actions_np = self.policy.unscale_action(actions_np)
        return np.asarray(actions_np, dtype=np.float32).reshape(-1), None

    def reset(self, obs: Any) -> None:
        if hasattr(self.model, "reset"):
            self.model.reset(obs)
