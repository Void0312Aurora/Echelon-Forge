from __future__ import annotations

from typing import Any

import numpy as np

from python.rl.tasking.bridge import mission_command_view


_C2_ROE_CONTRACT_FIELDS = {
    "wcs_state",
    "target_identity_state",
    "engage_order_state",
    "shot_policy_state",
    "shot_budget_remaining",
    "pending_assessment",
    "own_missiles_in_flight_count",
}
_C2_ROE_HOLD_ENGAGE_STATES = {3, 4, 5, 6}
_MASTER_ARM_INDEX = 8
_FIRE_WEAPON_INDEX = 9


def reset_air_combat_event_action_state(loader: Any) -> None:
    for name in (
        "_air_combat_event_action_engagement_state",
        "_air_combat_event_action_accepted_count",
        "_air_combat_event_action_initial_missiles",
        "_last_air_combat_event_action_info",
        "_air_combat_c2_roe_legal_open_age_steps",
        "_air_combat_c2_roe_legal_open_age_step_key",
        "_air_combat_c2_roe_launch_window_age_steps",
        "_air_combat_c2_roe_launch_window_age_step_key",
    ):
        try:
            if hasattr(loader, name):
                delattr(loader, name)
        except Exception:
            pass


def air_combat_event_action_contract_present(loader: Any) -> bool:
    cmd = getattr(loader, "mission_cmd", {})
    if not isinstance(cmd, dict):
        return False
    if "c2_roe_contract_present" in cmd:
        return _as_bool(cmd.get("c2_roe_contract_present"), False)
    return any(field in cmd for field in _C2_ROE_CONTRACT_FIELDS)


def apply_air_combat_event_action_gate(
    loader: Any,
    action: np.ndarray,
    *,
    agent_id: int,
    truth_before: Any = None,
) -> tuple[np.ndarray, dict[str, Any] | None]:
    if not air_combat_event_action_contract_present(loader):
        try:
            loader._last_air_combat_event_action_info = None
        except Exception:
            pass
        return action, None

    gated = np.asarray(action, dtype=np.float32).copy()
    if gated.size > _FIRE_WEAPON_INDEX and float(gated[_FIRE_WEAPON_INDEX]) > 0.5:
        gated[_MASTER_ARM_INDEX] = 1.0
    support = _build_fire_event_support(
        loader,
        gated,
        agent_id=int(agent_id),
        truth=truth_before,
    )
    requested = bool(support["fire_once_requested"])
    accepted = bool(requested and support["fire_mask"])
    reason = "" if (not requested or accepted) else str(support["fire_once_rejected_reason"])

    if requested and not accepted and gated.size > _FIRE_WEAPON_INDEX:
        gated[_FIRE_WEAPON_INDEX] = 0.0

    if accepted:
        _set_loader_attr(loader, "_air_combat_event_action_engagement_state", "FiredAssess")
        _set_loader_attr(
            loader,
            "_air_combat_event_action_accepted_count",
            int(getattr(loader, "_air_combat_event_action_accepted_count", 0) or 0) + 1,
        )
        if gated.size > _FIRE_WEAPON_INDEX:
            gated[_FIRE_WEAPON_INDEX] = 1.0

    info = dict(support)
    info["fire_once_accepted"] = bool(accepted)
    info["fire_once_rejected_reason"] = reason
    info["post_launch_suppressed"] = bool(
        requested and not accepted and str(support.get("fire_once_rejected_reason", "")) == "pending_assessment"
    )
    info["release_executed"] = False
    if accepted:
        info["engagement_state"] = "FiredAssess"
        info["fire_mask"] = 0
        info["fire_mask_not_pending_assessment"] = 0
        components = dict(info.get("fire_mask_components", {}))
        components["fire_mask_not_pending_assessment"] = 0
        info["fire_mask_components"] = components

    try:
        loader._last_air_combat_event_action_info = dict(info)
    except Exception:
        pass
    return gated.astype(np.float32, copy=False), info


