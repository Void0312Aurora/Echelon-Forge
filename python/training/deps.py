"""Lazy loader for the heavy training dependency surface (torch / SB3 / policies).

`train.py` must stay importable without pulling torch or Stable-Baselines3 so
CLI preflight paths (``--help``, bootstrap validation, ``--test_only`` without a
checkpoint) stay fast and dependency-free. All heavy imports happen inside
:func:`load_training_dependencies`, mirroring the ``_load_torch`` pattern in
``python.training.bootstrap``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from python.rl.policy_algo.model_contracts import (
    LaunchDecisionContractError,
    LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION,
    LAUNCH_DECISION_CONTRACT_VERSION_KEY,
    LaunchDecisionMode,
    resolve_launch_decision_contract,
)


LAUNCH_DECISION_CONFIG_MIGRATION_SCHEMA = "launch_decision_config_migration_v1"


class LaunchDecisionConfigMigrationError(ValueError):
    """Raised when a flat training config cannot be migrated safely."""


def translate_launch_decision_config(
    train_config: Mapping[str, Any],
    *,
    target_mode: str | LaunchDecisionMode | None = None,
    migration_id: str | None = None,
) -> dict[str, Any]:
    """Resolve the flat policy surface without rewriting its source JSON.

    Old configurations receive an in-memory explicit
    ``legacy_composed_v0`` key. Changing an already-resolved mode requires a
    named migration id; this prevents a checkpoint or optimizer state from
    silently changing owner semantics during startup.
    """

    if not isinstance(train_config, Mapping):
        raise LaunchDecisionConfigMigrationError("training config must be a mapping")
    translated = deepcopy(dict(train_config))
    hyperparameters = translated.setdefault("hyperparameters", {})
    if not isinstance(hyperparameters, dict):
        raise LaunchDecisionConfigMigrationError("hyperparameters must be a mapping")
    policy_kwargs = hyperparameters.setdefault("policy_kwargs", {})
    if not isinstance(policy_kwargs, dict):
        raise LaunchDecisionConfigMigrationError("hyperparameters.policy_kwargs must be a mapping")

    launch_surface_keys = {
        "hybrid_action_spec",
        "launch_decision_mode",
        "launch_decision_owner_mode",
        "hybrid_event_head_lr_scale",
        "hybrid_event_use_stopping_head",
        "hybrid_event_use_window_classifier_head",
    }
    launch_surface_active = (
        str(translated.get("policy", "")) == "HierarchicalMoEExecutionPolicy"
        or bool(launch_surface_keys.intersection(policy_kwargs))
    )
    if not launch_surface_active:
        if target_mode is not None or migration_id is not None:
            raise LaunchDecisionConfigMigrationError(
                "a target launch-decision mode was supplied for a policy without the hybrid launch surface"
            )
        return translated

    try:
        source_contract = resolve_launch_decision_contract(translated)
    except LaunchDecisionContractError as exc:
        raise LaunchDecisionConfigMigrationError(
            f"source launch-decision contract is invalid: {exc}"
        ) from exc

    source_mode = source_contract.mode
    resolved_mode = source_mode
    if target_mode is not None:
        try:
            resolved_mode = (
                target_mode
                if isinstance(target_mode, LaunchDecisionMode)
                else LaunchDecisionMode(str(target_mode))
            )
        except ValueError as exc:
            raise LaunchDecisionConfigMigrationError(
                f"unknown target launch-decision mode: {target_mode!r}"
            ) from exc
        if resolved_mode != source_mode and not str(migration_id or "").strip():
            raise LaunchDecisionConfigMigrationError(
                f"mode change {source_mode.value!r} -> {resolved_mode.value!r} "
                "requires an explicit migration_id"
            )

    policy_kwargs[LAUNCH_DECISION_CONTRACT_VERSION_KEY] = LAUNCH_DECISION_CONTRACT_SCHEMA_VERSION
    policy_kwargs["launch_decision_mode"] = resolved_mode.value
    if "launch_decision_owner_mode" in policy_kwargs:
        policy_kwargs["launch_decision_owner_mode"] = resolved_mode.value

    try:
        resolved_contract = resolve_launch_decision_contract(translated)
    except LaunchDecisionContractError as exc:
        raise LaunchDecisionConfigMigrationError(
            f"translated launch-decision contract is invalid: {exc}"
        ) from exc

    translated["launch_decision_migration"] = {
        "schema_version": LAUNCH_DECISION_CONFIG_MIGRATION_SCHEMA,
        "source_mode": source_mode.value,
        "resolved_mode": resolved_contract.mode.value,
        "source_explicit": bool(source_contract.explicit_mode),
        "compatibility_mode": resolved_contract.compatibility_mode,
        "compatibility_precedence": resolved_contract.compatibility_precedence,
        "migration_id": str(migration_id) if migration_id is not None else None,
    }
    return translated


def launch_decision_config_migration_metadata(
    train_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return validated in-memory migration metadata for diagnostics/tests."""

    translated = translate_launch_decision_config(train_config)
    metadata = translated.get("launch_decision_migration", {})
    return dict(metadata) if isinstance(metadata, Mapping) else {}


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
        from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv
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
    "LAUNCH_DECISION_CONFIG_MIGRATION_SCHEMA",
    "LaunchDecisionConfigMigrationError",
    "TrainingDependencies",
    "apply_policy_kwargs_feature_extractor_classes",
    "get_policy_kwargs",
    "launch_decision_config_migration_metadata",
    "load_training_dependencies",
    "translate_launch_decision_config",
]
