#!/usr/bin/env python3
"""
Runway drift / ground-roll directional stability sweep.

Purpose:
  Quantify how often the aircraft departs runway geometry during the takeoff roll
  under scenario randomization (wind + world yaw) when applying a fixed action.

This is a realism-first diagnostic:
  - No runway-heading leakage is introduced.
  - We only read existing env info channels (runway_cross_m/on_runway_geom) for evaluation.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gym_envs.universal_env import UniversalEnv
from python.rl.scripted_takeoff import ScriptedTakeoffController, scripted_takeoff_action


def _parse_seeds(spec: str) -> list[int]:
    spec = str(spec).strip()
    if not spec:
        raise ValueError("empty --seeds spec")
    if ":" in spec:
        parts = spec.split(":")
        if len(parts) != 2:
            raise ValueError(f"invalid --seeds range: {spec!r}")
        start = int(parts[0])
        end = int(parts[1])
        if end <= start:
            raise ValueError(f"invalid --seeds range (end must be > start): {spec!r}")
        return list(range(start, end))
    if "," in spec:
        out: list[int] = []
        for tok in spec.split(","):
            tok = tok.strip()
            if not tok:
                continue
            out.append(int(tok))
        if not out:
            raise ValueError(f"invalid --seeds list: {spec!r}")
        return out
    return [int(spec)]


def _make_action(
    *,
    action_mode: str,
    pitch: float,
    roll: float,
    rudder: float,
    throttle: float,
    gear: float,
) -> np.ndarray:
    action_mode = str(action_mode)
    if action_mode == "takeoff2":
        return np.asarray([pitch, throttle], dtype=np.float32)
    if action_mode == "takeoff4":
        return np.asarray([pitch, roll, rudder, throttle], dtype=np.float32)
    if action_mode == "full":
        a = np.zeros((17,), dtype=np.float32)
        a[0] = float(pitch)
        a[1] = float(roll)
        a[2] = float(rudder)
        a[3] = float(throttle)
        a[4] = float(gear)
        return a
    raise ValueError(f"unknown action_mode: {action_mode!r}")


@dataclass(frozen=True)
class EpisodeResult:
    seed: int
    world_yaw_deg: float
    wind_speed: float
    wind_dir: float
    dt: float
    steps: int
    terminated: bool
    truncated: bool
    max_abs_cross_m: float | None
    off_runway_first_t: float | None
    end_cross_m: float | None
    reason: str


def _run_one(
    env: UniversalEnv,
    *,
    seed: int,
    policy: str,
    action: np.ndarray | None,
    max_steps: int,
    trace_every_s: float | None,
) -> EpisodeResult:
    obs, _ = env.reset(seed=seed)
    dt = float(env.sim.get_time_step())
    steps = 0
    takeoff_ctrl = None
    if policy == "scripted_takeoff":
        takeoff_ctrl = ScriptedTakeoffController(action_dim=int(env.action_space.shape[0]), dt=dt)
        takeoff_ctrl.reset(obs)

    world_yaw = float(getattr(env.loader, "world_yaw_deg", 0.0))
    wind_speed = float("nan")
    wind_dir = float("nan")

    max_abs_cross: float | None = None
    off_first_t: float | None = None
    end_cross: float | None = None

    next_trace_t = 0.0 if trace_every_s is not None else None

    terminated = False
    truncated = False
    last_info = {}

    for k in range(int(max_steps)):
        if policy == "scripted_takeoff":
            if takeoff_ctrl is not None:
                act = takeoff_ctrl.step(obs)
            else:
                act = scripted_takeoff_action(obs, action_dim=int(env.action_space.shape[0]))
        else:
            assert action is not None
            act = action
        obs, reward, terminated, truncated, info = env.step(act)
        last_info = info if isinstance(info, dict) else {}
        steps = k + 1

        # Wind fields are updated after stepping.
        if k == 0:
            try:
                inst = env.sim.get_instrument_state(env.agent_id)
                wind_speed = float(getattr(inst, "wind_speed", float("nan")))
                wind_dir = float(getattr(inst, "wind_dir", float("nan")))
            except Exception:
                pass

        cross = last_info.get("runway_cross_m", None)
        if cross is not None:
            try:
                cross_f = float(cross)
                end_cross = cross_f
                max_abs_cross = max(abs(cross_f), max_abs_cross or 0.0)
            except Exception:
                pass

        on_geom = last_info.get("on_runway_geom", None)
        on_ground = last_info.get("on_ground", None)
        # `on_runway_geom` is only meaningful pre-liftoff (the env sets it to 0 once airborne).
        # Count "off runway" only while clearly on-ground to avoid misclassifying a normal liftoff.
        if off_first_t is None and on_geom is not None and on_ground is not None:
            try:
                if float(on_ground) > 0.5 and float(on_geom) < 0.5:
                    off_first_t = k * dt
            except Exception:
                pass

        if trace_every_s is not None and next_trace_t is not None:
            t = k * dt
            if t + 1.0e-9 >= next_trace_t:
                try:
                    inst = env.sim.get_instrument_state(env.agent_id)
                    hdg = float(getattr(inst, "heading", 0.0))
                    trk = float(getattr(inst, "ground_track", 0.0))
                    ias = float(getattr(inst, "ias", 0.0))
                except Exception:
                    hdg, trk, ias = 0.0, 0.0, 0.0
                print(
                    f"[trace] seed={seed} t={t:6.2f}s ias={ias:6.1f} hdg={hdg:6.1f} trk={trk:6.1f} "
                    f"cross={('n/a' if end_cross is None else f'{end_cross:7.2f}')} "
                    f"on_geom={last_info.get('on_runway_geom', 'n/a')}"
                )
                next_trace_t = float(next_trace_t) + float(trace_every_s)

        if terminated or truncated:
            break

    # Approximate termination reason
    reason = "truncated" if truncated else "terminated"
    if last_info.get("gear_collapsed", 0.0) > 0.5:
        reason = "gear_collapse"
    elif last_info.get("on_ground", 1.0) > 0.5 and last_info.get("on_runway_geom", 1.0) < 0.5:
        reason = "off_runway"

    return EpisodeResult(
        seed=int(seed),
        world_yaw_deg=world_yaw,
        wind_speed=wind_speed,
        wind_dir=wind_dir,
        dt=dt,
        steps=int(steps),
        terminated=bool(terminated),
        truncated=bool(truncated),
        max_abs_cross_m=max_abs_cross,
        off_runway_first_t=off_first_t,
        end_cross_m=end_cross,
        reason=reason,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Runway drift sweep (fixed action).")
    p.add_argument("--scenario", type=str, default="scenarios/takeoff_stage1.json")
    p.add_argument("--action_mode", type=str, choices=["full", "takeoff2", "takeoff4"], default="takeoff4")
    p.add_argument("--policy", type=str, choices=["fixed", "scripted_takeoff"], default="fixed")
    p.add_argument("--seeds", type=str, default="0:50", help="seed range 'a:b', list '1,2,3', or single '42'")
    p.add_argument("--max_steps", type=int, default=None, help="override scenario max_steps")
    p.add_argument("--trace_every_s", type=float, default=None, help="print a trace line every N seconds")

    # Fixed action knobs
    p.add_argument("--pitch", type=float, default=0.0)
    p.add_argument("--roll", type=float, default=0.0)
    p.add_argument("--rudder", type=float, default=0.0)
    p.add_argument("--throttle", type=float, default=1.0)
    p.add_argument("--gear", type=float, default=1.0)

    args = p.parse_args()

    seeds = _parse_seeds(args.seeds)
    env = UniversalEnv(args.scenario, action_mode=args.action_mode, include_visual=False)
    policy = str(args.policy)
    action = None
    if policy == "fixed":
        action = _make_action(
            action_mode=args.action_mode,
            pitch=args.pitch,
            roll=args.roll,
            rudder=args.rudder,
            throttle=args.throttle,
            gear=args.gear,
        )
        if action.shape != env.action_space.shape:
            raise ValueError(f"action shape mismatch: {action.shape} vs env expects {env.action_space.shape}")
    else:
        # Policy computes actions step-by-step; fixed-action knobs are ignored.
        if int(env.action_space.shape[0]) not in (2, 4, 17):
            raise ValueError(f"unsupported action_dim for policy={policy!r}: {env.action_space.shape}")

    max_steps = int(args.max_steps) if args.max_steps is not None else int(env.max_steps)

    results: list[EpisodeResult] = []
    for s in seeds:
        r = _run_one(
            env,
            seed=int(s),
            policy=policy,
            action=action,
            max_steps=max_steps,
            trace_every_s=args.trace_every_s,
        )
        results.append(r)
        t_end = r.steps * r.dt
        max_cross = "n/a" if r.max_abs_cross_m is None else f"{r.max_abs_cross_m:6.1f}"
        end_cross = "n/a" if r.end_cross_m is None else f"{r.end_cross_m:7.2f}"
        print(
            f"seed={r.seed:4d} yaw={r.world_yaw_deg:6.1f} wind={r.wind_speed:5.2f}@{r.wind_dir:6.1f} "
            f"end_t={t_end:6.2f}s reason={r.reason:10s} max|cross|={max_cross} end_cross={end_cross}"
        )

    # Summary
    off = [r for r in results if r.reason == "off_runway"]
    gear = [r for r in results if r.reason == "gear_collapse"]
    trunc = [r for r in results if r.reason == "truncated"]
    other_term = [r for r in results if r.reason == "terminated"]

    max_cross_vals = [r.max_abs_cross_m for r in results if r.max_abs_cross_m is not None]
    mean_max_cross = float(np.mean(max_cross_vals)) if max_cross_vals else float("nan")
    p95_max_cross = float(np.percentile(max_cross_vals, 95.0)) if max_cross_vals else float("nan")
    worst = None
    if max_cross_vals:
        worst = max(results, key=lambda rr: rr.max_abs_cross_m or -1.0)

    print("-" * 80)
    print(f"seeds: {len(results)} | off_runway: {len(off)} | gear_collapse: {len(gear)} | truncated: {len(trunc)} | other_term: {len(other_term)}")
    if max_cross_vals:
        print(f"max|cross| mean={mean_max_cross:.1f}m p95={p95_max_cross:.1f}m worst={worst.seed} ({worst.max_abs_cross_m:.1f}m)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