def finalize_air_combat_event_action_info(
    loader: Any,
    *,
    truth_before: Any = None,
    truth_after: Any = None,
) -> dict[str, Any] | None:
    info = getattr(loader, "_last_air_combat_event_action_info", None)
    if not isinstance(info, dict):
        return None

    before = _missiles_remaining(truth_before)
    after = _missiles_remaining(truth_after)
    release_executed = bool(before is not None and after is not None and int(after) < int(before))
    info["release_executed"] = bool(release_executed)
    if release_executed:
        _set_loader_attr(loader, "_air_combat_event_action_engagement_state", "FiredAssess")

    try:
        loader._last_air_combat_event_action_info = dict(info)
    except Exception:
        pass
    return info


def add_air_combat_event_action_info(info: dict[str, Any], loader: Any) -> dict[str, Any]:
    event_info = getattr(loader, "_last_air_combat_event_action_info", None)
    if not isinstance(event_info, dict):
        return info
    for key, value in event_info.items():
        info[key] = value
    return info


def _build_fire_event_support(
    loader: Any,
    action: np.ndarray,
    *,
    agent_id: int,
    truth: Any = None,
) -> dict[str, Any]:
    cmd_view = mission_command_view(loader)
    shot_policy_state = int(cmd_view.int_field("shot_policy_state", 0))
    engage_order_state = int(cmd_view.int_field("engage_order_state", 0))
    wcs_state = int(cmd_view.int_field("wcs_state", 1))

    requested = bool(action.size > _FIRE_WEAPON_INDEX and float(action[_FIRE_WEAPON_INDEX]) > 0.5)
    master_arm = bool(action.size > 8 and float(action[8]) > 0.5)
    accepted_count = max(0, int(getattr(loader, "_air_combat_event_action_accepted_count", 0) or 0))
    release_count = _observed_release_count(loader, truth)

    assigned_target_id = int(cmd_view.int_field("assigned_target_id", 0))
    target_id = assigned_target_id if assigned_target_id > 0 else int(getattr(loader, "primary_target_id", 0) or 0)
    target_present = bool(_target_track_present(truth, target_id))

    holder_id = int(cmd_view.int_field("engagement_authority_holder_id", 0))
    holder_ok = bool(holder_id <= 0 or holder_id == int(agent_id))
    c2_authorized = bool(cmd_view.bool_field("authorization_to_fire", False) and holder_ok)

    raw_budget = max(0, int(cmd_view.int_field("shot_budget_remaining", 0)))
    if shot_policy_state == 3:
        shot_budget_remaining = raw_budget
    else:
        shot_budget_remaining = max(0, raw_budget - max(accepted_count, release_count))

    command_pending = bool(cmd_view.bool_field("pending_assessment", False))
    local_state = str(getattr(loader, "_air_combat_event_action_engagement_state", "") or "")
    local_pending = bool(local_state == "FiredAssess" and shot_policy_state != 3)
    first_shot_pending = bool(shot_policy_state == 1 and max(accepted_count, release_count) > 0)
    pending_assessment = bool(command_pending or local_pending or first_shot_pending)

    ammo_available = bool((_missiles_remaining(truth) or 0) > 0)
    weapon_ready = bool(master_arm)
    hold_order = bool(wcs_state == 1 or shot_policy_state == 0 or engage_order_state in _C2_ROE_HOLD_ENGAGE_STATES)
    reattack_allowed = bool(shot_policy_state == 3)

    first_shot_components_ok = bool(
        c2_authorized
        and target_present
        and shot_budget_remaining > 0
        and weapon_ready
        and ammo_available
        and not hold_order
    )
    if pending_assessment:
        engagement_state = "FiredAssess"
    elif not ammo_available:
        engagement_state = "Winchester"
    elif reattack_allowed and first_shot_components_ok:
        engagement_state = "ReattackReady"
    elif first_shot_components_ok:
        engagement_state = "AuthorizedReady"
    else:
        engagement_state = "Hold"

    mask_components = {
        "fire_mask_c2_authorized": int(c2_authorized and not hold_order),
        "fire_mask_target_present": int(target_present),
        "fire_mask_shot_budget_available": int(shot_budget_remaining > 0),
        "fire_mask_not_pending_assessment": int(not pending_assessment),
        "fire_mask_weapon_ready": int(weapon_ready),
        "fire_mask_ammo_available": int(ammo_available),
        "fire_mask_reattack_allowed": int(reattack_allowed),
    }
    fire_mask = int(
        engagement_state in {"AuthorizedReady", "ReattackReady"}
        and mask_components["fire_mask_c2_authorized"]
        and mask_components["fire_mask_target_present"]
        and mask_components["fire_mask_shot_budget_available"]
        and mask_components["fire_mask_weapon_ready"]
        and mask_components["fire_mask_ammo_available"]
        and (engagement_state == "AuthorizedReady" or mask_components["fire_mask_reattack_allowed"])
        and mask_components["fire_mask_not_pending_assessment"]
    )

    reason = _rejection_reason(
        engagement_state=engagement_state,
        mask_components=mask_components,
        hold_order=hold_order,
        c2_authorized=c2_authorized,
        target_present=target_present,
        shot_budget_available=shot_budget_remaining > 0,
        pending_assessment=pending_assessment,
        weapon_ready=weapon_ready,
        ammo_available=ammo_available,
        reattack_allowed=reattack_allowed,
    )
    return {
        "engagement_state": engagement_state,
        "fire_mask": int(fire_mask),
        "event_action_mask": [1, int(fire_mask)],
        "fire_mask_components": mask_components,
        **mask_components,
        "fire_once_requested": bool(requested),
        "fire_once_accepted": False,
        "fire_once_rejected_reason": reason,
        "release_executed": False,
        "post_launch_suppressed": False,
        "reattack_ready": bool(engagement_state == "ReattackReady"),
        "shot_budget_remaining": int(shot_budget_remaining),
    }


