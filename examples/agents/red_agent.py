from __future__ import annotations

import math
from typing import Any

from python.angles import wrap_heading_deg

# Local name preserved as a thin alias; semantics owned by python.angles.
_wrap_heading_deg = wrap_heading_deg


class RedScriptedAgent:
    """
    Minimal scripted red-side baseline for the maintained 1v1 air-combat line.

    The intent is not to be a strong tactical opponent yet. Instead, this agent
    provides a deterministic, repeatable hostile baseline that can:
    1. Hold an intercept/offset geometry while outside the merge.
    2. Turn defensively when the blue fighter closes.
    3. Fire missiles once a hostile track exists and basic attack gates are met.
    """

    def __init__(
        self,
        kernel: Any,
        unit_id: int,
        *,
        target_id: int | None = None,
        cruise_speed_mps: float = 220.0,
        attack_speed_mps: float = 260.0,
        defensive_speed_mps: float = 290.0,
        threat_range_m: float = 9000.0,
        merge_range_m: float = 3500.0,
        fire_range_m: float = 9000.0,
        altitude_hold_m: float | None = None,
        beam_offset_deg: float = 85.0,
    ) -> None:
        self.kernel = kernel
        self.unit_id = int(unit_id)
        self.target_id = int(target_id) if target_id is not None else 0
        self.cruise_speed_mps = max(120.0, float(cruise_speed_mps))
        self.attack_speed_mps = max(self.cruise_speed_mps, float(attack_speed_mps))
        self.defensive_speed_mps = max(self.attack_speed_mps, float(defensive_speed_mps))
        self.threat_range_m = max(1000.0, float(threat_range_m))
        self.merge_range_m = max(500.0, min(float(merge_range_m), self.threat_range_m))
        self.fire_range_m = max(500.0, float(fire_range_m))
        self.altitude_hold_m = None if altitude_hold_m is None else float(altitude_hold_m)
        self.beam_offset_deg = float(beam_offset_deg)
        self.last_step_report: dict[str, Any] = {}

    def set_target_id(self, target_id: int | None) -> None:
        self.target_id = int(target_id) if target_id is not None else 0

    def _target_track(self, own_obs: Any):
        target_id = int(self.target_id or 0)
        if target_id <= 0:
            return None
        for track in getattr(own_obs, "contacts", []) or []:
            if int(getattr(track, "id", 0)) != target_id:
                continue
            if int(getattr(track, "classification", 0)) not in (0, 2):
                continue
            return track
        return None

    def _geometry(self) -> dict[str, float] | None:
        target_id = int(self.target_id or 0)
        if target_id <= 0:
            return None
        if not bool(self.kernel.is_unit_active(self.unit_id)) or not bool(self.kernel.is_unit_active(target_id)):
            return None
        own_pos = self.kernel.get_unit_position(self.unit_id)
        tgt_pos = self.kernel.get_unit_position(target_id)
        dx = float(tgt_pos[0]) - float(own_pos[0])
        dy = float(tgt_pos[1]) - float(own_pos[1])
        dz = float(tgt_pos[2]) - float(own_pos[2])
        horizontal_range_m = math.hypot(dx, dy)
        slant_range_m = math.sqrt(dx * dx + dy * dy + dz * dz)
        bearing_deg = math.degrees(math.atan2(dx, dy))
        return {
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "horizontal_range_m": horizontal_range_m,
            "slant_range_m": slant_range_m,
            "bearing_deg": _wrap_heading_deg(bearing_deg),
            "own_altitude_m": float(own_pos[2]),
            "target_altitude_m": float(tgt_pos[2]),
        }

    def _desired_command(self, geometry: dict[str, float]) -> tuple[float, float, float, str]:
        target_heading = float(geometry["bearing_deg"])
        target_speed = self.attack_speed_mps
        target_altitude = (
            float(self.altitude_hold_m)
            if self.altitude_hold_m is not None
            else float(geometry["target_altitude_m"])
        )
        mode = "intercept"

        if float(geometry["horizontal_range_m"]) <= self.merge_range_m:
            target_heading = _wrap_heading_deg(float(geometry["bearing_deg"]) + self.beam_offset_deg)
            target_speed = self.defensive_speed_mps
            mode = "beam_defense"
        elif float(geometry["horizontal_range_m"]) <= self.threat_range_m:
            target_heading = _wrap_heading_deg(float(geometry["bearing_deg"]) + 25.0)
            target_speed = self.attack_speed_mps
            mode = "offset_attack"
        else:
            target_heading = float(geometry["bearing_deg"])
            target_speed = self.cruise_speed_mps
            mode = "commit"

        return (
            _wrap_heading_deg(target_heading),
            float(target_speed),
            float(target_altitude),
            mode,
        )

    def _should_fire(self, own_obs: Any, track: Any) -> bool:
        missiles_remaining = int(getattr(own_obs, "missiles_remaining", 0))
        if missiles_remaining <= 0:
            return False
        if not bool(getattr(own_obs, "can_fire", False)):
            return False
        if int(getattr(track, "classification", 0)) not in (0, 2):
            return False
        track_range_m = float(getattr(track, "range", float("inf")))
        if track_range_m > self.fire_range_m:
            return False
        closing_speed = float(getattr(track, "closing_speed", 0.0))
        return closing_speed >= -250.0

    def step(self, current_time: float | None = None) -> dict[str, Any]:
        del current_time
        report: dict[str, Any] = {
            "active": False,
            "target_id": int(self.target_id or 0),
            "mode": "idle",
            "fired": False,
        }

        target_id = int(self.target_id or 0)
        if target_id <= 0:
            self.last_step_report = report
            return report
        if not bool(self.kernel.is_unit_active(self.unit_id)) or not bool(self.kernel.is_unit_active(target_id)):
            self.last_step_report = report
            return report

        geometry = self._geometry()
        if geometry is None:
            self.last_step_report = report
            return report

        own_obs = self.kernel.get_agent_observation(self.unit_id)
        track = self._target_track(own_obs)
        target_heading, target_speed, target_altitude, mode = self._desired_command(geometry)
        self.kernel.set_command(self.unit_id, target_heading, target_speed, target_altitude)

        fired = False
        if track is not None and self._should_fire(own_obs, track):
            missile_id = int(self.kernel.fire_missile(self.unit_id, target_id))
            fired = missile_id > 0
            report["missile_id"] = missile_id

        report.update(
            {
                "active": True,
                "mode": mode,
                "fired": bool(fired),
                "range_m": float(geometry["horizontal_range_m"]),
                "slant_range_m": float(geometry["slant_range_m"]),
                "bearing_deg": float(geometry["bearing_deg"]),
                "target_heading_deg": float(target_heading),
                "target_speed_mps": float(target_speed),
                "target_altitude_m": float(target_altitude),
                "track_available": bool(track is not None),
            }
        )
        self.last_step_report = report
        return report
