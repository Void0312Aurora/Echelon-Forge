from __future__ import annotations

from typing import Any
import json

import numpy as np

from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader


def copy_obs(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: copy_obs(value) for key, value in obs.items()}
    if isinstance(obs, tuple):
        return tuple(copy_obs(value) for value in obs)
    return np.array(obs, copy=True)


def copy_obs_batch_item(obs_batch: dict[str, Any], env_idx: int) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for key, value in obs_batch.items():
        out[key] = np.array(value[int(env_idx)], copy=True)
    return out


def parse_reward_terms_json(raw: Any) -> dict[str, float] | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    out: dict[str, float] = {}
    for key, value in data.items():
        try:
            out[str(key)] = float(value)
        except Exception:
            continue
    return out if out else None


def step_info_products_to_info_fields(step_info: Any, *, loader: Any | None = None) -> dict[str, float]:
    if loader is not None and tasking_profile_for_loader(loader) is resolve_tasking_profile("naval"):
        return {}
    fields: dict[str, float] = {}
    try:
        fields["on_runway"] = float(bool(getattr(step_info, "on_runway", True)))
        fields["gear_collapsed"] = float(bool(getattr(step_info, "gear_collapsed", False)))
        fields["gear_stress"] = float(getattr(step_info, "gear_stress", 0.0))
        fields["on_ground"] = float(bool(getattr(step_info, "on_ground", False)))
        if bool(getattr(step_info, "has_runway_frame", False)):
            fields["on_runway_geom"] = float(bool(getattr(step_info, "on_runway_geom", False)))
            fields["runway_cross_m"] = float(getattr(step_info, "runway_cross_m", 0.0))
            fields["runway_along_m"] = float(getattr(step_info, "runway_along_m", 0.0))
    except Exception:
        return {}
    return fields


def observation_timing_snapshot(timing: Any) -> dict[str, float]:
    if not isinstance(timing, dict):
        return {}
    return {
        f"obs_{str(key)}": float(value)
        for key, value in timing.items()
        if isinstance(value, (int, float))
    }


__all__ = [
    "copy_obs",
    "copy_obs_batch_item",
    "observation_timing_snapshot",
    "parse_reward_terms_json",
    "step_info_products_to_info_fields",
]
