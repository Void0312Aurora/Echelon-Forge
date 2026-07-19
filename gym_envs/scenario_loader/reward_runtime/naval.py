from __future__ import annotations

import math
from typing import Any

import numpy as np

from python.tasking_contracts.bridge_views import mission_command_dict


def _is_naval_profile(loader: Any) -> bool:
    scenario = getattr(loader, "scenario_data", {}) if loader is not None else {}
    mission = mission_command_dict(loader) if loader is not None else {}
    task = getattr(loader, "task_order", None)
    candidates = [
        scenario.get("tasking_profile") if isinstance(scenario, dict) else None,
        mission.get("tasking_profile") if isinstance(mission, dict) else None,
        getattr(task, "tasking_profile", None),
        getattr(task, "service_profile", None),
    ]
    for value in candidates:
        text = str(value).strip().lower()
        if text in {"naval", "navy"} or "navy" in text:
            return True
    return False


def _cfg_float(cfg: dict[str, Any], name: str, default: float) -> float:
    try:
        return float(cfg.get(name, default))
    except Exception:
        return float(default)


def _add_term(rb: dict[str, float], name: str, value: float) -> float:
    v = float(value)
    if v != 0.0:
        rb[name] = float(rb.get(name, 0.0) + v)
    return v


def _entity_position(sim: Any, entity_id: int) -> tuple[float, float] | None:
    if sim is None or entity_id <= 0:
        return None
    try:
        pos = sim.get_unit_position(int(entity_id))
    except Exception:
        return None
    if pos is None or len(pos) < 2:
        return None
    return float(pos[0]), float(pos[1])


def _target_track(truth: Any, target_id: int) -> Any | None:
    if truth is None or target_id <= 0:
        return None
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


def _support_entity_ids(loader: Any) -> list[int]:
    agent_id = int(getattr(loader, "agent_id", 0) or 0)
    out: list[int] = []
    for member in list(getattr(loader, "active_roster", []) or []):
        try:
            entity_id = int(getattr(member, "entity_id", 0) or 0)
            if entity_id <= 0 or entity_id == agent_id:
                continue
            reference_id = int(getattr(member, "reference_entity_id", 0) or 0)
            if reference_id == agent_id or not bool(getattr(member, "is_agent", True)):
                out.append(entity_id)
        except Exception:
            continue
    return out


def _support_has_target_track(sim: Any, support_ids: list[int], target_id: int) -> bool:
    if sim is None or target_id <= 0:
        return False
    for entity_id in support_ids:
        try:
            obs = sim.get_agent_observation(int(entity_id))
        except Exception:
            continue
        if _target_track(obs, target_id) is not None:
            return True
    return False


def _support_has_shared_target_track(sim: Any, support_ids: list[int], target_id: int) -> bool:
    if sim is None or target_id <= 0:
        return False
    for entity_id in support_ids:
        try:
            obs = sim.get_agent_observation(int(entity_id))
        except Exception:
            continue
        track = _target_track(obs, target_id)
        if track is None:
            continue
        try:
            if int(getattr(track, "source", 0)) == 3:
                return True
        except Exception:
            continue
    return False


def _support_received_target_report(sim: Any, support_ids: list[int], target_id: int) -> bool:
    if sim is None or target_id <= 0:
        return False
    if not hasattr(sim, "get_unit_messages"):
        return False
    for entity_id in support_ids:
        try:
            messages = list(sim.get_unit_messages(int(entity_id)))
        except Exception:
            continue
        for msg in messages:
            try:
                if int(getattr(msg, "entity_ref", 0)) == int(target_id):
                    return True
            except Exception:
                continue
    return False


