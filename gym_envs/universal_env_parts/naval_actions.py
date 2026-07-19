from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from python.angles import wrap_heading_deg
from python.tasking_contracts.bridge_views import (
    has_mission_command_dict,
    mission_command_dict,
)
from .common import ef_py
from .spaces import NAVAL_STATION3_ACTION_MODE


NAVAL_STATION3_BEARING_DELTA_DEG = 25.0
NAVAL_STATION3_RADIUS_DELTA_M = 1800.0
NAVAL_STATION3_SPEED_BIAS_MPS = 1.25
NAVAL_STATION3_ACTION_DEADBAND = 0.005
NAVAL_STATION3_ACTION_FAMILY = "naval_station_command"
NAVAL_STATION3_COMMAND_SURFACE_KIND = "naval_station3_command_surface"
NAVAL_STATION3_TRANSPORT_ADAPTER_KIND = "naval_station3_pilot_action_transport_compat"
NAVAL_STATION3_CARRIER_INTERFACE_KIND = "PilotActionAssignment"
NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE = "pilot_action"
NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE = (
    "PilotAction carrier is legacy compatibility-only transport for naval_station3 "
    "and not policy-visible action truth; use _naval_station3_command_surface for "
    "command diagnostics."
)


@dataclass(frozen=True)
class NavalStationActionTransport:
    policy_action: tuple[float, float, float]
    pilot_action: Any
    policy_surface: str = NAVAL_STATION3_ACTION_MODE
    action_family: str = NAVAL_STATION3_ACTION_FAMILY
    transport_adapter_kind: str = NAVAL_STATION3_TRANSPORT_ADAPTER_KIND
    carrier_interface_kind: str = NAVAL_STATION3_CARRIER_INTERFACE_KIND
    payload_type: str = NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE
    compatibility_only: bool = True
    diagnostics_note: str = NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE

    def as_dict(self) -> dict[str, Any]:
        pilot = self.pilot_action
        return {
            "policy_surface": self.policy_surface,
            "policy_action": [float(value) for value in self.policy_action],
            "action_family": self.action_family,
            "policy_truth_surface": NAVAL_STATION3_COMMAND_SURFACE_KIND,
            "transport_adapter_kind": self.transport_adapter_kind,
            "carrier_interface_kind": self.carrier_interface_kind,
            "payload_type": self.payload_type,
            "compatibility_only": bool(self.compatibility_only),
            "carrier_required": True,
            "diagnostics_note": self.diagnostics_note,
            "carrier_action": {
                "throttle": float(getattr(pilot, "throttle", 0.0)),
                "gear_handle": float(getattr(pilot, "gear_handle", 0.0)),
                "master_arm": bool(getattr(pilot, "master_arm", False)),
                "fire_weapon": bool(getattr(pilot, "fire_weapon", False)),
                "fire_gun": bool(getattr(pilot, "fire_gun", False)),
            },
        }


def is_naval_station_action_mode(action_mode: str) -> bool:
    return str(action_mode) == NAVAL_STATION3_ACTION_MODE


def validate_naval_action_mode_for_loader(loader: Any, action_mode: str) -> None:
    # Deferred: profile dispatch stays python.rl-resident (see I24/I27).
    from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader

    if tasking_profile_for_loader(loader) is not resolve_tasking_profile("naval"):
        return
    if is_naval_station_action_mode(action_mode):
        return
    raise RuntimeError(
        "Naval tasking profiles require action_mode='naval_station3'; "
        f"got action_mode='{action_mode}'."
    )


def build_neutral_ship_pilot_action():
    pilot_act = ef_py.PilotAction()
    pilot_act.active = True
    pilot_act.stick_pitch = 0.0
    pilot_act.stick_roll = 0.0
    pilot_act.rudder = 0.0
    pilot_act.throttle = 0.5
    pilot_act.gear_handle = 0.0
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
    pilot_act.jettison_emergency = False
    pilot_act.program_chaff = False
    pilot_act.program_flare = False
    return pilot_act


def naval_action_family_for_mode(action_mode: str) -> str:
    return NAVAL_STATION3_ACTION_FAMILY if is_naval_station_action_mode(action_mode) else "direct_control"


