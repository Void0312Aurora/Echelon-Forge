"""Lazy loader for the heavy training dependency surface (torch / SB3 / policies).

`train.py` must stay importable without pulling torch or Stable-Baselines3 so
CLI preflight paths (``--help``, bootstrap validation, ``--test_only`` without a
checkpoint) stay fast and dependency-free. All heavy imports happen inside
:func:`load_training_dependencies`, mirroring the ``_load_torch`` pattern in
``python.training.bootstrap``.
"""

from __future__ import annotations

from typing import Any


class TrainingDependencies:
    """Namespace of the lazily imported torch/SB3/policy training dependencies."""

    def __init__(self) -> None:
        import torch as torch_module
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import CallbackList
        from stable_baselines3.common.callbacks import CheckpointCallback
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.vec_env import DummyVecEnv
        from stable_baselines3.common.vec_env import SubprocVecEnv

        if hasattr(torch_module, "set_float32_matmul_precision"):
            # Enable TF32 for Ampere+ GPUs (significant speedup and memory savings).
            torch_module.set_float32_matmul_precision("high")

        from python.models.transformer import (
            TemporalTransformerExtractor,
            TransformerExtractor,
            TransformerVisualExtractor,
        )
        from python.training_callbacks import (
            CMODiagnosticsCallback,
            ScenarioCurriculumCallback,
            RewardPlateauEarlyStopCallback,
        )
        from python.rl.policy_algo.policies import (
            HierarchicalMoEExecutionPolicy,
            SquashedMultiInputPolicy,
        )
        from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
        from python.rl.support.nonfinite_probe import (
            NonFiniteProbeError,
            NonFiniteTrainingProbe,
        )
        from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv
        from python.rl.runtime.cooperative_world_batch_vec_env import (
            CooperativeWorldBatchVecEnv,
        )
        from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv
        from python.rl.control.wrappers import (
            MultiTimescaleActionWrapper,
            get_action_wrapper_spec,
        )

        self.torch = torch_module
        self.PPO = PPO
        self.DummyVecEnv = DummyVecEnv
        self.SubprocVecEnv = SubprocVecEnv
        self.make_vec_env = make_vec_env
        self.CallbackList = CallbackList
        self.CheckpointCallback = CheckpointCallback
        self.TemporalTransformerExtractor = TemporalTransformerExtractor
        self.TransformerExtractor = TransformerExtractor
        self.TransformerVisualExtractor = TransformerVisualExtractor
        self.CMODiagnosticsCallback = CMODiagnosticsCallback
        self.ScenarioCurriculumCallback = ScenarioCurriculumCallback
        self.RewardPlateauEarlyStopCallback = RewardPlateauEarlyStopCallback
        self.HierarchicalMoEExecutionPolicy = HierarchicalMoEExecutionPolicy
        self.SquashedMultiInputPolicy = SquashedMultiInputPolicy
        self.AdaptiveKLPPO = AdaptiveKLPPO
        self.NonFiniteProbeError = NonFiniteProbeError
        self.NonFiniteTrainingProbe = NonFiniteTrainingProbe
        self.SharedMemorySubprocVecEnv = SharedMemorySubprocVecEnv
        self.CooperativeWorldBatchVecEnv = CooperativeWorldBatchVecEnv
        self.WorldBatchVecEnv = WorldBatchVecEnv
        self.MultiTimescaleActionWrapper = MultiTimescaleActionWrapper
        self.get_action_wrapper_spec = get_action_wrapper_spec


_DEPS: TrainingDependencies | None = None


def load_training_dependencies() -> TrainingDependencies:
    """Import and cache the heavy SB3/torch training dependency surface."""
    global _DEPS
    if _DEPS is None:
        _DEPS = TrainingDependencies()
    return _DEPS


def get_policy_kwargs(train_config: dict[str, Any]) -> dict[str, Any]:
    """Resolve `hyperparameters.policy_kwargs`, mapping feature-extractor names to classes."""
    # Parse policy_kwargs from JSON
    kwargs = train_config.get("hyperparameters", {}).get("policy_kwargs", {})

    # Check for custom features_extractor. Only touch the heavy dependency
    # surface when a custom extractor is actually requested.
    fe_name = kwargs.get("features_extractor_class")
    if fe_name == "TransformerExtractor":
        kwargs["features_extractor_class"] = load_training_dependencies().TransformerExtractor
    elif fe_name == "TemporalTransformerExtractor":
        kwargs["features_extractor_class"] = load_training_dependencies().TemporalTransformerExtractor
    elif fe_name == "TransformerVisualExtractor":
        kwargs["features_extractor_class"] = load_training_dependencies().TransformerVisualExtractor

    return kwargs


def apply_policy_kwargs_feature_extractor_classes(hyperparams: dict[str, Any]) -> None:
    """Map string feature-extractor names inside `policy_kwargs` to their classes.

    Emits the same CLI notices the training entrypoint has always printed.
    """
    if "policy_kwargs" not in hyperparams:
        return
    deps = load_training_dependencies()
    p_kwargs = hyperparams["policy_kwargs"]
    if p_kwargs.get("features_extractor_class") == "TransformerExtractor":
        print("Using Transformer Feature Extractor")
        p_kwargs["features_extractor_class"] = deps.TransformerExtractor
    elif p_kwargs.get("features_extractor_class") == "TemporalTransformerExtractor":
        print("Using Temporal Transformer Feature Extractor")
        p_kwargs["features_extractor_class"] = deps.TemporalTransformerExtractor
    elif p_kwargs.get("features_extractor_class") == "TransformerVisualExtractor":
        print("Using Transformer+Visual Feature Extractor")
        p_kwargs["features_extractor_class"] = deps.TransformerVisualExtractor


__all__ = [
    "TrainingDependencies",
    "apply_policy_kwargs_feature_extractor_classes",
    "get_policy_kwargs",
    "load_training_dependencies",
]