def _rejection_reason(
    *,
    engagement_state: str,
    mask_components: dict[str, int],
    hold_order: bool,
    c2_authorized: bool,
    target_present: bool,
    shot_budget_available: bool,
    pending_assessment: bool,
    weapon_ready: bool,
    ammo_available: bool,
    reattack_allowed: bool,
) -> str:
    if int(mask_components.get("fire_mask_not_pending_assessment", 0)) == 0 or pending_assessment:
        return "pending_assessment"
    if hold_order or engagement_state == "Hold":
        if not c2_authorized:
            return "no_c2_authorization"
        if not target_present:
            return "no_target"
        if not shot_budget_available:
            return "shot_budget_empty"
        if not weapon_ready:
            return "weapon_not_ready"
        if not ammo_available:
            return "ammo_empty"
        return "hold_state"
    if not c2_authorized:
        return "no_c2_authorization"
    if not target_present:
        return "no_target"
    if not shot_budget_available:
        return "shot_budget_empty"
    if not weapon_ready:
        return "weapon_not_ready"
    if not ammo_available:
        return "ammo_empty"
    if engagement_state == "ReattackReady" and not reattack_allowed:
        return "reattack_not_authorized"
    if engagement_state not in {"AuthorizedReady", "ReattackReady"}:
        return "masked_hold_only"
    return ""


def _target_track_present(truth: Any, target_id: int) -> bool:
    if truth is None or int(target_id) <= 0:
        return False
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0) or 0) == int(target_id):
                return True
        except Exception:
            continue
    return False


def _missiles_remaining(truth: Any) -> int | None:
    try:
        value = int(getattr(truth, "missiles_remaining", -1))
    except Exception:
        return None
    return value if value >= 0 else None


def _observed_release_count(loader: Any, truth: Any) -> int:
    current_missiles = _missiles_remaining(truth)
    if current_missiles is None:
        return 0
    initial_missiles = getattr(loader, "_air_combat_event_action_initial_missiles", None)
    try:
        initial_missiles = int(initial_missiles)
    except Exception:
        initial_missiles = int(current_missiles)
    if initial_missiles < int(current_missiles):
        initial_missiles = int(current_missiles)
    _set_loader_attr(loader, "_air_combat_event_action_initial_missiles", int(initial_missiles))
    return max(0, int(initial_missiles) - int(current_missiles))


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled", ""}:
        return False
    return bool(default)


def _set_loader_attr(loader: Any, name: str, value: Any) -> None:
    try:
        setattr(loader, name, value)
    except Exception:
        pass


__all__ = [
    "add_air_combat_event_action_info",
    "air_combat_event_action_contract_present",
    "apply_air_combat_event_action_gate",
    "finalize_air_combat_event_action_info",
    "reset_air_combat_event_action_state",
]
