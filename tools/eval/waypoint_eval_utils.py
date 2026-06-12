from __future__ import annotations

from typing import Any

import numpy as np


def make_waypoint_distance_trackers(env) -> tuple[list[dict[str, Any]], list[float]]:
    base_env = getattr(env, "unwrapped", env)
    waypoints = list(getattr(getattr(base_env, "loader", None), "waypoints", []) or [])
    return waypoints, [float("inf")] * len(waypoints)


def update_waypoint_min_distances(env, waypoints: list[dict[str, Any]], wp_min_d: list[float]) -> None:
    if not wp_min_d:
        return
    try:
        base_env = getattr(env, "unwrapped", env)
        truth = base_env.sim.get_agent_observation(base_env.agent_id)
        x = float(getattr(truth, "x", 0.0))
        y = float(getattr(truth, "y", 0.0))
        for i, wp in enumerate(waypoints):
            dx = float(wp.get("x", 0.0)) - x
            dy = float(wp.get("y", 0.0)) - y
            dist = float(np.hypot(dx, dy))
            if dist < wp_min_d[i]:
                wp_min_d[i] = dist
    except Exception:
        pass


def update_waypoint_distance_samples(
    info: dict[str, Any] | Any,
    dists: list[float],
    last_ms: np.ndarray | None,
) -> np.ndarray | None:
    if not isinstance(info, dict):
        return last_ms
    mission_status = info.get("mission_status", None)
    if mission_status is None:
        return last_ms
    try:
        ms_arr = np.asarray(mission_status, dtype=np.float32).reshape(-1)
        if ms_arr.size >= 1:
            if ms_arr.size >= 4 and float(ms_arr[3]) < -0.5:
                return ms_arr
            dist = float(ms_arr[0])
            if np.isfinite(dist):
                dists.append(dist)
        return ms_arr
    except Exception:
        return last_ms


def finalize_waypoint_episode(
    *,
    last_ms: np.ndarray | None,
    dists: list[float],
    wp_min_d: list[float],
) -> dict[str, float | bool | int]:
    success = False
    failed = False
    wp_idx = 0
    dist_final = float("nan")
    if last_ms is not None and last_ms.size >= 4:
        success = bool(float(last_ms[3]) > 0.5)
        failed = bool(float(last_ms[3]) < -0.5)
        wp_idx = int(float(last_ms[1])) if last_ms.size >= 2 else 0
        if not failed and last_ms.size >= 1:
            dist_final = float(last_ms[0])

    if wp_min_d:
        wp_min_last = float(wp_min_d[-1])
        wp_min_max = float(np.max(np.asarray(wp_min_d, dtype=np.float64)))
    else:
        wp_min_last = float("nan")
        wp_min_max = float("nan")

    return {
        "success": success,
        "failed": failed,
        "wp_idx": wp_idx,
        "min_dist": float(np.min(dists)) if dists else float("nan"),
        "final_dist": float(dist_final),
        "wp_min_last": wp_min_last,
        "wp_min_max": wp_min_max,
    }
