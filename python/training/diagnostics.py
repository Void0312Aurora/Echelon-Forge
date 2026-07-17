from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any

import numpy as np

from python.rl.policy_algo.first_event_hazard import (
    FIRST_EVENT_FIELD_ACTIVE,
    FIRST_EVENT_FIELD_SOURCE,
    FIRST_EVENT_FIELD_TARGET,
    FIRST_EVENT_SOURCE_ACCEPTED,
    FIRST_EVENT_SOURCE_CURRICULUM,
    FIRST_EVENT_SOURCE_DEADLINE,
    FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
    FIRST_EVENT_SOURCE_PREWINDOW,
    FIRST_EVENT_SOURCE_SHADOW_QUALITY,
)


def _safe_mean(values):
    if values is None:
        return None
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return None
    return float(arr.mean())


def _as_numpy_array(value: Any, *, dtype=np.float64) -> np.ndarray | None:
    if value is None:
        return None
    try:
        if hasattr(value, "detach"):
            value = value.detach().to(device="cpu").numpy()
        return np.asarray(value, dtype=dtype)
    except Exception:
        return None


def _obs_field_array(obs: Any, key: str, *, length: int, dtype=np.float64) -> np.ndarray | None:
    if not isinstance(obs, dict) or key not in obs:
        return None
    arr = _as_numpy_array(obs.get(key), dtype=dtype)
    if arr is None:
        return None
    flat = arr.reshape(-1)
    if int(flat.size) != int(length):
        return None
    return flat


def _first_event_label_masks_from_obs(obs: Any, length: int) -> dict[str, np.ndarray]:
    active_arr = _obs_field_array(obs, FIRST_EVENT_FIELD_ACTIVE, length=length)
    target_arr = _obs_field_array(obs, FIRST_EVENT_FIELD_TARGET, length=length)
    source_arr = _obs_field_array(obs, FIRST_EVENT_FIELD_SOURCE, length=length)
    if active_arr is None and target_arr is None and source_arr is None:
        return {}

    active = np.ones(int(length), dtype=bool) if active_arr is None else active_arr > 0.5
    prewindow = np.zeros(int(length), dtype=bool)
    quality = np.zeros(int(length), dtype=bool)

    if source_arr is not None:
        source = source_arr.astype(np.int64, copy=False)
        prewindow |= np.isin(
            source,
            (
                FIRST_EVENT_SOURCE_PREWINDOW,
                FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
            ),
        )
        quality |= np.isin(
            source,
            (
                FIRST_EVENT_SOURCE_ACCEPTED,
                FIRST_EVENT_SOURCE_CURRICULUM,
                FIRST_EVENT_SOURCE_DEADLINE,
                FIRST_EVENT_SOURCE_SHADOW_QUALITY,
            ),
        )

    if target_arr is not None:
        prewindow |= active & (target_arr <= 0.5)
        quality |= active & (target_arr > 0.5)

    return {
        "prewindow": prewindow & active,
        "quality": quality & active,
    }


def _cumulative_event_probability(probabilities: np.ndarray) -> float:
    probs = np.clip(np.asarray(probabilities, dtype=np.float64).reshape(-1), 0.0, 1.0)
    if probs.size == 0:
        return 0.0
    return float(1.0 - np.exp(np.log1p(-probs).sum()))


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


def record_basic_step_diagnostics(
    *,
    logger: Any,
    obs: Any,
    rewards: Any,
) -> None:
    r_mean = _safe_mean(rewards)
    if r_mean is not None:
        logger.record("diag/reward_mean", r_mean)

    if not (isinstance(obs, dict) and "instruments" in obs):
        return
    try:
        inst = np.asarray(obs["instruments"], dtype=np.float32)
    except Exception:
        return
    if inst.ndim == 1:
        inst = inst.reshape(1, -1)
    if inst.ndim != 2 or inst.shape[1] < 10:
        return

    logger.record("diag/ias_mean", float(inst[:, 0].mean()))
    logger.record("diag/alt_baro_mean", float(inst[:, 2].mean()))
    logger.record("diag/aoa_mean", float(inst[:, 5].mean()))
    logger.record("diag/pitch_mean", float(inst[:, 7].mean()))
    logger.record("diag/roll_mean", float(inst[:, 8].mean()))

    if inst.shape[1] >= 42:
        ils = inst[:, -4:]
        logger.record("diag/ils_valid_frac", float((ils[:, 0] > 0.5).mean()))
        logger.record("diag/ils_loc_abs_mean", float(np.abs(ils[:, 1]).mean()))