def _station_reward_terms(loader: Any, sim: Any, truth: Any, cfg: dict[str, Any]) -> tuple[float, dict[str, float], float]:
    task = getattr(loader, "task_order", None)
    if task is None or truth is None:
        return 0.0, {}, 0.0

    agent_id = int(getattr(loader, "agent_id", 0) or 0)
    support_ids = _support_entity_ids(loader)
    if not support_ids:
        return 0.0, {}, 0.0

    ref_pos = _entity_position(sim, support_ids[0])
    if ref_pos is None:
        return 0.0, {}, 0.0

    station_radius_m = max(
        1.0,
        float(getattr(loader, "_naval_station3_eval_radius_m", getattr(task, "station_radius_m", 0.0)) or 0.0),
    )
    station_heading_deg = float(
        getattr(loader, "_naval_station3_eval_heading_deg", getattr(task, "station_heading_deg", 0.0)) or 0.0
    )
    heading_rad = math.radians(station_heading_deg)
    desired_x = float(ref_pos[0]) + math.sin(heading_rad) * station_radius_m
    desired_y = float(ref_pos[1]) + math.cos(heading_rad) * station_radius_m
    own_x = float(getattr(truth, "x", 0.0))
    own_y = float(getattr(truth, "y", 0.0))
    station_error_m = math.hypot(desired_x - own_x, desired_y - own_y)

    terms: dict[str, float] = {}
    reward = 0.0
    norm_m = max(1.0, _cfg_float(cfg, "naval_station_error_norm_m", 1000.0))
    clip = max(0.0, _cfg_float(cfg, "naval_station_error_clip", 4.0))
    error_norm = station_error_m / norm_m
    if clip > 0.0:
        error_norm = min(error_norm, clip)
    reward += _add_term(
        terms,
        "naval_station_error_penalty",
        -abs(_cfg_float(cfg, "naval_station_error_weight", 0.04)) * error_norm,
    )

    band_m = max(0.0, _cfg_float(cfg, "naval_station_band_m", 750.0))
    if band_m > 0.0 and station_error_m <= band_m:
        reward += _add_term(terms, "naval_station_band_bonus", _cfg_float(cfg, "naval_station_band_bonus", 0.04))

    recovery_weight = max(0.0, _cfg_float(cfg, "naval_station_recovery_progress_weight", 0.0))
    last_station_error = getattr(loader, "_naval_reward_last_station_error_m", None)
    if recovery_weight > 0.0 and last_station_error is not None:
        try:
            progress_m = max(0.0, float(last_station_error) - float(station_error_m))
        except Exception:
            progress_m = 0.0
        progress_norm_m = max(1.0, _cfg_float(cfg, "naval_station_recovery_progress_norm_m", 100.0))
        progress_clip = max(0.0, _cfg_float(cfg, "naval_station_recovery_progress_clip", 1.0))
        progress_norm = progress_m / progress_norm_m
        if progress_clip > 0.0:
            progress_norm = min(progress_norm, progress_clip)
        reward += _add_term(terms, "naval_station_recovery_progress_bonus", recovery_weight * progress_norm)
    setattr(loader, "_naval_reward_last_station_error_m", float(station_error_m))

    own_ref_sep_m = math.hypot(own_x - float(ref_pos[0]), own_y - float(ref_pos[1]))
    sep_error_m = abs(own_ref_sep_m - station_radius_m)
    sep_norm = sep_error_m / max(1.0, _cfg_float(cfg, "naval_screen_separation_norm_m", 1000.0))
    sep_clip = max(0.0, _cfg_float(cfg, "naval_screen_separation_clip", 4.0))
    if sep_clip > 0.0:
        sep_norm = min(sep_norm, sep_clip)
    reward += _add_term(
        terms,
        "naval_screen_separation_penalty",
        -abs(_cfg_float(cfg, "naval_screen_separation_weight", 0.02)) * sep_norm,
    )

    _ = agent_id
    return reward, terms, station_error_m


def _naval_station_action_penalty_terms(loader: Any, cfg: dict[str, Any]) -> tuple[float, dict[str, float]]:
    action = getattr(loader, "_naval_station3_last_action", None)
    if action is None:
        return 0.0, {}
    arr = np.asarray(action, dtype=np.float32).reshape(-1)
    if arr.size != 3:
        return 0.0, {}

    terms: dict[str, float] = {}
    reward = 0.0
    bearing_weight = abs(_cfg_float(cfg, "naval_station_action_bearing_weight", 0.0))
    radius_weight = abs(_cfg_float(cfg, "naval_station_action_radius_weight", 0.0))
    speed_weight = abs(_cfg_float(cfg, "naval_station_action_speed_weight", 0.0))
    total_weight = abs(_cfg_float(cfg, "naval_station_action_weight", 0.0))

    if bearing_weight > 0.0:
        reward += _add_term(terms, "naval_station_action_bearing_penalty", -bearing_weight * abs(float(arr[0])))
    if radius_weight > 0.0:
        reward += _add_term(terms, "naval_station_action_radius_penalty", -radius_weight * abs(float(arr[1])))
    if speed_weight > 0.0:
        reward += _add_term(terms, "naval_station_action_speed_penalty", -speed_weight * abs(float(arr[2])))
    if total_weight > 0.0:
        norm = min(1.0, float(np.linalg.norm(arr, ord=2) / math.sqrt(3.0)))
        reward += _add_term(terms, "naval_station_action_penalty", -total_weight * norm)

    return reward, terms


