from __future__ import annotations

import numpy as np

from .common import ef_py
from .naval_actions import build_naval_station_action_transport, is_naval_station_action_mode
from .spaces import (
    AIR_COMBAT_HYBRID_V1_ACTION_MODE,
    AIR_EW_HYBRID_V1_ACTION_MODE,
    AIR_EW_HYBRID_V2_ACTION_MODE,
    expected_action_dim,
)


def half_to_unit(x: float) -> float:
    y = (x - 0.5) * 2.0
    if y <= 0.0:
        return 0.0
    if y >= 1.0:
        return 1.0
    return y


def normalize_action(action, *, action_space, action_mode: str) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32)
    if action.ndim != 1:
        action = action.reshape(-1)
    expected_dim = expected_action_dim(action_mode)
    if action.size != expected_dim:
        raise ValueError(
            f"Action shape mismatch for action_mode='{action_mode}': got {action.shape} "
            f"(size={action.size}), expected ({expected_dim},)."
        )
    try:
        action = np.clip(action, action_space.low, action_space.high)
    except Exception:
        pass
    return action.astype(np.float32, copy=False)


def is_air_combat_hybrid_action_mode(action_mode: str) -> bool:
    return str(action_mode) in {
        AIR_COMBAT_HYBRID_V1_ACTION_MODE,
        AIR_EW_HYBRID_V1_ACTION_MODE,
        AIR_EW_HYBRID_V2_ACTION_MODE,
    }


def is_air_ew_hybrid_action_mode(action_mode: str) -> bool:
    return str(action_mode) in {AIR_EW_HYBRID_V1_ACTION_MODE, AIR_EW_HYBRID_V2_ACTION_MODE}


def jammer_mode_code(value: float) -> int:
    """Floor-quantize the EW v2 jammer technique slot."""

    return int(np.floor(np.clip(float(value), 0.0, 2.0)))


def air_combat_hybrid_effective_action(action: np.ndarray, *, previous_intent=None) -> np.ndarray:
    raw = np.asarray(action, dtype=np.float32).reshape(-1)
    combat_dim = expected_action_dim(AIR_COMBAT_HYBRID_V1_ACTION_MODE)
    ew_dims = {
        expected_action_dim(AIR_EW_HYBRID_V1_ACTION_MODE),
        expected_action_dim(AIR_EW_HYBRID_V2_ACTION_MODE),
    }
    if raw.size not in {combat_dim, *ew_dims}:
        raise ValueError(
            f"Action shape mismatch for action_mode='{AIR_COMBAT_HYBRID_V1_ACTION_MODE}': "
            f"got {raw.shape}."
        )

    prefix = raw[:combat_dim]
    prev = np.zeros((combat_dim,), dtype=np.float32)
    if previous_intent is not None:
        prev_arr = np.asarray(previous_intent, dtype=np.float32).reshape(-1)
        if prev_arr.size >= combat_dim:
            prev = prev_arr[:combat_dim]

    effective_prefix = prefix.astype(np.float32, copy=True)
    for idx in (6, 8):
        effective_prefix[idx] = 1.0 if float(prefix[idx]) > 0.5 else 0.0
    for idx in (7, 9, 10):
        effective_prefix[idx] = 1.0 if float(prefix[idx]) > 0.5 and float(prev[idx]) <= 0.5 else 0.0
    # Discrete weapon stations use floor quantization across every maintained
    # Air transport path; rounding would make half-step actions disagree with
    # the direct facade adapter.
    effective_prefix[11] = float(np.floor(np.clip(prefix[11], 0.0, 7.0)))
    if raw.size in ew_dims:
        return np.concatenate((effective_prefix, raw[combat_dim:]), axis=0).astype(
            np.float32,
            copy=False,
        )
    return effective_prefix.astype(np.float32, copy=False)


