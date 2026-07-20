"""Fail-closed world-model checkpoint restoration helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch

from python.world_model.features import DEFAULT_ANGLE_DEG_INDICES


def _normalized_angle_deg_indices(value: Any) -> tuple[int, ...]:
    if value is None:
        return tuple(DEFAULT_ANGLE_DEG_INDICES)
    if isinstance(value, str):
        raw: Sequence[Any] = [part.strip() for part in value.split(",") if part.strip()]
    else:
        try:
            raw = list(value)
        except TypeError as exc:
            raise RuntimeError("Checkpoint angle_deg_indices must be a sequence of integers") from exc
    try:
        return tuple(int(item) for item in raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Checkpoint angle_deg_indices must be a sequence of integers") from exc


def _actor_input_uses_sincos(actor_input: str) -> bool:
    return "_sincos" in str(actor_input)


def _validate_actor_feature_schema(
    *,
    source_input: str,
    target_input: str,
    source_angle_deg_indices: Any = None,
    target_angle_deg_indices: Any = None,
) -> None:
    if not (
        _actor_input_uses_sincos(source_input)
        and _actor_input_uses_sincos(target_input)
    ):
        return
    source_indices = _normalized_angle_deg_indices(source_angle_deg_indices)
    target_indices = _normalized_angle_deg_indices(target_angle_deg_indices)
    if source_indices != target_indices:
        raise RuntimeError(
            "Actor checkpoint angle_deg_indices do not match the target feature schema: "
            f"{source_indices!r} -> {target_indices!r}; use --reset_actor instead of "
            "reusing semantically misaligned sin/cos weights"
        )


def _load_padded_actor_state(
    actor,
    source_state: dict,
    *,
    source_input: str,
    target_input: str,
) -> None:
    destination_state = actor.state_dict()
    first_weight = "net.net.0.weight"
    if first_weight not in source_state or first_weight not in destination_state:
        raise RuntimeError("Cannot pad actor weights: missing first-layer key")
    source_weight = source_state[first_weight]
    destination_weight = destination_state[first_weight]
    if not (
        isinstance(source_weight, torch.Tensor)
        and isinstance(destination_weight, torch.Tensor)
        and source_weight.ndim == 2
        and destination_weight.ndim == 2
        and source_weight.shape[0] == destination_weight.shape[0]
        and destination_weight.shape[1] >= source_weight.shape[1]
    ):
        raise RuntimeError("Cannot pad actor weights: incompatible first-layer shapes")

    padded_weight = destination_weight.clone()
    padded_weight.zero_()
    padded_weight[:, : source_weight.shape[1]] = source_weight
    destination_state[first_weight] = padded_weight
    source_keys = set(source_state) - {first_weight}
    destination_keys = set(destination_state) - {first_weight}
    if source_keys != destination_keys:
        missing = sorted(destination_keys - source_keys)
        unexpected = sorted(source_keys - destination_keys)
        raise RuntimeError(
            "Cannot pad actor weights: non-input parameter keys differ "
            f"(missing={missing}, unexpected={unexpected})"
        )
    for key in sorted(source_keys):
        value = source_state[key]
        destination_value = destination_state[key]
        if not isinstance(value, torch.Tensor) or value.shape != destination_value.shape:
            raise RuntimeError(
                "Cannot pad actor weights: non-input parameter shape differs for "
                f"{key!r}"
            )
        destination_state[key] = value
    actor.load_state_dict(destination_state)
    print(
        f"[checkpoint] padded actor weights: {source_input} -> {target_input} "
        f"(in={source_weight.shape[1]} -> {destination_weight.shape[1]})"
    )


def _load_actor_checkpoint(
    actor,
    source_state: dict,
    *,
    source_input: str,
    target_input: str,
    source_angle_deg_indices: Any = None,
    target_angle_deg_indices: Any = None,
) -> None:
    _validate_actor_feature_schema(
        source_input=source_input,
        target_input=target_input,
        source_angle_deg_indices=source_angle_deg_indices,
        target_angle_deg_indices=target_angle_deg_indices,
    )

    if source_input == target_input:
        try:
            actor.load_state_dict(source_state)
        except RuntimeError as exc:
            raise RuntimeError(
                "Actor checkpoint architecture does not match the target actor for the same "
                f"actor_input={target_input!r}; use --reset_actor"
            ) from exc
        return

    supported_migrations = {
        ("embed", "embed_sincos"),
        ("embed_sincos", "embed_sincos_track"),
    }
    if (source_input, target_input) not in supported_migrations:
        raise RuntimeError(
            "Unsupported actor checkpoint input migration: "
            f"{source_input!r} -> {target_input!r}; use --reset_actor to start a new actor"
        )
    _load_padded_actor_state(
        actor,
        source_state,
        source_input=source_input,
        target_input=target_input,
    )


def _checkpoint_tensor(
    checkpoint: dict,
    name: str,
    current: torch.Tensor | None,
    *,
    device: torch.device,
    minimum: float | None = None,
) -> torch.Tensor | None:
    if current is None:
        return None
    if name not in checkpoint or checkpoint.get(name) is None:
        raise RuntimeError(f"Checkpoint is missing required normalization tensor {name!r}")
    restored = torch.as_tensor(
        checkpoint[name],
        device=device,
        dtype=torch.float32,
    ).reshape(-1)
    if restored.shape != current.shape:
        raise RuntimeError(
            f"Checkpoint normalization tensor {name!r} has shape {tuple(restored.shape)}, "
            f"expected {tuple(current.shape)}"
        )
    if not bool(torch.isfinite(restored).all().item()):
        raise RuntimeError(
            f"Checkpoint normalization tensor {name!r} contains non-finite values"
        )
    if minimum is not None:
        restored = torch.maximum(restored, torch.as_tensor(float(minimum), device=device))
    return restored


__all__ = [
    "_checkpoint_tensor",
    "_load_actor_checkpoint",
    "_load_padded_actor_state",
    "_validate_actor_feature_schema",
]
