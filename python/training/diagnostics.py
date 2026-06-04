from __future__ import annotations

from typing import Any

import numpy as np


def action_mode_from_width(width: int) -> str:
    if int(width) == 12:
        return "air_combat_hybrid_v1"
    if int(width) >= 17:
        return "full"
    return "other"


def combat_action_columns(mode: str) -> dict[str, int] | None:
    if mode == "air_combat_hybrid_v1":
        return {
            "radar_active": 6,
            "tms_up": 7,
            "master_arm": 8,
            "fire_weapon": 9,
            "fire_gun": 10,
            "weapon_select": 11,
        }
    if mode == "full":
        return {
            "radar_active": 9,
            "tms_up": 12,
            "master_arm": 13,
            "fire_weapon": 14,
            "fire_gun": 15,
            "weapon_select": 16,
        }
    return None


def record_action_diagnostics(*, logger: Any, actions: Any) -> None:
    if actions is None:
        return
    try:
        action_array = np.asarray(actions, dtype=np.float32)
    except Exception:
        return

    if action_array.ndim == 2 and action_array.shape[1] >= 4:
        logger.record("diag/action_pitch_mean", float(action_array[:, 0].mean()))
        logger.record("diag/action_roll_mean", float(action_array[:, 1].mean()))
        logger.record("diag/action_rudder_mean", float(action_array[:, 2].mean()))
        logger.record("diag/action_throttle_mean", float(action_array[:, 3].mean()))
    mode = action_mode_from_width(int(action_array.shape[1])) if action_array.ndim == 2 else "other"
    if action_array.ndim == 2 and mode == "full" and action_array.shape[1] >= 9:
        logger.record(
            "diag/action_brake_any_frac",
            float((np.maximum(action_array[:, 7], action_array[:, 8]) > 0.5).mean()),
        )
        brake_raw = np.maximum(action_array[:, 7], action_array[:, 8])
        brake_amt = np.clip((brake_raw - 0.5) * 2.0, 0.0, 1.0)
        logger.record("diag/action_brake_amt_mean", float(brake_amt.mean()))
    columns = combat_action_columns(mode)
    if action_array.ndim == 2 and columns is not None and action_array.shape[1] > max(columns.values()):
        logger.record(
            "diag/action_radar_active_frac",
            float((action_array[:, columns["radar_active"]] > 0.5).mean()),
        )
        logger.record("diag/action_tms_up_frac", float((action_array[:, columns["tms_up"]] > 0.5).mean()))
        logger.record(
            "diag/action_master_arm_frac",
            float((action_array[:, columns["master_arm"]] > 0.5).mean()),
        )
        logger.record(
            "diag/action_fire_weapon_frac",
            float((action_array[:, columns["fire_weapon"]] > 0.5).mean()),
        )
        logger.record(
            "diag/action_fire_gun_frac",
            float((action_array[:, columns["fire_gun"]] > 0.5).mean()),
        )
        if mode == "air_combat_hybrid_v1":
            weapon_select_id = np.clip(np.rint(action_array[:, columns["weapon_select"]]), 0.0, 7.0)
        else:
            weapon_select_id = np.floor(np.clip(action_array[:, columns["weapon_select"]], 0.0, 1.0) * 7.0)
        logger.record("diag/action_weapon_select_id_mean", float(weapon_select_id.mean()))


