"""Compatibility entrypoint for world-model training commands."""

from __future__ import annotations

from _world_model_train_impl.bootstrap import configure_repo_imports

configure_repo_imports()

from _world_model_train_impl.common import (  # noqa: E402,F401
    _apply_env_overrides,
    _apply_norm_clip,
    _apply_preset,
    _build_world_model,
    _downsample_visual,
    _flatten_obs,
    _format_metrics,
    _get_stage_overrides,
    _load_curriculum,
    _no_randomization_overrides,
    _normalize_action,
    _parse_angle_deg_indices,
    _resolve_visual_encoder_settings,
    _select_curriculum_stage,
    _unnormalize_action,
)
from _world_model_train_impl.cli import main  # noqa: E402,F401


def collect_dataset(args):
    from _world_model_train_impl.collect import collect_dataset as _collect_dataset

    return _collect_dataset(args)


def train_world_model(args):
    from _world_model_train_impl.train import train_world_model as _train_world_model

    return _train_world_model(args)


def online_train(args):
    from _world_model_train_impl.online import online_train as _online_train

    return _online_train(args)


def rollout_policy(args):
    from _world_model_train_impl.rollout import rollout_policy as _rollout_policy

    return _rollout_policy(args)


__all__ = (
    "collect_dataset",
    "main",
    "online_train",
    "rollout_policy",
    "train_world_model",
    "_apply_env_overrides",
    "_apply_norm_clip",
    "_apply_preset",
    "_build_world_model",
    "_downsample_visual",
    "_flatten_obs",
    "_format_metrics",
    "_get_stage_overrides",
    "_load_curriculum",
    "_no_randomization_overrides",
    "_normalize_action",
    "_parse_angle_deg_indices",
    "_resolve_visual_encoder_settings",
    "_select_curriculum_stage",
    "_unnormalize_action",
)


if __name__ == "__main__":
    main()
