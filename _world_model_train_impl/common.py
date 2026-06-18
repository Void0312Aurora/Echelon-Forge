"""Shared helpers for world-model training commands."""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np
import torch

from _world_model_train_impl.bootstrap import configure_repo_imports

configure_repo_imports()

from python.world_model.features import DEFAULT_ANGLE_DEG_INDICES  # noqa: E402
from python.world_model.networks import WorldModel  # noqa: E402


def _apply_preset(args: argparse.Namespace) -> None:
    preset = getattr(args, "preset", "default")
    if preset in (None, "", "default"):
        return
    if preset == "takeoff_stable":
        # Tuned to reduce return variance and critic blow-ups on takeoff tasks with large negative penalties.
        # Keeps realism intact (no observation leakage), only changes learning-side scalings.
        args.horizon = 10
        args.reward_symlog_clip = 3.0
        args.seq_len = 64
        if getattr(args, "bc_scale", None) is not None and float(args.bc_scale) <= 0.0:
            args.bc_scale = 0.1
        if getattr(args, "bc_teacher_prob", None) is not None:
            args.bc_teacher_prob = min(float(args.bc_teacher_prob), 0.7)
        if getattr(args, "log_compact", None) is not None:
            args.log_compact = True
        return
    raise ValueError(f"Unknown preset: {preset}")


def _format_metrics(metrics: dict[str, float], *, compact: bool) -> str:
    if not compact:
        items = sorted(metrics.items())
        return " ".join(f"{k}={v:.4f}" for k, v in items)

    keys = [
        "wm/total",
        "wm/kl",
        "wm/obs",
        "wm/visual",
        "wm/cont",
        "ac/return_mean",
        "ac/return_std",
        "ac/value_raw_mse",
        "ac/bc",
    ]
    items = [(k, float(metrics[k])) for k in keys if k in metrics]
    return " ".join(f"{k}={v:.4f}" for k, v in items)


def _no_randomization_overrides() -> dict:
    # Deterministic baseline: remove wind and world-yaw randomization.
    # This does NOT leak privileged information; it only fixes environment conditions.
    return {
        "world_yaw_range": [0.0, 0.0],
        # Global wind sampling
        "wind_speed_range": [0.0, 0.0],
        "wind_dir_from_range": [0.0, 0.0],
        # Runway-relative wind sampling (takeoff/landing scenarios)
        "wind_headwind_range": [0.0, 0.0],
        "wind_crosswind_range": [0.0, 0.0],
        "wind_tailwind_max_mps": 0.0,
        # Shear (both modes share this key)
        "wind_shear_range": [0.0, 0.0],
    }


def _apply_env_overrides(env: Any, args: argparse.Namespace) -> None:
    if bool(getattr(args, "no_randomization", False)):
        env.set_randomization_overrides(_no_randomization_overrides())


def _load_curriculum(path: str) -> list[dict]:
    import json

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("stages", None), list):
        stages = data["stages"]
    elif isinstance(data, list):
        stages = data
    else:
        raise ValueError("curriculum must be a JSON list or an object with a 'stages' list")
    if not stages:
        raise ValueError("curriculum stages list is empty")
    return [dict(s) for s in stages if isinstance(s, dict)]


def _select_curriculum_stage(stages: list[dict], t: int, *, key: str) -> int:
    for idx, st in enumerate(stages):
        until = st.get(key, None)
        if until is None:
            return idx
        if t < int(until):
            return idx
    return len(stages) - 1


def _get_stage_overrides(stage: dict) -> dict:
    overrides = stage.get("randomization_overrides", stage.get("randomization", {}))
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise TypeError(f"curriculum stage overrides must be a dict, got {type(overrides)}")
    return dict(overrides)


def _downsample_visual(visual: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return visual
    h, w, c = visual.shape
    if h % factor != 0 or w % factor != 0:
        raise ValueError(f"visual shape {visual.shape} not divisible by downsample factor {factor}")
    nh, nw = h // factor, w // factor
    return visual.reshape(nh, factor, nw, factor, c).mean(axis=(1, 3))


def _flatten_obs(obs: dict) -> np.ndarray:
    # Strict realism: only include pilot-observable avionics + mission command.
    # Do NOT include contacts/rwr arrays here until they are implemented as real sensor fusion outputs.
    inst = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
    mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
    proprio = np.asarray(obs.get("proprio", []), dtype=np.float32).reshape(-1)
    if proprio.size > 0:
        return np.concatenate([inst, mission, proprio], axis=0).astype(np.float32, copy=False)
    return np.concatenate([inst, mission], axis=0).astype(np.float32, copy=False)


def _normalize_action(action: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32).reshape(-1)
    low = np.asarray(low, dtype=np.float32).reshape(-1)
    high = np.asarray(high, dtype=np.float32).reshape(-1)
    denom = high - low
    denom = np.where(np.abs(denom) < 1e-8, 1.0, denom)
    out = 2.0 * (action - low) / denom - 1.0
    return np.clip(out, -1.0, 1.0).astype(np.float32, copy=False)


def _unnormalize_action(action: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32).reshape(-1)
    low = np.asarray(low, dtype=np.float32).reshape(-1)
    high = np.asarray(high, dtype=np.float32).reshape(-1)
    out = low + 0.5 * (action + 1.0) * (high - low)
    return np.clip(out, low, high).astype(np.float32, copy=False)


def _apply_norm_clip(t: torch.Tensor, clip: float | None) -> torch.Tensor:
    if clip is None:
        return t
    return torch.clamp(t, -float(clip), float(clip))


def _parse_angle_deg_indices(value: str | None) -> tuple[int, ...]:
    if value is None:
        return DEFAULT_ANGLE_DEG_INDICES
    s = str(value).strip()
    if not s:
        return DEFAULT_ANGLE_DEG_INDICES
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return tuple(int(p) for p in parts)


def _resolve_visual_encoder_settings(
    *,
    args: argparse.Namespace | None = None,
    ckpt_cfg: dict | None = None,
) -> tuple[str, int]:
    if isinstance(ckpt_cfg, dict):
        enc_type = str(ckpt_cfg.get("visual_encoder_type", "mlp")).strip().lower()
        channels = int(ckpt_cfg.get("visual_cnn_channels", 64))
    else:
        enc_type = str(getattr(args, "visual_encoder_type", "cnn")).strip().lower()
        channels = int(getattr(args, "visual_cnn_channels", 64))
    if enc_type not in ("cnn", "mlp"):
        raise ValueError(f"Unknown visual_encoder_type: {enc_type!r}")
    return enc_type, max(16, channels)


def _build_world_model(
    *,
    action_dim: int,
    obs_vec_dim: int,
    visual_shape: tuple[int, int, int] | None,
    visual_encoder_type: str,
    visual_cnn_channels: int,
) -> WorldModel:
    return WorldModel(
        action_dim=action_dim,
        obs_vec_dim=obs_vec_dim,
        visual_shape=visual_shape,
        visual_encoder_type=str(visual_encoder_type),
        visual_cnn_channels=int(visual_cnn_channels),
    )