def apply_naval_reward_surface(
    loader: Any,
    sim: Any,
    truth: Any,
    *,
    reward: float,
    terminated: bool,
    truncated: bool,
    status: list[float],
    reward_breakdown: dict | None,
) -> tuple[float, bool, bool, list[float], dict[str, float], str | None]:
    cfg = loader.get_rewards_config() if hasattr(loader, "get_rewards_config") else {}
    cfg = cfg if isinstance(cfg, dict) else {}
    naval_profile = _is_naval_profile(loader)
    if naval_profile and bool(cfg.get("naval_suppress_off_runway_penalty", False)):
        raise RuntimeError(
            "naval_suppress_off_runway_penalty is retired; naval profiles must disable "
            "runway/off-runway interpretation before safety rewards are built instead "
            "of cancelling off_runway_penalty afterward."
        )
    if not naval_profile or not bool(cfg.get("naval_reward_enabled", False)):
        return float(reward), bool(terminated), bool(truncated), status, dict(reward_breakdown or {}), None

    next_reward = float(reward)
    rb = {str(key): float(value) for key, value in dict(reward_breakdown or {}).items()}

    station_reward, station_terms, station_error_m = _station_reward_terms(loader, sim, truth, cfg)
    next_reward += station_reward
    for name, value in station_terms.items():
        _add_term(rb, name, value)

    action_reward, action_terms = _naval_station_action_penalty_terms(loader, cfg)
    next_reward += action_reward
    for name, value in action_terms.items():
        _add_term(rb, name, value)

    target_id = int(getattr(loader, "primary_target_id", 0) or 0)
    target_track = _target_track(truth, target_id)
    contact_seen = target_track is not None
    support_ids = _support_entity_ids(loader)
    shared_seen = _support_has_target_track(sim, support_ids, target_id)
    report_seen = _support_received_target_report(sim, support_ids, target_id)
    if not report_seen and not hasattr(sim, "get_unit_messages"):
        report_seen = _support_has_shared_target_track(sim, support_ids, target_id)

    if contact_seen:
        next_reward += _add_term(rb, "naval_contact_maintained_bonus", _cfg_float(cfg, "naval_contact_maintained_bonus", 0.01))
        if not bool(getattr(loader, "_naval_reward_contact_acquired", False)):
            loader._naval_reward_contact_acquired = True
            next_reward += _add_term(rb, "naval_contact_acquired_bonus", _cfg_float(cfg, "naval_contact_acquired_bonus", 0.08))
    if shared_seen:
        next_reward += _add_term(rb, "naval_shared_track_bonus", _cfg_float(cfg, "naval_shared_track_bonus", 0.015))
        if not bool(getattr(loader, "_naval_reward_shared_track_seen", False)):
            loader._naval_reward_shared_track_seen = True
            next_reward += _add_term(rb, "naval_shared_track_first_bonus", _cfg_float(cfg, "naval_shared_track_first_bonus", 0.08))
    if report_seen and not bool(getattr(loader, "_naval_reward_report_chain_seen", False)):
        loader._naval_reward_report_chain_seen = True
        next_reward += _add_term(rb, "naval_report_chain_bonus", _cfg_float(cfg, "naval_report_chain_bonus", 0.15))

    mission = mission_command_dict(loader)
    authorization_to_fire = bool(mission.get("authorization_to_fire", False)) if isinstance(mission, dict) else False
    roe_state = int(mission.get("roe_state", 0) or 0) if isinstance(mission, dict) else 0
    assigned_target_id = int(mission.get("assigned_target_id", target_id) or 0) if isinstance(mission, dict) else target_id
    if roe_state > 0 and assigned_target_id == target_id and not authorization_to_fire:
        next_reward += _add_term(rb, "naval_pre_fire_roe_hold_bonus", _cfg_float(cfg, "naval_pre_fire_roe_hold_bonus", 0.01))
    elif authorization_to_fire:
        next_reward += _add_term(
            rb,
            "naval_pre_fire_authorization_penalty",
            -abs(_cfg_float(cfg, "naval_pre_fire_authorization_penalty", 1.0)),
        )

    if len(status) >= 4:
        status[0] = float(station_error_m)
        status[1] = 1.0 if contact_seen else 0.0
        status[2] = 1.0 if report_seen else (0.5 if shared_seen else 0.0)

    return next_reward, bool(terminated), bool(truncated), status, rb, None
