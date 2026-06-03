from __future__ import annotations

import math
from typing import Any


_DEFAULT_TERMINAL_DAMAGE_STATES = {"lost", "mobility_kill", "mission_kill"}
_DAMAGE_DELTA_FIELDS = {"mission", "mobility", "sensor", "survivability"}
_LOSS_PROGRESS_BONUS_DEFAULTS = {
    "sensor_kill": 50.0,
    "mission_kill": 125.0,
    "mobility_kill": 125.0,
    "survivability_kill": 250.0,
    "lost": 250.0,
}
_C2_ROE_CONTRACT_FIELDS = {
    "wcs_state",
    "target_identity_state",
    "engage_order_state",
    "shot_policy_state",
    "shot_budget_remaining",
    "pending_assessment",
    "own_missiles_in_flight_count",
}
_C2_ROE_REWARD_KEYS = (
    "air_combat_roe_hold_fire_bonus",
    "air_combat_roe_hold_fire_violation_penalty",
    "air_combat_roe_unauthorized_fire_penalty",
    "air_combat_roe_authorized_radar_active_bonus",
    "air_combat_roe_authorized_tms_up_bonus",
    "air_combat_roe_authorized_master_arm_bonus",
    "air_combat_roe_authorized_weapon_selected_bonus",
    "air_combat_roe_authorized_fire_attempt_bonus",
    "air_combat_roe_authorized_fire_no_release_penalty",
    "air_combat_roe_authorized_fire_opportunity_penalty",
    "air_combat_roe_valid_authorized_release_bonus",
    "air_combat_roe_authorized_first_release_bonus",
    "air_combat_roe_pending_assessment_penalty",
    "air_combat_roe_premature_second_shot_penalty",
    "air_combat_roe_shot_budget_violation_penalty",
    "air_combat_roe_authorized_salvo_bonus",
    "air_combat_roe_authorized_reattack_bonus",
)
_C2_ROE_HOLD_ENGAGE_STATES = {3, 4, 5, 6}


def _normalized_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return int(default)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    return bool(default)


