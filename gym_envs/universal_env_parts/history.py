from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

import numpy as np


TEMPORAL_HISTORY_KEYS = (
    "instruments",
    "contacts",
    "rwr",
    "mission",
    "proprio",
)


def temporal_history_enabled(history_len: int | None) -> bool:
    return int(history_len or 1) > 1


def make_temporal_history_buffer(history_len: int) -> deque[dict[str, np.ndarray]]:
    return deque(maxlen=max(1, int(history_len)))


def _zero_like_from_obs(obs: dict[str, Any], key: str, action_dim: int) -> np.ndarray:
    if key == "proprio" and key not in obs:
        return np.zeros((int(action_dim),), dtype=np.float32)
    return np.zeros_like(np.asarray(obs[key], dtype=np.float32), dtype=np.float32)


def _history_frame_from_obs(obs: dict[str, Any], action_dim: int) -> dict[str, np.ndarray]:
    return {
        key: (
            np.asarray(obs[key], dtype=np.float32).copy()
            if key in obs
            else _zero_like_from_obs(obs, key, action_dim)
        )
        for key in TEMPORAL_HISTORY_KEYS
        if key in obs or key == "proprio"
    }


def reset_temporal_history(
    history: deque[dict[str, np.ndarray]],
    obs: dict[str, Any],
    *,
    history_len: int,
    action_dim: int,
) -> None:
    history.clear()
    current = _history_frame_from_obs(obs, int(action_dim))
    zero = {key: np.zeros_like(value, dtype=np.float32) for key, value in current.items()}
    for _ in range(max(0, int(history_len) - 1)):
        history.append({key: value.copy() for key, value in zero.items()})
    history.append({key: value.copy() for key, value in current.items()})


def append_temporal_history(
    history: deque[dict[str, np.ndarray]],
    obs: dict[str, Any],
    *,
    history_len: int,
    action_dim: int,
) -> None:
    if len(history) <= 0:
        reset_temporal_history(history, obs, history_len=int(history_len), action_dim=int(action_dim))
        return
    history.append(_history_frame_from_obs(obs, int(action_dim)))


def attach_temporal_history(
    obs: dict[str, np.ndarray],
    history: Iterable[dict[str, np.ndarray]],
    *,
    history_len: int,
    action_dim: int,
) -> dict[str, np.ndarray]:
    frames = list(history)
    if len(frames) <= 0:
        reset_buf = make_temporal_history_buffer(int(history_len))
        reset_temporal_history(reset_buf, obs, history_len=int(history_len), action_dim=int(action_dim))
        frames = list(reset_buf)
    if len(frames) < int(history_len):
        pad_source = frames[0]
        pads = [
            {key: np.zeros_like(value, dtype=np.float32) for key, value in pad_source.items()}
            for _ in range(int(history_len) - len(frames))
        ]
        frames = [*pads, *frames]
    elif len(frames) > int(history_len):
        frames = frames[-int(history_len):]

    for key in TEMPORAL_HISTORY_KEYS:
        if key == "proprio" and all(key not in frame for frame in frames):
            values = [np.zeros((int(action_dim),), dtype=np.float32) for _ in frames]
        else:
            values = [np.asarray(frame[key], dtype=np.float32) for frame in frames if key in frame]
        if len(values) != int(history_len):
            continue
        obs[f"{key}_history"] = np.stack(values, axis=0).astype(np.float32, copy=False)
    return obs


__all__ = [
    "TEMPORAL_HISTORY_KEYS",
    "append_temporal_history",
    "attach_temporal_history",
    "make_temporal_history_buffer",
    "reset_temporal_history",
    "temporal_history_enabled",
]
