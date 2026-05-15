#!/usr/bin/env python3
"""
Cooperative takeoff trajectory diagnostic for one cooperative world episode.

This script runs a real CooperativeWorldBatchVecEnv world and exports:
  - a PNG with both aircraft ground tracks plus key takeoff telemetry
  - a JSON payload with per-step traces and compact per-slot summaries

Use cases:
  - Verify that interval-takeoff clearance semantics actually propagate
  - Inspect whether the wingman remains hold-short, starts the roll too late,
    drifts off the runway, or never climbs into the departure profile
  - Compare a trained shared-execution policy against the scripted residual-zero
    baseline on the exact same cooperative scenario
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.env_config import resolve_env_settings
from python.rl.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec


CLEARANCE_LABELS = {
    0: "Unknown",
    1: "HoldShort",
    2: "Lineup",
    3: "Cleared",
    4: "Rolling",
    5: "Airborne",
}

SLOT_COLORS = ["#2563eb", "#d97706", "#16a34a", "#dc2626"]


@dataclass(frozen=True)
class SlotEpisodeSummary:
    slot_index: int
    slot_name: str
    entity_name: str
    formation_role_id: str
    reference_entity_name: str | None
    policy_route: str | None
    success: bool
    termination_reason: str
    episode_reward: float
    episode_length: int
    trace_sample_count: int
    first_release_step: int | None
    first_roll_step: int | None
    first_liftoff_step: int | None
    max_altitude_agl_m: float
    max_ground_speed_mps: float
    final_pre_reset_position_xyz_m: list[float]
    final_pre_reset_heading_deg: float | None
    final_pre_reset_runway_along_m: float | None
    final_pre_reset_runway_cross_m: float | None
    terminal_runway_along_m: float | None
    terminal_runway_cross_m: float | None
    clearance_segments: list[dict[str, Any]]


@dataclass(frozen=True)
class WorldEpisodeSummary:
    scenario: str
    train_config: str
    mode: str
    seed: int
    curriculum_stage: int | None
    world_success: bool
    world_steps: int
    trace_note: str
    slot_summaries: list[SlotEpisodeSummary]


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


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


def _make_env_settings(train_config: dict[str, Any]) -> dict[str, Any]:
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None
        execution_step_runtime_mode = None
        step_info_mode = None
        flight_shaping_backend = None

    return resolve_env_settings(train_config, _Args())


def _cooperative_action_wrapper_kwargs(
    train_config: dict[str, Any],
    *,
    scripted: bool,
) -> dict[str, Any] | None:
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_class is not MultiTimescaleActionWrapper:
        return None
    kwargs = dict(wrapper_kwargs or {})
    if scripted:
        kwargs["scripted_residual_scale"] = 0.0
        kwargs["scripted_residual_alt_breakpoints_m"] = []
        kwargs["scripted_residual_alt_scales"] = []
        kwargs["action_rate_penalty_coef"] = 0.0
    return kwargs


def _apply_curriculum_stage(
    env: CooperativeWorldBatchVecEnv,
    train_config: dict[str, Any],
    stage_index: int | None,
) -> dict[str, Any]:
    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    stages = list(curriculum_cfg.get("stages", []) or [])
    if not stages:
        env.set_randomization_overrides(None)
        env.set_leader_overrides(None)
        return {"stage_index": None, "randomization": {}, "leader_overrides": {}}

    idx = len(stages) - 1 if stage_index is None else max(0, min(len(stages) - 1, int(stage_index)))
    stage = dict(stages[idx] or {})
    overrides = stage.get("randomization_overrides", stage.get("randomization", {}))
    leader_overrides = stage.get("leader_env_overrides", {})
    env.set_randomization_overrides(dict(overrides or {}))
    env.set_leader_overrides(dict(leader_overrides or {}))
    return {
        "stage_index": int(idx),
        "randomization": dict(overrides or {}),
        "leader_overrides": dict(leader_overrides or {}),
    }


def _format_slot_name(slot_index: int, control_slot: Any) -> str:
    role = str(getattr(control_slot, "formation_role_id", "") or "").strip()
    entity_name = str(getattr(control_slot, "entity_name", "") or "").strip()
    if role:
        return f"{role}:{entity_name}" if entity_name else role
    if entity_name:
        return entity_name
    return f"slot{int(slot_index)}"


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
        for beacon in beacons:
            if str(beacon.get("name", "")).strip() == ref_name:
                return dict(beacon)
    best = None
    best_d2 = float("inf")
    for beacon in beacons:
        dx = float(x_ref) - float(beacon.get("cx", 0.0))
        dy = float(y_ref) - float(beacon.get("cy", 0.0))
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best = beacon
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


def _array_head(values: Any, *, limit: int = 4) -> list[float] | None:
    if values is None:
        return None
    try:
        arr = np.asarray(values, dtype=np.float32).reshape(-1)
    except Exception:
        return None
    if arr.size == 0:
        return None
    return [float(v) for v in arr[: max(1, int(limit))]]


def _mission_status_list(info: dict[str, Any] | None) -> list[float]:
    if not isinstance(info, dict):
        return []
    ms = info.get("mission_status", None)
    if ms is None:
        return []
    try:
        return np.asarray(ms, dtype=np.float32).reshape(-1).tolist()
    except Exception:
        return []


def _success_from_mission_status(mission_status: list[float]) -> bool:
    return bool(len(mission_status) >= 4 and float(mission_status[3]) > 0.5)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return _to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _runway_frame(loader, x_m: float, y_m: float) -> tuple[float | None, float | None, float | None, float | None]:
    try:
        valid, along_m, cross_m, rw_len_m, rw_wid_m = loader.get_runway_local_frame(float(x_m), float(y_m))
    except Exception:
        return None, None, None, None
    if not bool(valid):
        return None, None, None, None
    return float(along_m), float(cross_m), float(rw_len_m), float(rw_wid_m)


def _capture_slot_sample(
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

    mission_status = _mission_status_list(info)
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
        "success_flag": bool(_success_from_mission_status(mission_status)),
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
        "effective_action_head": None if not isinstance(info, dict) else _array_head(info.get("effective_action", None)),
        "baseline_action_head": None if not isinstance(info, dict) else _array_head(info.get("baseline_action", None)),
    }


def _clearance_segments(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not samples:
        return []
    out: list[dict[str, Any]] = []
    start_step = int(samples[0]["step"])
    current_code = int(samples[0].get("takeoff_clearance_code", 0) or 0)
    last_step = start_step
    for sample in samples[1:]:
        code = int(sample.get("takeoff_clearance_code", 0) or 0)
        step = int(sample["step"])
        if code != current_code:
            out.append(
                {
                    "from_step": int(start_step),
                    "to_step": int(last_step),
                    "code": int(current_code),
                    "label": CLEARANCE_LABELS.get(int(current_code), f"Code{int(current_code)}"),
                }
            )
            current_code = code
            start_step = step
        last_step = step
    out.append(
        {
            "from_step": int(start_step),
            "to_step": int(last_step),
            "code": int(current_code),
            "label": CLEARANCE_LABELS.get(int(current_code), f"Code{int(current_code)}"),
        }
    )
    return out


def _first_step(samples: list[dict[str, Any]], predicate) -> int | None:
    for sample in samples:
        try:
            if predicate(sample):
                return int(sample["step"])
        except Exception:
            continue
    return None


def _build_slot_summary(slot_meta: dict[str, Any], samples: list[dict[str, Any]], final_info: dict[str, Any]) -> SlotEpisodeSummary:
    final_sample = samples[-1]
    mission_status = _mission_status_list(final_info)
    termination_reason = str(final_info.get("termination_reason", "") or "")
    episode = final_info.get("episode", {}) if isinstance(final_info.get("episode", {}), dict) else {}
    episode_reward = float(episode.get("r", 0.0))
    episode_length = int(episode.get("l", 0))
    max_altitude_agl_m = float(
        np.nanmax(np.asarray([sample["altitude_agl_m"] for sample in samples], dtype=np.float64))
    )
    max_ground_speed_mps = float(
        np.nanmax(np.asarray([sample["ground_speed_mps"] for sample in samples], dtype=np.float64))
    )
    return SlotEpisodeSummary(
        slot_index=int(slot_meta["slot_index"]),
        slot_name=str(slot_meta["slot_name"]),
        entity_name=str(slot_meta["entity_name"]),
        formation_role_id=str(slot_meta["formation_role_id"] or ""),
        reference_entity_name=slot_meta["reference_entity_name"],
        policy_route=slot_meta["policy_route"],
        success=bool(_success_from_mission_status(mission_status)),
        termination_reason=termination_reason,
        episode_reward=float(episode_reward),
        episode_length=int(episode_length),
        trace_sample_count=int(len(samples)),
        first_release_step=_first_step(samples, lambda sample: int(sample.get("takeoff_clearance_code", 0) or 0) >= 3),
        first_roll_step=_first_step(samples, lambda sample: float(sample.get("ground_speed_mps", 0.0) or 0.0) >= 5.0),
        first_liftoff_step=_first_step(samples, lambda sample: float(sample.get("altitude_agl_m", 0.0) or 0.0) >= 5.0),
        max_altitude_agl_m=float(max_altitude_agl_m),
        max_ground_speed_mps=float(max_ground_speed_mps),
        final_pre_reset_position_xyz_m=[
            float(final_sample["x_m"]),
            float(final_sample["y_m"]),
            float(final_sample["z_m"]),
        ],
        final_pre_reset_heading_deg=None
        if final_sample["heading_deg"] is None
        else float(final_sample["heading_deg"]),
        final_pre_reset_runway_along_m=None
        if final_sample["runway_along_m"] is None
        else float(final_sample["runway_along_m"]),
        final_pre_reset_runway_cross_m=None
        if final_sample["runway_cross_m"] is None
        else float(final_sample["runway_cross_m"]),
        terminal_runway_along_m=None
        if final_info.get("runway_along_m", None) is None
        else float(final_info["runway_along_m"]),
        terminal_runway_cross_m=None
        if final_info.get("runway_cross_m", None) is None
        else float(final_info["runway_cross_m"]),
        clearance_segments=_clearance_segments(samples),
    )


def _run_episode(
    env: CooperativeWorldBatchVecEnv,
    model,
    *,
    scripted: bool,
    seed: int,
    max_world_steps: int | None,
) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]], list[dict[str, Any]]]:
    env.seed(int(seed))
    obs = env.reset()
    slot_control = env.slot_control_slots()
    slot_meta = [
        {
            "slot_index": int(idx),
            "slot_name": _format_slot_name(idx, slot),
            "entity_name": str(getattr(slot, "entity_name", "") or ""),
            "formation_role_id": str(getattr(slot, "formation_role_id", "") or ""),
            "reference_entity_name": getattr(slot, "reference_entity_name", None),
            "policy_route": None if getattr(slot, "policy_route", None) is None else str(getattr(slot, "policy_route")),
        }
        for idx, slot in enumerate(slot_control)
    ]
    traces: list[list[dict[str, Any]]] = [[] for _ in slot_meta]

    for slot_index, slot_state in enumerate(env._slots):
        if slot_state is None:
            continue
        traces[slot_index].append(
            _capture_slot_sample(
                slot_state,
                step_index=0,
                sim_time_s=0.0,
                reward=None,
                info=None,
            )
        )

    limit = int(max_world_steps) if max_world_steps is not None else 0
    if limit <= 0:
        limit = int(max((getattr(slot, "max_steps", 0) for slot in env._slots if slot is not None), default=0))
    if limit <= 0:
        limit = 100000

    final_infos: list[dict[str, Any]] | None = None
    for step_index in range(1, limit + 1):
        if scripted:
            action = np.zeros((env.num_envs, env.action_space.shape[0]), dtype=np.float32)
        else:
            action, _ = model.predict(obs, deterministic=True)
        obs, rewards, dones, infos = env.step(action)
        world_done = bool(np.any(dones))
        if not world_done:
            for slot_index, slot_state in enumerate(env._slots):
                if slot_state is None:
                    continue
                sim_time_s = float(getattr(slot_state.last_truth, "sim_time", step_index * 0.05))
                traces[slot_index].append(
                    _capture_slot_sample(
                        slot_state,
                        step_index=step_index,
                        sim_time_s=sim_time_s,
                        reward=float(rewards[slot_index]),
                        info=infos[slot_index] if slot_index < len(infos) else None,
                    )
                )
        else:
            final_infos = [dict(info) for info in infos]
            break

    if final_infos is None:
        raise RuntimeError(f"cooperative trajectory diagnostic failed to terminate within {limit} steps")

    return slot_meta, traces, final_infos


def _plot_ground_track(ax, traces: list[list[dict[str, Any]]], slot_meta: list[dict[str, Any]], runway_beacon: dict[str, Any] | None) -> None:
    for slot_index, samples in enumerate(traces):
        color = SLOT_COLORS[slot_index % len(SLOT_COLORS)]
        x = np.asarray([sample["x_m"] for sample in samples], dtype=np.float64)
        y = np.asarray([sample["y_m"] for sample in samples], dtype=np.float64)
        label = str(slot_meta[slot_index]["slot_name"])
        ax.plot(x, y, color=color, linewidth=1.8, label=label)
        ax.scatter([x[0]], [y[0]], s=30, marker="o", color=color, edgecolors="black", linewidths=0.5, zorder=5)
        ax.scatter([x[-1]], [y[-1]], s=42, marker="X", color=color, edgecolors="black", linewidths=0.5, zorder=5)
        liftoff_step = _first_step(samples, lambda sample: float(sample.get("altitude_agl_m", 0.0) or 0.0) >= 5.0)
        if liftoff_step is not None:
            idx = min(len(samples) - 1, int(liftoff_step))
            ax.scatter([x[idx]], [y[idx]], s=48, marker="^", color=color, edgecolors="black", linewidths=0.5, zorder=6)

    if isinstance(runway_beacon, dict):
        outline = _runway_outline(runway_beacon)
        ax.plot(outline[:, 0], outline[:, 1], color="#111827", linewidth=1.2, alpha=0.95, zorder=2)
        cx = float(runway_beacon.get("cx", 0.0))
        cy = float(runway_beacon.get("cy", 0.0))
        heading = math.radians(float(runway_beacon.get("heading", 0.0)))
        fwd_x = math.sin(heading)
        fwd_y = math.cos(heading)
        hl = 0.5 * float(runway_beacon.get("length", 0.0))
        ax.plot(
            [cx - hl * fwd_x, cx + hl * fwd_x],
            [cy - hl * fwd_y, cy + hl * fwd_y],
            color="#111827",
            linewidth=0.9,
            linestyle=":",
            alpha=0.8,
            zorder=2,
        )
    ax.set_title("Ground Track")
    ax.set_aspect("equal")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)
    ax.set_xlabel("East x (m)")
    ax.set_ylabel("North y (m)")
    ax.legend(loc="best", fontsize=8)


def _plot_scalar_trace(
    ax,
    traces: list[list[dict[str, Any]]],
    slot_meta: list[dict[str, Any]],
    *,
    value_key: str,
    title: str,
    ylabel: str,
    hlines: list[tuple[float, str, str]] | None = None,
) -> None:
    for slot_index, samples in enumerate(traces):
        color = SLOT_COLORS[slot_index % len(SLOT_COLORS)]
        t = np.asarray([sample["sim_time_s"] for sample in samples], dtype=np.float64)
        y = np.asarray([sample[value_key] for sample in samples], dtype=np.float64)
        ax.plot(t, y, color=color, linewidth=1.8, label=str(slot_meta[slot_index]["slot_name"]))
    if hlines:
        for value, label, color in hlines:
            ax.axhline(float(value), color=color, linestyle="--", linewidth=1.0, alpha=0.7)
            ax.text(ax.get_xlim()[1] if ax.get_xlim()[1] > 0.0 else 0.0, float(value), label, color=color, fontsize=7)
    ax.set_title(title)
    ax.set_xlabel("Sim Time (s)")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)


def _plot_clearance_trace(ax, traces: list[list[dict[str, Any]]], slot_meta: list[dict[str, Any]]) -> None:
    for slot_index, samples in enumerate(traces):
        color = SLOT_COLORS[slot_index % len(SLOT_COLORS)]
        t = np.asarray([sample["sim_time_s"] for sample in samples], dtype=np.float64)
        y = np.asarray([sample["takeoff_clearance_code"] for sample in samples], dtype=np.float64)
        ax.step(t, y, where="post", color=color, linewidth=1.8, label=str(slot_meta[slot_index]["slot_name"]))
    ticks = sorted(CLEARANCE_LABELS)
    ax.set_yticks(ticks)
    ax.set_yticklabels([CLEARANCE_LABELS[tick] for tick in ticks], fontsize=8)
    ax.set_title("Takeoff Clearance Timeline")
    ax.set_xlabel("Sim Time (s)")
    ax.set_ylabel("Clearance")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)


def _save_plot(
    *,
    traces: list[list[dict[str, Any]]],
    slot_meta: list[dict[str, Any]],
    runway_beacon: dict[str, Any] | None,
    summary: WorldEpisodeSummary,
    output_path: str,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    _plot_ground_track(axes[0, 0], traces, slot_meta, runway_beacon)
    _plot_scalar_trace(
        axes[0, 1],
        traces,
        slot_meta,
        value_key="altitude_agl_m",
        title="Altitude AGL",
        ylabel="Altitude AGL (m)",
        hlines=[(5.0, "liftoff", "#6b7280"), (120.0, "objective alt", "#9ca3af")],
    )
    _plot_scalar_trace(
        axes[1, 0],
        traces,
        slot_meta,
        value_key="ground_speed_mps",
        title="Ground Speed",
        ylabel="Ground Speed (m/s)",
        hlines=[(35.0, "roll gate", "#6b7280"), (140.0, "objective speed", "#9ca3af")],
    )
    _plot_clearance_trace(axes[1, 1], traces, slot_meta)
    axes[1, 1].legend(loc="best", fontsize=8)

    meta_lines = [
        f"mode={summary.mode} seed={summary.seed} curriculum_stage={summary.curriculum_stage} "
        f"world_success={summary.world_success} world_steps={summary.world_steps}",
    ]
    for slot_summary in summary.slot_summaries:
        meta_lines.append(
            f"{slot_summary.slot_name}: term={slot_summary.termination_reason or 'n/a'} "
            f"release={slot_summary.first_release_step} roll={slot_summary.first_roll_step} "
            f"liftoff={slot_summary.first_liftoff_step}"
        )
    fig.suptitle(os.path.basename(str(summary.scenario)), fontsize=13)
    fig.text(0.5, 0.01, "\n".join(meta_lines), ha="center", va="bottom", fontsize=8, family="monospace")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export one cooperative takeoff trajectory diagnostic episode.")
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

    train_config = _load_json(os.path.abspath(args.train_config))
    env_settings = _make_env_settings(train_config)
    action_wrapper_kwargs = _cooperative_action_wrapper_kwargs(train_config, scripted=bool(args.scripted))
    env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(args.scenario),
        n_envs=1,
        action_wrapper_kwargs=action_wrapper_kwargs,
        **env_settings,
    )
    curriculum = _apply_curriculum_stage(env, train_config, args.curriculum_stage)
    model = None if args.scripted else _load_policy(os.path.abspath(args.model), algo=str(args.algo))

    try:
        slot_meta, traces, final_infos = _run_episode(
            env,
            model,
            scripted=bool(args.scripted),
            seed=int(args.seed),
            max_world_steps=args.max_world_steps,
        )
        first_slot = next((slot_state for slot_state in env._slots if slot_state is not None), None)
        runway_beacon = None
        if first_slot is not None and traces and traces[0]:
            first_sample = traces[0][0]
            runway_beacon = _pick_runway_beacon(first_slot.loader, float(first_sample["x_m"]), float(first_sample["y_m"]))

        slot_summaries = [
            _build_slot_summary(slot_meta[idx], traces[idx], final_infos[idx])
            for idx in range(min(len(slot_meta), len(traces), len(final_infos)))
        ]
        world_success = bool(all(summary.success for summary in slot_summaries))
        world_steps = max((int(summary.episode_length) for summary in slot_summaries), default=0)
        summary = WorldEpisodeSummary(
            scenario=os.path.abspath(args.scenario),
            train_config=os.path.abspath(args.train_config),
            mode="scripted" if args.scripted else "model",
            seed=int(args.seed),
            curriculum_stage=curriculum["stage_index"],
            world_success=bool(world_success),
            world_steps=int(world_steps),
            trace_note=(
                "Per-step traces stop at the last pre-reset sample because CooperativeWorldBatchVecEnv "
                "auto-resets the world on terminal transitions."
            ),
            slot_summaries=slot_summaries,
        )

        payload = {
            "summary": asdict(summary),
            "slot_meta": slot_meta,
            "curriculum_applied": curriculum,
            "traces": {
                str(slot_meta[idx]["slot_name"]): traces[idx]
                for idx in range(min(len(slot_meta), len(traces)))
            },
            "terminal_infos": _to_jsonable(final_infos),
        }

        out_png = os.path.abspath(args.output)
        out_json = os.path.splitext(out_png)[0] + ".json"
        _save_plot(
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
        print(
            json.dumps(
                {
                    "mode": summary.mode,
                    "seed": summary.seed,
                    "curriculum_stage": summary.curriculum_stage,
                    "world_success": summary.world_success,
                    "world_steps": summary.world_steps,
                    "slot_summaries": [asdict(slot_summary) for slot_summary in slot_summaries],
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
