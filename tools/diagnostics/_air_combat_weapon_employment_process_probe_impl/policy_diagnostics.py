"""Action factories and policy diagnostics for the process probe."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from gym_envs.scenario_loader.reward_runtime.air_combat import air_combat_c2_roe_state_from_mapping
from gym_envs.universal_env_parts.air_combat_event_action import _build_fire_event_support
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.probe_env import _base_env
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    HYBRID_BINARY_POLICY_SIGNAL_NAMES,
    _action_columns_for_mode,
    _distance_m,
    _mission_command_dict,
)


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


def _forced_fire_action(
    _obs: dict[str, Any], _rng: np.random.Generator, _step: int, *, action_mode: str
) -> np.ndarray:
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


def _switch_explore_action(
    _obs: dict[str, Any], rng: np.random.Generator, _step: int, *, action_mode: str
) -> np.ndarray:
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


def _legal_fire_mask_open(env, *, action_mode: str, fire_range_m: float = 0.0) -> bool:
    base = _base_env(env)
    target_id = int(getattr(base.loader, "primary_target_id", 0) or 0)
    if target_id <= 0:
        return False
    if fire_range_m > 0.0:
        distance_m = _distance_m(base.sim, int(base.agent_id), target_id)
        if not math.isfinite(distance_m) or distance_m > float(fire_range_m):
            return False
    try:
        truth = base.sim.get_agent_observation(base.agent_id)
    except Exception:
        truth = None
    if str(action_mode) == "air_combat_hybrid_v1":
        support_action = _range_gate_fire_action(fire=False, action_mode=action_mode)
        try:
            support = _build_fire_event_support(
                base.loader,
                support_action,
                agent_id=int(base.agent_id),
                truth=truth,
            )
            return bool(int(support.get("fire_mask", 0) or 0) > 0)
        except Exception:
            return False
    return bool(getattr(truth, "can_fire", False))


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


def _m3_window_classifier_policy_diagnostics(policy: Any, obs_tensor: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    get_m3_window_logits = getattr(policy, "get_m3_window_logits", None)
    if not callable(get_m3_window_logits):
        return out
    out["policy_m3_window_classifier_probe_available"] = 1.0
    try:
        logits_tensor = get_m3_window_logits(obs_tensor, detach_latent=True)
    except TypeError:
        try:
            logits_tensor = get_m3_window_logits(obs_tensor)
        except Exception:
            return out
    except Exception:
        return out
    if logits_tensor is None:
        out["policy_m3_window_classifier_enabled"] = 0.0
        return out

    out["policy_m3_window_classifier_enabled"] = 1.0
    try:
        logits = logits_tensor.detach().to(device="cpu").numpy().astype(np.float64).reshape(-1)
        if logits.size > 0:
            logit = float(logits[0])
            out["policy_m3_window_classifier_logit"] = logit
            out["policy_m3_window_classifier_boundary_cross"] = float(logit >= 0.0)
            out["policy_m3_window_classifier_prob"] = float(
                1.0 / (1.0 + np.exp(-np.clip(logit, -60.0, 60.0)))
            )
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
        diagnostics.update(_m3_window_classifier_policy_diagnostics(policy, obs_tensor))
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
        "policy_c2_authorization_to_fire": float(
            int(bool(c2_state.get("authorization_to_fire", False)))
        ),
        "policy_c2_shot_budget_remaining": float(
            int(c2_state.get("shot_budget_remaining", 0) or 0)
        ),
        "policy_c2_pending_assessment": float(int(bool(c2_state.get("pending_assessment", False)))),
        "policy_c2_wcs_state": float(int(c2_state.get("wcs_state", 0) or 0)),
        "policy_c2_engage_order_state": float(int(c2_state.get("engage_order_state", 0) or 0)),
        "policy_c2_shot_policy_state": float(int(c2_state.get("shot_policy_state", 0) or 0)),
    }