def _loader_cfg(loader: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    rewards = loader.get_rewards_config() if hasattr(loader, "get_rewards_config") else {}
    rewards = rewards if isinstance(rewards, dict) else {}
    meta = getattr(loader, "_compiled_meta_cfg", {})
    meta = meta if isinstance(meta, dict) else {}
    return rewards, meta


def _cfg_value(loader: Any, name: str, default: Any = None) -> Any:
    rewards, meta = _loader_cfg(loader)
    if name in meta:
        return meta.get(name)
    return rewards.get(name, default)


def _cfg_float(loader: Any, name: str, default: float) -> float:
    try:
        return float(_cfg_value(loader, name, default))
    except Exception:
        return float(default)


def _add_term(rb: dict[str, float], name: str, value: float) -> float:
    v = float(value)
    if v != 0.0:
        rb[name] = float(rb.get(name, 0.0) + v)
    return v


def _add_once_term(loader: Any, rb: dict[str, float], name: str, value: float) -> float:
    awarded = getattr(loader, "_air_combat_c2_roe_reward_once_terms", None)
    if not isinstance(awarded, set):
        awarded = set()
        setattr(loader, "_air_combat_c2_roe_reward_once_terms", awarded)
    if name in awarded:
        return 0.0
    awarded.add(name)
    return _add_term(rb, name, value)


def is_air_combat_profile(loader: Any) -> bool:
    scenario = getattr(loader, "scenario_data", {}) if loader is not None else {}
    scenario = scenario if isinstance(scenario, dict) else {}
    realism = scenario.get("realism_gradient", {})
    realism = realism if isinstance(realism, dict) else {}
    mission = getattr(loader, "mission_cmd", {})
    mission = mission if isinstance(mission, dict) else {}
    source_path = str(getattr(loader, "_scenario_source_path", "") or "").lower()

    candidates = [
        scenario.get("domain"),
        scenario.get("tasking_profile"),
        scenario.get("scenario_name"),
        realism.get("domain"),
        realism.get("workline"),
        mission.get("tasking_profile"),
        source_path,
    ]
    for value in candidates:
        text = str(value or "").strip().lower()
        if text in {"air_combat", "air-combat"}:
            return True
        if "air_combat" in text or "air combat" in text:
            return True
    return False


def air_combat_damage_terminal_enabled(loader: Any) -> bool:
    explicit = _cfg_value(loader, "air_combat_damage_terminal_enabled", None)
    if explicit is None:
        explicit = _cfg_value(loader, "combat_damage_terminal_enabled", None)
    if explicit is not None:
        return _as_bool(explicit, True)
    return is_air_combat_profile(loader)


def air_combat_damage_shaping_enabled(loader: Any) -> bool:
    explicit = _cfg_value(loader, "air_combat_damage_shaping_enabled", None)
    if explicit is None:
        explicit = _cfg_value(loader, "combat_damage_shaping_enabled", None)
    if explicit is not None:
        return _as_bool(explicit, True)
    return is_air_combat_profile(loader)


def air_combat_release_shaping_enabled(loader: Any) -> bool:
    explicit = _cfg_value(loader, "air_combat_release_shaping_enabled", None)
    if explicit is not None:
        return _as_bool(explicit, False)
    return any(
        abs(_cfg_float(loader, key, 0.0)) > 0.0
        for key in (
            "air_combat_first_release_bonus",
            "air_combat_release_bonus",
            "air_combat_repeat_release_penalty",
            "air_combat_invalid_fire_penalty",
        )
    )


def air_combat_c2_roe_release_discipline_enabled(loader: Any) -> bool:
    explicit = _cfg_value(loader, "air_combat_c2_roe_release_discipline_enabled", None)
    if explicit is not None:
        return _as_bool(explicit, False)
    return any(abs(_cfg_float(loader, key, 0.0)) > 0.0 for key in _C2_ROE_REWARD_KEYS)


def air_combat_c2_roe_state_from_mapping(
    values: dict[str, Any] | None,
    *,
    target_id: int = 0,
    agent_id: int = 0,
) -> dict[str, Any]:
    data = values if isinstance(values, dict) else {}
    if "c2_roe_contract_present" in data:
        contract_present = _as_bool(data.get("c2_roe_contract_present"), False)
    else:
        contract_present = any(key in data for key in _C2_ROE_CONTRACT_FIELDS)

    roe_state = _as_int(data.get("roe_state", 0), 0)
    wcs_default = 1 if contract_present else roe_state
    wcs_state = _as_int(data.get("wcs_state", wcs_default), wcs_default)
    shot_policy_state = _as_int(data.get("shot_policy_state", 0), 0)
    engage_order_state = _as_int(data.get("engage_order_state", 0), 0)
    shot_budget_remaining = max(0, _as_int(data.get("shot_budget_remaining", 0), 0))
    authorization_to_fire = _as_bool(data.get("authorization_to_fire", False), False)
    assigned_target_id = _as_int(data.get("assigned_target_id", target_id), int(target_id or 0))

    return {
        "contract_present": bool(contract_present),
        "roe_state": int(roe_state),
        "wcs_state": int(wcs_state),
        "authorization_to_fire": bool(authorization_to_fire),
        "engage_order_state": int(engage_order_state),
        "shot_policy_state": int(shot_policy_state),
        "shot_budget_remaining": int(shot_budget_remaining),
        "pending_assessment": _as_bool(data.get("pending_assessment", False), False),
        "own_missiles_in_flight_count": _as_int(data.get("own_missiles_in_flight_count", 0), 0),
        "assigned_target_id": int(assigned_target_id),
        "agent_id": int(agent_id or 0),
    }


def air_combat_c2_roe_state_from_loader(loader: Any) -> dict[str, Any]:
    mission_cmd = getattr(loader, "mission_cmd", {})
    mission_cmd = mission_cmd if isinstance(mission_cmd, dict) else {}
    return air_combat_c2_roe_state_from_mapping(
        mission_cmd,
        target_id=int(getattr(loader, "primary_target_id", 0) or 0),
        agent_id=int(getattr(loader, "agent_id", 0) or 0),
    )


def classify_air_combat_c2_roe_event(
    state: dict[str, Any] | None,
    *,
    released: bool,
    fire_attempted: bool,
    previous_release_count: int = 0,
    release_ordinal: int = 0,
) -> dict[str, Any]:
    c2 = state if isinstance(state, dict) else {}
    contract_present = bool(c2.get("contract_present", False))
    roe_state = _as_int(c2.get("roe_state", 0), 0)
    wcs_state = _as_int(c2.get("wcs_state", 1 if contract_present else roe_state), 1 if contract_present else roe_state)
    shot_policy_state = _as_int(c2.get("shot_policy_state", 0), 0)
    engage_order_state = _as_int(c2.get("engage_order_state", 0), 0)
    shot_budget_remaining = max(0, _as_int(c2.get("shot_budget_remaining", 0), 0))
    pending_assessment = _as_bool(c2.get("pending_assessment", False), False)
    authorization_to_fire = _as_bool(c2.get("authorization_to_fire", False), False)
    release_number = max(0, int(previous_release_count or 0)) + max(0, int(release_ordinal or 0))

    event_happened = bool(released or fire_attempted)
    legacy_fallback_allowed = (not contract_present or wcs_state == 0) and roe_state in {0, 3}
    hold_order = bool(contract_present and (wcs_state == 1 or shot_policy_state == 0 or engage_order_state in _C2_ROE_HOLD_ENGAGE_STATES))
    authorized_candidate = bool(authorization_to_fire or legacy_fallback_allowed)

    bucket = "no_fire"
    if not event_happened:
        bucket = "hold_fire" if hold_order else "no_fire"
    elif hold_order:
        bucket = "hold_fire_violation"
    elif not authorized_candidate:
        bucket = "unauthorized_shot"
    elif contract_present and shot_budget_remaining <= int(release_ordinal or 0):
        bucket = "shot_budget_violation"
    elif contract_present and pending_assessment and shot_policy_state != 3:
        bucket = "pending_assessment_violation"
    elif contract_present and shot_policy_state == 1 and release_number > 0:
        bucket = "premature_second_shot"
    elif contract_present and shot_policy_state == 2:
        bucket = "authorized_salvo"
    elif contract_present and shot_policy_state == 3:
        bucket = "authorized_reattack"
    elif legacy_fallback_allowed and not contract_present:
        bucket = "legacy_roe_fallback"
    elif bool(released):
        bucket = "valid_authorized_release"
    else:
        bucket = "authorized_fire_attempt_no_release"

    authorized_release = bool(released and bucket in {
        "valid_authorized_release",
        "authorized_salvo",
        "authorized_reattack",
        "legacy_roe_fallback",
    })
    violation_release = bool(released and bucket in {
        "hold_fire_violation",
        "unauthorized_shot",
        "shot_budget_violation",
        "pending_assessment_violation",
        "premature_second_shot",
    })
    return {
        "bucket": bucket,
        "released": bool(released),
        "fire_attempted": bool(fire_attempted),
        "hold_fire": bool(hold_order),
        "hold_fire_obeyed": bool((not event_happened) and hold_order),
        "hold_fire_violation": bool(event_happened and bucket == "hold_fire_violation"),
        "unauthorized_shot": bool(event_happened and bucket == "unauthorized_shot"),
        "shot_budget_violation": bool(event_happened and bucket == "shot_budget_violation"),
        "pending_assessment_violation": bool(event_happened and bucket == "pending_assessment_violation"),
        "premature_second_shot": bool(event_happened and bucket == "premature_second_shot"),
        "authorized_release": bool(authorized_release),
        "violation_release": bool(violation_release),
        "valid_authorized_release": bool(released and bucket == "valid_authorized_release"),
        "authorized_first_release": bool(authorized_release and release_number == 0),
        "authorized_salvo": bool(released and bucket == "authorized_salvo"),
        "authorized_reattack": bool(released and bucket == "authorized_reattack"),
        "legacy_roe_fallback": bool(released and bucket == "legacy_roe_fallback"),
    }


def _terminal_damage_states(loader: Any) -> set[str]:
    raw = _cfg_value(loader, "air_combat_terminal_damage_states", None)
    if raw is None:
        raw = _cfg_value(loader, "combat_terminal_damage_states", None)
    if raw is None:
        return set(_DEFAULT_TERMINAL_DAMAGE_STATES)
    if isinstance(raw, str):
        values = [part for part in raw.replace(",", " ").split(" ") if part]
    elif isinstance(raw, (list, tuple, set)):
        values = list(raw)
    else:
        values = []
    states = {_normalized_token(value) for value in values if _normalized_token(value)}
    states.add("lost")
    return states


def _damage_report_terminal_reason(loader: Any, report: Any) -> str | None:
    loss_state = _normalized_token(getattr(report, "loss_state_to", ""))
    terminal_states = _terminal_damage_states(loader)
    if bool(getattr(report, "destroyed", False)) or loss_state == "lost":
        return "lost"
    if bool(getattr(report, "survivability_kill", False)):
        return "survivability_kill"
    if loss_state in terminal_states:
        return loss_state
    if bool(getattr(report, "mobility_kill", False)) and "mobility_kill" in terminal_states:
        return "mobility_kill"
    if bool(getattr(report, "mission_kill", False)) and "mission_kill" in terminal_states:
        return "mission_kill"
    if bool(getattr(report, "sensor_kill", False)) and "sensor_kill" in terminal_states:
        return "sensor_kill"
    return None


def _recent_damage_reports(sim: Any) -> list[Any]:
    if sim is None or not hasattr(sim, "export_recent_engagement_events"):
        return []
    try:
        events = sim.export_recent_engagement_events()
    except Exception:
        return []
    try:
        reports = list(getattr(events, "damage_reports", []) or [])
    except Exception:
        return []
    reports.sort(key=lambda report: int(getattr(report, "report_id", 0) or 0))
    return reports


def _parse_platform_damage_delta(value: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    text = str(value or "")
    for part in text.replace(";", ",").split(","):
        key, sep, raw = part.partition("=")
        if not sep:
            continue
        key = _normalized_token(key)
        if key not in _DAMAGE_DELTA_FIELDS:
            continue
        try:
            parsed = float(raw)
        except Exception:
            continue
        if not math.isfinite(parsed):
            continue
        out[key] = parsed
    return out


def _loss_progress_states(report: Any) -> set[str]:
    states: set[str] = set()
    from_state = _normalized_token(getattr(report, "loss_state_from", ""))
    to_state = _normalized_token(getattr(report, "loss_state_to", ""))
    if to_state and to_state != from_state and to_state != "combat_capable":
        states.add(to_state)
    if bool(getattr(report, "destroyed", False)):
        states.add("lost")
    if bool(getattr(report, "mission_kill", False)):
        states.add("mission_kill")
    if bool(getattr(report, "mobility_kill", False)):
        states.add("mobility_kill")
    if bool(getattr(report, "sensor_kill", False)):
        states.add("sensor_kill")
    if bool(getattr(report, "survivability_kill", False)):
        states.add("survivability_kill")
    return states


def _report_id(report: Any) -> int:
    try:
        return int(getattr(report, "report_id", 0) or 0)
    except Exception:
        return 0


def _report_target_id(report: Any) -> int:
    try:
        return int(getattr(getattr(report, "target", None), "entity_id", 0) or 0)
    except Exception:
        return 0


def _truth_missiles_remaining(truth: Any) -> int | None:
    try:
        value = int(getattr(truth, "missiles_remaining", -1))
    except Exception:
        return None
    return value if value >= 0 else None


def _last_fire_attempted(loader: Any) -> bool:
    return bool(_last_weapon_chain_state(loader).get("fire_attempted", False))


def _last_weapon_chain_state(loader: Any) -> dict[str, Any]:
    action = getattr(loader, "_last_effective_action", None)
    if action is None:
        return {
            "radar_active": False,
            "tms_up": False,
            "master_arm": False,
            "fire_attempted": False,
            "weapon_selected": False,
            "weapon_select_id": 0,
        }
    try:
        values = [float(v) for v in action]
    except Exception:
        values = []
    mode = str(getattr(loader, "_last_action_mode", "") or "")
    if mode == "air_combat_hybrid_v1":
        indices = {
            "radar_active": 6,
            "tms_up": 7,
            "master_arm": 8,
            "fire_attempted": 9,
            "weapon_select_id": 11,
        }
    else:
        indices = {
            "radar_active": 9,
            "tms_up": 12,
            "master_arm": 13,
            "fire_attempted": 14,
            "weapon_select_id": 16,
        }

    def _flag(name: str) -> bool:
        idx = int(indices[name])
        return bool(len(values) > idx and values[idx] > 0.5)

    weapon_idx = int(indices["weapon_select_id"])
    weapon_select_id = 0
    if len(values) > weapon_idx:
        try:
            weapon_select_id = max(0, int(round(float(values[weapon_idx]))))
        except Exception:
            weapon_select_id = 0
    return {
        "radar_active": _flag("radar_active"),
        "tms_up": _flag("tms_up"),
        "master_arm": _flag("master_arm"),
        "fire_attempted": _flag("fire_attempted"),
        "weapon_selected": bool(weapon_select_id > 0),
        "weapon_select_id": int(weapon_select_id),
    }


def _c2_roe_authorized_action_window(c2_state: dict[str, Any], *, previous_release_count: int) -> bool:
    contract_present = bool(c2_state.get("contract_present", False))
    roe_state = _as_int(c2_state.get("roe_state", 0), 0)
    wcs_state = _as_int(c2_state.get("wcs_state", 1 if contract_present else roe_state), 1 if contract_present else roe_state)
    shot_policy_state = _as_int(c2_state.get("shot_policy_state", 0), 0)
    engage_order_state = _as_int(c2_state.get("engage_order_state", 0), 0)
    shot_budget_remaining = max(0, _as_int(c2_state.get("shot_budget_remaining", 0), 0))
    pending_assessment = _as_bool(c2_state.get("pending_assessment", False), False)
    authorization_to_fire = _as_bool(c2_state.get("authorization_to_fire", False), False)

    legacy_fallback_allowed = (not contract_present or wcs_state == 0) and roe_state in {0, 3}
    hold_order = bool(contract_present and (wcs_state == 1 or shot_policy_state == 0 or engage_order_state in _C2_ROE_HOLD_ENGAGE_STATES))
    authorized_candidate = bool(authorization_to_fire or legacy_fallback_allowed)
    if hold_order or not authorized_candidate:
        return False
    if contract_present and shot_budget_remaining <= 0:
        return False
    if contract_present and pending_assessment and shot_policy_state != 3:
        return False
    if contract_present and shot_policy_state == 1 and int(previous_release_count or 0) > 0:
        return False
    return True


def _add_c2_roe_reward_terms(loader: Any, rb: dict[str, float], classification: dict[str, Any]) -> float:
    total = 0.0
    if bool(classification.get("hold_fire_obeyed", False)):
        total += _add_term(rb, "air_combat_roe_hold_fire_bonus", _cfg_float(loader, "air_combat_roe_hold_fire_bonus", 0.0))
    if bool(classification.get("hold_fire_violation", False)):
        total += _add_term(
            rb,
            "air_combat_roe_hold_fire_violation_penalty",
            _cfg_float(loader, "air_combat_roe_hold_fire_violation_penalty", 0.0),
        )
    if bool(classification.get("unauthorized_shot", False)):
        total += _add_term(
            rb,
            "air_combat_roe_unauthorized_fire_penalty",
            _cfg_float(loader, "air_combat_roe_unauthorized_fire_penalty", 0.0),
        )
    if bool(classification.get("shot_budget_violation", False)):
        total += _add_term(
            rb,
            "air_combat_roe_shot_budget_violation_penalty",
            _cfg_float(loader, "air_combat_roe_shot_budget_violation_penalty", 0.0),
        )
    if bool(classification.get("pending_assessment_violation", False)):
        total += _add_term(
            rb,
            "air_combat_roe_pending_assessment_penalty",
            _cfg_float(loader, "air_combat_roe_pending_assessment_penalty", 0.0),
        )
    if bool(classification.get("premature_second_shot", False)):
        total += _add_term(
            rb,
            "air_combat_roe_premature_second_shot_penalty",
            _cfg_float(loader, "air_combat_roe_premature_second_shot_penalty", 0.0),
        )
    if bool(classification.get("authorized_release", False)):
        total += _add_term(
            rb,
            "air_combat_roe_valid_authorized_release_bonus",
            _cfg_float(loader, "air_combat_roe_valid_authorized_release_bonus", 0.0),
        )
    if bool(classification.get("authorized_first_release", False)):
        total += _add_term(
            rb,
            "air_combat_roe_authorized_first_release_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_first_release_bonus", 0.0),
        )
    if bool(classification.get("authorized_salvo", False)):
        total += _add_term(
            rb,
            "air_combat_roe_authorized_salvo_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_salvo_bonus", 0.0),
        )
    if bool(classification.get("authorized_reattack", False)):
        total += _add_term(
            rb,
            "air_combat_roe_authorized_reattack_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_reattack_bonus", 0.0),
        )
    return total


