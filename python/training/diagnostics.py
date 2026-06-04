from __future__ import annotations

from typing import Any

import numpy as np


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


__all__ = ["record_policy_distribution_diagnostics"]
