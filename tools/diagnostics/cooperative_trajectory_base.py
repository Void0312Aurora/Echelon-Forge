from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Callable

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.env_config import resolve_env_settings
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec


CLEARANCE_LABELS = {
    0: "Unknown",
    1: "HoldShort",
    2: "Lineup",
    3: "Cleared",
    4: "Rolling",
    5: "Airborne",
}

SLOT_COLORS = ["#2563eb", "#d97706", "#16a34a", "#dc2626"]


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def load_policy_cpu(model_path: str, algo: str):
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


def make_env_settings(train_config: dict[str, Any]) -> dict[str, Any]:
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


def cooperative_action_wrapper_kwargs(train_config: dict[str, Any], *, scripted: bool) -> dict[str, Any] | None:
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


def apply_curriculum_stage(
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


def format_slot_name(slot_index: int, control_slot: Any) -> str:
    role = str(getattr(control_slot, "formation_role_id", "") or "").strip()
    entity_name = str(getattr(control_slot, "entity_name", "") or "").strip()
    if role:
        return f"{role}:{entity_name}" if entity_name else role
    if entity_name:
        return entity_name
    return f"slot{int(slot_index)}"


def pick_runway_beacon(
    loader,
    x_ref: float,
    y_ref: float,
    *,
    prefer_reference_runway: bool,
) -> dict[str, Any] | None:
    ref_name = None
    if prefer_reference_runway:
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


def runway_outline(beacon: dict[str, Any]) -> np.ndarray:
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


def array_head(values: Any, *, limit: int = 4) -> list[float] | None:
    if values is None:
        return None
    try:
        arr = np.asarray(values, dtype=np.float32).reshape(-1)
    except Exception:
        return None
    if arr.size == 0:
        return None
    return [float(v) for v in arr[: max(1, int(limit))]]


def mission_status_list(info: dict[str, Any] | None) -> list[float]:
    if not isinstance(info, dict):
        return []
    ms = info.get("mission_status", None)
    if ms is None:
        return []
    try:
        return np.asarray(ms, dtype=np.float32).reshape(-1).tolist()
    except Exception:
        return []


def success_from_mission_status(mission_status: list[float]) -> bool:
    return bool(len(mission_status) >= 4 and float(mission_status[3]) > 0.5)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def clearance_segments(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def first_step(samples: list[dict[str, Any]], predicate) -> int | None:
    for sample in samples:
        try:
            if predicate(sample):
                return int(sample["step"])
        except Exception:
            continue
    return None


def run_episode(
    env: CooperativeWorldBatchVecEnv,
    model,
    *,
    scripted: bool,
    seed: int,
    max_world_steps: int | None,
    capture_slot_sample: Callable[..., dict[str, Any]],
    allow_trace_cutoff: bool,
) -> tuple[list[dict[str, Any]], list[list[dict[str, Any]]], list[dict[str, Any]], bool]:
    env.seed(int(seed))
    obs = env.reset()
    slot_control = env.slot_control_slots()
    slot_meta = [
        {
            "slot_index": int(idx),
            "slot_name": format_slot_name(idx, slot),
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
            capture_slot_sample(
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
    terminated = False
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
                    capture_slot_sample(
                        slot_state,
                        step_index=step_index,
                        sim_time_s=sim_time_s,
                        reward=float(rewards[slot_index]),
                        info=infos[slot_index] if slot_index < len(infos) else None,
                    )
                )
        else:
            final_infos = [dict(info) for info in infos]
            terminated = True
            break

    if final_infos is None:
        if not allow_trace_cutoff:
            raise RuntimeError(f"cooperative trajectory diagnostic failed to terminate within {limit} steps")
        final_infos = []
        for slot_state in env._slots:
            if slot_state is None:
                final_infos.append({})
                continue
            final_infos.append(
                {
                    "termination_reason": "trace_cutoff",
                    "episode": {
                        "r": float(slot_state.episode_return),
                        "l": int(slot_state.episode_length),
                    },
                    "mission_status": (
                        np.asarray(slot_state.loader.mission_status(), dtype=np.float32).reshape(-1).tolist()
                        if hasattr(slot_state.loader, "mission_status")
                        else []
                    ),
                    "world_done": False,
                    "shared_world_reset": False,
                    "TimeLimit.truncated": False,
                }
            )

    return slot_meta, traces, final_infos, bool(terminated)


def plot_scalar_trace(
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


def plot_clearance_trace(ax, traces: list[list[dict[str, Any]]], slot_meta: list[dict[str, Any]]) -> None:
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
