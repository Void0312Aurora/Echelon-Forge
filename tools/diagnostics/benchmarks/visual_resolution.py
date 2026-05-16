#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.mission_obs_taxonomy import BASE_MISSION_OBS_MODES, COOPERATIVE_MISSION_OBS_MODES
from python.testing.runtime import ensure_repo_imports, resolve_repo_path
from tools.diagnostics.common import write_json_output

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from gym_envs.universal_env import UniversalEnv

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover
    torch = None

try:
    from python.models.transformer import TransformerVisualExtractor
except ModuleNotFoundError:  # pragma: no cover
    TransformerVisualExtractor = None


def _parse_factors(text: str) -> list[int]:
    values: list[int] = []
    for raw in str(text).split(","):
        token = raw.strip()
        if not token:
            continue
        values.append(max(1, int(token)))
    if not values:
        raise ValueError("at least one visual downsample factor is required")
    unique = sorted(set(values))
    return unique


def _format_bytes(num_bytes: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.2f} {units[idx]}"


def _repeat_obs(obs: dict[str, Any], batch_size: int, device: str) -> dict[str, Any]:
    if torch is None:
        raise RuntimeError("torch is not available")
    batch: dict[str, Any] = {}
    for key, value in obs.items():
        arr = np.asarray(value, dtype=np.float32)
        arr = np.repeat(arr[None, ...], batch_size, axis=0)
        batch[key] = torch.from_numpy(arr).to(device=device)
    return batch


