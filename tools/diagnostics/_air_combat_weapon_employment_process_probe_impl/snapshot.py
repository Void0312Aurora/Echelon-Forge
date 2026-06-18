"""Per-step snapshot rows for the process probe."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from gym_envs.scenario_loader.reward_runtime.air_combat import air_combat_c2_roe_state_from_mapping
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_chain import (
    _lethality_chain_rows,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_snapshot import (
    _lethality_chain_snapshot_columns,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.probe_env import _base_env
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    ACTION_SIGNAL_NAMES,
    _a5_event_info_columns,
    _action_columns_for_mode,
    _c2_roe_event_columns,
    _damage_consequence_reward_columns,
    _distance_m,
    _finite_float,
    _health_current,
    _mission_command_dict,
    _target_track,
    _unit_id_set,
    _weapon_select_id,
)


def _controlled_consequence_bridge_record(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode": int(summary.get("episode", 0) or 0),
        "first_release_step": summary.get("first_release_step"),
        "first_effects_event_step": summary.get("first_effects_event_step"),
        "first_damage_report_step": summary.get("first_damage_report_step"),
        "first_damage_consequence_reward_step": summary.get("first_damage_consequence_reward_step"),
        "target_damage_consequence_reward_total": float(
            summary.get("target_damage_consequence_reward_total", 0.0) or 0.0
        ),
        "self_damage_consequence_reward_total": float(
            summary.get("self_damage_consequence_reward_total", 0.0) or 0.0
        ),
        "damage_consequence_reward_total": float(
            summary.get("damage_consequence_reward_total", 0.0) or 0.0
        ),
        "effects_event_count": int(summary.get("effects_event_count", 0) or 0),
        "damage_report_count": int(summary.get("damage_report_count", 0) or 0),
        "lethality_chain_row_count": int(summary.get("lethality_chain_row_count", 0) or 0),
        "lethality_chain_chain_count": int(summary.get("lethality_chain_chain_count", 0) or 0),
        "lethality_chain_stages_json": str(
            summary.get("lethality_chain_stages_json", "[]") or "[]"
        ),
    }


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
    range_track = (
        _finite_float(getattr(target_track, "range", float("nan")))
        if target_track is not None
        else float("nan")
    )
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
    sim_time_s = _finite_float(getattr(truth, "sim_time", step * sim.get_time_step()))
    lethality_chain_rows = _lethality_chain_rows(
        episode=int(episode),
        step=int(step),
        sim_time_s=float(sim_time_s),
        engagement_events=engagement_events,
    )

    row: dict[str, Any] = {
        "episode": int(episode),
        "step": int(step),
        "sim_time_s": float(sim_time_s),
        "reward": float(reward),
        "total_reward_term": _finite_float(reward_terms.get("total", float("nan")))
        if isinstance(reward_terms, dict)
        else float("nan"),
        "combat_win_bonus": _finite_float(reward_terms.get("combat_win_bonus", 0.0))
        if isinstance(reward_terms, dict)
        else 0.0,
        "terminated": int(bool(terminated)),
        "truncated": int(bool(truncated)),
        "termination_reason": str(info.get("termination_reason", ""))
        if isinstance(info, dict)
        else "",
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
            _finite_float(getattr(target_track, "closing_speed", float("nan")))
            if target_track is not None
            else float("nan")
        ),
        "target_track_age_s": (
            _finite_float(getattr(target_track, "time_since_update", float("nan")))
            if target_track is not None
            else float("nan")
        ),
        "effects_event_count": int(len(effects_events)),
        "damage_report_count": int(len(damage_reports)),
    }
    row.update(_lethality_chain_snapshot_columns(lethality_chain_rows))
    row.update(_damage_consequence_reward_columns(reward_terms))
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
        row["effective_action_weapon_select_id"] = _weapon_select_id(
            effective_flat, action_mode=action_mode
        )
        radar_idx = int(columns["radar_active"])
        master_idx = int(columns["master_arm"])
        fire_idx = int(columns["fire_weapon"])
        row["policy_action_radar_on"] = int(flat.size > radar_idx and flat[radar_idx] > 0.5)
        row["policy_action_master_arm_on"] = int(flat.size > master_idx and flat[master_idx] > 0.5)
        row["policy_action_fire_weapon_on"] = int(flat.size > fire_idx and flat[fire_idx] > 0.5)
        row["action_radar_on"] = int(
            effective_flat.size > radar_idx and effective_flat[radar_idx] > 0.5
        )
        row["action_master_arm_on"] = int(
            effective_flat.size > master_idx and effective_flat[master_idx] > 0.5
        )
        row["action_fire_weapon_on"] = int(
            effective_flat.size > fire_idx and effective_flat[fire_idx] > 0.5
        )
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


def _last_row_before_auto_reset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    previous_time = float("nan")
    for idx, row in enumerate(rows):
        sim_time = _finite_float(row.get("sim_time_s", float("nan")))
        if idx > 0 and math.isfinite(sim_time) and math.isfinite(previous_time):
            if sim_time + 1.0e-9 < previous_time:
                return rows[idx - 1]
        if math.isfinite(sim_time):
            previous_time = sim_time
    return rows[-1]
