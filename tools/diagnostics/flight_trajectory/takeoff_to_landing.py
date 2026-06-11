#!/usr/bin/env python3
"""
2D trajectory diagnostic for the continuous takeoff-to-landing task.

This script runs a single episode through the real UniversalEnv + wrapper stack
and exports:
  - a PNG with the flown ground track, selected waypoints, and runway geometry
  - a JSON summary with termination / phase-transition metadata

Use cases:
  - Compare scripted baseline success vs failure seeds
  - Compare trained checkpoint behavior against the scripted baseline
  - Inspect whether failures come from route geometry, premature turn-in,
    landing overshoot, or complete failure to sequence the waypoint route
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

BASE_DIR = ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv
from python.env_config import resolve_env_settings
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.control.wrappers import get_action_wrapper_spec


@dataclass(frozen=True)
class EpisodeSummary:
    scenario: str
    seed: int
    mode: str
    zero_randomization: bool
    steps: int
    terminated: bool
    truncated: bool
    termination_reason: str
    mission_status: list[float]
    world_yaw_deg: float
    waypoint_template_idx: int
    selected_waypoint_count: int
    landing_transition_step: int | None
    final_waypoint_idx: int
    final_command_code: int
    final_baseline_mode: str
    final_position_xyz_m: list[float]
    final_runway_along_m: float | None
    final_runway_cross_m: float | None
    final_ias_mps: float | None
    final_ground_speed_mps: float | None
    final_altitude_agl_m: float | None
    final_on_ground: float | None
    final_on_runway_geom: float | None


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def _zero_randomization_overrides() -> dict[str, Any]:
    return {
        "world_yaw_range": [0.0, 0.0],
        "wind_headwind_range": [0.0, 0.0],
        "wind_crosswind_range": [0.0, 0.0],
        "wind_tailwind_max_mps": 0.0,
        "wind_shear_range": [0.0, 0.0],
    }


def _load_policy(model_path: str, algo: str):
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device="cpu")
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, device="cpu")


def _resolve_train_config(path: str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return _load_json(path)


def _make_env(
    *,
    scenario_path: str,
    train_config: dict[str, Any] | None,
    scripted: bool,
    zero_randomization: bool,
):
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None

    env_settings = resolve_env_settings(train_config or {}, _Args())
    if scripted:
        # Scripted diagnostics do not consume pixel observations; disabling them
        # keeps the diagnostic fast while preserving task geometry and mission logic.
        env_settings["include_visual"] = False
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config or {})
    if scripted:
        if wrapper_class is None:
            raise ValueError("scripted mode requires a train config that enables the action wrapper")
        wrapper_kwargs = dict(wrapper_kwargs or {})
        wrapper_kwargs["scripted_residual_scale"] = 0.0
        wrapper_kwargs["scripted_residual_alt_breakpoints_m"] = []
        wrapper_kwargs["scripted_residual_alt_scales"] = []
        wrapper_kwargs["action_rate_penalty_coef"] = 0.0

    env = UniversalEnv(os.path.abspath(scenario_path), **env_settings)
    if zero_randomization:
        env.set_randomization_overrides(_zero_randomization_overrides())
    if wrapper_class is not None:
        env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env


def _pick_runway_beacon(loader, x_ref: float, y_ref: float) -> dict[str, Any] | None:
    ref_name = None
    try:
        post = loader.scenario_data.get("mission_command", {}).get("post_waypoint_transition", {})
        if isinstance(post, dict):
            ref_name = str(post.get("reference_runway", "")).strip()
    except Exception:
        ref_name = None
    beacons = list(getattr(loader, "ils_beacons", []) or [])
    if not beacons:
        return None
    if ref_name:
        for b in beacons:
            if str(b.get("name", "")).strip() == ref_name:
                return dict(b)
    best = None
    best_d2 = float("inf")
    for b in beacons:
        dx = float(x_ref) - float(b.get("cx", 0.0))
        dy = float(y_ref) - float(b.get("cy", 0.0))
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best = b
    return dict(best) if isinstance(best, dict) else None


def _runway_outline(beacon: dict[str, Any]) -> np.ndarray:
    cx = float(beacon.get("cx", 0.0))
    cy = float(beacon.get("cy", 0.0))
    length = float(beacon.get("length", 0.0))
    width = float(beacon.get("width", 0.0))
    heading = math.radians(float(beacon.get("heading", 0.0)))
    fwd = np.asarray([math.sin(heading), math.cos(heading)], dtype=np.float64)
    right = np.asarray([math.cos(heading), -math.sin(heading)], dtype=np.float64)
    center = np.asarray([cx, cy], dtype=np.float64)
    hl = 0.5 * length
    hw = 0.5 * width
    corners = [
        center - hl * fwd - hw * right,
        center - hl * fwd + hw * right,
        center + hl * fwd + hw * right,
        center + hl * fwd - hw * right,
        center - hl * fwd - hw * right,
    ]
    return np.asarray(corners, dtype=np.float64)


def _collect_episode(
    *,
    env,
    model,
    scripted: bool,
    seed: int,
    max_steps: int | None,
    zero_randomization: bool,
):
    obs, _info = env.reset(seed=int(seed))
    sim_env = env.unwrapped
    loader = sim_env.loader

    start_pos = np.asarray(sim_env.sim.get_unit_position(sim_env.agent_id), dtype=np.float64)
    runway_beacon = _pick_runway_beacon(loader, float(start_pos[0]), float(start_pos[1]))
    waypoints = [dict(wp) for wp in list(getattr(loader, "waypoints", []) or [])]
    waypoint_template_idx = int(loader.mission_cmd.get("_waypoint_template_idx", -2))

    action = np.zeros(env.action_space.shape, dtype=np.float32)
    limit = int(max_steps) if max_steps is not None else int(getattr(sim_env, "max_steps", 0))
    if limit <= 0:
        limit = 20000

    xs = [float(start_pos[0])]
    ys = [float(start_pos[1])]
    zs = [float(start_pos[2])]
    cmd_codes = [int(loader.mission_cmd.get("command_code", 0))]
    wp_indices = [int(getattr(loader, "waypoint_idx", 0))]
    baseline_modes = [str("")]
    runway_crosses = [None]
    runway_alongs = [None]

    term_reason = ""
    mission_status = []
    terminated = False
    truncated = False
    landing_transition_step = None
    final_info: dict[str, Any] = {}
    final_inst = None

    for step in range(1, limit + 1):
        if scripted:
            act = action
        else:
            act, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(act)
        final_info = info if isinstance(info, dict) else {}
        try:
            final_inst = sim_env.sim.get_instrument_state(sim_env.agent_id)
        except Exception:
            final_inst = None

        pos = np.asarray(sim_env.sim.get_unit_position(sim_env.agent_id), dtype=np.float64)
        xs.append(float(pos[0]))
        ys.append(float(pos[1]))
        zs.append(float(pos[2]))

        cmd_code = int(loader.mission_cmd.get("command_code", 0))
        wp_idx = int(getattr(loader, "waypoint_idx", 0))
        mode_active = str(final_info.get("scripted_baseline_mode_active", ""))

        if landing_transition_step is None and cmd_code >= 4:
            landing_transition_step = int(step)

        cmd_codes.append(cmd_code)
        wp_indices.append(wp_idx)
        baseline_modes.append(mode_active)
        runway_crosses.append(
            float(final_info["runway_cross_m"]) if "runway_cross_m" in final_info and final_info["runway_cross_m"] is not None else None
        )
        runway_alongs.append(
            float(final_info["runway_along_m"]) if "runway_along_m" in final_info and final_info["runway_along_m"] is not None else None
        )

        if terminated or truncated:
            term_reason = str(final_info.get("termination_reason", ""))
            ms = final_info.get("mission_status", [])
            try:
                mission_status = np.asarray(ms, dtype=np.float32).reshape(-1).tolist()
            except Exception:
                mission_status = []
            break

    final_pos = [float(xs[-1]), float(ys[-1]), float(zs[-1])]
    final_ias = None
    final_ground_speed = None
    final_alt_agl = None
    if final_inst is not None:
        try:
            final_ias = float(getattr(final_inst, "ias", float("nan")))
        except Exception:
            final_ias = None
        try:
            final_ground_speed = float(getattr(final_inst, "ground_speed", float("nan")))
        except Exception:
            final_ground_speed = None
        try:
            final_alt_agl = float(getattr(final_inst, "altitude_agl", float("nan")))
        except Exception:
            final_alt_agl = None
    summary = EpisodeSummary(
        scenario=str(getattr(loader, "scenario_name", "")) or os.path.basename(str(getattr(sim_env, "scenario_path", ""))),
        seed=int(seed),
        mode="scripted" if scripted else "model",
        zero_randomization=bool(zero_randomization),
        steps=int(len(xs) - 1),
        terminated=bool(terminated),
        truncated=bool(truncated),
        termination_reason=str(term_reason),
        mission_status=list(mission_status),
        world_yaw_deg=float(getattr(loader, "world_yaw_deg", 0.0)),
        waypoint_template_idx=int(waypoint_template_idx),
        selected_waypoint_count=int(len(waypoints)),
        landing_transition_step=int(landing_transition_step) if landing_transition_step is not None else None,
        final_waypoint_idx=int(wp_indices[-1]),
        final_command_code=int(cmd_codes[-1]),
        final_baseline_mode=str(baseline_modes[-1]),
        final_position_xyz_m=list(final_pos),
        final_runway_along_m=runway_alongs[-1],
        final_runway_cross_m=runway_crosses[-1],
        final_ias_mps=final_ias,
        final_ground_speed_mps=final_ground_speed,
        final_altitude_agl_m=final_alt_agl,
        final_on_ground=float(final_info["on_ground"]) if "on_ground" in final_info and final_info["on_ground"] is not None else None,
        final_on_runway_geom=float(final_info["on_runway_geom"]) if "on_runway_geom" in final_info and final_info["on_runway_geom"] is not None else None,
    )
    return {
        "summary": summary,
        "x": np.asarray(xs, dtype=np.float64),
        "y": np.asarray(ys, dtype=np.float64),
        "z": np.asarray(zs, dtype=np.float64),
        "cmd_code": np.asarray(cmd_codes, dtype=np.int32),
        "waypoint_idx": np.asarray(wp_indices, dtype=np.int32),
        "baseline_mode": list(baseline_modes),
        "waypoints": waypoints,
        "runway_beacon": runway_beacon,
    }


def _phase_color(mode: str, cmd_code: int) -> str:
    mode = str(mode).strip().lower()
    if mode == "takeoff":
        return "#2a9d8f"
    if mode == "stable_flight":
        return "#1d4ed8"
    if mode == "landing_ils":
        return "#d97706"
    if int(cmd_code) >= 4:
        return "#d97706"
    return "#1d4ed8"


def _plot_track(ax, data: dict[str, Any], *, zoom: bool) -> None:
    x = np.asarray(data["x"], dtype=np.float64)
    y = np.asarray(data["y"], dtype=np.float64)
    cmd_code = np.asarray(data["cmd_code"], dtype=np.int32)
    baseline_mode = list(data["baseline_mode"])

    if x.size >= 2:
        segs = np.stack(
            [
                np.column_stack([x[:-1], y[:-1]]),
                np.column_stack([x[1:], y[1:]]),
            ],
            axis=1,
        )
        colors = [_phase_color(baseline_mode[i + 1], int(cmd_code[i + 1])) for i in range(x.size - 1)]
        lc = LineCollection(segs, colors=colors, linewidths=1.4 if zoom else 1.1, alpha=0.95)
        ax.add_collection(lc)

    wps = list(data["waypoints"])
    if wps:
        wp_xy = np.asarray([[float(wp.get("x", 0.0)), float(wp.get("y", 0.0))] for wp in wps], dtype=np.float64)
        ax.plot(wp_xy[:, 0], wp_xy[:, 1], linestyle="--", color="#6b7280", linewidth=1.0, alpha=0.7, zorder=1)
        for i, wp in enumerate(wps, start=1):
            wx = float(wp.get("x", 0.0))
            wy = float(wp.get("y", 0.0))
            rad = float(wp.get("radius_m", 0.0))
            mode = str(wp.get("waypoint_mode", "flyby")).strip().lower()
            edge = "#111827" if mode == "flyover" else "#6b7280"
            fill = "#fde68a" if mode == "flyover" else "#dbeafe"
            circ = plt.Circle((wx, wy), rad, edgecolor=edge, facecolor=fill, linewidth=0.9, alpha=0.18, zorder=0)
            ax.add_patch(circ)
            ax.scatter([wx], [wy], s=18 if mode == "flyover" else 12, color=edge, zorder=3)
            ax.text(wx, wy, f"WP{i}", fontsize=7, ha="left", va="bottom", color=edge)

    runway = data.get("runway_beacon")
    if isinstance(runway, dict):
        outline = _runway_outline(runway)
        ax.plot(outline[:, 0], outline[:, 1], color="#111827", linewidth=1.2, alpha=0.9, zorder=2)
        cx = float(runway.get("cx", 0.0))
        cy = float(runway.get("cy", 0.0))
        heading = math.radians(float(runway.get("heading", 0.0)))
        fwd_x = math.sin(heading)
        fwd_y = math.cos(heading)
        hl = 0.5 * float(runway.get("length", 0.0))
        ax.plot(
            [cx - hl * fwd_x, cx + hl * fwd_x],
            [cy - hl * fwd_y, cy + hl * fwd_y],
            color="#111827",
            linewidth=0.9,
            alpha=0.7,
            linestyle=":",
            zorder=2,
        )
        thr_x = float(runway.get("thr_x", cx - hl * fwd_x))
        thr_y = float(runway.get("thr_y", cy - hl * fwd_y))
        ax.scatter([thr_x], [thr_y], s=30, marker="s", color="#ef4444", zorder=4)
        ax.text(thr_x, thr_y, str(runway.get("name", "runway")), fontsize=7, ha="left", va="top", color="#991b1b")

    ax.scatter([x[0]], [y[0]], s=28, marker="o", color="#16a34a", zorder=5)
    ax.scatter([x[-1]], [y[-1]], s=34, marker="X", color="#dc2626", zorder=5)

    landing_transition_step = getattr(data["summary"], "landing_transition_step", None)
    if landing_transition_step is not None and 0 <= landing_transition_step < x.size:
        ax.scatter([x[landing_transition_step]], [y[landing_transition_step]], s=28, marker="D", color="#f59e0b", zorder=5)
        ax.text(
            x[landing_transition_step],
            y[landing_transition_step],
            "landing transition",
            fontsize=7,
            ha="left",
            va="bottom",
            color="#92400e",
        )

    if zoom:
        runway = data.get("runway_beacon")
        if isinstance(runway, dict):
            subset_x = [float(runway.get("cx", 0.0)), float(runway.get("thr_x", runway.get("cx", 0.0)))]
            subset_y = [float(runway.get("cy", 0.0)), float(runway.get("thr_y", runway.get("cy", 0.0)))]
            for wp in wps[-4:]:
                subset_x.append(float(wp.get("x", 0.0)))
                subset_y.append(float(wp.get("y", 0.0)))
            subset_x.extend(x[max(0, x.size - 2500) :].tolist())
            subset_y.extend(y[max(0, y.size - 2500) :].tolist())
            pad = 2500.0
            ax.set_xlim(min(subset_x) - pad, max(subset_x) + pad)
            ax.set_ylim(min(subset_y) - pad, max(subset_y) + pad)

    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)
    ax.set_xlabel("East x (m)")
    ax.set_ylabel("North y (m)")


def _save_plot(data: dict[str, Any], output_path: str) -> None:
    summary: EpisodeSummary = data["summary"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
    _plot_track(axes[0], data, zoom=False)
    _plot_track(axes[1], data, zoom=True)
    axes[0].set_title("Full Mission Track")
    axes[1].set_title("Approach / Runway Zoom")

    mission_status = ",".join(f"{v:.1f}" for v in summary.mission_status) if summary.mission_status else "n/a"
    meta = (
        f"mode={summary.mode} seed={summary.seed} steps={summary.steps} "
        f"term={summary.termination_reason or 'n/a'}\n"
        f"world_yaw={summary.world_yaw_deg:.1f}deg template={summary.waypoint_template_idx} "
        f"cmd_final={summary.final_command_code} wp_final={summary.final_waypoint_idx}\n"
        f"landing_transition_step={summary.landing_transition_step} mission_status=[{mission_status}]"
    )
    fig.suptitle(str(summary.scenario), fontsize=13)
    fig.text(0.5, 0.01, meta, ha="center", va="bottom", fontsize=9, family="monospace")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _main() -> int:
    p = argparse.ArgumentParser(description="Export 2D trajectory diagnostics for the continuous takeoff-to-landing task.")
    p.add_argument("--scenario", type=str, required=True)
    p.add_argument("--train_config", type=str, required=True)
    p.add_argument("--model", type=str, default=None, help="SB3 model zip/path. Omit for scripted baseline.")
    p.add_argument("--algo", type=str, default="auto", help="auto / AdaptiveKLPPO / PPO")
    p.add_argument("--scripted", action="store_true", help="Run the pure scripted baseline (wrapper residual scale forced to zero).")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max_steps", type=int, default=None)
    p.add_argument("--zero_randomization", action="store_true")
    p.add_argument("--output", type=str, required=True, help="PNG output path")
    args = p.parse_args()

    if bool(args.scripted) == bool(args.model):
        raise ValueError("choose exactly one of --scripted or --model")

    train_config = _resolve_train_config(args.train_config)
    env = _make_env(
        scenario_path=args.scenario,
        train_config=train_config,
        scripted=bool(args.scripted),
        zero_randomization=bool(args.zero_randomization),
    )
    model = None if args.scripted else _load_policy(os.path.abspath(args.model), algo=str(args.algo))

    data = _collect_episode(
        env=env,
        model=model,
        scripted=bool(args.scripted),
        seed=int(args.seed),
        max_steps=args.max_steps,
        zero_randomization=bool(args.zero_randomization),
    )
    summary: EpisodeSummary = data["summary"]

    out_png = os.path.abspath(args.output)
    out_json = os.path.splitext(out_png)[0] + ".json"
    _save_plot(data, out_png)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, indent=2)

    print(f"saved_plot={out_png}")
    print(f"saved_summary={out_json}")
    print(json.dumps(asdict(summary), indent=2))
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