def _benchmark_extractor(
    *,
    env: UniversalEnv,
    obs: dict[str, Any],
    batch_size: int,
    warmup: int,
    iters: int,
    device: str,
    use_amp: bool,
    features_dim: int,
    visual_cnn_channels: int,
) -> tuple[float | None, str | None]:
    if torch is None or TransformerVisualExtractor is None:
        return None, "torch or TransformerVisualExtractor unavailable"
    try:
        if device.startswith("cuda") and not torch.cuda.is_available():
            return None, f"device {device!r} unavailable"
        model = TransformerVisualExtractor(
            env.observation_space,
            features_dim=features_dim,
            visual_cnn_channels=visual_cnn_channels,
            use_amp=use_amp,
            use_checkpointing=False,
        ).to(device=device)
        model.eval()
        batch = _repeat_obs(obs, batch_size=batch_size, device=device)
        amp_enabled = bool(use_amp and device.startswith("cuda"))
        ctx = (
            torch.autocast(device_type="cuda", dtype=torch.float16, enabled=amp_enabled)
            if amp_enabled
            else None
        )
        with torch.no_grad():
            for _ in range(max(1, warmup)):
                if ctx is not None:
                    with ctx:
                        model(batch)
                else:
                    model(batch)
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            start = time.perf_counter()
            for _ in range(max(1, iters)):
                if ctx is not None:
                    with ctx:
                        model(batch)
                else:
                    model(batch)
            if device.startswith("cuda"):
                torch.cuda.synchronize()
            elapsed_ms = (time.perf_counter() - start) * 1000.0 / max(1, iters)
        return float(elapsed_ms), None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def _benchmark_case(
    *,
    scenario_path: str,
    action_mode: str,
    mission_obs_mode: str,
    visual_downsample: int,
    visual_update_interval: int,
    seed: int,
    warmup_steps: int,
    measure_steps: int,
    n_envs: int,
    n_steps: int,
    extractor_batch_size: int,
    extractor_device: str,
    extractor_use_amp: bool,
    extractor_features_dim: int,
    extractor_visual_channels: int,
) -> dict[str, Any]:
    env = UniversalEnv(
        scenario_path=scenario_path,
        include_visual=True,
        action_mode=action_mode,
        mission_obs_mode=mission_obs_mode,
        visual_downsample=visual_downsample,
        visual_update_interval=visual_update_interval,
    )
    try:
        obs, _info = env.reset(seed=seed)
        action = np.zeros(env.action_space.shape, dtype=np.float32)

        for _ in range(max(1, warmup_steps)):
            env.step(action)

        native_h = int(getattr(env, "arb_height_native", 48))
        native_w = int(getattr(env, "arb_width_native", 96))
        visual_h = int(env.arb_height)
        visual_w = int(env.arb_width)
        visual_c = int(env.arb_channels)
        visual_elems = visual_h * visual_w * visual_c
        per_obs_bytes = visual_elems * 4
        rollout_bytes = int(n_envs) * int(n_steps) * per_obs_bytes

        if visual_downsample > 1 and hasattr(env.sim, "get_visual_observation_downsampled"):
            fetch_fn = lambda: env.sim.get_visual_observation_downsampled(env.agent_id, visual_downsample)
        else:
            fetch_fn = lambda: env.sim.get_visual_observation(env.agent_id)

        start = time.perf_counter()
        for _ in range(max(1, measure_steps)):
            np.asarray(fetch_fn(), dtype=np.float32)
        visual_fetch_ms = (time.perf_counter() - start) * 1000.0 / max(1, measure_steps)

        start = time.perf_counter()
        for _ in range(max(1, measure_steps)):
            env._visual_cache = None
            env._visual_cache_step = -1
            env._get_obs()
        get_obs_uncached_ms = (time.perf_counter() - start) * 1000.0 / max(1, measure_steps)

        start = time.perf_counter()
        for _ in range(max(1, measure_steps)):
            env.step(action)
        env_step_ms = (time.perf_counter() - start) * 1000.0 / max(1, measure_steps)

        extractor_ms, extractor_error = _benchmark_extractor(
            env=env,
            obs=obs,
            batch_size=extractor_batch_size,
            warmup=max(4, warmup_steps // 4),
            iters=max(8, measure_steps // 8),
            device=extractor_device,
            use_amp=extractor_use_amp,
            features_dim=extractor_features_dim,
            visual_cnn_channels=extractor_visual_channels,
        )

        return {
            "visual_downsample": int(visual_downsample),
            "visual_update_interval": int(visual_update_interval),
            "visual_shape": [visual_h, visual_w, visual_c],
            "native_shape": [native_h, native_w, visual_c],
            "effective_cell_deg_h": float(180.0 / float(visual_w)),
            "effective_cell_deg_v": float(90.0 / float(visual_h)),
            "visual_elements": int(visual_elems),
            "per_obs_bytes": int(per_obs_bytes),
            "per_obs_human": _format_bytes(per_obs_bytes),
            "rollout_bytes": int(rollout_bytes),
            "rollout_human": _format_bytes(rollout_bytes),
            "visual_fetch_ms": round(float(visual_fetch_ms), 4),
            "get_obs_uncached_ms": round(float(get_obs_uncached_ms), 4),
            "env_step_ms": round(float(env_step_ms), 4),
            "env_step_fps": round(float(1000.0 / max(env_step_ms, 1.0e-9)), 1),
            "extractor_forward_ms": None if extractor_ms is None else round(float(extractor_ms), 4),
            "extractor_error": extractor_error,
            "extractor_batch_size": int(extractor_batch_size),
            "extractor_device": str(extractor_device),
        }
    finally:
        env.close()


def _print_table(results: list[dict[str, Any]]) -> None:
    header = (
        f"{'ds':>3}  {'shape':>12}  {'cell(deg)':>13}  {'obs':>10}  "
        f"{'rollout':>10}  {'vis(ms)':>8}  {'obs(ms)':>8}  {'step(ms)':>9}  "
        f"{'fps':>8}  {'extract(ms)':>12}"
    )
    print(header)
    print("-" * len(header))
    for row in results:
        shape = f"{row['visual_shape'][0]}x{row['visual_shape'][1]}x{row['visual_shape'][2]}"
        cell = f"{row['effective_cell_deg_h']:.2f}/{row['effective_cell_deg_v']:.2f}"
        extract = (
            f"{row['extractor_forward_ms']:.3f}"
            if row.get("extractor_forward_ms") is not None
            else "n/a"
        )
        print(
            f"{int(row['visual_downsample']):>3}  "
            f"{shape:>12}  "
            f"{cell:>13}  "
            f"{row['per_obs_human']:>10}  "
            f"{row['rollout_human']:>10}  "
            f"{float(row['visual_fetch_ms']):>8.3f}  "
            f"{float(row['get_obs_uncached_ms']):>8.3f}  "
            f"{float(row['env_step_ms']):>9.3f}  "
            f"{float(row['env_step_fps']):>8.1f}  "
            f"{extract:>12}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sweep ARB visual_downsample factors and report env/model cost proxies."
    )
    parser.add_argument(
        "--scenario",
        default="scenarios/takeoff/takeoff.json",
        help="Scenario path relative to repo root or absolute path.",
    )
    parser.add_argument("--action-mode", default="takeoff2")
    parser.add_argument(
        "--mission-obs-mode",
        default="basic",
        choices=list(BASE_MISSION_OBS_MODES) + list(COOPERATIVE_MISSION_OBS_MODES),
    )
    parser.add_argument("--factors", default="1,2,4", help="Comma-separated visual_downsample sweep.")
    parser.add_argument("--visual-update-interval", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-steps", type=int, default=32)
    parser.add_argument("--measure-steps", type=int, default=256)
    parser.add_argument("--n-envs", type=int, default=8, help="Used for rollout-memory estimates only.")
    parser.add_argument("--n-steps", type=int, default=256, help="Used for rollout-memory estimates only.")
    parser.add_argument("--extractor-batch-size", type=int, default=64)
    parser.add_argument("--extractor-device", default="cpu")
    parser.add_argument("--extractor-features-dim", type=int, default=128)
    parser.add_argument("--extractor-visual-cnn-channels", type=int, default=32)
    parser.add_argument("--extractor-use-amp", action="store_true")
    parser.add_argument("--json-out", default="", help="Optional path to write machine-readable JSON.")
    args = parser.parse_args()

    scenario_path = args.scenario
    if not os.path.isabs(scenario_path):
        scenario_path = resolve_repo_path(scenario_path)

    results: list[dict[str, Any]] = []
    for ds in _parse_factors(args.factors):
        results.append(
            _benchmark_case(
                scenario_path=scenario_path,
                action_mode=str(args.action_mode),
                mission_obs_mode=str(args.mission_obs_mode),
                visual_downsample=int(ds),
                visual_update_interval=max(1, int(args.visual_update_interval)),
                seed=int(args.seed),
                warmup_steps=max(1, int(args.warmup_steps)),
                measure_steps=max(1, int(args.measure_steps)),
                n_envs=max(1, int(args.n_envs)),
                n_steps=max(1, int(args.n_steps)),
                extractor_batch_size=max(1, int(args.extractor_batch_size)),
                extractor_device=str(args.extractor_device),
                extractor_use_amp=bool(args.extractor_use_amp),
                extractor_features_dim=max(8, int(args.extractor_features_dim)),
                extractor_visual_channels=max(4, int(args.extractor_visual_cnn_channels)),
            )
        )

    payload = {
        "scenario": scenario_path,
        "action_mode": str(args.action_mode),
        "mission_obs_mode": str(args.mission_obs_mode),
        "visual_update_interval": max(1, int(args.visual_update_interval)),
        "results": results,
    }

    print(json.dumps(payload, indent=2, ensure_ascii=True))
    print()
    _print_table(results)

    if args.json_out:
        out_path = args.json_out
        if not os.path.isabs(out_path):
            out_path = resolve_repo_path(out_path)
        write_json_output(out_path, payload)
        print()
        print(f"Wrote JSON report to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
