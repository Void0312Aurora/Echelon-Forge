#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from statistics import mean
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)


def _fire_action(*, fire: bool) -> np.ndarray:
    action = np.zeros((12,), dtype=np.float32)
    action[3] = 0.65
    action[6] = 1.0
    action[7] = 1.0 if fire else 0.0
    action[8] = 1.0
    action[9] = 1.0 if fire else 0.0
    action[11] = 1.0
    return action.reshape(1, -1)


def _managed_action() -> np.ndarray:
    action = np.zeros((12,), dtype=np.float32)
    action[3] = 0.65
    action[6] = 1.0
    return action.reshape(1, -1)


def _make_env(args: argparse.Namespace, *, enabled: bool) -> WorldBatchVecEnv:
    return WorldBatchVecEnv(
        scenario_path=os.path.abspath(str(args.scenario)),
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_mode="air_combat_hybrid_v1",
        mission_obs_mode="air_combat_c2_roe_v2",
        step_info_mode="full",
        execution_step_runtime_mode="compiled",
        flight_shaping_backend="compiled",
        worker_threads=int(args.worker_threads),
        batch_observation_backend="compiled",
        batch_visual_backend="compiled",
        observation_return_mode="view",
        air_combat_post_launch_assessment_enabled=enabled,
        air_combat_post_launch_assessment_stages=["A1-S1", "A1-S2"],
        air_combat_post_launch_assessment_max_steps=int(args.post_steps),
        air_combat_post_launch_assessment_gamma=float(args.gamma),
    )


def _run_episode(
    env: WorldBatchVecEnv,
    *,
    seed: int,
    post_steps: int,
    optimized: bool,
    max_prelaunch_steps: int,
) -> dict[str, Any]:
    env.seed(int(seed))
    env.reset()
    t0 = time.perf_counter()
    external_steps = 0
    released = False
    done = False
    release_info: dict[str, Any] = {}
    release_reward = 0.0
    for step in range(int(max_prelaunch_steps)):
        _obs, rewards, dones, infos = env.step(_fire_action(fire=(step % 2 == 0)))
        external_steps += 1
        info = dict(infos[0])
        done = bool(dones[0])
        if bool(info.get("release_executed", False)):
            released = True
            release_info = info
            release_reward = float(rewards[0])
            break
        if done:
            release_info = info
            break
    if released and not optimized:
        for _ in range(int(post_steps)):
            _obs, _rewards, dones, infos = env.step(_managed_action())
            external_steps += 1
            release_info = dict(infos[0])
            done = bool(dones[0])
            if done:
                break
    elapsed = time.perf_counter() - t0
    return {
        "seed": int(seed),
        "optimized": bool(optimized),
        "released": bool(released),
        "done": bool(done),
        "external_steps": int(external_steps),
        "wall_s": float(elapsed),
        "release_reward": float(release_reward),
        "post_launch_assessment_steps": int(release_info.get("post_launch_assessment_steps", 0) or 0),
        "termination_reason": str(release_info.get("termination_reason", "")),
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    released_rows = [row for row in rows if bool(row.get("released", False))]
    return {
        "episodes": len(rows),
        "released": len(released_rows),
        "wall_s_mean": float(mean(float(row["wall_s"]) for row in rows)) if rows else 0.0,
        "external_steps_mean": float(mean(int(row["external_steps"]) for row in rows)) if rows else 0.0,
        "released_wall_s_mean": (
            float(mean(float(row["wall_s"]) for row in released_rows)) if released_rows else 0.0
        ),
        "released_external_steps_mean": (
            float(mean(int(row["external_steps"]) for row in released_rows)) if released_rows else 0.0
        ),
        "assessment_steps_mean": (
            float(mean(int(row["post_launch_assessment_steps"]) for row in released_rows))
            if released_rows
            else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark air-combat post-launch assessment rollout.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument("--post-steps", type=int, default=240)
    parser.add_argument("--max-prelaunch-steps", type=int, default=180)
    parser.add_argument("--gamma", type=float, default=0.999)
    parser.add_argument("--worker-threads", type=int, default=0)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for optimized in (False, True):
        env = _make_env(args, enabled=optimized)
        try:
            for idx in range(int(args.episodes)):
                rows.append(
                    _run_episode(
                        env,
                        seed=int(args.seed) + idx,
                        post_steps=int(args.post_steps),
                        optimized=optimized,
                        max_prelaunch_steps=int(args.max_prelaunch_steps),
                    )
                )
        finally:
            env.close()

    baseline = [row for row in rows if not bool(row["optimized"])]
    optimized_rows = [row for row in rows if bool(row["optimized"])]
    baseline_summary = _summarize(baseline)
    optimized_summary = _summarize(optimized_rows)
    speedup = (
        float(baseline_summary["wall_s_mean"]) / float(optimized_summary["wall_s_mean"])
        if float(optimized_summary["wall_s_mean"]) > 0.0
        else 0.0
    )
    released_speedup = (
        float(baseline_summary["released_wall_s_mean"]) / float(optimized_summary["released_wall_s_mean"])
        if float(optimized_summary["released_wall_s_mean"]) > 0.0
        else 0.0
    )
    step_reduction = (
        1.0 - float(optimized_summary["external_steps_mean"]) / float(baseline_summary["external_steps_mean"])
        if float(baseline_summary["external_steps_mean"]) > 0.0
        else 0.0
    )
    released_step_reduction = (
        1.0
        - float(optimized_summary["released_external_steps_mean"])
        / float(baseline_summary["released_external_steps_mean"])
        if float(baseline_summary["released_external_steps_mean"]) > 0.0
        else 0.0
    )
    payload = {
        "scenario": os.path.abspath(str(args.scenario)),
        "post_steps": int(args.post_steps),
        "episodes": int(args.episodes),
        "baseline": baseline_summary,
        "optimized": optimized_summary,
        "speedup_wall_mean": float(speedup),
        "released_speedup_wall_mean": float(released_speedup),
        "external_step_reduction_fraction": float(step_reduction),
        "released_external_step_reduction_fraction": float(released_step_reduction),
        "rows": rows,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    print(text)
    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
