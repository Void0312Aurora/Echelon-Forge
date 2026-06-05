#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv
from gym_envs.scenario_loader.reward_runtime.air_combat import (
    air_combat_c2_roe_state_from_mapping,
    classify_air_combat_c2_roe_event,
)
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage0_drone_weapon_employment_v1.json",
)
DEFAULT_TRAIN_CONFIG = resolve_repo_path(
    "examples",
    "config",
    "training",
    "active",
    "air_combat",
    "air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json",
)


FULL_ACTION_COLUMNS = {
    "pitch": 0,
    "roll": 1,
    "rudder": 2,
    "throttle": 3,
    "tms_up": 12,
    "radar_active": 9,
    "master_arm": 13,
    "fire_weapon": 14,
    "fire_gun": 15,
    "weapon_select": 16,
}
HYBRID_ACTION_COLUMNS = {
    "pitch": 0,
    "roll": 1,
    "rudder": 2,
    "throttle": 3,
    "radar_active": 6,
    "tms_up": 7,
    "master_arm": 8,
    "fire_weapon": 9,
    "fire_gun": 10,
    "weapon_select": 11,
}
ACTION_SIGNAL_NAMES = tuple(FULL_ACTION_COLUMNS.keys())
HYBRID_BINARY_POLICY_SIGNAL_NAMES = (
    "radar_active",
    "tms_up",
    "master_arm",
    "fire_weapon",
    "fire_gun",
)
A5_FIRE_MASK_COMPONENT_NAMES = (
    "fire_mask_c2_authorized",
    "fire_mask_target_present",
    "fire_mask_shot_budget_available",
    "fire_mask_not_pending_assessment",
    "fire_mask_weapon_ready",
    "fire_mask_ammo_available",
    "fire_mask_reattack_allowed",
)


def _action_columns_for_mode(action_mode: str) -> dict[str, int]:
    mode = str(action_mode)
    if mode == "air_combat_hybrid_v1":
        return HYBRID_ACTION_COLUMNS
    return FULL_ACTION_COLUMNS


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _bool_int(value: Any) -> int:
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes", "on"})
    return int(bool(value))


def _stable_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        return ""


def _a7_launch_window_config_from_train_config(train_config: dict[str, Any] | None) -> dict[str, float]:
    hyper = train_config.get("hyperparameters", {}) if isinstance(train_config, dict) else {}
    if not isinstance(hyper, dict):
        hyper = {}
    return {
        "min_range_m": _finite_float(hyper.get("a6_first_event_launch_window_min_range_m", 0.0), 0.0),
        "max_range_m": _finite_float(hyper.get("a6_first_event_launch_window_max_range_m", 0.0), 0.0),
        "max_track_age_s": _finite_float(
            hyper.get("a6_first_event_launch_window_max_track_age_s", float("inf")),
            float("inf"),
        ),
        "min_window_age_steps": _finite_float(
            hyper.get("a6_first_event_launch_window_min_window_age_steps", 1),
            1.0,
        ),
    }


def _unit_id_set(sim) -> set[int]:
    out: set[int] = set()
    try:
        for unit in sim.get_all_units():
            out.add(int(getattr(unit, "id", 0)))
    except Exception:
        pass
    return out


def _target_track(truth, target_id: int):
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


def _distance_m(sim, blue_id: int, target_id: int) -> float:
    try:
        bx, by, bz = sim.get_unit_position(int(blue_id))
        tx, ty, tz = sim.get_unit_position(int(target_id))
        dx = float(tx) - float(bx)
        dy = float(ty) - float(by)
        dz = float(tz) - float(bz)
        return float(math.sqrt(dx * dx + dy * dy + dz * dz))
    except Exception:
        return float("nan")


def _health_current(sim, entity_id: int) -> float:
    try:
        health = sim.get_unit_health(int(entity_id))
        if health:
            return _finite_float(health[0])
    except Exception:
        pass
    return float("nan")


def _weapon_select_id(action: np.ndarray, *, action_mode: str) -> int:
    columns = _action_columns_for_mode(action_mode)
    weapon_select_idx = int(columns["weapon_select"])
    if action.size <= weapon_select_idx:
        return 0
    if str(action_mode) == "air_combat_hybrid_v1":
        return int(np.clip(round(float(action[weapon_select_idx])), 0, 7))
    return int(np.clip(float(action[weapon_select_idx]), 0.0, 1.0) * 7.0)


def _mission_command_dict(loader) -> dict[str, Any]:
    mission_cmd = getattr(loader, "mission_cmd", None)
    return mission_cmd if isinstance(mission_cmd, dict) else {}


def _c2_roe_event_columns(
    state: dict[str, Any],
    *,
    release_delta: int,
    fire_attempted: bool,
    previous_release_count: int,
) -> dict[str, Any]:
    release_delta = max(0, int(release_delta or 0))
    classifications = []
    if release_delta > 0:
        for release_ordinal in range(release_delta):
            classifications.append(
                classify_air_combat_c2_roe_event(
                    state,
                    released=True,
                    fire_attempted=bool(fire_attempted),
                    previous_release_count=int(previous_release_count or 0),
                    release_ordinal=int(release_ordinal),
                )
            )
    else:
        classifications.append(
            classify_air_combat_c2_roe_event(
                state,
                released=False,
                fire_attempted=bool(fire_attempted),
                previous_release_count=int(previous_release_count or 0),
            )
        )

    def count_flag(flag_name: str) -> int:
        return int(sum(1 for item in classifications if bool(item.get(flag_name, False))))

    violation_release_count = count_flag("violation_release")
    bucket = str(classifications[0].get("bucket", "no_fire")) if classifications else "no_fire"
    return {
        "c2_roe_release_bucket": bucket,
        "c2_roe_hold_fire": int(any(bool(item.get("hold_fire", False)) for item in classifications)),
        "c2_roe_hold_fire_obeyed": count_flag("hold_fire_obeyed"),
        "c2_roe_hold_fire_violation": count_flag("hold_fire_violation"),
        "c2_roe_unauthorized_shot": count_flag("unauthorized_shot"),
        "c2_roe_unauthorized_release_count": int(
            sum(1 for item in classifications if bool(item.get("released", False)) and bool(item.get("unauthorized_shot", False)))
        ),
        "c2_roe_authorized_release_count": count_flag("authorized_release"),
        "c2_roe_valid_authorized_release_count": count_flag("valid_authorized_release"),
        "c2_roe_violation_release_count": int(violation_release_count),
        "c2_roe_pending_assessment_violation": count_flag("pending_assessment_violation"),
        "c2_roe_pending_assessment_release_count": int(
            sum(
                1
                for item in classifications
                if bool(item.get("released", False)) and bool(item.get("pending_assessment_violation", False))
            )
        ),
        "c2_roe_premature_second_shot": count_flag("premature_second_shot"),
        "c2_roe_shot_budget_violation": count_flag("shot_budget_violation"),
        "c2_roe_authorized_salvo_release_count": count_flag("authorized_salvo"),
        "c2_roe_authorized_reattack_release_count": count_flag("authorized_reattack"),
        "c2_roe_legacy_fallback_release_count": count_flag("legacy_roe_fallback"),
    }


