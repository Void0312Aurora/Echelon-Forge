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


def _normalized_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


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
    action = getattr(loader, "_last_effective_action", None)
    if action is None:
        return False
    try:
        values = [float(v) for v in action]
    except Exception:
        return False
    mode = str(getattr(loader, "_last_action_mode", "") or "")
    fire_idx = 9 if mode == "air_combat_hybrid_v1" else 14
    if len(values) <= fire_idx:
        return False
    return bool(values[fire_idx] > 0.5)


def _apply_release_shaping(loader: Any, rb: dict[str, float], truth: Any) -> tuple[float, bool]:
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
    if release_count > 0:
        previous_release_count = int(getattr(loader, "_air_combat_reward_release_count", 0) or 0)
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

        setattr(
            loader,
            "_air_combat_reward_release_count",
            int(previous_release_count) + int(release_count),
        )
        return total, True

    invalid_fire_penalty = _cfg_float(loader, "air_combat_invalid_fire_penalty", 0.0)
    if invalid_fire_penalty != 0.0 and _last_fire_attempted(loader):
        total += _add_term(rb, "air_combat_invalid_fire_penalty", invalid_fire_penalty)
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
    damage_shaping_enabled = air_combat_damage_shaping_enabled(loader)
    if not release_shaping_enabled and not damage_shaping_enabled:
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

    if release_shaping_enabled:
        release_delta, _released = _apply_release_shaping(loader, rb, truth)
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