def build_naval_station_action_transport(action: np.ndarray) -> NavalStationActionTransport:
    action_arr = naval_station_action_command(action)
    pilot_act = build_neutral_ship_pilot_action()
    return NavalStationActionTransport(
        policy_action=tuple(float(value) for value in action_arr[:3]),
        pilot_action=pilot_act,
    )


# Local name preserved as a thin alias; semantics owned by python.angles.
_wrap_heading_deg = wrap_heading_deg


def _get_base(loader: Any, attr_name: str, value: float) -> float:
    if not hasattr(loader, attr_name):
        setattr(loader, attr_name, float(value))
    return float(getattr(loader, attr_name))


def reset_naval_station_action_state(loader: Any) -> None:
    for attr_name in (
        "_naval_station3_base_heading_deg",
        "_naval_station3_base_radius_m",
        "_naval_station3_base_speed_mps",
        "_naval_station3_eval_heading_deg",
        "_naval_station3_eval_radius_m",
        "_naval_station3_eval_speed_mps",
        "_naval_station3_last_action",
        "_naval_station3_command_surface",
        "_naval_station3_transport_adapter",
        "_naval_reward_last_station_error_m",
    ):
        try:
            delattr(loader, attr_name)
        except Exception:
            pass


def bind_naval_station_eval_reference(loader: Any) -> None:
    task = getattr(loader, "task_order", None)
    if task is None or not has_mission_command_dict(loader):
        return
    mission_cmd = mission_command_dict(loader)
    _get_base(
        loader,
        "_naval_station3_eval_heading_deg",
        float(
            getattr(
                task,
                "station_heading_deg",
                mission_cmd.get("station_bearing_deg", mission_cmd.get("target_heading", 0.0)),
            )
            or 0.0
        ),
    )
    _get_base(
        loader,
        "_naval_station3_eval_radius_m",
        float(getattr(task, "station_radius_m", mission_cmd.get("station_radius_m", 0.0)) or 0.0),
    )
    _get_base(
        loader,
        "_naval_station3_eval_speed_mps",
        float(getattr(task, "target_speed_mps", mission_cmd.get("target_speed", 0.0)) or 0.0),
    )


def naval_station_action_command(action: np.ndarray) -> np.ndarray:
    action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
    if action_arr.size != 3:
        raise ValueError(
            f"Action shape mismatch for action_mode='{NAVAL_STATION3_ACTION_MODE}': "
            f"got {action_arr.shape} (size={action_arr.size}), expected (3,)."
        )
    action_arr = np.clip(action_arr, -1.0, 1.0)
    action_arr = np.where(np.abs(action_arr) <= NAVAL_STATION3_ACTION_DEADBAND, 0.0, action_arr)
    return action_arr.astype(np.float32, copy=True)


def build_naval_station_command_surface(
    *,
    policy_action: np.ndarray,
    base_heading_deg: float,
    base_radius_m: float,
    base_speed_mps: float,
    heading_delta_deg: float,
    radius_delta_m: float,
    speed_delta_mps: float,
    station_heading_deg: float,
    station_radius_m: float,
    target_speed_mps: float,
) -> dict[str, Any]:
    action_arr = np.asarray(policy_action, dtype=np.float32).reshape(-1)
    return {
        "policy_surface": NAVAL_STATION3_ACTION_MODE,
        "action_family": NAVAL_STATION3_ACTION_FAMILY,
        "command_surface_kind": NAVAL_STATION3_COMMAND_SURFACE_KIND,
        "policy_action": [float(value) for value in action_arr[:3]],
        "compatibility_only": False,
        "carrier_required": True,
        "legacy_transport_adapter_kind": NAVAL_STATION3_TRANSPORT_ADAPTER_KIND,
        "base_heading_deg": float(base_heading_deg),
        "base_radius_m": float(base_radius_m),
        "base_speed_mps": float(base_speed_mps),
        "heading_delta_deg": float(heading_delta_deg),
        "radius_delta_m": float(radius_delta_m),
        "speed_delta_mps": float(speed_delta_mps),
        "station_heading_deg": float(station_heading_deg),
        "station_radius_m": float(station_radius_m),
        "target_speed_mps": float(target_speed_mps),
    }


