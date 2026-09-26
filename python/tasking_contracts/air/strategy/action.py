"""Air-owned action-layout and tactical pulse transport."""

from __future__ import annotations

from typing import Any

import numpy as np

from .contracts import AirActionApplication, AirActionAdapter, AirTacticalActionIntent


AIR_FULL_ACTION_DIM = 17
AIR_COMBAT_HYBRID_ACTION_DIM = 12


class AirActionLayoutAdapter:
    """Map one tactical intent onto the maintained full or hybrid Air action."""

    def __init__(self, *, action_dim: int) -> None:
        self.action_dim = int(action_dim)
        if self.action_dim not in (
            AIR_FULL_ACTION_DIM,
            AIR_COMBAT_HYBRID_ACTION_DIM,
        ):
            raise ValueError(f"unsupported Air action dimension: {self.action_dim}")
        self._fire_latched = False
        self._last_target_contact = False

    def reset(self) -> None:
        self._fire_latched = False
        self._last_target_contact = False

    def apply(
        self,
        action: Any,
        *,
        intent: AirTacticalActionIntent,
    ) -> AirActionApplication:
        values = np.asarray(action, dtype=np.float32).reshape(-1).copy()
        if values.size != self.action_dim:
            raise ValueError(
                f"Air action adapter received {values.size} values, expected {self.action_dim}"
            )
        tms_pulse = 1.0 if intent.target_contact_present and not self._last_target_contact else 0.0
        master_arm = (
            1.0
            if intent.authorization_to_fire
            and intent.target_contact_present
            and intent.shot_budget_available
            else 0.0
        )
        fire_pulse = 1.0 if intent.request_fire and not self._fire_latched else 0.0
        if not intent.fire_window_open or intent.assessment_blocked or not intent.shot_budget_available:
            self._fire_latched = False
        elif intent.request_fire:
            self._fire_latched = True
        self._last_target_contact = bool(intent.target_contact_present)

        station_available = (
            intent.target_contact_present
            and intent.authorization_to_fire
            and intent.shot_budget_available
        )
        if self.action_dim == AIR_FULL_ACTION_DIM:
            values[9] = 1.0
            values[10] = 0.0
            values[11] = 0.0
            values[12] = tms_pulse
            values[13] = master_arm
            values[14] = fire_pulse
            values[15] = 0.0
            values[16] = (float(intent.station_id) / 7.0) if station_available else 0.0
        else:
            values[4] = 0.0
            values[5] = 0.0
            values[6] = 1.0
            values[7] = tms_pulse
            values[8] = master_arm
            values[9] = fire_pulse
            values[10] = 0.0
            values[11] = float(intent.station_id) if station_available else 0.0
        return AirActionApplication(
            action=values,
            tms_pulse=tms_pulse,
            master_arm=master_arm,
            fire_pulse=fire_pulse,
        )


__all__ = [
    "AIR_COMBAT_HYBRID_ACTION_DIM",
    "AIR_FULL_ACTION_DIM",
    "AirActionAdapter",
    "AirActionLayoutAdapter",
]
