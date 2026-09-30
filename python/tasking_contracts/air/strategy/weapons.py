"""Source-backed Air weapon tuning for the RL-independent scripted line.

The simulator database exposes useful runtime tuning, but it does not by
itself establish a calibrated WEZ, probability of kill, or an optimal launch
range. This module preserves that boundary and exposes only declared fields.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Mapping


def _optional_finite(value: Any, *, name: str) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric when present") from exc
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be finite and non-negative when present")
    return number


@dataclass(frozen=True)
class AirWeaponEnvelope:
    """Declared missile tuning available to a scripted tactical planner.

    Guidance and sensor ranges are opportunities for planning, not effective
    weapon range. The current authored database has no calibrated Pk model.
    """

    weapon_id: str
    source_path: str = ""
    sensor_max_range_m: float | None = None
    seeker_activation_range_m: float | None = None
    max_flight_time_s: float | None = None
    max_speed_mps: float | None = None
    max_lateral_g: float | None = None
    min_launch_range_m: float | None = None
    max_launch_off_boresight_deg: float | None = None
    source_fields: tuple[str, ...] = ()
    envelope_status: str = "runtime_tuning_only"
    pk_authority: bool = False

    def __post_init__(self) -> None:
        weapon_id = str(self.weapon_id).strip()
        if not weapon_id:
            raise ValueError("weapon_id must be non-empty")
        object.__setattr__(self, "weapon_id", weapon_id)
        object.__setattr__(self, "source_path", str(self.source_path))
        object.__setattr__(self, "source_fields", tuple(str(field) for field in self.source_fields))
        object.__setattr__(self, "envelope_status", str(self.envelope_status).strip() or "runtime_tuning_only")
        if not isinstance(self.pk_authority, bool):
            raise TypeError("pk_authority must be bool")
        for name in (
            "sensor_max_range_m",
            "seeker_activation_range_m",
            "max_flight_time_s",
            "max_speed_mps",
            "max_lateral_g",
            "min_launch_range_m",
            "max_launch_off_boresight_deg",
        ):
            object.__setattr__(self, name, _optional_finite(getattr(self, name), name=name))
        if self.max_launch_off_boresight_deg is not None and self.max_launch_off_boresight_deg > 180.0:
            raise ValueError("max_launch_off_boresight_deg must be <= 180")

    @property
    def guidance_range_m(self) -> float | None:
        return self.seeker_activation_range_m or self.sensor_max_range_m

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, source_path: str = "") -> "AirWeaponEnvelope":
        if not isinstance(payload, Mapping):
            raise TypeError("weapon database entry must be a mapping")
        guidance = payload.get("guidance", {})
        flight_model = payload.get("flight_model", {})
        sensor = payload.get("sensor", {})
        if not isinstance(guidance, Mapping) or not isinstance(flight_model, Mapping) or not isinstance(sensor, Mapping):
            raise ValueError("guidance, flight_model, and sensor entries must be mappings")

        source_fields: list[str] = []
        guidance_range = None
        for owner, field in (
            (guidance, "active_seek_range"),
            (guidance, "seeker_activation_range_m"),
            (guidance, "sensor_max_range"),
            (sensor, "max_range"),
        ):
            if field in owner and owner[field] is not None:
                guidance_range = owner[field]
                source_fields.append(f"guidance.{field}" if owner is guidance else f"sensor.{field}")
                break
        return cls(
            weapon_id=str(payload.get("name", "")).strip(),
            source_path=source_path,
            sensor_max_range_m=guidance_range,
            seeker_activation_range_m=guidance_range,
            max_flight_time_s=payload.get("max_flight_time_s"),
            max_speed_mps=flight_model.get("max_speed"),
            max_lateral_g=flight_model.get("max_g"),
            min_launch_range_m=guidance.get("min_launch_range_m"),
            max_launch_off_boresight_deg=guidance.get("off_boresight_cap"),
            source_fields=tuple(source_fields),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "weapon_id": self.weapon_id,
            "source_path": self.source_path,
            "sensor_max_range_m": self.sensor_max_range_m,
            "seeker_activation_range_m": self.seeker_activation_range_m,
            "guidance_range_m": self.guidance_range_m,
            "max_flight_time_s": self.max_flight_time_s,
            "max_speed_mps": self.max_speed_mps,
            "max_lateral_g": self.max_lateral_g,
            "min_launch_range_m": self.min_launch_range_m,
            "max_launch_off_boresight_deg": self.max_launch_off_boresight_deg,
            "source_fields": list(self.source_fields),
            "envelope_status": self.envelope_status,
            "pk_authority": self.pk_authority,
        }


def load_air_weapon_envelope(path: str | Path) -> AirWeaponEnvelope:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return AirWeaponEnvelope.from_mapping(payload, source_path=str(source))


__all__ = ["AirWeaponEnvelope", "load_air_weapon_envelope"]