def apply_naval_station_action(loader: Any, action: np.ndarray) -> bool:
    task = getattr(loader, "task_order", None)
    if task is None or not has_mission_command_dict(loader):
        return False
    transport = build_naval_station_action_transport(action)
    action_arr = np.asarray(transport.policy_action, dtype=np.float32)
    setattr(loader, "_naval_station3_last_action", action_arr.astype(np.float32, copy=True))
    setattr(loader, "_naval_station3_transport_adapter", transport.as_dict())
    bind_naval_station_eval_reference(loader)

    mission_cmd = mission_command_dict(loader)
    base_heading = _get_base(
        loader,
        "_naval_station3_base_heading_deg",
        float(getattr(task, "station_heading_deg", mission_cmd.get("station_bearing_deg", mission_cmd.get("target_heading", 0.0))) or 0.0),
    )
    base_radius = _get_base(
        loader,
        "_naval_station3_base_radius_m",
        float(getattr(task, "station_radius_m", mission_cmd.get("station_radius_m", 0.0)) or 0.0),
    )
    base_speed = _get_base(
        loader,
        "_naval_station3_base_speed_mps",
        float(getattr(task, "target_speed_mps", mission_cmd.get("target_speed", 0.0)) or 0.0),
    )

    heading_delta = float(action_arr[0]) * NAVAL_STATION3_BEARING_DELTA_DEG
    radius_delta = float(action_arr[1]) * NAVAL_STATION3_RADIUS_DELTA_M
    speed_delta = float(action_arr[2]) * NAVAL_STATION3_SPEED_BIAS_MPS

    radius_floor = max(1000.0, base_radius - NAVAL_STATION3_RADIUS_DELTA_M)
    station_radius_m = max(radius_floor, base_radius + radius_delta)
    station_heading_deg = _wrap_heading_deg(base_heading + heading_delta)

    speed_min = float(getattr(task, "speed_min_mps", 0.0) or 0.0)
    speed_max = float(getattr(task, "speed_max_mps", 0.0) or 0.0)
    if speed_min > 0.0 and speed_max > 0.0:
        target_speed_mps = min(max(base_speed + speed_delta, speed_min), max(speed_min, speed_max))
    else:
        target_speed_mps = max(0.0, base_speed + speed_delta)

    task.station_radius_m = float(station_radius_m)
    task.station_heading_deg = float(station_heading_deg)
    task.target_speed_mps = float(target_speed_mps)
    mission_cmd["station_radius_m"] = float(station_radius_m)
    mission_cmd["station_bearing_deg"] = float(station_heading_deg)
    mission_cmd["target_speed"] = float(target_speed_mps)
    mission_cmd["target_altitude"] = 0.0
    setattr(
        loader,
        "_naval_station3_command_surface",
        build_naval_station_command_surface(
            policy_action=action_arr,
            base_heading_deg=base_heading,
            base_radius_m=base_radius,
            base_speed_mps=base_speed,
            heading_delta_deg=heading_delta,
            radius_delta_m=radius_delta,
            speed_delta_mps=speed_delta,
            station_heading_deg=station_heading_deg,
            station_radius_m=station_radius_m,
            target_speed_mps=target_speed_mps,
        ),
    )
    return True


__all__ = [
    "NAVAL_STATION3_ACTION_MODE",
    "NAVAL_STATION3_ACTION_DEADBAND",
    "NAVAL_STATION3_ACTION_FAMILY",
    "NAVAL_STATION3_CARRIER_INTERFACE_KIND",
    "NAVAL_STATION3_COMMAND_SURFACE_KIND",
    "NAVAL_STATION3_TRANSPORT_ADAPTER_KIND",
    "NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE",
    "NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE",
    "NavalStationActionTransport",
    "apply_naval_station_action",
    "bind_naval_station_eval_reference",
    "build_naval_station_command_surface",
    "build_naval_station_action_transport",
    "build_neutral_ship_pilot_action",
    "is_naval_station_action_mode",
    "naval_action_family_for_mode",
    "naval_station_action_command",
    "reset_naval_station_action_state",
    "validate_naval_action_mode_for_loader",
]
