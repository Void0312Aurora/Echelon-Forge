from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import numpy as np


def _safe_mean(values):
    if values is None:
        return None
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return None
    return float(arr.mean())


def _bool_int(value: Any) -> int:
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes", "on"})
    return int(bool(value))


def normalize_diagnostic_key(reason: str) -> str:
    if not reason:
        return "unknown"
    out = []
    for ch in str(reason).strip().lower():
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
        else:
            out.append("_")
    normalized = "".join(out).strip("_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized if normalized else "unknown"


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


def record_reward_term_diagnostics(
    *,
    logger: Any,
    infos: list[dict],
    reward_keys: tuple[str, ...],
) -> None:
    for key in reward_keys:
        vals = []
        for info in infos:
            if not isinstance(info, dict):
                continue
            reward_terms = info.get("reward_terms")
            if isinstance(reward_terms, dict) and key in reward_terms:
                try:
                    vals.append(float(reward_terms[key]))
                except Exception:
                    pass
        if vals:
            logger.record(f"diag/rew_{key}", float(np.asarray(vals, dtype=np.float32).mean()))


def record_runway_gear_diagnostics(
    *,
    logger: Any,
    infos: Any,
) -> None:
    if not isinstance(infos, (list, tuple)):
        return

    on_runway = [info.get("on_runway") for info in infos if isinstance(info, dict) and "on_runway" in info]
    if on_runway:
        logger.record("diag/on_runway_frac", float(np.asarray(on_runway, dtype=np.float32).mean()))

    on_runway_geom = [
        info.get("on_runway_geom") for info in infos if isinstance(info, dict) and "on_runway_geom" in info
    ]
    if on_runway_geom:
        logger.record("diag/on_runway_geom_frac", float(np.asarray(on_runway_geom, dtype=np.float32).mean()))

    runway_cross = [
        info.get("runway_cross_m") for info in infos if isinstance(info, dict) and "runway_cross_m" in info
    ]
    if runway_cross:
        runway_cross_array = np.asarray(runway_cross, dtype=np.float32)
        logger.record("diag/runway_cross_abs_mean_m", float(np.abs(runway_cross_array).mean()))
        abs_runway_cross = np.abs(runway_cross_array)
        try:
            logger.record("diag/runway_cross_abs_p95_m", float(np.percentile(abs_runway_cross, 95.0)))
        except Exception:
            pass
        logger.record("diag/runway_cross_abs_max_m", float(abs_runway_cross.max(initial=0.0)))

    gear_collapsed = [
        info.get("gear_collapsed") for info in infos if isinstance(info, dict) and "gear_collapsed" in info
    ]
    if gear_collapsed:
        logger.record("diag/gear_collapsed_frac", float(np.asarray(gear_collapsed, dtype=np.float32).mean()))

    gear_stress = [info.get("gear_stress") for info in infos if isinstance(info, dict) and "gear_stress" in info]
    if gear_stress:
        logger.record("diag/gear_stress_mean", float(np.asarray(gear_stress, dtype=np.float32).mean()))


def record_a6_first_event_info_diagnostics(
    *,
    model: Any,
    logger: Any,
    infos: Any,
) -> None:
    hazard_coef = float(getattr(model, "a6_first_event_hazard_coef", 0.0) or 0.0)
    curriculum_coef_fn = getattr(model, "_current_a6_first_event_curriculum_coef", None)
    if callable(curriculum_coef_fn):
        try:
            curriculum_coef = float(curriculum_coef_fn())
        except Exception:
            curriculum_coef = 0.0
    else:
        curriculum_coef = float(getattr(model, "a6_first_event_curriculum_coef", 0.0) or 0.0)

    deadline_weight = float(getattr(model, "a6_first_event_deadline_weight", 0.0) or 0.0)
    launch_window_enabled = bool(getattr(model, "a6_first_event_launch_window_enabled", False))
    prewindow_hold_weight = float(getattr(model, "a6_first_event_launch_window_prewindow_hold_weight", 0.0) or 0.0)
    has_model_knobs = (
        hazard_coef > 0.0
        or curriculum_coef > 0.0
        or deadline_weight > 0.0
        or launch_window_enabled
        or prewindow_hold_weight > 0.0
    )
    a6_infos = []
    if isinstance(infos, (list, tuple)):
        a6_infos = [
            info
            for info in infos
            if isinstance(info, dict)
            and any(
                key in info
                for key in (
                    "a6_first_event_active",
                    "a6_first_event_target",
                    "a6_first_event_weight",
                    "a6_first_event_source",
                    "a6_first_event_window_id",
                )
            )
        ]
    if not has_model_knobs and not a6_infos:
        return

    logger.record("a6/hazard_coef", hazard_coef)
    logger.record("a6/curriculum_coef", curriculum_coef)
    logger.record("a6/deadline_weight", deadline_weight)
    logger.record("a6/launch_window_enabled", float(launch_window_enabled))
    logger.record("a6/launch_window_prewindow_hold_weight", prewindow_hold_weight)
    if not a6_infos:
        logger.record("a6/active_count", 0.0)
        logger.record("a6/active_frac", 0.0)
        logger.record("a6/target_positive_count", 0.0)
        logger.record("a6/target_positive_frac", 0.0)
        logger.record("a6/curriculum_positive_count", 0.0)
        logger.record("a6/deadline_positive_count", 0.0)
        logger.record("a6/prewindow_hold_count", 0.0)
        logger.record("a6/early_accepted_count", 0.0)
        logger.record("a6/censored_window_count", 0.0)
        return

    denom = float(len(a6_infos))
    active_count = 0
    positive_count = 0
    curriculum_positive_count = 0
    deadline_positive_count = 0
    prewindow_hold_count = 0
    early_accepted_count = 0
    censored_window_ids: set[str] = set()
    censored_row_count = 0
    for idx, info in enumerate(a6_infos):
        active = _bool_int(info.get("a6_first_event_active", False))
        try:
            target = float(info.get("a6_first_event_target", 0.0))
        except Exception:
            target = 0.0
        try:
            weight = float(info.get("a6_first_event_weight", 1.0))
        except Exception:
            weight = 0.0
        source = str(info.get("a6_first_event_source", "") or "").strip().lower()
        active_weighted = bool(active and weight > 0.0)
        if active_weighted:
            active_count += 1
        if active_weighted and target > 0.5:
            positive_count += 1
            if source in {"curriculum", "2"}:
                curriculum_positive_count += 1
            if source in {"deadline", "4"}:
                deadline_positive_count += 1
        if active_weighted and target <= 0.5 and source in {"prewindow", "5"}:
            prewindow_hold_count += 1
        if active_weighted and target <= 0.5 and source in {"early_accepted", "early-accepted", "6"}:
            early_accepted_count += 1
        if source in {"censored", "3"}:
            censored_row_count += 1
            censored_window_ids.add(str(info.get("a6_first_event_window_id", idx)))

    logger.record("a6/active_count", float(active_count))
    logger.record("a6/active_frac", float(active_count) / denom)
    logger.record("a6/target_positive_count", float(positive_count))
    logger.record(
        "a6/target_positive_frac",
        float(positive_count) / float(active_count) if active_count > 0 else 0.0,
    )
    logger.record("a6/curriculum_positive_count", float(curriculum_positive_count))
    logger.record("a6/deadline_positive_count", float(deadline_positive_count))
    logger.record("a6/prewindow_hold_count", float(prewindow_hold_count))
    logger.record("a6/early_accepted_count", float(early_accepted_count))
    logger.record(
        "a6/censored_window_count",
        float(len(censored_window_ids) if censored_window_ids else censored_row_count),
    )


def record_a5_event_info_diagnostics(
    *,
    logger: Any,
    infos: Any,
) -> None:
    if not isinstance(infos, (list, tuple)):
        return
    a5_infos = [
        info
        for info in infos
        if isinstance(info, dict)
        and any(
            key in info
            for key in (
                "engagement_state",
                "fire_mask",
                "fire_once_requested",
                "fire_once_accepted",
                "fire_once_rejected_reason",
                "release_executed",
                "post_launch_suppressed",
            )
        )
    ]
    if not a5_infos:
        return
    denom = float(len(a5_infos))

    def _sum_bool(key: str) -> int:
        return int(sum(_bool_int(info.get(key, False)) for info in a5_infos))

    fire_mask_open = _sum_bool("fire_mask")
    requested = _sum_bool("fire_once_requested")
    accepted = _sum_bool("fire_once_accepted")
    executed = _sum_bool("release_executed")
    suppressed = _sum_bool("post_launch_suppressed")
    rejected = int(
        sum(
            1
            for info in a5_infos
            if _bool_int(info.get("fire_once_requested", False))
            and not _bool_int(info.get("fire_once_accepted", False))
        )
    )

    logger.record("diag/a5_event_info_count", float(len(a5_infos)))
    logger.record("diag/a5_fire_mask_open_frac", float(fire_mask_open) / denom)
    logger.record("diag/a5_fire_once_requested_count", float(requested))
    logger.record("diag/a5_fire_once_requested_frac", float(requested) / denom)
    logger.record("diag/a5_fire_once_accepted_count", float(accepted))
    logger.record("diag/a5_fire_once_rejected_count", float(rejected))
    logger.record("diag/a5_fire_once_rejected_frac", float(rejected) / denom)
    logger.record("diag/a5_release_executed_count", float(executed))
    logger.record("diag/a5_post_launch_suppressed_count", float(suppressed))

    reason_counts = Counter(
        str(info.get("fire_once_rejected_reason", "") or "unspecified")
        for info in a5_infos
        if _bool_int(info.get("fire_once_requested", False)) and not _bool_int(info.get("fire_once_accepted", False))
    )
    for reason, count in sorted(reason_counts.items()):
        logger.record(f"diag/a5_reject_reason_{normalize_diagnostic_key(reason)}_count", float(count))

    state_counts = Counter(str(info.get("engagement_state", "") or "unknown") for info in a5_infos)
    for state, count in sorted(state_counts.items()):
        logger.record(f"diag/a5_state_{normalize_diagnostic_key(state)}_frac", float(count) / denom)

    component_values: dict[str, list[float]] = defaultdict(list)
    for info in a5_infos:
        components = info.get("fire_mask_components", {})
        if not isinstance(components, dict):
            continue
        for key, value in components.items():
            component_values[str(key)].append(float(_bool_int(value)))
    for key, values in sorted(component_values.items()):
        if values:
            logger.record(
                f"diag/a5_mask_component_{normalize_diagnostic_key(key)}_open_frac",
                float(np.asarray(values, dtype=np.float32).mean()),
            )


def _mean_info_values(infos: list[dict], key: str) -> float | None:
    vals = []
    for info in infos:
        if not isinstance(info, dict) or key not in info:
            continue
        try:
            vals.append(float(info[key]))
        except Exception:
            continue
    return _safe_mean(vals)


def _mean_reward_term_values(infos: list[dict], info_key: str, term_key: str) -> float | None:
    vals = []
    for info in infos:
        if not isinstance(info, dict):
            continue
        reward_terms = info.get(info_key)
        if not isinstance(reward_terms, dict) or term_key not in reward_terms:
            continue
        try:
            vals.append(float(reward_terms[term_key]))
        except Exception:
            continue
    return _safe_mean(vals)


def record_leader_diagnostics(
    *,
    logger: Any,
    obs: Any,
    infos: list[dict],
    reward_keys: tuple[str, ...],
) -> None:
    if isinstance(obs, dict) and "ownship" in obs:
        try:
            ownship = np.asarray(obs["ownship"], dtype=np.float32)
            if ownship.ndim == 1:
                ownship = ownship.reshape(1, -1)
            if ownship.ndim == 2 and ownship.shape[1] >= 12:
                logger.record("leader_diag/ias_mean", float(ownship[:, 0].mean()))
                logger.record("leader_diag/alt_agl_mean", float(ownship[:, 2].mean()))
                logger.record("leader_diag/alt_baro_mean", float(ownship[:, 3].mean()))
                logger.record("leader_diag/vvi_mean", float(ownship[:, 4].mean()))
                logger.record("leader_diag/heading_mean", float(ownship[:, 5].mean()))
                logger.record("leader_diag/roll_abs_mean", float(np.abs(ownship[:, 7]).mean()))
                logger.record("leader_diag/pitch_abs_mean", float(np.abs(ownship[:, 8]).mean()))
                logger.record("leader_diag/gear_mean", float(ownship[:, 11].mean()))
        except Exception:
            pass

    if isinstance(obs, dict) and "terminal" in obs:
        try:
            terminal = np.asarray(obs["terminal"], dtype=np.float32)
            if terminal.ndim == 1:
                terminal = terminal.reshape(1, -1)
            if terminal.ndim == 2 and terminal.shape[1] >= 8:
                logger.record("leader_diag/dme_mean_m", float(terminal[:, 0].mean()))
                logger.record("leader_diag/loc_abs_mean", float(np.abs(terminal[:, 1]).mean()))
                logger.record("leader_diag/gs_abs_mean", float(np.abs(terminal[:, 2]).mean()))
                logger.record("leader_diag/runway_cross_abs_mean_m", float(np.abs(terminal[:, 4]).mean()))
                logger.record("leader_diag/runway_heading_abs_mean_deg", float(np.abs(terminal[:, 5]).mean()))
                logger.record("leader_diag/approach_phase_frac", float((terminal[:, 6] > 0.5).mean()))
                logger.record("leader_diag/landing_cmd_frac", float((terminal[:, 7] > 0.5).mean()))
        except Exception:
            pass

    if not infos:
        return

    mean_guarded = _mean_info_values(infos, "leader_phase_guarded")
    if mean_guarded is not None:
        logger.record("leader_diag/phase_guarded_frac", float(mean_guarded))
    mean_bias_guarded = _mean_info_values(infos, "leader_bias_guarded")
    if mean_bias_guarded is not None:
        logger.record("leader_diag/bias_guarded_frac", float(mean_bias_guarded))
    mean_terminal_feasible = _mean_info_values(infos, "leader_terminal_feasible")
    if mean_terminal_feasible is not None:
        logger.record("leader_diag/terminal_feasible_frac", float(mean_terminal_feasible))

    mode_counts: dict[str, int] = defaultdict(int)
    req_counts: dict[str, int] = defaultdict(int)
    reason_counts: dict[str, int] = defaultdict(int)
    bias_reason_counts: dict[str, int] = defaultdict(int)
    c2_task_counts: dict[str, int] = defaultdict(int)
    c2_transition_reason_counts: dict[str, int] = defaultdict(int)
    cmd_deltas = []
    for info in infos:
        if not isinstance(info, dict):
            continue
        mode = info.get("leader_phase_bucket")
        if isinstance(mode, str) and mode.strip():
            mode_counts[normalize_diagnostic_key(mode)] += 1
        req = info.get("leader_requested_phase_bucket")
        if isinstance(req, str) and req.strip():
            req_counts[normalize_diagnostic_key(req)] += 1
        reason = info.get("leader_phase_guard_reason")
        if isinstance(reason, str) and reason.strip():
            reason_counts[normalize_diagnostic_key(reason)] += 1
        bias_reason = info.get("leader_bias_guard_reason")
        if isinstance(bias_reason, str) and bias_reason.strip():
            bias_reason_counts[normalize_diagnostic_key(bias_reason)] += 1
        c2_task = info.get("leader_c2_task_name")
        if isinstance(c2_task, str) and c2_task.strip():
            c2_task_counts[normalize_diagnostic_key(c2_task)] += 1
        c2_reason = info.get("leader_c2_transition_reason")
        if isinstance(c2_reason, str) and c2_reason.strip():
            c2_transition_reason_counts[normalize_diagnostic_key(c2_reason)] += 1
        effective_command = info.get("leader_effective_command")
        baseline_command = info.get("leader_baseline_command")
        try:
            if effective_command is not None and baseline_command is not None:
                effective_arr = np.asarray(effective_command, dtype=np.float32).reshape(-1)
                baseline_arr = np.asarray(baseline_command, dtype=np.float32).reshape(-1)
                if effective_arr.size >= 4 and baseline_arr.size >= 4:
                    cmd_deltas.append(
                        abs(float(effective_arr[0]) - float(baseline_arr[0]))
                        + abs(float(effective_arr[1]) - float(baseline_arr[1])) / 180.0
                        + abs(float(effective_arr[2]) - float(baseline_arr[2]))
                        / max(1.0, abs(float(baseline_arr[2])) + 1.0)
                        + abs(float(effective_arr[3]) - float(baseline_arr[3]))
                        / max(1.0, abs(float(baseline_arr[3])) + 1.0)
                    )
        except Exception:
            continue

    total = float(max(1, len(infos)))
    for mode, count in sorted(mode_counts.items()):
        logger.record(f"leader_diag/phase_frac_{mode}", float(count) / total)
    for req, count in sorted(req_counts.items()):
        logger.record(f"leader_diag/request_frac_{req}", float(count) / total)
    for reason, count in sorted(reason_counts.items()):
        logger.record(f"leader_diag/guard_reason_frac_{reason}", float(count) / total)
    for reason, count in sorted(bias_reason_counts.items()):
        logger.record(f"leader_diag/bias_guard_reason_frac_{reason}", float(count) / total)
    for task_name, count in sorted(c2_task_counts.items()):
        logger.record(f"leader_diag/c2_task_frac_{task_name}", float(count) / total)
    for reason, count in sorted(c2_transition_reason_counts.items()):
        logger.record(f"leader_diag/c2_transition_reason_frac_{reason}", float(count) / total)
    if cmd_deltas:
        logger.record(
            "leader_diag/cmd_vs_baseline_delta_mean",
            float(np.mean(np.asarray(cmd_deltas, dtype=np.float32))),
        )
    report_valid = _mean_info_values(infos, "leader_report_valid")
    if report_valid is not None:
        logger.record("leader_diag/report_valid_frac", float(report_valid))
    c2_transitioned = _mean_info_values(infos, "leader_c2_transitioned")
    if c2_transitioned is not None:
        logger.record("leader_diag/c2_transition_frac", float(c2_transitioned))

    for key in reward_keys:
        mean_val = _mean_reward_term_values(infos, "leader_reward_terms", key)
        if mean_val is not None:
            logger.record(f"leader_diag/reward_{key}", float(mean_val))


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
    "normalize_diagnostic_key",
    "record_a5_event_info_diagnostics",
    "record_a6_first_event_info_diagnostics",
    "record_action_diagnostics",
    "record_hmoe_policy_diagnostics",
    "record_leader_diagnostics",
    "record_policy_distribution_diagnostics",
    "record_reward_term_diagnostics",
    "record_runway_gear_diagnostics",
]
