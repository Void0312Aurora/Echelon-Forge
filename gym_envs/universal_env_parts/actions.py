from __future__ import annotations

import numpy as np

from .common import ef_py
from .naval_actions import build_neutral_ship_pilot_action, is_naval_station_action_mode
from .spaces import expected_action_dim


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


def build_pilot_action(action: np.ndarray, *, action_mode: str, inst_now=None):
    if is_naval_station_action_mode(action_mode):
        return build_neutral_ship_pilot_action()

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


__all__ = ["build_pilot_action", "half_to_unit", "normalize_action"]
