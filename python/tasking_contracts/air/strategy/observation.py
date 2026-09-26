"""Air-owned observation decoding for scripted tactical strategy."""

from __future__ import annotations

from typing import Any, Mapping
from types import MappingProxyType

import numpy as np

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index

from .contracts import AirObservationAdapter, AirTacticalObservation


class AirMissionContactObservationAdapter:
    """Decode the declared C2/ROE mission fields and five-column contact token."""

    def decode(
        self,
        *,
        observation: Mapping[str, Any],
        mission_obs_mode: str,
    ) -> AirTacticalObservation:
        mode = str(mission_obs_mode).strip().lower()
        if mission_observation_dim(mode) <= 0:
            raise ValueError(f"unsupported Air tactical mission observation mode: {mode!r}")
        mission = np.asarray(observation.get("mission", []), dtype=np.float32).reshape(-1)
        required = {
            name: mission_observation_field_index(mode, name)
            for name in (
                "authorization_to_fire",
                "target_contact_present",
                "fire_mask_open",
                "launch_window_open",
                "shot_budget_remaining",
                "pending_assessment",
            )
        }
        missing = [name for name, index in required.items() if index >= mission.size]
        if missing:
            raise ValueError(
                f"Air tactical mission observation is missing required fields {missing!r} "
                f"for mode {mode!r}"
            )
        values = {name: float(mission[index]) for name, index in required.items()}
        for name, default in (
            ("quality_window_ready", values["fire_mask_open"] * values["launch_window_open"]),
            ("target_range_m", 0.0),
            ("target_track_age_s", 0.0),
            ("own_missiles_in_flight_count", 0.0),
        ):
            try:
                index = mission_observation_field_index(mode, name)
            except ValueError:
                values[name] = float(default)
            else:
                values[name] = float(mission[index]) if index < mission.size else float(default)
        bearing, elevation, closing = self._contact_geometry(
            observation,
            target_range_m=values["target_range_m"],
        )
        return AirTacticalObservation(
            mission_values=MappingProxyType(values),
            mission_obs_mode=mode,
            contact_bearing_deg=bearing,
            contact_elevation_deg=elevation,
            closing_speed_mps=closing,
        )

    @staticmethod
    def _contact_geometry(
        observation: Mapping[str, Any],
        *,
        target_range_m: float,
    ) -> tuple[float, float, float]:
        """Return the freshest directional/closure terms from the contact token."""

        contacts = np.asarray(observation.get("contacts", []), dtype=np.float32)
        if contacts.size == 0:
            return 0.0, 0.0, 0.0
        rows = contacts.reshape(-1, 5)
        valid = rows[np.isfinite(rows).all(axis=1) & (rows[:, 0] > 0.0)]
        if valid.size == 0:
            return 0.0, 0.0, 0.0
        if float(target_range_m) > 0.0:
            index = int(np.argmin(np.abs(valid[:, 0] - float(target_range_m))))
        else:
            index = 0
        row = valid[index]
        return float(row[1]), float(row[2]), float(row[3])


__all__ = ["AirMissionContactObservationAdapter", "AirObservationAdapter"]