def _add_c2_roe_authorized_action_terms(
    loader: Any,
    rb: dict[str, float],
    action_state: dict[str, Any],
    *,
    fire_attempted: bool,
) -> float:
    total = 0.0
    if bool(action_state.get("radar_active", False)):
        total += _add_once_term(
            loader,
            rb,
            "air_combat_roe_authorized_radar_active_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_radar_active_bonus", 0.0),
        )
    if bool(action_state.get("tms_up", False)):
        total += _add_once_term(
            loader,
            rb,
            "air_combat_roe_authorized_tms_up_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_tms_up_bonus", 0.0),
        )
    if bool(action_state.get("master_arm", False)):
        total += _add_once_term(
            loader,
            rb,
            "air_combat_roe_authorized_master_arm_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_master_arm_bonus", 0.0),
        )
    if bool(action_state.get("weapon_selected", False)):
        total += _add_once_term(
            loader,
            rb,
            "air_combat_roe_authorized_weapon_selected_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_weapon_selected_bonus", 0.0),
        )
    if bool(fire_attempted):
        total += _add_once_term(
            loader,
            rb,
            "air_combat_roe_authorized_fire_attempt_bonus",
            _cfg_float(loader, "air_combat_roe_authorized_fire_attempt_bonus", 0.0),
        )
        total += _add_term(
            rb,
            "air_combat_roe_authorized_fire_no_release_penalty",
            _cfg_float(loader, "air_combat_roe_authorized_fire_no_release_penalty", 0.0),
        )
    else:
        total += _add_term(
            rb,
            "air_combat_roe_authorized_fire_opportunity_penalty",
            _cfg_float(loader, "air_combat_roe_authorized_fire_opportunity_penalty", 0.0),
        )
    return total