def _coerce_instrument_array(obs: Any) -> np.ndarray | None:
    if not (isinstance(obs, dict) and "instruments" in obs):
        return None
    try:
        inst_arr = np.asarray(obs["instruments"], dtype=np.float32)
        if inst_arr.ndim == 1:
            inst_arr = inst_arr.reshape(1, -1)
        return inst_arr
    except Exception:
        return None


def _coerce_action_array(actions: Any) -> np.ndarray | None:
    if actions is None:
        return None
    try:
        action_arr = np.asarray(actions, dtype=np.float32)
        if action_arr.ndim == 1:
            action_arr = action_arr.reshape(1, -1)
        return action_arr
    except Exception:
        return None


def _coerce_effective_action_array(infos: Any) -> np.ndarray | None:
    if not (isinstance(infos, (list, tuple)) and infos):
        return None
    eff_rows = []
    for info in infos:
        if not isinstance(info, dict) or "effective_action" not in info:
            return None
        try:
            eff_rows.append(np.asarray(info["effective_action"], dtype=np.float32).reshape(-1))
        except Exception:
            return None
    if not eff_rows:
        return None
    try:
        return np.stack(eff_rows, axis=0)
    except Exception:
        return None


def action_array_for_diagnostics(*, actions: Any, infos: Any) -> np.ndarray | None:
    effective_action_arr = _coerce_effective_action_array(infos)
    if effective_action_arr is not None:
        return effective_action_arr
    return _coerce_action_array(actions)


def _coerce_reward_array(rewards: Any) -> np.ndarray | None:
    if rewards is None:
        return None
    try:
        return np.asarray(rewards, dtype=np.float32).reshape(-1)
    except Exception:
        return None


def _coerce_done_array(dones: Any) -> np.ndarray | None:
    if dones is None:
        return None
    try:
        return np.asarray(dones, dtype=bool).reshape(-1)
    except Exception:
        return None


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


def record_first_event_info_diagnostics(
    *,
    model: Any,
    logger: Any,
    infos: Any,
) -> None:
    hazard_coef = float(getattr(model, "first_event_hazard_coef", 0.0) or 0.0)
    curriculum_coef_fn = getattr(model, "_current_first_event_curriculum_coef", None)
    if callable(curriculum_coef_fn):
        try:
            curriculum_coef = float(curriculum_coef_fn())
        except Exception:
            curriculum_coef = 0.0
    else:
        curriculum_coef = float(getattr(model, "first_event_curriculum_coef", 0.0) or 0.0)

    deadline_weight = float(getattr(model, "first_event_deadline_weight", 0.0) or 0.0)
    launch_window_enabled = bool(getattr(model, "first_event_launch_window_enabled", False))
    prewindow_hold_weight = float(getattr(model, "first_event_launch_window_prewindow_hold_weight", 0.0) or 0.0)
    has_model_knobs = (
        hazard_coef > 0.0
        or curriculum_coef > 0.0
        or deadline_weight > 0.0
        or launch_window_enabled
        or prewindow_hold_weight > 0.0
    )
    first_event_infos = []
    if isinstance(infos, (list, tuple)):
        first_event_infos = [
            info
            for info in infos
            if isinstance(info, dict)
            and any(
                key in info
                for key in (
                    "first_event_active",
                    "first_event_target",
                    "first_event_weight",
                    "first_event_source",
                    "first_event_window_id",
                )
            )
        ]
    if not has_model_knobs and not first_event_infos:
        return

    logger.record("a6/hazard_coef", hazard_coef)
    logger.record("a6/curriculum_coef", curriculum_coef)
    logger.record("a6/deadline_weight", deadline_weight)
    logger.record("a6/launch_window_enabled", float(launch_window_enabled))
    logger.record("a6/launch_window_prewindow_hold_weight", prewindow_hold_weight)
    if not first_event_infos:
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

    denom = float(len(first_event_infos))
    active_count = 0
    positive_count = 0
    curriculum_positive_count = 0
    deadline_positive_count = 0
    prewindow_hold_count = 0
    early_accepted_count = 0
    censored_window_ids: set[str] = set()
    censored_row_count = 0
    for idx, info in enumerate(first_event_infos):
        active = _bool_int(info.get("first_event_active", False))
        try:
            target = float(info.get("first_event_target", 0.0))
        except Exception:
            target = 0.0
        try:
            weight = float(info.get("first_event_weight", 1.0))
        except Exception:
            weight = 0.0
        source = str(info.get("first_event_source", "") or "").strip().lower()
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
            censored_window_ids.add(str(info.get("first_event_window_id", idx)))

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


