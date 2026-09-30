"""Native PilotAction projection for the Air scripted simulation line."""

from __future__ import annotations

from typing import Any

import ef_py
import numpy as np


AIR_FULL_ACTION_DIM = 17
AIR_TAKEOFF4_ACTION_DIM = 4
AIR_TAKEOFF2_ACTION_DIM = 2


def half_to_unit(value: float) -> float:
    return float(np.clip((float(value) - 0.5) * 2.0, 0.0, 1.0))


def build_pilot_action(action: Any, *, action_mode: str = "full", instrument_state: Any = None) -> Any:
    """Map a neutral Air action vector to the native PilotAction DTO."""
    values = np.asarray(action, dtype=np.float32).reshape(-1)
    mode = str(action_mode).strip().lower()
    expected = {
        "full": AIR_FULL_ACTION_DIM,
        "takeoff4": AIR_TAKEOFF4_ACTION_DIM,
        "takeoff2": AIR_TAKEOFF2_ACTION_DIM,
    }.get(mode)
    if expected is None or values.size != expected:
        raise ValueError(f"unsupported Air action mode/shape: {mode!r}, {values.shape}")

    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.stick_pitch = float(values[0])
    pilot.stick_roll = float(values[1]) if values.size >= 4 else 0.0
    pilot.rudder = float(values[2]) if values.size >= 4 else 0.0
    pilot.throttle = float(values[3] if values.size >= 4 else values[1])
    pilot.gear_handle = float(values[4]) if mode == "full" else (1.0 if _float(instrument_state, "alt_radar") <= 30.0 else 0.0)
    pilot.flaps = half_to_unit(values[5]) if mode == "full" else 0.0
    pilot.speedbrake = half_to_unit(values[6]) if mode == "full" else 0.0
    pilot.brake_left = False
    pilot.brake_right = False
    pilot.brake = half_to_unit(max(float(values[7]), float(values[8]))) if mode == "full" else 0.0
    if mode == "full":
        pilot.radar_active = bool(values[9] > 0.5)
        pilot.radar_scan_az = float(values[10]) * 60.0
        pilot.radar_scan_el = float(values[11]) * 30.0
        pilot.tms_up = bool(values[12] > 0.5)
        pilot.master_arm = bool(values[13] > 0.5)
        pilot.fire_weapon = bool(values[14] > 0.5)
        pilot.fire_gun = bool(values[15] > 0.5)
        pilot.weapon_select_id = int(np.clip(round(float(values[16] * 7.0)), 0, 7))
    else:
        pilot.radar_active = False
        pilot.radar_scan_az = 0.0
        pilot.radar_scan_el = 0.0
        pilot.tms_up = False
        pilot.master_arm = False
        pilot.fire_weapon = False
        pilot.fire_gun = False
        pilot.weapon_select_id = 0
    pilot.program_chaff = False
    pilot.program_flare = False
    pilot.jettison_emergency = False
    return pilot


def _float(value: Any, name: str, default: float = 0.0) -> float:
    try:
        return float(getattr(value, name))
    except (AttributeError, TypeError, ValueError):
        return float(default)


__all__ = [
    "AIR_FULL_ACTION_DIM",
    "AIR_TAKEOFF2_ACTION_DIM",
    "AIR_TAKEOFF4_ACTION_DIM",
    "build_pilot_action",
    "half_to_unit",
]