def _apply_c2_roe_release_discipline(
    loader: Any,
    rb: dict[str, float],
    *,
    release_count: int,
    previous_release_count: int,
    fire_attempted: bool,
) -> float:
    c2_state = air_combat_c2_roe_state_from_loader(loader)
    action_state = _last_weapon_chain_state(loader)
    if int(release_count) > 0:
        total = 0.0
        for release_ordinal in range(int(release_count)):
            classification = classify_air_combat_c2_roe_event(
                c2_state,
                released=True,
                fire_attempted=bool(fire_attempted),
                previous_release_count=int(previous_release_count),
                release_ordinal=int(release_ordinal),
            )
            total += _add_c2_roe_reward_terms(loader, rb, classification)
        return total

    classification = classify_air_combat_c2_roe_event(
        c2_state,
        released=False,
        fire_attempted=bool(fire_attempted),
        previous_release_count=int(previous_release_count),
    )
    total = _add_c2_roe_reward_terms(loader, rb, classification)
    if _c2_roe_authorized_action_window(c2_state, previous_release_count=int(previous_release_count)):
        total += _add_c2_roe_authorized_action_terms(
            loader,
            rb,
            action_state,
            fire_attempted=bool(fire_attempted),
        )
    return total


def _apply_release_shaping(
    loader: Any,
    rb: dict[str, float],
    truth: Any,
    *,
    release_shaping_enabled: bool,
    c2_roe_shaping_enabled: bool,
) -> tuple[float, bool]:
    current_missiles = _truth_missiles_remaining(truth)
    if current_missiles is None:
        return 0.0, False

    previous_missiles = getattr(loader, "_air_combat_reward_prev_missiles", None)
    try:
        previous_missiles = None if previous_missiles is None else int(previous_missiles)
    except Exception:
        previous_missiles = None

    release_count = 0
    if previous_missiles is not None and previous_missiles >= 0:
        release_count = max(0, previous_missiles - int(current_missiles))
    setattr(loader, "_air_combat_reward_prev_missiles", int(current_missiles))

    total = 0.0
    fire_attempted = _last_fire_attempted(loader)
    if release_count > 0:
        previous_release_count = int(getattr(loader, "_air_combat_reward_release_count", 0) or 0)
        if bool(release_shaping_enabled):
            first_release_count = 1 if previous_release_count <= 0 else 0
            first_release_count = min(first_release_count, int(release_count))
            repeat_release_count = int(release_count) - int(first_release_count)

            first_bonus = _cfg_float(loader, "air_combat_first_release_bonus", 0.0)
            release_bonus = _cfg_float(loader, "air_combat_release_bonus", 0.0)
            repeat_penalty = _cfg_float(loader, "air_combat_repeat_release_penalty", 0.0)

            if first_release_count > 0 and first_bonus != 0.0:
                total += _add_term(rb, "air_combat_first_release_bonus", first_bonus * first_release_count)
            if release_bonus != 0.0:
                total += _add_term(rb, "air_combat_release_bonus", release_bonus * int(release_count))
            if repeat_release_count > 0 and repeat_penalty != 0.0:
                total += _add_term(
                    rb,
                    "air_combat_repeat_release_penalty",
                    repeat_penalty * int(repeat_release_count),
                )

        if bool(c2_roe_shaping_enabled):
            total += _apply_c2_roe_release_discipline(
                loader,
                rb,
                release_count=int(release_count),
                previous_release_count=int(previous_release_count),
                fire_attempted=bool(fire_attempted),
            )

        setattr(
            loader,
            "_air_combat_reward_release_count",
            int(previous_release_count) + int(release_count),
        )
        return total, True

    previous_release_count = int(getattr(loader, "_air_combat_reward_release_count", 0) or 0)
    invalid_fire_penalty = _cfg_float(loader, "air_combat_invalid_fire_penalty", 0.0)
    if bool(release_shaping_enabled) and invalid_fire_penalty != 0.0 and bool(fire_attempted):
        total += _add_term(rb, "air_combat_invalid_fire_penalty", invalid_fire_penalty)
    if bool(c2_roe_shaping_enabled):
        total += _apply_c2_roe_release_discipline(
            loader,
            rb,
            release_count=0,
            previous_release_count=int(previous_release_count),
            fire_attempted=bool(fire_attempted),
        )
    return total, False