def record_event_info_diagnostics(
    *,
    logger: Any,
    infos: Any,
) -> None:
    if not isinstance(infos, (list, tuple)):
        return
    event_info_infos = [
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
    if not event_info_infos:
        return
    denom = float(len(event_info_infos))

    def _sum_bool(key: str) -> int:
        return int(sum(_bool_int(info.get(key, False)) for info in event_info_infos))

    fire_mask_open = _sum_bool("fire_mask")
    requested = _sum_bool("fire_once_requested")
    accepted = _sum_bool("fire_once_accepted")
    executed = _sum_bool("release_executed")
    suppressed = _sum_bool("post_launch_suppressed")
    rejected = int(
        sum(
            1
            for info in event_info_infos
            if _bool_int(info.get("fire_once_requested", False))
            and not _bool_int(info.get("fire_once_accepted", False))
        )
    )

    logger.record("diag/event_info_count", float(len(event_info_infos)))
    logger.record("diag/fire_mask_open_frac", float(fire_mask_open) / denom)
    logger.record("diag/fire_once_requested_count", float(requested))
    logger.record("diag/fire_once_requested_frac", float(requested) / denom)
    logger.record("diag/fire_once_accepted_count", float(accepted))
    logger.record("diag/fire_once_rejected_count", float(rejected))
    logger.record("diag/fire_once_rejected_frac", float(rejected) / denom)
    logger.record("diag/release_executed_count", float(executed))
    logger.record("diag/post_launch_suppressed_count", float(suppressed))

    reason_counts = Counter(
        str(info.get("fire_once_rejected_reason", "") or "unspecified")
        for info in event_info_infos
        if _bool_int(info.get("fire_once_requested", False)) and not _bool_int(info.get("fire_once_accepted", False))
    )
    for reason, count in sorted(reason_counts.items()):
        logger.record(f"diag/reject_reason_{normalize_diagnostic_key(reason)}_count", float(count))

    state_counts = Counter(str(info.get("engagement_state", "") or "unknown") for info in event_info_infos)
    for state, count in sorted(state_counts.items()):
        logger.record(f"diag/state_{normalize_diagnostic_key(state)}_frac", float(count) / denom)

    component_values: dict[str, list[float]] = defaultdict(list)
    for info in event_info_infos:
        components = info.get("fire_mask_components", {})
        if not isinstance(components, dict):
            continue
        for key, value in components.items():
            component_values[str(key)].append(float(_bool_int(value)))
    for key, values in sorted(component_values.items()):
        if values:
            logger.record(
                f"diag/mask_component_{normalize_diagnostic_key(key)}_open_frac",
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
                label_masks = _first_event_label_masks_from_obs(obs, int(prob_arr.size))
                prewindow_mask = label_masks.get("prewindow")
                if prewindow_mask is not None:
                    prewindow_count = int(np.count_nonzero(prewindow_mask))
                    logger.record("a7/prewindow_step_count", float(prewindow_count))
                    if prewindow_count > 0:
                        prewindow_probs = prob_arr[prewindow_mask]
                        logger.record(
                            "a7/prewindow_event_fire_prob_cum",
                            _cumulative_event_probability(prewindow_probs),
                        )
                        logger.record("a7/prewindow_event_fire_prob_mean", float(prewindow_probs.mean()))
                        logger.record("a7/prewindow_event_fire_prob_max", float(prewindow_probs.max()))
                    else:
                        logger.record("a7/prewindow_event_fire_prob_cum", 0.0)
                        logger.record("a7/prewindow_event_fire_prob_mean", 0.0)
                        logger.record("a7/prewindow_event_fire_prob_max", 0.0)
                quality_mask = label_masks.get("quality")
                if quality_mask is not None:
                    quality_count = int(np.count_nonzero(quality_mask))
                    logger.record("a7/quality_window_step_count", float(quality_count))
                    if quality_count > 0:
                        logger.record(
                            "a7/quality_window_event_fire_prob_mean",
                            float(prob_arr[quality_mask].mean()),
                        )
                    else:
                        logger.record("a7/quality_window_event_fire_prob_mean", 0.0)
        except Exception:
            pass

    q_values_getter = getattr(distribution, "fire_event_q_values", None)
    if callable(q_values_getter):
        try:
            q_values_tensor = q_values_getter()
            if q_values_tensor is not None:
                values = q_values_tensor.detach().to(device="cpu").numpy().astype(np.float64)
                if values.ndim == 1:
                    values = values.reshape(1, -1)
                if values.ndim == 2 and values.shape[1] >= 2:
                    q_hold = values[:, 0]
                    q_fire = values[:, 1]
                    advantage = q_fire - q_hold
                    logger.record("a7/evc_q_hold_mean", float(q_hold.mean()))
                    logger.record("a7/evc_q_fire_mean", float(q_fire.mean()))
                    logger.record("a7/evc_adv_mean", float(advantage.mean()))
                    logger.record("a7/evc_adv_abs_mean", float(np.abs(advantage).mean()))
                    logger.record(
                        "a7/evc_adv_pos_frac",
                        float((advantage > 0.0).mean()),
                    )
                    logger.record(
                        "a7/evc_adv_neg_frac",
                        float((advantage < 0.0).mean()),
                    )

                    event_mask = getattr(distribution, "fire_event_mask", None)
                    if event_mask is not None:
                        mask = event_mask.detach().to(device="cpu").numpy().astype(bool)
                        if mask.ndim == 1:
                            mask = mask.reshape(1, -1)
                        if mask.ndim == 2 and mask.shape[1] >= 2 and mask.shape[0] == values.shape[0]:
                            open_mask = mask[:, 1].reshape(-1)
                            open_count = int(np.count_nonzero(open_mask))
                            logger.record("a7/evc_open_count", float(open_count))
                            if open_count > 0:
                                open_advantage = advantage[open_mask]
                                logger.record(
                                    "a7/evc_adv_mean_open",
                                    float(open_advantage.mean()),
                                )
                                logger.record(
                                    "a7/evc_adv_pos_frac_open",
                                    float((open_advantage > 0.0).mean()),
                                )
                            else:
                                logger.record("a7/evc_adv_mean_open", 0.0)
                                logger.record("a7/evc_adv_pos_frac_open", 0.0)

                    label_masks = _first_event_label_masks_from_obs(obs, int(values.shape[0]))
                    for label, mask in (
                        ("prewindow", label_masks.get("prewindow")),
                        ("quality", label_masks.get("quality")),
                    ):
                        if mask is None:
                            continue
                        label_key = "pre" if label == "prewindow" else "qual"
                        count = int(np.count_nonzero(mask))
                        logger.record(f"a7/evc_{label_key}_count", float(count))
                        if count <= 0:
                            logger.record(f"a7/evc_{label_key}_q_hold_mean", 0.0)
                            logger.record(f"a7/evc_{label_key}_q_fire_mean", 0.0)
                            logger.record(f"a7/evc_{label_key}_adv_mean", 0.0)
                            logger.record(f"a7/evc_{label_key}_adv_pos_frac", 0.0)
                            logger.record(f"a7/evc_{label_key}_adv_neg_frac", 0.0)
                            continue
                        label_advantage = advantage[mask]
                        logger.record(f"a7/evc_{label_key}_q_hold_mean", float(q_hold[mask].mean()))
                        logger.record(f"a7/evc_{label_key}_q_fire_mean", float(q_fire[mask].mean()))
                        logger.record(f"a7/evc_{label_key}_adv_mean", float(label_advantage.mean()))
                        logger.record(
                            f"a7/evc_{label_key}_adv_pos_frac",
                            float((label_advantage > 0.0).mean()),
                        )
                        logger.record(
                            f"a7/evc_{label_key}_adv_neg_frac",
                            float((label_advantage < 0.0).mean()),
                        )
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


class TrainingEventDiagnosticsWindow:
    def __init__(
        self,
        *,
        terminal_reward_keys: tuple[str, ...],
        preterm_window_steps: int,
    ) -> None:
        self.terminal_reward_keys = tuple(terminal_reward_keys)
        self.preterm_window_steps = max(4, int(preterm_window_steps))
        self.histories: list[deque] = []
        self.reset_for_training(1)

    def reset_for_training(self, n_envs: int) -> None:
        self.histories = [deque(maxlen=self.preterm_window_steps) for _ in range(max(1, int(n_envs)))]
        self.reset_window()

    def reset_window(self) -> None:
        self.episodes_window = 0
        self.term_counts_window: dict[str, int] = defaultdict(int)
        if not hasattr(self, "term_counts_total"):
            self.term_counts_total: dict[str, int] = defaultdict(int)
        self.failure_window = 0
        self.terminal_reward_window: dict[str, list[float]] = defaultdict(list)
        self.preterm_stats_window: dict[str, list[float]] = defaultdict(list)
        self.coop_world_done_window = 0
        self.coop_world_success_window = 0
        self.coop_shared_reset_window = 0
        self.coop_timeout_window = 0
        self.coop_role_episode_counts_window: dict[str, int] = defaultdict(int)
        self.coop_role_success_counts_window: dict[str, int] = defaultdict(int)
        self.coop_role_shared_reset_counts_window: dict[str, int] = defaultdict(int)
        self.coop_role_term_counts_window: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.coop_role_reward_window: dict[str, list[float]] = defaultdict(list)
        self.coop_role_length_window: dict[str, list[float]] = defaultdict(list)
        self.coop_role_waypoint_index_window: dict[str, list[float]] = defaultdict(list)
        self.coop_role_waypoint_progress_window: dict[str, list[float]] = defaultdict(list)
        self.coop_world_min_progress_window: list[float] = []
        self.coop_world_max_progress_window: list[float] = []
        self.coop_world_progress_gap_window: list[float] = []
        self.coop_world_slot_seen: dict[int, set[int]] = defaultdict(set)
        self.coop_world_slot_success: dict[int, bool] = defaultdict(bool)
        self.coop_world_slot_timeout: dict[int, bool] = defaultdict(bool)
        self.coop_world_slot_progress_values: dict[int, list[float]] = defaultdict(list)

    @staticmethod
    def is_failure_reason(reason: str) -> bool:
        if reason.startswith("success"):
            return False
        if reason == "combat_win":
            return False
        if reason in ("timeout", "running"):
            return False
        return True

    def infer_termination_reason(self, info: dict) -> str:
        if not isinstance(info, dict):
            return "done_unknown"

        tr = info.get("termination_reason")
        if isinstance(tr, str) and tr.strip():
            return normalize_diagnostic_key(tr)

        rt = info.get("reward_terms")
        if isinstance(rt, dict):
            try:
                if float(rt.get("nan_guard", 0.0)) > 0.0:
                    return "nan_guard"
            except Exception:
                pass
            if "waypoint_success_bonus" in rt:
                try:
                    if float(rt.get("waypoint_success_bonus", 0.0)) > 0.0:
                        return "success_waypoint"
                except Exception:
                    pass
            if "objective_bonus" in rt:
                try:
                    if float(rt.get("objective_bonus", 0.0)) > 0.0:
                        return "success_objective"
                except Exception:
                    pass
            if "off_runway_terminate_penalty" in rt:
                return "off_runway_terminate"
            if "gear_collapse_penalty" in rt:
                return "gear_collapse"
            if "failfast_penalty" in rt:
                return "failfast"
            if "crash_penalty" in rt:
                return "crash"

        ms = info.get("mission_status")
        if ms is not None:
            try:
                term = float(ms[3])
                if term > 0.5:
                    return "success"
                if term < -0.5:
                    return "failure_unknown"
            except Exception:
                pass

        if bool(info.get("TimeLimit.truncated", False)) or bool(info.get("truncated", False)):
            return "timeout"
        return "done_unknown"

    @staticmethod
    def extract_terminal_inst(info: dict) -> np.ndarray | None:
        if not isinstance(info, dict):
            return None
        term_obs = info.get("terminal_observation", None)
        if isinstance(term_obs, dict) and ("instruments" in term_obs):
            try:
                arr = np.asarray(term_obs["instruments"], dtype=np.float32).reshape(-1)
                if arr.size > 0:
                    return arr
            except Exception:
                return None
        return None

    @staticmethod
    def make_snapshot(inst_row: Any, action_row: Any, reward_scalar: Any) -> dict[str, float] | None:
        snap = {}
        if inst_row is not None:
            try:
                inst = np.asarray(inst_row, dtype=np.float32).reshape(-1)
            except Exception:
                inst = None
            if inst is not None and inst.size >= 11:
                snap["ias"] = float(inst[0])
                if inst.size > 3:
                    snap["alt_agl"] = float(inst[3])
                if inst.size > 5:
                    snap["aoa"] = float(inst[5])
                if inst.size > 6:
                    snap["beta"] = float(inst[6])
                if inst.size > 7:
                    snap["pitch"] = float(inst[7])
                if inst.size > 8:
                    snap["roll"] = float(inst[8])
                if inst.size > 10:
                    snap["g"] = float(inst[10])
                if inst.size > 14:
                    snap["yaw_rate"] = float(inst[14])

        if action_row is not None:
            try:
                action = np.asarray(action_row, dtype=np.float32).reshape(-1)
            except Exception:
                action = None
            if action is not None and action.size > 3:
                snap["throttle"] = float(action[3])
            mode = action_mode_from_width(0 if action is None else int(action.size))
            if action is not None and mode == "full" and action.size > 8:
                brake_raw = float(max(float(action[7]), float(action[8])))
                snap["brake"] = float(np.clip((brake_raw - 0.5) * 2.0, 0.0, 1.0))
            columns = combat_action_columns(mode)
            if action is not None and columns is not None and action.size > max(columns.values()):
                snap["radar_active"] = float(action[columns["radar_active"]] > 0.5)
                snap["master_arm"] = float(action[columns["master_arm"]] > 0.5)
                snap["fire_weapon"] = float(action[columns["fire_weapon"]] > 0.5)
                snap["fire_gun"] = float(action[columns["fire_gun"]] > 0.5)
                snap["tms_up"] = float(action[columns["tms_up"]] > 0.5)
                if mode == "air_combat_hybrid_v1":
                    snap["weapon_select_id"] = float(
                        int(np.clip(round(float(action[columns["weapon_select"]])), 0, 7))
                    )
                else:
                    snap["weapon_select_id"] = float(
                        int(np.clip(float(action[columns["weapon_select"]]), 0.0, 1.0) * 7.0)
                    )

        if reward_scalar is not None:
            try:
                snap["reward"] = float(reward_scalar)
            except Exception:
                pass
        return snap if snap else None

    def record_terminal_reward_terms(self, info: dict) -> None:
        if not isinstance(info, dict):
            return
        rt = info.get("reward_terms")
        if not isinstance(rt, dict):
            return
        for key in self.terminal_reward_keys:
            if key not in rt:
                continue
            try:
                self.terminal_reward_window[key].append(float(rt[key]))
            except Exception:
                continue

    def record_preterm_window(self, hist: deque) -> None:
        if not hist:
            return
        snap_list = list(hist)
        self.preterm_stats_window["window_len_steps"].append(float(len(snap_list)))

        def _values(name: str):
            vals = []
            for snap in snap_list:
                if name in snap:
                    try:
                        vals.append(float(snap[name]))
                    except Exception:
                        continue
            return vals

        alt = _values("alt_agl")
        if alt:
            self.preterm_stats_window["min_alt_agl_m"].append(float(np.min(alt)))
            self.preterm_stats_window["final_alt_agl_m"].append(float(alt[-1]))

        roll = _values("roll")
        if roll:
            self.preterm_stats_window["max_abs_roll_deg"].append(float(np.max(np.abs(roll))))
        pitch = _values("pitch")
        if pitch:
            self.preterm_stats_window["max_abs_pitch_deg"].append(float(np.max(np.abs(pitch))))
        aoa = _values("aoa")
        if aoa:
            self.preterm_stats_window["max_abs_aoa_deg"].append(float(np.max(np.abs(aoa))))
        beta = _values("beta")
        if beta:
            self.preterm_stats_window["max_abs_beta_deg"].append(float(np.max(np.abs(beta))))
        yaw_rate = _values("yaw_rate")
        if yaw_rate:
            self.preterm_stats_window["max_abs_yaw_rate_deg_s"].append(float(np.max(np.abs(yaw_rate))))
        g_vals = _values("g")
        if g_vals:
            self.preterm_stats_window["max_abs_g"].append(float(np.max(np.abs(g_vals))))
        throttle = _values("throttle")
        if throttle:
            self.preterm_stats_window["mean_throttle"].append(float(np.mean(throttle)))
        brake = _values("brake")
        if brake:
            self.preterm_stats_window["mean_brake"].append(float(np.mean(brake)))
        for switch_name in ("radar_active", "master_arm", "fire_weapon", "fire_gun"):
            vals = _values(switch_name)
            if vals:
                self.preterm_stats_window[f"mean_{switch_name}"].append(float(np.mean(vals)))
        weapon_select = _values("weapon_select_id")
        if weapon_select:
            self.preterm_stats_window["mean_weapon_select_id"].append(float(np.mean(weapon_select)))

    @staticmethod
    def coop_role_name(info: dict) -> str | None:
        if not isinstance(info, dict):
            return None
        role = str(info.get("formation_role_id", "") or "").strip()
        entity = str(info.get("entity_name", "") or "").strip()
        if role:
            return role
        if entity:
            return entity
        return None

    def record_cooperative_episode(self, info: dict, reason: str) -> None:
        if not isinstance(info, dict):
            return
        world_index = info.get("world_index", None)
        slot_index = info.get("slot_index", None)
        slots_per_world = info.get("slots_per_world", None)
        if world_index is None or slot_index is None:
            return
        try:
            world_idx = int(world_index)
            slot_idx = int(slot_index)
            expected_slots = max(1, int(slots_per_world)) if slots_per_world is not None else 1
        except Exception:
            return

        role_name = self.coop_role_name(info)
        ms = info.get("mission_status")
        if role_name:
            self.coop_role_episode_counts_window[role_name] += 1
            ep = info.get("episode", {})
            if isinstance(ep, dict):
                try:
                    self.coop_role_reward_window[role_name].append(float(ep.get("r", 0.0)))
                except Exception:
                    pass
                try:
                    self.coop_role_length_window[role_name].append(float(ep.get("l", 0.0)))
                except Exception:
                    pass
            if ms is not None:
                try:
                    arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                except Exception:
                    arr = None
                if arr is not None:
                    if arr.size >= 2:
                        try:
                            self.coop_role_waypoint_index_window[role_name].append(float(arr[1]))
                        except Exception:
                            pass
                    if arr.size >= 3:
                        try:
                            waypoint_count = float(arr[2])
                            progress = float(arr[1]) / waypoint_count if waypoint_count > 0.5 else 0.0
                            self.coop_role_waypoint_progress_window[role_name].append(progress)
                        except Exception:
                            pass
            if bool(float(info.get("shared_world_reset", 0.0)) > 0.5):
                self.coop_role_shared_reset_counts_window[role_name] += 1
            if str(reason).strip():
                self.coop_role_term_counts_window[role_name][str(reason)] += 1

        success = False
        if ms is not None:
            try:
                arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                if arr.size >= 4 and float(arr[3]) > 0.5:
                    success = True
            except Exception:
                success = False
            else:
                if arr.size >= 3:
                    try:
                        waypoint_count = float(arr[2])
                        progress = float(arr[1]) / waypoint_count if waypoint_count > 0.5 else 0.0
                        self.coop_world_slot_progress_values[world_idx].append(progress)
                    except Exception:
                        pass
        if role_name and success:
            self.coop_role_success_counts_window[role_name] += 1

        self.coop_world_slot_seen[world_idx].add(slot_idx)
        world_success_flag = bool(float(info.get("world_success", 0.0)) > 0.5) if isinstance(info, dict) else False
        self.coop_world_slot_success[world_idx] = bool(self.coop_world_slot_success[world_idx] or success)
        self.coop_world_slot_timeout[world_idx] = bool(self.coop_world_slot_timeout[world_idx] or str(reason) == "timeout")
        if bool(float(info.get("shared_world_reset", 0.0)) > 0.5):
            self.coop_shared_reset_window += 1

        if bool(float(info.get("world_done", 0.0)) > 0.5) and len(self.coop_world_slot_seen[world_idx]) >= expected_slots:
            self.coop_world_done_window += 1
            if bool(world_success_flag):
                self.coop_world_success_window += 1
            if bool(self.coop_world_slot_timeout[world_idx]):
                self.coop_timeout_window += 1
            progress_vals = self.coop_world_slot_progress_values.get(world_idx, [])
            if progress_vals:
                min_progress = float(np.min(progress_vals))
                max_progress = float(np.max(progress_vals))
                self.coop_world_min_progress_window.append(min_progress)
                self.coop_world_max_progress_window.append(max_progress)
                self.coop_world_progress_gap_window.append(float(max_progress - min_progress))
            self.coop_world_slot_seen.pop(world_idx, None)
            self.coop_world_slot_success.pop(world_idx, None)
            self.coop_world_slot_timeout.pop(world_idx, None)
            self.coop_world_slot_progress_values.pop(world_idx, None)

    def observe_step(self, *, obs: Any, actions: Any, rewards: Any, infos: Any, dones: Any) -> None:
        inst_arr = _coerce_instrument_array(obs)
        action_arr = _coerce_action_array(actions)
        effective_action_arr = _coerce_effective_action_array(infos)
        reward_arr = _coerce_reward_array(rewards)
        done_arr = _coerce_done_array(dones)
        info_rows = infos if isinstance(infos, (list, tuple)) else []

        n_envs = len(self.histories)
        for i in range(n_envs):
            done_i = bool(done_arr[i]) if (done_arr is not None and i < done_arr.shape[0]) else False
            info_i = info_rows[i] if i < len(info_rows) and isinstance(info_rows[i], dict) else {}
            if effective_action_arr is not None and i < effective_action_arr.shape[0]:
                act_i = effective_action_arr[i]
            else:
                act_i = action_arr[i] if (action_arr is not None and i < action_arr.shape[0]) else None
            rew_i = float(reward_arr[i]) if (reward_arr is not None and i < reward_arr.shape[0]) else None

            if done_i:
                inst_term = self.extract_terminal_inst(info_i)
                if inst_term is None:
                    inst_term = inst_arr[i] if (inst_arr is not None and i < inst_arr.shape[0]) else None
                snap = self.make_snapshot(inst_term, act_i, rew_i)
                if snap is not None:
                    self.histories[i].append(snap)

                reason = self.infer_termination_reason(info_i)
                self.episodes_window += 1
                self.term_counts_window[reason] += 1
                self.term_counts_total[reason] += 1
                self.record_terminal_reward_terms(info_i)
                self.record_cooperative_episode(info_i, reason)
                if self.is_failure_reason(reason):
                    self.failure_window += 1
                    self.record_preterm_window(self.histories[i])
                self.histories[i].clear()
            else:
                inst_i = inst_arr[i] if (inst_arr is not None and i < inst_arr.shape[0]) else None
                snap = self.make_snapshot(inst_i, act_i, rew_i)
                if snap is not None:
                    self.histories[i].append(snap)

    def record_and_reset(self, *, logger: Any) -> None:
        if self.episodes_window > 0:
            episodes = float(self.episodes_window)
            logger.record("diag/episodes_done_window", episodes)
            logger.record("diag/failure_frac_window", float(self.failure_window) / episodes)
            for reason in sorted(self.term_counts_window.keys()):
                cnt = float(self.term_counts_window[reason])
                logger.record(f"diag/term_frac_{reason}", cnt / episodes)
                logger.record(f"diag/term_count_total_{reason}", float(self.term_counts_total[reason]))

        for key, vals in self.terminal_reward_window.items():
            if vals:
                logger.record(f"diag/term_rew_{key}", float(np.mean(np.asarray(vals, dtype=np.float32))))

        for key, vals in self.preterm_stats_window.items():
            if vals:
                logger.record(f"diag/preterm_{key}", float(np.mean(np.asarray(vals, dtype=np.float32))))

        if self.coop_world_done_window > 0:
            worlds = float(self.coop_world_done_window)
            logger.record("coop_diag/world_episodes_done_window", worlds)
            logger.record("coop_diag/world_success_frac_window", float(self.coop_world_success_window) / worlds)
            logger.record("coop_diag/world_timeout_frac_window", float(self.coop_timeout_window) / worlds)
            logger.record("coop_diag/shared_reset_per_world_mean", float(self.coop_shared_reset_window) / worlds)
            if self.coop_world_min_progress_window:
                logger.record(
                    "coop_diag/world_min_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(self.coop_world_min_progress_window, dtype=np.float32))),
                )
            if self.coop_world_max_progress_window:
                logger.record(
                    "coop_diag/world_max_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(self.coop_world_max_progress_window, dtype=np.float32))),
                )
            if self.coop_world_progress_gap_window:
                logger.record(
                    "coop_diag/world_waypoint_progress_gap_frac_mean",
                    float(np.mean(np.asarray(self.coop_world_progress_gap_window, dtype=np.float32))),
                )
        total_role_eps = float(sum(self.coop_role_episode_counts_window.values()))
        if total_role_eps > 0.0:
            logger.record("coop_diag/slot_episodes_done_window", total_role_eps)
        for role_name in sorted(self.coop_role_episode_counts_window.keys()):
            episodes = float(self.coop_role_episode_counts_window[role_name])
            if episodes <= 0.0:
                continue
            role_key = normalize_diagnostic_key(role_name)
            logger.record(
                f"coop_diag/role_{role_key}_success_frac_window",
                float(self.coop_role_success_counts_window[role_name]) / episodes,
            )
            logger.record(
                f"coop_diag/role_{role_key}_shared_reset_frac_window",
                float(self.coop_role_shared_reset_counts_window[role_name]) / episodes,
            )
            rewards = self.coop_role_reward_window.get(role_name, [])
            if rewards:
                logger.record(
                    f"coop_diag/role_{role_key}_reward_mean",
                    float(np.mean(np.asarray(rewards, dtype=np.float32))),
                )
            lengths = self.coop_role_length_window.get(role_name, [])
            if lengths:
                logger.record(
                    f"coop_diag/role_{role_key}_episode_len_mean",
                    float(np.mean(np.asarray(lengths, dtype=np.float32))),
                )
            waypoint_indices = self.coop_role_waypoint_index_window.get(role_name, [])
            if waypoint_indices:
                logger.record(
                    f"coop_diag/role_{role_key}_waypoint_index_mean",
                    float(np.mean(np.asarray(waypoint_indices, dtype=np.float32))),
                )
            waypoint_progress = self.coop_role_waypoint_progress_window.get(role_name, [])
            if waypoint_progress:
                logger.record(
                    f"coop_diag/role_{role_key}_waypoint_progress_frac_mean",
                    float(np.mean(np.asarray(waypoint_progress, dtype=np.float32))),
                )
            for reason, count in sorted(self.coop_role_term_counts_window[role_name].items()):
                logger.record(f"coop_diag/role_{role_key}_term_frac_{reason}", float(count) / episodes)

        self.reset_window()


__all__ = [
    "TrainingEventDiagnosticsWindow",
    "action_mode_from_width",
    "action_array_for_diagnostics",
    "combat_action_columns",
    "normalize_diagnostic_key",
    "record_event_info_diagnostics",
    "record_first_event_info_diagnostics",
    "record_action_diagnostics",
    "record_basic_step_diagnostics",
    "record_hmoe_policy_diagnostics",
    "record_leader_diagnostics",
    "record_policy_distribution_diagnostics",
    "record_reward_term_diagnostics",
    "record_runway_gear_diagnostics",
]
