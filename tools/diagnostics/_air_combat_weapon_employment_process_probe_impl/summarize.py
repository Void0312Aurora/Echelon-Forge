"""Episode summary aggregation for the process probe."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

import numpy as np

from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_snapshot import (
    _lethality_chain_snapshot_columns,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import _finite_float
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.snapshot import (
    _last_row_before_auto_reset,
)


def _summarize_episode(
    rows: list[dict[str, Any]],
    launch_window_config: dict[str, Any] | None = None,
    lethality_chain_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not rows:
        return {}
    terminal_final = rows[-1]
    final = _last_row_before_auto_reset(rows)

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
    chain_snapshot = _lethality_chain_snapshot_columns(list(lethality_chain_rows or []))
    if not lethality_chain_rows:
        chain_snapshot = {key: final.get(key, value) for key, value in chain_snapshot.items()}
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
    invalid_fire_attempt_steps = [
        step for step in fire_switch_steps if step not in release_step_set
    ]
    release_intervals = [
        release_steps[idx] - release_steps[idx - 1] for idx in range(1, len(release_steps))
    ]
    fire_switch_intervals = [
        fire_switch_steps[idx] - fire_switch_steps[idx - 1]
        for idx in range(1, len(fire_switch_steps))
    ]
    row_by_step = {int(row.get("step", 0)): row for row in rows}
    authorized_release_count = int(
        sum(int(row.get("c2_roe_authorized_release_count", 0) or 0) for row in rows)
    )
    violation_release_count = int(
        sum(int(row.get("c2_roe_violation_release_count", 0) or 0) for row in rows)
    )
    unauthorized_release_count = int(
        sum(int(row.get("c2_roe_unauthorized_release_count", 0) or 0) for row in rows)
    )
    pending_assessment_release_count = int(
        sum(int(row.get("c2_roe_pending_assessment_release_count", 0) or 0) for row in rows)
    )
    rejection_reason_counts = Counter(
        str(row.get("fire_once_rejected_reason", "") or "unspecified")
        for row in rows
        if int(row.get("step", 0)) > 0 and int(row.get("fire_once_rejected", 0) or 0) > 0
    )
    engagement_state_counts = Counter(
        str(row.get("engagement_state", "") or "unknown")
        for row in rows
        if int(row.get("step", 0)) > 0 and str(row.get("engagement_state", "") or "") != ""
    )
    release_count_total = int(
        sum(
            int(row.get("missile_release_delta", row.get("missile_release", 0)) or 0)
            for row in rows
        )
    )
    unknown_release_count = max(
        0, release_count_total - authorized_release_count - violation_release_count
    )

    def action_stat(name: str, reducer, default: float = float("nan")) -> float:
        key = str(name) if str(name).startswith("effective_action_") else f"action_{name}"
        values = [
            float(row.get(key, float("nan")))
            for row in rows
            if int(row.get("step", 0)) > 0 and math.isfinite(float(row.get(key, float("nan"))))
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
        authorization_to_fire = row.get(
            "policy_c2_authorization_to_fire", row.get("authorization_to_fire", 0)
        )
        shot_budget_remaining = row.get(
            "policy_c2_shot_budget_remaining", row.get("shot_budget_remaining", 0)
        )
        pending_assessment = row.get(
            "policy_c2_pending_assessment", row.get("pending_assessment", 0)
        )
        return (
            int(authorization_to_fire or 0) > 0
            and int(shot_budget_remaining or 0) > 0
            and int(pending_assessment or 0) <= 0
        )

    authorized_window_step_count = int(
        sum(1 for row in rows if int(row.get("step", 0)) > 0 and authorized_first_shot_window(row))
    )
    fire_mask_open_step_count = int(
        sum(
            1
            for row in rows
            if int(row.get("step", 0)) > 0 and int(row.get("fire_mask", 0) or 0) > 0
        )
    )

    def open_window(row: dict[str, Any]) -> bool:
        return (
            int(row.get("step", 0)) > 0
            and str(row.get("engagement_state", "") or "") == "AuthorizedReady"
            and int(row.get("fire_mask", 0) or 0) > 0
        )

    launch_window = dict(launch_window_config or {})
    min_range_m = _finite_float(launch_window.get("min_range_m", 0.0), 0.0)
    max_range_m = _finite_float(launch_window.get("max_range_m", 0.0), 0.0)
    max_track_age_s = _finite_float(
        launch_window.get("max_track_age_s", float("inf")), float("inf")
    )
    min_window_age_steps = max(
        1, int(_finite_float(launch_window.get("min_window_age_steps", 1), 1.0))
    )
    legal_window_age_by_step: dict[int, int] = {}
    legal_window_age = 0
    for row in rows:
        step = int(row.get("step", 0))
        if open_window(row):
            legal_window_age += 1
        else:
            legal_window_age = 0
        legal_window_age_by_step[step] = int(legal_window_age)

    first_release_step = release_steps[0] if release_steps else None
    first_release_row = (
        row_by_step.get(int(first_release_step)) if first_release_step is not None else None
    )

    def release_row_float(key: str) -> float:
        if not isinstance(first_release_row, dict):
            return float("nan")
        return _finite_float(first_release_row.get(key, float("nan")))

    def release_row_int(key: str) -> int:
        if not isinstance(first_release_row, dict):
            return 0
        try:
            return int(first_release_row.get(key, 0) or 0)
        except Exception:
            return 0

    def quality_window(row: dict[str, Any]) -> bool:
        if not open_window(row):
            return False
        step = int(row.get("step", 0))
        if legal_window_age_by_step.get(step, 0) < min_window_age_steps:
            return False
        range_m = _finite_float(row.get("target_range_track_m", float("nan")))
        if not math.isfinite(range_m):
            range_m = _finite_float(row.get("target_range_geom_m", float("nan")))
        if min_range_m > 0.0 and (not math.isfinite(range_m) or range_m < min_range_m):
            return False
        if (
            max_range_m > 0.0
            and math.isfinite(max_range_m)
            and (not math.isfinite(range_m) or range_m > max_range_m)
        ):
            return False
        track_age_s = _finite_float(row.get("target_track_age_s", float("nan")))
        if math.isfinite(max_track_age_s) and max_track_age_s >= 0.0:
            if not math.isfinite(track_age_s) or track_age_s > max_track_age_s:
                return False
        return True

    def prewindow(row: dict[str, Any]) -> bool:
        return open_window(row) and not quality_window(row)

    def boundary_cross(row: dict[str, Any]) -> bool:
        return int(row.get("policy_boundary_cross", 0) or 0) > 0

    def window_classifier_boundary_cross(row: dict[str, Any]) -> bool:
        return int(row.get("policy_window_classifier_boundary_cross", 0) or 0) > 0

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

    def first_nonzero_reward_step(key: str) -> int | None:
        return first_step(
            lambda row: int(row.get("step", 0)) > 0
            and abs(_finite_float(row.get(key, 0.0), 0.0)) > 1.0e-12
        )

    reason = str(terminal_final.get("termination_reason", "")) or (
        "truncated"
        if int(terminal_final.get("truncated", 0))
        else "terminated"
        if int(terminal_final.get("terminated", 0))
        else "running"
    )
    return {
        "episode": int(terminal_final["episode"]),
        "steps": int(terminal_final["step"]),
        "termination_reason": reason,
        "terminated": bool(int(terminal_final.get("terminated", 0))),
        "truncated": bool(int(terminal_final.get("truncated", 0))),
        "total_reward": float(
            sum(float(row.get("reward", 0.0)) for row in rows if int(row.get("step", 0)) > 0)
        ),
        "damage_consequence_reward_total": row_stat(
            "damage_consequence_reward_total", np.sum, default=0.0
        ),
        "target_damage_consequence_reward_total": row_stat(
            "target_damage_consequence_reward_total", np.sum, default=0.0
        ),
        "self_damage_consequence_reward_total": row_stat(
            "self_damage_consequence_reward_total", np.sum, default=0.0
        ),
        "first_damage_consequence_reward_step": first_nonzero_reward_step(
            "damage_consequence_reward_total"
        ),
        "first_target_damage_consequence_reward_step": first_nonzero_reward_step(
            "target_damage_consequence_reward_total"
        ),
        "first_self_damage_consequence_reward_step": first_nonzero_reward_step(
            "self_damage_consequence_reward_total"
        ),
        "first_contact_step": first_step(lambda row: int(row.get("target_contact", 0)) > 0),
        "first_can_fire_step": first_step(lambda row: int(row.get("can_fire", 0)) > 0),
        "first_authorized_step": first_step(
            lambda row: int(row.get("authorization_to_fire", 0)) > 0
        ),
        "first_fire_switch_step": fire_steps[0] if fire_steps else None,
        "first_release_step": first_step(lambda row: int(row.get("missile_release", 0)) > 0),
        "first_release_sim_time_s": release_row_float("sim_time_s"),
        "first_release_target_range_geom_m": release_row_float("target_range_geom_m"),
        "first_release_target_range_track_m": release_row_float("target_range_track_m"),
        "first_release_target_track_age_s": release_row_float("target_track_age_s"),
        "first_release_legal_window_age_steps": (
            int(legal_window_age_by_step.get(int(first_release_step), 0))
            if first_release_step is not None
            else 0
        ),
        "first_release_fire_mask": release_row_int("fire_mask"),
        "first_release_engagement_state": (
            str(first_release_row.get("engagement_state", "") or "")
            if isinstance(first_release_row, dict)
            else ""
        ),
        "first_release_target_health": release_row_float("target_health"),
        "first_release_blue_health": release_row_float("blue_health"),
        "first_release_after_authorization_step": first_step(
            lambda row: int(row.get("missile_release", 0)) > 0
            and int(row.get("authorization_to_fire", 0)) > 0
        ),
        "first_effects_event_step": first_step(
            lambda row: int(row.get("effects_event_count", 0)) > 0
        ),
        "first_damage_report_step": first_step(
            lambda row: int(row.get("damage_report_count", 0)) > 0
        ),
        "first_damage_progress_step": first_step(
            lambda row: float(row.get("lethality_chain_system_health_delta", 0.0)) < 0.0
        ),
        "first_target_health_drop_step": first_step(
            lambda row: math.isfinite(initial_target_health)
            and float(row.get("target_health", initial_target_health))
            < initial_target_health - 1.0e-3
        ),
        "target_kill_step": first_step(lambda row: int(row.get("target_active", 1)) <= 0),
        "initial_missiles": int(rows[0].get("missiles_remaining", -1)),
        "final_missiles": int(final.get("missiles_remaining", -1)),
        "final_target_health": float(final.get("target_health", float("nan"))),
        "min_target_range_geom_m": min(target_ranges) if target_ranges else None,
        "radar_on_frac": float(
            np.mean(
                [int(row.get("action_radar_on", 0)) for row in rows if int(row["step"]) > 0] or [0]
            )
        ),
        "master_arm_on_frac": float(
            np.mean(
                [int(row.get("action_master_arm_on", 0)) for row in rows if int(row["step"]) > 0]
                or [0]
            )
        ),
        "fire_weapon_on_frac": float(
            np.mean(
                [int(row.get("action_fire_weapon_on", 0)) for row in rows if int(row["step"]) > 0]
                or [0]
            )
        ),
        "fire_high_step_count": int(len(fire_steps)),
        "fire_attempt_count": int(len(fire_switch_steps)),
        "fire_switch_count": int(len(fire_switch_steps)),
        "fire_switch_steps": fire_switch_steps,
        "roe_state_at_fire": [
            int(row_by_step[step].get("roe_state", 0) or 0)
            for step in fire_switch_steps
            if step in row_by_step
        ],
        "authorization_to_fire_at_fire": [
            int(row_by_step[step].get("authorization_to_fire", 0) or 0)
            for step in fire_switch_steps
            if step in row_by_step
        ],
        "fire_under_hold_count": int(
            sum(int(row.get("c2_roe_hold_fire_violation", 0) or 0) for row in rows)
        ),
        "hold_fire_step_count": int(
            sum(1 for row in rows if int(row.get("c2_roe_hold_fire", 0) or 0) > 0)
        ),
        "hold_fire_obeyed_count": int(
            sum(int(row.get("c2_roe_hold_fire_obeyed", 0) or 0) for row in rows)
        ),
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
            float(len(invalid_fire_attempt_steps)) / float(len(fire_switch_steps))
            if fire_switch_steps
            else 0.0
        ),
        "min_fire_switch_interval_steps": min(fire_switch_intervals)
        if fire_switch_intervals
        else None,
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
        "policy_stopping_head_enabled": row_stat(
            "policy_stopping_head_enabled",
            np.max,
            default=0.0,
        ),
        "policy_stop_logit_mean": row_stat("policy_stop_logit", np.mean, default=0.0),
        "policy_stop_logit_max": row_stat("policy_stop_logit", np.max, default=0.0),
        "policy_stop_prob_mean": row_stat("policy_stop_prob", np.mean, default=0.0),
        "policy_stop_prob_max": row_stat("policy_stop_prob", np.max, default=0.0),
        "policy_boundary_cross_count": count_rows(boundary_cross),
        "policy_first_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0 and boundary_cross(row)
        ),
        "policy_window_classifier_head_enabled": row_stat(
            "policy_window_classifier_enabled",
            np.max,
            default=0.0,
        ),
        "policy_window_classifier_logit_mean": row_stat(
            "policy_window_classifier_logit",
            np.mean,
            default=0.0,
        ),
        "policy_window_classifier_logit_max": row_stat(
            "policy_window_classifier_logit",
            np.max,
            default=0.0,
        ),
        "policy_window_classifier_prob_mean": row_stat(
            "policy_window_classifier_prob",
            np.mean,
            default=0.0,
        ),
        "policy_window_classifier_prob_max": row_stat(
            "policy_window_classifier_prob",
            np.max,
            default=0.0,
        ),
        "policy_window_classifier_boundary_cross_count": count_rows(
            window_classifier_boundary_cross
        ),
        "policy_window_classifier_first_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0 and window_classifier_boundary_cross(row)
        ),
        "event_logit_delta_mean_open": row_stat(
            "policy_event_logit_delta", np.mean, default=0.0, predicate=open_window
        ),
        "event_fire_prob_mean_open": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=open_window,
        ),
        "event_fire_prob_max_open": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.max,
            default=0.0,
            predicate=open_window,
        ),
        "open_window_step_count": int(sum(1 for row in rows if open_window(row))),
        "prewindow_step_count": int(
            sum(1 for row in rows if int(row.get("step", 0)) > 0 and prewindow(row))
        ),
        "quality_window_step_count": int(
            sum(1 for row in rows if int(row.get("step", 0)) > 0 and quality_window(row))
        ),
        "prewindow_event_fire_prob_cum": row_cumulative_prob(
            "policy_event_prob_fire_once_unmasked",
            prewindow,
        ),
        "prewindow_event_fire_prob_mean": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=prewindow,
        ),
        "quality_window_event_fire_prob_mean": row_stat(
            "policy_event_prob_fire_once_unmasked",
            np.mean,
            default=0.0,
            predicate=quality_window,
        ),
        "prewindow_stop_prob_cum": row_cumulative_prob(
            "policy_stop_prob",
            prewindow,
        ),
        "prewindow_stop_prob_mean": row_stat(
            "policy_stop_prob",
            np.mean,
            default=0.0,
            predicate=prewindow,
        ),
        "quality_window_stop_prob_mean": row_stat(
            "policy_stop_prob",
            np.mean,
            default=0.0,
            predicate=quality_window,
        ),
        "prewindow_boundary_cross_count": count_rows(
            lambda row: prewindow(row) and boundary_cross(row)
        ),
        "quality_window_boundary_cross_count": count_rows(
            lambda row: quality_window(row) and boundary_cross(row)
        ),
        "first_quality_window_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0
            and quality_window(row)
            and boundary_cross(row)
        ),
        "prewindow_window_classifier_prob_mean": row_stat(
            "policy_window_classifier_prob",
            np.mean,
            default=0.0,
            predicate=prewindow,
        ),
        "quality_window_window_classifier_prob_mean": row_stat(
            "policy_window_classifier_prob",
            np.mean,
            default=0.0,
            predicate=quality_window,
        ),
        "prewindow_window_classifier_logit_mean": row_stat(
            "policy_window_classifier_logit",
            np.mean,
            default=0.0,
            predicate=prewindow,
        ),
        "quality_window_window_classifier_logit_mean": row_stat(
            "policy_window_classifier_logit",
            np.mean,
            default=0.0,
            predicate=quality_window,
        ),
        "prewindow_window_classifier_boundary_cross_count": count_rows(
            lambda row: prewindow(row) and window_classifier_boundary_cross(row)
        ),
        "quality_window_window_classifier_boundary_cross_count": count_rows(
            lambda row: quality_window(row) and window_classifier_boundary_cross(row)
        ),
        "first_quality_window_window_classifier_boundary_cross_step": first_step(
            lambda row: int(row.get("step", 0)) > 0
            and quality_window(row)
            and window_classifier_boundary_cross(row)
        ),
        "event_credit_advantage_mean_prewindow": row_stat(
            "policy_event_advantage",
            np.mean,
            default=0.0,
            predicate=prewindow,
        ),
        "event_credit_advantage_positive_frac_prewindow": row_sign_frac(
            "policy_event_advantage",
            prewindow,
            positive=True,
        ),
        "event_credit_advantage_negative_frac_prewindow": row_sign_frac(
            "policy_event_advantage",
            prewindow,
            positive=False,
        ),
        "event_credit_advantage_mean_quality": row_stat(
            "policy_event_advantage",
            np.mean,
            default=0.0,
            predicate=quality_window,
        ),
        "event_credit_advantage_positive_frac_quality": row_sign_frac(
            "policy_event_advantage",
            quality_window,
            positive=True,
        ),
        "event_credit_advantage_negative_frac_quality": row_sign_frac(
            "policy_event_advantage",
            quality_window,
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
                if int(row.get("step", 0)) > 0
                and int(row.get("policy_event_mask_fire_once", 0) or 0) > 0
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
            sum(
                int(row.get("fire_once_requested", 0) or 0)
                for row in rows
                if int(row.get("step", 0)) > 0
            )
        ),
        "fire_once_accepted_count": int(
            sum(
                int(row.get("fire_once_accepted", 0) or 0)
                for row in rows
                if int(row.get("step", 0)) > 0
            )
        ),
        "fire_once_rejected_count": int(
            sum(
                int(row.get("fire_once_rejected", 0) or 0)
                for row in rows
                if int(row.get("step", 0)) > 0
            )
        ),
        "release_executed_count": int(
            sum(
                int(row.get("release_executed", 0) or 0)
                for row in rows
                if int(row.get("step", 0)) > 0
            )
        ),
        "post_launch_suppressed_count": int(
            sum(
                int(row.get("post_launch_suppressed", 0) or 0)
                for row in rows
                if int(row.get("step", 0)) > 0
            )
        ),
        "fire_once_rejected_reason_counts": dict(sorted(rejection_reason_counts.items())),
        "engagement_state_counts": dict(sorted(engagement_state_counts.items())),
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
            "unknown": int(unknown_release_count),
        },
        "repeat_release_before_assessment_count": int(
            sum(int(row.get("c2_roe_premature_second_shot", 0) or 0) for row in rows)
            + pending_assessment_release_count
        ),
        "pending_assessment_after_launch": bool(
            any(
                int(row.get("pending_assessment", 0) or 0) > 0
                and int(row.get("missile_release", 0) or 0) > 0
                for row in rows
            )
        ),
        "pending_assessment_release_count": int(pending_assessment_release_count),
        "shot_budget_violation_count": int(
            sum(int(row.get("c2_roe_shot_budget_violation", 0) or 0) for row in rows)
        ),
        "authorized_salvo_release_count": int(
            sum(int(row.get("c2_roe_authorized_salvo_release_count", 0) or 0) for row in rows)
        ),
        "authorized_reattack_release_count": int(
            sum(int(row.get("c2_roe_authorized_reattack_release_count", 0) or 0) for row in rows)
        ),
        "release_steps": release_steps,
        "min_release_interval_steps": min(release_intervals) if release_intervals else None,
        "effects_event_count": int(final.get("effects_event_count", 0)),
        "damage_report_count": int(final.get("damage_report_count", 0)),
        "lethality_chain_row_count": int(chain_snapshot.get("lethality_chain_row_count", 0) or 0),
        "lethality_chain_chain_count": int(
            chain_snapshot.get("lethality_chain_chain_count", 0) or 0
        ),
        "lethality_chain_stages_json": str(
            chain_snapshot.get("lethality_chain_stages_json", "[]") or "[]"
        ),
        "lethality_chain_miss_distance_m": float(
            chain_snapshot.get("lethality_chain_miss_distance_m", float("nan"))
        ),
        "lethality_chain_nearest_approach_time_s": float(
            chain_snapshot.get("lethality_chain_nearest_approach_time_s", float("nan"))
        ),
        "lethality_chain_local_forward_m": float(
            chain_snapshot.get("lethality_chain_local_forward_m", float("nan"))
        ),
        "lethality_chain_local_right_m": float(
            chain_snapshot.get("lethality_chain_local_right_m", float("nan"))
        ),
        "lethality_chain_local_up_m": float(
            chain_snapshot.get("lethality_chain_local_up_m", float("nan"))
        ),
        "lethality_chain_local_norm_m": float(
            chain_snapshot.get("lethality_chain_local_norm_m", float("nan"))
        ),
        "lethality_chain_closure_mps": float(
            chain_snapshot.get("lethality_chain_closure_mps", float("nan"))
        ),
        "lethality_chain_aspect_bucket": str(
            chain_snapshot.get("lethality_chain_aspect_bucket", "")
        ),
        "lethality_chain_fuze_type": str(chain_snapshot.get("lethality_chain_fuze_type", "")),
        "lethality_chain_fuze_armed": bool(
            int(chain_snapshot.get("lethality_chain_fuze_armed", 0) or 0)
        ),
        "lethality_chain_fuze_triggered": bool(
            int(chain_snapshot.get("lethality_chain_fuze_triggered", 0) or 0)
        ),
        "lethality_chain_fuze_failure_reason": str(
            chain_snapshot.get("lethality_chain_fuze_failure_reason", "")
        ),
        "lethality_chain_fuze_delay_s": float(
            chain_snapshot.get("lethality_chain_fuze_delay_s", float("nan"))
        ),
        "lethality_chain_fuze_reliability": float(
            chain_snapshot.get("lethality_chain_fuze_reliability", float("nan"))
        ),
        "lethality_chain_fuze_sample": float(
            chain_snapshot.get("lethality_chain_fuze_sample", float("nan"))
        ),
        "lethality_chain_fuze_expected_detonation_probability": float(
            chain_snapshot.get(
                "lethality_chain_fuze_expected_detonation_probability",
                float("nan"),
            )
        ),
        "lethality_chain_fuze_sampled_outcome": bool(
            int(chain_snapshot.get("lethality_chain_fuze_sampled_outcome", 0) or 0)
        ),
        "lethality_chain_fuze_trigger_radius_m": float(
            chain_snapshot.get("lethality_chain_fuze_trigger_radius_m", float("nan"))
        ),
        "lethality_chain_fuze_sensor_opportunity_source": str(
            chain_snapshot.get("lethality_chain_fuze_sensor_opportunity_source", "")
        ),
        "lethality_chain_fuze_sensor_opportunity_score": float(
            chain_snapshot.get("lethality_chain_fuze_sensor_opportunity_score", float("nan"))
        ),
        "lethality_chain_fuze_terminal_track_valid": bool(
            int(chain_snapshot.get("lethality_chain_fuze_terminal_track_valid", 0) or 0)
        ),
        "lethality_chain_fuze_target_detected": bool(
            int(chain_snapshot.get("lethality_chain_fuze_target_detected", 0) or 0)
        ),
        "lethality_chain_fuze_target_detection_source": str(
            chain_snapshot.get("lethality_chain_fuze_target_detection_source", "")
        ),
        "lethality_chain_fuze_target_detection_confidence": float(
            chain_snapshot.get("lethality_chain_fuze_target_detection_confidence", float("nan"))
        ),
        "lethality_chain_fuze_target_detection_threshold": float(
            chain_snapshot.get("lethality_chain_fuze_target_detection_threshold", float("nan"))
        ),
        "lethality_chain_detonation_point_source": str(
            chain_snapshot.get("lethality_chain_detonation_point_source", "")
        ),
        "lethality_chain_fuze_mechanism_coverage_score": float(
            chain_snapshot.get("lethality_chain_fuze_mechanism_coverage_score", float("nan"))
        ),
        "lethality_chain_direct_hitbox_intersection": bool(
            int(chain_snapshot.get("lethality_chain_direct_hitbox_intersection", 0) or 0)
        ),
        "lethality_chain_projected_hitbox_count": int(
            chain_snapshot.get("lethality_chain_projected_hitbox_count", 0) or 0
        ),
        "lethality_chain_component_hit_count": int(
            chain_snapshot.get("lethality_chain_component_hit_count", 0) or 0
        ),
        "lethality_chain_component_name": str(
            chain_snapshot.get("lethality_chain_component_name", "")
        ),
        "lethality_chain_component_system": str(
            chain_snapshot.get("lethality_chain_component_system", "")
        ),
        "lethality_chain_component_load_source": str(
            chain_snapshot.get("lethality_chain_component_load_source", "")
        ),
        "lethality_chain_rod_cut_margin": float(
            chain_snapshot.get("lethality_chain_rod_cut_margin", float("nan"))
        ),
        "lethality_chain_component_rod_cut_margin": float(
            chain_snapshot.get("lethality_chain_component_rod_cut_margin", float("nan"))
        ),
        "lethality_chain_component_damage_count": int(
            chain_snapshot.get("lethality_chain_component_damage_count", 0) or 0
        ),
        "lethality_chain_component_damage_name": str(
            chain_snapshot.get("lethality_chain_component_damage_name", "")
        ),
        "lethality_chain_component_damage_system": str(
            chain_snapshot.get("lethality_chain_component_damage_system", "")
        ),
        "lethality_chain_component_integrity_before": float(
            chain_snapshot.get("lethality_chain_component_integrity_before", float("nan"))
        ),
        "lethality_chain_component_integrity_after": float(
            chain_snapshot.get("lethality_chain_component_integrity_after", float("nan"))
        ),
        "lethality_chain_component_failure_mode": str(
            chain_snapshot.get("lethality_chain_component_failure_mode", "")
        ),
        "lethality_chain_component_failure_severity": float(
            chain_snapshot.get("lethality_chain_component_failure_severity", float("nan"))
        ),
        "lethality_chain_component_failure_probability": float(
            chain_snapshot.get("lethality_chain_component_failure_probability", float("nan"))
        ),
        "lethality_chain_component_failure_sample": float(
            chain_snapshot.get("lethality_chain_component_failure_sample", float("nan"))
        ),
        "lethality_chain_damage_report_id": int(
            chain_snapshot.get("lethality_chain_damage_report_id", 0) or 0
        ),
        "lethality_chain_system_health_delta": float(
            chain_snapshot.get("lethality_chain_system_health_delta", float("nan"))
        ),
        "lethality_chain_mission_capability_before": float(
            chain_snapshot.get("lethality_chain_mission_capability_before", float("nan"))
        ),
        "lethality_chain_mission_capability_after": float(
            chain_snapshot.get("lethality_chain_mission_capability_after", float("nan"))
        ),
        "lethality_chain_mission_capability_delta": float(
            chain_snapshot.get("lethality_chain_mission_capability_delta", float("nan"))
        ),
        "lethality_chain_mobility_capability_before": float(
            chain_snapshot.get("lethality_chain_mobility_capability_before", float("nan"))
        ),
        "lethality_chain_mobility_capability_after": float(
            chain_snapshot.get("lethality_chain_mobility_capability_after", float("nan"))
        ),
        "lethality_chain_mobility_capability_delta": float(
            chain_snapshot.get("lethality_chain_mobility_capability_delta", float("nan"))
        ),
        "lethality_chain_sensor_capability_before": float(
            chain_snapshot.get("lethality_chain_sensor_capability_before", float("nan"))
        ),
        "lethality_chain_sensor_capability_after": float(
            chain_snapshot.get("lethality_chain_sensor_capability_after", float("nan"))
        ),
        "lethality_chain_sensor_capability_delta": float(
            chain_snapshot.get("lethality_chain_sensor_capability_delta", float("nan"))
        ),
        "lethality_chain_survivability_margin_before": float(
            chain_snapshot.get("lethality_chain_survivability_margin_before", float("nan"))
        ),
        "lethality_chain_survivability_margin_after": float(
            chain_snapshot.get("lethality_chain_survivability_margin_after", float("nan"))
        ),
        "lethality_chain_survivability_margin_delta": float(
            chain_snapshot.get("lethality_chain_survivability_margin_delta", float("nan"))
        ),
        "lethality_chain_control_delta": float(
            chain_snapshot.get("lethality_chain_control_delta", float("nan"))
        ),
        "lethality_chain_engine_delta": float(
            chain_snapshot.get("lethality_chain_engine_delta", float("nan"))
        ),
        "lethality_chain_fuel_leak_delta": float(
            chain_snapshot.get("lethality_chain_fuel_leak_delta", float("nan"))
        ),
        "lethality_chain_fire_state": str(chain_snapshot.get("lethality_chain_fire_state", "")),
        "lethality_chain_aircraft_damage_state_before": str(
            chain_snapshot.get("lethality_chain_aircraft_damage_state_before", "")
        ),
        "lethality_chain_aircraft_damage_state_after": str(
            chain_snapshot.get("lethality_chain_aircraft_damage_state_after", "")
        ),
        "lethality_chain_aircraft_damage_state_delta": str(
            chain_snapshot.get("lethality_chain_aircraft_damage_state_delta", "")
        ),
        "lethality_chain_air_system_hit_flags": str(
            chain_snapshot.get("lethality_chain_air_system_hit_flags", "")
        ),
        "lethality_chain_air_system_spatial_scales": str(
            chain_snapshot.get("lethality_chain_air_system_spatial_scales", "")
        ),
        "lethality_chain_vulnerability_scale_trace": str(
            chain_snapshot.get("lethality_chain_vulnerability_scale_trace", "")
        ),
        "lethality_chain_mission_kill": bool(
            int(chain_snapshot.get("lethality_chain_mission_kill", 0) or 0)
        ),
        "lethality_chain_mobility_kill": bool(
            int(chain_snapshot.get("lethality_chain_mobility_kill", 0) or 0)
        ),
        "lethality_chain_sensor_kill": bool(
            int(chain_snapshot.get("lethality_chain_sensor_kill", 0) or 0)
        ),
        "lethality_chain_destroyed": bool(
            int(chain_snapshot.get("lethality_chain_destroyed", 0) or 0)
        ),
        "lethality_chain_loss_state": str(chain_snapshot.get("lethality_chain_loss_state", "")),
        "lethality_chain_lifecycle_count": int(
            chain_snapshot.get("lethality_chain_lifecycle_count", 0) or 0
        ),
        "lethality_chain_lifecycle_from": str(
            chain_snapshot.get("lethality_chain_lifecycle_from", "")
        ),
        "lethality_chain_lifecycle_to": str(
            chain_snapshot.get("lethality_chain_lifecycle_to", "")
        ),
        "lethality_chain_ground_lifecycle": str(
            chain_snapshot.get("lethality_chain_ground_lifecycle", "")
        ),
        "lethality_chain_wreck_entity_id": int(
            chain_snapshot.get("lethality_chain_wreck_entity_id", 0) or 0
        ),
        "lethality_chain_debris_count": int(
            chain_snapshot.get("lethality_chain_debris_count", 0) or 0
        ),
        "lethality_chain_lifecycle_terminal": bool(
            int(chain_snapshot.get("lethality_chain_lifecycle_terminal", 0) or 0)
        ),
        "lethality_chain_terminal_projection_id": int(
            chain_snapshot.get("lethality_chain_terminal_projection_id", 0) or 0
        ),
    }
