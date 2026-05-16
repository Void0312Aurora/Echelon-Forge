#!/usr/bin/env python3
"""
Unified cooperative trajectory diagnostic for maintained cooperative tasks.

This CLI replays one cooperative world episode and exports:
  - a PNG with task-specific trajectory / telemetry panels
  - a JSON payload with per-step traces and per-slot summaries

Supported tasks:
  - takeoff
  - takeoff_to_cruise
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from tools.diagnostics.cooperative_trajectory_base import (
    SLOT_COLORS,
    apply_curriculum_stage,
    array_head,
    clearance_segments,
    cooperative_action_wrapper_kwargs,
    first_step,
    load_json_config,
    load_policy_cpu,
    make_env_settings,
    mission_status_list,
    pick_runway_beacon,
    plot_clearance_trace,
    plot_scalar_trace,
    runway_outline,
    run_episode,
    success_from_mission_status,
    to_jsonable,
)


TASK_TAKEOFF = "takeoff"
TASK_TAKEOFF_TO_CRUISE = "takeoff_to_cruise"


def _safe_metric_max(samples: list[dict[str, Any]], key: str) -> float:
    values = np.asarray([sample.get(key, np.nan) for sample in samples], dtype=np.float64).reshape(-1)
    finite = values[np.isfinite(values)]
    if finite.size <= 0:
        return float("nan")
    return float(np.max(finite))


def _runway_frame(loader, x_m: float, y_m: float) -> tuple[float | None, float | None, float | None, float | None]:
    try:
        valid, along_m, cross_m, rw_len_m, rw_wid_m = loader.get_runway_local_frame(float(x_m), float(y_m))
    except Exception:
        return None, None, None, None
    if not bool(valid):
        return None, None, None, None
    return float(along_m), float(cross_m), float(rw_len_m), float(rw_wid_m)


def _capture_takeoff_sample(
    slot_state,
    *,
    step_index: int,
    sim_time_s: float,
    reward: float | None,
    info: dict[str, Any] | None,
) -> dict[str, Any]:
    loader = slot_state.loader
    truth = slot_state.last_truth
    inst = slot_state.last_inst
    mission_cmd = dict(getattr(loader, "mission_cmd", {}) or {})

    x_m = float(getattr(truth, "x", float("nan"))) if truth is not None else float("nan")
    y_m = float(getattr(truth, "y", float("nan"))) if truth is not None else float("nan")
    z_m = float(getattr(truth, "z", float("nan"))) if truth is not None else float("nan")
    heading_deg = None
    if truth is not None and hasattr(truth, "heading"):
        heading_deg = float(getattr(truth, "heading"))
    elif inst is not None and hasattr(inst, "heading"):
        heading_deg = float(getattr(inst, "heading"))

    ground_speed_mps = float(getattr(inst, "ground_speed", float("nan"))) if inst is not None else float("nan")
    ias_mps = float(getattr(inst, "ias", float("nan"))) if inst is not None else float("nan")
    alt_agl_m = float(getattr(inst, "alt_radar", float("nan"))) if inst is not None else float("nan")
    gear_pos = float(getattr(inst, "gear_pos", float("nan"))) if inst is not None else float("nan")
    throttle_pos = float(getattr(inst, "throttle_pos", float("nan"))) if inst is not None else float("nan")

    runway_along_m, runway_cross_m, runway_len_m, runway_wid_m = _runway_frame(loader, x_m, y_m)
    rewards_cfg = loader.get_rewards_config()
    on_ground_alt_threshold = float(rewards_cfg.get("on_ground_alt_threshold", 2.5))
    on_ground = bool(np.isfinite(alt_agl_m) and alt_agl_m <= on_ground_alt_threshold)
    on_runway_geom = None
    if runway_along_m is not None and runway_cross_m is not None and runway_len_m is not None and runway_wid_m is not None:
        width_margin_m = float(rewards_cfg.get("runway_width_margin_m", 2.0))
        length_margin_m = float(rewards_cfg.get("runway_length_margin_m", 0.0))
        on_runway_geom = bool(
            on_ground
            and abs(float(runway_cross_m)) <= 0.5 * float(runway_wid_m) + width_margin_m
            and abs(float(runway_along_m)) <= 0.5 * float(runway_len_m) + length_margin_m
        )

    mission_status = mission_status_list(info)
    return {
        "step": int(step_index),
        "sim_time_s": float(sim_time_s),
        "x_m": float(x_m),
        "y_m": float(y_m),
        "z_m": float(z_m),
        "heading_deg": None if heading_deg is None else float(heading_deg),
        "ground_speed_mps": float(ground_speed_mps),
        "ias_mps": float(ias_mps),
        "altitude_agl_m": float(alt_agl_m),
        "gear_pos": float(gear_pos),
        "throttle_pos": float(throttle_pos),
        "reward": None if reward is None else float(reward),
        "mission_status": mission_status,
        "success_flag": bool(success_from_mission_status(mission_status)),
        "runway_along_m": None if runway_along_m is None else float(runway_along_m),
        "runway_cross_m": None if runway_cross_m is None else float(runway_cross_m),
        "on_ground": bool(on_ground),
        "on_runway_geom": on_runway_geom,
        "takeoff_procedure_code": int(mission_cmd.get("takeoff_procedure_code", 0) or 0),
        "takeoff_clearance_code": int(mission_cmd.get("takeoff_clearance_code", 0) or 0),
        "takeoff_interval_s": float(mission_cmd.get("takeoff_interval_s", 0.0) or 0.0),
        "runway_slot_code": int(mission_cmd.get("runway_slot_code", 0) or 0),
        "scripted_baseline_mode_active": (
            None if not isinstance(info, dict) else str(info.get("scripted_baseline_mode_active", "") or "")
        ),
        "effective_action_head": None if not isinstance(info, dict) else array_head(info.get("effective_action", None)),
        "baseline_action_head": None if not isinstance(info, dict) else array_head(info.get("baseline_action", None)),
    }


def _capture_takeoff_to_cruise_sample(
    slot_state,
    *,
    step_index: int,
    sim_time_s: float,
    reward: float | None,
    info: dict[str, Any] | None,
) -> dict[str, Any]:
    loader = slot_state.loader
    truth = slot_state.last_truth
    inst = slot_state.last_inst
    mission_cmd = dict(getattr(loader, "mission_cmd", {}) or {})

    x_m = float(getattr(truth, "x", float("nan"))) if truth is not None else float("nan")
    y_m = float(getattr(truth, "y", float("nan"))) if truth is not None else float("nan")
    z_m = float(getattr(truth, "z", float("nan"))) if truth is not None else float("nan")
    heading_deg = float(getattr(truth, "heading", float("nan"))) if truth is not None and hasattr(truth, "heading") else None
    ground_speed_mps = float(getattr(inst, "ground_speed", float("nan"))) if inst is not None else float("nan")
    alt_agl_m = float(getattr(inst, "alt_radar", float("nan"))) if inst is not None else float("nan")

    mission_status = mission_status_list(info)
    distance_to_wp_m = None if len(mission_status) < 1 else float(mission_status[0])
    waypoint_index = None if len(mission_status) < 2 else float(mission_status[1])
    waypoint_count = None if len(mission_status) < 3 else float(mission_status[2])

    return {
        "step": int(step_index),
        "sim_time_s": float(sim_time_s),
        "x_m": float(x_m),
        "y_m": float(y_m),
        "z_m": float(z_m),
        "heading_deg": None if heading_deg is None else float(heading_deg),
        "ground_speed_mps": float(ground_speed_mps),
        "altitude_agl_m": float(alt_agl_m),
        "reward": None if reward is None else float(reward),
        "mission_status": mission_status,
        "success_flag": bool(success_from_mission_status(mission_status)),
        "distance_to_active_waypoint_m": distance_to_wp_m,
        "waypoint_index": waypoint_index,
        "waypoint_count": waypoint_count,
        "takeoff_clearance_code": int(mission_cmd.get("takeoff_clearance_code", 0) or 0),
        "takeoff_interval_s": float(mission_cmd.get("takeoff_interval_s", 0.0) or 0.0),
        "target_heading_deg": float(mission_cmd.get("target_heading", 0.0) or 0.0),
        "target_altitude_m": float(mission_cmd.get("target_altitude", 0.0) or 0.0),
        "target_speed_mps": float(mission_cmd.get("target_speed", 0.0) or 0.0),
        "scripted_baseline_mode_active": (
            None if not isinstance(info, dict) else str(info.get("scripted_baseline_mode_active", "") or "")
        ),
        "effective_action_head": None if not isinstance(info, dict) else array_head(info.get("effective_action", None)),
        "baseline_action_head": None if not isinstance(info, dict) else array_head(info.get("baseline_action", None)),
    }


def _build_takeoff_slot_summary(slot_meta: dict[str, Any], samples: list[dict[str, Any]], final_info: dict[str, Any]) -> dict[str, Any]:
    final_sample = samples[-1]
    mission_status = mission_status_list(final_info)
    episode = final_info.get("episode", {}) if isinstance(final_info.get("episode", {}), dict) else {}
    return {
        "slot_index": int(slot_meta["slot_index"]),
        "slot_name": str(slot_meta["slot_name"]),
        "entity_name": str(slot_meta["entity_name"]),
        "formation_role_id": str(slot_meta["formation_role_id"] or ""),
        "reference_entity_name": slot_meta["reference_entity_name"],
        "policy_route": slot_meta["policy_route"],
        "success": bool(success_from_mission_status(mission_status)),
        "termination_reason": str(final_info.get("termination_reason", "") or ""),
        "episode_reward": float(episode.get("r", 0.0)),
        "episode_length": int(episode.get("l", 0)),
        "trace_sample_count": int(len(samples)),
        "first_release_step": first_step(samples, lambda sample: int(sample.get("takeoff_clearance_code", 0) or 0) >= 3),
        "first_roll_step": first_step(samples, lambda sample: float(sample.get("ground_speed_mps", 0.0) or 0.0) >= 5.0),
        "first_liftoff_step": first_step(samples, lambda sample: float(sample.get("altitude_agl_m", 0.0) or 0.0) >= 5.0),
        "max_altitude_agl_m": _safe_metric_max(samples, "altitude_agl_m"),
        "max_ground_speed_mps": _safe_metric_max(samples, "ground_speed_mps"),
        "final_pre_reset_position_xyz_m": [
            float(final_sample["x_m"]),
            float(final_sample["y_m"]),
            float(final_sample["z_m"]),
        ],
        "final_pre_reset_heading_deg": None if final_sample["heading_deg"] is None else float(final_sample["heading_deg"]),
        "final_pre_reset_runway_along_m": (
            None if final_sample.get("runway_along_m") is None else float(final_sample["runway_along_m"])
        ),
        "final_pre_reset_runway_cross_m": (
            None if final_sample.get("runway_cross_m") is None else float(final_sample["runway_cross_m"])
        ),
        "terminal_runway_along_m": (
            None if final_info.get("runway_along_m", None) is None else float(final_info["runway_along_m"])
        ),
        "terminal_runway_cross_m": (
            None if final_info.get("runway_cross_m", None) is None else float(final_info["runway_cross_m"])
        ),
        "clearance_segments": clearance_segments(samples),
    }


def _build_takeoff_to_cruise_slot_summary(
    slot_meta: dict[str, Any],
    samples: list[dict[str, Any]],
    final_info: dict[str, Any],
) -> dict[str, Any]:
    mission_status = mission_status_list(final_info)
    episode = final_info.get("episode", {}) if isinstance(final_info.get("episode", {}), dict) else {}
    return {
        "slot_index": int(slot_meta["slot_index"]),
        "slot_name": str(slot_meta["slot_name"]),
        "entity_name": str(slot_meta["entity_name"]),
        "formation_role_id": str(slot_meta["formation_role_id"] or ""),
        "reference_entity_name": slot_meta["reference_entity_name"],
        "policy_route": slot_meta["policy_route"],
        "success": bool(success_from_mission_status(mission_status)),
        "termination_reason": str(final_info.get("termination_reason", "") or ""),
        "episode_reward": float(episode.get("r", 0.0)),
        "episode_length": int(episode.get("l", 0)),
        "trace_sample_count": int(len(samples)),
        "first_release_step": first_step(samples, lambda sample: int(sample.get("takeoff_clearance_code", 0) or 0) >= 3),
        "first_roll_step": first_step(samples, lambda sample: float(sample.get("ground_speed_mps", 0.0) or 0.0) >= 5.0),
        "first_liftoff_step": first_step(samples, lambda sample: float(sample.get("altitude_agl_m", 0.0) or 0.0) >= 5.0),
        "first_waypoint_capture_step": first_step(
            samples,
            lambda sample: float(sample.get("waypoint_index", 0.0) or 0.0) >= 1.0,
        ),
        "max_altitude_agl_m": _safe_metric_max(samples, "altitude_agl_m"),
        "max_ground_speed_mps": _safe_metric_max(samples, "ground_speed_mps"),
        "final_waypoint_index": None if len(mission_status) < 2 else float(mission_status[1]),
        "final_waypoint_count": None if len(mission_status) < 3 else float(mission_status[2]),
        "final_distance_to_active_waypoint_m": None if len(mission_status) < 1 else float(mission_status[0]),
        "clearance_segments": clearance_segments(samples),
    }


def _plot_ground_track(
    ax,
    traces: list[list[dict[str, Any]]],
    slot_meta: list[dict[str, Any]],
    runway_beacon: dict[str, Any] | None,
    *,
    mark_liftoff: bool,
) -> None:
    for slot_index, samples in enumerate(traces):
        color = SLOT_COLORS[slot_index % len(SLOT_COLORS)]
        x = np.asarray([sample["x_m"] for sample in samples], dtype=np.float64)
        y = np.asarray([sample["y_m"] for sample in samples], dtype=np.float64)
        label = str(slot_meta[slot_index]["slot_name"])
        ax.plot(x, y, color=color, linewidth=1.8, label=label)
        ax.scatter([x[0]], [y[0]], s=30, marker="o", color=color, edgecolors="black", linewidths=0.5, zorder=5)
        ax.scatter([x[-1]], [y[-1]], s=42, marker="X", color=color, edgecolors="black", linewidths=0.5, zorder=5)
        if mark_liftoff:
            liftoff_step = first_step(
                samples,
                lambda sample: float(sample.get("altitude_agl_m", 0.0) or 0.0) >= 5.0,
            )
            if liftoff_step is not None:
                idx = min(len(samples) - 1, max(0, int(liftoff_step) - int(samples[0]["step"])))
                ax.scatter([x[idx]], [y[idx]], s=48, marker="^", color=color, edgecolors="black", linewidths=0.5, zorder=6)

    if isinstance(runway_beacon, dict):
        outline = runway_outline(runway_beacon)
        ax.plot(outline[:, 0], outline[:, 1], color="#111827", linewidth=1.2, alpha=0.95, zorder=2)
    ax.set_title("Ground Track")
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)
    ax.set_xlabel("East x (m)")
    ax.set_ylabel("North y (m)")
    ax.legend(loc="best", fontsize=8)


def _plot_waypoint_trace(ax, traces: list[list[dict[str, Any]]], slot_meta: list[dict[str, Any]]) -> None:
    ax2 = ax.twinx()
    for slot_index, samples in enumerate(traces):
        color = SLOT_COLORS[slot_index % len(SLOT_COLORS)]
        t = np.asarray([sample["sim_time_s"] for sample in samples], dtype=np.float64)
        idx = np.asarray(
            [0.0 if sample.get("waypoint_index") is None else float(sample["waypoint_index"]) for sample in samples],
            dtype=np.float64,
        )
        dist = np.asarray(
            [
                np.nan
                if sample.get("distance_to_active_waypoint_m") is None
                else float(sample["distance_to_active_waypoint_m"])
                for sample in samples
            ],
            dtype=np.float64,
        )
        ax.plot(t, idx, color=color, linewidth=1.8, label=f"{slot_meta[slot_index]['slot_name']} wp_idx")
        ax2.plot(t, dist, color=color, linewidth=1.0, linestyle="--", alpha=0.55)
    ax.set_title("Waypoint Progress")
    ax.set_xlabel("Sim Time (s)")
    ax.set_ylabel("Waypoint Index")
    ax2.set_ylabel("Distance To Active WP (m)")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)


def _trace_note(task: str, terminated: bool) -> str:
    if task == TASK_TAKEOFF:
        return (
            "Per-step traces stop at the last pre-reset sample because CooperativeWorldBatchVecEnv "
            "auto-resets the world on terminal transitions."
        )
    if terminated:
        return (
            "Per-step traces stop at the last pre-reset sample because CooperativeWorldBatchVecEnv "
            "auto-resets the world on terminal transitions."
        )
    return "Trace stopped at max_world_steps before termination; use a higher limit for full-episode export."


def _save_plot(
    *,
    task: str,
    traces: list[list[dict[str, Any]]],
    slot_meta: list[dict[str, Any]],
    runway_beacon: dict[str, Any] | None,
    summary: dict[str, Any],
    output_path: str,
) -> None:
    if task == TASK_TAKEOFF:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
        _plot_ground_track(axes[0, 0], traces, slot_meta, runway_beacon, mark_liftoff=True)
        plot_scalar_trace(
            axes[0, 1],
            traces,
            slot_meta,
            value_key="altitude_agl_m",
            title="Altitude AGL",
            ylabel="Altitude AGL (m)",
            hlines=[(5.0, "liftoff", "#6b7280"), (120.0, "objective alt", "#9ca3af")],
        )
        plot_scalar_trace(
            axes[1, 0],
            traces,
            slot_meta,
            value_key="ground_speed_mps",
            title="Ground Speed",
            ylabel="Ground Speed (m/s)",
            hlines=[(35.0, "roll gate", "#6b7280"), (140.0, "objective speed", "#9ca3af")],
        )
        plot_clearance_trace(axes[1, 1], traces, slot_meta)
        axes[1, 1].legend(loc="best", fontsize=8)
    else:
        fig, axes = plt.subplots(3, 2, figsize=(16, 13), constrained_layout=True)
        _plot_ground_track(axes[0, 0], traces, slot_meta, runway_beacon, mark_liftoff=False)
        plot_scalar_trace(
            axes[0, 1],
            traces,
            slot_meta,
            value_key="altitude_agl_m",
            title="Altitude AGL",
            ylabel="Altitude AGL (m)",
            hlines=[(5.0, "liftoff", "#6b7280"), (120.0, "departure gate", "#9ca3af")],
        )
        plot_scalar_trace(
            axes[1, 0],
            traces,
            slot_meta,
            value_key="ground_speed_mps",
            title="Ground Speed",
            ylabel="Ground Speed (m/s)",
            hlines=[(35.0, "roll gate", "#6b7280"), (140.0, "climb speed", "#9ca3af")],
        )
        plot_clearance_trace(axes[1, 1], traces, slot_meta)
        _plot_waypoint_trace(axes[2, 0], traces, slot_meta)
        axes[2, 1].axis("off")

    meta_lines = [
        f"task={summary['task']} mode={summary['mode']} seed={summary['seed']} "
        f"curriculum_stage={summary['curriculum_stage']} world_success={summary['world_success']} "
        f"world_steps={summary['world_steps']}",
    ]
    for slot_summary in summary["slot_summaries"]:
        if task == TASK_TAKEOFF:
            meta_lines.append(
                f"{slot_summary['slot_name']}: term={slot_summary['termination_reason'] or 'n/a'} "
                f"release={slot_summary['first_release_step']} roll={slot_summary['first_roll_step']} "
                f"liftoff={slot_summary['first_liftoff_step']}"
            )
        else:
            meta_lines.append(
                f"{slot_summary['slot_name']}: term={slot_summary['termination_reason'] or 'n/a'} "
                f"release={slot_summary['first_release_step']} roll={slot_summary['first_roll_step']} "
                f"liftoff={slot_summary['first_liftoff_step']} wp1={slot_summary['first_waypoint_capture_step']} "
                f"final_wp={slot_summary['final_waypoint_index']}/{slot_summary['final_waypoint_count']}"
            )
    fig.suptitle(os.path.basename(str(summary["scenario"])), fontsize=13)
    fig.text(0.5, 0.01, "\n".join(meta_lines), ha="center", va="bottom", fontsize=8, family="monospace")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export one cooperative trajectory diagnostic episode.")
    parser.add_argument("--task", required=True, choices=[TASK_TAKEOFF, TASK_TAKEOFF_TO_CRUISE])
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--model", default=None, help="Path to SB3 model zip/path. Omit when using --scripted.")
    parser.add_argument("--algo", default="auto", help="auto / AdaptiveKLPPO / PPO")
    parser.add_argument("--scripted", action="store_true", help="Run the scripted residual-zero baseline.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--curriculum_stage", type=int, default=None)
    parser.add_argument("--max_world_steps", type=int, default=None)
    parser.add_argument("--output", required=True, help="PNG output path")
    args = parser.parse_args()

    if bool(args.scripted) == bool(args.model):
        raise ValueError("choose exactly one of --model or --scripted")

    task = str(args.task)
    if task == TASK_TAKEOFF:
        capture_slot_sample: Callable[..., dict[str, Any]] = _capture_takeoff_sample
        build_slot_summary = _build_takeoff_slot_summary
        allow_trace_cutoff = False
        prefer_reference_runway = True
    else:
        capture_slot_sample = _capture_takeoff_to_cruise_sample
        build_slot_summary = _build_takeoff_to_cruise_slot_summary
        allow_trace_cutoff = True
        prefer_reference_runway = False

    train_config = load_json_config(os.path.abspath(args.train_config))
    env_settings = make_env_settings(train_config)
    action_wrapper_kwargs = cooperative_action_wrapper_kwargs(train_config, scripted=bool(args.scripted))
    env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(args.scenario),
        n_envs=1,
        action_wrapper_kwargs=action_wrapper_kwargs,
        **env_settings,
    )
    curriculum = apply_curriculum_stage(env, train_config, args.curriculum_stage)
    model = None if args.scripted else load_policy_cpu(os.path.abspath(args.model), algo=str(args.algo))

    try:
        slot_meta, traces, final_infos, terminated = run_episode(
            env,
            model,
            scripted=bool(args.scripted),
            seed=int(args.seed),
            max_world_steps=args.max_world_steps,
            capture_slot_sample=capture_slot_sample,
            allow_trace_cutoff=allow_trace_cutoff,
        )
        first_slot = next((slot_state for slot_state in env._slots if slot_state is not None), None)
        runway_beacon = None
        if first_slot is not None and traces and traces[0]:
            first_sample = traces[0][0]
            runway_beacon = pick_runway_beacon(
                first_slot.loader,
                float(first_sample["x_m"]),
                float(first_sample["y_m"]),
                prefer_reference_runway=prefer_reference_runway,
            )

        slot_summaries = [
            build_slot_summary(slot_meta[idx], traces[idx], final_infos[idx])
            for idx in range(min(len(slot_meta), len(traces), len(final_infos)))
        ]
        world_success = bool(all(bool(slot_summary.get("success", False)) for slot_summary in slot_summaries))
        world_steps = max((int(slot_summary.get("episode_length", 0)) for slot_summary in slot_summaries), default=0)
        summary = {
            "task": task,
            "scenario": os.path.abspath(args.scenario),
            "train_config": os.path.abspath(args.train_config),
            "mode": "scripted" if args.scripted else "model",
            "seed": int(args.seed),
            "curriculum_stage": curriculum["stage_index"],
            "world_success": bool(world_success),
            "world_steps": int(world_steps),
            "trace_note": _trace_note(task, bool(terminated)),
            "slot_summaries": slot_summaries,
        }

        payload = {
            "summary": summary,
            "slot_meta": slot_meta,
            "curriculum_applied": curriculum,
            "traces": {
                str(slot_meta[idx]["slot_name"]): traces[idx]
                for idx in range(min(len(slot_meta), len(traces)))
            },
            "terminal_infos": to_jsonable(final_infos),
        }

        out_png = os.path.abspath(args.output)
        out_json = os.path.splitext(out_png)[0] + ".json"
        _save_plot(
            task=task,
            traces=traces,
            slot_meta=slot_meta,
            runway_beacon=runway_beacon,
            summary=summary,
            output_path=out_png,
        )
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=True)
            f.write("\n")

        print(f"saved_plot={out_png}")
        print(f"saved_summary={out_json}")
        print(json.dumps(summary, indent=2, ensure_ascii=True))
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
