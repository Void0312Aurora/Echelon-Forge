"""Stable-Baselines policy checkpoint loading without runtime bootstrap side effects.

Callers own repository/runtime import configuration. Production entry points can
therefore keep the installed-wheel fallback provided by ``configure_repo_imports``,
while diagnostics tools may still fail closed with ``ensure_repo_imports`` before
importing this module.
"""

from __future__ import annotations

import base64
import json
import zipfile
from typing import Any


def _historical_policy_class_override(model_path: str):
    zip_path = model_path if model_path.endswith(".zip") else f"{model_path}.zip"
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            data = json.loads(zf.read("data").decode("utf-8"))
            serialized = data.get("policy_class", {})
            if not isinstance(serialized, dict) or ":serialized:" not in serialized:
                return None
            blob = base64.b64decode(serialized[":serialized:"])
    except Exception:
        return None

    if b"HierarchicalMoEExecutionPolicy" in blob:
        from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy

        return HierarchicalMoEExecutionPolicy
    if b"SquashedMultiInputPolicy" in blob:
        from python.rl.policy_algo.policies import SquashedMultiInputPolicy

        return SquashedMultiInputPolicy
    return None


def load_sb3_policy(model_path: str, *, algo: str, device: str, env: Any | None = None):
    """Load a maintained SB3 policy, including historical custom policy classes."""
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    policy_class = _historical_policy_class_override(model_path)
    custom_objects = {"policy_class": policy_class} if policy_class is not None else None
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO

        try:
            return AdaptiveKLPPO.load(load_path, env=env, device=device, custom_objects=custom_objects)
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, env=env, device=device, custom_objects=custom_objects)


__all__ = ["load_sb3_policy"]