def _a5_event_info_columns(info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    has_a5_field = any(
        key in info
        for key in (
            "engagement_state",
            "fire_mask",
            "event_action_mask",
            "fire_once_requested",
            "fire_once_accepted",
            "fire_once_rejected_reason",
            "release_executed",
            "post_launch_suppressed",
            "reattack_ready",
            "fire_mask_components",
        )
    )
    if not has_a5_field:
        return {}

    out: dict[str, Any] = {
        "engagement_state": str(info.get("engagement_state", "") or ""),
        "fire_mask": int(_bool_int(info.get("fire_mask", 0))),
        "fire_once_requested": int(_bool_int(info.get("fire_once_requested", False))),
        "fire_once_accepted": int(_bool_int(info.get("fire_once_accepted", False))),
        "fire_once_rejected_reason": str(info.get("fire_once_rejected_reason", "") or ""),
        "release_executed": int(_bool_int(info.get("release_executed", False))),
        "post_launch_suppressed": int(_bool_int(info.get("post_launch_suppressed", False))),
        "reattack_ready": int(_bool_int(info.get("reattack_ready", False))),
    }
    out["fire_once_rejected"] = int(out["fire_once_requested"] > 0 and out["fire_once_accepted"] <= 0)

    event_mask = info.get("event_action_mask", None)
    if isinstance(event_mask, np.ndarray):
        event_mask_list = event_mask.reshape(-1).tolist()
    elif isinstance(event_mask, (list, tuple)):
        event_mask_list = list(event_mask)
    else:
        event_mask_list = []
    if event_mask_list:
        mask_values = [int(_bool_int(value)) for value in event_mask_list]
        out["event_action_mask_json"] = _stable_json(mask_values)
        out["event_action_mask_hold"] = int(mask_values[0]) if len(mask_values) >= 1 else 1
        out["event_action_mask_fire_once"] = int(mask_values[1]) if len(mask_values) >= 2 else out["fire_mask"]
    else:
        out["event_action_mask_json"] = _stable_json([1, int(out["fire_mask"])])
        out["event_action_mask_hold"] = 1
        out["event_action_mask_fire_once"] = int(out["fire_mask"])

    components = info.get("fire_mask_components", {})
    component_map = components if isinstance(components, dict) else {}
    stable_components = {str(key): int(_bool_int(value)) for key, value in sorted(component_map.items())}
    out["fire_mask_components_json"] = _stable_json(stable_components)
    for name in A5_FIRE_MASK_COMPONENT_NAMES:
        if name in stable_components:
            out[name] = int(stable_components[name])
    return out


def _base_action(action_mode: str) -> np.ndarray:
    columns = _action_columns_for_mode(action_mode)
    action_dim = 12 if str(action_mode) == "air_combat_hybrid_v1" else 17
    action = np.zeros((action_dim,), dtype=np.float32)
    action[columns["pitch"]] = 0.02
    action[columns["throttle"]] = 0.65
    if str(action_mode) == "air_combat_hybrid_v1":
        action[columns["weapon_select"]] = 1.0
    else:
        action[columns["weapon_select"]] = 1.0 / 7.0
    return action


def _forced_fire_action(_obs: dict[str, Any], _rng: np.random.Generator, _step: int, *, action_mode: str) -> np.ndarray:
    columns = _action_columns_for_mode(action_mode)
    action = _base_action(action_mode)
    action[columns["radar_active"]] = 1.0
    action[columns["tms_up"]] = 1.0
    action[columns["master_arm"]] = 1.0
    action[columns["fire_weapon"]] = 1.0
    return action


def _range_gate_fire_action(*, fire: bool, action_mode: str) -> np.ndarray:
    columns = _action_columns_for_mode(action_mode)
    action = _base_action(action_mode)
    action[columns["radar_active"]] = 1.0
    action[columns["tms_up"]] = 1.0
    action[columns["master_arm"]] = 1.0
    action[columns["fire_weapon"]] = 1.0 if bool(fire) else 0.0
    return action


def _switch_explore_action(_obs: dict[str, Any], rng: np.random.Generator, _step: int, *, action_mode: str) -> np.ndarray:
    columns = _action_columns_for_mode(action_mode)
    action = _base_action(action_mode)
    action[columns["pitch"]] = float(np.clip(rng.normal(0.02, 0.04), -0.15, 0.18))
    action[columns["roll"]] = float(np.clip(rng.normal(0.0, 0.05), -0.18, 0.18))
    action[columns["rudder"]] = float(np.clip(rng.normal(0.0, 0.03), -0.12, 0.12))
    action[columns["throttle"]] = float(np.clip(rng.normal(0.65, 0.08), 0.45, 0.85))
    action[columns["radar_active"]] = float(rng.random() < 0.75)
    action[columns["tms_up"]] = float(rng.random() < 0.35)
    action[columns["master_arm"]] = float(rng.random() < 0.45)
    action[columns["fire_weapon"]] = float(rng.random() < 0.35)
    if str(action_mode) == "air_combat_hybrid_v1":
        action[columns["weapon_select"]] = float(rng.integers(0, 8))
    else:
        action[columns["weapon_select"]] = float(rng.random())
    return action


def _uniform_action(env, _obs: dict[str, Any], rng: np.random.Generator, _step: int) -> np.ndarray:
    low = np.asarray(env.action_space.low, dtype=np.float32)
    high = np.asarray(env.action_space.high, dtype=np.float32)
    return rng.uniform(low, high).astype(np.float32)


def _model_action(model, obs: dict[str, Any], *, deterministic: bool) -> np.ndarray:
    action, _state = model.predict(obs, deterministic=bool(deterministic))
    return np.asarray(action, dtype=np.float32).reshape(-1)


def _distribution_policy_diagnostics(distribution: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    binary_logits = getattr(distribution, "binary_logits", None)
    if binary_logits is not None:
        try:
            logits = binary_logits.detach().to(device="cpu").numpy().astype(np.float64)
            if logits.ndim == 1:
                logits = logits.reshape(1, -1)
            if logits.ndim == 2 and logits.shape[1] >= len(HYBRID_BINARY_POLICY_SIGNAL_NAMES):
                probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -60.0, 60.0)))
                for idx, name in enumerate(HYBRID_BINARY_POLICY_SIGNAL_NAMES):
                    out[f"policy_logit_{name}"] = float(logits[0, idx])
                    out[f"policy_prob_{name}"] = float(probs[0, idx])
        except Exception:
            pass

    event_logits_fn = getattr(distribution, "_fire_event_logits", None)
    if callable(event_logits_fn):
        try:
            event_logits_tensor = event_logits_fn()
            logits = event_logits_tensor.detach().to(device="cpu").numpy().astype(np.float64)
            if logits.ndim == 1:
                logits = logits.reshape(1, -1)
            if logits.ndim == 2 and logits.shape[1] >= 2:
                shifted = logits - logits.max(axis=1, keepdims=True)
                probs = np.exp(shifted)
                probs = probs / np.clip(probs.sum(axis=1, keepdims=True), 1.0e-12, None)
                mode = int(np.argmax(probs[0]))
                entropy = -float(np.sum(probs[0, :2] * np.log(np.clip(probs[0, :2], 1.0e-12, 1.0))))
                out["policy_event_logit_hold"] = float(logits[0, 0])
                out["policy_event_logit_fire_once"] = float(logits[0, 1])
                out["policy_event_prob_hold"] = float(probs[0, 0])
                out["policy_event_prob_fire_once"] = float(probs[0, 1])
                out["policy_event_mode"] = float(mode)
                out["policy_event_entropy"] = float(entropy)
                event_mask = getattr(distribution, "fire_event_mask", None)
                if event_mask is not None:
                    mask = event_mask.detach().to(device="cpu").numpy().astype(np.float64)
                    if mask.ndim == 1:
                        mask = mask.reshape(1, -1)
                    if mask.ndim == 2 and mask.shape[1] >= 2:
                        out["policy_event_mask_hold"] = float(mask[0, 0])
                        out["policy_event_mask_fire_once"] = float(mask[0, 1])
        except Exception:
            pass

    event_delta_fn = getattr(distribution, "fire_event_logit_delta", None)
    event_prob_fn = getattr(distribution, "fire_event_probability", None)
    if callable(event_delta_fn) and callable(event_prob_fn):
        try:
            delta = event_delta_fn()
            prob = event_prob_fn()
            if delta is not None and prob is not None:
                delta_arr = delta.detach().to(device="cpu").numpy().astype(np.float64).reshape(-1)
                prob_arr = prob.detach().to(device="cpu").numpy().astype(np.float64).reshape(-1)
                if delta_arr.size > 0 and prob_arr.size > 0:
                    out["policy_event_logit_delta"] = float(delta_arr[0])
                    out["policy_event_prob_fire_once_unmasked"] = float(prob_arr[0])
        except Exception:
            pass

    q_values_fn = getattr(distribution, "fire_event_q_values", None)
    if callable(q_values_fn):
        try:
            q_values_tensor = q_values_fn()
            if q_values_tensor is not None:
                q_values = q_values_tensor.detach().to(device="cpu").numpy().astype(np.float64)
                if q_values.ndim == 1:
                    q_values = q_values.reshape(1, -1)
                if q_values.ndim == 2 and q_values.shape[1] >= 2:
                    out["policy_event_q_hold"] = float(q_values[0, 0])
                    out["policy_event_q_fire_once"] = float(q_values[0, 1])
                    out["policy_event_advantage"] = float(q_values[0, 1] - q_values[0, 0])
        except Exception:
            pass

    categorical_logits = getattr(distribution, "categorical_logits", None)
    if categorical_logits:
        try:
            _action_index, logits_tensor = list(categorical_logits)[0]
            logits = logits_tensor.detach().to(device="cpu").numpy().astype(np.float64)
            if logits.ndim == 1:
                logits = logits.reshape(1, -1)
            logits = logits - logits.max(axis=1, keepdims=True)
            probs = np.exp(logits)
            probs = probs / np.clip(probs.sum(axis=1, keepdims=True), 1.0e-12, None)
            mode = int(np.argmax(probs[0]))
            out["policy_weapon_select_mode"] = float(mode)
            out["policy_weapon_select_station0_prob"] = float(probs[0, 0])
            if probs.shape[1] > 1:
                out["policy_weapon_select_station1_prob"] = float(probs[0, 1])
            out["policy_weapon_select_mode_prob"] = float(probs[0, mode])
        except Exception:
            pass
    return out