def _apply_report_shaping(
    loader: Any,
    rb: dict[str, float],
    report: Any,
    *,
    role: str,
) -> float:
    sign = 1.0 if role == "target" else -1.0
    total = 0.0

    try:
        system_delta = float(getattr(report, "system_health_delta", 0.0) or 0.0)
    except Exception:
        system_delta = 0.0
    if math.isfinite(system_delta):
        magnitude = max(0.0, -system_delta)
        if magnitude > 0.0:
            default_scale = 10.0 if role == "target" else 10.0
            scale = abs(_cfg_float(loader, f"air_combat_{role}_system_damage_progress_scale", default_scale))
            total += _add_term(
                rb,
                f"air_combat_{role}_system_damage_{'progress' if role == 'target' else 'penalty'}",
                sign * magnitude * scale,
            )

    subsystem_scale = abs(_cfg_float(loader, f"air_combat_{role}_subsystem_progress_scale", 2.0))
    for field, delta in _parse_platform_damage_delta(getattr(report, "platform_damage_state_delta", "")).items():
        magnitude = max(0.0, -float(delta))
        if magnitude <= 0.0:
            continue
        scale = abs(_cfg_float(loader, f"air_combat_{role}_{field}_capability_progress_scale", subsystem_scale))
        total += _add_term(
            rb,
            f"air_combat_{role}_{field}_capability_{'progress' if role == 'target' else 'penalty'}",
            sign * magnitude * scale,
        )

    for state in sorted(_loss_progress_states(report)):
        default_bonus = _LOSS_PROGRESS_BONUS_DEFAULTS.get(state, 0.0)
        bonus = abs(_cfg_float(loader, f"air_combat_{role}_{state}_progress_bonus", default_bonus))
        if bonus <= 0.0:
            continue
        total += _add_term(
            rb,
            f"air_combat_{role}_{state}_{'progress' if role == 'target' else 'penalty'}",
            sign * bonus,
        )

    return total