def build_pilot_action(action: np.ndarray, *, action_mode: str, inst_now=None):
    if is_naval_station_action_mode(action_mode):
        return build_naval_station_action_transport(action).pilot_action

    pilot_act = ef_py.PilotAction()
    pilot_act.active = True

    if action_mode == "full":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        pilot_act.gear_handle = float(action[4])
        pilot_act.flaps = float(half_to_unit(float(action[5])))
        pilot_act.speedbrake = float(half_to_unit(float(action[6])))
        pilot_act.brake_left = False
        pilot_act.brake_right = False
        pilot_act.brake = float(half_to_unit(float(max(action[7], action[8]))))
        pilot_act.radar_active = bool(action[9] > 0.5)
        pilot_act.radar_scan_az = float(action[10]) * 60.0
        pilot_act.radar_scan_el = float(action[11]) * 30.0
        pilot_act.tms_up = bool(action[12] > 0.5)
        pilot_act.master_arm = bool(action[13] > 0.5)
        pilot_act.fire_weapon = bool(action[14] > 0.5)
        pilot_act.fire_gun = bool(action[15] > 0.5)
        pilot_act.weapon_select_id = int(action[16] * 7)
        pilot_act.program_chaff = False
        pilot_act.program_flare = False
        pilot_act.jettison_emergency = False
        return pilot_act

    if action_mode == AIR_COMBAT_HYBRID_V1_ACTION_MODE:
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        pilot_act.gear_handle = 0.0
        pilot_act.flaps = 0.0
        pilot_act.speedbrake = 0.0
        pilot_act.brake_left = False
        pilot_act.brake_right = False
        pilot_act.brake = 0.0
        pilot_act.radar_active = bool(action[6] > 0.5)
        pilot_act.radar_scan_az = float(action[4]) * 60.0
        pilot_act.radar_scan_el = float(action[5]) * 30.0
        pilot_act.tms_up = bool(action[7] > 0.5)
        pilot_act.master_arm = bool(action[8] > 0.5)
        pilot_act.fire_weapon = bool(action[9] > 0.5)
        pilot_act.fire_gun = bool(action[10] > 0.5)
        pilot_act.weapon_select_id = int(np.clip(float(action[11]), 0.0, 7.0))
        pilot_act.program_chaff = False
        pilot_act.program_flare = False
        pilot_act.jettison_emergency = False
        return pilot_act

    if action_mode in (AIR_EW_HYBRID_V1_ACTION_MODE, AIR_EW_HYBRID_V2_ACTION_MODE):
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
        pilot_act.gear_handle = 0.0
        pilot_act.flaps = 0.0
        pilot_act.speedbrake = 0.0
        pilot_act.brake_left = False
        pilot_act.brake_right = False
        pilot_act.brake = 0.0
        pilot_act.radar_active = bool(action[6] > 0.5)
        pilot_act.radar_scan_az = float(action[4]) * 60.0
        pilot_act.radar_scan_el = float(action[5]) * 30.0
        pilot_act.tms_up = bool(action[7] > 0.5)
        pilot_act.master_arm = bool(action[8] > 0.5)
        pilot_act.fire_weapon = bool(action[9] > 0.5)
        pilot_act.fire_gun = bool(action[10] > 0.5)
        pilot_act.weapon_select_id = int(np.clip(float(action[11]), 0.0, 7.0))
        pilot_act.program_chaff = bool(action[12] > 0.5)
        pilot_act.program_flare = bool(action[13] > 0.5)
        pilot_act.jammer_transmit = bool(action[14] > 0.5) if action_mode == AIR_EW_HYBRID_V2_ACTION_MODE else False
        pilot_act.jammer_mode = (
            jammer_mode_code(action[15])
            if action_mode == AIR_EW_HYBRID_V2_ACTION_MODE
            else -1
        )
        pilot_act.jettison_emergency = False
        return pilot_act

    pilot_act.stick_roll = 0.0
    pilot_act.rudder = 0.0
    pilot_act.flaps = 0.0
    pilot_act.speedbrake = 0.0
    pilot_act.brake = 0.0
    pilot_act.brake_left = False
    pilot_act.brake_right = False
    pilot_act.radar_active = False
    pilot_act.radar_scan_az = 0.0
    pilot_act.radar_scan_el = 0.0
    pilot_act.tms_up = False
    pilot_act.master_arm = False
    pilot_act.fire_weapon = False
    pilot_act.fire_gun = False
    pilot_act.weapon_select_id = 0
    pilot_act.program_chaff = False
    pilot_act.program_flare = False
    pilot_act.jammer_transmit = False
    pilot_act.jammer_mode = -1
    pilot_act.jettison_emergency = False

    if action_mode == "takeoff2":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.throttle = float(action[1])
    elif action_mode == "takeoff4":
        pilot_act.stick_pitch = float(action[0])
        pilot_act.stick_roll = float(action[1])
        pilot_act.rudder = float(action[2])
        pilot_act.throttle = float(action[3])
    else:
        raise ValueError(f"Unknown action_mode: {action_mode}")

    alt_radar = float(getattr(inst_now, "alt_radar", 0.0)) if inst_now is not None else 0.0
    pilot_act.gear_handle = 0.0 if alt_radar > 30.0 else 1.0
    return pilot_act


__all__ = [
    "air_combat_hybrid_effective_action",
    "build_pilot_action",
    "half_to_unit",
    "is_air_combat_hybrid_action_mode",
    "is_air_ew_hybrid_action_mode",
    "jammer_mode_code",
    "normalize_action",
]
