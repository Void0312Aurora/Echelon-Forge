from __future__ import annotations

import argparse

import numpy as np

from python.angles import wrap_signed_deg
from python.env_config import ACTION_MODES
from python.testing.runtime import ensure_repo_imports


ACTION_MODE_CHOICES = tuple(ACTION_MODES)


def bootstrap_repo_imports() -> str:
    return ensure_repo_imports()


def add_common_env_args(
    parser: argparse.ArgumentParser,
    *,
    episodes_default: int,
    max_steps_default: int,
    seed_default: int,
    default_action_mode: str,
    include_no_randomization: bool = False,
) -> None:
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--episodes", type=int, default=int(episodes_default))
    parser.add_argument("--max_steps", type=int, default=int(max_steps_default))
    parser.add_argument("--seed", type=int, default=int(seed_default))
    parser.add_argument("--action_mode", type=str, default=str(default_action_mode), choices=ACTION_MODE_CHOICES)
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    if include_no_randomization:
        parser.add_argument("--no_randomization", action="store_true")


def make_single_world_batch_env_from_args(args, *, mission_obs_mode: str | None = None):
    bootstrap_repo_imports()

    from python.rl.runtime.single_world_batch_runtime import build_single_world_batch_execution_runtime

    env_settings = {
        "include_visual": bool(getattr(args, "include_visual", False)),
        "include_proprio": bool(getattr(args, "include_proprio", False)),
        "action_mode": str(getattr(args, "action_mode", "full")),
    }
    if mission_obs_mode is not None:
        env_settings["mission_obs_mode"] = str(mission_obs_mode)
    env = build_single_world_batch_execution_runtime(
        scenario_path=str(args.scenario),
        env_settings=env_settings,
        worker_threads=1,
    )

    if bool(getattr(args, "no_randomization", False)):
        from world_model_train import _no_randomization_overrides

        env.set_randomization_overrides(_no_randomization_overrides())
    return env


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    arr = np.asarray(xs, dtype=np.float64).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.percentile(arr, q))


def format_stats(name: str, xs: list[float], *, unit: str = "") -> str:
    if not xs:
        return f"{name}: <empty>"
    arr = np.asarray(xs, dtype=np.float64).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return f"{name}: <all_nan>"
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    p50 = float(np.percentile(arr, 50))
    p90 = float(np.percentile(arr, 90))
    p95 = float(np.percentile(arr, 95))
    mn = float(np.min(arr))
    mx = float(np.max(arr))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.3f}{suffix} std={std:.3f}{suffix} "
        f"p50={p50:.3f}{suffix} p90={p90:.3f}{suffix} p95={p95:.3f}{suffix} "
        f"min={mn:.3f}{suffix} max={mx:.3f}{suffix}"
    )


def quantile_summary(xs: list[float], qs: list[float]) -> dict[str, float]:
    if not xs:
        return {}
    arr = np.asarray(xs, dtype=np.float64).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {}
    out: dict[str, float] = {}
    for q in qs:
        out[f"p{int(q * 100):02d}"] = float(np.quantile(arr, q))
    out["max"] = float(np.max(arr))
    out["mean"] = float(np.mean(arr))
    return out


def wrap_deg(x: float) -> float:
    # Deliberate variant of python.angles.wrap_signed_deg: values within 1e-9
    # of zero (including negative zero) are snapped to exactly 0.0.
    y = wrap_signed_deg(x)
    return 0.0 if abs(y) < 1.0e-9 else y