def _m3_stopping_policy_diagnostics(policy: Any, obs_tensor: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    get_m3_stopping = getattr(policy, "get_m3_stopping", None)
    if not callable(get_m3_stopping):
        return out
    out["policy_m3_stopping_head_probe_available"] = 1.0
    try:
        stopping = get_m3_stopping(obs_tensor, detach_latent=True)
    except TypeError:
        try:
            stopping = get_m3_stopping(obs_tensor)
        except Exception:
            return out
    except Exception:
        return out
    if stopping is None:
        out["policy_m3_stopping_head_enabled"] = 0.0
        return out

    out["policy_m3_stopping_head_enabled"] = 1.0
    logit_tensor = getattr(stopping, "stopping_logit", getattr(stopping, "hazard_logit", None))
    hazard_tensor = getattr(stopping, "hazard", None)
    if logit_tensor is not None:
        try:
            logits = logit_tensor.detach().to(device="cpu").numpy().astype(np.float64).reshape(-1)
            if logits.size > 0:
                out["policy_m3_stop_logit"] = float(logits[0])
                out["policy_m3_boundary_cross"] = float(logits[0] >= 0.0)
        except Exception:
            pass
    if hazard_tensor is not None:
        try:
            hazards = hazard_tensor.detach().to(device="cpu").numpy().astype(np.float64).reshape(-1)
            if hazards.size > 0:
                out["policy_m3_stop_prob"] = float(hazards[0])
        except Exception:
            pass
    return out


def _model_policy_diagnostics(model: Any, obs: dict[str, Any]) -> dict[str, float]:
    policy = getattr(model, "policy", None)
    get_distribution = getattr(policy, "get_distribution", None)
    if not callable(get_distribution):
        return {}
    try:
        import torch as th

        obs_to_tensor = getattr(policy, "obs_to_tensor", None)
        if callable(obs_to_tensor):
            obs_tensor, _vectorized = obs_to_tensor(obs)
        else:
            from stable_baselines3.common.utils import obs_as_tensor

            obs_tensor = obs_as_tensor(obs, getattr(policy, "device", "cpu"))
        with th.no_grad():
            distribution = get_distribution(obs_tensor)
    except Exception:
        return {}
    diagnostics = _distribution_policy_diagnostics(distribution)
    with th.no_grad():
        diagnostics.update(_m3_stopping_policy_diagnostics(policy, obs_tensor))
    return diagnostics


def _policy_c2_context(env) -> dict[str, float]:
    try:
        base = _base_env(env)
        target_id = int(base.loader.primary_target_id or 0)
        blue_id = int(base.agent_id)
        c2_state = air_combat_c2_roe_state_from_mapping(
            _mission_command_dict(base.loader),
            target_id=int(target_id),
            agent_id=int(blue_id),
        )
    except Exception:
        return {}
    return {
        "policy_c2_authorization_to_fire": float(int(bool(c2_state.get("authorization_to_fire", False)))),
        "policy_c2_shot_budget_remaining": float(int(c2_state.get("shot_budget_remaining", 0) or 0)),
        "policy_c2_pending_assessment": float(int(bool(c2_state.get("pending_assessment", False)))),
        "policy_c2_wcs_state": float(int(c2_state.get("wcs_state", 0) or 0)),
        "policy_c2_engage_order_state": float(int(c2_state.get("engage_order_state", 0) or 0)),
        "policy_c2_shot_policy_state": float(int(c2_state.get("shot_policy_state", 0) or 0)),
    }


def _base_env(env):
    return getattr(env, "unwrapped", env)


def _build_env(scenario_path: str, train_config: dict[str, Any] | None):
    env_cfg = train_config.get("env", {}) if isinstance(train_config, dict) else {}
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
    env = UniversalEnv(
        os.path.abspath(scenario_path),
        include_visual=bool(env_cfg.get("include_visual", False)),
        include_proprio=bool(env_cfg.get("include_proprio", True)),
        action_mode=str(env_cfg.get("action_mode", "full")),
        mission_obs_mode=str(env_cfg.get("mission_obs_mode", "basic")),
        visual_downsample=int(env_cfg.get("visual_downsample", 1)),
        visual_update_interval=int(env_cfg.get("visual_update_interval", 1)),
        temporal_history_len=int(env_cfg.get("temporal_history_len", 1)),
        execution_step_runtime_mode=str(env_cfg.get("execution_step_runtime_mode", "compiled")),
        flight_shaping_backend=str(env_cfg.get("flight_shaping_backend", "compiled")),
        step_info_mode="full",
        runtime_compatibility_enabled=True,
    )
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_class is MultiTimescaleActionWrapper:
        return wrapper_class(env, **dict(wrapper_kwargs or {}))
    return env


def _snapshot_row(
    *,
    episode: int,
    step: int,
    env,
    action: np.ndarray | None,
    reward: float,
    terminated: bool,
    truncated: bool,
    info: dict[str, Any],
    initial_units: set[int],
    prev_missiles: int | None,
    prev_release_count: int = 0,
    policy_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = _base_env(env)
    sim = base.sim
    blue_id = int(base.agent_id)
    target_id = int(base.loader.primary_target_id or 0)
    truth = sim.get_agent_observation(blue_id)
    inst = sim.get_instrument_state(blue_id)
    target_track = _target_track(truth, target_id)
    current_units = _unit_id_set(sim)
    new_units = current_units - initial_units
    missiles_remaining = int(getattr(truth, "missiles_remaining", -1))
    target_active = bool(sim.is_unit_active(target_id)) if target_id > 0 else False
    target_health = _health_current(sim, target_id) if target_id > 0 else float("nan")
    range_geom = _distance_m(sim, blue_id, target_id) if target_id > 0 else float("nan")
    range_track = _finite_float(getattr(target_track, "range", float("nan"))) if target_track is not None else float("nan")
    reward_terms = info.get("reward_terms", {}) if isinstance(info, dict) else {}
    release_delta = (
        max(0, int(prev_missiles) - int(missiles_remaining))
        if prev_missiles is not None and missiles_remaining >= 0
        else 0
    )
    release = release_delta > 0
    engagement_events = sim.export_recent_engagement_events()
    effects_events = list(getattr(engagement_events, "effects_events", []) or [])
    damage_reports = list(getattr(engagement_events, "damage_reports", []) or [])
    last_effect = effects_events[-1] if effects_events else None
    last_report = damage_reports[-1] if damage_reports else None

    row: dict[str, Any] = {
        "episode": int(episode),
        "step": int(step),
        "sim_time_s": _finite_float(getattr(truth, "sim_time", step * sim.get_time_step())),
        "reward": float(reward),
        "total_reward_term": _finite_float(reward_terms.get("total", float("nan"))) if isinstance(reward_terms, dict) else float("nan"),
        "combat_win_bonus": _finite_float(reward_terms.get("combat_win_bonus", 0.0)) if isinstance(reward_terms, dict) else 0.0,
        "terminated": int(bool(terminated)),
        "truncated": int(bool(truncated)),
        "termination_reason": str(info.get("termination_reason", "")) if isinstance(info, dict) else "",
        "blue_health": _finite_float(getattr(truth, "health", float("nan"))),
        "blue_ias_mps": _finite_float(getattr(inst, "ias", float("nan"))),
        "blue_alt_baro_m": _finite_float(getattr(inst, "alt_baro", float("nan"))),
        "blue_alt_agl_m": _finite_float(getattr(inst, "alt_radar", float("nan"))),
        "blue_pitch_deg": _finite_float(getattr(inst, "pitch", float("nan"))),
        "blue_roll_deg": _finite_float(getattr(inst, "roll", float("nan"))),
        "blue_aoa_deg": _finite_float(getattr(inst, "aoa", float("nan"))),
        "can_fire": int(bool(getattr(truth, "can_fire", False))),
        "missiles_remaining": missiles_remaining,
        "missile_release": int(bool(release)),
        "missile_release_delta": int(release_delta),
        "spawned_units": int(len(new_units)),
        "target_id": int(target_id),
        "target_active": int(bool(target_active)),
        "target_health": float(target_health),
        "target_range_geom_m": float(range_geom),
        "target_contact": int(target_track is not None),
        "target_range_track_m": float(range_track),
        "target_closing_speed_mps": (
            _finite_float(getattr(target_track, "closing_speed", float("nan"))) if target_track is not None else float("nan")
        ),
        "target_track_age_s": (
            _finite_float(getattr(target_track, "time_since_update", float("nan"))) if target_track is not None else float("nan")
        ),
        "effects_event_count": int(len(effects_events)),
        "damage_report_count": int(len(damage_reports)),
        "last_effect_miss_distance_m": (
            _finite_float(getattr(last_effect, "miss_distance_m", float("nan"))) if last_effect is not None else float("nan")
        ),
        "last_effect_detonation_local_forward_m": (
            _finite_float(getattr(last_effect, "detonation_local_forward_m", float("nan")))
            if last_effect is not None
            else float("nan")
        ),
        "last_effect_detonation_local_right_m": (
            _finite_float(getattr(last_effect, "detonation_local_right_m", float("nan")))
            if last_effect is not None
            else float("nan")
        ),
        "last_effect_detonation_local_up_m": (
            _finite_float(getattr(last_effect, "detonation_local_up_m", float("nan")))
            if last_effect is not None
            else float("nan")
        ),
        "last_effect_direct_hitbox_intersection": int(
            bool(getattr(last_effect, "direct_hitbox_intersection", False)) if last_effect is not None else False
        ),
        "last_effect_projected_hitbox_count": int(
            getattr(last_effect, "projected_hitbox_count", 0) if last_effect is not None else 0
        ),
        "last_effect_component_hit_count": int(
            getattr(last_effect, "component_hit_count", 0) if last_effect is not None else 0
        ),
        "last_effect_fuze_type": str(getattr(last_effect, "fuze_type", "") or "") if last_effect is not None else "",
        "last_damage_report_id": int(getattr(last_report, "report_id", 0) or 0) if last_report is not None else 0,
        "last_damage_loss_state": str(getattr(last_report, "loss_state_to", "") or "") if last_report is not None else "",
        "last_damage_system_health_delta": (
            _finite_float(getattr(last_report, "system_health_delta", float("nan")))
            if last_report is not None
            else float("nan")
        ),
        "last_damage_mission_kill": int(
            bool(getattr(last_report, "mission_kill", False)) if last_report is not None else False
        ),
        "last_damage_mobility_kill": int(
            bool(getattr(last_report, "mobility_kill", False)) if last_report is not None else False
        ),
        "last_damage_sensor_kill": int(
            bool(getattr(last_report, "sensor_kill", False)) if last_report is not None else False
        ),
        "last_damage_destroyed": int(
            bool(getattr(last_report, "destroyed", False)) if last_report is not None else False
        ),
    }
    action_mode = str(getattr(base, "action_mode", "full"))
    columns = _action_columns_for_mode(action_mode)
    effective_action = getattr(base, "_last_action", None)
    if action is None:
        for name in ACTION_SIGNAL_NAMES:
            row[f"action_{name}"] = float("nan")
            row[f"effective_action_{name}"] = float("nan")
        row["action_weapon_select_id"] = float("nan")
        row["effective_action_weapon_select_id"] = float("nan")
    else:
        flat = np.asarray(action, dtype=np.float32).reshape(-1)
        effective_flat = (
            np.asarray(effective_action, dtype=np.float32).reshape(-1)
            if effective_action is not None
            else flat
        )
        for name in ACTION_SIGNAL_NAMES:
            idx = int(columns[name])
            row[f"action_{name}"] = _finite_float(flat[idx]) if flat.size > idx else float("nan")
            row[f"effective_action_{name}"] = (
                _finite_float(effective_flat[idx]) if effective_flat.size > idx else float("nan")
            )
        row["action_weapon_select_id"] = _weapon_select_id(flat, action_mode=action_mode)
        row["effective_action_weapon_select_id"] = _weapon_select_id(effective_flat, action_mode=action_mode)
        radar_idx = int(columns["radar_active"])
        master_idx = int(columns["master_arm"])
        fire_idx = int(columns["fire_weapon"])
        row["policy_action_radar_on"] = int(flat.size > radar_idx and flat[radar_idx] > 0.5)
        row["policy_action_master_arm_on"] = int(flat.size > master_idx and flat[master_idx] > 0.5)
        row["policy_action_fire_weapon_on"] = int(flat.size > fire_idx and flat[fire_idx] > 0.5)
        row["action_radar_on"] = int(effective_flat.size > radar_idx and effective_flat[radar_idx] > 0.5)
        row["action_master_arm_on"] = int(effective_flat.size > master_idx and effective_flat[master_idx] > 0.5)
        row["action_fire_weapon_on"] = int(effective_flat.size > fire_idx and effective_flat[fire_idx] > 0.5)
    mission_cmd = _mission_command_dict(base.loader)
    c2_state = air_combat_c2_roe_state_from_mapping(
        mission_cmd,
        target_id=int(target_id),
        agent_id=int(blue_id),
    )
    row.update(
        {
            "c2_roe_contract_present": int(bool(c2_state.get("contract_present", False))),
            "roe_state": int(c2_state.get("roe_state", 0)),
            "wcs_state": int(c2_state.get("wcs_state", 0)),
            "authorization_to_fire": int(bool(c2_state.get("authorization_to_fire", False))),
            "engage_order_state": int(c2_state.get("engage_order_state", 0)),
            "shot_policy_state": int(c2_state.get("shot_policy_state", 0)),
            "shot_budget_remaining": int(c2_state.get("shot_budget_remaining", 0)),
            "pending_assessment": int(bool(c2_state.get("pending_assessment", False))),
            "own_missiles_in_flight_count": int(c2_state.get("own_missiles_in_flight_count", 0)),
        }
    )
    row.update(
        _c2_roe_event_columns(
            c2_state,
            release_delta=int(release_delta),
            fire_attempted=bool(row.get("action_fire_weapon_on", 0)),
            previous_release_count=int(prev_release_count or 0),
        )
    )
    row.update(_a5_event_info_columns(info))
    if isinstance(policy_diagnostics, dict):
        for key, value in policy_diagnostics.items():
            row[str(key)] = _finite_float(value)
    return row


def _summarize_episode(
    rows: list[dict[str, Any]],
    launch_window_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not rows:
        return {}
    final = rows[-1]

    def first_step(predicate) -> int | None:
        for row in rows:
            if predicate(row):
                return int(row["step"])
        return None

    target_ranges = [
        float(row["target_range_geom_m"])
        for row in rows
        if math.isfinite(float(row.get("target_range_geom_m", float("nan"))))
    ]
    initial_target_health = float(rows[0].get("target_health", float("nan")))
    detonation_local = (
        float(final.get("last_effect_detonation_local_forward_m", float("nan"))),
        float(final.get("last_effect_detonation_local_right_m", float("nan"))),
        float(final.get("last_effect_detonation_local_up_m", float("nan"))),
    )
    detonation_local_norm = (
        math.sqrt(sum(value * value for value in detonation_local))
        if all(math.isfinite(value) for value in detonation_local)
        else float("nan")
    )
    fire_steps = [int(row["step"]) for row in rows if int(row.get("action_fire_weapon_on", 0)) > 0]
    fire_switch_steps: list[int] = []
    release_steps: list[int] = []
    prev_fire_on = False
    for row in rows:
        step = int(row.get("step", 0))
        fire_on = int(row.get("action_fire_weapon_on", 0)) > 0
        if step > 0 and fire_on and not prev_fire_on:
            fire_switch_steps.append(step)
        if int(row.get("missile_release", 0)) > 0:
            release_steps.append(step)
        prev_fire_on = fire_on
    release_step_set = set(release_steps)
    invalid_fire_attempt_steps = [step for step in fire_switch_steps if step not in release_step_set]
    release_intervals = [
        release_steps[idx] - release_steps[idx - 1]
        for idx in range(1, len(release_steps))
    ]
    fire_switch_intervals = [
        fire_switch_steps[idx] - fire_switch_steps[idx - 1]
        for idx in range(1, len(fire_switch_steps))
    ]
    row_by_step = {int(row.get("step", 0)): row for row in rows}
    authorized_release_count = int(sum(int(row.get("c2_roe_authorized_release_count", 0) or 0) for row in rows))
    violation_release_count = int(sum(int(row.get("c2_roe_violation_release_count", 0) or 0) for row in rows))
    unauthorized_release_count = int(sum(int(row.get("c2_roe_unauthorized_release_count", 0) or 0) for row in rows))
    pending_assessment_release_count = int(
        sum(int(row.get("c2_roe_pending_assessment_release_count", 0) or 0) for row in rows)
    )
    legacy_fallback_release_count = int(
        sum(int(row.get("c2_roe_legacy_fallback_release_count", 0) or 0) for row in rows)
    )
    a5_rejection_reason_counts = Counter(
        str(row.get("fire_once_rejected_reason", "") or "unspecified")
        for row in rows
        if int(row.get("step", 0)) > 0 and int(row.get("fire_once_rejected", 0) or 0) > 0
    )
    a5_engagement_state_counts = Counter(
        str(row.get("engagement_state", "") or "unknown")
        for row in rows
        if int(row.get("step", 0)) > 0 and str(row.get("engagement_state", "") or "") != ""
    )
    release_count_total = int(sum(int(row.get("missile_release_delta", row.get("missile_release", 0)) or 0) for row in rows))
    unknown_release_count = max(0, release_count_total - authorized_release_count - violation_release_count)

    def action_stat(name: str, reducer, default: float = float("nan")) -> float:
        key = str(name) if str(name).startswith("effective_action_") else f"action_{name}"
        values = [
            float(row.get(key, float("nan")))
            for row in rows
            if int(row.get("step", 0)) > 0
            and math.isfinite(float(row.get(key, float("nan"))))
        ]
        if not values:
            return float(default)
        return float(reducer(np.asarray(values, dtype=np.float64)))

    def row_stat(key: str, reducer, default: float = float("nan"), predicate=None) -> float:
        values = []
        for row in rows:
            if int(row.get("step", 0)) <= 0:
                continue
            if predicate is not None and not bool(predicate(row)):
                continue
            value = float(row.get(key, float("nan")))
            if math.isfinite(value):
                values.append(value)
        if not values:
            return float(default)
        return float(reducer(np.asarray(values, dtype=np.float64)))

    def authorized_first_shot_window(row: dict[str, Any]) -> bool:
        authorization_to_fire = row.get("policy_c2_authorization_to_fire", row.get("authorization_to_fire", 0))
        shot_budget_remaining = row.get("policy_c2_shot_budget_remaining", row.get("shot_budget_remaining", 0))
        pending_assessment = row.get("policy_c2_pending_assessment", row.get("pending_assessment", 0))
        return (
            int(authorization_to_fire or 0) > 0
            and int(shot_budget_remaining or 0) > 0
            and int(pending_assessment or 0) <= 0
        )

    authorized_window_step_count = int(
        sum(1 for row in rows if int(row.get("step", 0)) > 0 and authorized_first_shot_window(row))
    )
    fire_mask_open_step_count = int(
        sum(1 for row in rows if int(row.get("step", 0)) > 0 and int(row.get("fire_mask", 0) or 0) > 0)
    )

    def a6_open_window(row: dict[str, Any]) -> bool:
        return (
            int(row.get("step", 0)) > 0
            and str(row.get("engagement_state", "") or "") == "AuthorizedReady"
            and int(row.get("fire_mask", 0) or 0) > 0
        )

    launch_window = dict(launch_window_config or {})
    min_range_m = _finite_float(launch_window.get("min_range_m", 0.0), 0.0)
    max_range_m = _finite_float(launch_window.get("max_range_m", 0.0), 0.0)
    max_track_age_s = _finite_float(launch_window.get("max_track_age_s", float("inf")), float("inf"))
    min_window_age_steps = max(1, int(_finite_float(launch_window.get("min_window_age_steps", 1), 1.0)))
    legal_window_age_by_step: dict[int, int] = {}
    legal_window_age = 0
    for row in rows:
        step = int(row.get("step", 0))
        if a6_open_window(row):
            legal_window_age += 1
        else:
            legal_window_age = 0
        legal_window_age_by_step[step] = int(legal_window_age)

    def a7_quality_window(row: dict[str, Any]) -> bool:
        if not a6_open_window(row):
            return False
        step = int(row.get("step", 0))
        if legal_window_age_by_step.get(step, 0) < min_window_age_steps:
            return False
        range_m = _finite_float(row.get("target_range_track_m", float("nan")))
        if not math.isfinite(range_m):
            range_m = _finite_float(row.get("target_range_geom_m", float("nan")))
        if min_range_m > 0.0 and (not math.isfinite(range_m) or range_m < min_range_m):
            return False
        if max_range_m > 0.0 and math.isfinite(max_range_m) and (
            not math.isfinite(range_m) or range_m > max_range_m
        ):
            return False
        track_age_s = _finite_float(row.get("target_track_age_s", float("nan")))
        if math.isfinite(max_track_age_s) and max_track_age_s >= 0.0:
            if not math.isfinite(track_age_s) or track_age_s > max_track_age_s:
                return False
        return True

    def a7_prewindow(row: dict[str, Any]) -> bool:
        return a6_open_window(row) and not a7_quality_window(row)

    def m3_boundary_cross(row: dict[str, Any]) -> bool:
        return int(row.get("policy_m3_boundary_cross", 0) or 0) > 0

    def row_sign_frac(key: str, predicate, *, positive: bool) -> float:
        values = []
        for row in rows:
            if int(row.get("step", 0)) <= 0 or not bool(predicate(row)):
                continue
            value = float(row.get(key, float("nan")))
            if math.isfinite(value):
                values.append(value)
        if not values:
            return 0.0
        arr = np.asarray(values, dtype=np.float64)
        return float((arr > 0.0).mean() if positive else (arr < 0.0).mean())

    def row_cumulative_prob(key: str, predicate) -> float:
        values = []
        for row in rows:
            if int(row.get("step", 0)) <= 0 or not bool(predicate(row)):
                continue
            value = float(row.get(key, float("nan")))
            if math.isfinite(value):
                values.append(float(np.clip(value, 0.0, 1.0)))
        if not values:
            return 0.0
        probs = np.asarray(values, dtype=np.float64)
        return float(1.0 - np.exp(np.log1p(-probs).sum()))

    def count_rows(predicate) -> int:
        return int(sum(1 for row in rows if int(row.get("step", 0)) > 0 and bool(predicate(row))))

    reason = str(final.get("termination_reason", "")) or (
        "truncated" if int(final.get("truncated", 0)) else "terminated" if int(final.get("terminated", 0)) else "running"
    )
    return {
        "episode": int(final["episode"]),
        "steps": int(final["step"]),
        "termination_reason": reason,
        "terminated": bool(int(final.get("terminated", 0))),
        "truncated": bool(int(final.get("truncated", 0))),
        "total_reward": float(sum(float(row.get("reward", 0.0)) for row in rows if int(row.get("step", 0)) > 0)),
        "first_contact_step": first_step(lambda row: int(row.get("target_contact", 0)) > 0),
        "first_can_fire_step": first_step(lambda row: int(row.get("can_fire", 0)) > 0),
        "first_authorized_step": first_step(lambda row: int(row.get("authorization_to_fire", 0)) > 0),
        "first_fire_switch_step": fire_steps[0] if fire_steps else None,
        "first_release_step": first_step(lambda row: int(row.get("missile_release", 0)) > 0),
        "first_release_after_authorization_step": first_step(
            lambda row: int(row.get("missile_release", 0)) > 0 and int(row.get("authorization_to_fire", 0)) > 0
        ),
        "first_effects_event_step": first_step(lambda row: int(row.get("effects_event_count", 0)) > 0),
        "first_damage_report_step": first_step(lambda row: int(row.get("damage_report_count", 0)) > 0),
        "first_damage_progress_step": first_step(
            lambda row: float(row.get("last_damage_system_health_delta", 0.0)) < 0.0
        ),
        "first_target_health_drop_step": first_step(
            lambda row: math.isfinite(initial_target_health)
            and float(row.get("target_health", initial_target_health)) < initial_target_health - 1.0e-3
        ),
        "target_kill_step": first_step(lambda row: int(row.get("target_active", 1)) <= 0),
        "initial_missiles": int(rows[0].get("missiles_remaining", -1)),
        "final_missiles": int(final.get("missiles_remaining", -1)),
        "final_target_health": float(final.get("target_health", float("nan"))),
        "min_target_range_geom_m": min(target_ranges) if target_ranges else None,
        "radar_on_frac": float(np.mean([int(row.get("action_radar_on", 0)) for row in rows if int(row["step"]) > 0] or [0])),
        "master_arm_on_frac": float(
            np.mean([int(row.get("action_master_arm_on", 0)) for row in rows if int(row["step"]) > 0] or [0])
        ),
        "fire_weapon_on_frac": float(
            np.mean([int(row.get("action_fire_weapon_on", 0)) for row in rows if int(row["step"]) > 0] or [0])
        ),
        "fire_high_step_count": int(len(fire_steps)),
        "fire_attempt_count": int(len(fire_switch_steps)),
        "fire_switch_count": int(len(fire_switch_steps)),
        "fire_switch_steps": fire_switch_steps,
        "roe_state_at_fire": [int(row_by_step[step].get("roe_state", 0) or 0) for step in fire_switch_steps if step in row_by_step],
        "authorization_to_fire_at_fire": [
            int(row_by_step[step].get("authorization_to_fire", 0) or 0)
            for step in fire_switch_steps
            if step in row_by_step
        ],
        "fire_under_hold_count": int(sum(int(row.get("c2_roe_hold_fire_violation", 0) or 0) for row in rows)),
        "hold_fire_step_count": int(sum(1 for row in rows if int(row.get("c2_roe_hold_fire", 0) or 0) > 0)),
        "hold_fire_obeyed_count": int(sum(int(row.get("c2_roe_hold_fire_obeyed", 0) or 0) for row in rows)),
        "tight_without_assigned_authorized_target_count": int(
            sum(
                1
                for row in rows
                if int(row.get("wcs_state", 0) or 0) == 2
                and int(row.get("authorization_to_fire", 0) or 0) <= 0
                and int(row.get("action_fire_weapon_on", 0) or 0) > 0
            )
        ),
        "invalid_fire_attempt_count": int(len(invalid_fire_attempt_steps)),
        "invalid_fire_attempt_steps": invalid_fire_attempt_steps,
        "invalid_fire_attempt_rate": (
            float(len(invalid_fire_attempt_steps)) / float(len(fire_switch_steps)) if fire_switch_steps else 0.0
        ),
        "min_fire_switch_interval_steps": min(fire_switch_intervals) if fire_switch_intervals else None,
        "action_radar_active_mean": action_stat("radar_active", np.mean),
        "action_radar_active_max": action_stat("radar_active", np.max),
        "action_master_arm_mean": action_stat("master_arm", np.mean),
        "action_master_arm_max": action_stat("master_arm", np.max),
        "action_fire_weapon_mean": action_stat("fire_weapon", np.mean),
        "action_fire_weapon_max": action_stat("fire_weapon", np.max),
        "effective_action_fire_weapon_mean": action_stat("effective_action_fire_weapon", np.mean),
        "effective_action_fire_weapon_max": action_stat("effective_action_fire_weapon", np.max),
        "policy_prob_tms_up_mean": row_stat("policy_prob_tms_up", np.mean),
        "policy_prob_tms_up_max": row_stat("policy_prob_tms_up", np.max),
        "policy_logit_tms_up_mean": row_stat("policy_logit_tms_up", np.mean),
        "policy_logit_tms_up_max": row_stat("policy_logit_tms_up", np.max),
        "policy_prob_fire_weapon_mean": row_stat("policy_prob_fire_weapon", np.mean),
        "policy_prob_fire_weapon_max": row_stat("policy_prob_fire_weapon", np.max),
        "policy_logit_fire_weapon_mean": row_stat("policy_logit_fire_weapon", np.mean),
        "policy_logit_fire_weapon_max": row_stat("policy_logit_fire_weapon", np.max),
        "policy_event_prob_fire_once_mean": row_stat("policy_event_prob_fire_once", np.mean),
        "policy_event_prob_fire_once_max": row_stat("policy_event_prob_fire_once", np.max),
        "policy_event_logit_fire_once_max": row_stat("policy_event_logit_fire_once", np.max),
        "policy_m3_stopping_head_enabled": row_stat(
            "policy_m3_stopping_head_enabled",
            np.max,
            default=0.0,
        ),
        "policy_m3_stop_logit_mean": row_stat("policy_m3_stop_logit", np.mean, default=0.0),
        "policy_m3_stop_logit_max": row_stat("policy_m3_stop_logit", np.max, default=0.0),
        "policy_m3_stop_prob_mean": row_stat("policy_m3_stop_prob", np.mean, default=0.0),
        "policy_m3_stop_prob_max": row_stat("policy_m3_stop_prob", np.max, default=0.0),
        "policy_m3_boundary_cross_count": count_rows(m3_boundary_cross),
        "policy_m3_first_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0 and m3_boundary_cross(row)
        ),
        "a6_event_logit_delta_mean_open": row_stat("policy_event_logit_delta", np.mean, default=0.0, predicate=a6_open_window),
        "a6_event_fire_prob_mean_open": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=a6_open_window,
        ),
        "a6_event_fire_prob_max_open": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.max,
            default=0.0,
            predicate=a6_open_window,
        ),
        "a6_open_window_step_count": int(sum(1 for row in rows if a6_open_window(row))),
        "a7_prewindow_step_count": int(
            sum(1 for row in rows if int(row.get("step", 0)) > 0 and a7_prewindow(row))
        ),
        "a7_quality_window_step_count": int(
            sum(1 for row in rows if int(row.get("step", 0)) > 0 and a7_quality_window(row))
        ),
        "a7_prewindow_event_fire_prob_cum": row_cumulative_prob(
            "policy_event_prob_fire_once_unmasked",
            a7_prewindow,
        ),
        "a7_prewindow_event_fire_prob_mean": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=a7_prewindow,
        ),
        "a7_quality_window_event_fire_prob_mean": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=a7_quality_window,
        ),
        "a7_prewindow_m3_stop_prob_cum": row_cumulative_prob(
            "policy_m3_stop_prob",
            a7_prewindow,
        ),
        "a7_prewindow_m3_stop_prob_mean": row_stat(
            "policy_m3_stop_prob",
            np.mean,
            default=0.0,
            predicate=a7_prewindow,
        ),
        "a7_quality_window_m3_stop_prob_mean": row_stat(
            "policy_m3_stop_prob",
            np.mean,
            default=0.0,
            predicate=a7_quality_window,
        ),
        "a7_prewindow_m3_boundary_cross_count": count_rows(
            lambda row: a7_prewindow(row) and m3_boundary_cross(row)
        ),
        "a7_quality_window_m3_boundary_cross_count": count_rows(
            lambda row: a7_quality_window(row) and m3_boundary_cross(row)
        ),
        "a7_first_quality_window_m3_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0 and a7_quality_window(row) and m3_boundary_cross(row)
        ),
        "a7_event_credit_advantage_mean_prewindow": row_stat(
            "policy_event_advantage",
            np.mean,
            default=0.0,
            predicate=a7_prewindow,
        ),
        "a7_event_credit_advantage_positive_frac_prewindow": row_sign_frac(
            "policy_event_advantage",
            a7_prewindow,
            positive=True,
        ),
        "a7_event_credit_advantage_negative_frac_prewindow": row_sign_frac(
            "policy_event_advantage",
            a7_prewindow,
            positive=False,
        ),
        "a7_event_credit_advantage_mean_quality": row_stat(
            "policy_event_advantage",
            np.mean,
            default=0.0,
            predicate=a7_quality_window,
        ),
        "a7_event_credit_advantage_positive_frac_quality": row_sign_frac(
            "policy_event_advantage",
            a7_quality_window,
            positive=True,
        ),
        "a7_event_credit_advantage_negative_frac_quality": row_sign_frac(
            "policy_event_advantage",
            a7_quality_window,
            positive=False,
        ),
        "policy_event_mode_fire_once_count": int(
            sum(
                1
                for row in rows
                if int(row.get("step", 0)) > 0 and int(row.get("policy_event_mode", -1) or -1) == 1
            )
        ),
        "policy_event_mask_fire_once_open_count": int(
            sum(
                1
                for row in rows
                if int(row.get("step", 0)) > 0 and int(row.get("policy_event_mask_fire_once", 0) or 0) > 0
            )
        ),
        "authorized_window_step_count": int(authorized_window_step_count),
        "authorized_window_policy_prob_tms_up_mean": row_stat(
            "policy_prob_tms_up", np.mean, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_prob_tms_up_max": row_stat(
            "policy_prob_tms_up", np.max, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_logit_tms_up_max": row_stat(
            "policy_logit_tms_up", np.max, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_prob_fire_weapon_mean": row_stat(
            "policy_prob_fire_weapon", np.mean, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_prob_fire_weapon_max": row_stat(
            "policy_prob_fire_weapon", np.max, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_logit_fire_weapon_max": row_stat(
            "policy_logit_fire_weapon", np.max, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_event_prob_fire_once_mean": row_stat(
            "policy_event_prob_fire_once", np.mean, predicate=authorized_first_shot_window
        ),
        "authorized_window_policy_event_prob_fire_once_max": row_stat(
            "policy_event_prob_fire_once", np.max, predicate=authorized_first_shot_window
        ),
        "fire_mask_open_step_count": int(fire_mask_open_step_count),
        "fire_mask_open_frac": (
            float(fire_mask_open_step_count)
            / float(max(1, sum(1 for row in rows if int(row.get("step", 0)) > 0)))
        ),
        "fire_once_requested_count": int(
            sum(int(row.get("fire_once_requested", 0) or 0) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "fire_once_accepted_count": int(
            sum(int(row.get("fire_once_accepted", 0) or 0) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "fire_once_rejected_count": int(
            sum(int(row.get("fire_once_rejected", 0) or 0) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "release_executed_count": int(
            sum(int(row.get("release_executed", 0) or 0) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "post_launch_suppressed_count": int(
            sum(int(row.get("post_launch_suppressed", 0) or 0) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "fire_once_rejected_reason_counts": dict(sorted(a5_rejection_reason_counts.items())),
        "engagement_state_counts": dict(sorted(a5_engagement_state_counts.items())),
        "release_count": int(sum(int(row.get("missile_release", 0)) for row in rows)),
        "authorized_release_count": int(authorized_release_count),
        "unauthorized_release_count": int(unauthorized_release_count),
        "valid_authorized_release_count": int(
            sum(int(row.get("c2_roe_valid_authorized_release_count", 0) or 0) for row in rows)
        ),
        "violation_release_count": int(violation_release_count),
        "release_count_by_authorization_state": {
            "authorized": int(authorized_release_count),
            "unauthorized": int(unauthorized_release_count),
            "violation": int(violation_release_count),
            "legacy_or_unknown": int(unknown_release_count),
        },
        "repeat_release_before_assessment_count": int(
            sum(int(row.get("c2_roe_premature_second_shot", 0) or 0) for row in rows)
            + pending_assessment_release_count
        ),
        "pending_assessment_after_launch": bool(
            any(int(row.get("pending_assessment", 0) or 0) > 0 and int(row.get("missile_release", 0) or 0) > 0 for row in rows)
        ),
        "pending_assessment_release_count": int(pending_assessment_release_count),
        "shot_budget_violation_count": int(sum(int(row.get("c2_roe_shot_budget_violation", 0) or 0) for row in rows)),
        "authorized_salvo_release_count": int(
            sum(int(row.get("c2_roe_authorized_salvo_release_count", 0) or 0) for row in rows)
        ),
        "authorized_reattack_release_count": int(
            sum(int(row.get("c2_roe_authorized_reattack_release_count", 0) or 0) for row in rows)
        ),
        "legacy_roe_fallback_release_count": int(legacy_fallback_release_count),
        "release_steps": release_steps,
        "min_release_interval_steps": min(release_intervals) if release_intervals else None,
        "effects_event_count": int(final.get("effects_event_count", 0)),
        "damage_report_count": int(final.get("damage_report_count", 0)),
        "last_effect_miss_distance_m": float(final.get("last_effect_miss_distance_m", float("nan"))),
        "last_effect_detonation_local_forward_m": float(
            final.get("last_effect_detonation_local_forward_m", float("nan"))
        ),
        "last_effect_detonation_local_right_m": float(
            final.get("last_effect_detonation_local_right_m", float("nan"))
        ),
        "last_effect_detonation_local_up_m": float(
            final.get("last_effect_detonation_local_up_m", float("nan"))
        ),
        "last_effect_detonation_local_norm_m": detonation_local_norm,
        "last_effect_direct_hitbox_intersection": bool(
            int(final.get("last_effect_direct_hitbox_intersection", 0))
        ),
        "last_effect_projected_hitbox_count": int(final.get("last_effect_projected_hitbox_count", 0)),
        "last_effect_component_hit_count": int(final.get("last_effect_component_hit_count", 0)),
        "last_effect_fuze_type": str(final.get("last_effect_fuze_type", "")),
        "last_damage_loss_state": str(final.get("last_damage_loss_state", "")),
        "last_damage_system_health_delta": float(final.get("last_damage_system_health_delta", float("nan"))),
        "last_damage_mission_kill": bool(int(final.get("last_damage_mission_kill", 0))),
        "last_damage_mobility_kill": bool(int(final.get("last_damage_mobility_kill", 0))),
        "last_damage_sensor_kill": bool(int(final.get("last_damage_sensor_kill", 0))),
        "last_damage_destroyed": bool(int(final.get("last_damage_destroyed", 0))),
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario_path = os.path.abspath(args.scenario)
    train_config = load_json_config(os.path.abspath(args.train_config)) if args.train_config else {}
    launch_window_config = _a7_launch_window_config_from_train_config(train_config)
    model = None
    if args.mode == "model":
        if not args.model:
            raise ValueError("--mode model requires --model")
        model = load_sb3_policy(os.path.abspath(args.model), algo=str(args.algo), device=str(args.device))

    env = _build_env(scenario_path, train_config)
    base_env = _base_env(env)
    action_mode = str(getattr(base_env, "action_mode", "full"))
    rows: list[dict[str, Any]] = []
    episode_summaries: list[dict[str, Any]] = []
    try:
        for ep in range(int(args.episodes)):
            rng = np.random.default_rng(int(args.seed) + ep)
            obs, _info = env.reset(seed=int(args.seed) + ep)
            base_env = _base_env(env)
            max_steps = int(args.max_steps) if int(args.max_steps) > 0 else int(getattr(base_env, "max_steps", 0) or 1200)
            initial_units = _unit_id_set(base_env.sim)
            prev_missiles = int(getattr(base_env.sim.get_agent_observation(base_env.agent_id), "missiles_remaining", -1))
            release_count_so_far = 0
            range_gate_fired = False
            ep_rows: list[dict[str, Any]] = []
            initial_row = _snapshot_row(
                episode=ep,
                step=0,
                env=env,
                action=None,
                reward=0.0,
                terminated=False,
                truncated=False,
                info={},
                initial_units=initial_units,
                prev_missiles=None,
                prev_release_count=release_count_so_far,
                policy_diagnostics=None,
            )
            rows.append(initial_row)
            ep_rows.append(initial_row)
            for step in range(1, max_steps + 1):
                policy_diagnostics: dict[str, Any] = {}
                if args.mode == "forced_fire":
                    action = _forced_fire_action(obs, rng, step, action_mode=action_mode)
                elif args.mode == "range_gate_fire":
                    base_env = _base_env(env)
                    target_id = int(base_env.loader.primary_target_id or 0)
                    own_obs = base_env.sim.get_agent_observation(base_env.agent_id)
                    fire = (
                        not bool(range_gate_fired)
                        and target_id > 0
                        and bool(getattr(own_obs, "can_fire", False))
                        and _distance_m(base_env.sim, base_env.agent_id, target_id) <= float(args.fire_range_m)
                    )
                    action = _range_gate_fire_action(fire=fire, action_mode=action_mode)
                    if fire:
                        range_gate_fired = True
                elif args.mode == "switch_explore":
                    action = _switch_explore_action(obs, rng, step, action_mode=action_mode)
                elif args.mode == "uniform":
                    action = _uniform_action(env, obs, rng, step)
                elif args.mode == "model":
                    policy_diagnostics = _model_policy_diagnostics(model, obs)
                    policy_diagnostics.update(_policy_c2_context(env))
                    action = _model_action(model, obs, deterministic=not bool(args.stochastic))
                else:
                    raise ValueError(f"unknown mode: {args.mode}")

                obs, reward, terminated, truncated, info = env.step(action)
                row = _snapshot_row(
                    episode=ep,
                    step=step,
                    env=env,
                    action=action,
                    reward=float(reward),
                    terminated=bool(terminated),
                    truncated=bool(truncated),
                    info=info if isinstance(info, dict) else {},
                    initial_units=initial_units,
                    prev_missiles=prev_missiles,
                    prev_release_count=release_count_so_far,
                    policy_diagnostics=policy_diagnostics,
                )
                rows.append(row)
                ep_rows.append(row)
                prev_missiles = int(row.get("missiles_remaining", prev_missiles))
                release_count_so_far += int(row.get("missile_release_delta", 0) or 0)
                if bool(terminated or truncated):
                    break
            episode_summaries.append(_summarize_episode(ep_rows, launch_window_config=launch_window_config))
    finally:
        try:
            env.close()
        except Exception:
            pass

    reasons = Counter(str(row.get("termination_reason", "")) for row in episode_summaries)
    payload = {
        "scenario": scenario_path,
        "train_config": os.path.abspath(args.train_config) if args.train_config else None,
        "action_mode": action_mode,
        "mode": str(args.mode),
        "model": os.path.abspath(args.model) if args.model else None,
        "seed": int(args.seed),
        "episodes": int(args.episodes),
        "rows": len(rows),
        "termination_reasons": dict(sorted(reasons.items())),
        "episode_summaries": episode_summaries,
    }
    if args.csv_out:
        write_csv(args.csv_out, rows)
        payload["csv_out"] = os.path.abspath(args.csv_out)
    if args.json_out:
        write_json(args.json_out, payload)
    if args.plot_out:
        plot_rows(rows, args.plot_out)
        payload["plot_out"] = os.path.abspath(args.plot_out)
    return payload


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str, payload: dict[str, Any]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def plot_rows(rows: list[dict[str, Any]], path: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError("plotting requires matplotlib") from exc
    first_episode = min(int(row["episode"]) for row in rows)
    ep_rows = [row for row in rows if int(row["episode"]) == first_episode]
    x = np.asarray([float(row["sim_time_s"]) for row in ep_rows], dtype=np.float32)
    target_health = np.asarray([float(row["target_health"]) for row in ep_rows], dtype=np.float32)
    missiles = np.asarray([float(row["missiles_remaining"]) for row in ep_rows], dtype=np.float32)
    range_km = np.asarray([float(row["target_range_geom_m"]) / 1000.0 for row in ep_rows], dtype=np.float32)
    radar = np.asarray([float(row.get("action_radar_on", 0.0)) for row in ep_rows], dtype=np.float32)
    master = np.asarray([float(row.get("action_master_arm_on", 0.0)) for row in ep_rows], dtype=np.float32)
    fire = np.asarray([float(row.get("action_fire_weapon_on", 0.0)) for row in ep_rows], dtype=np.float32)

    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(x, target_health, label="target health")
    axes[0].plot(x, missiles * 25.0, label="blue missiles x25")
    axes[0].set_ylabel("health / ammo")
    axes[0].legend(loc="best")
    axes[1].plot(x, range_km, label="target range km", color="tab:green")
    axes[1].set_ylabel("range km")
    axes[1].legend(loc="best")
    axes[2].step(x, radar, where="post", label="radar")
    axes[2].step(x, master + 1.2, where="post", label="master arm")
    axes[2].step(x, fire + 2.4, where="post", label="fire weapon")
    axes[2].set_yticks([0.5, 1.7, 2.9])
    axes[2].set_yticklabels(["radar", "master", "fire"])
    axes[2].set_xlabel("sim time s")
    axes[2].legend(loc="best")
    fig.tight_layout()
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trace stage-0/stage-1 air-combat weapon-employment process.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument(
        "--mode",
        choices=["forced_fire", "range_gate_fire", "switch_explore", "uniform", "model"],
        default="forced_fire",
    )
    parser.add_argument("--fire_range_m", type=float, default=12000.0)
    parser.add_argument("--model", default="", help="SB3 model path for --mode model.")
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260525)
    parser.add_argument("--max_steps", type=int, default=0)
    parser.add_argument("--stochastic", action="store_true", help="Use stochastic policy prediction in --mode model.")
    parser.add_argument("--csv_out", default="")
    parser.add_argument("--json_out", default="")
    parser.add_argument("--plot_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_probe(args)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