def apply_air_combat_reward_surface(
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
    _ = truth
    rb = {str(key): float(value) for key, value in dict(reward_breakdown or {}).items()}
    release_shaping_enabled = air_combat_release_shaping_enabled(loader)
    c2_roe_shaping_enabled = air_combat_c2_roe_release_discipline_enabled(loader)
    damage_shaping_enabled = air_combat_damage_shaping_enabled(loader)
    if not release_shaping_enabled and not c2_roe_shaping_enabled and not damage_shaping_enabled:
        return float(reward), bool(terminated), bool(truncated), status, rb, None

    reports = _recent_damage_reports(sim)
    report_ids = [_report_id(report) for report in reports if _report_id(report) > 0]
    max_report_id = max(report_ids, default=0)
    last_report_id = int(getattr(loader, "_air_combat_reward_last_report_id", 0) or 0)
    if max_report_id > 0 and max_report_id < last_report_id:
        last_report_id = 0

    if bool(terminated):
        current_missiles = _truth_missiles_remaining(truth)
        if current_missiles is not None:
            setattr(loader, "_air_combat_reward_prev_missiles", int(current_missiles))
        if max_report_id > last_report_id:
            setattr(loader, "_air_combat_reward_last_report_id", int(max_report_id))
        return float(reward), bool(terminated), bool(truncated), status, rb, None

    agent_id = int(getattr(loader, "agent_id", 0) or 0)
    target_id = int(getattr(loader, "primary_target_id", 0) or 0)
    next_reward = float(reward)
    consumed_max_report_id = last_report_id

    if release_shaping_enabled or c2_roe_shaping_enabled:
        release_delta, _released = _apply_release_shaping(
            loader,
            rb,
            truth,
            release_shaping_enabled=bool(release_shaping_enabled),
            c2_roe_shaping_enabled=bool(c2_roe_shaping_enabled),
        )
        next_reward += float(release_delta)

    if not damage_shaping_enabled:
        return next_reward, bool(terminated), bool(truncated), status, rb, None

    for report in reports:
        report_id = _report_id(report)
        if report_id <= last_report_id:
            continue
        consumed_max_report_id = max(consumed_max_report_id, report_id)
        report_target_id = _report_target_id(report)
        if target_id > 0 and report_target_id == target_id:
            next_reward += _apply_report_shaping(loader, rb, report, role="target")
        elif agent_id > 0 and report_target_id == agent_id:
            next_reward += _apply_report_shaping(loader, rb, report, role="self")

    if consumed_max_report_id != int(getattr(loader, "_air_combat_reward_last_report_id", 0) or 0):
        setattr(loader, "_air_combat_reward_last_report_id", int(consumed_max_report_id))
    return next_reward, bool(terminated), bool(truncated), status, rb, None


def combat_entity_terminal_state(loader: Any, sim: Any, entity_id: int) -> dict[str, Any]:
    entity_id = int(entity_id or 0)
    active = False
    if sim is not None and entity_id > 0 and hasattr(sim, "is_unit_active"):
        try:
            active = bool(sim.is_unit_active(entity_id))
        except Exception:
            active = False

    state: dict[str, Any] = {
        "entity_id": entity_id,
        "active": bool(active),
        "neutralized": bool(not active),
        "actionable": bool(active),
        "reason": "entity_inactive" if not active else "",
        "damage_report_id": 0,
        "loss_state": "",
    }
    if entity_id <= 0 or not active or not air_combat_damage_terminal_enabled(loader):
        return state

    for report in _recent_damage_reports(sim):
        if _report_target_id(report) != entity_id:
            continue
        reason = _damage_report_terminal_reason(loader, report)
        if reason is None:
            continue
        state["neutralized"] = True
        state["actionable"] = False
        state["reason"] = reason
        state["damage_report_id"] = int(getattr(report, "report_id", 0) or 0)
        state["loss_state"] = str(getattr(report, "loss_state_to", "") or "")
    return state