def record_policy_distribution_diagnostics(
    *,
    model: Any,
    logger: Any,
    obs: Any,
) -> None:
    policy = getattr(model, "policy", None)
    get_distribution = getattr(policy, "get_distribution", None)
    if obs is None or not callable(get_distribution):
        return

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
        return

    binary_logits = getattr(distribution, "binary_logits", None)
    if binary_logits is not None:
        try:
            logits = binary_logits.detach().to(device="cpu").numpy().astype(np.float64)
            if logits.ndim == 1:
                logits = logits.reshape(1, -1)
            if logits.ndim == 2 and logits.shape[1] >= 5:
                probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -60.0, 60.0)))
                names = ("radar", "tms", "arm", "fire", "gun")
                for idx, name in enumerate(names):
                    logger.record(f"diag/pi_bin_{name}_logit_mean", float(logits[:, idx].mean()))
                    logger.record(f"diag/pi_bin_{name}_p_mean", float(probs[:, idx].mean()))
                    logger.record(f"diag/pi_bin_{name}_p_max", float(probs[:, idx].max()))
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
                denom = np.clip(probs.sum(axis=1, keepdims=True), 1.0e-12, None)
                probs = probs / denom
                mode = np.argmax(probs[:, :2], axis=1)
                entropy = -np.sum(
                    probs[:, :2] * np.log(np.clip(probs[:, :2], 1.0e-12, 1.0)),
                    axis=1,
                )
                logger.record("diag/pi_event_fire_p_mean", float(probs[:, 1].mean()))
                logger.record("diag/pi_event_fire_p_max", float(probs[:, 1].max()))
                logger.record("diag/pi_event_mode_fire_frac", float((mode == 1).mean()))
                logger.record("diag/pi_event_entropy_mean", float(entropy.mean()))
                event_mask = getattr(distribution, "fire_event_mask", None)
                if event_mask is not None:
                    mask = event_mask.detach().to(device="cpu").numpy().astype(np.float64)
                    if mask.ndim == 1:
                        mask = mask.reshape(1, -1)
                    if mask.ndim == 2 and mask.shape[1] >= 2:
                        logger.record("diag/pi_event_fire_mask_frac", float(mask[:, 1].mean()))
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
                mask_arr = np.ones_like(prob_arr, dtype=bool)
                event_mask = getattr(distribution, "fire_event_mask", None)
                if event_mask is not None:
                    mask = event_mask.detach().to(device="cpu").numpy().astype(bool)
                    if mask.ndim == 1:
                        mask = mask.reshape(1, -1)
                    if mask.ndim == 2 and mask.shape[1] >= 2:
                        mask_arr = mask[:, 1].reshape(-1)
                open_count = int(np.count_nonzero(mask_arr))
                logger.record("a6/open_window_count", float(open_count))
                if open_count > 0:
                    logger.record("a6/event_logit_delta_mean_open", float(delta_arr[mask_arr].mean()))
                    logger.record("a6/event_fire_prob_mean_open", float(prob_arr[mask_arr].mean()))
                    logger.record("a6/event_fire_prob_max_open", float(prob_arr[mask_arr].max()))
                else:
                    logger.record("a6/event_logit_delta_mean_open", 0.0)
                    logger.record("a6/event_fire_prob_mean_open", 0.0)
                    logger.record("a6/event_fire_prob_max_open", 0.0)
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
            denom = np.clip(probs.sum(axis=1, keepdims=True), 1.0e-12, None)
            probs = probs / denom
            mode = np.argmax(probs, axis=1)
            logger.record("diag/pi_wsel_mode_mean", float(mode.mean()))
            logger.record("diag/pi_wsel_s0_p_mean", float(probs[:, 0].mean()))
            if probs.shape[1] > 1:
                logger.record("diag/pi_wsel_s1_p_mean", float(probs[:, 1].mean()))
        except Exception:
            pass


def record_hmoe_policy_diagnostics(
    *,
    model: Any,
    logger: Any,
    num_timesteps: int,
    next_param_stats_t: int,
    log_every_timesteps: int,
) -> int:
    policy = getattr(model, "policy", None)

    get_route_stats = getattr(policy, "get_hmoe_route_stats", None)
    if callable(get_route_stats):
        try:
            route_stats = get_route_stats()
        except Exception:
            route_stats = None
        if isinstance(route_stats, dict):
            for key, value in route_stats.items():
                try:
                    logger.record(str(key), float(value))
                except Exception:
                    continue

    get_param_stats = getattr(policy, "get_hmoe_parameter_stats", None)
    if not callable(get_param_stats) or int(num_timesteps) < int(next_param_stats_t):
        return int(next_param_stats_t)

    try:
        param_stats = get_param_stats()
    except Exception:
        param_stats = None
    if isinstance(param_stats, dict):
        for key, value in param_stats.items():
            try:
                logger.record(str(key), float(value))
            except Exception:
                continue
    return int(num_timesteps) + int(log_every_timesteps)


__all__ = [
    "action_mode_from_width",
    "combat_action_columns",
    "record_action_diagnostics",
    "record_hmoe_policy_diagnostics",
    "record_policy_distribution_diagnostics",
]
